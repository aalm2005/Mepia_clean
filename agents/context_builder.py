"""
N10 — Context Builder (Constructor de Contexto Determinista)
Python puro — sin LLM. Transforma ParallelGatherResult en EnrichedAuditPayload.
Spec: .kiro/specs/mepia/n10_context_builder.md
"""
from __future__ import annotations

import time
from datetime import datetime, date as date_type, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel

from agents.layer3_state import Layer3State


# ---------------------------------------------------------------------------
# Modelos de output de N10
# ---------------------------------------------------------------------------

class ShortPeriodMetrics(BaseModel):
    periodo: str           # date ISO
    ingresos: Decimal
    gastos_variable: Decimal
    gastos_fijos: Decimal
    num_transacciones: int


class MediumPeriodMetrics(BaseModel):
    periodo: str           # inicio de semana ISO
    ingresos: Decimal
    egresos: Decimal
    ingreso_promedio_semanal: Decimal


class LongPeriodMetrics(BaseModel):
    periodo: str           # inicio de mes ISO
    capex_mes: Decimal
    ingresos_mes: Decimal
    egresos_mes: Decimal


class TimeSeriesRollup(BaseModel):
    temporalidad: str
    date_start: str
    date_end: str
    granularidad: str      # "dia" | "semana" | "mes"
    periodos: list         # list[Short|Medium|LongPeriodMetrics]


class ParallelNodeSummary(BaseModel):
    n09_available: bool
    n09_result: Optional[dict] = None
    n07_status: str
    n08_status: str
    all_warnings: list[str]


class BrandIdentityBlock(BaseModel):
    retrieved: bool
    content: str
    fallback_used: bool


class EnrichedAuditPayload(BaseModel):
    layer3_run_id: str
    layer2_run_id: str
    sequential_run_id: str
    business_id: str
    date: str
    archetype: str
    temporalidad: str
    forensic_report: dict
    audit_insights: list
    time_series: TimeSeriesRollup
    parallel_summary: ParallelNodeSummary
    brand_identity: BrandIdentityBlock
    historical_context: str
    built_at: str
    build_duration_ms: int
    source_s3_result_id: Optional[str] = None


# Máximo de tokens para historical_context (spec: n10_context_builder.md)
MAX_HISTORICAL_TOKENS = 1500

# Identidad genérica cuando no hay chunk de onboarding
_FALLBACK_BRAND_IDENTITY = (
    "Negocio de hospitalidad. Sin restricciones de marca configuradas. "
    "Aplicar criterios generales de operación de restaurante."
)


# ---------------------------------------------------------------------------
# Nodo principal del grafo LangGraph
# ---------------------------------------------------------------------------

