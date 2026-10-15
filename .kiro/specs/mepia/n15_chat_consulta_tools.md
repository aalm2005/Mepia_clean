# N15 — Herramientas deterministas de consulta

**Estado documental al 15-oct-2026:** consultar [flujo, avance y pendientes](../../../docs/estado_actual_mepia.md). La sesión identifica y carga el negocio autorizado automáticamente; el selector con un solo negocio aún puede simplificarse. Tutorial guiado pendiente y adaptación móvil parcial. Los registros y conteos fechados siguientes conservan su alcance histórico; la publicación de código no equivale a despliegue.

**Estado vigente del chatbot — 14-oct-2026:** Pasos 1–5 implementados en desarrollo local; Paso 4 y seguimiento aceptados. Paso 5 con acceso real aprobado en MEPIA - PRUEBAS (29/29, proveedor simulado); E2E original 8/8, acceso general inicial 13/13 y frontend del equipo integrado 15/15 simulados; presentación 12/12, build final código 0, sin despliegue. Controles de producción separados.

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
- La evaluación offline de las salidas fundamentadas está aceptada: base
  36/36 independientes, 548/548 controles y cobertura 22/22; seguimiento
  dirigido 12/12, 161/161 y 5/5, cero pendientes. Las herramientas no
  cambian; el siguiente trabajo es Paso 5, autenticación y permisos.

### Historial de evaluaciones — 29-sep–12-oct-2026

Los estados pendientes, cantidades y siguientes acciones de los registros
fechados describen su ejecución histórica; el cierre vigente es el del
12-oct-2026. No se modifican informes, planes ni juicios anteriores.

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

### Primer intento del seguimiento — 10-oct-2026

`fd31f3a2` produjo 3/3 partes validadas, 2/2 cobertura y 45/45 controles
con cuatro generaciones. El juez Flash devolvio 503/UNAVAILABLE con pista
de capacidad en una llamada: cero juicios, tres pendientes. Serie detenida,
un intento iniciado y cero completos. El conjunto offline aceptado se conserva.
El usuario autorizo una llamada adicional solo del juez sobre las respuestas
originales, sin regenerar ni borrar el 503; no reanuda la serie automaticamente.
INC-016 pendiente externo para este seguimiento, codigo y plan intactos.
Progreso: `docs/evaluations/chatbot_step4_consistency_progress_20261010.json` y Markdown.
Rama `codex/chatbot-q4`, HEAD `6fa66bc`, sin commit de este registro.

### Juicio suplementario ejecutado — 10-oct-2026

`022049_dce57cb8` uso la unica llamada adicional autorizada del juez y tambien
recibio 503/UNAVAILABLE con pista de capacidad. Cero generaciones adicionales;
cuatro generaciones y dos llamadas del juez historicas, seis API en total.
Consolidado `chatbot_step4_consistency_fd31f3a2_20261011_022049_dce57cb8_combined`
conserva los dos errores por intento, tres revisiones pendientes y cero juicios
adversos; no hay aprobacion semantica. Resumen y SHA verificados sin API;
salida 1. Serie detenida, cero ejecuciones que cumplen el protocolo original,
dos sin iniciar; no hay otra llamada adicional aprobada. INC-016 pendiente
externo solo para el seguimiento. Codigo, plan y conjunto aceptado intactos.
Rama `codex/chatbot-q4`, HEAD `6fa66bc`, sin commit; suite no repetida.

El 11-oct se ejecuto el tercer intento del juez autorizado por "volvamos a
intentar": `193719_626f984c`, una llamada Flash, cero generaciones/reintentos,
otro 503/UNAVAILABLE con pista de capacidad. Consolidado actual de tres intentos:
`chatbot_step4_consistency_fd31f3a2_20261011_193719_626f984c_combined`.
Siete API historicas y tres revisiones pendientes; resumen y SHA verificados
sin API. Ambas llamadas adicionales utilizadas; serie detenida, INC-016
pendiente externo. Producto, planes y conjunto aceptado conservados.

