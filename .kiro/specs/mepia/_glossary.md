# MEPIA — Glosario Compartido

**Distinción de datos vigente:** `audit_results` guarda las métricas S3 y el
informe N14 que consulta N15 con negocio, fecha y raíz S3 coincidentes.
`ChatHistoryStore` conserva conversación temporal en memoria; `mepia_memory`
es memoria semántica del pipeline. Son tres contratos diferentes.
[Consulta del motor y requisito de base compartida](n15_chat_consulta_datos.md).
[Estado de unificación y validación por entorno](../../../docs/database_unification.md).
Los conteos y estados de las ejecuciones fechadas siguientes son históricos.

**Acceso e inicio — 15-oct-2026, validado localmente; sin commit:** sesión por pestaña (recargar conserva; cerrar/abrir pide login), Dashboard como inicio y bienvenida eliminada. API con Bearer y verificación de servidor; cookies antiguas no autentican. [Contrato, pruebas y límites](../../../docs/mepia_access_navigation.md). INC-042 resuelta localmente: Edge 24/24, cero errores; build y tipos código 0. 42 incidencias: 39 resueltas, dos mitigadas y una pendiente externa. Los informes fechados anteriores no validan este cambio.

**Continuidad al 15-oct-2026:** [estado actual](../../../docs/estado_actual_mepia.md).
Los Pasos 1–4 están aceptados; el Paso 5 está implementado con validación
funcional pendiente. Las cifras fechadas conservan su alcance original.

**Estado vigente del chatbot — 14-oct-2026:** Pasos 1–5 implementados en desarrollo local; Paso 4 y seguimiento aceptados. Paso 5 con acceso real aprobado en MEPIA - PRUEBAS (29/29, proveedor simulado); E2E original 8/8, acceso general inicial 13/13 y frontend del equipo integrado 15/15 simulados; presentación 12/12, build final código 0, sin despliegue. Controles de producción separados.

## Términos del dominio

| Término              | Definición |
|----------------------|------------|
| POS_PDF              | Reporte diario de ventas del sistema de punto de venta |
| Ticket diario        | Sinónimo de POS_PDF |
| Metadata             | `business_name`, `period`, `totals` extraídos del POS_PDF |
| SharedHeader         | Subconjunto de Metadata para agentes paralelos: `business_name`, `period`, `totals` |
| CEO Archetype        | Perfil del dueño: `Operative Genius` \| `Product Purist` \| `Growth Hacker` |
| CEO Cognitive Frame  | Lente + blind spots + question set inyectado en system prompt de cada agente |
| Q-Framework          | 5 preguntas del Auditor Agent: constraint, margin leak, ignored data, 3x scale, bottleneck |
| AgentResult          | Output estándar de todo agente: `module`, `raw_result`, `copilot_phrase`, `archetype` |
| Warning              | Señal de anomalía generada por agente paralelo, recolectada para Loop/Critic |
| Informe Final        | Output terminal: expandido, validado, CEO-framed |
| BOM                  | Bill of Materials — Receta técnica de un producto con ingredientes y cantidades |
| expense_behavior     | Clasificación de gasto: `FIXED` \| `VARIABLE` \| `CAPEX` — confirmada vía `PATCH /transactions/{id}/expense-behavior` |
| needs_human_review   | Flag en `documents`: true si OCR < 85% de confianza o campo obligatorio ausente |
| initial_float        | Fondo inicial del cajón al abrir el día |
| raw_metadata         | JSONB en `transactions` con campos extraídos fuera del mapeo obligatorio (future-proofing) |
| multi_sucursal       | Flag en `businesses`: true si el negocio tiene más de una sucursal — habilita `calc_sales_by_branch` en S3 |

## Componentes de infraestructura

| Componente           | Tecnología        | Responsabilidad |
|----------------------|-------------------|-----------------|
| Ingest_Service       | FastAPI           | Valida, persiste, parsea documentos — endpoints en `n01`, `n02`, `n03` |
| Ingesta Worker       | Python + Pydantic | Extrae, valida esquema, infiere category, evalúa confianza OCR |
| Storage              | Supabase Storage  | Persiste PDFs/XML en `pos-tickets/` y `facturas/` |
| mepia.db             | SQLite            | Memoria estructurada: audit_runs, daily_metrics, ceo_insights, warnings_log |
| Memory_Writer        | Python module     | Escribe JSON en mepia.db tras Sequential pipeline |
| Memory_Reader        | Python module     | Lee últimos N días + deltas para Auditor Agent |
| RAG_KB               | Vector store      | Entrevistas de auditores + NIIF |
| Prompt Dictionary    | Python dict/YAML  | Templates de arquetipo para N05 CEO Orchestrator — prohíbe frases genéricas, define lente por arquetipo (Operative Genius, Product Purist, Growth Hacker) |
| Engram               | Binario Go (local)| Memoria de largo plazo (CAS). Requiere compilar el repo Engram y tener el binario en PATH. Configurado como servidor MCP en `.kiro/settings/mcp.json` con `{"command": "engram", "args": ["mcp"]}`. Expone herramientas `search` (read) y `store` (write). |
| MemoryService        | Python (`utils/memory_service.py`) | Wrapper que abstrae pgvector + Engram. Expone `get_context()` (read, todos los agentes) y `store_memory()` (write, solo N12/N13). |
| mepia_memory         | Supabase pgvector | Tabla de embeddings semánticos ("Brain"). Single Source of Truth para RAG. Embedding: `text-embedding-3-small` 1536 dims. FK real a `businesses`. Engram reconstruye desde aquí al reiniciar. |
| Auth Middleware      | FastAPI Dependency | Valida JWT de Supabase Auth. Extrae `user_id` del claim `sub`. Verifica acceso a `business_id`. Ver `_auth_strategy.md`. |

## Base de datos — Tablas

| Tabla                  | Propósito |
|------------------------|-----------|
| `businesses`           | Entidad raíz con `operating_hours` |
| `business_fixed_costs` | Gastos fijos del onboarding con `expense_behavior` y `recurrence` |
| `documents`            | Archivos subidos con `ocr_confidence`, `needs_human_review`, `extracted_data` |
| `transactions`         | Datos financieros con `expense_behavior`, `raw_metadata`, `supplier_name`, `tax_amount` |
| `pos_inputs`           | Ventas diarias POS: `cash_sales`, `card_sales`, `refunds` |
| `cash_counts`          | Conteo físico del cajón: `initial_float`, `actual_counted`, `cash_payouts` |
| `recipes`              | BOM por producto con `sale_price` e `ingredients` (JSONB) |
| `daily_context`        | Tags de contexto del día (JSONB) — ⚠️ **DEPRECATED**: tabla retirada del pipeline |
| `metric_status`        | Estado `dormant`/`active`/`blocked` por métrica, negocio y fecha |
| `unit_conversions`     | Catálogo de conversiones de unidades para el Motor de Cálculo |
| `audit_results`        | Outputs de todos los nodos del pipeline con `pipeline_layer`, `node_id`, `node_status` |
| `mepia_memory`         | Embeddings semánticos para LangChain RAG ("Brain"). FK real a `businesses`. Escritura solo desde N12/N13 vía `MemoryService`. Engram reconstruye desde aquí. |
| `shift_audit_events`   | Eventos de auditoría operativa por turno — cancelaciones, reimpresiones, clock_in/out |
| `inventory_daily`      | Snapshot diario de inventario: consumo teórico, merma, stock, costo unitario |
| `delivery_platform_config` | Comisiones por plataforma de delivery (UberEats, Rappi, DiDi). Config del negocio |

## Campos JSONB clave

| Campo            | Tabla           | Contenido |
|------------------|-----------------|-----------|
| `extracted_data` | `documents`     | Respuesta cruda del agente IA |
| `metadata`       | `transactions`  | Datos extra por tipo de documento |
| `raw_metadata`   | `transactions`  | Todo campo extraído fuera del mapeo obligatorio |
| `tags`           | `daily_context` | `{ clima, equipo, evento, personal, otros }` — ⚠️ DEPRECATED |
| `ingredients`    | `recipes`       | `{ cafe_g: 18, leche_ml: 250 }` |
| `missing_fields` | `metric_status` | Lista de datos faltantes para activar la métrica |
| `metadata`       | `mepia_memory`  | `{ "node_origin": "N12", "date": "YYYY-MM-DD", "chunk_index": 0, "chunk_total": 4 }` |
| `operating_hours`| `businesses`    | `{ open: "08:00", close: "22:00" }` |

## Estados de métricas (Gatekeeper S2)

