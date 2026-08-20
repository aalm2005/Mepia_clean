"""
N05 — CEO Orchestrator (Motor de Síntesis Estratégica)
Coordina S3 → S4 → síntesis con arquetipo CEO.
LLM: gpt-4o, temperatura 0.3.
Spec: .kiro/specs/mepia/n05_ceo_orchestrator.md
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel

from agents.calc_engine import CalcResult, run_calc_engine
from agents.forensic_cfo import AnomalyItem, ForensicReport, ForensicCFOAgent
from agents.gatekeeper import GatekeeperAgent, GatekeeperResult
from agents.parallel_orchestrator import (
    ContextTags,
    Layer2RunPayload,
    N06ParallelOrchestrator,
    SequentialContext,
)


# ---------------------------------------------------------------------------
# Tipos y modelos
# ---------------------------------------------------------------------------

Archetype = Literal["Operative Genius", "Product Purist", "Growth Hacker"]
AlertLevel = Literal["info", "warning", "critical"]
ContextWeight = Literal["reducido", "normal", "amplificado"]
PipelineStatus = Literal["completed", "partial", "escalated", "failed"]


class AuditInsight(BaseModel):
    """
    Output de N05 por cada AnomalyItem del ForensicReport.
    Generado con arquetipo CEO aplicado.
    Spec: n05_ceo_orchestrator.md §AuditInsight
    """
    anomaly_ref: str                   # anomaly_id del AnomalyItem origen
    copilot_phrase: str                # frase CEO-framed, específica y accionable
    archetype: Archetype
    alert_level: AlertLevel            # mapeado desde AnomalyItem.severity (P6)
    recommended_action: str            # acción específica con frecuencia o plazo
    context_weight: ContextWeight
    module: str                        # nombre del módulo auditado
    raw_result: str                    # quantified_impact del AnomalyItem


class EscalationInfo(BaseModel):
    triggered: bool
    reason: Optional[str] = None
    layer2_run_id: Optional[str] = None


class SequentialResults(BaseModel):
    active_metrics: list[str]
    calc_results: list[dict]           # CalcResult[] serializados
    forensic_report: dict              # ForensicReport serializado
    audit_insights: list[AuditInsight]


class OrchestratorResult(BaseModel):
    """
    Output de POST /orchestrator/run.
    Spec: n05_ceo_orchestrator.md §OrchestratorResult
    """
    run_id: str
    business_id: str
    date: str
    archetype: Archetype
    pipeline_status: PipelineStatus
    sequential_results: SequentialResults
    escalation: EscalationInfo
    dormant_metrics: list[dict]        # [{ metric, missing }]
    completed_at: str


# ---------------------------------------------------------------------------
# Diccionario de CEO Cognitive Frames por arquetipo
# Spec: n05_ceo_orchestrator.md §Diccionario de Prompt Templates
# ---------------------------------------------------------------------------

_CEO_FRAMES: dict[str, str] = {
    "Operative Genius": (
        "Eres el copiloto de un CEO con perfil OPERATIVE GENIUS: obsesionado con la eficiencia "
        "operativa, los procesos y la eliminación de desperdicios. "
        "Traduce cada anomalía en una alerta sobre cuellos de botella, fugas de capital en procesos "
        "o ineficiencias operativas. "
        "Usa lenguaje directo, técnico y orientado a procesos. "
        "Prohibido usar frases genéricas como 'debes mejorar' o 'considera revisar'. "
        "Cada frase debe mencionar el número exacto y la acción específica con frecuencia o plazo."
    ),
    "Product Purist": (
        "Eres el copiloto de un CEO con perfil PRODUCT PURIST: obsesionado con la calidad del "
        "producto y la experiencia del cliente. "
        "Traduce cada anomalía en su impacto directo sobre la calidad del producto, la consistencia "
        "del servicio o la experiencia del cliente. "
        "Usa lenguaje que conecte los números con la experiencia real del comensal. "
        "Prohibido usar frases genéricas. Cada frase debe mencionar el número exacto y cómo afecta "
        "la calidad o la experiencia."
    ),
    "Growth Hacker": (
        "Eres el copiloto de un CEO con perfil GROWTH HACKER: orientado a escala, métricas de "
        "crecimiento, recompra y expansión. "
        "Traduce cada anomalía en una oportunidad perdida de crecimiento, recompra o escala. "
        "Usa lenguaje orientado a métricas de crecimiento y retención. "
        "Prohibido usar frases genéricas. Cada frase debe mencionar el número exacto y el impacto "
        "en crecimiento o recompra."
    ),
}

# Schema para structured output del LLM
_INSIGHT_SCHEMA = {
    "type": "object",
    "properties": {
        "copilot_phrase": {"type": "string"},
        "recommended_action": {"type": "string"},
    },
    "required": ["copilot_phrase", "recommended_action"],
    "additionalProperties": False,
}


# ---------------------------------------------------------------------------
# Mapeo severity → alert_level (P6 — garantizado en código, no solo en prompt)
# ---------------------------------------------------------------------------

_SEVERITY_TO_ALERT: dict[str, AlertLevel] = {
    "high": "critical",
    "medium": "warning",
    "low": "info",
}


# ---------------------------------------------------------------------------
# N05CEOOrchestrator
# ---------------------------------------------------------------------------

class N05CEOOrchestrator:
    """
    N05 — CEO Orchestrator.
    Coordina S3 → S4 → síntesis con arquetipo y decide escalación a Layer 2.
    """

    def __init__(self, supabase_client: Any) -> None:
        self._db = supabase_client
        try:
            from openai import OpenAI
            self._llm = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        except Exception as exc:
            raise RuntimeError(f"N05CEOOrchestrator requiere OPENAI_API_KEY: {exc}")

    # ------------------------------------------------------------------
    # Punto de entrada principal
    # ------------------------------------------------------------------

    def run(
        self,
        business_id: str,
        date: str,
        archetype: Archetype,
        escalate_to_parallel: bool,
        temporalidad: str,
    ) -> OrchestratorResult:
        """
        Ejecuta el pipeline completo: S3 → S4 → síntesis N05.

        Args:
            business_id          : UUID del negocio
            date                 : YYYY-MM-DD
            archetype            : CEO archetype para síntesis
            escalate_to_parallel : si True y risk_level="high" → escalar a Layer 2
            temporalidad         : "short"|"medium"|"long" — propagado hasta N10

        Returns:
            OrchestratorResult con todos los resultados del pipeline
        """
        run_id = str(uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        # --- 1. Obtener GatekeeperResult ---
        gk_agent = GatekeeperAgent(self._db)
        gk_result = gk_agent.get_status(business_id, date)

        # Si no hay registros → evaluar
        if not gk_result.active_metrics and not gk_result.dormant_metrics and not gk_result.blocked_metrics:
            gk_result = gk_agent.evaluate(business_id, date)

        dormant_metrics = [dm.model_dump() for dm in gk_result.dormant_metrics]

        # --- 2. Ejecutar S3 Motor de Cálculo ---
        calc_run = run_calc_engine(gk_result, self._db, date, business_id)
        calc_results_dicts = [r.model_dump(mode="json") for r in calc_run.results]

        # --- 3. Ejecutar S4 Forensic CFO ---
        # daily_context reading removed (deprecated) — observed_causality always None
        daily_context_tags = None

        forensic_agent = ForensicCFOAgent()
        forensic_report = forensic_agent.run(
            calc_results=calc_results_dicts,
            business_id=business_id,
            date=date,
            daily_context_tags=daily_context_tags,
        )

        # --- 4. Recuperar contexto RAG desde MemoryService ---
        rag_context = self._get_rag_context(forensic_report, business_id)

        # --- 5. Sintetizar AuditInsight[] con arquetipo CEO ---
        audit_insights = self._synthesize_insights(
            forensic_report=forensic_report,
            archetype=archetype,
            rag_context=rag_context,
            calc_results=calc_results_dicts,
        )

        # --- 6. Determinar pipeline_status ---
        has_dormant = len(dormant_metrics) > 0
        pipeline_status: PipelineStatus = "partial" if has_dormant else "completed"

        # --- 7. Evaluar escalación a Layer 2 ---
        escalation = self._evaluate_escalation(
            forensic_report=forensic_report,
            escalate_to_parallel=escalate_to_parallel,
            run_id=run_id,
            business_id=business_id,
            date=date,
            archetype=archetype,
            temporalidad=temporalidad,
            calc_results=calc_results_dicts,
            audit_insights=audit_insights,
            active_metrics=gk_result.active_metrics,
        )

        if escalation.triggered:
            pipeline_status = "escalated"

        # --- 8. Persistir en audit_results con node_id="N05" ---
        completed_at = datetime.now(timezone.utc).isoformat()
        self._persist_result(
            run_id=run_id,
            business_id=business_id,
            date=date,
            archetype=archetype,
            forensic_report=forensic_report,
            audit_insights=audit_insights,
            pipeline_status=pipeline_status,
            escalation=escalation,
            completed_at=completed_at,
        )

        return OrchestratorResult(
            run_id=run_id,
            business_id=business_id,
            date=date,
            archetype=archetype,
            pipeline_status=pipeline_status,
            sequential_results=SequentialResults(
                active_metrics=gk_result.active_metrics,
                calc_results=calc_results_dicts,
                forensic_report=forensic_report.model_dump(mode="json"),
                audit_insights=audit_insights,
            ),
            escalation=escalation,
            dormant_metrics=dormant_metrics,
            completed_at=completed_at,
        )

    # ------------------------------------------------------------------
    # Síntesis de AuditInsight[] con arquetipo CEO
    # ------------------------------------------------------------------

    def _synthesize_insights(
        self,
        forensic_report: ForensicReport,
        archetype: Archetype,
        rag_context: str,
        calc_results: list[dict] | None = None,
    ) -> list[AuditInsight]:
        """
        Para cada AnomalyItem del ForensicReport genera un AuditInsight
        aplicando el CEO Cognitive Frame del arquetipo.

        Además, genera insights positivos (confirmaciones) para métricas
        con status "ok" que no tienen anomalías — el copiloto siempre habla.

        Correctness properties garantizadas en código:
            P6: severity "high" → alert_level "critical" (override post-LLM)
            P7: observed_causality no cambia alert_level, solo tono de frase
        """
        insights: list[AuditInsight] = []
        frame = _CEO_FRAMES[archetype]
        # observed_causality is always None (deprecated)
        observed = None

        # --- Insights para anomalías (negativos) ---
        for anomaly in forensic_report.anomalies:
            # P6: mapeo severity → alert_level garantizado en código
            alert_level: AlertLevel = _SEVERITY_TO_ALERT.get(anomaly.severity, "info")

            # Asignar context_weight según lógica RAG + severity
            context_weight = self._assign_context_weight(anomaly, rag_context)

            # Construir prompt para el LLM
            user_prompt = self._build_synthesis_prompt(
                anomaly=anomaly,
                archetype=archetype,
                frame=frame,
                observed_causality=observed,
                rag_context=rag_context,
                context_weight=context_weight,
            )

            # Llamar al LLM para generar copilot_phrase + recommended_action
            try:
                response = self._llm.chat.completions.create(
                    model="gpt-4o",
                    temperature=0.3,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "audit_insight",
                            "strict": True,
                            "schema": _INSIGHT_SCHEMA,
                        },
                    },
                    messages=[
                        {"role": "system", "content": frame},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                llm_data = json.loads(response.choices[0].message.content)
                copilot_phrase = llm_data["copilot_phrase"]
                recommended_action = llm_data["recommended_action"]
            except Exception as exc:
                # Fallback: frase genérica si el LLM falla
                copilot_phrase = (
                    f"Anomalía detectada en {anomaly.metric_origin}: "
                    f"{anomaly.quantified_impact}."
                )
                recommended_action = "Revisar datos y tomar acción correctiva."

            insights.append(
                AuditInsight(
                    anomaly_ref=anomaly.anomaly_id,
                    copilot_phrase=copilot_phrase,
                    archetype=archetype,
                    alert_level=alert_level,   # P6: nunca modificado por observed_causality
                    recommended_action=recommended_action,
                    context_weight=context_weight,
                    module=anomaly.metric_origin,
                    raw_result=anomaly.quantified_impact,
                )
            )

        # --- Insights positivos para métricas "ok" sin anomalías ---
        if calc_results:
            anomaly_metrics = {a.metric_origin for a in forensic_report.anomalies}
            ok_metrics = [
                cr for cr in calc_results
                if cr.get("status") == "ok" and cr.get("metric") not in anomaly_metrics
            ]

            for cr in ok_metrics:
                metric_name = cr.get("metric", "unknown")
                value = cr.get("value", "N/A")
                unit = cr.get("unit", "")
                context = cr.get("context", "")

                try:
                    positive_prompt = (
                        f"Métrica: {metric_name}\n"
                        f"Valor: {value} {unit}\n"
                        f"Contexto: {context}\n\n"
                        f"Esta métrica está dentro de parámetros saludables. "
                        f"Genera una frase breve de confirmación positiva para el dueño "
                        f"del restaurante (arquetipo: {archetype}). "
                        f"Incluye una sugerencia de mejora o mantenimiento. "
                        f"Responde en JSON con campos: copilot_phrase, recommended_action."
                    )
                    response = self._llm.chat.completions.create(
                        model="gpt-4o",
                        temperature=0.3,
                        response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": "audit_insight",
                                "strict": True,
                                "schema": _INSIGHT_SCHEMA,
                            },
                        },
                        messages=[
                            {"role": "system", "content": frame},
                            {"role": "user", "content": positive_prompt},
                        ],
                    )
                    llm_data = json.loads(response.choices[0].message.content)
                    copilot_phrase = llm_data["copilot_phrase"]
                    recommended_action = llm_data["recommended_action"]
                except Exception:
                    copilot_phrase = f"Tu {metric_name} está en buen estado: {value} {unit}."
                    recommended_action = "Mantener el ritmo actual."

                insights.append(
                    AuditInsight(
                        anomaly_ref=str(uuid4()),
                        copilot_phrase=copilot_phrase,
                        archetype=archetype,
                        alert_level="info",
                        recommended_action=recommended_action,
                        context_weight="normal",
                        module=metric_name,
                        raw_result=f"{value} {unit}",
                    )
                )

        return insights

    def _build_synthesis_prompt(
        self,
        anomaly: AnomalyItem,
        archetype: Archetype,
        frame: str,
        observed_causality: Optional[dict],
        rag_context: str,
        context_weight: ContextWeight,
    ) -> str:
        """Construye el prompt de síntesis para una anomalía específica."""
        causality_str = (
            json.dumps(observed_causality, ensure_ascii=False)
            if observed_causality
            else "ninguno"
        )
        rag_str = rag_context if rag_context else "Sin historial relevante disponible."

        return f"""Genera una frase de copiloto CEO y una acción recomendada para la siguiente anomalía.

