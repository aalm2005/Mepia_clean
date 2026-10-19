# MEPIA — Flujo y estado actual

**Quincena 5 — preparación del 19-oct-2026:** versión reunida en
`codex/quincena-5`, desde `f9cfddc84721a9ea32f8e56ba804f0ed8dc77f09`.
Incluye configuración automática, conexión unificada, controles de persistencia,
correcciones del Dashboard y documentos de demostración; INC-044–053 conservan
su estado registrado. INC-054 resuelta: los cuatro artefactos conservan sus
bytes al clonar en Windows; 8/8 comparaciones y cuatro lecturas aprobadas.
Estado actual: 54 incidencias, 51 resueltas, dos mitigadas y una pendiente externa.
Regresión actual: **226 pruebas y 41 subpruebas**, dos
advertencias, 36.57 s, código 0. Fechas 11/11, presentación 16/16 y tipos código 0.
Los 23 controles Edge del 15-oct se conservan como evidencia previa, sin repetirlos.
Revisión de credenciales y documentos aprobada; cambios aún sin commit ni push
en este registro preparatorio. El ensayo real del 14-oct, revisión humana N15,
tutorial guiado, adaptación móvil completa y controles de producción siguen
pendientes. Esta publicación de código no aplica cambios en Supabase ni despliega.
[Publicación y evidencia](quincena5_publicacion_20261019.md).

**Correcciones del ensayo — 15-oct-2026:** INC-051/052/053 resueltas
localmente. Fecha inferida desde ventas o selección compatible; selección del
análisis conservada en el menú para la misma sesión/negocio; N05 guarda el
resultado completo. Históricos recuperados solo por su S3 explícito compatible,
con estado S2 desconocido cuando no se conservó. Regresión: **226 pruebas y
41 subpruebas**, dos advertencias, 58.42 s, código 0. Edge: **23/23 controles**,
cero errores; fechas 11/11 y presentación 16/16; tipos código 0.
Lectura principal por API local: HTTP 200, cuatro métricas recuperadas de la
corrida de enero; cero escrituras externas y cero llamadas del agente a modelos.
Servidor local actualizado. **53 incidencias: 50 resueltas, dos mitigadas,
una pendiente externa y cero abiertas.** Ensayo real del 14-oct y revisión humana
del Paso 5 siguen pendientes. Rama `codex/chatbot-q4`, HEAD `f9cfddc84721a9ea32f8e56ba804f0ed8dc77f09`;
sin commit/push ni despliegue. Sigue ejecutar una vez el ensayo con fecha 14-oct.
[Archivos, evidencia y límites](dashboard_demo_fix_20261015.md).

**Diagnóstico inicial anterior a la corrección — 15-oct-2026:** los documentos se registraron para
14-oct-2026, pero las capturas corresponden a una corrida del 15-ene-2024.
INC-051 abierta: fecha antigua prellenada prevalece sobre la de los archivos.
INC-052 abierta: volver al Dashboard desde el menú pierde la selección visual
del análisis, conservado en la base. INC-053 abierta: N05 guarda insights pero
omite resultados completos/listas; GET local devuelve cuatro insights y listas
vacías. Lectura principal y HTTP 200 verificados, cero escrituras externas y
cero llamadas del agente a modelos. Sin cambios de producto ni repetición de
suites/build/E2E. **53 incidencias: 47 resueltas, dos mitigadas, una pendiente
externa y tres abiertas.** El ensayo del 14-oct sigue sin aprobar.
Rama `codex/chatbot-q4`, HEAD `f9cfddc84721a9ea32f8e56ba804f0ed8dc77f09`;
documentación sin commit/push. Sigue corregir 051/052/053 y verificar el ensayo
con fecha correcta. [Diagnóstico y límites](dashboard_demo_diagnosis_20261015.md).

