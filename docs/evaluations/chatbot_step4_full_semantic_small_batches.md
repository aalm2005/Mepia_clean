# Revisión semántica separada de N15

Casos: 12; partes: 18; llamadas de generación: 23; llamadas del juez: 4.
Cobertura respondible: 11/12.
Juicios: 4 favorables, 1 adversos, 13 pendientes.
Fallos mecánicos confirmados: 5; falso positivo del arnés histórico: 0.
Contradicciones del juez: 0.
Paso 4: no validado.

## Juicios por caso y parte

| Caso | Parte | Juicio | Motivo |
|---|---:|---|---|
| cash_warning | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| same_day_result_and_report | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| same_day_result_and_report | 1 | not_reviewed | sin juicio ligado al informe y su digest |
| available_result_missing_report | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| available_result_missing_report | 1 | not_reviewed | sin juicio ligado al informe y su digest |
| result_and_projection | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| result_and_projection | 1 | not_reviewed | sin juicio ligado al informe y su digest |
| adversarial_metric_context | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| question_injection | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| question_injection | 1 | not_reviewed | sin juicio ligado al informe y su digest |
| metrics | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| catalog | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| explicit_date_result | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| concept_and_outside | 0 | pass | La respuesta define el ticket promedio de manera conceptual a partir de las fuentes y explica su fórmula e interpretación sin realizar cálculos. |
| concept_and_outside | 1 | pass | Reconoce correctamente que la tasa interna de retorno está fuera del dominio del motor. |
| arithmetic_division | 0 | pass | Rechaza correctamente la solicitud de cálculo aritmético de acuerdo con las políticas del sistema. |
| two_named_results | 0 | pass | Muestra el resultado del ticket promedio con su valor y unidad de forma directa sin realizar cálculos adicionales. |
| two_named_results | 1 | fail | La respuesta omite indicar el estado del resultado ('warning'), lo cual es requerido por la expectativa de la evaluación para cubrir completamente la métrica. |

## Fallos mecánicos conservados

- chatbot_step4_full_real_batch3.json · question_injection / 0: provider_generation — generación=fallback; motivos=['unsupported_or_prohibited_claim']
- chatbot_step4_full_real_batch3.json · question_injection / 1: provider_generation — generación=fallback; motivos=['unsupported_or_prohibited_claim']
- chatbot_step4_full_real_batch3.json · catalog / 0: answerable_coverage — generación=fallback; claims=0
- chatbot_step4_full_real_batch3.json · catalog / 0: provider_generation — generación=fallback; motivos=['invalid_model_draft']
- chatbot_step4_full_real_batch3.json · concept_and_outside / 1: provider_generation — generación=fallback; motivos=['unsupported_or_prohibited_claim']

## Límite

El juez es un modelo distinto del generador Flash-Lite y no recibe las decisiones del verificador interno. Puede equivocarse y no reemplaza una revisión humana. Los informes originales siguen intactos; el falso positivo de negocio equivocado se señala por separado, sin ocultarlo.
