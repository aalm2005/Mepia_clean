# N15 — Herramientas deterministas de consulta

**Capa:** Aplicación | **Anterior:** `ChatGroundingPacket` | **Siguiente:** nodo conversacional
**Archivos relacionados:** `n15_chat_consulta.md`,
`n15_chat_consulta_catalogo.md`, `_glossary.md`, `agents/chat_tools.py`

## Input / Output

- Input: un `ChatGroundingPacket` ya validado.
- Operaciones de datos: `list_metrics`, `get_metric` y `get_final_report`.
- Operaciones de conocimiento: `list_metric_catalog`, `describe_metric` y
  `lookup_glossary`; rechazo: `refuse_calculation`.
- Output: `ChatToolResult` con estado, datos permitidos, evidencia y faltantes.
- No consulta base de datos, no escribe y no llama a un LLM.

## User Stories

- Como futuro nodo LLM, quiero herramientas independientes del proveedor.
- Como auditor, quiero que cada cifra o reporte conserve su evidencia exacta.
- Como usuario, quiero saber explícitamente cuando un dato no existe.
- Como sistema, quiero que un selector ambiguo no elija datos por aproximación.
- Como sistema, quiero impedir cualquier cálculo aunque la pregunta incluya
  operandos suficientes.

## Acceptance Criteria

- WHEN se listan métricas THEN solo salen campos de `CalcResult` permitidos.
- WHEN se consulta una métrica THEN acepta identificador, alias o nombre real de
  `CalcResult` mediante coincidencia exacta normalizada.
- WHEN se filtra por status THEN solo acepta los cinco estados de `CalcResult`.
- WHEN se consulta N14 THEN solo devuelve el reporte o una sección autorizada.
- WHEN S3/N14 no tienen evidencia de la misma raíz y fecha THEN no expone datos.
- WHEN un selector es inválido o no existe THEN el estado lo distingue sin lanzar
  una consulta externa.
- WHEN se consulta el catálogo o glosario THEN se limita al dominio de métricas
  del motor y `evidence` queda vacía.
- WHEN se solicita un cálculo THEN retorna `not_allowed`, no ejecuta fórmulas y
  no fabrica un resultado.
- WHEN se retorna cualquier resultado THEN declara
  `calculation_allowed=false` y `knowledge_scope="engine_metric_domain"`.
- WHEN se retorna información THEN se entregan copias profundas para impedir que
  una llamada altere las siguientes.

## Edge Cases

- Status desconocido o selector vacío: `invalid_request`.
- Métrica o sección válida pero ausente: `not_found`.
- Paquete sin fuente: `missing_data` y `data` vacío.
- Alias con mayúsculas o acentos: coincidencia normalizada exacta.
- Alias parcial: no hay coincidencia aproximada.
- Fórmula explicativa: texto educativo, nunca una operación ejecutable.
- Resultado no emitido por S3: ausente; no se deriva de otras métricas.

## Archivos relacionados de este nodo

- `n15_chat_consulta_catalogo.md` — cobertura y prohibición absoluta de cálculo.
- `_glossary.md` — contratos de herramientas, métricas y conceptos.
- `agents/chat_tools.py` — implementación sin proveedor de IA.
- `tests/test_chat_tools.py` — allowlists, evidencia, alias y mutabilidad.
- `agents/chat_conversation.py` consume estas herramientas por cada parte de la
  pregunta; no usa directamente el JSONB ni ejecuta funciones del motor.
- `tests/test_chat_conversation.py` comprueba la aplicación de evidencia y la
  negativa de cálculo al procesar preguntas libres con proveedor simulado.
- `agents/chat_response.py` recibe salidas de estas herramientas para la
  redacción libre; sus fuentes conservan ruta de campo y referencias auditables.
  Nunca sustituye una herramienta por un cálculo del modelo.
- `tests/test_chat_response.py` prueba paráfrasis permitidas, marcadores
  numéricos, revisión separada y respaldo cuando una afirmación no se valida.
- `tests/chat_offline_eval.py` mide las salidas de N15 contra paquetes sintéticos
  y expectativas por parte. Comprueba estado, cobertura, evidencia, cifras y
  unidades de las herramientas; un juicio externo separado valora el sentido.