**Preparación del video anterior a este diagnóstico — 15-oct-2026:** INC-048/049/050 resueltas localmente:
N14 entrega respuesta solo tras guardar; el seguimiento avanzado resuelve el ID
de Layer 2 al ID real de Layer 3 y muestra el fallo de persistencia. Registro de
errores limitado a 128/30 minutos en un proceso; no sustituye estados durables.
Dashboard acepta decimales textuales del motor sin ocultar cero: 16/16
controles de presentación y TypeScript código 0.
Regresión: **208 aprobadas y 41 subpruebas**, dos advertencias, 9.93 s, código 0;
dos controles HTTP aislados aprobados, 8 deseleccionados, dos advertencias,
4.21 s. PDF/XML ficticios del 14-oct preparados, renderizados y leídos por los
parsers reales; motor S3 y grounding con DB simulada: conciliación **0.00 MXN**.
OpenAI configurado en privado, Claude vacío con respaldo OpenAI comprobado por
simulación; Gemini configurado. Cero llamadas del agente a modelos en esta tarea.
Con autorización expresa se añadió un conteo ficticio de caja, verificado una
sola vez por lectura; sin sobrescribir registros. Ensayo real de IA pendiente.
**50 incidencias: 47 resueltas, dos mitigadas (023/031), una pendiente externa
(041), cero abiertas.** Preparación local no equivale a ensayo real aprobado.
Rama `codex/chatbot-q4`, HEAD `f9cfddc84721a9ea32f8e56ba804f0ed8dc77f09`;
sin commit/push ni despliegue. [Pasos para el ensayo](demo_video_paso_a_paso.md)
y [evidencia](evaluations/demo_preparation_20261015.json).

**Unificación operativa anterior a esta preparación — 15-oct-2026:** interfaz y servidor completo usan
MEPIA principal con claves modernas; cuenta y propietario verificados.
009/010 y 011 aplicadas con autorización: 18 tablas/175 columnas, 658 referencias
estáticas sin faltantes. Se conservan las 58 auditorías, 21 documentos y demás
conteos previos; huellas anteriores de auditorías/negocio coinciden.
Regresión: 178 pruebas y 41 subpruebas aprobadas, dos advertencias, 12.67 s,
código 0. SQL real: 9/9 contratos y 4/4 controles de aislamiento aprobados;
escrituras del ensayo revertidas. Usuario confirmó login, negocio, Documentos
y Chat IA, también después del retiro de claves antiguas.
INC-046 resuelta en su alcance de esquema/conexión. INC-047 resuelta tras
desactivar API keys heredadas y revocar la firma anterior HS256: ambos usos
del token antiguo reciben 401; ECC/ES256 y claves modernas siguen funcionando.
**48 incidencias: 44 resueltas, dos mitigadas (023/031), una pendiente externa
(041) y una abierta (048).** INC-048 y el ensayo de análisis nuevo siguen
pendientes; OpenAI/Anthropic vacías. El chat recuperó cuatro métricas existentes,
sin N14 enlazado y sin llamadas a modelos. No se infiere linaje histórico.
Rama `codex/chatbot-q4`, HEAD `f9cfddc84721a9ea32f8e56ba804f0ed8dc77f09`;
cambios **sin commit/push**. Principal sí recibió los cambios autorizados;
no se publicó una web. PRUEBAS se conserva, sin copiar sus fixtures.
[Evidencia, archivos y límites](database_unification.md).

Los registros fechados siguientes conservan su alcance histórico. Los Pasos
1–4 aceptados y la evaluación funcional/humana pendiente del Paso 5 se conservan.

[Archivos actualizados, rutas y comprobaciones de este corte](actualizacion_documental_20261015.md).

