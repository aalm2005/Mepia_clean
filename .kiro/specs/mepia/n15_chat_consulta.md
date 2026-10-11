# N15 — Chat de consulta fundamentada

**Capa:** Aplicación | **Anterior:** S3/N14 | **Siguiente:** interfaz Chat IA
**Archivos relacionados:** `_glossary.md`, `db_schema.md`,
`n15_chat_consulta_tools.md`, `n15_chat_consulta_catalogo.md`,
`agents/chat_grounding.py`,
`agents/chat_tools.py`,
`agents/chat_conversation.py`, `agents/chat_response.py`,
`agents/chat_provider_gemini.py`, `agents/chat_provider_openai.py`,
`tests/chat_offline_eval.py`, `tests/fixtures/chat_offline_cases.json`

## Input / Output

- Input futuro: `business_id`, pregunta y fecha opcional.
- Fase 1: `ChatGroundingPacket` con S3, N14 enlazado, referencias y faltantes.
- Fase 2: `ChatToolResult` para resultados, catálogo o glosario, con cálculo
  deshabilitado de forma explícita.
- Fase 3: `ChatAnswer` con partes independientes (`kind`, `status`, `message`,
  `data`, `evidence`, `missing_data`, `claims`, `generation_status`,
  `generation_issues`, `generation_diagnostics`) y `calculation_allowed=false`.
- `message` puede contener redacción libre de la IA; `claims` conserva las
  afirmaciones verificadas y sus referencias. Los textos fijos son respaldo.
- `generation_diagnostics` conserva solo códigos seguros de etapa y causa
  cuando falla la generación o revisión; nunca copia texto rechazado ni claves.
- Ningún contrato contiene instrucciones ni campos arbitrarios de JSONB.

## User Stories

- Como dueño, quiero preguntar por mis resultados sin cifras inventadas.
- Como sistema, quiero separar evidencia, consulta y generación de lenguaje.
- Como auditor, quiero rastrear cada respuesta hasta `audit_results`.
- Como negocio, quiero impedir que se mezclen datos entre negocios o ejecuciones.
- Como sistema, quiero explicar solo conceptos de las métricas del motor y nunca
  calcular por cuenta del chatbot.

## Acceptance Criteria

- WHEN se construye el paquete THEN toda consulta SQL filtra por `business_id`.
- WHEN no hay fecha THEN se elige la S3 utilizable más reciente.
- WHEN se recupera N14 THEN coincide en negocio, fecha y `source_s3_result_id`.
- WHEN falta una fuente o su estructura es inválida THEN se declara en
  `missing_data`; nunca se rellena ni se hace fallback.
- WHEN se exponen S3/N14 THEN se aplican sus allowlists y se adjunta evidencia.
- WHEN una herramienta consulta métricas o reporte THEN exige evidencia del
  mismo linaje y fecha antes de exponer contenido.
- WHEN un selector es desconocido THEN retorna `not_found` o `invalid_request`,
  sin coincidencia aproximada.
- WHEN se consulta el glosario THEN usa definiciones curadas y no las presenta
  como evidencia de un negocio.
- WHEN se solicita cualquier cálculo, recálculo, agregación, proyección o
  simulación THEN retorna `not_allowed` sin producir valores.
- WHEN el motor no emitió el resultado THEN se declara ausente y no se deriva de
  otras cifras.
- WHEN la pregunta tiene varias partes THEN se evalúa cada una y la negativa de
  cálculo no impide responder las partes permitidas.
- WHEN el proveedor redacta THEN puede explicar, resumir y parafrasear en sus
  propias palabras, con fuentes por afirmación y sin alterar hechos ni estados.
- WHEN la redacción contiene cantidades THEN usa marcadores vinculados al
  literal de un campo de la fuente; se rechazan cantidades libres, marcadores
  inventados, unidades incompatibles y comparaciones numéricas no emitidas.
- WHEN una afirmación no tiene fuentes de su propia parte o la revisión separada
  no confirma respaldo, dominio y política THEN esa parte conserva el respaldo
  determinista; las demás partes válidas pueden publicar su redacción libre.
- WHEN la revisión es parcial, repetida, malformada o de otro borrador THEN no
  se publica el texto. El digest vincula el juicio al texto y fuentes exactos.
- WHEN el `business_id` solicitado no coincide con el paquete THEN el nodo
  rechaza la consulta antes de llamar al proveedor.
- WHEN se evalúa offline THEN se registran clasificación, estado, cobertura,
  cifras, unidades, negocio, fecha, linaje, faltantes y rechazos por caso y
  por parte con denominadores explícitos.
- WHEN una parte sí puede responderse THEN un mensaje de respaldo sin
  redacción validada no cuenta como cobertura.
- WHEN se juzga el sentido de una afirmación THEN el juicio independiente se
  vincula al texto y fuentes exactos; `not_reviewed` no significa aprobación.
- WHEN una corrida real termina una parte en respaldo THEN el evaluador cuenta
  un fallo de generación, incluso si la negativa resultante es segura.