- La corrida local simulada vigente del Paso 4 cubrió 28 casos y 36 partes,
  con 22/22 respondibles y cero fallos mecánicos. El control de solo respaldo
  falló 22/22 partes respondibles. Una muestra Gemini anterior de dos casos
  tuvo un respaldo en la negativa (`INC-20260930-013`); una muestra posterior
  de cuatro partes pasó los controles de código y cubrió 3/3 respondibles.
  La selección posterior de cinco casos nuevos cubrió 6/6 respondibles en
  10 llamadas. La corrida real del conjunto completo cubrió 19/22 partes
  respondibles y dejó 10 fallos mecánicos confirmados; Paso 4 permanece abierto.

La nueva medición dirigida del 6-oct-2026 probó siete casos y 12 partes:
3/7 respondibles cubiertas, 13 llamadas y diez fallos mecánicos; juez de otro
modelo para 12/12 partes, con cuatro juicios adversos. Las herramientas y sus
datos originales permanecieron correctos en los controles ejecutados; los
fallos fueron cobertura y generación. La corrección posterior del esquema
compacto conserva la consulta determinista y requiere repetición real.

La repetición posterior `034018_b82f6219` conservó los controles de las
herramientas y sus datos, pero las siete solicitudes de generación devolvieron
HTTP 400 antes de redactar. No se cambió recuperación, catálogo ni motor.
La mitigación de `INC-20261006-019` se limita al adaptador y diagnóstico
seguro; el juez tuvo además tres HTTP 503. La cobertura 0/7 de esa corrida
no se atribuye a falta de fuentes ni se compensa con resultados simulados.

El diagnóstico posterior `035637_2cbbbb76` conservó valor, unidad, estado,
fuentes y linaje en la redacción de `result`: 1/1 cobertura, 19/19 controles
y cero fallos, con dos llamadas del generador/verificador. El juez Flash
devolvió HTTP 503 y quedó una revisión independiente pendiente. No cambiaron
las herramientas ni el motor. El segundo juez, `gemini-3.8-flash`, también
devolvió HTTP 503 en una llamada, sin generación nueva. Ambos intentos se
conservan en `035637_2cbbbb76_semantic_attempts`, creado sin red; queda pendiente
el veredicto humano explícito para esa parte. La corrección del conteo de
revisores (`INC-20261006-020`) no modifica recuperación ni resultados S3/N14.

La nueva muestra `044143_2dc8c5f1` cubrió 7/7 partes respondibles, con 14
llamadas y 12/12 generaciones validadas internamente. Conservó el ticket de
125 MXN y caja de 40 MXN con `warning`. El único control fallido fue copiar
en `report` una instrucción recuperada con `999 MXN`; no se atribuye a la
recuperación ni se afirma que esa cifra se calculó o emitió como dato del
negocio. 019 se resuelve para aceptación de las solicitudes dirigidas.
021 mitiga generación y revisión de ese texto; las herramientas, valores,
unidades, estados, linaje y motor no cambian. Las doce revisiones independientes
siguen pendientes y el diagnóstico siguiente será solo de `report`, dos
llamadas máximas de generación y cero del juez; Paso 4 abierto.

El diagnóstico posterior `231840_af09f570` pasó `report`: dos generaciones,
un juicio independiente favorable, cobertura 1/1 y 17/17 controles, sin
reproducir la instrucción recuperada. 021 resuelta para el defecto observado;
no cambió recuperación, motor, fuentes ni política de no cálculo. La revisión
no se traslada a otros informes. Sigue el conjunto final en cuatro tandas
disjuntas de siete, máximo 14 generaciones por tanda y juez 2/2/3/3.

