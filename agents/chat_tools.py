"""Herramientas deterministas de consulta para el chatbot de MEPIA.

Este modulo no consulta la base de datos y no llama a ningun LLM. Recibe un
``ChatGroundingPacket`` ya construido y expone solo datos permitidos con su
evidencia auditable. Las consultas sin evidencia se rechazan en lugar de
devolver cifras o reportes no verificables.
"""
from __future__ import annotations

from copy import deepcopy
import re
import unicodedata
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from agents.chat_grounding import (
    CHAT_FINAL_REPORT_FIELDS,
    CHAT_METRIC_FIELDS,
    ChatEvidenceReference,
    ChatGroundingPacket,
)
from agents.chat_metric_catalog import (
    CHAT_SCOPE_POLICY,
    CONCEPT_CATALOG,
    METRIC_CATALOG,
    MetricConceptDefinition,
    MetricDefinition,
)


ChatToolName = Literal[
    "list_metrics",
    "get_metric",
    "get_final_report",
    "list_metric_catalog",
    "describe_metric",
    "lookup_glossary",
    "refuse_calculation",
]
ChatToolStatus = Literal[
    "ok", "not_found", "missing_data", "invalid_request", "not_allowed"
]

# Alias conservado para consumidores del primer contrato del Paso 2.
ChatGlossaryEntry = MetricConceptDefinition


class ChatToolResult(BaseModel):
    """Salida comun y serializable de cualquier herramienta determinista."""

    tool: ChatToolName
    status: ChatToolStatus
    business_id: str
    resolved_date: Optional[str] = None
    source_s3_result_id: Optional[str] = None
    data: dict[str, Any] = Field(default_factory=dict)
    evidence: list[ChatEvidenceReference] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    knowledge_scope: Literal["engine_metric_domain"] = "engine_metric_domain"
    calculation_allowed: Literal[False] = False


_METRIC_STATUSES = frozenset(
    {"ok", "warning", "critical", "incomplete_data", "unit_mismatch"}
)

_REPORT_SECTION_ALIASES = {
    "resumen": "executive_summary",
    "resumen_ejecutivo": "executive_summary",
    "executive_summary": "executive_summary",
    "narrativa": "operational_narrative_md",
    "narrativa_operativa": "operational_narrative_md",
    "operational_narrative": "operational_narrative_md",
    "operational_narrative_md": "operational_narrative_md",
    "acciones": "pragmatic_actions",
    "acciones_pragmaticas": "pragmatic_actions",
    "pragmatic_actions": "pragmatic_actions",
    "estado": "draft_status",
    "status": "draft_status",
    "draft_status": "draft_status",
    "advertencias": "quality_warnings",
    "quality_warnings": "quality_warnings",
    "modelo": "model_used",
    "model_used": "model_used",
    "fecha_finalizacion": "finalized_at",
    "finalized_at": "finalized_at",
    "linaje": "source_s3_result_id",
    "source_s3_result_id": "source_s3_result_id",
    "ejecucion_layer3": "layer3_run_id",
    "layer3_run_id": "layer3_run_id",
}

def _normalize(value: str) -> str:
    """Normaliza un selector sin aplicar coincidencias aproximadas."""

    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    without_accents = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", "_", without_accents).strip("_")


def _build_glossary_index() -> dict[str, MetricConceptDefinition]:
    index: dict[str, MetricConceptDefinition] = {}
    for entry in CONCEPT_CATALOG:
        for selector in (entry.term, *entry.aliases):
            key = _normalize(selector)
            existing = index.get(key)
            if existing is not None and existing.term != entry.term:
                raise RuntimeError(f"Alias de glosario duplicado: {selector}")
            index[key] = entry
    return index


_GLOSSARY_INDEX = _build_glossary_index()