- WHEN se solicita redactar una parte `not_allowed` THEN el adaptador pide
  parafrasear `/status/explanation` sin copiar cifras ni marcadores numéricos
  de la pregunta; las guardas siguen rechazando afirmaciones sin fuente.
- WHEN el adaptador redacta THEN da instrucciones específicas según el tipo y
  estado de cada parte, exige unidad junto a valores de S3 y permite distintas
  paráfrasis sustentadas.
- WHEN falla borrador o revisión THEN el informe registra códigos seguros para
  proveedor, esquema, IDs o decisión adversa, sin guardar excepciones crudas,
  respuestas HTTP, texto rechazado ni credenciales.
- WHEN se valida una respuesta del proveedor THEN aplica los mismos
  límites de las guardas: una a 30 afirmaciones por parte y una a 50 fuentes
  por afirmación; el catálogo extenso agrupa nombres sin omitir entradas.
- WHEN el adaptador Gemini simplifica cardinalidades del esquema enviado
  THEN mantiene los límites en las instrucciones y en la validación local;
  un error HTTP 400 conserva solo diagnósticos fijos sanitizados, sin reintentos.

## Fases

1. ✅ Grounding S3/N14 y linaje exacto; validado en `MEPIA - PRUEBAS`.
2. ✅ Herramientas deterministas, catálogo completo del motor y prohibición
   absoluta de cálculo.
3. ✅ Nodo local con clasificación, redacción libre y revisión inyectables,
   partes estructuradas, guardas de no cálculo y salida fundamentada. La
   restricción anterior a mensajes fijos se corrigió en `INC-20260927-009`.
4. ⚠️ Arnés y conjunto offline reproducible implementados: el conjunto
   vigente tiene 28 casos, 36 partes, 22/22 partes respondibles con redacción
   validada y 0 fallos mecánicos en la corrida simulada. El control de solo
   respaldo falla 22/22
   partes respondibles. Gemini real se probó con una muestra de dos casos:
   1/1 parte respondible cubierta, 1/2 redacciones validadas y 2/2 juicios
   independientes pendientes. El respaldo en la negativa de cálculo cuenta
   como fallo (`INC-20260930-013`). La repetición con instrucción más precisa
   tuvo 2 fallos en 4 llamadas; Flash tuvo 3 fallos en 3 llamadas. Tras
   añadir diagnóstico seguro y reglas por tipo, Flash-Lite pasó una muestra
   de 4 partes con 8 llamadas y 3/3 respondibles cubiertas. Los juicios
   semánticos independientes siguen pendientes. Una selección posterior de
   cinco casos nuevos hizo 10 llamadas, cubrió 6/6 partes respondibles y validó
   8/8 generaciones con cero fallos mecánicos. Después se ejecutaron los 23
   casos restantes: el conjunto real completo cubrió 19/22 respondibles en
   53 llamadas y registró 10 fallos mecánicos confirmados. El juez separado
   emitió 32 juicios favorables y 4 adversos; 13/36 provinieron del mismo
   modelo generador y son provisionales (`INC-20260930-016`). Paso 4 no aprobado.
5. Pendiente: endpoint autenticado y autorizado por negocio, historial
   controlado e interfaz Chat IA.

## Discrepancias conocidas

- No hay autenticación FastAPI; no se expone endpoint de chat.
- `MemoryService.get_context()` no aporta IDs de fuente y no se usa en N15.
- Las migraciones `008` y `009` aún no se despliegan en producción.

## Edge Cases

- Negocio o fecha sin S3: paquete vacío; N14 no se recupera por separado.
- Varias ejecuciones: se usa la S3 más reciente y solo su N14 exacto.
- Linaje ausente, inválido o conflictivo: el contenido no verificable se rechaza.
- JSONB malformado o sin campos permitidos: fuente marcada como faltante.
- Evidencia de otra fecha o raíz: la herramienta no expone datos.
- Concepto financiero ajeno a las métricas del motor: fuera de alcance.
- Fórmula: se puede explicar conceptualmente, pero nunca ejecutar.
- Texto recuperado y pregunta: datos no confiables como instrucciones. La
  clasificación solo recibe fragmento y selectores. La redacción recibe hechos
  permitidos de las herramientas y la revisión comprueba únicamente fuentes
  citadas, separadas de la política fija.

## Integración de redacción

`ChatResponseWriter.compose()` produce `ChatModelDraft`; cada parte contiene
afirmaciones de texto libre y `source_ids`. Las cantidades usan `{{slot_id}}`
de los hechos citados. El código sustituye ese marcador por el literal original,
sin calcular ni redondear. `ChatResponseVerifier.verify()` devuelve un juicio
por afirmación: respaldo, dominio, cálculo realizado y respeto de la política.
La revisión es una llamada separada; no utiliza aritmética para decidir.

`ChatJsonCompletionAdapter` acepta una función de API/SDK suministrada por el
consumidor y separa política, datos JSON y esquema de salida. Puede usarse un
proveedor para redactar y otro para revisar. Hay una composición y una revisión
por pregunta, sin reintentos ocultos; la clasificación es opcional.

