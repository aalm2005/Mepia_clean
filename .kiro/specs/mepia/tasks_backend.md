# Tasks Backend — MEPIA Pipeline Completo

## Estado del análisis

Las tareas de implementación siguientes están marcadas como realizadas y sus
componentes existen en el repositorio: ingesta, gatekeeper, cálculo, diagnóstico,
orquestación, gastos y Layer 3. N07/N08/N12 se omiten deliberadamente en v1.
Estos checks son registro de implementación, no una nueva ejecución de pruebas.

Al 15-oct-2026 falta validar el recorrido completo con datos representativos en
el entorno de presentación y cerrar los controles de producción. El perfil
exclusivo del chat no sirve carga/auditoría. Véase [estado actual](../../../docs/estado_actual_mepia.md).

---

## Fase 4 — S1: Ingesta de Documentos

### 4.1 — N01: Parser de POS PDF (`POST /ingest/pos`)
- [x] 4.1.1 Instalar `pdfplumber` en `api/requirements.txt`
- [x] 4.1.2 Crear `agents/pos_parser.py` con función `extract_pos_data(pdf_bytes) -> POSExtractResult`
  - Extraer `date`, `totals.total`, `totals.cash`, `totals.card`, `line_items[]`
  - Calcular `ocr_confidence` por sección (totals, payment_methods, line_items)
  - Umbral 90% para campos obligatorios → `needs_human_review: true` si no alcanza
  - Soporte multi-día: retornar array de N objetos si el PDF contiene N días
  - Deduplicación por SHA-256 + `business_id`
  - _Spec: n01_pos_pdf_input.md_
- [x] 4.1.3 Implementar `POST /ingest/pos` en `api/main.py`
  - Validar MIME (`application/pdf`), tamaño (< 20MB), business_id existe
  - Subir a Supabase Storage en `pos-tickets/{business_id}/{date}/{file_id}.pdf`
  - Persistir en `documents` + `pos_inputs` por cada día detectado
  - Retornar `POSIngestResult[]`
  - _Spec: n01_pos_pdf_input.md_
- [x] 4.1.4 Implementar `PATCH /ingest/pos/{file_id}/review`
  - Actualizar `documents.needs_human_review = false`
  - Crear registro en `pos_inputs` con datos corregidos
  - _Spec: n01_pos_pdf_input.md_

### 4.2 — N02: Parser de Facturas (`POST /ingest/factura`)
- [x] 4.2.1 Instalar `lxml` en `api/requirements.txt`
- [x] 4.2.2 Crear `agents/factura_parser.py`
  - XML CFDI: parseo determinístico con lxml → confianza 100%
    - Mapear `@Fecha`, `@Total`, IVA, `cfdi:Emisor/@Nombre`, `cfdi:Conceptos`, `@Folio`
    - Todo campo fuera del mapeo → `raw_metadata` JSONB
  - PDF: OCR con pdfplumber → umbral 85%
  - Deduplicación por SHA-256 + `business_id`
  - _Spec: n02_facturas_input.md_
- [x] 4.2.3 Implementar `POST /ingest/factura` en `api/main.py`
  - Validar MIME (XML o PDF), tamaño, `document_type` coincide con MIME real
  - Subir a Supabase Storage
  - Persistir en `documents` + `transactions` (con `expense_behavior = null`)
  - Retornar `FacturaIngestResult`
  - _Spec: n02_facturas_input.md_
- [x] 4.2.4 Implementar `PATCH /ingest/factura/{file_id}/review`
  - Validar `FacturaReviewPayload` (Pydantic)
  - Actualizar `documents`, crear `transactions`
  - _Spec: n02_facturas_input.md_

### 4.3 — N03: Human Input Endpoints
- [x] 4.3.1 Implementar `PATCH /transactions/{id}/expense-behavior`
  - Validar `ExpenseBehaviorPayload`
  - Actualizar `transactions.expense_behavior`
  - Disparar re-evaluación de S2 (trigger gatekeeper)
  - Retornar `gatekeeper_triggered: true`
  - _Spec: n03_human_input_endpoints.md_
