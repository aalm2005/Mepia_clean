# N06 — Orquestador ADK (Layer 2 — Scatter-Gather)

**Capa:** Parallel | **Anterior:** N05 CEO Orchestrator | **Siguiente:** N11 Consultor (Layer 3)
**Archivo de implementación:** `agents/parallel_orchestrator.py`
**Patrón:** Scatter-Gather — estructural puro, sin toma de decisiones autónoma
**Tecnología:** LangGraph `StateGraph` con nodos async / LCEL `RunnableParallel`

---

## Responsabilidad

Recibir el payload de Layer 1, despachar en paralelo a los nodos N07, N08 y N09,
manejar timeouts individuales por nodo, y consolidar todas las respuestas en un único
`ParallelGatherResult`. No interpreta resultados ni toma decisiones — solo scatter y gather.

```
N05 CEO Orchestrator
  │
  └─ POST /layer2/run
        │
        ├─── scatter ──────────────────────────────────────┐
        │    asyncio.gather (timeout independiente/nodo)   │
        │    ├─ N07 Conciliación Efectivo  (timeout: 15s)  │
        │    ├─ N08 Cumplimiento PLD       (timeout: 60s)  │
        │    └─ N09 Auditoría Gastos       (timeout: 20s)  │
        │                                                  │
        └─── gather ───────────────────────────────────────┘
             Consolidar → ParallelGatherResult
             Persistir en audit_results
             → N11 Consultor (Layer 3)
```

---

## Modelos Pydantic

### Input — `Layer2RunPayload`

Recibido desde N05. Contiene el contexto completo de Layer 1.

```python
class CalcResultItem(BaseModel):
    metric: str
    value: Optional[Decimal]
    unit: str
    status: Literal["ok", "warning", "critical", "incomplete_data", "unit_mismatch"]
    context: str


class AuditInsightItem(BaseModel):
    """Insight CEO-framed generado por N05. No hereda de AgentResult."""
    anomaly_ref:        str   = Field(description="ID de la anomalía base del ForensicReport")
    copilot_phrase:     str   = Field(description="Explicación con tono de CEO, arquetipo aplicado")
    recommended_action: str   = Field(description="Acción sugerida al dueño con plazo o frecuencia")
    context_weight:     Literal["reducido", "normal", "amplificado"]


class ForensicAnomalyItem(BaseModel):
    """Anomalía individual del ForensicReport de S4 — diagnóstico puro sin lenguaje CEO."""
    anomaly_id:        str
    type:              Literal["margin_leak", "source_discrepancy", "operational_ceiling", "cost_spike", "other"]
    description:       str
    severity:          Literal["low", "medium", "high"]
    quantified_impact: str
    data_points:       list[str]
    metric_origin:     str


class ForensicReport(BaseModel):
    """Output de S4 Forensic CFO — diagnóstico crudo y objetivo, sin arquetipos."""
    business_id:          str
    date:                 date
    risk_level:           Literal["low", "medium", "high"]
    anomalies:            list[ForensicAnomalyItem]   # campo canónico — 'diagnostics' es alias
    evidence_sources:     list[str]
    observed_causality:   Optional[dict] = None       # DailyContextTags adjunto sin interpretación
    generated_at:         datetime

    @property
    def diagnostics(self) -> list[ForensicAnomalyItem]:
        """Alias de compatibilidad — usar 'anomalies' en código nuevo."""
        return self.anomalies

    @property
    def severity_score(self) -> float:
        """Score numérico: high=1.0, medium=0.5, low=0.1. Promedio del reporte."""
        mapping = {"high": 1.0, "medium": 0.5, "low": 0.1}
        if not self.anomalies:
            return 0.0
        return sum(mapping[a.severity] for a in self.anomalies) / len(self.anomalies)


class ContextTags(BaseModel):
    """Tipado estricto — evita KeyError en nodos paralelos."""
    clima:    Optional[Literal["lluvia", "calor", "frio"]]              = None
    equipo:   Optional[Literal["falla_maquina", "mantenimiento"]]       = None
    evento:   Optional[Literal["festivo", "obra_vial", "promocion"]]    = None
    personal: Optional[Literal["falta_staff", "capacitacion"]]          = None
    otros:    Optional[str]                                              = None


class SequentialContext(BaseModel):
    """Resultados completos de Layer 1 — pasados como contexto a cada nodo paralelo."""
    business_id:     str
    active_metrics:  list[str]
    calc_results:    list[CalcResultItem]
    forensic_report: ForensicReport      = Field(description="Diagnóstico crudo y objetivo generado por S4")
    insights:        list[AuditInsightItem] = Field(description="Insights adaptados por N05 con arquetipo CEO")
    context_tags:    ContextTags            # tipado estricto, nunca dict libre


class NodeTimeouts(BaseModel):
    """Timeouts independientes por nodo en segundos."""
    n07_conciliacion: int = Field(default=15, ge=5, le=60)
    n08_pld:          int = Field(default=60, ge=5, le=120)
    n09_gastos:       int = Field(default=20, ge=5, le=60)


class Layer2RunPayload(BaseModel):
    layer2_run_id:    UUID
    sequential_run_id: UUID                 # run_id de N05 — trazabilidad
    source_s3_result_id: Optional[UUID]     # audit_results.id de S3; null para legacy/aislado
    business_id:      UUID
    date:             date
    archetype:        Literal["Operative Genius", "Product Purist", "Growth Hacker"]
    temporalidad:     Literal["short", "medium", "long"]  # propagado desde OrchestratorRunPayload
    sequential_context: SequentialContext
    node_timeouts:    NodeTimeouts = NodeTimeouts()
```

