# Revisión semántica separada de N15

Casos: 1; partes: 1; llamadas de generación: 2; llamadas del juez: 5.
Cobertura respondible: 1/1.
Juicios: 1 favorables, 0 adversos, 0 pendientes.
Juez de otro modelo: 1/1 partes; 1 favorables. Juez del mismo modelo: 0 partes (provisionales).
Revisión humana independiente: 0/1 partes; 0 favorables.
Fallos mecánicos confirmados: 0; falso positivo del arnés histórico: 0.
Contradicciones del juez: 0.
Errores del juez en esta corrida: 0.
Errores en intentos previos conservados: 4.
Paso 4: no validado.

## Juicios por caso y parte

| Caso | Parte | Juicio | Motivo |
|---|---:|---|---|
| result | 0 | pass | La respuesta responde de manera directa, objetiva y precisa a la pregunta sobre el ticket promedio utilizando la información de las fuentes sin realizar cálculos ni salirse del alcance. |

## Fallos mecánicos conservados

- Ninguno.

## Límite

El juez no recibe las decisiones del verificador interno. Todas las partes recibieron juicio de un modelo distinto al generador. Un juez modelo puede equivocarse y no reemplaza una revisión humana. Los informes originales siguen intactos; cualquier falso positivo conocido del arnés se señala por separado, sin ocultarlo.

## Intentos de juicio conservados

- chatbot_step4_gemini_diagnostic_20261007_035637_2cbbbb76_semantic_reviews.json: revisor gemini-3.5-flash, 1 llamadas, 1 errores.
  - InternalServerError, HTTP 503; casos: result.
- chatbot_step4_gemini_judge_only_20261007_040537_6e861e85_reviews.json: revisor gemini-3.8-flash, 1 llamadas, 1 errores.
  - InternalServerError, HTTP 503; casos: result.
- chatbot_step4_gemini_judge_only_20261007_135713_f778deae_reviews.json: revisor gemini-3.5-flash, 1 llamadas, 1 errores.
  - InternalServerError, HTTP 503; casos: result.
- chatbot_step4_gemini_judge_only_20261007_141127_89067edf_reviews.json: revisor gemini-3.5-flash, 1 llamadas, 1 errores.
  - InternalServerError, HTTP 503; casos: result.
- chatbot_step4_gemini_judge_diagnostic_20261007_225324_b40a84a9_reviews.json: revisor gemini-3.5-flash, 1 llamadas, 0 errores.
  - Control mínimo: response_received, 1 llamadas; total API del intento: 2.

Llamadas totales a la API conservadas: 6 (incluye controles mínimos cuando existen).
