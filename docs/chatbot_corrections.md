# Bitácora oficial del chatbot de MEPIA

Este documento es la fuente de verdad para continuar el desarrollo del chatbot sin
depender del historial de conversaciones. Debe actualizarse después de cada cambio
con evidencia real de Git, pruebas y validaciones.

Las incidencias ocurridas durante desarrollo, pruebas, documentación o publicación
se registran por separado en [`chatbot_incidents.md`](chatbot_incidents.md). No
duplicar aquí su contenido operativo; citar el identificador cuando sea relevante.

**Estado al 15-sep-2026:** las correcciones 1, 2, 3 y 4 están terminadas en
desarrollo y pruebas. El **Trabajo 5 — linaje exacto entre S3 y N14** es el
siguiente trabajo obligatorio. Producción no ha sido modificada y no se ha
desplegado el chatbot.

## A. Correcciones de defectos del Paso 1

### Corrección 1 — terminada en desarrollo y pruebas

**Objetivo.** Normalizar los estados históricos de `audit_results` antes de
instalar el nuevo constraint:

| Estado anterior | Estado normalizado |
|---|---|
| `completed`, `complete`, `approved`, `approved_with_warning_cortafuegos` | `success` |
| `rejected`, `pending` | `partial` |
| Estado vigente | Se conserva |
| Estado desconocido | `error` |
| `NULL` | Se conserva |

**Registro Git verificado:**

- Rama: `codex/chat-grounding-step1`.
- Commit: `ca96ba9326118e216e9553ad9e5ee1d3b66d1e10`
  (`feat: implementar grounding del chatbot y corregir contrato audit_results`).
- El commit contiene el Paso 1 inicial y esta corrección; no es un commit aislado.
- Archivos modificados en el commit: `.kiro/specs/mepia/_glossary.md`,
  `.kiro/specs/mepia/_index.md`, `.kiro/specs/mepia/db_schema.md`,
  `.kiro/specs/mepia/n15_chat_consulta.md`, `agents/calc_engine.py`,
  `agents/ceo_orchestrator.py`, `agents/chat_grounding.py`,
  `agents/n13_revisor.py`, `agents/parallel_orchestrator.py`, `api/main.py`,
  `docs/mepia_v4_metricas_diseno.md`,
  `supabase/migrations/008_audit_results_runtime_contract.sql`,
  `supabase/migrations/APPLY_ALL.sql`,
  `tests/test_audit_results_migration.py` y `tests/test_chat_grounding.py`.

**Pruebas y validaciones registradas:**

- Pruebas locales de ese estado: 6/6 de grounding y 2/2 de migración; 8/8 en
  total.
- La migración se ejecutó dos veces en `MEPIA - PRUEBAS`.
- Se preservaron 13/13 filas sintéticas.
- Resultado final: 0 estados inválidos, constraint correcto y 2 índices presentes.
- La fila de prueba `N06_pending` terminó con estado `partial`.
- Producción solo se consultó en modo de lectura. No se realizó despliegue.

**Pendiente de producción:** el despliegue de la migración forma parte de la
sección D y no cambia el estado de esta corrección en desarrollo y pruebas.

### Corrección 2 — terminada en desarrollo y pruebas

**Objetivo.** `ChatGroundingService._latest_row()` filtra mediante
Supabase/PostgREST los estados utilizables antes de ordenar y aplicar `limit(5)`.
Esto evita que cinco ejecuciones `failed`, `partial`, `error`, `timeout` o inválidas
más recientes oculten una ejecución exitosa anterior.

**Registro Git verificado:**

- Rama: `codex/chat-grounding-step2`.
- Commit: `abd165b8f1cafbe3c92b5ebf7da5459eca0bc689`
  (`fix: filtrar estados válidos antes del límite`).
- Archivos modificados: `agents/chat_grounding.py`,
  `tests/test_chat_grounding.py` y `docs/mepia_v4_metricas_diseno.md`.

**Pruebas y validaciones registradas:**

- 7/7 pruebas de grounding aprobadas.
- 2/2 pruebas de migración aprobadas.
- Total relacionado: 9/9 pruebas aprobadas.
- El caso de regresión se validó en `MEPIA - PRUEBAS`: una fila `success` anterior
  fue recuperada detrás de cinco filas recientes no utilizables.
