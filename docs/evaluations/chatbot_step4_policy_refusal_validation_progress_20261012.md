# Estado actual: Paso 4 offline y seguimiento completados

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

## Evidencia de estados anteriores (histórico)

# Avance actual: cinco aprobadas, revisar cuatro pendientes

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

## Estado previo conservado (histórico)

# Avance actual: juez alternativo Gemini 3.6 preparado

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

## Estado previo conservado (histórico)

# Avance actual: tercer suplemento de fase 2 preparado

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

## Estado previo conservado (histórico)

# Avance actual: segundo suplemento de fase 2 preparado

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

## Estado previo conservado (histórico)

# Avance actual: recuperación de fase 2 autorizada

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


Verificación local del plan autorizado: sintaxis PowerShell/Python y MostrarPlan
correctos, repetición original de fase 2 bloqueada antes de clave/reserva;
presupuesto ligado al progreso, diez huellas/264 originales/298 protegidos intactos,
diff de espacios código 0, ningún intento reservado y cero API. Registro
`chatbot_step4_policy_refusal_phase2_judge_recovery_authorized_preflight_20261012.json`.

## Estado previo conservado (histórico)

# Avance de validación de negativas — fase 2 detenida

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

## Estados anteriores conservados

# Avance de validación de negativas — fase 2 lista

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

## Estados anteriores conservados

# Avance de validación de negativas — revisión suplementaria autorizada

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

## Fase 1 y auditoría anteriores (histórico)

# Avance de validacion de negativas — fase 1 detenida

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

No repetir el ejecutor original ni iniciar fase 2. Propuesta de una sola llamada
suplementaria del juez sobre las tres respuestas, sin nuevas generaciones,
conservando timeout y aceptando recuperacion si pasa; maximo total adicional
19 en lugar de 18. Propuesta no autorizada; ninguna nueva llamada habilitada.

Verificación local del plan autorizado: sintaxis PowerShell sin errores,
MostrarPlan código 0 y fase 2 bloqueada código 1 esperado antes de clave/reserva.
Diez huellas de código, 264 originales del plan y 274 de la auditoría intactos;
ningún intento real reservado y cero API. Registro
`chatbot_step4_policy_refusal_phase1_judge_recovery_authorized_preflight_20261012.json`.
Estas verificaciones no aportan juicios de calidad del chatbot.

Verificación local: sintaxis y MostrarPlan correctos, recuperación sin aprobación
y repetición de fase 2 bloqueadas antes de clave/reserva; ningún intento nuevo
reservado, 298 originales intactos y cero API. Registro
`chatbot_step4_policy_refusal_phase2_judge_recovery_proposal_preflight_20261012.json`.
