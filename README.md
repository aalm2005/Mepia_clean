# MEPIA

**Acceso e inicio — 15-oct-2026, validado localmente; sin commit:** sesión por pestaña (recargar conserva; cerrar/abrir pide login), Dashboard como inicio y bienvenida eliminada. API con Bearer y verificación de servidor; cookies antiguas no autentican. [Contrato, pruebas y límites](docs/mepia_access_navigation.md). INC-042 resuelta localmente: Edge 24/24, cero errores; build y tipos código 0. 42 incidencias: 39 resueltas, dos mitigadas y una pendiente externa. Los informes fechados anteriores no validan este cambio.

**GitHub verificado — 15-oct-2026:** avances y sincronización publicados en `codex/chatbot-q4`, commit `2c2ad07754204cf6216483de017dd898b2685255`. Push normal código 0 y hash remoto coincidente. Este registro se guarda en un commit documental posterior. [Estado y evidencia](docs/estado_actual_mepia.md). Los registros previos de «sin commit/push» conservan la situación de su fecha; producción sin cambios.

**Estado documental al 15-oct-2026:** consultar [flujo, avance y pendientes](docs/estado_actual_mepia.md). La sesión identifica y carga el negocio autorizado automáticamente; el selector con un solo negocio aún puede simplificarse. Tutorial guiado pendiente y adaptación móvil parcial. Los registros y conteos fechados siguientes conservan su alcance histórico; la publicación de código no equivale a despliegue.

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
Ver [ejecutor, resultados y revisión](docs/chatbot_step5_automation.md).

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
OpenAI y publicación separados. Ver [plan detallado](docs/chatbot_step5_test_plan.md).

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

Motor de evaluacion y chatbot de consulta fundamentada en resultados de MEPIA.

## MEPIA con acceso único y Chat IA integrado

Abre MEPIA: `/login` precede a toda la aplicación. Menú común con icono **Chat IA**;
el chat reutiliza sesión/negocio, sin formulario de acceso propio. Interfaz de
conversación con bienvenida, mensajes y campo inferior, responsive. Nuevo
recorrido sintético **15/15**, cero errores de página; build final código 0.
Frontend del equipo integrado el 14-oct-2026: diseño azul, fondo/bienvenida,
KPI y gráficas, Salud/Reportes junto a Chat IA. Presentación 12/12; valores y
unidades preservados, contexto de negocio comprobado antes de mostrar análisis.
Detalles en [registro de integración](docs/chatbot_frontend_merge.md).
Sesión Supabase por pestaña en sessionStorage, validada antes de mostrar la
interfaz; APIs con Bearer verificado en servidor; negocios propios,
preguntas S3/N14, fuentes, historial acotado y rechazo de cálculos. API Chat
protegida y permisos antes de
datos/modelo. General local: **292 aprobadas, 1 opt-in omitida y 119 subpruebas**;
API/auth/arranque anteriores 62/62; navegador original 8/8 simulado, sustituido
por el acceso común 13/13 y la versión combinada final 15/15. Next 15.5.27 y tipos/build final código 0.
Acceso real en **MEPIA - PRUEBAS: 29/29**, ES256/JWKS/RLS/permisos/historial,
proveedor simulado. Migración 010 aplicada dos veces, datos originales conservados
y fixtures limpiados. Sin commit, push ni despliegue. Configuración y reproducción
en [procedimiento del Paso 5](docs/chatbot_step5_integration.md). Recorrido de
interfaz/modelo reales pendiente. Cuenta propia confirmada vinculada al negocio
de pruebas; login y negocio confirmados por el usuario en Edge/Chrome desde
`http://127.0.0.1:3016/chat`, login registrado en Auth y listado 200. Mensaje de
conexión corregido: SDK con fetch simulado 3/3, tipos código 0. Causa exacta del
primer `Failed to fetch` no demostrada (INC-031 mitigada). Esa confirmación real
corresponde al flujo anterior. El 13-oct-2026 el usuario confirmó el nuevo
ingreso general con su cuenta propia y Chat IA desde el menú sin segundo login.
Confirmación del usuario del 13-oct, sin inspección independiente del navegador.
El 14-oct confirmó una respuesta conceptual real de Gemini y su claridad tras el
ajuste de lenguaje. La validación amplia sigue pendiente; véase el estado actual.
Arranque exclusivo `api.chat_app:create_app`
sin claves de agentes del pipeline; véase el procedimiento. Registro/invitaciones en MEPIA
serán trabajo posterior para las altas de clientes;
permisos legados y dependencias siguen como controles para publicar.

