# N15 — Datos del motor consultables por el chat

**Capa:** aplicación. **Anterior:** S3/N14. **Siguiente:** respuesta fundamentada.
**Referencia:** [N15 principal](n15_chat_consulta.md).

## Input / Output

Entrada: negocio autorizado, fecha opcional y pregunta. Salida: métricas,
informe permitido, fuentes y faltantes; conceptos desde catálogo/glosario local.
Implementación: `agents/chat_grounding.py`, `agents/chat_tools.py`, `api/chat.py`.

## User Stories

- Como dueño, quiero preguntar por resultados que el motor ya guardó.
- Como usuario, quiero distinguir una definición de una cifra de mi negocio.
- Como auditor, quiero evitar mezclar proyectos, negocios o ejecuciones.

## Acceptance Criteria

- WHEN el motor guarda S3 THEN usa `audit_results`, `node_id=S3`, resultados
  en `result_data.results` y su ID como raíz `source_s3_result_id`.
- WHEN se guarda N14 THEN contiene el informe en `result_data` y el linaje de S3.
- WHEN el chat consulta THEN verifica usuario/propiedad y filtra negocio;
  con fecha selecciona esa fecha, sin ella la S3 válida más reciente.
- WHEN recupera N14 THEN exige negocio, fecha y raíz S3 coincidentes. Sin N14
  puede consultar métricas válidas, indicando que falta el informe.
- WHEN motor y chat usan proyectos distintos THEN no comparten registros
  automáticamente. Compartir archivos de código no unifica sus bases.
- WHEN hay resultados persistidos THEN el motor puede estar detenido: el chat
  los recupera de la base, sin recalcular ni modificar auditorías.
- WHEN pregunta conceptos THEN el catálogo local es fuente conceptual;
  nunca demuestra que exista ese resultado para el negocio.
- WHEN solo hay documentos crudos o cálculos sin guardar THEN no se presentan
  como resultados consultables. El chat no tiene consulta libre a todas las tablas.

## Perfiles y entorno

`api.main:app` registra motor, chat y ajustes. `api.chat_app:create_app --factory`
registra chat, negocios y ajustes, sin ingesta/análisis. Ambos leen `api/.env`
y `.env`; el frontend debe usar el mismo proyecto Supabase y una sesión válida
de ese proyecto. El historial conversacional es temporal en memoria y distinto
de los resultados persistidos en `audit_results`.

Interfaz y servidor completo comparten principal. Lectura real de grounding:
cuatro métricas existentes, una evidencia S3 y ningún informe N14 enlazado.
No se reconstruye linaje histórico ni se generan respuestas en esa comprobación.
INC-046 resuelta; la validación anterior conserva su alcance. Ver [estado operativo](../../../docs/database_unification.md).

## Edge Cases

- Sin S3 utilizable: faltantes explícitos, sin cifras inferidas ni N14 alternativo.
- INC-048 resuelta localmente: N14 no devuelve informe tras fallo al guardar;
  el chat sigue recuperando únicamente el informe realmente persistido.
- Demo acotada: conciliación S3 0.00 MXN recuperable sin exigir escalación N14;
  prueba local con DB simulada, respuesta real de Gemini pendiente.
- Sin propietario/sesión válida: rechazo antes de evidencia y modelo.
- Seleccionar una fecha no habilita agregaciones ni comparaciones calculadas.

## Archivos relacionados de este nodo

- [Herramientas](n15_chat_consulta_tools.md), [catálogo](n15_chat_consulta_catalogo.md).
- [Esquema](db_schema.md), [informe final](n14_informe_final.md).
