"""
N11 — Consultor Especialista (Core Auditor LLM)
LLM primario: claude-3-5-sonnet-20241022 | Fallback: gpt-4o
Temperatura dinámica: 0.7 primer intento / 0.3 reintento.
Spec: .kiro/specs/mepia/n11_consultor.md
"""
from __future__ import annotations

import json
import time
from datetime import datetime, date as date_type, timezone
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel

from agents.layer3_state import Layer3State


# ---------------------------------------------------------------------------
# Modelos de output
# ---------------------------------------------------------------------------

class PragmaticAction(BaseModel):
    action: str
    priority: Literal["immediate", "this_week", "this_month"]
    owner: str


class DraftReport(BaseModel):
    layer3_run_id: str
    business_id: str
    date: str
    archetype: str
    temporalidad: str
    executive_summary: str
    operational_narrative: str
    pragmatic_actions: list[PragmaticAction]
    model_used: str
    generated_at: str
    generation_duration_ms: int
    draft_status: Literal["draft"] = "draft"


# ---------------------------------------------------------------------------
# System prompt (las 4 directivas — spec n11_consultor.md §Sección 4)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """Eres el Consultor Especialista de MEPIA, un operador de piso experto en cafeterías de
especialidad con 15 años de experiencia en operaciones de hospitalidad.

Tu trabajo en esta sesión es redactar un borrador de auditoría financiera y operativa
para el dueño de un negocio de hospitalidad. Recibirás datos matemáticos ya procesados
y tu trabajo es traducirlos a realidades físicas y acciones concretas.

═══════════════════════════════════════════════════════
DIRECTIVA 1 — LENTE OPERATIVO (EL PISO)
═══════════════════════════════════════════════════════
Traduce los "audit_insights" y el "forensic_report" a realidades físicas —
PERO SOLO cuando el hallazgo es genuinamente sobre pérdida física (merma,
desperdicio de insumo, producto servido sin cobrar, inventario faltante). En
esos casos, no digas "el margen bajó 10%". Di algo como "eso equivale a X
kilos de [INSUMO REAL DEL CASO] desperdiciados" — SIEMPRE calculando X a
partir de los data_points y valores reales de ESTE caso, y SIEMPRE usando el
insumo/producto que de verdad aparece en los datos, nunca uno inventado.
REGLA ABSOLUTA: "3 kilos de café" y "40 bebidas" son ejemplos de ESTILO
únicamente — NUNCA los repitas literalmente salvo que el caso real sea
específicamente sobre café y esas cifras salgan de sus propios data_points.

Cuando el hallazgo es sobre POLÍTICA O DECISIÓN FINANCIERA (tasa de descuento,
cortesías, comisión de plataforma de delivery, costo de nómina, varianza de
caja, etc.) — NO fuerces una analogía de "esto se regaló" o "esto no se
cobró". Un descuento no es lo mismo que un producto no cobrado: el cliente sí
pagó, solo pagó menos por una decisión de precio. Describe estos hallazgos en
sus propios términos financieros reales (pesos, % del subtotal, quién lo
autorizó o aplicó) sin inventar una historia de pérdida física que los datos
no respaldan. Ejemplo correcto: "M-03 aplicó $350 MXN en descuentos, el
25.93% de su subtotal del día — muy por encima del 10% que se considera
normal" — sin convertirlo en "regaló X platillos" o "X transacciones sin
cobrar", porque eso no es lo que pasó.

Piensa en purgas, mal dial-in, cuellos de botella en barra, desgaste de equipo
humano en turno tarde, compras de emergencia que rompen el costo estándar —
como categorías de ejemplo para pérdida física, no como contenido a copiar ni
como plantilla para hallazgos que en realidad son financieros.

═══════════════════════════════════════════════════════
DIRECTIVA 2 — REGLA DE ORO (ANCLAJE RAG)
═══════════════════════════════════════════════════════
Antes de redactar la "operational_narrative", lee la sección "brand_identity".
Cualquier recomendación DEBE alinearse con las reglas del dueño ahí descritas.
Si las reglas de brand_identity contradicen tu conocimiento general de operaciones,
OBEDECES a la brand_identity. Siempre.

═══════════════════════════════════════════════════════
DIRECTIVA 3 — CONTINUIDAD HISTÓRICA
═══════════════════════════════════════════════════════
Si existe un "historical_context" relacionado con equipo físico o infraestructura
(molino, máquina de espresso, refrigeración), úsalo como causa probable para explicar
anomalías actuales ANTES de asumir errores humanos.
El equipo falla antes que las personas. Documenta esa hipótesis primero.

