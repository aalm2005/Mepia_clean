# S3 — Motor de Cálculo (Python)

**Capa:** Sequential | **Anterior:** S2 Gatekeeper | **Siguiente:** S4 Forensic CFO
**Archivo de implementación:** `agents/calc_engine.py`
**Responsabilidad:** Cálculos financieros puros. Sin IA, sin interpretación, solo números.

## Reglas de Oro

1. Cero cálculos en LLM — agentes solo leen resultados de estas funciones
2. Normalización de unidades obligatoria antes de operar
3. División por cero o dato faltante → `status: "incomplete_data"`, nunca romper el proceso
4. Solo opera sobre métricas con `status: "active"` del Gatekeeper

## Principio de Diseño — Desagregación por Responsable (Dimensión Estándar)

> **Origen:** El patrón "un responsable concentra el problema, pero el agregado del día
> lo diluye" apareció tres veces independientes al construir el set de evaluación
> (cancelaciones, reimpresiones, descuentos, cortesías). No es casualidad — es información
> real sobre cómo se manifiestan los problemas reales en un negocio con varios cajeros/meseros.

**Regla:** En vez de agregar `por_responsable` función por función como excepción,
se trata como una **dimensión estándar** disponible en cualquier métrica **Tipo B**
(métricas que tienen sentido desagregadas por persona):

| Métrica Tipo B (con desagregación)   | Campo de agrupación              |
|--------------------------------------|----------------------------------|
| `calc_cancellation_rate`             | `cancellations.responsable`      |
| `calc_reprint_rate`                  | `responsable` (si POS lo entrega)|
| `calc_discount_rate`                 | `cajero_id` / `mesero_id`        |
| `calc_staff_courtesy_ratio`          | `cajero_id` / `mesero_id`        |

**No aplica a:**
- `calc_shift_cash_variance` — ya es por turno, no por persona
- Métricas de inventario — no tienen responsable asociado
- `calc_payment_mix`, `calc_channel_mix` — dimensión es canal, no persona

**Implementación:** Toda métrica Tipo B retorna en su `context` un campo
`by_responsable: dict[str, {count, pct_of_total, ...}]` además del valor agregado.
El valor principal (`value`) sigue siendo el agregado del día/turno. La desagregación
es contexto para que S4/N11 detecten concentraciones anómalas.

## Principio de Diseño — Base de Cálculo para Ratios "% de ventas"

> **Origen:** Encontrado en revisión ciega del Caso 8 del eval set. Dos cálculos
> independientes del mismo día dieron 12.4% y 9.63% para el mismo `staff_courtesy_ratio`
> porque uno usaba `subtotal` y otro `total_net` como denominador.

**Regla:** Todo ratio "% de ventas" (`calc_discount_rate`, `calc_staff_courtesy_ratio`,
y cualquier ratio nuevo de este tipo que se agregue después) **debe usar `subtotal`
como denominador — nunca `total_net`**.

**Razón:** `total_net` ya trae restado el descuento/cortesía de OTRAS órdenes del mismo
periodo, lo que distorsiona el ratio cuando dos anomalías coinciden en la misma persona.
Usar `subtotal` como base (ventas brutas antes de descuentos) evita la contaminación
cruzada y produce un número estable independiente del orden de cálculo.

## Distinción Fijo vs Variable — Flujo API-First

`expense_behavior` (ENUM: `FIXED` | `VARIABLE` | `CAPEX`) en `transactions`.

Flujo de confirmación vía API (ver contrato completo en `n03_human_input_endpoints.md`):
```
1. S1/N02 extrae gasto → expense_behavior = null en transactions
2. Cliente consulta GET /transactions/pending-review para ver pendientes
3. Sistema sugiere expense_behavior por supplier_name/concept (nunca persiste automáticamente)
4. Cliente envía PATCH /transactions/{id}/expense-behavior con valor confirmado
5. Solo tras confirmación → gasto disponible para S3
```
S3 nunca asume `expense_behavior` — solo usa gastos con valor confirmado explícitamente.

## Normalización de Unidades

| Unidad origen | Unidad base | Factor |
|---------------|-------------|--------|
| kg            | g           | × 1000 |
| L             | ml          | × 1000 |
| unidad        | unidad      | × 1    |

Unidades incompatibles → `status: "unit_mismatch"`, no calcular.

## Formato de respuesta — `CalcResult`