La revision con Flash 3.8 se ejecuto el 11-oct: `20261012_010837_4fc9b3df`,
una llamada, cero generaciones/reintentos, 3/3 juicios independientes favorables,
cero pendientes/fallos. SHA y digests verificados; codigo 1 por criterio global
de 36 partes. Cuatro intentos del juez, tres 503 conservados, ocho API historicas.
INC-016 mitigada; revision completa, serie original detenida. Propuesta de tres
repeticiones nuevas con juez 3.8, maximo 15 API adicionales, aun sin autorizar:
`chatbot_step4_consistency_judge38_resume_proposal_20261011.json` y Markdown.
Originales y criterio conservados; preflight verificado sin clave ni API.

La nueva serie de tres repeticiones con juez 3.8 ya esta autorizada, maximo
15 API adicionales, sin reintentos; primera lista y aun sin ejecutar.
Plan `chatbot_step4_consistency_judge38_authorized_plan_20261011.json` y estado
de serie separado. Envoltorio `probar_consistencia_juez38.ps1` bloquea duplicados
y avance sin auditoria; sintaxis, tres preflights y bloqueo de posicion 2
comprobados sin API. La autorizacion persiste entre exitos; detener ante fallos.

Primera nueva repeticion `025040_58b2769d`: 45/45, 2/2 y 3/3 generaciones;
juez 3.8 con 503/UNAVAILABLE, tres revisiones pendientes. Auditoria sin API,
SHA/traza/plan coherentes. Serie detenida, 0/3 completas, posiciones 2/3
bloqueadas; cinco de las 15 API usadas y diez sin usar no habilitan continuar.
Seguimiento total 13 API. INC-016 pendiente externo; el juicio previo se
conserva solo para su informe y no se transfiere al nuevo. Codigo sin cambios.


### Revision suplementaria preparada — 11-oct-2026

El usuario autorizo seguir intentando: se preparo una unica revision
adicional con juez Gemini 3.8 de las tres respuestas guardadas `58b2769d`,
cero generaciones y maximo una llamada suplementaria sin reintentos. Aun no
ejecutada; historial 13 API, maximo 14 tras el intento. Presupuesto separado;
las diez API sin usar y repeticiones 2/3 permanecen bloqueadas. El 503 original
y criterio de tres ejecuciones sin errores se conservan; revisar el resultado
antes de continuar. Plan `chatbot_step4_consistency_judge38_run1_retry1_plan_20261011.json` y Markdown,
ejecutor `.test_tmp/revisar_consistencia_juez38_run1.ps1`. INC-016 pendiente externo, cero API en preparacion.


### Revision recuperada y propuesta de continuacion — 11-oct-2026

Revision actual de `58b2769d` recuperada con Gemini 3.8: 3/3 juicios
independientes favorables, cero pendientes/fallos; una llamada suplementaria
del juez y cero generaciones. Salida 1 solo por gate global de 36 partes.
503 original conservado en `chatbot_step4_consistency_judge38_run1_20261012_045201_1e1da5bf_combined`; seguimiento total 14 API.
La serie mantiene 0/3 ejecuciones sin errores del plan original y posiciones
2/3 bloqueadas. Propuesta `chatbot_step4_consistency_judge38_recovery_amendment_proposal_20261011.json` y Markdown, aun no autorizada:
aceptar esta generacion revisada para calidad y completar solo las dos
restantes con las diez API ya presupuestadas, conservando el error de
disponibilidad. INC-016 mitigada, conjunto aceptado intacto; cero API nuevas
en auditoria y ninguna nueva llamada habilitada por esta propuesta.


### Continuacion con recuperacion aceptada — 11-oct-2026

Continuacion aceptada: primera generacion aprobada para calidad (1/3),
503 original registrado como disponibilidad. Nuevo plan `chatbot_step4_consistency_judge38_recovery_authorized_plan_20261011.json`;
estado en `chatbot_step4_consistency_judge38_recovery_series_progress_20261011.json` y Markdown. Posicion 2 lista, 3 bloqueada
hasta auditoria; ejecutar solo las dos restantes con maximo diez API ya
presupuestadas, sin reintentos y detener ante nuevo fallo. Historial actual
14 API, maximo acumulado 24; cero llamadas nuevas en preparacion. Ejecutor
`.test_tmp/probar_consistencia_recuperada_juez38.ps1 -Repeticion 2..3`. Plan/runner originales y sus 0/3 ejecuciones
sin errores conservados; conjunto aceptado intacto e INC-016 mitigada.


### Repeticion 2 aprobada y tercera habilitada — 11-oct-2026

