# MEPIA — Estrategia de autenticación y autorización

**Acceso e inicio — 15-oct-2026, validado localmente; sin commit:** sesión por pestaña (recargar conserva; cerrar/abrir pide login), Dashboard como inicio y bienvenida eliminada. API con Bearer y verificación de servidor; cookies antiguas no autentican. [Contrato, pruebas y límites](../../../docs/mepia_access_navigation.md). INC-042 resuelta localmente: Edge 24/24, cero errores; build y tipos código 0. 42 incidencias: 39 resueltas, dos mitigadas y una pendiente externa. Los informes fechados anteriores no validan este cambio.

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

Estado al 14-oct-2026: login general previo a MEPIA y menú común implementados,
frontend combinado validado 15/15 E2E, 12/12 presentación y build final código 0. Chat IA/listado conservan permisos
por negocio. Proxies Next legados exigen sesión; autorización por recurso y
la incorporación al resto de endpoints FastAPI legados siguen pendientes
como gate antes de publicar el backend completo. No se declara autenticada toda
la API. Sin despliegue. Acceso real en `MEPIA - PRUEBAS` aprobado: 29/29.

## Estrategia implementada

Supabase Auth genera una sesión guardada solo en sessionStorage de la pestaña.
Recargar conserva acceso; abrir otra exige login. Una clave por pestaña aísla
los eventos del SDK. No se recuperan cookies/localStorage anteriores.

AuthProvider verifica al usuario remoto antes de mostrar MEPIA/cargar negocios.
El HTML inicial es un marco sin datos; el guard del cliente redirige páginas
sin sesión. El middleware valida Bearer con getUser para APIs legadas; Chat
conserva verificación y permisos en FastAPI. Cookies antiguas se eliminan y
no autorizan peticiones. Cache-Control private/no-store; secretos solo servidor.
Dashboard es inicio único y `/` redirige allí; destinos internos seguros se
conservan tras login. La bienvenida independiente y el enlace Inicio se retiran.

`AuthService`
en `api/core/auth.py` verifica el algoritmo explícito SUPABASE_JWT_ALGORITHM:
HS256 con SUPABASE_JWT_SECRET privado, o ES256 con claves públicas JWKS del proyecto configurado. Comprueba
firma, exp/iat, emisor SUPABASE_URL/auth/v1, audiencia authenticated, rol
authenticated y sub UUID. Rechaza usuarios anónimos, service_role/anon como
sesión, claims ausentes y algoritmos diferentes. `MEPIA - PRUEBAS` usa ES256
vigente (ECC P-256), observado en JWT Keys. No hay fallback entre algoritmos ni
se seleccionan algoritmo/origen desde el JWT. JWKS: caché del conjunto cinco
minutos, sin caché permanente de claves; timeout cinco segundos. Desconocimiento
de kid/firma inválida: 401; fallo de conexión/conjunto inválido: 503 cerrado.

