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
esa bitácora. Las correcciones 1, 2, 3 y 4 están terminadas en desarrollo y
pruebas. El Trabajo 5 de linaje exacto entre S3 y N14 es el siguiente trabajo
obligatorio de robustez para cerrar el Paso 1; no es una quinta corrección ni la
fase 5 del chatbot descrita más adelante. Las incidencias del proceso de desarrollo
y validación se mantienen, sin duplicar la bitácora de correcciones, en
[`docs/chatbot_incidents.md`](../../../docs/chatbot_incidents.md).

## Input / Output

- Input futuro: `business_id`, pregunta y fecha opcional.
- Output de fase 1: `ChatGroundingPacket` con métricas S3, reporte N14, referencias y datos faltantes.
- El paquete no contiene instrucciones ni campos arbitrarios de `result_data`.

## User Stories

- Como dueño, quiero preguntar por mis resultados sin que la IA invente cifras.
- Como sistema, quiero separar recuperación de evidencia y generación de lenguaje.
- Como auditor, quiero rastrear cada respuesta hasta filas de `audit_results`.
- Como negocio, quiero impedir que una consulta recupere datos de otro negocio.

## Acceptance Criteria

- WHEN se construye un paquete THEN cada consulta filtra por `business_id`.
- WHEN no se solicita fecha THEN se usa la fecha S3 exitosa más reciente.
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
- WHEN se incluye evidencia THEN contiene `audit_result_id`, nodo, fecha y timestamp.
- WHEN la fecha es inválida THEN la construcción falla antes de consultar la base.

## Fases

1. 🔧 Paquete determinista S3/N14 y contrato de persistencia implementados;
   siguiente: robustez de linaje del Trabajo 5.
2. Pendiente: herramientas de consulta de métricas, reportes y glosario.
3. Pendiente: nodo LLM con respuesta estructurada y rechazo por falta de evidencia.
4. Pendiente: evaluación offline y pruebas de aislamiento.
5. Pendiente: endpoint autenticado e interfaz Chat IA.

## Discrepancias conocidas

- La autenticación FastAPI aún no está implementada. No se expone endpoint de chat hasta aplicar autorización por negocio.
- `MemoryService.get_context()` retorna texto sin IDs de fuente; no se usará en el chat hasta agregar procedencia verificable.

## Edge Cases

- Negocio sin auditorías: paquete vacío con `no_audit_results`.
- Fecha sin S3 pero con N14: se conserva el reporte y se marca la métrica faltante.
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
- `tests/test_chat_grounding.py` - aislamiento, fechas, allowlist, tipos
  persistidos inválidos y datos faltantes.