Repeticion 2 aprobada (`052052_dabc0f75`): 45/45 controles, cobertura
2/2 y 3/3 juicios independientes favorables, cero fallos/pendientes/errores.
Avance bajo el ajuste aceptado 2/3 generaciones aprobadas para calidad;
tercera habilitada con la autorizacion existente, maximo cinco API restantes,
sin reintentos y detener ante nuevo fallo. Historial 19 API (12 gen/7 juez),
maximo acumulado 24. Auditoria `chatbot_step4_consistency_judge38_recovered_run2_audit_20261011.json` y Markdown, cero API nuevas.
503 inicial conservado; conjunto aceptado intacto e INC-016 mitigada. Estado
en `chatbot_step4_consistency_judge38_recovery_series_progress_20261011.json`; ejecutar solo
`.test_tmp/probar_consistencia_recuperada_juez38.ps1 -Repeticion 3` y auditar.


### Tercera detenida y presupuesto agotado — 11-oct-2026

Tercera `052919_6ff8abfb` fallida: 44/45 controles, cobertura 2/2, revisor
interno veta una negativa a dividir identica a las aprobadas antes; respaldo
seguro, sin calculo. Juez externo 503, tres juicios pendientes. Serie detenida
2/3, diez de diez API usadas y ninguna adicional autorizada; historial 24 API
(16 gen/8 juez). INC-013 reabierta para este seguimiento e INC-016 pendiente
externo; conjunto historico aceptado preservado. Auditoria `chatbot_step4_consistency_judge38_recovered_run3_audit_20261011.json`
y Markdown; cero API en auditoria. Tratar revision interna antes de nuevas pruebas.


### Mitigacion local de negativas aun sin medir — 11-oct-2026

Mitigacion local preparada en agents/chat_response.py: guia especial solo
para la revision de negativas calculation/not_allowed respaldadas por policy.
Escritor, datos, schemas, guardas y veto intactos. 48 pruebas/23 subpruebas
aprobadas, comparacion de 28 fixtures/54 callbacks con seis casos afectados,
cero API. Efecto con Gemini real pendiente; version nueva no validada offline
todavia. INC-013 abierta para seguimiento e INC-016 pendiente externo.
Presupuesto anterior agotado (24 API), ejecutores anteriores congelados.
**Fase 1 ejecutada y detenida — 12-oct-2026:**
`chatbot_step4_policy_refusal_phase1_20261012_063948_772d6fd5` produjo tres
partes validadas internamente: 45/45 controles, cobertura 2/2 y cero fallos
mecanicos, en cuatro generaciones. La negativa a dividir paso la revision
interna con la nueva guia en esta ejecucion; esto no demuestra estabilidad
general ni sustituye el juicio independiente. Flash 3.8 hizo una llamada,
`APITimeoutError`, sin HTTP ni respuesta guardada: cero juicios y tres pendientes.
No se clasifica como 503/capacidad ni se atribuye a la clave; causa no demostrada.

Auditoria `chatbot_step4_policy_refusal_phase1_audit_20261012.json` y Markdown:
fuente/plan/ejecutores/intento/fixture/diez huellas correctos, replay completo de
cuatro registros identico y resumen semantico recalculado identico. Las 264
huellas originales del plan y 274 archivos previos a la auditoria intactos;
cero API al auditar. Fase 1 conserva el timeout; fase 2 bloqueada segun el plan.
Cinco de 18 API autorizadas usadas. Las trece restantes pertenecen a fase 2,
sin habilitar; historial del seguimiento 29 API (20 gen/9 juez).
Dos exitos previos para calidad, ninguna nueva generacion con guia revisada
aprobada independientemente. No contar el reemplazo ni cerrar Paso 4.
INC-20260930-013 abierta; INC-20260930-016 pendiente externo por timeout.

**Revisión suplementaria autorizada — 12-oct-2026:** el usuario indicó
«ok entonces hagamos las pruebas», tras explicar el presupuesto y la recuperación.
Plan `chatbot_step4_policy_refusal_phase1_judge_recovery_authorized_20261012.json`:
revisar una vez las tres respuestas guardadas de `063948_772d6fd5` con Gemini 3.8,
cero generaciones, máximo una llamada del juez, espera 60 s y cero reintentos.
La propuesta y el plan original se conservan como registros históricos.
El máximo de esta validación aumenta de 18 a 19 API adicionales: cinco usadas,
una suplementaria autorizada aún sin ejecutar y trece reservadas para fase 2.
El historial sigue en 29 API (20 generación/9 juez); máximo acumulado 43.