```json
{
  "metric": "merma_leche",
  "value": 12.5,
  "unit": "litros",
  "status": "ok | warning | critical | incomplete_data | unit_mismatch",
  "context": "Se compraron 100L, se debieron usar 87.5L según recetas."
}
```

## Funciones auxiliares puras

### `normalize_units(value, from_unit, to_unit, conversions) -> Decimal | None`
Convierte entre unidades usando la lista `conversions` (ya cargada desde DB).
- `from_unit == to_unit` → retorna value sin cambio.
- Sin conversión disponible → retorna `None` (el caller emite `unit_mismatch`).

### `days_in_month(date_str) -> int`
Retorna días reales del mes (28/29/30/31) para una fecha YYYY-MM-DD.
Usa `calendar.monthrange` — respeta años bisiestos. NUNCA retorna 30 fijo.

## Funciones

### `calc_contribution_margin(product_id, db)`
```
MC = precio_venta - sum(ingrediente_qty × precio_unitario)
```
- `precio_unitario`: última factura del ingrediente en `transactions`.
- Edge: sin receta → `incomplete_data`; ingrediente sin factura → `incomplete_data`.

### `calc_daily_break_even(business_id, date)`
```
PE_unidades = (sum(FIXED expenses del mes) / days_in_month(date)) / MC_promedio
```
Usa solo `transactions` con `expense_behavior = "FIXED"` confirmado vía API.
Divisor: `days_in_month(date)` — NUNCA 30 fijo.
Edge: MC_promedio = 0 → `incomplete_data`; sin gastos FIXED → `incomplete_data`

### `calc_waste_analysis(ingredient_id, start_date, end_date, business_id, db)`
```
merma_pct = (comprado_base - consumo_teorico_base) / comprado_base × 100
```
- Normalizar unidades con `unit_conversions` antes de restar.
- `consumo_teorico` = sum(ventas_producto × qty_ingrediente_en_receta) desde `pos_inputs`.
- Edge: unidades incompatibles → `unit_mismatch`; sin compras → `incomplete_data`.

### `calc_burn_rate(business_id, date)`
```
BR = sum(FIXED + VARIABLE expenses del mes) / days_in_month(date)
```
Divisor: `days_in_month(date)` — NUNCA 30 fijo.
Edge: sin gastos confirmados → `incomplete_data`. Sin umbrales (siempre "ok" si hay datos).

### `check_price_inflation(ingredient_id, business_id, db)`
```
delta_pct = ((precio_ultima_factura - precio_promedio_anteriores) / precio_promedio_anteriores) × 100
```
- Facturas ordenadas por `transaction_date DESC`; la primera es la más reciente.
- Edge: solo 1 factura → `incomplete_data`; precio_promedio = 0 → `incomplete_data`.

### `calc_cash_reconciliation(business_id, date, db)`
```
expected_cash = initial_float + pos_cash_sales - refunds - cash_payouts
variance      = actual_cash_counted - expected_cash
variance_pct  = variance / pos_cash_sales × 100  (si pos_cash_sales > 0)
```
- Input: `pos_inputs` (cash_sales, refunds) + `cash_counts` (initial_float, actual_counted, cash_payouts).
- `value`: variance en MXN.
- Si `pos_cash_sales = 0` → usar variance absoluta para determinar status.
- Edge: sin pos_inputs o sin cash_counts → `incomplete_data`.

---

## Funciones — Nivel Transacción (nuevas, requieren S1B API)

### `calc_avg_ticket(business_id, start_date, end_date, db) -> CalcResult`
```
avg_ticket = Σ(total_net de tickets) / COUNT(tickets)
```
- Input: `transactions` tipo="ingreso", category="venta" en rango de fechas.
- Unidad: `"MXN"`.
- Status: `ok` por defecto — umbrales definidos en Tarea 5.
- Edge: 0 tickets en el periodo → `status: "incomplete_data"`, `value: null`.

### `calc_ticket_volume(business_id, date, granularity, db) -> CalcResult`
```
ticket_count = COUNT(transactions WHERE type="ingreso" AND category="venta")
```
- Input: `transactions` + `shift_audit_events` (para agrupar por turno si `granularity="turno"`).
- `granularity`: `"turno"` | `"dia"`.
- Unidad: `"tickets"`.
- Edge: sin datos → `status: "incomplete_data"`.

