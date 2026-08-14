"""
MEPIA Eval Runner - Level 1 & Level 2

Level 1 (Deterministic S3):
  Tolerancias para comparacion numerica:
    - Relativa: +/-1% para valores > 1.0
    - Absoluta: +/-$0.50 MXN para valores cercanos a cero o < $1.0
    - Status: comparacion exacta (string match)
  Requiere: NO necesita LLM, NO necesita DB real. Rapido (<5s para 8 casos).

Level 2 (Pipeline S3→S4, con LLM):
  Ejecuta S3 completo + ForensicCFO (S4) y compara anomalias generadas
  contra esperado_hallazgos del ground truth.
  NO es pass/fail — produce reporte estructurado para revision humana.
  Requiere: OPENAI_API_KEY. Costo: ~$0.02-0.05 por caso (gpt-4o).

Uso:
  python tests/eval_test/eval_runner.py                 # Level 1 (default, all cases)
  python tests/eval_test/eval_runner.py --case 01       # Only case 01
  python tests/eval_test/eval_runner.py --full-pipeline # Level 2 (S3→S4 con LLM)
  python tests/eval_test/eval_runner.py --full-pipeline --json  # Level 2 + JSON output
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Path setup — ensure agents/ is importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.calc_engine import (
    CalcResult,
    calc_avg_ticket,
    calc_cancellation_rate,
    calc_channel_mix,
    calc_commission_cost_ratio,
    calc_contribution_margin,
    calc_contribution_margin_by_channel,
    calc_delivery_commission_cost,
    calc_discount_rate,
    calc_payment_mix,
    calc_reprint_rate,
    calc_shift_cash_variance,
    calc_staff_courtesy_ratio,
    calc_stock_days_remaining,
    calc_waste_analysis,
    calc_waste_cost,
    check_price_inflation,
)


# ---------------------------------------------------------------------------
# Helper: extract per-responsable value from CalcResult context
# ---------------------------------------------------------------------------

def _derive_per_responsable_status(metric_name: str, personal_rate: float) -> str:
    """
    Derive status for a per-responsable value using the same thresholds
    as the aggregate function. personal_rate is expressed as a ratio (0.4 = 40%).
    """
    # Convert ratio to percentage for threshold comparison
    pct = personal_rate * 100.0 if personal_rate < 1.0 else personal_rate

    if metric_name == "calc_reprint_rate":
        # >10% critical, >5% warning
        if pct > 10:
            return "critical"
        elif pct > 5:
            return "warning"
        return "ok"
    elif metric_name == "calc_cancellation_rate":
        # >5% critical, >2% warning
        if pct > 5:
            return "critical"
        elif pct > 2:
            return "warning"
        return "ok"
    elif metric_name == "calc_discount_rate":
        # >10% warning (no critical)
        if pct > 10:
            return "warning"
        return "ok"
    elif metric_name == "calc_staff_courtesy_ratio":
        # >5% critical (no warning)
        if pct > 5:
            return "critical"
        return "ok"
    else:
        return "ok"


def _extract_by_responsable(context: str, responsable: str) -> float | None:
    """Extract a responsable's personal rate from the by_responsable JSON embedded in context."""
    import json as _json
    marker = "by_responsable: "
    idx = context.find(marker)
    if idx == -1:
        return None
    json_start = idx + len(marker)
    # Find the end of the JSON object (matching braces)
    brace_count = 0
    json_end = json_start
    for i, ch in enumerate(context[json_start:], start=json_start):
        if ch == '{':
            brace_count += 1
        elif ch == '}':
            brace_count -= 1
            if brace_count == 0:
                json_end = i + 1
                break
    try:
        by_resp = _json.loads(context[json_start:json_end])
    except (ValueError, _json.JSONDecodeError):
        return None
    resp_data = by_resp.get(responsable)
    if resp_data is None:
        # Responsable not in by_responsable = they had 0 anomalies
        # Return 0.0 (not None/error) as long as context exists (function ran successfully)
        return 0.0
    # Priority: rate_pct (personal rate) first, then fallbacks
    if "rate_pct" in resp_data:
        return float(resp_data["rate_pct"])
    if "pct_of_total" in resp_data:
        return float(resp_data["pct_of_total"])
    if "pct_of_all_courtesy" in resp_data:
        return float(resp_data["pct_of_all_courtesy"])
    if "discount_pct" in resp_data:
        return float(resp_data["discount_pct"])
    if "count" in resp_data:
        return float(resp_data["count"])
    # Fallback: try first numeric value
    for v in resp_data.values():
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None


# ---------------------------------------------------------------------------
# Tolerance constants
# ---------------------------------------------------------------------------
RELATIVE_TOLERANCE = 0.01   # ±1% for values > 1.0
ABSOLUTE_TOLERANCE = 0.50   # ±$0.50 MXN for values near zero or < $1.0


# ---------------------------------------------------------------------------
# Data classes for results
# ---------------------------------------------------------------------------

@dataclass
class MetricComparison:
    metric: str
    qualifier: str  # turno, periodo, insumo — for disambiguation
    expected_value: Any
    expected_status: str
    actual_value: Any
    actual_status: Optional[str]
    value_match: bool
    status_match: bool
    passed: bool
    error: Optional[str] = None


@dataclass
class CaseResult:
    case_id: str
    caso_nombre: str
    total_metrics: int
    passed_metrics: int
    failed_metrics: int
    metric_results: list[MetricComparison] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.failed_metrics == 0


@dataclass
class EvalSummary:
    total_cases: int
    passed_cases: int
    failed_cases: int
    total_metrics: int
    correct_metrics: int
    accuracy_pct: float
    case_results: list[CaseResult] = field(default_factory=list)
    elapsed_seconds: float = 0.0


# ---------------------------------------------------------------------------
# MockDB — simulates Supabase client for S3 functions
# ---------------------------------------------------------------------------

class MockQueryResult:
    """Simulates Supabase execute() response."""
    def __init__(self, data: list[dict] | dict | None):
        self.data = data


class MockQueryBuilder:
    """
    Fluent query builder that mimics Supabase .table().select().eq()... chains.
    Routes queries to appropriate data based on table name and filters.
    """

    def __init__(self, table_name: str, store: dict[str, list[dict]]):
        self._table = table_name
        self._store = store
        self._filters: list[tuple[str, str, Any]] = []
        self._select_fields: str = "*"
        self._order_field: Optional[str] = None
        self._order_desc: bool = False
        self._limit_val: Optional[int] = None
        self._is_single: bool = False

    def select(self, fields: str = "*") -> "MockQueryBuilder":
        self._select_fields = fields
        return self

    def eq(self, field: str, value: Any) -> "MockQueryBuilder":
        self._filters.append(("eq", field, value))
        return self

    def gte(self, field: str, value: Any) -> "MockQueryBuilder":
        self._filters.append(("gte", field, value))
        return self

    def lte(self, field: str, value: Any) -> "MockQueryBuilder":
        self._filters.append(("lte", field, value))
        return self

    def in_(self, field: str, values: list) -> "MockQueryBuilder":
        self._filters.append(("in", field, values))
        return self

    def order(self, field: str, desc: bool = False) -> "MockQueryBuilder":
        self._order_field = field
        self._order_desc = desc
        return self

    def limit(self, n: int) -> "MockQueryBuilder":
        self._limit_val = n
        return self

    def single(self) -> "MockQueryBuilder":
        self._is_single = True
        return self

    def execute(self) -> MockQueryResult:
        """Apply filters to stored data and return matching rows."""
        rows = self._store.get(self._table, [])

        # Apply filters
        for op, fld, val in self._filters:
            if op == "eq":
                rows = [r for r in rows if r.get(fld) == val]
            elif op == "gte":
                rows = [r for r in rows if str(r.get(fld, "")) >= str(val)]
            elif op == "lte":
                rows = [r for r in rows if str(r.get(fld, "")) <= str(val)]
            elif op == "in":
                rows = [r for r in rows if r.get(fld) in val]

        # Apply ordering
        if self._order_field:
            rows = sorted(
                rows,
                key=lambda r: r.get(self._order_field, ""),
                reverse=self._order_desc,
            )

        # Apply limit
        if self._limit_val is not None:
            rows = rows[: self._limit_val]

        # Single mode
        if self._is_single:
            if rows:
                return MockQueryResult(rows[0])
            return MockQueryResult(None)

        return MockQueryResult(rows)


