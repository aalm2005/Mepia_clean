# N15 — Chat de consulta fundamentada

**Capa:** Aplicación | **Anterior:** S3/N14 | **Siguiente:** interfaz Chat IA
**Archivos relacionados:** `_glossary.md`, `db_schema.md`,
`n15_chat_consulta_tools.md`, `n15_chat_consulta_catalogo.md`,
`agents/chat_grounding.py`,
`agents/chat_tools.py`

## Input / Output

- Input futuro: `business_id`, pregunta y fecha opcional.
- Fase 1: `ChatGroundingPacket` con S3, N14 enlazado, referencias y faltantes.
- Fase 2: `ChatToolResult` para resultados, catálogo o glosario, con cálculo
  deshabilitado de forma explícita.
- Ningún contrato contiene instrucciones ni campos arbitrarios de JSONB.

## User Stories

- Como dueño, quiero preguntar por mis resultados sin cifras inventadas.
- Como sistema, quiero separar evidencia, consulta y generación de lenguaje.
- Como auditor, quiero rastrear cada respuesta hasta `audit_results`.
- Como negocio, quiero impedir que se mezclen datos entre negocios o ejecuciones.
- Como sistema, quiero explicar solo conceptos de las métricas del motor y nunca
  calcular por cuenta del chatbot.

## Acceptance Criteria

- WHEN se construye el paquete THEN toda consulta SQL filtra por `business_id`.
- WHEN no hay fecha THEN se elige la S3 utilizable más reciente.
- WHEN se recupera N14 THEN coincide en negocio, fecha y `source_s3_result_id`.
- WHEN falta una fuente o su estructura es inválida THEN se declara en
  `missing_data`; nunca se rellena ni se hace fallback.
- WHEN se exponen S3/N14 THEN se aplican sus allowlists y se adjunta evidencia.
- WHEN una herramienta consulta métricas o reporte THEN exige evidencia del
  mismo linaje y fecha antes de exponer contenido.
- WHEN un selector es desconocido THEN retorna `not_found` o `invalid_request`,
  sin coincidencia aproximada.
- WHEN se consulta el glosario THEN usa definiciones curadas y no las presenta
  como evidencia de un negocio.
- WHEN se solicita cualquier cálculo, recálculo, agregación, proyección o
  simulación THEN retorna `not_allowed` sin producir valores.
- WHEN el motor no emitió el resultado THEN se declara ausente y no se deriva de
  otras cifras.

## Fases

1. ✅ Grounding S3/N14 y linaje exacto; validado en `MEPIA - PRUEBAS`.
2. ✅ Herramientas deterministas, catálogo completo del motor y prohibición
   absoluta de cálculo.
3. **Siguiente:** nodo LLM con respuesta estructurada y rechazo sin evidencia.
4. Pendiente: evaluación offline y pruebas de aislamiento.
5. Pendiente: endpoint autenticado e interfaz Chat IA.

## Discrepancias conocidas

- No hay autenticación FastAPI; no se expone endpoint de chat.
- `MemoryService.get_context()` no aporta IDs de fuente y no se usa en N15.
- Las migraciones `008` y `009` aún no se despliegan en producción.

## Edge Cases

- Negocio o fecha sin S3: paquete vacío; N14 no se recupera por separado.
- Varias ejecuciones: se usa la S3 más reciente y solo su N14 exacto.
- Linaje ausente, inválido o conflictivo: el contenido no verificable se rechaza.
- JSONB malformado o sin campos permitidos: fuente marcada como faltante.
- Evidencia de otra fecha o raíz: la herramienta no expone datos.
- Concepto financiero ajeno a las métricas del motor: fuera de alcance.
- Fórmula: se puede explicar conceptualmente, pero nunca ejecutar.