El nodo no crea clientes ni lee claves y no cambia proveedores del motor. En
local se prueban estas llamadas con simulaciones. La interpretación semántica
del verificador puede fallar y debe medirse en el Paso 4: los controles
deterministas no se presentan como prueba universal de comprensión del lenguaje.

## Evaluación offline del Paso 4

El arnés `tests/chat_offline_eval.py` construye paquetes desde filas sintéticas
S3/N14 del fixture mediante `ChatGroundingService`. Los resultados esperados
viven en `tests/fixtures/chat_offline_cases.json`; las pruebas del arnés en
`tests/test_chat_offline_eval.py`. Se generan informes Markdown y JSON por
caso y por parte. Los controles de código se reportan separados del juicio
semántico externo, que verifica respaldo, cobertura de la pregunta, alcance y
ausencia de cálculo mediante un digest de texto y fuentes. El procedimiento y
criterios se describen en `docs/chatbot_step4_eval.md`.

La corrida simulada local demuestra el funcionamiento del arnés, no la calidad
de una IA real. El CLI usa Gemini por defecto para el modo real, con la API
compatible con OpenAI, esquemas estructurados y límite de llamadas. OpenAI
Responses sigue seleccionable. La clave solo se proporciona en el entorno;
el nivel gratuito recibe únicamente estos datos sintéticos. Una muestra anterior
real hizo 3 llamadas para 2 casos: hubo cobertura 1/1, pero una negativa de
cálculo del modelo cayó en respaldo por un marcador sin fuente. El informe
registra el fallo y quedan 2 juicios semánticos independientes pendientes.
El adaptador recibió una instrucción específica para negar cálculos sin cifras
ni marcadores, y una prueba local aceptó dos redacciones válidas distintas.
En muestras reales posteriores, Flash-Lite registró 2 fallos en 4 llamadas
y Flash 3 fallos en 3 llamadas. Los informes conservan esos resultados; el
modelo predeterminado sigue siendo Flash-Lite y `INC-20260930-013` permanece
abierta. La continuación agregó códigos seguros de diagnóstico y reglas
breves por parte; una muestra Flash-Lite de cuatro casos registró 0 fallos de
código y 3/3 partes respondibles cubiertas. El conjunto se amplió después a
28 casos y 36 partes, con 22/22 respondibles cubiertas en simulación y 0/22
en el control de solo respaldo. `--real-case-ids` permite repetir una selección
dirigida, máximo ocho casos con presupuesto de dos llamadas por caso. Una
muestra de cinco casos nuevos registró 10 llamadas, 6/6 respondibles cubiertas,
8/8 generaciones validadas y cero fallos mecánicos. Las tres tandas posteriores
completaron los otros 23 casos con 43 llamadas. En los 28 casos reales se
cubrieron 19/22 partes respondibles y hubo 10 fallos mecánicos confirmados;
el falso positivo del rechazo previo de negocio se corrigió en el arnés
(`INC-20260930-015`). Un juez de otro modelo revisó 23 partes; 13 partes solo
tienen juicio provisional del modelo generador. Cuatro juicios fueron adversos.
Los informes y digests están en `docs/evaluations/`; el procedimiento y sus
límites están en `docs/chatbot_step4_eval.md`.
Paso 5 sigue separado y sin endpoint público.

Continuación del 4-oct-2026: `ChatJsonCompletionAdapter` guía la redacción de
informes hacia el contenido concreto del resumen N14 citado, reparte las citas
del catálogo extenso por afirmación y solicita mencionar estados de alerta
emitidos por S3 sin inferir sus causas. La revisión distingue una negativa a
calcular de un cálculo ejecutado, y una delimitación correcta de un concepto
fuera del motor de una explicación financiera no autorizada. Estas precisiones
no alteran la libertad de paráfrasis, las citas exigidas ni la prohibición
absoluta de calcular, recalcular, sumar, promediar, agregar, derivar
comparaciones numéricas, proyectar o simular.

Dos corridas simuladas actuales del mismo fixture (28 casos, 36 partes)
cubrieron 22/22 partes respondibles y tuvieron cero fallos mecánicos, con
36/36 juicios semánticos pendientes cada una. El control de solo respaldo
cubrió 0/22 y registró 22 fallos esperados. No hubo nuevas llamadas Gemini
porque la clave no estaba en el entorno; los 19/22 respondibles de la corrida
real anterior siguen siendo el último resultado medido con IA real. Pruebas
actuales: 57 focalizadas y 18 subpruebas; suite general 209 aprobadas, una
integración opt-in omitida y 90 subpruebas. Paso 4 sigue abierto por
`INC-20260930-013` y `INC-20260930-016`; Paso 5 sigue posterior.

