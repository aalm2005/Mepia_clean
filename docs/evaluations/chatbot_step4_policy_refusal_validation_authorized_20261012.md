# Validación autorizada de la guía de negativas — 12-oct-2026

Autorización: «Sí, validar el ajuste con máximo 18 llamadas adicionales».
Preparado, sin ejecutar. Gemini Lite 3.5 genera; Flash 3.8 revisa.
Timeout 60 s, cero reintentos, detener ante cualquier fallo o revisión pendiente.

| Fase | Casos | Partes | Respondibles | Generación máx. | Juez máx. | API máx. |
|---|---:|---:|---:|---:|---:|---:|
| 1: informe de dos ejecuciones y división | 2 | 3 | 2 | 4 | 1 | 5 |
| 2: las otras negativas afectadas | 5 | 9 | 3 | 10 | 3 | 13 |
| Total adicional autorizado | 7 | 12 | 5 | 14 | 4 | 18 |

Fase 1 lista; fase 2 exige auditoría favorable de la primera ligada a sus
informes y huellas. Reserva exclusiva por fase antes de pedir la clave; no
repetir un intento con el mismo ejecutor. Clave oculta temporal en el proceso.
Se omite el juez ante fallo de generación y se detiene su revisión ante el
primer lote adverso, error o salida incompleta. El criterio global de 36
partes del resumen semántico permanece; el código de salida del ejecutor
expresa únicamente si pasó la fase y todavía exige auditoría.

Solo si ambas fases pasan, la nueva generación de fase 1 reemplaza el tercer
intento fallido para calidad, junto con los dos éxitos anteriores. Esos éxitos
usaron la guía anterior: conservar ambas versiones, fuentes, errores y juicios;
no afirmar tres repeticiones aprobadas con la nueva guía. No trasladar juicios.
El tercer intento anterior sigue fallido y sus tres revisiones históricas
pendientes; no contarlas como aprobadas por un informe nuevo.

Historial previo del seguimiento: 24 API (16 generación, 8 juez). Máximo tras
esta autorización: 42; nuevas llamadas realizadas en preparación: cero.
INC-20260930-013 abierta y INC-20260930-016 pendiente externo. Versión nueva
aún sin medir con Gemini; Paso 4 no cerrado. Plan/propuesta y todos los errores
históricos preservados. Código y ejecutores congelados por SHA en el JSON.
Rama codex/chatbot-q4, HEAD 6fa66bcc6a731a3f06df79edb5a4bf62e3c8e03c, sin commit.