class MockDB:
    """
    Mock Supabase client that holds all data for a single eval case.
    The data is pre-transformed from ground truth JSON into the format
    that S3 functions expect from DB queries.
    """

    def __init__(self, store: dict[str, list[dict]]):
        self._store = store

    def table(self, name: str) -> MockQueryBuilder:
        return MockQueryBuilder(name, self._store)


# ---------------------------------------------------------------------------
# Data transformation: ground truth input → MockDB store
# ---------------------------------------------------------------------------

def build_mock_store(case_data: dict) -> dict[str, list[dict]]:
    """
    Transforms ground truth JSON input into table-shaped data for MockDB.

    Tables populated:
      - shift_audit_events: from input.turnos[].shift_data, cancellations, reprints
      - transactions: from input.turnos[].ordenes[] (type=ingreso, category=venta)
      - pos_inputs: aggregated ticket count per day
      - inventory_daily: from input.inventario.insumos[]
      - delivery_platform_config: from config_negocio.comisiones_delivery
    """
    inp = case_data["input"]
    config = case_data.get("config_negocio", {})
    negocio_id = inp["negocio_id"]
    fecha = inp["fecha"]

    store: dict[str, list[dict]] = {
        "shift_audit_events": [],
        "transactions": [],
        "pos_inputs": [],
        "inventory_daily": [],
        "delivery_platform_config": [],
        "recipes": [],
        "unit_conversions": [],
    }

    total_tickets = 0

    for turno in inp.get("turnos", []):
        turno_id = turno["turno_id"]
        shift_data = turno.get("shift_data", {})
        ordenes = turno.get("ordenes", [])
        cancellations = turno.get("cancellations", [])
        reprints = turno.get("reprints", [])

        # --- shift_audit_events ---
        # Calculate expected cash for the shift from orders paid in cash
        efectivo_turno = Decimal("0")
        for orden in ordenes:
            pago = orden.get("forma_de_pago", "")
            if pago == "Efectivo":
                efectivo_turno += Decimal(str(orden["total_net"]))

        saldo_inicial = Decimal(str(shift_data.get("saldo_inicial", 0)))
        saldo_final_contado = Decimal(str(shift_data.get("saldo_final_contado", 0)))
        esperado_cierre = saldo_inicial + efectivo_turno
        sobrante_faltante = saldo_final_contado - esperado_cierre

        store["shift_audit_events"].append({
            "business_id": negocio_id,
            "date": fecha,
            "turno": turno_id,
            "apertura": float(saldo_inicial),
            "cierre_z": float(saldo_final_contado),
            "sobrante_faltante": float(sobrante_faltante),
            "cancellations": cancellations,
            "reprints": reprints,
            "clock_records": turno.get("clock_in_out", []),
        })

        # --- transactions (one per order) ---
        for orden in ordenes:
            pago = orden.get("forma_de_pago", "")
            total_net = float(orden["total_net"])
            subtotal = float(orden.get("subtotal", 0))
            discounts = float(orden.get("discounts", 0))

            # Build PaymentBreakdown — use the original forma_de_pago as key
            # The S3 functions read whatever keys are in PaymentBreakdown
            payment_breakdown = {pago: total_net}

            # For delivery platforms: calc_delivery_commission_cost expects lowercase
            # keys (uber_eats, rappi, didi_food). We use the lowercase form
            # and rely on key normalization in comparison for payment_mix.
            _DELIVERY_KEY_MAP = {
                "UberEats": "uber_eats",
                "Rappi": "rappi",
                "DiDiFood": "didi_food",
            }
            if pago in _DELIVERY_KEY_MAP:
                # Replace original key with lowercase delivery key
                payment_breakdown = {_DELIVERY_KEY_MAP[pago]: subtotal}

            # Special case: Cortesía_Staff
            # staff_courtesy_ratio reads "cortesia_staff" (lowercase, no accent).
            # payment_mix reads ALL keys from PaymentBreakdown.
            # We use "cortesia_staff" as the key (what the function needs) and
            # normalize key names during comparison.
            if pago == "Cortesía_Staff":
                courtesy_val = float(orden.get("subtotal", 0))
                payment_breakdown = {"cortesia_staff": courtesy_val}

            raw_metadata = {
                "order_type": orden.get("order_type", ""),
                "PaymentBreakdown": payment_breakdown,
                "subtotal": subtotal,
                "discounts": discounts,
                "cajero_id": orden.get("cajero_id", ""),
            }

            # Include product items detail if available (for calc_contribution_margin_by_channel)
            detalle = orden.get("detalle_producto")
            if detalle:
                raw_metadata["items"] = detalle

            store["transactions"].append({
                "business_id": negocio_id,
                "type": "ingreso",
                "category": "venta",
                "transaction_date": fecha,
                "amount": total_net,
                "raw_metadata": raw_metadata,
            })

            total_tickets += 1

    # --- pos_inputs: aggregated ticket count ---
    store["pos_inputs"].append({
        "business_id": negocio_id,
        "date": fecha,
        "num_transactions": total_tickets,
    })

    # --- pos_inputs: per-product quantity records (for calc_waste_analysis) ---
    # Count how many of each product were sold based on detalle_producto in orders
    product_qty_sold: dict[str, int] = {}
    for turno in inp.get("turnos", []):
        for orden in turno.get("ordenes", []):
            detalle = orden.get("detalle_producto") or []
            if detalle:
                for item in detalle:
                    pid = item.get("item_id", "")
                    qty = int(item.get("quantity", 1))
                    if pid:
                        product_qty_sold[pid] = product_qty_sold.get(pid, 0) + qty
            else:
                # No detalle_producto: try to match by subtotal to a known recipe
                subtotal_val = orden.get("subtotal", 0)
                for receta in inp.get("recetas", []):
                    if abs(float(receta.get("sale_price", 0)) - float(subtotal_val)) < 0.01:
                        pid = receta["id"]
                        product_qty_sold[pid] = product_qty_sold.get(pid, 0) + 1
                        break

    for pid, qty in product_qty_sold.items():
        store["pos_inputs"].append({
            "business_id": negocio_id,
            "date": fecha,
            "product_id": pid,
            "quantity": qty,
        })

    # --- inventory_daily ---
    inventario = inp.get("inventario", {})
    for insumo in inventario.get("insumos", []):
        nombre = insumo["insumo"]

        # Determine usage and waste based on available fields
        usage = float(
            insumo.get("ingredients_usage_kg")
            or insumo.get("ingredients_usage_l")
            or 0
        )
        waste = float(
            insumo.get("waste_recorded_kg")
            or insumo.get("waste_recorded_l")
            or 0
        )
        stock = float(
            insumo.get("current_stock_kg")
            or insumo.get("current_stock_l")
            or 0
        )
        unit_cost = float(
            insumo.get("unit_cost_mxn_kg")
            or insumo.get("unit_cost_mxn_l")
            or 0
        )
        unit_cost_30d = float(
            insumo.get("unit_cost_hace_30d_mxn_kg")
            or insumo.get("unit_cost_hace_30d_mxn_l")
            or 0
        )

        # Current day record
        store["inventory_daily"].append({
            "business_id": negocio_id,
            "date": fecha,
            "ingredient_id": nombre,
            "ingredient_name": nombre,
            "waste_recorded": waste,
            "unit_cost": unit_cost,
            "current_stock": stock,
            "consumo_teorico": usage,
            "unit_cost_30d_ago": unit_cost_30d,
        })

        # Historical records for calc_stock_days_remaining (needs 7-day window)
        # Assume same daily usage for the past 6 days
        from datetime import datetime as _dt, timedelta as _td
        dt_base = _dt.strptime(fecha, "%Y-%m-%d")
        for days_back in range(1, 7):
            hist_date = (dt_base - _td(days=days_back)).strftime("%Y-%m-%d")
            store["inventory_daily"].append({
                "business_id": negocio_id,
                "date": hist_date,
                "ingredient_id": nombre,
                "ingredient_name": nombre,
                "waste_recorded": waste,
                "unit_cost": unit_cost,
                "current_stock": stock,  # Not used for historical
                "consumo_teorico": usage,
            })

    # --- delivery_platform_config ---
    comisiones = config.get("comisiones_delivery", {})
    for platform, rate in comisiones.items():
        store["delivery_platform_config"].append({
            "business_id": negocio_id,
            "platform": platform,
            "commission_rate": rate,
            "effective_date": "2020-01-01",  # Always effective
        })

    # --- Ingredient price transactions (for check_price_inflation) ---
    # We need at least 2 invoices per ingredient: current + historical
    # The function compares last invoice vs average of previous invoices
    # Skip ingredients that already have explicit compras records (which include unit_price)
    compras_ingredient_ids = {c["ingredient_id"] for c in inp.get("compras", [])}
    inventario = inp.get("inventario", {})
    for insumo in inventario.get("insumos", []):
        nombre = insumo["insumo"]

        unit_cost = float(
            insumo.get("unit_cost_mxn_kg")
            or insumo.get("unit_cost_mxn_l")
            or 0
        )
        unit_cost_30d = float(
            insumo.get("unit_cost_hace_30d_mxn_kg")
            or insumo.get("unit_cost_hace_30d_mxn_l")
            or 0
        )

        # If explicit compras exist, they provide the current price record already
        # Only add the historical record for check_price_inflation to have 2 data points
        if nombre in compras_ingredient_ids:
            from datetime import datetime, timedelta
            dt = datetime.strptime(fecha, "%Y-%m-%d")
            fecha_30d = (dt - timedelta(days=30)).strftime("%Y-%m-%d")
            store["transactions"].append({
                "business_id": negocio_id,
                "type": "egreso",
                "category": "compra_ingrediente",
                "ingredient_id": nombre,
                "unit_price": unit_cost_30d,
                "transaction_date": fecha_30d,
            })
            continue

        # Current price invoice
        store["transactions"].append({
            "business_id": negocio_id,
            "type": "egreso",
            "category": "compra_ingrediente",
            "ingredient_id": nombre,
            "unit_price": unit_cost,
            "transaction_date": fecha,
        })
        # Historical price invoice (30 days ago)
        from datetime import datetime, timedelta
        dt = datetime.strptime(fecha, "%Y-%m-%d")
        fecha_30d = (dt - timedelta(days=30)).strftime("%Y-%m-%d")
        store["transactions"].append({
            "business_id": negocio_id,
            "type": "egreso",
            "category": "compra_ingrediente",
            "ingredient_id": nombre,
            "unit_price": unit_cost_30d,
            "transaction_date": fecha_30d,
        })

    # --- recipes (for calc_contribution_margin) ---
    for receta in inp.get("recetas", []):
        store["recipes"].append({
            "id": receta["id"],
            "business_id": negocio_id,
            "product_name": receta.get("product_name", ""),
            "sale_price": receta.get("sale_price", 0),
            "ingredients": receta.get("ingredients", {}),
        })

    # --- Synthetic ingredient price transactions for recipe ingredients ---
    # When recetario_referencia provides costo_receta, derive unit prices so that
    # sum(qty × unit_price) == costo_receta for each product.
    # This enables calc_contribution_margin_by_channel to compute correct costs.
    recetario_ref = case_data.get("recetario_referencia", {}).get("productos", [])
    recetario_map = {p["item_id"]: p.get("costo_receta", 0) for p in recetario_ref}

    # Collect all ingredients from recipes and assign synthetic prices
    # Strategy: for each recipe, if costo_receta is known, compute a uniform
    # unit_price such that the total cost matches.
    _ingredient_prices_set: set[str] = set()
    for receta in inp.get("recetas", []):
        product_id = receta["id"]
        ingredientes = receta.get("ingredients", {})
        costo_receta = recetario_map.get(product_id, 0)

        if not ingredientes or not costo_receta:
            continue

        # Calculate total qty to distribute cost proportionally
        total_qty = sum(float(v) for v in ingredientes.values())
        if total_qty == 0:
            continue

        for ing_id, qty_raw in ingredientes.items():
            if ing_id in _ingredient_prices_set:
                continue
            _ingredient_prices_set.add(ing_id)

            qty = float(qty_raw)
            # Proportional unit_price: (costo_receta × qty/total_qty) / qty = costo_receta / total_qty
            unit_price = costo_receta / total_qty

            store["transactions"].append({
                "business_id": negocio_id,
                "type": "egreso",
                "category": "compra_ingrediente",
                "ingredient_id": ing_id,
                "unit_price": unit_price,
                "transaction_date": fecha,
            })

    # --- compras (ingredient purchase transactions for calc_waste_analysis) ---
    for compra in inp.get("compras", []):
        compra_record: dict[str, Any] = {
            "business_id": negocio_id,
            "type": "egreso",
            "category": "compra_ingrediente",
            "ingredient_id": compra["ingredient_id"],
            "quantity": compra["quantity"],
            "unit": compra["unit"],
            "transaction_date": compra.get("fecha", fecha),
        }
        # Include unit_price if available (needed by check_price_inflation)
        if "unit_price" in compra:
            compra_record["unit_price"] = compra["unit_price"]
        store["transactions"].append(compra_record)

    return store


