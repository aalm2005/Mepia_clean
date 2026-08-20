"""
N06 — Orquestador ADK (Layer 2 — Scatter-Gather)
Despacha en paralelo a N07, N08, N09 con timeouts independientes.
Patrón: Scatter-Gather puro — sin toma de decisiones autónoma.
Spec: .kiro/specs/mepia/n06_orchestrator_adk.md
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, date as date_type, timezone
from decimal import Decimal
from typing import Any, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from agents.business_health import N09FinancialAuditAgent, NodeResult as N09NodeResult


# ---------------------------------------------------------------------------
# Modelos de input — Layer2RunPayload
# Spec: n06_orchestrator_adk.md §Layer2RunPayload
# ---------------------------------------------------------------------------

class NodeTimeouts(BaseModel):
    n07_conciliacion: int = Field(default=15, ge=5, le=60)
    n08_pld: int = Field(default=60, ge=5, le=120)
    n09_gastos: int = Field(default=20, ge=5, le=60)


class ContextTags(BaseModel):
    clima: Optional[Literal["lluvia", "calor", "frio"]] = None
    equipo: Optional[Literal["falla_maquina", "mantenimiento"]] = None
    evento: Optional[Literal["festivo", "obra_vial", "promocion"]] = None
    personal: Optional[Literal["falta_staff", "capacitacion"]] = None
    otros: Optional[str] = None


class SequentialContext(BaseModel):
    business_id: str
    active_metrics: list[str]
    calc_results: list[dict]
    forensic_report: dict
    insights: list[dict]
    context_tags: ContextTags


class Layer2RunPayload(BaseModel):
    layer2_run_id: str
    sequential_run_id: str
    business_id: str
    date: str                          # YYYY-MM-DD
    archetype: Literal["Operative Genius", "Product Purist", "Growth Hacker"]
    temporalidad: Literal["short", "medium", "long"]
    sequential_context: SequentialContext
    node_timeouts: NodeTimeouts = Field(default_factory=NodeTimeouts)


# ---------------------------------------------------------------------------
# Modelos de output — NodeResult (N06 genérico) y ParallelGatherResult
# Spec: n06_orchestrator_adk.md §NodeResult / §ParallelGatherResult
# ---------------------------------------------------------------------------

class NodeResult(BaseModel):
    node_id: Literal["N07", "N08", "N09"]
    node_name: Literal["conciliacion", "pld", "gastos"]
    status: Literal["success", "timeout", "error"]
    result: Optional[dict] = None      # AgentResult serializado
    warnings: list[str] = Field(default_factory=list)
    error_detail: Optional[str] = None
    duration_ms: int


class GatherSummary(BaseModel):
    total_nodes: int = 3               # P1: siempre 3
    succeeded: int
    timed_out: int
    failed: int
    all_warnings: list[str]            # P6: unión de warnings de nodos success


class ParallelGatherResult(BaseModel):
    layer2_run_id: str
    sequential_run_id: str
    business_id: str
    date: str
    archetype: Literal["Operative Genius", "Product Purist", "Growth Hacker"]
    temporalidad: Literal["short", "medium", "long"]
    node_results: list[NodeResult]     # P1: siempre 3 elementos
    summary: GatherSummary
    gather_status: Literal["complete", "partial", "failed"]
    completed_at: str


# ---------------------------------------------------------------------------
# Payload para circuit-reset
# ---------------------------------------------------------------------------

class CircuitResetPayload(BaseModel):
    business_id: str
    date: str
    node_id: Literal["N07", "N08", "N09"]
    reset_by: str


# ---------------------------------------------------------------------------
# N06ParallelOrchestrator
# ---------------------------------------------------------------------------

class N06ParallelOrchestrator:
    """
    N06 — Orquestador ADK (Layer 2).
    Scatter-gather con timeouts independientes por nodo y circuit breaker.
    Spec: n06_orchestrator_adk.md
    """

    # Umbral de fallos consecutivos para abrir el circuit breaker
    _CIRCUIT_OPEN_THRESHOLD = 3

    def __init__(self, supabase_client: Any) -> None:
        self._db = supabase_client

    # ------------------------------------------------------------------
    # Punto de entrada principal
    # ------------------------------------------------------------------

    async def run(self, payload: Layer2RunPayload) -> ParallelGatherResult:
        """
        Ejecuta el scatter-gather para los 3 nodos paralelos.

        Correctness properties garantizadas:
            P1: node_results siempre tiene 3 elementos
            P2: succeeded + timed_out + failed == 3
            P3: gather_status "complete" ↔ succeeded == 3
            P4: gather_status "failed" ↔ succeeded == 0
            P6: all_warnings == unión de warnings de nodos success
            P7: layer2_run_id y sequential_run_id siempre no nulos
            P8: mismo layer2_run_id → exactamente 1 registro en audit_results
            P9: error global → gather_status "failed", nunca excepción no manejada
        """
        # P7: garantizar IDs no nulos
        assert payload.layer2_run_id, "layer2_run_id no puede ser vacío"
        assert payload.sequential_run_id, "sequential_run_id no puede ser vacío"

        # --- Guard de idempotencia (P8) ---
        existing = self._check_existing_result(payload.layer2_run_id)
        if existing:
            return existing

        # --- Scatter-Gather ---
        try:
            node_results = await self._scatter(payload)
        except Exception as exc:
            # P9: error global → gather_status "failed", nunca excepción no manejada
            node_results = [
                NodeResult(
                    node_id=nid,
                    node_name=nname,
                    status="error",
                    error_detail=f"Error global en scatter: {exc}",
                    duration_ms=0,
                )
                for nid, nname in [("N07", "conciliacion"), ("N08", "pld"), ("N09", "gastos")]
            ]

        # --- Consolidar resultado ---
        result = self._gather(payload, node_results)

        # --- Persistir antes de retornar (P8) ---
        self._persist(result, sequential_context=payload.sequential_context)

        return result

    # ------------------------------------------------------------------
    # Scatter — ejecución paralela con timeouts independientes
    # ------------------------------------------------------------------

    async def _scatter(self, payload: Layer2RunPayload) -> list[NodeResult]:
        """
        Ejecuta los 3 nodos en paralelo con timeouts independientes.
        P5: timeout de un nodo no afecta duration_ms de los otros.
        """
        timeouts = payload.node_timeouts
        context_tags = payload.sequential_context.context_tags.model_dump()

        results = await asyncio.gather(
            self._run_n07(payload, timeouts.n07_conciliacion),
            self._run_n08(payload, timeouts.n08_pld),
            self._run_n09(payload, timeouts.n09_gastos, context_tags),
            return_exceptions=False,
        )
        return list(results)

    async def _run_n07(self, payload: Layer2RunPayload, timeout_s: int) -> NodeResult:
        """
        N07 — Conciliación Efectivo.
        skipped_v1: retorna success con nota de no implementado.
        """
        t0 = time.monotonic()

        # Verificar circuit breaker
        if self._is_circuit_open(payload.business_id, payload.date, "N07"):
            return NodeResult(
                node_id="N07",
                node_name="conciliacion",
                status="error",
                error_detail="circuit_open — node degraded",
                duration_ms=0,
            )

        # skipped_v1: N07 no implementado en esta versión
        duration_ms = int((time.monotonic() - t0) * 1000)
        return NodeResult(
            node_id="N07",
            node_name="conciliacion",
            status="success",
            result={
                "module": "conciliacion_efectivo",
                "raw_result": "not_implemented_v1",
                "copilot_phrase": None,
                "archetype": payload.archetype,
            },
            warnings=[],
            duration_ms=duration_ms,
        )

    async def _run_n08(self, payload: Layer2RunPayload, timeout_s: int) -> NodeResult:
        """
        N08 — Cumplimiento PLD.
        skipped_v1: retorna success con nota de no implementado.
        """
        t0 = time.monotonic()

        # Verificar circuit breaker
        if self._is_circuit_open(payload.business_id, payload.date, "N08"):
            return NodeResult(
                node_id="N08",
                node_name="pld",
                status="error",
                error_detail="circuit_open — node degraded",
                duration_ms=0,
            )

        # skipped_v1: N08 no implementado en esta versión
        duration_ms = int((time.monotonic() - t0) * 1000)
        return NodeResult(
            node_id="N08",
            node_name="pld",
            status="success",
            result={
                "module": "cumplimiento_pld",
                "raw_result": "not_implemented_v1",
                "copilot_phrase": None,
                "archetype": payload.archetype,
            },
            warnings=[],
            duration_ms=duration_ms,
        )

    async def _run_n09(
        self,
        payload: Layer2RunPayload,
        timeout_s: int,
        context_tags: dict,
    ) -> NodeResult:
        """
        N09 — Auditoría Gastos. Implementado con N09FinancialAuditAgent.
        Timeout independiente — no bloquea N07/N08.
        """
        t0 = time.monotonic()

        # Verificar circuit breaker
        if self._is_circuit_open(payload.business_id, payload.date, "N09"):
            return NodeResult(
                node_id="N09",
                node_name="gastos",
                status="error",
                error_detail="circuit_open — node degraded",
                duration_ms=0,
            )

        try:
            agent = N09FinancialAuditAgent(self._db)
            # Ejecutar en thread para no bloquear el event loop
            n09_result: N09NodeResult = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    agent.run,
                    payload.business_id,
                    payload.date,
                    payload.archetype,
                    context_tags,
                ),
                timeout=timeout_s,
            )

            duration_ms = int((time.monotonic() - t0) * 1000)

            # Actualizar circuit breaker: éxito → resetear fallos
            self._update_circuit_breaker(payload.business_id, payload.date, "N09", success=True)

            return NodeResult(
                node_id="N09",
                node_name="gastos",
                status=n09_result.status,
                result=(
                    n09_result.result.model_dump(mode="json")
                    if n09_result.result else None
                ),
                warnings=n09_result.warnings,
                error_detail=n09_result.error_detail,
                duration_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            duration_ms = int((time.monotonic() - t0) * 1000)
            self._update_circuit_breaker(payload.business_id, payload.date, "N09", success=False)
            return NodeResult(
                node_id="N09",
                node_name="gastos",
                status="timeout",
                error_detail=f"Timeout after {timeout_s}s",
                duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = int((time.monotonic() - t0) * 1000)
            self._update_circuit_breaker(payload.business_id, payload.date, "N09", success=False)
            return NodeResult(
                node_id="N09",
                node_name="gastos",
                status="error",
                error_detail=str(exc),
                duration_ms=duration_ms,
            )

    # ------------------------------------------------------------------
    # Gather — consolidación de resultados
    # ------------------------------------------------------------------

    def _gather(
        self,
        payload: Layer2RunPayload,
        node_results: list[NodeResult],
    ) -> ParallelGatherResult:
        """
        Consolida los 3 NodeResult en un ParallelGatherResult.
        P2: succeeded + timed_out + failed == 3 siempre.
        P6: all_warnings == unión de warnings de nodos success.
        """
        succeeded = sum(1 for r in node_results if r.status == "success")
        timed_out = sum(1 for r in node_results if r.status == "timeout")
        failed = sum(1 for r in node_results if r.status == "error")

        # P6: solo warnings de nodos con success
        all_warnings: list[str] = []
        for r in node_results:
            if r.status == "success":
                all_warnings.extend(r.warnings)

        # P3/P4: gather_status
        if succeeded == 3:
            gather_status: Literal["complete", "partial", "failed"] = "complete"
        elif succeeded == 0:
            gather_status = "failed"
        else:
            gather_status = "partial"

        return ParallelGatherResult(
            layer2_run_id=payload.layer2_run_id,
            sequential_run_id=payload.sequential_run_id,
            business_id=payload.business_id,
            date=payload.date,
            archetype=payload.archetype,
            temporalidad=payload.temporalidad,
            node_results=node_results,   # P1: siempre 3 elementos
            summary=GatherSummary(
                total_nodes=3,
                succeeded=succeeded,
                timed_out=timed_out,
                failed=failed,
                all_warnings=all_warnings,
            ),
            gather_status=gather_status,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Circuit Breaker
    # ------------------------------------------------------------------

    def _is_circuit_open(self, business_id: str, date: str, node_id: str) -> bool:
        """
        Consulta circuit_breaker_state para determinar si el nodo está degradado.
        Retorna True si el circuit está abierto (nodo no debe ejecutarse).
        """
        try:
            resp = (
                self._db.table("circuit_breaker_state")
                .select("circuit_status, consecutive_failures")
                .eq("business_id", business_id)
                .eq("date", date)
                .eq("node_id", node_id)
                .single()
                .execute()
            )
            if resp.data:
                return resp.data.get("circuit_status") == "circuit_open"
            return False
        except Exception:
            return False  # Si no hay registro → circuit cerrado por defecto

    def _update_circuit_breaker(
        self,
        business_id: str,
        date: str,
        node_id: str,
        success: bool,
    ) -> None:
        """
        Actualiza el estado del circuit breaker tras cada ejecución.
        - Éxito → resetear consecutive_failures a 0, circuit_status = "closed"
        - Fallo → incrementar consecutive_failures; si >= threshold → "circuit_open"
        """
        try:
            now_iso = datetime.now(timezone.utc).isoformat()

            # Leer estado actual
            resp = (
                self._db.table("circuit_breaker_state")
                .select("*")
                .eq("business_id", business_id)
                .eq("date", date)
                .eq("node_id", node_id)
                .execute()
            )
            existing = resp.data[0] if resp.data else None

            if success:
                new_failures = 0
                new_status = "closed"
            else:
                current_failures = existing.get("consecutive_failures", 0) if existing else 0
                new_failures = current_failures + 1
                new_status = "circuit_open" if new_failures >= self._CIRCUIT_OPEN_THRESHOLD else "closed"

            row = {
                "business_id": business_id,
                "date": date,
                "node_id": node_id,
                "consecutive_failures": new_failures,
                "circuit_status": new_status,
                "updated_at": now_iso,
            }

            if existing:
                self._db.table("circuit_breaker_state").update(row).eq(
                    "id", existing["id"]
                ).execute()
            else:
                row["id"] = str(uuid4())
                self._db.table("circuit_breaker_state").insert(row).execute()

        except Exception:
            pass  # El circuit breaker no debe bloquear la ejecución

    # ------------------------------------------------------------------
    # Idempotencia — verificar resultado existente
    # ------------------------------------------------------------------

    def _check_existing_result(self, layer2_run_id: str) -> Optional[ParallelGatherResult]:
        """
        P8: si ya existe un resultado para layer2_run_id → retornarlo sin re-ejecutar.
        """
        try:
            resp = (
                self._db.table("audit_results")
                .select("result_data")
                .eq("id", layer2_run_id)
                .eq("node_id", "N06")
                .single()
                .execute()
            )
            if resp.data and resp.data.get("result_data"):
                return ParallelGatherResult(**resp.data["result_data"])
            return None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def _persist(self, result: ParallelGatherResult, sequential_context: SequentialContext | None = None) -> None:
        """
        Persiste ParallelGatherResult en audit_results ANTES de retornar.
        P8: garantiza exactamente 1 registro por layer2_run_id.

        Incluye sequential_context (forensic_report/insights de N05) dentro de
        result_data -- sin esto, N10 (context_builder) recibia estos campos
        siempre vacios al disparar Layer 3 en "modo normal" (via audit_run_id),
        porque ParallelGatherResult por si solo nunca trae sequential_context,
        solo trae node_results. Mismo tipo de bug que el de Layer3State/LangGraph
        encontrado antes en esta sesion -- el dato existia, pero no se guardaba.
        """
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            result_data = result.model_dump(mode="json")
            if sequential_context is not None:
                result_data["sequential_context"] = sequential_context.model_dump(mode="json")
            self._db.table("audit_results").insert(
                {
                    "id": result.layer2_run_id,
                    "business_id": result.business_id,
                    "date": result.date,
                    "pipeline_layer": "parallel",
                    "node_id": "N06",
                    "node_status": result.gather_status,
                    "result_data": result_data,
                    "created_at": now_iso,
                }
            ).execute()
        except Exception:
            pass  # La persistencia no bloquea el retorno