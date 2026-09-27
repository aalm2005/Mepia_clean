# N15 — Herramientas deterministas de consulta

**Capa:** Aplicación | **Anterior:** `ChatGroundingPacket` | **Siguiente:** nodo conversacional
**Archivos relacionados:** `n15_chat_consulta.md`,
`n15_chat_consulta_catalogo.md`, `_glossary.md`, `agents/chat_tools.py`

## Input / Output

- Input: un `ChatGroundingPacket` ya validado.
- Operaciones de datos: `list_metrics`, `get_metric` y `get_final_report`.
- Operaciones de conocimiento: `list_metric_catalog`, `describe_metric` y
  `lookup_glossary`; rechazo: `refuse_calculation`.
- Output: `ChatToolResult` con estado, datos permitidos, evidencia y faltantes.
- No consulta base de datos, no escribe y no llama a un LLM.

## User Stories

- Como futuro nodo LLM, quiero herramientas independientes del proveedor.
- Como auditor, quiero que cada cifra o reporte conserve su evidencia exacta.
- Como usuario, quiero saber explícitamente cuando un dato no existe.
- Como sistema, quiero que un selector ambiguo no elija datos por aproximación.
- Como sistema, quiero impedir cualquier cálculo aunque la pregunta incluya
  operandos suficientes.

## Acceptance Criteria

- WHEN se listan métricas THEN solo salen campos de `CalcResult` permitidos.
- WHEN se consulta una métrica THEN acepta identificador, alias o nombre real de
  `CalcResult` mediante coincidencia exacta normalizada.
- WHEN se filtra por status THEN solo acepta los cinco estados de `CalcResult`.
- WHEN se consulta N14 THEN solo devuelve el reporte o una sección autorizada.
- WHEN S3/N14 no tienen evidencia de la misma raíz y fecha THEN no expone datos.
- WHEN un selector es inválido o no existe THEN el estado lo distingue sin lanzar
  una consulta externa.
- WHEN se consulta el catálogo o glosario THEN se limita al dominio de métricas
  del motor y `evidence` queda vacía.
- WHEN se solicita un cálculo THEN retorna `not_allowed`, no ejecuta fórmulas y
  no fabrica un resultado.
- WHEN se retorna cualquier resultado THEN declara
  `calculation_allowed=false` y `knowledge_scope="engine_metric_domain"`.
- WHEN se retorna información THEN se entregan copias profundas para impedir que
  una llamada altere las siguientes.

## Edge Cases

- Status desconocido o selector vacío: `invalid_request`.
- Métrica o sección válida pero ausente: `not_found`.
- Paquete sin fuente: `missing_data` y `data` vacío.
- Alias con mayúsculas o acentos: coincidencia normalizada exacta.
- Alias parcial: no hay coincidencia aproximada.
- Fórmula explicativa: texto educativo, nunca una operación ejecutable.
- Resultado no emitido por S3: ausente; no se deriva de otras métricas.

## Archivos relacionados de este nodo

- `n15_chat_consulta_catalogo.md` — cobertura y prohibición absoluta de cálculo.
- `_glossary.md` — contratos de herramientas, métricas y conceptos.
- `agents/chat_tools.py` — implementación sin proveedor de IA.
- `tests/test_chat_tools.py` — allowlists, evidencia, alias y mutabilidad.