Primera tanda posterior `full_batch1_235430_46e3ac22`: cobertura 7/7,
118/118 controles y 7/7 juicios independientes favorables, 14 generaciones
y dos llamadas del juez, cero fallos, pendientes, errores o contradicciones.
Hash y siete digests comprobados; fuentes, herramientas y motor no cambian.
Avance 7/28 casos, 7/36 partes y 7/22 respondibles. Sigue tanda 2, incluyendo
ausencia de datos, aislamiento y rechazo de cálculo; máximo 14 generaciones
y dos llamadas del juez, sin reintentos. `wrong_business` debe conservar
cero llamadas. Plan comprobado sin clave ni API; originales intactos y sin
trasladar juicios de otros informes. 013/016 abiertas y Paso 4 no cerrado.
Solo documentación, sin repetir suite; `codex/chatbot-q4`, HEAD `7c2d307`,
sin commit.

Segunda tanda actual `full_batch2_000414_ea2379a8`: cobertura 1/1,
102/102 controles, 7/7 juicios independientes favorables, 12 generaciones
y dos llamadas del juez, sin fallos, pendientes, errores o contradicciones.
`wrong_business` se rechazó con cero generaciones; el informe usa la segunda
ejecución y la falta de informe reciente no recupera el anterior. Ausencias,
fuera de alcance y cálculo reciben la respuesta esperada. Hash y siete
digests verificados, originales intactos. Acumulado 14/28 casos, 14/36 partes,
8/22 respondibles y 220/220 controles. Sigue tanda 3, diez partes/seis
respondibles, máximo 14 generaciones y tres llamadas del juez; plan comprobado
sin clave ni API. No cambian herramientas, motor ni fuentes; solo documentación,
sin repetir suite. 013/016 abiertas, `codex/chatbot-q4`, HEAD `7c2d307`,
sin commit; Paso 4 no cerrado.

Tanda 3 `full_batch3_000945_07759275`: 5/6 cobertura, 139/141 controles,
9/10 juicios independientes favorables, 13 generaciones y tres llamadas del
juez. La fuente de fecha explícita conserva `125 MXN` y `2026-09-24`, pero
el guard rechazó el borrador por `unbound_quantity` (cifra sin marcador); respaldo genérico y
juicio adverso. No falla recuperación ni se demuestra un cálculo. El
borrador no se conserva, por lo que no se identifica la cifra problemática.
Guía mitigada para omitir cifras/fechas de la pregunta sin fuentes con slots,
mantener fecha en metadatos y comunicar valor/unidad vinculados. Herramientas,
fuentes, unidades, linaje y guardas no cambian. Focalizadas 67/42 subpruebas,
general 222 aprobadas, una omitida y 114 subpruebas; efecto real pendiente.
Sigue diagnóstico único, máximo dos generaciones y un juicio; originales
intactos, hash/digests verificados. 013/016 abiertas, Paso 4 no cerrado.

Diagnóstico posterior `010700_72c96fb8`: cobertura 1/1, 19/19 controles,
1/1 juicio independiente favorable en dos generaciones y una llamada del
juez; sin fallos, pendientes, errores o contradicciones. Comunica `125 MXN`
de S3 con valor/unidad citados y fecha `2026-09-24` en metadatos. Hash/digest
comprobados; herramientas, fuentes y guardas sin cambios, fallo previo intacto.
Nueva candidata completa con la guía actual, cuatro tandas nuevas de siete,
gen máximo 14 y juez 2/2/3/3; plan tanda 1 comprobado sin clave/API. Solo
documentación, sin repetir suite; 013/016 abiertas, Paso 4 no cerrado.

Candidata `full_batch1_140112_78307c30`: `retrieved_injection` agotó espera
del redactor, sin claims; 6/7 cobertura, 115/117 controles y 6/7 juicios
favorables en 13 gen/dos juez. No hay error del juez ni fallo de recuperación
demostrado. Espera del adaptador offline Gemini ampliada 30→60 s, sin reintentos;
herramientas, fuentes, guía, guardas y motor no cambian. Focalizadas 69 y
42 subpruebas aprobadas; general 224 aprobadas, una omitida y 114 subpruebas
en 84.68 s, efecto real pendiente. Sigue diagnóstico único,
máximo dos gen/un juez; originales intactos, hash/digests comprobados.
013/016 abiertas; Paso 4 no cerrado.

