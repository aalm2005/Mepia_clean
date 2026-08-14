"""
S4 — Forensic CFO Agent
Diagnóstico forense de anomalías financieras. Sin recomendaciones. Sin arquetipos.
LLM: gpt-4o, temperatura 0, structured output.
Spec: .kiro/specs/mepia/s4_auditoria_ia.md
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Modelos de salida — ForensicReport y AnomalyItem
# Spec: s4_auditoria_ia.md §Output
# ---------------------------------------------------------------------------

AnomalyType = Literal[
    "margin_leak",
    "source_discrepancy",
    "operational_ceiling",
    "cost_spike",
    "other",
]

Severity = Literal["low", "medium", "high"]
RiskLevel = Literal["low", "medium", "high"]


class AnomalyItem(BaseModel):
    """
    Anomalía individual detectada por el Forensic CFO.
    Cada anomalía es independiente — nunca consolidar en texto.
    Spec: s4_auditoria_ia.md §AnomalyItem
    """
    anomaly_id: str                    # UUID generado por S4
    type: AnomalyType
    description: str                   # descripción técnica, sin lenguaje CEO
    severity: Severity
    quantified_impact: str             # ej. "-320 MXN", "-10% margen"
    data_points: list[str]             # evidencia numérica de S3
    metric_origin: str                 # nombre de la CalcResult origen


class ForensicReport(BaseModel):
    """
    Output estricto de S4. Sin frases CEO-framed ni recomendaciones.
    Spec: s4_auditoria_ia.md §ForensicReport
    """
    business_id: str
    date: str                          # YYYY-MM-DD
    risk_level: RiskLevel
    anomalies: list[AnomalyItem]
    evidence_sources: list[str]        # fuentes realmente comparadas: ["POS", "facturas", "cash_count"]
    observed_causality: Optional[dict] = None  # DailyContextTags adjuntos sin interpretación
    generated_at: str                  # ISO-8601 UTC


# ---------------------------------------------------------------------------
# Structured output schema para gpt-4o
# El LLM retorna este JSON que luego se valida con Pydantic
# ---------------------------------------------------------------------------

_ANOMALY_SCHEMA = {
    "type": "object",
    "properties": {
        "anomaly_id": {"type": "string"},
        "type": {
            "type": "string",
            "enum": ["margin_leak", "source_discrepancy", "operational_ceiling", "cost_spike", "other"],
        },
        "description": {"type": "string"},
        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
        "quantified_impact": {"type": "string"},
        "data_points": {"type": "array", "items": {"type": "string"}},
        "metric_origin": {"type": "string"},
    },
    "required": ["anomaly_id", "type", "description", "severity", "quantified_impact", "data_points", "metric_origin"],
    "additionalProperties": False,
}

_FORENSIC_REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "anomalies": {
            "type": "array",
            "items": _ANOMALY_SCHEMA,
        },
        "evidence_sources": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["anomalies", "evidence_sources"],
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# System prompt del Forensic CFO
# Spec: s4_auditoria_ia.md §System Prompt Base
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """Eres el Auditor Forense Financiero (S4) del sistema MEPIA.
Tu único objetivo es el diagnóstico clínico y la cuantificación de desviaciones operativas.
Operas con precisión quirúrgica.

REGLAS ESTRICTAS:
1. PROHIBIDO sugerir soluciones, mejoras, o estrategias de mitigación.
   Tu trabajo es el diagnóstico, no la consultoría.
2. PROHIBIDO usar lenguaje empático, de "CEO", motivacional o de negocios.
   Mantén un tono estrictamente analítico, contable y forense.
3. PROHIBIDO especular sobre las causas si no están respaldadas explícitamente
   en los datos (evidence_sources).
4. LIMITA tu salida a la identificación de la anomalía, el cálculo de su impacto
   matemático y la categorización del riesgo.
5. PROHIBIDO consolidar múltiples anomalías en una sola frase — cada AnomalyItem
   es independiente y debe documentarse por separado.
6. PROHIBIDO omitir el campo quantified_impact — si no puede calcularse con precisión,
   usa un rango estimado con la fuente de datos usada.
7. REGLA ABSOLUTA: anomalías de tipo "source_discrepancy" SIEMPRE tienen severity "high",
   sin excepción, independientemente del contexto o daily_context.tags.
8. observed_causality está DEPRECADO y siempre es null. No existe contexto externo
   que modifique severity — la severidad se basa EXCLUSIVAMENTE en los datos de S3.