### `calc_channel_mix(business_id, date, db) -> CalcResult`
```
Para cada order_type ∈ {Comedor, Para llevar, Delivery App}:
  pct = Σ(total_net WHERE order_type) / Σ(total_net total) × 100
```
- Input: `transactions.raw_metadata` (donde se guarda `order_type` de S1B).
- Unidad: `"%"` — `value` es un dict `{order_type: pct}` serializado.
- Edge: sin datos de `order_type` (ingestas legacy PDF) → `status: "incomplete_data"`.

### `calc_discount_rate(business_id, start_date, end_date, db) -> CalcResult`
```
discount_rate = Σ(discounts) / Σ(subtotal) × 100

# Desagregación por responsable (dimensión estándar Tipo B)
by_responsable = GROUP BY cajero_id/mesero_id:
  {staff_id: {discount_total: Decimal, subtotal: Decimal, rate_pct: float}}
```
- Input: `transactions.raw_metadata` (campos `discounts`, `subtotal`, `cajero_id`/`mesero_id` de S1B).
- Unidad: `"%"`.
- **Tipo B:** Incluye desagregación por responsable en `context.by_responsable` (ver principio de diseño arriba).
- Edge: `Σsubtotal = 0` → `status: "incomplete_data"`.

### `calc_hourly_sales_pattern(business_id, date, db) -> CalcResult`
```
Para cada hora H en rango [open_hour, close_hour] de businesses.operating_hours:
  sales_H = Σ(total_net WHERE EXTRACT(HOUR FROM timestamp) = H)

hora_pico = H con mayor sales_H
hora_valle = H con menor sales_H (excluyendo horas con 0 tickets)

value = { "hora_pico": H_pico, "ventas_pico": sales_pico,
           "hora_valle": H_valle, "ventas_valle": sales_valle }
```
- Input: `transactions` (campo `timestamp` de S1B guardado en raw_metadata o derivado del TicketEvent).
- Unidad: `"resumen"` — **solo retorna hora pico y hora valle, nunca la serie horaria completa** (evitar ruido).
- Edge: <3 horas con ventas → `status: "incomplete_data"`. Día sin tickets → `status: "incomplete_data"`.

### `calc_sales_by_staff(business_id, date, db) -> CalcResult`
```
Para cada cajero_id/mesero_id:
  sales_staff = Σ(total_net WHERE cajero_id = X OR mesero_id = X)
  ticket_count_staff = COUNT(tickets del staff)
```
- Input: `transactions.raw_metadata` (campos `cajero_id`, `mesero_id` de S1B).
- Unidad: `"MXN"` — `value` = dict `{staff_id: {total: Decimal, tickets: int}}`.
- **⚠️ Dato sensible de personal:** Su exposición en el reporte final (N11/N14) debe ser
  agregada/con umbral (ej. solo alertar si un staff tiene >40% de las cancelaciones),
  no un ranking rutinario que se muestre siempre al dueño. Documentar esta restricción
  en N11 y N14 al consumir esta métrica.
- Edge: sin `cajero_id` ni `mesero_id` (ingestas legacy PDF) → `status: "incomplete_data"`.

### `calc_sales_by_branch(business_id, date, db) -> CalcResult`
```
Para cada sucursal_id:
  sales_branch = Σ(total_net WHERE sucursal_id = X)
  ticket_count_branch = COUNT(tickets)
```
- Input: `transactions.raw_metadata` (campo `sucursal_id` de S1B).
- Unidad: `"MXN"` — `value` = dict `{sucursal_id: {total: Decimal, tickets: int}}`.
- **Prerequisito:** Solo se ejecuta si `businesses.multi_sucursal = true` (ver campo en db_schema).
  Si es una sola sucursal, la función **ni se llama** — S2 Gatekeeper no la marca como `active`.
- Edge: campo `multi_sucursal` no existe o es false → función no invocada (no es `incomplete_data`, simplemente no aplica).

---

## Funciones — Nivel Producto (nuevas)

### `calc_top_bottom_sellers(business_id, start_date, end_date, top_n, db) -> CalcResult`
```
ranking_qty = ProductLine agrupado por product_name, ORDER BY Σ(quantity) DESC
ranking_rev = ProductLine agrupado por product_name, ORDER BY Σ(unit_price × quantity) DESC
top = ranking[:top_n]
bottom = ranking[-top_n:]
```
- Input: `transactions.raw_metadata` → items (ProductLine[] persistidos por S1B).
- `top_n`: default 5.
- Unidad: `"ranking"` — `value` es dict `{top_by_qty, bottom_by_qty, top_by_revenue, bottom_by_revenue}`.
- Edge: sin datos de ProductLine → `status: "incomplete_data"`.

