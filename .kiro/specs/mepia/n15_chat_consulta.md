# N15 — Chat de consulta fundamentada

**Continuidad de la demostración — 15-oct-2026:** correcciones de fecha y
Dashboard 051/052/053 pertenecen a integración, sin cambiar herramientas,
permisos ni prohibición de cálculo del chat. El menú conserva el análisis al
volver de Chat IA, dentro de la misma sesión y negocio. La fecha consultada
en el chat se elige para el mismo día de la auditoría. Ensayo real del 14-oct
continúa pendiente; no se reabren Pasos 1–4 ni se recalifica evidencia anterior.

**Actualización del ensayo — 15-oct-2026:** INC-048/049 resueltas localmente:
guardado terminal N14 y seguimiento por padre con error saneado. 208 pruebas y
41 subpruebas aprobadas, dos advertencias, código 0; proveedores/DB simulados.
OpenAI configurado, Claude opcional mediante respaldo ya existente.
Ver [ejecución y límites](layer3_execution.md) y
[ensayo real pendiente](../../../docs/demo_video_paso_a_paso.md).

**Entorno verificado — 15-oct-2026:** interfaz y servidor completo usan
MEPIA principal; 009/010/011 aplicadas con autorización y datos preservados.
Regresión 178/41 subpruebas, código 0; SQL real 13/13 controles. Usuario confirmó
login y pantallas antes/después del retiro de claves heredadas y firma HS256.
INC-046/047 resueltas en su alcance; INC-048 y ensayo de análisis nuevo pendientes.
Las evaluaciones anteriores conservan su entorno original.
[Ejecución, archivos y límites](../../../docs/database_unification.md).

**Publicación verificada — 15-oct-2026:** acceso por pestaña, Dashboard como
inicio y saludos del chat publicados en `codex/chatbot-q4`, commit
`49a5d05184a6e3f50c4353cafd84092df1e9b285`. Push normal código 0 y hash remoto
coincidente. INC-042/043 resueltas localmente y publicadas; INC-041 sigue pendiente
externa. [Evidencia de publicación](../../../docs/evaluations/github_access_greetings_verified_20261015.json).
Este registro se guarda en un commit documental posterior. Las menciones previas
«sin commit/push» describen su validación original. Producción sin cambios.


**Acceso e inicio — 15-oct-2026, validado localmente; sin commit:** sesión por pestaña (recargar conserva; cerrar/abrir pide login), Dashboard como inicio y bienvenida eliminada. API con Bearer y verificación de servidor; cookies antiguas no autentican. [Contrato, pruebas y límites](../../../docs/mepia_access_navigation.md). INC-042 resuelta localmente: Edge 24/24, cero errores; build y tipos código 0. 42 incidencias: 39 resueltas, dos mitigadas y una pendiente externa. Los informes fechados anteriores no validan este cambio.

**GitHub verificado — 15-oct-2026:** avances y sincronización publicados en `codex/chatbot-q4`, commit `2c2ad07754204cf6216483de017dd898b2685255`. Push normal código 0 y hash remoto coincidente. Este registro se guarda en un commit documental posterior. [Estado y evidencia](../../../docs/estado_actual_mepia.md). Los registros previos de «sin commit/push» conservan la situación de su fecha; producción sin cambios.

**Estado documental al 15-oct-2026:** consultar [flujo, avance y pendientes](../../../docs/estado_actual_mepia.md). La sesión identifica y carga el negocio autorizado automáticamente; el selector con un solo negocio aún puede simplificarse. Tutorial guiado pendiente y adaptación móvil parcial. Los registros y conteos fechados siguientes conservan su alcance histórico; la publicación de código no equivale a despliegue.

