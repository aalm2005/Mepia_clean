# Historial de análisis y gráficas — cierre local del 19-oct-2026

Rama `codex/quincena-5`, base y HEAD conservados:
`5ae4c868be6843513a3b8a4f0be2962762c6442d`. El repositorio estaba limpio al
comenzar; no existían cambios posteriores que reemplazar. Todo este trabajo
está **sin commit**, sin push ni despliegue. Categoría C solicitada por el usuario;
no reabre Pasos 1–4 ni las correcciones de INC-050–053.

## Funcionamiento

Dashboard, Salud del Negocio y Reportes muestran un historial del negocio propio
con fecha analizada, fecha/hora de guardado, estado, número dentro de la lista y
referencia breve. El listado conserva las ejecuciones del mismo día y permite
cargar páginas anteriores. Elegir una recupera resultados guardados mediante GET;
no vuelve a analizar documentos ni consume IA.

Sin selección se recupera el último N05 terminado por orden de guardado,
incluidos los terminados con datos pendientes o revisión avanzada. Un run_id
explícito tiene prioridad; uno vacío/inválido/ausente/ajeno devuelve un mensaje
claro y no se sustituye silenciosamente por otro análisis. Se recuerda la
selección por pestaña, usuario y negocio; funciona al navegar y recargar incluso
después de visitar el chat. Cambiar negocio o salir retira de inmediato los datos
anteriores y descarta respuestas tardías. Cada lectura vuelve a verificar permiso.

Dashboard y Salud consultan resultados de otras fechas. Las series se ordenan
y usan una corrida por día: la elegida en su fecha y la última terminada en las
demás. Se comparan únicamente indicadores diarios identificados y su unidad
exacta. No se suman corridas, productos, unidades ni porcentajes. Cero es válido;
un dato ausente o incompatible deja un espacio. Una sola fecha no dibuja una
tendencia y la interfaz explica qué falta.

Las tarjetas muestran los indicadores realmente conservados. No se presenta
concentración de ingresos como ingresos, coste como margen ni una media en MXN
como puntuación de salud. Los títulos y series corresponden al indicador leído;
no hay ingresos/márgenes inventados. Se retiran los textos de arrays, calc_results,
Excel/CSV y códigos internos de las etapas en estos recorridos.

Carga, búsqueda automática, historial vacío, fallo de lectura, análisis fallido,
falta de cálculos y ausencia de evidencia forense tienen mensajes distintos.
«Sin anomalías detectadas en los indicadores evaluados» exige informe original
coincidente y cálculos válidos de una corrida terminada. Un fallback o un riesgo
desconocido nunca acreditan evaluación ni riesgo bajo.

## Validación ejecutada

| Verificación | Resultado real |
| --- | --- |
| Dirigidas de historial, recuperación N05 y guardado N14 | 81 aprobadas, dos advertencias; 11.38 s; código 0 |
| Regresión completa `tests` con red externa bloqueada | 452 aprobadas, una integración opt-in omitida, 136 subpruebas, dos advertencias; 85.83 s; código 0 |
| Edge: historial, navegación, aislamiento, vacíos y errores | 11/11, cero errores de página; código 0; repetido tras presentación final |
| Edge: acceso común, Documentos, INC-050–053, chat y móvil acotado | 23/23, cero errores de página; código 0 |
| Presentación S3 existente | 16/16, código 0 |
| Presentación adicional del historial y significado de indicadores | 8/8, código 0 |
| Fechas de documentos | 11/11, código 0 |
| TypeScript final y build Next 15.5.27 | Ambos código 0 |
| Formato del diff y preservación | Código 0; evidencia y demostración originales verificadas por bytes |