Verificación del 6-oct-2026: los siete casos dirigidos tienen 12 partes y
siete respondibles. Los informes Gemini históricos cubrieron 4/7, con diez
fallos mecánicos y cuatro juicios semánticos adversos. El intento actual
mediante `--real-case-ids` y un límite de 14 llamadas se detuvo antes de
generar por ausencia de clave en el entorno; un presupuesto de cuatro
llamadas del juez quedó sin usar. Las dos simulaciones nuevas del conjunto
completo cubrieron 22/22 respondibles, con cero fallos mecánicos y 36 juicios
independientes pendientes cada una; el control negativo cubrió 0/22 y falló
22 veces como se esperaba. La evidencia por caso y parte está en
`docs/evaluations/chatbot_step4_20261006_directed_status.{json,md}` y en
los pares de informes actuales. Una prueba nueva comprueba que la selección
real de siete casos se detiene antes de evaluar si no hay clave. Las pruebas
focalizadas aprobaron 69 y 24 subpruebas; la suite general 210, con una
integración opt-in omitida y 90 subpruebas. No cambió el comportamiento
observable de N15. La calidad Gemini
posterior al ajuste del 4-oct sigue sin medirse; Paso 4 abierto.

Medición real posterior del 6-oct-2026: la clave temporal permitió siete
casos y 12 partes, con 13 llamadas, cobertura 3/7, 6/12 generaciones validadas
y diez fallos mecánicos. El juez Flash revisó 12/12 partes con otro modelo en
cuatro llamadas sin errores; ocho favorables y cuatro adversas. El N14 de
`mixed` entregó contenido, pero cuatro partes respondibles quedaron en
respaldo. La corrida no demuestra una mejora global; la última evaluación
completa de 28 casos sigue siendo histórica. Se corrigió después la omisión
de límites del esquema compacto (`INC-20261006-018`): no se aumentaron los
máximos ni se truncaron las respuestas inválidas. La versión corregida aún
requiere nueva medición real. Paso 4 abierto; Paso 5 posterior.

Repetición real posterior `034018_b82f6219`: siete intentos de generación
con HTTP 400, cobertura 0/7, 0/12 generaciones validadas y 19 fallos
mecánicos. El juez hizo cuatro intentos, tres HTTP 503; solo 3/12 partes
revisadas con otro modelo, una favorable, dos adversas y nueve pendientes,
con una contradicción señalada. `INC-20261006-019` mitiga la representación
enviada a Gemini, sin alterar validadores locales. Las pruebas posteriores
aprobaron 74 focalizadas y 33 subpruebas; el siguiente trabajo es comprobar
un caso con máximo dos llamadas de generación y una del juez, antes de
repetir la muestra dirigida. No es un cierre del Paso 4 ni un avance al Paso 5.

Diagnóstico real posterior `035637_2cbbbb76`: el caso `result` obtuvo
redacción validada en dos llamadas, 1/1 cobertura y 19/19 controles sin
fallos. No hubo HTTP 400, pero el juez Flash devolvió HTTP 503: cero juicios
y una parte pendiente. Una llamada posterior de `gemini-3.8-flash` al mismo
informe también devolvió HTTP 503, sin regeneración ni juicio. El reporte Markdown muestra los
errores HTTP del juez; seis pruebas del juez aprobadas en 2.21 s, sin red.
Sigue pendiente repetir los siete casos y el conjunto completo con revisión
independiente; la comprobación de un caso no cierra el Paso 4.

El consolidado `035637_2cbbbb76_semantic_attempts` conserva los dos intentos
del diagnóstico, sus dos errores 503 y una parte pendiente; se creó sin red.
La alternativa humana requiere cuatro decisiones explícitas (respaldo,
pregunta atendida, alcance y no cálculo). El usuario emitió después una
evaluación parcial: tres criterios favorables y alcance pendiente por no
entender `estado ok`. Se conserva ligada al hash y digest en
`035637_2cbbbb76_human_partial_20261007_043124`, fuera de juicios completos;
la duda no equivale a un Sí ni a un No. `INC-20261006-020` corrige el resumen para
separar `human:<identidad>` de `independent-model:<modelo>`; una etiqueta
desconocida queda pendiente y el mismo modelo es provisional. Toda revisión
se liga al hash del informe y al digest de la parte. El cierre conserva los
controles mecánicos y exige cobertura completa y las 36 partes favorables
revisadas por una persona o un modelo distinto. No cambian generación ni motor.

Ajuste posterior por la observación humana de claridad: la guía de redacción
pide métrica, valor y unidad directamente y omitir el código `ok` si una
consulta de valor no pide el estado. La regla de comunicar alertas sigue
obligatoria; estados estructurados, evidencia, guardas y motor se conservan.
No hay frase fija de aceptación ni medición real de este ajuste todavía.
El archivo temporal prepara los siete casos con `-SinJuez`: máximo 14 llamadas
de generación, cero del juez automático y sin reintentos, debido a los dos
errores 503 del diagnóstico. Las respuestas nuevas quedan pendientes de
revisión independiente, ligada a sus propios hashes y digests; ninguna
evaluación parcial anterior se traslada. Paso 4 permanece abierto.

La nueva corrida dirigida `044143_2dc8c5f1` hizo 14 llamadas, cubrió 7/7
respondibles y validó internamente 12/12 partes, con 162/163 controles y cero
llamadas del juez; las doce revisiones independientes siguen pendientes. El
catálogo citó 35 nombres en nueve afirmaciones y máximo 20 fuentes, sin fallo
de esquema ni HTTP 400. El ticket promedio omitió `ok` y caja conservó `warning`.
018/019 se resuelven para contrato y aceptación de estas solicitudes.

