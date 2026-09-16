# Bitácora oficial de incidencias del chatbot de MEPIA

Este documento registra problemas ocurridos durante el desarrollo, las pruebas,
la documentación o la publicación del chatbot. Es distinto de
[`chatbot_corrections.md`](chatbot_corrections.md), que registra defectos y
trabajos planificados del producto.

No incluir contraseñas, API keys, tokens, cadenas de conexión completas, datos
personales ni otra información sensible. Cuando la fecha exacta o la causa no
estén demostradas, indicarlo expresamente en lugar de inferirlas.

## Cuándo registrar una incidencia

Registrar una incidencia cuando un error bloquee el trabajo, obligue a cambiar de
entorno, dependencia o procedimiento, produzca un resultado inesperado en una
migración o consulta, impida publicar o desplegar por permisos, revele diferencias
entre entornos, requiera un workaround o pueda repetirse y aportar aprendizaje.

No registrar fallos intencionales de pruebas negativas, advertencias inocuas,
reintentos normales sin impacto ni errores tipográficos sin consecuencias. Si se
descubre nueva evidencia, actualizar la incidencia existente en vez de duplicarla.

Estados permitidos: `abierta`, `mitigada`, `resuelta` y `pendiente externo`.

## INC-20260915-001 — Database Branching requería Supabase Pro

- **Fecha:** 15-sep-2026 (fecha de registro; fecha exacta del incidente no
  documentada).
- **Trabajo o corrección relacionada:** Corrección 1; validación aislada de la
  migración 008.
- **Rama:** `codex/chat-grounding-step1`.
- **Categoría:** Supabase.
- **Severidad:** bloqueante.
- **Acción:** Crear una rama de base de datos para probar la migración sin afectar
  producción.
- **Síntoma:** Supabase solicitó una suscripción Pro para utilizar Database
  Branching.
- **Impacto:** El procedimiento elegido no podía continuar en el plan disponible.
- **Causa:** Confirmada: Database Branching requería una suscripción Pro. No se
  documenta una causa más específica.
- **Solución o alternativa:** Se creó y utilizó un proyecto gratuito aislado
  llamado `MEPIA - PRUEBAS`.
- **Evidencia de resolución:** La migración 008 se ejecutó dos veces en el proyecto
  aislado; preservó 13/13 filas sintéticas, dejó 0 estados inválidos, instaló el
  constraint esperado y conservó los 2 índices requeridos.
- **Estado:** resuelta.
- **Acción preventiva:** Confirmar las funciones disponibles en el plan de
  Supabase antes de diseñar una estrategia de pruebas basada en branching y
  mantener una alternativa aislada sin datos de producción.
- **Archivos o commits relacionados:**
  `supabase/migrations/008_audit_results_runtime_contract.sql`,
  `supabase/migrations/APPLY_ALL.sql`, commit `ca96ba9`.

## INC-20260915-002 — El Python local no estaba listo para ejecutar las pruebas

- **Fecha:** 15-sep-2026 (fecha de registro; fecha exacta del incidente no
  documentada).
- **Trabajo o corrección relacionada:** Correcciones 3 y 4, revisión final y
  Trabajo 5; ejecución de las pruebas de grounding, migración, persistencia de
  linaje y suite general.
- **Ramas:** `codex/chat-grounding-step3`, `codex/chat-grounding-step4` y
  `codex/chat-grounding-step5`.
- **Categoría:** dependencias.
- **Severidad:** bloqueante.
- **Acción:** Ejecutar la suite relacionada con el intérprete Python inicialmente
  disponible.
- **Síntoma:** En la Corrección 3, Python 3.14 produjo `ModuleNotFoundError` porque
  `pydantic` no estaba instalado. En la Corrección 4, el comando `python` no fue
  reconocido porque el ejecutable no estaba disponible en el `PATH`. En la
  revisión final, el runtime incluido con Codex no pudo importar nueve módulos de
  la suite general porque no tenía instalado `pytest`. En el Trabajo 5, Python
  3.14 volvió a no importar grounding porque no tenía `pydantic`; el runtime de
  Codex ejecutó las suites específicas, pero sigue sin `pytest` ni `hypothesis`.
