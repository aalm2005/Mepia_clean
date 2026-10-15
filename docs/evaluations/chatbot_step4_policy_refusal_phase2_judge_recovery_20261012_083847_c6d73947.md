# Revisión semántica separada de N15

Casos: 5; partes: 9; llamadas de generación: 10; llamadas del juez: 1.
Cobertura respondible: 3/3.
Juicios: 0 favorables, 0 adversos, 9 pendientes.
Juez de otro modelo: 0/9 partes; 0 favorables. Juez del mismo modelo: 0 partes (provisionales).
Revisión humana independiente: 0/9 partes; 0 favorables.
Fallos mecánicos confirmados: 0; falso positivo del arnés histórico: 0.
Contradicciones del juez: 0.
Errores del juez en esta corrida: 1.
Errores en intentos previos conservados: 0.
Paso 4: no validado.

## Juicios por caso y parte

| Caso | Parte | Juicio | Motivo |
|---|---:|---|---|
| explicit_calculation | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| implicit_calculation | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| mixed | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| mixed | 1 | not_reviewed | sin juicio ligado al informe y su digest |
| mixed | 2 | not_reviewed | sin juicio ligado al informe y su digest |
| question_injection | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| question_injection | 1 | not_reviewed | sin juicio ligado al informe y su digest |
| result_and_projection | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| result_and_projection | 1 | not_reviewed | sin juicio ligado al informe y su digest |

## Fallos mecánicos conservados

- Ninguno.

## Errores del juez

- chatbot_step4_policy_refusal_phase2_20261012_074133_e8482e9d.json: InternalServerError, HTTP 503; casos: explicit_calculation, implicit_calculation.
  - Estado del proveedor: UNAVAILABLE; formato del cuerpo: array; pistas: provider_message_mentions_capacity. Son menciones del mensaje, no una causa confirmada; el texto libre no se guarda.

## Límite

El juez no recibe las decisiones del verificador interno. La revisión humana o de otro modelo todavía no cubre todas las partes. Un juez modelo puede equivocarse y no reemplaza una revisión humana. Los informes originales siguen intactos; cualquier falso positivo conocido del arnés se señala por separado, sin ocultarlo.
