# Q7: conversación conservada y selección exacta de análisis

El chat se desmontaba al navegar al Dashboard y perdía sus mensajes, borrador e
identificador de conversación. El servidor conservaba temporalmente el intercambio,
pero la vista nueva no tenía su referencia. ChatPanel vive ahora en MepiaShell y se
oculta durante la navegación; los cambios de usuario o negocio desmontan el ámbito.
Una petición en curso termina sin que cambiar de pantalla la vuelva a enviar.

El selector muestra análisis N05 recientes, paginados de 25 en 25, con fecha,
guardado y referencia. El botón del Dashboard reutiliza la selección compartida.
El POST acepta `analysis_run_id` opcional: comprueba propiedad, estado terminado,
fecha y linaje, y recupera el S3 exacto y su N14 compatible antes de crear el proveedor.
No se sustituye una ejecución antigua por la más reciente del mismo día.
El historial usado como contexto se restringe al S3 seleccionado; cambiar de análisis
en la interfaz inicia una conversación nueva. Los errores específicos se comunican
con mensajes de una lista cerrada del proxy, sin propagar excepciones privadas.

Las fechas manuales y consultas conceptuales conservan su funcionamiento anterior.
Se mantienen los límites de ocho turnos y treinta minutos del servidor. Esta
corrección no añade almacenamiento durable tras recarga o cierre/reinicio.

## Verificación y estado

Verificación del 10-nov-2026: 220 pruebas y 103 subpruebas Python aprobadas
(dos advertencias preexistentes de lifespan), 29 controles Edge aprobados sin errores
de página, ocho controles aislados del proxy aprobados, compilación y tipos código 0.
Los tres controles nuevos de navegación/selección pasaron también antes de ajustar
la espera de una aserción antigua; el segundo recorrido completo aprobó conservando
su comprobación de aislamiento. Intentos anteriores preservados.
La aplicación local se reinició con `.test_tmp/q7_chat_20261110/principal/build`;
login y OpenAPI HTTP 200, campo `analysis_run_id` confirmado. Cero llamadas reales
a modelos y cero escrituras de datos del negocio en esta corrección. Aceptación
manual con IA pendiente. INC-20261110-060/061 resueltas para el alcance local verificado.
Evidencia: `docs/evaluations/q7_chat_20261110.json` y `docs/q7_chat_navigation_20261110.md`.

Rama `codex/quincena-6`, HEAD/base `5ae4c868be6843513a3b8a4f0be2962762c6442d`,
sin commit/push. Categoría C solicitada expresamente, sin reabrir Pasos 1–4.
La [guía manual versionada](../output/pdf/MEPIA_Q7_DaAx_Coffee/Comprobar_resultados_y_chat_Q7.md) incluye cifras de control de los cinco PDF y 35 preguntas,
siete por análisis, con criterios numéricos, límites y evidencia. Su ejecución
con proveedores reales y aceptación humana siguen pendientes.
