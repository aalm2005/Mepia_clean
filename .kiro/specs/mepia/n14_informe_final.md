# N14 — Informe Final (Nodo de Persistencia y Entrega)

**Capa:** Layer 3 — Nodo final | **Anterior:** N13 Revisor de Calidad | **Siguiente:** END
**Archivo de implementación:** `agents/n14_informe_final.py`
**Tipo:** Python puro — sin LLM, 100% determinista
**Patrón:** Nodo pasivo de persistencia y formateo

> N14 es el nodo terminal del grafo Layer 3. No genera texto ni toma decisiones.
> Su única responsabilidad es tomar el `DraftReport` aprobado del `Layer3State`,
> formatearlo para entrega y persistirlo en `audit_results`.

---

## Input / Output

**Input:** `Layer3State` con `draft_report` aprobado y `draft_status` en
`"approved"` o `"approved_with_warning"`.

**Output:** `final_response`, `draft_status` y `layer3_status=completed` solo
tras guardar `FinalReport`. Sin DB o ante error, `N14PersistenceError` saneado:
no hay respuesta final. API y N05 usan [ejecución compartida](layer3_execution.md).
INC-048 resuelta localmente; prueba real de IA separada.

---

## Responsabilidad

```
Layer3State (draft_report aprobado)
        │
        ↓
N14 Informe Final (Python puro)
  ├─ Extrae DraftReport del estado
  ├─ Propaga DraftReport.model_used (o "unknown" si falta)
  ├─ Construye FinalReport (separa narrativa Markdown y metadatos)
  ├─ Persiste FinalReport en audit_results (node_id: "N14")
  └─ Retorna final_response/draft_status/completed solo tras guardar; fallo saneado
        │
        ↓
END (grafo completado)
```

---

## Decisión de LLM

**N14 NO usa LLM.** Es un nodo Python puro y determinista.

El campo `model_used` se toma de `DraftReport.model_used` y usa `"unknown"`
si falta. Si N11 activó fallback, N14 conserva ese valor; no fija un proveedor.

---

## Contrato de Salida — `FinalReport`

```python
class FinalReport(BaseModel):
    # Trazabilidad
    layer3_run_id: str
    source_s3_result_id: Optional[str]  # audit_results.id de la fila S3 raíz
    business_id: str
    date: str
    archetype: str
    temporalidad: str

    # Contenido formateado para entrega al frontend
    executive_summary: str           # tomado directamente de DraftReport
    operational_narrative_md: str    # narrativa en formato Markdown (headers, bullets)
    pragmatic_actions: list[dict]    # lista de acciones con priority y owner

    # Metadatos de calidad
    draft_status: str                # "approved" | "approved_with_warning"
    model_used: str                  # propagado desde DraftReport.model_used
    intentos_critico: int            # número de revisiones que requirió el borrador
    quality_warnings: list[str]      # historial_feedback del Layer3State si hubo rechazos

    # Metadatos de generación
    finalized_at: str                # ISO-8601 UTC
    layer3_duration_ms: int          # duración total del grafo Layer 3
```

### Regla de formateo de `operational_narrative_md`

N14 convierte el `operational_narrative` (texto plano de N11) a Markdown estructurado:

```
## Hallazgos del período

{operational_narrative}

---
*Generado por MEPIA · {date} · Arquetipo: {archetype}*
```

Si `draft_status == "approved_with_warning"`, agrega al final:

```
> ⚠️ Este reporte contiene advertencias de calidad no resueltas.
> Revisar manualmente antes de tomar decisiones.
```

---

## Persistencia en `audit_results`

N14 persiste el `FinalReport` como el registro terminal del pipeline Layer 3.

| Campo           | Valor |
|-----------------|-------|
| `source_s3_result_id` | ID de la fila S3 raíz recibido en `Layer3State` |
| `business_id`   | FK → businesses |
| `date`          | Fecha auditada |
| `pipeline_layer`| `"loop"` |
| `node_id`       | `"N14"` |
| `id`            | UUID nuevo de la fila N14 |
| `result_data`   | `FinalReport` serializado (incluye arquetipo y resumen) |
| `created_at`    | `FinalReport.finalized_at` |
| `node_status`   | `"success"` en la inserción intentada; `_persist_n14` devuelve false ante error |

---

## Acceptance Criteria — comprobados localmente, INC-048 resuelta

- WHEN `draft_status == "approved"` → `FinalReport` sin advertencias de calidad
- WHEN `draft_status == "approved_with_warning"` → `quality_warnings` contiene el historial de rechazos y el Markdown incluye el bloque de advertencia
- WHEN N14 completa → `layer3_status: "completed"` en el estado del grafo
- WHEN N14 completa → `FinalReport` persistido en `audit_results` antes de retornar END
- WHEN `Layer3State.source_s3_result_id` está presente → el `FinalReport`, su
  `result_data` y la columna de la fila N14 conservan exactamente ese UUID
- WHEN `DraftReport.model_used` contiene `"fallback"` → N14 lo propaga sin modificar
- WHEN N14 falla al persistir → no entrega informe; wrapper registra status failed y polling de resultado devuelve 503 sin excepción del proveedor

---

## Edge Cases

- `draft_report` vacío o nulo → el nodo usa un diccionario vacío y construye campos vacíos; no implementa rechazo explícito
- Supabase no disponible → `_persist_n14` devuelve false y N14 lanza error saneado; wrapper conserva fallo temporal. No hay reintento ni inserción failed en DB caída
- `draft_status` inesperado → se propaga; el nodo no lo normaliza ni registra una advertencia por ese motivo. Validarlo antes de entrar es un requisito del flujo

---

## Resolución local — 15-oct-2026

INC-048/049 resueltas localmente: no hay finalización válida sin guardado.
Grafo real con generadores simulados y polling de éxito/fallo comprobados en
la [evidencia de preparación](../../../docs/evaluations/demo_preparation_20261015.json).
El diagnóstico anterior se conserva como reproducción histórica. El registro
temporal de errores caduca a los 30 minutos y no sobrevive reinicios; ver
[ejecución](layer3_execution.md). Ensayo con proveedores/base reales pendiente.

## Correctness Properties (PBT)

| ID | Propiedad |
|----|-----------|
| P1 | `FinalReport.draft_status` == `Layer3State.draft_status` siempre |
| P2 | `draft_status == "approved_with_warning"` → `quality_warnings` nunca vacío |
| P3 | `draft_status == "approved"` → `quality_warnings` siempre vacío |
| P4 | `model_used` propagado desde `DraftReport.model_used` — nunca sobreescrito por N14 |
| P5 | `layer3_status: "completed"` solo cuando `FinalReport` persistido exitosamente |
| P6 | N14 nunca modifica `executive_summary` ni `pragmatic_actions` — solo formatea `operational_narrative` |

---

## Archivos relacionados de este nodo
- `agents/n14_informe_final.py` — implementación
- `agents/layer3_state.py` — `Layer3State` (input)
- `agents/layer3_graph.py` — grafo que conecta N14 con END
- `n13_revisor.md` — nodo anterior (produce el `draft_report` aprobado)
- `_glossary.md` — contrato `FinalReport`