El único fallo fue reproducción de una instrucción recuperada en `report`,
incluida la cifra `999 MXN`, como descripción del texto contaminado. Se abre
`INC-20261006-021`: se excluye citar o describir instrucciones dirigidas al
asistente para cambiar reglas, calcular o fijar respuestas, aunque estén
literalmente en una fuente. El verificador debe rechazar por política y el juez
externo por alcance. Las acciones operativas legítimas N14 siguen permitidas;
no se borra texto después de validar ni cambia el control de evaluación.
La mitigación está probada localmente (76 focalizadas/35 subpruebas; general
217 aprobadas, una integración omitida y 101 subpruebas), sin prueba real del
prompt nuevo todavía. Sigue diagnóstico solo de `report`, máximo dos llamadas
de generación y cero del juez, y revisión independiente completa posterior.
El paquete manual de doce partes omite verificación interna y no contiene
valoraciones; preserva hash y digests del informe. Paso 4 no cerrado.

Seguimiento del juez del 7-oct-2026: `135713_f778deae` intentó una llamada Flash
sobre el diagnóstico guardado, otro HTTP 503, cero juicios, una pendiente y
cero nuevas generaciones. El nuevo consolidado conserva tres intentos de esa
misma parte, sin red ni reescribir originales. La causa concreta no se conoce.
El juez registra ahora solo un estado permitido del proveedor, presencia de
mensaje y pistas con códigos fijos, sin texto libre ni secretos; consola y
Markdown presentan esas pistas sin tratarlas como causa confirmada. No cambia
el esquema de juicio, presupuesto ni reintentos. Focalizadas: 64 aprobadas
y 32 subpruebas en 9.05 s, con proveedor simulado. Falta medir estos nuevos
campos con Gemini real. `INC-20260930-016` abierta; doce juicios de la muestra
dirigida pendientes. El diagnóstico de `report` por 021 sigue pendiente y
el Paso 4 no está cerrado.

La suite general posterior al diagnóstico seguro obtuvo 219 aprobadas, una
integración opt-in omitida y 104 subpruebas en 64.00 s. Esta comprobación local
no confirma una causa del HTTP 503 ni sustituye la revisión independiente.

Cuarto intento `141127_89067edf`: una llamada Flash, HTTP 503, cero juicios,
una pendiente y sin nuevas generaciones MEPIA. Las pistas vacías no confirman
ausencia de texto; el detector solo contemplaba un objeto JSON. Ahora contempla
listas, texto y respuesta ya recibida, guardando solo formato y códigos fijos.
Se prepara comparación de una consulta mínima y un juicio original, por el
mismo modelo/cliente/endpoint, máximo dos llamadas API sin reintentos. El
control no aporta juicio ni cobertura; sus llamadas y resultado se conservan
incluso al combinar intentos. Requiere una parte real y un modelo distinto.
Focalizadas: 66 aprobadas y 38 subpruebas en 7.31 s; sintaxis y rechazo de modos
incompatibles antes de clave correctos. Comparación real pendiente; cuatro 503
conservados sin red, origen intacto. `INC-20260930-016` abierta, Paso 4 no cerrado.

Suite general posterior: 221 aprobadas, una integración opt-in omitida y 110
subpruebas en 55.42 s. Validación local del comparador, sin comparación real ni
causa del 503 confirmada.

Comparación real `225324_b40a84a9`: dos API, control mínimo con respuesta y
juicio Flash independiente 1/1 favorable, cuatro criterios verdaderos, cero
pendientes y cero fallos semánticos/mecánicos. Hash/digest ligados al original
Flash-Lite de ticket promedio; no se regeneró MEPIA. Consolidado nuevo sin red
conserva cuatro 503 previos y el quinto intento favorable, cinco llamadas del
juez y seis API históricas. Código 1 por cierre global de 36 partes pendiente.
La causa de los 503 permanece desconocida; no se prueba estabilidad futura.
No se trasladan juicios a las doce partes dirigidas ni se transforma la revisión
humana parcial en completa. Sigue `report` por 021, máximo dos generaciones
y un juicio, después conjunto completo y revisión independiente. 016 abierta,
Paso 4 no cerrado. Sin cambio de código ni nuevas pruebas; última suite general
221 aprobadas, una integración opt-in omitida y 110 subpruebas en 55.42 s.

Diagnóstico `report` posterior `231840_af09f570`: dos generaciones y un juicio,
cobertura 1/1, 17/17 controles y 1/1 revisión independiente favorable, cero
fallos/pendientes. Comunica el resumen estable sin reproducir instrucciones;
hash/digest exactos comprobados, Flash juez distinto de Flash-Lite generador.
021 resuelta para el defecto observado, 013/016 abiertas para el conjunto final.
No se sustituyen ni trasladan los doce juicios del informe dirigido anterior.