- **Impacto:** Las pruebas no podían iniciar con el intérprete local disponible en
  cada worktree. La suite específica de las correcciones sí pudo ejecutarse, pero
  la suite general no pudo completarse en este entorno.
- **Causa:** Confirmada para cada intento: en la Corrección 3, el entorno Python
  3.14 no tenía `pydantic`; en la Corrección 4, no había un ejecutable `python`
  resoluble desde el `PATH`; en la revisión final, el runtime de Codex no incluía
  `pytest` y no se encontró otro intérprete o entorno virtual local utilizable.
- **Solución o alternativa:** Primero se utilizó el runtime de Python incluido con
  Codex para la suite específica. Durante el Trabajo 5 se creó después un entorno
  virtual temporal y aislado con Python 3.12.14, se instalaron las dependencias
  declaradas y `pytest`, y se agregó `api/requirements-dev.txt` para hacer
  reproducible la preparación del entorno de pruebas sin modificar el Python del
  sistema.
- **Evidencia de resolución:** Para la Corrección 3, la ejecución posterior terminó
  con 8/8 pruebas de grounding y 2/2 de migración aprobadas; 10/10 en total
  (`OK`). Para la Corrección 4, el runtime incluido con Codex ejecutó 10/10 pruebas
  de grounding y 2/2 de migración; 12/12 en total (`Ran 12 tests in 0.021s`,
  `OK`). En la revisión final se repitió esa suite: 12/12 aprobadas
  (`Ran 12 tests in 0.017s`, `OK`). El descubrimiento general alcanzó 21 pruebas,
  aprobó las 12 importables y terminó con 9 errores de importación por ausencia de
  `pytest` (`FAILED (errors=9)`). En el Trabajo 5, el comando mínimo con Python
  3.14 ejecutó 4 pruebas de migración y terminó con un error de importación de
  grounding por ausencia de `pydantic` (`Ran 5 tests`, `FAILED (errors=1)`). El
  runtime de Codex aprobó 13/13 pruebas de grounding, 4/4 de migración y 4/4 de
  persistencia de linaje; 21/21 en total (`Ran 21 tests in 0.038s`, `OK`). La
  comprobación inicial de dependencias reportó `pydantic=True`, `pytest=False` e
  `hypothesis=False` en el runtime, y las tres ausentes en Python local. En el
  entorno aislado posterior, la primera suite general recopiló 118 pruebas y
  terminó con 112 aprobadas y 6 fallidas por una inconsistencia histórica no
  relacionada con el Trabajo 5 (`INC-20260915-006`). Tras corregirla, la suite
  completa sin caché terminó con 118/118 pruebas y 17 subpruebas aprobadas en
  39.18 s.
- **Estado:** resuelta.
- **Acción preventiva:** Comprobar el intérprete y sus dependencias antes de correr
  la suite, usar el runtime incluido con Codex cuando el entorno local no cumpla
  los requisitos y declarar las dependencias de desarrollo necesarias para la
  suite general, incluido `pytest`.
- **Archivos o commits relacionados:** `agents/chat_grounding.py`,
  `api/requirements-dev.txt`, `tests/test_chat_grounding.py`,
  `tests/test_audit_results_migration.py`; commit
  `922ba91` para la Corrección 3; commits `367ab96` (código y pruebas) y
  `f13e2e8` (cierre documental) para la Corrección 4 en la rama
  `codex/chat-grounding-step4`; Trabajo 5 `sin commit`, base `855151f`, en
  `codex/chat-grounding-step5`.

## INC-20260915-003 — Push de step2 rechazado con HTTP 403

- **Fecha:** 15-sep-2026 (fecha de registro; fecha exacta del incidente no
  documentada).
- **Trabajo o corrección relacionada:** Corrección 2; publicación de la rama.
- **Rama:** `codex/chat-grounding-step2`.
- **Categoría:** Git.
- **Severidad:** bloqueante.
- **Acción:** Ejecutar el push de `codex/chat-grounding-step2`.
- **Síntoma:** El remoto respondió HTTP 403.
- **Impacto:** La rama no pudo publicarse en `aalm2005/Mepia_clean`.
- **Causa:** Confirmada: la cuenta utilizada no tiene permiso de escritura sobre
  ese repositorio. El identificador se omite por sanitización.
