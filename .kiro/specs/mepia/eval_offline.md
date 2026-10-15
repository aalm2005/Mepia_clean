# EVAL — Set de Evaluación Offline

**Estado al 15-oct-2026:** harness y fixtures implementados; ya no es un
placeholder. Las corridas y sus alcances están en el [documento maestro](../../../docs/mepia_v4_metricas_diseno.md).
Este archivo describe la evaluación del motor; el chatbot N15 tiene su
[evaluación](../../../docs/chatbot_step4_eval.md) y su [ejecutor de integración](../../../docs/chatbot_step5_automation.md)
separados. No se repiten aquí las pruebas ni se trasladan sus aprobaciones.

**Capa:** Transversal (Calidad) | **Relación:** Valida S3, S4, N05, N11
**Archivos relacionados:** `s3_motor_calculo.md`, `s4_auditoria_ia.md`, `n05_ceo_orchestrator.md`, `n11_consultor.md`

## Decisión de LLM

No aplica — evaluación offline sin LLM en el propio set. Los nodos evaluados sí usan LLM.

## Responsabilidad

Definir un set de casos de evaluación con ground truth conocido para validar que:
1. S3 produce cálculos correctos ante inputs controlados.
2. S4 detecta las anomalías esperadas.
3. N05 genera insights alineados al arquetipo.
4. N11 produce reportes que cumplen las directivas y restricciones de marca.

---

## Decisiones Resueltas

### Ubicación de los casos

Los casos viven en `tests/eval_test/mepia_ground_truth_caso_NN_descripcion.json`, un archivo por caso.

**Nunca en mepia.db.** Los casos son fixtures de prueba sintéticos y deben quedarse
fijos para que el número de accuracy sea comparable entre corridas. Meterlos a la base
de producción contaminaría `mepia_memory` con historial falso.

### Runner de evaluación

El harness de evaluación es un script standalone:

```
tests/eval_test/eval_runner.py
```

Resultados se guardan en: `tests/eval_test/results/run_<timestamp>.json`

### Formato del caso

Ya existen casos reales en `tests/eval_test/` — se usa como plantilla de estructura.
Los campos obligatorios de cada caso:

```json
{
  "id": "caso_02_faltante_caja",
  "tipo": "anomalia_caja",
  "escenario_narrativo": "Descripción humana del escenario de prueba",
  "anomalias_inyectadas": [
    { "tipo": "faltante_caja", "magnitud": "-$350 MXN", "turno": "vespertino" }
  ],
  "input": {
    "tickets": [ /* TicketEvent[] */ ],
    "payments": [ /* PaymentBreakdown[] */ ],
    "shift_audit": [ /* ShiftAuditEvent[] */ ],
    "inventory": [ /* InventoryUsageEvent[] */ ],
    "config_negocio": {
      "business_id": "uuid",
      "opening_date": "2023-01-15",
      "archetype": "Operative Genius",
      "multi_sucursal": false,
      "delivery_platform_config": [ /* tasas de comisión */ ]
    }
  },
  "esperado_S3": {
    "calc_shift_cash_variance": { "value": -350, "status": "critical" },
    "calc_cancellation_rate": { "value": 0, "status": "ok" }
  },
  "esperado_hallazgos": [
    { "tipo_anomalia": "source_discrepancy", "severity": "high", "metric_origin": "calc_shift_cash_variance" }
  ],
  "esperado_narrativa": {
    "debe_mencionar": ["faltante", "turno vespertino", "$350"],
    "no_debe_mencionar": ["cancelación", "merma"]
  },
  "revisado_por": "aalm2",
  "notas_construccion": "string libre — observaciones del etiquetador"
}
```

---

## Niveles de Verificación

El harness implementa dos niveles de evaluación con diferentes requisitos y objetivos.

### Nivel 1 — Determinista (S3 solo, sin LLM)

**CLI:** `python tests/eval_test/eval_runner.py`

