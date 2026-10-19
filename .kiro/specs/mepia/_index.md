# MEPIA — Índice del Sistema

**Actualización del ensayo — 15-oct-2026:** INC-048/049 resueltas localmente:
guardado terminal N14 y seguimiento por padre con error saneado. 208 pruebas y
41 subpruebas aprobadas, dos advertencias, código 0; proveedores/DB simulados.
OpenAI configurado, Claude opcional mediante respaldo ya existente.
Ver [ejecución y límites](layer3_execution.md) y
[ensayo real pendiente](../../../docs/demo_video_paso_a_paso.md).

**Entorno verificado — 15-oct-2026:** interfaz y servidor completo usan
MEPIA principal; 009/010/011 aplicadas con autorización y datos preservados.
Regresión 178/41 subpruebas, código 0; SQL real 13/13 controles. Usuario confirmó
login y pantallas antes/después del retiro de claves heredadas y firma HS256.
INC-046/047 resueltas en su alcance; INC-048 y ensayo de análisis nuevo pendientes.
Las evaluaciones anteriores conservan su entorno original.
[Ejecución, archivos y límites](../../../docs/database_unification.md).

**Acceso e inicio — 15-oct-2026, validado localmente; sin commit:** sesión por pestaña (recargar conserva; cerrar/abrir pide login), Dashboard como inicio y bienvenida eliminada. API con Bearer y verificación de servidor; cookies antiguas no autentican. [Contrato, pruebas y límites](../../../docs/mepia_access_navigation.md). INC-042 resuelta localmente: Edge 24/24, cero errores; build y tipos código 0. 42 incidencias: 39 resueltas, dos mitigadas y una pendiente externa. Los informes fechados anteriores no validan este cambio.

**GitHub verificado — 15-oct-2026:** avances y sincronización publicados en `codex/chatbot-q4`, commit `2c2ad07754204cf6216483de017dd898b2685255`. Push normal código 0 y hash remoto coincidente. Este registro se guarda en un commit documental posterior. [Estado y evidencia](../../../docs/estado_actual_mepia.md). Los registros previos de «sin commit/push» conservan la situación de su fecha; producción sin cambios.

**Estado documental al 15-oct-2026:** consultar [flujo, avance y pendientes](../../../docs/estado_actual_mepia.md). La sesión identifica y carga el negocio autorizado automáticamente; el selector con un solo negocio aún puede simplificarse. Tutorial guiado pendiente y adaptación móvil parcial. Los registros y conteos fechados siguientes conservan su alcance histórico; la publicación de código no equivale a despliegue.

**Automatización del 14-oct-2026 (histórica, anterior al acceso por pestaña):** ejecutor por capas implementado.
Final local: 43 capas por caso aprobadas, cinco pendientes, cero fallidas,
código 0; no equivale a 43 casos funcionales completos. Regresión 154 pruebas
y 41 subpruebas, dos advertencias, 22.73 s, código 0. Edge sintético: 18
controles, cero errores, código 0; carga 70 POST simulados. Gemini real con
datos/Auth en memoria: siete de ocho casos con controles mecánicos aprobados,
C02 detenido por HTTP 429; 17/18 intentos, código 1, sin reintentos ni juez.
Ocho respuestas validadas para revisión humana, aún sin calificaciones.
INC-040 resuelta localmente, 035 actualizada/resuelta, 041 pendiente externo.
41 incidencias: 38 resueltas, dos mitigadas, una pendiente externa, cero
abiertas. Supabase/cuentas/producción y preview del usuario sin cambios;
sin commit/push. Los avisos siguientes conservan sus registros históricos;
el diseño v1 y su plantilla permanecen intactos, anteriores al ejecutor.
Sigue disponibilidad/C02, revisión humana y ampliar solo lo pendiente.
Ver [ejecutor, resultados y revisión](../../../docs/chatbot_step5_automation.md).

**Diseño original — 14-oct-2026 (histórico, previo al ejecutor):** preparados cinco conjuntos y
48 casos: datos/fuentes (12), lenguaje/límites (10), conversación/historial
(10), seguridad/fallos (10) y preparación para publicación (6). Todos pendientes
de ejecución; no se trasladan aprobaciones anteriores. Primera tanda propuesta:
D01/D03/D05/D06/L01/L07/C01/C02, nueve POST reales como máximo y hasta 18 intentos
Gemini. Plan completo: 36 POST, hasta 72 intentos, cero juez y cero reintentos
SDK; presupuesto habilitado cero. Rúbrica con dos lectores objetivo, oráculos
sintéticos, aislamiento/limpieza y plantilla vacía. Riesgo estático L02
(«qué son») pendiente de comprobar; no es una regresión demostrada. Sin cambios
de producto, modelo, SQL, usuarios, producción, commit o push. Acceso y evaluación
previos siguen cerrados en su alcance. Ejecución funcional amplia pendiente;
OpenAI y publicación separados. Ver [plan detallado](../../../docs/chatbot_step5_test_plan.md).