**Automatización del 14-oct-2026 (histórica, anterior al acceso por pestaña):** ejecutor por capas implementado.
Final local: 43 capas por caso aprobadas, cinco pendientes, cero fallidas,
código 0; no equivale a 43 casos funcionales completos. Regresión 154 pruebas
y 41 subpruebas, dos advertencias, 22.73 s, código 0. Edge sintético: 18
controles, cero errores, código 0; carga 70 POST simulados. Gemini real con
datos/Auth en memoria: siete de ocho casos con controles mecánicos aprobados,
C02 detenido por HTTP 429; 17/18 intentos, código 1, sin reintentos ni juez.
Ocho respuestas validadas para revisión humana, aún sin calificaciones.
INC-040 resuelta localmente, 035 actualizada/resuelta, 041 pendiente externo.
41 incidencias: 38 resueltas, dos mitigadas, una pendiente externa, cero
abiertas. Supabase/cuentas/producción y preview del usuario sin cambios;
sin commit/push. Los avisos siguientes conservan sus registros históricos;
el diseño v1 y su plantilla permanecen intactos, anteriores al ejecutor.
Sigue disponibilidad/C02, revisión humana y ampliar solo lo pendiente.
Ver [ejecutor, resultados y revisión](../../../docs/chatbot_step5_automation.md).

**Diseño original — 14-oct-2026 (histórico, previo al ejecutor):** preparados cinco conjuntos y
48 casos: datos/fuentes (12), lenguaje/límites (10), conversación/historial
(10), seguridad/fallos (10) y preparación para publicación (6). Todos pendientes
de ejecución; no se trasladan aprobaciones anteriores. Primera tanda propuesta:
D01/D03/D05/D06/L01/L07/C01/C02, nueve POST reales como máximo y hasta 18 intentos
Gemini. Plan completo: 36 POST, hasta 72 intentos, cero juez y cero reintentos
SDK; presupuesto habilitado cero. Rúbrica con dos lectores objetivo, oráculos
sintéticos, aislamiento/limpieza y plantilla vacía. Riesgo estático L02
(«qué son») pendiente de comprobar; no es una regresión demostrada. Sin cambios
de producto, modelo, SQL, usuarios, producción, commit o push. Acceso y evaluación
previos siguen cerrados en su alcance. Ejecución funcional amplia pendiente;
OpenAI y publicación separados. Ver [plan detallado](../../../docs/chatbot_step5_test_plan.md).

**Ajuste de lenguaje — 14-oct-2026 (registro anterior a la automatización):** el usuario pidió respuestas
comprensibles sin conocimientos financieros y para diversos niveles de lectura.
Se ajustó la guía común de composición: palabras cotidianas, frases cortas,
tono respetuoso, respuesta directa y breve por defecto; detalles técnicos según
la pregunta. Una definición sencilla omite fórmulas, insumos y alias no pedidos,
conservando condiciones esenciales. Redacción libre, fuentes, cifras/unidades,
alertas y prohibición de calcular intactas. Backend local reiniciado, código 0.
115 pruebas y 41 subpruebas aprobadas, dos advertencias, 11.09 s, código 0;
proveedores simulados. El usuario repitió ticket promedio en una conversación
nueva y confirmó «Sí, ahora es clara»; Next registra POST 200. Es confirmación
humana de legibilidad en esa consulta, no un juicio semántico independiente ni
una medida universal de comprensión. INC-039 resuelta en este alcance;
INC-035 actualizada por atasco del ejecutor en sandbox y ejecución posterior
aprobada fuera de él. 39 incidencias: 37 resueltas, dos mitigadas (023/031),
cero abiertas. Un archivo de producto modificado: `agents/chat_response.py`.
Sin preguntas del agente al modelo, SQL, datos/usuarios, producción, commit
ni push. Evidencias anteriores conservadas; general/build/E2E no repetidos.
Evidencia `docs/evaluations/chatbot_step5_plain_language_20261014.json`.

### Preparación de la clave Gemini del chat — 14-oct-2026 (histórico, antes del guardado)

El usuario confirmó disponer de una clave Gemini; su ingreso privado en
`api/.env`, campo `CHAT_GEMINI_API_KEY`, estaba pendiente de confirmar en este registro inicial.
Modelo previsto `gemini-3.5-flash-lite`, configuración inicial sin clave y
archivo ignorado por Git; no se cambió código ni se hicieron llamadas al
modelo. La acción siguiente de este registro era verificar presencia sin imprimir la clave,
se reiniciará únicamente Chat IA local y se comprobará una pregunta desde
la sesión del usuario. Máximo dos intentos por petición, sin reintentos del
SDK; no es una nueva evaluación completa del Paso 4 ni una adopción de OpenAI.
Rama `codex/chatbot-q4`, HEAD `6fa66bc`, sin commit/push/SQL/producción.
Evidencia `docs/evaluations/chatbot_step5_gemini_setup_20261014.json`.

