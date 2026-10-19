# S1B — Ingesta API (Ruta Primaria)

**Actualización de persistencia — 15-oct-2026:** el agregado POS se guarda por
RPC `upsert_pos_daily`; bloqueo por negocio/fecha, sin borrar duplicados
históricos. Varias filas para la fecha producen conflicto seguro HTTP 409;
otro fallo de guardado, 503, sin continuar como éxito. Contrato 011 aplicado en principal; RPC comprobada
con inserción, actualización y conflicto sin cambios, dentro de ROLLBACK.
Regresión 178 pruebas/41 subpruebas, dos advertencias, 12.67 s, código 0. [Contrato físico](db_schema_pipeline_contract.md)
y [avance real](../../../docs/database_unification.md).

**Capa:** Sequential | **Siguiente nodo:** S2 Gatekeeper
**Archivos relacionados:** `api/main.py`, `db_schema.md`, `s1_ingesta.md`
**Enfoque:** API-First / Headless — JSON estructurado a nivel línea

## Decisión de LLM

No aplica — este nodo es 100% determinístico (validación + mapeo Pydantic). Sin IA.

## Responsabilidad

Recibir datos estructurados de ventas, operación e inventario vía API JSON y persistirlos
en las tablas de Supabase correspondientes. Esta es la **ruta primaria** de ingesta — reemplaza
al PDF/OCR como fuente de datos principal. N01 (POS PDF) queda como fallback para negocios
sin integración API.

## Input — Contrato de Entrada (5 niveles)

El endpoint `POST /ingest/api-event` recibe un payload JSON con 5 capas anidadas.
Cada request contiene un batch de eventos de un mismo día y sucursal.

```python
class APIIngestPayload(BaseModel):
    business_id: UUID
    date: date                          # YYYY-MM-DD
    sucursal_id: str                    # identificador de la sucursal origen

    tickets: list[TicketEvent]          # Nivel 1 — Transacciones
    payments: list[PaymentBreakdown]    # Nivel 3 — Formas de pago (1 por ticket)
    shift_audit: list[ShiftAuditEvent]  # Nivel 4 — Operación/Caja
    inventory: list[InventoryUsageEvent]# Nivel 5 — Inventarios/Costos Teóricos
```

### Nivel 1 — Transacción/Ticket: `TicketEvent`

```python
class TicketEvent(BaseModel):
    order_id: str                       # ID único del ticket en el POS
    timestamp: datetime                 # UTC ISO-8601
    sucursal_id: str
    cajero_id: str | None = None
    mesero_id: str | None = None
    order_type: Literal["Comedor", "Para llevar", "Delivery App"]
    subtotal: Decimal                   # antes de IVA y descuentos
    tax: Decimal                        # IVA — debe ser ≈ 16% de subtotal
    discounts: Decimal = Decimal("0")   # descuentos aplicados
    total_net: Decimal                  # subtotal + tax - discounts
    items: list[ProductLine]            # Nivel 2 — detalle de productos
```

### Nivel 2 — Detalle de Producto: `ProductLine`

```python
class ProductLine(BaseModel):
    item_id: str                        # ID del producto en catálogo POS
    product_name: str
    group: str                          # categoría principal (ej. "Bebidas calientes")
    subgroup: str | None = None         # subcategoría (ej. "Espresso")
    variant_modifier: str | None = None # modificadores (ej. "extra shot", "leche avena")
    unit_price: Decimal                 # precio unitario sin descuento
    quantity: int                       # Field(ge=1)
    item_discount: Decimal = Decimal("0")
```

### Nivel 3 — Formas de Pago: `PaymentBreakdown`

```python
class PaymentBreakdown(BaseModel):
    order_id: str                       # FK lógico a TicketEvent.order_id
    efectivo: Decimal = Decimal("0")
    tarjeta_clip: Decimal = Decimal("0")
    uber_eats: Decimal = Decimal("0")
    rappi: Decimal = Decimal("0")
    didi_food: Decimal = Decimal("0")
    cortesia_staff: Decimal = Decimal("0")
    tarjetas_lealtad: Decimal = Decimal("0")
```

### Nivel 4 — Operación/Caja/Auditoría: `ShiftAuditEvent`

```python
class CancellationRecord(BaseModel):
    order_id: str
    motivo: str
    responsable: str                    # cajero/mesero que canceló
    timing: Literal["pre_comanda", "post_comanda"]

class ShiftData(BaseModel):
    turno: str                          # ej. "matutino", "vespertino"
    apertura: Decimal                   # fondo de apertura del turno
    cierre_x: Decimal                   # lectura X (parcial)
    cierre_z: Decimal                   # lectura Z (cierre final)
    sobrante_faltante: Decimal          # positivo = sobrante, negativo = faltante

class ClockRecord(BaseModel):
    employee_id: str
    clock_in: datetime
    clock_out: datetime | None = None   # null si turno aún abierto

class ShiftAuditEvent(BaseModel):
    sucursal_id: str
    date: date
    cancellations: list[CancellationRecord] = []
    reprints: int = 0                   # número de reimpresiones de tickets
    shifts: list[ShiftData]             # al menos 1 turno por día
    clock_records: list[ClockRecord] = []
```

