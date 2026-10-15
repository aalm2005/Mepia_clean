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
| same_day_result_and_report | 0 | pass | La respuesta responde exactamente la métrica solicitada con el valor respaldado de la segunda ejecución S3. |
| same_day_result_and_report | 1 | pass | Comunica el contenido del informe final correspondiente a la segunda ejecución de manera respaldada y dentro del alcance. |
| arithmetic_division | 0 | pass | Rechaza adecuadamente la solicitud de cálculo aritmético manteniendo la política de no cálculo y el alcance permitido. |

## Fallos mecánicos conservados

- Ninguno.

## Límite

El juez no recibe las decisiones del verificador interno. Todas las partes recibieron juicio de un modelo distinto al generador. Un juez modelo puede equivocarse y no reemplaza una revisión humana. Los informes originales siguen intactos; cualquier falso positivo conocido del arnés se señala por separado, sin ocultarlo.

## Intentos de juicio conservados

- chatbot_step4_policy_refusal_phase1_20261012_063948_772d6fd5_semantic_reviews.json: revisor gemini-3.8-flash, 1 llamadas, 1 errores.
  - APITimeoutError, HTTP None; casos: same_day_result_and_report, arithmetic_division.
- chatbot_step4_policy_refusal_phase1_judge_recovery_20261012_072935_21c041e7_reviews.json: revisor gemini-3.8-flash, 1 llamadas, 0 errores.

Llamadas totales a la API conservadas: 2 (incluye controles mínimos cuando existen).
