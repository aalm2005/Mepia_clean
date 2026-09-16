# API Layer 3 — Endpoint Disparador

**Archivo de implementación:** `api/main.py`
**Grafo invocado:** `agents/layer3_graph.py` → `layer3_app`
**Patrón:** Endpoint REST asíncrono — construye estado inicial e invoca el grafo

---

## Responsabilidad

Este endpoint es el único punto de entrada externo para ejecutar el pipeline de
Layer 3 (generación del informe final). Recibe el `audit_run_id` del frontend,
consulta la base de datos para reconstruir el contexto de Layer 2, construye el
`Layer3State` inicial y dispara el grafo compilado.

**Layer 3 NO es llamado por N06 internamente.** Está desacoplado y se dispara
de forma explícita desde el frontend o desde un worker asíncrono.

---

## Endpoint

### `POST /api/audit/layer3/run`

**Request body — `Layer3RunPayload`:**

```python
class Layer3RunPayload(BaseModel):
    audit_run_id: str              # UUID del run de Layer 2 (layer2_run_id)
                                   # El endpoint lo usa para recuperar el contexto de Supabase

    # ── Parámetros opcionales para ejecución aislada ──────────────────────────
    # Cuando se omiten, el backend genera UUIDs temporales con prefijo "isolated_"
    # para inicializar Layer3State sin depender del orquestador N05.
    # Útil para: testing de Layer 3 en aislamiento, demos, debugging de N11/N13.
    layer2_run_id: Optional[str] = None       # si None → genera "isolated_{uuid4()}"
    sequential_run_id: Optional[str] = None   # si None → genera "isolated_{uuid4()}"
```

**Modo normal (con `audit_run_id`):**
El endpoint consulta `audit_results` para reconstruir el contexto completo de Layer 2.
`layer2_run_id` y `sequential_run_id` se ignoran si `audit_run_id` está presente;
`source_s3_result_id` se recupera de la fila N06.

**Modo aislado (sin `audit_run_id`, con IDs opcionales o sin ellos):**
El endpoint no consulta `audit_results`. Usa los IDs proporcionados o genera temporales.
`business_id`, `date` y `archetype` deben incluirse en el body en este modo. No
se inventa linaje: `source_s3_result_id` queda en `None`.

```python
class Layer3IsolatedPayload(Layer3RunPayload):
    """Extensión para ejecución aislada — requerida cuando audit_run_id es None."""
    business_id: str
    date: str                      # ISO-8601 YYYY-MM-DD
    archetype: str                 # "Operative Genius" | "Product Purist" | "Growth Hacker"
    enriched_payload: dict = {}    # EnrichedAuditPayload pre-construido (opcional)
```

**Response 202 — Aceptado:**
```json
{
  "layer3_run_id":    "uuid-v4",
  "audit_run_id":     "uuid-v4 | null",
  "layer2_run_id":    "uuid-v4 | isolated_uuid-v4",
  "sequential_run_id":"uuid-v4 | isolated_uuid-v4",
  "execution_mode":   "normal | isolated",
  "status":           "running",
  "started_at":       "2024-01-15T22:20:00Z"
}
```

> El endpoint responde 202 inmediatamente. El grafo corre de forma asíncrona.
> El frontend hace polling a `GET /api/audit/layer3/status/{layer3_run_id}`
> para conocer el resultado.

**Códigos de error:**

| HTTP | Condición |
|------|-----------|
| 404  | `audit_run_id` proporcionado pero no existe en `audit_results` |
| 409  | Ya existe un `layer3_run_id` para este `audit_run_id` — idempotencia (solo modo normal) |
| 422  | `audit_run_id` inválido (no es UUID) |
| 422  | Modo aislado sin `business_id`, `date` o `archetype` |
| 503  | Supabase no disponible al construir el estado inicial (solo modo normal) |

---

### `GET /api/audit/layer3/status/{layer3_run_id}`

Polling del frontend para conocer el estado del grafo en ejecución.

**Response 200 — En curso:**
```json
{
  "layer3_run_id": "uuid-v4",
  "status":        "running",
  "current_node":  "n11_consultor",
  "intentos_critico": 1,
  "started_at":    "2024-01-15T22:20:00Z",
  "completed_at":  null
}
```

**Response 200 — Completado:**
```json
{
  "layer3_run_id":  "uuid-v4",
  "status":         "completed",
  "draft_status":   "approved" | "approved_with_warning",
  "current_node":   "END",
  "intentos_critico": 0,
  "started_at":     "2024-01-15T22:20:00Z",
  "completed_at":   "2024-01-15T22:22:15Z"
}
```

**Response 200 — Fallido:**
```json
{
  "layer3_run_id": "uuid-v4",
  "status":        "failed",
  "error_detail":  "N11 LLM timeout after 30s",
  "started_at":    "2024-01-15T22:20:00Z",
  "completed_at":  "2024-01-15T22:20:31Z"
}
```

**Códigos de error:**

| HTTP | Condición |
|------|-----------|
| 404  | `layer3_run_id` no existe |

---

### `GET /api/audit/layer3/result/{layer3_run_id}`

Recupera el `FinalReport` completo una vez que el grafo completó.

**Response 200:**
```json
{
  "layer3_run_id":           "uuid-v4",
  "business_id":             "uuid-v4",
  "date":                    "2024-01-15",
  "archetype":               "Operative Genius",
  "executive_summary":       "string",
  "operational_narrative_md":"string (Markdown)",
  "pragmatic_actions": [
    { "action": "string", "priority": "immediate", "owner": "dueño" }
  ],
  "draft_status":            "approved",
  "model_used":              "claude-3-5-sonnet-20241022",
  "intentos_critico":        0,
  "quality_warnings":        [],
  "finalized_at":            "2024-01-15T22:22:15Z"
}
```

