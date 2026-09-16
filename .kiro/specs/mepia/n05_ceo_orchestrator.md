# N05 — CEO Orchestrator (Motor de Síntesis Estratégica)

**Capa:** CEO Layer | **Anterior:** S4 Forensic CFO | **Siguiente:** N06 Orquestador ADK (Layer 2)
**Archivo de implementación:** `agents/ceo_orchestrator.py`
**Enfoque:** API-First / Headless — stateless, sin dependencias de UI

## Decisión de LLM

| Campo | Valor |
|-------|-------|
| **Modelo** | `gpt-4o` |
| **Proveedor** | OpenAI |
| **Temperatura** | `0.3` — permite variación controlada en el tono por arquetipo sin perder coherencia |
| **Justificación** | Capacidad fuerte para adoptar el arquetipo directivo (Operative Genius / Product Purist / Growth Hacker) y generar frases CEO-framed específicas y accionables. Requiere razonamiento sobre causalidad contextual (`observed_causality`). |
| **Variable de entorno requerida** | `OPENAI_API_KEY` |

---

## Responsabilidad

Dos roles en uno:

1. **Orquestador del pipeline** — coordina S3 → S4 → síntesis y decide si escalar a Layer 2
2. **Motor de Síntesis Estratégica** — toma el `ForensicReport` de S4 + memoria RAG y genera
   el `AuditInsight` final con `copilot_phrase` y `recommended_action` filtrados por arquetipo CEO

```
Cliente
  │
  └─ POST /orchestrator/run
        │
        ├─ Verificar prerequisitos
        ├─ Ejecutar S3 → CalcResult[]
        ├─ Ejecutar S4 → ForensicReport
        ├─ Leer memoria RAG (MemoryService.get_context)
        ├─ Sintetizar ForensicReport + contexto → AuditInsight[] (con arquetipo)
        ├─ Evaluar si escalar a Layer 2
        └─ Retornar OrchestratorResult
```

---

## Gestión de Arquetipos (heredado de S4)

N05 es ahora el único nodo que aplica el filtro de arquetipo CEO.
Inyecta el `CEO Cognitive Frame` al sintetizar el `ForensicReport` en `AuditInsight`.

### Diccionario de Prompt Templates

Cada template tiene instrucciones base que **prohíben resúmenes genéricos** y obligan a
frases directas y pragmáticas. El input siempre es el `ForensicReport` completo + `observed_causality`.

| Arquetipo        | Enfoque del prompt de síntesis |
|------------------|-------------------------------|
| Operative Genius | Traduce anomalías en alertas sobre cuellos de botella y fugas de capital en procesos |
| Product Purist   | Traduce anomalías en impacto directo a la calidad del producto/experiencia |
| Growth Hacker    | Traduce anomalías en oportunidades de escala, recompra y crecimiento |

### Uso de `observed_causality`

> **NOTA:** `observed_causality` queda como `null` siempre a partir del retiro de `daily_context`.
> La lógica de ajuste de tono se mantiene documentada por si se reintroduce una fuente de
> causalidad contextual en el futuro, pero actualmente no tiene efecto.

N05 lee el campo `observed_causality` del `ForensicReport` para decidir el tono de la
`copilot_phrase`. Si hay causalidad contextual (ej. `falla_maquina`), N05 puede redactar
una recomendación más comprensiva — pero **nunca omite la anomalía**.

```
Ejemplo:
  ForensicReport.anomalies[0].severity = "high"  (margen -10%)
  ForensicReport.observed_causality = { equipo: "falla_maquina" }

  AuditInsight generado por N05:
    alert_level: "critical"
    copilot_phrase: "Tu margen bajó 10% por la falla de la máquina de espresso.
                     El impacto es real (~$1,200 MXN). Acción: mantenimiento
                     preventivo cada 90 días para evitar que esto se repita."
    recommended_action: "Mantenimiento preventivo + revisión de caja inmediata"
```

---

## Endpoint principal

### `POST /orchestrator/run`

**Request body — `OrchestratorRunPayload`:**