## Version de desarrollo actual

La rama `codex/chatbot-q4` contiene el grounding, las herramientas deterministas,
el nodo conversacional, los adaptadores Gemini/OpenAI y la evaluacion offline
del chatbot. El conjunto aceptado del Paso 4 cubre 28 casos, 36 partes y 22
partes respondibles: 548/548 controles y 36/36 revisiones independientes
favorables. Los informes anteriores, incluidos los fallidos, se conservan.

El seguimiento de consistencia esta completado bajo el criterio de reemplazo
autorizado: dos generaciones anteriores mas la nueva validada en ambas fases.
Las versiones de guia y la tercera fallida se conservan en la evidencia. El Paso 5
(autenticacion, autorizacion por negocio, endpoint, historial e interfaz del
chatbot) está implementado y validado en el alcance descrito arriba. Esta
publicacion no despliega produccion.

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
Secuencia histórica al cerrar el Paso 4: continuar con el Paso 5. Al 15-oct,
su implementación y acceso ya existen; faltan las capas de validación indicadas
en el resumen actual, no volver a implementar el acceso.
Chat de solo lectura conservado; producción sin cambios. Los estados anteriores
de pendiente/detenido describen las ejecuciones históricas previas a este cierre.

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

## Historial de evaluaciones y recuperaciones

Seguimiento del 10-oct: primera repeticion con generacion correcta; el juez
original y la llamada adicional autorizada devolvieron 503/UNAVAILABLE.
Serie detenida, tres juicios pendientes; cuatro generaciones y dos llamadas
del juez (seis API historicas). La llamada adicional ya se utilizo. Consultar el
[progreso actual](docs/evaluations/chatbot_step4_consistency_progress_20261010.md)
antes de ejecutar nuevas generaciones.

El 11-oct el usuario autorizo volver a intentar: tercer intento solo del juez
ejecutado, una llamada Flash y cero generaciones; tambien devolvio 503/UNAVAILABLE.
Tres revisiones pendientes, siete API historicas en total. Ambas llamadas
adicionales autorizadas ya se utilizaron; serie detenida. Estado en el progreso actual.

La revision suplementaria con `gemini-3.8-flash` ya se ejecuto: 3/3 juicios
independientes favorables, cero pendientes/fallos, ocho API historicas en total.
El codigo 1 de esta muestra se debe al criterio global de 36 partes.
Los tres 503 anteriores se conservan. La nueva serie autorizada con juez 3.8
se detuvo en su primera repeticion: generacion 45/45 y 2/2, juez 503 y tres
respuestas nuevas pendientes. Cinco de las 15 API autorizadas utilizadas;
diez sin usar, bloqueadas por la regla de detencion. Total del seguimiento 13 API.
Repeticiones 2/3 bloqueadas. Estado en el progreso actual.

El usuario autorizo seguir intentando: se preparo una unica revision
adicional con juez Gemini 3.8 de las tres respuestas guardadas `58b2769d`,
cero generaciones y maximo una llamada suplementaria sin reintentos. Aun no
ejecutada; historial 13 API, maximo 14 tras el intento. Presupuesto separado;
las diez API sin usar y repeticiones 2/3 permanecen bloqueadas. El 503 original
y criterio de tres ejecuciones sin errores se conservan; revisar el resultado
antes de continuar. Plan `chatbot_step4_consistency_judge38_run1_retry1_plan_20261011.json` y Markdown,
ejecutor `.test_tmp/revisar_consistencia_juez38_run1.ps1`. INC-016 pendiente externo, cero API en preparacion.

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

