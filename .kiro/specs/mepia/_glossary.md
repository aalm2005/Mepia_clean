# MEPIA — Glosario Compartido

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
expected_cost_structure: ExpectedCostStructure[] (mínimo 1)
audit_rules: {
  red_alert_triggers: string[]            # condiciones que siempre generan alerta roja
  ignored_anomaly_types: string[]         # anomalías aceptadas como normales (default [])
  audit_frequency: "daily" | "weekly"     # default "daily"
}
```
> Spec completo: `n10_onboarding_identidad.md`
> Prerequisito obligatorio para ejecutar Layer 3 — HTTP 412 si no está completo.

### ParallelGatherResult
```
layer2_run_id: UUID
sequential_run_id: UUID
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
completed_at: datetime
```

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
```

### ChatGroundingPacket
Paquete determinista permitido como evidencia del futuro chatbot.
```
business_id: str
requested_date: YYYY-MM-DD | null
resolved_date: YYYY-MM-DD | null
metrics: list[dict]              # allowlist de CalcResult
final_report: dict | null        # allowlist de FinalReport
evidence: ChatEvidenceReference[]
missing_data: str[]
built_at: datetime
```