def n10_context_builder_node(state: Layer3State) -> dict:
    """
    N10 — Context Builder.
    Construye EnrichedAuditPayload desde el estado del grafo.
    Persiste en audit_results antes de retornar.
    Spec: n10_context_builder.md
    """
    t0 = time.monotonic()

    # Importar DB desde el estado (inyectado por el endpoint)
    db = state.get("_db")  # cliente Supabase inyectado por el endpoint
    memory_service = state.get("_memory_service")

    business_id = state["business_id"]
    date_str = state["date"]
    archetype = state["archetype"]
    layer2_run_id = state["layer2_run_id"]
    sequential_run_id = state["sequential_run_id"]
    layer3_run_id = state.get("layer3_run_id") or str(uuid4())
    source_s3_result_id = state.get("source_s3_result_id")

    # Extraer datos del parallel_gather_result almacenado en el estado
    pgr = state.get("_parallel_gather_result") or {}
    temporalidad = pgr.get("temporalidad", "short")

    # Extraer contexto secuencial
    seq_ctx = pgr.get("sequential_context") or {}
    forensic_report = seq_ctx.get("forensic_report") or {}
    audit_insights = seq_ctx.get("insights") or []
    context_tags = seq_ctx.get("context_tags") or {}

    # Extraer resultado de N09
    node_results = pgr.get("node_results") or []
    n09_node = next(
        (r for r in node_results if r.get("node_id") == "N09" and r.get("status") == "success"),
        None,
    )
    n07_node = next((r for r in node_results if r.get("node_id") == "N07"), None)
    n08_node = next((r for r in node_results if r.get("node_id") == "N08"), None)

    # Determinar status de N07/N08 (skipped_v1 en esta versión)
    def _node_status(node: Optional[dict]) -> str:
        if node is None:
            return "not_implemented_v1"
        detail = node.get("error_detail", "")
        if detail == "not_implemented_v1":
            return "not_implemented_v1"
        return node.get("status", "error")

    n07_status = _node_status(n07_node)
    n08_status = _node_status(n08_node)

    # Warnings de nodos success (P4: N07/N08 con not_implemented_v1 → sin warning)
    all_warnings: list[str] = []
    for r in node_results:
        if r.get("status") == "success" and r.get("error_detail") != "not_implemented_v1":
            all_warnings.extend(r.get("warnings") or [])

    parallel_summary = ParallelNodeSummary(
        n09_available=n09_node is not None,
        n09_result=n09_node.get("result") if n09_node else None,
        n07_status=n07_status,
        n08_status=n08_status,
        all_warnings=all_warnings,
    )

    # --- SQL Rollups según temporalidad ---
    audit_date = date_type.fromisoformat(date_str)
    time_series = _build_time_series(db, business_id, audit_date, temporalidad)

    # --- Brand Identity (SQL directo — NO semántico) ---
    brand_identity = _get_brand_identity(db, business_id)

    # --- Historial RAG (MemoryService, máx 1500 tokens) ---
    historical_context = _get_historical_context(memory_service, business_id, archetype)

    build_duration_ms = int((time.monotonic() - t0) * 1000)
    built_at = datetime.now(timezone.utc).isoformat()

    payload = EnrichedAuditPayload(
        layer3_run_id=layer3_run_id,
        layer2_run_id=layer2_run_id,
        sequential_run_id=sequential_run_id,
        business_id=business_id,
        date=date_str,
        archetype=archetype,
        temporalidad=temporalidad,
        forensic_report=forensic_report,
        audit_insights=audit_insights,
        time_series=time_series,
        parallel_summary=parallel_summary,
        brand_identity=brand_identity,
        historical_context=historical_context,
        built_at=built_at,
        build_duration_ms=build_duration_ms,
        source_s3_result_id=source_s3_result_id,
    )

    # Persistir en audit_results antes de retornar (P10)
    _persist_n10(db, payload, layer3_run_id)

    # Actualizar layer3_run_id en el estado si fue generado aquí
    return {
        "layer3_run_id": layer3_run_id,
        "enriched_payload": payload.model_dump(mode="json"),
    }


# ---------------------------------------------------------------------------
# SQL Rollups
# ---------------------------------------------------------------------------

def _build_time_series(
    db: Any,
    business_id: str,
    audit_date: date_type,
    temporalidad: str,
) -> TimeSeriesRollup:
    """Ejecuta el SQL rollup según temporalidad. Retorna TimeSeriesRollup."""
    ranges = {
        "short": 30,
        "medium": 180,
        "long": 365,
    }
    granularidades = {
        "short": "dia",
        "medium": "semana",
        "long": "mes",
    }

    days_back = ranges.get(temporalidad, 30)
    date_start = audit_date - timedelta(days=days_back)
    granularidad = granularidades.get(temporalidad, "dia")

    periodos: list = []

    if db is None:
        return TimeSeriesRollup(
            temporalidad=temporalidad,
            date_start=date_start.isoformat(),
            date_end=audit_date.isoformat(),
            granularidad=granularidad,
            periodos=[],
        )

    try:
        if temporalidad == "short":
            periodos = _rollup_short(db, business_id, date_start, audit_date)
        elif temporalidad == "medium":
            periodos = _rollup_medium(db, business_id, date_start, audit_date)
        else:
            periodos = _rollup_long(db, business_id, date_start, audit_date)
    except Exception:
        periodos = []

    return TimeSeriesRollup(
        temporalidad=temporalidad,
        date_start=date_start.isoformat(),
        date_end=audit_date.isoformat(),
        granularidad=granularidad,
        periodos=[p.model_dump(mode="json") for p in periodos],
    )


