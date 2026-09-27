# Bitácora oficial del chatbot de MEPIA

Este documento es la fuente de verdad para continuar el desarrollo del chatbot sin
depender del historial de conversaciones. Debe actualizarse después de cada cambio
con evidencia real de Git, pruebas y validaciones.

Las incidencias ocurridas durante desarrollo, pruebas, documentación o publicación
se registran por separado en [`chatbot_incidents.md`](chatbot_incidents.md). No
duplicar aquí su contenido operativo; citar el identificador cuando sea relevante.

**Estado al 24-sep-2026:** las correcciones 1–5, el **Trabajo 5 — linaje exacto
entre S3 y N14**, la prueba integral del Paso 1 y el Paso 2 ampliado están
terminados en desarrollo. El Paso 2 cubre las 31 métricas del pipeline, cuatro
cálculos auxiliares y prohíbe absolutamente calcular desde el chat. La validación
real del Paso 1 en `MEPIA - PRUEBAS` permanece aprobada. La siguiente acción es el
Paso 3: nodo conversacional estructurado. Producción no ha sido modificada.

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
ninguno de sus campos pertenece a `CHAT_FINAL_REPORT_FIELDS`. Como `build_packet()`
solo comprueba `final_report is None`, interpreta el diccionario vacío como un
reporte válido y no agrega `final_report_not_found`.

**Resultado esperado:**

- Filtrar `result_data` usando `CHAT_FINAL_REPORT_FIELDS`.
- Si después del filtrado no queda ningún campo autorizado, devolver `None`.
- Agregar `final_report_not_found` a `missing_data`.
- No exponer campos no autorizados.
- Mantener el funcionamiento normal de reportes N14 válidos.
- Agregar una prueba de regresión con un N14 que contenga únicamente un campo no
  permitido, por ejemplo `instructions`.

**Implementación:** `_extract_final_report()` construye el reporte exclusivamente
con `CHAT_FINAL_REPORT_FIELDS` y devuelve `None` cuando el filtrado no conserva ningún
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
continúan filtrándose mediante `CHAT_METRIC_FIELDS`.

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

### Corrección 5 — copia JSONB de linaje conflictiva — terminada en desarrollo

**Defecto confirmado.** El linaje verificable de N14 vive en la columna
`audit_results.source_s3_result_id`, pero `_extract_final_report()` también podía
exponer una copia distinta guardada dentro de `result_data`. Aunque la selección
de la fila N14 ya usaba la columna correcta, esa duplicación podía mostrar al
chat un identificador no verificado.

**Implementación.** Si el reporte contiene `source_s3_result_id`, el valor de
salida se sustituye por el UUID validado de la columna de la fila N14. Los demás
campos siguen bajo allowlist. La regresión crea una fila cuyo JSONB apunta a otro
UUID y confirma que solo se conserva la raíz S3 verificada.

**Registro Git verificado:** rama `codex/chatbot-q4`; `sin commit`, HEAD
`48bdbc4`. Archivos de código y prueba: `agents/chat_grounding.py` y
`tests/test_chat_grounding.py`.

**Pruebas focalizadas:** `26 passed, 13 subtests passed in 1.55s` con pytest sin
caché; la misma selección terminó `Ran 26 tests in 0.028s`, `OK` con unittest.
No se consultó ni modificó ninguna base de datos.

Las cinco correcciones encontradas están terminadas en desarrollo. La cantidad
puede aumentar: cualquier defecto nuevo descubierto por una prueba debe agregarse
a esta bitácora y priorizarse explícitamente.

## B. Trabajo obligatorio de robustez para cerrar el Paso 1

### Trabajo 5 — linaje exacto entre S3 y N14 — terminado en desarrollo y pruebas

**Estado:** terminado en desarrollo y pruebas, confirmado en Git y validado
integralmente contra `MEPIA - PRUEBAS`.

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

**Análisis de identificadores verificado antes de implementar:**

| Etapa | Identificadores creados o recibidos | Persistencia actual antes del Trabajo 5 |
|---|---|---|
| S3 | Genera `CalcRunResult.run_id` | El valor se usa como `audit_results.id`; la columna `run_id` queda vacía. |
| N05 | Genera otro `OrchestratorResult.run_id` independiente | Se usa como `audit_results.id`; el identificador de la fila S3 no se conserva. |
| N06 | Recibe `sequential_run_id` = ID de N05 y genera/recibe `layer2_run_id` | La fila N06 usa `id = layer2_run_id`; ambos identificadores quedan en `result_data`. |
| Layer 3 | Recibe `sequential_run_id` y `layer2_run_id`; genera `layer3_run_id` | N10 usa `id = layer3_run_id`; N11, N13 y N14 generan sus propios IDs de fila. N14 conserva `layer3_run_id` en `result_data`. |
| API Layer 3 | Recibe `audit_run_id` | No es un identificador adicional: en modo normal es el `audit_results.id` de N06 y, por tanto, el mismo valor que `layer2_run_id`. |