# ---------------------------------------------------------------------------
# Metric invocation — maps ground truth metric name → S3 function call
# ---------------------------------------------------------------------------

def _filter_db_for_ingredient(db: MockDB, ingredient_id: str) -> MockDB:
    """
    Creates a new MockDB with inventory_daily filtered to a single ingredient.
    Useful when ground truth expects per-ingredient results from functions
    that aggregate all ingredients.
    """
    import copy
    new_store = copy.deepcopy(db._store)
    new_store["inventory_daily"] = [
        row for row in new_store["inventory_daily"]
        if row.get("ingredient_id") == ingredient_id
    ]
    return MockDB(new_store)


def invoke_metric(metric_name: str, expected: dict, case_data: dict, db: MockDB) -> CalcResult | None:
    """
    Invokes the appropriate S3 function for a given metric expectation.
    Returns CalcResult or None if the metric is not mapped.
    """
    negocio_id = case_data["input"]["negocio_id"]
    fecha = case_data["input"]["fecha"]

    if metric_name == "calc_shift_cash_variance":
        # This function returns aggregate for all shifts,
        # but ground truth may have per-turno expectations.
        # We invoke once and compare the aggregate value.
        return calc_shift_cash_variance(negocio_id, fecha, db)

    elif metric_name == "calc_avg_ticket":
        # Uses start_date = end_date = fecha for daily
        return calc_avg_ticket(negocio_id, fecha, fecha, db)

    elif metric_name == "calc_payment_mix":
        return calc_payment_mix(negocio_id, fecha, db)

    elif metric_name == "calc_channel_mix":
        return calc_channel_mix(negocio_id, fecha, db)

    elif metric_name == "calc_staff_courtesy_ratio":
        return calc_staff_courtesy_ratio(negocio_id, fecha, db)

    elif metric_name == "calc_cancellation_rate":
        return calc_cancellation_rate(negocio_id, fecha, db)

    elif metric_name == "calc_reprint_rate":
        return calc_reprint_rate(negocio_id, fecha, db)

    elif metric_name == "check_price_inflation":
        insumo = expected.get("insumo", "")
        return check_price_inflation(insumo, negocio_id, db)

    elif metric_name == "calc_waste_cost":
        # If ground truth specifies a specific insumo, filter inventory_daily
        insumo = expected.get("insumo")
        if insumo:
            filtered_db = _filter_db_for_ingredient(db, insumo)
            return calc_waste_cost(negocio_id, fecha, filtered_db)
        return calc_waste_cost(negocio_id, fecha, db)

    elif metric_name == "calc_stock_days_remaining":
        # If ground truth specifies a specific insumo, filter inventory_daily
        insumo = expected.get("insumo")
        if insumo:
            filtered_db = _filter_db_for_ingredient(db, insumo)
            return calc_stock_days_remaining(negocio_id, fecha, filtered_db)
        return calc_stock_days_remaining(negocio_id, fecha, db)

    elif metric_name == "calc_discount_rate":
        return calc_discount_rate(negocio_id, fecha, fecha, db)

    elif metric_name == "calc_delivery_commission_cost":
        return calc_delivery_commission_cost(negocio_id, fecha, db)

    elif metric_name == "calc_commission_cost_ratio":
        return calc_commission_cost_ratio(negocio_id, fecha, db)

    elif metric_name == "calc_contribution_margin":
        # Per-product metric — requires product_id from expected
        product_id = expected.get("product_id", expected.get("producto", ""))
        if product_id:
            return calc_contribution_margin(product_id, db)
        return None

    elif metric_name == "calc_contribution_margin_by_channel":
        return calc_contribution_margin_by_channel(negocio_id, fecha, db)

    elif metric_name == "calc_waste_analysis":
        # Per-ingredient waste analysis
        insumo = expected.get("insumo", "")
        if insumo:
            return calc_waste_analysis(insumo, fecha, fecha, negocio_id, db)
        return None

    else:
        return None