Aceptar la recuperación de fase 1 para calidad solo con tres juicios favorables,
sin nuevos errores ni contradicciones y auditoría favorable ligada a las mismas
respuestas. Conservar el timeout original como fallo de disponibilidad. Entonces
se puede habilitar fase 2 con sus trece llamadas ya autorizadas, sin otra aprobación
entre éxitos y con detención ante cualquier fallo o revisión pendiente. Ambas
fases deben pasar para contar el reemplazo de la tercera generación fallida;
no afirmar tres repeticiones exitosas con la guía nueva ni trasladar juicios.
Fase 2 permanece bloqueada; ningún intento suplementario real reservado.
INC-20260930-013 abierta; INC-20260930-016 pendiente externo; Paso 4 no cerrado.

**Fase 1 recuperada y fase 2 habilitada — 12-oct-2026:** el suplemento
`chatbot_step4_policy_refusal_phase1_judge_recovery_20261012_072935_21c041e7`
obtuvo 3/3 juicios independientes favorables, cero pendientes, errores nuevos,
fallos o contradicciones, con una llamada del juez 3.8 y cero generaciones.
Fuente y tres digests coinciden; resumen recalculado idéntico. Código de revisión
1 únicamente por el requisito global de 36 partes frente a las tres de esta muestra.
Auditoría `chatbot_step4_policy_refusal_phase1_judge_recovery_audit_20261012.json`
favorable, diez huellas de código y 286 archivos previos preservados; cero API.
El consolidado conserva el APITimeoutError original en attempts, cuatro
generaciones contadas una sola vez y dos llamadas históricas del juez.

Fase 1 aceptada para calidad bajo el criterio de recuperación autorizado:
45/45 controles, cobertura 2/2 y 3/3 favorables. Su timeout permanece registrado
como disponibilidad. Fase 2 lista con la autorización existente: cinco preguntas,
nueve partes y tres respondibles, máximo diez generaciones/tres juez (trece API),
espera 60 s, sin reintentos y detener ante cualquier fallo o revisión pendiente.
Ejecutar una vez `.test_tmp/validar_negativas_paso4.ps1 -Fase 2` y auditar.
Seis de 19 API adicionales usadas; trece restantes. Historial del seguimiento
30 API (20 generación/10 juez). La fase 2 todavía no se ha ejecutado.
Dos éxitos anteriores y uno con la guía nueva se conservan por separado;
el reemplazo de la tercera generación fallida sigue condicionado a fase 2
aprobada. No afirmar tres repeticiones exitosas con la guía nueva ni trasladar
juicios. INC-20260930-013 abierta; INC-20260930-016 mitigada para esta recuperación.
21 incidencias: 19 resueltas, una abierta y una mitigada; Paso 4 no cerrado.

**Fase 2 detenida por 503 del juez — 12-oct-2026:**
`chatbot_step4_policy_refusal_phase2_20261012_074133_e8482e9d` completó cinco
casos/nueve partes con diez generaciones: 116/116 controles, cobertura 3/3 y
nueve partes validadas internamente, cero fallos mecánicos. El juez 3.8 hizo
una llamada al primer lote (dos partes), InternalServerError, HTTP 503,
UNAVAILABLE y pista de capacidad. Cero juicios favorables/adversos y nueve
pendientes; se detuvo sin llamar los otros dos lotes. La pista no demuestra
la causa interna y el error no es un rechazo semántico de las respuestas.

Auditoría `chatbot_step4_policy_refusal_phase2_audit_20261012.json`:
fuente/plan/intento/ejecutores/diez huellas correctos, resumen recalculado
idéntico, 298 archivos previos intactos y cero API al auditar. La fase 1
recuperada mantiene 3/3 favorables; su timeout y el 503 de fase 2 se conservan.
17 de 19 API adicionales usadas (14 generación/3 juez); dos llamadas del juez
sin usar, bloqueadas por la regla de detención. Historial del seguimiento
41 API (30 generación/11 juez). Fase 2 detenida, reemplazo sin contar y Paso 4
sin cerrar. INC-20260930-013 abierta; INC-20260930-016 pendiente externo;
21 incidencias: 19 resueltas, una abierta y una pendiente externa.