| Estado    | Significado                                                  |
|-----------|--------------------------------------------------------------|
| `dormant` | Faltan datos. No se calcula en S3.                           |
| `active`  | Set completo. Pasa al Motor de Cálculo.                      |
| `blocked` | Documento pendiente de revisión humana (`needs_human_review`)|

## Status de CalcResult (Motor S3)

| Status            | Significado                                              |
|-------------------|----------------------------------------------------------|
| `ok`              | Dentro de umbrales normales                              |
| `warning`         | En zona de atención                                      |
| `critical`        | Fuera de umbral crítico                                  |
| `incomplete_data` | Faltan datos o división por cero                         |
| `unit_mismatch`   | Unidades incompatibles entre receta y factura            |

## Normalización de unidades

| Unidad origen | Unidad base | Factor |
|---------------|-------------|--------|
| kg            | g           | × 1000 |
| L             | ml          | × 1000 |
| unidad        | unidad      | × 1    |

## Contratos de datos

### DailyContextPayload ⚠️ DEPRECATED
```
# DEPRECATED — daily_context fue retirado del pipeline.
# Endpoint POST /daily-context retorna HTTP 410 Gone.
# Se conserva aquí solo como referencia histórica.
business_id: UUID
date: YYYY-MM-DD
tags: {
  clima: "lluvia" | "calor" | "frio" | null
  equipo: "falla_maquina" | "mantenimiento" | null
  evento: "festivo" | "obra_vial" | "promocion" | null
  personal: "falta_staff" | "capacitacion" | null
  otros: string | null (max 500 chars)
}
```

### FacturaIngestResult
```
file_id: UUID
storage_path: string
extraction_status: "success" | "needs_human_review"
needs_human_review: bool
ocr_confidence: float | null       # null para XML
transaction_id: UUID | null        # null si needs_human_review
extracted_fields: ExtractedFacturaFields | null
missing_fields: string[] | null
```

### TicketEvent (S1B — Ingesta API)
```
order_id: str                       # ID único del ticket en el POS
timestamp: datetime                 # UTC ISO-8601
sucursal_id: str
cajero_id: str | null
mesero_id: str | null
order_type: "Comedor" | "Para llevar" | "Delivery App"
subtotal: Decimal                   # antes de IVA y descuentos
tax: Decimal                        # IVA — debe ser ≈ 16% de subtotal
discounts: Decimal                  # default 0
total_net: Decimal                  # subtotal + tax - discounts
items: ProductLine[]                # detalle de productos (Nivel 2)
```

### ProductLine (S1B — Ingesta API)
```
item_id: str                        # ID del producto en catálogo POS
product_name: str
group: str                          # categoría principal
subgroup: str | null                # subcategoría
variant_modifier: str | null        # modificadores (ej. "extra shot")
unit_price: Decimal                 # precio unitario sin descuento
quantity: int                       # >= 1
item_discount: Decimal              # default 0
```

### PaymentBreakdown (S1B — Ingesta API)
```
order_id: str                       # FK lógico a TicketEvent.order_id
efectivo: Decimal                   # default 0
tarjeta_clip: Decimal               # default 0
uber_eats: Decimal                  # default 0
rappi: Decimal                      # default 0
didi_food: Decimal                  # default 0
cortesia_staff: Decimal             # default 0
tarjetas_lealtad: Decimal           # default 0
```

### ShiftAuditEvent (S1B — Ingesta API)
```
sucursal_id: str
date: date
cancellations: CancellationRecord[]     # motivo, responsable, timing (pre/post comanda)
reprints: int                           # reimpresiones de tickets
shifts: ShiftData[]                     # al menos 1 turno por día
clock_records: ClockRecord[]            # registros de entrada/salida de personal
```

### InventoryUsageEvent (S1B — Ingesta API)
```
ingredient_id: str                  # ID del insumo en catálogo
ingredient_name: str
unit: str                           # unidad base (g, ml, unidad)
consumo_teorico: Decimal            # consumo teórico del día por recetas
waste_recorded: Decimal             # merma registrada manualmente
current_stock: Decimal              # existencia actual
unit_cost: Decimal                  # costo unitario última compra
```

### APIIngestResult (S1B — Ingesta API)
```
business_id: UUID
date: date
sucursal_id: str
tickets_received: int
tickets_persisted: int
tickets_skipped: int                # duplicados (idempotencia)
validation_flags: string[]          # flags de integridad detectados
inventory_records: int
shift_records: int
status: "success" | "partial" | "rejected"
```

### ExpenseBehaviorPayload
```
expense_behavior: "FIXED" | "VARIABLE" | "CAPEX"
confirmed_by: UUID
force: bool (opcional, default false)
```

### CashCountPayload
```
business_id: UUID
date: YYYY-MM-DD
initial_float: Decimal (≥ 0)
actual_counted: Decimal (≥ 0)
cash_payouts: Decimal (≥ 0, default 0)
recorded_by: UUID
```

### OnboardingPayload (DEPRECADO — reemplazado por OnboardingIdentityPayload)
```
# Contrato anterior — solo para referencia histórica
# Ver n10_onboarding_identidad.md para el contrato actual completo
business_name: string
industry_sector: string
currency: string (ISO 4217, default "MXN")
operating_hours: { open: "HH:MM", close: "HH:MM" }
fixed_costs: FixedCostItem[] (mínimo 1)
```

### OnboardingIdentityPayload (contrato actual — reemplaza OnboardingPayload)
```
brand_identity: {
  brand_voice: string (max 500 chars)
  prohibited_recommendations: string[]
  priority_focus: "efficiency" | "quality" | "growth"
}
audit_tolerances: {
  max_cash_discrepancy_pct: float (0–1)   # umbral porcentual de diferencia en caja
  max_cash_discrepancy_abs: Decimal       # umbral absoluto en MXN (se usa el más permisivo)
  margin_warning_threshold: float (0–1)   # margen neto mínimo → warning
  margin_critical_threshold: float (0–1)  # margen neto mínimo → alerta roja
  cost_spike_threshold_pct: float (0–1)   # incremento de costo que dispara alerta
}
expected_cost_structure: ExpectedCostStructure[] (opcional; default []; sin gastos inventados)
audit_rules: {
  red_alert_triggers: string[]            # condiciones que siempre generan alerta roja
  ignored_anomaly_types: string[]         # anomalías aceptadas como normales (default [])
  audit_frequency: "daily" | "weekly"     # default "daily"
}
```
> Spec completo: `n10_onboarding_identidad.md`. GET/POST/PUT N10 con JWT y
> propiedad verificadas en `api/onboarding.py` (ambos perfiles). El body Python
> rechaza campos extra; identidad viene de la sesión y negocio del path.
> GET `settings.expected_cost_structure` usa `amount_per_month` y `tolerance_pct`
> en porcentaje visible; escritura usa `expected_monthly_amount` y decimal 0–1.
> El formulario divide siempre entre 100 al guardar. Defaults automáticos en
> Documentos; personalización avanzada opcional. INC-044/045 resueltas localmente.
> Prerequisito obligatorio para ejecutar Layer 3 — HTTP 412 si no está completo.

### ParallelGatherResult
```
layer2_run_id: UUID
sequential_run_id: UUID
source_s3_result_id: UUID | null  # audit_results.id de la fila S3 raíz
business_id: UUID
date: YYYY-MM-DD
archetype: "Operative Genius" | "Product Purist" | "Growth Hacker"
temporalidad: "short" | "medium" | "long"   # propagado desde OrchestratorRunPayload
node_results: NodeResult[3]     # siempre 3 elementos
summary: {
  total_nodes: 3
  succeeded: int
  timed_out: int
  failed: int
  all_warnings: string[]
}
gather_status: "complete" | "partial" | "failed"
completed_at: datetime
```

### NodeResult
```
node_id: "N07" | "N08" | "N09"
node_name: "conciliacion" | "pld" | "gastos"
status: "success" | "timeout" | "error"
result: AgentResult | null
warnings: string[]
error_detail: string | null     # "circuit_open" si nodo degradado
duration_ms: int
```

### Layer2RunPayload
```
layer2_run_id: UUID
sequential_run_id: UUID
source_s3_result_id: UUID | null  # requerido para linaje verificable; null en legacy/aislado
business_id: UUID
date: YYYY-MM-DD
archetype: "Operative Genius" | "Product Purist" | "Growth Hacker"
temporalidad: "short" | "medium" | "long"   # propagado desde OrchestratorRunPayload
sequential_context: SequentialContext
node_timeouts: {
  n07_conciliacion: int (default 15s)
  n08_pld:          int (default 60s)
  n09_gastos:       int (default 20s)
}
```