## Anomalía detectada por el Forensic CFO:
- Tipo: {anomaly.type}
- Descripción técnica: {anomaly.description}
- Impacto cuantificado: {anomaly.quantified_impact}
- Evidencia: {', '.join(anomaly.data_points)}
- Módulo origen: {anomaly.metric_origin}

## Contexto del día (observed_causality):
{causality_str}

## Historial relevante (RAG — peso: {context_weight}):
{rag_str}

## Instrucciones:
1. copilot_phrase: frase directa al dueño del restaurante, en primera persona plural ("Tu...").
   - Menciona el número exacto del impacto.
   - Si hay observed_causality, puedes ajustar el TONO (más comprensivo), pero NUNCA omitas la anomalía.
   - Máximo 2 oraciones.
2. recommended_action: acción específica con frecuencia o plazo concreto (ej. "Revisar caja diariamente a las 10pm").
   - Una sola acción, sin listas.
   - Máximo 1 oración."""

    # ------------------------------------------------------------------
    # Lógica de context_weight
    # ------------------------------------------------------------------

    def _assign_context_weight(
        self,
        anomaly: AnomalyItem,
        rag_context: str,
    ) -> ContextWeight:
        """
        Asigna context_weight según lógica RAG + severity.

        Reglas (spec n05_ceo_orchestrator.md §Lógica de context_weight):
        - severity "low" → "reducido" siempre (precedencia máxima)
        - RAG con incidentes similares recientes → "amplificado"
        - RAG con contexto pero no recurrente → "normal"
        - Sin RAG relevante → "reducido"
        """
        # Precedencia: severity "low" → siempre "reducido"
        if anomaly.severity == "low":
            return "reducido"

        if not rag_context or rag_context.strip() == "":
            return "reducido"

        # Heurística: si el RAG menciona la misma métrica → patrón recurrente
        metric_lower = anomaly.metric_origin.lower()
        rag_lower = rag_context.lower()

        if metric_lower in rag_lower:
            return "amplificado"

        return "normal"

    # ------------------------------------------------------------------
    # Recuperación de contexto RAG
    # ------------------------------------------------------------------

    def _get_rag_context(
        self,
        forensic_report: ForensicReport,
        business_id: str,
    ) -> str:
        """
        Construye la query RAG desde anomalías high/medium y llama MemoryService.
        Anomalías low no se incluyen en la query.
        Spec: n05_ceo_orchestrator.md §Lógica de Recuperación de Memoria
        """
        relevant_anomalies = [
            a for a in forensic_report.anomalies
            if a.severity in ("high", "medium")
        ]

        if not relevant_anomalies:
            return ""

        query = " ".join([
            f"Anomalía: {a.description}. Evidencia: {', '.join(a.data_points)}."
            for a in relevant_anomalies
        ])

        try:
            from utils.memory_service import MemoryService
            memory = MemoryService(supabase_client=self._db)
            # get_context es síncrono en V1 (wrapper sobre pgvector)
            import asyncio
            context = asyncio.get_event_loop().run_until_complete(
                memory.get_context(query=query, business_id=business_id, limit=3)
            )
            return context or ""
        except Exception:
            # MemoryService puede no estar disponible en V1 — no bloquear
            return ""

    # ------------------------------------------------------------------
    # Recuperación de daily_context (DEPRECATED — stub returning None)
    # ------------------------------------------------------------------

    def _get_daily_context(self, business_id: str, date: str) -> None:
        """DEPRECATED: daily_context reading removed. Always returns None."""
        return None

    # ------------------------------------------------------------------
    # Lógica de escalación a Layer 2
    # ------------------------------------------------------------------

    def _evaluate_escalation(
        self,
        forensic_report: ForensicReport,
        escalate_to_parallel: bool,
        run_id: str,
        business_id: str,
        date: str,
        archetype: Archetype,
        temporalidad: str,
        calc_results: list[dict],
        audit_insights: list[AuditInsight],
        active_metrics: list[str],
    ) -> EscalationInfo:
        """
        Evalúa si escalar a Layer 2 según risk_level y flag del request.

        Correctness properties:
            P2: triggered=True → layer2_run_id no nulo
            P3: triggered=False → layer2_run_id es null
            P4: escalate_to_parallel=False → triggered siempre False
        """
        # P4: flag explícito del cliente
        if not escalate_to_parallel:
            return EscalationInfo(triggered=False, reason=None, layer2_run_id=None)

        # Solo escalar si risk_level es "high"
        if forensic_report.risk_level != "high":
            return EscalationInfo(triggered=False, reason=None, layer2_run_id=None)

        # Intentar disparar Layer 2
        layer2_run_id = str(uuid4())
        try:
            self._trigger_layer2(
                layer2_run_id=layer2_run_id,
                sequential_run_id=run_id,
                business_id=business_id,
                date=date,
                archetype=archetype,
                temporalidad=temporalidad,
                calc_results=calc_results,
                forensic_report=forensic_report,
                audit_insights=audit_insights,
                active_metrics=active_metrics,
            )
            # P2: triggered=True → layer2_run_id no nulo
            return EscalationInfo(
                triggered=True,
                reason="critical_alerts_detected",
                layer2_run_id=layer2_run_id,
            )
        except Exception as exc:
            # Si Layer 2 falla → pipeline_status="failed", no reintentar
            raise RuntimeError(f"Layer 2 falló al escalar: {exc}")

    def _trigger_layer2(
        self,
        layer2_run_id: str,
        sequential_run_id: str,
        business_id: str,
        date: str,
        archetype: Archetype,
        temporalidad: str,
        calc_results: list[dict],
        forensic_report: ForensicReport,
        audit_insights: list[AuditInsight],
        active_metrics: list[str],
    ) -> None:
        """
        Dispara N06 (Layer 2 scatter-gather) de verdad.

        Antes (V1) solo se registraba el intent en audit_results ("N06_pending")
        sin invocar nada -- N06 ya existe y funciona (agents/parallel_orchestrator.py,
        con su propio endpoint /layer2/run), simplemente nunca se conectó a N05.

        Fire-and-forget: N05 dispara Layer 2 y sigue con su propio reporte sin
        esperar a que termine (coincide con el docstring original: "Dispara
        POST /layer2/run internamente"). N06ParallelOrchestrator.run() hace su
        propia persistencia en audit_results con node_id="N06" -- /layer2/status
        ya sabe leer de ahí, no hace falta loguear un placeholder aparte.
        """
        payload = Layer2RunPayload(
            layer2_run_id=layer2_run_id,
            sequential_run_id=sequential_run_id,
            business_id=business_id,
            date=date,
            archetype=archetype,
            temporalidad=temporalidad,
            sequential_context=SequentialContext(
                business_id=business_id,
                active_metrics=active_metrics,
                calc_results=calc_results,
                forensic_report=forensic_report.model_dump(mode="json"),
                insights=[i.model_dump(mode="json") for i in audit_insights],
                context_tags=ContextTags(),
            ),
        )
        coro = self._run_layer2_then_layer3(payload)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is not None:
            # Ya hay un event loop corriendo (ej. llamado desde un endpoint
            # async de FastAPI) -- programar como task, no bloquear.
            loop.create_task(coro)
        else:
            # Sin event loop activo (ej. llamado sync desde un script/test) --
            # correrlo directo, sin bloquear nada mas porque no hay nada mas
            # corriendo en este hilo de todas formas.
            asyncio.run(coro)

    async def _run_layer2_then_layer3(self, payload: Layer2RunPayload) -> None:
        """
        Corre N06 y, si termina con al menos un nodo exitoso, encadena Layer 3
        automaticamente -- antes nada disparaba Layer 3 al terminar N06, el
        endpoint real (/layer3/run, modo normal) requeria que alguien lo
        llamara a mano con el audit_run_id. Ahora es automatico.

        Usa los datos ya en memoria (payload.sequential_context + el resultado
        fresco de N06) en vez de re-leerlos de la DB -- evita depender de que
        _persist ya haya escrito (aunque tambien se corrigio para incluir
        sequential_context, por si alguien dispara Layer 3 manualmente despues).

        Un fallo en Layer 3 nunca debe borrar el trabajo de N06, que ya
        termino y ya se persistio -- por eso todo el bloque de Layer 3 esta
        en su propio try/except.
        """
        result = await N06ParallelOrchestrator(self._db).run(payload)

        if result.gather_status == "failed":
            # Los 3 nodos de Layer 2 fallaron -- no tiene caso generar un
            # reporte consolidado sin ninguna señal nueva que aportar.
            return

        try:
            from agents.layer3_graph import build_layer3_graph

            try:
                from utils.memory_service import MemoryService
                memory_service = MemoryService(supabase_client=self._db)
            except Exception:
                memory_service = None

            initial_state = {
                "layer3_run_id": str(uuid4()),
                "layer2_run_id": payload.layer2_run_id,
                "sequential_run_id": payload.sequential_run_id,
                "business_id": payload.business_id,
                "date": payload.date,
                "archetype": payload.archetype,
                "enriched_payload": {},
                "draft_report": None,
                "intentos_critico": 0,
                "feedback_critico": None,
                "historial_feedback": [],
                "tipos_falla_critico": [],
                "draft_status": "pending",
                "audit_results": [],
                "final_response": None,
                "_db": self._db,
                "_memory_service": memory_service,
                "_parallel_gather_result": {
                    "temporalidad": payload.temporalidad,
                    "sequential_context": payload.sequential_context.model_dump(mode="json"),
                    "node_results": [nr.model_dump(mode="json") for nr in result.node_results],
                },
            }
            graph = build_layer3_graph(memory_service)
            await graph.ainvoke(initial_state)
        except Exception:
            # Layer 3 fallo -- N06 ya corrio y ya se persistio, no se pierde.
            # Alguien puede reintentar Layer 3 manualmente despues via
            # /layer3/run con este mismo layer2_run_id como audit_run_id.
            pass

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def _persist_result(
        self,
        run_id: str,
        business_id: str,
        date: str,
        archetype: Archetype,
        forensic_report: ForensicReport,
        audit_insights: list[AuditInsight],
        pipeline_status: PipelineStatus,
        escalation: EscalationInfo,
        completed_at: str,
    ) -> None:
        """Persiste el resultado de N05 en audit_results."""
        try:
            self._db.table("audit_results").insert(
                {
                    "id": run_id,
                    "business_id": business_id,
                    "date": date,
                    "pipeline_layer": "sequential",
                    "node_id": "N05",
                    "node_status": "completed",
                    "result_data": {
                        "archetype": archetype,
                        "pipeline_status": pipeline_status,
                        "forensic_report": forensic_report.model_dump(mode="json"),
                        "audit_insights": [i.model_dump(mode="json") for i in audit_insights],
                        "escalation": escalation.model_dump(),
                    },
                    "created_at": completed_at,
                }
            ).execute()
        except Exception:
            pass  # La persistencia no bloquea el retorno