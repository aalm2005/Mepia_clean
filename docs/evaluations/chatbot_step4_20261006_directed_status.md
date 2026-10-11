# Paso 4 — estado de la muestra dirigida (6-oct-2026)

Rama `codex/chatbot-q4`; HEAD `7c2d307`; cambios sin commit.

## Intento real actual

El CLI recibió los siete IDs mediante `--real-case-ids`, con límite de 14 llamadas de generación. Salió con código 2 antes de llamar al proveedor porque faltaban `MEPIA_CHAT_EVAL_API_KEY` y `GEMINI_API_KEY` en este proceso. **0/14 llamadas consumidas**. Presupuesto previsto del juez externo: **4 llamadas**, 0 consumidas; no hay respuestas nuevas que juzgar.

## Denominadores y resultados

Siete casos, 12 partes, 7 respondibles. La evidencia histórica Gemini en estos casos usó 13 llamadas, cubrió 4/7 respondibles, tuvo 10 fallos mecánicos y 4/12 juicios semánticos adversos. El juez fue de otro modelo en 9/12 partes; los otros 3 juicios son provisionales por usar el modelo generador. Los resultados originales permanecen en sus informes del 30-sep-2026.

Las dos simulaciones actuales cubrieron cada una 7/7 respondibles y tuvieron 0 fallos mecánicos; 12/12 juicios independientes continúan pendientes. No son una nueva medición con Gemini.

| Caso | Parte | Respondible | Gemini histórico | Fallos mecánicos históricos | Juicio histórico | Simulación actual A/B |
|---|---:|---|---|---|---|---|
| report | 0 | sí | fallback | answerable_coverage, provider_generation | fail | validated/validated |
| mixed | 0 | sí | validated | ninguno | pass | validated/validated |
| mixed | 1 | no | validated | ninguno | pass | validated/validated |
| mixed | 2 | sí | fallback | answerable_coverage, provider_generation | fail | validated/validated |
| catalog | 0 | sí | fallback | answerable_coverage, provider_generation | fail | validated/validated |
| outside | 0 | no | fallback | provider_generation | pass | validated/validated |
| question_injection | 0 | no | fallback | provider_generation | pass | validated/validated |
| question_injection | 1 | no | fallback | provider_generation | pass | validated/validated |
| concept_and_outside | 0 | sí | validated | ninguno | pass | validated/validated |
| concept_and_outside | 1 | no | fallback | provider_generation | pass | validated/validated |
| two_named_results | 0 | sí | validated | ninguno | pass | validated/validated |
| two_named_results | 1 | sí | validated | ninguno | fail | validated/validated |

## Pruebas locales

69 focalizadas y 24 subpruebas aprobadas en 9.31 s; suite general: 210 aprobadas, una integración opt-in omitida y 90 subpruebas aprobadas en 60.34 s.

## Evidencia y límites

- Fallos por parte y diagnósticos seguros: [JSON de este estado](chatbot_step4_20261006_directed_status.json).
- Corridas actuales completas: `chatbot_step4_20261006_simulated_a`, `chatbot_step4_20261006_simulated_b` y `chatbot_step4_20261006_fallback` (pares JSON/Markdown). El respaldo cubrió 0/22 en el conjunto completo y registró 22 fallos esperados.
- Los borradores rechazados no constan en los informes históricos. Los códigos de diagnóstico no prueban el contenido ni la causa semántica exacta del rechazo.
- La evaluación real del código ajustado el 4-oct y su revisión semántica independiente continúan pendientes. Paso 4 no validado.