### OrchestratorResult
```
run_id: UUID
business_id: UUID
date: YYYY-MM-DD
archetype: "Operative Genius" | "Product Purist" | "Growth Hacker"
pipeline_status: "completed" | "partial" | "escalated" | "failed"
sequential_results: {
  active_metrics: string[]
  calc_results: CalcResult[]
  forensic_report: ForensicReport    # output crudo de S4
  audit_insights: AuditInsight[]     # generados por N05 con arquetipo
}
escalation: { triggered: bool, reason: str | null, layer2_run_id: UUID | null }
dormant_metrics: [{ metric, missing: string[] }]
blocked_metrics: [{ metric, reason: string }]  # pendientes de revisión humana
metric_status_available: bool       # false si el histórico no conserva el estado S2
completed_at: datetime
```

El resultado completo de N05 se conserva en `result_data`, incluido
`sequential_results`, listas dormant/blocked y el linaje S3. La lectura histórica
solo recupera cálculos desde el S3 enlazado explícitamente y del mismo negocio y
fecha; no reconstruye el estado S2 desde datos actuales. Sin ese estado,
`metric_status_available=false`: una lista vacía no acredita activación total.

### AuditRunPayload
Payload de `POST /audit/run` — exclusivo de S4 Forensic CFO. Sin arquetipo.
```
business_id: UUID
date: YYYY-MM-DD
```
> `archetype` vive en `OrchestratorRunPayload` (N05), no aquí.

### POSIngestResult
```
file_id: UUID                    → documents.id
storage_path: string             → documents.storage_path
extraction_status: "success" | "needs_human_review"
needs_human_review: bool
uploaded_at: datetime (UTC ISO-8601)
date: date | null                → fecha de operación del ticket
totals: {
  cash: Decimal
  card: Decimal
  total: Decimal
} | null
payment_methods: {
  cash: Decimal
  card: Decimal
  other: Decimal                 → default 0.00
} | null
line_items: LineItem[] | null    → array de ítems vendidos
ocr_confidence: {
  totals: float | null           → 0.0–1.0. Umbral obligatorio: 0.90
  payment_methods: float | null  → 0.0–1.0. Umbral obligatorio: 0.90
  line_items: float | null       → 0.0–1.0. Umbral permisivo: 0.80
}
missing_fields: string[] | null  → campos que no alcanzaron su umbral
```
> El endpoint retorna `POSIngestResult[]` — un objeto por día detectado en el PDF.
> Spec completo: `n01_pos_pdf_input.md`

### GatekeeperResult
```
business_id: UUID
date: YYYY-MM-DD
active_metrics: string[]
dormant_metrics: [{ metric, missing: string[] }]
blocked_metrics: [{ metric, reason: "needs_human_review" }]
```

### CalcResult
```
metric: string
value: decimal | null
# JSON de Pydantic: decimal puede llegar como string (ej. "0.00").
# El frontend admite number | string | null; convierte solo texto numérico
# finito para presentación/gráficas, sin reescalar porcentajes ni calcular métricas.
unit: string
status: "ok"|"warning"|"critical"|"incomplete_data"|"unit_mismatch"
context: string
```

### ForensicReport (output de S4)
```
business_id: UUID
date: date
risk_level: "low" | "medium" | "high"
anomalies: AnomalyItem[]
evidence_sources: string[]           # fuentes comparadas: ["POS", "facturas", "cash_count"]
observed_causality: DailyContextTags | null  # tags del día adjuntos sin interpretación
generated_at: datetime
```

### AnomalyItem
```
anomaly_id: UUID
type: "margin_leak" | "source_discrepancy" | "operational_ceiling" | "cost_spike" | "other"
description: string          # descripción técnica precisa, sin lenguaje CEO
severity: "low" | "medium" | "high"
quantified_impact: string    # ej. "-320 MXN", "-10% margen", "techo: 180 unidades/día"
data_points: string[]        # evidencia numérica de S3 que sustenta la anomalía
metric_origin: string        # nombre de la CalcResult que originó la anomalía
```

### AuditInsight (generado exclusivamente por N05 CEO Orchestrator — NO hereda de AgentResult)
```
anomaly_ref: UUID                # ID del AnomalyItem origen en ForensicReport
copilot_phrase: string           # frase CEO-framed generada por N05 con arquetipo
archetype: CEO Archetype         # arquetipo aplicado por N05
recommended_action: string       # acción específica con frecuencia o plazo
context_weight: "reducido" | "normal" | "amplificado"
alert_level: "info" | "warning" | "critical"   # mapeado desde AnomalyItem.severity
module: string                   # nombre del módulo auditado (ej. "conciliacion_caja")
raw_result: string               # número crudo de S3 pasado desde ForensicReport.quantified_impact
```

### AgentResult (base — exclusivo para nodos paralelos N07/N08/N09)
```
module: string
raw_result: string
copilot_phrase: string
archetype: "Operative Genius" | "Product Purist" | "Growth Hacker"
```
> Contrato base EXCLUSIVO para los resultados de los agentes paralelos (N07, N08, N09).
> NO es el padre de AuditInsight — ese contrato es independiente y generado por N05.

### MemoryChunk
Payload que N12, N13 o el proceso de onboarding envían a `MemoryService.store_memory()`.
```
business_id: UUID
source_audit_run_id: UUID | null     # null para chunks de onboarding — columna nullable en DB
node_origin: "N12" | "N13" | "onboarding"   # "onboarding" para identidad de marca
date: YYYY-MM-DD
content: string                      # texto completo — MemoryService lo divide en chunks internamente
archetype: "Operative Genius" | "Product Purist" | "Growth Hacker" | null  # null para onboarding
quality_approved: bool               # true si N13 validó el contenido, o true para onboarding
```

### Enriched_Audit_Payload (output de N10 — input de N11)
```
layer3_run_id: UUID              # UUID generado por N10
layer2_run_id: UUID
sequential_run_id: UUID
source_s3_result_id: UUID | null  # audit_results.id de la fila S3 raíz
business_id: UUID
date: date
archetype: "Operative Genius" | "Product Purist" | "Growth Hacker"
temporalidad: "short" | "medium" | "long"
forensic_report: ForensicReport
audit_insights: AuditInsightItem[]
time_series: TimeSeriesRollup
parallel_summary: ParallelNodeSummary
brand_identity: BrandIdentityBlock
historical_context: string       # máx 1,500 tokens
built_at: datetime
build_duration_ms: int
```

### TimeSeriesRollup
```
temporalidad: "short" | "medium" | "long"
date_start: date
date_end: date
granularidad: "dia" | "semana" | "mes"
periodos: ShortPeriodMetrics[] | MediumPeriodMetrics[] | LongPeriodMetrics[]
```

### ShortPeriodMetrics (temporalidad == "short" — últimos 30 días)
```
periodo: date
ingresos: Decimal
gastos_variable: Decimal
gastos_fijos: Decimal
num_transacciones: int
```

### MediumPeriodMetrics (temporalidad == "medium" — últimos 6 meses)
```
periodo: date    # inicio de semana
ingresos: Decimal
egresos: Decimal
ingreso_promedio_semanal: Decimal
```

### LongPeriodMetrics (temporalidad == "long" — último año)
```
periodo: date    # inicio de mes
capex_mes: Decimal
ingresos_mes: Decimal
egresos_mes: Decimal
```

### ParallelNodeSummary
```
n09_available: bool
n09_result: FinancialAuditResult | null
n07_status: "not_implemented_v1" | "success" | "error"
n08_status: "not_implemented_v1" | "success" | "error"
all_warnings: string[]
```

### BrandIdentityBlock
```
retrieved: bool          # false si no hay chunk node_origin="onboarding" en mepia_memory
content: string          # texto del Lente del CEO — recuperado por SQL directo, no RAG
fallback_used: bool      # true si se usó identidad genérica
```
> Recuperado con SQL directo: `WHERE metadata->>'node_origin' = 'onboarding' AND business_id = :id`
> En V1 se inserta manualmente. En versiones posteriores lo genera el onboarding automáticamente.

### DraftReport (output de N11 — input de N12/N13)
```
layer3_run_id: UUID
business_id: UUID
date: date
archetype: "Operative Genius" | "Product Purist" | "Growth Hacker"
temporalidad: "short" | "medium" | "long"
executive_summary: string        # máx 2 frases directas al dueño
operational_narrative: string    # hallazgos traducidos a realidades físicas
pragmatic_actions: PragmaticAction[]  # 1–3 acciones, nunca más
model_used: string
generated_at: datetime
generation_duration_ms: int
draft_status: "draft"            # siempre "draft" — N12/N13 lo validan
```

