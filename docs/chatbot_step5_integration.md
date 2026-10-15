# Paso 5 — Integración local del chatbot

**Saludos — 15-oct-2026:** `kind=greeting` separa la bienvenida social de las
respuestas factuales, sin modelo ni fuentes para el saludo. Seguridad e historial
protegido conservados; consultas mixtas mantienen guardas. INC-043 resuelta
localmente: 112 pruebas/41 subpruebas, dos advertencias, código 0; Edge 25/25,
cero errores; helper 3/3 y tipos código 0. Sin commit/push; 43 incidencias:
40 resueltas, dos mitigadas y una pendiente externa. [Contrato y evidencia](chatbot_greetings.md).

**Acceso e inicio — 15-oct-2026, validado localmente; sin commit:** sesión por pestaña (recargar conserva; cerrar/abrir pide login), Dashboard como inicio y bienvenida eliminada. API con Bearer y verificación de servidor; cookies antiguas no autentican. [Contrato, pruebas y límites](mepia_access_navigation.md). INC-042 resuelta localmente: Edge 24/24, cero errores; build y tipos código 0. 42 incidencias: 39 resueltas, dos mitigadas y una pendiente externa. Los informes fechados anteriores no validan este cambio.

**Estado documental al 15-oct-2026:** consultar [flujo, avance y pendientes](estado_actual_mepia.md). La sesión identifica y carga el negocio autorizado automáticamente; el selector con un solo negocio aún puede simplificarse. Tutorial guiado pendiente y adaptación móvil parcial. Los registros y conteos fechados siguientes conservan su alcance histórico; la publicación de código no equivale a despliegue.

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
Ver [ejecutor, resultados y revisión](chatbot_step5_automation.md).

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
OpenAI y publicación separados. Ver [plan detallado](chatbot_step5_test_plan.md).

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

**Flujo vigente de interfaz:** un solo login en `/login`, previo a MEPIA.
Menú común con icono Chat IA; chat como sección de la misma aplicación, sesión
y negocio compartidos, sin login dedicado. Bienvenida, mensajes de usuario/
asistente y compositor inferior de apariencia similar a ChatGPT, con identidad
MEPIA. Acceso común inicial 13/13; frontend del equipo integrado el 14-oct:
E2E final 15/15 y presentación 12/12, cero errores, códigos 0; build final código 0.
Diseño azul/fondo/bienvenida y Salud/Reportes, conservando Chat IA y sesión común.
Ver `chatbot_frontend_merge.md`; INC-034/035/036/037 resueltas localmente.
El 13-oct-2026 el usuario confirmó el ingreso general con su cuenta propia
y la apertura de Chat IA desde el menú sin otro login. Confirmación del usuario,
sin inspección independiente del navegador ni validación de respuestas reales.
Evidencia: `evaluations/chatbot_step5_global_account_confirmation_20261013.json`.
Configuración/validación del modelo pendientes; cero modelos reales/producción
en esta confirmación.
Evidencia: `evaluations/chatbot_step5_shared_access_20261012.json` y cinco
informes por intento; 384 evidencias anteriores intactas. INC-032/033 resueltas.

Estado: integración local completada y probada; la evidencia de cierre vive en la bitácora y
`evaluations/chatbot_step5_local_validation_20261012.json`. Paso 4 aceptado y
su evidencia histórica conservados. No se ejecutaron APIs reales ni se accedió
a `MEPIA - PRUEBAS` o producción en ese cierre local original. Sin commit ni push.

Continuación real aprobada: proyecto reactivado y saludable; 010 aplicada dos
veces conservando un negocio y 19 auditorías. ES256/JWKS, sesiones/RLS/permisos
e historial reales: 29/29 controles aprobados, proveedor simulado. Limpieza
independiente confirma cero usuarios temporales; sin propietarios inferidos.

Cuenta propia posterior: el usuario creó personalmente su contraseña y cuenta
y autorizó vincularla al negocio existente de pruebas. Propietario asignado y
verificado, negocio/19 auditorías conservados. Un usuario propio persiste;
todos los temporales de la evaluación anterior fueron eliminados. Login y
negocio confirmados por el usuario en Edge/Chrome, Auth registra login reciente
y Next listado 200. Evidencia inicial de asignación sanitizada en
`evaluations/chatbot_step5_owner_assignment_20261012.json`; producción intacta.

