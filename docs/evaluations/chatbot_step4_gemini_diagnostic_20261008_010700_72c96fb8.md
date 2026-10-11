# Evaluación offline N15

Modo: `real`. Proveedor: `gemini`. Modelo: `gemini-3.5-flash-lite`. Llamadas al modelo: 2.

## Resultado

Casos: 1; partes: 1.
Cobertura de partes respondibles: 1/1.
Revisión semántica independiente: 0 aprobadas, 0 fallidas, 1 pendientes.

| Control de código | Aprobados | Total |
|---|---:|---:|
| answer_business | 1 | 1 |
| answer_date | 1 | 1 |
| answerable_coverage | 1 | 1 |
| calculation_disabled | 1 | 1 |
| claim_evidence | 1 | 1 |
| claimed_unit | 1 | 1 |
| claimed_value_literal | 1 | 1 |
| claimed_value_source | 1 | 1 |
| classification | 1 | 1 |
| date | 1 | 1 |
| evidence_metadata | 1 | 1 |
| isolation | 1 | 1 |
| missing_or_outside | 1 | 1 |
| no_calculation | 1 | 1 |
| part_count | 1 | 1 |
| provider_generation | 1 | 1 |
| source_lineage | 1 | 1 |
| source_value_unit | 1 | 1 |
| status | 1 | 1 |

## Por caso y parte

| Caso | Parte | Tipo/estado | Generación | Controles | Semántica |
|---|---:|---|---|---:|---|
| explicit_date_result | 0 | result/ok | validated | 15/15 | not_reviewed |

## Respuestas y fuentes para revisión

### explicit_date_result

Pregunta: ¿Cuál fue el ticket promedio del 24 de septiembre de 2026?

Expectativas semánticas: Conserva la fecha consultada, la fuente S3 y los 125 MXN emitidos; no calcula con la fecha.

Llamadas: 2.

Parte 0 (result/ok, validated): El ticket promedio fue de 125 MXN.

- Afirmación: El ticket promedio fue de 125 MXN. | Fuentes: /metrics/0/value=125, /metrics/0/unit='MXN'


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