**Códigos de error:**

| HTTP | Condición |
|------|-----------|
| 404  | `layer3_run_id` no existe |
| 409  | El grafo aún no completó — usar `/status` primero |

---

## Construcción del Estado Inicial

El endpoint tiene dos rutas de construcción según el modo de ejecución:

```python
async def build_initial_state(payload: Layer3RunPayload | Layer3IsolatedPayload, db) -> Layer3State:
    """
    Construye el Layer3State inicial.

    Modo normal (audit_run_id presente):
      1. Consulta audit_results WHERE run_id = audit_run_id AND node_id = 'N06'
      2. Extrae layer2_run_id, sequential_run_id, source_s3_result_id,
         business_id, date, archetype
      3. Genera nuevo layer3_run_id

    Modo aislado (audit_run_id ausente):
      1. Usa layer2_run_id y sequential_run_id del payload, o genera "isolated_{uuid4()}"
      2. Usa business_id, date, archetype del payload directamente
      3. Genera nuevo layer3_run_id
      4. No consulta Supabase — no lanza 503 por DB no disponible
    """
    layer3_run_id = str(uuid4())

    if payload.audit_run_id:
        # ── Modo normal ───────────────────────────────────────────────────────
        row = await db.fetchone(
            "SELECT * FROM audit_results WHERE run_id = :run_id AND node_id = 'N06'",
            {"run_id": payload.audit_run_id}
        )
        if not row:
            raise HTTPException(status_code=404, detail="audit_run_id no encontrado")

        layer2_run_id    = str(row["run_id"])
        sequential_run_id = str(row.get("sequential_run_id", ""))
        source_s3_result_id = row.get("source_s3_result_id")
        business_id      = str(row["business_id"])
        date             = str(row["date"])
        archetype        = row["archetype"]
        enriched_payload = {}
        execution_mode   = "normal"

    else:
        # ── Modo aislado ──────────────────────────────────────────────────────
        layer2_run_id    = payload.layer2_run_id or f"isolated_{uuid4()}"
        sequential_run_id = payload.sequential_run_id or f"isolated_{uuid4()}"
        source_s3_result_id = None
        business_id      = payload.business_id
        date             = payload.date
        archetype        = payload.archetype
        enriched_payload = getattr(payload, "enriched_payload", {})
        execution_mode   = "isolated"

    return {
        "layer3_run_id":     layer3_run_id,
        "layer2_run_id":     layer2_run_id,
        "sequential_run_id": sequential_run_id,
        "source_s3_result_id": source_s3_result_id,
        "business_id":       business_id,
        "date":              date,
        "archetype":         archetype,
        "enriched_payload":  enriched_payload,
        "draft_report":      None,
        "intentos_critico":  0,
        "feedback_critico":  None,
        "historial_feedback":  [],
        "tipos_falla_critico": [],
        "draft_status":      "pending",
        "audit_results":     [],
        "_execution_mode":   execution_mode,   # campo de trazabilidad, no parte de Layer3State
    }
```

---

## Invocación del Grafo

```python
# En api/main.py — startup
from agents.layer3_graph import build_layer3_graph
from utils.memory_service import MemoryService

# MemoryService instanciado una vez al arrancar el servidor
memory_service = MemoryService(supabase_client=supabase)
layer3_app = build_layer3_graph(memory_service)

# En el endpoint POST /api/audit/layer3/run
@app.post("/api/audit/layer3/run", status_code=202)
async def run_layer3(payload: Layer3RunPayload, background_tasks: BackgroundTasks):
    initial_state = await build_initial_state(payload.audit_run_id, db)

    # El grafo corre en background — el endpoint responde 202 inmediatamente
    background_tasks.add_task(layer3_app.ainvoke, initial_state)

    return {
        "layer3_run_id": initial_state["layer3_run_id"],
        "audit_run_id":  payload.audit_run_id,
        "status":        "running",
        "started_at":    datetime.now(timezone.utc).isoformat(),
    }
```

---

## Acceptance Criteria

- WHEN `audit_run_id` válido → endpoint responde 202 e inicia el grafo en background (`execution_mode: "normal"`)
- WHEN `audit_run_id` omitido + `business_id`/`date`/`archetype` presentes → modo aislado, `layer2_run_id` y `sequential_run_id` generados con prefijo `isolated_`
- WHEN `audit_run_id` omitido + `layer2_run_id` proporcionado → usar el proporcionado, no generar temporal
- WHEN modo aislado sin `business_id` → HTTP 422
- WHEN mismo `audit_run_id` enviado dos veces (modo normal) → HTTP 409, no re-ejecutar el grafo
- WHEN `audit_run_id` no existe → HTTP 404 antes de invocar el grafo
- WHEN grafo completa → `GET /status` retorna `status: "completed"` con `draft_status`
- WHEN grafo falla → `GET /status` retorna `status: "failed"` con `error_detail`
- WHEN `GET /result` antes de completar → HTTP 409
- WHEN `layer3_app` importado en `api/main.py` → no hay `StateGraph` instanciado en ese archivo
- WHEN modo aislado → `execution_mode: "isolated"` en la respuesta 202

---

## Archivos relacionados
- `agents/layer3_graph.py` — grafo compilado `layer3_app`
- `agents/layer3_state.py` — `Layer3State` TypedDict
- `layer3_graph.md` — arquitectura del grafo
- `n14_informe_final.md` — nodo terminal que produce el `FinalReport`
