"""
MEPIA — FastAPI backend
Expone /ingest, /audit y /business/{id}/onboarding al frontend Next.js
"""
import sys
import os
from pathlib import Path

# Agrega tanto la raíz del proyecto (para agents/, utils/) como api/ (para core/)
# al path de Python, sin importar desde dónde se corra uvicorn.
_ROOT = Path(__file__).resolve().parent.parent   # MEPIA-V2/
_API  = Path(__file__).resolve().parent          # MEPIA-V2/api/
for _p in [str(_ROOT), str(_API)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import asyncio
from dataclasses import asdict
from datetime import date as date_type, datetime, timezone
from decimal import Decimal
from typing import Literal, Optional
from uuid import uuid4

from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client, Client

from agents import CashReconciliationAgent, OperativeCostAgent, BusinessHealthAgent
from agents.gatekeeper import GatekeeperAgent
from agents.calc_engine import run_calc_engine, CalcRunRequest, CalcRunResult
from agents.forensic_cfo import ForensicCFOAgent, ForensicReport
from agents.ceo_orchestrator import (
    N05CEOOrchestrator,
    OrchestratorResult,
    AuditInsight,
)
from agents.parallel_orchestrator import (
    N06ParallelOrchestrator,
    Layer2RunPayload,
    ParallelGatherResult,
    CircuitResetPayload,
)
from utils.memory_service import MemoryService, MemoryChunk
from agents.layer3_graph import build_layer3_graph
from agents.pos_parser import extract_pos_data, POSExtractResult
from agents.factura_parser import (
    extract_factura_xml,
    extract_factura_pdf,
    FacturaExtractResult,
    ExtractedFacturaFields,
    calculate_sha256,
)
from agents.api_ingest import (
    APIIngestPayload,
    APIIngestResult,
    ValidationResult,
    validate_payload,
    persist_ingestion,
)
from core.config import settings

# ---------------------------------------------------------------------------
# Exportar variables de settings a os.environ para agentes que usan os.environ
# directamente (N05, S4, N13, etc.)
# ---------------------------------------------------------------------------
for _key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
    _val = getattr(settings, _key, None)
    if _val and _key not in os.environ:
        os.environ[_key] = _val

app = FastAPI(title="MEPIA Agents API")

# ---------------------------------------------------------------------------
# Global exception handler — muestra tracebacks en logs de desarrollo
# ---------------------------------------------------------------------------
import logging
import traceback as _tb
from fastapi.responses import JSONResponse
from starlette.requests import Request

logging.basicConfig(level=logging.DEBUG if settings.ENVIRONMENT == "dev" else logging.INFO)
_logger = logging.getLogger("mepia")


@app.exception_handler(Exception)
async def _global_exception_handler(request: Request, exc: Exception):
    _logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url.path, _tb.format_exc())
    return JSONResponse(status_code=500, content={"detail": str(exc)})

# ---------------------------------------------------------------------------
# Singleton de MemoryService — inicializado en startup
# Spec: mem_memory_layer.md
# ---------------------------------------------------------------------------
_memory_service: Optional[MemoryService] = None
_layer3_app = None  # Inicializado en startup con build_layer3_graph(memory_service)


@app.on_event("startup")
async def startup_event():
    """Inicializa MemoryService y layer3_app al arrancar el servidor."""
    global _memory_service, _layer3_app
    db = get_supabase()
    _memory_service = MemoryService(supabase_client=db)
    _layer3_app = build_layer3_graph(_memory_service)


