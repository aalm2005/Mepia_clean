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

**Output:** `FinalReport` persistido en `audit_results` + actualización del estado
con `layer3_status: "completed"`.

---

## Responsabilidad

```
Layer3State (draft_report aprobado)
        │
        ↓
N14 Informe Final (Python puro)
  ├─ Extrae DraftReport del estado
  ├─ Fija model_used = "claude-3-5-sonnet-20241022"
  ├─ Construye FinalReport (separa narrativa Markdown y metadatos)
  ├─ Persiste FinalReport en audit_results (node_id: "N14")
  └─ Retorna layer3_status: "completed"
        │
        ↓
END (grafo completado)
```

---

## Decisión de LLM

**N14 NO usa LLM.** Es un nodo Python puro y determinista.

El campo `model_used` en el `FinalReport` se fija estáticamente a
`"claude-3-5-sonnet-20241022"` — el modelo que generó el borrador en N11.
Si N11 activó el fallback, el valor correcto ya está registrado en
`DraftReport.model_used` y N14 lo propaga sin modificarlo.

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
| `module`        | `"informe_final"` |
| `archetype`     | Arquetipo del run |
| `raw_result`    | `FinalReport` serializado (JSON) |
| `copilot_phrase`| `executive_summary` del `FinalReport` |
| `node_status`   | `"success"` \| `"failed"` |

---

## Acceptance Criteria

- WHEN `draft_status == "approved"` → `FinalReport` sin advertencias de calidad
- WHEN `draft_status == "approved_with_warning"` → `quality_warnings` contiene el historial de rechazos y el Markdown incluye el bloque de advertencia
- WHEN N14 completa → `layer3_status: "completed"` en el estado del grafo
- WHEN N14 completa → `FinalReport` persistido en `audit_results` antes de retornar END
- WHEN `Layer3State.source_s3_result_id` está presente → el `FinalReport`, su
  `result_data` y la columna de la fila N14 conservan exactamente ese UUID
- WHEN `DraftReport.model_used` contiene `"fallback"` → N14 lo propaga sin modificar
- WHEN N14 falla al persistir → `node_status: "failed"`, error reportado al endpoint disparador

---

## Edge Cases

- `draft_report` vacío o nulo en el estado → `node_status: "failed"`, no persistir
- Supabase no disponible → reintentar 1 vez, luego `node_status: "failed"` con detalle
- `draft_status` inesperado (ni `"approved"` ni `"approved_with_warning"`) → log error, persistir con advertencia

---

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