**Conexión Gemini — 14-oct-2026 (registro anterior al ajuste de lenguaje):** clave Gemini guardada de forma
privada y backend local reiniciado; `api/.env` ignorado por Git. El usuario
envió «¿Qué es el ticket promedio?» y confirmó respuesta; Next registra POST
200 después del 503 previo a configurar. El texto compartido explica el
concepto y fórmula metodológica, cita diez rutas del catálogo y no incluye
el aviso de explicación no validada. Por el contrato de publicación, esa
redacción y sus claims corresponden a generación validada; inferencia desde
la evidencia visible del usuario, sin inspeccionar su sesión ni el JSON real.
Conexión de Gemini `gemini-3.5-flash-lite` confirmada para esta consulta
conceptual; no sustituye la evaluación offline ni valida todos los recorridos
reales. Fecha 2099 comprobada por lectura en MEPIA - PRUEBAS: procede del
fixture histórico `chat_grounding_correction2_test`, conservado; no se corrigió
ni eliminó. Cero preguntas del agente al modelo; una pregunta real del usuario,
con el límite existente de dos intentos por petición, sin reintentos del SDK.
38 incidencias: 36 resueltas, dos mitigadas (023/031), cero abiertas;
INC-035/038 actualizadas y resueltas en su alcance. Sin cambio de código de
producto, SQL administrativo, usuarios/propiedad, producción, commit ni push.
Pruebas anteriores conservadas; no se repitieron suites/build.
Evidencia `docs/evaluations/chatbot_step5_gemini_activation_confirmation_20261014.json`.

**Estado vigente del chatbot — 14-oct-2026:** Pasos 1–5 implementados; Paso 4 y seguimiento aceptados. Acceso del Paso 5 aprobado en `MEPIA - PRUEBAS`: ES256/JWKS/RLS/permisos/historial, 29/29, proveedor simulado. E2E original 8/8, acceso general inicial 13/13 y frontend combinado final 15/15 simulados; presentación 12/12, build/tipos código 0. Sin despliegue; producción separada.

**Capa:** Aplicación | **Anterior:** S3/N14 | **Siguiente:** ampliar el recorrido real de métricas e historial; OpenAI y producción separados
**Flujo vigente implementado/probado:** login general `/login` antes
de entrar a MEPIA. Menú compartido con icono Chat IA; `/chat` es una sección de
la misma aplicación y reutiliza sesión/negocio, sin formulario propio de login.
Mensajes de usuario/asistente, bienvenida y compositor inferior de apariencia
similar a ChatGPT; identidad visual MEPIA y fuentes/estados existentes conservados.
Validación sintética integrada 13/13, cero errores de página, código 0;
build final Next 15.5.27 código 0. Ingreso general con cuenta propia y Chat IA
desde el menú sin segundo login confirmados por el usuario el 13-oct-2026.
No se inspeccionó su navegador ni se validaron respuestas del modelo real.
Configuración/validación del modelo pendientes; producción separada.

**Integración de frontend del 14-oct-2026, terminada localmente:** apariencia
azul/fondo/bienvenida, KPI/gráficas y Salud/Reportes sobre MepiaShell, conservando
acceso único, Chat IA, contexto propio y permisos de consulta. E2E final 15/15,
presentación 12/12, build/tipos código 0, cero errores y servicios externos en
pruebas. Valor/unidad S3 sin reescalar; series separadas por unidad. Hook de
auditoría cancela respuestas anteriores y exige negocio/corrida coincidentes
para mostrar resultados; no sustituye autorización del backend legado.
INC-034/035/036/037 resueltas. Directorio entregado y 391 evidencias anteriores
intactos. Modelo real/producción separados; evidencia en la bitácora y reporte
`docs/evaluations/chatbot_step5_frontend_merge_20261014.json`.
**Archivos relacionados:** [datos del motor y bases](n15_chat_consulta_datos.md), `_glossary.md`, `db_schema.md`,
`n15_chat_consulta_tools.md`, `n15_chat_consulta_catalogo.md`,
`agents/chat_grounding.py`,
`agents/chat_tools.py`,
`agents/chat_conversation.py`, `agents/chat_response.py`,
`agents/chat_provider_gemini.py`, `agents/chat_provider_openai.py`,
`tests/chat_offline_eval.py`, `tests/fixtures/chat_offline_cases.json`