- [x] 4.3.2 Implementar `GET /transactions/pending-review`
  - Filtrar `transactions` con `expense_behavior IS NULL` por `business_id + date`
  - Incluir `suggested_behavior` por inferencia de `supplier_name`/`concept`
  - _Spec: n03_human_input_endpoints.md_
- [x] 4.3.3 Implementar `POST /cash-counts` y `PUT /cash-counts/{id}`
  - Validar `CashCountPayload`
  - Persistir en `cash_counts`
  - Disparar re-evaluación de S2
  - _Spec: n03_human_input_endpoints.md_
- [x] 4.3.4 Implementar `GET /cash-counts`
  - Retornar conteo del día o `{ cash_count_id: null, status: "pending" }` si no existe
  - _Spec: n03_human_input_endpoints.md_
- [x] 4.3.5 Implementar `POST /daily-context` y `PUT /daily-context/{id}`
  - Validar `DailyContextPayload` con enum estricto de tags
  - Persistir en `daily_context`
  - _Spec: n03_human_input_endpoints.md_

---

## Fase 5 — S2: Gatekeeper

- [x] 5.1 Crear `agents/gatekeeper.py` con clase `GatekeeperAgent`
  - Evaluar cada métrica del catálogo: `daily_break_even`, `cash_reconciliation`,
    `operative_cost_margin`, `health_score`, `inventory_variance`
  - Para cada métrica: consultar datos requeridos en Supabase
  - Verificar `needs_human_review = false` en todos los documentos del día
  - Escribir resultado en `metric_status` (upsert por `business_id + date + metric_name`)
  - Retornar `GatekeeperResult` con `active_metrics[]`, `dormant_metrics[]`, `blocked_metrics[]`
  - _Spec: s2_gatekeeper.md_
- [x] 5.2 Implementar triggers de S2
  - Trigger event-driven: llamar S2 tras INSERT/UPDATE en `transactions` o `pos_inputs`
  - Trigger manual: re-evaluar tras `PATCH /transactions/{id}/expense-behavior`
  - Trigger manual: re-evaluar tras `POST /cash-counts`
  - _Spec: s2_gatekeeper.md_
- [x] 5.3 Implementar `GET /gatekeeper/status`
  - Retornar `GatekeeperResult` actual para `business_id + date`
  - _Spec: s2_gatekeeper.md_

---

## Fase 6 — S3: Motor de Cálculo

- [x] 6.1 Crear `agents/calc_engine.py` con funciones puras (sin LLM)
  - `calc_contribution_margin(product_id, db)` → `CalcResult`
  - `calc_daily_break_even(business_id, date, db)` → `CalcResult`
    - Usar `days_in_month(date)` como divisor, nunca 30 fijo
    - Solo gastos con `expense_behavior` confirmado
  - `calc_waste_analysis(ingredient_id, start_date, end_date, db)` → `CalcResult`
    - Normalizar unidades con tabla `unit_conversions`
  - `calc_burn_rate(business_id, date, db)` → `CalcResult`
  - `check_price_inflation(ingredient_id, db)` → `CalcResult`
  - `calc_cash_reconciliation(business_id, date, db)` → `CalcResult`
    - `expected_cash = initial_float + pos_cash_sales - refunds - cash_payouts`
    - `variance = actual_cash_counted - expected_cash`
  - División por cero o dato faltante → `status: "incomplete_data"`, nunca excepción
  - Solo operar sobre métricas con `status: "active"` del Gatekeeper
  - _Spec: s3_motor_calculo.md_
- [x] 6.2 Implementar normalización de unidades
  - Leer factores de conversión desde tabla `unit_conversions`
  - Unidades incompatibles → `status: "unit_mismatch"`
  - _Spec: s3_motor_calculo.md_