═══════════════════════════════════════════════════════
DIRECTIVA 4 — PROHIBICIÓN DE ESTILO
═══════════════════════════════════════════════════════
PROHIBIDO usar lenguaje corporativo o de consultor tradicional.
Palabras y frases prohibidas: "optimizar recursos", "sinergia", "KPIs", "roadmap",
"stakeholders", "apalancar", "deep dive", "best practices".
Habla de frente, con humildad y empatía. Como un colega que conoce el negocio,
no como un consultor que factura por hora.

═══════════════════════════════════════════════════════
FORMATO DE SALIDA OBLIGATORIO
═══════════════════════════════════════════════════════
Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{
  "executive_summary": "string — máx 2 frases",
  "operational_narrative": "string — hallazgos físicos y contextuales",
  "pragmatic_actions": [
    {
      "action": "string",
      "priority": "immediate | this_week | this_month",
      "owner": "string"
    }
  ]
}
No incluyas texto fuera del JSON. No uses markdown dentro del JSON.

REGLA DE COBERTURA (independiente del límite de acciones de abajo):
"operational_narrative" DEBE mencionar TODAS las anomalías reales del Bloque A,
sin excepción — aunque haya 4, 5 o más. Nunca omitas una anomalía real solo
porque ya cubriste otras. Si son muchas, sé más breve en cada una (una o dos
frases por anomalía) en vez de omitir alguna por completo.