```python
class OrchestratorRunPayload(BaseModel):
    business_id: UUID
    date: date
    archetype: Literal[
        "Operative Genius", "Product Purist", "Growth Hacker"
    ] = "Operative Genius"
    escalate_to_parallel: bool = True
    temporalidad: Literal["short", "medium", "long"] = "short"  # propagado hasta N10
```

**Response 200:**
```json
{
  "run_id": "uuid-v4",
  "business_id": "uuid-v4",
  "date": "2024-01-15",
  "archetype": "Operative Genius",
  "pipeline_status": "completed" | "partial" | "escalated" | "failed",
  "sequential_results": {
    "active_metrics": ["cash_reconciliation", "daily_break_even"],
    "calc_results": [ /* CalcResult[] */ ],
    "forensic_report": { /* ForensicReport de S4 */ },
    "audit_insights": [ /* AuditInsight[] generados por N05 */ ]
  },
  "escalation": {
    "triggered": true,
    "reason": "critical_alerts_detected",
    "layer2_run_id": "uuid-v4"
  },
  "dormant_metrics": [
    { "metric": "inventory_variance", "missing": ["recipes"] }
  ],
  "completed_at": "2024-01-15T22:10:00Z"
}
```

**Códigos de error:**

| HTTP | Condición |
|------|-----------|
| 404  | `business_id` no existe |
| 409  | S2 no ha corrido o todas las métricas en `dormant`/`blocked` |
| 422  | `archetype` inválido |
| 422  | `date` en el futuro |
| 503  | Fallo interno en S3 o S4 — incluye detalle del nodo que falló |

---

### `GET /orchestrator/status/{run_id}`

**Response 200:**
```json
{
  "run_id": "uuid-v4",
  "business_id": "uuid-v4",
  "date": "2024-01-15",
  "pipeline_status": "running" | "completed" | "partial" | "failed",
  "current_node": "N05_synthesis",
  "completed_at": "2024-01-15T22:10:00Z"
}
```

---

## Lógica de escalación a Layer 2

N05 evalúa el `ForensicReport.risk_level` de S4 para decidir si escalar.

| Condición | Acción |
|-----------|--------|
| `risk_level: "high"` | Escalar a Layer 2 automáticamente |
| `risk_level: "medium"` o `"low"` | No escalar (solo Sequential) |
| `escalate_to_parallel: false` en request | Nunca escalar |

Cuando escala: dispara N06 internamente con el `run_id` del Sequential como
contexto y con `source_s3_result_id = CalcRunResult.run_id` como raíz exacta del
linaje.

Si N06 retorna HTTP 503:
- Actualizar `pipeline_status` a `"failed"` en `OrchestratorResult`
- Persistir error en `audit_results` con `module: "N06"` y detalle del fallo
- No reintentar automáticamente — retornar HTTP 503 al cliente

---

## Flujo de síntesis (N05 como CEO)

```
1. Recibe ForensicReport de S4
2. Construye query RAG desde anomalías de severidad "high" y "medium"
3. Llama MemoryService.get_context(query, business_id)
4. Para cada AnomalyItem en ForensicReport.anomalies:
   a. Aplica CEO Cognitive Frame del arquetipo recibido
   b. Lee observed_causality para ajustar tono (no severidad)
   c. Asigna context_weight según lógica de memoria histórica
   d. Genera AuditInsight con copilot_phrase + recommended_action
5. Determina alert_level de cada AuditInsight desde severity del AnomalyItem
```

### Lógica de Recuperación de Memoria (RAG)

La `query` para `MemoryService.get_context` se construye concatenando los campos
`description` y `evidence_sources` de las anomalías con `severity: "high"` o `"medium"`:

```python
query = " ".join([
    f"Anomalía: {a.description}. Evidencia: {', '.join(a.evidence_sources or [])}."
    for a in forensic_report.anomalies
    if a.severity in ("high", "medium")
])
```

Las anomalías `severity: "low"` no se incluyen en la query RAG — no justifican
consumir contexto histórico.

### Lógica de Asignación de `context_weight`