Auth, DB y proveedores fueron simulados. En el recorrido exclusivo del historial:
cero invocaciones de modelos, cero cambios de filas y solo GET en las consultas.
El recorrido general usa el proveedor simulado existente. La red externa estuvo
bloqueada en el proceso de la regresión completa y en el contexto de los navegadores.
Las dos advertencias Python son las deprecaciones ya existentes de `on_event`.
La integración real omitida conserva su diseño opt-in; no se habilitó.
Se reutilizaron dependencias locales; no se modificaron manifests ni lockfiles.

Los intentos iniciales no se cuentan como aprobación: una aserción antigua de
rutas, una expectativa que omitía una fecha vacía y dos selectores del E2E previo
necesitaron actualizarse o separar el texto de su acción. Sus logs, JSON, XML y
capturas se conservan en `.test_tmp/history_20261019/attempt1`,
`previous-e2e-initial`, `previous-e2e-second` y `e2e-before-presentation`.
El cierre usa exclusivamente los resultados posteriores descritos arriba.

Resumen verificable, inventario y preservación:
[`evaluations/analysis_history_dashboard_20261019.json`](evaluations/analysis_history_dashboard_20261019.json).
Las evidencias históricas originales no se reescribieron ni recalificaron.

## Incidencias y límites

INC-055 (historial/recuperación), INC-056 (tendencias/significado de series) e
INC-057 (mensajes/evidencia forense) resueltas localmente. INC-017 actualizada por
la restricción inicial del sandbox; el acceso autorizado al repositorio solicitado
permitió verificar Git y ejecutar las pruebas. Sin bloqueantes nuevos abiertos.
57 incidencias en la bitácora: 54 resueltas, dos mitigadas y una pendiente externa;
los estados de INC-023/031/041 y la evaluación humana N15 no se cambian.

El contrato detallado está en `.kiro/specs/mepia/analysis_history.md`. El alcance
de tendencias se limita explícitamente a 300 ejecuciones y 90 fechas hasta la
seleccionada; la búsqueda automática a 10 000 candidatos. No se comparan productos,
ingredientes o canales si no se conserva su identidad suficiente. El registro
temporal de fallos N14 mantiene su límite previo de 128 corridas/30 minutos por
proceso. Las APIs legadas fuera de los nuevos GET conservan controles de producción
pendientes. Reportes no agrega ahora una presentación integral de N14; N15 sigue
consultando por fecha/S3/linaje, sin convertir la selección N05 en fuente nueva.

La validación es local y sintética: no acredita lectura nueva de la base principal,
pruebas con proveedores reales, despliegue ni revisión humana. No se modificó
Supabase principal/PRUEBAS, ni se ejecutaron modelos reales, commit o push.

## Comprobar desde la interfaz

1. Iniciar los servicios locales de este repositorio con la configuración habitual
   y entrar con la cuenta propia. Abrir Dashboard sin run_id: debe recuperar el
   último análisis terminado del negocio, si existe.
2. En «Análisis guardado», elegir otra ejecución. Comprobar fecha, hora de guardado,
   estado y referencia; tarjetas, gráficas y hallazgos deben corresponder a ella.
3. Abrir Salud del Negocio y Reportes, visitar Chat IA y volver. Recargar: la misma
   selección debe conservarse. Elegir historial no inicia un análisis nuevo.
4. Revisar la evolución de indicadores diarios: una fecha por punto, mismo indicador
   y unidad, espacios por faltantes y explicación si no hay dos fechas válidas.
5. Cambiar negocio y cerrar sesión: los datos previos desaparecen. Un negocio sin
   historial debe explicarlo, sin afirmar que no hay anomalías. Probar un enlace
   inválido o ajeno debe producir error, sin cargar silenciosamente otro resultado.

Para reproducir sin servicios reales se incluyen `tests/analysis_history_e2e.cjs`,
su servidor sintético y `tests/test_analysis_history.py`. El E2E requiere las
variables MEPIA_TEST_PYTHON y MEPIA_PLAYWRIGHT_MODULE; usa Edge local y cierra los
procesos de prueba al terminar. Logs detallados en `.test_tmp/history_20261019`.
