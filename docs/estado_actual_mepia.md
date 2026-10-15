# MEPIA — Flujo y estado actual

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
3. **Configurar el negocio, cuando haga falta.** El formulario existente tiene
   cuatro pasos: identidad, umbrales, costos y reglas. No es el tutorial de uso.
   Guardar lleva a Documentos; el flujo de análisis comprueba la configuración.
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

## Avance y pendientes

| Área | Implementado o demostrado | Pendiente / límite del alcance |
|---|---|---|
| Acceso | Login común, sesión Supabase, lista propia, selección automática y permisos del chat | Simplificar selector con un negocio; registro/invitaciones de clientes; autorización por recurso de endpoints FastAPI legados |
| Diseño | Frontend azul, Dashboard como inicio único, menú, KPI, gráficas, Salud, Reportes y chat; bienvenida independiente eliminada | Completar experiencia integral de resultados e historial entre periodos |
| Motor | Ingesta, validación, cálculo, interpretación, escalación y revisión implementados; evaluaciones del motor documentadas | Validar recorrido completo con datos representativos y servidor completo en el entorno de presentación; módulos omitidos de v1 separados |
| Chat Pasos 1–4 | Grounding, herramientas, conversación y evaluación offline aceptados en desarrollo; seguimiento cerrado el 12-oct | No reabrirlos por pendientes de integración o publicación |
| Chat Paso 5 | API, Auth/propiedad, historial, interfaz y ejecutor de pruebas implementados; acceso y pregunta conceptual confirmados por el usuario | Completar capas funcionales pendientes, pruebas reales y revisión humana de claridad |
| Tutorial guiado | Formulario de configuración ya existente | Recorrido didáctico por pantallas aún sin implementar |
| Celulares | Menú desplegable, chat y distribuciones adaptables; verificaciones sintéticas acotadas | Adaptación y pruebas completas de formularios, tablas, gráficas, teclado y tamaños/dispositivos |
| Producción | Código y controles locales; entorno `MEPIA - PRUEBAS` usado en validaciones previas | Despliegue autorizado, migraciones/control de acceso, revisión de dependencias, límites/observabilidad e historial compartido si hay varias réplicas |


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
`api.chat_app:create_app` sirve solo al chat y listado; para demostrar carga y
análisis se necesita el servidor completo `api.main:app` y su configuración.
