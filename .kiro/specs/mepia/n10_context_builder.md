# N10 — Context Builder (Constructor de Contexto Determinista)

**Capa:** Layer 3 — primer paso | **Anterior:** N06 Orquestador ADK | **Siguiente:** N11 Consultor Especialista
**Archivo de implementación:** `agents/context_builder.py`
**Tecnología:** Python puro — sin LLM, 100% determinista
**Patrón:** Transformador de datos — recibe `ParallelGatherResult`, emite `Enriched_Audit_Payload`

---

## Responsabilidad

Actuar como el preparador de datos de Layer 3. No analiza, no interpreta, no genera texto.
Su único trabajo es consolidar y comprimir el contexto financiero, operativo y de identidad
en un payload estructurado listo para que N11 lo consuma sin overhead de tokens.

```
N06 ParallelGatherResult
        │
        ↓
N10 Context Builder (Python determinista)
  ├─ Extrae ForensicReport + N09 result de ParallelGatherResult
  ├─ Ejecuta SQL Rollups según temporalidad
  ├─ Consulta SQL directa para brand_identity (mepia_memory)
  ├─ Consulta MemoryService para historial RAG (limit=3, max 1500 tokens)
  ├─ Persiste Enriched_Audit_Payload en audit_results
  └─ Emite Enriched_Audit_Payload a N11
        │
        ↓
N11 Consultor Especialista (LLM)
```

---

## Endpoint REST

### `POST /layer3/context-build`

Llamado internamente por N06 tras completar el gather. También invocable directamente para testing.

**Request body:** `ContextBuilderInput`

**Response 202:** Acepta la solicitud y procesa de forma síncrona (N10 es determinista, no necesita polling).

**Response 200:**
```json
{
  "layer3_run_id": "uuid-v4",
  "layer2_run_id": "uuid-v4",
  "build_status": "complete" | "partial",
  "built_at": "2024-01-15T22:15:00Z",
  "build_duration_ms": 340
}
```

**Códigos de error:**

| HTTP | Condición |
|------|-----------|
| 404  | `business_id` no existe |
| 422  | `ContextBuilderInput` inválido |
| 503  | Fallo en SQL rollup o MemoryService — incluye detalle |

---

## Input

```python
class ContextBuilderInput(BaseModel):
    parallel_gather_result: ParallelGatherResult  # output completo de N06
    # temporalidad se lee de parallel_gather_result.temporalidad — no se duplica aquí
```

### Extracción desde `ParallelGatherResult`

```python
# temporalidad viene dentro del ParallelGatherResult — no se duplica
temporalidad = parallel_gather_result.temporalidad

# Datos base de Layer 1 (via sequential_context)
forensic_report  = parallel_gather_result.sequential_context.forensic_report
audit_insights   = parallel_gather_result.sequential_context.insights
calc_results     = parallel_gather_result.sequential_context.calc_results
context_tags     = parallel_gather_result.sequential_context.context_tags
archetype        = parallel_gather_result.archetype
business_id      = parallel_gather_result.business_id
date             = parallel_gather_result.date

# Resultado de N09 (único nodo activo en V1)
n09_result = next(
    (r for r in parallel_gather_result.node_results
     if r.node_id == "N09" and r.status == "success"),
    None
)

# N07 y N08 en V1: status="error", error_detail="not_implemented_v1"
# N10 los ignora silenciosamente — no genera warning por este código específico
```

---

## Mecánica Principal — Time-Series Rollups (SQL Dinámico)

La granularidad de las consultas SQL depende del parámetro `temporalidad`.

### Modos de agrupación

| `temporalidad` | Rango | Granularidad SQL | Casos de uso |
|----------------|-------|-----------------|--------------|
| `"short"` | últimos 30 días | `GROUP BY dia` | Eficiencia de barra, horarios pico, varianza diaria |
| `"medium"` | últimos 6 meses | `GROUP BY semana` | Tendencias, retención, ingeniería de menú, estacionalidad |
| `"long"` | último año | `GROUP BY mes` | Resúmenes CapEx, servicios estructurales, ciclo anual |

### Modelos tipados por granularidad

```python
class ShortPeriodMetrics(BaseModel):
    """Métricas diarias — usado cuando temporalidad == 'short'."""
    periodo: date
    ingresos: Decimal
    gastos_variable: Decimal
    gastos_fijos: Decimal
    num_transacciones: int

class MediumPeriodMetrics(BaseModel):
    """Métricas semanales — usado cuando temporalidad == 'medium'."""
    periodo: date                    # inicio de la semana (DATE_TRUNC result)
    ingresos: Decimal
    egresos: Decimal
    ingreso_promedio_semanal: Decimal

class LongPeriodMetrics(BaseModel):
    """Métricas mensuales — usado cuando temporalidad == 'long'."""
    periodo: date                    # inicio del mes (DATE_TRUNC result)
    capex_mes: Decimal
    ingresos_mes: Decimal
    egresos_mes: Decimal
```