## Input / Output

Paso 5 implementado y probado localmente (12-oct-2026): `POST /business/{business_id}/chat`
exige sesión Supabase y propiedad antes de evidencia/modelo. Body cerrado:
`question`, `requested_date` opcional, `conversation_id` opcional asignado por
servidor. `GET /me/businesses` solo lista negocios propios; GET/DELETE del
historial vuelven a comprobar permiso. Contexto anterior tratado como dato no
confiable y nunca citable; ocho turnos/30 minutos/256 conversaciones por proceso.
API 38/38, auth ES256 20/20 y arranque 4/4; general 292 aprobadas/1 omitida/119 subpruebas;
E2E original 8/8 simulado; acceso común inicial 13/13 y frontend integrado 15/15 simulados; acceso real anterior
29/29 con proveedor simulado.
Build Next 15.5.27 y tipos código 0. Migración 010 aplicada dos veces en
`MEPIA - PRUEBAS` en la continuación real: un negocio/19 auditorías preservados.

Asignación posterior autorizada: cuenta propia creada por el usuario con
contraseña definida por él, propietario del negocio de pruebas verificado;
19 auditorías/UUID preservados. Login/negocio confirmados por el usuario en
Edge/Chrome, login registrado en Auth y listado Next 200,
sin llamadas reales al modelo ni producción. Registro/invitación de futuros
clientes en la interfaz es trabajo posterior; propiedad permite cuentas aisladas.

Perfil `api.chat_app:create_app --factory`: reutiliza el router N15,
exige configuración Supabase propia y valida auth/service key al iniciar.
Expone listado, consulta e historial de Chat IA. Desde el 15-oct también registra
GET/POST/PUT de configuración N10 con JWT y propiedad verificadas; guardar
ajustes es una operación separada, el chat sigue siendo de solo lectura.
No incluye ingesta/análisis ni exige sus claves. N10 validado: regresión 151/41
subpruebas, Edge 14/14 y general 25/25, build código 0; INC-044/045 resueltas,
sin commit/push. [Alcance](../../../docs/onboarding_defaults_integration.md).
Para archivos nuevos hace falta `api.main:app` y claves del motor; el ensayo
integral en la computadora de grabación sigue pendiente. Lee `api/.env` y `.env`; ES256 debe seleccionarse
expresamente para el proyecto de pruebas. Sin clave de chat, consulta devuelve
503; login/listado siguen disponibles. Interfaz local en `127.0.0.1:3016/chat`
y API en `127.0.0.1:8016`, configuradas con claves privadas fuera de Git.
Login propio confirmado en navegador normal. Focalizadas anteriores 62/62,
general 292 aprobadas/1 omitida/119 subpruebas, códigos 0.

`ChatPanel` usa `utils/chat-login-error.ts`: `AuthRetryableFetchError` del SDK
muestra «No se pudo conectar con el servicio de inicio de sesión. Revisa tu
conexión y vuelve a intentarlo.»; otros errores retornados conservan el mensaje
de credenciales, excepciones lanzadas conservan el mensaje de disponibilidad.
No se muestran excepciones privadas. SDK con fetch simulado 3/3 y tipos código 0.
INC-031 mitigada: primer `Failed to fetch` no reproducido; navegación directa
a health bloqueada en navegador integrado. No se desactivaron protecciones.
Login/listado propio confirmado no equivale a recorrido completo del modelo.

### Acceso general y navegación de MEPIA

`MepiaAuthProvider` verifica al usuario antes de compartir sesión/negocios.
La sesión se guarda en sessionStorage y una clave por pestaña aísla eventos
del SDK: recargar conserva; cerrar/abrir exige login. No recupera cookies ni
localStorage anteriores. Dashboard es el inicio único y `/` redirige allí;
la bienvenida y el enlace Inicio duplicado se retiran.

