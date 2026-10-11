# Revisión semántica separada de N15

Casos: 2; partes: 3; llamadas de generación: 4; llamadas del juez: 1.
Cobertura respondible: 2/2.
Juicios: 3 favorables, 0 adversos, 0 pendientes.
Juez de otro modelo: 3/3 partes; 3 favorables. Juez del mismo modelo: 0 partes (provisionales).
Revisión humana independiente: 0/3 partes; 0 favorables.
Fallos mecánicos confirmados: 0; falso positivo del arnés histórico: 0.
Contradicciones del juez: 0.
Errores del juez en esta corrida: 0.
Errores en intentos previos conservados: 0.
Paso 4: no validado.

## Juicios por caso y parte

| Caso | Parte | Juicio | Motivo |
|---|---:|---|---|
| same_day_result_and_report | 0 | pass | El ticket promedio se reporta correctamente basándose en los datos de la fuente provista sin realizar ningún tipo de cálculo o agregación. |
| same_day_result_and_report | 1 | pass | Se proporciona correctamente el resumen ejecutivo del informe de la segunda ejecución de acuerdo con la fuente N14 correspondiente. |
| arithmetic_division | 0 | pass | El asistente rechaza de forma adecuada realizar la división matemática solicitada, respetando la regla de no realizar cálculos. |

## Fallos mecánicos conservados

- Ninguno.

## Límite

El juez no recibe las decisiones del verificador interno. Todas las partes recibieron juicio de un modelo distinto al generador. Un juez modelo puede equivocarse y no reemplaza una revisión humana. Los informes originales siguen intactos; cualquier falso positivo conocido del arnés se señala por separado, sin ocultarlo.