- La construcción de la consulta se comprobó con `supabase-py==2.4.0` y
  `supabase-py==2.31.0`.
- Producción únicamente se consultó en modo de lectura. No se realizó despliegue.

### Corrección 3 — terminada en desarrollo y pruebas

**Estado:** terminada en desarrollo y pruebas.

**Defecto confirmado.** En `agents/chat_grounding.py`,
`_extract_final_report()` devuelve `{}` cuando una fila N14 contiene datos, pero
ninguno de sus campos pertenece a `_FINAL_REPORT_FIELDS`. Como `build_packet()`
solo comprueba `final_report is None`, interpreta el diccionario vacío como un
reporte válido y no agrega `final_report_not_found`.

**Resultado esperado:**

- Filtrar `result_data` usando `_FINAL_REPORT_FIELDS`.
- Si después del filtrado no queda ningún campo autorizado, devolver `None`.
- Agregar `final_report_not_found` a `missing_data`.
- No exponer campos no autorizados.
- Mantener el funcionamiento normal de reportes N14 válidos.
- Agregar una prueba de regresión con un N14 que contenga únicamente un campo no
  permitido, por ejemplo `instructions`.

**Implementación:** `_extract_final_report()` construye el reporte exclusivamente
con `_FINAL_REPORT_FIELDS` y devuelve `None` cuando el filtrado no conserva ningún
campo. `build_packet()` registra entonces `final_report_not_found`; la fila N14
permanece en la evidencia auditable, pero sus campos no autorizados no se exponen.

**Registro Git verificado:**

- Rama: `codex/chat-grounding-step3`.
- Commit de código y pruebas: `922ba91fcc088465fc52b0ed1a4be19921422ba1`
  (`fix: tratar reportes N14 sin campos autorizados como ausentes`).
- Archivos modificados: `AGENTS.md`, `.kiro/specs/mepia/n15_chat_consulta.md`,
  `agents/chat_grounding.py`, `docs/chatbot_corrections.md`,
  `docs/chatbot_incidents.md`, `docs/mepia_v4_metricas_diseno.md` y
  `tests/test_chat_grounding.py`.

**Pruebas y validaciones registradas:**

- Comando ejecutado con el Python incluido en el entorno de Codex:
  `python -m unittest tests.test_chat_grounding tests.test_audit_results_migration -v`.
- Resultado real: 8/8 pruebas de grounding y 2/2 pruebas de migración aprobadas;
  10/10 en total (`OK`).
- Incidencia de entorno relacionada: `INC-20260915-002`, resuelta mediante el
  runtime de Python incluido con Codex.
- La regresión usa un N14 cuyo único campo es `instructions` y comprueba
  `final_report is None`, `final_report_not_found` y ausencia de `instructions`
  en el paquete.
- La prueba existente de un N14 válido continúa aprobando y conserva sus campos
  autorizados.
- No se consultó, desplegó ni modificó producción.

### Corrección 4 — terminada en desarrollo y pruebas

**Estado:** terminada en desarrollo y pruebas.

**Defecto confirmado.** `ChatGroundingService._extract_metrics()` presupone que
`result_data` es un diccionario. Un JSONB con una lista, texto, número u otro tipo
inesperado puede producir `AttributeError` y romper la construcción completa del
paquete. También debe validarse el tipo de `results`.

**Resultado esperado:**

- Validar los tipos de `result_data` y `results`.
- No lanzar excepciones por contenido persistido malformado.
- No exponer contenido inesperado.
- Tratar los datos inválidos como información no disponible.
- Registrar la ausencia o invalidez correspondiente en `missing_data`.
- Agregar pruebas de regresión para lista, texto, número y `null`.

**Implementación:** `_extract_metrics()` comprueba primero que `result_data` sea
un diccionario y que `results` sea una lista. Si cualquiera tiene un tipo
inesperado, devuelve una lista vacía sin iterar ni exponer el contenido persistido;
`build_packet()` registra entonces `metrics_not_found`. Las métricas S3 válidas
continúan filtrándose mediante `_METRIC_FIELDS`.

**Registro Git verificado:**

- Rama: `codex/chat-grounding-step4`.
- Commit de código y pruebas: `367ab96e9e6a16cc63781dce4f462aa7a6556565`
  (`fix: validar estructura de metricas S3`).
