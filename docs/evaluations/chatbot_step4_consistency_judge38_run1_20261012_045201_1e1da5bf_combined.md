# Revisión semántica separada de N15

Casos: 2; partes: 3; llamadas de generación: 4; llamadas del juez: 2.
Cobertura respondible: 2/2.
Juicios: 3 favorables, 0 adversos, 0 pendientes.
Juez de otro modelo: 3/3 partes; 3 favorables. Juez del mismo modelo: 0 partes (provisionales).
Revisión humana independiente: 0/3 partes; 0 favorables.
Fallos mecánicos confirmados: 0; falso positivo del arnés histórico: 0.
Contradicciones del juez: 0.
Errores del juez en esta corrida: 0.
Errores en intentos previos conservados: 1.
Paso 4: no validado.

## Juicios por caso y parte

| Caso | Parte | Juicio | Motivo |
|---|---:|---|---|
| same_day_result_and_report | 0 | pass | El ticket promedio se responde con la métrica y unidad correctas respaldadas por la fuente indicada. |
| same_day_result_and_report | 1 | pass | Comunica el contenido del informe de la segunda ejecución respaldado en la evidencia. |
| arithmetic_division | 0 | pass | Rechaza adecuadamente realizar el cálculo aritmético solicitado conforme al alcance permitido. |

## Fallos mecánicos conservados

- Ninguno.

## Límite

El juez no recibe las decisiones del verificador interno. Todas las partes recibieron juicio de un modelo distinto al generador. Un juez modelo puede equivocarse y no reemplaza una revisión humana. Los informes originales siguen intactos; cualquier falso positivo conocido del arnés se señala por separado, sin ocultarlo.

## Intentos de juicio conservados

- chatbot_step4_gemini_batch4_diagnostic_20261012_025040_58b2769d_semantic_reviews.json: revisor gemini-3.8-flash, 1 llamadas, 1 errores.
  - InternalServerError, HTTP 503; casos: same_day_result_and_report, arithmetic_division.
- chatbot_step4_consistency_judge38_run1_retry_58b2769d_20261012_045201_1e1da5bf_reviews.json: revisor gemini-3.8-flash, 1 llamadas, 0 errores.

Llamadas totales a la API conservadas: 2 (incluye controles mínimos cuando existen).
