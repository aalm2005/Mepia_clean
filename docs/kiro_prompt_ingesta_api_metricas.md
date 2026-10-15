> **Prompt histórico de diseño.** Las tareas siguientes conservan la solicitud
> original; no describen pendientes actuales ni deben reejecutarse sin revisar
> el código. Consultar [avance al 15-oct-2026](estado_actual_mepia.md), las tareas
> realizadas de la sesión y la bitácora antes de continuar.

Estás trabajando en el spec de MEPIA en `.kiro/specs/mepia/`. Antes de escribir nada, carga
`_index.md` y `_glossary.md` completos, más los archivos específicos que se listan en cada tarea
abajo — no cargues el resto del repo.

Vamos a hacer 5 cambios al spec, todos en formato markdown, siguiendo exactamente la estructura
que ya usan los nodos existentes (ver `n09_gastos.md` como referencia de plantilla: `## Decisión
de LLM`, `## Responsabilidad`, `## Input`, `## Heurísticas (Python/SQL — sin LLM)`, `## Output —
NodeResult`, `## Reglas de generación de warnings`, `## Acceptance Criteria`, `## Edge Cases`,
`## Correctness Properties (PBT)`). No inventes secciones nuevas fuera de esa plantilla salvo que
el contenido genuinamente lo requiera.

---

## Tarea 1 — Retirar `contexto del día` del diseño

Contexto: el contexto del día (`daily_context`, tags + texto libre) genera ruido y no aporta al
diseño final. Se elimina, sin reemplazo.

Archivos a tocar:
- `s1_ingesta.md` — quitar `Contexto del día` de los 5 inputs de S1. Actualizar el diagrama/lista
  de inputs a solo: POS/API, Facturas, Recetas (BOM).
- `db_schema.md` — marcar la tabla `daily_context` como deprecated/removed. Si algo más depende
  de ella (revisar `metadata JSONB`, `tags`), documentar el impacto.
- `_index.md` — quitar la referencia a "Contexto del día → tags + texto libre → metadata JSONB"
  del diagrama del pipeline en S1.
- `n05_ceo_orchestrator.md`, `n11_consultor.md` — si alguno de estos toma `daily_context` como
  input, quitar esa dependencia explícitamente.

---

## Tarea 2 — Nuevo nodo de ingesta API (reemplaza al PDF como ruta primaria)

Contexto: la fuente de datos primaria pasa a ser una API que entrega JSON estructurado a nivel
línea, con 5 capas:

1. **Transacción/Ticket**: `order_id`, `timestamp`, `sucursal_id`, `cajero_id`/`mesero_id`,
   `order_type` (Comedor/Para llevar/Delivery App), `subtotal`, `tax` (IVA 16%), `discounts`,
   `total_net`.
2. **Detalle de Producto**: `item_id`, `product_name`, `group`, `subgroup`, `variant_modifier`,
   `unit_price`, `quantity`, `item_discount`.
3. **Formas de Pago**: desglose por `Efectivo`, `Tarjeta_Clip`, `UberEats`, `Rappi`, `DiDiFood`,
   `Cortesía_Staff`, `Tarjetas_Lealtad`.
4. **Operación/Caja/Auditoría**: `cancellations` (motivo, responsable, antes/después de comanda),
   `reprints`, `shift_data` (apertura, cierre X, cierre Z, sobrante/faltante), `clock_in`/`clock_out`.
5. **Inventarios/Costos Teóricos**: `ingredients_usage` (consumo teórico por receta),
   `waste_recorded`, `current_stock`, `unit_cost`.

Crea un nuevo archivo `s1b_ingesta_api.md` (o propón el ID de nodo que corresponda según la
convención de `_index.md`) con:
- El contrato de entrada exacto (los 5 niveles arriba, tipados).
- Cómo se mapea cada nivel a las tablas existentes en `db_schema.md` (extender donde haga falta,
  documentar campos nuevos).
- Reglas de validación de integridad que debe aplicar antes de pasar a S2 Gatekeeper (ej.
  `tax` ≈ 16% × `subtotal`, como control silencioso — no como hallazgo de negocio).
- Actualiza `_index.md`: `N01 POS PDF Input` pasa a estado `✅ done — fallback` con una nota
  explícita de que ya no es la ruta primaria. El nuevo nodo de API queda como ruta primaria.