**Configuración automática integrada — 15-oct-2026:** INC-044/045 resueltas
localmente: tolerancias conservadas al guardar y GET/POST/PUT con sesión y
propiedad verificadas. Documentos abre sin formulario obligatorio, aplica
valores iniciales si faltan y conserva ajustes previos, sin inventar gastos.
Regresión: 151 pruebas/41 subpruebas, dos advertencias, 9.54 s, código 0;
Edge N10 14/14 y general 25/25, cero errores; helper 3/3 y build/tipos código 0.
MEPIA - PRUEBAS: tres consultas de esquema `limit 0`, cero filas/escrituras;
cero llamadas nuevas del agente a modelos. Usuario confirma que Documentos y
ajustes avanzados abren sin error. Rama `codex/chatbot-q4`, HEAD `f9cfddc`,
sin commit/push; producción sin cambios. 45 incidencias: 42 resueltas, dos
mitigadas, una pendiente externa (041), cero abiertas.
[Archivos, evidencia y límites](onboarding_defaults_integration.md).
El usuario grabará desde otra computadora con archivos nuevos: falta configurar
las claves del motor (OpenAI/Anthropic vacías aquí) y ensayar el servidor completo.
[Guía de instalación y ensayo](mepia_setup_video.md). Pasos 1–4 aceptados y
pendientes funcionales/humanos del Paso 5 conservados.

**Publicación verificada — 15-oct-2026:** acceso por pestaña, Dashboard como
inicio y saludos del chat publicados en `codex/chatbot-q4`, commit
`49a5d05184a6e3f50c4353cafd84092df1e9b285`. Push normal código 0 y hash remoto
coincidente. INC-042/043 resueltas localmente y publicadas; INC-041 sigue pendiente
externa. [Evidencia de publicación](evaluations/github_access_greetings_verified_20261015.json).
Este registro se guarda en un commit documental posterior. Las menciones previas
«sin commit/push» describen su validación original. Producción sin cambios.


**Saludos — 15-oct-2026:** bienvenida breve sin generación ni fuentes vacías,
INC-043 resuelta localmente. 112 pruebas/41 subpruebas, dos advertencias, código 0;
Edge 25/25 y cero errores; helper 3/3 y tipos código 0. 43 incidencias:
40 resueltas, dos mitigadas y una pendiente externa (041). Sin commit/push;
los registros de acceso y conteos siguientes describen su ejecución anterior.
[Contrato e informe](chatbot_greetings.md).

**Acceso e inicio — 15-oct-2026, validado localmente; sin commit:** sesión por pestaña (recargar conserva; cerrar/abrir pide login), Dashboard como inicio y bienvenida eliminada. API con Bearer y verificación de servidor; cookies antiguas no autentican. [Contrato, pruebas y límites](mepia_access_navigation.md). INC-042 resuelta localmente: Edge 24/24, cero errores; build y tipos código 0. 42 incidencias: 39 resueltas, dos mitigadas y una pendiente externa. Los informes fechados anteriores no validan este cambio.

**Actualización documental: 15-oct-2026. Rama: `codex/chatbot-q4`.**
Este resumen distingue implementación, evidencia de pruebas y trabajo pendiente.
La [bitácora del chatbot](chatbot_corrections.md) conserva la fuente de verdad
de su avance; los registros fechados y las evaluaciones son evidencia histórica.
Publicar código en GitHub no despliega MEPIA ni cierra sus pendientes de producción.

## Recorrido del usuario

1. **Iniciar sesión.** `/login` precede a las páginas privadas de MEPIA. La
   sesión vive en la pestaña: recargar conserva el acceso; cerrar y abrir una
   nueva exige login. El proveedor verifica al usuario antes de mostrar MEPIA y
   el servidor consulta únicamente los negocios
   asociados a su `owner_id`. El chat verifica además la propiedad antes de
   consultar datos o invocar el modelo.
2. **Identificar el negocio automáticamente.** La interfaz carga un negocio
   autorizado sin exigir una selección manual cuando solo hay uno. El selector
   todavía es visible; mostrar únicamente el nombre en ese caso es una mejora
   pendiente acordada. No se ha implementado una relación obligatoria de un
   único negocio por cuenta. No se muestran negocios de otros propietarios en
   la lista autorizada.
