# Serie nueva autorizada con juez Gemini 3.8 — 11-oct-2026

Autorizacion del usuario: «Si, tres repeticiones con Gemini 3.8
(maximo 15 llamadas adicionales)». Aun no se ejecuto ninguna repeticion nueva.
La propuesta anterior y el plan original del 9-oct se conservan.

| Control | Limite autorizado |
|---|---|
| Repeticiones | 3, de una en una, con auditoria entre ellas |
| Casos | `same_day_result_and_report` y `arithmetic_division` |
| Cada repeticion | 2 casos, 3 respuestas, 2 respondibles |
| Generador | `gemini-3.5-flash-lite` |
| Juez | `gemini-3.8-flash` |
| Cada intento | Maximo 4 llamadas de generacion y 1 del juez |
| Serie nueva completa | Maximo 12 gen/3 juez, 15 API adicionales |
| Historial previo | 8 API; maximo acumulado 23 si se usa todo el presupuesto nuevo |
| Reintentos automaticos | 0 |
| Tiempo configurado | 60 segundos |
| Traza | Obligatoria |
| Detencion | Ante cualquier fallo, error, juicio adverso, pendiente o conflicto |

Exigir cero fallos mecanicos y del juez, cobertura 2/2 y 3/3 juicios
independientes favorables, ligados al SHA/digest y traza de cada nueva
repeticion. El codigo de revision 1 de una muestra aislada puede corresponder
al criterio global de 36 partes: revisar los contadores y la evidencia.
La generacion recuperada anterior se conserva como evidencia separada y no
cuenta como una repeticion sin errores. El conjunto offline aceptado mantiene
22/22, 548/548 y 36/36; solo se repiten estos dos casos.

## Primera repeticion

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Documentos\PROYECTO INTEGRADOR 2\chatbot_paso4_continuacion\.test_tmp\probar_consistencia_juez38.ps1" -Repeticion 1
```

Introducir la clave actual de forma oculta cuando la solicite. El ejecutor
original la usa solo temporalmente en el proceso. Compartir el resultado para
la auditoria antes de la repeticion 2. La autorizacion ya cubre las tres
repeticiones dentro de estos limites; no pedir otra aprobacion entre exitos.

El envoltorio crea un registro de intento exclusivo antes de llamar al
proveedor; impide repetir una misma posicion y bloquea las posteriores hasta
que su predecesora tenga una auditoria aprobada. Si el proceso se interrumpe,
inspeccionar el registro y los informes antes de nuevas llamadas. No asumir
cero llamadas cuando un intento queda incompleto.

Sintaxis, preflight de las tres posiciones y bloqueo de la posicion 2 antes
de solicitar clave correctos, cero API. Diez huellas del plan original y
SHA del envoltorio comprobados. Fuente de avance:
`chatbot_step4_consistency_judge38_series_progress_20261011.json`.
Codigo y fixtures originales sin cambios; suite no repetida.
`codex/chatbot-q4`, HEAD `6fa66bc`, sin commit del seguimiento.
INC-20260930-016 mitigada; 20 incidencias resueltas y una mitigada.
