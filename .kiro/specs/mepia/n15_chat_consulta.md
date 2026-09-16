# N15 - Chat de consulta fundamentada

**Capa:** Aplicación | **Anterior:** S3/N14 | **Siguiente:** interfaz Chat IA
**Archivos relacionados:** `_glossary.md`, `db_schema.md`,
`agents/chat_grounding.py`,
[`docs/chatbot_corrections.md`](../../../docs/chatbot_corrections.md),
[`docs/chatbot_incidents.md`](../../../docs/chatbot_incidents.md)

## Continuidad del trabajo

La fuente de verdad para el avance, las correcciones obligatorias, las pruebas y
los controles de producción es
[`docs/chatbot_corrections.md`](../../../docs/chatbot_corrections.md). Todo trabajo
futuro debe comenzar por el primer elemento obligatorio marcado como pendiente en
esa bitácora. Las correcciones 1, 2, 3 y 4 y el Trabajo 5 de linaje exacto entre
S3 y N14 están terminados en desarrollo y pruebas. La siguiente acción
obligatoria es la prueba integral del Paso 1 registrada en la sección C.3; el
Trabajo 5 no es una quinta corrección ni la fase 5 del chatbot descrita más
adelante. Las incidencias del proceso de desarrollo y validación se mantienen,
sin duplicar la bitácora de correcciones, en
[`docs/chatbot_incidents.md`](../../../docs/chatbot_incidents.md).

## Input / Output

- Input futuro: `business_id`, pregunta y fecha opcional.
- Output de fase 1: `ChatGroundingPacket` con el `source_s3_result_id` elegido,
  métricas S3, reporte N14 enlazado, referencias y datos faltantes.
- El paquete no contiene instrucciones ni campos arbitrarios de `result_data`.

## User Stories

- Como dueño, quiero preguntar por mis resultados sin que la IA invente cifras.
- Como sistema, quiero separar recuperación de evidencia y generación de lenguaje.
- Como auditor, quiero rastrear cada respuesta hasta filas de `audit_results`.
- Como negocio, quiero impedir que una consulta recupere datos de otro negocio.

## Acceptance Criteria

- WHEN se construye un paquete THEN cada consulta filtra por `business_id`.
- WHEN no se solicita fecha THEN se usa la fecha S3 exitosa más reciente.
- WHEN una fecha contiene varias ejecuciones THEN se elige la fila S3 utilizable
  más reciente por `created_at`.
- WHEN se busca N14 THEN debe coincidir en `business_id`, fecha y
  `source_s3_result_id = audit_results.id` de la fila S3 elegida.
- WHEN el S3 elegido no tiene un N14 con el mismo `source_s3_result_id` THEN no se
  usa un N14 de otra ejecución y `missing_data` incluye
  `final_report_not_found`.
- WHEN el identificador de linaje falta, es inválido o no coincide THEN se trata
  como reporte no encontrado; nunca se hace fallback por fecha.
- WHEN existe S3 THEN solo se exponen `metric`, `value`, `unit`, `status` y `context`.
- WHEN `result_data` de S3 no es un objeto THEN no se lanza una excepción, no se
  expone su contenido y `missing_data` incluye `metrics_not_found`.
- WHEN `results` de S3 no es una lista THEN no se itera ni se expone su contenido
  y `missing_data` incluye `metrics_not_found`.
- WHEN existe N14 THEN solo se exponen los campos permitidos del reporte final.
- WHEN el `result_data` de N14 no contiene ningún campo autorizado THEN
  `final_report` es `None` y `missing_data` incluye `final_report_not_found`.
- WHEN `result_data` contiene campos no autorizados THEN nunca se exponen en el
  paquete, exista o no un reporte final válido.
- WHEN falta una fuente THEN se declara en `missing_data`; nunca se rellena.
- WHEN se incluye evidencia THEN contiene `audit_result_id`,
  `source_s3_result_id`, nodo, fecha y timestamp.
- WHEN la fecha es inválida THEN la construcción falla antes de consultar la base.

## Fases

1. ✅ Paquete determinista S3/N14, contrato de persistencia y linaje exacto
   implementados y probados localmente; pendiente la prueba integral del Paso 1.
2. Pendiente después de esa prueba integral: herramientas de consulta de
   métricas, reportes y glosario.
3. Pendiente: nodo LLM con respuesta estructurada y rechazo por falta de evidencia.
4. Pendiente: evaluación offline y pruebas de aislamiento.
5. Pendiente: endpoint autenticado e interfaz Chat IA.

## Discrepancias conocidas

- La autenticación FastAPI aún no está implementada. No se expone endpoint de chat hasta aplicar autorización por negocio.
- `MemoryService.get_context()` retorna texto sin IDs de fuente; no se usará en el chat hasta agregar procedencia verificable.

## Edge Cases

- Negocio sin auditorías: paquete vacío con `no_audit_results`.
- Fecha sin S3 pero con N14: el N14 no se usa porque no existe una raíz S3
  verificable; se marcan métricas y reporte faltantes.
- Dos ejecuciones del mismo negocio y fecha: se usa la S3 más reciente y solo el
  N14 cuyo `source_s3_result_id` coincide exactamente.
- S3 más reciente sin N14 enlazado y una ejecución anterior con N14: no se hace
  fallback al reporte anterior; se agrega `final_report_not_found`.
- Registros históricos con `source_s3_result_id = NULL`: se conservan, pero no
  se infiere linaje por negocio y fecha.
- S3 con `result_data` como lista, texto, número, booleano o `null`: conserva la
  evidencia, devuelve métricas vacías y agrega `metrics_not_found`.
- S3 con `results` de cualquier tipo distinto de lista: conserva la evidencia,
  devuelve métricas vacías y agrega `metrics_not_found`.
- N14 con campos autorizados y no autorizados: conserva solo los autorizados.
- N14 sin ningún campo autorizado: `final_report = None`, agrega
  `final_report_not_found` y no expone los campos descartados.
- Registro devuelto con otro `business_id`: se rechaza.

## Archivos relacionados de este nodo

- `agents/chat_grounding.py` - implementación de la fase 1.
- `tests/test_chat_grounding.py` - aislamiento, fechas, linaje exacto, múltiples
  ejecuciones, allowlists, tipos persistidos inválidos y datos faltantes.
- `tests/test_chat_lineage_persistence.py` - propagación y persistencia del UUID
  raíz desde S3 hasta N14.
- `supabase/migrations/009_audit_results_s3_lineage.sql` - FK e índice de linaje
  para instalaciones existentes.
