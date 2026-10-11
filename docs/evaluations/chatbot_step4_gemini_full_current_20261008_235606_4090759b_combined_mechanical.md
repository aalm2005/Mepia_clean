# Consolidado mecánico de las cuatro tandas Gemini

Casos: 28/28; partes: 36/36.
Cobertura respondible: 21/22.
Controles aprobados: 544/547; tres fallos.
Llamadas históricas de generación: 54; llamadas nuevas de esta consolidación: 0.

La [revisión independiente consolidada](chatbot_step4_gemini_full_current_20261008_235606_4090759b_combined.md) registra 35/36 favorables, un juicio adverso y diez llamadas históricas del juez. Paso 4 no validado.

## Por tanda

| Tanda | Casos | Partes | Cobertura | Controles | Generación |
|---|---|---|---|---|---|
| 1 | 7 | 7 | 7/7 | 118/118 | 14 |
| 2 | 7 | 7 | 1/1 | 102/102 | 12 |
| 3 | 7 | 10 | 6/6 | 145/145 | 14 |
| 4 | 7 | 12 | 7/8 | 179/182 | 14 |

## Fallos

| Caso | Parte | Control | Detalle |
|---|---|---|---|
| same_day_result_and_report | 1 | answerable_coverage | generación=fallback; claims=0 |
| same_day_result_and_report | 1 | provider_generation | generación=fallback; motivos=['unsupported_or_prohibited_claim'] |
| arithmetic_division | 0 | provider_generation | generación=fallback; motivos=['unsupported_or_prohibited_claim'] |

## Fuentes conservadas

- [chatbot_step4_gemini_full_batch1_20261008_231009_cae0310c](chatbot_step4_gemini_full_batch1_20261008_231009_cae0310c.json)
- [chatbot_step4_gemini_full_batch2_20261008_231955_a1e7d7bd](chatbot_step4_gemini_full_batch2_20261008_231955_a1e7d7bd.json)
- [chatbot_step4_gemini_full_batch3_20261008_232441_8d0d024f](chatbot_step4_gemini_full_batch3_20261008_232441_8d0d024f.json)
- [chatbot_step4_gemini_full_batch4_20261008_235606_4090759b](chatbot_step4_gemini_full_batch4_20261008_235606_4090759b.json)

## Alcance y limitaciones

Datos sintéticos; no se consultó producción. La negativa de respaldo ante división sigue contando como fallo de generación aunque sea segura y el juez la apruebe. El respaldo del informe no comunica su contenido. Los borradores rechazados no quedaron guardados, por lo que no se identifica su texto ni se confirma un falso positivo interno. Los intentos y sus hashes se conservan; los diagnósticos aislados no se suman como partes adicionales.