### Nivel 5 — Inventarios/Costos Teóricos: `InventoryUsageEvent`

```python
class InventoryUsageEvent(BaseModel):
    ingredient_id: str                  # ID del insumo en catálogo
    ingredient_name: str
    unit: str                           # unidad base (g, ml, unidad)
    consumo_teorico: Decimal            # consumo teórico del día por recetas vendidas
    waste_recorded: Decimal = Decimal("0")  # merma registrada manualmente
    current_stock: Decimal              # existencia actual
    unit_cost: Decimal                  # costo unitario de la última compra
```

---

## Mapeo a tablas existentes en `db_schema.md`

| Nivel API           | Tabla destino         | Campos mapeados / Notas                                   |
|---------------------|-----------------------|------------------------------------------------------------|
| `TicketEvent`       | `pos_inputs`          | Agrega a `total_sales`, `cash_sales` (calculado desde PaymentBreakdown), `num_transactions` += 1 |
| `TicketEvent`       | `transactions`        | 1 registro tipo="ingreso", category="venta", amount=total_net |
| `ProductLine`       | `transactions.raw_metadata` | Detalle de items guardado en JSONB para trazabilidad |
| `PaymentBreakdown`  | `pos_inputs`          | Suma `efectivo` → `cash_sales`, suma no-efectivo → `card_sales` |
| `ShiftAuditEvent`   | `cash_counts`         | Mapeo: `apertura` → `initial_float`, `cierre_z` → `actual_counted` por turno |
| `ShiftAuditEvent`   | `shift_audit_events` (NUEVA) | Cancellations, reprints, clock_records — ver extensión abajo |
| `InventoryUsageEvent` | `inventory_daily` (NUEVA) | Snapshot diario de consumo teórico, merma, stock, costo |

### Tablas nuevas requeridas (agregar a `db_schema.md`)

**`shift_audit_events`** — Eventos de auditoría operativa por turno:

| Campo              | Tipo         | Notas                                    |
|--------------------|--------------|------------------------------------------|
| id                 | uuid PK      | gen_random_uuid()                        |
| business_id        | uuid FK      | → businesses.id                          |
| sucursal_id        | text         |                                          |
| date               | date         |                                          |
| turno              | text         | "matutino", "vespertino", etc.           |
| apertura           | numeric(12,2)| fondo de apertura                        |
| cierre_x           | numeric(12,2)| lectura X                                |
| cierre_z           | numeric(12,2)| lectura Z                                |
| sobrante_faltante  | numeric(12,2)| positivo = sobrante                      |
| cancellations      | jsonb        | array de CancellationRecord              |
| reprints           | int          | default 0                                |
| clock_records      | jsonb        | array de ClockRecord                     |
| created_at         | timestamptz  | default now()                            |

**`inventory_daily`** — Snapshot diario de inventario/costos teóricos:

| Campo              | Tipo         | Notas                                    |
|--------------------|--------------|------------------------------------------|
| id                 | uuid PK      | gen_random_uuid()                        |
| business_id        | uuid FK      | → businesses.id                          |
| date               | date         |                                          |
| ingredient_id      | text         | ID del insumo en catálogo POS            |
| ingredient_name    | text         |                                          |
| unit               | text         | unidad base (g, ml, unidad)              |
| consumo_teorico    | numeric(12,4)| consumo teórico por recetas vendidas     |
| waste_recorded     | numeric(12,4)| merma registrada                         |
| current_stock      | numeric(12,4)| existencia actual                        |
| unit_cost          | numeric(12,4)| costo unitario última compra             |
| created_at         | timestamptz  | default now()                            |

**Índices nuevos:**
```sql
CREATE INDEX idx_shift_audit_lookup ON shift_audit_events (business_id, date, sucursal_id);
CREATE INDEX idx_inventory_daily_lookup ON inventory_daily (business_id, date);
CREATE INDEX idx_inventory_daily_ingredient ON inventory_daily (business_id, ingredient_id, date);
```

---

## Heurísticas (Python/SQL — sin LLM)

### Reglas de validación de integridad (pre-S2 Gatekeeper)

Estas validaciones se aplican como **controles silenciosos** antes de persistir.
No generan hallazgos de negocio — solo garantizan integridad del dato.