Continuacion aceptada: primera generacion aprobada para calidad (1/3),
503 original registrado como disponibilidad. Nuevo plan `chatbot_step4_consistency_judge38_recovery_authorized_plan_20261011.json`;
estado en `chatbot_step4_consistency_judge38_recovery_series_progress_20261011.json` y Markdown. Posicion 2 lista, 3 bloqueada
hasta auditoria; ejecutar solo las dos restantes con maximo diez API ya
presupuestadas, sin reintentos y detener ante nuevo fallo. Historial actual
14 API, maximo acumulado 24; cero llamadas nuevas en preparacion. Ejecutor
`.test_tmp/probar_consistencia_recuperada_juez38.ps1 -Repeticion 2..3`. Plan/runner originales y sus 0/3 ejecuciones
sin errores conservados; conjunto aceptado intacto e INC-016 mitigada.

Repeticion 2 aprobada (`052052_dabc0f75`): 45/45 controles, cobertura
2/2 y 3/3 juicios independientes favorables, cero fallos/pendientes/errores.
Avance bajo el ajuste aceptado 2/3 generaciones aprobadas para calidad;
tercera habilitada con la autorizacion existente, maximo cinco API restantes,
sin reintentos y detener ante nuevo fallo. Historial 19 API (12 gen/7 juez),
maximo acumulado 24. Auditoria `chatbot_step4_consistency_judge38_recovered_run2_audit_20261011.json` y Markdown, cero API nuevas.
503 inicial conservado; conjunto aceptado intacto e INC-016 mitigada. Estado
en `chatbot_step4_consistency_judge38_recovery_series_progress_20261011.json`; ejecutar solo
`.test_tmp/probar_consistencia_recuperada_juez38.ps1 -Repeticion 3` y auditar.

Tercera `052919_6ff8abfb` fallida: 44/45 controles, cobertura 2/2, revisor
interno veta una negativa a dividir identica a las aprobadas antes; respaldo
seguro, sin calculo. Juez externo 503, tres juicios pendientes. Serie detenida
2/3, diez de diez API usadas y ninguna adicional autorizada; historial 24 API
(16 gen/8 juez). INC-013 reabierta para este seguimiento e INC-016 pendiente
externo; conjunto historico aceptado preservado. Auditoria `chatbot_step4_consistency_judge38_recovered_run3_audit_20261011.json`
y Markdown; cero API en auditoria. Tratar revision interna antes de nuevas pruebas.

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

El estado detallado esta en [la bitacora](docs/chatbot_corrections.md),
[las incidencias](docs/chatbot_incidents.md) y
[el procedimiento de evaluacion](docs/chatbot_step4_eval.md).

## Pruebas locales

Desde la raiz del repositorio, en PowerShell, con Python 3.12 disponible:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r api/requirements-dev.txt
$env:RUN_SUPABASE_INTEGRATION='0'
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

La integracion Supabase requiere habilitacion explicita y se omite en esta
ejecucion. Las pruebas locales usan proveedores simulados; las evaluaciones
reales se ejecutan por separado.

## Evaluacion con Gemini

El ejecutor `scripts/medir_gemini.ps1` utiliza la carpeta del repositorio donde
esta guardado. Por defecto busca `.venv\Scripts\python.exe`; acepta
`-PythonPath` para utilizar otro entorno con las dependencias instaladas.

Comprobar el plan sin pedir clave ni realizar llamadas:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/medir_gemini.ps1 -DiagnosticoTanda4 -MostrarPlan
```

Comando del plan original (serie detenida; no ejecutar nuevas repeticiones):

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/medir_gemini.ps1 -DiagnosticoTanda4 -ModeloJuez gemini-3.5-flash
```

Cada repeticion permite como maximo cuatro llamadas de generacion y una del
juez, sin reintentos. Pide la clave oculta y la usa temporalmente en ese proceso;
los informes solo contienen datos sinteticos. Seguir los criterios y la regla de
detencion del [plan de consistencia](docs/evaluations/chatbot_step4_consistency_plan_20261009.md).
El codigo de revision de una muestra aislada debe interpretarse con sus
conteos: el criterio global exige 36 partes.

El ejecutor local historico de `.test_tmp` permanece en la computadora y su
SHA en el plan original se conserva. `scripts/medir_gemini.ps1` es una copia
adaptada para ejecutar desde otras ubicaciones; no cambia el generador, el
juez, los fixtures ni los presupuestos. Archivos temporales, entornos virtuales
y claves no forman parte de la publicacion.