`audit_results.id` identifica inequívocamente una fila, pero ninguno de
`run_id`, `audit_run_id`, `sequential_run_id`, `layer2_run_id` o
`layer3_run_id` enlaza actualmente una fila N14 con la fila S3 concreta que la
originó. Por tanto, no basta con cambiar la consulta del chat: se necesita
persistir y propagar un identificador de linaje nuevo.

**Decisión de diseño:** el identificador canónico será el `audit_results.id` de
la fila S3, expuesto como `source_s3_result_id`. Se agregará a `audit_results`
como UUID nullable con FK autorreferencial a `audit_results(id)` e índice de
consulta. N05 lo tomará de `CalcRunResult.run_id` y lo propagará por N06 y el
estado de Layer 3 hasta N14; las filas descendientes persistirán el mismo valor.
El servicio de grounding elegirá primero una sola fila S3 utilizable y después
buscará N14 por `business_id`, fecha y `source_s3_result_id = S3.id`. Nunca habrá
fallback por fecha.

Cuando una fecha contenga varias ejecuciones, se elige la fila S3 utilizable más
reciente por `created_at`; solo su N14 exacto puede acompañarla. Si esa ejecución
no tiene N14 enlazado, se devuelve `final_report_not_found`, aunque una ejecución
anterior del mismo día sí tenga reporte. Los registros históricos conservarán
`source_s3_result_id = NULL`: no se intentará inferir o rellenar el linaje por
negocio y fecha porque esa asociación no es demostrable. Un identificador
ausente, inválido o no coincidente se trata igualmente como reporte no
encontrado y no se incluye como evidencia.

**Implementación:** la migración incremental
`009_audit_results_s3_lineage.sql` agrega `source_s3_result_id` como UUID
nullable, FK autorreferencial a `audit_results(id)` con `ON DELETE SET NULL`, y
el índice `idx_audit_results_s3_lineage`. La FK se crea solo si falta, primero
como `NOT VALID` y después se valida, de modo que una reejecución no elimine una
restricción ya instalada ni abra una ventana sin integridad referencial.
`APPLY_ALL.sql` contiene el mismo contrato para instalaciones completas. S3 usa
su propio `audit_results.id` como raíz; N05, N06, N10, N11, N13 y N14 propagan y
persisten ese valor. La ruta manual normal de Layer 3 lo recupera de N06; el modo
aislado y los históricos permanecen sin linaje verificable.

`ChatGroundingService` selecciona primero la fila S3 utilizable más reciente y
solo consulta N14 con el mismo `business_id`, fecha y `source_s3_result_id`. El
paquete y sus referencias exponen el identificador de linaje; las allowlists de
métricas y reporte final siguen limitando el contenido permitido. Si falta S3,
su ID no es un UUID válido o N14 no coincide exactamente, no se usa ningún N14 y
se agrega `final_report_not_found`.

**Registro Git verificado:**

- Rama del Trabajo 5: `codex/chat-grounding-step5`.
- Rama actual de continuidad: `codex/chatbot-q4`.
- Worktree actual:
  `C:\Users\giova\.codex\worktrees\chatbot-q4\Mepia_clean`.
- Base: `855151f64797e721ede75d1e627a8e07a820ed98`
  (`docs: sincronizar cierre de correccion 4`).
- Commit del Trabajo 5: `48bdbc4`
  (`feat: add exact S3-to-N14 lineage`).

**Archivos modificados:**

- Código: `agents/api_ingest.py`, `agents/calc_engine.py`, `agents/ceo_orchestrator.py`,
  `agents/chat_grounding.py`, `agents/context_builder.py`,
  `agents/core_auditor.py`, `agents/layer3_state.py`,
  `agents/n13_revisor.py`, `agents/n14_informe_final.py`,
  `agents/parallel_orchestrator.py` y `api/main.py`.
- SQL: `supabase/migrations/009_audit_results_s3_lineage.sql` y
  `supabase/migrations/APPLY_ALL.sql`.