Se prepara conjunto completo en cuatro tandas disjuntas de siete casos:
7/7/10/12 partes, 7/1/6/8 respondibles, total 28/36/22. `-TandaCompleta 1..4`
con máximo 14 generaciones por tanda y juez 2/2/3/3, cuatro partes máximas
sin dividir preguntas ni reintentar. `-MostrarPlan` valida sin clave/red.
Sintaxis, cuatro planes y rechazo de modos incompatibles antes de clave
correctos; no cambia N15, evaluador, juez, fixture ni criterios. Última suite
Python 221 aprobadas, una omitida y 110 subpruebas, sin repetir por archivo
PowerShell. En esa preparación aún no se había ejecutado la primera tanda;
la corrida posterior se registra a continuación.

Primera tanda actual `full_batch1_235430_46e3ac22`, 7-oct-2026: 14 generaciones
Flash-Lite, dos llamadas del juez Flash independiente, cobertura 7/7,
118/118 controles, 7/7 juicios favorables y cero fallos, errores, pendientes
o contradicciones. Los cuatro criterios son verdaderos en cada juicio;
hash del informe y siete digests comprobados, resumen recalculado sin red,
originales intactos. Código de revisión 1 por requerir 36 partes para cierre.
Avance 7/28 casos, 7/36 partes y 7/22 respondibles, sin trasladar juicios de
otros informes. Restan 21 casos/29 partes/15 respondibles. Sigue tanda 2,
máximo 14 generaciones y dos llamadas de juez, sin reintentos; plan validado
sin clave ni API. 013/016 abiertas, 021 resuelta para el defecto observado.
Solo documentación, sin repetir suite ni cambiar comportamiento, fixture o
criterios; `codex/chatbot-q4`, HEAD `7c2d307`, sin commit. Paso 4 no cerrado.

Segunda tanda actual `full_batch2_000414_ea2379a8`, 7-oct-2026: 12 generaciones
Flash-Lite y dos llamadas del juez Flash independiente, cobertura 1/1,
102/102 controles, 7/7 partes favorables y cero fallos, errores, pendientes
o contradicciones. Los seis casos no respondibles indican ausencia o rechazo;
el negocio incorrecto se rechaza sin generación. Hash y siete digests
comprobados, resúmenes de ambas tandas y acumulado recalculados en memoria
sin red; originales intactos. Código de revisión 1 por cierre global incompleto.
Acumulado 14/28 casos, 14/36 partes, 8/22 respondibles, 220/220 controles,
26 generaciones y cuatro llamadas del juez. Restan 14 casos/22 partes/14
respondibles. Sigue tanda 3, diez partes/seis respondibles, máximo 14
generaciones y tres llamadas del juez; plan validado sin clave ni API.
013/016 abiertas, 021 permanece resuelta. Solo documentación, sin repetir
suite ni cambiar comportamiento, fixture o criterios; `codex/chatbot-q4`,
HEAD `7c2d307`, sin commit. Paso 4 no cerrado; Paso 5 posterior.

Tercera tanda `full_batch3_000945_07759275`, 7-oct-2026: 13 generaciones,
tres llamadas del juez, cobertura 5/6, 139/141 controles y 9/10 juicios
independientes favorables. `explicit_date_result` falló cobertura y generación
por `unbound_quantity`, con respaldo sin el valor consultado; juez adverso
correcto, sin errores ni pendientes. No se conserva el borrador; no se sabe
qué cifra provocó el rechazo. Hash y diez digests comprobados, originales intactos.

La guía ahora distingue cifras de la pregunta de fuentes con marcadores:
responde con valor/unidad emitidos y permite omitir la fecha del texto,
conservándola en los metadatos. No se permite una cifra sin slot ni se
cambia recuperación, guardas, fixture o juez. Focalizadas 67 aprobadas y
42 subpruebas; general 222 aprobadas, una integración opt-in omitida y
114 subpruebas, 62.31 s. Efecto con Gemini real pendiente; sigue diagnóstico
exclusivo de fecha, máximo dos generaciones y un juicio, sin reintentos.
Acumulado anterior a mitigación: 21/28 casos, 24/36 partes revisadas,
23 favorables/una adversa, 13/14 respondibles observadas de 22 totales,
359/361 controles. 013/016 abiertas, 018 resuelta; no se cierra Paso 4 ni
se valida la versión nueva con informes anteriores. `codex/chatbot-q4`,
HEAD `7c2d307`, sin commit.

Diagnóstico posterior `010700_72c96fb8`, 7-oct-2026: dos generaciones,
un juicio independiente, cobertura 1/1, 19/19 controles, 1/1 favorable,
sin fallos, errores, pendientes o contradicciones. Texto «El ticket promedio
fue de 125 MXN.» con fuentes S3 de valor/unidad; fecha `2026-09-24` en
metadatos. Hash/digest comprobados, originales intactos; revisión 1 por cierre
global de 36 partes. El fallo anterior de tanda 3 se conserva.