### PragmaticAction
```
action: string                   # descripción directa, sin jerga corporativa
priority: "immediate" | "this_week" | "this_month"
owner: string                    # quién ejecuta (ej. "barista líder", "dueño")
```

### CriticVerdict (output de N13 — Structured Output del LLM)
```
aprobado: bool
tipos_falla: List["ALUCINACION_MATEMATICA" | "DESVIACION_IDENTIDAD" | "NINGUNA"]
  # Lista — permite detectar múltiples fallas simultáneas en el mismo borrador.
  # Si aprueba: ["NINGUNA"]. Si falla: lista con todas las fallas encontradas.
  # Ej: ["ALUCINACION_MATEMATICA", "DESVIACION_IDENTIDAD"]
  # CORRECCIÓN: campo renombrado de tipo_falla (singular) a tipos_falla (plural)
  # para alinearse con la implementación real en agents/n13_revisor.py (TipoFalla enum).
warning_especifico: string | null   # feedback para N11 si aprobado=false — describe TODAS las fallas
insight_para_memoria: string | null # resumen 2 líneas para mepia_memory si aprobado=true
```
> Retornado por el LLM de N13 con structured output (Pydantic). Nunca texto libre.
> `tipos_falla` es una lista para soportar fallas concurrentes — el LLM puede detectar
> alucinación matemática Y desviación de identidad en el mismo borrador.

### FinalReport (output de N14 — contrato para el endpoint GET /result)
```
layer3_run_id: str
business_id: str
date: str
archetype: str
temporalidad: str
executive_summary: str           # tomado directamente de DraftReport
operational_narrative_md: str    # narrativa en Markdown con headers y bullets
pragmatic_actions: list[dict]    # lista de acciones con priority y owner
draft_status: str                # "approved" | "approved_with_warning"
model_used: str                  # propagado desde DraftReport.model_used
intentos_critico: int            # número de revisiones que requirió el borrador
quality_warnings: list[str]      # historial_feedback si hubo rechazos
finalized_at: str                # ISO-8601 UTC
layer3_duration_ms: int          # duración total del grafo Layer 3
source_s3_result_id: str | null  # audit_results.id de la fila S3 raíz
```
> Generado por N14 de forma determinista. Sin llamadas a LLM.
> Persistido en `audit_results` con `node_id: "N14"`.

### FinalResponse (output de N14 — contrato para el frontend vía GET /result)
```
report_markdown: str             # operational_narrative_md formateado
status: str                      # "approved" | "approved_with_warning"
has_warnings: bool               # True si status == "approved_with_warning"
metadata: {
  generated_at: str              # timestamp UTC ISO-8601 del momento de empaquetado
  audit_trail: List[Dict]        # historial completo de audit_results incluyendo entrada N14
}
```
> `has_warnings` es el flag que el frontend usa para mostrar banner de advertencia al dueño.

### Layer3State (estado del grafo LangGraph — Layer 3)
```
# Trazabilidad (escritas por N10, inmutables)
layer3_run_id: str
layer2_run_id: str          # puede tener prefijo "isolated_" en modo aislado
sequential_run_id: str      # puede tener prefijo "isolated_" en modo aislado
source_s3_result_id: str | null  # null en modo aislado o registros legacy
business_id: str
date: str
archetype: str

# Payload de datos (fuente de verdad para N13)
enriched_payload: dict           # EnrichedAuditPayload serializado

# Borrador (escrito por N11, evaluado por N13)
draft_report: dict | None        # DraftReport serializado

# Control del loop de calidad (escritas por N13)
intentos_critico: int            # default 0
feedback_critico: str | None     # default None — leído por N11 para corregir
historial_feedback: List[str]    # acumulado de todos los warnings — default []
tipos_falla_critico: List[str]   # fallas del último veredicto — default []
draft_status: str                # "pending" | "approved" | "approved_with_warning" | "rejected"

# Auditoría del nodo (escritas por N13 en cada ejecución)
audit_results: List[dict]        # veredictos serializados — default []

# Output terminal (escrito por N14)
final_response: dict | None      # FinalResponse empaquetado — default None
```

### ChatEvidenceReference
```
audit_result_id: str             # audit_results.id
node_id: str                     # "S3" o "N14" en fase 1
date: YYYY-MM-DD
created_at: datetime | null
source_s3_result_id: str | null  # raíz S3 compartida por la evidencia
```

### ChatGroundingPacket
Paquete determinista permitido como evidencia del nodo de consulta N15.
```
business_id: str
requested_date: YYYY-MM-DD | null
resolved_date: YYYY-MM-DD | null
source_s3_result_id: str | null  # audit_results.id de la fila S3 elegida
metrics: list[dict]              # allowlist de CalcResult
final_report: dict | null        # allowlist de FinalReport
evidence: ChatEvidenceReference[]
missing_data: str[]
built_at: datetime
```

### MetricConceptDefinition / ChatGlossaryEntry
Concepto estrictamente necesario para comprender métricas del motor. El segundo
nombre es un alias de compatibilidad del contrato inicial.
```
term: str
display_name: str
definition: str
aliases: list[str]
related_metrics: list[str]       # identificadores de MetricDefinition
```

### MetricDefinition
Definición explicativa de una métrica cuyo cálculo pertenece únicamente a S3.
```
metric_id: str
display_name: str
definition: str
interpretation: str
formula_explanation: str         # texto educativo; nunca ejecutable
inputs: list[str]
units: list[str]
aliases: list[str]
result_metric_names: list[str]   # nombres reales posibles de CalcResult
result_metric_prefixes: list[str]
related_concepts: list[str]
limitations: list[str]
availability: "pipeline" | "engine_support"
calculation_owner: "deterministic_engine"
```

### ChatScopePolicy
Frontera funcional inmutable del chatbot.
```
knowledge_scope: "engine_metric_domain"
calculation_allowed: false
allowed_operations: ["retrieve_existing_engine_results", "explain_engine_metrics", "paraphrase_verified_results"]
prohibited_operations: ["calculate", "recalculate", "aggregate", "derive_numeric_comparison", "project", "simulate"]
```

### ChatToolResult
Salida común de las herramientas deterministas de N15.
```
tool: "list_metrics" | "get_metric" | "get_final_report" | "list_metric_catalog" | "describe_metric" | "lookup_glossary" | "refuse_calculation"
status: "ok" | "not_found" | "missing_data" | "invalid_request" | "not_allowed"
business_id: str
resolved_date: YYYY-MM-DD | null
source_s3_result_id: str | null
data: dict                         # payload allowlisted de la herramienta
evidence: ChatEvidenceReference[] # vacío para catálogo, glosario y rechazo
missing_data: str[]
knowledge_scope: "engine_metric_domain"
calculation_allowed: false
```

### ChatModelDecision / ChatIntentProvider
Contrato de clasificación del Paso 3. El proveedor inyectable recibe un
fragmento de pregunta y los selectores del catálogo encontrados en él, sin datos
del negocio. Solo puede devolver los campos siguientes; cualquier campo
adicional o selector ajeno al fragmento se descarta.
```
kind: "concept" | "result" | "report" | "metrics" | "catalog" | "outside"
selector: str | null
```

### ChatAnswerPart
Respuesta independiente para una parte de la pregunta. La IA puede redactar
libremente después de validar fuentes, cantidades y revisión semántica. Los
mensajes fijos son respaldo cuando no se publica generación validada, salvo
la bienvenida social `greeting` descrita en [N15 saludos](n15_chat_consulta_saludos.md).
```
question_part: str                 # pregunta del usuario como dato
kind: "concept" | "result" | "report" | "metrics" | "catalog" | "calculation" | "outside" | "greeting"
status: "ok" | "not_found" | "missing_data" | "not_allowed" | "outside_domain" | "invalid_request"
message: str                      # redacción libre verificada o respaldo
data: dict                        # vacío salvo cuando status="ok"
evidence: ChatEvidenceReference[]  # referencias exactas de las herramientas
missing_data: str[]
claims: ChatValidatedClaim[]       # afirmaciones y referencias de la redacción
generation_status: "fallback" | "validated"
generation_issues: str[]          # códigos de rechazo, sin prosa del proveedor
generation_diagnostics: str[]     # etapa y causa seguras; sin texto rechazado ni claves
```
Un cálculo solicitado siempre se rechaza y no contiene datos ni evidencia.
Un saludo usa exclusivamente el mensaje social fijo, `status=ok` y
`generation_status=fallback`; todos sus datos, fuentes, claims y diagnósticos
permanecen vacíos. No requiere ni recibe generación del modelo.