- Pruebas y entorno: `api/requirements-dev.txt`, `tests/test_chat_grounding.py`,
  `tests/test_chat_lineage_persistence.py` y
  `tests/test_audit_results_migration.py`, además de la actualización de
  `tests/test_persist_ingestion.py` para el contrato vigente de reimpresiones.
- Documentación: `docs/chatbot_corrections.md`,
  `docs/chatbot_incidents.md`, `docs/mepia_v4_metricas_diseno.md`, y las
  especificaciones `.kiro` `_glossary.md`, `api_layer3.md`, `db_schema.md`,
  `layer3_graph.md`, `n05_ceo_orchestrator.md`, `n06_orchestrator_adk.md`,
  `n10_context_builder.md`, `n11_consultor.md`, `n13_revisor.md`,
  `n14_informe_final.md` y `n15_chat_consulta.md`.

**Pruebas y validaciones ejecutadas:**

- Los intentos iniciales incompletos con Python 3.14 y el runtime de Codex quedan
  preservados en `INC-20260915-002`. Después se creó un entorno virtual aislado
  con Python 3.12.14 y se instalaron `api/requirements.txt` y `pytest`; el nuevo
  `api/requirements-dev.txt` deja documentado el comando reproducible.
- La primera suite general real recopiló 118 pruebas: 112 aprobaron y 6 fallaron
  en `tests/test_persist_ingestion.py`. La comparación con la base `855151f`
  confirmó que no eran regresiones del Trabajo 5: el fixture histórico todavía
  enviaba `reprints=2` aunque `ShiftAuditEvent` ya exigía
  `list[ReprintRecord]`. También se corrigió la persistencia para convertir cada
  `ReprintRecord` a JSON antes del `upsert`; véase `INC-20260915-006`.
- Después de la corrección, `tests/test_persist_ingestion.py` aprobó 23/23. La
  repetición completa sin caché aprobó **118/118 pruebas y 17 subpruebas** en
  39.22 s con Python 3.12.14, pytest 9.1.1, Hypothesis 6.168.0 y Pydantic 2.13.5.
- Las 21 pruebas específicas del Trabajo 5 —13 de grounding, 4 del contrato SQL
  y 4 de propagación/persistencia— están incluidas en ese resultado y aprobaron.
  Los 13 archivos Python del Trabajo 5 también compilaron correctamente mediante
  `compile()` sin generar artefactos.
- Las regresiones incluyen dos S3 y dos N14 del mismo negocio y fecha, un N14
  anterior con timestamp más reciente, ausencia de N14 para el S3 elegido y
  enlaces N14 ausentes, inválidos o no coincidentes.
- `pglast` 8.4 analizó sin errores la sintaxis SQL exterior de
  `009_audit_results_s3_lineage.sql` y `APPLY_ALL.sql`. La prueba real mostró el
  límite de esa validación: el cuerpo de `DO` es una cadena para el parser SQL y
  su sintaxis PL/pgSQL solo se comprobó al ejecutarlo; véase
  `INC-20260915-007`.
- La migración 009 se probó en PostgreSQL real mediante el editor SQL del proyecto
  aislado `MEPIA - PRUEBAS`. Antes había 19 filas, la tabla ocupaba 96 kB y no
  existían columna, FK ni índice. El primer intento se detuvo en el bloque `DO`;
  solo alcanzó a crear la columna nullable y no modificó filas. Se cambió el DDL
  condicional a `EXECUTE`, se comprobó que las 21 pruebas específicas seguían
  aprobando y se ejecutó de nuevo correctamente.
- La validación posterior confirmó columna `uuid`, FK validada con definición
  `FOREIGN KEY (source_s3_result_id) REFERENCES audit_results(id) ON DELETE SET
  NULL`, e índice btree sobre `(business_id, source_s3_result_id, node_id,
  created_at DESC)`. Se conservaron 19/19 filas y 0 históricos recibieron un
  enlace inferido. Una segunda ejecución completa terminó correctamente; la
  comprobación final reportó 19 filas, 0 enlaces históricos, 1 FK y 1 índice.
- `git diff --check` terminó con código 0 y sin errores de espacios; Git emitió
  advertencias de normalización futura de LF a CRLF para archivos modificados.
- No se consultó, desplegó ni modificó producción.

## C. Mejoras de robustez y validación

Mejoras separadas del cierre funcional inmediato:

1. Fijar una versión compatible de `supabase-py` o agregar un mecanismo de bloqueo
   de dependencias.
