# N15 — Catalogo financiero y prohibicion de calculo

**Capa:** Aplicacion | **Anterior:** S3 | **Consumidor:** nodo conversacional
**Archivos relacionados:** `n15_chat_consulta.md`,
`n15_chat_consulta_tools.md`, `agents/chat_metric_catalog.py`

## Alcance

El chatbot explica exclusivamente metricas del motor determinista y conceptos
necesarios para comprenderlas. El catalogo cubre las 31 metricas despachadas por
`GatekeeperAgent.METRICS` y cuatro calculos auxiliares reales del motor:
`contribution_margin`, `waste_analysis`, `burn_rate` y `price_inflation`.
No es un glosario financiero general.

Cada `MetricDefinition` declara identificador, nombre visible, definicion,
interpretacion, explicacion conceptual de la formula, entradas, unidades, alias,
nombres reales de `CalcResult`, conceptos relacionados, limitaciones,
disponibilidad y `calculation_owner="deterministic_engine"`.

## Regla absoluta

`calculation_allowed=false`. N15 puede recuperar resultados existentes,
explicarlos y parafrasearlos. No puede calcular, recalcular, sumar, promediar,
agregar, derivar comparaciones numericas, proyectar ni simular. Una formula del
catalogo es texto educativo, nunca una interfaz ejecutable. Si el motor no emitio
un resultado, el chatbot debe declararlo ausente y no reconstruirlo a partir de
otros valores.

Toda solicitud de calculo produce `status="not_allowed"` y
`missing_data=["calculation_not_allowed"]`. La negativa no incluye evidencia ni
un valor calculado.

El nodo del Paso 3 inspecciona cada fragmento de la pregunta antes de consultar
las herramientas. Distingue una explicación conceptual de fórmula de una
solicitud de ejecutarla. La clasificación propuesta por un proveedor no puede
anular el rechazo ni introducir cifras o afirmaciones: su salida solo contiene
tipo de consulta y selector presente en el fragmento.

La etapa posterior de redacción sí admite texto libre, explicaciones y
paráfrasis del catálogo y de resultados existentes. No impone frases
predefinidas. Cada afirmación cita fuentes y sus cantidades se insertan con
marcadores de valores originales; una revisión separada comprueba el sentido
completo. El catálogo nunca acredita un hecho particular del negocio. Un
resultado numérico ya comparado por S3/N14 puede describirse sin realizar una
comparación nueva.

## Casos historicos que deben explicarse con precision

- `operative_cost_margin` es un promedio diario de costos, no un margen
  porcentual, pese a su identificador legado.
- `health_score` es el promedio monetario de margenes de contribucion
  calculables; no es una puntuacion compuesta de salud.
- `inventory_variance` puede emitir varias salidas con prefijo
  `inventory_variance_`; no es una unica variacion global.

## Acceptance Criteria

- WHEN cambia `GatekeeperAgent.METRICS` THEN una prueba de igualdad exacta falla
  hasta actualizar y revisar el catalogo.
- WHEN se solicita una metrica por identificador, alias o nombre real de salida
  THEN la coincidencia es normalizada exacta, nunca difusa.
- WHEN se consulta un concepto ajeno al motor THEN retorna `not_found`.
- WHEN se entrega cualquier `ChatToolResult` THEN declara
  `knowledge_scope="engine_metric_domain"` y `calculation_allowed=false`.
- WHEN se explica una formula THEN se identifica como explicacion solamente.
- WHEN se redacta un catálogo extenso THEN se pueden agrupar nombres en una
  afirmación con sus citas pertinentes para conservar todas las entradas
  dentro de 30 afirmaciones por parte y 50 fuentes por afirmación; el esquema
  local de validación y las guardas comparten esos límites. La representación
  enviada a Gemini puede simplificar cardinalidades para compatibilidad,
  conservándolas en las instrucciones y en la validación local.

## Fuente de verdad

La fuente implementada es `agents/chat_metric_catalog.py`, contrastada con
`agents/gatekeeper.py` y `agents/calc_engine.py`. No usa RAG, Supabase ni LLM.

## Verificación offline del Paso 4

`tests/fixtures/chat_offline_cases.json` distingue explicación conceptual de
fórmula y ejecución prohibida, además de concepto del motor y finanzas fuera
del motor. El evaluador comprueba el tipo y estado, ausencia de evidencia de
negocio en conceptos, rechazo de cálculos y cobertura de preguntas permitidas.
La calidad de las paráfrasis se deja a revisión semántica independiente; las
dos variantes simuladas aceptadas no constituyen prueba de un proveedor real.
Una muestra Gemini anterior registró un fallo de generación al negar un
cálculo; otra posterior de cuatro partes cubrió 3/3 respondibles sin fallos
de código. El conjunto real completo posterior cubrió 19/22 respondibles y
registró cuatro juicios semánticos adversos; uno detectó que una respuesta de
dos métricas omitió el estado `warning` requerido. Falta corregir las salidas
y revisar independientemente la versión final. Véase
`docs/chatbot_step4_eval.md` y `INC-20260930-013`.

