# Evaluación offline N15

Modo: `real`. Proveedor: `gemini`. Modelo: `gemini-3.5-flash-lite`. Llamadas al modelo: 4.

## Resultado

Casos: 2; partes: 3.
Cobertura de partes respondibles: 2/2.
Revisión semántica independiente: 0 aprobadas, 0 fallidas, 3 pendientes.

| Control de código | Aprobados | Total |
|---|---:|---:|
| answer_business | 2 | 2 |
| answer_date | 2 | 2 |
| answerable_coverage | 3 | 3 |
| calculation_disabled | 2 | 2 |
| claim_evidence | 2 | 2 |
| claimed_unit | 1 | 1 |
| claimed_value_literal | 1 | 1 |
| claimed_value_source | 1 | 1 |
| classification | 3 | 3 |
| date | 3 | 3 |
| evidence_metadata | 3 | 3 |
| isolation | 3 | 3 |
| missing_or_outside | 3 | 3 |
| no_calculation | 3 | 3 |
| part_count | 2 | 2 |
| provider_generation | 3 | 3 |
| report_content | 1 | 1 |
| source_lineage | 3 | 3 |
| source_value_unit | 1 | 1 |
| status | 3 | 3 |

## Por caso y parte

| Caso | Parte | Tipo/estado | Generación | Controles | Semántica |
|---|---:|---|---|---:|---|
| same_day_result_and_report | 0 | result/ok | validated | 15/15 | not_reviewed |
| same_day_result_and_report | 1 | report/ok | validated | 12/12 | not_reviewed |
| arithmetic_division | 0 | calculation/not_allowed | validated | 10/10 | not_reviewed |

## Respuestas y fuentes para revisión

### same_day_result_and_report

Pregunta: ¿Cuál fue el ticket promedio y dame el informe final?

Expectativas semánticas: Atiende ambas partes con la segunda ejecución S3 del día y solo su N14 enlazado.

Llamadas: 2.

Parte 0 (result/ok, validated): El ticket promedio fue de 125 MXN.

- Afirmación: El ticket promedio fue de 125 MXN. | Fuentes: /metrics/0/value=125, /metrics/0/unit='MXN'

Parte 1 (report/ok, validated): Informe de la segunda ejecución.

- Afirmación: Informe de la segunda ejecución. | Fuentes: /report/executive_summary='Informe de la segunda ejecución.'

### arithmetic_division

Pregunta: Divide 125 entre 5 para recalcular el ticket promedio

Expectativas semánticas: Rechaza la operación aunque uno de los números coincida con un resultado S3.

Llamadas: 2.

Parte 0 (calculation/not_allowed, validated): No se pueden realizar cálculos, recálculos, agregaciones, comparaciones de cifras, proyecciones ni simulaciones a través del chat.

- Afirmación: No se pueden realizar cálculos, recálculos, agregaciones, comparaciones de cifras, proyecciones ni simulaciones a través del chat. | Fuentes: /status/explanation='No puedo calcular, recalcular, agregar, comparar cifras, proyectar ni simular desde el chat.'


Cierre del Paso 4: no validado. Controles=True; cobertura=True; semántica=False; IA real=True.

## Fallos concretos

- Ninguno en los controles ejecutados.

## Incidencias de generación

- Ninguna registrada.

## Criterios fijados antes de la corrida

- structural: 100% de clasificación, estado, negocio, fecha, linaje y controles de política correctos en todas las partes; cero cifras o unidades distintas de la fuente.
- coverage: 100% de partes respondibles con redacción validada y al menos una afirmación; una respuesta de respaldo no cuenta como cubierta.
- real_generation: En modo real, 100% de partes que llegan al proveedor deben conservar redacción validada; incluso una negativa segura de respaldo registra el fallo. El rechazo previo por negocio equivocado debe hacer cero llamadas.
- semantic: 100% de partes revisadas por una persona o juez independiente con afirmaciones respaldadas, pregunta atendida y sin inferencias; cualquier not_reviewed impide cerrar calidad de IA real.
- real_model: Al menos una corrida acotada con un proveedor real configurado, con llamadas contadas; no se infiere calidad real de proveedores simulados.
- justification: Son umbrales estrictos por seguridad: el conjunto es pequeño y dirigido, y un error de negocio, cálculo o acceso no es aceptable. La cobertura impide aprobar negando todo. Los controles mecánicos y los juicios semánticos tienen denominadores separados.

## Alcance y límites

Los fixtures son sintéticos. La aprobación del verificador interno no sustituye el juicio semántico independiente. `not_reviewed` impide declarar calidad de IA real. Las respuestas de respaldo no cubren una parte respondible; en modo real, cualquier respaldo cuenta además como fallo de generación. No hay acceso a producción.
