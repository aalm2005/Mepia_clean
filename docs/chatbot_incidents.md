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
- **Trabajo o corrección relacionada:** Correcciones 3 y 4; ejecución de las
  pruebas de grounding y migración.
- **Ramas:** `codex/chat-grounding-step3` y `codex/chat-grounding-step4`.
- **Categoría:** dependencias.
- **Severidad:** bloqueante.
- **Acción:** Ejecutar la suite relacionada con el intérprete Python inicialmente
  disponible.
- **Síntoma:** En la Corrección 3, Python 3.14 produjo `ModuleNotFoundError` porque
  `pydantic` no estaba instalado. En la Corrección 4, el comando `python` no fue
  reconocido porque el ejecutable no estaba disponible en el `PATH`.
- **Impacto:** Las pruebas no podían iniciar con el intérprete local disponible en
  cada worktree.
- **Causa:** Confirmada para cada intento: en la Corrección 3, el entorno Python
  3.14 no tenía `pydantic`; en la Corrección 4, no había un ejecutable `python`
  resoluble desde el `PATH`.
- **Solución o alternativa:** Se utilizó el runtime de Python incluido con Codex.
- **Evidencia de resolución:** Para la Corrección 3, la ejecución posterior terminó
  con 8/8 pruebas de grounding y 2/2 de migración aprobadas; 10/10 en total
  (`OK`). Para la Corrección 4, el runtime incluido con Codex ejecutó 10/10 pruebas
  de grounding y 2/2 de migración; 12/12 en total (`Ran 12 tests in 0.021s`,
  `OK`).
- **Estado:** resuelta.
- **Acción preventiva:** Comprobar el intérprete y sus dependencias antes de correr
  la suite, y usar el runtime incluido con Codex cuando el entorno local no cumpla
  los requisitos.
- **Archivos o commits relacionados:** `agents/chat_grounding.py`,
  `tests/test_chat_grounding.py`, `tests/test_audit_results_migration.py`; commit
  `922ba91` para la Corrección 3; Corrección 4 en rama
  `codex/chat-grounding-step4`, `sin commit`.

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