Al 4-oct-2026, la guía de redacción del catálogo extenso pide distribuir los
conceptos entre afirmaciones y citar en cada una solo los campos que expresa.
Esto responde al borrador real previo que excedió el máximo de `source_ids`
por afirmación. La guía de resultados pide mencionar el estado de alerta
emitido por S3 sin inferir causas. Los controles del catálogo siguen
distinguiendo una explicación conceptual válida de un cálculo ejecutado. Dos
paráfrasis simuladas del conjunto vigente cubrieron 22/22 respondibles con
cero fallos mecánicos, pero no hubo nueva prueba Gemini: la mejora real sigue
sin medir y el Paso 4 permanece abierto.

La revisión del 6-oct-2026 confirmó que `catalog` y la segunda parte de
`two_named_results` forman parte de los fallos históricos de los siete casos
dirigidos: el primero quedó en respaldo por un borrador inválido y el segundo
omitió comunicar `warning` según el juez externo. No se reconstruyen los
borradores rechazados desde los diagnósticos. La corrida dirigida con Gemini
actual no empezó por falta de clave en el entorno; las simulaciones nuevas
siguen sin sustituir el juicio semántico independiente. El contrato del
catálogo y la prohibición absoluta de cálculo permanecen vigentes.

La medición real posterior del 6-oct-2026 sí ejecutó los siete casos dirigidos.
`catalog` volvió a caer en respaldo; esta vez el diagnóstico fue
`draft:schema:parts.0.claims:too_long`. El esquema compacto no enviaba el
máximo de 30 afirmaciones exigido internamente. Se corrigió el contrato y
la guía de agrupación de nombres, conservando las 35 entradas del catálogo
y todos los límites. `INC-20261006-018` está mitigada; falta comprobarlo con
Gemini real. La muestra completa dirigida cubrió 3/7 respondibles y tuvo
cuatro juicios adversos en 12 partes, todas revisadas por otro modelo. No se
declara cerrado el Paso 4.

La repetición posterior `034018_b82f6219` fue rechazada con HTTP 400 en los
siete intentos antes de redactar, incluido `catalog`. No demuestra cobertura
del catálogo ni calidad de su redacción. `INC-20261006-019` simplifica el
esquema enviado a Gemini, manteniendo los límites y la agrupación locales.
El siguiente diagnóstico real es de un solo caso para comprobar la solicitud;
el catálogo y la muestra completa dirigida siguen pendientes.

El diagnóstico posterior `035637_2cbbbb76` validó un resultado S3, con
1/1 cobertura y cero fallos; no consultó el catálogo. Por ello sigue pendiente
medir la agrupación y cobertura de las 35 entradas con Gemini. El juez de
ese diagnóstico recibió HTTP 503 y no emitió veredicto semántico; el segundo
intento con `gemini-3.8-flash` también devolvió 503. Ambos quedan conservados
en `035637_2cbbbb76_semantic_attempts`, sin llamadas nuevas. La revisión humana
del resultado S3 sigue pendiente y no demuestra cobertura del catálogo.

La muestra posterior `044143_2dc8c5f1` sí validó `catalog` en dos llamadas:
35 nombres citados en nueve afirmaciones, máximo 20 fuentes por afirmación,
dentro de los límites 30/50 y sin error de esquema. `INC-20261006-018` queda
resuelta para contrato y agrupación del catálogo; su revisión independiente
continúa pendiente. La muestra global cubrió 7/7 respondibles, con un fallo
de reproducción de instrucciones en `report` (021), ajeno al catálogo. No se
declara validación semántica ni cierre del Paso 4; el paquete manual conserva
las fuentes del catálogo sin registrar juicios humanos.

Seguimiento del 7-oct-2026: `report` pasó por separado en `231840_af09f570`,
con 17/17 controles y un juicio independiente favorable; 021 resuelta para
ese defecto. No revisa el catálogo ni transfiere juicios a la muestra previa.
Su validación semántica completa sigue en el conjunto final preparado: cuatro
tandas de siete casos, con `catalog` en la tercera y presupuesto explícito.
Paso 4 permanece abierto; no cambió el catálogo ni sus límites.

Evidencia posterior de la tanda 3 `full_batch3_000945_07759275`: el catálogo
comunica las 35 entradas en once afirmaciones, máximo cinco fuentes por
afirmación, dentro de los límites 30/50. Flash independiente aprobó sus
cuatro criterios; hash/digest ligados al informe exacto comprobados,
originales intactos. 018 continúa resuelta y este catálogo tiene revisión
favorable; no se trasladan esos juicios al informe dirigido anterior.
La tanda falló en una consulta de resultado con fecha, ajena al catálogo.
013/016 abiertas; guía de cifras/fechas mitigada con pruebas locales, efecto
real pendiente. No cambia catálogo ni límites; Paso 4 no cerrado.