### `calc_revenue_concentration(business_id, start_date, end_date, db) -> CalcResult`
```
Pareto 80/20:
  Ordenar productos por revenue DESC
  concentration_index = % de productos que acumulan 80% del revenue
```
- Input: mismo que calc_top_bottom_sellers.
- Unidad: `"%"` — `value` = porcentaje de SKUs que concentran 80% del ingreso.
- Status: valor bajo (<20%) = alta concentración (pocos productos dominan).
- Edge: <3 productos → `status: "incomplete_data"`.

### `check_price_consistency(business_id, date, db) -> CalcResult`
```
Para cada item vendido en `date`:
  expected_price = recipes.sale_price WHERE product_name matches
  actual_price = ProductLine.unit_price
  IF abs(actual_price - expected_price) / expected_price > 0.05 → flag inconsistencia
```
- Input: `transactions.raw_metadata` (items) + `recipes.sale_price`.
- **Nota:** esto es una excepción/verificación puntual, no una serie completa.
- Unidad: `"items"` — `value` = count de items con precio inconsistente.
- Edge: producto sin receta → skip (no es error). Sin items → `status: "incomplete_data"`.

### `calc_category_mix(business_id, start_date, end_date, db) -> CalcResult`
```
Para cada group (y opcionalmente subgroup):
  pct = Σ(unit_price × quantity WHERE group = X) / Σ(total revenue) × 100
```
- Input: `transactions.raw_metadata` → items (ProductLine[] con `group` y `subgroup`).
- Unidad: `"%"` — `value` = dict `{group: pct, ...}`. Context incluye desglose por subgroup.
- Edge: sin datos de ProductLine → `status: "incomplete_data"`. Items sin `group` → skip.

### `calc_modifier_attach_rate(business_id, start_date, end_date, db) -> CalcResult`
```
lines_with_modifier = COUNT(ProductLine WHERE variant_modifier IS NOT NULL AND variant_modifier != "")
total_lines = COUNT(ProductLine)

attach_rate = lines_with_modifier / total_lines × 100
```
- Input: `transactions.raw_metadata` → items (campo `variant_modifier` de S1B).
- Unidad: `"%"` — tasa de upsell (qué % de líneas de venta llevan un modificador/extra).
- Edge: 0 líneas → `status: "incomplete_data"`. Ningún modifier → `value: 0`, `status: "ok"`.

### `calc_item_discount_split(business_id, date, db) -> CalcResult`
```
item_level_discount = Σ(ProductLine.item_discount) por ticket
ticket_level_discount = TicketEvent.discounts - item_level_discount

split = {
  "item_discount_total": item_level_discount,
  "ticket_discount_total": ticket_level_discount,
  "item_discount_pct": item_level_discount / (item_level + ticket_level) × 100,
  "ticket_discount_pct": ticket_level_discount / (item_level + ticket_level) × 100
}
```
- Input: `transactions.raw_metadata` (campos `discounts` del ticket + `item_discount` de ProductLine).
- Unidad: `"MXN"` — `value` = dict con el split. Context explica proporción.
- **Nota de diseño:** Separar descuento a nivel item (cortesía puntual, ej. "esta bebida va por la casa")
  vs descuento a nivel ticket completo (descuento generalizado, ej. "10% por aniversario").
  Permite a S4/N11 distinguir patrones de cortesía interna de políticas comerciales.
- Edge: sin descuentos → ambos en 0, `status: "ok"`. Sin items → `status: "incomplete_data"`.

---

## Funciones — Nivel Forma de Pago (nuevas)

### `calc_payment_mix(business_id, date, db) -> CalcResult`
```
Para cada forma de pago ∈ PaymentBreakdown:
  pct = Σ(monto_forma) / Σ(total_net de todos los tickets) × 100
```
- Input: `pos_inputs` (cash_sales, card_sales) + `transactions.raw_metadata` (PaymentBreakdown detallado de S1B).
- Unidad: `"%"` — `value` es dict `{efectivo: pct, tarjeta_clip: pct, uber_eats: pct, ...}`.
- Edge: sin datos de pago → `status: "incomplete_data"`.