---

### Output por nodo — `NodeResult`

Cada nodo paralelo (N07, N08, N09) retorna este contrato.

```python
class NodeResult(BaseModel):
    node_id:      Literal["N07", "N08", "N09"]
    node_name:    Literal["conciliacion", "pld", "gastos"]
    status:       Literal["success", "timeout", "error"]
    result:       Optional[AgentResult]     # None si status != "success"
    warnings:     list[str] = []            # señales para Layer 3
    error_detail: Optional[str] = None      # mensaje si status != "success"
    duration_ms:  int                       # tiempo real de ejecución
```

---

### Output consolidado — `ParallelGatherResult`

Output final del orquestador. Entrada para Layer 3. Se persiste en `audit_results`.

```python
class GatherSummary(BaseModel):
    total_nodes:  int           # siempre 3
    succeeded:    int
    timed_out:    int
    failed:       int
    all_warnings: list[str]     # warnings agregados de todos los nodos con success


class ParallelGatherResult(BaseModel):
    layer2_run_id:     UUID
    sequential_run_id: UUID
    source_s3_result_id: Optional[UUID]
    business_id:       UUID
    date:              date
    archetype:         Literal["Operative Genius", "Product Purist", "Growth Hacker"]
    temporalidad:      Literal["short", "medium", "long"]  # propagado para N10
    node_results:      list[NodeResult]     # siempre 3 elementos
    summary:           GatherSummary
    gather_status:     Literal[
        "complete",   # los 3 nodos respondieron con success
        "partial",    # ≥ 1 nodo con timeout/error, ≥ 1 con success
        "failed"      # los 3 nodos fallaron — no hay resultados útiles
    ]
    completed_at:      datetime
```

---

## Flujo de ejecución — Scatter-Gather

### Fase 1 — Guard de idempotencia

Antes de ejecutar cualquier nodo, verificar si ya existe un `ParallelGatherResult`
persistido para `layer2_run_id`:

```
IF audit_results contiene layer2_run_id → retornar resultado existente (HTTP 200)
ELSE → continuar con scatter
```

Esto previene ejecuciones duplicadas si N05 reintenta por timeout de red.

### Fase 2 — Scatter (ejecución paralela)

Cada nodo se ejecuta con su propio timeout independiente usando `time.monotonic()`
para medir duración (no `asyncio.get_event_loop().time()` — deprecado en Python 3.10+).

```
asyncio.gather(
    run_with_timeout(N07, timeout=node_timeouts.n07_conciliacion),
    run_with_timeout(N08, timeout=node_timeouts.n08_pld),
    run_with_timeout(N09, timeout=node_timeouts.n09_gastos),
    return_exceptions=False   # cada nodo maneja sus propias excepciones internamente
)
```

El `scatter_node` completo está envuelto en un `try/except` de nivel superior.
Si el propio `asyncio.gather` falla (OOM, loop cerrado, error de serialización),
se retorna un `ParallelGatherResult` con los 3 nodos en `status: "error"` y
`gather_status: "failed"` — nunca estado indefinido.

### Fase 3 — Gather (consolidación)

```
succeeded = count(results where status == "success")
timed_out = count(results where status == "timeout")
failed    = count(results where status == "error")

gather_status:
  succeeded == 3 → "complete"
  succeeded == 0 → "failed"
  else           → "partial"
```

### Fase 4 — Persistencia

`ParallelGatherResult` se persiste en `audit_results` **antes** de retornar la respuesta
y **antes** de disparar Layer 3. Si Layer 3 falla, los resultados de Layer 2 son recuperables
sin re-ejecutar el pipeline.

---

## Tolerancia a fallos