- [x] 6.3 Implementar umbrales de status por métrica
  - Merma: warning > 5%, critical > 10% (condiciones vigentes de S3)
  - Inflación precio: warning 5–15%, critical > 15%
  - Conciliación caja: warning < 0, critical < -1% de ventas
  - Margen contribución: warning < 20%, critical < 10%
  - _Spec: s3_motor_calculo.md_

---

## Fase 7 — S4: Forensic CFO (IA)

- [x] 7.1 Crear `agents/forensic_cfo.py` con clase `ForensicCFOAgent`
  - LLM: `gpt-4o`, temperatura `0`, structured output
  - System prompt del Forensic CFO (ver s4_auditoria_ia.md)
  - Input: `CalcResult[]` + `daily_context.tags` + `business_id` + `date`
  - Output: `ForensicReport` con `anomalies[]`, `risk_level`, `evidence_sources`, `observed_causality`
  - Reglas de `risk_level`: high si ≥1 anomalía high, medium si solo medium, low si no hay
  - `source_discrepancy` siempre `severity: "high"` sin excepción
  - `observed_causality` adjunta tags sin modificar ningún `severity`
  - _Spec: s4_auditoria_ia.md_
- [x] 7.2 Implementar `POST /audit/run` en `api/main.py`
  - Verificar que S3 corrió para `business_id + date` (HTTP 409 si no)
  - Ejecutar S4 y retornar `ForensicReport`
  - _Spec: s4_auditoria_ia.md_

---

## Fase 8 — N05: CEO Orchestrator

- [x] 8.1 Crear `agents/ceo_orchestrator.py`
  - LLM: `gpt-4o`, temperatura `0.3`
  - Coordinar S3 → S4 → síntesis con arquetipo
  - Para cada `AnomalyItem`: aplicar CEO Cognitive Frame del arquetipo
  - Construir query RAG desde anomalías high/medium
  - Llamar `MemoryService.get_context(query, business_id)`
  - Asignar `context_weight` según lógica RAG (amplificado/normal/reducido)
  - Mapear `severity` → `alert_level` (high→critical, medium→warning, low→info)
  - Generar `AuditInsight[]` con `copilot_phrase` + `recommended_action`
  - _Spec: n05_ceo_orchestrator.md_
- [x] 8.2 Implementar lógica de escalación a Layer 2
  - `risk_level: "high"` + `escalate_to_parallel: true` → disparar `POST /layer2/run`
  - Si N06 retorna 503 → `pipeline_status: "failed"`, no reintentar
  - _Spec: n05_ceo_orchestrator.md_
- [x] 8.3 Implementar `POST /orchestrator/run` en `api/main.py`
  - Verificar prerequisitos (business existe, S2 corrió, no hay docs pendientes de review)
  - Ejecutar S3 → S4 → N05 síntesis
  - Persistir en `audit_results` con `node_id: "N05"`
  - Retornar `OrchestratorResult` con `run_id`, `sequential_results`, `escalation`, `dormant_metrics`
  - _Spec: n05_ceo_orchestrator.md_
- [x] 8.4 Implementar `GET /orchestrator/status/{run_id}` en `api/main.py`
  - _Spec: n05_ceo_orchestrator.md_

---

## Fase 9 — N06: Orquestador ADK (Layer 2)

- [x] 9.1 Crear `agents/parallel_orchestrator.py`
  - Instalar `langgraph` en `api/requirements.txt`
  - Implementar scatter-gather con `asyncio.gather`
  - Timeouts independientes por nodo (N07: 15s, N08: 60s, N09: 20s)
  - Usar `time.monotonic()` para medir duración
  - Guard de idempotencia: si `layer2_run_id` ya existe → retornar resultado existente
  - Consolidar en `ParallelGatherResult`
  - Persistir en `audit_results` antes de retornar
  - _Spec: n06_orchestrator_adk.md_