**Ajuste de lenguaje — 14-oct-2026 (registro anterior a la automatización):** el usuario pidió respuestas
comprensibles sin conocimientos financieros y para diversos niveles de lectura.
Se ajustó la guía común de composición: palabras cotidianas, frases cortas,
tono respetuoso, respuesta directa y breve por defecto; detalles técnicos según
la pregunta. Una definición sencilla omite fórmulas, insumos y alias no pedidos,
conservando condiciones esenciales. Redacción libre, fuentes, cifras/unidades,
alertas y prohibición de calcular intactas. Backend local reiniciado, código 0.
115 pruebas y 41 subpruebas aprobadas, dos advertencias, 11.09 s, código 0;
proveedores simulados. El usuario repitió ticket promedio en una conversación
nueva y confirmó «Sí, ahora es clara»; Next registra POST 200. Es confirmación
humana de legibilidad en esa consulta, no un juicio semántico independiente ni
una medida universal de comprensión. INC-039 resuelta en este alcance;
INC-035 actualizada por atasco del ejecutor en sandbox y ejecución posterior
aprobada fuera de él. 39 incidencias: 37 resueltas, dos mitigadas (023/031),
cero abiertas. Un archivo de producto modificado: `agents/chat_response.py`.
Sin preguntas del agente al modelo, SQL, datos/usuarios, producción, commit
ni push. Evidencias anteriores conservadas; general/build/E2E no repetidos.
Evidencia `docs/evaluations/chatbot_step5_plain_language_20261014.json`.

**Conexión Gemini — 14-oct-2026 (registro anterior al ajuste de lenguaje):** clave Gemini guardada de forma
privada y backend local reiniciado; `api/.env` ignorado por Git. El usuario
envió «¿Qué es el ticket promedio?» y confirmó respuesta; Next registra POST
200 después del 503 previo a configurar. El texto compartido explica el
concepto y fórmula metodológica, cita diez rutas del catálogo y no incluye
el aviso de explicación no validada. Por el contrato de publicación, esa
redacción y sus claims corresponden a generación validada; inferencia desde
la evidencia visible del usuario, sin inspeccionar su sesión ni el JSON real.
Conexión de Gemini `gemini-3.5-flash-lite` confirmada para esta consulta
conceptual; no sustituye la evaluación offline ni valida todos los recorridos
reales. Fecha 2099 comprobada por lectura en MEPIA - PRUEBAS: procede del
fixture histórico `chat_grounding_correction2_test`, conservado; no se corrigió
ni eliminó. Cero preguntas del agente al modelo; una pregunta real del usuario,
con el límite existente de dos intentos por petición, sin reintentos del SDK.
38 incidencias: 36 resueltas, dos mitigadas (023/031), cero abiertas;
INC-035/038 actualizadas y resueltas en su alcance. Sin cambio de código de
producto, SQL administrativo, usuarios/propiedad, producción, commit ni push.
Pruebas anteriores conservadas; no se repitieron suites/build.
Evidencia `docs/evaluations/chatbot_step5_gemini_activation_confirmation_20261014.json`.

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
| S1   | Ingesta (3 inputs)      | Sequential | `s1_ingesta.md`            | Implementada; UI PDF/XML, API y conectores con alcances separados |
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
| EVAL | Set de Evaluación Offline | Transversal | `eval_offline.md`       | Harness y fixtures implementados; resultados históricos en el documento maestro |
| N15  | Chat de consulta fundamentada | Aplicación | `n15_chat_consulta.md` | Pasos 1–4 aceptados en desarrollo; Paso 5 implementado y validación funcional pendiente. Resultados y límites: [estado actual](../../../docs/estado_actual_mepia.md) |

**Continuación acordada de N15:** acceso real del Paso 5 aprobado 29/29;
ingreso general y apertura de Chat IA confirmados por el usuario el 13-oct-2026;
conexión conceptual de Gemini y una definición clara confirmadas el 14-oct.
La matriz local ya se ejecutó: 43 capas aprobadas y cinco pendientes; primera
tanda Gemini 7/8 mecánicos, C02 pendiente externo por cuota y revisión humana
pendiente. Sigue completar solo esas capas y ampliar métricas/lenguaje/historial.
Después integrar OpenAI GPT-6 Luna y validar esa configuración con los mismos casos
y reglas del Paso 4. El modelo todavía no tiene validación real en MEPIA.

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
- **ChatToolResult** → `n15_chat_consulta_tools.md`
- **MetricDefinition** → `n15_chat_consulta_catalogo.md`
- **MetricConceptDefinition / ChatGlossaryEntry** → `n15_chat_consulta_catalogo.md`
- **ChatScopePolicy** → `n15_chat_consulta_catalogo.md`
- **ChatModelDecision / ChatIntentProvider** → `n15_chat_consulta.md`
- **ChatAnswer / ChatAnswerPart** → `n15_chat_consulta.md`
- **ChatSourceFact / ChatModelDraft / ChatReviewResult / ChatValidatedClaim** → `n15_chat_consulta.md`

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
| N03           | `api/main.py` → `/transactions`, `/cash-counts` |
| ONB (configuración N10) | `api/onboarding.py` → `/business/{id}/onboarding[/status]`, registrado en `api.main` y `api.chat_app`; JWT/propiedad; defaults automáticos y costos opcionales |
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
| N15 Chat tools      | `agents/chat_tools.py`                   |
| N15 Chat catalog    | `agents/chat_metric_catalog.py`          |
| N15 Conversation    | `agents/chat_conversation.py`            |
| N15 Free response   | `agents/chat_response.py`                |
| N15 Eval Gemini     | `agents/chat_provider_gemini.py`         |
| N15 Eval OpenAI     | `agents/chat_provider_openai.py`         |
| N15 Offline eval    | `tests/chat_offline_eval.py`             |

## Schema de base de datos

- **Arquitectura híbrida** → `db_schema.md`
- **Compatibilidad de despliegue** → [contrato 011](db_schema_pipeline_contract.md), preparado; aplicación pendiente
- **Datos consultables del motor en N15** → [contrato de consulta](n15_chat_consulta_datos.md)
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