MepiaShell no muestra páginas ni carga datos antes de validar sesión; el HTML
inicial es solo un marco. APIs Next legadas verifican Bearer en servidor antes
del proxy; formularios/polling lo envían con authenticatedFetch. Chat mantiene
verificación Bearer/propiedad en FastAPI. Cookies antiguas no autorizan. Los
permisos por recurso de FastAPI legado siguen pendientes de producción.

Entrada/salida de auth usa navegación completa tras verificar/retirar sesión;
destino `next` limitado a rutas internas conocidas. Chat usa mensajes separados,
fuentes desplegables, compositor inferior, Enter para enviar/Shift+Enter para
línea nueva y botón Nueva conversación. Sugerencias solo preparan la pregunta;
no generan llamadas. Cambiar usuario/negocio/fecha descarta vista y peticiones.
Historial conserva contrato temporal anterior; no se promete lista persistente
de conversaciones. Formulario de documentos/configuración usa negocio común
autorizado, sin constante `NEXT_PUBLIC_BUSINESS_ID`.


- Input HTTP protegido: `business_id` UUID en path, pregunta y fecha opcional en body. El usuario procede exclusivamente de la sesión verificada.
- Fase 1: `ChatGroundingPacket` con S3, N14 enlazado, referencias y faltantes.
- Fase 2: `ChatToolResult` para resultados, catálogo o glosario, con cálculo
  deshabilitado de forma explícita.
- Fase 3: `ChatAnswer` con partes independientes (`kind`, `status`, `message`,
  `data`, `evidence`, `missing_data`, `claims`, `generation_status`,
  `generation_issues`, `generation_diagnostics`) y `calculation_allowed=false`.
- `message` puede contener redacción libre de la IA; `claims` conserva las
  afirmaciones verificadas y sus referencias. Los textos fijos son respaldo,
  salvo la bienvenida social acotada `kind=greeting`, sin hechos ni fuentes.
  Contrato y aceptación: [saludos](n15_chat_consulta_saludos.md).
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

- WHEN una persona pregunta por un concepto THEN explica su significado con palabras cotidianas y conserva las condiciones esenciales; la fórmula, insumos y alias se amplían cuando se piden.
- WHEN redacta cualquier parte THEN usa lenguaje comprensible sin conocimientos financieros, tono adulto respetuoso y frases breves; la longitud se adapta a lo solicitado.
- WHEN simplifica una explicación THEN conserva cifras/unidades, alertas y fuentes exactas; no inventa ejemplos numéricos, cálculos, causas ni recomendaciones.
- La guía de estilo orienta al modelo; la revisión factual y sus esquemas siguen intactos. La confirmación humana de una respuesta no es una prueba universal de legibilidad.

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
4. ✅ Evaluación offline y seguimiento aceptados el 12-oct-2026 bajo el
   criterio de reemplazo autorizado. Base: 28 casos/36 partes, 36/36
   independientes, 548/548 controles y cobertura 22/22. Validación
   dirigida: 12/12 independientes, 161/161 controles y cobertura 5/5;
   cero pendientes/fallos/contradicciones. Versiones de guía y tercera
   fallida preservadas; no se afirma tres repeticiones con la guía revisada.
5. ✅ Endpoint protegido, historial acotado e interfaz Chat IA integrados y
   probados localmente; datos/sesiones/proveedor simulados, sin despliegue.

**Continuación acordada:** Paso 5 integrado localmente y acceso real aprobado
en `MEPIA - PRUEBAS`: ES256/JWKS/RLS/permisos/historial, 29/29, proveedor
simulado. Gemini y la legibilidad de una definición real confirmados el 14-oct.
Sigue ejecutar las tandas del plan de pruebas del Paso 5 para ampliar métricas,
legibilidad e historial según las capas pendientes del ejecutor; la matriz
local ya se ejecutó y la primera tanda real quedó detenida por cuota (INC-041).
Producción continúa separada. Desarrollo posterior previsto: integrar OpenAI
GPT-6 Luna en N15. Su adaptador de evaluación ya existe y fue probado con
simulaciones; la calidad real de Luna todavía no está validada. Se usarán
los mismos casos y reglas, revisión independiente y comprobaciones de
integración, tiempo y costo antes de adoptar la nueva configuración.

## Discrepancias conocidas