def _build_metric_index() -> dict[str, tuple[MetricDefinition, ...]]:
    grouped: dict[str, list[MetricDefinition]] = {}
    for definition in METRIC_CATALOG:
        selectors = (
            definition.metric_id,
            definition.display_name,
            *definition.aliases,
            *definition.result_metric_names,
        )
        for selector in selectors:
            bucket = grouped.setdefault(_normalize(selector), [])
            if definition not in bucket:
                bucket.append(definition)
    return {key: tuple(value) for key, value in grouped.items()}


_METRIC_INDEX = _build_metric_index()
_METRIC_BY_ID = {definition.metric_id: definition for definition in METRIC_CATALOG}


def _resolve_metric_definitions(selector: str) -> tuple[MetricDefinition, ...]:
    direct = _METRIC_INDEX.get(selector)
    if direct is not None:
        return direct
    concept = _GLOSSARY_INDEX.get(selector)
    if concept is None:
        return ()
    return tuple(
        _METRIC_BY_ID[metric_id]
        for metric_id in concept.related_metrics
        if metric_id in _METRIC_BY_ID
    )


def _matches_definition(metric_name: str, definition: MetricDefinition) -> bool:
    selector = _normalize(metric_name)
    if selector in {_normalize(name) for name in definition.result_metric_names}:
        return True
    return any(
        selector.startswith(_normalize(prefix))
        for prefix in definition.result_metric_prefixes
    )


