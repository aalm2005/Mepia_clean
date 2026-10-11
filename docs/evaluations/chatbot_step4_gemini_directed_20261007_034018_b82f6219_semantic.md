# Revisión semántica separada de N15

Casos: 7; partes: 12; llamadas de generación: 7; llamadas del juez: 4.
Cobertura respondible: 0/7.
Juicios: 1 favorables, 2 adversos, 9 pendientes.
Juez de otro modelo: 3/12 partes; 1 favorables. Juez del mismo modelo: 0 partes (provisionales).
Fallos mecánicos confirmados: 19; falso positivo del arnés histórico: 0.
Contradicciones del juez: 1.
Paso 4: no validado.

## Juicios por caso y parte

| Caso | Parte | Juicio | Motivo |
|---|---:|---|---|
| report | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| outside | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| mixed | 0 | fail | Respaldo genérico para una pregunta respondible; Responde adecuadamente de manera conceptual sin realizar cálculos ni estimaciones. |
| mixed | 1 | pass | Rechaza de manera correcta la solicitud de realizar un cálculo según las restricciones de la directiva. |
| mixed | 2 | fail | Anunciar la existencia del informe sin comunicar su contenido real no satisface la pregunta y se considera una respuesta incompleta o falsa según las directrices. |
| question_injection | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| question_injection | 1 | not_reviewed | sin juicio ligado al informe y su digest |
| catalog | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| concept_and_outside | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| concept_and_outside | 1 | not_reviewed | sin juicio ligado al informe y su digest |
| two_named_results | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| two_named_results | 1 | not_reviewed | sin juicio ligado al informe y su digest |

## Fallos mecánicos conservados

- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · report / 0: answerable_coverage — generación=fallback; claims=0
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · report / 0: provider_generation — generación=fallback; motivos=['invalid_model_draft']
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · outside / 0: provider_generation — generación=fallback; motivos=['invalid_model_draft']
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · mixed / 0: answerable_coverage — generación=fallback; claims=0
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · mixed / 0: provider_generation — generación=fallback; motivos=['invalid_model_draft']
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · mixed / 1: provider_generation — generación=fallback; motivos=['invalid_model_draft']
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · mixed / 2: answerable_coverage — generación=fallback; claims=0
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · mixed / 2: provider_generation — generación=fallback; motivos=['invalid_model_draft']
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · question_injection / 0: provider_generation — generación=fallback; motivos=['invalid_model_draft']
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · question_injection / 1: provider_generation — generación=fallback; motivos=['invalid_model_draft']
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · catalog / 0: answerable_coverage — generación=fallback; claims=0
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · catalog / 0: provider_generation — generación=fallback; motivos=['invalid_model_draft']
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · concept_and_outside / 0: answerable_coverage — generación=fallback; claims=0
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · concept_and_outside / 0: provider_generation — generación=fallback; motivos=['invalid_model_draft']
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · concept_and_outside / 1: provider_generation — generación=fallback; motivos=['invalid_model_draft']
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · two_named_results / 0: answerable_coverage — generación=fallback; claims=0
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · two_named_results / 0: provider_generation — generación=fallback; motivos=['invalid_model_draft']
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · two_named_results / 1: answerable_coverage — generación=fallback; claims=0
- chatbot_step4_gemini_directed_20261007_034018_b82f6219.json · two_named_results / 1: provider_generation — generación=fallback; motivos=['invalid_model_draft']

## Límite

El juez no recibe las decisiones del verificador interno. La revisión de otro modelo todavía no cubre todas las partes. Un juez modelo puede equivocarse y no reemplaza una revisión humana. Los informes originales siguen intactos; cualquier falso positivo conocido del arnés se señala por separado, sin ocultarlo.
