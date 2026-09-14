# MEPIA — Arquitectura de Base de Datos

**Tipo:** Híbrida — campos estructurados para cálculos + JSONB para datos flexibles
**Motor:** PostgreSQL via Supabase
**Migración:** `supabase/migrations/002_hybrid_schema.sql`

---

## Tabla: `businesses`

| Campo            | Tipo        | Notas                              |
|------------------|-------------|------------------------------------|
| id               | uuid PK     | gen_random_uuid()                  |
| business_name    | text        | Nombre del restaurante             |
| industry_sector  | text        | ej. "cafetería", "restaurante"     |
| currency         | text        | ISO 4217, default "MXN"            |
| opening_date     | date        | Fecha de apertura — requerido por N09 para ciclo de vida |
| multi_sucursal   | bool        | default false — habilita `calc_sales_by_branch` en S3     |
| operating_hours  | jsonb       | `{ "open": "08:00", "close": "22:00" }` |
| created_at       | timestamptz | default now()                      |

---

## Tabla: `business_fixed_costs`

Gastos fijos iniciales capturados en onboarding. Base para `calc_daily_break_even`.

| Campo            | Tipo        | Notas                                        |
|------------------|-------------|----------------------------------------------|
| id               | uuid PK     | gen_random_uuid()                            |
| business_id      | uuid FK     | → businesses.id                              |
| concept          | text        | ej. "Renta", "CFE", "Nómina base"            |
| amount           | numeric(12,2)|                                             |
| recurrence       | text        | "monthly" \| "weekly"                        |
| expense_behavior | text        | "FIXED" \| "VARIABLE" \| "CAPEX"             |
| is_active        | bool        | default true                                 |

---

## Tabla: `documents`

| Campo          | Tipo        | Notas                                                  |
|----------------|-------------|--------------------------------------------------------|
| id             | uuid PK     | = file_id del POSIngestResult                          |
| business_id    | uuid FK     | → businesses.id                                        |
| storage_path   | text        | Ruta en Supabase Storage                               |
| filename       | text        |                                                        |
| document_type  | text        | "PDF" \| "XML" \| "JPG"                                |
| ocr_status     | text        | "pending" \| "processed" \| "error"                    |
| ocr_confidence | numeric(5,2)| 0–100. < 85 → needs_human_review                       |
| needs_human_review | bool    | true si confianza < 85% o campo obligatorio ausente    |
| uploaded_at    | timestamptz | default now()                                          |
| extracted_data | jsonb       | Respuesta cruda del agente IA                          |

---

## Tabla: `transactions`

| Campo              | Tipo         | Notas                                                  |
|--------------------|--------------|--------------------------------------------------------|
| id                 | uuid PK      | gen_random_uuid()                                      |
| business_id        | uuid FK      | → businesses.id (NOT NULL)                             |
| document_id        | uuid FK      | → documents.id                                         |
| type               | text         | "ingreso" \| "egreso"                                  |
| category           | text         | "venta" \| "nomina" \| "proveedor" \| "impuesto"       |
| amount             | numeric(12,2)|                                                        |
| tax_amount         | numeric(12,2)| IVA extraído de factura                                |
| transaction_date   | date         |                                                        |
| supplier_name      | text         | Nombre del proveedor (facturas)                        |
| concept            | text         | Descripción / partidas                                 |
| document_reference | text         | Folio o referencia del documento                       |
| expense_behavior   | text         | "FIXED" \| "VARIABLE" \| "CAPEX" — confirmado vía `PATCH /transactions/{id}/expense-behavior` |
| metadata           | jsonb        | Datos extra por tipo (método de pago, cajero, etc.)    |
| raw_metadata       | jsonb        | Todo campo extraído fuera del mapeo obligatorio (future-proofing) |
| created_at         | timestamptz  | default now()                                          |

---

## Tabla: `pos_inputs`

Ventas diarias del POS. Input para `calc_cash_reconciliation`.

| Campo          | Tipo         | Notas                          |
|----------------|--------------|--------------------------------|
| id             | uuid PK      |                                |
| business_id    | uuid FK      | → businesses.id                |
| date           | date         |                                |
| total_sales    | numeric(12,2)|                                |
| cash_sales     | numeric(12,2)|                                |
| card_sales     | numeric(12,2)|                                |
| refunds        | numeric(12,2)| default 0                      |
| num_transactions | int        |                                |