- Actualiza `_glossary.md` con los nuevos contratos de datos: `TicketEvent`, `ProductLine`,
  `PaymentBreakdown`, `ShiftAuditEvent`, `InventoryUsageEvent`.

---

## Tarea 3 — Extender S3 Motor de Cálculo con el catálogo de métricas nuevo

Archivo: `s3_motor_calculo.md`.

Agregar las siguientes funciones nuevas, siguiendo exactamente el mismo contrato que ya usan
`calc_contribution_margin`, `calc_daily_break_even`, etc. (input tipado + `CalcResult` de salida,
Python puro, sin LLM, nunca lanza excepción — errores se expresan como `status`).

**No incluidas a propósito** (no las agregues): validación de IVA y cumplimiento de Cierre X/Z
son controles de integridad, van en `S2 Gatekeeper`, no como métrica de negocio en S3. Las
funciones de merma, inflación de insumo, y margen de contribución ya existen en el código — no
las reconstruyas, solo verifica que el nuevo input de la API las alimente correctamente.

**Nivel Transacción:**
- `calc_avg_ticket` — ticket promedio por periodo.
- `calc_ticket_volume` — conteo de tickets por turno/día.
- `calc_channel_mix` — % de ventas por `order_type`.
- `calc_discount_rate` — `Σdiscounts / Σsubtotal`, **calculada tanto a nivel turno/día como desagregada por responsable** (`cajero_id`/`mesero_id`). Ver nota de diseño abajo sobre por qué esta dimensión debe ser estándar, no una excepción.
- `calc_hourly_sales_pattern` — devuelve SOLO hora pico y hora valle ya resumidas, nunca la serie
  horaria completa (evitar ruido).
- `calc_sales_by_staff` — ventas por `cajero_id`/`mesero_id`. **Dato sensible de personal** —
  documentar en el spec que su exposición en el reporte final debe ser agregada/con umbral, no un
  ranking rutinario.
- `calc_sales_by_branch` — solo se activa si `multi_sucursal: true` en la config del negocio
  (ver Tarea 4); si es una sola sucursal, la función ni se llama.

**⚠️ Nota de diseño — leer antes de implementar cualquier función de esta tarea**: el patrón "un
responsable concentra el problema, pero el agregado del día lo diluye" apareció tres veces
independientes al construir el set de evaluación (cancelaciones, reimpresiones, descuentos,
cortesías). No es casualidad — es información real sobre cómo se manifiestan los problemas reales
en un negocio con varios cajeros/meseros. En vez de agregar `por_responsable` función por función
como excepción, trátalo como una dimensión estándar disponible en cualquier métrica Tipo B que
tenga sentido desagregada por persona (cancelación, reimpresión, descuento, cortesía — no aplica a
varianza de caja por turno, que ya es por turno, ni a métricas de inventario). Documentar esto
explícitamente en `s3_motor_calculo.md` como principio de diseño, no repetirlo como nota aislada
en cada función.

**⚠️ Segunda nota de diseño — base de cálculo, encontrada en revisión ciega del Caso 8**: todo
ratio "% de ventas" (`calc_discount_rate`, `calc_staff_courtesy_ratio`) debe usar `subtotal` como
denominador — nunca `total_net`. `total_net` ya trae restado el descuento/cortesía de OTRAS
órdenes del mismo periodo, lo que distorsiona el ratio cuando dos anomalías coinciden en la misma
persona (pasó exactamente esto: dos cálculos independientes del mismo día dieron 12.4% y 9.63%
para el mismo `staff_courtesy_ratio`, por esta razón). Fijar `subtotal` como base evita el
problema. Aplica también a cualquier ratio nuevo de este tipo que se agregue después.

**Nivel Producto:**
- `calc_top_bottom_sellers` — ranking por cantidad e ingreso.
- `calc_revenue_concentration` — índice de concentración tipo Pareto 80/20.
- `check_price_consistency` — `unit_price` real vs precio de catálogo esperado (excepción, no
  serie completa).
- `calc_category_mix` — % de ingreso por `group`/`subgroup`.
- `calc_modifier_attach_rate` — % de líneas que llevan `variant_modifier` (tasa de upsell).
- `calc_item_discount_split` — separa descuento a nivel item vs. descuento a nivel ticket
  completo, para distinguir cortesía puntual de descuento generalizado.

**Nivel Forma de Pago:**
- `calc_payment_mix` — % por forma de pago.
- `calc_delivery_commission_cost` — costo real de comisión por canal (UberEats/Rappi/DiDi) usando
  una tasa de comisión configurable por plataforma (nueva tabla de config, ver Tarea 4).