| # | Validación                                      | Acción si falla                                      |
|---|--------------------------------------------------|------------------------------------------------------|
| 1 | `tax ≈ subtotal × 0.16` (tolerancia ±2%)        | Flag `tax_mismatch: true` en `raw_metadata`, persistir igualmente |
| 2 | `total_net ≈ subtotal + tax - discounts` (±$1 MXN) | Flag `total_inconsistency: true`, persistir          |
| 3 | `Σ PaymentBreakdown == TicketEvent.total_net`    | Flag `payment_mismatch: true`, persistir             |
| 4 | `quantity >= 1` en cada ProductLine              | Rechazar el item, persistir resto del ticket         |
| 5 | `order_id` único por (business_id, date)         | Idempotencia — si ya existe, skip (no duplicar)      |
| 6 | `shifts` no vacío en ShiftAuditEvent             | Rechazar el ShiftAuditEvent completo, warning        |
| 7 | `current_stock >= 0` en InventoryUsageEvent      | Flag `negative_stock: true`, persistir               |
| 8 | `unit_cost > 0` en InventoryUsageEvent           | Flag `zero_cost: true`, persistir con warning        |
| 9 | `date` no en el futuro                           | Rechazar payload completo, HTTP 422                  |
| 10| `business_id` existe en `businesses`             | Rechazar, HTTP 404                                   |

**Política de flags:** Los flags (tax_mismatch, payment_mismatch, etc.) se guardan en
`transactions.raw_metadata` o en la tabla destino correspondiente. S2 Gatekeeper puede
consultarlos para decidir si la métrica es `active` o `blocked`.

---

## Output — `APIIngestResult`

```python
class APIIngestResult(BaseModel):
    business_id: UUID
    date: date
    sucursal_id: str
    tickets_received: int
    tickets_persisted: int
    tickets_skipped: int                # duplicados por idempotencia
    validation_flags: list[str]         # flags de integridad detectados
    inventory_records: int
    shift_records: int
    status: Literal["success", "partial", "rejected"]
    # success = todo OK
    # partial = algunos items rechazados pero batch persistido
    # rejected = payload completo rechazado (fecha futura, business no existe)
```

---

## Reglas de generación de warnings

| Condición                                         | Warning                                               |
|---------------------------------------------------|-------------------------------------------------------|
| `tax_mismatch: true` en ≥1 ticket                 | `"IVA inconsistente detectado en N tickets"`          |
| `payment_mismatch: true` en ≥1 ticket             | `"Descuadre entre formas de pago y total_net"`        |
| `negative_stock: true` en ≥1 item                 | `"Stock negativo reportado — posible error de conteo"`|
| `tickets_skipped > 0`                             | `"N tickets duplicados ignorados (idempotencia)"`     |
| ShiftAuditEvent rechazado por shifts vacío         | `"Evento de turno sin datos de shift — rechazado"`    |

---

## Acceptance Criteria

- WHEN payload válido → persistir en tablas correspondientes, retornar `status: "success"`
- WHEN `tax != subtotal × 0.16 ± 2%` → flag silencioso, persistir igualmente
- WHEN `order_id` duplicado → skip sin error, incrementar `tickets_skipped`
- WHEN `date` en el futuro → HTTP 422, rechazar todo el payload
- WHEN `business_id` no existe → HTTP 404
- WHEN algunos items fallan validación → `status: "partial"`, persistir lo válido
- WHEN todos los tickets fallan → `status: "rejected"` si no se persiste nada
- WHEN batch grande (>500 tickets) → procesar en chunks de 100 (no bloquear endpoint)
- WHEN `InventoryUsageEvent` recibido → persistir en `inventory_daily`, disponible para S3

---

## Edge Cases

- Ticket con `discounts > subtotal` → flag `excessive_discount: true`, persistir
- `PaymentBreakdown.order_id` sin `TicketEvent` correspondiente → rechazar esa PaymentBreakdown, warning
- `ShiftData` con `cierre_z < apertura` (faltante grande) → persistir, S3 lo evaluará
- `ClockRecord.clock_out = null` → turno abierto, persistir como está
- Múltiples `ShiftAuditEvent` para mismo turno → usar el más reciente (por created_at)
- `ingredient_id` no existe en `recipes` → persistir igualmente (el catálogo API puede tener más items)

---

## Correctness Properties (PBT)

| ID | Propiedad |
|----|-----------|
| P1 | `tickets_persisted + tickets_skipped == tickets_received` siempre |
| P2 | `order_id` duplicado → nunca genera registro nuevo en `transactions` |
| P3 | `status: "rejected"` → cero registros nuevos en cualquier tabla |
| P4 | `tax_mismatch` flag no impide persistencia — dato se guarda siempre |
| P5 | `Σ(PaymentBreakdown campos)` se verifica contra `TicketEvent.total_net` para cada ticket |
| P6 | `date` en el futuro → HTTP 422, sin efectos secundarios en DB |
| P7 | Idempotencia: enviar mismo payload 2 veces → mismo estado final en DB |
| P8 | `inventory_daily` tiene exactamente 1 registro por (business_id, date, ingredient_id) — upsert |

---

## Nota sobre S3

S3 Motor de Cálculo debe leer de `shift_audit_events` e `inventory_daily` para las métricas
nuevas de Tarea 3 (calc_shift_cash_variance, calc_cancellation_rate, calc_reprint_rate,
calc_labor_cost_ratio, calc_waste_cost, calc_stock_days_remaining).

La tabla `delivery_platform_config` (ver `db_schema.md`) provee las tasas de comisión para
`calc_delivery_commission_cost` — S3 lee de ahí, nunca asume tasa fija en código.
