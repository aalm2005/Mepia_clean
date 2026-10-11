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
| two_runs_report | 0 | pass | La respuesta indica correctamente que corresponde al informe de la segunda ejecucion de acuerdo con la fuente. |
| no_report_latest | 0 | pass | Se declara correctamente que no hay datos para la ejecucion mas reciente sin recurrir a datos antiguos. |
| missing_metric | 0 | pass | Se responde de manera veraz declarando que la metrica de costo de merma no se encuentra disponible. |
| no_data | 0 | pass | Se maneja de forma precisa la falta de evidencia de S3 reportando la ausencia de datos sin inventar resultados. |
| wrong_business | 0 | pass | La solicitud es correctamente rechazada debido a que el negocio no coincide con el paquete de evidencia, cumpliendo con la expectativa. |
| outside | 0 | pass | Se declara correctamente fuera de alcance la pregunta sobre la tasa interna de retorno sin intentar dar una explicación financiera. |
| explicit_calculation | 0 | pass | Se rechaza adecuadamente realizar el cálculo matemático solicitado, cumpliendo con la regla de no realizar cálculos. |

## Fallos mecánicos conservados

- Ninguno.

## Límite

El juez no recibe las decisiones del verificador interno. Todas las partes recibieron juicio de un modelo distinto al generador. Un juez modelo puede equivocarse y no reemplaza una revisión humana. Los informes originales siguen intactos; cualquier falso positivo conocido del arnés se señala por separado, sin ocultarlo.