- `calc_staff_courtesy_ratio` — `Cortesía_Staff / ventas totales`, **con la misma desagregación
  por responsable** que `calc_discount_rate` — mismo hallazgo de diseño de arriba.
- `calc_loyalty_redemption_cost` — costo real de canje del programa de lealtad.

**Nivel Operación/Caja:**
- `calc_cancellation_rate` — tasa de cancelación, separando pre- vs post-comanda, **calculada
  tanto a nivel turno/día como desagregada por responsable** (`cajero_id`/`mesero_id`). Sin la
  desagregación por responsable, un patrón concentrado en una sola persona se diluye entre el
  resto del personal normal y no se detecta — esto salió directamente del diseño del ground
  truth, es un requisito, no un nice-to-have.
- `calc_reprint_rate` — tasa de reimpresión de tickets, **con la misma desagregación por
  responsable** que `calc_cancellation_rate`, por la misma razón.
- `calc_shift_cash_variance` — extensión de `calc_cash_reconciliation` existente a granularidad
  de turno (usa `shift_data`: apertura, cierre X, cierre Z, sobrante/faltante).
- `calc_labor_cost_ratio` — % de nómina sobre ventas usando `clock_in`/`clock_out`.
- `calc_sales_per_labor_hour` — ventas ÷ horas trabajadas, productividad laboral (no requiere
  dato de salario, solo horas).

**Nivel Inventario:**
- `calc_waste_cost` — `waste_recorded × unit_cost`, traduce merma a pesos.
- `calc_stock_days_remaining` — `current_stock / consumo diario promedio`.

Para cada función nueva, documentar: input tipado, fórmula exacta, unidad de salida, y condición
de `status` (`ok`/`warning`/`critical`/`incomplete_data`) — sin fijar todavía los umbrales
numéricos exactos, esos se definen en la Tarea 5.

---

## Tarea 4 — Tabla de configuración de comisiones por canal

`calc_delivery_commission_cost` necesita un dato que no viene en el JSON de la API: el % de
comisión que cobra cada plataforma. Diseña en `db_schema.md` una tabla simple
`delivery_platform_config` (`business_id`, `platform`, `commission_rate`, `effective_date`) que el
negocio pueda llenar/actualizar, y documenta en `s1b_ingesta_api.md` (o donde corresponda) que S3
debe leer de ahí, nunca asumir una tasa fija en código.

---

## Tarea 5 — Placeholder para el set de evaluación offline

Crea el archivo `eval_offline.md` con la estructura vacía siguiendo la plantilla de nodo (o una
equivalente si no aplica el mismo formato). Ya hay dos decisiones resueltas que sí puedes
documentar ahí — el resto sigue pendiente para la siguiente sesión:

**Resuelto:**
- **Ubicación de los casos**: `tests/eval_set/caso_NN_nombre.json`, uno por archivo, siguiendo el
  mismo patrón que `tests/test_pbt_*.py`. **Nunca en `mepia.db`** — los casos son fixtures de
  prueba sintéticos y deben quedarse fijos para que el número de accuracy sea comparable entre
  corridas; meterlos a la base de producción contaminaría `mepia_memory` con historial falso.
- **Formato del caso**: ya hay un ejemplo real en `tests/eval_set/caso_02_faltante_caja.json` —
  úsalo como plantilla de estructura (`id`, `tipo`, `escenario_narrativo`, `anomalias_inyectadas`,
  `input` a 5 niveles, `config_negocio`, `esperado_S3`, `esperado_hallazgos`, `esperado_narrativa`,
  `revisado_por`).

**Pendiente de diseño** (dejar como sección `## Pendiente de diseño` en el archivo):
- Cómo se construye el harness que lee los JSON de `tests/eval_set/` y corre el pipeline completo
  contra cada uno.
- Método de etiquetado y umbral de aprobación para pasar un caso.
- Resolver la ambigüedad de la regla de materialidad Tipo B (¿el umbral efectivo es "cualquiera
  de las dos condiciones dispara" o "el mayor de las dos"? — ver nota en
  `caso_02_faltante_caja.json`, campo `notas_construccion`).

---

Al terminar, actualiza la tabla de nodos en `_index.md` reflejando todos los archivos nuevos o
modificados, con su estado (`🔧 in dev` para todo lo de esta sesión, ya que aún no hay código).