| Aspecto | Detalle |
|---------|---------|
| Scope | Solo funciones S3 — sin ingesta, sin gatekeeper, sin LLM |
| Input | Lee cada ground truth JSON, extrae `input` y `config_negocio` |
| Mock | Construye MockDB que simula respuestas de Supabase a partir del caso |
| Invocación | Llama funciones S3 directamente (calc_shift_cash_variance, etc.) |
| Comparación | CalcResult vs `esperado_S3`: match exacto de status + valor numérico dentro de tolerancia |
| Tolerancia | ±1% relativo para valores > 1.0; ±$0.50 absoluto para valores cercanos a cero |
| Velocidad | <5 segundos total |
| Dependencias | Ninguna externa — puede correr en CI sin API keys ni DB |

**Resultado:** Pass/Fail por caso con delta numérico si falla.

### Nivel 2 — Pipeline S3→S4 (con LLM)

**CLI:** `python tests/eval_test/eval_runner.py --full-pipeline`

| Aspecto | Detalle |
|---------|---------|
| Requisito | Variable de entorno `OPENAI_API_KEY` |
| Scope | Ejecuta todas las funciones S3, luego alimenta CalcResult[] al ForensicCFOAgent (gpt-4o, temp=0) |
| Comparación | ForensicReport.anomalies vs `esperado_hallazgos` |
| Naturaleza | **NO es test pass/fail** — produce reporte estructurado para revisión humana |

**Reporte estructurado por caso:**

- **Found:** hallazgos esperados que aparecieron en el output
- **Missing:** hallazgos esperados que no se generaron
- **Extra:** hallazgos inesperados generados por el sistema

**Resultado:** Reporte JSON + consola. No determina pass/fail automáticamente.

---

## Output

Resultados se guardan en `tests/eval_test/results/run_<timestamp>.json` con estructura:

```python
class EvalCaseResult(BaseModel):
    case_id: str
    node_under_test: str            # "S3" | "S4" | "N05" | "N11"
    passed: bool | None             # None para Nivel 2 (no es pass/fail)
    expected: dict                  # ground truth
    actual: dict                    # output del nodo
    delta: dict | None              # diferencia si numérico
    notes: str | None
```

Además se imprime resumen agregado en consola: total casos, pasados, fallidos, y lista de fallos.

---

## Preguntas del diseño inicial y ampliaciones futuras

Registro histórico de preguntas anteriores a construir los ocho casos. El
etiquetado y las condiciones efectivas de los fixtures existentes se consultan
en cada JSON y en las funciones; la regla de materialidad no se presume universal
para todas las métricas. Los pendientes de ampliación/CI que siguen no significan
que falte implementar el harness actual.

### Método de etiquetado y umbral de aprobación

- Quién etiqueta los ground truths (experto de dominio, generados programáticamente, híbrido).
- Cuántos casos mínimo para una evaluación confiable (target por nodo).
- Qué % de casos pasados constituye un "pass" del set completo (ej. 95% para S3, 80% para N11).
- Cómo se versionan los casos — actualmente en git (`tests/eval_test/`), confirmar que es suficiente.

### Ambigüedad de regla de materialidad Tipo B

Resolver: ¿el umbral efectivo para generar un hallazgo es "cualquiera de las dos condiciones
dispara" (umbral absoluto O umbral porcentual) o "el mayor de las dos"?

> Referencia: ver `notas_construccion` en los casos del eval set.
> Ejemplo: faltante de $350 en un día de $50,000 ventas = 0.7% (bajo en %) pero $350 en absoluto.
> ¿Es critical, warning, o ok? Depende de cuál regla domina.

Esta ambigüedad afecta directamente la etiqueta de `esperado_S3.status` en los casos
del eval set — debe resolverse antes de escalar a >5 casos.

---

## Reglas de generación de warnings

Pendiente — se definirán alertas de regresión cuando un caso previamente pasado falla.

## Acceptance Criteria

- WHEN un caso definido se ejecuta → produce `EvalCaseResult` con `passed: bool`
- WHEN `passed: false` → `delta` documenta la diferencia exacta
- WHEN se agrega nueva función a S3 → debe existir al menos 1 caso de eval para ella
- WHEN se modifica umbral de status → los casos de eval reflejan el nuevo umbral
- WHEN el eval set corre en CI → los casos JSON de `tests/eval_test/` nunca tocan mepia.db

## Edge Cases

Pendiente.

## Correctness Properties (PBT)

Pendiente — las propiedades del set de evaluación se derivarán de las propiedades
ya definidas en cada nodo (S3.P1–P12, S4.P1–Pn, etc.).