def _rollup_short(db: Any, business_id: str, date_start: date_type, date_end: date_type) -> list:
    """GROUP BY transaction_date — últimos 30 días."""
    resp = (
        db.table("transactions")
        .select("transaction_date, amount, type, expense_behavior")
        .eq("business_id", business_id)
        .eq("needs_human_review", False)
        .gte("transaction_date", date_start.isoformat())
        .lte("transaction_date", date_end.isoformat())
        .execute()
    )
    rows = resp.data or []

    # Agrupar por día en Python (Supabase no soporta GROUP BY nativo en el cliente)
    from collections import defaultdict
    by_day: dict = defaultdict(lambda: {"ingresos": Decimal("0"), "gastos_variable": Decimal("0"), "gastos_fijos": Decimal("0"), "num": 0})

    for r in rows:
        d = r["transaction_date"]
        amt = Decimal(str(r.get("amount") or 0))
        by_day[d]["num"] += 1
        if r.get("type") == "ingreso":
            by_day[d]["ingresos"] += amt
        elif r.get("expense_behavior") == "VARIABLE":
            by_day[d]["gastos_variable"] += amt
        elif r.get("expense_behavior") == "FIXED":
            by_day[d]["gastos_fijos"] += amt

    return [
        ShortPeriodMetrics(
            periodo=d,
            ingresos=v["ingresos"],
            gastos_variable=v["gastos_variable"],
            gastos_fijos=v["gastos_fijos"],
            num_transacciones=v["num"],
        )
        for d, v in sorted(by_day.items(), reverse=True)
    ]


def _rollup_medium(db: Any, business_id: str, date_start: date_type, date_end: date_type) -> list:
    """GROUP BY semana — últimos 6 meses."""
    resp = (
        db.table("transactions")
        .select("transaction_date, amount, type")
        .eq("business_id", business_id)
        .eq("needs_human_review", False)
        .gte("transaction_date", date_start.isoformat())
        .lte("transaction_date", date_end.isoformat())
        .execute()
    )
    rows = resp.data or []

    from collections import defaultdict
    by_week: dict = defaultdict(lambda: {"ingresos": Decimal("0"), "egresos": Decimal("0"), "n_ingresos": 0})

    for r in rows:
        d = date_type.fromisoformat(r["transaction_date"])
        # Inicio de semana (lunes)
        week_start = (d - timedelta(days=d.weekday())).isoformat()
        amt = Decimal(str(r.get("amount") or 0))
        if r.get("type") == "ingreso":
            by_week[week_start]["ingresos"] += amt
            by_week[week_start]["n_ingresos"] += 1
        else:
            by_week[week_start]["egresos"] += amt

    return [
        MediumPeriodMetrics(
            periodo=w,
            ingresos=v["ingresos"],
            egresos=v["egresos"],
            ingreso_promedio_semanal=(
                v["ingresos"] / Decimal(str(v["n_ingresos"])) if v["n_ingresos"] > 0 else Decimal("0")
            ),
        )
        for w, v in sorted(by_week.items(), reverse=True)
    ]