# ---------------------------------------------------------------------------
# Comparison logic
# ---------------------------------------------------------------------------

def _normalize_key(key: str) -> str:
    """
    Normalizes payment/channel key for comparison.
    Removes accents, lowercases, strips underscores.
    e.g., 'Cortesía_Staff' → 'cortesiastaff'
    e.g., 'UberEats' → 'ubereats'
    e.g., 'uber_eats' → 'ubereats'
    """
    import unicodedata
    # Remove accents
    nfkd = unicodedata.normalize("NFKD", key)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    # Lowercase and remove underscores/spaces
    return ascii_str.lower().replace("_", "").replace(" ", "").strip()


def values_within_tolerance(expected: Any, actual: Any) -> bool:
    """
    Compares expected vs actual value with documented tolerance.

    Rules:
      - If expected is a dict (e.g., payment_mix, channel_mix) → compare each key
      - If expected is numeric: use relative ±1% for |expected| > 1.0,
        absolute ±$0.50 otherwise
      - If expected is None → actual must also be None
    """
    if expected is None and actual is None:
        return True
    if expected is None or actual is None:
        return False

    # Dict comparison (payment_mix, channel_mix)
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        # Normalize keys for comparison (handle accent/case differences)
        # e.g., ground truth "Cortesía_Staff" vs actual "cortesia_staff"
        actual_normalized = {_normalize_key(k): v for k, v in actual.items()}
        for key, exp_val in expected.items():
            norm_key = _normalize_key(key)
            if norm_key not in actual_normalized:
                return False
            if not _numeric_within_tolerance(float(exp_val), float(actual_normalized[norm_key])):
                return False
        return True

    # Numeric comparison
    try:
        exp_f = float(expected)
        act_f = float(actual)
        return _numeric_within_tolerance(exp_f, act_f)
    except (TypeError, ValueError):
        return str(expected) == str(actual)


def _numeric_within_tolerance(expected: float, actual: float) -> bool:
    """
    ±1% relative for |expected| > 1.0
    ±$0.50 absolute for |expected| <= 1.0
    """
    if abs(expected) > 1.0:
        # Relative tolerance
        if expected == 0:
            return abs(actual) <= ABSOLUTE_TOLERANCE
        return abs(actual - expected) / abs(expected) <= RELATIVE_TOLERANCE
    else:
        # Absolute tolerance
        return abs(actual - expected) <= ABSOLUTE_TOLERANCE


def extract_actual_value(result: CalcResult, expected: dict) -> Any:
    """
    Extracts the comparable value from a CalcResult.

    For metrics where the ground truth expects a dict (payment_mix, channel_mix),
    we parse the context JSON. For shift_cash_variance with per-turno expectations,
    we extract per-turno values from context.

    Unit normalization:
      - Functions returning "%" store percentage values (e.g., 2.45 meaning 2.45%)
      - Ground truth may store the same as a ratio (0.0245)
      - When ground truth value < 1 and unit is "%" → convert actual from pct to ratio

    For simple numeric metrics, we use result.value directly.
    """
    metric_name = expected["metric"]
    expected_value = expected.get("value")

    # For calc_contribution_margin_by_channel with canal qualifier: parse context JSON
    if metric_name == "calc_contribution_margin_by_channel" and "canal" in expected:
        canal = expected["canal"]
        ctx = result.context or ""
        try:
            import re
            json_match = re.search(r'\{[^{}]*\}', ctx)
            if json_match:
                parsed = json.loads(json_match.group())
                val = parsed.get(canal)
                if val is not None:
                    return float(val)
        except (json.JSONDecodeError, ValueError):
            pass
        return None

    # Dict-valued metrics: parse from context (the functions store mix in context)
    if isinstance(expected_value, dict):
        # Try to parse the JSON from context
        import re
        ctx = result.context or ""
        # Look for JSON-like dict in context
        json_match = re.search(r'\{[^{}]+\}', ctx)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                # Convert string percentages to ratios for comparison
                return {k: float(v) / 100.0 if float(v) > 1 else float(v)
                        for k, v in parsed.items()}
            except (json.JSONDecodeError, ValueError):
                pass
        # Fallback: return value as-is
        if result.value is not None:
            return float(result.value)
        return None

    # For shift_cash_variance with turno qualifier — the function returns
    # the aggregate sum. We need per-turno data from context for multi-shift cases.
    if metric_name == "calc_shift_cash_variance" and "turno" in expected:
        turno_id = expected["turno"]
        # Parse per-turno detail from context
        ctx = result.context or ""
        import re
        # Pattern: "T1: +0.00 MXN" or "T2: -650.00 MXN"
        pattern = rf'{turno_id}:\s*([+-]?\d+\.?\d*)\s*MXN'
        match = re.search(pattern, ctx)
        if match:
            return float(match.group(1))
        # If only one shift and value matches, return it
        if result.value is not None:
            return float(result.value)
        return None

    # For percentage metrics where ground truth is expressed as ratio (< 1):
    # staff_courtesy_ratio, cancellation_rate, reprint_rate
    # The functions return percentage values (e.g., 2.45 for 2.45%)
    # Ground truth may store as ratio (0.0245)
    if result.unit == "%" and result.value is not None:
        actual_pct = float(result.value)
        if expected_value is not None and isinstance(expected_value, (int, float)):
            # If expected is < 1, it's likely a ratio — convert actual to ratio
            if abs(expected_value) < 1.0 and abs(actual_pct) < 100:
                return actual_pct / 100.0
        return actual_pct

    # Standard numeric value
    if result.value is not None:
        return float(result.value)
    return None