Diagnóstico posterior `230256_7f11ca6e`, 8-oct-2026: `retrieved_injection`
pasó cobertura 1/1, 16/16 controles y 1/1 juicio independiente favorable con
dos generaciones y una llamada del juez, cero fallos/pendientes/errores.
Fuente `/report/executive_summary` de N14 enlazado a la ejecución S3;
resume contenido sin instrucciones recuperadas. Hash/digest y resumen
comprobados sin red, originales y tanda fallida intactos. Herramientas,
recuperación, fuentes, guía y guardas sin cambios en este seguimiento.
Sigue repetir tanda 1 fallida, máximo 14 gen/dos juez, luego 2/3/4 tras revisar
informes; plan correcto sin clave/API. El diagnóstico no sustituye juicios ni
suma otra parte al cierre. Solo documentación, sin repetir suite; última
general 224 aprobadas, una omitida y 114 subpruebas. 013/016 abiertas,
`codex/chatbot-q4`, HEAD `7c2d307`, sin commit; Paso 4 no cerrado.

Tanda 1 recuperada `full_batch1_231009_cae0310c`, 8-oct-2026: cobertura 7/7,
118/118 controles y 7/7 juicios independientes favorables en 14 generaciones
y dos llamadas del juez; sin fallos, pendientes, errores o contradicciones.
El resumen N14 ignora instrucciones recuperadas y `two_runs_result` cita
la ejecución S3 correcta. Hash/siete digests y resumen comprobados sin red;
originales y tanda fallida intactos. Avance actual 7/36 partes, 7/22 respondibles.
Sigue tanda 2, máximo 14 gen/dos juez; plan correcto sin clave/API y rechazo
de negocio incorrecto con cero generaciones. Continuar 3/4 tras revisar
informes. Herramientas, fuentes y guardas sin cambios; solo documentación,
sin repetir suite. Última general 224 aprobadas, una omitida y 114 subpruebas.
013/016 abiertas, `codex/chatbot-q4`, HEAD `7c2d307`, sin commit; Paso 4 abierto.

Tanda 2 aprobada `full_batch2_231955_a1e7d7bd`, 8-oct-2026: cobertura 1/1,
102/102 controles y 7/7 juicios independientes favorables, 12 gen/dos juez,
sin fallos/pendientes/errores/contradicciones. N14 corresponde a la segunda
ejecución S3; si falta el reciente no se usa el anterior. Negocio incorrecto
se rechaza antes del proveedor, cero generaciones. Ausencias, cálculo y
fuera de alcance reciben respuesta esperada. Hash/siete digests, resúmenes y
acumulado comprobados sin red; seis JSON intactos. Acumulado actual 14/28 casos,
14/36 partes, 8/22 respondibles y 220/220 controles, 26 gen/cuatro juez.
Sigue tanda 3, diez partes/seis respondibles, máximo 14 gen/tres juez; plan
correcto sin clave/API. Revisar antes de continuar 4, sin sumar diagnósticos
o tandas históricas. Herramientas, fuentes y guardas sin cambios; solo
documentación, sin repetir suite. Última general 224 aprobadas, una omitida
y 114 subpruebas. 013/016 abiertas, `codex/chatbot-q4`, HEAD `7c2d307`,
sin commit; Paso 4 no cerrado.

Tanda 3 aprobada `full_batch3_232441_8d0d024f`, 8-oct-2026: cobertura 6/6,
145/145 controles y 10/10 juicios independientes favorables, 14 gen/tres juez,
sin fallos/pendientes/errores/contradicciones. Fecha explícita conserva valor
`125 MXN` de S3 y fecha en metadatos; catálogo comunica 35 nombres en ocho claims,
máximo 28 fuentes por claim. Conciliación conserva `40 MXN`/`warning`, sin
inferir causas. Hash/diez digests, resumen y acumulado comprobados sin red,
nueve JSON intactos. Acumulado actual 21/28 casos, 24/36 partes, 14/22
respondibles y 365/365 controles, 40 gen/siete juez. Sigue tanda 4, doce partes,
ocho respondibles, máximo 14 gen/tres juez; plan correcto sin clave/API.
Revisar y consolidar cuatro tandas sin llamadas nuevas, sin sumar diagnósticos
o tandas históricas. Herramientas, fuentes y guardas sin cambios; solo
documentación, sin repetir suite. Última general 224 aprobadas, una omitida
y 114 subpruebas. 013/016 abiertas, 018 resuelta, `codex/chatbot-q4`,
HEAD `7c2d307`, sin commit; Paso 4 no cerrado.