def _rollup_long(db: Any, business_id: str, date_start: date_type, date_end: date_type) -> list:
    """GROUP BY mes — último año."""
    resp = (
        db.table("transactions")
        .select("transaction_date, amount, type, expense_behavior")
        .eq("business_id", business_id)
        .eq("needs_human_review", False)
        .gte("transaction_date", date_start.isoformat())
        .lte("transaction_date", date_end.isoformat())
        .execute()
    )
    rows = resp.data or []

    from collections import defaultdict
    by_month: dict = defaultdict(lambda: {"capex": Decimal("0"), "ingresos": Decimal("0"), "egresos": Decimal("0")})

    for r in rows:
        d = date_type.fromisoformat(r["transaction_date"])
        month_start = d.replace(day=1).isoformat()
        amt = Decimal(str(r.get("amount") or 0))
        if r.get("type") == "ingreso":
            by_month[month_start]["ingresos"] += amt
        elif r.get("expense_behavior") == "CAPEX":
            by_month[month_start]["capex"] += amt
            by_month[month_start]["egresos"] += amt
        else:
            by_month[month_start]["egresos"] += amt

    return [
        LongPeriodMetrics(
            periodo=m,
            capex_mes=v["capex"],
            ingresos_mes=v["ingresos"],
            egresos_mes=v["egresos"],
        )
        for m, v in sorted(by_month.items(), reverse=True)
    ]


# ---------------------------------------------------------------------------
# Brand Identity (SQL directo — P11: nunca semántico)
# ---------------------------------------------------------------------------

def _get_brand_identity(db: Any, business_id: str) -> BrandIdentityBlock:
    """Recupera identidad de marca por SQL directo a mepia_memory."""
    if db is None:
        return BrandIdentityBlock(retrieved=False, content=_FALLBACK_BRAND_IDENTITY, fallback_used=True)

    try:
        resp = (
            db.table("mepia_memory")
            .select("content")
            .eq("business_id", business_id)
            .execute()
        )
        # Filtrar por node_origin="onboarding" en Python (JSONB filter)
        onboarding_rows = [
            r for r in (resp.data or [])
            if (r.get("metadata") or {}).get("node_origin") == "onboarding"
        ]

        if onboarding_rows:
            # Tomar el más reciente (último en la lista)
            content = onboarding_rows[-1]["content"]
            return BrandIdentityBlock(retrieved=True, content=content, fallback_used=False)

        return BrandIdentityBlock(retrieved=False, content=_FALLBACK_BRAND_IDENTITY, fallback_used=True)

    except Exception:
        return BrandIdentityBlock(retrieved=False, content=_FALLBACK_BRAND_IDENTITY, fallback_used=True)


# ---------------------------------------------------------------------------
# Historial RAG (MemoryService — máx 1500 tokens)
# ---------------------------------------------------------------------------

def _get_historical_context(
    memory_service: Any,
    business_id: str,
    archetype: str,
) -> str:
    """Recupera historial RAG y trunca a MAX_HISTORICAL_TOKENS."""
    if memory_service is None:
        return ""

    try:
        import asyncio
        query = f"auditoria financiera {archetype} anomalias gastos rentabilidad"
        context = asyncio.get_event_loop().run_until_complete(
            memory_service.get_context(query=query, business_id=business_id, limit=3)
        )
        return _truncate_to_tokens(context, MAX_HISTORICAL_TOKENS)
    except Exception:
        return ""


def _truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Trunca texto al límite de tokens usando tiktoken (fallback: caracteres)."""
    if not text:
        return ""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return enc.decode(tokens[:max_tokens])
    except ImportError:
        # Fallback: ~4 chars por token
        max_chars = max_tokens * 4
        return text[:max_chars] if len(text) > max_chars else text


# ---------------------------------------------------------------------------
# Persistencia
# ---------------------------------------------------------------------------

def _persist_n10(db: Any, payload: EnrichedAuditPayload, layer3_run_id: str) -> None:
    """Persiste EnrichedAuditPayload en audit_results con node_id='N10'."""
    if db is None:
        return
    try:
        db.table("audit_results").insert(
            {
                "id": layer3_run_id,
                "source_s3_result_id": payload.source_s3_result_id,
                "business_id": payload.business_id,
                "date": payload.date,
                "pipeline_layer": "loop",
                "node_id": "N10",
                "node_status": "success",
                "result_data": payload.model_dump(mode="json"),
                "created_at": payload.built_at,
            }
        ).execute()
    except Exception:
        pass