class ChatQueryTools:
    """Consulta segura y de solo lectura sobre un paquete de grounding."""

    def __init__(self, packet: ChatGroundingPacket) -> None:
        self._packet = packet.model_copy(deep=True)

    def list_metrics(self, status: Optional[str] = None) -> ChatToolResult:
        """Lista metricas verificables, opcionalmente por status de CalcResult."""

        normalized_status = None
        if status is not None:
            normalized_status = status.strip().casefold()
            if normalized_status not in _METRIC_STATUSES:
                return self._result(
                    tool="list_metrics",
                    status="invalid_request",
                    missing_data=["invalid_metric_status"],
                )

        evidence = self._evidence_for("S3")
        metrics = self._safe_metrics()
        if not evidence:
            return self._result(
                tool="list_metrics",
                status="missing_data",
                missing_data=["metric_evidence_not_found"],
            )
        if not metrics:
            return self._result(
                tool="list_metrics",
                status="missing_data",
                evidence=evidence,
                missing_data=["metrics_not_found"],
            )

        if normalized_status is not None:
            metrics = [
                metric
                for metric in metrics
                if str(metric.get("status", "")).casefold() == normalized_status
            ]
        if not metrics:
            return self._result(
                tool="list_metrics",
                status="not_found",
                data={"metrics": [], "count": 0, "status_filter": normalized_status},
                evidence=evidence,
                missing_data=[f"metrics_with_status_not_found:{normalized_status}"],
            )

        return self._result(
            tool="list_metrics",
            status="ok",
            data={
                "metrics": metrics,
                "count": len(metrics),
                "status_filter": normalized_status,
            },
            evidence=evidence,
        )

    def get_metric(self, metric_name: str) -> ChatToolResult:
        """Busca una salida existente por identificador, alias o concepto exacto."""

        selector = _normalize(metric_name)
        if not selector:
            return self._result(
                tool="get_metric",
                status="invalid_request",
                missing_data=["metric_name_required"],
            )

        evidence = self._evidence_for("S3")
        metrics = self._safe_metrics()
        if not evidence:
            return self._result(
                tool="get_metric",
                status="missing_data",
                missing_data=["metric_evidence_not_found"],
            )
        if not metrics:
            return self._result(
                tool="get_metric",
                status="missing_data",
                evidence=evidence,
                missing_data=["metrics_not_found"],
            )

        definitions = _resolve_metric_definitions(selector)
        matches = [
            metric
            for metric in metrics
            if _normalize(str(metric.get("metric", ""))) == selector
            or any(
                _matches_definition(str(metric.get("metric", "")), definition)
                for definition in definitions
            )
        ]
        if not matches:
            return self._result(
                tool="get_metric",
                status="not_found",
                data={"requested_metric": metric_name, "metrics": [], "count": 0},
                evidence=evidence,
                missing_data=[f"metric_not_found:{selector}"],
            )

        return self._result(
            tool="get_metric",
            status="ok",
            data={
                "requested_metric": metric_name,
                "metrics": matches,
                "count": len(matches),
            },
            evidence=evidence,
        )

    def list_metric_catalog(
        self, availability: Optional[str] = None
    ) -> ChatToolResult:
        """Lista el dominio explicable sin consultar ni calcular datos del negocio."""

        normalized_availability = None
        if availability is not None:
            normalized_availability = _normalize(availability)
            if normalized_availability not in {"pipeline", "engine_support"}:
                return self._result(
                    tool="list_metric_catalog",
                    status="invalid_request",
                    missing_data=["invalid_metric_availability"],
                )
        definitions = [
            definition
            for definition in METRIC_CATALOG
            if normalized_availability is None
            or definition.availability == normalized_availability
        ]
        entries = [
            {
                "metric_id": definition.metric_id,
                "display_name": definition.display_name,
                "availability": definition.availability,
                "units": deepcopy(definition.units),
            }
            for definition in definitions
        ]
        return self._result(
            tool="list_metric_catalog",
            status="ok",
            data={
                "entries": entries,
                "count": len(entries),
                "availability_filter": normalized_availability,
                "source": "mepia_engine_metric_catalog_v2",
            },
        )

    def describe_metric(self, metric_name: str) -> ChatToolResult:
        """Explica una metrica o un concepto relacionado sin ejecutar su formula."""

        selector = _normalize(metric_name)
        if not selector:
            return self._result(
                tool="describe_metric",
                status="invalid_request",
                missing_data=["metric_name_required"],
            )
        definitions = _resolve_metric_definitions(selector)
        if not definitions:
            return self._result(
                tool="describe_metric",
                status="not_found",
                data={
                    "requested_metric": metric_name,
                    "source": "mepia_engine_metric_catalog_v2",
                },
                missing_data=[f"metric_definition_not_found:{selector}"],
            )
        return self._result(
            tool="describe_metric",
            status="ok",
            data={
                "requested_metric": metric_name,
                "definitions": [item.model_dump() for item in definitions],
                "count": len(definitions),
                "formula_is_explanatory_only": True,
                "source": "mepia_engine_metric_catalog_v2",
            },
        )

    def get_final_report(self, section: Optional[str] = None) -> ChatToolResult:
        """Devuelve el reporte N14 completo o una seccion autorizada."""

        canonical_section = None
        if section is not None:
            selector = _normalize(section)
            if not selector:
                return self._result(
                    tool="get_final_report",
                    status="invalid_request",
                    missing_data=["report_section_required"],
                )
            canonical_section = _REPORT_SECTION_ALIASES.get(selector)
            if canonical_section not in CHAT_FINAL_REPORT_FIELDS:
                return self._result(
                    tool="get_final_report",
                    status="invalid_request",
                    missing_data=[f"invalid_report_section:{selector}"],
                )

        evidence = self._evidence_for("N14")
        report = self._safe_report()
        if not evidence:
            return self._result(
                tool="get_final_report",
                status="missing_data",
                missing_data=["report_evidence_not_found"],
            )
        if not report:
            return self._result(
                tool="get_final_report",
                status="missing_data",
                evidence=evidence,
                missing_data=["final_report_not_found"],
            )

        if canonical_section is None:
            data = {"report": report}
        elif canonical_section not in report or report[canonical_section] is None:
            return self._result(
                tool="get_final_report",
                status="not_found",
                data={"section": canonical_section},
                evidence=evidence,
                missing_data=[f"report_section_not_found:{canonical_section}"],
            )
        else:
            data = {
                "section": canonical_section,
                "value": deepcopy(report[canonical_section]),
            }

        return self._result(
            tool="get_final_report",
            status="ok",
            data=data,
            evidence=evidence,
        )

    def lookup_glossary(self, term: Optional[str] = None) -> ChatToolResult:
        """Consulta una definicion exacta; sin termino devuelve el catalogo."""

        if term is None:
            entries = [entry.model_dump() for entry in CONCEPT_CATALOG]
            return self._result(
                tool="lookup_glossary",
                status="ok",
                data={
                    "entries": entries,
                    "count": len(entries),
                    "source": "mepia_engine_concept_glossary_v2",
                },
            )

        selector = _normalize(term)
        if not selector:
            return self._result(
                tool="lookup_glossary",
                status="invalid_request",
                missing_data=["glossary_term_required"],
            )
        entry = _GLOSSARY_INDEX.get(selector)
        if entry is None:
            return self._result(
                tool="lookup_glossary",
                status="not_found",
                data={
                    "requested_term": term,
                    "source": "mepia_engine_concept_glossary_v2",
                },
                missing_data=[f"glossary_term_not_found:{selector}"],
            )
        return self._result(
            tool="lookup_glossary",
            status="ok",
            data={
                "requested_term": term,
                "entry": entry.model_dump(),
                "source": "mepia_engine_concept_glossary_v2",
            },
        )

    def refuse_calculation(self, request: Optional[str] = None) -> ChatToolResult:
        """Produce el rechazo determinista para cualquier solicitud de calculo."""

        data = {
            "reason": "calculation_not_allowed",
            "message": (
                "El chatbot de MEPIA no calcula, recalcula, agrega, proyecta ni "
                "simula. Solo puede explicar resultados ya emitidos por el motor "
                "determinista y conceptos ligados a sus metricas."
            ),
            "allowed_operations": deepcopy(CHAT_SCOPE_POLICY.allowed_operations),
            "prohibited_operations": deepcopy(
                CHAT_SCOPE_POLICY.prohibited_operations
            ),
        }
        if request is not None and request.strip():
            data["request"] = request.strip()
        return self._result(
            tool="refuse_calculation",
            status="not_allowed",
            data=data,
            missing_data=["calculation_not_allowed"],
        )

    def _safe_metrics(self) -> list[dict[str, Any]]:
        return [
            {
                key: deepcopy(item.get(key))
                for key in CHAT_METRIC_FIELDS
            }
            for item in self._packet.metrics
            if isinstance(item, dict) and item.get("metric")
        ]

    def _safe_report(self) -> dict[str, Any]:
        report = self._packet.final_report
        if not isinstance(report, dict):
            return {}
        safe_report = {
            key: deepcopy(report[key])
            for key in CHAT_FINAL_REPORT_FIELDS
            if key in report
        }
        if "source_s3_result_id" in safe_report:
            safe_report["source_s3_result_id"] = self._packet.source_s3_result_id
        return safe_report

    def _evidence_for(self, node_id: str) -> list[ChatEvidenceReference]:
        source_id = self._packet.source_s3_result_id
        if source_id is None:
            return []

        evidence = []
        for reference in self._packet.evidence:
            if reference.node_id != node_id:
                continue
            if (
                self._packet.resolved_date is not None
                and reference.date != self._packet.resolved_date
            ):
                continue
            if node_id == "S3" and reference.audit_result_id != source_id:
                continue
            if node_id == "N14" and reference.source_s3_result_id != source_id:
                continue
            evidence.append(reference.model_copy(deep=True))
        return evidence

    def _result(
        self,
        *,
        tool: ChatToolName,
        status: ChatToolStatus,
        data: Optional[dict[str, Any]] = None,
        evidence: Optional[list[ChatEvidenceReference]] = None,
        missing_data: Optional[list[str]] = None,
    ) -> ChatToolResult:
        return ChatToolResult(
            tool=tool,
            status=status,
            business_id=self._packet.business_id,
            resolved_date=self._packet.resolved_date,
            source_s3_result_id=self._packet.source_s3_result_id,
            data=deepcopy(data) if data is not None else {},
            evidence=evidence or [],
            missing_data=missing_data or [],
        )