### Consultas por modo

**`short` — detalle diario:**
```sql
SELECT
    transaction_date AS periodo,
    SUM(amount) FILTER (WHERE type = 'ingreso') AS ingresos,
    SUM(amount) FILTER (WHERE type = 'egreso' AND expense_behavior = 'VARIABLE') AS gastos_variable,
    SUM(amount) FILTER (WHERE type = 'egreso' AND expense_behavior = 'FIXED') AS gastos_fijos,
    COUNT(*) AS num_transacciones
FROM transactions
WHERE business_id = :business_id
  AND transaction_date BETWEEN :date_start AND :date
  AND needs_human_review = false
GROUP BY transaction_date
ORDER BY transaction_date DESC
```

**`medium` — tendencia semanal (últimos 6 meses):**
```sql
SELECT
    DATE_TRUNC('week', transaction_date) AS periodo,
    SUM(amount) FILTER (WHERE type = 'ingreso') AS ingresos,
    SUM(amount) FILTER (WHERE type = 'egreso') AS egresos,
    AVG(amount) FILTER (WHERE type = 'ingreso') AS ingreso_promedio_semanal
FROM transactions
WHERE business_id = :business_id
  AND transaction_date BETWEEN :date_start AND :date
  AND needs_human_review = false
GROUP BY DATE_TRUNC('week', transaction_date)
ORDER BY periodo DESC
```

**`long` — resumen mensual (último año):**
```sql
SELECT
    DATE_TRUNC('month', transaction_date) AS periodo,
    SUM(amount) FILTER (WHERE type = 'egreso' AND expense_behavior = 'CAPEX') AS capex_mes,
    SUM(amount) FILTER (WHERE type = 'ingreso') AS ingresos_mes,
    SUM(amount) FILTER (WHERE type = 'egreso') AS egresos_mes
FROM transactions
WHERE business_id = :business_id
  AND transaction_date BETWEEN :date_start AND :date
  AND needs_human_review = false
GROUP BY DATE_TRUNC('month', transaction_date)
ORDER BY periodo DESC
```

### Cálculo de `date_start` por `temporalidad`

```python
date_start = {
    "short":  date - timedelta(days=30),
    "medium": date - timedelta(days=180),   # últimos 6 meses exactos
    "long":   date - timedelta(days=365),
}[temporalidad]
```

---

## Inyección de Identidad de Marca (SQL Determinístico)

La identidad de marca **no usa búsqueda semántica** — usa una consulta SQL directa por metadata.
Esto garantiza que siempre se recupera el documento correcto sin depender del score vectorial.

```python
# Consulta SQL directa — NO usa MemoryService.get_context()
brand_identity_row = await db.fetchone("""
    SELECT content
    FROM mepia_memory
    WHERE (metadata->>'node_origin') = 'onboarding'
      AND business_id = :business_id
    ORDER BY created_at DESC
    LIMIT 1
""", {"business_id": business_id})

brand_content = brand_identity_row["content"] if brand_identity_row else None
```

### Historial RAG (MemoryService — límite de tokens)

El historial usa `MemoryService.get_context()` con límite estricto de tokens:

```python
historical_context = await memory_service.get_context(
    query=f"auditoria financiera {archetype} anomalias gastos",
    business_id=business_id,
    limit=3   # máximo 3 chunks × 500 tokens = 1,500 tokens máximo
)
# Si historical_context supera 1,500 tokens → truncar al límite antes de incluir en payload
MAX_HISTORICAL_TOKENS = 1500
```

Razón del límite: `Enriched_Audit_Payload` completo no debe superar ~4,000 tokens para
dejar margen al system prompt y respuesta de N11.

> **Motor de embeddings (V1 — fijo):** `text-embedding-3-small` de OpenAI, **1536 dimensiones**.
> La búsqueda semántica en `mepia_memory` usa distancia coseno vía índice HNSW.
> Cambiar el modelo de embeddings requiere recrear la tabla y regenerar todos los vectores existentes.

### Identidad de marca en `mepia_memory`

El "Lente del CEO" se inserta en `mepia_memory` durante el onboarding:

```python
MemoryChunk(
    business_id=business_id,
    source_audit_run_id=None,   # nullable — ver nota de schema
    node_origin="onboarding",   # enum ampliado: "N12" | "N13" | "onboarding"
    date=opening_date,
    content="""
        Identidad de marca: hospitalidad invisible.
        Principios: humildad, espacio seguro, experiencia sin fricción.
        PROHIBIDO en recomendaciones: tácticas de fidelización ostentosas,
        mecánicas estilo casino, marketing agresivo o pretencioso.
        El análisis debe priorizar la experiencia del cliente sobre métricas de conversión.
    """,
    archetype=None,              # null — identidad fija, no depende del arquetipo
    quality_approved=True
)
```

> El contenido anterior es ilustrativo. GET/POST/PUT de
> `/business/{id}/onboarding[/status]`, en `api/onboarding.py`, verifican sesión y
> propiedad; el guardado inserta el chunk con `status="pending_embed"`.
> Desde el 15-oct-2026 Documentos aplica ajustes iniciales si faltan y permite
> personalización avanzada opcional. El guardado no genera embeddings; la
> identidad se recupera por SQL directo. Ver `n10_onboarding_identidad.md`.

La identidad de marca es **fija e independiente del arquetipo**.

---

## Output — `Enriched_Audit_Payload`

```python
class TimeSeriesRollup(BaseModel):
    temporalidad: Literal["short", "medium", "long"]
    date_start: date
    date_end: date
    granularidad: Literal["dia", "semana", "mes"]
    # periodos tipado estrictamente según granularidad:
    periodos: list[ShortPeriodMetrics] | list[MediumPeriodMetrics] | list[LongPeriodMetrics]


class ParallelNodeSummary(BaseModel):
    n09_available: bool
    n09_result: Optional[FinancialAuditResult]   # None si N09 falló
    n07_status: Literal["not_implemented_v1", "success", "error"]
    n08_status: Literal["not_implemented_v1", "success", "error"]
    all_warnings: list[str]   # warnings agregados de nodos disponibles


class BrandIdentityBlock(BaseModel):
    retrieved: bool          # false si mepia_memory no tiene chunk de onboarding
    content: str             # texto del Lente del CEO — vacío si retrieved=false
    fallback_used: bool      # true si se usó identidad genérica por ausencia de chunk


class EnrichedAuditPayload(BaseModel):
    # Trazabilidad
    layer3_run_id: UUID          # nuevo UUID generado por N10
    layer2_run_id: UUID
    sequential_run_id: UUID
    source_s3_result_id: Optional[UUID]  # audit_results.id de S3; null en legacy/aislado
    business_id: UUID
    date: date
    archetype: Literal["Operative Genius", "Product Purist", "Growth Hacker"]
    temporalidad: Literal["short", "medium", "long"]

    # Diagnóstico base (S4 via N06)
    forensic_report: ForensicReport

    # Insights CEO (N05 via N06)
    audit_insights: list[AuditInsightItem]

    # Rollups temporales (SQL dinámico, tipado estricto)
    time_series: TimeSeriesRollup

    # Estado de nodos paralelos
    parallel_summary: ParallelNodeSummary

    # Identidad de marca (SQL directo a mepia_memory)
    brand_identity: BrandIdentityBlock

    # Historial RAG (máx 1,500 tokens)
    historical_context: str

    # Metadata de construcción
    built_at: datetime
    build_duration_ms: int
```

> Nota de naming: el contrato se llama `EnrichedAuditPayload` en código Python (snake_case class).
> En documentación y glosario se referencia como `Enriched_Audit_Payload` por legibilidad.

---

## Persistencia en `audit_results`

N10 persiste el payload **antes** de entregarlo a N11. Si N11 falla, el payload es recuperable.

| Campo           | Valor |
|-----------------|-------|
| `id`            | `layer3_run_id` (nuevo UUID de N10) |
| `source_s3_result_id` | ID de la fila S3 raíz, propagado sin cambios |
| `business_id`   | FK → businesses |
| `date`          | Fecha auditada |
| `pipeline_layer`| `"loop"` |
| `node_id`       | `"N10"` |
| `module`        | `"context_builder"` |
| `archetype`     | Arquetipo del run |
| `raw_result`    | `EnrichedAuditPayload` serializado (JSON) |
| `copilot_phrase`| `null` — N10 no genera frases |
| `node_status`   | `"success"` \| `"partial"` \| `"failed"` |

---

## Notas de Schema — Cambios Requeridos

### 1. `mepia_memory.source_audit_run_id` → nullable

La columna debe ser `NULL`able para permitir chunks de onboarding sin auditoría previa:

```sql
-- En 003_memory.sql:
source_audit_run_id UUID REFERENCES audit_results(run_id) ON DELETE SET NULL
-- (no NOT NULL)
```

### 2. `MemoryChunk.node_origin` → enum ampliado