### ChatAnswer
Salida del nodo N15, también expuesta por el endpoint autenticado del Paso 5.
El transporte agrega conversation_id; las fuentes del historial no se admiten.
```
business_id: str
resolved_date: YYYY-MM-DD | null
parts: ChatAnswerPart[]
calculation_allowed: false
knowledge_scope: "engine_metric_domain"
```

### ChatSourceFact / ChatNumberSlot
Hecho copiado de la salida de una herramienta con ruta de campo. No es una
inferencia del modelo. Las cantidades son literales de la fuente.
```
source_id: str
scope: "business" | "catalog" | "policy" | "availability"
path: str
label: str
value: JSON
unit: str | null
numbers: [{slot_id: str, literal: str}]
evidence: ChatEvidenceReference[]
```

### ChatModelDraft / ChatDraftClaim
Redacción libre propuesta. Debe cubrir todas las partes sin alterar su estado.
```
parts: [{part_id: str, claims: [{text: str, source_ids: str[]}]}]
```
Cada cantidad se escribe con el valor de `slot_id` entre llaves dobles: si el
ID vale `abc`, se escribe `{{abc}}`. El nodo
sustituye el literal original; no admite cantidades generadas o redondeadas.

### ChatResponseWriter / ChatResponseVerifier
Interfaces inyectables `compose(ChatWritingRequest)` y
`verify(ChatReviewRequest)`. `ChatJsonCompletionAdapter` conecta funciones de
API/SDK sin cambiar los proveedores de otros agentes. La revisión semántica es
una llamada separada. El arnés offline del Paso 4 está implementado y probado
con proveedores simulados y Gemini real. Su revisión interna se distingue del
juicio de otro modelo sobre la respuesta publicada. Las corridas históricas
registraron fallos de generación y cobertura (`INC-20260930-013`); se
conservan en sus informes. El conjunto completo vigente del 9-oct-2026 cubrió
22/22 respondibles, aprobó 548/548 controles y obtuvo 36/36 juicios
independientes favorables en 28 casos/36 partes. El conjunto offline está
aceptado. El seguimiento se cerró el 12-oct-2026 bajo el criterio de reemplazo
autorizado: 12/12 independientes, 161/161 controles y cobertura 5/5, cero
pendientes. Las dos generaciones previas y el reemplazo nuevo conservan sus
versiones de guía; la tercera fallida permanece como histórico. Paso 5 de
autenticación, autorización e interfaz continúa pendiente.

**Historial del seguimiento — 10–12-oct-2026:** los siguientes estados
son registros de las ejecuciones anteriores al cierre auditado.

Actualizacion del 10-oct: primer intento de consistencia con generacion
3/3 validada, 2/2 cobertura y 45/45 controles; juez 503/UNAVAILABLE,
cero juicios y tres pendientes. La unica llamada adicional autorizada del juez
ya se ejecuto y tambien devolvio 503/UNAVAILABLE: ambos errores se conservan,
cuatro generaciones y dos llamadas del juez (seis API historicas), sin regenerar.
Serie detenida, tres pendientes. El tercer intento autorizado el 11-oct ya
se ejecuto: una llamada Flash, cero generaciones/reintentos, tambien 503.
Tres errores conservados; cuatro generaciones y tres llamadas del juez,
siete API historicas. Ambas llamadas adicionales autorizadas utilizadas.
El intento suplementario con `gemini-3.8-flash` ya aprobo 3/3 respuestas,
sin pendientes/fallos, en una llamada. Ocho API historicas (4 gen/4 juez), tres
503 conservados. Codigo 1 por criterio global de 36 partes. INC-016 mitigada;
revision completa, serie original detenida y conjunto offline aceptado intacto.
Propuesta de tres repeticiones nuevas con juez 3.8, maximo 15 API adicionales,
ya autorizada y detenida en su primera repeticion por otro 503 del juez 3.8:
generacion 45/45 y 2/2, tres juicios nuevos pendientes, posiciones 2/3 bloqueadas.
Cinco de las 15 API usadas; diez sin usar no habilitan continuar. Historial
total 13 API. INC-016 pendiente externo para esta serie; revision anterior
conservada solo para su informe, sin transferirla a la generacion nueva.

### ChatReviewResult
Juicios ligados mediante digest al borrador renderizado y sus fuentes exactas.
Una respuesta parcial, repetida o malformada no autoriza publicar.
```
request_id: str
judgments: [{claim_id: str, supported: bool, in_domain: bool,
             calculation_performed: bool, follows_policy: bool}]
```

### ChatValidatedClaim
Texto publicado después de controles deterministas y revisión separada.
```
text: str
source_ids: str[]
sources: ChatSourceFact[]           # ruta y valor disponibles para auditoría
evidence: ChatEvidenceReference[]
```


### Revision suplementaria preparada — 11-oct-2026

El usuario autorizo seguir intentando: se preparo una unica revision
adicional con juez Gemini 3.8 de las tres respuestas guardadas `58b2769d`,
cero generaciones y maximo una llamada suplementaria sin reintentos. Aun no
ejecutada; historial 13 API, maximo 14 tras el intento. Presupuesto separado;
las diez API sin usar y repeticiones 2/3 permanecen bloqueadas. El 503 original
y criterio de tres ejecuciones sin errores se conservan; revisar el resultado
antes de continuar. Plan `chatbot_step4_consistency_judge38_run1_retry1_plan_20261011.json` y Markdown,
ejecutor `.test_tmp/revisar_consistencia_juez38_run1.ps1`. INC-016 pendiente externo, cero API en preparacion.


### Revision recuperada y propuesta de continuacion — 11-oct-2026

Revision actual de `58b2769d` recuperada con Gemini 3.8: 3/3 juicios
independientes favorables, cero pendientes/fallos; una llamada suplementaria
del juez y cero generaciones. Salida 1 solo por gate global de 36 partes.
503 original conservado en `chatbot_step4_consistency_judge38_run1_20261012_045201_1e1da5bf_combined`; seguimiento total 14 API.
La serie mantiene 0/3 ejecuciones sin errores del plan original y posiciones
2/3 bloqueadas. Propuesta `chatbot_step4_consistency_judge38_recovery_amendment_proposal_20261011.json` y Markdown, aun no autorizada:
aceptar esta generacion revisada para calidad y completar solo las dos
restantes con las diez API ya presupuestadas, conservando el error de
disponibilidad. INC-016 mitigada, conjunto aceptado intacto; cero API nuevas
en auditoria y ninguna nueva llamada habilitada por esta propuesta.


### Continuacion con recuperacion aceptada — 11-oct-2026

Continuacion aceptada: primera generacion aprobada para calidad (1/3),
503 original registrado como disponibilidad. Nuevo plan `chatbot_step4_consistency_judge38_recovery_authorized_plan_20261011.json`;
estado en `chatbot_step4_consistency_judge38_recovery_series_progress_20261011.json` y Markdown. Posicion 2 lista, 3 bloqueada
hasta auditoria; ejecutar solo las dos restantes con maximo diez API ya
presupuestadas, sin reintentos y detener ante nuevo fallo. Historial actual
14 API, maximo acumulado 24; cero llamadas nuevas en preparacion. Ejecutor
`.test_tmp/probar_consistencia_recuperada_juez38.ps1 -Repeticion 2..3`. Plan/runner originales y sus 0/3 ejecuciones
sin errores conservados; conjunto aceptado intacto e INC-016 mitigada.


### Repeticion 2 aprobada y tercera habilitada — 11-oct-2026

Repeticion 2 aprobada (`052052_dabc0f75`): 45/45 controles, cobertura
2/2 y 3/3 juicios independientes favorables, cero fallos/pendientes/errores.
Avance bajo el ajuste aceptado 2/3 generaciones aprobadas para calidad;
tercera habilitada con la autorizacion existente, maximo cinco API restantes,
sin reintentos y detener ante nuevo fallo. Historial 19 API (12 gen/7 juez),
maximo acumulado 24. Auditoria `chatbot_step4_consistency_judge38_recovered_run2_audit_20261011.json` y Markdown, cero API nuevas.
503 inicial conservado; conjunto aceptado intacto e INC-016 mitigada. Estado
en `chatbot_step4_consistency_judge38_recovery_series_progress_20261011.json`; ejecutar solo
`.test_tmp/probar_consistencia_recuperada_juez38.ps1 -Repeticion 3` y auditar.


