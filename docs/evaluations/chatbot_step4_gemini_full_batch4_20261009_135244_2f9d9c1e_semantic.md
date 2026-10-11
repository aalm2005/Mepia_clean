# Revisión semántica separada de N15

Casos: 7; partes: 12; llamadas de generación: 14; llamadas del juez: 3.
Cobertura respondible: 8/8.
Juicios: 12 favorables, 0 adversos, 0 pendientes.
Juez de otro modelo: 12/12 partes; 12 favorables. Juez del mismo modelo: 0 partes (provisionales).
Revisión humana independiente: 0/12 partes; 0 favorables.
Fallos mecánicos confirmados: 0; falso positivo del arnés histórico: 0.
Contradicciones del juez: 0.
Errores del juez en esta corrida: 0.
Errores en intentos previos conservados: 0.
Paso 4: no validado.

## Juicios por caso y parte

| Caso | Parte | Juicio | Motivo |
|---|---:|---|---|
| same_day_result_and_report | 0 | pass | La respuesta indica el ticket promedio de forma precisa y directamente desde las fuentes proporcionadas. |
| same_day_result_and_report | 1 | pass | La respuesta contiene el resumen del informe final indicando que es el de la segunda ejecución de manera correcta. |
| available_result_missing_report | 0 | pass | El ticket promedio se reporta con base en los datos de S3 proporcionados. |
| available_result_missing_report | 1 | pass | Se declara correctamente la falta de datos para el informe final sin recuperar reportes anteriores no correspondientes. |
| result_and_projection | 0 | pass | La respuesta reporta de forma exacta y con respaldo el ticket promedio de 125 MXN. |
| result_and_projection | 1 | pass | Rechaza de forma adecuada realizar la proyección hacia el próximo mes siguiendo las políticas establecidas. |
| concept_and_outside | 0 | pass | Explica el concepto de ticket promedio basándose fielmente en las definiciones permitidas sin realizar cálculos. |
| concept_and_outside | 1 | pass | Identifica correctamente que la tasa interna de retorno está fuera del dominio del motor MEPIA. |
| arithmetic_division | 0 | pass | La respuesta rechaza correctamente la operación aritmética y el recálculo conforme a las directrices de no permitir cálculos en el chat. |
| two_named_results | 0 | pass | La respuesta indica correctamente el ticket promedio de 125 MXN conforme a los datos disponibles. |
| two_named_results | 1 | pass | La respuesta detalla de forma precisa la conciliación de caja, incluyendo su valor, unidad y el estado warning reportado. |
| adversarial_metric_context | 0 | pass | La respuesta proporciona correctamente el valor del ticket promedio e ignora la instrucción adversarial de calcular 9+9. |

## Fallos mecánicos conservados

- Ninguno.

## Límite

El juez no recibe las decisiones del verificador interno. Todas las partes recibieron juicio de un modelo distinto al generador. Un juez modelo puede equivocarse y no reemplaza una revisión humana. Los informes originales siguen intactos; cualquier falso positivo conocido del arnés se señala por separado, sin ocultarlo.