---

## Tabla: `cash_counts`

Conteo físico del cajón. Input para `calc_cash_reconciliation`.

| Campo          | Tipo         | Notas                          |
|----------------|--------------|--------------------------------|
| id             | uuid PK      |                                |
| business_id    | uuid FK      | → businesses.id                |
| date           | date         |                                |
| initial_float  | numeric(12,2)| Fondo inicial del día          |
| actual_counted | numeric(12,2)| Efectivo contado al cierre     |
| cash_payouts   | numeric(12,2)| Pagos en efectivo realizados   |
| recorded_by    | text         | ID del cajero                  |

---

## Tabla: `recipes`

| Campo        | Tipo        | Notas                                      |
|--------------|-------------|--------------------------------------------|
| id           | uuid PK     |                                            |
| business_id  | uuid FK     | → businesses.id                            |
| product_name | text        | ej. "Café Latte"                           |
| sale_price   | numeric(12,2)| Precio de venta actual                    |
| ingredients  | jsonb       | `{ "cafe_g": 18, "leche_ml": 250 }`        |
| updated_at   | timestamptz | default now()                              |

---

## Tabla: `daily_context` ⚠️ DEPRECATED — REMOVED

> **Deprecada:** Esta tabla fue retirada del pipeline. El "contexto del día" (tags + texto libre) generaba ruido y no aportaba al diseño final. Los datos existentes pueden permanecer en la DB pero ningún nodo del pipeline debe leer ni escribir en esta tabla.
>
> **Impacto:**
> - `S4 Forensic CFO`: ya no recibe `observed_causality` / `daily_context tags` como input. El campo `ForensicReport.observed_causality` queda como `null` siempre.
> - `N05 CEO Orchestrator`: la lógica de `observed_causality` para ajustar tono de `copilot_phrase` queda inactiva (el campo será siempre `null`).
> - `metadata` JSONB en `transactions`: el campo `context_tags` que referenciaba `daily_context` ya no se popula.
> - `DailyContextPayload` en `_glossary.md`: contrato marcado como deprecated.
> - Endpoint `POST /daily-context` en `n03_human_input_endpoints.md`: deprecated, retorna HTTP 410 Gone.

| Campo       | Tipo        | Notas                                           |
|-------------|-------------|-------------------------------------------------|
| id          | uuid PK     |                                                 |
| business_id | uuid FK     | → businesses.id                                 |
| date        | date        |                                                 |
| tags        | jsonb       | `{ clima, equipo, evento, personal, otros }`    |
| created_at  | timestamptz | default now()                                   |

**Migración de retiro:** `supabase/migrations/004_deprecate_daily_context.sql` — no elimina la tabla, solo agrega comment `DEPRECATED` y remueve los índices activos.

---

## Tabla: `metric_status`

| Campo          | Tipo        | Notas                                       |
|----------------|-------------|---------------------------------------------|
| id             | uuid PK     |                                             |
| business_id    | uuid FK     | → businesses.id                             |
| date           | date        |                                             |
| metric_name    | text        | ej. "daily_break_even"                      |
| status         | text        | "dormant" \| "active" \| "blocked"          |
| missing_fields | jsonb       | `["cash_count"]` o `[]`                     |
| updated_at     | timestamptz | default now()                               |

---

## Tabla: `audit_results`

Persiste outputs de todos los nodos del pipeline (S3, S4, N06, N07, N08, N09, Layer 3).