### Tercera detenida y presupuesto agotado — 11-oct-2026

Tercera `052919_6ff8abfb` fallida: 44/45 controles, cobertura 2/2, revisor
interno veta una negativa a dividir identica a las aprobadas antes; respaldo
seguro, sin calculo. Juez externo 503, tres juicios pendientes. Serie detenida
2/3, diez de diez API usadas y ninguna adicional autorizada; historial 24 API
(16 gen/8 juez). INC-013 reabierta para este seguimiento e INC-016 pendiente
externo; conjunto historico aceptado preservado. Auditoria `chatbot_step4_consistency_judge38_recovered_run3_audit_20261011.json`
y Markdown; cero API en auditoria. Tratar revision interna antes de nuevas pruebas.


### Mitigacion local de negativas aun sin medir — 11-oct-2026

Mitigacion local preparada en agents/chat_response.py: guia especial solo
para la revision de negativas calculation/not_allowed respaldadas por policy.
Escritor, datos, schemas, guardas y veto intactos. 48 pruebas/23 subpruebas
aprobadas, comparacion de 28 fixtures/54 callbacks con seis casos afectados,
cero API. Efecto con Gemini real pendiente; version nueva no validada offline
todavia. INC-013 abierta para seguimiento e INC-016 pendiente externo.
Presupuesto anterior agotado (24 API), ejecutores anteriores congelados.
**Fase 1 ejecutada y detenida — 12-oct-2026:**
`chatbot_step4_policy_refusal_phase1_20261012_063948_772d6fd5` produjo tres
partes validadas internamente: 45/45 controles, cobertura 2/2 y cero fallos
mecanicos, en cuatro generaciones. La negativa a dividir paso la revision
interna con la nueva guia en esta ejecucion; esto no demuestra estabilidad
general ni sustituye el juicio independiente. Flash 3.8 hizo una llamada,
`APITimeoutError`, sin HTTP ni respuesta guardada: cero juicios y tres pendientes.
No se clasifica como 503/capacidad ni se atribuye a la clave; causa no demostrada.

Auditoria `chatbot_step4_policy_refusal_phase1_audit_20261012.json` y Markdown:
fuente/plan/ejecutores/intento/fixture/diez huellas correctos, replay completo de
cuatro registros identico y resumen semantico recalculado identico. Las 264
huellas originales del plan y 274 archivos previos a la auditoria intactos;
cero API al auditar. Fase 1 conserva el timeout; fase 2 bloqueada segun el plan.
Cinco de 18 API autorizadas usadas. Las trece restantes pertenecen a fase 2,
sin habilitar; historial del seguimiento 29 API (20 gen/9 juez).
Dos exitos previos para calidad, ninguna nueva generacion con guia revisada
aprobada independientemente. No contar el reemplazo ni cerrar Paso 4.
INC-20260930-013 abierta; INC-20260930-016 pendiente externo por timeout.

**Revisión suplementaria autorizada — 12-oct-2026:** el usuario indicó
«ok entonces hagamos las pruebas», tras explicar el presupuesto y la recuperación.
Plan `chatbot_step4_policy_refusal_phase1_judge_recovery_authorized_20261012.json`:
revisar una vez las tres respuestas guardadas de `063948_772d6fd5` con Gemini 3.8,
cero generaciones, máximo una llamada del juez, espera 60 s y cero reintentos.
La propuesta y el plan original se conservan como registros históricos.
El máximo de esta validación aumenta de 18 a 19 API adicionales: cinco usadas,
una suplementaria autorizada aún sin ejecutar y trece reservadas para fase 2.
El historial sigue en 29 API (20 generación/9 juez); máximo acumulado 43.

Aceptar la recuperación de fase 1 para calidad solo con tres juicios favorables,
sin nuevos errores ni contradicciones y auditoría favorable ligada a las mismas
respuestas. Conservar el timeout original como fallo de disponibilidad. Entonces
se puede habilitar fase 2 con sus trece llamadas ya autorizadas, sin otra aprobación
entre éxitos y con detención ante cualquier fallo o revisión pendiente. Ambas
fases deben pasar para contar el reemplazo de la tercera generación fallida;
no afirmar tres repeticiones exitosas con la guía nueva ni trasladar juicios.
Fase 2 permanece bloqueada; ningún intento suplementario real reservado.
INC-20260930-013 abierta; INC-20260930-016 pendiente externo; Paso 4 no cerrado.

**Fase 1 recuperada y fase 2 habilitada — 12-oct-2026:** el suplemento
`chatbot_step4_policy_refusal_phase1_judge_recovery_20261012_072935_21c041e7`
obtuvo 3/3 juicios independientes favorables, cero pendientes, errores nuevos,
fallos o contradicciones, con una llamada del juez 3.8 y cero generaciones.
Fuente y tres digests coinciden; resumen recalculado idéntico. Código de revisión
1 únicamente por el requisito global de 36 partes frente a las tres de esta muestra.
Auditoría `chatbot_step4_policy_refusal_phase1_judge_recovery_audit_20261012.json`
favorable, diez huellas de código y 286 archivos previos preservados; cero API.
El consolidado conserva el APITimeoutError original en attempts, cuatro
generaciones contadas una sola vez y dos llamadas históricas del juez.

Fase 1 aceptada para calidad bajo el criterio de recuperación autorizado:
45/45 controles, cobertura 2/2 y 3/3 favorables. Su timeout permanece registrado
como disponibilidad. Fase 2 lista con la autorización existente: cinco preguntas,
nueve partes y tres respondibles, máximo diez generaciones/tres juez (trece API),
espera 60 s, sin reintentos y detener ante cualquier fallo o revisión pendiente.
Ejecutar una vez `.test_tmp/validar_negativas_paso4.ps1 -Fase 2` y auditar.
Seis de 19 API adicionales usadas; trece restantes. Historial del seguimiento
30 API (20 generación/10 juez). La fase 2 todavía no se ha ejecutado.
Dos éxitos anteriores y uno con la guía nueva se conservan por separado;
el reemplazo de la tercera generación fallida sigue condicionado a fase 2
aprobada. No afirmar tres repeticiones exitosas con la guía nueva ni trasladar
juicios. INC-20260930-013 abierta; INC-20260930-016 mitigada para esta recuperación.
21 incidencias: 19 resueltas, una abierta y una mitigada; Paso 4 no cerrado.

**Fase 2 detenida por 503 del juez — 12-oct-2026:**
`chatbot_step4_policy_refusal_phase2_20261012_074133_e8482e9d` completó cinco
casos/nueve partes con diez generaciones: 116/116 controles, cobertura 3/3 y
nueve partes validadas internamente, cero fallos mecánicos. El juez 3.8 hizo
una llamada al primer lote (dos partes), InternalServerError, HTTP 503,
UNAVAILABLE y pista de capacidad. Cero juicios favorables/adversos y nueve
pendientes; se detuvo sin llamar los otros dos lotes. La pista no demuestra
la causa interna y el error no es un rechazo semántico de las respuestas.

Auditoría `chatbot_step4_policy_refusal_phase2_audit_20261012.json`:
fuente/plan/intento/ejecutores/diez huellas correctos, resumen recalculado
idéntico, 298 archivos previos intactos y cero API al auditar. La fase 1
recuperada mantiene 3/3 favorables; su timeout y el 503 de fase 2 se conservan.
17 de 19 API adicionales usadas (14 generación/3 juez); dos llamadas del juez
sin usar, bloqueadas por la regla de detención. Historial del seguimiento
41 API (30 generación/11 juez). Fase 2 detenida, reemplazo sin contar y Paso 4
sin cerrar. INC-20260930-013 abierta; INC-20260930-016 pendiente externo;
21 incidencias: 19 resueltas, una abierta y una pendiente externa.

Propuesta `chatbot_step4_policy_refusal_phase2_judge_recovery_proposal_20261012.json`,
todavía sin autorizar: revisar únicamente las nueve respuestas guardadas en
tres lotes de 2/3/4 partes, cero generaciones, máximo tres llamadas del juez,
sin reintentos y detener ante primer fallo. Usaría las dos llamadas restantes
y una extra, elevando el máximo adicional de 19 a 20 (máximo acumulado 44).
Aceptar recuperación para calidad solo con 9/9 juicios independientes favorables,
sin errores nuevos ni contradicciones y auditoría favorable; conservar el 503
original. El criterio de reemplazo exige ambas fases aprobadas y conserva las
versiones distintas de guía y errores. La propuesta no habilita llamadas;
ejecutor `.test_tmp/revisar_negativas_fase2_juez.ps1` bloqueado hasta aprobación.