- [x] 9.2 Implementar circuit breaker
  - Consultar `circuit_breaker_state` antes del scatter
  - Si nodo en `circuit_open` → `status: "error"`, `error_detail: "circuit_open"`
  - Actualizar `circuit_breaker_state` tras cada fallo consecutivo
  - _Spec: n06_orchestrator_adk.md_
- [x] 9.3 Implementar `POST /layer2/run` en `api/main.py`
  - _Spec: n06_orchestrator_adk.md_
- [x] 9.4 Implementar `GET /layer2/status/{layer2_run_id}` en `api/main.py`
  - _Spec: n06_orchestrator_adk.md_
- [x] 9.5 Implementar `POST /layer2/circuit-reset` en `api/main.py`
  - _Spec: n06_orchestrator_adk.md_

---

## Fase 10 — N09: Agente de Auditoría Financiera (Layer 2)

- [x] 10.1 Refactorizar `agents/business_health.py` → implementar `N09FinancialAuditAgent`
  - Heurística A: Break-Even + Ciclo de Vida
    - `business_age_months` desde `businesses.opening_date`
    - `costo_fijo_diario = SUM(fixed_costs) / days_in_month(date)`
    - `gasto_variable_dia` desde `transactions` confirmadas del día
    - Clasificar fase: Luna de miel / Valle crítico / Construcción lenta / Break-even zone / Madurez
  - Heurística B: Burn Rate Variable
    - `burn_rate_variable_pct = gasto_variable_dia / total_sales × 100`
    - Umbrales: ok ≤35%, warning 36–50%, critical >50%
    - Reportar valor real aunque supere 100%, nunca capear
  - Heurística C: Detección de Anomalías
    - Caída de ventas vs promedio móvil 7 días (solo días anteriores con ventas > 0)
    - CAPEX sin categorizar
  - LLM `gpt-4o-mini` para `copilot_phrase` (fallback: `copilot_phrase: null`, status sigue "success")
  - Retornar `NodeResult` con `FinancialAuditResult`
  - _Spec: n09_gastos.md_

---

## Fase 11 — MemoryService: Implementación Real

- [x] 11.1 Implementar `MemoryService._get_embedding(text)` en `utils/memory_service.py`
  - Usar `openai.AsyncOpenAI` con modelo `text-embedding-3-small`
  - _Spec: mem_memory_layer.md_
- [x] 11.2 Implementar `MemoryService._search_pgvector(embedding, business_id, limit)`
  - Llamar RPC `match_mepia_memory` en Supabase
  - _Spec: mem_memory_layer.md_
- [x] 11.3 Implementar `MemoryService._insert_chunk(row)`
  - Insertar en tabla `mepia_memory` con `status: "pending_embed"`
  - _Spec: mem_memory_layer.md_
- [x] 11.4 Crear worker de embeddings `utils/embedding_worker.py`
  - Consultar `mepia_memory WHERE status = 'pending_embed'`
  - Generar embedding con OpenAI
  - Actualizar `embedding` + `status = 'embedded'`
  - Marcar `status = 'failed'` tras 3 intentos fallidos
  - _Spec: mem_memory_layer.md_

---

## Fase 12 — Layer 3: N10 Context Builder

- [x] 12.1 Crear `agents/context_builder.py` con función `n10_context_builder_node(state)`
  - Extraer `forensic_report`, `audit_insights`, `calc_results`, `context_tags` de `ParallelGatherResult`
  - Ejecutar SQL rollup según `temporalidad` (short/medium/long)
    - short: `GROUP BY transaction_date`, rango 30 días → `list[ShortPeriodMetrics]`
    - medium: `GROUP BY DATE_TRUNC('week', ...)`, rango 180 días → `list[MediumPeriodMetrics]`
    - long: `GROUP BY DATE_TRUNC('month', ...)`, rango 365 días → `list[LongPeriodMetrics]`
  - Excluir transacciones con `needs_human_review = true`
  - Recuperar `brand_identity` por SQL directo a `mepia_memory` (no semántico)
  - Llamar `MemoryService.get_context(query, business_id, limit=3)` para historial RAG
  - Truncar `historical_context` a 1,500 tokens máximo
  - Construir `EnrichedAuditPayload` tipado
  - Persistir en `audit_results` con `node_id: "N10"` antes de retornar
  - _Spec: n10_context_builder.md_