Pragmatic_actions: mínimo 1, máximo 3 -- este límite es SOLO para las acciones
recomendadas, no limita cuántas anomalías puedes narrar arriba. Si hay más de 3
anomalías, agrupa varias en una sola acción cuando tenga sentido (ej. una
acción de "revisar con el equipo el manejo de caja y descuentos" puede cubrir
tanto una varianza de caja como una tasa de descuento alta) -- pero eso nunca
justifica dejar una anomalía real fuera de operational_narrative."""

_FEEDBACK_TEMPLATE = """
⚠️ REVISIÓN RECHAZADA: Tu borrador anterior no cumplió con los estándares.
Motivos del revisor: {feedback_critico}
Corrige estrictamente estos puntos en tu nueva redacción."""


# ---------------------------------------------------------------------------
# Nodo del grafo LangGraph
# ---------------------------------------------------------------------------

def n11_consultor_node(state: Layer3State) -> dict:
    """
    N11 — Consultor Especialista.
    Genera DraftReport desde EnrichedAuditPayload.
    Temperatura dinámica: 0.7 primer intento / 0.3 reintento.
    Spec: n11_consultor.md
    """
    t0 = time.monotonic()
    db = state.get("_db")
    layer3_run_id = state["layer3_run_id"]
    feedback_critico = state.get("feedback_critico")
    intentos = state.get("intentos_critico", 0)
    payload = state.get("enriched_payload") or {}

    # Idempotencia: si ya existe un draft aprobado, no regenerar (P6)
    if state.get("draft_status") in ("approved", "approved_with_warning"):
        return {}

    # Temperatura dinámica (P8/P9)
    temperatura = 0.3 if feedback_critico else 0.7

    # Construir prompt de usuario
    user_prompt = _build_user_prompt(payload, feedback_critico)

    # Llamar al LLM con fallback
    draft_data, model_used = _call_llm_with_fallback(user_prompt, temperatura)

    duration_ms = int((time.monotonic() - t0) * 1000)
    now_iso = datetime.now(timezone.utc).isoformat()

    # Validar y construir DraftReport
    try:
        actions = [
            PragmaticAction(**a) for a in (draft_data.get("pragmatic_actions") or [])[:3]
        ]
        if not actions:
            actions = [PragmaticAction(
                action="Revisar datos del día con el equipo.",
                priority="immediate",
                owner="dueño",
            )]

        draft = DraftReport(
            layer3_run_id=layer3_run_id,
            business_id=state["business_id"],
            date=state["date"],
            archetype=state["archetype"],
            temporalidad=payload.get("temporalidad", "short"),
            executive_summary=draft_data.get("executive_summary", "Análisis completado."),
            operational_narrative=draft_data.get("operational_narrative", "Sin hallazgos adicionales."),
            pragmatic_actions=actions,
            model_used=model_used,
            generated_at=now_iso,
            generation_duration_ms=duration_ms,
        )
    except Exception as exc:
        # Fallback de emergencia si el LLM retornó JSON inválido
        draft = DraftReport(
            layer3_run_id=layer3_run_id,
            business_id=state["business_id"],
            date=state["date"],
            archetype=state["archetype"],
            temporalidad=payload.get("temporalidad", "short"),
            executive_summary="No se pudo generar el resumen ejecutivo.",
            operational_narrative=f"Error al procesar la respuesta del LLM: {exc}",
            pragmatic_actions=[PragmaticAction(
                action="Revisar logs del sistema y reintentar.",
                priority="immediate",
                owner="dueño",
            )],
            model_used=model_used,
            generated_at=now_iso,
            generation_duration_ms=duration_ms,
        )

    # Persistir en audit_results
    _persist_n11(db, draft, layer3_run_id)

    return {"draft_report": draft.model_dump(mode="json")}


def _build_user_prompt(payload: dict, feedback_critico: Optional[str]) -> str:
    """Construye el HumanMessage con datos del payload y feedback si existe."""
    # Truncar time_series a los últimos 7 periodos para no saturar el contexto
    ts = payload.get("time_series") or {}
    periodos = (ts.get("periodos") or [])[:7]
    ts_truncated = {**ts, "periodos": periodos}

    data = {
        "temporalidad": payload.get("temporalidad"),
        "forensic_report": payload.get("forensic_report"),
        "audit_insights": payload.get("audit_insights"),
        "time_series": ts_truncated,
        "brand_identity": payload.get("brand_identity"),
        "historical_context": payload.get("historical_context"),
        "parallel_summary": payload.get("parallel_summary"),
    }

    data_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)

    feedback_block = ""
    if feedback_critico:
        # Truncar feedback a 500 chars (spec n11_consultor.md §Edge Cases)
        fb = feedback_critico[:500]
        feedback_block = _FEEDBACK_TEMPLATE.format(feedback_critico=fb)

    return f"{data_str}\n\n{feedback_block}".strip()


def _call_llm_with_fallback(user_prompt: str, temperatura: float) -> tuple[dict, str]:
    """
    Llama a Claude 3.5 Sonnet con fallback a gpt-4o.
    Retorna (parsed_dict, model_used).
    """
    import os

    # Intentar con Claude (primario)
    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage

        llm_primary = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=temperatura,
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        )
        llm_fallback = ChatOpenAI(
            model="gpt-4o",
            temperature=temperatura,
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        )
        llm = llm_primary.with_fallbacks([llm_fallback])

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        response = llm.invoke(messages)
        content = response.content

        # Detectar qué modelo respondió
        model_used = "claude-3-5-sonnet-20241022"
        if hasattr(response, "response_metadata"):
            meta = response.response_metadata or {}
            if "gpt" in str(meta.get("model_name", "")).lower():
                model_used = "gpt-4o (fallback — anthropic_unavailable)"

        parsed = _parse_json_response(content)
        return parsed, model_used

    except Exception:
        pass

    # Fallback directo con OpenAI si LangChain falla
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=temperatura,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        parsed = _parse_json_response(content)
        return parsed, "gpt-4o (fallback — anthropic_unavailable)"
    except Exception as exc:
        return {
            "executive_summary": "Error al generar el reporte.",
            "operational_narrative": f"LLM no disponible: {exc}",
            "pragmatic_actions": [{"action": "Reintentar más tarde.", "priority": "immediate", "owner": "dueño"}],
        }, "error"


def _parse_json_response(content: str) -> dict:
    """Parsea la respuesta JSON del LLM. Reintenta limpiando markdown si falla."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Limpiar bloques markdown ```json ... ```
        clean = content.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            clean = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        return json.loads(clean)


def _persist_n11(db: Any, draft: DraftReport, layer3_run_id: str) -> None:
    """Persiste DraftReport en audit_results con node_id='N11'."""
    if db is None:
        return
    try:
        db.table("audit_results").insert(
            {
                "id": str(uuid4()),
                "business_id": draft.business_id,
                "date": draft.date,
                "pipeline_layer": "loop",
                "node_id": "N11",
                "node_status": "success",
                "result_data": draft.model_dump(mode="json"),
                "created_at": draft.generated_at,
            }
        ).execute()
    except Exception:
        pass