- Commit de cierre documental: `f13e2e86fb770d7b730447670ebaf6c9978a8bce`
  (`docs: cerrar correccion 4`).
- Base verificada: `b1aa4ca8a542f57f9e1052696289b54955e7028f`
  (`docs: cerrar corrección 3 y registrar incidencias`).
- Archivos modificados: `.kiro/specs/mepia/n15_chat_consulta.md`,
  `agents/chat_grounding.py`, `docs/chatbot_corrections.md`,
  `docs/chatbot_incidents.md`, `docs/mepia_v4_metricas_diseno.md` y
  `tests/test_chat_grounding.py`.

**Pruebas y validaciones registradas:**

- El comando `python -m unittest tests.test_chat_grounding
  tests.test_audit_results_migration -v` no pudo iniciar porque `python` no
  estaba disponible en el `PATH`; se actualizó `INC-20260915-002`.
- El mismo módulo de pruebas se ejecutó con el runtime de Python incluido con
  Codex: 10/10 pruebas de grounding y 2/2 de migración aprobadas; 12/12 en total
  (`Ran 12 tests in 0.021s`, `OK`).
- `git diff --check` terminó con código 0 y sin errores de espacios; Git emitió
  advertencias de normalización futura de LF a CRLF para los seis archivos
  modificados.
- Las regresiones cubren `result_data` como lista, texto, número, booleano y
  `null`, además de `results` como objeto, texto, número, booleano y `null`.
- La prueba existente con métricas S3 válidas continúa aprobando y conserva los
  campos autorizados.
- No se consultó, desplegó ni modificó producción.

Estas son las cuatro correcciones concretas encontradas durante la revisión
inicial y todas están terminadas en desarrollo y pruebas. La cantidad puede
aumentar: cualquier defecto nuevo descubierto por una prueba debe agregarse a
esta bitácora y priorizarse explícitamente.

## B. Trabajo obligatorio de robustez para cerrar el Paso 1

### Trabajo 5 — linaje exacto entre S3 y N14 — siguiente trabajo obligatorio

**Estado:** pendiente de diseño e implementación.

Actualmente `ChatGroundingService` relaciona S3 y N14 mediante `business_id` y
fecha. Si el mismo negocio tiene dos auditorías el mismo día, puede seleccionar las
métricas de una ejecución y el reporte de otra.

**Objetivo:**

- Diseñar una relación verificable mediante `run_id`, `layer3_run_id` u otro
  identificador común.
- Revisar cómo S3 y N14 persisten sus identificadores actualmente.
- Determinar si se necesita una migración.
- Evitar relacionar las fuentes solamente por fecha.
- Agregar pruebas con dos ejecuciones del mismo negocio y fecha.
- Documentar la decisión antes de implementarla.

No implementar este trabajo dentro de las correcciones 3 o 4 sin revisar primero
el flujo completo S3 → N05 → N06 → Layer 3 → N14.

## C. Mejoras de robustez y validación

Pendientes separados del cierre funcional inmediato:

1. Fijar una versión compatible de `supabase-py` o agregar un mecanismo de bloqueo
   de dependencias.
2. Ejecutar una prueba HTTP completa contra el Data API de `MEPIA - PRUEBAS`.
3. Ejecutar una prueba integral del Paso 1 después de terminar las correcciones 3
   y 4 y el Trabajo 5.
4. Definir cuándo dejar de aceptar `completed` y `NULL` como estados legacy.
5. Ejecutar la suite general del proyecto, además de las pruebas específicas del
   grounding.
6. Comprobar que ningún cambio aumente innecesariamente las llamadas al LLM ni
   rompa el enfoque RAG. El Paso 1 actual es determinista y no llama a un LLM.

## D. Preparación para producción

**Estado:** todo pendiente. Producción todavía no ha sido modificada.

1. Generar un respaldo lógico verificable de producción inmediatamente antes del
   despliegue.
2. Ejecutar consultas previas para contar los estados que serán transformados.
3. Confirmar la versión real del backend y sus dependencias.
4. Detener o evitar escrituras concurrentes sobre `audit_results`.
5. Ejecutar la migración `008` transaccionalmente.
6. Verificar filas, estados, constraints e índices después de la migración.
7. Desplegar el código solo después de aprobar la prueba integral.
8. Preparar un procedimiento de reversión.