Propuesta `chatbot_step4_policy_refusal_phase2_judge_recovery_proposal_20261012.json`,
todavía sin autorizar: revisar únicamente las nueve respuestas guardadas en
tres lotes de 2/3/4 partes, cero generaciones, máximo tres llamadas del juez,
sin reintentos y detener ante primer fallo. Usaría las dos llamadas restantes
y una extra, elevando el máximo adicional de 19 a 20 (máximo acumulado 44).
Aceptar recuperación para calidad solo con 9/9 juicios independientes favorables,
sin errores nuevos ni contradicciones y auditoría favorable; conservar el 503
original. El criterio de reemplazo exige ambas fases aprobadas y conserva las
versiones distintas de guía y errores. La propuesta no habilita llamadas;
ejecutor `.test_tmp/revisar_negativas_fase2_juez.ps1` bloqueado hasta aprobación.

**Continuación de intentos autorizada — 12-oct-2026:** el usuario indicó
«bueno vamos a seguir haciendo mas intentos hasta que todas las pruebas pasen».
Autoriza continuar la validación pendiente y sus recuperaciones, sin volver a
solicitar autorización para intentos del mismo alcance. Cada ejecución mantiene
un plan acotado, registro propio y auditoría antes del intento siguiente. Ante
indisponibilidad del proveedor se prepara otro intento sobre las respuestas
pendientes, dejando una pausa; un juicio adverso exige análisis del posible
defecto antes de repetir. No se descartan errores ni juicios desfavorables.

Siguiente intento preparado, aún sin ejecutar: plan
`chatbot_step4_policy_refusal_phase2_judge_recovery_authorized_20261012.json`;
ejecutor existente `.test_tmp/revisar_negativas_fase2_juez.ps1`. Revisar las nueve
respuestas de `074133_e8482e9d` en tres lotes de 2/3/4 partes, cero generaciones,
máximo tres llamadas del juez Gemini 3.8, espera 60 s, cero reintentos internos
y detener ante primer error, juicio adverso o lote incompleto. Usar las dos
llamadas restantes y una extra: máximo de esta validación 20 API adicionales,
17 usadas y tres habilitadas solo para esta recuperación. Historial 41 API
(30 generación/11 juez), máximo 44 tras este intento. Una ampliación posterior
se registrará en un nuevo plan bajo esta misma autorización antes de ejecutarla.

Aceptar fase 2 para calidad únicamente con 9/9 juicios independientes favorables,
sin errores nuevos ni contradicciones y auditoría favorable; conservar su 503
original y el timeout de fase 1. Después evaluar ambas fases bajo el criterio
de reemplazo ya aceptado, conservando las versiones distintas de guía. No afirmar
tres repeticiones con la guía nueva ni trasladar juicios de otras respuestas.
Generación de fase 2 ya aprobada: 116/116 controles, cobertura 3/3 y nueve partes
validadas internamente. Reemplazo sin contar, Paso 4 abierto; INC-20260930-013
abierta e INC-20260930-016 pendiente externo. Ningún intento nuevo reservado.

**Segundo suplemento de fase 2 preparado tras otro 503 — 12-oct-2026:**
El intento `083847_c6d73947` hizo una llamada del juez 3.8, cero generaciones
y cero reintentos; primer lote con InternalServerError, 503/UNAVAILABLE y pista
de capacidad. Cero juicios y nueve pendientes; los otros dos lotes no se llamaron.
La pista no demuestra causa ni fallo de contenido. Auditoría
`chatbot_step4_policy_refusal_phase2_judge_recovery_audit_20261012.json`:
fuente/plan/intento/ejecutores correctos, resumen recalculado idéntico y 310
evidencias anteriores intactas. Consolidado `083847_c6d73947_combined` conserva
ambos 503 en attempts y diez generaciones contadas una sola vez. El campo
total_api_calls del consolidado cuenta solo las dos llamadas históricas del juez.
Generación 116/116 y cobertura 3/3 conservadas; fase 1 recuperada y timeout intactos.