- **Solución o alternativa:** Pendiente: obtener permiso de escritura o publicar
  mediante un fork.
- **Evidencia de resolución:** No existe evidencia de resolución; el bloqueo de
  publicación continúa.
- **Estado:** pendiente externo.
- **Acción preventiva:** Verificar permisos de escritura del remoto antes de
  iniciar una publicación y acordar previamente si se utilizará un fork.
- **Archivos o commits relacionados:** commit `abd165b`; no hay archivos locales
  que resuelvan el permiso externo.

## INC-20260915-004 — Error de sintaxis al cargar la migración 008 en Supabase

- **Fecha:** 15-sep-2026 (fecha de registro; fecha exacta del incidente no
  documentada).
- **Trabajo o corrección relacionada:** Corrección 1; validación de la migración
  008 en `MEPIA - PRUEBAS`.
- **Rama:** `codex/chat-grounding-step1`.
- **Categoría:** Supabase.
- **Severidad:** bloqueante.
- **Acción:** Ejecutar la migración 008 en el editor SQL de Supabase.
- **Síntoma:** El editor reportó un error de sintaxis relacionado con el texto
  cargado.
- **Impacto:** La ejecución no aplicó la normalización en ese intento.
- **Causa:** Confirmada únicamente al nivel disponible: el error estaba relacionado
  con el texto cargado en el editor SQL. No existe evidencia documental para una
  causa más específica.
- **Solución o alternativa:** Se comprobó primero que la fila seguía en su estado
  inicial, se corrigió la carga del texto y se volvió a ejecutar la migración.
- **Evidencia de resolución:** La migración terminó correctamente; la fila de
  prueba pasó de `pending` a `partial` y la validación final reportó 0 estados
  inválidos.
- **Estado:** resuelta.
- **Acción preventiva:** Verificar que el editor contenga el archivo completo y
  sin alteraciones antes de ejecutar; tras cualquier error, comprobar el estado de
  los datos antes de reintentar.
- **Archivos o commits relacionados:**
  `supabase/migrations/008_audit_results_runtime_contract.sql`, commit `ca96ba9`.

## INC-20260915-005 — Validación HTTP del Data API sin credenciales locales

- **Fecha:** 15-sep-2026 (fecha de registro; fecha exacta del incidente no
  documentada).
- **Trabajo o corrección relacionada:** Corrección 2; validación HTTP end-to-end
  contra el Data API de `MEPIA - PRUEBAS`.
- **Rama:** `codex/chat-grounding-step2`.
- **Categoría:** entorno.
- **Severidad:** no bloqueante.
- **Acción:** Ejecutar una llamada HTTP end-to-end al Data API.
- **Síntoma:** No había credenciales disponibles en el entorno local.
- **Impacto:** No pudo comprobarse el recorrido HTTP completo.
- **Causa:** Confirmada: las credenciales necesarias no estaban disponibles en el
  entorno local. No se documenta una causa más específica.
- **Solución o alternativa:** PostgreSQL y la construcción de la consulta se
  validaron por separado; la llamada HTTP completa quedó pendiente.
- **Evidencia de resolución:** No existe resolución end-to-end. Las validaciones
  separadas están registradas, pero no sustituyen la llamada HTTP pendiente.
- **Estado:** pendiente externo.
- **Acción preventiva:** Preparar credenciales de prueba con alcance mínimo en el
  entorno autorizado antes de planear la validación HTTP, sin copiarlas a la
  bitácora ni al repositorio.
- **Archivos o commits relacionados:** `agents/chat_grounding.py`, commit
  `abd165b`.

## INC-20260915-006 — Prueba de reimpresiones desfasada respecto al modelo vigente

- **Fecha:** 15-sep-2026.
- **Trabajo o corrección relacionada:** Validación de regresión completa durante
  el Trabajo 5; defecto histórico no causado por el linaje S3/N14.
