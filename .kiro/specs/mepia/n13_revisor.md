# N13 — Revisor de Calidad (Critic & Enforcer)

**Capa:** Layer 3 — Nodo 3 | **Anterior:** N11 Consultor | **Siguiente:** N14 Informe Final
**Archivo de implementación:** `agents/n13_revisor.py`
**Tipo:** LLM Critic — Structured Output, patrón Actor-Critic
**Archivos relacionados:** `n11_consultor.md`, `mem_memory_layer.md`, `_glossary.md`

> **V1:** N12 (Phrase Expander) skipped. Flujo directo: N11 → N13 → N14.

## Decisión de LLM

| Campo | Valor |
|-------|-------|
| **Modelo** | `gpt-4o` |
| **Proveedor** | OpenAI |
| **Temperatura** | `0` — determinismo máximo para verificación matemática |
| **Justificación** | Verificación matemática estricta y structured output (`CriticVerdict`). Requiere extraer cifras del texto narrativo y cruzarlas contra datos crudos con precisión. `gpt-4o` con `temperature=0` es el más confiable para este tipo de razonamiento analítico-verificador. Confirmado como decisión final. |
| **Variable de entorno requerida** | `OPENAI_API_KEY` |
| **Fallback** | No aplica — si el LLM falla, el nodo retorna `approved_with_warning` directamente (ver lógica de cortafuegos en `agents/n13_revisor.py`). |

---

## Input / Output

**Input:** `Layer3State` con `draft_report` (DraftReport de N11) + `enriched_payload`
**Output:** Actualización de estado: `draft_status`, `feedback_critico`, `intentos_critico`

---

## Responsabilidad

Actúa como "unit test cognitivo" del pipeline. Evalúa el `DraftReport` de N11
contra los datos crudos del `EnrichedAuditPayload` en dos dimensiones:

1. **Test Matemático** — detecta cifras inventadas o incorrectas (alucinaciones)
2. **Test de Identidad** — detecta lenguaje corporativo / pérdida del tono de piso

---

## Contrato de Salida Estructurada — `CriticVerdict`

```python
class TipoFalla(str, Enum):
    ALUCINACION_MATEMATICA = "ALUCINACION_MATEMATICA"
    DESVIACION_IDENTIDAD   = "DESVIACION_IDENTIDAD"
    NINGUNA                = "NINGUNA"

class CriticVerdict(BaseModel):
    aprobado: bool
    tipos_falla: List[TipoFalla]     # lista — captura múltiples fallas simultáneas
    warning_especifico: str | None   # feedback para N11 si falla — describe TODAS las fallas
    insight_para_memoria: str | None # resumen 2 líneas si aprueba → mepia_memory
```

---

## Estado del Grafo — `Layer3State` (campos de control)

```python
intentos_critico: int          # default 0 — incrementado por N13 en cada rechazo
feedback_critico: str | None   # último warning — default None
historial_feedback: List[str]  # acumulado de todos los warnings — default []
tipos_falla_critico: List[str] # fallas del último veredicto — default []
draft_status: str              # "pending" | "approved" | "approved_with_warning" | "rejected"
audit_results: List[Dict]      # veredictos serializados de N13 — default []
```

---

## Lógica de Enrutamiento (Conditional Edge)

| Condición | `draft_status` | Siguiente nodo |
|-----------|---------------|----------------|
| `aprobado == true` | `"approved"` | `n14_informe_final` |
| `aprobado == false` y `intentos_critico < 2` | `"rejected"` | `n11_consultor` |
| `aprobado == false` y `intentos_critico >= 2` | `"approved_with_warning"` | `n14_informe_final` |

**Cortafuegos (Ruta C):** Cuando `intentos >= 2`, N13 agrega `SYSTEM_WARNING_TEXT`
al final de `DraftReport.operational_narrative` antes de pasar a N14.

---

## Guardado en Memoria

Solo cuando `aprobado == true`: llama a `MemoryService.store_memory()` con `await` directo
(parte del contrato del nodo — no es best-effort):

```python
MemoryChunk(
    node_origin="N13",
    content=verdict.insight_para_memoria,
    quality_approved=True,
    source_audit_run_id=layer3_run_id,
)
```

> **Decisión de implementación:** Se usa `await` directo, no `asyncio.create_task`.
> El guardado en memoria es parte del contrato de N13 — si falla, el nodo retorna
> `approved_with_warning` en lugar de `approved`. No es una operación best-effort.

---

## Acceptance Criteria

- WHEN cifra en `operational_narrative` no existe en `forensic_report` o `audit_insights` → `ALUCINACION_MATEMATICA` en `tipos_falla`
- WHEN texto contiene palabras prohibidas o tono corporativo → `DESVIACION_IDENTIDAD` en `tipos_falla`
- WHEN ambas fallas presentes → `tipos_falla` contiene ambos valores, `warning_especifico` describe ambas
- WHEN `aprobado == false` y `intentos_critico < 2` → incrementar contador, actualizar `historial_feedback`, volver a N11
- WHEN `aprobado == false` y `intentos_critico >= 2` → `approved_with_warning`, advertencia incluye `warning_especifico` explícito, ir a N14
- WHEN `aprobado == true` → guardar `insight_para_memoria` en `mepia_memory` vía `await` directo
- WHEN `aprobado == true` → `warning_especifico` es `null` siempre
- WHEN `aprobado == false` → `insight_para_memoria` es `null` siempre
- WHEN LLM falla (timeout/error) → `approved_with_warning` con mensaje de error, pipeline no se bloquea
- WHEN N13 ejecuta → entrada agregada a `audit_results` siempre, independientemente del resultado
- WHEN `Layer3State.source_s3_result_id` está presente → la fila N13 conserva
  exactamente ese UUID en `audit_results.source_s3_result_id`
- WHEN `time_series.periodos` tiene más de 7 registros → truncado a los últimos 7 antes de enviar al LLM

---

## Correctness Properties (PBT)

| ID | Propiedad |
|----|-----------|
| P1 | `aprobado == true` → `tipos_falla == ["NINGUNA"]` siempre |
| P2 | `aprobado == false` → `warning_especifico` nunca es `null` |
| P3 | `aprobado == true` → `insight_para_memoria` nunca es `null` |
| P4 | `intentos_critico >= 2` → `draft_status == "approved_with_warning"`, nunca `"rejected"` |
| P5 | `draft_status == "approved_with_warning"` → texto de advertencia con `warning_especifico` en `operational_narrative` |
| P6 | `MemoryService.store_memory()` solo llamado cuando `aprobado == true` |
| P7 | Cada ejecución de N13 → exactamente 1 entrada nueva en `audit_results` |
| P8 | `historial_feedback` crece en 1 por cada rechazo — nunca se sobreescribe |
| P9 | LLM error → `draft_status == "approved_with_warning"`, pipeline continúa |
| P10 | `time_series.periodos` enviado al LLM nunca supera 7 registros |

---

## Archivos relacionados de este nodo
- `agents/n13_revisor.py` — implementación completa
- `agents/layer3_state.py` — definición del `Layer3State`
- `n11_consultor.md` — origen del `DraftReport` + cómo lee `feedback_critico`
- `mem_memory_layer.md` — `MemoryService.store_memory()` + contrato `MemoryChunk`
- `_glossary.md` — contratos `DraftReport`, `CriticVerdict`, `MemoryChunk`