Nuevo intento autorizado bajo la indicación vigente de continuar hasta completar
las pruebas: `chatbot_step4_policy_refusal_phase2_judge_recovery_retry2_authorized_20261012.json`,
ejecutor `.test_tmp/reintentar_negativas_fase2_juez.ps1`. Revisar las mismas nueve
partes pendientes en lotes 2/3/4, cero generaciones, máximo tres juez 3.8, espera
60 s y cero reintentos internos; detener ante error, juicio adverso o incompleto.
18/21 API adicionales usadas, tres habilitadas (dos sin usar y una extra);
historial 42 API (30 generación/12 juez), máximo 45 tras este intento. Pausa
entre intentos manuales; auditar antes de preparar otro bajo la misma autorización.
Un fallo de contenido requiere análisis antes de repetir, sin descartar juicios.

Aceptar recuperación solo con 9/9 independientes favorables y auditoría favorable,
sin errores nuevos ni contradicciones, manteniendo ambos 503 como disponibilidad.
Reemplazo sin contar, Paso 4 abierto; INC-20260930-013 abierta e INC-20260930-016
pendiente externo. Nuevo intento aún sin ejecutar ni reservar, cero API del agente.
Comprobación local: sintaxis PowerShell/Python correcta, MostrarPlan nuevo código 0,
ejecutor suplementario anterior bloqueado código 1 antes de clave/nueva reserva.
Diez huellas, 264 originales, 310 protegidos y cinco archivos de consolidado/auditoría
coincidentes antes/después; presupuesto ligado al progreso, diff de espacios código 0.
Registro `chatbot_step4_policy_refusal_phase2_judge_recovery_retry2_preflight_20261012.json`.
Estos controles habilitan el intento, no constituyen juicio independiente.

**Tercer suplemento de fase 2 preparado tras otro 503 — 12-oct-2026:**
El intento `093132_828546ec` hizo una llamada del juez 3.8, cero generaciones
y cero reintentos; primer lote con InternalServerError, 503/UNAVAILABLE y pista
de capacidad. Cero juicios y nueve pendientes; los otros dos lotes no se llamaron.
La pista no demuestra causa ni fallo de contenido. Auditoría
`chatbot_step4_policy_refusal_phase2_judge_recovery_retry2_audit_20261012.json`:
fuente/plan/intento/ejecutores correctos, resumen recalculado idéntico y 322
evidencias anteriores intactas. Consolidado `093132_828546ec_combined` conserva
los tres 503 en attempts y diez generaciones contadas una sola vez. El campo
total_api_calls del consolidado cuenta solo las tres llamadas históricas del juez.
Generación 116/116 y cobertura 3/3 conservadas; fase 1 recuperada y timeout intactos.

Nuevo intento autorizado bajo la indicación vigente de continuar hasta completar
las pruebas: `chatbot_step4_policy_refusal_phase2_judge_recovery_retry3_authorized_20261012.json`,
ejecutor `.test_tmp/reintentar_negativas_fase2_juez_intento3.ps1`. Revisar las mismas nueve
partes pendientes en lotes 2/3/4, cero generaciones, máximo tres juez 3.8, espera
60 s y cero reintentos internos; detener ante error, juicio adverso o incompleto.
19/22 API adicionales usadas, tres habilitadas (dos sin usar y una extra);
historial 43 API (30 generación/13 juez), máximo 46 tras este intento. Pausa
entre intentos manuales; auditar antes de preparar otro bajo la misma autorización.
Un fallo de contenido requiere análisis antes de repetir, sin descartar juicios.

Aceptar recuperación solo con 9/9 independientes favorables y auditoría favorable,
sin errores nuevos ni contradicciones, manteniendo los tres 503 como disponibilidad.
Reemplazo sin contar, Paso 4 abierto; INC-20260930-013 abierta e INC-20260930-016
pendiente externo. Nuevo intento aún sin ejecutar ni reservar, cero API del agente.
Comprobación local: sintaxis PowerShell/Python correcta, MostrarPlan nuevo código 0,
ejecutor suplementario anterior bloqueado código 1 antes de clave/nueva reserva.
Diez huellas, 264 originales, 322 protegidos y cinco archivos de consolidado/auditoría
coincidentes antes/después; presupuesto ligado al progreso, diff de espacios código 0.
Registro `chatbot_step4_policy_refusal_phase2_judge_recovery_retry3_preflight_20261012.json`.
Estos controles habilitan el intento, no constituyen juicio independiente.