def extract_actual_status(result: CalcResult, expected: dict) -> str:
    """
    Extracts the status from CalcResult. For per-turno shift_cash_variance,
    we derive status from the per-turno value against thresholds.
    """
    metric_name = expected["metric"]

    if metric_name == "calc_shift_cash_variance" and "turno" in expected:
        # Per-turno status derivation from the turno's sobrante_faltante
        turno_id = expected["turno"]
        ctx = result.context or ""
        import re
        pattern = rf'{turno_id}:\s*([+-]?\d+\.?\d*)\s*MXN'
        match = re.search(pattern, ctx)
        if match:
            val = abs(float(match.group(1)))
            if val > 500:
                return "critical"
            elif val > 100:
                return "warning"
            else:
                return "ok"
        # Fallback to aggregate status
        return result.status

    return result.status


def get_qualifier(expected: dict) -> str:
    """Get a human-readable qualifier for the metric (turno, periodo, insumo, etc.)."""
    parts = []
    if "turno" in expected:
        parts.append(f"turno={expected['turno']}")
    if "periodo" in expected:
        parts.append(f"periodo={expected['periodo']}")
    if "insumo" in expected:
        parts.append(f"insumo={expected['insumo']}")
    if "canal" in expected:
        parts.append(f"canal={expected['canal']}")
    if "nivel" in expected:
        parts.append(f"nivel={expected['nivel']}")
    if "responsable" in expected:
        parts.append(f"responsable={expected['responsable']}")
    if "tipo" in expected and expected.get("metric") != expected.get("tipo"):
        parts.append(f"tipo={expected['tipo']}")
    if "producto" in expected:
        parts.append(f"producto={expected['producto']}")
    if "product_id" in expected:
        parts.append(f"product_id={expected['product_id']}")
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Core evaluation logic
# ---------------------------------------------------------------------------

def evaluate_case(case_path: str) -> CaseResult:
    """
    Evaluates a single ground truth case against S3 functions.
    Returns CaseResult with per-metric pass/fail details.
    """
    with open(case_path, "r", encoding="utf-8") as f:
        case_data = json.load(f)

    case_id = case_data["id"]
    esperado_s3 = case_data.get("esperado_S3", [])

    # Build mock database from case input
    store = build_mock_store(case_data)
    db = MockDB(store)

    metric_results: list[MetricComparison] = []
    # Track which metrics have been invoked (some are called once for multi-turno)
    invoked_metrics: dict[str, CalcResult | None] = {}

    for expected in esperado_s3:
        metric_name = expected["metric"]
        qualifier = get_qualifier(expected)
        expected_value = expected.get("value")
        expected_status = expected.get("status", "ok")

        try:
            # Invoke function — use metric+qualifier as cache key to handle
            # multiple expectations for the same metric (different turno/insumo)
            cache_key = f"{metric_name}|{qualifier}"
            if cache_key not in invoked_metrics:
                result = invoke_metric(metric_name, expected, case_data, db)
                invoked_metrics[cache_key] = result
            else:
                result = invoked_metrics[cache_key]

            if result is None:
                # Determine if it's truly unmapped or just not-yet-supported
                error_msg = f"Metric '{metric_name}' not mapped in eval runner"

                metric_results.append(MetricComparison(
                    metric=metric_name,
                    qualifier=qualifier,
                    expected_value=expected_value,
                    expected_status=expected_status,
                    actual_value=None,
                    actual_status=None,
                    value_match=False,
                    status_match=False,
                    passed=False,
                    error=error_msg,
                ))
                continue

            # For por_responsable: extract the per-responsable value from context
            if expected.get("nivel") == "por_responsable" and result.context:
                resp_value = _extract_by_responsable(
                    result.context, expected.get("responsable", "")
                )
                if resp_value is not None:
                    actual_value = resp_value
                    # Convert percentage to ratio for comparison (ground truth uses ratios < 1)
                    expected_value_check = expected.get("value")
                    if expected_value_check is not None and isinstance(expected_value_check, (int, float)):
                        if abs(expected_value_check) < 1.0 and actual_value > 1.0:
                            actual_value = actual_value / 100.0

                    # Derive per-responsable status from personal rate using metric thresholds
                    # (not the aggregate result.status which reflects the day-level status)
                    actual_status = _derive_per_responsable_status(metric_name, actual_value)
                else:
                    metric_results.append(MetricComparison(
                        metric=metric_name,
                        qualifier=qualifier,
                        expected_value=expected_value,
                        expected_status=expected_status,
                        actual_value=None,
                        actual_status=None,
                        value_match=False,
                        status_match=False,
                        passed=False,
                        error=(
                            f"Could not extract by_responsable value for "
                            f"'{expected.get('responsable', '')}' from context"
                        ),
                    ))
                    continue

                # Compare
                value_match = values_within_tolerance(expected_value, actual_value)
                status_match = actual_status == expected_status
                passed = value_match and status_match

                metric_results.append(MetricComparison(
                    metric=metric_name,
                    qualifier=qualifier,
                    expected_value=expected_value,
                    expected_status=expected_status,
                    actual_value=actual_value,
                    actual_status=actual_status,
                    value_match=value_match,
                    status_match=status_match,
                    passed=passed,
                ))
                continue

            # Extract actual value and status
            actual_value = extract_actual_value(result, expected)
            actual_status = extract_actual_status(result, expected)

            # Compare
            value_match = values_within_tolerance(expected_value, actual_value)
            status_match = actual_status == expected_status

            passed = value_match and status_match

            metric_results.append(MetricComparison(
                metric=metric_name,
                qualifier=qualifier,
                expected_value=expected_value,
                expected_status=expected_status,
                actual_value=actual_value,
                actual_status=actual_status,
                value_match=value_match,
                status_match=status_match,
                passed=passed,
            ))

        except Exception as exc:
            metric_results.append(MetricComparison(
                metric=metric_name,
                qualifier=qualifier,
                expected_value=expected_value,
                expected_status=expected_status,
                actual_value=None,
                actual_status=None,
                value_match=False,
                status_match=False,
                passed=False,
                error=str(exc),
            ))

    total = len(metric_results)
    passed_count = sum(1 for m in metric_results if m.passed)
    failed_count = total - passed_count

    return CaseResult(
        case_id=case_id,
        caso_nombre=case_id.replace("caso_", "").replace("_", " "),
        total_metrics=total,
        passed_metrics=passed_count,
        failed_metrics=failed_count,
        metric_results=metric_results,
    )


# ---------------------------------------------------------------------------
# Discovery and orchestration
# ---------------------------------------------------------------------------

def discover_cases(case_filter: Optional[str] = None) -> list[str]:
    """
    Finds ground truth JSON files in tests/eval_test/.
    Optionally filters by case number (e.g., '01').
    """
    eval_dir = Path(__file__).parent
    pattern = str(eval_dir / "mepia_ground_truth_caso_*.json")
    cases = sorted(glob.glob(pattern))

    if case_filter:
        cases = [c for c in cases if f"caso_{case_filter}" in c]

    return cases


