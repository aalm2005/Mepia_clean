# Selección de análisis y mensajes de interfaz

## Prioridad y navegación

1. run_id explícito, incluso vacío/inválido: error sin fallback si no es válido.
2. Referencia recordada de la pestaña para usuario y negocio actuales.
3. Último N05 terminado del negocio autorizado, por orden de guardado.

La recuperación automática incorpora run_id al enlace. El historial distingue
fecha analizada, guardado, estado, número y referencia breve; permite cargar
páginas anteriores. Elegir uno solo lee resultados: no ingesta, motor ni IA.

MepiaAuthProvider conserva referencias mínimas en memoria y sessionStorage.
Revalida sesión/negocios propios antes de restaurarlas; no guarda resultados
ni un token adicional. Dashboard, Salud, Reportes y vuelta del chat conservan
la selección, también después de recargar el chat.

Cambiar negocio o cerrar sesión elimina inmediatamente el contexto anterior.
El marco remonta por usuario/negocio; hooks abortan peticiones y descartan
respuestas tardías. El nuevo negocio puede recuperar su propio último análisis.
Estos controles de interfaz acompañan la verificación de propietario en servidor.

N15 permite elegir un N05 reciente o pulsar **Usar análisis del Dashboard**.
Envía `analysis_run_id` y consulta el S3 exacto y su N14 compatible. Una visita
al chat no aplica automáticamente la selección del Dashboard. La fecha manual
sigue disponible. La conversación visible se conserva durante navegación
interna del mismo usuario y negocio; recargar la página la reinicia.

## Estados que deben distinguirse

- Buscando último análisis y cargando análisis elegido.
- Sin análisis guardados; sin análisis terminado recuperable; alcance limitado.
- Error de acceso, resultado ausente/ajeno o fallo de conexión, con texto claro.
- Análisis fallido, cálculos insuficientes y tendencia con menos de dos fechas.
- Evaluación forense no disponible y evaluación acreditada sin anomalías.

«Sin anomalías detectadas en los indicadores evaluados» solo aparece cuando
`forensic_status_available` acredita el informe y su lista de anomalías está
vacía. No certifica indicadores no evaluados. Riesgo desconocido no se muestra
como bajo. Sin cálculos no se inventan cifras ni tarjetas de ingresos/margen.

PipelineStatusBar muestra estados en español; Layer2Banner indica preparación,
guardado o fallo del informe avanzado, sin enlazar a un visor inexistente.
Se sustituyen arrays, calc_results y códigos internos por instrucciones sencillas.
No se anuncia un recorrido de carga Excel/CSV sin implementar.

[Consulta protegida](analysis_history.md), [tendencias](analysis_history_trends.md),
[contratos](analysis_history_contracts.md),
[validación local](../../../docs/analysis_history_dashboard_20261019.md).