Perfil local real de acceso preparado: `/chat` 200; API y proxy anónimos 401.
Focalizadas 62 aprobadas/2 advertencias en 6.02 s; general 292 aprobadas,
1 opt-in omitida, 119 subpruebas/2 advertencias en 52.36 s; códigos 0.
Formulario con Auth de pruebas; login de cuenta propia confirmado en navegador
normal. En ese registro del 12-oct, modelo sin clave y cero llamadas reales al modelo;
Evidencia sanitizada: `evaluations/chatbot_step5_account_login_20261012.json`;
382 evidencias anteriores cotejadas por SHA sin cambios, configuración privada
ignorada por Git, enlaces locales correctos y `git diff --check` código 0.

## Abrir Chat IA local con la cuenta propia

Configurar `.env.local` a partir de `.env.example`: URL y clave pública del
proyecto de pruebas; `AGENTS_API_URL=http://127.0.0.1:8016`. Configurar
`api/.env` a partir de su ejemplo: URL, clave de servidor privada y algoritmo
de firma real (`ES256` en MEPIA - PRUEBAS). Los archivos reales están ignorados
por Git. No poner la clave de servidor ni credenciales de modelo en frontend.

Desde la raíz del repositorio, iniciar en dos terminales:

```powershell
python -B -m uvicorn api.chat_app:create_app --factory --host 127.0.0.1 --port 8016 --log-level warning --no-access-log
node node_modules/next/dist/bin/next dev --hostname 127.0.0.1 --port 3016
```

Abrir `http://localhost:3016/`, escribir correo y contraseña en el login general
y pulsar «Iniciar sesión». Entrar a MEPIA y abrir **Chat IA** desde su menú.
Visitar `/chat` sin sesión también dirige al login general y conserva ese
destino. La contraseña la introduce el usuario. La cuenta ya existente se reutiliza;
al migrar las cookies anteriores al almacenamiento por pestaña hay que
iniciar sesión una vez en el nuevo flujo. El perfil
`api.chat_app` reutiliza los permisos existentes, valida configuración en
lifespan, no exige claves del pipeline y solo registra rutas de Chat IA/listado.
Los servidores actuales se conservan activos para el acceso local. Al cerrar
los procesos deberá iniciarlos otra vez; no hay despliegue ni exposición pública.

Usar Edge o Chrome para el acceso actual. El primer intento en navegador
integrado falló con `Failed to fetch`; abrir directamente health allí produce
`ERR_BLOCKED_BY_CLIENT`, sin demostrar la causa exacta del POST inicial.
No modificar protecciones. INC-031 mitigada por acceso operativo confirmado.
El login general distingue `AuthRetryableFetchError` con mensaje de conexión;
validación con SDK instalado/fetch simulado 3/3 y tipos código 0. La comprobación
sintética en navegador no reprodujo el fallo de red y no valida ese escenario.
Evidencia sanitizada del login confirmado, mensaje y límites:
`evaluations/chatbot_step5_login_connection_fix_20261012.json`; 383 evidencias
previas intactas, enlaces locales/privacidad revisados y `git diff --check` código 0.

Sin `CHAT_GEMINI_API_KEY`, entrar y listar el negocio están disponibles;
preguntar devuelve 503 por falta de configuración. El 14-oct el usuario guardó
la clave y se reinició Chat IA; confirmó respuesta conceptual con fuentes y POST 200. Las claves
OpenAI/Anthropic del pipeline no son necesarias para este perfil.

## Contrato de acceso y consulta

Supabase Auth inicia sesión en `/login` y guarda credenciales de sesión en
sessionStorage, aisladas por pestaña y por clave de eventos del SDK. Recargar
conserva el acceso; una pestaña nueva exige credenciales. Las cookies de la
versión anterior se retiran y no se usan para autenticar. La contraseña no se
guarda.