### `calc_delivery_commission_cost(business_id, date, db) -> CalcResult`
```
Para cada plataforma ∈ {UberEats, Rappi, DiDiFood}:
  ventas_plataforma = Σ(PaymentBreakdown.{plataforma})
  tasa = delivery_platform_config WHERE business_id AND platform AND effective_date <= date
         ORDER BY effective_date DESC LIMIT 1
  comision = ventas_plataforma × tasa.commission_rate

total_commission = Σ(comisiones de todas las plataformas)
```
- Input: `transactions.raw_metadata` (PaymentBreakdown) + `delivery_platform_config`.
- Unidad: `"MXN"` — `value` = total_commission. Context incluye desglose por plataforma.
- **Dependencia:** Lee `delivery_platform_config` — nunca asume tasa fija en código.
- Edge: plataforma sin configuración → `status: "incomplete_data"` para esa plataforma (reportar cuáles faltan).
- Edge: sin ventas delivery en el día → `value: 0`, `status: "ok"`.

### `calc_staff_courtesy_ratio(business_id, date, db) -> CalcResult`
```
courtesy_ratio = Σ(PaymentBreakdown.cortesia_staff) / Σ(subtotal) × 100

# Desagregación por responsable (dimensión estándar Tipo B)
# Requiere cruzar PaymentBreakdown con cajero_id/mesero_id del TicketEvent asociado
by_responsable = GROUP BY cajero_id/mesero_id:
  {staff_id: {courtesy_total: Decimal, pct_of_all_courtesy: float}}
```
- Input: `transactions.raw_metadata` (PaymentBreakdown + cajero_id/mesero_id del ticket, `subtotal` del ticket).
- Unidad: `"%"`.
- **Tipo B:** Incluye desagregación por responsable en `context.by_responsable` — mismo hallazgo
  de diseño que `calc_cancellation_rate` (una persona dando cortesías desproporcionadas se diluye en el agregado).
- **Base de cálculo:** Usa `subtotal` como denominador, nunca `total_net` (ver principio de diseño arriba).
- Edge: sin ventas (Σsubtotal = 0) → `status: "incomplete_data"`. Cortesía = 0 → `value: 0`, `status: "ok"`.

### `calc_loyalty_redemption_cost(business_id, date, db) -> CalcResult`
```
loyalty_total = Σ(PaymentBreakdown.tarjetas_lealtad)
loyalty_pct = loyalty_total / Σ(subtotal) × 100
```
- Input: `transactions.raw_metadata` (campo `tarjetas_lealtad` de PaymentBreakdown).
- Unidad: `"MXN"` — `value` = loyalty_total. Context incluye `loyalty_pct`.
- **Nota:** Representa el costo real de canje del programa de lealtad como forma de pago.
  Permite medir cuánto revenue se "pierde" por canjes vs ventas totales.
- Edge: sin ventas → `status: "incomplete_data"`. tarjetas_lealtad = 0 → `value: 0`, `status: "ok"`.

---

## Funciones — Nivel Operación/Caja (nuevas)

### `calc_cancellation_rate(business_id, date, db) -> CalcResult`
```
cancellations = shift_audit_events.cancellations (JSONB array) para business_id + date
total_tickets = COUNT(tickets del día)

cancellation_rate = COUNT(cancellations) / total_tickets × 100
pre_comanda_pct = COUNT(WHERE timing="pre_comanda") / COUNT(cancellations) × 100
post_comanda_pct = COUNT(WHERE timing="post_comanda") / COUNT(cancellations) × 100

# Desagregación por responsable (OBLIGATORIA — requisito de diseño)
by_responsable = GROUP BY cancellations.responsable:
  {responsable: {count: int, pct_of_total: float, pre: int, post: int}}
```
- Input: `shift_audit_events` + `pos_inputs.num_transactions` (o count de transactions).
- Unidad: `"%"` — `value` = cancellation_rate total. Context incluye desglose pre/post **y por responsable**.
- **Desagregación por responsable:** Sin ella, un patrón concentrado en una sola persona
  se diluye entre el resto del personal normal y no se detecta. Esto es un requisito de diseño
  (salido del ground truth), no un nice-to-have. S4/N11 deben poder ver si un cajero/mesero
  específico tiene cancelaciones desproporcionadas.
- Edge: 0 tickets → `status: "incomplete_data"`. 0 cancelaciones → `value: 0`, `status: "ok"`.