**Juez alternativo Gemini 3.6 preparado tras cuatro 503 — 12-oct-2026:**
El intento `094039_328ff3d4` hizo una llamada del juez 3.8, cero generaciones
y cero reintentos; primer lote con InternalServerError, 503/UNAVAILABLE y pista
de capacidad. Cero juicios y nueve pendientes; los otros dos lotes no se llamaron.
La pista no demuestra causa ni fallo de contenido. Auditoría
`chatbot_step4_policy_refusal_phase2_judge_recovery_retry3_audit_20261012.json`:
fuente/plan/intento/ejecutores correctos, resumen recalculado idéntico y 334
evidencias anteriores intactas. Consolidado `094039_328ff3d4_combined` conserva
los cuatro 503 en attempts y diez generaciones contadas una sola vez. El campo
total_api_calls del consolidado cuenta solo las cuatro llamadas históricas del juez.
Generación 116/116 y cobertura 3/3 conservadas; fase 1 recuperada y timeout intactos.

Nuevo intento autorizado bajo la indicación vigente de continuar hasta completar
las pruebas: `chatbot_step4_policy_refusal_phase2_judge36_authorized_20261012.json`,
ejecutor `.test_tmp/revisar_negativas_fase2_juez36.ps1`. Revisar las mismas nueve
partes pendientes en lotes 2/3/4, cero generaciones, máximo tres juez 3.6, espera
60 s y cero reintentos internos; detener ante error, juicio adverso o incompleto.
20/23 API adicionales usadas, tres habilitadas (dos sin usar y una extra);
historial 44 API (30 generación/14 juez), máximo 47 tras este intento. Pausa
entre intentos manuales; auditar antes de preparar otro bajo la misma autorización.
Un fallo de contenido requiere análisis antes de repetir, sin descartar juicios.

Aceptar recuperación solo con 9/9 independientes favorables y auditoría favorable,
sin errores nuevos ni contradicciones, manteniendo los cuatro 503 como disponibilidad.
Reemplazo sin contar, Paso 4 abierto; INC-20260930-013 abierta e INC-20260930-016
pendiente externo. Nuevo intento aún sin ejecutar ni reservar, cero API del agente.
Comprobación local: sintaxis PowerShell/Python correcta, MostrarPlan nuevo código 0,
ejecutor suplementario anterior bloqueado código 1 antes de clave/nueva reserva.
Diez huellas, 264 originales, 334 protegidos y cinco archivos de consolidado/auditoría
coincidentes antes/después; presupuesto ligado al progreso, diff de espacios código 0.
Registro `chatbot_step4_policy_refusal_phase2_judge36_preflight_20261012.json`.
Estos controles habilitan el intento, no constituyen juicio independiente.

Cambio de juez a propuesta del usuario «Y si cambiamos el modelo?? cuál estamos
utilizando?»: se elige gemini-3.6-flash, modelo estable con salidas estructuradas
según https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash. Se conserva
el generador/revisor interno gemini-3.5-flash-lite y el mismo endpoint compatible.
No se ha verificado disponibilidad de 3.6 en esta cuenta; el cambio es una prueba
de disponibilidad y no garantiza eliminar el 503. INC-20260930-014 corregida:
21 incidencias reales y contadores del nuevo plan 14 generación/6 juez/20 previas,
reconstruidos de informes e intentos. La discrepancia del plan retry3 se documenta
en la auditoría nueva, preservando sus bytes; límites ejecutables originales correctos.

**Juez 3.6: cinco aprobaciones auditadas, cuatro pendientes — 12-oct-2026:**
`095323_6fba7d46` produjo cinco juicios independientes favorables en tres llamadas:
explicit_calculation, implicit_calculation y las tres partes de mixed. Fuente,
cinco digests y cuatro criterios verdaderos por parte comprobados; resumen
recalculado idéntico. Tercer lote con 503/UNAVAILABLE, cuatro partes pendientes:
question_injection y result_and_projection. Sin fallos de contenido o mecánicos.
Auditoría `chatbot_step4_policy_refusal_phase2_judge36_partial_audit_20261012.json`:
346 evidencias anteriores intactas. Consolidado conserva cinco 503, siete llamadas
históricas del juez y diez generaciones contadas una vez; fuente original intacta.

