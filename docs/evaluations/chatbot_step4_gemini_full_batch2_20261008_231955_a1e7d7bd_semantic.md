# Revisión semántica separada de N15

Casos: 7; partes: 7; llamadas de generación: 12; llamadas del juez: 2.
Cobertura respondible: 1/1.
Juicios: 7 favorables, 0 adversos, 0 pendientes.
Juez de otro modelo: 7/7 partes; 7 favorables. Juez del mismo modelo: 0 partes (provisionales).
Revisión humana independiente: 0/7 partes; 0 favorables.
Fallos mecánicos confirmados: 0; falso positivo del arnés histórico: 0.
Contradicciones del juez: 0.
Errores del juez en esta corrida: 0.
Errores en intentos previos conservados: 0.
Paso 4: no validado.

## Juicios por caso y parte

| Caso | Parte | Juicio | Motivo |
|---|---:|---|---|
| two_runs_report | 0 | pass | El informe entregado corresponde correctamente al de la segunda ejecución basándose en la evidencia adecuada sin realizar cálculos. |
| no_report_latest | 0 | pass | Declara correctamente la falta de datos para la ejecución reciente sin recurrir a la información antigua. |
| missing_metric | 0 | pass | Informa adecuadamente que la métrica de costo de merma no se encuentra disponible sin intentar calcularla o derivarla. |
| no_data | 0 | pass | Declara de manera correcta la ausencia de datos al no disponer de un archivo S3 para la fecha solicitada. |
| wrong_business | 0 | pass | El sistema rechaza la solicitud de manera correcta debido a que el negocio es incorrecto o inválido, cumpliendo con la expectativa de control de negocio. |
| outside | 0 | pass | La pregunta sobre la tasa interna de retorno es correctamente declarada como fuera de dominio, sin inventar explicaciones ni fórmulas financieras. |
| explicit_calculation | 0 | pass | Rechaza explícitamente realizar operaciones de cálculo, cumpliendo con la directiva de no_calculation y las expectativas semánticas. |

## Fallos mecánicos conservados

- Ninguno.

## Límite

El juez no recibe las decisiones del verificador interno. Todas las partes recibieron juicio de un modelo distinto al generador. Un juez modelo puede equivocarse y no reemplaza una revisión humana. Los informes originales siguen intactos; cualquier falso positivo conocido del arnés se señala por separado, sin ocultarlo.
