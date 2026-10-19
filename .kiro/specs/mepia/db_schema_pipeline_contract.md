# Contrato físico del pipeline — migración 011

**Estado al 15-oct-2026:** contrato observado en inventario posterior de principal:
18 tablas/175 columnas; revisión estática de 658 referencias sin faltantes.
La RPC conserva históricos POS duplicados y rechaza fechas ambiguas, sin imponer
índice único en esa tabla. SQL real 9/9 contratos y 4/4 controles de aislamiento aprobados,
con ROLLBACK; conteos y huellas anteriores preservados. INC-046 resuelta. [Ejecución y límites](../../../docs/database_unification.md).

**Capa:** infraestructura. **Referencia:** `db_schema.md`.
**Implementación:** `supabase/migrations/011_full_pipeline_contract.sql`.

## Tablas

- `shift_audit_events`: eventos por negocio/fecha/sucursal/turno; apertura,
  cierres, diferencia de caja, `cancellations`, `reprints` y `clock_records`
  JSONB. `reprints` empieza como lista, conservando el contrato 006 actual
  sin ejecutar su conversión que descartaba datos. Campos opcionales
  `shift_id` text y `start_time`/`end_time` timestamptz para lectores existentes.
- `inventory_daily`: ingrediente, unidad, consumo teórico, merma, existencia y
  costo unitario por negocio/fecha.
- `delivery_platform_config`: plataforma, comisión decimal y fecha efectiva
  por negocio; no se inventan tasas.

Las tres tablas tienen UUID, FK al negocio y RLS habilitado. No se conceden
políticas anónimas: el servidor autorizado usa service_role. EXECUTE de la
RPC se revoca explícitamente a PUBLIC, anon y authenticated porque Supabase
puede concederlo directamente por privilegios predeterminados.

## Columnas adicionales

| Tabla | Columnas |
|---|---|
| `businesses` | `multi_sucursal` boolean |
| `cash_counts` | `created_at`, `updated_at` timestamptz |
| `transactions` | `needs_human_review` boolean |
| `pos_inputs` | `product_id` UUID FK recipes, `quantity` numeric |
| `mepia_memory` | `attempt_count` integer; `embedded_at`, `updated_at` timestamptz |

Los valores históricos desconocidos quedan NULL. Los defaults se establecen
después de añadir columnas, para aplicarlos a nuevas filas: multi_sucursal y
revisión false, intentos cero, fechas técnicas now cuando corresponda.
Estos campos no reconstruyen datos financieros ni horarios ausentes.

## Integridad y aceptación

- WHEN ingesta POS usa `upsert_pos_daily(jsonb)` THEN bloqueo transaccional
  por negocio/fecha; cero filas crea, una actualiza, varias rechaza con
  `MEPIA_POS_DATE_AMBIGUOUS`. Sin borrar ni deduplicar históricos.
- WHEN el endpoint recibe ese conflicto THEN 409; fallo de guardado, 503.
- WHEN otros upserts guardan THEN índices únicos cubren negocio/fecha en
  `cash_counts` y negocio/fecha/métrica en `metric_status`.
- WHEN eventos/inventario/comisiones se repiten THEN sus claves compuestas
  permiten upsert sin duplicar filas.
- WHEN existen duplicados incompatibles o `reprints` no es JSONB THEN se aborta
  la transacción completa; ningún registro se elimina para imponer índices.
- WHEN faltan datos específicos THEN no se rellenan con cantidades o costos
  ficticios; disponibilidad/semántica de métricas se valida separadamente.
- WHEN termina la migración THEN PostgREST recibe recarga de esquema.

## Archivos relacionados

- `s1b_ingesta_api.md`, `s2_gatekeeper.md`, `s3_motor_calculo.md`.
- `n10_onboarding_identidad.md`, `mem_memory_layer.md`.
- `../../../docs/database_unification.md`: ejecución real y límites.
