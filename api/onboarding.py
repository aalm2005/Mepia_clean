"""N10: configuración del negocio con sesión y autorización por recurso."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

from api.core.auth import AuthService

class AuditTolerances(BaseModel):
    max_cash_discrepancy_pct: float = Field(gt=0, le=1)
    max_cash_discrepancy_abs: Decimal = Field(ge=0)
    margin_warning_threshold: float = Field(gt=0, le=1)
    margin_critical_threshold: float = Field(gt=0, le=1)
    cost_spike_threshold_pct: float = Field(gt=0, le=1)

class ExpectedCostStructure(BaseModel):
    concept: str
    expected_monthly_amount: Decimal = Field(ge=0)
    tolerance_pct: float = Field(ge=0, le=1, default=0.05)
    expense_behavior: Literal["FIXED", "VARIABLE", "CAPEX"]

class AuditRules(BaseModel):
    red_alert_triggers: list[str] = Field(default=[])
    ignored_anomaly_types: list[str] = Field(default=[])
    audit_frequency: Literal["daily", "weekly"] = "daily"

class BrandIdentity(BaseModel):
    brand_voice: str = Field(max_length=500)
    prohibited_recommendations: list[str] = Field(default=[])
    priority_focus: Literal["efficiency", "quality", "growth"]

class OnboardingIdentityPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    brand_identity: BrandIdentity
    audit_tolerances: AuditTolerances
    expected_cost_structure: list[ExpectedCostStructure] = Field(default_factory=list)
    audit_rules: AuditRules

    def validate_thresholds(self) -> None:
        """Regla de negocio: umbral crítico debe ser menor que warning."""
        t = self.audit_tolerances
        if t.margin_critical_threshold >= t.margin_warning_threshold:
            raise ValueError(
                "margin_critical_threshold debe ser menor que margin_warning_threshold"
            )

def _build_memory_content(business_id: str, payload: OnboardingIdentityPayload) -> str:
    """Construye el texto del chunk de identidad para mepia_memory."""
    bi = payload.brand_identity
    at = payload.audit_tolerances
    ar = payload.audit_rules
    prohibited = ", ".join(bi.prohibited_recommendations) or "ninguna"
    triggers = ", ".join(ar.red_alert_triggers) or "ninguna"
    return (
        f"IDENTIDAD DE MARCA:\n{bi.brand_voice}\n\n"
        f"PROHIBIDO EN RECOMENDACIONES:\n{prohibited}\n\n"
        f"FOCO PRINCIPAL: {bi.priority_focus}\n\n"
        f"UMBRALES DE AUDITORÍA:\n"
        f"- Discrepancia caja máxima: {at.max_cash_discrepancy_pct * 100:.1f}%"
        f" o ${at.max_cash_discrepancy_abs} MXN (el más permisivo)\n"
        f"- Margen warning: {at.margin_warning_threshold * 100:.1f}%\n"
        f"- Margen crítico: {at.margin_critical_threshold * 100:.1f}%\n"
        f"- Spike de costo: {at.cost_spike_threshold_pct * 100:.1f}%\n\n"
        f"ALERTAS ROJAS AUTOMÁTICAS:\n{triggers}\n"
    )

def _upsert_onboarding(
    db: Any,
    business_id: str,
    payload: OnboardingIdentityPayload,
    now_iso: str,
) -> str:
    """
    Persiste la configuración en business_onboarding y business_fixed_costs.
    Retorna el memory_chunk_id insertado en mepia_memory.
    """
    bi = payload.brand_identity
    at = payload.audit_tolerances
    ar = payload.audit_rules

    # 1. Upsert en business_onboarding
    db.table("business_onboarding").upsert(
        {
            "business_id": business_id,
            "brand_voice": bi.brand_voice,
            "prohibited_recommendations": bi.prohibited_recommendations,
            "priority_focus": bi.priority_focus,
            "max_cash_discrepancy_pct": float(at.max_cash_discrepancy_pct),
            "max_cash_discrepancy_abs": float(at.max_cash_discrepancy_abs),
            "margin_warning_threshold": float(at.margin_warning_threshold),
            "margin_critical_threshold": float(at.margin_critical_threshold),
            "cost_spike_threshold_pct": float(at.cost_spike_threshold_pct),
            "audit_rules": ar.model_dump(),
            "completed_at": now_iso,
            "updated_at": now_iso,
        },
        on_conflict="business_id",
    ).execute()

    # 2. Marcar costos anteriores como inactivos
    db.table("business_fixed_costs").update({"is_active": False}).eq(
        "business_id", business_id
    ).execute()

    # 3. Insertar nueva estructura de costos
    if payload.expected_cost_structure:
        cost_rows = [
            {
                "business_id": business_id,
                "concept": item.concept,
                "expected_monthly_amount": float(item.expected_monthly_amount),
                "tolerance_pct": float(item.tolerance_pct),
                "expense_behavior": item.expense_behavior,
                "is_active": True,
            }
            for item in payload.expected_cost_structure
        ]
        db.table("business_fixed_costs").insert(cost_rows).execute()

    # 4. Insertar chunk en mepia_memory
    content = _build_memory_content(business_id, payload)
    memory_res = (
        db.table("mepia_memory")
        .insert(
            {
                "business_id": business_id,
                "source_audit_run_id": None,
                "content": content,
                "metadata": {
                    "node_origin": "onboarding",
                    "date": now_iso[:10],
                    "chunk_index": 0,
                    "chunk_total": 1,
                    "archetype": None,
                },
                "status": "pending_embed",
            }
        )
        .execute()
    )
    return memory_res.data[0]["id"]

def _read_onboarding_status(db: Any, business_id: str):
    """
    GET /business/{business_id}/onboarding/status
    Verifica si el onboarding está completo antes de disparar Layer 3.
    """

    biz = db.table("businesses").select("id").eq("id", business_id).execute()
    if not biz.data:
        raise HTTPException(status_code=404, detail=f"Negocio '{business_id}' no encontrado.")

    onboarding = (
        db.table("business_onboarding")
        .select("*")
        .eq("business_id", business_id)
        .execute()
    )

    if not onboarding.data:
        return {
            "business_id": business_id,
            "onboarding_complete": False,
            "completed_at": None,
            "has_brand_identity": False,
            "has_audit_tolerances": False,
            "has_cost_structure": False,
            "settings": None,
        }

    row = onboarding.data[0]
    costs = (
        db.table("business_fixed_costs")
        .select("id,concept,expected_monthly_amount,tolerance_pct,expense_behavior")
        .eq("business_id", business_id)
        .eq("is_active", True)
        .execute()
    )

    return {
        "business_id": business_id,
        "onboarding_complete": True,
        "completed_at": row.get("completed_at"),
        "has_brand_identity": bool(row.get("brand_voice")),
        "has_audit_tolerances": row.get("max_cash_discrepancy_pct") is not None,
        "has_cost_structure": len(costs.data) > 0,
        "settings": {
            "brand_identity": {
                "brand_voice": row.get("brand_voice") or "",
                "prohibited_recommendations": row.get("prohibited_recommendations") or [],
                "priority_focus": row.get("priority_focus") or "efficiency",
            },
            "audit_tolerances": {
                "max_cash_discrepancy_pct": row.get("max_cash_discrepancy_pct"),
                "max_cash_discrepancy_abs": row.get("max_cash_discrepancy_abs"),
                "margin_warning_threshold": row.get("margin_warning_threshold"),
                "margin_critical_threshold": row.get("margin_critical_threshold"),
                "cost_spike_threshold_pct": row.get("cost_spike_threshold_pct"),
            },
            "expected_cost_structure": [
                {
                    "concept": cost.get("concept", ""),
                    "amount_per_month": cost.get("expected_monthly_amount", 0),
                    "tolerance_pct": float(cost.get("tolerance_pct", 0)) * 100,
                    "expense_behavior": cost.get("expense_behavior", "FIXED"),
                }
                for cost in costs.data
            ],
            "audit_rules": row.get("audit_rules") or {
                "red_alert_triggers": [],
                "ignored_anomaly_types": [],
                "audit_frequency": "daily",
            },
        },
    }


@dataclass
class OnboardingAccess:
    business_id: str
    db: Any


def create_onboarding_router(*, auth: AuthService, db_factory: Callable) -> APIRouter:
    """Identidad y propiedad antes de leer o escribir ajustes del negocio."""
    router = APIRouter(tags=["Configuración del negocio"])
    bearer = HTTPBearer(auto_error=False)

    def access(business_id: UUID,
               credentials: HTTPAuthorizationCredentials | None = Security(bearer)):
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(401, "Inicia sesión", headers={"WWW-Authenticate": "Bearer"})
        user_id = auth.user_id(credentials.credentials)
        try:
            db = db_factory()
        except Exception:
            raise HTTPException(503, "Datos no disponibles") from None
        bid = str(business_id)
        auth.verify_business_access(db, user_id, bid)
        return OnboardingAccess(bid, db)

    @router.get("/business/{business_id}/onboarding/status")
    def status(response: Response, scope: OnboardingAccess = Depends(access)):
        response.headers["Cache-Control"] = "private, no-store"
        try:
            return _read_onboarding_status(scope.db, scope.business_id)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(503, "No fue posible cargar la configuración") from None

    async def save(payload: OnboardingIdentityPayload, scope: OnboardingAccess, *, create: bool):
        try:
            payload.validate_thresholds()
        except ValueError:
            raise HTTPException(422, "El límite crítico debe ser menor que el de advertencia") from None
        try:
            if create:
                rows = (scope.db.table("business_onboarding").select("id")
                        .eq("business_id", scope.business_id).execute()).data
                if rows:
                    raise HTTPException(409, "La configuración ya existe; puedes actualizarla")
            now = datetime.now(timezone.utc).isoformat()
            memory_id = await asyncio.to_thread(
                _upsert_onboarding, scope.db, scope.business_id, payload, now)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(503, "No fue posible guardar la configuración") from None
        return {"business_id": scope.business_id,
                "onboarding_status": "complete" if create else "updated",
                "memory_chunk_id": memory_id, "audit_config_stored": True,
                "completed_at": now}

    @router.post("/business/{business_id}/onboarding", status_code=201)
    async def create(payload: OnboardingIdentityPayload, response: Response,
                     scope: OnboardingAccess = Depends(access)):
        response.headers["Cache-Control"] = "private, no-store"
        return await save(payload, scope, create=True)

    @router.put("/business/{business_id}/onboarding")
    async def update(payload: OnboardingIdentityPayload, response: Response,
                     scope: OnboardingAccess = Depends(access)):
        response.headers["Cache-Control"] = "private, no-store"
        return await save(payload, scope, create=False)

    return router