| Condición | `context_weight` |
|-----------|-----------------|
| RAG devuelve incidentes similares en los últimos 90 días para la misma categoría de anomalía | `"amplificado"` — requiere acción correctiva fuerte, patrón recurrente |
| RAG devuelve contexto histórico pero no recurrente a corto plazo | `"normal"` — comportamiento por defecto |
| RAG no devuelve contexto histórico relevante, O `AnomalyItem.severity: "low"` | `"reducido"` — anomalía aislada o de bajo impacto |

Regla de precedencia: si `severity: "low"` → `context_weight: "reducido"` siempre,
independientemente del resultado del RAG.

### Mapeo `AnomalyItem.severity` → `AuditInsight.alert_level`

| `severity` (S4) | `alert_level` (N05) |
|-----------------|---------------------|
| `"high"`        | `"critical"`        |
| `"medium"`      | `"warning"`         |
| `"low"`         | `"info"`            |

---

## Output — `AuditInsight` (generado por N05)

```
anomaly_ref: UUID                // anomaly_id del AnomalyItem origen en ForensicReport
copilot_phrase: string           // frase CEO-framed, específica y accionable
archetype: CEO Archetype         // arquetipo aplicado
alert_level: "info"|"warning"|"critical"
recommended_action: string       // acción específica con frecuencia o plazo
context_weight: "reducido"|"normal"|"amplificado"
module: string                   // nombre del módulo auditado (ej. "conciliacion_caja")
raw_result: string               // número crudo de S3 — tomado de AnomalyItem.quantified_impact
```

---

## Prerequisitos de ejecución

```
1. business_id existe en businesses
2. metric_status para business_id + date tiene al menos 1 status = "active"
3. No hay documentos con needs_human_review = true sin resolver para esa fecha
```

---

## Persistencia

Cada ejecución se registra en `audit_results`:

| Campo           | Valor |
|-----------------|-------|
| `id`            | UUID de la ejecución N05 (`OrchestratorResult.run_id`) |
| `source_s3_result_id` | `audit_results.id` de la fila S3 producida en esta ejecución |
| `business_id`   | FK → businesses |
| `date`          | Fecha auditada |
| `node_id`       | `"N05"` para la síntesis CEO |
| `archetype`     | Arquetipo usado |
| `raw_result`    | `ForensicReport` serializado (de S4) |
| `copilot_phrase`| Frase generada por N05 |

---

## Acceptance Criteria

- WHEN S2 no ha corrido → HTTP 409, no ejecutar pipeline
- WHEN `ForensicReport.risk_level: "high"` y `escalate_to_parallel: true` → `escalation.triggered: true`
- WHEN `escalate_to_parallel: false` → `escalation.triggered: false` siempre
- WHEN `AnomalyItem.severity: "high"` → `AuditInsight.alert_level: "critical"` siempre
- WHEN `observed_causality` presente → N05 puede ajustar tono de `copilot_phrase`, nunca `alert_level`
- WHEN pipeline completa sin errores → `pipeline_status: "completed"`
- WHEN pipeline completa con métricas `dormant` → `pipeline_status: "partial"`
- WHEN escaló a Layer 2 → `pipeline_status: "escalated"`, `layer2_run_id` no nulo

---

## Correctness Properties (PBT)

| ID | Propiedad |
|----|-----------|
| P1 | `run_id`, `pipeline_status`, `completed_at` siempre no nulos en `OrchestratorResult` |
| P2 | `escalation.triggered: true` → `layer2_run_id` no nulo |
| P3 | `escalation.triggered: false` → `layer2_run_id` es null siempre |
| P4 | `escalate_to_parallel: false` → `escalation.triggered` siempre false |
| P5 | S2 sin métricas `active` → HTTP 409, ningún nodo S3/S4/N05 ejecutado |
| P6 | `AnomalyItem.severity: "high"` → `AuditInsight.alert_level: "critical"` sin excepción |
| P7 | `observed_causality` presente → `alert_level` no cambia, solo `context_weight` y tono de frase |