**Continuación de intentos autorizada — 12-oct-2026:** el usuario indicó
«bueno vamos a seguir haciendo mas intentos hasta que todas las pruebas pasen».
Autoriza continuar la validación pendiente y sus recuperaciones, sin volver a
solicitar autorización para intentos del mismo alcance. Cada ejecución mantiene
un plan acotado, registro propio y auditoría antes del intento siguiente. Ante
indisponibilidad del proveedor se prepara otro intento sobre las respuestas
pendientes, dejando una pausa; un juicio adverso exige análisis del posible
defecto antes de repetir. No se descartan errores ni juicios desfavorables.

Siguiente intento preparado, aún sin ejecutar: plan
`chatbot_step4_policy_refusal_phase2_judge_recovery_authorized_20261012.json`;
ejecutor existente `.test_tmp/revisar_negativas_fase2_juez.ps1`. Revisar las nueve
respuestas de `074133_e8482e9d` en tres lotes de 2/3/4 partes, cero generaciones,
máximo tres llamadas del juez Gemini 3.8, espera 60 s, cero reintentos internos
y detener ante primer error, juicio adverso o lote incompleto. Usar las dos
llamadas restantes y una extra: máximo de esta validación 20 API adicionales,
17 usadas y tres habilitadas solo para esta recuperación. Historial 41 API
(30 generación/11 juez), máximo 44 tras este intento. Una ampliación posterior
se registrará en un nuevo plan bajo esta misma autorización antes de ejecutarla.

Aceptar fase 2 para calidad únicamente con 9/9 juicios independientes favorables,
sin errores nuevos ni contradicciones y auditoría favorable; conservar su 503
original y el timeout de fase 1. Después evaluar ambas fases bajo el criterio
de reemplazo ya aceptado, conservando las versiones distintas de guía. No afirmar
tres repeticiones con la guía nueva ni trasladar juicios de otras respuestas.
Generación de fase 2 ya aprobada: 116/116 controles, cobertura 3/3 y nueve partes
validadas internamente. Reemplazo sin contar, Paso 4 abierto; INC-20260930-013
abierta e INC-20260930-016 pendiente externo. Ningún intento nuevo reservado.

**Segundo suplemento de fase 2 preparado tras otro 503 — 12-oct-2026:**
El intento `083847_c6d73947` hizo una llamada del juez 3.8, cero generaciones
y cero reintentos; primer lote con InternalServerError, 503/UNAVAILABLE y pista
de capacidad. Cero juicios y nueve pendientes; los otros dos lotes no se llamaron.
La pista no demuestra causa ni fallo de contenido. Auditoría
`chatbot_step4_policy_refusal_phase2_judge_recovery_audit_20261012.json`:
fuente/plan/intento/ejecutores correctos, resumen recalculado idéntico y 310
evidencias anteriores intactas. Consolidado `083847_c6d73947_combined` conserva
ambos 503 en attempts y diez generaciones contadas una sola vez. El campo
total_api_calls del consolidado cuenta solo las dos llamadas históricas del juez.
Generación 116/116 y cobertura 3/3 conservadas; fase 1 recuperada y timeout intactos.

Nuevo intento autorizado bajo la indicación vigente de continuar hasta completar
las pruebas: `chatbot_step4_policy_refusal_phase2_judge_recovery_retry2_authorized_20261012.json`,
ejecutor `.test_tmp/reintentar_negativas_fase2_juez.ps1`. Revisar las mismas nueve
partes pendientes en lotes 2/3/4, cero generaciones, máximo tres juez 3.8, espera
60 s y cero reintentos internos; detener ante error, juicio adverso o incompleto.
18/21 API adicionales usadas, tres habilitadas (dos sin usar y una extra);
historial 42 API (30 generación/12 juez), máximo 45 tras este intento. Pausa
entre intentos manuales; auditar antes de preparar otro bajo la misma autorización.
Un fallo de contenido requiere análisis antes de repetir, sin descartar juicios.

Aceptar recuperación solo con 9/9 independientes favorables y auditoría favorable,
sin errores nuevos ni contradicciones, manteniendo ambos 503 como disponibilidad.
Reemplazo sin contar, Paso 4 abierto; INC-20260930-013 abierta e INC-20260930-016
pendiente externo. Nuevo intento aún sin ejecutar ni reservar, cero API del agente.
Comprobación local: sintaxis PowerShell/Python correcta, MostrarPlan nuevo código 0,
ejecutor suplementario anterior bloqueado código 1 antes de clave/nueva reserva.
Diez huellas, 264 originales, 310 protegidos y cinco archivos de consolidado/auditoría
coincidentes antes/después; presupuesto ligado al progreso, diff de espacios código 0.
Registro `chatbot_step4_policy_refusal_phase2_judge_recovery_retry2_preflight_20261012.json`.
Estos controles habilitan el intento, no constituyen juicio independiente.

**Tercer suplemento de fase 2 preparado tras otro 503 — 12-oct-2026:**
El intento `093132_828546ec` hizo una llamada del juez 3.8, cero generaciones
y cero reintentos; primer lote con InternalServerError, 503/UNAVAILABLE y pista
de capacidad. Cero juicios y nueve pendientes; los otros dos lotes no se llamaron.
La pista no demuestra causa ni fallo de contenido. Auditoría
`chatbot_step4_policy_refusal_phase2_judge_recovery_retry2_audit_20261012.json`:
fuente/plan/intento/ejecutores correctos, resumen recalculado idéntico y 322
evidencias anteriores intactas. Consolidado `093132_828546ec_combined` conserva
los tres 503 en attempts y diez generaciones contadas una sola vez. El campo
total_api_calls del consolidado cuenta solo las tres llamadas históricas del juez.
Generación 116/116 y cobertura 3/3 conservadas; fase 1 recuperada y timeout intactos.

Nuevo intento autorizado bajo la indicación vigente de continuar hasta completar
las pruebas: `chatbot_step4_policy_refusal_phase2_judge_recovery_retry3_authorized_20261012.json`,
ejecutor `.test_tmp/reintentar_negativas_fase2_juez_intento3.ps1`. Revisar las mismas nueve
partes pendientes en lotes 2/3/4, cero generaciones, máximo tres juez 3.8, espera
60 s y cero reintentos internos; detener ante error, juicio adverso o incompleto.
19/22 API adicionales usadas, tres habilitadas (dos sin usar y una extra);
historial 43 API (30 generación/13 juez), máximo 46 tras este intento. Pausa
entre intentos manuales; auditar antes de preparar otro bajo la misma autorización.
Un fallo de contenido requiere análisis antes de repetir, sin descartar juicios.

Aceptar recuperación solo con 9/9 independientes favorables y auditoría favorable,
sin errores nuevos ni contradicciones, manteniendo los tres 503 como disponibilidad.
Reemplazo sin contar, Paso 4 abierto; INC-20260930-013 abierta e INC-20260930-016
pendiente externo. Nuevo intento aún sin ejecutar ni reservar, cero API del agente.
Comprobación local: sintaxis PowerShell/Python correcta, MostrarPlan nuevo código 0,
ejecutor suplementario anterior bloqueado código 1 antes de clave/nueva reserva.
Diez huellas, 264 originales, 322 protegidos y cinco archivos de consolidado/auditoría
coincidentes antes/después; presupuesto ligado al progreso, diff de espacios código 0.
Registro `chatbot_step4_policy_refusal_phase2_judge_recovery_retry3_preflight_20261012.json`.
Estos controles habilitan el intento, no constituyen juicio independiente.

**Juez alternativo Gemini 3.6 preparado tras cuatro 503 — 12-oct-2026:**
El intento `094039_328ff3d4` hizo una llamada del juez 3.8, cero generaciones
y cero reintentos; primer lote con InternalServerError, 503/UNAVAILABLE y pista
de capacidad. Cero juicios y nueve pendientes; los otros dos lotes no se llamaron.
La pista no demuestra causa ni fallo de contenido. Auditoría
`chatbot_step4_policy_refusal_phase2_judge_recovery_retry3_audit_20261012.json`:
fuente/plan/intento/ejecutores correctos, resumen recalculado idéntico y 334
evidencias anteriores intactas. Consolidado `094039_328ff3d4_combined` conserva
los cuatro 503 en attempts y diez generaciones contadas una sola vez. El campo
total_api_calls del consolidado cuenta solo las cuatro llamadas históricas del juez.
Generación 116/116 y cobertura 3/3 conservadas; fase 1 recuperada y timeout intactos.

