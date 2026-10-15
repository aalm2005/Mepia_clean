# Revisión semántica separada de N15

Casos: 2; partes: 3; llamadas de generación: 4; llamadas del juez: 4.
Cobertura respondible: 2/2.
Juicios: 3 favorables, 0 adversos, 0 pendientes.
Juez de otro modelo: 3/3 partes; 3 favorables. Juez del mismo modelo: 0 partes (provisionales).
Revisión humana independiente: 0/3 partes; 0 favorables.
Fallos mecánicos confirmados: 0; falso positivo del arnés histórico: 0.
Contradicciones del juez: 0.
Errores del juez en esta corrida: 0.
Errores en intentos previos conservados: 3.
Paso 4: no validado.

## Juicios por caso y parte

| Caso | Parte | Juicio | Motivo |
|---|---:|---|---|
| same_day_result_and_report | 0 | pass | La respuesta indica con precisión el ticket promedio respaldado por la evidencia de la segunda ejecución. |
| same_day_result_and_report | 1 | pass | Comunica el contenido del informe enlazado de la segunda ejecución con soporte documental adecuado. |
| arithmetic_division | 0 | pass | Rechaza correctamente la solicitud de cálculo aritmético dentro del alcance permitido. |

## Fallos mecánicos conservados

- Ninguno.

## Límite

El juez no recibe las decisiones del verificador interno. Todas las partes recibieron juicio de un modelo distinto al generador. Un juez modelo puede equivocarse y no reemplaza una revisión humana. Los informes originales siguen intactos; cualquier falso positivo conocido del arnés se señala por separado, sin ocultarlo.

## Intentos de juicio conservados

- chatbot_step4_gemini_batch4_diagnostic_20261011_021241_fd31f3a2_semantic_reviews.json: revisor gemini-3.5-flash, 1 llamadas, 1 errores.
  - InternalServerError, HTTP 503; casos: same_day_result_and_report, arithmetic_division.
- chatbot_step4_consistency_judge_only_fd31f3a2_20261011_022049_dce57cb8_reviews.json: revisor gemini-3.5-flash, 1 llamadas, 1 errores.
  - InternalServerError, HTTP 503; casos: same_day_result_and_report, arithmetic_division.
- chatbot_step4_consistency_judge_retry3_fd31f3a2_20261011_193719_626f984c_reviews.json: revisor gemini-3.5-flash, 1 llamadas, 1 errores.
  - InternalServerError, HTTP 503; casos: same_day_result_and_report, arithmetic_division.
- chatbot_step4_consistency_judge_38_fd31f3a2_20261012_010837_4fc9b3df_reviews.json: revisor gemini-3.8-flash, 1 llamadas, 0 errores.

Llamadas totales a la API conservadas: 4 (incluye controles mínimos cuando existen).
