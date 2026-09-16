# Layer 3 — Orquestador del StateGraph (layer3_graph.py)

**Capa:** Layer 3 | **Disparado por:** `POST /api/audit/layer3/run`
**Archivo de implementación:** `agents/layer3_graph.py`
**Tecnología:** LangGraph `StateGraph`
**Patrón:** Loop con conditional edge (Actor-Critic)

---

## Responsabilidad

`layer3_graph.py` es el único lugar donde se define y compila el grafo LangGraph
de Layer 3. Ningún otro archivo puede instanciar `StateGraph` para este pipeline.

**Regla de desacoplamiento:** `api/main.py` y cualquier endpoint REST están
**prohibidos** de definir lógica LangGraph directamente. Solo importan el grafo
compilado y llaman `.invoke()` o `.stream()`.

```python
# ✅ Correcto — en api/main.py
from agents.layer3_graph import layer3_app
result = await layer3_app.ainvoke(initial_state)

# ❌ Prohibido — en api/main.py
from langgraph.graph import StateGraph
graph = StateGraph(...)  # NUNCA aquí
```

---

## Flujo del Grafo

```
START
  │
  ▼
[N10 — Context Builder]     Python puro, determinista
  │                         Construye EnrichedAuditPayload
  ▼
[N11 — Consultor]           LLM: claude-3-5-sonnet (fallback: gpt-4o)
  │                         Genera DraftReport
  ▼
[N13 — Revisor]             LLM: gpt-4o, temperature=0
  │                         Evalúa DraftReport → CriticVerdict
  │
  ├─── aprobado / cortafuegos ──────────────────────────────┐
  │    (draft_status: "approved" | "approved_with_warning") │
  │                                                         ▼
  │                                               [N14 — Informe Final]
  │                                               Python puro
  │                                               Persiste FinalReport
  │                                                         │
  │                                                         ▼
  │                                                        END
  │
  └─── rechazado ──────────────────────────────────────────┐
       (draft_status: "rejected",                          │
        intentos_critico < 2)                              │
                                                           ▼
                                               [N11 — Consultor] (reintento)
                                               Lee feedback_critico del estado
                                               Genera nuevo DraftReport corregido
```

---

## Estructura del Archivo `agents/layer3_graph.py`

```python
from langgraph.graph import StateGraph, END

from agents.layer3_state import Layer3State
from agents.context_builder import n10_context_builder_node
from agents.core_auditor import n11_consultor_node
from agents.n13_revisor import make_n13_node, n13_conditional_edge
from agents.n14_informe_final import n14_informe_final_node
from utils.memory_service import MemoryService


def build_layer3_graph(memory_service: MemoryService) -> ...:
    """
    Construye y compila el grafo LangGraph de Layer 3.

    Args:
        memory_service: Instancia de MemoryService inyectada por el endpoint.
                        N13 la usa para store_memory() al aprobar.

    Returns:
        Grafo compilado listo para .invoke() o .stream().
    """
    graph = StateGraph(Layer3State)

    # ── Registrar nodos ───────────────────────────────────────────────────────
    graph.add_node("n10_context_builder", n10_context_builder_node)
    graph.add_node("n11_consultor",       n11_consultor_node)
    graph.add_node("n13_revisor",         make_n13_node(memory_service))
    graph.add_node("n14_informe_final",   n14_informe_final_node)

    # ── Flujo secuencial ──────────────────────────────────────────────────────
    graph.set_entry_point("n10_context_builder")
    graph.add_edge("n10_context_builder", "n11_consultor")
    graph.add_edge("n11_consultor",       "n13_revisor")

    # ── Conditional edge post-N13 (loop o avance) ─────────────────────────────
    # n13_conditional_edge retorna:
    #   "n11_consultor"    → rechazado, reintento (intentos_critico < 2)
    #   "n14_informe_final"→ aprobado o cortafuegos (intentos_critico >= 2)
    graph.add_conditional_edges(
        "n13_revisor",
        n13_conditional_edge,
        {
            "n11_consultor":    "n11_consultor",
            "n14_informe_final": "n14_informe_final",
        },
    )

    graph.add_edge("n14_informe_final", END)

    return graph.compile()


# Instancia exportada — el endpoint importa esto directamente.
# MemoryService se inyecta en tiempo de startup del servidor.
# Ver: api/main.py → startup_event → layer3_app = build_layer3_graph(memory_service)
```

---

## Estado Inicial — Construcción en el Endpoint

El endpoint `POST /api/audit/layer3/run` es el responsable de construir el
`Layer3State` inicial antes de llamar `.invoke()`. Soporta dos modos:

**Modo normal** (`audit_run_id` presente): consulta `audit_results` para reconstruir
el contexto de Layer 2, incluido `source_s3_result_id`. Verifica que el negocio
tenga onboarding completo (HTTP 412 si no).