El startup exige origen HTTPS y algoritmo permitido; HS256 exige secreto de al menos 32 bytes. Una ruta sin
configuración de auth deniega con 503. Credenciales inválidas/ausentes/vencidas
devuelven 401 con WWW-Authenticate, mensajes fijos y sin excepción privada.
Referencias: [Supabase JWT](https://supabase.com/docs/guides/auth/jwts),
[PyJWT](https://pyjwt.readthedocs.io/en/stable/usage.html).

## Permisos por negocio

El backend usa service_role (bypass RLS). La dependencia del router verifica
`db.table("businesses").select("id,owner_id").eq("id", bid).eq("owner_id", uid)`
mediante el cliente PostgREST real, antes de recuperar auditorías, crear el
paquete, consultar historial o invocar el modelo. También comprueba que la fila
devuelta corresponde a usuario/negocio. Ausencia, dueño NULL y negocio ajeno
devuelven el mismo 403; error de consulta devuelve 503 sin revelar datos.

La migración 010 agrega owner_id **nullable** con FK auth.users/ON DELETE SET
NULL e índice. Se preservan históricos sin inferir dueño; NULL deniega acceso.
Retira políticas anónimas e instala SELECT autenticado por propietario en
businesses y audit_results. APPLY_ALL incluye el mismo contrato final. Se
aplicó 010 dos veces en `MEPIA - PRUEBAS` con autorización: UUID nullable, FK
ON DELETE SET NULL, índice y políticas verificados; un negocio y 19 auditorías
conservados, cero propietarios inferidos. Producción no modificada.

Cuenta propia posterior: usuario creado con contraseña definida personalmente,
propiedad del único negocio de pruebas asignada por confirmación explícita y
verificada por DB/`verify_business_access`, código 0. Auditorías/UUID conservados;
correo y UUID privados excluidos de documentos. Login/negocio de esta cuenta
confirmados por el usuario en navegador normal, Auth registra login reciente y
Next listado 200; cero modelos reales y producción. El esquema admite varias cuentas
y negocios aislados; registro/invitación en la interfaz requiere trabajo posterior.

El frontend combinado del 14-oct agrega Salud/Reportes bajo el mismo middleware;
el hook oculta resultados que no coinciden con usuario/negocio/corrida actuales
y cancela peticiones al cambiar contexto. E2E 15/15 incluye respuesta ajena
sintética y limpieza de análisis. Este control de presentación no autoriza
endpoints FastAPI legados; la verificación de recursos en servidor sigue pendiente.

## Alcance actual

| Endpoint | Control implementado |
|---|---|
| Páginas MEPIA | Marco inicial sin datos; proveedor verifica usuario remoto y guard exige sesión de la pestaña |
| Proxies Next legados | Bearer obligatorio validado con getUser antes del proxy; cookies no bastan; permisos por recurso aún pendientes en FastAPI legado |
| GET /me/businesses | Sesión; solo negocios propios |
| POST /business/{business_id}/chat | Sesión, propiedad y ámbito de conversación antes de evidencia/modelo |
| GET/DELETE /business/{business_id}/chat/{conversation_id} | Sesión, propiedad revalidada y combinación usuario/negocio/conversación |
| Endpoints legados de ingesta/auditoría/memoria | Incorporación pendiente antes de exposición del backend completo |

E2E original del acceso común 13/13 (12-oct): entrada directa/forja de cookie, login, menú sin segundo login,
recarga, conversación/fuentes, historial, cambio de usuario/negocio, 403 ajeno,
rechazo de cálculo, móvil y logout. Sesiones/datos/proveedor sintéticos; cero
servicios externos. El 13-oct-2026 el usuario confirmó el nuevo ingreso general
con su cuenta propia y la apertura de Chat IA desde el menú sin otro login.
Confirmación del usuario, sin inspección independiente del navegador ni prueba
de respuestas reales. No certificar toda la API por proteger las páginas.
Modelo real y producción separados; INC-032/033 resueltas localmente.

Historial efímero y acotado, independiente de RAG. Las claves y elección del
modelo permanecen en servidor. No se autorizan cálculo ni escrituras a métricas
o auditorías desde el chat. Producción sigue pendiente: migraciones 008/009/010,
propietarios/sesiones reales, controles de endpoints legados, dependencias y
historial compartido para múltiples réplicas. Ver
`docs/chatbot_step5_integration.md`, configuración en `api/.env.example` y
`api/core/config.py`, schema y spec N15. Para acceso local exclusivo usar
`api.chat_app:create_app --factory` y `api/core/chat_config.py`: exige Supabase,
valida auth y clave de servidor al iniciar; no registra rutas legadas ni exige
claves de agentes. Falta de clave del modelo conserva 503 para preguntas.

## Cierre local original y validaciones posteriores

38 pruebas API; general 268 aprobadas, 1 opt-in omitida y 119 subpruebas;
navegador 8/8, build Next 15.5.27/tipos código 0. Prueba anónimos, firmas,
claims, expiración, negocios ajenos/sin dueño, revocación, aislamiento/expiración/
capacidad/concurrencia de historial, instrucciones/cifras no confiables, errores
sanitizados, startup sin secreto y recorrido con fuentes. Proveedores, sesiones
y filas simulados, cero servicios externos. No garantiza seguridad universal
ni sustituye validación de sesiones/RLS reales.

Adaptación ES256: 58 pruebas focalizadas aprobadas en 5.23 s; general 288
aprobadas, 1 omitida, 119 subpruebas y 2 advertencias en 47.18 s. Primera
focalizada 57 aprobadas/1 fallida por faltar el nuevo campo en la configuración
sintética del test de startup; corregido. Integración real 29/29: Auth, JWKS,
RLS, propiedad, historial y revocación; proveedor simulado. Dos usuarios,
cuatro negocios/seis auditorías temporales eliminados, consulta SQL posterior
confirma un negocio/19 auditorías/cero usuarios. No valida el modelo ni navegador
con Auth real. Reloj sincronizado por el usuario, sin leeway adicional.

Perfil exclusivo de acceso local: focalizadas 62 aprobadas/2 advertencias en
6.02 s; general 292 aprobadas/1 omitida/119 subpruebas/2 advertencias en
52.36 s, códigos 0. `/chat` 200, API/listado y proxy anónimos 401. Formulario
con Auth real listo en `127.0.0.1:3016/chat`; login propio confirmado en Edge/Chrome.
Mensaje de transporte `AuthRetryableFetchError` corregido; SDK con fetch simulado
3/3 y tipos código 0, sin secretos/errores privados en UI. INC-031 mitigada:
causa exacta de fallo inicial no demostrada; bloqueo de navegación directa en
navegador integrado no implica todos los POST. Ninguna protección modificada.
Servidores locales, cero modelos reales, sin producción.