Nuevo intento autorizado bajo la indicación vigente de continuar hasta completar
las pruebas: `chatbot_step4_policy_refusal_phase2_judge36_authorized_20261012.json`,
ejecutor `.test_tmp/revisar_negativas_fase2_juez36.ps1`. Revisar las mismas nueve
partes pendientes en lotes 2/3/4, cero generaciones, máximo tres juez 3.6, espera
60 s y cero reintentos internos; detener ante error, juicio adverso o incompleto.
20/23 API adicionales usadas, tres habilitadas (dos sin usar y una extra);
historial 44 API (30 generación/14 juez), máximo 47 tras este intento. Pausa
entre intentos manuales; auditar antes de preparar otro bajo la misma autorización.
Un fallo de contenido requiere análisis antes de repetir, sin descartar juicios.

Aceptar recuperación solo con 9/9 independientes favorables y auditoría favorable,
sin errores nuevos ni contradicciones, manteniendo los cuatro 503 como disponibilidad.
Reemplazo sin contar, Paso 4 abierto; INC-20260930-013 abierta e INC-20260930-016
pendiente externo. Nuevo intento aún sin ejecutar ni reservar, cero API del agente.
Comprobación local: sintaxis PowerShell/Python correcta, MostrarPlan nuevo código 0,
ejecutor suplementario anterior bloqueado código 1 antes de clave/nueva reserva.
Diez huellas, 264 originales, 334 protegidos y cinco archivos de consolidado/auditoría
coincidentes antes/después; presupuesto ligado al progreso, diff de espacios código 0.
Registro `chatbot_step4_policy_refusal_phase2_judge36_preflight_20261012.json`.
Estos controles habilitan el intento, no constituyen juicio independiente.

Cambio de juez a propuesta del usuario «Y si cambiamos el modelo?? cuál estamos
utilizando?»: se elige gemini-3.6-flash, modelo estable con salidas estructuradas
según https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash. Se conserva
el generador/revisor interno gemini-3.5-flash-lite y el mismo endpoint compatible.
No se ha verificado disponibilidad de 3.6 en esta cuenta; el cambio es una prueba
de disponibilidad y no garantiza eliminar el 503. INC-20260930-014 corregida:
21 incidencias reales y contadores del nuevo plan 14 generación/6 juez/20 previas,
reconstruidos de informes e intentos. La discrepancia del plan retry3 se documenta
en la auditoría nueva, preservando sus bytes; límites ejecutables originales correctos.

**Juez 3.6: cinco aprobaciones auditadas, cuatro pendientes — 12-oct-2026:**
`095323_6fba7d46` produjo cinco juicios independientes favorables en tres llamadas:
explicit_calculation, implicit_calculation y las tres partes de mixed. Fuente,
cinco digests y cuatro criterios verdaderos por parte comprobados; resumen
recalculado idéntico. Tercer lote con 503/UNAVAILABLE, cuatro partes pendientes:
question_injection y result_and_projection. Sin fallos de contenido o mecánicos.
Auditoría `chatbot_step4_policy_refusal_phase2_judge36_partial_audit_20261012.json`:
346 evidencias anteriores intactas. Consolidado conserva cinco 503, siete llamadas
históricas del juez y diez generaciones contadas una vez; fuente original intacta.

Se prepara únicamente el lote pendiente bajo la autorización vigente:
`chatbot_step4_policy_refusal_phase2_judge36_pending_authorized_20261012.json`,
ejecutor `.test_tmp/revisar_pendientes_fase2_juez36.ps1`. Cuatro partes, máximo una
llamada del juez 3.6, cero generaciones/reintentos, 60 s. Preguntas completas,
mismo informe/digests y payload idéntico al tercer lote original; el juez no ve
juicios previos. Mantener las cinco aprobaciones sin repetirlas. Nuevo intento
aún sin ejecutar ni reservar. 23/24 API adicionales usadas (14 gen/9 juez),
una habilitada; historial 47 API (30 gen/17 juez), máximo 48 tras el intento.

Aceptar recuperación de fase 2 solo si las cuatro pendientes pasan sin error
nuevo/contradicción y una auditoría confirma las nueve aprobaciones acumuladas.
Conservar los cinco 503 como disponibilidad; criterio global de 36 intacto,
sin afirmar una corrida original sin errores. Fase 1 recuperada/timeout y 116/116,
3/3 de generación preservados; reemplazo sin contar y Paso 4 abierto.
INC-20260930-013 abierta e INC-20260930-016 pendiente externo; 21 incidencias,
19 resueltas, una abierta y una pendiente externa. Rama codex/chatbot-q4,
HEAD 6fa66bcc6a731a3f06df79edb5a4bf62e3c8e03c, sin commit; cero API del agente.

Controles locales: sintaxis y MostrarPlan correctos, ejecutor de nueve partes
bloqueado antes de clave/reserva; dos dobles locales (éxito/503) verifican una
llamada solo para las cuatro pendientes y conservación de cinco aprobaciones.
Diez huellas, 264 originales, 346 protegidos y cinco archivos de auditoría/
consolidado intactos; diff de espacios código 0. Registro
`chatbot_step4_policy_refusal_phase2_judge36_pending_preflight_20261012.json`.
Los dobles no aportan evidencia semántica real; suite de producto no repetida.

**Paso 4 offline y seguimiento cerrados — 12-oct-2026:** la última revisión
`121907_b98e4274` obtuvo cuatro juicios nuevos favorables en una llamada del juez
3.6, sin errores; las cinco aprobaciones previas permanecen intactas. Fase 2:
9/9 independientes, 116/116 controles y cobertura 3/3. Fase 1 ya auditada: 3/3,
45/45 y 2/2. Validación dirigida completa: siete casos/doce partes, 12/12
independientes favorables, 161/161 controles y cobertura 5/5; cero pendientes,
fallos mecánicos/semánticos o contradicciones. Fuente, digests y resúmenes
aislado/consolidado recalculados y comprobados; 361 evidencias previas intactas.
Auditoría final `chatbot_step4_policy_refusal_phase2_final_audit_20261012.json`.

Aceptación `chatbot_step4_policy_refusal_validation_acceptance_20261012.json` y
Markdown: se aplica el criterio explícitamente autorizado de dos generaciones
previas con la guía anterior más la nueva fase 1 como reemplazo del tercer
intento, condicionado a ambas fases aprobadas. Tres posiciones de calidad
aceptadas; no se afirma tres repeticiones con la guía revisada. La tercera
fallida y la serie detenida 2/3 se conservan como históricos, sin trasladarles
juicios. El conjunto base aceptado sigue intacto: 28 casos/36 partes, 36/36
independientes, 548/548 controles y cobertura 22/22. La muestra de doce partes
no sustituye el conjunto base ni modifica el gate global de 36.

Se resuelven INC-20260930-013 para el defecto validado e INC-20260930-016 para
los juicios pendientes actuales. 21 incidencias: 21 resueltas, cero abiertas o
pendientes externas en este alcance. El timeout de fase 1 y cinco 503 de fase 2
se conservan como disponibilidad; no se demuestra estabilidad estadística ni
disponibilidad general del proveedor. 24/24 API adicionales usadas (14 gen/10
juez), historial del seguimiento 48 API (30 gen/18 juez); cero llamadas habilitadas.
Cero API al auditar/consolidar; suite no repetida. Rama codex/chatbot-q4,
HEAD 6fa66bcc6a731a3f06df79edb5a4bf62e3c8e03c, sin commit ni push.
Siguiente fase: Paso 5, autenticación y autorización por negocio, trabajo separado.
Chat de solo lectura conservado; producción sin cambios. Los estados anteriores
de pendiente/detenido describen las ejecuciones históricas previas a este cierre.

### ChatRequest / ChatResponse / ChatHistoryStore (Paso 5)
`ChatRequest`: question (1–2000 caracteres), requested_date opcional y
conversation_id UUID opcional; campos extra prohibidos. Negocio en el path y
usuario en sesión, nunca en historial del cliente. `ChatResponse` contiene
conversation_id y ChatAnswer. Historial temporal por usuario/negocio/conversación:
8 turnos, 30 min, 256 conversaciones por proceso. No es memoria RAG ni fuente
de cifras. GET/DELETE revalidan propietario; contexto de hasta 4 turnos de igual
fecha se trata como dato no confiable. Integración local aprobada, sin despliegue.