---

## Fase 13 — Layer 3: N11 Consultor Especialista

- [x] 13.1 Crear `agents/core_auditor.py` con función `n11_consultor_node(state)`
  - LLM primario: `claude-3-5-sonnet-20241022` (Anthropic)
  - LLM fallback: `gpt-4o` (OpenAI) vía `with_fallbacks()`
  - Temperatura dinámica: 0.7 primer intento, 0.3 en reintento
  - Inyectar `feedback_critico` al final del `HumanMessage` si existe
  - System prompt con las 4 directivas (ver n11_consultor.md)
  - Mapeo de `temporalidad` → enfoque analítico (short/medium/long)
  - Output: `DraftReport` con `executive_summary`, `operational_narrative`, `pragmatic_actions[1–3]`
  - Persistir en `audit_results` con `node_id: "N11"`
  - Idempotencia: mismo `layer3_run_id` → retornar resultado existente
  - _Spec: n11_consultor.md_
- [x] 13.2 Implementar `POST /api/audit/test/n11_consultor` (solo testing)
  - _Spec: n11_consultor.md_

---

## Fase 14 — Layer 3: N14 Informe Final

- [x] 14.1 Crear `agents/n14_informe_final.py` con función `n14_informe_final_node(state)`
  - Python puro, sin LLM
  - Extraer `DraftReport` aprobado del estado
  - Formatear `operational_narrative` a Markdown con header y footer
  - Si `draft_status == "approved_with_warning"` → agregar bloque de advertencia
  - Propagar `model_used` desde `DraftReport` sin modificar
  - Construir `FinalReport` con `quality_warnings` del `historial_feedback`
  - Persistir en `audit_results` con `node_id: "N14"`
  - Actualizar estado con `layer3_status: "completed"`
  - _Spec: n14_informe_final.md_

---

## Fase 15 — Layer 3: Grafo LangGraph

- [x] 15.1 Crear `agents/layer3_graph.py`
  - Instanciar `StateGraph(Layer3State)`
  - Registrar nodos: N10, N11, N13, N14
  - Flujo: N10 → N11 → N13 → (conditional) → N14 o N11
  - `n13_conditional_edge`: approved/approved_with_warning → N14, rejected → N11
  - Exportar `layer3_app = build_layer3_graph(memory_service)`
  - Prohibido instanciar `StateGraph` fuera de este archivo
  - _Spec: layer3_graph.md_

---

## Fase 16 — API Layer 3

- [x] 16.1 Implementar `POST /api/audit/layer3/run` en `api/main.py`
  - Modo normal: reconstruir contexto desde `audit_results` por `audit_run_id`
  - Modo aislado: usar `business_id`, `date`, `archetype` del body
  - Verificar onboarding completo (HTTP 412 si no hay chunk `node_origin: "onboarding"`)
  - Construir `Layer3State` inicial
  - Ejecutar grafo en `BackgroundTasks`
  - Responder 202 inmediatamente
  - Idempotencia: mismo `audit_run_id` → HTTP 409
  - _Spec: api_layer3.md_
- [x] 16.2 Implementar `GET /api/audit/layer3/status/{layer3_run_id}`
  - Retornar estado actual del grafo (running/completed/failed)
  - _Spec: api_layer3.md_
- [x] 16.3 Implementar `GET /api/audit/layer3/result/{layer3_run_id}`
  - Retornar `FinalReport` completo
  - HTTP 409 si el grafo aún no completó
  - _Spec: api_layer3.md_
- [x] 16.4 Inicializar `MemoryService` y `layer3_app` en startup de FastAPI
  - `memory_service = MemoryService(supabase_client=supabase)`
  - `layer3_app = build_layer3_graph(memory_service)`
  - _Spec: api_layer3.md, layer3_graph.md_