### `calc_reprint_rate(business_id, date, db) -> CalcResult`
```
reprints = Σ(shift_audit_events.reprints) para business_id + date
total_tickets = COUNT(tickets del día)

reprint_rate = reprints / total_tickets × 100

# Desagregación por responsable (misma razón que calc_cancellation_rate)
# Requiere que shift_audit_events guarde reprints asociados a un responsable.
# En v1, si el POS no entrega responsable por reprint, reportar solo el total.
```
- Input: `shift_audit_events` + count de tickets.
- Unidad: `"%"`.
- **Desagregación por responsable:** Misma lógica que `calc_cancellation_rate` — un patrón
  de reimpresiones concentrado en una persona es señal de fraude potencial (reimprimir para
  cobrar doble o anular cobro). Si el POS no entrega responsable por reprint en v1,
  reportar solo el total y documentar como limitación.
- Edge: 0 tickets → `status: "incomplete_data"`. 0 reprints → `value: 0`, `status: "ok"`.

### `calc_shift_cash_variance(business_id, date, db) -> CalcResult`
```
Para cada turno en shift_audit_events:
  variance = sobrante_faltante (ya calculado por el POS)
  # Extensión de calc_cash_reconciliation a granularidad de turno

Retorna array de varianzas por turno con detalle:
  {turno, apertura, cierre_z, sobrante_faltante, variance_pct}
```
- Input: `shift_audit_events` (shifts: apertura, cierre_x, cierre_z, sobrante_faltante).
- Unidad: `"MXN"` — `value` = Σ(sobrante_faltante) del día. Context = desglose por turno.
- Edge: sin shift_audit_events → `status: "incomplete_data"`.

### `calc_labor_cost_ratio(business_id, date, db) -> CalcResult`
```
horas_trabajadas = Σ(clock_out - clock_in) de shift_audit_events.clock_records
costo_hora = (se necesita fuente — v1 usa Σ(FIXED costs WHERE concept ILIKE '%nómina%') / 30 / 8)
labor_cost = horas_trabajadas × costo_hora_estimado
labor_ratio = labor_cost / total_sales × 100
```
- Input: `shift_audit_events.clock_records` + `pos_inputs.total_sales` + `business_fixed_costs`.
- Unidad: `"%"`.
- **Nota v1:** el costo por hora es una estimación basada en nómina fija / días / horas.
  En versiones futuras se integrará un catálogo de salarios por empleado.
- Edge: sin clock_records → `status: "incomplete_data"`. total_sales = 0 → `status: "incomplete_data"`.

### `calc_sales_per_labor_hour(business_id, date, db) -> CalcResult`
```
horas_trabajadas = Σ(clock_out - clock_in) de shift_audit_events.clock_records
sales_per_hour = pos_inputs.total_sales / horas_trabajadas
```
- Input: `shift_audit_events.clock_records` + `pos_inputs.total_sales`.
- Unidad: `"MXN/hora"` — productividad laboral.
- **Nota:** No requiere dato de salario, solo horas trabajadas. Complementa a `calc_labor_cost_ratio`
  dando una vista de productividad pura sin depender de la estimación de costo por hora.
- Edge: sin clock_records → `status: "incomplete_data"`. horas_trabajadas = 0 → `status: "incomplete_data"`. total_sales = 0 → `value: 0`, `status: "ok"`.

---

## Funciones — Nivel Inventario (nuevas)

### `calc_waste_cost(business_id, date, db) -> CalcResult`
```
waste_cost = Σ(inventory_daily.waste_recorded × inventory_daily.unit_cost)
             WHERE business_id AND date
```
- Input: `inventory_daily`.
- Unidad: `"MXN"` — traduce merma de unidades físicas a pesos.
- Edge: sin registros inventory_daily → `status: "incomplete_data"`. waste_recorded = 0 en todos → `value: 0`, `status: "ok"`.

### `calc_stock_days_remaining(business_id, date, db) -> CalcResult`
```
Para cada ingrediente en inventory_daily:
  consumo_diario_promedio = AVG(consumo_teorico) de últimos 7 días
  days_remaining = current_stock / consumo_diario_promedio

Retorna lista de ingredientes con sus days_remaining.
```
- Input: `inventory_daily` (current_stock, consumo_teorico de últimos 7 días).
- Unidad: `"días"` — `value` = mínimo days_remaining entre todos los ingredientes (alerta temprana).
  Context incluye lista completa.
- Edge: consumo_diario_promedio = 0 para un ingrediente → skip (no se consume). Sin historial → `status: "incomplete_data"`.