9. NUNCA generes un AnomalyItem cuyo metric_origin corresponda a un CalcResult con status "ok".
   S3 ya evaluó ese valor contra su umbral de negocio y determinó que está dentro de rango normal 
   no lo reevalües con tu propio criterio. Un CalcResult con status "ok" SÍ puede citarse como 
   data_points/evidence_sources para cuantificar o explicar una anomalía distinta que sí tenga status 
   "warning" o "critical" -- pero nunca genera su propio AnomalyItem. EXCEPCIÓN: si un CalcResult trae el campo "_ALERTA_INDIVIDUAL", SÍ debes generar un AnomalyItem para el responsable que ahí se menciona, aunque el campo "status" del mismo CalcResult diga "ok" -- ese campo refleja el agregado del día, que puede diluir el problema de una sola persona. La nota de "_ALERTA_INDIVIDUAL" siempre manda sobre el "status" agregado cuando ambos aparecen juntos.

Responde ÚNICAMENTE con el JSON estructurado solicitado. Sin texto adicional."""

_PERSONAL_THRESHOLDS: dict[str, tuple[Optional[float], Optional[float]]] = {
    "tasa_descuento": (10, None),
    "staff_courtesy_ratio": (None, 5),
    "cancellation_rate": (2, 5),
    "reprint_rate": (5, 10),
}


def _individual_alert_detail(calc_result: dict) -> str | None:
    thresholds = _PERSONAL_THRESHOLDS.get(calc_result.get("metric", ""))
    if not thresholds:
        return None
    warning_t, critical_t = thresholds
    context = calc_result.get("context") or ""
    marker = "by_responsable: "
    idx = context.find(marker)
    if idx == -1:
        return None
    try:
        by_resp = json.loads(context[idx + len(marker):])
    except (ValueError, json.JSONDecodeError):
        return None
    alerts = []
    for responsable, data in by_resp.items():
        rate = data.get("rate_pct")
        if rate is None:
            continue
        rate = float(rate)
        if critical_t is not None and rate > critical_t:
            alerts.append(f"{responsable}: {rate}% (critical, umbral {critical_t}%)")
        elif warning_t is not None and rate > warning_t:
            alerts.append(f"{responsable}: {rate}% (warning, umbral {warning_t}%)")
    return "; ".join(alerts) if alerts else None


def _has_individual_alert(calc_result: dict) -> bool:
    return _individual_alert_detail(calc_result) is not None
    
def _build_user_prompt(
    calc_results: list[dict],
    business_id: str,
    date: str,
) -> str:
    """Construye el mensaje de usuario con los datos de S3 para el LLM.

    Separa fisicamente los CalcResult en dos bloques -- una instruccion de texto
    entre varias reglas numeradas no fue suficiente para que el modelo dejara de
    generar anomalias sobre datos con status "ok" (confirmado en eval real: seguia
    marcando "merma" en el caso de dia limpio pese a la regla explicita). Separar
    estructuralmente el input es una senal mucho mas dificil de ignorar que una
    regla mas en una lista.
    """
    accionables = []
    promoted_ids: set[int] = set()
    for r in calc_results:
        if r.get("status") in ("warning", "critical"):
            accionables.append(r)
            promoted_ids.add(id(r))
            continue
        detail = _individual_alert_detail(r)
        if detail is not None:
            r2 = dict(r)
            r2["_ALERTA_INDIVIDUAL"] = (
                f"El agregado del dia dice status=ok, pero esto es una EXCEPCION "
                f"a la Regla 9: {detail}. Genera un AnomalyItem para este "
                f"responsable especifico -- el status agregado no aplica a su caso "
                f"individual, que si cruza su propio umbral."
            )
            accionables.append(r2)
            promoted_ids.add(id(r))
    referencia = [r for r in calc_results if id(r) not in promoted_ids]

    accionables_json = json.dumps(accionables, ensure_ascii=False, indent=2, default=str)
    referencia_json = json.dumps(referencia, ensure_ascii=False, indent=2, default=str)

    return f"""Analiza los siguientes resultados del Motor de Cálculo S3 para el negocio {business_id} el {date}.

## BLOQUE A — Resultados ACCIONABLES (status != "ok"):
Estos son los ÚNICOS CalcResult sobre los que puedes generar un AnomalyItem. Si este
bloque está vacío ([]), la respuesta correcta es anomalies: [] — no hay nada que
reportar, sin importar qué haya en el Bloque B.
{accionables_json}

## BLOQUE B — Resultados de REFERENCIA (status == "ok", solo contexto):
S3 ya evaluó estos valores contra su umbral de negocio y determinó que están dentro
de rango normal. PROHIBIDO generar un AnomalyItem cuyo metric_origin sea alguno de
estos — no los reevalúes con tu propio criterio. Solo úsalos como data_points de
apoyo si ayudan a cuantificar o explicar una anomalía real del Bloque A (ej. el
desglose de calc_delivery_commission_cost para explicar un calc_commission_cost_ratio
en warning).
{referencia_json}

## observed_causality (deprecado):
null

## Tu tarea:
1. Genera un AnomalyItem por cada anomalía real que identifiques, tomando el
   metric_origin ÚNICAMENTE del Bloque A. El Bloque B es solo lectura de apoyo.