---

## Fase 17 — Tests de Propiedades (PBT)

- [x] 17.1 Instalar `hypothesis` en `api/requirements.txt`
- [x] 17.2 Tests PBT para N01 (POSIngestResult)
  - P1: campos obligatorios siempre presentes
  - P2: `needs_human_review` ↔ campo con confianza < 90%
  - P4: round-trip JSON
  - P5: deduplicación SHA-256
  - _Spec: n01_pos_pdf_input.md §Correctness Properties_
- [x] 17.3 Tests PBT para S3 (CalcEngine)
  - División por cero → `incomplete_data`, nunca excepción
  - Unidades incompatibles → `unit_mismatch`
  - `calc_cash_reconciliation`: fórmula matemática correcta
  - _Spec: s3_motor_calculo.md_
- [x] 17.4 Tests PBT para S4 (ForensicReport)
  - P1: `observed_causality` nunca modifica `severity`
  - P2: `risk_level: "high"` ↔ ≥1 anomalía high
  - P3: `source_discrepancy` siempre `severity: "high"`
  - _Spec: s4_auditoria_ia.md §Correctness Properties_
- [x] 17.5 Tests PBT para N05 (OrchestratorResult)
  - P2: `escalation.triggered: true` → `layer2_run_id` no nulo
  - P6: `severity: "high"` → `alert_level: "critical"` sin excepción
  - _Spec: n05_ceo_orchestrator.md §Correctness Properties_
- [x] 17.6 Tests PBT para N06 (ParallelGatherResult)
  - P1: `node_results` siempre 3 elementos
  - P2: `succeeded + timed_out + failed == 3`
  - P8: idempotencia de `layer2_run_id`
  - _Spec: n06_orchestrator_adk.md §Correctness Properties_
- [x] 17.7 Tests PBT para N09 (FinancialAuditResult)
  - P4: `resultado_operativo = total_sales - costo_fijo - gasto_variable`
  - P10: `costo_fijo_diario` usa `days_in_month`, nunca 30 fijo
  - P12: `burn_rate` nunca capeado
  - _Spec: n09_gastos.md §Correctness Properties_
- [x] 17.8 Tests PBT para N13 (CriticVerdict)
  - P1: `observed_causality` nunca modifica `severity`
  - Cortafuegos: `intentos_critico >= 2` → siempre `approved_with_warning`
  - _Spec: n13_revisor.md_
- [x] 17.9 Tests PBT para Layer 3 Graph
  - P1: el grafo siempre termina (cortafuegos garantiza salida)
  - P3: `draft_status` al llegar a END es `approved` o `approved_with_warning`
  - _Spec: layer3_graph.md §Correctness Properties_

---

## Fase 18 — Integración Frontend ↔ Backend

- [x] 18.1 Actualizar `app/api/upload/route.ts`
  - Handler `POST` para POS → proxy a `POST /ingest/pos`
  - Handler `POST` para factura → proxy a `POST /ingest/factura`
  - Handler `PATCH` para review → proxy a `PATCH /ingest/{type}/{file_id}/review`
- [x] 18.2 Actualizar `app/api/audit/route.ts`
  - `POST /api/audit` → proxy a `POST /orchestrator/run`
- [x] 18.3 Actualizar `hooks/useAuditPolling.ts`
  - Polling a `GET /api/audit/status/{run_id}` → `GET /orchestrator/status/{run_id}`
  - Si `escalation.triggered` → iniciar segundo polling a `GET /api/audit/layer3/status/{layer3_run_id}`
  - Detener polling cuando `status` es `completed | partial | escalated | failed`
- [x] 18.4 Checkpoint de integración end-to-end
  - Flujo completo: onboarding → subir POS PDF → subir factura → analizar → dashboard
  - Verificar que `DormantMetricsList` muestra métricas con datos faltantes
  - Verificar que `PipelineStatusBar` actualiza nodos durante polling