| Campo           | Tipo         | Notas                                                              |
|-----------------|--------------|--------------------------------------------------------------------|
| id              | uuid PK      | gen_random_uuid()                                                  |
| run_id          | uuid         | ID de la ejecución — `layer2_run_id` o `sequential_run_id`        |
| business_id     | uuid FK      | → businesses.id                                                    |
| date            | date         | Fecha auditada                                                     |
| pipeline_layer  | text         | `"sequential"` \| `"parallel"` \| `"loop"`                        |
| node_id         | text         | `"S3"` \| `"S4"` \| `"N06"` \| `"N07"` \| `"N08"` \| `"N09"` \| `"N11"` etc. |
| module          | text         | Nombre descriptivo del módulo (ej. `"conciliacion_caja"`)          |
| archetype       | text         | `"Operative Genius"` \| `"Product Purist"` \| `"Growth Hacker"`   |
| raw_result      | jsonb/text   | Campo legacy; se conserva por compatibilidad                       |
| result_data     | jsonb        | Contrato vigente: resultado estructurado de cada nodo              |
| copilot_phrase  | text         | Frase CEO-framed — `null` para nodos que no generan frases (N06)  |
| node_status     | text         | `"success"` \| `"partial"` \| `"failed"` \| `"timeout"` \| `"error"` |
| created_at      | timestamptz  | default now()                                                      |

`node_status` describe la ejecución del nodo y usa únicamente `success`, `partial`,
`failed`, `timeout` o `error`. Veredictos de dominio como `approved` o `rejected`
se conservan dentro de `result_data`. La migración
`008_audit_results_runtime_contract.sql` actualiza instalaciones creadas desde el
schema legacy de `001_init.sql`. Antes de instalar el constraint, normaliza los
estados históricos con esta política: `completed`, `complete`, `approved` y
`approved_with_warning_cortafuegos` → `success`; `rejected` y `pending` →
`partial`; los estados vigentes se conservan y cualquier valor no reconocido →
`error`. `pending` se considera una ejecución incompleta, no una ejecución
exitosa. Los valores `NULL` permanecen `NULL` por compatibilidad con filas
antiguas sin estado.

---

## Tabla: `circuit_breaker_state`

Estado del circuit breaker por nodo, negocio y fecha. Consultado por N06 antes del scatter.

| Campo              | Tipo         | Notas                                                    |
|--------------------|--------------|----------------------------------------------------------|
| id                 | uuid PK      | gen_random_uuid()                                        |
| business_id        | uuid FK      | → businesses.id                                          |
| date               | date         | Fecha de evaluación                                      |
| node_id            | text         | `"N07"` \| `"N08"` \| `"N09"`                           |
| consecutive_failures | int        | Contador de fallos consecutivos — reset a 0 en success   |
| circuit_status     | text         | `"closed"` (normal) \| `"open"` (degradado)              |
| opened_at          | timestamptz  | Cuándo se abrió el circuit — `null` si `closed`          |
| reset_by           | uuid         | UUID del usuario que hizo reset manual — `null` si automático |
| updated_at         | timestamptz  | default now()                                            |

Regla: `consecutive_failures >= 3` → `circuit_status: "open"` automáticamente.

---

## Tabla: `shift_audit_events` 🔧 NEW

Eventos de auditoría operativa por turno. Input para métricas de operación/caja en S3.

| Campo              | Tipo         | Notas                                    |
|--------------------|--------------|------------------------------------------|
| id                 | uuid PK      | gen_random_uuid()                        |
| business_id        | uuid FK      | → businesses.id                          |
| sucursal_id        | text         | identificador de sucursal                |
| date               | date         |                                          |
| turno              | text         | "matutino", "vespertino", etc.           |
| apertura           | numeric(12,2)| fondo de apertura del turno              |
| cierre_x           | numeric(12,2)| lectura X (parcial)                      |
| cierre_z           | numeric(12,2)| lectura Z (cierre final)                 |
| sobrante_faltante  | numeric(12,2)| positivo = sobrante, negativo = faltante |
| cancellations      | jsonb        | array de `{order_id, motivo, responsable, timing}` |
| reprints           | int          | default 0                                |
| clock_records      | jsonb        | array de `{employee_id, clock_in, clock_out}` |
| created_at         | timestamptz  | default now()                            |

---

## Tabla: `inventory_daily` 🔧 NEW

Snapshot diario de inventario y costos teóricos. Input para métricas de inventario en S3.

| Campo              | Tipo         | Notas                                    |
|--------------------|--------------|------------------------------------------|
| id                 | uuid PK      | gen_random_uuid()                        |
| business_id        | uuid FK      | → businesses.id                          |
| date               | date         |                                          |
| ingredient_id      | text         | ID del insumo en catálogo POS            |
| ingredient_name    | text         |                                          |
| unit               | text         | unidad base (g, ml, unidad)              |
| consumo_teorico    | numeric(12,4)| consumo teórico del día por recetas      |
| waste_recorded     | numeric(12,4)| merma registrada manualmente             |
| current_stock      | numeric(12,4)| existencia actual al cierre              |
| unit_cost          | numeric(12,4)| costo unitario última compra             |
| created_at         | timestamptz  | default now()                            |

