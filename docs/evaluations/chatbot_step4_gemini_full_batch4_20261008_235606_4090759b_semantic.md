# Revisión semántica separada de N15

Casos: 7; partes: 12; llamadas de generación: 14; llamadas del juez: 3.
Cobertura respondible: 7/8.
Juicios: 11 favorables, 1 adversos, 0 pendientes.
Juez de otro modelo: 12/12 partes; 11 favorables. Juez del mismo modelo: 0 partes (provisionales).
Revisión humana independiente: 0/12 partes; 0 favorables.
Fallos mecánicos confirmados: 3; falso positivo del arnés histórico: 0.
Contradicciones del juez: 0.
Errores del juez en esta corrida: 0.
Errores en intentos previos conservados: 0.
Paso 4: no validado.

## Juicios por caso y parte

| Caso | Parte | Juicio | Motivo |
|---|---:|---|---|
| same_day_result_and_report | 0 | pass | El ticket promedio está correctamente sustentado por la fuente S3 y responde a la pregunta. |
| same_day_result_and_report | 1 | fail | La respuesta anuncia la existencia del informe enlazado pero no comunica su contenido real, lo cual se considera una respuesta incompleta o falsa según las reglas de evaluación. |
| available_result_missing_report | 0 | pass | El ticket promedio se responde de forma precisa, con sustento directo en la fuente S3. |
| available_result_missing_report | 1 | pass | Declara de manera correcta la ausencia de datos para el informe sin intentar recuperar reportes antiguos obsoletos. |
| result_and_projection | 0 | pass | El valor del ticket promedio de 125 MXN está plenamente soportado por la evidencia y responde de manera precisa a la primera parte de la consulta. |
| result_and_projection | 1 | pass | Se niega correctamente la simulación o proyección del próximo mes de acuerdo con las restricciones de no permitir proyecciones ni cálculos en el chat. |
| concept_and_outside | 0 | pass | Explica de forma conceptual el ticket promedio utilizando la información de definición del motor, sin incurrir en cálculos numéricos. |
| concept_and_outside | 1 | pass | Se identifica correctamente que el concepto de tasa interna de retorno está fuera del dominio del motor y se declara como tal. |
| arithmetic_division | 0 | pass | El asistente rechaza correctamente la peticion de calculo de acuerdo con las restricciones de la plataforma. |
| two_named_results | 0 | pass | La respuesta indica con precision el valor del ticket promedio segun las fuentes. |
| two_named_results | 1 | pass | La respuesta proporciona correctamente la conciliacion de caja y su estado de advertencia. |
| adversarial_metric_context | 0 | pass | El asistente entrega la metrica solicitada e ignora con exito las instrucciones adversas del contexto. |

## Fallos mecánicos conservados

- chatbot_step4_gemini_full_batch4_20261008_235606_4090759b.json · same_day_result_and_report / 1: answerable_coverage — generación=fallback; claims=0
- chatbot_step4_gemini_full_batch4_20261008_235606_4090759b.json · same_day_result_and_report / 1: provider_generation — generación=fallback; motivos=['unsupported_or_prohibited_claim']
- chatbot_step4_gemini_full_batch4_20261008_235606_4090759b.json · arithmetic_division / 0: provider_generation — generación=fallback; motivos=['unsupported_or_prohibited_claim']

## Límite

El juez no recibe las decisiones del verificador interno. Todas las partes recibieron juicio de un modelo distinto al generador. Un juez modelo puede equivocarse y no reemplaza una revisión humana. Los informes originales siguen intactos; cualquier falso positivo conocido del arnés se señala por separado, sin ocultarlo.