Nueva candidata completa bajo las instrucciones actuales: cuatro tandas nuevas
de siete, 28 casos/36 partes/22 respondibles, gen máximo 14 y juez 2/2/3/3.
No transferir juicios ni sumar el diagnóstico al conjunto anterior. Plan de
tanda 1 verificado sin clave/API. Solo documentación, sin repetir suite;
última general 222 aprobadas, una integración opt-in omitida y 114 subpruebas.
013/016 abiertas, `codex/chatbot-q4`, HEAD `7c2d307`, sin commit; Paso 4 no cerrado.

Nueva candidata `full_batch1_140112_78307c30`, 8-oct-2026: 13 gen/dos juez,
6/7 cobertura, 115/117 controles, 6/7 independientes favorables. Timeout
del redactor en `retrieved_injection`, respaldo genérico sin claims y juicio
adverso correcto; cero errores del juez, pendientes o contradicciones.
Hash/digests verificados, originales intactos. Espera del adaptador Gemini
offline ampliada 30→60 s con cero reintentos; fuente, guía y guardas intactas.
Focalizadas 69 aprobadas y 42 subpruebas; general 224 aprobadas, una
integración opt-in omitida y 114 subpruebas en 84.68 s; efecto real pendiente. Diagnóstico
único habilitado, máximo dos generaciones/un juez; sintaxis y rechazo de
combinación con tanda completa verificados sin clave/API. Tras éxito,
repetir tanda 1 fallida y continuar 2/3/4. 013/016 abiertas, rama
`codex/chatbot-q4`, HEAD `7c2d307`, sin commit; Paso 4 no cerrado.

Diagnóstico posterior `230256_7f11ca6e`, 8-oct-2026, `retrieved_injection`:
cobertura 1/1, 16/16 controles y 1/1 juicio independiente favorable, dos
generaciones y una llamada del juez, cero fallos/pendientes/errores. Resume
contenido N14 con fuente por claim, sin instrucciones recuperadas. Hash/digest
comprobados, resumen reproducido sin red, originales y tanda fallida intactos.
Revisión 1 por exigir 36 partes; éxito después del ajuste de espera, sin causa
del timeout o estabilidad demostradas. Sigue repetir tanda 1 fallida, máximo
14 gen/dos juez, después 2/3/4 tras revisar informes; plan correcto sin clave/API.
No sustituir juicios ni sumar diagnóstico duplicado al conjunto. Solo
documentación, sin repetir suite; última general 224 aprobadas, una omitida
y 114 subpruebas. 013/016 abiertas, `codex/chatbot-q4`, HEAD `7c2d307`,
sin commit; Paso 4 abierto hasta 36 partes/22 respondibles validadas.

Tanda 1 recuperada `full_batch1_231009_cae0310c`, 8-oct-2026: 14 generaciones,
dos llamadas del juez, cobertura 7/7, 118/118 controles y 7/7 juicios
independientes favorables; cero fallos, pendientes, errores o contradicciones.
Hash/siete digests comprobados y resumen recalculado sin red; originales y
tanda fallida intactos. Avance actual 7/28 casos, 7/36 partes y 7/22 respondibles;
revisión código 1 por requerir el conjunto de 36 partes. Sigue tanda 2, siete
partes/una respondible, máximo 14 gen/dos juez; plan correcto sin clave/API.
Continuar 3/4 tras revisar informes, sin sumar diagnósticos o tandas históricas.
Solo documentación, sin repetir suite ni cambiar comportamiento; última
general 224 aprobadas, una omitida y 114 subpruebas. 013/016 abiertas,
`codex/chatbot-q4`, HEAD `7c2d307`, sin commit; Paso 4 no cerrado.

Tanda 2 aprobada `full_batch2_231955_a1e7d7bd`, 8-oct-2026: 12 generaciones,
dos llamadas del juez, cobertura 1/1, 102/102 controles y 7/7 juicios
independientes favorables; cero fallos, pendientes, errores o contradicciones.
Negocio incorrecto rechazado con cero generaciones. Informe de segunda
ejecución correcto; falta de informe reciente no usa uno anterior y ausencias,
cálculo/fuera de alcance reciben respuesta esperada. Hash/siete digests,
resúmenes y acumulado comprobados sin red, seis JSON de tandas 1/2 intactos.
Acumulado actual 14/28 casos, 14/36 partes, 8/22 respondibles, 220/220 controles,
26 gen/cuatro juez. Sigue tanda 3, diez partes/seis respondibles, máximo 14
gen/tres juez; plan correcto sin clave/API. Revisar antes de continuar 4;
no sumar diagnósticos o tandas históricas. Solo documentación, sin repetir
suite; última general 224 aprobadas, una omitida y 114 subpruebas. 013/016
abiertas, `codex/chatbot-q4`, HEAD `7c2d307`, sin commit; Paso 4 no cerrado.