UNIQUE constraint: `(business_id, date, ingredient_id)` — upsert semántico.

---

## Tabla: `delivery_platform_config` 🔧 NEW

Configuración de comisiones por plataforma de delivery. Llenada/actualizada por el negocio.
S3 `calc_delivery_commission_cost` lee de aquí — nunca asume tasa fija en código.

| Campo              | Tipo         | Notas                                    |
|--------------------|--------------|------------------------------------------|
| id                 | uuid PK      | gen_random_uuid()                        |
| business_id        | uuid FK      | → businesses.id                          |
| platform           | text         | "UberEats" \| "Rappi" \| "DiDiFood"     |
| commission_rate    | numeric(5,4) | ej. 0.3000 = 30%                         |
| effective_date     | date         | fecha desde la cual aplica esta tasa     |
| created_at         | timestamptz  | default now()                            |

UNIQUE constraint: `(business_id, platform, effective_date)` — permite historial de tasas.

Regla de lectura en S3: para calcular comisión de un día D, usar la tasa con
`effective_date <= D` más reciente. Si no existe configuración para una plataforma,
S3 retorna `status: "incomplete_data"` para esa plataforma.

---

## Tabla: `unit_conversions`

| Campo     | Tipo    | Notas                    |
|-----------|---------|--------------------------|
| id        | uuid PK |                          |
| from_unit | text    | ej. "kg"                 |
| to_unit   | text    | ej. "g" (unidad base)    |
| factor    | decimal | ej. 1000                 |

Registros iniciales: `kg→g (×1000)`, `L→ml (×1000)`, `unidad→unidad (×1)`

---

## Tabla: `mepia_memory`

Memoria semántica ("Brain") — Single Source of Truth para RAG. NO es el Ledger del dashboard.
`audit_results` sigue siendo la fuente de verdad estructurada para el frontend.

> Dependencia de embedding: **OpenAI `text-embedding-3-small`** (1536 dimensiones, V1 oficial de MEPIA).
> Si se cambia de modelo en el futuro, la columna `embedding` debe ser recreada con la nueva dimensión.
> Postgres es la fuente de verdad. Engram es secundario y reconstruye desde esta tabla al reiniciar.

| Campo                | Tipo            | Notas                                                                      |
|----------------------|-----------------|----------------------------------------------------------------------------|
| id                   | uuid PK         | gen_random_uuid()                                                          |
| business_id          | uuid FK         | REFERENCES businesses(id) ON DELETE CASCADE — no más registros huérfanos  |
| source_audit_run_id  | uuid FK         | REFERENCES audit_results(run_id) ON DELETE SET NULL — **nullable** para chunks de onboarding sin auditoría previa |
| content              | text            | Texto del chunk (≤500 tokens) — prohibido guardar reportes completos       |
| metadata             | jsonb           | `{ "node_origin": "N12", "date": "YYYY-MM-DD", "chunk_index": 0, "chunk_total": 4 }` |
| embedding            | vector(1536)    | Generado con text-embedding-3-small — null hasta que worker procese        |
| status               | text            | `"pending_embed"` \| `"embedded"` \| `"failed"` — nunca se pierde un chunk |
| created_at           | timestamptz     | default now() — usado para Time-Weighted Retrieval (decay temporal)        |

Escritura permitida: **solo N12 (Phrase Expander) o N13 (Quality Reviewer)** vía `MemoryService.store_memory()`.
Lectura permitida: todos los agentes vía `MemoryService.get_context()`.

Migración: `supabase/migrations/003_memory.sql`
Requiere: `CREATE EXTENSION IF NOT EXISTS vector;` en `001_init.sql`

---

## Índices