| Escenario                              | Comportamiento                                                        |
|----------------------------------------|-----------------------------------------------------------------------|
| 1 nodo timeout                         | `partial` — los otros 2 resultados se preservan                       |
| 1 nodo error                           | `partial` — `error_detail` en el `NodeResult` correspondiente         |
| 2 nodos timeout/error                  | `partial` — Layer 3 recibe el 1 resultado disponible                  |
| 3 nodos timeout/error                  | `failed` — HTTP 503, Layer 3 no se ejecuta                            |
| `asyncio.gather` falla a nivel global  | `failed` — todos los NodeResult con `status: "error"`, nunca indefinido |
| N05 reintenta con mismo `layer2_run_id`| Idempotente — retorna resultado existente sin re-ejecutar             |
| Timeout asimétrico                     | Cada nodo tiene su propio `wait_for` — un nodo lento no bloquea a los demás |

**Regla de oro: un nodo lento, caído o duplicado nunca bloquea ni corrompe a los demás.**

### Circuit breaker (degradación controlada)

Si un nodo específico falla en ≥ 3 ejecuciones consecutivas para el mismo `business_id`
en el mismo día, el orquestador lo marca como `status: "error"` directamente sin intentar
ejecutarlo, con `error_detail: "circuit_open — node degraded"`. Esto evita acumular
timeouts innecesarios en runs subsecuentes.

El estado del circuit breaker se evalúa consultando `audit_results` para
`business_id + date + node_id` antes del scatter.

---

## Contrato con N05 — manejo de `gather_status: "failed"`

Cuando N06 retorna HTTP 503 (`gather_status: "failed"`), N05 debe:

1. Actualizar `pipeline_status` a `"failed"` en su `OrchestratorResult`
2. Persistir el error en `audit_results` con `module: "N06"` y `raw_result: error_detail`
3. **No reintentar automáticamente** — retornar HTTP 503 al cliente con detalle del fallo
4. El cliente puede reintentar vía `POST /orchestrator/run` en una nueva sesión

Este contrato está especificado en ambos lados: N05 no reintenta, N06 es idempotente.

---

## Endpoint REST

### `POST /layer2/run`

Llamado internamente por N05. También puede ser invocado directamente para testing.

**Request body:** `Layer2RunPayload`

**Response 200 — complete:**
```json
{
  "layer2_run_id": "uuid-v4",
  "gather_status": "complete",
  "summary": {
    "total_nodes": 3,
    "succeeded": 3,
    "timed_out": 0,
    "failed": 0,
    "all_warnings": ["Varianza de caja > 5%"]
  },
  "node_results": [
    { "node_id": "N07", "node_name": "conciliacion", "status": "success", "duration_ms": 1240, "warnings": ["Varianza de caja > 5%"] },
    { "node_id": "N08", "node_name": "pld",          "status": "success", "duration_ms": 8300, "warnings": [] },
    { "node_id": "N09", "node_name": "gastos",        "status": "success", "duration_ms": 980,  "warnings": [] }
  ],
  "completed_at": "2024-01-15T22:11:45Z"
}
```

**Response 200 — partial:**
```json
{
  "layer2_run_id": "uuid-v4",
  "gather_status": "partial",
  "summary": { "total_nodes": 3, "succeeded": 2, "timed_out": 1, "failed": 0, "all_warnings": [] },
  "node_results": [
    { "node_id": "N07", "node_name": "conciliacion", "status": "success",  "duration_ms": 1240 },
    { "node_id": "N08", "node_name": "pld",          "status": "timeout",  "duration_ms": 60000, "error_detail": "Timeout after 60s" },
    { "node_id": "N09", "node_name": "gastos",        "status": "success",  "duration_ms": 980 }
  ],
  "completed_at": "2024-01-15T22:12:05Z"
}
```

**Códigos de error:**

| HTTP | Condición                                                        |
|------|------------------------------------------------------------------|
| 404  | `business_id` no existe                                          |
| 409  | `layer2_run_id` ya existe y está en ejecución activa             |
| 422  | `Layer2RunPayload` inválido                                      |
| 503  | `gather_status: "failed"` — los 3 nodos fallaron o error global  |

---

### `GET /layer2/status/{layer2_run_id}`

Consulta el estado de una ejecución de Layer 2 en curso o completada.
Útil para polling cuando N08 (PLD) puede tardar hasta 60s.

**Response 200 — en curso:**
```json
{
  "layer2_run_id": "uuid-v4",
  "gather_status": "running",
  "nodes_completed": 2,
  "nodes_pending": ["N08"],
  "started_at": "2024-01-15T22:11:00Z",
  "completed_at": null
}
```

**Response 200 — completado:**
```json
{
  "layer2_run_id": "uuid-v4",
  "gather_status": "complete" | "partial" | "failed",
  "nodes_completed": 3,
  "nodes_pending": [],
  "started_at": "2024-01-15T22:11:00Z",
  "completed_at": "2024-01-15T22:11:45Z"
}
```

**Códigos de error:**

| HTTP | Condición                          |
|------|------------------------------------|
| 404  | `layer2_run_id` no existe          |