def get_memory_service() -> MemoryService:
    """Retorna el singleton de MemoryService. Crea uno nuevo si no existe."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService(supabase_client=get_supabase())
    return _memory_service

# En prod, reemplazar por el dominio real del frontend.
_ALLOWED_ORIGINS = (
    ["http://localhost:3000"]
    if settings.ENVIRONMENT == "dev"
    else ["https://mepia.app"]  # ajustar al dominio de producción
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Supabase client (singleton)
# ---------------------------------------------------------------------------
def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


# ---------------------------------------------------------------------------
# Pydantic models — OnboardingIdentityPayload (spec: n10_onboarding_identidad.md)
# ---------------------------------------------------------------------------
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
    brand_identity: BrandIdentity
    audit_tolerances: AuditTolerances
    expected_cost_structure: list[ExpectedCostStructure] = Field(min_length=1)
    audit_rules: AuditRules

    def validate_thresholds(self) -> None:
        """Regla de negocio: umbral crítico debe ser menor que warning."""
        t = self.audit_tolerances
        if t.margin_critical_threshold >= t.margin_warning_threshold:
            raise ValueError(
                "margin_critical_threshold debe ser menor que margin_warning_threshold"
            )

# ---------------------------------------------------------------------------
# Flujo paralelo: los tres agentes corren simultáneamente
# ---------------------------------------------------------------------------
async def run_audit_pipeline(payload: dict) -> list[dict]:
    loop = asyncio.get_event_loop()

    cash_agent   = CashReconciliationAgent()
    cost_agent   = OperativeCostAgent()
    health_agent = BusinessHealthAgent()

    results = await asyncio.gather(
        loop.run_in_executor(None, cash_agent.run,   payload.get("cash", {})),
        loop.run_in_executor(None, cost_agent.run,   payload.get("cost", {})),
        loop.run_in_executor(None, health_agent.run, payload.get("health", {})),
    )

    return [asdict(r) for r in results]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/audit")
async def audit():
    """Devuelve resultados de auditoría con datos de ejemplo."""
    sample_payload = {
        "cash":   {"pos_total": 5150.00, "deposit": 5000.00},
        "cost":   {"item": "leche deslactosada", "prev": 800.0, "current": 896.0},
        "health": {"revenue": 50000.0, "costs": 41000.0, "archetype": "Operative Genius"},
    }
    rows = await run_audit_pipeline(sample_payload)
    return {"rows": rows}


@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    """Recibe un PDF, extrae datos y dispara el pipeline de agentes."""
    content = await file.read()
    # TODO: parsear PDF con pdfplumber y extraer tablas de POS/facturas
    # Por ahora retorna confirmación
    return {
        "status": "received",
        "filename": file.filename,
        "size_kb": round(len(content) / 1024, 1),
        "message": "Documento en cola para procesamiento.",
    }


# ---------------------------------------------------------------------------
# Onboarding — N10 Identidad del Negocio
# Spec: .kiro/specs/mepia/n10_onboarding_identidad.md
# ---------------------------------------------------------------------------

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
    db: Client,
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


@app.post("/business/{business_id}/onboarding", status_code=201)
async def create_onboarding(business_id: str, payload: OnboardingIdentityPayload):
    """
    POST /business/{business_id}/onboarding
    Crea la configuración de identidad y auditoría del negocio.
    Prerequisito obligatorio para ejecutar Layer 3.
    """
    # Validación de umbrales cruzados
    try:
        payload.validate_thresholds()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    db = get_supabase()

    # Verificar que el negocio existe
    biz = db.table("businesses").select("id").eq("id", business_id).execute()
    if not biz.data:
        raise HTTPException(
            status_code=404,
            detail=f"Negocio '{business_id}' no encontrado. Crear el negocio primero.",
        )

    # Verificar si ya existe onboarding (409 Conflict)
    existing = (
        db.table("business_onboarding")
        .select("id")
        .eq("business_id", business_id)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=409,
            detail="Onboarding ya completado. Usar PUT para actualizar.",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    memory_chunk_id = await asyncio.to_thread(
        _upsert_onboarding, db, business_id, payload, now_iso
    )

    return {
        "business_id": business_id,
        "onboarding_status": "complete",
        "memory_chunk_id": memory_chunk_id,
        "audit_config_stored": True,
        "completed_at": now_iso,
    }


@app.put("/business/{business_id}/onboarding", status_code=200)
async def update_onboarding(business_id: str, payload: OnboardingIdentityPayload):
    """
    PUT /business/{business_id}/onboarding
    Actualiza la configuración de onboarding. Crea nuevo chunk en mepia_memory.
    """
    try:
        payload.validate_thresholds()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    db = get_supabase()

    biz = db.table("businesses").select("id").eq("id", business_id).execute()
    if not biz.data:
        raise HTTPException(
            status_code=404,
            detail=f"Negocio '{business_id}' no encontrado.",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    memory_chunk_id = await asyncio.to_thread(
        _upsert_onboarding, db, business_id, payload, now_iso
    )

    return {
        "business_id": business_id,
        "onboarding_status": "updated",
        "memory_chunk_id": memory_chunk_id,
        "audit_config_stored": True,
        "completed_at": now_iso,
    }


@app.get("/business/{business_id}/onboarding/status")
async def get_onboarding_status(business_id: str):
    """
    GET /business/{business_id}/onboarding/status
    Verifica si el onboarding está completo antes de disparar Layer 3.
    """
    db = get_supabase()

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
        }

    row = onboarding.data[0]
    costs = (
        db.table("business_fixed_costs")
        .select("id")
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
    }


# ===========================================================================
# S1 Ingesta — N01: POS PDF Input
# Spec: .kiro/specs/mepia/n01_pos_pdf_input.md
# ===========================================================================

_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


class POSIngestResult(BaseModel):
    file_id: str
    storage_path: str
    extraction_status: Literal["success", "needs_human_review"]
    needs_human_review: bool
    uploaded_at: str
    date: Optional[str] = None
    totals: Optional[dict] = None
    payment_methods: Optional[dict] = None
    line_items: Optional[list] = None
    ocr_confidence: dict
    missing_fields: Optional[list[str]] = None


class POSReviewPayload(BaseModel):
    date: str                          # YYYY-MM-DD
    totals: dict                       # { cash, card, total }
    payment_methods: Optional[dict] = None


def _upload_to_storage(db: Client, path: str, data: bytes) -> str:
    """
    Sube bytes a Supabase Storage en el bucket 'mepia-documents'.
    Si el bucket no existe o hay error, retorna un path local como fallback.
    """
    try:
        db.storage.from_("mepia-documents").upload(
            path,
            data,
            {"content-type": "application/octet-stream"},
        )
        return path
    except Exception:
        # Fallback: continuar sin subir el archivo
        return f"local/{path.split('/')[-1]}"


def _verify_business_exists(db: Client, business_id: str) -> None:
    """Verifica que el business_id existe en la tabla businesses. HTTP 404 si no."""
    result = db.table("businesses").select("id").eq("id", business_id).execute()
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail=f"Negocio '{business_id}' no encontrado.",
        )


def _check_duplicate_sha256(db: Client, sha256: str, business_id: str) -> Optional[dict]:
    """
    Verifica si ya existe un documento con el mismo SHA-256 y business_id.
    Retorna el registro existente o None.
    """
    result = (
        db.table("documents")
        .select("*")
        .eq("business_id", business_id)
        .execute()
    )
    for row in result.data or []:
        extracted = row.get("extracted_data") or {}
        if extracted.get("sha256") == sha256:
            return row
    return None


@app.post("/ingest/pos", response_model=list[POSIngestResult])
async def ingest_pos(
    file: UploadFile = File(...),
    business_id: str = Form(...),
):
    """
    POST /ingest/pos
    Recibe un PDF de ticket POS, extrae datos y persiste en documents + pos_inputs.
    Retorna un array de POSIngestResult, uno por día detectado.
    Spec: n01_pos_pdf_input.md
    """
    # 1. Validar MIME
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        # Intentar detectar por nombre si el content_type es genérico
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(
                status_code=422,
                detail="El archivo debe ser un PDF (MIME: application/pdf).",
            )

    # 2. Leer bytes y validar tamaño
    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=422, detail="El archivo está vacío.")
    if len(pdf_bytes) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=422, detail="El archivo supera el límite de 20 MB.")

    db = get_supabase()

    # 3. Verificar business_id
    _verify_business_exists(db, business_id)

    # 4. Calcular SHA-256 y verificar deduplicación
    from agents.pos_parser import calculate_sha256 as pos_sha256
    sha = pos_sha256(pdf_bytes)
    existing = _check_duplicate_sha256(db, sha, business_id)
    if existing:
        # Retornar resultado existente sin duplicar
        uploaded_at = existing.get("uploaded_at", datetime.now(timezone.utc).isoformat())
        extracted = existing.get("extracted_data") or {}
        return [
            POSIngestResult(
                file_id=existing["id"],
                storage_path=existing.get("storage_path", ""),
                extraction_status="success" if not existing.get("needs_human_review") else "needs_human_review",
                needs_human_review=existing.get("needs_human_review", False),
                uploaded_at=uploaded_at,
                date=extracted.get("date"),
                totals=extracted.get("totals"),
                payment_methods=extracted.get("payment_methods"),
                line_items=extracted.get("line_items"),
                ocr_confidence=extracted.get("ocr_confidence", {}),
                missing_fields=extracted.get("missing_fields"),
            )
        ]

    # 5. Extraer datos del PDF
    extract_results: list[POSExtractResult] = await asyncio.to_thread(
        extract_pos_data, pdf_bytes
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    output: list[POSIngestResult] = []

    for result in extract_results:
        file_id = str(uuid4())
        date_str = result.date.isoformat() if result.date else "unknown"

        # 6a. Subir a Storage
        storage_path = _upload_to_storage(
            db,
            f"pos-tickets/{business_id}/{date_str}/{file_id}.pdf",
            pdf_bytes,
        )

        # Serializar datos extraídos para JSONB
        extracted_data = {
            "sha256": sha,
            "date": date_str if result.date else None,
            "totals": (
                {
                    "cash": str(result.totals.cash),
                    "card": str(result.totals.card),
                    "total": str(result.totals.total),
                }
                if result.totals
                else None
            ),
            "payment_methods": (
                {
                    "cash": str(result.payment_methods.cash),
                    "card": str(result.payment_methods.card),
                    "other": str(result.payment_methods.other),
                }
                if result.payment_methods
                else None
            ),
            "line_items": (
                [li.model_dump(mode="json") for li in result.line_items]
                if result.line_items
                else None
            ),
            "ocr_confidence": result.ocr_confidence.model_dump(),
            "missing_fields": result.missing_fields,
        }

        ocr_status = "error" if result.needs_human_review else "processed"
        ocr_confidence_val = result.ocr_confidence.totals

        # 6b. Insertar en documents
        doc_row = {
            "id": file_id,
            "business_id": business_id,
            "storage_path": storage_path,
            "filename": file.filename or f"{file_id}.pdf",
            "document_type": "PDF",
            "ocr_status": ocr_status,
            "ocr_confidence": ocr_confidence_val,
            "needs_human_review": result.needs_human_review,
            "extracted_data": extracted_data,
        }
        db.table("documents").insert(doc_row).execute()

        # 6c. Insertar en pos_inputs si no requiere revisión
        if not result.needs_human_review and result.totals and result.date:
            db.table("pos_inputs").insert(
                {
                    "business_id": business_id,
                    "date": result.date.isoformat(),
                    "total_sales": float(result.totals.total),
                    "cash_sales": float(result.totals.cash),
                    "card_sales": float(result.totals.card),
                }
            ).execute()

        output.append(
            POSIngestResult(
                file_id=file_id,
                storage_path=storage_path,
                extraction_status="needs_human_review" if result.needs_human_review else "success",
                needs_human_review=result.needs_human_review,
                uploaded_at=now_iso,
                date=date_str if result.date else None,
                totals=(
                    {
                        "cash": float(result.totals.cash),
                        "card": float(result.totals.card),
                        "total": float(result.totals.total),
                    }
                    if result.totals
                    else None
                ),
                payment_methods=(
                    {
                        "cash": float(result.payment_methods.cash),
                        "card": float(result.payment_methods.card),
                        "other": float(result.payment_methods.other),
                    }
                    if result.payment_methods
                    else None
                ),
                line_items=(
                    [li.model_dump(mode="json") for li in result.line_items]
                    if result.line_items
                    else None
                ),
                ocr_confidence=result.ocr_confidence.model_dump(),
                missing_fields=result.missing_fields,
            )
        )

    return output


@app.patch("/ingest/pos/{file_id}/review")
async def review_pos(file_id: str, payload: POSReviewPayload):
    """
    PATCH /ingest/pos/{file_id}/review
    Permite enviar datos corregidos para un documento POS que requiere revisión humana.
    Spec: n01_pos_pdf_input.md
    """
    db = get_supabase()

    # 1. Verificar que file_id existe
    doc_result = db.table("documents").select("*").eq("id", file_id).execute()
    if not doc_result.data:
        raise HTTPException(status_code=404, detail=f"Documento '{file_id}' no encontrado.")

    doc = doc_result.data[0]

    # 2. Verificar que necesita revisión
    if not doc.get("needs_human_review", False):
        raise HTTPException(
            status_code=409,
            detail="El documento ya fue procesado. No requiere revisión.",
        )

    # 3. Actualizar documents
    db.table("documents").update(
        {
            "needs_human_review": False,
            "ocr_status": "processed",
        }
    ).eq("id", file_id).execute()

    # 4. Insertar en pos_inputs con datos corregidos
    totals = payload.totals
    db.table("pos_inputs").insert(
        {
            "business_id": doc["business_id"],
            "date": payload.date,
            "total_sales": float(totals.get("total", 0)),
            "cash_sales": float(totals.get("cash", 0)),
            "card_sales": float(totals.get("card", 0)),
        }
    ).execute()

    return {
        "file_id": file_id,
        "extraction_status": "success",
        "needs_human_review": False,
    }


# ===========================================================================
# S1 Ingesta — N02: Facturas de Proveedor
# Spec: .kiro/specs/mepia/n02_facturas_input.md
# ===========================================================================

class FacturaIngestResult(BaseModel):
    file_id: str
    storage_path: str
    extraction_status: Literal["success", "needs_human_review"]
    needs_human_review: bool
    ocr_confidence: Optional[float] = None
    transaction_id: Optional[str] = None
    extracted_fields: Optional[dict] = None
    missing_fields: Optional[list[str]] = None


class FacturaReviewPayload(BaseModel):
    transaction_date: str              # YYYY-MM-DD
    amount: float
    tax_amount: float
    supplier_name: str
    concept: str
    document_reference: str


_XML_MIMES = {"text/xml", "application/xml", "text/plain"}
_PDF_MIMES = {"application/pdf", "application/octet-stream"}


@app.post("/ingest/factura", response_model=FacturaIngestResult)
async def ingest_factura(
    file: UploadFile = File(...),
    business_id: str = Form(...),
    document_type: str = Form(...),
):
    """
    POST /ingest/factura
    Recibe una factura XML (CFDI) o PDF, extrae datos y persiste en documents + transactions.
    Spec: n02_facturas_input.md
    """
    document_type = document_type.upper()
    if document_type not in ("XML", "PDF"):
        raise HTTPException(
            status_code=422,
            detail="document_type debe ser 'XML' o 'PDF'.",
        )

    # 1. Validar MIME vs document_type declarado
    content_type = file.content_type or ""
    filename = (file.filename or "").lower()

    if document_type == "XML":
        mime_ok = content_type in _XML_MIMES or filename.endswith(".xml")
    else:
        mime_ok = content_type in _PDF_MIMES or filename.endswith(".pdf")

    if not mime_ok:
        raise HTTPException(
            status_code=422,
            detail=f"El MIME del archivo ({content_type}) no coincide con document_type='{document_type}'.",
        )

    # 2. Leer bytes y validar tamaño
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=422, detail="El archivo está vacío.")
    if len(file_bytes) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=422, detail="El archivo supera el límite de 20 MB.")

    db = get_supabase()

    # 3. Verificar business_id
    _verify_business_exists(db, business_id)

    # 4. Deduplicación por SHA-256
    sha = calculate_sha256(file_bytes)
    existing = _check_duplicate_sha256(db, sha, business_id)
    if existing:
        extracted = existing.get("extracted_data") or {}
        return FacturaIngestResult(
            file_id=existing["id"],
            storage_path=existing.get("storage_path", ""),
            extraction_status="success" if not existing.get("needs_human_review") else "needs_human_review",
            needs_human_review=existing.get("needs_human_review", False),
            ocr_confidence=existing.get("ocr_confidence"),
            transaction_id=extracted.get("transaction_id"),
            extracted_fields=extracted.get("extracted_fields"),
            missing_fields=extracted.get("missing_fields"),
        )

    file_id = str(uuid4())
    ext = "xml" if document_type == "XML" else "pdf"
    now_iso = datetime.now(timezone.utc).isoformat()

    # 5. Extraer datos
    try:
        if document_type == "XML":
            extract_result: FacturaExtractResult = await asyncio.to_thread(
                extract_factura_xml, file_bytes
            )
        else:
            extract_result = await asyncio.to_thread(
                extract_factura_pdf, file_bytes
            )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Determinar fecha para el path de storage
    date_str = "unknown"
    if extract_result.extracted_fields and extract_result.extracted_fields.transaction_date:
        date_str = extract_result.extracted_fields.transaction_date.isoformat()

    # 6. Subir a Storage
    storage_path = _upload_to_storage(
        db,
        f"facturas/{business_id}/{date_str}/{file_id}.{ext}",
        file_bytes,
    )

    # 7. Insertar en documents PRIMERO (transactions tiene FK a documents)
    extracted_data_json = {
        "sha256": sha,
        "transaction_id": None,  # se actualiza después si se crea transaction
        "extracted_fields": (
            extract_result.extracted_fields.model_dump(mode="json")
            if extract_result.extracted_fields
            else None
        ),
        "missing_fields": extract_result.missing_fields,
    }

    ocr_status = "error" if extract_result.needs_human_review else "processed"
    db.table("documents").insert(
        {
            "id": file_id,
            "business_id": business_id,
            "storage_path": storage_path,
            "filename": file.filename or f"{file_id}.{ext}",
            "document_type": document_type,
            "ocr_status": ocr_status,
            "ocr_confidence": extract_result.ocr_confidence,
            "needs_human_review": extract_result.needs_human_review,
            "extracted_data": extracted_data_json,
        }
    ).execute()

    # 8. Insertar en transactions si no requiere revisión
    transaction_id: Optional[str] = None
    if not extract_result.needs_human_review and extract_result.extracted_fields:
        ef = extract_result.extracted_fields
        transaction_id = str(uuid4())
        db.table("transactions").insert(
            {
                "id": transaction_id,
                "business_id": business_id,
                "document_id": file_id,
                "type": "egreso",
                "category": "proveedor",
                "amount": float(ef.amount),
                "tax_amount": float(ef.tax_amount),
                "transaction_date": ef.transaction_date.isoformat(),
                "supplier_name": ef.supplier_name,
                "concept": ef.concept,
                "document_reference": ef.document_reference,
                "expense_behavior": None,
                "raw_metadata": extract_result.raw_metadata,
            }
        ).execute()

        # Actualizar extracted_data con el transaction_id
        extracted_data_json["transaction_id"] = transaction_id
        db.table("documents").update(
            {"extracted_data": extracted_data_json}
        ).eq("id", file_id).execute()

    return FacturaIngestResult(
        file_id=file_id,
        storage_path=storage_path,
        extraction_status=extract_result.extraction_status,
        needs_human_review=extract_result.needs_human_review,
        ocr_confidence=extract_result.ocr_confidence,
        transaction_id=transaction_id,
        extracted_fields=(
            extract_result.extracted_fields.model_dump(mode="json")
            if extract_result.extracted_fields
            else None
        ),
        missing_fields=extract_result.missing_fields,
    )


@app.patch("/ingest/factura/{file_id}/review")
async def review_factura(file_id: str, payload: FacturaReviewPayload):
    """
    PATCH /ingest/factura/{file_id}/review
    Permite enviar campos corregidos para una factura que requiere revisión humana.
    Spec: n02_facturas_input.md
    """
    db = get_supabase()

    # 1. Verificar que file_id existe
    doc_result = db.table("documents").select("*").eq("id", file_id).execute()
    if not doc_result.data:
        raise HTTPException(status_code=404, detail=f"Documento '{file_id}' no encontrado.")

    doc = doc_result.data[0]

    # 2. Verificar que necesita revisión
    if not doc.get("needs_human_review", False):
        raise HTTPException(
            status_code=409,
            detail="El documento ya fue procesado. No requiere revisión.",
        )

    # 3. Actualizar documents
    db.table("documents").update(
        {
            "needs_human_review": False,
            "ocr_status": "processed",
        }
    ).eq("id", file_id).execute()

    # 4. Insertar en transactions con datos corregidos
    transaction_id = str(uuid4())
    db.table("transactions").insert(
        {
            "id": transaction_id,
            "business_id": doc["business_id"],
            "document_id": file_id,
            "type": "egreso",
            "category": "proveedor",
            "amount": payload.amount,
            "tax_amount": payload.tax_amount,
            "transaction_date": payload.transaction_date,
            "supplier_name": payload.supplier_name,
            "concept": payload.concept,
            "document_reference": payload.document_reference,
            "expense_behavior": None,
        }
    ).execute()

    return {
        "file_id": file_id,
        "transaction_id": transaction_id,
        "extraction_status": "success",
        "needs_human_review": False,
    }


# ===========================================================================
# S1B Ingesta API — POST /ingest/api-event (Ruta Primaria)
# Spec: .kiro/specs/mepia/s1b_ingesta_api.md
# ===========================================================================

@app.post("/ingest/api-event", response_model=APIIngestResult, status_code=201)
async def ingest_api_event(payload: APIIngestPayload):
    """
    POST /ingest/api-event
    Ruta primaria de ingesta — recibe datos estructurados del POS vía API JSON.
    Spec: s1b_ingesta_api.md
    """
    db = get_supabase()

    # 1. Verify business exists (rule 10)
    business_resp = (
        db.table("businesses")
        .select("id")
        .eq("id", str(payload.business_id))
        .execute()
    )
    business_exists = bool(business_resp.data)

    # 2. Get existing order_ids for idempotency (rule 5)
    existing_orders_resp = (
        db.table("transactions")
        .select("raw_metadata")
        .eq("business_id", str(payload.business_id))
        .eq("transaction_date", payload.date.isoformat())
        .execute()
    )
    existing_order_ids: set[str] = set()
    for row in existing_orders_resp.data or []:
        meta = row.get("raw_metadata") or {}
        order_id = meta.get("order_id")
        if order_id:
            existing_order_ids.add(order_id)

    # 3. Validate payload (rules 1–10)
    validation = validate_payload(payload, existing_order_ids, business_exists)

    # 4. Return appropriate HTTP error if rejected
    if validation.is_rejected:
        if "404" in (validation.reject_reason or ""):
            raise HTTPException(status_code=404, detail=validation.reject_reason)
        elif "422" in (validation.reject_reason or ""):
            raise HTTPException(status_code=422, detail=validation.reject_reason)
        else:
            raise HTTPException(status_code=400, detail=validation.reject_reason)

    # 5. Persist to all tables
    result = await asyncio.to_thread(persist_ingestion, payload, validation, db)

    return result


# ===========================================================================
# S1 Ingesta — N03: Human Input Endpoints
# Spec: .kiro/specs/mepia/n03_human_input_endpoints.md
# ===========================================================================

# ---------------------------------------------------------------------------
# 4.3.1 — Expense Behavior
# ---------------------------------------------------------------------------

class ExpenseBehaviorPayload(BaseModel):
    expense_behavior: Literal["FIXED", "VARIABLE", "CAPEX"]
    confirmed_by: str  # UUID del usuario
    force: bool = False  # permite sobreescribir si ya está confirmado


@app.patch("/transactions/{transaction_id}/expense-behavior")
async def confirm_expense_behavior(
    transaction_id: str,
    payload: ExpenseBehaviorPayload,
):
    """
    PATCH /transactions/{transaction_id}/expense-behavior
    Confirma o corrige la clasificación de un gasto extraído.
    Spec: n03_human_input_endpoints.md §1
    """
    db = get_supabase()

    # 1. Verificar que transaction_id existe
    tx_result = db.table("transactions").select("*").eq("id", transaction_id).execute()
    if not tx_result.data:
        raise HTTPException(
            status_code=404,
            detail=f"Transacción '{transaction_id}' no encontrada.",
        )

    tx = tx_result.data[0]

    # 2. Si ya tiene expense_behavior confirmado y force=False → 409
    if tx.get("expense_behavior") is not None and not payload.force:
        raise HTTPException(
            status_code=409,
            detail=(
                "La transacción ya tiene expense_behavior confirmado. "
                "Usar force=true para sobreescribir."
            ),
        )

    # 3. Actualizar transactions.expense_behavior
    now_iso = datetime.now(timezone.utc).isoformat()
    db.table("transactions").update(
        {"expense_behavior": payload.expense_behavior}
    ).eq("id", transaction_id).execute()

    # 4. Disparar re-evaluación de S2 (Gatekeeper)
    business_id = tx.get("business_id")
    transaction_date = tx.get("transaction_date")
    if business_id and transaction_date:
        try:
            GatekeeperAgent(db).evaluate(business_id, transaction_date)
        except Exception:
            pass  # El trigger no debe bloquear la respuesta

    # 5. Retornar resultado
    return {
        "transaction_id": transaction_id,
        "expense_behavior": payload.expense_behavior,
        "confirmed_by": payload.confirmed_by,
        "confirmed_at": now_iso,
        "gatekeeper_triggered": True,
    }


# ---------------------------------------------------------------------------
# 4.3.2 — Pending Review
# ---------------------------------------------------------------------------

_FIXED_SUPPLIER_KEYWORDS = {
    "CFE", "TELMEX", "IZZI", "TOTALPLAY", "MEGACABLE", "RENTA", "ARRENDAMIENTO"
}


def _infer_suggested_behavior(
    supplier_name: Optional[str],
    category: Optional[str],
) -> str:
    """
    Infiere el expense_behavior sugerido a partir de supplier_name y category.
    Nunca persiste el valor — solo es una sugerencia para el cliente.
    """
    if supplier_name:
        upper = supplier_name.upper()
        for keyword in _FIXED_SUPPLIER_KEYWORDS:
            if keyword in upper:
                return "FIXED"
    if category == "nomina":
        return "FIXED"
    return "VARIABLE"


@app.get("/transactions/pending-review")
async def get_pending_review(
    business_id: str,
    date: Optional[str] = None,
):
    """
    GET /transactions/pending-review
    Lista transacciones con expense_behavior=null para un negocio y fecha.
    Spec: n03_human_input_endpoints.md §1
    """
    if not business_id:
        raise HTTPException(status_code=400, detail="business_id es requerido.")

    # Default: hoy en formato YYYY-MM-DD
    if date is None:
        date = datetime.now(timezone.utc).date().isoformat()

    db = get_supabase()

    # Consultar transactions con expense_behavior IS NULL
    result = (
        db.table("transactions")
        .select("id, supplier_name, concept, amount, transaction_date, category")
        .eq("business_id", business_id)
        .eq("transaction_date", date)
        .is_("expense_behavior", "null")
        .execute()
    )

    pending = [
        {
            "transaction_id": row["id"],
            "supplier_name": row.get("supplier_name"),
            "concept": row.get("concept"),
            "amount": float(row["amount"]) if row.get("amount") is not None else None,
            "transaction_date": row.get("transaction_date"),
            "suggested_behavior": _infer_suggested_behavior(
                row.get("supplier_name"), row.get("category")
            ),
        }
        for row in (result.data or [])
    ]

    return {"pending": pending, "total": len(pending)}


# ---------------------------------------------------------------------------
# 4.3.3 — Cash Counts (POST + PUT)
# ---------------------------------------------------------------------------

class CashCountPayload(BaseModel):
    business_id: str
    date: str  # YYYY-MM-DD
    initial_float: float = 0.0
    actual_counted: float
    cash_payouts: float = 0.0
    recorded_by: str  # UUID


@app.post("/cash-counts", status_code=201)
async def create_cash_count(payload: CashCountPayload):
    """
    POST /cash-counts
    Registra el conteo físico del cajón para un negocio y fecha.
    Spec: n03_human_input_endpoints.md §2
    """
    db = get_supabase()

    # 1. Verificar business_id existe
    biz = db.table("businesses").select("id").eq("id", payload.business_id).execute()
    if not biz.data:
        raise HTTPException(
            status_code=404,
            detail=f"Negocio '{payload.business_id}' no encontrado.",
        )

    # 2. Verificar que date no es futuro
    try:
        count_date = date_type.fromisoformat(payload.date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Formato de fecha inválido. Usar YYYY-MM-DD.")

    today = datetime.now(timezone.utc).date()
    if count_date > today:
        raise HTTPException(
            status_code=422,
            detail="La fecha del conteo no puede ser futura.",
        )

    # 3. Verificar que no existe ya un conteo para business_id + date
    existing = (
        db.table("cash_counts")
        .select("id")
        .eq("business_id", payload.business_id)
        .eq("date", payload.date)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Ya existe un conteo para business_id='{payload.business_id}' "
                f"y date='{payload.date}'. Usar PUT para actualizar."
            ),
        )

    # 4. Insertar en cash_counts
    cash_count_id = str(uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    db.table("cash_counts").insert(
        {
            "id": cash_count_id,
            "business_id": payload.business_id,
            "date": payload.date,
            "initial_float": payload.initial_float,
            "actual_counted": payload.actual_counted,
            "cash_payouts": payload.cash_payouts,
            "recorded_by": payload.recorded_by,
            "created_at": now_iso,
        }
    ).execute()

    # 5. Disparar re-evaluación de S2 (Gatekeeper)
    try:
        GatekeeperAgent(db).evaluate(payload.business_id, payload.date)
    except Exception:
        pass  # El trigger no debe bloquear la respuesta

    # 6. Retornar registro creado con gatekeeper_triggered: true
    return {
        "cash_count_id": cash_count_id,
        "business_id": payload.business_id,
        "date": payload.date,
        "initial_float": payload.initial_float,
        "actual_counted": payload.actual_counted,
        "cash_payouts": payload.cash_payouts,
        "recorded_by": payload.recorded_by,
        "created_at": now_iso,
        "gatekeeper_triggered": True,
    }


@app.put("/cash-counts/{cash_count_id}")
async def update_cash_count(cash_count_id: str, payload: CashCountPayload):
    """
    PUT /cash-counts/{cash_count_id}
    Actualiza un conteo ya registrado (corrección antes del cierre contable).
    Spec: n03_human_input_endpoints.md §2
    """
    db = get_supabase()

    # 1. Verificar que cash_count_id existe
    existing = (
        db.table("cash_counts").select("*").eq("id", cash_count_id).execute()
    )
    if not existing.data:
        raise HTTPException(
            status_code=404,
            detail=f"Conteo '{cash_count_id}' no encontrado.",
        )

    # 2. Actualizar el registro
    now_iso = datetime.now(timezone.utc).isoformat()
    db.table("cash_counts").update(
        {
            "business_id": payload.business_id,
            "date": payload.date,
            "initial_float": payload.initial_float,
            "actual_counted": payload.actual_counted,
            "cash_payouts": payload.cash_payouts,
            "recorded_by": payload.recorded_by,
            "updated_at": now_iso,
        }
    ).eq("id", cash_count_id).execute()

    # 3. Disparar re-evaluación de S2 (Gatekeeper)
    try:
        GatekeeperAgent(db).evaluate(payload.business_id, payload.date)
    except Exception:
        pass  # El trigger no debe bloquear la respuesta

    # 4. Retornar registro actualizado con gatekeeper_triggered: true
    return {
        "cash_count_id": cash_count_id,
        "business_id": payload.business_id,
        "date": payload.date,
        "initial_float": payload.initial_float,
        "actual_counted": payload.actual_counted,
        "cash_payouts": payload.cash_payouts,
        "recorded_by": payload.recorded_by,
        "updated_at": now_iso,
        "gatekeeper_triggered": True,
    }


# ---------------------------------------------------------------------------
# 4.3.4 — GET /cash-counts
# ---------------------------------------------------------------------------

@app.get("/cash-counts")
async def get_cash_count(
    business_id: str,
    date: Optional[str] = None,
):
    """
    GET /cash-counts
    Consulta el estado del conteo para un negocio y fecha.
    Nunca retorna HTTP 404 — siempre HTTP 200.
    Spec: n03_human_input_endpoints.md §2
    """
    if not business_id:
        raise HTTPException(status_code=400, detail="business_id es requerido.")

    if date is None:
        date = datetime.now(timezone.utc).date().isoformat()

    db = get_supabase()

    result = (
        db.table("cash_counts")
        .select("*")
        .eq("business_id", business_id)
        .eq("date", date)
        .execute()
    )

    if result.data:
        row = result.data[0]
        return {
            "cash_count_id": row["id"],
            "date": row.get("date"),
            "initial_float": row.get("initial_float"),
            "actual_counted": row.get("actual_counted"),
            "cash_payouts": row.get("cash_payouts"),
            "recorded_by": row.get("recorded_by"),
            "created_at": row.get("created_at"),
        }

    # Sin conteo registrado — siempre HTTP 200
    return {
        "cash_count_id": None,
        "date": date,
        "status": "pending",
        "message": "No hay conteo registrado para esta fecha. cash_reconciliation en dormant.",
    }


# ---------------------------------------------------------------------------
# 4.3.5 — Daily Context (POST + PUT) — DEPRECATED (HTTP 410 Gone)
# ---------------------------------------------------------------------------


@app.post("/daily-context")
async def create_daily_context():
    """
    POST /daily-context — DEPRECATED (HTTP 410 Gone)
    daily_context fue retirado del pipeline en la sesión de codificación.
    """
    raise HTTPException(
        status_code=410,
        detail="daily_context fue retirado del pipeline. Este endpoint ya no está disponible."
    )


@app.put("/daily-context/{context_id}")
async def update_daily_context(context_id: str):
    """
    PUT /daily-context/{context_id} — DEPRECATED (HTTP 410 Gone)
    daily_context fue retirado del pipeline en la sesión de codificación.
    """
    raise HTTPException(
        status_code=410,
        detail="daily_context fue retirado del pipeline. Este endpoint ya no está disponible."
    )


# ===========================================================================
# S2 Gatekeeper — GET /gatekeeper/status
# Spec: .kiro/specs/mepia/s2_gatekeeper.md
# ===========================================================================

@app.get("/gatekeeper/status")
async def get_gatekeeper_status(
    business_id: str,
    date: Optional[str] = None,
):
    """
    GET /gatekeeper/status
    Retorna el GatekeeperResult actual para business_id + date.
    Si no hay registros en metric_status para esa fecha, evalúa primero.
    Spec: s2_gatekeeper.md
    """
    # 1. Default: hoy en formato YYYY-MM-DD
    if date is None:
        date = datetime.now(timezone.utc).date().isoformat()

    db = get_supabase()

    # 2. Verificar que business_id existe
    biz = db.table("businesses").select("id").eq("id", business_id).execute()
    if not biz.data:
        raise HTTPException(
            status_code=404,
            detail=f"Negocio '{business_id}' no encontrado.",
        )

    agent = GatekeeperAgent(db)

    # 3. Leer estado actual desde metric_status
    result = await asyncio.to_thread(agent.get_status, business_id, date)

    # 4. Si no hay registros → evaluar primero
    if (
        not result.active_metrics
        and not result.dormant_metrics
        and not result.blocked_metrics
    ):
        result = await asyncio.to_thread(agent.evaluate, business_id, date)

    # 5. Retornar GatekeeperResult
    return result


# ===========================================================================
# S3 Motor de Cálculo — POST /calc/run
# Spec: .kiro/specs/mepia/s3_motor_calculo.md
# ===========================================================================

@app.post("/calc/run", response_model=CalcRunResult)
async def run_calc(payload: CalcRunRequest):
    """
    POST /calc/run
    Ejecuta el Motor de Cálculo S3 para un negocio y fecha.

    Flujo:
        1. Verificar que el negocio existe
        2. Obtener GatekeeperResult actual (evalúa si no hay registros)
        3. Ejecutar run_calc_engine() con las métricas active
        4. Retornar CalcRunResult con results[] y skipped_metrics[]

    HTTP 409 si no hay ninguna métrica active (S2 no ha corrido o todo dormant).
    Spec: s3_motor_calculo.md
    """
    db = get_supabase()

    # 1. Verificar que el negocio existe
    _verify_business_exists(db, payload.business_id)

    # 2. Obtener estado del Gatekeeper
    agent = GatekeeperAgent(db)
    gk_result = await asyncio.to_thread(agent.get_status, payload.business_id, payload.date)

    # Si no hay registros → evaluar primero
    if (
        not gk_result.active_metrics
        and not gk_result.dormant_metrics
        and not gk_result.blocked_metrics
    ):
        gk_result = await asyncio.to_thread(
            agent.evaluate, payload.business_id, payload.date
        )

    # 3. Si no hay métricas active → 409 (S3 no tiene nada que calcular)
    if not gk_result.active_metrics:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "No hay métricas active para calcular. Completar ingesta de datos primero.",
                "dormant_metrics": [dm.model_dump() for dm in gk_result.dormant_metrics],
                "blocked_metrics": [bm.model_dump() for bm in gk_result.blocked_metrics],
            },
        )

    # 4. Ejecutar Motor de Cálculo
    calc_result = await asyncio.to_thread(
        run_calc_engine,
        gk_result,
        db,
        payload.date,
        payload.business_id,
    )

    return calc_result


# ===========================================================================
# S4 Forensic CFO — POST /audit/run
# Spec: .kiro/specs/mepia/s4_auditoria_ia.md
# ===========================================================================

class AuditRunPayload(BaseModel):
    """
    Payload de POST /audit/run — exclusivo de S4 Forensic CFO.
    Sin arquetipo: el arquetipo es responsabilidad de N05.
    Spec: s4_auditoria_ia.md §Endpoint
    """
    business_id: str
    date: str  # YYYY-MM-DD


@app.post("/audit/run", response_model=ForensicReport)
async def run_audit(payload: AuditRunPayload):
    """
    POST /audit/run
    Ejecuta el Forensic CFO (S4) para un negocio y fecha.

    Flujo:
        1. Verificar que el negocio existe (404 si no)
        2. Verificar que S3 corrió — hay métricas active en metric_status (409 si no)
        3. Recuperar CalcResult[] desde audit_results (node_id="S3")
        4. daily_context_tags = None (daily_context fue retirado del pipeline)
        5. Ejecutar ForensicCFOAgent.run()
        6. Persistir ForensicReport en audit_results con node_id="S4"
        7. Retornar ForensicReport

    Spec: s4_auditoria_ia.md
    """
    db = get_supabase()

    # 1. Verificar que el negocio existe
    _verify_business_exists(db, payload.business_id)

    # 2. Verificar que S3 corrió — buscar registro en audit_results con node_id="S3"
    s3_check = (
        db.table("audit_results")
        .select("id, result_data")
        .eq("business_id", payload.business_id)
        .eq("date", payload.date)
        .eq("node_id", "S3")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not s3_check.data:
        raise HTTPException(
            status_code=409,
            detail=(
                f"S3 no ha corrido para business_id='{payload.business_id}' "
                f"y date='{payload.date}'. Ejecutar POST /calc/run primero."
            ),
        )

    # 3. Extraer CalcResult[] del último run de S3
    s3_result_data = s3_check.data[0].get("result_data") or {}
    calc_results: list[dict] = s3_result_data.get("results", [])

    if not calc_results:
        raise HTTPException(
            status_code=409,
            detail="S3 corrió pero no produjo resultados. Verificar datos de ingesta.",
        )

    # 4. daily_context fue retirado del pipeline — siempre None
    daily_context_tags: Optional[dict] = None

    # 5. Ejecutar ForensicCFOAgent
    agent = ForensicCFOAgent()
    report: ForensicReport = await asyncio.to_thread(
        agent.run,
        calc_results,
        payload.business_id,
        payload.date,
        daily_context_tags,
    )

    # 6. Persistir ForensicReport en audit_results con node_id="S4"
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        db.table("audit_results").insert(
            {
                "id": str(uuid4()),
                "business_id": payload.business_id,
                "date": payload.date,
                "pipeline_layer": "sequential",
                "node_id": "S4",
                "node_status": "success",
                "result_data": report.model_dump(mode="json"),
                "created_at": now_iso,
            }
        ).execute()
    except Exception:
        pass  # La persistencia no bloquea el retorno

    return report


# ===========================================================================
# N05 CEO Orchestrator — POST /orchestrator/run + GET /orchestrator/status/{run_id}
# Spec: .kiro/specs/mepia/n05_ceo_orchestrator.md
# ===========================================================================

class OrchestratorRunPayload(BaseModel):
    """
    Payload de POST /orchestrator/run.
    Spec: n05_ceo_orchestrator.md §OrchestratorRunPayload
    """
    business_id: str
    date: str                                          # YYYY-MM-DD
    archetype: Literal[
        "Operative Genius", "Product Purist", "Growth Hacker"
    ] = "Operative Genius"
    escalate_to_parallel: bool = True
    temporalidad: Literal["short", "medium", "long"] = "short"


@app.post("/orchestrator/run", response_model=OrchestratorResult)
async def orchestrator_run(payload: OrchestratorRunPayload):
    """
    POST /orchestrator/run
    Ejecuta el pipeline completo: S3 → S4 → N05 síntesis con arquetipo CEO.

    Prerequisitos verificados:
        1. business_id existe en businesses (404 si no)
        2. S2 corrió y hay al menos 1 métrica active (409 si no)
        3. No hay documentos con needs_human_review=true sin resolver (409 si hay)

    Spec: n05_ceo_orchestrator.md
    """
    db = get_supabase()

    # 1. Verificar que el negocio existe
    _verify_business_exists(db, payload.business_id)

    # 2. Verificar fecha no futura
    try:
        run_date = date_type.fromisoformat(payload.date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Formato de fecha inválido. Usar YYYY-MM-DD.")

    if run_date > datetime.now(timezone.utc).date():
        raise HTTPException(status_code=422, detail="La fecha no puede ser futura.")

    # 3. Verificar que S2 corrió y hay métricas active
    gk_agent = GatekeeperAgent(db)
    gk_result = await asyncio.to_thread(gk_agent.get_status, payload.business_id, payload.date)

    if not gk_result.active_metrics and not gk_result.dormant_metrics and not gk_result.blocked_metrics:
        gk_result = await asyncio.to_thread(gk_agent.evaluate, payload.business_id, payload.date)

    if not gk_result.active_metrics:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "No hay métricas active. Completar ingesta de datos primero.",
                "dormant_metrics": [dm.model_dump() for dm in gk_result.dormant_metrics],
                "blocked_metrics": [bm.model_dump() for bm in gk_result.blocked_metrics],
            },
        )

    # 4. Verificar que no hay documentos pendientes de revisión humana
    pending_docs = (
        db.table("documents")
        .select("id")
        .eq("business_id", payload.business_id)
        .eq("needs_human_review", True)
        .execute()
    )
    if pending_docs.data:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Hay {len(pending_docs.data)} documento(s) pendiente(s) de revisión humana. "
                "Resolver antes de ejecutar el pipeline."
            ),
        )

    # 5. Ejecutar N05 CEO Orchestrator (S3 → S4 → síntesis)
    try:
        orchestrator = N05CEOOrchestrator(db)
        result: OrchestratorResult = await asyncio.to_thread(
            orchestrator.run,
            payload.business_id,
            payload.date,
            payload.archetype,
            payload.escalate_to_parallel,
            payload.temporalidad,
        )
    except RuntimeError as exc:
        # Layer 2 falló → 503
        raise HTTPException(status_code=503, detail=str(exc))

    return result


@app.get("/orchestrator/status/{run_id}")
async def orchestrator_status(run_id: str):
    """
    GET /orchestrator/status/{run_id}
    Retorna el estado actual de una ejecución del orquestador.
    Spec: n05_ceo_orchestrator.md §GET /orchestrator/status
    """
    db = get_supabase()

    result = (
        db.table("audit_results")
        .select("*")
        .eq("id", run_id)
        .eq("node_id", "N05")
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_id}' no encontrado.",
        )

    row = result.data
    result_data = row.get("result_data") or {}

    return {
        "run_id": run_id,
        "business_id": row.get("business_id"),
        "date": row.get("date"),
        "pipeline_status": result_data.get("pipeline_status", "completed"),
        "current_node": "N05_synthesis",
        "completed_at": row.get("created_at"),
    }


@app.get("/orchestrator/result/{run_id}")
async def orchestrator_result(run_id: str):
    """
    GET /orchestrator/result/{run_id}
    Retorna el OrchestratorResult completo persistido por N05.
    Usado por el dashboard para renderizar resultados.
    """
    db = get_supabase()

    # Buscar por run_id en audit_results (N05 guarda el resultado completo)
    result = (
        db.table("audit_results")
        .select("*")
        .eq("id", run_id)
        .eq("node_id", "N05")
        .execute()
    )

    if not result.data:
        # Intentar buscar por run_id en la columna run_id
        result = (
            db.table("audit_results")
            .select("*")
            .eq("run_id", run_id)
            .eq("node_id", "N05")
            .execute()
        )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail=f"Resultado para run '{run_id}' no encontrado.",
        )

    row = result.data[0]
    result_data = row.get("result_data") or {}

    # Reconstruir OrchestratorResult desde result_data
    return {
        "run_id": run_id,
        "business_id": row.get("business_id"),
        "date": row.get("date"),
        "archetype": result_data.get("archetype", row.get("archetype", "Operative Genius")),
        "pipeline_status": result_data.get("pipeline_status", "completed"),
        "sequential_results": result_data.get("sequential_results", {
            "active_metrics": [],
            "calc_results": [],
            "forensic_report": result_data.get("forensic_report", {
                "business_id": row.get("business_id"),
                "date": row.get("date"),
                "risk_level": "low",
                "anomalies": [],
                "evidence_sources": [],
                "observed_causality": None,
                "generated_at": row.get("created_at"),
            }),
            "audit_insights": result_data.get("audit_insights", []),
        }),
        "escalation": result_data.get("escalation", {
            "triggered": False,
            "reason": None,
            "layer2_run_id": None,
        }),
        "dormant_metrics": result_data.get("dormant_metrics", []),
        "completed_at": row.get("created_at"),
    }


# ===========================================================================
# N06 Orquestador ADK — Layer 2 endpoints
# Spec: .kiro/specs/mepia/n06_orchestrator_adk.md
# ===========================================================================

@app.post("/layer2/run", response_model=ParallelGatherResult)
async def layer2_run(payload: Layer2RunPayload):
    """
    POST /layer2/run
    Ejecuta el scatter-gather de Layer 2 (N07, N08, N09) en paralelo.

    Idempotente: mismo layer2_run_id → retorna resultado existente.
    HTTP 503 si gather_status="failed" (los 3 nodos fallaron).
    Spec: n06_orchestrator_adk.md
    """
    db = get_supabase()
    _verify_business_exists(db, payload.business_id)

    orchestrator = N06ParallelOrchestrator(db)
    result = await orchestrator.run(payload)

    if result.gather_status == "failed":
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Los 3 nodos de Layer 2 fallaron.",
                "layer2_run_id": result.layer2_run_id,
                "node_results": [r.model_dump() for r in result.node_results],
            },
        )

    return result


@app.get("/layer2/status/{layer2_run_id}")
async def layer2_status(layer2_run_id: str):
    """
    GET /layer2/status/{layer2_run_id}
    Consulta el estado de una ejecución de Layer 2.
    P11: siempre HTTP 200 si el run existe, nunca 404.
    Spec: n06_orchestrator_adk.md
    """
    db = get_supabase()

    resp = (
        db.table("audit_results")
        .select("*")
        .eq("id", layer2_run_id)
        .eq("node_id", "N06")
        .single()
        .execute()
    )

    if not resp.data:
        raise HTTPException(
            status_code=404,
            detail=f"layer2_run_id '{layer2_run_id}' no encontrado.",
        )

    row = resp.data
    result_data = row.get("result_data") or {}
    gather_status = result_data.get("gather_status", row.get("node_status", "unknown"))

    node_results = result_data.get("node_results", [])
    nodes_completed = sum(1 for n in node_results if n.get("status") == "success")
    nodes_pending = [
        n["node_id"] for n in node_results
        if n.get("status") not in ("success", "timeout", "error")
    ]

    return {
        "layer2_run_id": layer2_run_id,
        "gather_status": gather_status,
        "nodes_completed": nodes_completed,
        "nodes_pending": nodes_pending,
        "started_at": row.get("created_at"),
        "completed_at": result_data.get("completed_at"),
    }


@app.post("/layer2/circuit-reset")
async def layer2_circuit_reset(payload: CircuitResetPayload):
    """
    POST /layer2/circuit-reset
    Resetea manualmente el circuit breaker de un nodo.
    HTTP 409 si el nodo no está en circuit_open.
    Spec: n06_orchestrator_adk.md
    """
    db = get_supabase()
    _verify_business_exists(db, payload.business_id)

    # Verificar estado actual del circuit breaker
    resp = (
        db.table("circuit_breaker_state")
        .select("*")
        .eq("business_id", payload.business_id)
        .eq("date", payload.date)
        .eq("node_id", payload.node_id)
        .execute()
    )

    if not resp.data:
        raise HTTPException(
            status_code=409,
            detail=f"No hay registro de circuit breaker para node_id='{payload.node_id}'. Reset innecesario.",
        )

    row = resp.data[0]
    if row.get("circuit_status") != "circuit_open":
        raise HTTPException(
            status_code=409,
            detail=f"El nodo '{payload.node_id}' no está en circuit_open. Estado actual: {row.get('circuit_status')}.",
        )

    # Resetear: consecutive_failures=0, circuit_status="closed"
    now_iso = datetime.now(timezone.utc).isoformat()
    db.table("circuit_breaker_state").update(
        {
            "consecutive_failures": 0,
            "circuit_status": "closed",
            "reset_by": payload.reset_by,
            "updated_at": now_iso,
        }
    ).eq("id", row["id"]).execute()

    return {
        "node_id": payload.node_id,
        "business_id": payload.business_id,
        "date": payload.date,
        "circuit_status": "closed",
        "reset_by": payload.reset_by,
        "reset_at": now_iso,
    }


# ===========================================================================
# MemoryService — POST /memory/store + GET /admin/memory/reconcile
# Spec: .kiro/specs/mepia/mem_memory_layer.md
# ===========================================================================

from fastapi import BackgroundTasks


@app.post("/memory/store", status_code=202)
async def memory_store(chunk: MemoryChunk, background_tasks: BackgroundTasks):
    """
    POST /memory/store
    Persiste un MemoryChunk en mepia_memory con status='pending_embed'.
    Responde 202 inmediatamente — el embedding se genera en BackgroundTask.

    Solo accesible para nodos N12, N13 y el proceso de onboarding.
    Spec: mem_memory_layer.md §store_memory
    """
    memory = get_memory_service()

    # Insertar chunk(s) en mepia_memory con status='pending_embed'
    await memory.store_memory(chunk)

    # Disparar embedding en background (no bloquea la respuesta)
    from utils.embedding_worker import process_pending_embeddings
    db = get_supabase()
    background_tasks.add_task(process_pending_embeddings, db, 10)

    return {
        "status": "accepted",
        "message": "Chunk(s) insertados. Embedding se generará en background.",
        "business_id": chunk.business_id,
        "node_origin": chunk.node_origin,
    }


@app.get("/admin/memory/reconcile")
async def memory_reconcile(background_tasks: BackgroundTasks):
    """
    GET /admin/memory/reconcile
    Reintenta generar embeddings para chunks en status='pending_embed' o 'failed'.
    Útil para reconciliación manual o al arrancar el servidor.
    Spec: mem_memory_layer.md §Reconciliación al arranque
    """
    from utils.embedding_worker import process_pending_embeddings
    db = get_supabase()

    # Ejecutar en background para no bloquear
    background_tasks.add_task(process_pending_embeddings, db, 100)

    return {
        "status": "accepted",
        "message": "Reconciliación iniciada en background. Revisar logs para resultado.",
    }


# ===========================================================================
# Layer 3 — POST /api/audit/layer3/run + GET status + GET result
# Spec: .kiro/specs/mepia/api_layer3.md
# ===========================================================================

class Layer3RunPayload(BaseModel):
    """Payload de POST /api/audit/layer3/run."""
    audit_run_id: Optional[str] = None        # UUID del run de Layer 2 (modo normal)
    layer2_run_id: Optional[str] = None       # si None en modo aislado → genera "isolated_"
    sequential_run_id: Optional[str] = None   # si None en modo aislado → genera "isolated_"
    # Campos requeridos en modo aislado
    business_id: Optional[str] = None
    date: Optional[str] = None
    archetype: Optional[Literal["Operative Genius", "Product Purist", "Growth Hacker"]] = None
    enriched_payload: Optional[dict] = None   # EnrichedAuditPayload pre-construido (opcional)


@app.post("/api/audit/layer3/run", status_code=202)
async def layer3_run(payload: Layer3RunPayload, background_tasks: BackgroundTasks):
    """
    POST /api/audit/layer3/run
    Dispara el grafo Layer 3 en background. Responde 202 inmediatamente.

    Modo normal: audit_run_id presente → reconstruye contexto desde audit_results.
    Modo aislado: audit_run_id ausente → usa business_id/date/archetype del body.

    Spec: api_layer3.md
    """
    global _layer3_app
    db = get_supabase()

    layer3_run_id = str(uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    if payload.audit_run_id:
        # ── Modo normal ───────────────────────────────────────────────────────
        # Verificar que el audit_run_id existe
        run_resp = (
            db.table("audit_results")
            .select("*")
            .eq("id", payload.audit_run_id)
            .eq("node_id", "N06")
            .single()
            .execute()
        )
        if not run_resp.data:
            raise HTTPException(
                status_code=404,
                detail=f"audit_run_id '{payload.audit_run_id}' no encontrado en Layer 2.",
            )

        # Idempotencia: verificar si ya existe un layer3 para este run
        existing_l3 = (
            db.table("audit_results")
            .select("id")
            .eq("node_id", "N10")
            .execute()
        )
        # Buscar por layer2_run_id en result_data
        for row in (existing_l3.data or []):
            rd = row.get("result_data") or {}
            if rd.get("layer2_run_id") == payload.audit_run_id:
                raise HTTPException(
                    status_code=409,
                    detail=f"Ya existe un Layer 3 para audit_run_id='{payload.audit_run_id}'.",
                )

        row = run_resp.data
        result_data = row.get("result_data") or {}
        business_id = row.get("business_id")
        date_str = row.get("date")
        archetype = result_data.get("archetype", "Operative Genius")
        layer2_run_id = payload.audit_run_id
        sequential_run_id = result_data.get("sequential_run_id", f"isolated_{uuid4()}")
        execution_mode = "normal"
        pgr = result_data  # ParallelGatherResult serializado
        source_s3_result_id = (
            row.get("source_s3_result_id")
            or result_data.get("source_s3_result_id")
        )

    else:
        # ── Modo aislado ──────────────────────────────────────────────────────
        if not payload.business_id or not payload.date or not payload.archetype:
            raise HTTPException(
                status_code=422,
                detail="Modo aislado requiere business_id, date y archetype.",
            )
        _verify_business_exists(db, payload.business_id)

        business_id = payload.business_id
        date_str = payload.date
        archetype = payload.archetype
        layer2_run_id = payload.layer2_run_id or f"isolated_{uuid4()}"
        sequential_run_id = payload.sequential_run_id or f"isolated_{uuid4()}"
        execution_mode = "isolated"
        pgr = {}
        source_s3_result_id = None

    # Verificar onboarding completo (HTTP 412 si no hay chunk de onboarding)
    onboarding_resp = (
        db.table("mepia_memory")
        .select("id")
        .eq("business_id", business_id)
        .execute()
    )
    has_onboarding = any(
        (r.get("metadata") or {}).get("node_origin") == "onboarding"
        for r in (onboarding_resp.data or [])
    )
    if not has_onboarding:
        raise HTTPException(
            status_code=412,
            detail={
                "error": "onboarding_required",
                "message": "El negocio no tiene onboarding completo. Ejecutar POST /business/{id}/onboarding primero.",
            },
        )

    # Construir estado inicial
    initial_state = {
        "layer3_run_id": layer3_run_id,
        "layer2_run_id": layer2_run_id,
        "sequential_run_id": sequential_run_id,
        "source_s3_result_id": source_s3_result_id,
        "business_id": business_id,
        "date": date_str,
        "archetype": archetype,
        "enriched_payload": payload.enriched_payload or {},
        "draft_report": None,
        "intentos_critico": 0,
        "feedback_critico": None,
        "historial_feedback": [],
        "tipos_falla_critico": [],
        "draft_status": "pending",
        "audit_results": [],
        "final_response": None,
        # Inyección de dependencias para los nodos
        "_db": db,
        "_memory_service": get_memory_service(),
        "_parallel_gather_result": pgr,
    }

    # Inicializar layer3_app si no está listo
    if _layer3_app is None:
        from agents.layer3_graph import build_layer3_graph
        _layer3_app = build_layer3_graph(get_memory_service())

    # Ejecutar grafo en background — responde 202 inmediatamente
    background_tasks.add_task(_layer3_app.ainvoke, initial_state)

    return {
        "layer3_run_id": layer3_run_id,
        "audit_run_id": payload.audit_run_id,
        "layer2_run_id": layer2_run_id,
        "sequential_run_id": sequential_run_id,
        "execution_mode": execution_mode,
        "status": "running",
        "started_at": now_iso,
    }


@app.get("/api/audit/layer3/status/{layer3_run_id}")
async def layer3_status(layer3_run_id: str):
    """
    GET /api/audit/layer3/status/{layer3_run_id}
    Polling del estado del grafo Layer 3.
    Spec: api_layer3.md
    """
    db = get_supabase()

    # Buscar el registro de N14 (terminal) o N10 (inicio)
    n14_resp = (
        db.table("audit_results")
        .select("*")
        .eq("node_id", "N14")
        .execute()
    )
    for row in (n14_resp.data or []):
        rd = row.get("result_data") or {}
        if rd.get("layer3_run_id") == layer3_run_id:
            return {
                "layer3_run_id": layer3_run_id,
                "status": "completed",
                "draft_status": rd.get("draft_status"),
                "current_node": "END",
                "intentos_critico": rd.get("intentos_critico", 0),
                "started_at": None,
                "completed_at": rd.get("finalized_at"),
            }

    # Buscar N10 para confirmar que el run existe
    n10_resp = (
        db.table("audit_results")
        .select("*")
        .eq("node_id", "N10")
        .execute()
    )
    for row in (n10_resp.data or []):
        rd = row.get("result_data") or {}
        if rd.get("layer3_run_id") == layer3_run_id:
            return {
                "layer3_run_id": layer3_run_id,
                "status": "running",
                "current_node": "n11_consultor",
                "intentos_critico": 0,
                "started_at": rd.get("built_at"),
                "completed_at": None,
            }

    raise HTTPException(
        status_code=404,
        detail=f"layer3_run_id '{layer3_run_id}' no encontrado.",
    )


@app.get("/api/audit/layer3/result/{layer3_run_id}")
async def layer3_result(layer3_run_id: str):
    """
    GET /api/audit/layer3/result/{layer3_run_id}
    Retorna el FinalReport completo.
    HTTP 409 si el grafo aún no completó.
    Spec: api_layer3.md
    """
    db = get_supabase()

    n14_resp = (
        db.table("audit_results")
        .select("*")
        .eq("node_id", "N14")
        .execute()
    )
    for row in (n14_resp.data or []):
        rd = row.get("result_data") or {}
        if rd.get("layer3_run_id") == layer3_run_id:
            return rd

    # Verificar si existe pero aún no completó
    n10_resp = (
        db.table("audit_results")
        .select("id")
        .eq("node_id", "N10")
        .execute()
    )
    for row in (n10_resp.data or []):
        rd = row.get("result_data") or {}
        if rd.get("layer3_run_id") == layer3_run_id:
            raise HTTPException(
                status_code=409,
                detail="El grafo Layer 3 aún no completó. Usar GET /status para verificar.",
            )

    raise HTTPException(
        status_code=404,
        detail=f"layer3_run_id '{layer3_run_id}' no encontrado.",
    )