2. ✅ Prueba HTTP completa contra el Data API de `MEPIA - PRUEBAS`, ejecutada el
   24-sep-2026 mediante la prueba integral opt-in.
3. ✅ Prueba integral del Paso 1 ejecutada y aprobada el 24-sep-2026.
4. Definir cuándo dejar de aceptar `completed` y `NULL` como estados legacy.
5. Suite general del proyecto ejecutada de nuevo después del Paso 2: 131 pruebas
   aprobadas, 1 prueba de integración omitida por diseño y 17 subpruebas
   aprobadas con el entorno aislado de Python 3.12.14.
6. Comprobar que ningún cambio aumente innecesariamente las llamadas al LLM ni
   rompa el enfoque RAG. Los Pasos 1 y 2 son deterministas y no llaman a un LLM.

**Cierre de la prueba integral del Paso 1 (24-sep-2026):**

- Se agregó `tests/test_chat_grounding_supabase_integration.py`, una prueba opt-in
  con guardas para `ENVIRONMENT=dev`, el identificador exacto del proyecto de
  pruebas y una bandera explícita de ejecución.
- La conexión de solo lectura confirmó 19 filas iniciales en `audit_results`.
- La prueba creó únicamente negocios y filas sintéticas con UUID nuevos. Validó
  dos negocios aislados, dos ejecuciones S3/N14 del mismo día, selección del S3
  más reciente, coincidencia exacta de `source_s3_result_id`, ausencia de fallback
  a un N14 anterior, recuperación de una fila `success` detrás de cinco filas
  `failed`, allowlists y el caso sin auditorías.
- Resultado real de la integración con Python 3.12.14 y `supabase-py==2.31.0`:
  `1 passed`, con dos advertencias de deprecación provenientes del cliente;
  no hubo fallos funcionales.
- El bloque de limpieza eliminó exactamente los UUID creados. La verificación
  independiente posterior confirmó 19 filas en `audit_results`, 0 negocios
  temporales y 0 filas temporales de auditoría.
- La suite general posterior terminó con `118 passed, 1 skipped, 17 subtests
  passed in 40.85s`. El `skip` corresponde exclusivamente a esta prueba opt-in
  cuando no se proporcionan las banderas de integración.
- La restricción inicial de red del entorno y su resolución mediante permiso
  acotado quedaron registradas en `INC-20260924-008`.
- No se consultó ni modificó producción.

## D. Preparación para producción

**Estado:** todo pendiente. Producción todavía no ha sido modificada.

1. Generar un respaldo lógico verificable de producción inmediatamente antes del
   despliegue.
2. Ejecutar consultas previas para contar estados, filas y tamaño real de
   `audit_results`. Si la tabla no es pequeña, separar la creación del índice en
   una operación concurrente compatible con el mecanismo de despliegue; el
   `CREATE INDEX` estándar actual requiere una ventana sin escrituras.
3. Confirmar la versión real del backend y sus dependencias.
4. Detener o evitar escrituras concurrentes sobre `audit_results`.
5. Ejecutar las migraciones `008` y `009` en orden y transaccionalmente.
6. Verificar filas, estados, constraints e índices después de la migración.
7. Desplegar el código solo después de aprobar la prueba integral.
8. Preparar un procedimiento de reversión.

Ninguno de estos pasos está autorizado por el estado actual de esta bitácora.

## E. Fases posteriores del chatbot

Este plan general no debe confundirse con las correcciones anteriores:

1. Datos verificables y grounding S3/N14 — implementado y validado integralmente
   contra el Data API de `MEPIA - PRUEBAS`; las cuatro correcciones iniciales y
   el Trabajo 5 de linaje están terminados.
2. Herramientas deterministas, catálogo completo del motor, glosario acotado y
   prohibición absoluta de cálculo — implementados y probados localmente.
3. **Siguiente acción:** nodo conversacional con respuesta estructurada y rechazo
   cuando falta evidencia.
4. Evaluación offline de exactitud, ausencia de invención, aislamiento y preguntas
   fuera de alcance — pendiente.
5. Endpoint autenticado, autorización por negocio, historial controlado e interfaz
   Chat IA — pendiente.

La **Corrección 3** es un defecto concreto de `_extract_final_report()` dentro del
Paso 1. No es el **Paso 3 del chatbot**, que corresponde al futuro nodo
conversacional.

### Paso 2 — herramientas deterministas — terminado en desarrollo

