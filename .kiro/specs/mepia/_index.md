# MEPIA — Índice del Sistema

## Pipeline redefinido (Sequential Layer)

```
[CEO Orchestrator Layer]
        ↓
[Layer 1: Sequential — 3 sub-nodos]

  ┌─────────────────────────────────────────────────────────┐
  │ S1: INGESTA (3 inputs)                                  │
  │   POS/API (primaria) + PDF (fallback) → transactions    │
  │   Facturas proveedor → documents + transactions         │
  │   Recipes (BOM) → tabla recipes                         │
  └──────────────────┬──────────────────────────────────────┘
                     ↓
  ┌─────────────────────────────────────────────────────────┐
  │ S2: STAND-BY / GATEKEEPER                               │
  │   Valida integridad de datos por métrica                │
  │   Estado: dormant (faltan datos) → active (set completo)│
  └──────────────────┬──────────────────────────────────────┘
                     ↓
  ┌─────────────────────────────────────────────────────────┐
  │ S3: MOTOR DE CÁLCULO (Python puro)                      │
  │   Cálculos financieros sobre métricas active            │
  │   Output: números crudos sin interpretación             │
  └──────────────────┬──────────────────────────────────────┘
                     ↓
  ┌─────────────────────────────────────────────────────────┐
  │ S4: FORENSIC CFO (IA)                                   │
  │   Input: CalcResult[]                                   │
  │   Diagnóstico forense: fugas, discrepancias, techos     │
  │   Output: ForensicReport — sin recomendaciones          │
  └─────────────────────────────────────────────────────────┘
        ↓
[CEO Orchestrator Layer — N05]
  Recibe ForensicReport + memoria RAG
  Aplica arquetipo CEO → genera AuditInsight[] con copilot_phrase
        ↓
[Layer 2: Parallel]   Orquestador → N09 Gastos (N07/N08 skipped_v1)
        ↓
[Layer 3: Loop/Critic] N10 Context Builder → N11 Consultor → N12 Phrase Expander → N13 Revisor → N14 Informe Final
        ↓
[Application Layer] N15 Chat fundamentado → interfaz Chat IA
```

## Nodos y archivos de spec

| ID   | Nodo                    | Capa       | Archivo                    | Estado      |
|------|-------------------------|------------|----------------------------|-------------|
| S1   | Ingesta (3 inputs)      | Sequential | `s1_ingesta.md`            | 🔧 in dev   |
| S1B  | Ingesta API (primaria)  | Sequential | `s1b_ingesta_api.md`       | ✅ done     |
| N01  | POS PDF Input (fallback)| Sequential | `n01_pos_pdf_input.md`     | ✅ done — fallback, ya no ruta primaria |
| N02  | Facturas Proveedor Input| Sequential | `n02_facturas_input.md`    | ✅ done      |
| N03  | Human Input Endpoints   | Sequential | `n03_human_input_endpoints.md` | ✅ req done |
| S2   | Stand-by / Gatekeeper   | Sequential | `s2_gatekeeper.md`         | ✅ req done  |
| S3   | Motor de Cálculo        | Sequential | `s3_motor_calculo.md`      | ✅ done — extendido con 26 métricas nuevas |
| S4   | Forensic CFO (Auditoría IA) | Sequential | `s4_auditoria_ia.md`       | ✅ done      |
| N05  | CEO Orchestrator (Síntesis Estratégica) | CEO Layer  | `n05_ceo_orchestrator.md`  | ✅ done     |
| N06  | Orquestador ADK         | Parallel   | `n06_orchestrator_adk.md`  | ✅ done     |
| N07  | Conciliación Efectivo   | Parallel   | `n07_conciliacion.md`      | skipped_v1  |
| N08  | Cumplimiento PLD        | Parallel   | `n08_pld.md`               | skipped_v1  |
| N09  | Auditoría Gastos        | Parallel   | `n09_gastos.md`            | ✅ done     |
| N10  | Context Builder (Layer 3)| Loop      | `n10_context_builder.md`   | ✅ done     |
| N11  | Consultor Especialista (Core Auditor) | Loop | `n11_consultor.md`         | ✅ done     |
| N12  | Phrase Expander         | Loop       | `n12_phrase_expander.md`   | skipped_v1  |
| N13  | Revisor de Calidad (Critic & Enforcer) | Loop | `n13_revisor.md` | ✅ done     |
| N14  | Informe Final           | Loop       | `n14_informe_final.md`     | ✅ done     |
| L3G  | Layer 3 Graph           | Loop       | `layer3_graph.md`          | ✅ done     |
| API3 | API Layer 3 Endpoint    | API        | `api_layer3.md`            | ✅ done     |
| COST | Estrategia de Costos    | Transversal| `cost_strategy.md`         | ✅ req done |
| MEM  | Memory Layer            | Transversal| `mem_memory_layer.md`      | ✅ done     |
| AUTH | Autenticación y Autorización | Transversal | `_auth_strategy.md`   | ✅ req done |
| ONB  | Onboarding de Identidad | Transversal| `n10_onboarding_identidad.md` | ✅ req done |
| EVAL | Set de Evaluación Offline | Transversal | `eval_offline.md`       | 🔧 in dev — placeholder |
| N15  | Chat de consulta fundamentada | Aplicación | `n15_chat_consulta.md` | 🔧 in dev — fase 1 completa |