Evidencia de la candidata actual, 8-oct-2026: `full_batch3_232441_8d0d024f`
comunica las 35/35 entradas en ocho afirmaciones, máximo 28 fuentes por
afirmación, dentro de límites locales 30/50. Flash independiente aprobó los
cuatro criterios; hash/digest corresponden al informe exacto, originales
intactos. 018 permanece resuelta; no se trasladan juicios a informes históricos.
Toda la tanda actual pasó: cobertura 6/6, 145/145 controles y 10/10 juicios
favorables; fecha explícita también aprobada. Acumulado actual 24/36 partes,
14/22 respondibles, 365/365 controles. Sigue tanda 4, máximo 14 gen/tres juez;
plan correcto sin clave/API. Solo documentación, sin cambiar catálogo, límites
o código ni repetir suite; última general 224 aprobadas, una omitida y 114
subpruebas. 013/016 abiertas, `codex/chatbot-q4`, HEAD `7c2d307`, sin commit.
Paso 4 abierto hasta completar el conjunto; consolidación posterior sin llamadas nuevas.

Consolidado completo posterior, 8-oct-2026: tanda 4
`full_batch4_235606_4090759b` falló en informe mixto y negativa aritmética,
ajenos al catálogo. Total 35/36 juicios favorables, 21/22 respondibles,
544/547 controles, 54 gen/diez juez históricos; sin pendientes/errores y cero
API nuevas al consolidar. El catálogo aprobado de tanda 3 conserva su juicio
y 018 permanece resuelta, sin cambiar catálogo o límites. Sigue `-DiagnosticoTanda4`,
con traza sintética de esos dos casos, máximo cuatro gen/un juez; la traza
no es revisión independiente. Focalizadas 75/47 subpruebas, general 230
aprobadas, una omitida y 119 subpruebas en 54.15 s. 013/016 abiertas,
`codex/chatbot-q4`, HEAD `7c2d307`, sin commit; Paso 4 no cerrado.

Seguimiento global, 9-oct-2026: `batch4_diagnostic_133615_e9264e7f` aprobó
los dos casos ajenos al catálogo: 45/45 controles, cobertura 2/2, 3/3 juicios
independientes favorables, cuatro gen/un juez, cero fallos/pendientes/errores.
SHA/tres digests, fixture, fuentes, traza y resúmenes comprobados sin API.
Rechazo previo no reproducido, causa exacta sin demostrar. El consolidado
fallido conserva 35/36 favorables, 21/22 cobertura y 544/547 controles;
diagnóstico no sustituye partes ni transfiere juicios. Sigue repetir solo
tanda 4, máximo 14 gen/tres juez, plan correcto sin clave/API; si pasa,
consolidar offline con tandas 1/2/3 aprobadas. Catálogo y límites sin cambios,
018 resuelta. Solo documentación, suite no repetida; última general 230
aprobadas, una omitida/119 subpruebas. 013/016 abiertas, `codex/chatbot-q4`,
HEAD `7c2d307`, sin commit; Paso 4 no cerrado.

Seguimiento global, 9-oct-2026: nueva tanda 4
`full_batch4_20261009_135244_2f9d9c1e`, ajena al catálogo, aprobó
8/8 cobertura, 183/183 controles y 12/12 juicios independientes favorables;
14 generaciones/tres juez. Consolidado de las tandas actuales 1/2/3/4:
28/28 casos, 36/36 partes, 22/22 cobertura, 548/548 controles y 36/36
juicios independientes favorables, código 0 y cero nuevas API. Catálogo de
la tanda 3 y sus límites no cambiaron; 018 permanece resuelta. Históricos
fallidos conservados. 013/016 resueltas para el conjunto offline; 21
incidencias, 20 resueltas, una pendiente externa, cero abiertas. Solo
informes/documentación, suite no repetida; última general 230 aprobadas,
una omitida/119 subpruebas. `codex/chatbot-q4`, HEAD `7c2d307`, sin commit;
Paso 4 validado offline, Paso 5 posterior.

### Seguimiento de consistencia autorizado — 9-oct-2026

Conjunto offline aceptado: cobertura 22/22, 548/548 controles y 36/36 juicios
favorables. Seguimiento adicional pendiente: tres ejecuciones nuevas de los
dos casos afectados, con `-DiagnosticoTanda4`, traza y configuración idéntica.
Máximo 4 gen/1 juez por ejecución, 12 gen/3 juez (15 API) en total, sin
reintentos. Exigir 2/2 cobertura, 3/3 juicios favorables y cero fallos/errores/
pendientes en cada ejecución. Detener la serie ante un fallo y analizar traza;
conservar todos los intentos. Tres éxitos no demostrarían la causa histórica.
Plan `docs/evaluations/chatbot_step4_consistency_plan_20261009.json`, con SHA de código/fixture/helper.
Plan/sintaxis comprobados sin clave ni API. Solo documentación, sin repetir
suite; última general 230 aprobadas, una omitida/119 subpruebas. 013/016
resueltas para el conjunto original; seguimiento adicional pendiente antes
de Paso 5. `codex/chatbot-q4`, HEAD `7c2d307`, sin commit.
