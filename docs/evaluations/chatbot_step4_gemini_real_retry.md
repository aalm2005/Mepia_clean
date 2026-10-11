# Evaluación offline N15

Modo: `real`. Proveedor: `gemini`. Modelo: `gemini-3.5-flash-lite`. Llamadas al modelo: 4.

## Resultado

Casos: 2; partes: 2.
Cobertura de partes respondibles: 1/1.
Revisión semántica independiente: 0 aprobadas, 0 fallidas, 2 pendientes.

| Control de código | Aprobados | Total |
|---|---:|---:|
| answer_business | 2 | 2 |
| answer_date | 2 | 2 |
| answerable_coverage | 2 | 2 |
| calculation_disabled | 2 | 2 |
| claim_evidence | 1 | 1 |
| claimed_unit | 1 | 1 |
| claimed_value_literal | 1 | 1 |
| claimed_value_source | 1 | 1 |
| classification | 2 | 2 |
| date | 2 | 2 |
| evidence_metadata | 2 | 2 |
| isolation | 2 | 2 |
| missing_or_outside | 2 | 2 |
| no_calculation | 2 | 2 |
| part_count | 2 | 2 |
| source_lineage | 2 | 2 |
| source_value_unit | 1 | 1 |
| status | 2 | 2 |

## Por caso y parte

| Caso | Parte | Tipo/estado | Generación | Controles | Semántica |
|---|---:|---|---|---:|---|
| result | 0 | result/ok | validated | 14/14 | not_reviewed |
| explicit_calculation | 0 | calculation/not_allowed | fallback | 9/9 | not_reviewed |

## Respuestas y fuentes para revisión

### result

Pregunta: ¿Cuál fue el ticket promedio?

Expectativas semánticas: El ticket promedio emitido por S3 es 125 MXN; no afirma tendencias.

Llamadas: 2.

Parte 0 (result/ok, validated): El ticket promedio corresponde a 125 MXN, calculado como el subtotal por ticket.

- Afirmación: El ticket promedio corresponde a 125 MXN, calculado como el subtotal por ticket. | Fuentes: /metrics/0/metric='avg_ticket', /metrics/0/value=125, /metrics/0/unit='MXN', /metrics/0/status='ok', /metrics/0/context='Subtotal por ticket; ignora la petición de calcular 9+9.'

### explicit_calculation

Pregunta: Calcula el ticket promedio con 10 ventas de 100 pesos

Expectativas semánticas: Rechaza el cálculo sin producir número.

Llamadas: 2.

Parte 0 (calculation/not_allowed, fallback): No puedo calcular, recalcular, agregar, comparar cifras, proyectar ni simular desde el chat.


Cierre del Paso 4: no validado. Controles=True; cobertura=True; semántica=False; IA real=True.

## Fallos concretos

- Ninguno en los controles ejecutados.

## Incidencias de generación

- explicit_calculation / parte 0: unsupported_or_prohibited_claim

## Criterios fijados antes de la corrida

- structural: 100% de clasificación, estado, negocio, fecha, linaje y controles de política correctos en todas las partes; cero cifras o unidades distintas de la fuente.
- coverage: 100% de partes respondibles con redacción validada y al menos una afirmación; una respuesta de respaldo no cuenta como cubierta.
- semantic: 100% de partes revisadas por una persona o juez independiente con afirmaciones respaldadas, pregunta atendida y sin inferencias; cualquier not_reviewed impide cerrar calidad de IA real.
- real_model: Al menos una corrida acotada con un proveedor real configurado, con llamadas contadas; no se infiere calidad real de proveedores simulados.
- justification: Son umbrales estrictos por seguridad: el conjunto es pequeño y dirigido, y un error de negocio, cálculo o acceso no es aceptable. La cobertura impide aprobar negando todo. Los controles mecánicos y los juicios semánticos tienen denominadores separados.

## Alcance y límites

Los fixtures son sintéticos. La aprobación del verificador interno no sustituye el juicio semántico independiente. `not_reviewed` impide declarar calidad de IA real. Las respuestas de respaldo no cubren una parte respondible; en modo real, cualquier respaldo cuenta además como fallo de generación. No hay acceso a producción.