- Chat IA, listado y configuración N10 tienen autenticación/permisos; otros endpoints
  legados del pipeline aún requieren protección antes de publicar toda la API.
- `MemoryService.get_context()` no aporta IDs de fuente y no se usa en N15.
- Las migraciones `008`, `009` y `010` no se han desplegado en producción.
- JWT admite HS256 o ES256 elegido explícitamente en servidor. Firma ES256
  vigente en el proyecto de pruebas, JWKS del origen configurado (caché 5 min,
  timeout 5 s), sin fallback ni origen del token. Sesiones/RLS reales aprobados 29/29.
- Historial efímero por proceso; múltiples réplicas requieren almacén compartido.
- Avisos residuales de dependencias (INC-023) siguen como gate de publicación.

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
el nivel gratuito recibe únicamente estos datos sintéticos.

Paso 4 offline y seguimiento completados bajo el criterio de reemplazo
autorizado: base de 28 casos/36 partes, 36/36 juicios independientes,
548/548 controles y cobertura 22/22; validación dirigida de siete casos/doce
partes, 12/12 independientes, 161/161 controles y cobertura 5/5. Cero
pendientes o fallos en el alcance aceptado. Los intentos fallidos y sus
versiones de guía permanecen como evidencia histórica.

### Historial de evaluaciones y seguimiento — 29-sep–12-oct-2026

Los estados pendientes, cantidades y siguientes acciones de los registros
fechados describen su ejecución histórica; el cierre vigente es el del
12-oct-2026. No se modifican informes, planes ni juicios anteriores.

Una muestra anterior
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

## Acceptance Criteria del Paso 5

- WHEN faltan credenciales, su firma/algoritmo/claims fallan o vencen THEN 401 y cero acceso a auditorías/modelo.
- WHEN el proyecto configura ES256 THEN verifica firma con JWKS exclusivamente del origen configurado; kid desconocido es 401 y descubrimiento no disponible/malformado es 503 cerrado. Nunca mezcla HS256/ES256 ni sigue jku/x5u del token.
- WHEN el negocio es ajeno, inexistente o no tiene dueño THEN 403 ambiguo antes de evidencia/modelo.
- WHEN falla la consulta de propiedad THEN 503 cerrado, sin excepción cruda.
- WHEN se intenta historial de otro usuario/negocio THEN 404 y cero evidencia/modelo.
- WHEN se revoca la propiedad THEN ninguna lectura, eliminación o continuación del historial se permite.
- WHEN el historial contiene cifras/instrucciones THEN no se convierte en fuente; las guardas actuales siguen rechazando cantidades libres.
- WHEN cambia la fecha THEN contexto previo de otra fecha no se envía a composición.
- WHEN el cliente envía user_id/history/provider u otros campos extra THEN 422.
- WHEN la misma conversación procesa otra petición THEN 409 antes de evidencia/modelo.
- WHEN vence la conversación o excede capacidad THEN 404/429 sin mezclar ni desalojar historial ajeno.
- WHEN el usuario cambia negocio/fecha/sesión THEN la interfaz limpia el contexto y descarta respuestas tardías.

Contrato, configuración, reproducción y límites: `docs/chatbot_step5_integration.md`.
INC-022/024/025 resueltas localmente; INC-023 mitigada, producción pendiente.

### Reconocimiento conceptual y evaluación por capas — 14-oct-2026

- WHEN se pregunta «qué son» sobre un concepto del catálogo THEN se explica el concepto, sin buscar un resultado del negocio.
- WHEN «Explícame el método» sigue en la misma pregunta a un concepto inequívoco THEN se hereda solo ese selector; sin un selector inequívoco no se inventa el ámbito. Solicitudes de cálculo siguen rechazadas antes de esta herencia. El caso probado es «¿Cómo se calcula el ticket promedio? Explícame el método.».
- WHEN un informe automático usa proveedor/Auth/datos simulados THEN lo declara y deja la comprensión y validación del proveedor real pendientes. La revisión humana exige dos lectores y respuestas ligadas por digest.
- WHEN Gemini limita la petición THEN se conserva respaldo seguro, se detiene la tanda y no se cuenta como generación positiva validada; INC-041 pendiente externo.
