"""
N14 — Informe Final (Nodo de Persistencia y Entrega)
Python puro — sin LLM. Formatea y persiste el DraftReport aprobado.
Spec: .kiro/specs/mepia/n14_informe_final.md
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel

from agents.layer3_state import Layer3State


# ---------------------------------------------------------------------------
# Modelos de output
# ---------------------------------------------------------------------------

class FinalReport(BaseModel):
    layer3_run_id: str
    business_id: str
    date: str
    archetype: str
    temporalidad: str
    executive_summary: str
    operational_narrative_md: str      # narrativa formateada en Markdown
    pragmatic_actions: list[dict]
    draft_status: str                  # "approved" | "approved_with_warning"
    model_used: str
    intentos_critico: int
    quality_warnings: list[str]
    finalized_at: str
    layer3_duration_ms: int
    source_s3_result_id: Optional[str] = None


class FinalResponse(BaseModel):
    report_markdown: str
    status: str
    has_warnings: bool
    metadata: dict


# ---------------------------------------------------------------------------
# Nodo del grafo LangGraph
# ---------------------------------------------------------------------------

def n14_informe_final_node(state: Layer3State) -> dict:
    """
    N14 — Informe Final.
    Formatea DraftReport a Markdown y persiste FinalReport.
    Spec: n14_informe_final.md
    """
    db = state.get("_db")
    draft_report = state.get("draft_report") or {}
    draft_status = state.get("draft_status", "approved")
    layer3_run_id = state["layer3_run_id"]
    intentos = state.get("intentos_critico", 0)
    historial = list(state.get("historial_feedback") or [])

    # Calcular duración total del grafo (desde built_at de N10)
    enriched = state.get("enriched_payload") or {}
    built_at_str = enriched.get("built_at")
    layer3_duration_ms = _calc_duration(built_at_str)

    finalized_at = datetime.now(timezone.utc).isoformat()

    # Extraer campos del DraftReport
    executive_summary = draft_report.get("executive_summary", "")
    operational_narrative = draft_report.get("operational_narrative", "")
    pragmatic_actions = draft_report.get("pragmatic_actions") or []
    model_used = draft_report.get("model_used", "unknown")
    archetype = draft_report.get("archetype") or state.get("archetype", "")
    temporalidad = draft_report.get("temporalidad") or enriched.get("temporalidad", "short")

    # Formatear narrativa a Markdown (P6: N14 nunca modifica executive_summary ni actions)
    operational_narrative_md = _format_to_markdown(
        narrative=operational_narrative,
        date=state["date"],
        archetype=archetype,
        draft_status=draft_status,
    )

    # quality_warnings: historial de rechazos (P2/P3)
    quality_warnings = historial if draft_status == "approved_with_warning" else []

    final_report = FinalReport(
        layer3_run_id=layer3_run_id,
        business_id=state["business_id"],
        date=state["date"],
        archetype=archetype,
        temporalidad=temporalidad,
        executive_summary=executive_summary,
        operational_narrative_md=operational_narrative_md,
        pragmatic_actions=pragmatic_actions,
        draft_status=draft_status,
        model_used=model_used,
        intentos_critico=intentos,
        quality_warnings=quality_warnings,
        finalized_at=finalized_at,
        layer3_duration_ms=layer3_duration_ms,
        source_s3_result_id=state.get("source_s3_result_id"),
    )

    # Persistir en audit_results (P5: layer3_status="completed" solo tras persistencia exitosa)
    persist_ok = _persist_n14(db, final_report, layer3_run_id)

    # Construir FinalResponse para el frontend
    final_response = FinalResponse(
        report_markdown=operational_narrative_md,
        status=draft_status,
        has_warnings=(draft_status == "approved_with_warning"),
        metadata={
            "generated_at": finalized_at,
            "audit_trail": list(state.get("audit_results") or []),
        },
    )

    return {
        "final_response": final_response.model_dump(mode="json"),
        "draft_status": draft_status,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_to_markdown(
    narrative: str,
    date: str,
    archetype: str,
    draft_status: str,
) -> str:
    """
    Convierte operational_narrative a Markdown estructurado.
    Spec: n14_informe_final.md §Regla de formateo
    """
    md = f"## Hallazgos del período\n\n{narrative}\n\n---\n*Generado por MEPIA · {date} · Arquetipo: {archetype}*"

    if draft_status == "approved_with_warning":
        md += (
            "\n\n> ⚠️ Este reporte contiene advertencias de calidad no resueltas.\n"
            "> Revisar manualmente antes de tomar decisiones."
        )

    return md


def _calc_duration(built_at_str: Optional[str]) -> int:
    """Calcula duración total del grafo en ms desde built_at de N10."""
    if not built_at_str:
        return 0
    try:
        built_at = datetime.fromisoformat(built_at_str)
        if built_at.tzinfo is None:
            built_at = built_at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return max(0, int((now - built_at).total_seconds() * 1000))
    except Exception:
        return 0


def _persist_n14(db: Any, report: FinalReport, layer3_run_id: str) -> bool:
    """Persiste FinalReport en audit_results con node_id='N14'. Retorna True si éxito."""
    if db is None:
        return False
    try:
        db.table("audit_results").insert(
            {
                "id": str(uuid4()),
                "source_s3_result_id": report.source_s3_result_id,
                "business_id": report.business_id,
                "date": report.date,
                "pipeline_layer": "loop",
                "node_id": "N14",
                "node_status": "success",
                "result_data": report.model_dump(mode="json"),
                "created_at": report.finalized_at,
            }
        ).execute()
        return True
    except Exception:
        return False