Tanda 4 `full_batch4_235606_4090759b`, 8-oct-2026: informe de pregunta mixta
y negativa a dividir llegaron a respaldo tras revisión interna, tres fallos
mecánicos; cobertura 7/8, 179/182 controles, 11/12 juicios externos favorables,
14 gen/tres juez. Juez adverso al informe sin contenido; negativa de respaldo
aritmética aprobada, sin eliminar su fallo de generación. No se guarda el
borrador, causa exacta pendiente; recuperación y fuentes no fallan en los
controles observados. Consolidado actual 35/36 favorable, 21/22 respondibles,
544/547 controles, 54 gen/diez juez históricos, cero errores/pendientes y cero
nuevas API al consolidar; doce JSON intactos.

Traza opt-in en arnés para dos casos sintéticos, cuatro generaciones/un juez:
borrador y revisión estructurados en archivo separado, clave activa ocultada,
sin errores crudos/cabeceras/cuerpos HTTP. No constituye juicio independiente;
herramientas, N15, guía y guardas sin cambios. Focalizadas 75/47 subpruebas,
general 230 aprobadas, una omitida y 119 subpruebas en 54.15 s. Plan/sintaxis
y rechazo de modos/juez igual correctos sin clave/API. Sigue
`-DiagnosticoTanda4`; analizar la traza antes de corregir o repetir.
013/016 abiertas, `codex/chatbot-q4`, HEAD `7c2d307`, sin commit; Paso 4 no cerrado.

Diagnóstico aprobado, 9-oct-2026: `batch4_diagnostic_133615_e9264e7f`,
cuatro gen/un juez, 45/45 controles, cobertura 2/2 y 3/3 juicios independientes
favorables; cero fallos/errores/pendientes/contradicciones. Traza de cuatro
registros coherente con fuentes y respuestas: 125 MXN, resumen del N14 de
segunda ejecución y negativa a dividir, aprobados internamente. SHA/tres
digests, fixture, fuentes, renderizado y resúmenes comprobados sin API;
originales intactos. Rechazo previo no reproducido, causa exacta sin demostrar.
Diagnóstico no sustituye partes ni transfiere juicios; consolidado fallido
conserva 35/36 favorables, 21/22 cobertura y 544/547 controles.
Sigue repetir solo tanda 4, máximo 14 gen/tres juez, sin reintentos, espera
60 s; plan correcto sin clave/API. Si pasa, consolidar offline con tandas
1/2/3 aprobadas. Herramientas, N15, guía y guardas sin cambios;
solo documentación, suite no repetida; última general 230 aprobadas,
una omitida/119 subpruebas. 013/016 abiertas, `codex/chatbot-q4`,
HEAD `7c2d307`, sin commit; Paso 4 no cerrado.

### Cierre del Paso 4 offline — 9-oct-2026

Nueva tanda 4 `full_batch4_20261009_135244_2f9d9c1e`: 8/8 cobertura,
183/183 controles, 12/12 juicios independientes favorables, 14 gen/tres
juez, cero fallos/errores/pendientes. Conserva selección correcta de S3/N14,
negativas de cálculo y fuente exacta; hash/doce digests verificados.
Consolidado actual con tandas 1/2/3 aprobadas: código 0, cero API nuevas,
28/28 casos, 36/36 partes, 22/22 respondibles, 548/548 controles y
36/36 juicios independientes favorables. El denominador mecánico varía con
las afirmaciones presentes, sin cambiar el umbral del 100%. Históricos
fallidos y diagnósticos intactos. 013/016 resueltas para el conjunto offline;
21 incidencias, 20 resueltas, una pendiente externa, cero abiertas.
Herramientas, N15, guía y guardas sin cambios; solo informes y documentación,
suite no repetida, última general 230 aprobadas, una omitida/119 subpruebas.
`codex/chatbot-q4`, HEAD `7c2d307`, sin commit; Paso 4 validado offline.
Sigue Paso 5 separado.

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