2. Para cada anomalía, genera un AnomalyItem con:
   - anomaly_id: UUID único (genera uno nuevo)
   - type: clasifica según el tipo de anomalía
   - description: descripción técnica precisa, sin lenguaje CEO
   - severity: "low" | "medium" | "high" — basado SOLO en los datos
   - quantified_impact: impacto cuantificado en MXN o % (nunca null)
   - data_points: evidencia numérica específica de los CalcResult
   - metric_origin: nombre exacto de la métrica de S3 que originó la anomalía
3. Lista las evidence_sources realmente usadas (solo las que aparecen en los datos).

RECUERDA:
- "source_discrepancy" SIEMPRE severity "high"
- Si no hay anomalías, retorna anomalies: []
- Cada anomalía en su propio AnomalyItem, nunca consolidadas"""


# ---------------------------------------------------------------------------
# ForensicCFOAgent
# ---------------------------------------------------------------------------

class ForensicCFOAgent:
    """
    S4 — Forensic CFO Agent.
    Recibe CalcResult[] de S3 y genera un ForensicReport con anomalías detectadas.

    Usa gpt-4o con temperatura 0 y structured output para garantizar
    determinismo y conformidad con el contrato ForensicReport.
    """

    def __init__(self) -> None:
        # Importación lazy para no requerir openai en tests unitarios
        try:
            from openai import OpenAI
            import os
            self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        except Exception as exc:
            raise RuntimeError(
                f"ForensicCFOAgent requiere OPENAI_API_KEY configurado: {exc}"
            )

    def run(
        self,
        calc_results: list[dict],
        business_id: str,
        date: str,
        daily_context_tags: Optional[dict] = None,
    ) -> ForensicReport:
        """
        Ejecuta el diagnóstico forense sobre los resultados de S3.

        Args:
            calc_results       : lista de CalcResult serializados (dicts)
            business_id        : UUID del negocio
            date               : YYYY-MM-DD
            daily_context_tags : DEPRECATED — parámetro mantenido por backward
                                 compatibility pero siempre ignorado.
                                 observed_causality es siempre None.

        Returns:
            ForensicReport validado con Pydantic

        Correctness properties garantizadas:
            P1: observed_causality siempre None (deprecated)
            P2: risk_level "high" ↔ ≥1 anomalía high
            P3: source_discrepancy siempre severity "high"
            P4: ForensicReport sin campo archetype
            P5: evidence_sources solo contiene fuentes realmente comparadas
        """
        # --- 1. Construir prompt ---
        # daily_context_tags is ignored (deprecated) — observed_causality always None
        user_prompt = _build_user_prompt(calc_results, business_id, date)

        # --- 2. Llamar a gpt-4o con structured output (JSON schema) ---
        response = self._client.chat.completions.create(
            model="gpt-4o",
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "forensic_report",
                    "strict": True,
                    "schema": _FORENSIC_REPORT_SCHEMA,
                },
            },
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )

        # --- 3. Parsear respuesta del LLM ---
        raw_json = response.choices[0].message.content
        llm_data = json.loads(raw_json)

        # --- 4. Construir AnomalyItems con garantías de correctness ---
        anomalies: list[AnomalyItem] = []
        for item in llm_data.get("anomalies", []):
            # P3: source_discrepancy SIEMPRE severity "high" — override incondicional
            if item.get("type") == "source_discrepancy":
                item["severity"] = "high"

            # Garantizar anomaly_id válido
            if not item.get("anomaly_id"):
                item["anomaly_id"] = str(uuid4())

            anomalies.append(AnomalyItem(**item))

        # --- 5. Calcular risk_level global (P2) ---
        # P2: "high" ↔ ≥1 anomalía high; "medium" si solo medium; "low" si no hay o solo low
        risk_level = _compute_risk_level(anomalies)

        # --- 6. Construir ForensicReport ---
        # P1: observed_causality is always None (deprecated — daily_context removed)
        # P4: sin campo archetype
        report = ForensicReport(
            business_id=business_id,
            date=date,
            risk_level=risk_level,
            anomalies=anomalies,
            evidence_sources=llm_data.get("evidence_sources", []),
            observed_causality=None,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        return report


# ---------------------------------------------------------------------------
# Función auxiliar pura — cálculo de risk_level
# Separada para facilitar tests PBT (P2)
# ---------------------------------------------------------------------------

def _compute_risk_level(anomalies: list[AnomalyItem]) -> RiskLevel:
    """
    Calcula el risk_level global del reporte.

    Reglas (spec s4_auditoria_ia.md §Reglas de risk_level):
        - "high"   : ≥ 1 anomalía con severity "high"
        - "medium" : solo anomalías "medium" (ninguna "high")
        - "low"    : solo anomalías "low" o sin anomalías
    """
    if not anomalies:
        return "low"

    severities = {a.severity for a in anomalies}

    if "high" in severities:
        return "high"
    if "medium" in severities:
        return "medium"
    return "low"