`ChatQueryTools` recibe exclusivamente un `ChatGroundingPacket`; no consulta
Supabase, no escribe datos y no llama a un proveedor de IA. Expone consultas de
resultados S3/N14, catálogo de métricas, descripciones, glosario y un rechazo
determinista de solicitudes de cálculo.

El catálogo cubre por igualdad exacta las 31 entradas de
`GatekeeperAgent.METRICS` y cuatro cálculos auxiliares reales del motor:
`contribution_margin`, `waste_analysis`, `burn_rate` y `price_inflation`. Los
conceptos se limitan a los necesarios para entender esas métricas; no es un
glosario financiero general. Cada definición declara entradas, unidades, nombres
reales de `CalcResult`, limitaciones y que el dueño del cálculo es S3.

Cada resultado usa el contrato `ChatToolResult` con estados `ok`, `not_found`,
`missing_data`, `invalid_request` o `not_allowed`, y declara siempre
`knowledge_scope="engine_metric_domain"` y `calculation_allowed=false`. Las
herramientas vuelven a aplicar las
allowlists y solo exponen métricas con evidencia S3 o reportes con evidencia N14
de la misma fecha y raíz. Los alias se normalizan por mayúsculas y acentos, pero
no se permiten coincidencias aproximadas. Catálogo y glosario nunca se presentan
como evidencia de un negocio.

La regla de producto es absoluta: el chatbot puede recuperar, explicar y
parafrasear resultados existentes, pero no calcular, recalcular, sumar,
promediar, agregar, derivar comparaciones numéricas, proyectar ni simular. Las
fórmulas del catálogo son texto educativo, no una interfaz ejecutable. Si el
motor no emitió un resultado, se declara ausente y no se reconstruye. El método
`refuse_calculation()` devuelve `not_allowed` sin evidencia ni valor calculado.

Se documentaron sin reinterpretación tres contratos legados:
`operative_cost_margin` es costo diario y no margen porcentual; `health_score`
es margen promedio monetario y no una puntuación compuesta; `inventory_variance`
puede producir varias salidas de merma con prefijo dinámico.

**Registro Git verificado:** rama `codex/chatbot-q4`; `sin commit`, HEAD
`48bdbc4`. Archivos principales: `agents/chat_metric_catalog.py`,
`agents/chat_tools.py`, `agents/chat_grounding.py`,
`tests/test_chat_tools.py`, `tests/test_chat_grounding.py`,
`.kiro/specs/mepia/n15_chat_consulta.md`,
`.kiro/specs/mepia/n15_chat_consulta_tools.md`,
`.kiro/specs/mepia/n15_chat_consulta_catalogo.md`, `.kiro/specs/mepia/_index.md`,
`.kiro/specs/mepia/_glossary.md` y documentación de seguimiento.

**Validación ampliada:** la selección de grounding y herramientas terminó con
`36 passed, 1 skipped, 62 subtests passed`; la omisión es la integración opt-in
con Supabase. La suite general terminó con `141 passed, 1 skipped, 66 subtests
passed in 41.84s`. La cobertura comprueba igualdad exacta con el registro del
Gatekeeper, los 35 contratos, nombres reales y prefijos dinámicos de salida,
limitaciones legadas, rechazo de finanzas generales y rechazo absoluto de
cálculos. Se ejecutó con `-p no:cacheprovider` por `INC-20260924-008`. No se
usaron claves OpenAI/Anthropic, no se accedió a Supabase y no se modificó
producción. Este paso no incorpora RAG; el catálogo es determinista y versionado.

## Registro operativo