3. **Entrar a Documentos con ajustes iniciales automáticos.** La carga se
   muestra sin completar antes el formulario. Si faltan ajustes, se guardan
   valores iniciales sin inventar gastos; los existentes se conservan.
   «Personalizar configuración avanzada» permite editar identidad, umbrales,
   costos y reglas, cargando sus valores anteriores. Guardar lleva a Documentos.
   GET/POST/PUT verifican sesión y propiedad. No es el tutorial de uso.
   Los campos avanzados de catálogo/comisiones/salarios deben distinguirse del
   formulario general ya implementado: no se declaran todos capturados en la UI.
4. **Cargar información e iniciar el análisis.** La interfaz admite POS en PDF y
   facturas en PDF/XML, fecha y enfoque del análisis. También existe ingesta API
   en el backend; cada conexión con un POS externo requiere su integración.
   Pulsar Analizar inicia el flujo; configurar una frecuencia no demuestra un
   programador de auditorías automáticas.
5. **Extraer, revisar y calcular.** El sistema identifica campos, permite
   revisión humana del documento y valida los requisitos de cada métrica.
   Las métricas sin datos suficientes permanecen pendientes/incompletas. S3
   calcula con reglas programadas; la IA interpreta esos resultados.
6. **Interpretar y profundizar si corresponde.** S4 realiza diagnóstico y N05
   sintetiza hallazgos según el enfoque. Con riesgo alto y escalación habilitada,
   N06 ejecuta el análisis adicional; N09 está implementado, N07/N08 se omiten
   deliberadamente en v1. Layer 3 construye contexto, consulta, revisa y produce
   N14; N12 se omite en v1. La revisión puede terminar con advertencias.
7. **Consultar resultados.** Dashboard y Salud incluyen indicadores/gráficas;
   Reportes reutiliza la vista de hallazgos sin el bloque de métricas. Las vistas
   actuales consumen una corrida por `run_id`; no se ha demostrado recuperación
   automática del último análisis al entrar desde cualquier enlace del menú.
   El componente de tendencias recibe actualmente una serie vacía: falta conectar
   periodos históricos. La vista Reportes no prueba por sí sola la presentación
   integral de todo el contenido N14.
8. **Preguntar en Chat IA.** Comparte sesión y negocio, sin otro login. Consulta
   conceptos del catálogo y resultados existentes S3/N14, muestra fuentes/fecha y
   usa lenguaje cotidiano. No necesita repetir el análisis para explicar un
   resultado disponible. Si falta evidencia o no se valida la redacción, comunica
   su limitación/respaldo. Es de solo lectura: no calcula nuevos resultados del
   negocio ni modifica auditorías. El historial es temporal: ocho turnos, treinta
   minutos de inactividad y límite global de 256 conversaciones por proceso.
   Los saludos reciben una bienvenida social breve, sin fuentes ni aviso de
   generación fallida; corrección validada localmente. Ver [saludos](chatbot_greetings.md).

## Conexión del motor con el chat

El motor calcula y guarda; el chat recupera y explica. El intercambio ya está
implementado mediante `audit_results`: métricas S3 e informe N14, cuando existe,
filtrados por negocio, fecha y `source_s3_result_id`. El chat no vuelve a procesar
los PDF ni tiene consulta libre a todas las tablas. Las definiciones proceden
del catálogo local y no acreditan resultados del negocio.

`api.main:app` sirve motor, chat y ajustes; `api.chat_app:create_app --factory`
sirve chat, negocios y ajustes sin ingesta/análisis. Ejecutarlos por separado
es opcional. La consulta posterior exige resultados realmente persistidos en
el mismo proyecto; no requiere que el motor siga trabajando.

La base principal y PRUEBAS siguen siendo proyectos separados. Esta instalación
usa principal: interfaz y servidor completo fueron reiniciados y verificados;
login y pantallas confirmados por el usuario. No se copiaron fixtures de PRUEBAS.
El análisis nuevo completo conserva su ensayo pendiente.
[Unificación y evidencia](database_unification.md).

## Avance y pendientes