```python
node_origin: Literal["N12", "N13", "onboarding"]
```

Actualizar en: `_glossary.md` contrato `MemoryChunk`, `mem_memory_layer.md`, y modelo Pydantic.

---

## Acceptance Criteria

- WHEN `temporalidad == "short"` → SQL usa `GROUP BY transaction_date`, rango 30 días, `periodos` es `list[ShortPeriodMetrics]`
- WHEN `temporalidad == "medium"` → SQL usa `GROUP BY DATE_TRUNC('week', ...)`, rango 180 días (6 meses), `periodos` es `list[MediumPeriodMetrics]`
- WHEN `temporalidad == "long"` → SQL usa `GROUP BY DATE_TRUNC('month', ...)`, rango 365 días, `periodos` es `list[LongPeriodMetrics]`
- WHEN N07/N08 tienen `error_detail: "not_implemented_v1"` → ignorados silenciosamente, sin warning
- WHEN N09 tiene `status: "success"` → `parallel_summary.n09_available: true`, datos incluidos
- WHEN N09 tiene `status: "error"` o `"timeout"` → `parallel_summary.n09_available: false`, `n09_result: null`
- WHEN `mepia_memory` tiene chunk `node_origin: "onboarding"` → `brand_identity.retrieved: true`, recuperado por SQL directo
- WHEN no hay chunk de onboarding → `brand_identity.fallback_used: true`, contenido genérico
- WHEN `needs_human_review = true` en transacciones → excluidas del rollup SQL
- WHEN `historical_context` supera 1,500 tokens → truncado antes de incluir en payload
- WHEN N10 completa → `EnrichedAuditPayload` persistido en `audit_results` antes de entregar a N11
- WHEN N10 completa → N11 recibe `EnrichedAuditPayload`, nunca `ParallelGatherResult` crudo
- WHEN Layer 3 recibe `source_s3_result_id` → N10 lo conserva en el payload y
  en su fila de `audit_results`

---

## Edge Cases

- `temporalidad` no enviado → default `"short"` (heredado de `OrchestratorRunPayload`)
- N09 timeout → `n09_available: false`, warning en `all_warnings`, N10 continúa
- `mepia_memory` vacío (negocio nuevo) → `brand_identity.fallback_used: true`, análisis continúa
- Sin transacciones en el rango → `time_series.periodos: []`, N11 recibe contexto vacío con nota
- `MemoryService` no disponible → `historical_context: ""`, `brand_identity.retrieved: false`, continúa
- SQL rollup falla → `node_status: "partial"`, `time_series.periodos: []`, N11 notificado

---

## Correctness Properties (PBT)

| ID | Propiedad |
|----|-----------|
| P1 | `temporalidad == "short"` → `time_series.granularidad == "dia"` y `periodos` es `list[ShortPeriodMetrics]` |
| P2 | `temporalidad == "medium"` → `time_series.granularidad == "semana"` y `periodos` es `list[MediumPeriodMetrics]` |
| P3 | `temporalidad == "long"` → `time_series.granularidad == "mes"` y `periodos` es `list[LongPeriodMetrics]` |
| P4 | N07/N08 con `error_detail: "not_implemented_v1"` → `all_warnings` no incluye mención de ellos |
| P5 | `EnrichedAuditPayload.forensic_report` == `ParallelGatherResult.sequential_context.forensic_report` |
| P6 | `brand_identity.retrieved: true` → `brand_identity.fallback_used: false` siempre |
| P7 | `build_duration_ms` siempre > 0 y presente en el output |
| P8 | Transacciones con `needs_human_review = true` nunca aparecen en `time_series.periodos` |
| P9 | `historical_context` nunca supera 1,500 tokens en el payload entregado a N11 |
| P10 | `EnrichedAuditPayload` siempre persistido en `audit_results` antes de retornar a N06 |
| P11 | `brand_identity` recuperada por SQL directo — nunca por búsqueda semántica |
| P12 | `ContextBuilderInput.temporalidad` no existe — se lee de `parallel_gather_result.temporalidad` |

---

## Archivos relacionados de este nodo
- `n06_orchestrator_adk.md` — `ParallelGatherResult` (input)
- `n05_ceo_orchestrator.md` — `OrchestratorRunPayload` (origen de `temporalidad`)
- `n11_consultor.md` — consumidor del `EnrichedAuditPayload`
- `mem_memory_layer.md` — `MemoryService.get_context()` + chunk `node_origin: "onboarding"`
- `db_schema.md` — `mepia_memory.source_audit_run_id` nullable
- `_glossary.md` — contratos `EnrichedAuditPayload`, `TimeSeriesRollup`, `BrandIdentityBlock`, `MemoryChunk`