Se prepara únicamente el lote pendiente bajo la autorización vigente:
`chatbot_step4_policy_refusal_phase2_judge36_pending_authorized_20261012.json`,
ejecutor `.test_tmp/revisar_pendientes_fase2_juez36.ps1`. Cuatro partes, máximo una
llamada del juez 3.6, cero generaciones/reintentos, 60 s. Preguntas completas,
mismo informe/digests y payload idéntico al tercer lote original; el juez no ve
juicios previos. Mantener las cinco aprobaciones sin repetirlas. Nuevo intento
aún sin ejecutar ni reservar. 23/24 API adicionales usadas (14 gen/9 juez),
una habilitada; historial 47 API (30 gen/17 juez), máximo 48 tras el intento.

Aceptar recuperación de fase 2 solo si las cuatro pendientes pasan sin error
nuevo/contradicción y una auditoría confirma las nueve aprobaciones acumuladas.
Conservar los cinco 503 como disponibilidad; criterio global de 36 intacto,
sin afirmar una corrida original sin errores. Fase 1 recuperada/timeout y 116/116,
3/3 de generación preservados; reemplazo sin contar y Paso 4 abierto.
INC-20260930-013 abierta e INC-20260930-016 pendiente externo; 21 incidencias,
19 resueltas, una abierta y una pendiente externa. Rama codex/chatbot-q4,
HEAD 6fa66bcc6a731a3f06df79edb5a4bf62e3c8e03c, sin commit; cero API del agente.

Controles locales: sintaxis y MostrarPlan correctos, ejecutor de nueve partes
bloqueado antes de clave/reserva; dos dobles locales (éxito/503) verifican una
llamada solo para las cuatro pendientes y conservación de cinco aprobaciones.
Diez huellas, 264 originales, 346 protegidos y cinco archivos de auditoría/
consolidado intactos; diff de espacios código 0. Registro
`chatbot_step4_policy_refusal_phase2_judge36_pending_preflight_20261012.json`.
Los dobles no aportan evidencia semántica real; suite de producto no repetida.

**Paso 4 offline y seguimiento cerrados — 12-oct-2026:** la última revisión
`121907_b98e4274` obtuvo cuatro juicios nuevos favorables en una llamada del juez
3.6, sin errores; las cinco aprobaciones previas permanecen intactas. Fase 2:
9/9 independientes, 116/116 controles y cobertura 3/3. Fase 1 ya auditada: 3/3,
45/45 y 2/2. Validación dirigida completa: siete casos/doce partes, 12/12
independientes favorables, 161/161 controles y cobertura 5/5; cero pendientes,
fallos mecánicos/semánticos o contradicciones. Fuente, digests y resúmenes
aislado/consolidado recalculados y comprobados; 361 evidencias previas intactas.
Auditoría final `chatbot_step4_policy_refusal_phase2_final_audit_20261012.json`.

Aceptación `chatbot_step4_policy_refusal_validation_acceptance_20261012.json` y
Markdown: se aplica el criterio explícitamente autorizado de dos generaciones
previas con la guía anterior más la nueva fase 1 como reemplazo del tercer
intento, condicionado a ambas fases aprobadas. Tres posiciones de calidad
aceptadas; no se afirma tres repeticiones con la guía revisada. La tercera
fallida y la serie detenida 2/3 se conservan como históricos, sin trasladarles
juicios. El conjunto base aceptado sigue intacto: 28 casos/36 partes, 36/36
independientes, 548/548 controles y cobertura 22/22. La muestra de doce partes
no sustituye el conjunto base ni modifica el gate global de 36.

Se resuelven INC-20260930-013 para el defecto validado e INC-20260930-016 para
los juicios pendientes actuales. 21 incidencias: 21 resueltas, cero abiertas o
pendientes externas en este alcance. El timeout de fase 1 y cinco 503 de fase 2
se conservan como disponibilidad; no se demuestra estabilidad estadística ni
disponibilidad general del proveedor. 24/24 API adicionales usadas (14 gen/10
juez), historial del seguimiento 48 API (30 gen/18 juez); cero llamadas habilitadas.
Cero API al auditar/consolidar; suite no repetida. Rama codex/chatbot-q4,
HEAD 6fa66bcc6a731a3f06df79edb5a4bf62e3c8e03c, sin commit ni push.
Siguiente fase: Paso 5, autenticación y autorización por negocio, trabajo separado.
Chat de solo lectura conservado; producción sin cambios. Los estados anteriores
de pendiente/detenido describen las ejecuciones históricas previas a este cierre.
