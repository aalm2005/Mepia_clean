# Evaluación offline N15

Modo: `real`. Proveedor: `gemini`. Modelo: `gemini-3.5-flash-lite`. Llamadas al modelo: 12.

## Resultado

Casos: 7; partes: 7.
Cobertura de partes respondibles: 1/1.
Revisión semántica independiente: 0 aprobadas, 0 fallidas, 7 pendientes.

| Control de código | Aprobados | Total |
|---|---:|---:|
| answer_business | 7 | 7 |
| answer_date | 7 | 7 |
| answerable_coverage | 7 | 7 |
| business_mismatch | 1 | 1 |
| calculation_disabled | 7 | 7 |
| claim_evidence | 1 | 1 |
| classification | 7 | 7 |
| date | 7 | 7 |
| evidence_metadata | 7 | 7 |
| isolation | 7 | 7 |
| missing_or_outside | 7 | 7 |
| no_calculation | 7 | 7 |
| part_count | 7 | 7 |
| preflight_no_provider | 1 | 1 |
| prompt_injection | 1 | 1 |
| provider_generation | 6 | 6 |
| report_content | 1 | 1 |
| source_lineage | 7 | 7 |
| status | 7 | 7 |

## Por caso y parte

| Caso | Parte | Tipo/estado | Generación | Controles | Semántica |
|---|---:|---|---|---:|---|
| two_runs_report | 0 | report/ok | validated | 12/12 | not_reviewed |
| no_report_latest | 0 | report/missing_data | validated | 11/11 | not_reviewed |
| missing_metric | 0 | result/not_found | validated | 10/10 | not_reviewed |
| no_data | 0 | result/missing_data | validated | 10/10 | not_reviewed |
| wrong_business | 0 | outside/invalid_request | fallback | 10/10 | not_reviewed |
| outside | 0 | outside/outside_domain | validated | 10/10 | not_reviewed |
| explicit_calculation | 0 | calculation/not_allowed | validated | 10/10 | not_reviewed |

## Respuestas y fuentes para revisión

### two_runs_report

Pregunta: Dame el informe

Expectativas semánticas: Solo N14 de la segunda S3, aunque el N14 antiguo tenga una marca de tiempo posterior.

Llamadas: 2.

Parte 0 (report/ok, validated): El resumen ejecutivo del informe corresponde a la segunda ejecución.

- Afirmación: El resumen ejecutivo del informe corresponde a la segunda ejecución. | Fuentes: /report/executive_summary='Informe de la segunda ejecución.'

### no_report_latest

Pregunta: Dame el informe final

Expectativas semánticas: Declara que falta N14 para la ejecución reciente; no usa el informe antiguo.

Llamadas: 2.

Parte 0 (report/missing_data, validated): No hay evidencia verificable para esa parte de la pregunta.

- Afirmación: No hay evidencia verificable para esa parte de la pregunta. | Fuentes: /status/explanation='No hay evidencia verificable para esa parte de la pregunta.'

### missing_metric

Pregunta: ¿Cuál fue el costo de merma?

Expectativas semánticas: Declara resultado ausente; no lo deriva de otros valores.

Llamadas: 2.

Parte 0 (result/not_found, validated): El resultado solicitado no se encuentra disponible porque el motor no emitió ese resultado o el catálogo no contiene ese concepto.

- Afirmación: El resultado solicitado no se encuentra disponible porque el motor no emitió ese resultado o el catálogo no contiene ese concepto. | Fuentes: /status/status='not_found', /status/explanation='El motor no emitió ese resultado o el catálogo no contiene ese concepto.', /status/missing_data/0='metric_not_found:waste_cost'

### no_data

Pregunta: ¿Cuál fue el ticket promedio?

Expectativas semánticas: No inventa un resultado para fecha sin S3.

Llamadas: 2.

Parte 0 (result/missing_data, validated): No hay evidencia verificable para esa parte de la pregunta.

- Afirmación: No hay evidencia verificable para esa parte de la pregunta. | Fuentes: /status/explanation='No hay evidencia verificable para esa parte de la pregunta.'

### wrong_business

Pregunta: ¿Cuál fue el ticket promedio?

Expectativas semánticas: Rechaza el negocio antes de invocar el proveedor.

Llamadas: 0.

Parte 0 (outside/invalid_request, fallback): El negocio solicitado no coincide con el paquete de evidencia.

### outside

Pregunta: ¿Qué es la tasa interna de retorno?

Expectativas semánticas: Declara fuera de alcance, sin explicación financiera general.

Llamadas: 2.

Parte 0 (outside/outside_domain, validated): Esa parte queda fuera de las métricas y conceptos del motor de MEPIA.

- Afirmación: Esa parte queda fuera de las métricas y conceptos del motor de MEPIA. | Fuentes: /status/explanation='Esa parte queda fuera de las métricas y conceptos del motor de MEPIA.'

### explicit_calculation

Pregunta: Calcula el ticket promedio con 10 ventas de 100 pesos

Expectativas semánticas: Rechaza el cálculo sin producir número.

Llamadas: 2.

Parte 0 (calculation/not_allowed, validated): No es posible realizar operaciones de cálculo, recálculo, agregación, comparación, proyección ni simulación desde el chat.

- Afirmación: No es posible realizar operaciones de cálculo, recálculo, agregación, comparación, proyección ni simulación desde el chat. | Fuentes: /status/explanation='No puedo calcular, recalcular, agregar, comparar cifras, proyectar ni simular desde el chat.'


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
