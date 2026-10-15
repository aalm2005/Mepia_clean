# Propuesta de repeticiones con juez Gemini 3.8 — 11-oct-2026

**Propuesta pendiente de autorizacion. Cero llamadas nuevas ejecutadas.**

La revision suplementaria aprobo 3/3 respuestas de una sola generacion previa,
con cero pendientes y los cuatro criterios verdaderos por respuesta.
Los tres 503 originales se conservan. Esa ejecucion no cuenta como una
repeticion sin errores bajo el plan original del 9-oct. Para completar tres
repeticiones sin errores se propone una serie nueva con el juez que respondio.

| Alcance | Propuesta |
|---|---|
| Casos | `same_day_result_and_report` y `arithmetic_division` |
| Repeticiones nuevas | 3, ejecutadas de una en una |
| Generador | `gemini-3.5-flash-lite` |
| Juez | `gemini-3.8-flash` |
| Cada repeticion | 2 casos, 3 respuestas, cobertura 2/2, revision independiente 3/3 |
| Presupuesto por repeticion | Maximo 4 llamadas de generacion y 1 del juez |
| Presupuesto nuevo total | Maximo 12 generacion + 3 juez = 15 API |
| Historial previo | 8 API; maximo 23 si se utiliza todo el presupuesto propuesto |
| Reintentos automaticos | 0 |
| Tiempo configurado | 60 segundos |
| Traza | Obligatoria, junto con informes, SHA y digests |
| Detencion | Ante cualquier fallo, error, juicio adverso, pendiente o conflicto |

Exigir cero fallos mecanicos y del juez en cada nueva repeticion, cobertura
2/2 y 3/3 juicios independientes favorables. Revisar cada resultado antes de
iniciar el siguiente. Todos los intentos se conservan, incluidos los fallidos.
La generacion anterior y su revision recuperada son evidencia separada;
no se reetiquetan como una ejecucion sin errores ni se duplican sus partes
para cumplir el criterio global de 36.

Solo se repiten los dos casos dirigidos. El conjunto offline aceptado conserva
22/22, 548/548 y 36/36. No hay cambios de codigo, fixtures, motor o produccion.
El ejecutor original y sus diez huellas siguen iguales; su preflight con
`-DiagnosticoTanda4 -ModeloJuez gemini-3.8-flash -MostrarPlan` se verifico sin
clave ni API. El plan original del 9-oct permanece intacto.

Siguiente accion: aprobar o rechazar esta propuesta. La autorizacion anterior
cubria una sola llamada suplementaria sobre respuestas guardadas y ya se uso;
no autoriza estas nuevas generaciones ni los 15 intentos de API propuestos.

El codigo de revision 1 de una muestra aislada puede corresponder al criterio
global de 36 partes. Aceptar cada repeticion solo por sus controles, cobertura,
3/3 juicios independientes, SHA/digests/traza y ausencia de errores o conflictos;
no decidirlo solo por ese codigo de salida.
