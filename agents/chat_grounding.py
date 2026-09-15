"""
MEPIA - construcción determinista de evidencia para el chatbot.

Este módulo no llama a un LLM. Su única responsabilidad es recuperar y
normalizar los datos verificables que un chat podrá usar más adelante.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class ChatEvidenceReference(BaseModel):
    """Referencia auditable a una fila de ``audit_results``."""

    audit_result_id: str = Field(min_length=1)
    node_id: str = Field(min_length=1)
    date: str = Field(min_length=1)
    created_at: Optional[str] = None


class ChatGroundingPacket(BaseModel):
    """Datos permitidos para fundamentar una futura respuesta del chat."""

    business_id: str
    requested_date: Optional[str] = None
    resolved_date: Optional[str] = None
    metrics: list[dict] = Field(default_factory=list)
    final_report: Optional[dict] = None
    evidence: list[ChatEvidenceReference] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    built_at: str

    @field_validator("requested_date")
    @classmethod
    def validate_requested_date(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("requested_date debe usar el formato YYYY-MM-DD") from exc
        return value


_FINAL_REPORT_FIELDS = (
    "layer3_run_id",
    "executive_summary",
    "operational_narrative_md",
    "pragmatic_actions",
    "draft_status",
    "quality_warnings",
    "model_used",
    "finalized_at",
)

_METRIC_FIELDS = ("metric", "value", "unit", "status", "context")

# PostgREST aplica este filtro antes de ordenar y limitar la consulta. ``NULL``
# y ``completed`` se conservan por compatibilidad con filas históricas.
_VALID_NODE_STATUS_FILTER = (
    "node_status.is.null,node_status.in.(success,completed)"
)


class ChatGroundingService:
    """
    Recupera el último resultado S3 y su reporte N14 asociado por fecha.

    ``business_id`` se aplica en cada consulta y se vuelve a comprobar en la
    respuesta. Esta defensa en profundidad evita mezclar datos entre negocios.
    """

    def __init__(self, db: Any) -> None:
        self._db = db

    def build_packet(
        self,
        business_id: str,
        requested_date: Optional[str] = None,
    ) -> ChatGroundingPacket:
        if not business_id or not business_id.strip():
            raise ValueError("business_id no puede estar vacío")
        if requested_date is not None:
            try:
                datetime.strptime(requested_date, "%Y-%m-%d")
            except ValueError as exc:
                raise ValueError("requested_date debe usar el formato YYYY-MM-DD") from exc

        s3_row = self._latest_row(business_id, "S3", requested_date)
        resolved_date = requested_date or self._row_date(s3_row)

        n14_row = self._latest_row(business_id, "N14", resolved_date)
        if resolved_date is None:
            resolved_date = self._row_date(n14_row)

        metrics = self._extract_metrics(s3_row)
        final_report = self._extract_final_report(n14_row)
        evidence: list[ChatEvidenceReference] = []

        for row in (s3_row, n14_row):
            if row is None:
                continue
            evidence.append(
                ChatEvidenceReference(
                    audit_result_id=str(row.get("id", "")),
                    node_id=str(row.get("node_id", "")),
                    date=str(row.get("date", "")),
                    created_at=row.get("created_at"),
                )
            )

        missing_data: list[str] = []
        if not metrics:
            missing_data.append("metrics_not_found")
        if final_report is None:
            missing_data.append("final_report_not_found")
        if not evidence:
            missing_data.append("no_audit_results")

        return ChatGroundingPacket(
            business_id=business_id,
            requested_date=requested_date,
            resolved_date=resolved_date,
            metrics=metrics,
            final_report=final_report,
            evidence=evidence,
            missing_data=missing_data,
            built_at=datetime.now(timezone.utc).isoformat(),
        )

    def _latest_row(
        self,
        business_id: str,
        node_id: str,
        requested_date: Optional[str],
    ) -> Optional[dict]:
        query = (
            self._db.table("audit_results")
            .select("id,business_id,date,node_id,node_status,result_data,created_at")
            .eq("business_id", business_id)
            .eq("node_id", node_id)
        )
        if requested_date:
            query = query.eq("date", requested_date)

        response = (
            query.or_(_VALID_NODE_STATUS_FILTER)
            .order("date", desc=True)
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
        rows = response.data or []
        for row in rows:
            if str(row.get("business_id")) != business_id:
                continue
            # ``completed`` se acepta solo como compatibilidad con datos
            # generados antes de normalizar el contrato de node_status.
            if row.get("node_status") not in (None, "success", "completed"):
                continue
            return row
        return None

    @staticmethod
    def _row_date(row: Optional[dict]) -> Optional[str]:
        if not row or not row.get("date"):
            return None
        return str(row["date"])

    @staticmethod
    def _extract_metrics(row: Optional[dict]) -> list[dict]:
        if row is None:
            return []
        result_data = row.get("result_data")
        if not isinstance(result_data, dict):
            return []
        raw_metrics = result_data.get("results")
        if not isinstance(raw_metrics, list):
            return []
        return [
            {key: item.get(key) for key in _METRIC_FIELDS}
            for item in raw_metrics
            if isinstance(item, dict) and item.get("metric")
        ]

    @staticmethod
    def _extract_final_report(row: Optional[dict]) -> Optional[dict]:
        if row is None:
            return None
        result_data = row.get("result_data") or {}
        if not isinstance(result_data, dict) or not result_data:
            return None
        final_report = {
            key: result_data.get(key)
            for key in _FINAL_REPORT_FIELDS
            if key in result_data
        }
        return final_report or None