- **POSIngestResult** → `n01_pos_pdf_input.md`
- **FacturaIngestResult** → `n02_facturas_input.md`
- **TicketEvent** → `s1b_ingesta_api.md`
- **ProductLine** → `s1b_ingesta_api.md`
- **PaymentBreakdown** → `s1b_ingesta_api.md`
- **ShiftAuditEvent** → `s1b_ingesta_api.md`
- **InventoryUsageEvent** → `s1b_ingesta_api.md`
- **APIIngestResult** → `s1b_ingesta_api.md`
- **MetricStatus** (dormant/active) → `s2_gatekeeper.md`
- **CalcResult** → `s3_motor_calculo.md`
- **ForensicReport** → `s4_auditoria_ia.md`
- **AuditInsight** → `n05_ceo_orchestrator.md` (generado por N05, no por S4)
- **Enriched_Audit_Payload** → `n10_context_builder.md`
- **DraftReport** → `n11_consultor.md`
- **CriticVerdict** → `n13_revisor.md`
- **FinalResponse** → `n14_informe_final.md`
- **FinalReport** → `n14_informe_final.md`
- **Layer3RunPayload** → `api_layer3.md`
- **Layer3State** → `agents/layer3_state.py`
- **OrchestratorResult** → `n05_ceo_orchestrator.md`
- **AgentResult** → `agents/base_agent.py`
- **MemoryChunk** → `mem_memory_layer.md`
- **ChatGroundingPacket** → `n15_chat_consulta.md`

## Diseño Frontend (Fase 2)

| Archivo | Contenido | Estado |
|---------|-----------|--------|
| `design.md` | Índice del diseño frontend — rutas, principios, decisiones de arquitectura | ✅ req done |
| `design_components.md` | Árbol de componentes React, props, contratos de UI | ✅ req done |
| `design_system.md` | `tailwind.config.ts`, paleta brutalista, tokens de color y tipografía | ✅ req done |
| `design_wireframes.md` | Wireframing lógico de `/dashboard` y `/upload` | ✅ req done |
| `design_flows.md` | Flujo de interacción completo: ingesta → pipeline → pantalla | ✅ req done |

## Archivos de implementación (referencia)

| Spec          | Archivo de código                        |
|---------------|------------------------------------------|
| N01           | `api/main.py` + `agents/pos_parser.py` + `app/api/upload/route.ts`|
| S1B           | `api/main.py` → `POST /ingest/api-event`             |
| N02           | `api/main.py` → `POST /ingest/factura` + `agents/factura_parser.py`|
| N03           | `api/main.py` → `/transactions`, `/cash-counts`, `/onboarding` |
| N05           | `api/main.py` → `POST /orchestrator/run`, `GET /orchestrator/status/{run_id}` |
| N06           | `agents/parallel_orchestrator.py` → LangGraph StateGraph / LCEL RunnableParallel |
| N09           | `agents/business_health.py`                              |
| S2 gatekeeper | `agents/gatekeeper.py`                   |
| S3            | `agents/calc_engine.py`                  |
| S4 forensic CFO     | `agents/forensic_cfo.py`                 |
| N10 context builder | `agents/context_builder.py`              |
| N11 consultor       | `agents/core_auditor.py`                 |
| N13 revisor         | `agents/n13_revisor.py`                  |
| N14 informe final   | `agents/n14_informe_final.py`            |
| Layer 3 Graph       | `agents/layer3_graph.py`                 |
| Layer 3 State       | `agents/layer3_state.py`                 |
| API Layer 3         | `api/main.py` → `POST /api/audit/layer3/run`, `GET /api/audit/layer3/status/{id}`, `GET /api/audit/layer3/result/{id}` |
| MEM MemoryService   | `utils/memory_service.py`                |
| N15 Chat grounding  | `agents/chat_grounding.py`               |

## Schema de base de datos

- **Arquitectura híbrida** → `db_schema.md`
- Tablas: `businesses`, `business_fixed_costs`, `documents`, `transactions`, `pos_inputs`, `cash_counts`, `recipes`, `daily_context` _(deprecated)_, `metric_status`, `unit_conversions`, `audit_results`, `circuit_breaker_state`, `mepia_memory`, `delivery_platform_config`
- JSONB: `extracted_data`, `metadata`, `raw_metadata`, `tags` _(deprecated)_, `ingredients`, `missing_fields`
- Campos clave nuevos: `expense_behavior` (FIXED/VARIABLE/CAPEX), `needs_human_review`, `ocr_confidence`, `raw_metadata`, `multi_sucursal`

## Reglas de carga de contexto

Al implementar un nodo, cargar SOLO:
1. `_index.md` + `_glossary.md`
2. El archivo del nodo específico
3. Los archivos de código directamente relacionados

---

## Arquitectura de LLMs (Decisión fija — V1)

Estrategia híbrida OpenAI + Anthropic. Variables de entorno obligatorias: `OPENAI_API_KEY` + `ANTHROPIC_API_KEY`.

| Nodo | Modelo | Proveedor | Rol |
|------|--------|-----------|-----|
| S4 Forensic CFO | `gpt-4o` | OpenAI | Diagnóstico forense, structured output |
| N05 CEO Orchestrator | `gpt-4o` | OpenAI | Síntesis estratégica con arquetipo |
| N09 Copilot Phrase | `gpt-4o-mini` | OpenAI | Frase de soporte, no crítico |
| N11 Consultor | `claude-3-5-sonnet-20241022` | Anthropic (primario) | Redacción narrativa — el reporte que lee el dueño |
| N11 Fallback | `gpt-4o` | OpenAI | Activado si Anthropic no está disponible |
| N13 Revisor | `gpt-4o` | OpenAI | Verificación matemática, structured output |