---

## Umbrales de status

| Métrica              | warning            | critical                        |
|----------------------|--------------------|--------------------------------------|
| Merma                | merma_pct > 5%     | merma_pct > 10%                      |
| Inflación precio     | delta_abs 5–15%    | delta_abs > 15%                      |
| Conciliación caja    | variance < 0       | variance_pct < -1% de ventas         |
| Margen contribución  | MC_pct < 20%       | MC_pct < 10%                         |
| Burn rate            | —                  | — (siempre "ok" si hay datos)        |
| Punto de equilibrio  | —                  | — (siempre "ok" si hay datos)        |

### Métricas nuevas — condiciones implementadas al 15-oct-2026

Lectura de las condiciones ejecutables de `agents/calc_engine.py`, sin cambios
ni nueva ejecución del motor. Se aplica primero el estado más grave y se
conservan los estados de datos incompletos. Los límites usan comparación estricta:

| Métrica | warning | critical |
|---|---|---|
| Descuentos | >10% | Sin corte adicional |
| Cortesías | Sin corte intermedio | Excedente permitido >5% del subtotal |
| Cancelaciones | >2% | >5% |
| Reimpresiones | >5% | >10% |
| Varianza de caja por turno | Valor absoluto >100 MXN | Valor absoluto >500 MXN |
| Nómina sobre ventas | >30% | >35% |
| Costo monetario de merma | Merma/consumo teórico >5% | >10%; conserva el peor ingrediente |
| Días de inventario | <7 días | <3 días |

El catálogo conceptual del chat explica los resultados emitidos; no recalcula
estos estados. Los valores propuestos originalmente en el documento maestro
son criterios de diseño, no sustituyen las condiciones de cada función.

### Tabla inicial de diseño (histórica, anterior a los umbrales implementados)

La tabla siguiente conserva la clasificación inicial y sus preguntas de diseño.
Sus referencias a umbrales pendientes no describen el comportamiento actual;
consultar arriba y la función correspondiente antes de modificar un estado.

| Métrica                     | Status default | Notas                                          |
|-----------------------------|----------------|------------------------------------------------|
| calc_avg_ticket             | ok             | Requiere baseline por industria/tamaño         |
| calc_ticket_volume          | ok             | Requiere baseline por negocio                  |
| calc_channel_mix            | ok             | No tiene umbral universal                      |
| calc_discount_rate          | ok             | Umbral depende de política del negocio         |
| calc_hourly_sales_pattern   | ok             | Informativo — solo hora pico y hora valle      |
| calc_sales_by_staff         | ok             | ⚠️ Dato sensible — exposición con umbral       |
| calc_sales_by_branch        | ok             | Solo si multi_sucursal: true                   |
| calc_top_bottom_sellers     | ok             | Informativo                                    |
| calc_revenue_concentration  | ok             | Alta concentración puede ser riesgo o no       |
| check_price_consistency     | ok/warning     | >0 inconsistencias → warning (fijo)            |
| calc_category_mix           | ok             | Informativo — desglose por group/subgroup      |
| calc_modifier_attach_rate   | ok             | Tasa de upsell, sin umbral universal           |
| calc_item_discount_split    | ok             | Informativo — distingue cortesía de política   |
| calc_payment_mix            | ok             | Informativo                                    |
| calc_delivery_commission_cost | ok           | Umbral depende de márgenes del negocio         |
| calc_staff_courtesy_ratio   | ok             | Umbral depende de política del negocio         |
| calc_loyalty_redemption_cost| ok             | Umbral depende de programa de lealtad          |
| calc_cancellation_rate      | ok             | Requiere benchmark sectorial + desagregación   |
| calc_reprint_rate           | ok             | Requiere benchmark + desagregación             |
| calc_shift_cash_variance    | ok             | Hereda umbrales de calc_cash_reconciliation    |
| calc_labor_cost_ratio       | ok             | Depende del sector (hospitalidad: 25–35%)      |
| calc_sales_per_labor_hour   | ok             | Productividad — requiere baseline por negocio  |
| calc_waste_cost             | ok             | Depende de merma aceptable por negocio         |
| calc_stock_days_remaining   | ok             | < 2 días podría ser warning, pendiente definir |

## Extensibilidad

Nueva métrica: crear `calc_nueva_metrica()` → retorna `CalcResult`. No modificar funciones existentes. Registrar prerrequisitos en S2.