| Fecha | Trabajo | Rama | Commit | Archivos | Pruebas y resultado |
|---|---|---|---|---|---|
| 14-sep-2026 | Corrección 1 | `codex/chat-grounding-step1` | `ca96ba9` | 15 archivos; detalle en la sección A | 8/8 locales; validación doble de migración en `MEPIA - PRUEBAS` correcta |
| 14-sep-2026 | Corrección 2 | `codex/chat-grounding-step2` | `abd165b` | `agents/chat_grounding.py`, `tests/test_chat_grounding.py`, `docs/mepia_v4_metricas_diseno.md` | 9/9 relacionadas; regresión e integración en `MEPIA - PRUEBAS` correctas |
| 15-sep-2026 | Continuidad documental | `codex/chat-grounding-step2` | Sin commit; base `abd165b` | `AGENTS.md`, `docs/chatbot_corrections.md`, `docs/mepia_v4_metricas_diseno.md`, `.kiro/specs/mepia/n15_chat_consulta.md` | No se ejecutaron pruebas unitarias porque no cambió código; `git diff --check` sin errores |
| 15-sep-2026 | Corrección 3, cierre documental y bitácora de incidencias | `codex/chat-grounding-step3` | `922ba91` (código y pruebas) | `AGENTS.md`, `.kiro/specs/mepia/n15_chat_consulta.md`, `agents/chat_grounding.py`, `docs/chatbot_corrections.md`, `docs/chatbot_incidents.md`, `docs/mepia_v4_metricas_diseno.md`, `tests/test_chat_grounding.py` | 8/8 grounding y 2/2 migración; 10/10 relacionadas aprobadas (`OK`) |
| 15-sep-2026 | Corrección 4 y cierre documental | `codex/chat-grounding-step4` | `367ab96` (código y pruebas); `f13e2e8` (cierre documental); base `b1aa4ca` | `.kiro/specs/mepia/n15_chat_consulta.md`, `agents/chat_grounding.py`, `docs/chatbot_corrections.md`, `docs/chatbot_incidents.md`, `docs/mepia_v4_metricas_diseno.md`, `tests/test_chat_grounding.py` | 10/10 grounding y 2/2 migración; 12/12 relacionadas aprobadas (`Ran 12 tests in 0.021s`, `OK`) con el runtime de Codex; el intento con `python` no inició (`INC-20260915-002`); `git diff --check` código 0, sin errores de espacios y con advertencias LF→CRLF |
| 15-sep-2026 | Revisión final y sincronización documental antes del Trabajo 5 | `codex/chat-grounding-step4` | `sin commit`; HEAD `f13e2e8` | `docs/chatbot_corrections.md`, `docs/chatbot_incidents.md`, `docs/mepia_v4_metricas_diseno.md` | Suite específica: 12/12 aprobadas (`Ran 12 tests in 0.017s`, `OK`). Suite general: 12 pruebas importables aprobadas y 9 módulos no importados por ausencia de `pytest` (`Ran 21 tests in 0.020s`, `FAILED (errors=9)`); incidencia `INC-20260915-002` actualizada. `git diff --check`: código 0, sin errores de espacios y con advertencias LF→CRLF |
| 15-sep-2026 | Trabajo 5 — linaje exacto S3/N14 | `codex/chat-grounding-step5` | `48bdbc4`; base `855151f` | Código de S3/N05/N06/Layer 3/N14 y grounding; migración `009`, `APPLY_ALL.sql`, pruebas, entorno reproducible y documentación relacionada; corrección incidental de serialización de `reprints` | Suite completa final: 118/118 pruebas y 17 subpruebas aprobadas en 39.22 s con Python 3.12.14; 21/21 específicas aprobadas. Migración 009 ejecutada dos veces correctamente en `MEPIA - PRUEBAS`: 19/19 filas preservadas, 0 históricos enlazados, FK validada e índice único presente. Primer intento PL/pgSQL fallido y resolución en `INC-20260915-007` |
| 24-sep-2026 | Prueba integral del Paso 1 | `codex/chatbot-q4` | `sin commit`; HEAD `48bdbc4` | `tests/test_chat_grounding_supabase_integration.py` y documentación relacionada | Data API real de `MEPIA - PRUEBAS`: 1/1 integración aprobada; limpieza verificada con 19 filas originales, 0 negocios temporales y 0 auditorías temporales. Suite general: 118 aprobadas, 1 integración opt-in omitida y 17 subpruebas aprobadas en 40.85 s. Incidencia de entorno resuelta: `INC-20260924-008` |
| 24-sep-2026 | Paso 2 y Corrección 5 | `codex/chatbot-q4` | `sin commit`; HEAD `48bdbc4` | `agents/chat_tools.py`, refuerzo de grounding, pruebas y specs N15; detalle en sección E | Focalizadas: 26 aprobadas y 13 subpruebas con pytest; 26/26 con unittest. Suite general: 131 aprobadas, 1 integración opt-in omitida y 17 subpruebas aprobadas en 41.43 s. `INC-20260924-008` actualizada por caché de pytest |
| 24-sep-2026 | Ampliación del Paso 2: dominio completo y no cálculo | `codex/chatbot-q4` | `sin commit`; HEAD `48bdbc4` | Nuevo catálogo de 35 métricas, glosario acotado, política y rechazo determinista, pruebas y tres specs N15 | Focalizadas: 36 aprobadas, 1 integración opt-in omitida y 62 subpruebas. Suite general: 141 aprobadas, 1 omitida y 66 subpruebas en 41.84 s; sin DB, LLM ni producción |
