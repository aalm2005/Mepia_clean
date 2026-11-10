# Diseño Frontend — Flujos y estados

Vigente al 19-oct-2026. [Secuencia](design_flows_main.md),
[contrato de historial](analysis_history.md).

## Entrada y selección

Sin sesión → login con destino interno; usuario validado → negocio propio.
Prioridad: run_id explícito → selección de pestaña/usuario/negocio → último
análisis terminado. Un run_id inválido, vacío, ausente o ajeno muestra su error
sin reemplazarlo silenciosamente. Elegir en el historial actualiza el enlace.
Cambiar negocio/salir limpia datos y cancela solicitudes anteriores.

## Estados de la consulta

| Estado | Presentación |
|---|---|
| Buscando último | Indica recuperación en curso |
| Cargando elegido | Indica lectura del análisis guardado |
| Historial vacío | Explica que no hay análisis guardados para ese negocio |
| Sin terminado recuperable | Solicita elegir otro; un límite no se llama historial vacío |
| Error | Mensaje claro y reintento según operación |
| Sin cálculos suficientes | Explica qué indicadores/datos faltan |
| Sin evidencia forense | No afirma ausencia de anomalías ni riesgo bajo |
| Evaluación acreditada sin anomalías | «Sin anomalías detectadas en los indicadores evaluados» |

## Estado guardado del análisis

PipelineStatusBar expresa running, completed, partial, escalated, failed o
unknown en español. unknown es proyección de lectura histórica, sin cambiar
el motor. No muestra nodos S1/S2 al usuario. Partial no acredita todos los
indicadores; failed ofrece elegir otra corrida o revisar documentos.

La escalación muestra preparación, informe avanzado guardado o fallo de guardado.
El GET protegido `/{run_id}/layer3` resuelve el padre desde N05. Un 404 significa
que aún no inició; no acredita éxito. Un fallo N14 conserva los indicadores
guardados y no entrega como persistido el informe perdido. No hay enlace a un
visor avanzado inexistente.

## Acceso y errores

Next exige Bearer/sesión para APIs; FastAPI verifica sesión y propietario en
chat, ajustes y las nuevas lecturas de análisis. 401 sin consultar auditorías;
403 para negocio no autorizado; 404 ambiguo para corrida ausente/ajena;
503 saneado ante permisos/DB. El acceso por recurso del backend legado sigue
pendiente para producción, separado de la guarda de interfaz.

## Documentos, ajustes y chat

Documentos crea defaults si faltan, conserva ajustes y ofrece personalización
opcional. Las fechas de ventas deben ser inequívocas y compatibles con la
selección. La revisión de campos precede al análisis cuando corresponde.
Chat comparte sesión/negocio y conserva la selección N05 al volver. Consulta
S3/N14 por fecha/linaje; no convierte esa referencia visual en fuente de respuesta.
Historial conversacional: memoria temporal por proceso, separado de auditorías.

[Pruebas y límites](../../../docs/analysis_history_dashboard_20261019.md).
## Tutorial guiado en quincena 6

El botón Tutorial repite el recorrido de 26 pasos en seis vistas.
El progreso se guarda por cuenta y negocio. Al cambiar de negocio se retira
el tutorial anterior y, si el Dashboard aún muestra la referencia del
análisis anterior, la bienvenida espera a que se limpie la URL.
Un enlace directo a un análisis tiene prioridad sobre la bienvenida.
En Dashboard, el recorrido señala el selector del historial, el mensaje de
estado y los títulos de indicadores, hallazgos y tendencias. Si falta un
apartado de resultados, el aviso señala el estado y explica qué dato hace
falta para verlo.
El recorrido señala los controles de guardado, análisis y chat sin accionarlos.
Pruebas locales en escritorio y móvil aprobadas. Siguen pendientes la
adaptación móvil integral, la evaluación humana y el ensayo real.


[Versión anterior conservada](../../../docs/history/documentation_before_sync_20261019/.kiro/specs/mepia/design_flows.md). Sus estados y cifras describen su fecha original.