def run_level_1(case_filter: Optional[str] = None) -> EvalSummary:
    """
    Runs Level 1 deterministic evaluation (S3 only, no LLM).
    Returns EvalSummary with all case results.
    """
    start_time = time.time()
    cases = discover_cases(case_filter)

    if not cases:
        print(f"[!] No ground truth cases found"
              + (f" matching filter '{case_filter}'" if case_filter else ""))
        return EvalSummary(
            total_cases=0, passed_cases=0, failed_cases=0,
            total_metrics=0, correct_metrics=0, accuracy_pct=0.0,
        )

    case_results: list[CaseResult] = []
    for case_path in cases:
        try:
            result = evaluate_case(case_path)
            case_results.append(result)
        except Exception as exc:
            # Don't let one broken case stop the rest
            case_name = Path(case_path).stem.replace("mepia_ground_truth_", "")
            print(f"  [!] Error loading {case_name}: {exc}")
            case_results.append(CaseResult(
                case_id=case_name,
                caso_nombre=case_name,
                total_metrics=0,
                passed_metrics=0,
                failed_metrics=1,
                metric_results=[],
            ))

    elapsed = time.time() - start_time
    total_metrics = sum(r.total_metrics for r in case_results)
    correct_metrics = sum(r.passed_metrics for r in case_results)
    passed_cases = sum(1 for r in case_results if r.passed)
    failed_cases = len(case_results) - passed_cases

    accuracy = (correct_metrics / total_metrics * 100) if total_metrics > 0 else 0.0

    return EvalSummary(
        total_cases=len(case_results),
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        total_metrics=total_metrics,
        correct_metrics=correct_metrics,
        accuracy_pct=round(accuracy, 1),
        case_results=case_results,
        elapsed_seconds=round(elapsed, 2),
    )


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def print_results(summary: EvalSummary) -> None:
    """Prints formatted results to console."""
    import io
    # Force UTF-8 output on Windows
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("\n=== MEPIA Eval Runner - Level 1 (Deterministic S3) ===\n")

    for case in summary.case_results:
        status_icon = "[PASS]" if case.passed else "[FAIL]"
        print(
            f"{status_icon} {case.case_id}: "
            f"{case.passed_metrics}/{case.total_metrics} metrics passed"
        )

        # Print failures
        for m in case.metric_results:
            if not m.passed:
                qualifier_str = f" ({m.qualifier})" if m.qualifier else ""
                if m.error:
                    print(f"  X {m.metric}{qualifier_str}: ERROR -- {m.error}")
                else:
                    val_icon = "OK" if m.value_match else "MISS"
                    status_icon_m = "OK" if m.status_match else "MISS"
                    print(
                        f"  X {m.metric}{qualifier_str}: "
                        f"expected value={m.expected_value} status={m.expected_status}, "
                        f"got value={m.actual_value} status={m.actual_status} "
                        f"(value {val_icon}, status {status_icon_m})"
                    )

    print(f"\n=== Summary ===")
    print(f"Cases: {summary.total_cases} total, "
          f"{summary.passed_cases} passed, {summary.failed_cases} failed")
    print(f"Metrics: {summary.total_metrics} total, "
          f"{summary.correct_metrics} correct ({summary.accuracy_pct}% accuracy)")
    print(f"Elapsed: {summary.elapsed_seconds}s")


def summary_to_dict(summary: EvalSummary) -> dict:
    """Serializes EvalSummary to a JSON-compatible dict."""
    return {
        "level": 1,
        "total_cases": summary.total_cases,
        "passed_cases": summary.passed_cases,
        "failed_cases": summary.failed_cases,
        "total_metrics": summary.total_metrics,
        "correct_metrics": summary.correct_metrics,
        "accuracy_pct": summary.accuracy_pct,
        "elapsed_seconds": summary.elapsed_seconds,
        "cases": [
            {
                "case_id": c.case_id,
                "passed": c.passed,
                "total_metrics": c.total_metrics,
                "passed_metrics": c.passed_metrics,
                "failures": [
                    {
                        "metric": m.metric,
                        "qualifier": m.qualifier,
                        "expected_value": m.expected_value,
                        "expected_status": m.expected_status,
                        "actual_value": m.actual_value,
                        "actual_status": m.actual_status,
                        "value_match": m.value_match,
                        "status_match": m.status_match,
                        "error": m.error,
                    }
                    for m in c.metric_results if not m.passed
                ],
            }
            for c in summary.case_results
        ],
    }


# ---------------------------------------------------------------------------
# Level 2 — Pipeline S3→S4 (requires OPENAI_API_KEY)
# ---------------------------------------------------------------------------

# Mapping from ground truth 'flag' → likely S3 metric_origin
# Used for soft matching between esperado_hallazgos and ForensicReport.anomalies
_FLAG_TO_METRIC_HINTS: dict[str, list[str]] = { 
    "faltante_de_caja": ["shift_cash_variance"],
    "sobrante_de_caja": ["shift_cash_variance"], 
    "reprint_rate_alto": ["reprint_rate"], 
    "cancelacion_post_comanda_alta": ["cancellation_rate"],
    "patron_fraude_operativo": ["cancellation_rate", "reprint_rate"],
    "erosion_margen_canal_delivery": ["delivery_commission_cost","commission_cost_ratio", "contribution_margin_by_channel"], 
    "merma_excesiva": ["waste_cost", "merma"], 
    "merma_inventario": ["waste_cost", "merma"],
    "descuentos_cortesias_concentrados": ["tasa_descuento", "staff_courtesy_ratio"], 
    "descuentos_zona_gris": ["tasa_descuento", "staff_courtesy_ratio"],
    "inflacion_proveedor": ["inflacion_precio"], 
    "stock_bajo": ["stock_days_remaining"], 
 }
# Mapping from ground truth 'flag' → likely AnomalyType(s) in ForensicReport
_FLAG_TO_TYPE_HINTS: dict[str, list[str]] = {
    "faltante_de_caja": ["source_discrepancy"],
    "sobrante_de_caja": ["source_discrepancy"],
    "reprint_rate_alto": ["operational_ceiling"],
    "cancelacion_post_comanda_alta": ["operational_ceiling"],
    "patron_fraude_operativo": ["operational_ceiling", "source_discrepancy"],
    "erosion_margen_canal_delivery": ["margin_leak", "cost_spike"],
    "merma_excesiva": ["cost_spike", "margin_leak"],
    "merma_inventario": ["cost_spike", "margin_leak"],
    "descuentos_cortesias_concentrados": ["margin_leak"],
    "descuentos_zona_gris": ["margin_leak"],
    "inflacion_proveedor": ["cost_spike"],
    "stock_bajo": ["operational_ceiling"],
}


@dataclass
class HallazgoMatch:
    """Represents whether an expected hallazgo was found in the ForensicReport."""
    flag: str
    severidad: str
    matched: bool
    matched_anomaly_type: Optional[str] = None
    matched_metric_origin: Optional[str] = None
    matched_severity: Optional[str] = None


@dataclass
class Level2CaseResult:
    """Result of Level 2 evaluation for a single case."""
    case_id: str
    total_expected: int
    found: list[HallazgoMatch]
    missing: list[HallazgoMatch]
    extra: list[dict]  # anomalies generated that don't match any expected
    error: Optional[str] = None


def _get_esperado_hallazgos(case_data: dict) -> list[dict]:
    """
    Extracts the expected hallazgos from a ground truth case.
    Handles both 'esperado_hallazgos' and the variant
    'esperado_hallazgos_sin_desagregacion_por_responsable' (caso_03).
    Filters out entries that are just notes (have 'nota' key only).
    """
    hallazgos = case_data.get("esperado_hallazgos")
    if hallazgos is None:
        # Fallback for caso_03 which uses the sin_desagregacion variant
        hallazgos = case_data.get(
            "esperado_hallazgos_sin_desagregacion_por_responsable", []
        )
    # Filter out note-only entries
    return [h for h in hallazgos if "flag" in h]