| Área | Implementado o demostrado | Pendiente / límite del alcance |
|---|---|---|
| Acceso | Login común, sesión Supabase, lista propia, selección automática y permisos del chat | Simplificar selector con un negocio; registro/invitaciones de clientes; autorización por recurso de endpoints FastAPI legados |
| Diseño | Frontend azul, Dashboard como inicio único, menú, KPI, gráficas, Salud, Reportes y chat; bienvenida independiente eliminada | Completar experiencia integral de resultados e historial entre periodos |
| Base compartida | Principal con 18 tablas/175 columnas; datos preservados, procesos y acceso verificados; SQL 13/13 de unificación. INC-046/047 resueltas; INC-048/049 corregidas localmente con regresión 208/41 subpruebas | Ensayar documentos e IA reales, persistencia y consulta posterior; sin certificar despliegue público |
| Motor | Ingesta, validación, cálculo, interpretación, escalación y revisión implementados; evaluaciones del motor documentadas | Validar recorrido completo con datos representativos y servidor completo en el entorno de presentación; módulos omitidos de v1 separados |
| Chat Pasos 1–4 | Grounding, herramientas, conversación y evaluación offline aceptados en desarrollo; seguimiento cerrado el 12-oct | No reabrirlos por pendientes de integración o publicación |
| Chat Paso 5 | API, Auth/propiedad, historial, interfaz y ejecutor de pruebas implementados; acceso y pregunta conceptual confirmados por el usuario | Completar capas funcionales pendientes, pruebas reales y revisión humana de claridad |
| Configuración inicial | Automática sin gastos ficticios; edición avanzada opcional y protegida, 14/14 controles Edge N10 | Ensayo integral con documentos nuevos y servidor completo en la computadora de grabación |
| Tutorial guiado | Formulario de configuración y marcas `data-tour` | Recorrido didáctico por pantallas aún sin implementar |
| Celulares | Menú desplegable, chat y distribuciones adaptables; verificaciones sintéticas acotadas | Adaptación y pruebas completas de formularios, tablas, gráficas, teclado y tamaños/dispositivos |
| Producción | Base principal reactivada y actualizada con autorización; validaciones anteriores en PRUEBAS conservadas; sin despliegue web | Autorización por recurso en endpoints legados, revisión de dependencias, límites/observabilidad, historial entre réplicas y despliegue web autorizado |


## Acceso y navegación validados el 15-oct-2026

Dashboard es el inicio único. La sesión vive en la pestaña, conserva recargas y
no se recupera de cookies antiguas en una pestaña nueva. AuthProvider verifica
al usuario antes de mostrar datos; APIs verifican Bearer en servidor. La raíz
redirige con la configuración de Next, conservando origen. Bienvenida retirada.

Edge **24/24**, cero errores; helper **3/3**; build y tipos **código 0**.
Son pruebas con datos/Auth/modelo simulados: no una nueva validación de cuenta,
Supabase o Gemini reales. **42 incidencias: 39 resueltas, dos mitigadas y una
pendiente externa**. INC-042 resuelta localmente; INC-041 pendiente externo.
Código nuevo **sin commit/push** sobre HEAD `6d7cabc`; publicación anterior
conservada. Ver [contrato y límites](mepia_access_navigation.md) e
[informe verificable](evaluations/mepia_access_navigation_20261015.json).


## Evidencia de la automatización del 14-oct (anterior a esta corrección)

Las ejecuciones siguientes son del **14-oct-2026**; esta sincronización no las
convierte en pruebas nuevas ni en certificación de producción:

- Matriz local: **43 capas aprobadas, cinco pendientes, cero fallidas**. No son
  43 casos funcionales completos; existen subcontroles específicos pendientes.
- Regresión: **154 pruebas y 41 subpruebas**, dos advertencias, 22.73 s, código 0.
- Edge sintético: **18 controles, cero errores de página**, código 0. Carga:
  70 POST simulados. Sin servicios externos ni cuenta real en esos recorridos.
  El recorrido funcional es anterior a extraer el helper de limpieza del
  ejecutor; su verificación posterior es independiente. El 15-oct pasaron las
  tres pruebas del helper actual y TypeScript sin emisión ni caché. No se
  atribuye una nueva ejecución completa del navegador a esa comprobación.