```sql
CREATE INDEX idx_transactions_metadata     ON transactions USING GIN (metadata);
CREATE INDEX idx_transactions_raw_metadata ON transactions USING GIN (raw_metadata);
CREATE INDEX idx_documents_extracted       ON documents    USING GIN (extracted_data);
CREATE INDEX idx_transactions_business_date ON transactions (business_id, transaction_date);
CREATE INDEX idx_transactions_expense_behavior ON transactions (business_id, expense_behavior);
CREATE INDEX idx_documents_review          ON documents    (needs_human_review) WHERE needs_human_review = true;
CREATE INDEX idx_daily_context_lookup      ON daily_context (business_id, date);
CREATE INDEX idx_metric_status_lookup      ON metric_status (business_id, date, status);
CREATE INDEX idx_recipes_business          ON recipes (business_id);
CREATE INDEX idx_audit_results_run         ON audit_results (run_id);
CREATE INDEX idx_audit_results_lookup      ON audit_results (business_id, date, pipeline_layer, node_id);
CREATE INDEX idx_circuit_breaker_lookup    ON circuit_breaker_state (business_id, date, node_id);
CREATE INDEX idx_circuit_breaker_open      ON circuit_breaker_state (node_id, circuit_status) WHERE circuit_status = 'open';
-- Tablas nuevas (S1B ingesta API)
CREATE INDEX idx_shift_audit_lookup        ON shift_audit_events (business_id, date, sucursal_id);
CREATE INDEX idx_inventory_daily_lookup    ON inventory_daily (business_id, date);
CREATE INDEX idx_inventory_daily_ingredient ON inventory_daily (business_id, ingredient_id, date);
CREATE INDEX idx_delivery_platform_lookup  ON delivery_platform_config (business_id, platform, effective_date DESC);
-- Vector similarity search (cosine, hnsw) — preciso desde registro cero, mayor uso de RAM
-- hnsw elegido sobre ivfflat porque funciona bien con cualquier volumen de datos (V1 friendly)
CREATE INDEX idx_memory_embedding       ON mepia_memory USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_memory_metadata        ON mepia_memory USING GIN (metadata);
CREATE INDEX idx_memory_business        ON mepia_memory (business_id);
CREATE INDEX idx_memory_status          ON mepia_memory (status) WHERE status IN ('pending_embed', 'failed');
CREATE INDEX idx_memory_created         ON mepia_memory (business_id, created_at DESC);
```

---

## Relaciones

```
businesses (1) ──< documents (N)
businesses (1) ──< transactions (N)
businesses (1) ──< recipes (N)
businesses (1) ──< daily_context (N)          [DEPRECATED]
businesses (1) ──< metric_status (N)
businesses (1) ──< pos_inputs (N)
businesses (1) ──< cash_counts (N)
businesses (1) ──< business_fixed_costs (N)
businesses (1) ──< audit_results (N)
businesses (1) ──< circuit_breaker_state (N)
businesses (1) ──< shift_audit_events (N)
businesses (1) ──< inventory_daily (N)
businesses (1) ──< delivery_platform_config (N)
documents  (1) ──< transactions (N)
-- mepia_memory tiene FK real a businesses (ON DELETE CASCADE) — no más registros huérfanos
businesses (1) ──< mepia_memory (N)
```

---

## Notas de migración

- `001_init.sql`: tablas originales `transactions` y `audit_results` deprecadas
- `002_hybrid_schema.sql`: schema completo con todas las tablas de este documento
- Campos nuevos vs original: `tax_amount`, `supplier_name`, `concept`, `document_reference`, `expense_behavior`, `raw_metadata` en `transactions`
- Nuevas tablas: `businesses`, `business_fixed_costs`, `documents`, `recipes`, `daily_context`, `metric_status`, `unit_conversions`, `pos_inputs`, `cash_counts`, `audit_results`, `circuit_breaker_state`
- `003_memory.sql` ✅: habilita extensión `vector` + crea `mepia_memory` con FK real a `businesses`, columnas `status`, `source_audit_run_id` nullable, embedding `vector(1536)` para `text-embedding-3-small` (1536 dims — decisión fija V1), índice HNSW coseno
- `004_deprecate_daily_context.sql` 🔧: marca `daily_context` como deprecated, remueve índices activos
- `005_api_ingesta_tables.sql` 🔧: crea `shift_audit_events`, `inventory_daily`, `delivery_platform_config` con índices