MepiaAuthProvider verifica getUser antes de mostrar la interfaz/cargar negocios.
El HTML inicial solo es el marco sin datos; el guard redirige al login. APIs del
pipeline requieren Bearer y verificación de servidor; los formularios y polling
lo añaden con authenticatedFetch. Chat conserva Bearer y permisos en FastAPI.
El login normal y `/` llevan a Dashboard; no hay bienvenida ni enlace Inicio
duplicado. Destinos internos explícitos seguros permanecen. Permisos por recurso
de FastAPI legado siguen pendientes antes de publicar.
FastAPI verifica el algoritmo configurado (HS256 con secreto privado o ES256 con
claves públicas JWKS del proyecto), expiración, `iat`, emisor del proyecto,
audiencia `authenticated`, rol `authenticated` y `sub` UUID. No acepta
usuarios anónimos de Supabase, claves anon/service_role como sesión, otro
algoritmo ni un JWT de otro proyecto. ES256 vigente (ECC P-256) confirmado en
`MEPIA - PRUEBAS`; HS256 sigue siendo el default para compatibilidad. Selección
explícita en servidor, sin fallback ni URL/algoritmo tomados del token. Caché
JWKS cinco minutos, sin caché permanente de claves, timeout cinco segundos.
Referencia de claims: [Supabase JWT](https://supabase.com/docs/guides/auth/jwts).

El servidor consulta `businesses` por `id` **y** `owner_id` antes de crear
evidencia, recuperar auditorías o invocar un modelo. Negocio ajeno, ausente
o sin dueño devuelve el mismo 403. Si falla la comprobación de permisos,
deniega con 503. Cada operación de historial vuelve a comprobar propiedad.

| Operación | Contrato |
|---|---|
| `GET /me/businesses` | Solo negocios del usuario, máximo 100 |
| `POST /business/{business_id}/chat` | Body cerrado: `question` (1–2000 caracteres), `requested_date` opcional, `conversation_id` opcional |
| Respuesta | `conversation_id` asignado por servidor y `answer: ChatAnswer` |
| `GET /business/{business_id}/chat/{conversation_id}` | Turnos de esa combinación de usuario, negocio y conversación |
| `DELETE /business/{business_id}/chat/{conversation_id}` | Elimina solo ese historial; 204 |

Credenciales ausentes/inválidas/vencidas: 401. Conversación ajena, desconocida
o expirada: 404 sin revelar su existencia. Petición simultánea en la misma
conversación: 409. Límite de conversaciones: 429. Campos extra, fecha o UUID
inválidos: 422. Fallos de datos/configuración: 503 con mensaje fijo, sin
excepciones crudas. Respuestas con datos usan `Cache-Control: no-store`.

## Evidencia, proveedor e historial

La ruta reutiliza `ChatGroundingService`, `ChatConversationNode`, las herramientas
y guardas existentes, y `GeminiCompletion` con un presupuesto nuevo de dos
intentos por petición: composición y revisión, sin reintentos. Credenciales y
modelo se configuran exclusivamente en servidor con `CHAT_GEMINI_API_KEY` y
`CHAT_MODEL`; no se reutilizan las claves del pipeline. Falta de configuración
produce 503. Fallos de generación/revisión conservan el respaldo determinista,
datos originales y códigos seguros del contrato existente. La interfaz muestra
la cifra/unidad y referencias; si no hubo explicación validada, lo indica y
permite leer los datos emitidos. Nunca calcula ni modifica auditorías.

Historial en memoria, por proceso: máximo 256 conversaciones, ocho turnos
por conversación, 60 000 caracteres serializados por turno y 30 minutos de
inactividad. No hay persistencia ni uso de `mepia_memory`; reiniciar el proceso
elimina el historial. Varias réplicas requerirían un almacén compartido o
afinidad antes de desplegar. Se deniega la capacidad excedida; no se expulsa
silenciosamente la conversación de otro usuario.

La composición recibe hasta cuatro turnos de la misma fecha, como datos no
confiables. Ninguna cantidad o fuente del historial puede justificar una
afirmación: solo cuentan las fuentes actuales recuperadas. Un seguimiento breve
como «¿Qué significa eso?» puede heredar únicamente un selector único del
catálogo de la pregunta previa; no hereda cifras. Cambiar usuario, negocio o
fecha limpia la vista y descarta respuestas tardías. El servidor impide usar
una conversación de otro ámbito aunque se conozca su UUID.

## Preparación reproducible y límites

Instalar `api/requirements-dev.txt` en un entorno Python compatible y ejecutar:

```powershell
python -B -m pytest tests/test_chat_api.py -q -p no:cacheprovider
python -B -m pytest tests -q -p no:cacheprovider
npm ci
npm run build
```

Para E2E se necesita Playwright y un navegador instalado. El runner crea
servidores sintéticos en **127.0.0.1:3015/8015**, con Auth simulado servido
por el fixture local (CORS solo de los alias locales de prueba),
bloquea servicios externos y usa S3/N14/SDK simulados. Guarda resultados en
`.test_tmp/step5_integrated` (o `MEPIA_STEP5_E2E_OUTPUT` por intento);
el build de prueba usa distDir privado y termina sus procesos al finalizar.
No usar el servidor
`tests.chat_step5_server` en despliegues. Ejemplo con Playwright instalado:

```powershell
$env:MEPIA_TEST_PYTHON = (Resolve-Path '.venv/Scripts/python.exe').Path
$env:MEPIA_TEST_BROWSER = 'msedge' # opcional; navegador instalado
$env:MEPIA_STEP5_E2E_OUTPUT = '.test_tmp/step5_integrated/mi-intento'
node tests/chat_step5_e2e.cjs
```

Se puede indicar `MEPIA_PLAYWRIGHT_MODULE` para un runtime externo de Playwright.
Recorrido común inicial: 13/13 (intento 7 del 12-oct). Versión combinada vigente:
15/15, cero errores de página, código 0 (intento 6 de frontend_merge del 14-oct).
Los seis intentos de integración se preservan separados; presentación 12/12 y
build/tipos finales código 0. En el aislamiento de este runtime asyncio se
atasca creando socketpair (INC-035); el mismo ejecutor local fuera de él pasó.
Esto no cambia la configuración de autenticación o permisos del producto.
Los informes 1/4/5/6 fallidos y logs incompletos 2/3 se conservan; no se sobrescriben.
No contiene credenciales reales. Las pruebas simuladas no validan la firma de
sesiones de una cuenta real, disponibilidad/calidad del proveedor, aplicación
SQL real ni disponibilidad en producción.

La migración 010 agrega propiedad nullable y políticas por dueño, retirando la
lectura anónima antigua; `APPLY_ALL.sql` incluye el mismo bloque. No infiere
propietarios. Aplicada dos veces en el proyecto de pruebas, sin asignar dueños
al negocio histórico en esa evaluación. Después se asignó por confirmación
expresa del usuario a su cuenta propia; aplicación en producción requiere
autorización separada. El resto de endpoints
legados del pipeline sigue requiriendo incorporación de autenticación/permisos
antes de exponer el backend completo. Esta integración protege los endpoints
de Chat IA y listado de negocios, y no declara autenticada toda la API.

INC-20261012-023 registra los avisos de dependencias: Next.js se actualizó a
la línea 15 para corregir los avisos reales encontrados, con compatibilidad
de parámetros asincrónicos en cinco handlers. Los avisos residuales quedan
como gate de publicación separado; no se afirma una auditoría de seguridad
integral. Proveedor OpenAI GPT-6 Luna sigue como trabajo posterior, sin
validación real atribuida a Luna ni cambios a los proveedores del motor.

Validación opt-in de acceso real: `python -m tests.chat_step5_access_real --config
<archivo privado> --output <informe>`, con RUN_CHAT_ACCESS_INTEGRATION=1,
ENVIRONMENT=dev y MEPIA_TEST_PROJECT_REF exacto. El archivo privado contiene
SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_PUBLIC_KEY y
SUPABASE_JWT_ALGORITHM=ES256. No incluirlo en Git. Crea dos usuarios y negocios/
auditorías sintéticos, prueba Auth/JWKS/RLS/router/historial y elimina solamente
sus UUID. Proveedor simulado y cero llamadas reales al modelo; no equivale a
validación del modelo ni del navegador con Auth real. Resultado final: 29/29,
código 0, en `evaluations/chatbot_step5_access_real_attempt3_20261012.json`.
Los intentos fallidos 1/2 permanecen como evidencia; sus fixtures se limpiaron.
El reloj del servidor debe estar sincronizado: iat/exp se verifican sin añadir
tolerancia para un desfase del entorno. INC-026 a 030 resueltas y 022 actualizada.

### Redacción para usuarios sin formación financiera

El compositor compartido usa lenguaje cotidiano y una respuesta breve por
defecto. En conceptos explica el significado; fórmulas, insumos y alias se
incluyen cuando la pregunta los requiere. El detalle se adapta sin alterar
datos, unidades, alertas o fuentes. No hay una plantilla literal obligatoria
ni una tercera llamada de estilo: se conserva composición y revisión factual.
Después de reiniciar el backend local, abrir una conversación nueva para
comprobar la guía vigente; el historial sigue siendo temporal en memoria.