- Gemini real con Auth/datos en memoria: **siete de ocho casos mecánicos
  aprobados**, 17/18 intentos; C02 detenido por HTTP 429, código 1. No es una
  validación de Supabase ni del recorrido completo con una cuenta real.
- **Ocho respuestas validadas para dos lectores, cero evaluaciones humanas
  registradas.** El usuario confirmó claridad de una definición; eso no sustituye
  la evaluación del conjunto.
- Incidencias: **41**, con **38 resueltas, dos mitigadas y una pendiente externa**.
  INC-20261014-041 continúa pendiente por disponibilidad/límite de Gemini.
  INC-20260930-014 se actualiza por la presente sincronización documental.

Fuentes: [ejecutor y límites](chatbot_step5_automation.md),
[intento local final](evaluations/chatbot_step5_automation_attempt6_20261014.json),
[intento Gemini](evaluations/chatbot_step5_automation_gemini_attempt1_20261014.json),
[revisión humana](evaluations/chatbot_step5_human_review_20261014.html),
[integración del frontend](chatbot_frontend_merge.md) y
[registro de incidencias](chatbot_incidents.md).

Los planes v1 y plantillas originales permanecen intactos como diseño previo;
no son el informe de resultados actual. El adaptador OpenAI existe para
evaluación, pero la configuración real vigente del chat utiliza Gemini. La
adopción de otro proveedor requiere validación separada.

## Publicación verificada en GitHub

El usuario autorizó actualizar la documentación, crear el commit y hacer push
el 15-oct-2026. La rama remota consultada inicialmente apunta a `6fa66bc`.
Publicado el commit de avances **`2c2ad07754204cf6216483de017dd898b2685255`** en
`github/codex/chatbot-q4`: push normal código 0 y consulta posterior del remoto
con el mismo hash. Incluye 374 archivos y 33 documentos de continuidad/diseño
en el conjunto. TypeScript sin errores, helper 3/3, package/lock coherentes,
207 enlaces válidos, cero coincidencias de secretos y 429 artefactos históricos
intactos por SHA-256.

Ver [auditoría previa](evaluations/github_publication_audit_20261015.json) y
[confirmación del push](evaluations/github_publication_verified_20261015.json).
La auditoría previa conserva su fotografía anterior al commit; este registro
de confirmación se guarda en un commit documental posterior, sin alterar pruebas
ni el historial de evidencia. Publicación del código completada; validación
funcional pendiente y despliegue de producción siguen separados.
No se cambia código funcional, datos, cuentas ni producción. Se retiran de
`tsconfig.json` referencias generadas a `.test_tmp` y se deja de versionar el
caché `tsconfig.tsbuildinfo`, conservando el archivo local.

## Explicación para el video

**MEPIA recibe información del restaurante, comprueba los datos, calcula
indicadores y utiliza IA para interpretar los resultados. El dueño puede
consultarlos y pedir explicaciones sencillas desde el chat integrado.**

Para 3–5 minutos: presentar el problema, mostrar login/identificación automática,
configuración, documentos, resultados y una pregunta al chat; cerrar con tutorial,
adaptación móvil y validación/publicación pendientes. Usar datos de prueba
preparados y comprobar previamente el recorrido que se mostrará. El perfil
`api.chat_app:create_app` sirve al chat, listado y ajustes protegidos; para
demostrar carga y análisis se necesita `api.main:app`. Aquí faltan las claves
OpenAI/Anthropic y no se ejecutó un análisis nuevo real. El usuario confirma las
pantallas de Documentos/ajustes en su cuenta, pero grabará otro integrante desde
su computadora con archivos nuevos. Preparar y ensayar esa instalación según la
[guía de grabación](mepia_setup_video.md); el éxito del ensayo sigue pendiente.