Ninguno de estos pasos está autorizado por el estado actual de esta bitácora.

## E. Fases posteriores del chatbot

Este plan general no debe confundirse con las correcciones anteriores:

1. Datos verificables y grounding S3/N14 — implementado; las cuatro correcciones
   iniciales están terminadas y el robustecimiento de linaje del Trabajo 5 es el
   siguiente trabajo obligatorio.
2. Herramientas deterministas para consultar métricas, reportes y glosario —
   pendiente.
3. Nodo conversacional con respuesta estructurada y rechazo cuando falta evidencia
   — pendiente.
4. Evaluación offline de exactitud, ausencia de invención, aislamiento y preguntas
   fuera de alcance — pendiente.
5. Endpoint autenticado, autorización por negocio, historial controlado e interfaz
   Chat IA — pendiente.

La **Corrección 3** es un defecto concreto de `_extract_final_report()` dentro del
Paso 1. No es el **Paso 3 del chatbot**, que corresponde al futuro nodo
conversacional.

## Registro operativo

| Fecha | Trabajo | Rama | Commit | Archivos | Pruebas y resultado |
|---|---|---|---|---|---|
| 14-sep-2026 | Corrección 1 | `codex/chat-grounding-step1` | `ca96ba9` | 15 archivos; detalle en la sección A | 8/8 locales; validación doble de migración en `MEPIA - PRUEBAS` correcta |
| 14-sep-2026 | Corrección 2 | `codex/chat-grounding-step2` | `abd165b` | `agents/chat_grounding.py`, `tests/test_chat_grounding.py`, `docs/mepia_v4_metricas_diseno.md` | 9/9 relacionadas; regresión e integración en `MEPIA - PRUEBAS` correctas |
| 15-sep-2026 | Continuidad documental | `codex/chat-grounding-step2` | Sin commit; base `abd165b` | `AGENTS.md`, `docs/chatbot_corrections.md`, `docs/mepia_v4_metricas_diseno.md`, `.kiro/specs/mepia/n15_chat_consulta.md` | No se ejecutaron pruebas unitarias porque no cambió código; `git diff --check` sin errores |
| 15-sep-2026 | Corrección 3, cierre documental y bitácora de incidencias | `codex/chat-grounding-step3` | `922ba91` (código y pruebas) | `AGENTS.md`, `.kiro/specs/mepia/n15_chat_consulta.md`, `agents/chat_grounding.py`, `docs/chatbot_corrections.md`, `docs/chatbot_incidents.md`, `docs/mepia_v4_metricas_diseno.md`, `tests/test_chat_grounding.py` | 8/8 grounding y 2/2 migración; 10/10 relacionadas aprobadas (`OK`) |
| 15-sep-2026 | Corrección 4 y cierre documental | `codex/chat-grounding-step4` | `367ab96` (código y pruebas); `f13e2e8` (cierre documental); base `b1aa4ca` | `.kiro/specs/mepia/n15_chat_consulta.md`, `agents/chat_grounding.py`, `docs/chatbot_corrections.md`, `docs/chatbot_incidents.md`, `docs/mepia_v4_metricas_diseno.md`, `tests/test_chat_grounding.py` | 10/10 grounding y 2/2 migración; 12/12 relacionadas aprobadas (`Ran 12 tests in 0.021s`, `OK`) con el runtime de Codex; el intento con `python` no inició (`INC-20260915-002`); `git diff --check` código 0, sin errores de espacios y con advertencias LF→CRLF |
| 15-sep-2026 | Revisión final y sincronización documental antes del Trabajo 5 | `codex/chat-grounding-step4` | `sin commit`; HEAD `f13e2e8` | `docs/chatbot_corrections.md`, `docs/chatbot_incidents.md`, `docs/mepia_v4_metricas_diseno.md` | Suite específica: 12/12 aprobadas (`Ran 12 tests in 0.017s`, `OK`). Suite general: 12 pruebas importables aprobadas y 9 módulos no importados por ausencia de `pytest` (`Ran 21 tests in 0.020s`, `FAILED (errors=9)`); incidencia `INC-20260915-002` actualizada. `git diff --check`: código 0, sin errores de espacios y con advertencias LF→CRLF |