**Modo aislado** (`audit_run_id` ausente): usa `business_id`, `date` y `archetype`
del body directamente. Genera `layer2_run_id` y `sequential_run_id` con prefijo
`isolated_` si no se proporcionan y deja `source_s3_result_id = None`. Útil para
testing y debugging de Layer 3 en aislamiento.

```python
# Estructura del estado inicial (construido por el endpoint)
initial_state: Layer3State = {
    # Trazabilidad — leída de audit_results (modo normal) o del body (modo aislado)
    "layer3_run_id":     str(uuid4()),
    "layer2_run_id":     layer2_run_id,        # puede tener prefijo "isolated_"
    "sequential_run_id": sequential_run_id,    # puede tener prefijo "isolated_"
    "source_s3_result_id": source_s3_result_id, # null solo en legacy/aislado
    "business_id":       business_id,
    "date":              date_str,
    "archetype":         archetype,

    # Payload de datos — EnrichedAuditPayload serializado (construido por N10)
    # Se pasa vacío; N10 lo construye como primer paso del grafo
    "enriched_payload": {},

    # Borrador — None hasta que N11 lo genere
    "draft_report": None,

    # Control del loop — valores iniciales
    "intentos_critico":    0,
    "feedback_critico":    None,
    "historial_feedback":  [],
    "tipos_falla_critico": [],
    "draft_status":        "pending",
    "audit_results":       [],

    # Output terminal — None hasta que N14 ejecute
    "final_response": None,
}
```

> **Prerequisito de onboarding:** Antes de construir el estado inicial, el endpoint
> verifica que `mepia_memory` tenga un chunk `node_origin: "onboarding"` para el
> `business_id`. Si no existe → HTTP 412 con `error: "onboarding_required"`.
> Ver: `n10_onboarding_identidad.md` y `api_layer3.md`.

---

## Reglas de Desacoplamiento

| Regla | Descripción |
|-------|-------------|
| **Grafo único** | Solo `layer3_graph.py` instancia `StateGraph(Layer3State)` |
| **Sin LangGraph en API** | `api/main.py` solo importa `layer3_app` y llama `.ainvoke()` |
| **MemoryService inyectado** | El grafo recibe `MemoryService` en `build_layer3_graph()`, no lo instancia internamente |
| **Nodos independientes** | Cada nodo (`n10`, `n11`, `n13`, `n14`) puede testearse sin el grafo completo |
| **Estado inmutable en trazabilidad** | Los campos de trazabilidad (`layer3_run_id`, `business_id`, etc.) solo los escribe el endpoint — ningún nodo los modifica |

---

## Acceptance Criteria

- WHEN `build_layer3_graph(memory_service)` es llamado → retorna grafo compilado sin errores
- WHEN `draft_status == "rejected"` y `intentos_critico < 2` → grafo regresa a N11
- WHEN `draft_status == "approved"` → grafo avanza a N14 y termina en END
- WHEN `draft_status == "approved_with_warning"` → grafo avanza a N14 y termina en END
- WHEN N11 es reejecutado → lee `feedback_critico` del estado para corregir el borrador
- WHEN `api/main.py` importa `layer3_app` → no hay instanciación de `StateGraph` en ese archivo
- WHEN el grafo completa → `Layer3State.draft_status` es `"approved"` o `"approved_with_warning"` — nunca `"pending"` o `"rejected"`
- WHEN modo aislado → `layer2_run_id` y `sequential_run_id` tienen prefijo `"isolated_"` si no se proporcionaron
- WHEN negocio sin onboarding → HTTP 412 antes de invocar el grafo, nunca llega a N10

---

## Correctness Properties (PBT)

| ID | Propiedad |
|----|-----------|
| P1 | El grafo siempre termina — `intentos_critico >= 2` garantiza salida del loop |
| P2 | `intentos_critico` nunca supera `MAX_INTENTOS (2)` al llegar a N14 |
| P3 | `draft_status` al llegar a END es siempre `"approved"` o `"approved_with_warning"` |
| P4 | `enriched_payload` nunca vacío cuando N11 ejecuta (N10 lo construye primero) |
| P5 | `layer3_app` es el único grafo compilado exportado desde `layer3_graph.py` |
| P6 | Modo aislado: `layer2_run_id` contiene prefijo `"isolated_"` si no fue proporcionado |
| P7 | Negocio sin onboarding → HTTP 412, `layer3_app.ainvoke()` nunca llamado |

---

## Archivos relacionados
- `agents/layer3_state.py` — `Layer3State` TypedDict
- `agents/context_builder.py` — nodo N10
- `agents/core_auditor.py` — nodo N11
- `agents/n13_revisor.py` — nodo N13 + `n13_conditional_edge`
- `agents/n14_informe_final.py` — nodo N14
- `api_layer3.md` — endpoint disparador `POST /api/audit/layer3/run`
- `utils/memory_service.py` — inyectado en `build_layer3_graph()`