def _match_anomaly_to_hallazgo(
    anomaly: dict, hallazgo: dict
) -> bool:
    """
    Soft match: determines if a ForensicReport anomaly corresponds to
    an expected hallazgo from ground truth.

    Matching strategy (any ONE of these is sufficient):
    1. anomaly.metric_origin matches a known metric for the flag
    2. anomaly.type matches a known AnomalyType for the flag
    3. Both metric_origin hint AND type hint overlap
    """
    flag = hallazgo.get("flag", "")
    anomaly_type = anomaly.get("type", "")
    metric_origin = anomaly.get("metric_origin", "")

    # Try metric_origin match
    metric_hints = _FLAG_TO_METRIC_HINTS.get(flag, [])
    type_hints = _FLAG_TO_TYPE_HINTS.get(flag, [])

    metric_match = metric_origin in metric_hints
    type_match = anomaly_type in type_hints

    # If we have hints for this flag, require at least one match
    if metric_hints: 
        return metric_match 
    if type_hints: 
        return type_match 

    # No hints available — fall back to substring matching on description
    # This handles unknown flags gracefully
    desc_lower = anomaly.get("description", "").lower()
    flag_words = flag.replace("_", " ").lower().split()
    # At least half the words in the flag appear in the description
    word_matches = sum(1 for w in flag_words if w in desc_lower)
    return word_matches >= max(1, len(flag_words) // 2)


def _run_s3_all_metrics(case_data: dict, db: MockDB) -> list[dict]:
    """
    Runs all applicable S3 functions for a case and returns serialized CalcResults.
    This is a simplified version that invokes each known metric function once.
    """
    negocio_id = case_data["input"]["negocio_id"]
    fecha = case_data["input"]["fecha"]

    all_functions = [
        ("calc_shift_cash_variance", lambda: calc_shift_cash_variance(negocio_id, fecha, db)),
        ("calc_avg_ticket", lambda: calc_avg_ticket(negocio_id, fecha, fecha, db)),
        ("calc_payment_mix", lambda: calc_payment_mix(negocio_id, fecha, db)),
        ("calc_channel_mix", lambda: calc_channel_mix(negocio_id, fecha, db)),
        ("calc_staff_courtesy_ratio", lambda: calc_staff_courtesy_ratio(negocio_id, fecha, db)),
        ("calc_cancellation_rate", lambda: calc_cancellation_rate(negocio_id, fecha, db)),
        ("calc_reprint_rate", lambda: calc_reprint_rate(negocio_id, fecha, db)),
        ("calc_discount_rate", lambda: calc_discount_rate(negocio_id, fecha, fecha, db)),
        ("calc_delivery_commission_cost", lambda: calc_delivery_commission_cost(negocio_id, fecha, db)),
        ("calc_commission_cost_ratio", lambda: calc_commission_cost_ratio(negocio_id, fecha, db)),
        ("calc_contribution_margin_by_channel", lambda: calc_contribution_margin_by_channel(negocio_id, fecha, db)),
        ("calc_waste_cost", lambda: calc_waste_cost(negocio_id, fecha, db)),
        ("calc_stock_days_remaining", lambda: calc_stock_days_remaining(negocio_id, fecha, db)),
    ]

    # Add per-ingredient functions
    inventario = case_data.get("input", {}).get("inventario", {})
    for insumo in inventario.get("insumos", []):
        nombre = insumo["insumo"]
        all_functions.append(
            (f"check_price_inflation/{nombre}",
             lambda n=nombre: check_price_inflation(n, negocio_id, db))
        )
        all_functions.append(
            (f"calc_waste_analysis/{nombre}",
             lambda n=nombre: calc_waste_analysis(n, fecha, fecha, negocio_id, db))
        )

    results: list[dict] = []
    for name, fn in all_functions:
        try:
            result = fn()
            if result is not None:
                results.append({
                    "metric": result.metric,
                    "value": float(result.value) if result.value is not None else None,
                    "unit": result.unit,
                    "status": result.status,
                    "context": result.context,
                })
        except Exception:
            # Skip metrics that fail — Level 2 is best-effort
            pass

    return results


def _evaluate_level2_case(case_path: str) -> Level2CaseResult:
    """
    Evaluates a single case at Level 2: runs S3→S4 pipeline and compares
    generated anomalies against esperado_hallazgos.
    """
    from agents.forensic_cfo import ForensicCFOAgent

    with open(case_path, "r", encoding="utf-8") as f:
        case_data = json.load(f)

    case_id = case_data["id"]
    esperado = _get_esperado_hallazgos(case_data)

    # Build mock database and run all S3 functions
    store = build_mock_store(case_data)
    db = MockDB(store)
    calc_results = _run_s3_all_metrics(case_data, db)

    if not calc_results:
        return Level2CaseResult(
            case_id=case_id,
            total_expected=len(esperado),
            found=[],
            missing=[
                HallazgoMatch(flag=h["flag"], severidad=h.get("severidad", "?"), matched=False)
                for h in esperado
            ],
            extra=[],
            error="No S3 metrics could be calculated",
        )

    # Run ForensicCFO (S4) — this calls the LLM
    negocio_id = case_data["input"]["negocio_id"]
    fecha = case_data["input"]["fecha"]

    try:
        agent = ForensicCFOAgent()
        report = agent.run(
            calc_results=calc_results,
            business_id=negocio_id,
            date=fecha,
        )
    except Exception as exc:
        return Level2CaseResult(
            case_id=case_id,
            total_expected=len(esperado),
            found=[],
            missing=[
                HallazgoMatch(flag=h["flag"], severidad=h.get("severidad", "?"), matched=False)
                for h in esperado
            ],
            extra=[],
            error=f"ForensicCFO error: {exc}",
        )

    # Convert anomalies to dicts for comparison
    generated_anomalies = [
        {
            "type": a.type,
            "severity": a.severity,
            "metric_origin": a.metric_origin,
            "description": a.description,
            "quantified_impact": a.quantified_impact,
        }
        for a in report.anomalies
    ]

    # Match expected hallazgos against generated anomalies
    found: list[HallazgoMatch] = []
    missing: list[HallazgoMatch] = []
    matched_anomaly_indices: set[int] = set()

    for hallazgo in esperado:
        flag = hallazgo.get("flag", "")
        severidad = hallazgo.get("severidad", "?")
        matched = False

        for idx, anomaly in enumerate(generated_anomalies):
            if idx in matched_anomaly_indices:
                continue
            if _match_anomaly_to_hallazgo(anomaly, hallazgo):
                found.append(HallazgoMatch(
                    flag=flag,
                    severidad=severidad,
                    matched=True,
                    matched_anomaly_type=anomaly["type"],
                    matched_metric_origin=anomaly["metric_origin"],
                    matched_severity=anomaly["severity"],
                ))
                matched_anomaly_indices.add(idx)
                matched = True
                break

        if not matched:
            missing.append(HallazgoMatch(
                flag=flag,
                severidad=severidad,
                matched=False,
            ))

    # Extra: anomalies that didn't match any expected hallazgo
    extra = [
        generated_anomalies[i]
        for i in range(len(generated_anomalies))
        if i not in matched_anomaly_indices
    ]

    return Level2CaseResult(
        case_id=case_id,
        total_expected=len(esperado),
        found=found,
        missing=missing,
        extra=extra,
    )


def run_level_2(case_filter: Optional[str] = None) -> list[Level2CaseResult]:
    """
    Runs Level 2 evaluation: S3 → S4 (ForensicCFO with LLM).
    Requires OPENAI_API_KEY environment variable.

    This is NOT a pass/fail test — it produces a structured report for human review,
    since LLM output varies between runs.

    Returns list of Level2CaseResult for each case processed.
    """
    # Check required environment variables
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("\n[!] Level 2 requires OPENAI_API_KEY environment variable.")
        print("    Set it and re-run with --full-pipeline.")
        print("    Skipping Level 2 evaluation.\n")
        return []

    cases = discover_cases(case_filter)
    if not cases:
        print(f"[!] No ground truth cases found"
              + (f" matching filter '{case_filter}'" if case_filter else ""))
        return []

    print("\n=== MEPIA Eval Runner — Level 2 (Pipeline S3→S4) ===")
    print(f"    Cases: {len(cases)} | LLM: gpt-4o (temp=0)")
    print(f"    NOTE: Results vary between runs (LLM non-determinism).")
    print(f"    This report is for HUMAN REVIEW, not automated scoring.\n")

    results: list[Level2CaseResult] = []

    for case_path in cases:
        case_name = Path(case_path).stem.replace("mepia_ground_truth_", "")
        print(f"  Processing {case_name}...", end=" ", flush=True)

        try:
            result = _evaluate_level2_case(case_path)
            results.append(result)
            print("done.")
        except Exception as exc:
            print(f"ERROR: {exc}")
            results.append(Level2CaseResult(
                case_id=case_name,
                total_expected=0,
                found=[],
                missing=[],
                extra=[],
                error=str(exc),
            ))

    # Print formatted report
    _print_level2_report(results)

    return results


def _print_level2_report(results: list[Level2CaseResult]) -> None:
    """Prints the Level 2 structured report to console."""
    print("\n" + "=" * 60)
    print("  LEVEL 2 REPORT — Hallazgos Comparison (S3→S4)")
    print("=" * 60 + "\n")

    total_expected = 0
    total_found = 0
    total_missing = 0
    total_extra = 0

    for r in results:
        print(f"[{r.case_id}]")

        if r.error:
            print(f"  ERROR: {r.error}")
            print()
            continue

        total_expected += r.total_expected
        total_found += len(r.found)
        total_missing += len(r.missing)
        total_extra += len(r.extra)

        print(f"  Expected hallazgos: {r.total_expected}")
        print(f"  Found: {len(r.found)}, Missing: {len(r.missing)}, Extra: {len(r.extra)}")

        # Status summary line
        if r.total_expected == 0 and len(r.extra) == 0:
            print(f"  Status: CLEAN (no false positives)")
        elif r.total_expected == 0 and len(r.extra) > 0:
            print(f"  Status: FALSE POSITIVES ({len(r.extra)} unexpected)")
        elif len(r.missing) == 0 and len(r.extra) == 0:
            print(f"  Status: ALL EXPECTED FOUND")
        elif len(r.missing) == 0:
            print(f"  Status: ALL EXPECTED FOUND + {len(r.extra)} extra")
        else:
            print(f"  Status: PARTIAL ({len(r.found)}/{r.total_expected} found)")

        # Detail: found
        for h in r.found:
            type_info = h.matched_anomaly_type or "?"
            origin_info = h.matched_metric_origin or "?"
            sev_note = ""
            if h.matched_severity and h.matched_severity != h.severidad:
                sev_note = f" [sev: expected={h.severidad}, got={h.matched_severity}]"
            print(f"    \u2713 {h.flag} → {type_info}/{origin_info}{sev_note}")

        # Detail: missing
        for h in r.missing:
            print(f"    \u2717 {h.flag} (expected {h.severidad}) — NOT FOUND")

        # Detail: extra
        for ex in r.extra:
            print(f"    ? {ex['type']}/{ex['metric_origin']} "
                  f"(severity={ex['severity']}) — UNEXPECTED")

        print()

    # Aggregate summary
    print("-" * 60)
    print(f"  AGGREGATE: {total_found} found, {total_missing} missing, "
          f"{total_extra} extra (across {len(results)} cases)")
    if total_expected > 0:
        recall_pct = round(total_found / total_expected * 100, 1)
        print(f"  Recall: {total_found}/{total_expected} = {recall_pct}%")
    print()


def level2_to_dict(results: list[Level2CaseResult]) -> dict:
    """Serializes Level 2 results to a JSON-compatible dict."""
    return {
        "level": 2,
        "total_cases": len(results),
        "cases": [
            {
                "case_id": r.case_id,
                "total_expected": r.total_expected,
                "found": [
                    {
                        "flag": h.flag,
                        "severidad": h.severidad,
                        "matched_type": h.matched_anomaly_type,
                        "matched_metric_origin": h.matched_metric_origin,
                        "matched_severity": h.matched_severity,
                    }
                    for h in r.found
                ],
                "missing": [
                    {"flag": h.flag, "severidad": h.severidad}
                    for h in r.missing
                ],
                "extra": r.extra,
                "error": r.error,
            }
            for r in results
        ],
    }


# ---------------------------------------------------------------------------
# File output — save results to tests/eval_test/results/run_<timestamp>.json
# ---------------------------------------------------------------------------

def save_results(summary: EvalSummary, level2_results: list | None = None) -> str:
    """
    Saves evaluation results to a JSON file under tests/eval_test/results/.
    Returns the path to the saved file.

    File naming: run_<timestamp>.json where timestamp uses dashes instead of
    colons for filename safety (e.g., 2024-06-15T10-30-45).
    """
    from datetime import datetime

    results_dir = Path(__file__).parent / "results"
    os.makedirs(results_dir, exist_ok=True)

    now = datetime.now()
    timestamp_iso = now.strftime("%Y-%m-%dT%H:%M:%S")
    timestamp_filename = now.strftime("%Y-%m-%dT%H-%M-%S")

    output = {
        "timestamp": timestamp_iso,
        "level": 1,
        "summary": {
            "total_cases": summary.total_cases,
            "passed_cases": summary.passed_cases,
            "failed_cases": summary.failed_cases,
            "total_metrics": summary.total_metrics,
            "correct_metrics": summary.correct_metrics,
            "accuracy_pct": summary.accuracy_pct,
        },
        "cases": summary_to_dict(summary)["cases"],
        "level2": level2_to_dict(level2_results) if level2_results else None,
    }

    output_path = results_dir / f"run_{timestamp_filename}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return str(output_path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="MEPIA Eval Runner — validate S3 functions against ground truth"
    )
    parser.add_argument(
        "--case",
        type=str,
        default=None,
        help="Run only a specific case number (e.g., '01')",
    )
    parser.add_argument(
        "--full-pipeline",
        action="store_true",
        help="Run Level 2 full pipeline evaluation (S3→S4, requires OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON to stdout (in addition to formatted output)",
    )

    args = parser.parse_args()

    if args.full_pipeline:
        # Level 1 first (always run)
        summary = run_level_1(case_filter=args.case)
        print_results(summary)

        # Level 2: S3 → S4 (with LLM)
        level2_results = run_level_2(case_filter=args.case)

        if args.json and level2_results:
            print("\n--- JSON Output ---")
            print(json.dumps(level2_to_dict(level2_results), indent=2, ensure_ascii=False))

        # Save results to file
        output_path = save_results(summary, level2_results=level2_results or None)
        print(f"\n[*] Results saved to: {output_path}")

        # Level 2 never fails the process — it's for human review
        sys.exit(0)

    # Default: Level 1 (deterministic S3 only)
    summary = run_level_1(case_filter=args.case)
    print_results(summary)

    if args.json:
        print("\n--- JSON Output ---")
        print(json.dumps(summary_to_dict(summary), indent=2, ensure_ascii=False))

    # Save results to file
    output_path = save_results(summary)
    print(f"\n[*] Results saved to: {output_path}")

    # Exit with non-zero if any case failed
    sys.exit(0 if summary.failed_cases == 0 else 1)


if __name__ == "__main__":
    main()
