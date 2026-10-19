# Configuración inicial automática — integración local

**Alcance de esta evidencia:** integración N10 validada en su entorno y fecha.
El conteo de 45 incidencias al final corresponde a ese cierre. El estado posterior
incluye la [unificación en principal](database_unification.md), con INC-046/047
resueltas en su alcance y las pruebas nuevas descritas allí.
No se traslada a principal la aprobación previa de ajustes en PRUEBAS;
el chat sigue siendo de consulta. [Estado actual](estado_actual_mepia.md).

Fecha: 15-oct-2026. Rama: `codex/chatbot-q4`. HEAD de referencia:
`f9cfddc84721a9ea32f8e56ba804f0ed8dc77f09`. Cambios **sin commit/push**.
Categoría: mejora adicional de configuración N10 y corrección de los defectos
encontrados en la entrega del equipo. No reabre los Pasos 1–4 del chatbot.

## Comportamiento vigente

Documentos muestra directamente los campos de carga. Al entrar, consulta los
ajustes del negocio autenticado; si no existen, guarda valores iniciales. No
inventa gastos: `expected_cost_structure` empieza vacío. Una configuración ya
guardada se conserva; repetir la creación devuelve 409 sin sobrescribirla.
«Personalizar configuración avanzada» permite editar los cuatro pasos y carga
los ajustes anteriores antes de habilitar el guardado.

Valores iniciales: diferencia de caja 2% o 150 MXN, margen de advertencia 15%,
crítico 8%, incremento de costo 10%, foco eficiencia y frecuencia diaria. Son
parámetros iniciales editables; no gastos ni resultados reales del negocio.
Elegir frecuencia no implementa un programador automático.

## Defectos corregidos

- **INC-20261015-044:** el campo de tolerancia de costos usa porcentajes visibles.
  GET convierte decimal a porcentaje; al guardar, el formulario divide siempre
  entre 100. `0.005 → 0.5% → 0.005`, incluso por debajo de 1%.
- **INC-20261015-045:** GET/POST/PUT N10 exigen JWT Bearer verificado y propiedad
  del negocio antes de consultar o escribir ajustes. Negocio ajeno, inexistente
  o sin dueño se rechaza con 403 antes de acceder a su configuración; sin sesión
  válida, 401. El proxy Next reenvía Bearer y valida identificadores/cuerpo.

El router `api/onboarding.py` se registra tanto en `api.main` como en
`api.chat_app`. No quedan las rutas N10 anónimas anteriores en `api/main.py`.
Esta protección no cierra los permisos pendientes de otros endpoints legados.
El chat sigue siendo de solo lectura; guardar ajustes es una operación separada.

## Archivos de producto

- `api/onboarding.py`, `api/main.py`, `api/chat_app.py` y
  `app/api/onboarding/route.ts`.
- `app/onboarding/page.tsx`, `app/upload/page.tsx`.
- `components/onboarding/{OnboardingForm,AuditRulesStep,AuditTolerancesStep,BrandIdentityStep,CostStructureStep}.tsx`
  y `components/onboarding/defaults.ts`.
- `components/upload/UploadForm.tsx`; eliminado el componente obsoleto
  `components/upload/OnboardingGate.tsx`.

Pruebas nuevas: `tests/onboarding_fixtures.py`, `tests/test_onboarding_api.py`,
`tests/onboarding_step_server.py`, `tests/onboarding_step_e2e.cjs`.
Actualizado `tests/test_chat_app.py` para comprobar ambos perfiles.
Actualizados README, plantilla privada sin valores, bitácoras, estado actual,
contratos N10/N15/Auth/glosario, diseños y guía de instalación para el equipo.

## Evidencia ejecutada

| Validación | Resultado y alcance |
|---|---|
| Regresión Python: N10, API/chat, arranque, conversación, respuesta y ES256 | 151 aprobadas, 41 subpruebas, dos advertencias de deprecación existentes; 9.54 s, código 0 |
| Edge N10, Next y FastAPI reales con Auth/DB en memoria | 14/14, cero errores de página, código 0 |
| Edge general, acceso/navegación/chat y controles ampliados | 25/25, cero errores de página, código 0 |
| Helper de restauración del ejecutor | 3/3, código 0 |
| Build Next con verificación de tipos | Código 0, 74770 ms; configuración pública sintética |
| Esquema real MEPIA - PRUEBAS | Tres consultas `limit 0`; tres tablas disponibles, cero filas devueltas y cero escrituras |
| Servicios locales iniciados | Frontend 3016 y perfil Chat IA/ajustes 8016; login 200, N10 anónimo directo y por proxy 401 |
| Confirmación del usuario | Documentos y ajustes avanzados abren sin error; no se exigió completar el formulario para ver la carga |

Las seis vueltas de porcentaje **0%, 0.1%, 0.5%, 1%, 5% y 100%** conservaron
su valor al abrir y guardar sin editar en Edge. GET/POST/PUT de negocio ajeno
devolvieron 403 sin datos ni cambios. Las pruebas funcionales usan servicios
externos simulados; no son nuevas evaluaciones reales de Gemini ni del motor.
La confirmación manual corresponde a lo informado por el usuario, sin inspección
independiente del navegador ni comprobación de un guardado real de ajustes.

El chequeo de esquema real solo verificó columnas de `business_onboarding`,
`business_fixed_costs` y `mepia_memory`, sin leer registros. No valida todas las
migraciones ni el recorrido de análisis completo. Cero llamadas nuevas del
agente a modelos, cero cambios de producción, cuentas o migraciones.

Se conservaron los resultados originales de la revisión: 11/13 controles y dos
defectos. No se convierten retrospectivamente en aprobados. También se preserva
la carpeta original del equipo. Un falso conflicto al preparar la fusión
documental, causado por finales de línea, se resolvió antes de escribir esos
documentos. El primer intento de reiniciar el backend no encontró procesos;
después se iniciaron los dos servicios, sin detener procesos ajenos.

[Informe verificable](evaluations/onboarding_defaults_integration_20261015.json).
[Revisión histórica](onboarding_candidate_review_20261015.md).

La revisión documental conservó por SHA-256 **436 artefactos históricos** y los
**705 archivos originales** del equipo. Escaneo de 716 archivos candidatos:
cero hallazgos de secretos/correos personales, 289 enlaces locales válidos y
cero rotos; `git diff --check` código 0. Las menciones antiguas del gate y de
configuración obligatoria en tareas fechadas se mantienen como historia. El
mínimo de costos de la spec N03 es otro contrato, distinto del N10 actual.

## Límites y siguiente acción

INC-044/045 resueltas localmente. Estado global: 45 incidencias, 42 resueltas,
dos mitigadas (023/031), una pendiente externa (041), cero abiertas. Los
pendientes funcionales/humanos del Paso 5 siguen según su propia matriz.

El perfil local activo permite login, negocios, ajustes y chat. **Para subir
documentos nuevos al backend y analizarlos hace falta `api.main:app` y la
configuración completa.** En esta máquina las claves OpenAI y Anthropic siguen
vacías. No se ejecutó un análisis nuevo real en esta corrección. El usuario
aclara que otro integrante grabará el video desde su propia computadora,
incluyendo archivos nuevos: seguir la [guía de preparación](mepia_setup_video.md)
y ensayar allí el recorrido antes de grabar. No se declara ese recorrido listo
por haber aprobado N10. Tutorial guiado pendiente y adaptación móvil parcial.