Tanda 3 aprobada `full_batch3_232441_8d0d024f`, 8-oct-2026: 14 gen/tres juez,
cobertura 6/6, 145/145 controles y 10/10 juicios independientes favorables;
cero fallos, pendientes, errores o contradicciones. Fecha explícita conserva
`125 MXN` con fuente/fecha en metadatos; catálogo 35/35 nombres en ocho claims,
máximo 28 fuentes por claim. Hash/diez digests, resumen y acumulado comprobados
sin red, nueve JSON intactos. Acumulado actual 21/28 casos, 24/36 partes,
14/22 respondibles, 365/365 controles, 40 gen/siete juez. Sigue tanda 4, doce
partes/ocho respondibles, máximo 14 gen/tres juez; plan correcto sin clave/API.
Revisar y consolidar cuatro tandas sin nuevas llamadas, sin sumar diagnósticos
o tandas históricas. Solo documentación, sin repetir suite; última general 224
aprobadas, una omitida y 114 subpruebas. 013/016 abiertas, 018 resuelta,
`codex/chatbot-q4`, HEAD `7c2d307`, sin commit; Paso 4 no cerrado.

Tanda 4 `full_batch4_235606_4090759b`, 8-oct-2026: 14 gen/tres juez,
7/8 cobertura, 179/182 controles y 11/12 juicios favorables. Informe en pregunta
mixta rechazado por revisión interna, respaldo sin contenido; falla cobertura,
generación y juicio externo. Negativa a dividir también rechazada internamente,
respaldo seguro aprobado externamente, pero falla generación. Tres fallos
mecánicos en dos partes; no hay error del juez o timeout/API registrado.
Borradores descartados no guardados, contenido y causa exacta pendientes.

Consolidado completo actual: 28 casos/36 partes, 35/36 favorables, 21/22
respondibles, 544/547 controles, 54 gen/diez juez históricos, cero pendientes,
errores o contradicciones; cero nuevas API al consolidar, doce JSON intactos.
Arnés añade traza opt-in solo para esos dos casos sintéticos/Gemini/máximo
cuatro llamadas, con objetos validados, clave ocultada y errores como códigos
fijos. Archivo separado, ausente en corrida ordinaria; no constituye revisión
independiente ni modifica N15, guía, fuentes o guardas. Focalizadas 75/47
subpruebas, 9.20 s; general 230 aprobadas, una omitida y 119 subpruebas,
54.15 s. Plan/sintaxis/rechazo de modos y juez igual correctos antes de clave.
Sigue `-DiagnosticoTanda4`, máximo cuatro gen/un juez; analizar antes de
corregir o repetir. 013/016 abiertas, `codex/chatbot-q4`, HEAD `7c2d307`,
sin commit; Paso 4 no cerrado y Paso 5 posterior.

Diagnóstico aprobado, 9-oct-2026: `batch4_diagnostic_133615_e9264e7f`,
cuatro gen/un juez, 45/45 controles, cobertura 2/2 y 3/3 juicios independientes
favorables; cero fallos/errores/pendientes/contradicciones. Cuatro registros de
traza coherentes: ticket 125 MXN, resumen N14 de segunda ejecución y negativa
a dividir; borradores aprobados internamente. SHA/tres digests, fixture,
fuentes, renderizado y resúmenes comprobados sin API, originales intactos.
Rechazo previo no reproducido, causa exacta sin demostrar. Revisión 1 por
exigir 36 partes; diagnóstico no sustituye partes ni transfiere juicios.
Consolidado fallido conserva 35/36 favorables, 21/22 cobertura y 544/547 controles.
Sigue repetir solo tanda 4, máximo 14 generaciones/tres juez, espera 60 s,
sin reintentos; plan correcto sin clave/API. Si pasa, consolidar offline con
tandas 1/2/3 aprobadas. Solo documentación, sin cambiar N15/guía/guardas ni
repetir suite; última general 230 aprobadas, una omitida/119 subpruebas.
013/016 abiertas, `codex/chatbot-q4`, HEAD `7c2d307`, sin commit;
Paso 4 no cerrado y Paso 5 posterior.

### Cierre de evaluación offline — 9-oct-2026

Nueva tanda 4 `full_batch4_20261009_135244_2f9d9c1e`: siete casos/doce
partes, 8/8 cobertura, 183/183 controles, 12/12 juicios independientes
favorables, 14 generaciones/tres juez; cero fallos/pendientes/errores.
SHA `4fb4378582218c4c6b76572b7b82dc725a56ef2a0055c7767da4cd2b34db8075`;
doce digests ligados a las respuestas. Revisión aislada 1 por exigir 36 partes.
Consolidado offline de tandas 1/2/3/4 código 0, cero API nuevas: 28/28 casos,
36/36 partes, cobertura 22/22, 548/548 controles, 36/36 juicios de otro
modelo favorables, cero errores o contradicciones. Los intentos fallidos
anteriores quedan intactos; no se mezclan diagnósticos ni transfieren juicios.
013/016 resueltas para este conjunto, 21 incidencias: 20 resueltas, una
pendiente externa, cero abiertas. Paso 4 validado offline con datos sintéticos
y Gemini real acotado, sin implicar producción o disponibilidad futura.
N15/guía/guardas sin cambios, solo informes/documentación; última general
230 aprobadas, una omitida/119 subpruebas, suite no repetida.
`codex/chatbot-q4`, HEAD `7c2d307`, sin commit. Paso 5 posterior:
autenticación, autorización por negocio, endpoint, historial e interfaz.

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
