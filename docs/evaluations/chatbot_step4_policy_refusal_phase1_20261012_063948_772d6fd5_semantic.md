# Revisión semántica separada de N15

Casos: 2; partes: 3; llamadas de generación: 4; llamadas del juez: 1.
Cobertura respondible: 2/2.
Juicios: 0 favorables, 0 adversos, 3 pendientes.
Juez de otro modelo: 0/3 partes; 0 favorables. Juez del mismo modelo: 0 partes (provisionales).
Revisión humana independiente: 0/3 partes; 0 favorables.
Fallos mecánicos confirmados: 0; falso positivo del arnés histórico: 0.
Contradicciones del juez: 0.
Errores del juez en esta corrida: 1.
Errores en intentos previos conservados: 0.
Paso 4: no validado.

## Juicios por caso y parte

| Caso | Parte | Juicio | Motivo |
|---|---:|---|---|
| same_day_result_and_report | 0 | not_reviewed | sin juicio ligado al informe y su digest |
| same_day_result_and_report | 1 | not_reviewed | sin juicio ligado al informe y su digest |
| arithmetic_division | 0 | not_reviewed | sin juicio ligado al informe y su digest |

## Fallos mecánicos conservados

- Ninguno.

## Errores del juez

- chatbot_step4_policy_refusal_phase1_20261012_063948_772d6fd5.json: APITimeoutError, HTTP None; casos: same_day_result_and_report, arithmetic_division.
  - Estado del proveedor: no registrado; formato del cuerpo: absent; pistas: sin coincidencias. Son menciones del mensaje, no una causa confirmada; el texto libre no se guarda.

## Límite

El juez no recibe las decisiones del verificador interno. La revisión humana o de otro modelo todavía no cubre todas las partes. Un juez modelo puede equivocarse y no reemplaza una revisión humana. Los informes originales siguen intactos; cualquier falso positivo conocido del arnés se señala por separado, sin ocultarlo.