- **Rama:** `codex/chat-grounding-step5`.
- **Categoría:** pruebas y persistencia.
- **Severidad:** media.
- **Acción:** Ejecutar la suite general después de instalar todas sus
  dependencias.
- **Síntoma:** 6 de 118 pruebas fallaron al construir `ShiftAuditEvent` con
  `reprints=2`; Pydantic rechazó el entero porque el modelo vigente exige una
  lista de `ReprintRecord`.
- **Impacto:** La suite general no podía quedar verde. La inspección adicional
  mostró además que la persistencia enviaba objetos Pydantic directamente en la
  columna JSONB de reimpresiones.
- **Causa:** Confirmada en la base `855151f`: el modelo había cambiado de entero a
  `list[ReprintRecord]`, pero el fixture de `tests/test_persist_ingestion.py` no se
  actualizó y `_persist_shift_audit_events()` no convertía esos modelos a JSON.
- **Solución o alternativa:** Se actualizó el fixture con dos
  `ReprintRecord`, se agregó una aserción del JSON persistido y se serializan los
  registros mediante `model_dump(mode="json")` antes del `upsert`.
- **Evidencia de resolución:** La suite focalizada aprobó 23/23 pruebas; la suite
  completa final aprobó 118/118 pruebas y 17 subpruebas en 39.22 s.
- **Estado:** resuelta.
- **Acción preventiva:** Cuando cambie un contrato Pydantic destinado a JSONB,
  actualizar simultáneamente fixtures y pruebas de serialización, no solo las
  anotaciones del modelo.
- **Archivos o commits relacionados:** `agents/api_ingest.py`,
  `tests/test_persist_ingestion.py`; sin commit, base `855151f`.

## INC-20260915-007 — DDL directo no válido dentro del bloque PL/pgSQL de la migración 009

- **Fecha:** 15-sep-2026.
- **Trabajo o corrección relacionada:** Trabajo 5; validación de la migración 009
  en `MEPIA - PRUEBAS`.
- **Rama:** `codex/chat-grounding-step5`.
- **Categoría:** Supabase y migraciones.
- **Severidad:** bloqueante para la migración, sin pérdida de datos.
- **Acción:** Ejecutar la migración 009 endurecida en PostgreSQL real.
- **Síntoma:** Supabase devolvió `ERROR 42601`, error de sintaxis cerca de
  `TABLE`, en el `ALTER TABLE` situado dentro del `IF` del bloque `DO`.
- **Impacto:** La primera ejecución se detuvo después de crear únicamente la
  columna nullable `source_s3_result_id`; no creó la FK ni el índice y no cambió
  ninguna de las 19 filas existentes.
- **Causa:** Confirmada: el DDL condicional se escribió como `ALTER TABLE`
  directo dentro del bloque PL/pgSQL. `pglast` validó el SQL exterior, pero no el
  contenido del cuerpo `DO`, que recibe como una cadena.
- **Solución o alternativa:** El `ALTER TABLE ... ADD CONSTRAINT` condicional se
  ejecuta mediante `EXECUTE $ddl$ ... $ddl$` tanto en la migración incremental
  como en `APPLY_ALL.sql`. La prueba contractual exige ahora esa forma.
- **Evidencia de resolución:** Las 21 pruebas específicas aprobaron después del
  cambio. La migración corregida terminó correctamente en `MEPIA - PRUEBAS` y se
  ejecutó una segunda vez sin error. La verificación final reportó columna UUID,
  FK validada con `ON DELETE SET NULL`, el índice btree esperado, 19/19 filas
  preservadas, 0 enlaces históricos, 1 FK y 1 índice.
- **Estado:** resuelta.
- **Acción preventiva:** Validar siempre los cuerpos PL/pgSQL en una instancia
  PostgreSQL real; un parser SQL exterior no sustituye esa prueba.
- **Archivos o commits relacionados:**
  `supabase/migrations/009_audit_results_s3_lineage.sql`,
  `supabase/migrations/APPLY_ALL.sql`,
  `tests/test_audit_results_migration.py`; sin commit, base `855151f`.
