# Acceso por pestaña e inicio único de MEPIA

**Publicación verificada — 15-oct-2026:** acceso por pestaña, Dashboard como
inicio y saludos del chat publicados en `codex/chatbot-q4`, commit
`49a5d05184a6e3f50c4353cafd84092df1e9b285`. Push normal código 0 y hash remoto
coincidente. INC-042/043 resueltas localmente y publicadas; INC-041 sigue pendiente
externa. [Evidencia de publicación](evaluations/github_access_greetings_verified_20261015.json).
Este registro se guarda en un commit documental posterior. Las menciones previas
«sin commit/push» describen su validación original. Producción sin cambios.


**Decisión del usuario: 15-oct-2026. Rama: `codex/chatbot-q4`. Sin commit.**
Reemplaza la persistencia en cookies y la bienvenida de la integración del 14-oct.
La evaluación anterior conserva su alcance histórico; no prueba esta versión.

## Comportamiento solicitado

- El usuario inicia sesión al abrir una pestaña nueva de MEPIA.
- Recargar la misma pestaña conserva el acceso.
- Cerrar la pestaña y abrir otra requiere credenciales de nuevo.
- Dashboard es el inicio: `/` lleva a `/dashboard` y el login sin destino usa Dashboard.
- Se quitan la bienvenida independiente y el enlace Inicio duplicado. El logo lleva a Dashboard.
- Los destinos internos explícitos, como Chat IA, se conservan tras autenticar.

## Implementación y límites

`getSupabaseBrowser` usa el SDK de Supabase con `sessionStorage`, sin recuperar
sesiones de cookies/localStorage. Una clave por pestaña también aísla el canal
de eventos del SDK. No se guardan contraseñas ni se usa un cierre remoto por
`beforeunload`: eso confundiría una recarga con un cierre y afectaría otras pestañas.
La pérdida del almacenamiento local no se presenta como revocación instantánea
de todos los tokens del servidor. Restaurar pestañas mediante funciones propias
del navegador queda fuera de la comprobación ordinaria cerrar/abrir realizada aquí.

`MepiaAuthProvider` verifica el usuario con Supabase antes de mostrar el marco
privado o cargar negocios; descarta respuestas de validaciones anteriores.
La respuesta HTML inicial contiene el marco sin información del negocio. La
redirección de páginas al login es del cliente: ya no se atribuye un 307 de
autenticación al middleware para cada página.

Las APIs mantienen autorización en servidor. Chat verifica Bearer, firma y
propiedad en FastAPI. Los proxies Next del pipeline exigen Bearer y `getUser`
antes de procesar la petición; `authenticatedFetch` lo añade a los formularios y
consultas de resultados. Las cookies antiguas se eliminan y no conceden acceso.
La autorización por recurso de FastAPI legado sigue pendiente para producción.

No cambian el motor, las fuentes S3/N14, la selección automática del negocio,
el historial temporal, los modelos ni los límites del proveedor. Tutorial y
adaptación móvil completa siguen pendientes.

## Validación

INC-20261015-042 resuelta localmente: **24/24 controles de Edge, cero errores
de página**, código 0; helper de limpieza **3/3**, código 0; build de Next y
validación de tipos **código 0**, 84218 ms. La configuración generada se restauró
exactamente. Los seis intentos anteriores conservan sus fallos: expectativa de
URL, redirección de raíz, contexto del ejecutor, cambio de origen y conteo de KPI
como mensajes. Diagnóstico del origen reproducido antes de corregirlo mediante
redirección relativa de Next. No se cambian criterios para ocultar un fallo.

La prueba incluye sesiones/cookies manipuladas, sesión persistida antigua que
no basta, recarga, pestañas con cuentas distintas, logout, cerrar/abrir de nuevo,
Chat IA, contexto, fuentes, historial, teclado y menú móvil. No certifica todos
los dispositivos, proveedor real ni restauración de pestañas del navegador.
Ver [informe de esta versión](evaluations/mepia_access_navigation_20261015.json).

Los escenarios usan Edge sin ventana visible, cuentas/DB/modelo sintéticos,
puertos 3015/8015 y caché privada. No leen claves del proveedor ni acceden a
Supabase real, y no reinician los servicios del usuario en 3016/8016.
El resultado final y las limitaciones se registran en la
[bitácora](chatbot_corrections.md) y el [estado actual](estado_actual_mepia.md).