---

### `POST /layer2/circuit-reset`

Resetea manualmente el circuit breaker de un nodo para un negocio y fecha.
Útil cuando el nodo se recuperó y se quiere permitir nuevos intentos.

**Request body:**
```python
class CircuitResetPayload(BaseModel):
    business_id: UUID
    date: date
    node_id: Literal["N07", "N08", "N09"]
    reset_by: UUID    # quién autoriza el reset — trazabilidad
```

**Response 200:**
```json
{
  "node_id": "N08",
  "business_id": "uuid-v4",
  "date": "2024-01-15",
  "circuit_status": "closed",
  "reset_by": "user-uuid",
  "reset_at": "2024-01-15T23:00:00Z"
}
```

**Códigos de error:**

| HTTP | Condición                                              |
|------|--------------------------------------------------------|
| 404  | `business_id` no existe                                |
| 422  | `node_id` inválido                                     |
| 409  | El nodo no está en `circuit_open` — reset innecesario  |

---

## Persistencia

`ParallelGatherResult` se persiste en `audit_results` antes de retornar al cliente:

| Campo           | Valor                                                    |
|-----------------|----------------------------------------------------------|
| `id`            | `layer2_run_id`                                          |
| `source_s3_result_id` | ID de la fila S3 raíz, propagado sin cambios      |
| `business_id`   | FK → businesses                                          |
| `date`          | Fecha auditada                                           |
| `module`        | `"N06_gather"`                                           |
| `raw_result`    | JSON serializado de `ParallelGatherResult`               |
| `copilot_phrase`| `null` — N06 no genera frases, eso es responsabilidad de Layer 3 |

Esto garantiza que si Layer 3 falla, los resultados de Layer 2 son recuperables.

---

## Acceptance Criteria

- WHEN los 3 nodos responden exitosamente → `gather_status: "complete"`, `summary.succeeded: 3`
- WHEN 1 nodo hace timeout → `gather_status: "partial"`, los otros 2 resultados presentes
- WHEN 3 nodos fallan → `gather_status: "failed"`, HTTP 503
- WHEN `asyncio.gather` falla a nivel global → `gather_status: "failed"`, nunca estado indefinido
- WHEN mismo `layer2_run_id` enviado dos veces → retornar resultado existente, no re-ejecutar
- WHEN nodo en circuit open → `status: "error"`, `error_detail: "circuit_open"`, sin ejecutar
- WHEN `node_timeouts` no enviado → usar defaults (N07: 15s, N08: 60s, N09: 20s)
- WHEN nodo retorna `warnings` → agregados en `summary.all_warnings`
- WHEN `gather_status: "partial"` → Layer 3 recibe `ParallelGatherResult` con nodos fallidos marcados
- WHEN `gather_status: "failed"` → N05 no reintenta, retorna HTTP 503 al cliente
- WHEN `gather_status` cualquiera → `ParallelGatherResult` persistido en `audit_results` antes de retornar
- WHEN `source_s3_result_id` está presente → el resultado y la fila N06
  conservan exactamente el mismo UUID
- WHEN `GET /layer2/status/{layer2_run_id}` → retornar estado actual, nunca 404 si el run existe
- WHEN `POST /layer2/circuit-reset` con nodo no en `circuit_open` → HTTP 409
- WHEN `POST /layer2/circuit-reset` exitoso → `circuit_breaker_state.circuit_status: "closed"`, `consecutive_failures: 0`

---

## Correctness Properties (PBT)

| ID | Propiedad |
|----|-----------|
| P1 | `node_results` siempre tiene exactamente 3 elementos en `ParallelGatherResult` |
| P2 | `summary.succeeded + summary.timed_out + summary.failed == 3` siempre |
| P3 | `gather_status: "complete"` ↔ `summary.succeeded == 3` |
| P4 | `gather_status: "failed"` ↔ `summary.succeeded == 0` |
| P5 | Timeout de nodo X no afecta `duration_ms` de nodos Y y Z |
| P6 | `all_warnings` == unión de `warnings` de todos los nodos con `status: "success"` |
| P7 | `layer2_run_id` y `sequential_run_id` siempre no nulos en `ParallelGatherResult` |
| P8 | Mismo `layer2_run_id` enviado N veces → exactamente 1 registro en `audit_results` |
| P9 | Error global en scatter → `ParallelGatherResult` retornado con `gather_status: "failed"`, nunca excepción no manejada |
| P10| `ContextTags` con campo fuera de enum → HTTP 422 en validación Pydantic, scatter no ejecutado |
| P11| `GET /layer2/status/{layer2_run_id}` existente → siempre HTTP 200, nunca 404 |
| P12| `POST /layer2/circuit-reset` exitoso → `consecutive_failures == 0` en `circuit_breaker_state` |
