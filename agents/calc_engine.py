"""
S3 — Motor de Cálculo
Funciones puras de cálculo financiero. Sin LLM, sin interpretación.
Spec: .kiro/specs/mepia/s3_motor_calculo.md
"""
from __future__ import annotations

import calendar
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Literal, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# CalcStatus — valores posibles del campo status en CalcResult
# ---------------------------------------------------------------------------

CalcStatus = Literal[
    "ok",
    "warning",
    "critical",
    "incomplete_data",
    "unit_mismatch",
]


# ---------------------------------------------------------------------------
# CalcResult — contrato de salida de TODAS las funciones de S3
# Spec: s3_motor_calculo.md §Formato de respuesta
# ---------------------------------------------------------------------------

class CalcResult(BaseModel):
    """
    Output estándar de cada función del Motor de Cálculo.
    Nunca lanza excepción — errores se expresan como status.
    """
    metric: str                        # nombre de la métrica calculada
    value: Optional[Decimal] = None    # None cuando status es incomplete_data o unit_mismatch
    unit: str                          # unidad del valor (MXN, %, litros, unidades, etc.)
    status: CalcStatus                 # resultado de la evaluación contra umbrales
    context: str                       # descripción legible del resultado para S4


# ---------------------------------------------------------------------------
# Inputs de cada función — tipados para claridad interna
# (las funciones reciben estos valores + el cliente Supabase)
# ---------------------------------------------------------------------------

class ContributionMarginInput(BaseModel):
    """Input para calc_contribution_margin."""
    product_id: str                    # FK a recipes.id


class BreakEvenInput(BaseModel):
    """Input para calc_daily_break_even."""
    business_id: str
    date: str                          # YYYY-MM-DD


class WasteAnalysisInput(BaseModel):
    """Input para calc_waste_analysis."""
    ingredient_id: str                 # FK a recipes.ingredients key
    start_date: str                    # YYYY-MM-DD
    end_date: str                      # YYYY-MM-DD
    business_id: str


class BurnRateInput(BaseModel):
    """Input para calc_burn_rate."""
    business_id: str
    date: str                          # YYYY-MM-DD — determina el mes de cálculo


class PriceInflationInput(BaseModel):
    """Input para check_price_inflation."""
    ingredient_id: str
    business_id: str


class CashReconciliationInput(BaseModel):
    """Input para calc_cash_reconciliation."""
    business_id: str
    date: str                          # YYYY-MM-DD


# ---------------------------------------------------------------------------
# UnitConversion — fila de la tabla unit_conversions en Supabase
# Spec: s3_motor_calculo.md §Normalización de Unidades
# ---------------------------------------------------------------------------

class UnitConversion(BaseModel):
    """Representa una fila de la tabla unit_conversions."""
    from_unit: str                     # unidad origen (ej. "kg", "L")
    to_unit: str                       # unidad base (ej. "g", "ml")
    factor: Decimal                    # multiplicador (ej. 1000)


# ---------------------------------------------------------------------------
# CalcEngineResult — wrapper para ejecutar múltiples métricas en un solo run
# Usado por POST /calc/run en api/main.py
# ---------------------------------------------------------------------------

class CalcRunRequest(BaseModel):
    """Payload de POST /calc/run."""
    business_id: str
    date: str                          # YYYY-MM-DD
    metrics: list[str] = []            # lista de métricas a calcular; vacío = todas las active


class CalcRunResult(BaseModel):
    """Respuesta de POST /calc/run."""
    business_id: str
    date: str
    results: list[CalcResult]
    skipped_metrics: list[str] = []    # métricas dormant/blocked que no se calcularon
    run_id: str                        # UUID del registro en audit_results


# ===========================================================================
# FUNCIONES AUXILIARES PURAS (sin DB)
# ===========================================================================

def normalize_units(
    value: Decimal,
    from_unit: str,
    to_unit: str,
    conversions: list[UnitConversion],
) -> Decimal | None:
    """
    Convierte `value` de `from_unit` a `to_unit` usando la tabla de conversiones.

    Reglas:
    - Si from_unit == to_unit → retorna value sin cambio.
    - Si existe conversión directa → aplica el factor.
    - Si no hay conversión disponible → retorna None (indica unit_mismatch).
    """
    # Misma unidad: no hay nada que convertir
    if from_unit == to_unit:
        return value

    # Buscar conversión directa en la lista cargada desde DB
    for conv in conversions:
        if conv.from_unit == from_unit and conv.to_unit == to_unit:
            return value * conv.factor

    # No se encontró conversión — el caller debe emitir unit_mismatch
    return None


def days_in_month(date_str: str) -> int:
    """
    Retorna el número real de días del mes para la fecha dada (YYYY-MM-DD).

    Usa calendar.monthrange para respetar años bisiestos (febrero 28/29).
    NUNCA retorna 30 fijo.
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    # monthrange retorna (weekday_del_primer_dia, total_dias_del_mes)
    _, total_days = calendar.monthrange(dt.year, dt.month)
    return total_days


# ===========================================================================
# FUNCIONES DE CÁLCULO FINANCIERO
# ===========================================================================

def calc_contribution_margin(product_id: str, db: Any) -> CalcResult:
    """
    Calcula el Margen de Contribución (MC) de un producto.

    Fórmula:
        MC = precio_venta - sum(ingrediente_qty × precio_unitario)

    Fuentes de datos:
        - recipes: sale_price + ingredients (JSONB con qty por ingrediente)
        - transactions: última factura por ingrediente para precio_unitario

    Umbrales:
        - critical : MC_pct < 10%
        - warning  : MC_pct < 20%
        - ok       : MC_pct >= 20%
    """
    try:
        # --- 1. Obtener receta del producto ---
        receta_resp = (
            db.table("recipes")
            .select("sale_price, ingredients")
            .eq("id", product_id)
            .single()
            .execute()
        )
        receta = receta_resp.data
        if not receta:
            return CalcResult(
                metric="margen_contribucion",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=f"No se encontró receta para product_id={product_id}.",
            )

        precio_venta = Decimal(str(receta["sale_price"]))
        ingredientes: dict = receta.get("ingredients") or {}

        if not ingredientes:
            return CalcResult(
                metric="margen_contribucion",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=f"La receta de product_id={product_id} no tiene ingredientes.",
            )

        # --- 2. Calcular costo total de ingredientes ---
        costo_total = Decimal("0")
        ingredientes_sin_precio: list[str] = []

        for ing_id, qty_raw in ingredientes.items():
            qty = Decimal(str(qty_raw))

            # Última factura del ingrediente (precio unitario más reciente)
            tx_resp = (
                db.table("transactions")
                .select("unit_price")
                .eq("ingredient_id", ing_id)
                .order("transaction_date", desc=True)
                .limit(1)
                .execute()
            )
            tx_rows = tx_resp.data or []

            if not tx_rows or tx_rows[0].get("unit_price") is None:
                ingredientes_sin_precio.append(ing_id)
                continue

            precio_unitario = Decimal(str(tx_rows[0]["unit_price"]))
            costo_total += qty * precio_unitario

        # Si algún ingrediente no tiene precio, no podemos calcular con certeza
        if ingredientes_sin_precio:
            return CalcResult(
                metric="margen_contribucion",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=(
                    f"Sin precio para ingrediente(s): {', '.join(ingredientes_sin_precio)}. "
                    "Se requiere al menos una factura por ingrediente."
                ),
            )

        # --- 3. Calcular MC y evaluar umbrales ---
        mc = precio_venta - costo_total

        if precio_venta == Decimal("0"):
            return CalcResult(
                metric="margen_contribucion",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context="El precio de venta del producto es 0.",
            )

        mc_pct = (mc / precio_venta * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if mc_pct < Decimal("10"):
            status: CalcStatus = "critical"
        elif mc_pct < Decimal("20"):
            status = "warning"
        else:
            status = "ok"

        return CalcResult(
            metric="margen_contribucion",
            value=mc.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            unit="MXN",
            status=status,
            context=(
                f"MC={mc:.2f} MXN ({mc_pct:.1f}% del precio de venta {precio_venta:.2f} MXN). "
                f"Costo de ingredientes: {costo_total:.2f} MXN."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="margen_contribucion",
            value=None,
            unit="MXN",
            status="incomplete_data",
            context=f"Error al consultar datos para product_id={product_id}: {exc}",
        )


def calc_daily_break_even(business_id: str, date: str, db: Any) -> CalcResult:
    """
    Calcula el Punto de Equilibrio diario en unidades.

    Fórmula:
        PE_unidades = (sum(FIXED expenses del mes) / days_in_month(date)) / MC_promedio

    Fuentes de datos:
        - transactions: expense_behavior = "FIXED" del mes
        - recipes + transactions: MC promedio de todos los productos con receta

    Notas:
        - Usa days_in_month(date) como divisor, NUNCA 30 fijo.
        - Solo gastos con expense_behavior confirmado explícitamente.
    """
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        # Rango del mes completo
        primer_dia = dt.replace(day=1).strftime("%Y-%m-%d")
        ultimo_dia = dt.replace(
            day=days_in_month(date)
        ).strftime("%Y-%m-%d")

        # --- 1. Gastos FIXED del mes ---
        gastos_resp = (
            db.table("transactions")
            .select("amount")
            .eq("business_id", business_id)
            .eq("expense_behavior", "FIXED")
            .gte("transaction_date", primer_dia)
            .lte("transaction_date", ultimo_dia)
            .execute()
        )
        gastos_rows = gastos_resp.data or []

        if not gastos_rows:
            return CalcResult(
                metric="punto_equilibrio_diario",
                value=None,
                unit="unidades/día",
                status="incomplete_data",
                context=(
                    f"No hay gastos FIXED confirmados para {business_id} "
                    f"en {dt.strftime('%B %Y')}."
                ),
            )

        total_fixed = sum(Decimal(str(r["amount"])) for r in gastos_rows)

        # --- 2. MC promedio de todos los productos con receta ---
        recetas_resp = (
            db.table("recipes")
            .select("id, sale_price, ingredients")
            .eq("business_id", business_id)
            .execute()
        )
        recetas = recetas_resp.data or []

        mc_valores: list[Decimal] = []
        for receta in recetas:
            pid = receta["id"]
            # Reutilizamos calc_contribution_margin para obtener el MC de cada producto
            resultado = calc_contribution_margin(pid, db)
            if resultado.status == "ok" or resultado.status == "warning" or resultado.status == "critical":
                if resultado.value is not None:
                    mc_valores.append(resultado.value)

        if not mc_valores:
            return CalcResult(
                metric="punto_equilibrio_diario",
                value=None,
                unit="unidades/día",
                status="incomplete_data",
                context="No se pudo calcular MC promedio: sin productos con receta y precios completos.",
            )

        mc_promedio = sum(mc_valores) / Decimal(str(len(mc_valores)))

        if mc_promedio == Decimal("0"):
            return CalcResult(
                metric="punto_equilibrio_diario",
                value=None,
                unit="unidades/día",
                status="incomplete_data",
                context="MC promedio es 0 — no es posible calcular el punto de equilibrio.",
            )

        # --- 3. Calcular PE diario ---
        dias = Decimal(str(days_in_month(date)))
        pe_diario = (total_fixed / dias / mc_promedio).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return CalcResult(
            metric="punto_equilibrio_diario",
            value=pe_diario,
            unit="unidades/día",
            status="ok",
            context=(
                f"Gastos fijos del mes: {total_fixed:.2f} MXN / {int(dias)} días. "
                f"MC promedio: {mc_promedio:.2f} MXN. "
                f"Se necesitan vender {pe_diario:.1f} unidades/día para cubrir costos fijos."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="punto_equilibrio_diario",
            value=None,
            unit="unidades/día",
            status="incomplete_data",
            context=f"Error al calcular punto de equilibrio para {business_id}: {exc}",
        )


def calc_waste_analysis(
    ingredient_id: str,
    start_date: str,
    end_date: str,
    business_id: str,
    db: Any,
) -> CalcResult:
    """
    Calcula el porcentaje de merma de un ingrediente en un rango de fechas.

    Fórmula:
        merma_pct = (comprado_base - consumo_teorico_base) / comprado_base × 100

    Donde:
        comprado_base    = sum de qty comprada, normalizada a unidad base
        consumo_teorico  = sum(ventas_producto × qty_ingrediente_en_receta), normalizada

    Umbrales:
        - critical : merma_pct > 15%
        - warning  : merma_pct > 5%
        - ok       : merma_pct <= 5%
    """
    try:
        # --- 1. Cargar conversiones de unidades desde DB ---
        conv_resp = db.table("unit_conversions").select("*").execute()
        conversions = [UnitConversion(**r) for r in (conv_resp.data or [])]

        # --- 2. Cantidad comprada del ingrediente en el rango ---
        compras_resp = (
            db.table("transactions")
            .select("quantity, unit")
            .eq("business_id", business_id)
            .eq("ingredient_id", ingredient_id)
            .gte("transaction_date", start_date)
            .lte("transaction_date", end_date)
            .execute()
        )
        compras = compras_resp.data or []

        if not compras:
            return CalcResult(
                metric="merma",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Sin compras registradas para ingrediente {ingredient_id} "
                    f"entre {start_date} y {end_date}."
                ),
            )

        # Normalizar todas las compras a la unidad base del primer registro
        unidad_base = compras[0]["unit"]
        total_comprado = Decimal("0")

        for compra in compras:
            qty = Decimal(str(compra["quantity"]))
            unidad_origen = compra["unit"]
            qty_normalizada = normalize_units(qty, unidad_origen, unidad_base, conversions)

            if qty_normalizada is None:
                return CalcResult(
                    metric="merma",
                    value=None,
                    unit="%",
                    status="unit_mismatch",
                    context=(
                        f"Unidades incompatibles en compras de {ingredient_id}: "
                        f"'{unidad_origen}' no se puede convertir a '{unidad_base}'."
                    ),
                )
            total_comprado += qty_normalizada

        # --- 3. Consumo teórico: ventas × qty en receta ---
        # Buscar todas las recetas que usan este ingrediente
        recetas_resp = (
            db.table("recipes")
            .select("id, ingredients")
            .eq("business_id", business_id)
            .execute()
        )
        recetas = recetas_resp.data or []

        # Filtrar recetas que contienen el ingrediente
        recetas_con_ing = [
            r for r in recetas
            if ingredient_id in (r.get("ingredients") or {})
        ]

        consumo_teorico = Decimal("0")

        for receta in recetas_con_ing:
            pid = receta["id"]
            ing_info = receta["ingredients"][ingredient_id]

            # ing_info puede ser un número (qty) o un dict {"qty": x, "unit": y}
            if isinstance(ing_info, dict):
                qty_receta = Decimal(str(ing_info.get("qty", 0)))
                unidad_receta = ing_info.get("unit", unidad_base)
            else:
                qty_receta = Decimal(str(ing_info))
                unidad_receta = unidad_base

            # Ventas del producto en el rango desde pos_inputs
            ventas_resp = (
                db.table("pos_inputs")
                .select("quantity")
                .eq("business_id", business_id)
                .eq("product_id", pid)
                .gte("date", start_date)
                .lte("date", end_date)
                .execute()
            )
            ventas_rows = ventas_resp.data or []
            total_ventas = sum(Decimal(str(v["quantity"])) for v in ventas_rows)

            # Normalizar qty de receta a unidad base
            qty_receta_base = normalize_units(qty_receta, unidad_receta, unidad_base, conversions)
            if qty_receta_base is None:
                return CalcResult(
                    metric="merma",
                    value=None,
                    unit="%",
                    status="unit_mismatch",
                    context=(
                        f"Unidades incompatibles en receta de {pid}: "
                        f"'{unidad_receta}' no se puede convertir a '{unidad_base}'."
                    ),
                )

            consumo_teorico += total_ventas * qty_receta_base

        # --- 4. Calcular merma ---
        if total_comprado == Decimal("0"):
            return CalcResult(
                metric="merma",
                value=None,
                unit="%",
                status="incomplete_data",
                context="Total comprado es 0 — no se puede calcular merma.",
            )

        merma_abs = total_comprado - consumo_teorico
        merma_pct = (merma_abs / total_comprado * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if merma_pct > Decimal("10"):
            status: CalcStatus = "critical"
        elif merma_pct > Decimal("5"):
            status = "warning"
        else:
            status = "ok"

        return CalcResult(
            metric="merma",
            value=merma_pct,
            unit="%",
            status=status,
            context=(
                f"Comprado: {total_comprado:.2f} {unidad_base}. "
                f"Consumo teórico: {consumo_teorico:.2f} {unidad_base}. "
                f"Merma: {merma_abs:.2f} {unidad_base} ({merma_pct:.1f}%)."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="merma",
            value=None,
            unit="%",
            status="incomplete_data",
            context=f"Error al calcular merma para {ingredient_id}: {exc}",
        )


def calc_burn_rate(business_id: str, date: str, db: Any) -> CalcResult:
    """
    Calcula el Burn Rate diario del negocio (gasto promedio por día del mes).

    Fórmula:
        BR = sum(FIXED + VARIABLE expenses del mes) / days_in_month(date)

    Notas:
        - Usa days_in_month(date) como divisor, NUNCA 30 fijo.
        - Solo gastos con expense_behavior confirmado (FIXED o VARIABLE).
        - No hay umbrales de warning/critical — siempre "ok" si hay datos.
    """
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        primer_dia = dt.replace(day=1).strftime("%Y-%m-%d")
        ultimo_dia = dt.replace(day=days_in_month(date)).strftime("%Y-%m-%d")

        # --- 1. Gastos FIXED + VARIABLE del mes ---
        gastos_resp = (
            db.table("transactions")
            .select("amount, expense_behavior")
            .eq("business_id", business_id)
            .in_("expense_behavior", ["FIXED", "VARIABLE"])
            .gte("transaction_date", primer_dia)
            .lte("transaction_date", ultimo_dia)
            .execute()
        )
        gastos_rows = gastos_resp.data or []

        if not gastos_rows:
            return CalcResult(
                metric="burn_rate",
                value=None,
                unit="MXN/día",
                status="incomplete_data",
                context=(
                    f"No hay gastos FIXED o VARIABLE confirmados para {business_id} "
                    f"en {dt.strftime('%B %Y')}."
                ),
            )

        # --- 2. Sumar todos los gastos del mes ---
        total_gastos = sum(Decimal(str(r["amount"])) for r in gastos_rows)
        dias = Decimal(str(days_in_month(date)))

        burn_rate = (total_gastos / dias).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Desglose por tipo para el contexto
        total_fixed = sum(
            Decimal(str(r["amount"])) for r in gastos_rows if r["expense_behavior"] == "FIXED"
        )
        total_variable = sum(
            Decimal(str(r["amount"])) for r in gastos_rows if r["expense_behavior"] == "VARIABLE"
        )

        return CalcResult(
            metric="burn_rate",
            value=burn_rate,
            unit="MXN/día",
            status="ok",
            context=(
                f"Gastos del mes ({dt.strftime('%B %Y')}): "
                f"Fijos {total_fixed:.2f} MXN + Variables {total_variable:.2f} MXN "
                f"= {total_gastos:.2f} MXN / {int(dias)} días = {burn_rate:.2f} MXN/día."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="burn_rate",
            value=None,
            unit="MXN/día",
            status="incomplete_data",
            context=f"Error al calcular burn rate para {business_id}: {exc}",
        )


def check_price_inflation(ingredient_id: str, business_id: str, db: Any) -> CalcResult:
    """
    Detecta inflación de precio en un ingrediente comparando la última factura
    contra el promedio histórico de facturas anteriores.

    Fórmula:
        delta_pct = ((precio_ultima - precio_promedio_anteriores) / precio_promedio_anteriores) × 100

    Umbrales:
        - critical : delta_pct > 15%
        - warning  : delta_pct entre 5% y 15%
        - ok       : delta_pct <= 5%
    """
    try:
        # --- 1. Obtener todas las facturas del ingrediente, más reciente primero ---
        facturas_resp = (
            db.table("transactions")
            .select("unit_price, transaction_date")
            .eq("business_id", business_id)
            .eq("ingredient_id", ingredient_id)
            .order("transaction_date", desc=True)
            .execute()
        )
        facturas = facturas_resp.data or []

        # Filter out records without unit_price (e.g., quantity-only purchase records)
        facturas = [f for f in facturas if f.get("unit_price") is not None]

        # Se necesitan al menos 2 facturas para comparar
        if len(facturas) < 2:
            return CalcResult(
                metric="inflacion_precio",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Solo {len(facturas)} factura(s) para {ingredient_id}. "
                    "Se necesitan al menos 2 para detectar inflación."
                ),
            )

        # --- 2. Precio de la última factura y promedio de las anteriores ---
        precio_ultima = Decimal(str(facturas[0]["unit_price"]))
        fecha_ultima = facturas[0]["transaction_date"]

        precios_anteriores = [
            Decimal(str(f["unit_price"])) for f in facturas[1:]
            if f.get("unit_price") is not None
        ]

        if not precios_anteriores:
            return CalcResult(
                metric="inflacion_precio",
                value=None,
                unit="%",
                status="incomplete_data",
                context="Las facturas anteriores no tienen precio unitario registrado.",
            )

        precio_promedio = sum(precios_anteriores) / Decimal(str(len(precios_anteriores)))

        if precio_promedio == Decimal("0"):
            return CalcResult(
                metric="inflacion_precio",
                value=None,
                unit="%",
                status="incomplete_data",
                context="El precio promedio histórico es 0 — no se puede calcular delta.",
            )

        # --- 3. Calcular delta y evaluar umbrales ---
        delta_pct = (
            (precio_ultima - precio_promedio) / precio_promedio * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        delta_abs = abs(delta_pct)

        if delta_abs > Decimal("15"):
            status: CalcStatus = "critical"
        elif delta_abs > Decimal("5"):
            status = "warning"
        else:
            status = "ok"

        return CalcResult(
            metric="inflacion_precio",
            value=delta_pct,
            unit="%",
            status=status,
            context=(
                f"Última factura ({fecha_ultima}): {precio_ultima:.2f} MXN. "
                f"Promedio histórico ({len(precios_anteriores)} facturas): {precio_promedio:.2f} MXN. "
                f"Variación: {delta_pct:+.1f}%."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="inflacion_precio",
            value=None,
            unit="%",
            status="incomplete_data",
            context=f"Error al calcular inflación de precio para {ingredient_id}: {exc}",
        )


def calc_cash_reconciliation(business_id: str, date: str, db: Any) -> CalcResult:
    """
    Concilia el efectivo del día comparando lo esperado (POS) vs lo contado físicamente.

    Fórmula:
        expected_cash = initial_float + pos_cash_sales - refunds - cash_payouts
        variance      = actual_cash_counted - expected_cash
        variance_pct  = variance / pos_cash_sales × 100  (si pos_cash_sales > 0)

    Fuentes de datos:
        - pos_inputs  : cash_sales, refunds del día
        - cash_counts : initial_float, actual_counted, cash_payouts del día

    Umbrales:
        - critical : variance < -1% de pos_cash_sales (o variance < 0 si pos_cash_sales = 0)
        - warning  : variance < 0
        - ok       : variance >= 0
    """
    try:
        # --- 1. Datos del POS del día ---
        pos_resp = (
            db.table("pos_inputs")
            .select("cash_sales, refunds")
            .eq("business_id", business_id)
            .eq("date", date)
            .single()
            .execute()
        )
        pos_data = pos_resp.data

        if not pos_data:
            return CalcResult(
                metric="conciliacion_caja",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=f"Sin datos de POS para {business_id} el {date}.",
            )

        pos_cash_sales = Decimal(str(pos_data.get("cash_sales") or 0))
        refunds = Decimal(str(pos_data.get("refunds") or 0))

        # --- 2. Conteo físico de caja del día ---
        cash_resp = (
            db.table("cash_counts")
            .select("initial_float, actual_counted, cash_payouts")
            .eq("business_id", business_id)
            .eq("date", date)
            .single()
            .execute()
        )
        cash_data = cash_resp.data

        if not cash_data:
            return CalcResult(
                metric="conciliacion_caja",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=f"Sin conteo de caja registrado para {business_id} el {date}.",
            )

        initial_float = Decimal(str(cash_data.get("initial_float") or 0))
        actual_counted = Decimal(str(cash_data.get("actual_counted") or 0))
        cash_payouts = Decimal(str(cash_data.get("cash_payouts") or 0))

        # --- 3. Calcular varianza ---
        expected_cash = initial_float + pos_cash_sales - refunds - cash_payouts
        variance = actual_counted - expected_cash

        # --- 4. Evaluar umbrales ---
        if pos_cash_sales > Decimal("0"):
            variance_pct = (variance / pos_cash_sales * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            # critical: varianza negativa mayor al 1% de ventas en efectivo
            if variance_pct < Decimal("-1"):
                status: CalcStatus = "critical"
            elif variance < Decimal("0"):
                status = "warning"
            else:
                status = "ok"
            pct_context = f" ({variance_pct:+.2f}% de ventas en efectivo)"
        else:
            # Sin ventas en efectivo: usar varianza absoluta
            variance_pct = Decimal("0")
            if variance < Decimal("0"):
                status = "critical"
            else:
                status = "ok"
            pct_context = " (sin ventas en efectivo registradas)"

        return CalcResult(
            metric="conciliacion_caja",
            value=variance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            unit="MXN",
            status=status,
            context=(
                f"Efectivo esperado: {expected_cash:.2f} MXN "
                f"(fondo inicial {initial_float:.2f} + ventas {pos_cash_sales:.2f} "
                f"- devoluciones {refunds:.2f} - pagos {cash_payouts:.2f}). "
                f"Contado: {actual_counted:.2f} MXN. "
                f"Varianza: {variance:+.2f} MXN{pct_context}."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="conciliacion_caja",
            value=None,
            unit="MXN",
            status="incomplete_data",
            context=f"Error al conciliar caja para {business_id} el {date}: {exc}",
        )


# ===========================================================================
# ORQUESTADOR PRINCIPAL — run_calc_engine()
# Spec: s3_motor_calculo.md §Reglas de Oro
# ===========================================================================

def run_calc_engine(
    gatekeeper_result: Any,
    db: Any,
    date: str,
    business_id: str,
) -> CalcRunResult:
    """
    Orquesta todas las funciones de cálculo financiero para un negocio y fecha.

    Recibe el GatekeeperResult (output de S2) y ejecuta SOLO las métricas
    con status "active". Las métricas dormant/blocked se registran en
    skipped_metrics sin calcular.

    Flujo:
        1. Leer active_metrics del GatekeeperResult
        2. Para cada métrica active → ejecutar la función correspondiente
        3. Métricas dormant/blocked → agregar a skipped_metrics
        4. Persistir resultados en audit_results con node_id="S3"
        5. Retornar CalcRunResult

    Args:
        gatekeeper_result : GatekeeperResult (o dict compatible) de S2
        db                : cliente Supabase (inyección de dependencias)
        date              : YYYY-MM-DD del día a calcular
        business_id       : UUID del negocio

    Returns:
        CalcRunResult con results[], skipped_metrics[] y run_id
    """
    from uuid import uuid4
    from datetime import datetime, timezone

    run_id = str(uuid4())
    results: list[CalcResult] = []
    skipped: list[str] = []

    # Extraer active_metrics — soporta tanto objeto Pydantic como dict
    if isinstance(gatekeeper_result, dict):
        active_metrics: list[str] = gatekeeper_result.get("active_metrics", [])
        dormant_metrics = gatekeeper_result.get("dormant_metrics", [])
        blocked_metrics = gatekeeper_result.get("blocked_metrics", [])
    else:
        active_metrics = getattr(gatekeeper_result, "active_metrics", [])
        dormant_metrics = getattr(gatekeeper_result, "dormant_metrics", [])
        blocked_metrics = getattr(gatekeeper_result, "blocked_metrics", [])

    # Registrar métricas que no se calculan (dormant + blocked)
    for dm in dormant_metrics:
        metric_name = dm["metric"] if isinstance(dm, dict) else dm.metric
        skipped.append(metric_name)

    for bm in blocked_metrics:
        metric_name = bm["metric"] if isinstance(bm, dict) else bm.metric
        skipped.append(metric_name)

    # ---------------------------------------------------------------------------
    # Mapa métrica → función de cálculo
    # Cada función recibe (business_id, date, db) o variantes según el spec.
    # Las métricas que requieren IDs adicionales (product_id, ingredient_id)
    # se resuelven consultando los registros activos del negocio.
    # ---------------------------------------------------------------------------

    for metric in active_metrics:

        # --- cash_reconciliation ---
        if metric == "cash_reconciliation":
            result = calc_cash_reconciliation(business_id, date, db)
            results.append(result)

        # --- daily_break_even ---
        elif metric == "daily_break_even":
            result = calc_daily_break_even(business_id, date, db)
            results.append(result)

        # --- operative_cost_margin (burn_rate como proxy del margen operativo) ---
        elif metric == "operative_cost_margin":
            result = calc_burn_rate(business_id, date, db)
            # Renombrar métrica para alinear con el nombre del Gatekeeper
            results.append(
                CalcResult(
                    metric="operative_cost_margin",
                    value=result.value,
                    unit=result.unit,
                    status=result.status,
                    context=result.context,
                )
            )

        # --- health_score: calcula MC de todos los productos activos ---
        elif metric == "health_score":
            try:
                recetas_resp = (
                    db.table("recipes")
                    .select("id")
                    .eq("business_id", business_id)
                    .execute()
                )
                product_ids = [r["id"] for r in (recetas_resp.data or [])]

                if not product_ids:
                    results.append(
                        CalcResult(
                            metric="health_score",
                            value=None,
                            unit="MXN",
                            status="incomplete_data",
                            context="Sin recetas registradas para calcular health_score.",
                        )
                    )
                else:
                    # Calcular MC de cada producto y promediar
                    mc_results = [calc_contribution_margin(pid, db) for pid in product_ids]
                    mc_validos = [
                        r.value for r in mc_results
                        if r.value is not None and r.status in ("ok", "warning", "critical")
                    ]

                    if not mc_validos:
                        results.append(
                            CalcResult(
                                metric="health_score",
                                value=None,
                                unit="MXN",
                                status="incomplete_data",
                                context="No se pudo calcular MC de ningún producto.",
                            )
                        )
                    else:
                        mc_promedio = sum(mc_validos) / Decimal(str(len(mc_validos)))
                        # Determinar status por el peor resultado individual
                        worst = "ok"
                        for r in mc_results:
                            if r.status == "critical":
                                worst = "critical"
                                break
                            if r.status == "warning":
                                worst = "warning"
                        results.append(
                            CalcResult(
                                metric="health_score",
                                value=mc_promedio.quantize(
                                    Decimal("0.01"), rounding=ROUND_HALF_UP
                                ),
                                unit="MXN",
                                status=worst,
                                context=(
                                    f"MC promedio de {len(mc_validos)} producto(s): "
                                    f"{mc_promedio:.2f} MXN."
                                ),
                            )
                        )
            except Exception as exc:
                results.append(
                    CalcResult(
                        metric="health_score",
                        value=None,
                        unit="MXN",
                        status="incomplete_data",
                        context=f"Error al calcular health_score: {exc}",
                    )
                )

        # --- inventory_variance: merma de todos los ingredientes activos ---
        elif metric == "inventory_variance":
            try:
                # Obtener ingredientes únicos de todas las recetas del negocio
                recetas_resp = (
                    db.table("recipes")
                    .select("ingredients")
                    .eq("business_id", business_id)
                    .execute()
                )
                ingredient_ids: set[str] = set()
                for receta in (recetas_resp.data or []):
                    for ing_id in (receta.get("ingredients") or {}).keys():
                        ingredient_ids.add(ing_id)

                if not ingredient_ids:
                    results.append(
                        CalcResult(
                            metric="inventory_variance",
                            value=None,
                            unit="%",
                            status="incomplete_data",
                            context="Sin ingredientes en recetas para calcular merma.",
                        )
                    )
                else:
                    # Calcular merma del mes (inicio de mes → date)
                    dt = datetime.strptime(date, "%Y-%m-%d")
                    start_date = dt.replace(day=1).strftime("%Y-%m-%d")

                    waste_results = [
                        calc_waste_analysis(ing_id, start_date, date, business_id, db)
                        for ing_id in ingredient_ids
                    ]

                    # Agregar todos los resultados individuales
                    for wr in waste_results:
                        results.append(
                            CalcResult(
                                metric=f"inventory_variance_{wr.metric}",
                                value=wr.value,
                                unit=wr.unit,
                                status=wr.status,
                                context=wr.context,
                            )
                        )
            except Exception as exc:
                results.append(
                    CalcResult(
                        metric="inventory_variance",
                        value=None,
                        unit="%",
                        status="incomplete_data",
                        context=f"Error al calcular inventory_variance: {exc}",
                    )
                )

        # =====================================================================
        # 26 métricas nuevas de S3 (extensión post spec-driven original)
        # =====================================================================

        elif metric == "avg_ticket":
            try:
                results.append(calc_avg_ticket(business_id, date, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="avg_ticket", value=None, unit="MXN",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "channel_mix":
            try:
                results.append(calc_channel_mix(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="channel_mix", value=None, unit="%",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "discount_rate":
            try:
                results.append(calc_discount_rate(business_id, date, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="tasa_descuento", value=None, unit="%",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "hourly_sales_pattern":
            try:
                results.append(calc_hourly_sales_pattern(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="hourly_sales_pattern", value=None, unit="",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "sales_by_staff":
            try:
                results.append(calc_sales_by_staff(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="sales_by_staff", value=None, unit="MXN",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "sales_by_branch":
            try:
                results.append(calc_sales_by_branch(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="sales_by_branch", value=None, unit="MXN",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "top_bottom_sellers":
            try:
                results.append(calc_top_bottom_sellers(business_id, date, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="top_bottom_sellers", value=None, unit="",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "revenue_concentration":
            try:
                results.append(calc_revenue_concentration(business_id, date, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="revenue_concentration", value=None, unit="%",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "category_mix":
            try:
                results.append(calc_category_mix(business_id, date, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="category_mix", value=None, unit="%",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "modifier_attach_rate":
            try:
                results.append(calc_modifier_attach_rate(business_id, date, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="modifier_attach_rate", value=None, unit="%",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "item_discount_split":
            try:
                results.append(calc_item_discount_split(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="item_discount_split", value=None, unit="%",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "payment_mix":
            try:
                results.append(calc_payment_mix(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="payment_mix", value=None, unit="%",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "staff_courtesy_ratio":
            try:
                results.append(calc_staff_courtesy_ratio(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="staff_courtesy_ratio", value=None, unit="%",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "loyalty_redemption_cost":
            try:
                results.append(calc_loyalty_redemption_cost(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="loyalty_redemption_cost", value=None, unit="MXN",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "price_consistency":
            try:
                results.append(check_price_consistency(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="consistencia_precios", value=None, unit="",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "delivery_commission_cost":
            try:
                results.append(calc_delivery_commission_cost(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="delivery_commission_cost", value=None, unit="MXN",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "commission_cost_ratio":
            try:
                results.append(calc_commission_cost_ratio(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="commission_cost_ratio", value=None, unit="%",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "contribution_margin_by_channel":
            try:
                results.append(calc_contribution_margin_by_channel(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="contribution_margin_by_channel", value=None, unit="%",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "ticket_volume":
            try:
                results.append(calc_ticket_volume(business_id, date, "dia", db))
            except Exception as exc:
                results.append(CalcResult(metric="ticket_volume", value=None, unit="",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "cancellation_rate":
            try:
                results.append(calc_cancellation_rate(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="cancellation_rate", value=None, unit="%",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "reprint_rate":
            try:
                results.append(calc_reprint_rate(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="reprint_rate", value=None, unit="%",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "shift_cash_variance":
            try:
                results.append(calc_shift_cash_variance(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="shift_cash_variance", value=None, unit="MXN",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "labor_cost_ratio":
            try:
                results.append(calc_labor_cost_ratio(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="labor_cost_ratio", value=None, unit="%",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "sales_per_labor_hour":
            try:
                results.append(calc_sales_per_labor_hour(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="sales_per_labor_hour", value=None, unit="MXN",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "waste_cost":
            try:
                results.append(calc_waste_cost(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="waste_cost", value=None, unit="MXN",
                                           status="incomplete_data", context=f"Error: {exc}"))

        elif metric == "stock_days_remaining":
            try:
                results.append(calc_stock_days_remaining(business_id, date, db))
            except Exception as exc:
                results.append(CalcResult(metric="stock_days_remaining", value=None, unit="días",
                                           status="incomplete_data", context=f"Error: {exc}"))

        else:
            # Métrica activa sin función implementada — registrar como incomplete_data
            results.append(
                CalcResult(
                    metric=metric,
                    value=None,
                    unit="",
                    status="incomplete_data",
                    context=f"Métrica '{metric}' activa pero sin función de cálculo implementada.",
                )
            )

    # ---------------------------------------------------------------------------
    # Persistir resultados en audit_results con node_id="S3"
    # ---------------------------------------------------------------------------
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        db.table("audit_results").insert(
            {
                "id": run_id,
                "business_id": business_id,
                "date": date,
                "pipeline_layer": "sequential",
                "node_id": "S3",
                "node_status": "completed",
                "result_data": {
                    "results": [r.model_dump(mode="json") for r in results],
                    "skipped_metrics": skipped,
                },
                "created_at": now_iso,
            }
        ).execute()
    except Exception:
        # La persistencia no debe bloquear el retorno de resultados
        pass

    return CalcRunResult(
        business_id=business_id,
        date=date,
        results=results,
        skipped_metrics=skipped,
        run_id=run_id,
    )


# ===========================================================================
# FUNCIONES DE CÁLCULO — NIVEL TRANSACCIÓN (nuevas, requieren S1B API)
# Spec: s3_motor_calculo.md §Funciones — Nivel Transacción
# ===========================================================================


def calc_avg_ticket(
    business_id: str,
    start_date: str,
    end_date: str,
    db: Any,
) -> CalcResult:
    """
    Calcula el ticket promedio de ventas en un rango de fechas.

    Fórmula:
        avg_ticket = Σ(subtotal) / COUNT(tickets)

    Fuentes de datos:
        - transactions: type="ingreso", category="venta" en rango de fechas.
        - Campo raw_metadata.subtotal de cada ticket.

    Unidad: "MXN"
    Status: siempre "ok" (sin umbrales definidos aún).
    Edge: 0 tickets en el periodo → status: "incomplete_data", value: None.
    """
    try:
        # --- 1. Obtener tickets de venta en el rango ---
        resp = (
            db.table("transactions")
            .select("amount, raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .gte("transaction_date", start_date)
            .lte("transaction_date", end_date)
            .execute()
        )
        rows = resp.data or []

        if not rows:
            return CalcResult(
                metric="ticket_promedio",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=(
                    f"Sin tickets de venta para {business_id} "
                    f"entre {start_date} y {end_date}."
                ),
            )

        # --- 2. Calcular promedio ---
        total_subtotal = sum(
            Decimal(str((r.get("raw_metadata") or {}).get("subtotal", 0)))
            for r in rows
        )
        count = Decimal(str(len(rows)))
        avg = (total_subtotal / count).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return CalcResult(
            metric="ticket_promedio",
            value=avg,
            unit="MXN",
            status="ok",
            context=(
                f"Ticket promedio: {avg} MXN. "
                f"Total ventas: {total_subtotal:.2f} MXN en {len(rows)} tickets "
                f"({start_date} a {end_date})."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="ticket_promedio",
            value=None,
            unit="MXN",
            status="incomplete_data",
            context=f"Error al calcular ticket promedio para {business_id}: {exc}",
        )


def calc_ticket_volume(
    business_id: str,
    date: str,
    granularity: str,
    db: Any,
) -> CalcResult:
    """
    Calcula el volumen de tickets (cantidad) para una fecha dada.

    Fórmula:
        ticket_count = COUNT(transactions WHERE type="ingreso" AND category="venta")

    Parámetros:
        - granularity: "turno" | "dia"
          Si "turno", agrupa por turno usando shift_audit_events.
          Si "dia", retorna conteo total del día.

    Fuentes de datos:
        - transactions: type="ingreso", category="venta"
        - shift_audit_events: para agrupar por turno si granularity="turno"

    Unidad: "tickets"
    Status: siempre "ok" (sin umbrales definidos aún).
    Edge: sin datos → status: "incomplete_data".
    """
    try:
        # --- 1. Obtener tickets de venta del día ---
        resp = (
            db.table("transactions")
            .select("id, transaction_date, raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .eq("transaction_date", date)
            .execute()
        )
        rows = resp.data or []

        if not rows:
            return CalcResult(
                metric="volumen_tickets",
                value=None,
                unit="tickets",
                status="incomplete_data",
                context=(
                    f"Sin tickets de venta para {business_id} el {date}."
                ),
            )

        ticket_count = len(rows)

        # --- 2. Si granularidad es por turno, agrupar ---
        if granularity == "turno":
            shift_resp = (
                db.table("shift_audit_events")
                .select("shift_id, start_time, end_time")
                .eq("business_id", business_id)
                .eq("date", date)
                .execute()
            )
            shifts = shift_resp.data or []

            if shifts:
                # Agrupar tickets por turno usando timestamp en raw_metadata
                by_shift: dict[str, int] = {}
                for shift in shifts:
                    by_shift[shift.get("shift_id", "unknown")] = 0

                # Conteo simple por turno (se reporta en context)
                context_detail = (
                    f"Volumen total: {ticket_count} tickets el {date}. "
                    f"Turnos encontrados: {len(shifts)}."
                )
            else:
                context_detail = (
                    f"Volumen total: {ticket_count} tickets el {date}. "
                    f"Sin datos de turnos para desglose."
                )
        else:
            context_detail = (
                f"Volumen total: {ticket_count} tickets el {date}."
            )

        return CalcResult(
            metric="volumen_tickets",
            value=Decimal(str(ticket_count)),
            unit="tickets",
            status="ok",
            context=context_detail,
        )

    except Exception as exc:
        return CalcResult(
            metric="volumen_tickets",
            value=None,
            unit="tickets",
            status="incomplete_data",
            context=f"Error al calcular volumen de tickets para {business_id}: {exc}",
        )


def calc_channel_mix(
    business_id: str,
    date: str,
    db: Any,
) -> CalcResult:
    """
    Calcula la distribución porcentual de ventas por canal (order_type).

    Fórmula:
        Para cada order_type ∈ {Comedor, Para llevar, Delivery App}:
          pct = Σ(total_net WHERE order_type) / Σ(total_net total) × 100

    Fuentes de datos:
        - transactions: type="ingreso", category="venta"
        - transactions.raw_metadata.order_type (campo de S1B)

    Unidad: "%"
    value: dict serializado {order_type: pct}
    Status: siempre "ok" (sin umbrales).
    Edge: sin datos de order_type (ingestas legacy PDF) → status: "incomplete_data".
    """
    try:
        # --- 1. Obtener tickets con raw_metadata del día ---
        resp = (
            db.table("transactions")
            .select("amount, raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .eq("transaction_date", date)
            .execute()
        )
        rows = resp.data or []

        if not rows:
            return CalcResult(
                metric="channel_mix",
                value=None,
                unit="%",
                status="incomplete_data",
                context=f"Sin tickets de venta para {business_id} el {date}.",
            )

        # --- 2. Agrupar por order_type ---
        sales_by_channel: dict[str, Decimal] = {}
        total_sales = Decimal("0")
        tickets_sin_order_type = 0

        for row in rows:
            amount = Decimal(str(row["amount"]))
            total_sales += amount

            metadata = row.get("raw_metadata") or {}
            order_type = metadata.get("order_type")

            if not order_type:
                tickets_sin_order_type += 1
                continue

            sales_by_channel[order_type] = (
                sales_by_channel.get(order_type, Decimal("0")) + amount
            )

        # Edge: ningún ticket tiene order_type
        if not sales_by_channel:
            return CalcResult(
                metric="channel_mix",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Ningún ticket tiene order_type en raw_metadata para "
                    f"{business_id} el {date}. Posible ingesta legacy PDF."
                ),
            )

        # --- 3. Calcular porcentajes ---
        mix: dict[str, str] = {}
        for channel, channel_sales in sales_by_channel.items():
            pct = (channel_sales / total_sales * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            mix[channel] = str(pct)

        # value se serializa como Decimal del total (el dict va en context)
        # Per spec: value es un dict serializado — usamos el total_sales como
        # value principal y el mix completo en context
        import json
        mix_json = json.dumps(mix)

        return CalcResult(
            metric="channel_mix",
            value=total_sales.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            unit="%",
            status="ok",
            context=(
                f"Distribución por canal el {date}: {mix_json}. "
                f"Total ventas: {total_sales:.2f} MXN. "
                f"Tickets sin order_type: {tickets_sin_order_type}."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="channel_mix",
            value=None,
            unit="%",
            status="incomplete_data",
            context=f"Error al calcular channel mix para {business_id}: {exc}",
        )


def calc_discount_rate(
    business_id: str,
    start_date: str,
    end_date: str,
    db: Any,
) -> CalcResult:
    """
    Calcula la tasa de descuento como porcentaje del subtotal.

    Fórmula:
        discount_rate = Σ(discounts) / Σ(subtotal) × 100

    Desagregación por responsable (Tipo B):
        by_responsable = GROUP BY cajero_id/mesero_id:
          {staff_id: {discount_total, subtotal, rate_pct}}

    Principio de diseño:
        - DENOMINADOR: subtotal, NUNCA total_net.
        - Usar subtotal evita contaminación cruzada entre descuentos concurrentes.

    Fuentes de datos:
        - transactions: type="ingreso", category="venta"
        - transactions.raw_metadata: campos discounts, subtotal, cajero_id, mesero_id

    Unidad: "%"
    Umbrales:
        - warning  : discount_rate > 10%
        - ok       : discount_rate <= 10%
    Edge: Σsubtotal = 0 → status: "incomplete_data".
    """
    try:
        # --- 1. Obtener tickets con raw_metadata ---
        resp = (
            db.table("transactions")
            .select("amount, raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .gte("transaction_date", start_date)
            .lte("transaction_date", end_date)
            .execute()
        )
        rows = resp.data or []

        if not rows:
            return CalcResult(
                metric="tasa_descuento",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Sin tickets de venta para {business_id} "
                    f"entre {start_date} y {end_date}."
                ),
            )

        # --- 2. Acumular descuentos y subtotales ---
        total_discounts = Decimal("0")
        total_subtotal = Decimal("0")
        by_responsable: dict[str, dict[str, Decimal]] = {}

        for row in rows:
            metadata = row.get("raw_metadata") or {}
            discounts = Decimal(str(metadata.get("discounts", 0) or 0))
            subtotal = Decimal(str(metadata.get("subtotal", 0) or 0))

            total_discounts += discounts
            total_subtotal += subtotal

            # Identificar responsable (cajero_id o mesero_id)
            staff_id = metadata.get("cajero_id") or metadata.get("mesero_id")
            if staff_id:
                if staff_id not in by_responsable:
                    by_responsable[staff_id] = {
                        "discount_total": Decimal("0"),
                        "subtotal": Decimal("0"),
                    }
                by_responsable[staff_id]["discount_total"] += discounts
                by_responsable[staff_id]["subtotal"] += subtotal

        # Edge: subtotal total es 0
        if total_subtotal == Decimal("0"):
            return CalcResult(
                metric="tasa_descuento",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Subtotal acumulado es 0 para {business_id} "
                    f"entre {start_date} y {end_date}. "
                    "No es posible calcular tasa de descuento."
                ),
            )

        # --- 3. Calcular tasa global ---
        discount_rate = (
            total_discounts / total_subtotal * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # --- 3b. Evaluar umbrales ---
        status: CalcStatus = "ok"
        if discount_rate > Decimal("10"):
            status = "warning"

        # --- 4. Calcular tasa por responsable ---
        responsable_detail: dict[str, dict[str, str]] = {}
        for staff_id, data in by_responsable.items():
            staff_subtotal = data["subtotal"]
            staff_discount = data["discount_total"]
            if staff_subtotal > Decimal("0"):
                staff_rate = (
                    staff_discount / staff_subtotal * Decimal("100")
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                staff_rate = Decimal("0")
            responsable_detail[staff_id] = {
                "discount_total": str(staff_discount.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )),
                "subtotal": str(staff_subtotal.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )),
                "rate_pct": str(staff_rate),
            }

        import json
        by_responsable_json = json.dumps(responsable_detail)

        return CalcResult(
            metric="tasa_descuento",
            value=discount_rate,
            unit="%",
            status=status,
            context=(
                f"Tasa de descuento: {discount_rate}% "
                f"(descuentos: {total_discounts:.2f} MXN / subtotal: {total_subtotal:.2f} MXN). "
                f"Periodo: {start_date} a {end_date}. "
                f"by_responsable: {by_responsable_json}"
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="tasa_descuento",
            value=None,
            unit="%",
            status="incomplete_data",
            context=f"Error al calcular tasa de descuento para {business_id}: {exc}",
        )


def calc_hourly_sales_pattern(
    business_id: str,
    date: str,
    db: Any,
) -> CalcResult:
    """
    Identifica hora pico y hora valle de ventas para un día dado.

    Fórmula:
        Para cada hora H:
          sales_H = Σ(total_net WHERE EXTRACT(HOUR FROM timestamp) = H)

        hora_pico = H con mayor sales_H
        hora_valle = H con menor sales_H (excluyendo horas con 0 tickets)

        value = {"hora_pico": H_pico, "ventas_pico": sales_pico,
                 "hora_valle": H_valle, "ventas_valle": sales_valle}

    Fuentes de datos:
        - transactions: type="ingreso", category="venta"
        - transactions.raw_metadata.timestamp (ISO-8601 de S1B)

    Unidad: "resumen" — solo hora pico y hora valle, nunca la serie completa.
    Status: siempre "ok" (sin umbrales).
    Edge: <3 horas con ventas → status: "incomplete_data".
    """
    try:
        # --- 1. Obtener tickets con timestamp ---
        resp = (
            db.table("transactions")
            .select("amount, raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .eq("transaction_date", date)
            .execute()
        )
        rows = resp.data or []

        if not rows:
            return CalcResult(
                metric="patron_horario_ventas",
                value=None,
                unit="resumen",
                status="incomplete_data",
                context=f"Sin tickets de venta para {business_id} el {date}.",
            )

        # --- 2. Agrupar ventas por hora ---
        sales_by_hour: dict[int, Decimal] = {}

        for row in rows:
            amount = Decimal(str(row["amount"]))
            metadata = row.get("raw_metadata") or {}
            timestamp_str = metadata.get("timestamp")

            if not timestamp_str:
                continue

            try:
                # Parse ISO-8601 timestamp para extraer la hora
                dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                hour = dt.hour
            except (ValueError, AttributeError):
                continue

            sales_by_hour[hour] = sales_by_hour.get(hour, Decimal("0")) + amount

        # Edge: menos de 3 horas con ventas
        if len(sales_by_hour) < 3:
            return CalcResult(
                metric="patron_horario_ventas",
                value=None,
                unit="resumen",
                status="incomplete_data",
                context=(
                    f"Solo {len(sales_by_hour)} hora(s) con ventas el {date}. "
                    "Se requieren al menos 3 horas para identificar patrón."
                ),
            )

        # --- 3. Identificar hora pico y hora valle ---
        hora_pico = max(sales_by_hour, key=lambda h: sales_by_hour[h])
        ventas_pico = sales_by_hour[hora_pico].quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Hora valle: mínimo excluyendo horas con 0 (todas tienen >0 por construcción)
        hora_valle = min(sales_by_hour, key=lambda h: sales_by_hour[h])
        ventas_valle = sales_by_hour[hora_valle].quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        import json
        value_dict = {
            "hora_pico": hora_pico,
            "ventas_pico": str(ventas_pico),
            "hora_valle": hora_valle,
            "ventas_valle": str(ventas_valle),
        }
        value_json = json.dumps(value_dict)

        return CalcResult(
            metric="patron_horario_ventas",
            value=ventas_pico,  # value principal: ventas de hora pico
            unit="resumen",
            status="ok",
            context=(
                f"Patrón horario del {date}: "
                f"Hora pico={hora_pico}:00 ({ventas_pico} MXN), "
                f"Hora valle={hora_valle}:00 ({ventas_valle} MXN). "
                f"Horas con actividad: {len(sales_by_hour)}. "
                f"Detalle: {value_json}"
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="patron_horario_ventas",
            value=None,
            unit="resumen",
            status="incomplete_data",
            context=(
                f"Error al calcular patrón horario para {business_id}: {exc}"
            ),
        )


def calc_sales_by_staff(
    business_id: str,
    date: str,
    db: Any,
) -> CalcResult:
    """
    Calcula ventas y conteo de tickets por cajero/mesero.

    Fórmula:
        Para cada cajero_id/mesero_id:
          sales_staff = Σ(total_net)
          ticket_count_staff = COUNT(tickets)

    Fuentes de datos:
        - transactions: type="ingreso", category="venta"
        - transactions.raw_metadata: campos cajero_id, mesero_id de S1B

    Unidad: "MXN"
    value: dict {staff_id: {total, tickets}}
    Status: siempre "ok" (sin umbrales — dato sensible de personal).
    Edge: sin cajero_id ni mesero_id → status: "incomplete_data".

    ⚠️ Dato sensible: exposición en reportes con umbral, no ranking rutinario.
    """
    try:
        # --- 1. Obtener tickets con raw_metadata ---
        resp = (
            db.table("transactions")
            .select("amount, raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .eq("transaction_date", date)
            .execute()
        )
        rows = resp.data or []

        if not rows:
            return CalcResult(
                metric="ventas_por_staff",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=f"Sin tickets de venta para {business_id} el {date}.",
            )

        # --- 2. Agrupar por staff ---
        by_staff: dict[str, dict[str, Any]] = {}
        tickets_sin_staff = 0

        for row in rows:
            amount = Decimal(str(row["amount"]))
            metadata = row.get("raw_metadata") or {}

            staff_id = metadata.get("cajero_id") or metadata.get("mesero_id")
            if not staff_id:
                tickets_sin_staff += 1
                continue

            if staff_id not in by_staff:
                by_staff[staff_id] = {"total": Decimal("0"), "tickets": 0}

            by_staff[staff_id]["total"] += amount
            by_staff[staff_id]["tickets"] += 1

        # Edge: ningún ticket tiene staff identificado
        if not by_staff:
            return CalcResult(
                metric="ventas_por_staff",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=(
                    f"Ningún ticket tiene cajero_id/mesero_id en raw_metadata "
                    f"para {business_id} el {date}. Posible ingesta legacy PDF."
                ),
            )

        # --- 3. Serializar resultado ---
        import json
        staff_detail: dict[str, dict[str, str]] = {}
        total_all_staff = Decimal("0")

        for staff_id, data in by_staff.items():
            staff_total = data["total"].quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            staff_detail[staff_id] = {
                "total": str(staff_total),
                "tickets": str(data["tickets"]),
            }
            total_all_staff += data["total"]

        staff_json = json.dumps(staff_detail)

        return CalcResult(
            metric="ventas_por_staff",
            value=total_all_staff.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            unit="MXN",
            status="ok",
            context=(
                f"Ventas por staff el {date}: {staff_json}. "
                f"Total staff identificados: {len(by_staff)}. "
                f"Tickets sin staff: {tickets_sin_staff}."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="ventas_por_staff",
            value=None,
            unit="MXN",
            status="incomplete_data",
            context=f"Error al calcular ventas por staff para {business_id}: {exc}",
        )


def calc_sales_by_branch(
    business_id: str,
    date: str,
    db: Any,
) -> CalcResult:
    """
    Calcula ventas y conteo de tickets por sucursal.

    Fórmula:
        Para cada sucursal_id:
          sales_branch = Σ(total_net)
          ticket_count_branch = COUNT(tickets)

    Fuentes de datos:
        - transactions: type="ingreso", category="venta"
        - transactions.raw_metadata: campo sucursal_id de S1B

    Prerequisito:
        Solo se ejecuta si businesses.multi_sucursal = true.
        Si es una sola sucursal, S2 Gatekeeper no activa esta función.

    Unidad: "MXN"
    value: dict {sucursal_id: {total, tickets}}
    Status: siempre "ok" (sin umbrales).
    Edge: sin datos → status: "incomplete_data".
    """
    try:
        # --- 1. Obtener tickets con raw_metadata ---
        resp = (
            db.table("transactions")
            .select("amount, raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .eq("transaction_date", date)
            .execute()
        )
        rows = resp.data or []

        if not rows:
            return CalcResult(
                metric="ventas_por_sucursal",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=f"Sin tickets de venta para {business_id} el {date}.",
            )

        # --- 2. Agrupar por sucursal ---
        by_branch: dict[str, dict[str, Any]] = {}
        tickets_sin_sucursal = 0

        for row in rows:
            amount = Decimal(str(row["amount"]))
            metadata = row.get("raw_metadata") or {}

            sucursal_id = metadata.get("sucursal_id")
            if not sucursal_id:
                tickets_sin_sucursal += 1
                continue

            if sucursal_id not in by_branch:
                by_branch[sucursal_id] = {"total": Decimal("0"), "tickets": 0}

            by_branch[sucursal_id]["total"] += amount
            by_branch[sucursal_id]["tickets"] += 1

        # Edge: ningún ticket tiene sucursal
        if not by_branch:
            return CalcResult(
                metric="ventas_por_sucursal",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=(
                    f"Ningún ticket tiene sucursal_id en raw_metadata "
                    f"para {business_id} el {date}."
                ),
            )

        # --- 3. Serializar resultado ---
        import json
        branch_detail: dict[str, dict[str, str]] = {}
        total_all_branches = Decimal("0")

        for branch_id, data in by_branch.items():
            branch_total = data["total"].quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            branch_detail[branch_id] = {
                "total": str(branch_total),
                "tickets": str(data["tickets"]),
            }
            total_all_branches += data["total"]

        branch_json = json.dumps(branch_detail)

        return CalcResult(
            metric="ventas_por_sucursal",
            value=total_all_branches.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ),
            unit="MXN",
            status="ok",
            context=(
                f"Ventas por sucursal el {date}: {branch_json}. "
                f"Sucursales con actividad: {len(by_branch)}. "
                f"Tickets sin sucursal_id: {tickets_sin_sucursal}."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="ventas_por_sucursal",
            value=None,
            unit="MXN",
            status="incomplete_data",
            context=(
                f"Error al calcular ventas por sucursal para {business_id}: {exc}"
            ),
        )


# ===========================================================================
# FUNCIONES DE CÁLCULO — NIVEL PRODUCTO (nuevas)
# Spec: s3_motor_calculo.md §Funciones — Nivel Producto
# ===========================================================================


def calc_top_bottom_sellers(
    business_id: str,
    start_date: str,
    end_date: str,
    db: Any,
    top_n: int = 5,
) -> CalcResult:
    """
    Calcula los productos más y menos vendidos por cantidad y por revenue.

    Fórmula:
        ranking_qty = ProductLine agrupado por product_name, ORDER BY Σ(quantity) DESC
        ranking_rev = ProductLine agrupado por product_name, ORDER BY Σ(unit_price × quantity) DESC
        top = ranking[:top_n]
        bottom = ranking[-top_n:]

    Fuentes de datos:
        - transactions: type="ingreso", category="venta"
        - transactions.raw_metadata.items (ProductLine[] persistidos por S1B)

    Unidad: "ranking"
    value: dict {top_by_qty, bottom_by_qty, top_by_revenue, bottom_by_revenue}
    Edge: sin datos de ProductLine → status: "incomplete_data".
    """
    try:
        import json

        # --- 1. Obtener tickets de venta con items en el rango ---
        resp = (
            db.table("transactions")
            .select("raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .gte("transaction_date", start_date)
            .lte("transaction_date", end_date)
            .execute()
        )
        rows = resp.data or []

        # --- 2. Extraer y agrupar ProductLines ---
        qty_by_product: dict[str, Decimal] = {}
        rev_by_product: dict[str, Decimal] = {}

        for row in rows:
            metadata = row.get("raw_metadata") or {}
            items = metadata.get("items") or []

            for item in items:
                product_name = item.get("product_name")
                if not product_name:
                    continue

                quantity = Decimal(str(item.get("quantity", 0) or 0))
                unit_price = Decimal(str(item.get("unit_price", 0) or 0))
                revenue = unit_price * quantity

                qty_by_product[product_name] = (
                    qty_by_product.get(product_name, Decimal("0")) + quantity
                )
                rev_by_product[product_name] = (
                    rev_by_product.get(product_name, Decimal("0")) + revenue
                )

        # Edge: sin datos de ProductLine
        if not qty_by_product:
            return CalcResult(
                metric="top_bottom_sellers",
                value=None,
                unit="ranking",
                status="incomplete_data",
                context=(
                    f"Sin datos de ProductLine para {business_id} "
                    f"entre {start_date} y {end_date}."
                ),
            )

        # --- 3. Crear rankings ---
        sorted_by_qty = sorted(
            qty_by_product.items(), key=lambda x: x[1], reverse=True
        )
        sorted_by_rev = sorted(
            rev_by_product.items(), key=lambda x: x[1], reverse=True
        )

        top_by_qty = [
            {"product_name": name, "quantity": str(qty.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))}
            for name, qty in sorted_by_qty[:top_n]
        ]
        bottom_by_qty = [
            {"product_name": name, "quantity": str(qty.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))}
            for name, qty in sorted_by_qty[-top_n:]
        ]
        top_by_revenue = [
            {"product_name": name, "revenue": str(rev.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))}
            for name, rev in sorted_by_rev[:top_n]
        ]
        bottom_by_revenue = [
            {"product_name": name, "revenue": str(rev.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))}
            for name, rev in sorted_by_rev[-top_n:]
        ]

        value_dict = {
            "top_by_qty": top_by_qty,
            "bottom_by_qty": bottom_by_qty,
            "top_by_revenue": top_by_revenue,
            "bottom_by_revenue": bottom_by_revenue,
        }
        value_json = json.dumps(value_dict)

        return CalcResult(
            metric="top_bottom_sellers",
            value=Decimal(str(len(qty_by_product))),
            unit="ranking",
            status="ok",
            context=(
                f"Ranking de productos ({start_date} a {end_date}), "
                f"top_n={top_n}, total productos: {len(qty_by_product)}. "
                f"Detalle: {value_json}"
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="top_bottom_sellers",
            value=None,
            unit="ranking",
            status="incomplete_data",
            context=f"Error al calcular top/bottom sellers para {business_id}: {exc}",
        )


def calc_revenue_concentration(
    business_id: str,
    start_date: str,
    end_date: str,
    db: Any,
) -> CalcResult:
    """
    Calcula el índice de concentración de ingresos (Pareto 80/20).

    Fórmula:
        Ordenar productos por revenue DESC.
        concentration_index = % de productos que acumulan 80% del revenue total.

    Fuentes de datos:
        - transactions: type="ingreso", category="venta"
        - transactions.raw_metadata.items (ProductLine[])

    Unidad: "%"
    value: porcentaje de SKUs que concentran 80% del ingreso.
    Status: valor bajo (<20%) = alta concentración (pocos productos dominan).
    Edge: <3 productos → status: "incomplete_data".
    """
    try:
        import json

        # --- 1. Obtener tickets de venta con items ---
        resp = (
            db.table("transactions")
            .select("raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .gte("transaction_date", start_date)
            .lte("transaction_date", end_date)
            .execute()
        )
        rows = resp.data or []

        # --- 2. Agrupar revenue por producto ---
        rev_by_product: dict[str, Decimal] = {}

        for row in rows:
            metadata = row.get("raw_metadata") or {}
            items = metadata.get("items") or []

            for item in items:
                product_name = item.get("product_name")
                if not product_name:
                    continue

                quantity = Decimal(str(item.get("quantity", 0) or 0))
                unit_price = Decimal(str(item.get("unit_price", 0) or 0))
                revenue = unit_price * quantity

                rev_by_product[product_name] = (
                    rev_by_product.get(product_name, Decimal("0")) + revenue
                )

        # Edge: menos de 3 productos
        if len(rev_by_product) < 3:
            return CalcResult(
                metric="concentracion_ingresos",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Solo {len(rev_by_product)} producto(s) con ventas para {business_id} "
                    f"entre {start_date} y {end_date}. "
                    "Se requieren al menos 3 para calcular concentración."
                ),
            )

        # --- 3. Calcular Pareto: % de SKUs que acumulan 80% del revenue ---
        total_revenue = sum(rev_by_product.values())

        if total_revenue == Decimal("0"):
            return CalcResult(
                metric="concentracion_ingresos",
                value=None,
                unit="%",
                status="incomplete_data",
                context="Revenue total es 0 — no es posible calcular concentración.",
            )

        sorted_products = sorted(
            rev_by_product.values(), reverse=True
        )

        threshold = total_revenue * Decimal("0.80")
        accumulated = Decimal("0")
        products_needed = 0

        for rev in sorted_products:
            accumulated += rev
            products_needed += 1
            if accumulated >= threshold:
                break

        total_products = len(rev_by_product)
        concentration_index = (
            Decimal(str(products_needed)) / Decimal(str(total_products)) * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Status: valor bajo (<20%) = alta concentración
        if concentration_index < Decimal("20"):
            status: CalcStatus = "warning"
        else:
            status = "ok"

        return CalcResult(
            metric="concentracion_ingresos",
            value=concentration_index,
            unit="%",
            status=status,
            context=(
                f"Concentración de ingresos: {concentration_index}% de los SKUs "
                f"({products_needed} de {total_products}) acumulan 80% del revenue. "
                f"Revenue total: {total_revenue:.2f} MXN. "
                f"Periodo: {start_date} a {end_date}."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="concentracion_ingresos",
            value=None,
            unit="%",
            status="incomplete_data",
            context=f"Error al calcular concentración de ingresos para {business_id}: {exc}",
        )


def check_price_consistency(
    business_id: str,
    date: str,
    db: Any,
) -> CalcResult:
    """
    Verifica consistencia de precios comparando precio real vs esperado (receta).

    Fórmula:
        Para cada item vendido en `date`:
          expected_price = recipes.sale_price WHERE product_name matches
          actual_price = ProductLine.unit_price
          IF abs(actual - expected) / expected > 0.05 → flag inconsistencia

    Fuentes de datos:
        - transactions: type="ingreso", category="venta"
        - transactions.raw_metadata.items (ProductLine[])
        - recipes: sale_price por product_name

    Unidad: "items"
    value: count de items con precio inconsistente.
    Status: >0 inconsistencias → "warning" (fijo).
    Edge: producto sin receta → skip. Sin items → status: "incomplete_data".
    """
    try:
        import json

        # --- 1. Obtener recetas con sale_price para el negocio ---
        recetas_resp = (
            db.table("recipes")
            .select("product_name, sale_price")
            .eq("business_id", business_id)
            .execute()
        )
        recetas = recetas_resp.data or []

        # Mapa product_name → expected_price
        price_map: dict[str, Decimal] = {}
        for receta in recetas:
            name = receta.get("product_name")
            sale_price = receta.get("sale_price")
            if name and sale_price is not None:
                price_map[name] = Decimal(str(sale_price))

        # --- 2. Obtener tickets de venta del día con items ---
        resp = (
            db.table("transactions")
            .select("raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .eq("transaction_date", date)
            .execute()
        )
        rows = resp.data or []

        # --- 3. Verificar precios de cada item ---
        inconsistencies: list[dict[str, str]] = []
        total_items_checked = 0

        for row in rows:
            metadata = row.get("raw_metadata") or {}
            items = metadata.get("items") or []

            for item in items:
                product_name = item.get("product_name")
                if not product_name:
                    continue

                # Si no hay receta para este producto → skip
                expected_price = price_map.get(product_name)
                if expected_price is None:
                    continue

                actual_price = Decimal(str(item.get("unit_price", 0) or 0))
                total_items_checked += 1

                # Umbral: diferencia > 5%
                if expected_price == Decimal("0"):
                    continue

                diff = abs(actual_price - expected_price)
                diff_pct = diff / expected_price

                if diff_pct > Decimal("0.05"):
                    inconsistencies.append({
                        "product_name": product_name,
                        "expected": str(expected_price),
                        "actual": str(actual_price),
                        "diff_pct": str(
                            (diff_pct * Decimal("100")).quantize(
                                Decimal("0.01"), rounding=ROUND_HALF_UP
                            )
                        ),
                    })

        # Edge: sin items verificados
        if total_items_checked == 0:
            return CalcResult(
                metric="consistencia_precios",
                value=None,
                unit="items",
                status="incomplete_data",
                context=(
                    f"Sin items verificables para {business_id} el {date}. "
                    "No hay items con receta correspondiente."
                ),
            )

        # --- 4. Resultado ---
        inconsistency_count = Decimal(str(len(inconsistencies)))
        status: CalcStatus = "warning" if len(inconsistencies) > 0 else "ok"

        inconsistencies_json = json.dumps(inconsistencies[:20])  # Limitar a 20 para context

        return CalcResult(
            metric="consistencia_precios",
            value=inconsistency_count,
            unit="items",
            status=status,
            context=(
                f"Verificación de precios el {date}: "
                f"{len(inconsistencies)} inconsistencia(s) de {total_items_checked} items verificados. "
                f"Umbral: >5% de diferencia vs receta. "
                f"Detalle: {inconsistencies_json}"
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="consistencia_precios",
            value=None,
            unit="items",
            status="incomplete_data",
            context=f"Error al verificar consistencia de precios para {business_id}: {exc}",
        )


def calc_category_mix(
    business_id: str,
    start_date: str,
    end_date: str,
    db: Any,
) -> CalcResult:
    """
    Calcula la distribución porcentual de ventas por categoría (group/subgroup).

    Fórmula:
        Para cada group (y opcionalmente subgroup):
          pct = Σ(unit_price × quantity WHERE group = X) / Σ(total revenue) × 100

    Fuentes de datos:
        - transactions: type="ingreso", category="venta"
        - transactions.raw_metadata.items (ProductLine[] con group y subgroup)

    Unidad: "%"
    value: dict {group: pct, ...}. Context incluye desglose por subgroup.
    Edge: sin datos de ProductLine → status: "incomplete_data". Items sin group → skip.
    """
    try:
        import json

        # --- 1. Obtener tickets de venta con items ---
        resp = (
            db.table("transactions")
            .select("raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .gte("transaction_date", start_date)
            .lte("transaction_date", end_date)
            .execute()
        )
        rows = resp.data or []

        # --- 2. Agrupar revenue por group y subgroup ---
        rev_by_group: dict[str, Decimal] = {}
        rev_by_subgroup: dict[str, dict[str, Decimal]] = {}
        total_revenue = Decimal("0")
        items_sin_group = 0

        for row in rows:
            metadata = row.get("raw_metadata") or {}
            items = metadata.get("items") or []

            for item in items:
                group = item.get("group")
                if not group:
                    items_sin_group += 1
                    continue

                quantity = Decimal(str(item.get("quantity", 0) or 0))
                unit_price = Decimal(str(item.get("unit_price", 0) or 0))
                revenue = unit_price * quantity

                total_revenue += revenue
                rev_by_group[group] = (
                    rev_by_group.get(group, Decimal("0")) + revenue
                )

                # Subgroup breakdown
                subgroup = item.get("subgroup")
                if subgroup:
                    if group not in rev_by_subgroup:
                        rev_by_subgroup[group] = {}
                    rev_by_subgroup[group][subgroup] = (
                        rev_by_subgroup[group].get(subgroup, Decimal("0")) + revenue
                    )

        # Edge: sin datos de ProductLine con group
        if not rev_by_group:
            return CalcResult(
                metric="category_mix",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Sin datos de ProductLine con group para {business_id} "
                    f"entre {start_date} y {end_date}."
                ),
            )

        # --- 3. Calcular porcentajes por group ---
        if total_revenue == Decimal("0"):
            return CalcResult(
                metric="category_mix",
                value=None,
                unit="%",
                status="incomplete_data",
                context="Revenue total es 0 — no es posible calcular category mix.",
            )

        group_mix: dict[str, str] = {}
        for group, rev in rev_by_group.items():
            pct = (rev / total_revenue * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            group_mix[group] = str(pct)

        # --- 4. Calcular porcentajes por subgroup ---
        subgroup_mix: dict[str, dict[str, str]] = {}
        for group, subgroups in rev_by_subgroup.items():
            subgroup_mix[group] = {}
            for subgroup, rev in subgroups.items():
                pct = (rev / total_revenue * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                subgroup_mix[group][subgroup] = str(pct)

        group_json = json.dumps(group_mix)
        subgroup_json = json.dumps(subgroup_mix)

        return CalcResult(
            metric="category_mix",
            value=total_revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            unit="%",
            status="ok",
            context=(
                f"Distribución por categoría ({start_date} a {end_date}): {group_json}. "
                f"Desglose subgroup: {subgroup_json}. "
                f"Revenue total: {total_revenue:.2f} MXN. "
                f"Items sin group: {items_sin_group}."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="category_mix",
            value=None,
            unit="%",
            status="incomplete_data",
            context=f"Error al calcular category mix para {business_id}: {exc}",
        )


def calc_modifier_attach_rate(
    business_id: str,
    start_date: str,
    end_date: str,
    db: Any,
) -> CalcResult:
    """
    Calcula la tasa de attach de modificadores (upsell rate).

    Fórmula:
        lines_with_modifier = COUNT(ProductLine WHERE variant_modifier IS NOT NULL AND != "")
        total_lines = COUNT(ProductLine)
        attach_rate = lines_with_modifier / total_lines × 100

    Fuentes de datos:
        - transactions: type="ingreso", category="venta"
        - transactions.raw_metadata.items (campo variant_modifier de S1B)

    Unidad: "%"
    Tasa de upsell: qué % de líneas de venta llevan un modificador/extra.
    Edge: 0 líneas → status: "incomplete_data". Ningún modifier → value: 0, status: "ok".
    """
    try:
        # --- 1. Obtener tickets de venta con items ---
        resp = (
            db.table("transactions")
            .select("raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .gte("transaction_date", start_date)
            .lte("transaction_date", end_date)
            .execute()
        )
        rows = resp.data or []

        # --- 2. Contar líneas con y sin modificador ---
        total_lines = 0
        lines_with_modifier = 0

        for row in rows:
            metadata = row.get("raw_metadata") or {}
            items = metadata.get("items") or []

            for item in items:
                total_lines += 1
                variant_modifier = item.get("variant_modifier")
                if variant_modifier is not None and variant_modifier != "":
                    lines_with_modifier += 1

        # Edge: 0 líneas
        if total_lines == 0:
            return CalcResult(
                metric="modifier_attach_rate",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Sin líneas de producto para {business_id} "
                    f"entre {start_date} y {end_date}."
                ),
            )

        # --- 3. Calcular attach rate ---
        attach_rate = (
            Decimal(str(lines_with_modifier)) / Decimal(str(total_lines)) * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return CalcResult(
            metric="modifier_attach_rate",
            value=attach_rate,
            unit="%",
            status="ok",
            context=(
                f"Tasa de modificadores: {attach_rate}% "
                f"({lines_with_modifier} de {total_lines} líneas con modificador). "
                f"Periodo: {start_date} a {end_date}."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="modifier_attach_rate",
            value=None,
            unit="%",
            status="incomplete_data",
            context=f"Error al calcular modifier attach rate para {business_id}: {exc}",
        )


def calc_item_discount_split(
    business_id: str,
    date: str,
    db: Any,
) -> CalcResult:
    """
    Calcula el split entre descuentos a nivel item vs a nivel ticket.

    Fórmula:
        item_level_discount = Σ(ProductLine.item_discount) por ticket
        ticket_level_discount = TicketEvent.discounts - item_level_discount
        split = {
          "item_discount_total": item_level_discount,
          "ticket_discount_total": ticket_level_discount,
          "item_discount_pct": item / (item + ticket) × 100,
          "ticket_discount_pct": ticket / (item + ticket) × 100
        }

    Fuentes de datos:
        - transactions: type="ingreso", category="venta"
        - transactions.raw_metadata: campos discounts (ticket) + items[].item_discount

    Unidad: "MXN"
    value: dict con el split.
    Edge: no discounts → ambos 0, status "ok". No items → status: "incomplete_data".
    """
    try:
        import json

        # --- 1. Obtener tickets de venta del día ---
        resp = (
            db.table("transactions")
            .select("raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .eq("transaction_date", date)
            .execute()
        )
        rows = resp.data or []

        # --- 2. Acumular descuentos por nivel ---
        total_item_discount = Decimal("0")
        total_ticket_discount_raw = Decimal("0")
        has_items = False

        for row in rows:
            metadata = row.get("raw_metadata") or {}
            items = metadata.get("items") or []

            # Descuento total del ticket (campo discounts en raw_metadata)
            ticket_discounts = Decimal(str(metadata.get("discounts", 0) or 0))
            total_ticket_discount_raw += ticket_discounts

            # Descuento a nivel item
            ticket_item_discount = Decimal("0")
            for item in items:
                has_items = True
                item_discount = Decimal(str(item.get("item_discount", 0) or 0))
                ticket_item_discount += item_discount

            total_item_discount += ticket_item_discount

        # Edge: sin items
        if not has_items:
            return CalcResult(
                metric="item_discount_split",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=(
                    f"Sin items de producto para {business_id} el {date}. "
                    "No es posible calcular split de descuentos."
                ),
            )

        # ticket_level_discount = total discounts del ticket - item_level_discount
        total_ticket_discount = total_ticket_discount_raw - total_item_discount

        # Asegurar que no sea negativo (si item_discount > ticket discounts)
        if total_ticket_discount < Decimal("0"):
            total_ticket_discount = Decimal("0")

        # --- 3. Calcular porcentajes ---
        total_discounts = total_item_discount + total_ticket_discount

        if total_discounts == Decimal("0"):
            # No hay descuentos → ambos 0
            split = {
                "item_discount_total": "0.00",
                "ticket_discount_total": "0.00",
                "item_discount_pct": "0.00",
                "ticket_discount_pct": "0.00",
            }
        else:
            item_pct = (
                total_item_discount / total_discounts * Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            ticket_pct = (
                total_ticket_discount / total_discounts * Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            split = {
                "item_discount_total": str(
                    total_item_discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                ),
                "ticket_discount_total": str(
                    total_ticket_discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                ),
                "item_discount_pct": str(item_pct),
                "ticket_discount_pct": str(ticket_pct),
            }

        split_json = json.dumps(split)

        return CalcResult(
            metric="item_discount_split",
            value=total_discounts.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            unit="MXN",
            status="ok",
            context=(
                f"Split de descuentos el {date}: {split_json}. "
                f"Total descuentos: {total_discounts:.2f} MXN."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="item_discount_split",
            value=None,
            unit="MXN",
            status="incomplete_data",
            context=f"Error al calcular item discount split para {business_id}: {exc}",
        )


# ===========================================================================
# FUNCIONES DE CÁLCULO — NIVEL FORMA DE PAGO (nuevas)
# Spec: s3_motor_calculo.md §Funciones — Nivel Forma de Pago
# ===========================================================================


def calc_payment_mix(
    business_id: str,
    date: str,
    db: Any,
) -> CalcResult:
    """
    Calcula la distribución porcentual de ventas por forma de pago (PaymentBreakdown).

    Fórmula:
        Para cada forma de pago ∈ PaymentBreakdown:
          pct = Σ(monto_forma) / Σ(total_net de todos los tickets) × 100

    Fuentes de datos:
        - pos_inputs: cash_sales, card_sales del día
        - transactions.raw_metadata: PaymentBreakdown detallado de S1B

    Unidad: "%"
    value: total_net (Decimal). Context incluye dict {forma_pago: pct}.
    Nota: Usa total_net como denominador (NO subtotal) — no aplica la regla "subtotal base".
    Edge: sin datos de pago → status: "incomplete_data".
    """
    try:
        import json

        # --- 1. Obtener tickets con raw_metadata del día ---
        resp = (
            db.table("transactions")
            .select("amount, raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .eq("transaction_date", date)
            .execute()
        )
        rows = resp.data or []

        if not rows:
            return CalcResult(
                metric="payment_mix",
                value=None,
                unit="%",
                status="incomplete_data",
                context=f"Sin tickets de venta para {business_id} el {date}.",
            )

        # --- 2. Acumular montos por forma de pago ---
        payment_totals: dict[str, Decimal] = {}
        total_net = Decimal("0")
        tickets_sin_payment = 0

        for row in rows:
            amount = Decimal(str(row["amount"]))
            total_net += amount

            metadata = row.get("raw_metadata") or {}
            payment_breakdown = metadata.get("PaymentBreakdown") or {}

            if not payment_breakdown:
                tickets_sin_payment += 1
                continue

            for method, method_amount in payment_breakdown.items():
                val = Decimal(str(method_amount or 0))
                payment_totals[method] = (
                    payment_totals.get(method, Decimal("0")) + val
                )

        # Edge: ningún ticket tiene PaymentBreakdown
        if not payment_totals:
            return CalcResult(
                metric="payment_mix",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Ningún ticket tiene PaymentBreakdown en raw_metadata para "
                    f"{business_id} el {date}. Sin datos de forma de pago."
                ),
            )

        # --- 3. Calcular porcentajes ---
        mix: dict[str, str] = {}
        for method, method_total in payment_totals.items():
            if total_net > Decimal("0"):
                pct = (method_total / total_net * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            else:
                pct = Decimal("0")
            mix[method] = str(pct)

        mix_json = json.dumps(mix)

        return CalcResult(
            metric="payment_mix",
            value=total_net.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            unit="%",
            status="ok",
            context=(
                f"Distribución por forma de pago el {date}: {mix_json}. "
                f"Total ventas (total_net): {total_net:.2f} MXN. "
                f"Tickets sin PaymentBreakdown: {tickets_sin_payment}."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="payment_mix",
            value=None,
            unit="%",
            status="incomplete_data",
            context=f"Error al calcular payment mix para {business_id}: {exc}",
        )


def calc_delivery_commission_cost(
    business_id: str,
    date: str,
    db: Any,
) -> CalcResult:
    """
    Calcula el costo total de comisiones por plataformas de delivery.

    Fórmula:
        Para cada plataforma ∈ {UberEats, Rappi, DiDiFood}:
          ventas_plataforma = Σ(PaymentBreakdown.{plataforma})
          tasa = delivery_platform_config WHERE business_id AND platform AND effective_date <= date
                 ORDER BY effective_date DESC LIMIT 1
          comision = ventas_plataforma × tasa.commission_rate

        total_commission = Σ(comisiones de todas las plataformas)

    Fuentes de datos:
        - transactions.raw_metadata: PaymentBreakdown (uber_eats, rappi, didi_food)
        - delivery_platform_config: commission_rate por plataforma

    Unidad: "MXN"
    value: total_commission. Context incluye desglose por plataforma.
    DEPENDENCIA: Lee delivery_platform_config — NUNCA asume tasa fija en código.
    Edge: plataforma sin configuración → status: "incomplete_data" para esa plataforma.
    Edge: sin ventas delivery → value: 0, status: "ok".
    """
    try:
        import json

        # Mapeo: campo en PaymentBreakdown → nombre en delivery_platform_config.platform
        PLATFORM_MAP = {
            "uber_eats": "UberEats",
            "rappi": "Rappi",
            "didi_food": "DiDiFood",
        }

        # --- 1. Obtener tickets con raw_metadata del día ---
        resp = (
            db.table("transactions")
            .select("raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .eq("transaction_date", date)
            .execute()
        )
        rows = resp.data or []

        # --- 2. Acumular ventas por plataforma desde PaymentBreakdown ---
        platform_sales: dict[str, Decimal] = {field: Decimal("0") for field in PLATFORM_MAP}

        for row in rows:
            metadata = row.get("raw_metadata") or {}
            payment_breakdown = metadata.get("PaymentBreakdown") or {}

            for field in PLATFORM_MAP:
                val = Decimal(str(payment_breakdown.get(field, 0) or 0))
                platform_sales[field] += val

        # Verificar si hay ventas delivery
        total_delivery_sales = sum(platform_sales.values())
        if total_delivery_sales == Decimal("0"):
            return CalcResult(
                metric="delivery_commission_cost",
                value=Decimal("0"),
                unit="MXN",
                status="ok",
                context=(
                    f"Sin ventas delivery para {business_id} el {date}. "
                    "Comisión total: 0 MXN."
                ),
            )

        # --- 3. Obtener tasas de comisión desde delivery_platform_config ---
        total_commission = Decimal("0")
        breakdown: dict[str, dict[str, str]] = {}
        missing_configs: list[str] = []

        for field, platform_name in PLATFORM_MAP.items():
            sales = platform_sales[field]
            if sales == Decimal("0"):
                continue

            # Buscar tasa vigente para la plataforma
            config_resp = (
                db.table("delivery_platform_config")
                .select("commission_rate")
                .eq("business_id", business_id)
                .eq("platform", platform_name)
                .lte("effective_date", date)
                .order("effective_date", desc=True)
                .limit(1)
                .execute()
            )
            config_rows = config_resp.data or []

            if not config_rows:
                missing_configs.append(platform_name)
                continue

            commission_rate = Decimal(str(config_rows[0]["commission_rate"]))
            commission = (sales * commission_rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            total_commission += commission

            breakdown[platform_name] = {
                "ventas": str(sales.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "tasa": str(commission_rate),
                "comision": str(commission),
            }

        # Edge: alguna plataforma con ventas no tiene config
        if missing_configs:
            breakdown_json = json.dumps(breakdown) if breakdown else "{}"
            return CalcResult(
                metric="delivery_commission_cost",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=(
                    f"Sin configuración de comisión para: {', '.join(missing_configs)}. "
                    f"No se puede calcular comisión total. "
                    f"Plataformas calculadas: {breakdown_json}."
                ),
            )

        # --- 4. Resultado exitoso ---
        breakdown_json = json.dumps(breakdown)

        return CalcResult(
            metric="delivery_commission_cost",
            value=total_commission.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            unit="MXN",
            status="ok",
            context=(
                f"Comisión delivery total: {total_commission:.2f} MXN el {date}. "
                f"Desglose por plataforma: {breakdown_json}."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="delivery_commission_cost",
            value=None,
            unit="MXN",
            status="incomplete_data",
            context=f"Error al calcular comisiones delivery para {business_id}: {exc}",
        )


def calc_commission_cost_ratio(
    business_id: str,
    date: str,
    db: Any,
) -> CalcResult:
    """
    Ratio de comisión de delivery sobre las ventas totales del día.

    Formula:
        ratio = total_commission / Σ(subtotal de TODAS las ordenes del dia, todos los canales) × 100

    Umbral: >8% (base subtotal, todos los canales) -> warning. Sin nivel critico
    definido todavia -- dejar solo "warning"/"ok" por ahora.

    NOTA: esta funcion necesita el subtotal del dia COMPLETO (Comedor + Para llevar +
    Delivery), no solo las ordenes de delivery.
    """
    try:
        import json

        # Mapeo: campo en PaymentBreakdown → nombre en delivery_platform_config.platform
        PLATFORM_MAP = {
            "uber_eats": "UberEats",
            "rappi": "Rappi",
            "didi_food": "DiDiFood",
        }

        # --- 1. Obtener TODOS los tickets del día (todos los canales) ---
        resp = (
            db.table("transactions")
            .select("amount, raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .eq("transaction_date", date)
            .execute()
        )
        rows = resp.data or []

        if not rows:
            return CalcResult(
                metric="commission_cost_ratio",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Sin tickets de venta para {business_id} el {date}."
                ),
            )

        # --- 2. Acumular subtotal TOTAL del día y ventas por plataforma ---
        total_subtotal = Decimal("0")
        platform_sales: dict[str, Decimal] = {field: Decimal("0") for field in PLATFORM_MAP}

        for row in rows:
            metadata = row.get("raw_metadata") or {}
            subtotal = Decimal(str(metadata.get("subtotal", 0) or 0))
            total_subtotal += subtotal

            # Acumular ventas por plataforma desde PaymentBreakdown
            payment_breakdown = metadata.get("PaymentBreakdown") or {}
            for field in PLATFORM_MAP:
                val = Decimal(str(payment_breakdown.get(field, 0) or 0))
                platform_sales[field] += val

        # Edge: subtotal total es 0
        if total_subtotal == Decimal("0"):
            return CalcResult(
                metric="commission_cost_ratio",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Subtotal acumulado es 0 para {business_id} el {date}. "
                    "No es posible calcular ratio de comisión."
                ),
            )

        # --- 3. Calcular comisión total desde delivery_platform_config ---
        total_commission = Decimal("0")
        breakdown: dict[str, dict[str, str]] = {}
        missing_configs: list[str] = []

        for field, platform_name in PLATFORM_MAP.items():
            sales = platform_sales[field]
            if sales == Decimal("0"):
                continue

            # Buscar tasa vigente para la plataforma
            config_resp = (
                db.table("delivery_platform_config")
                .select("commission_rate")
                .eq("business_id", business_id)
                .eq("platform", platform_name)
                .lte("effective_date", date)
                .order("effective_date", desc=True)
                .limit(1)
                .execute()
            )
            config_rows = config_resp.data or []

            if not config_rows:
                missing_configs.append(platform_name)
                continue

            commission_rate = Decimal(str(config_rows[0]["commission_rate"]))
            commission = (sales * commission_rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            total_commission += commission

            breakdown[platform_name] = {
                "ventas": str(sales.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "tasa": str(commission_rate),
                "comision": str(commission),
            }

        # Edge: alguna plataforma con ventas no tiene config
        if missing_configs:
            breakdown_json = json.dumps(breakdown) if breakdown else "{}"
            return CalcResult(
                metric="commission_cost_ratio",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Sin configuración de comisión para: {', '.join(missing_configs)}. "
                    f"No se puede calcular ratio. "
                    f"Plataformas calculadas: {breakdown_json}."
                ),
            )

        # --- 4. Calcular ratio ---
        ratio = (
            total_commission / total_subtotal * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # --- 5. Determinar status por umbral ---
        status = "warning" if ratio > Decimal("8") else "ok"

        breakdown_json = json.dumps(breakdown)

        return CalcResult(
            metric="commission_cost_ratio",
            value=ratio,
            unit="%",
            status=status,
            context=(
                f"Ratio comisión delivery: {ratio}% "
                f"(comisión total: {total_commission:.2f} MXN / "
                f"subtotal día completo: {total_subtotal:.2f} MXN). "
                f"Umbral: 8%. "
                f"Desglose: {breakdown_json}."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="commission_cost_ratio",
            value=None,
            unit="%",
            status="incomplete_data",
            context=f"Error al calcular ratio de comisión para {business_id}: {exc}",
        )


def calc_staff_courtesy_ratio(
    business_id: str,
    date: str,
    db: Any,
) -> CalcResult:
    """
    Calcula el ratio de cortesías de staff como porcentaje del subtotal.

    Fórmula:
        courtesy_ratio = Σ(PaymentBreakdown.cortesia_staff) / Σ(subtotal) × 100

    Desagregación por responsable (Tipo B):
        by_responsable = GROUP BY cajero_id/mesero_id:
          {staff_id: {courtesy_total: Decimal, pct_of_all_courtesy: float}}

    Principio de diseño:
        - DENOMINADOR: subtotal, NUNCA total_net.
        - TIPO B: Incluye by_responsable en context — una persona dando cortesías
          desproporcionadas se diluye en el agregado si no se desagrega.

    Fuentes de datos:
        - transactions.raw_metadata: PaymentBreakdown.cortesia_staff, subtotal,
          cajero_id, mesero_id

    Unidad: "%"
    Edge: Σsubtotal = 0 → status: "incomplete_data".
    Edge: cortesia_staff = 0 → value: 0, status: "ok".
    """
    try:
        import json

        # --- 1. Obtener tickets con raw_metadata del día ---
        resp = (
            db.table("transactions")
            .select("amount, raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .eq("transaction_date", date)
            .execute()
        )
        rows = resp.data or []

        if not rows:
            return CalcResult(
                metric="staff_courtesy_ratio",
                value=None,
                unit="%",
                status="incomplete_data",
                context=f"Sin tickets de venta para {business_id} el {date}.",
            )

        # --- 2. Acumular cortesías y subtotales ---
        total_courtesy = Decimal("0")
        total_subtotal = Decimal("0")
        by_responsable: dict[str, Decimal] = {}
        # Track subtotal per responsable (for personal rate calculation)
        by_responsable_subtotal: dict[str, Decimal] = {}

        for row in rows:
            metadata = row.get("raw_metadata") or {}
            payment_breakdown = metadata.get("PaymentBreakdown") or {}

            courtesy = Decimal(str(payment_breakdown.get("cortesia_staff", 0) or 0))
            subtotal = Decimal(str(metadata.get("subtotal", 0) or 0))

            total_courtesy += courtesy
            total_subtotal += subtotal

            # Identificar responsable (cajero_id o mesero_id)
            staff_id = metadata.get("cajero_id") or metadata.get("mesero_id")
            if staff_id:
                # Track ALL subtotals per responsable (not just courtesy orders)
                by_responsable_subtotal[staff_id] = (
                    by_responsable_subtotal.get(staff_id, Decimal("0")) + subtotal
                )
                if courtesy > Decimal("0"):
                    by_responsable[staff_id] = (
                        by_responsable.get(staff_id, Decimal("0")) + courtesy
                    )

        # Edge: subtotal total es 0
        if total_subtotal == Decimal("0"):
            return CalcResult(
                metric="staff_courtesy_ratio",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Subtotal acumulado es 0 para {business_id} el {date}. "
                    "No es posible calcular ratio de cortesía."
                ),
            )

        # Edge: cortesía total es 0
        if total_courtesy == Decimal("0"):
            return CalcResult(
                metric="staff_courtesy_ratio",
                value=Decimal("0"),
                unit="%",
                status="ok",
                context=(
                    f"Sin cortesías de staff para {business_id} el {date}. "
                    f"Subtotal del día: {total_subtotal:.2f} MXN."
                ),
            )

        # --- 3. Calcular ratio global ---
        courtesy_ratio = (
            total_courtesy / total_subtotal * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Evaluar umbrales
        # Nota: 1%/2% salió de benchmarks mensuales aplicados por error a datos diarios,
        # que tienen mucho más ruido natural. 5% es el corte grounded para variación diaria
        # (ver mepia_v4_metricas_diseno.md sección 3 para las fuentes).
        status: CalcStatus = "ok"
        if courtesy_ratio > Decimal("5"):
            status = "critical"

        # --- 4. Desagregación por responsable (Tipo B) ---
        responsable_detail: dict[str, dict[str, str]] = {}
        for staff_id, staff_courtesy in by_responsable.items():
            pct_of_all = (
                staff_courtesy / total_courtesy * Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            staff_subtotal = by_responsable_subtotal.get(staff_id, Decimal("0"))
            staff_rate = (
                (staff_courtesy / staff_subtotal * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                if staff_subtotal > Decimal("0")
                else Decimal("0")
            )
            responsable_detail[staff_id] = {
                "courtesy_total": str(staff_courtesy.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )),
                "pct_of_all_courtesy": str(pct_of_all),
                "subtotal_propio": str(staff_subtotal.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )),
                "rate_pct": str(staff_rate),
            }

        by_responsable_json = json.dumps(responsable_detail)

        return CalcResult(
            metric="staff_courtesy_ratio",
            value=courtesy_ratio,
            unit="%",
            status=status,
            context=(
                f"Ratio de cortesía staff: {courtesy_ratio}% "
                f"(cortesías: {total_courtesy:.2f} MXN / subtotal: {total_subtotal:.2f} MXN). "
                f"Fecha: {date}. "
                f"by_responsable: {by_responsable_json}"
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="staff_courtesy_ratio",
            value=None,
            unit="%",
            status="incomplete_data",
            context=f"Error al calcular staff courtesy ratio para {business_id}: {exc}",
        )


def calc_loyalty_redemption_cost(
    business_id: str,
    date: str,
    db: Any,
) -> CalcResult:
    """
    Calcula el costo total de canjes de programa de lealtad (tarjetas_lealtad).

    Fórmula:
        loyalty_total = Σ(PaymentBreakdown.tarjetas_lealtad)
        loyalty_pct = loyalty_total / Σ(subtotal) × 100

    Fuentes de datos:
        - transactions.raw_metadata: campo tarjetas_lealtad de PaymentBreakdown, subtotal

    Unidad: "MXN"
    value: loyalty_total. Context incluye loyalty_pct.
    Nota: Representa el costo real de canje del programa de lealtad como forma de pago.
    Edge: sin ventas → status: "incomplete_data".
    Edge: tarjetas_lealtad = 0 → value: 0, status: "ok".
    """
    try:
        # --- 1. Obtener tickets con raw_metadata del día ---
        resp = (
            db.table("transactions")
            .select("amount, raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .eq("transaction_date", date)
            .execute()
        )
        rows = resp.data or []

        if not rows:
            return CalcResult(
                metric="loyalty_redemption_cost",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=f"Sin tickets de venta para {business_id} el {date}.",
            )

        # --- 2. Acumular loyalty y subtotales ---
        total_loyalty = Decimal("0")
        total_subtotal = Decimal("0")

        for row in rows:
            metadata = row.get("raw_metadata") or {}
            payment_breakdown = metadata.get("PaymentBreakdown") or {}

            loyalty = Decimal(str(payment_breakdown.get("tarjetas_lealtad", 0) or 0))
            subtotal = Decimal(str(metadata.get("subtotal", 0) or 0))

            total_loyalty += loyalty
            total_subtotal += subtotal

        # Edge: sin ventas (subtotal = 0 y no hay datos significativos)
        if total_subtotal == Decimal("0") and not rows:
            return CalcResult(
                metric="loyalty_redemption_cost",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=(
                    f"Sin datos de ventas para {business_id} el {date}. "
                    "No es posible calcular costo de lealtad."
                ),
            )

        # Edge: loyalty total es 0
        if total_loyalty == Decimal("0"):
            return CalcResult(
                metric="loyalty_redemption_cost",
                value=Decimal("0"),
                unit="MXN",
                status="ok",
                context=(
                    f"Sin canjes de lealtad para {business_id} el {date}. "
                    f"Subtotal del día: {total_subtotal:.2f} MXN."
                ),
            )

        # --- 3. Calcular porcentaje ---
        if total_subtotal > Decimal("0"):
            loyalty_pct = (
                total_loyalty / total_subtotal * Decimal("100")
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            loyalty_pct = Decimal("0")

        return CalcResult(
            metric="loyalty_redemption_cost",
            value=total_loyalty.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            unit="MXN",
            status="ok",
            context=(
                f"Costo de canjes de lealtad: {total_loyalty:.2f} MXN "
                f"({loyalty_pct}% del subtotal {total_subtotal:.2f} MXN). "
                f"Fecha: {date}."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="loyalty_redemption_cost",
            value=None,
            unit="MXN",
            status="incomplete_data",
            context=f"Error al calcular loyalty redemption cost para {business_id}: {exc}",
        )


# ===========================================================================
# FUNCIONES DE CÁLCULO — NIVEL OPERACIÓN / CAJA (shift_audit_events)
# Spec: s3_motor_calculo.md §Funciones — Nivel Operación
# ===========================================================================


def calc_cancellation_rate(business_id: str, date: str, db: Any) -> CalcResult:
    """
    Calcula la tasa de cancelaciones del día como porcentaje del total de tickets.

    Tipo B — incluye desagregación por responsable (MANDATORY).

    Fórmula:
        cancellation_rate = COUNT(cancellations) / total_tickets × 100
        pre_comanda_pct   = COUNT(timing="pre_comanda") / COUNT(cancellations) × 100
        post_comanda_pct  = COUNT(timing="post_comanda") / COUNT(cancellations) × 100

    Desagregación by_responsable:
        GROUP BY cancellations.responsable → {count, pct_of_total, pre, post}

    Fuentes de datos:
        - shift_audit_events.cancellations (JSONB array)
        - pos_inputs.num_transactions (total tickets del día)

    Umbrales:
        - critical : cancellation_rate > 5%
        - warning  : cancellation_rate > 2%
        - ok       : cancellation_rate <= 2%

    Edge:
        - 0 tickets → status: "incomplete_data"
        - 0 cancellations → value: 0, status: "ok"
    """
    try:
        import json

        # --- 1. Obtener shift_audit_events del día ---
        events_resp = (
            db.table("shift_audit_events")
            .select("cancellations")
            .eq("business_id", business_id)
            .eq("date", date)
            .execute()
        )
        events_rows = events_resp.data or []

        # --- 2. Consolidar todas las cancelaciones del día ---
        all_cancellations: list[dict] = []
        for row in events_rows:
            cancels = row.get("cancellations") or []
            if isinstance(cancels, list):
                all_cancellations.extend(cancels)

        # --- 3. Obtener total de tickets del día ---
        pos_resp = (
            db.table("pos_inputs")
            .select("num_transactions")
            .eq("business_id", business_id)
            .eq("date", date)
            .execute()
        )
        pos_rows = pos_resp.data or []

        total_tickets = 0
        for pr in pos_rows:
            val = pr.get("num_transactions")
            if val is not None:
                total_tickets += int(val)

        # --- 3b. Count tickets per responsable from transactions (for personal rate) ---
        tx_resp = (
            db.table("transactions")
            .select("raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .eq("transaction_date", date)
            .execute()
        )
        tx_rows = tx_resp.data or []
        tickets_per_resp: dict[str, int] = {}
        for tx in tx_rows:
            md = tx.get("raw_metadata") or {}
            cid = md.get("cajero_id") or ""
            if cid:
                tickets_per_resp[cid] = tickets_per_resp.get(cid, 0) + 1

        # Edge: sin tickets → incomplete_data
        if total_tickets == 0:
            return CalcResult(
                metric="cancellation_rate",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Sin tickets registrados para {business_id} el {date}. "
                    "No se puede calcular tasa de cancelación."
                ),
            )

        # Edge: 0 cancelaciones → value: 0, ok
        cancel_count = len(all_cancellations)
        if cancel_count == 0:
            return CalcResult(
                metric="cancellation_rate",
                value=Decimal("0"),
                unit="%",
                status="ok",
                context=(
                    f"0 cancelaciones sobre {total_tickets} tickets el {date}. "
                    "Tasa de cancelación: 0%."
                ),
            )

        # --- 4. Calcular tasa general ---
        cancellation_rate = (
            Decimal(str(cancel_count)) / Decimal(str(total_tickets)) * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # --- 5. Desglose pre/post comanda ---
        pre_count = sum(
            1 for c in all_cancellations if c.get("timing") == "pre_comanda"
        )
        post_count = sum(
            1 for c in all_cancellations if c.get("timing") == "post_comanda"
        )

        pre_pct = (
            Decimal(str(pre_count)) / Decimal(str(cancel_count)) * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        post_pct = (
            Decimal(str(post_count)) / Decimal(str(cancel_count)) * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # --- 6. Desagregación por responsable (Tipo B MANDATORY) ---
        by_responsable: dict[str, dict] = {}
        for c in all_cancellations:
            resp_name = c.get("responsable", "desconocido")
            if resp_name not in by_responsable:
                by_responsable[resp_name] = {"count": 0, "pct_of_total": Decimal("0"), "pre": 0, "post": 0}
            by_responsable[resp_name]["count"] += 1
            if c.get("timing") == "pre_comanda":
                by_responsable[resp_name]["pre"] += 1
            elif c.get("timing") == "post_comanda":
                by_responsable[resp_name]["post"] += 1

        # Calcular pct_of_total para cada responsable
        for resp_name, data in by_responsable.items():
            data["pct_of_total"] = float(
                (Decimal(str(data["count"])) / Decimal(str(cancel_count)) * Decimal("100"))
                .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            )
            # Add personal rate
            own_tickets = tickets_per_resp.get(resp_name, 0)
            if own_tickets > 0:
                data["rate_pct"] = float(
                    (Decimal(str(data["count"])) / Decimal(str(own_tickets)) * Decimal("100"))
                    .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                )
                data["own_tickets"] = own_tickets
            else:
                data["rate_pct"] = 0.0
                data["own_tickets"] = 0

        # --- 7. Evaluar umbrales ---
        if cancellation_rate > Decimal("5"):
            status: CalcStatus = "critical"
        elif cancellation_rate > Decimal("2"):
            status = "warning"
        else:
            status = "ok"

        # Construir context con desglose
        responsable_summary = "; ".join(
            f"{name}: {info['count']} ({info['pct_of_total']}%)"
            for name, info in by_responsable.items()
        )

        return CalcResult(
            metric="cancellation_rate",
            value=cancellation_rate,
            unit="%",
            status=status,
            context=(
                f"Tasa de cancelación: {cancellation_rate}% "
                f"({cancel_count}/{total_tickets} tickets). "
                f"Pre-comanda: {pre_count} ({pre_pct}%), Post-comanda: {post_count} ({post_pct}%). "
                f"Por responsable: {responsable_summary}. "
                f"by_responsable: {json.dumps(by_responsable)}"
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="cancellation_rate",
            value=None,
            unit="%",
            status="incomplete_data",
            context=f"Error al calcular cancellation_rate para {business_id}: {exc}",
        )


def calc_reprint_rate(business_id: str, date: str, db: Any) -> CalcResult:
    """
    Calcula la tasa de reimpresiones del día como porcentaje del total de tickets.

    Tipo B — incluye desagregación por responsable (MANDATORY).

    Fórmula:
        reprint_rate = COUNT(reprints) / total_tickets × 100

    Desagregación by_responsable:
        GROUP BY reprints.responsable → {count, pct_of_total}

    Fuentes de datos:
        - shift_audit_events.reprints (JSONB array de objetos {order_id, responsable, hora})
        - pos_inputs.num_transactions (total tickets del día)

    Umbrales:
        - critical : reprint_rate > 10%
        - warning  : reprint_rate > 5%
        - ok       : reprint_rate <= 5%

    Edge:
        - 0 tickets → status: "incomplete_data"
        - 0 reprints → value: 0, status: "ok"
    """
    try:
        import json

        # --- 1. Obtener shift_audit_events del día ---
        events_resp = (
            db.table("shift_audit_events")
            .select("reprints")
            .eq("business_id", business_id)
            .eq("date", date)
            .execute()
        )
        events_rows = events_resp.data or []

        # --- 2. Consolidar todos los registros de reimpresión del día ---
        all_reprints: list[dict] = []
        for row in events_rows:
            reprints_data = row.get("reprints") or []
            if isinstance(reprints_data, list):
                all_reprints.extend(reprints_data)
            elif isinstance(reprints_data, int):
                # Legacy: int means N reprints with no responsable detail
                # Treat as N unknown reprints (backwards compat)
                for _ in range(reprints_data):
                    all_reprints.append({"order_id": "unknown", "responsable": "desconocido", "hora": ""})

        # Count
        total_reprints = len(all_reprints)

        # --- 3. Obtener total de tickets del día ---
        pos_resp = (
            db.table("pos_inputs")
            .select("num_transactions")
            .eq("business_id", business_id)
            .eq("date", date)
            .execute()
        )
        pos_rows = pos_resp.data or []

        total_tickets = 0
        for pr in pos_rows:
            val = pr.get("num_transactions")
            if val is not None:
                total_tickets += int(val)

        # --- 3b. Count tickets per responsable from transactions (for personal rate) ---
        tx_resp = (
            db.table("transactions")
            .select("raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .eq("transaction_date", date)
            .execute()
        )
        tx_rows = tx_resp.data or []
        tickets_per_resp: dict[str, int] = {}
        for tx in tx_rows:
            md = tx.get("raw_metadata") or {}
            cid = md.get("cajero_id") or ""
            if cid:
                tickets_per_resp[cid] = tickets_per_resp.get(cid, 0) + 1

        # Edge: sin tickets → incomplete_data
        if total_tickets == 0:
            return CalcResult(
                metric="reprint_rate",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Sin tickets registrados para {business_id} el {date}. "
                    "No se puede calcular tasa de reimpresión."
                ),
            )

        # Edge: 0 reprints → value: 0, ok
        if total_reprints == 0:
            return CalcResult(
                metric="reprint_rate",
                value=Decimal("0"),
                unit="%",
                status="ok",
                context=(
                    f"0 reimpresiones sobre {total_tickets} tickets el {date}. "
                    "Tasa de reimpresión: 0%."
                ),
            )

        # --- 4. Calcular tasa ---
        reprint_rate = (
            Decimal(str(total_reprints)) / Decimal(str(total_tickets)) * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # --- 5. Desagregación por responsable ---
        by_responsable: dict[str, dict] = {}
        for r in all_reprints:
            resp_name = r.get("responsable", "desconocido")
            if resp_name not in by_responsable:
                by_responsable[resp_name] = {"count": 0, "pct_of_total": Decimal("0")}
            by_responsable[resp_name]["count"] += 1

        # Calculate pct_of_total and personal rate
        for resp_name, data in by_responsable.items():
            data["pct_of_total"] = float(
                (Decimal(str(data["count"])) / Decimal(str(total_reprints)) * Decimal("100"))
                .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            )
            # Add personal rate
            own_tickets = tickets_per_resp.get(resp_name, 0)
            if own_tickets > 0:
                data["rate_pct"] = float(
                    (Decimal(str(data["count"])) / Decimal(str(own_tickets)) * Decimal("100"))
                    .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                )
                data["own_tickets"] = own_tickets
            else:
                data["rate_pct"] = 0.0
                data["own_tickets"] = 0

        # --- 6. Evaluar umbrales ---
        if reprint_rate > Decimal("10"):
            status: CalcStatus = "critical"
        elif reprint_rate > Decimal("5"):
            status = "warning"
        else:
            status = "ok"

        # Construir context con desglose
        responsable_summary = "; ".join(
            f"{name}: {info['count']} ({info['pct_of_total']}%)"
            for name, info in by_responsable.items()
        )

        return CalcResult(
            metric="reprint_rate",
            value=reprint_rate,
            unit="%",
            status=status,
            context=(
                f"Tasa de reimpresión: {reprint_rate}% "
                f"({total_reprints}/{total_tickets} tickets el {date}). "
                f"Por responsable: {responsable_summary}. "
                f"by_responsable: {json.dumps(by_responsable)}"
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="reprint_rate",
            value=None,
            unit="%",
            status="incomplete_data",
            context=f"Error al calcular reprint_rate para {business_id}: {exc}",
        )


def calc_shift_cash_variance(business_id: str, date: str, db: Any) -> CalcResult:
    """
    Calcula la varianza de caja por turno del día.

    NO es Tipo B — es por turno, no por persona.

    Para cada turno en shift_audit_events:
        variance = sobrante_faltante (ya calculado por el POS)

    Retorna Σ(sobrante_faltante) como value y desglose por turno en context.

    Fuentes de datos:
        - shift_audit_events (turno, apertura, cierre_z, sobrante_faltante)

    Unidad: "MXN"
    value = Σ(sobrante_faltante) del día

    Umbrales:
        - critical : |Σ(sobrante_faltante)| > 500 MXN
        - warning  : |Σ(sobrante_faltante)| > 100 MXN
        - ok       : |Σ(sobrante_faltante)| <= 100 MXN

    Edge:
        - sin shift_audit_events → status: "incomplete_data"
    """
    try:
        # --- 1. Obtener shift_audit_events del día ---
        events_resp = (
            db.table("shift_audit_events")
            .select("turno, apertura, cierre_z, sobrante_faltante")
            .eq("business_id", business_id)
            .eq("date", date)
            .execute()
        )
        events_rows = events_resp.data or []

        # Edge: sin eventos → incomplete_data
        if not events_rows:
            return CalcResult(
                metric="shift_cash_variance",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=(
                    f"Sin shift_audit_events para {business_id} el {date}. "
                    "No se puede calcular varianza de caja por turno."
                ),
            )

        # --- 2. Calcular varianza total y desglose por turno ---
        total_variance = Decimal("0")
        shifts_detail: list[dict] = []

        for row in events_rows:
            turno = row.get("turno", "desconocido")
            apertura = Decimal(str(row.get("apertura") or 0))
            cierre_z = Decimal(str(row.get("cierre_z") or 0))
            sobrante_faltante = Decimal(str(row.get("sobrante_faltante") or 0))

            total_variance += sobrante_faltante

            # Calcular variance_pct respecto a cierre_z (si > 0)
            if cierre_z > Decimal("0"):
                variance_pct = (
                    sobrante_faltante / cierre_z * Decimal("100")
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                variance_pct = Decimal("0")

            shifts_detail.append({
                "turno": turno,
                "apertura": float(apertura),
                "cierre_z": float(cierre_z),
                "sobrante_faltante": float(sobrante_faltante),
                "variance_pct": float(variance_pct),
            })

        # --- 3. Evaluar umbrales ---
        abs_variance = abs(total_variance)
        if abs_variance > Decimal("500"):
            status: CalcStatus = "critical"
        elif abs_variance > Decimal("100"):
            status = "warning"
        else:
            status = "ok"

        # --- 4. Construir context con desglose ---
        shifts_summary = "; ".join(
            f"{s['turno']}: {s['sobrante_faltante']:+.2f} MXN ({s['variance_pct']:+.2f}%)"
            for s in shifts_detail
        )

        return CalcResult(
            metric="shift_cash_variance",
            value=total_variance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            unit="MXN",
            status=status,
            context=(
                f"Varianza total de caja: {total_variance:+.2f} MXN el {date}. "
                f"Desglose por turno: {shifts_summary}."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="shift_cash_variance",
            value=None,
            unit="MXN",
            status="incomplete_data",
            context=f"Error al calcular shift_cash_variance para {business_id}: {exc}",
        )


def _parse_clock_records_hours(clock_records: list[dict] | None) -> Decimal:
    """
    Auxiliar: calcula el total de horas trabajadas a partir de clock_records JSONB.

    Cada registro: {"employee_id": "...", "clock_in": "ISO-8601", "clock_out": "ISO-8601"}
    - Ignora registros donde clock_out es None (turno aún abierto).
    - Retorna suma total de horas (Decimal).
    """
    if not clock_records:
        return Decimal("0")

    total_hours = Decimal("0")
    for record in clock_records:
        clock_in_str = record.get("clock_in")
        clock_out_str = record.get("clock_out")

        if not clock_in_str or not clock_out_str:
            continue  # Skip registros con turno aún abierto

        try:
            clock_in = datetime.fromisoformat(clock_in_str)
            clock_out = datetime.fromisoformat(clock_out_str)
            diff_seconds = (clock_out - clock_in).total_seconds()
            if diff_seconds > 0:
                total_hours += Decimal(str(diff_seconds)) / Decimal("3600")
        except (ValueError, TypeError):
            continue  # Skip registros con timestamps inválidos

    return total_hours


def calc_labor_cost_ratio(business_id: str, date: str, db: Any) -> CalcResult:
    """
    Calcula el ratio de costo laboral respecto a ventas totales.

    Fórmula:
        horas_trabajadas = Σ(clock_out - clock_in) de shift_audit_events.clock_records
        costo_hora = Σ(business_fixed_costs WHERE concept ILIKE '%nómina%') / 30 / 8
        labor_cost = horas_trabajadas × costo_hora_estimado
        labor_ratio = labor_cost / total_sales × 100

    Fuentes de datos:
        - shift_audit_events.clock_records (JSONB array)
        - pos_inputs.total_sales
        - business_fixed_costs (concept ILIKE '%nómina%')

    Unidad: "%"
    Nota v1: costo por hora es estimación basada en nómina fija / 30 / 8.

    Umbrales:
        - critical : labor_ratio > 35%
        - warning  : labor_ratio > 30%
        - ok       : labor_ratio <= 30%

    Edge:
        - sin clock_records → status: "incomplete_data"
        - total_sales = 0 → status: "incomplete_data"
    """
    try:
        # --- 1. Obtener clock_records del día ---
        events_resp = (
            db.table("shift_audit_events")
            .select("clock_records")
            .eq("business_id", business_id)
            .eq("date", date)
            .execute()
        )
        events_rows = events_resp.data or []

        # Consolidar todas las horas trabajadas
        total_hours = Decimal("0")
        for row in events_rows:
            records = row.get("clock_records")
            if isinstance(records, list):
                total_hours += _parse_clock_records_hours(records)

        # Edge: sin clock_records → incomplete_data
        if total_hours == Decimal("0"):
            return CalcResult(
                metric="labor_cost_ratio",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Sin registros de clock_records para {business_id} el {date}. "
                    "No se puede calcular ratio de costo laboral."
                ),
            )

        # --- 2. Obtener total_sales del día ---
        pos_resp = (
            db.table("pos_inputs")
            .select("total_sales")
            .eq("business_id", business_id)
            .eq("date", date)
            .execute()
        )
        pos_rows = pos_resp.data or []

        total_sales = Decimal("0")
        for pr in pos_rows:
            val = pr.get("total_sales")
            if val is not None:
                total_sales += Decimal(str(val))

        # Edge: total_sales = 0 → incomplete_data
        if total_sales == Decimal("0"):
            return CalcResult(
                metric="labor_cost_ratio",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Total de ventas es 0 para {business_id} el {date}. "
                    "No se puede calcular ratio de costo laboral."
                ),
            )

        # --- 3. Estimar costo por hora (v1: nómina fija / 30 / 8) ---
        nomina_resp = (
            db.table("business_fixed_costs")
            .select("amount")
            .eq("business_id", business_id)
            .ilike("concept", "%nómina%")
            .execute()
        )
        nomina_rows = nomina_resp.data or []

        if not nomina_rows:
            return CalcResult(
                metric="labor_cost_ratio",
                value=None,
                unit="%",
                status="incomplete_data",
                context=(
                    f"Sin costos fijos de nómina para {business_id}. "
                    "No se puede estimar costo por hora laboral."
                ),
            )

        total_nomina = sum(Decimal(str(r["amount"])) for r in nomina_rows)
        # Estimación v1: nómina mensual / 30 días / 8 horas
        costo_hora = (total_nomina / Decimal("30") / Decimal("8")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # --- 4. Calcular labor_cost y ratio ---
        labor_cost = (total_hours * costo_hora).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        labor_ratio = (
            labor_cost / total_sales * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # --- 5. Evaluar umbrales ---
        if labor_ratio > Decimal("35"):
            status: CalcStatus = "critical"
        elif labor_ratio > Decimal("30"):
            status = "warning"
        else:
            status = "ok"

        return CalcResult(
            metric="labor_cost_ratio",
            value=labor_ratio,
            unit="%",
            status=status,
            context=(
                f"Ratio costo laboral: {labor_ratio}%. "
                f"Horas trabajadas: {total_hours:.2f}h × {costo_hora:.2f} MXN/h "
                f"= {labor_cost:.2f} MXN. "
                f"Ventas totales: {total_sales:.2f} MXN. "
                f"(Nota v1: costo/hora estimado desde nómina fija {total_nomina:.2f}/30/8)."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="labor_cost_ratio",
            value=None,
            unit="%",
            status="incomplete_data",
            context=f"Error al calcular labor_cost_ratio para {business_id}: {exc}",
        )


def calc_sales_per_labor_hour(business_id: str, date: str, db: Any) -> CalcResult:
    """
    Calcula la productividad laboral: ventas por hora trabajada.

    Fórmula:
        horas_trabajadas = Σ(clock_out - clock_in) de shift_audit_events.clock_records
        sales_per_hour = pos_inputs.total_sales / horas_trabajadas

    No requiere dato de salario — solo horas y ventas.
    Complementa a calc_labor_cost_ratio con una vista de productividad pura.

    Fuentes de datos:
        - shift_audit_events.clock_records (JSONB array)
        - pos_inputs.total_sales

    Unidad: "MXN/hora"

    Umbrales:
        - No definidos en v1 — siempre "ok" si hay datos válidos.

    Edge:
        - sin clock_records → status: "incomplete_data"
        - horas_trabajadas = 0 → status: "incomplete_data"
        - total_sales = 0 → value: 0, status: "ok"
    """
    try:
        # --- 1. Obtener clock_records del día ---
        events_resp = (
            db.table("shift_audit_events")
            .select("clock_records")
            .eq("business_id", business_id)
            .eq("date", date)
            .execute()
        )
        events_rows = events_resp.data or []

        # Consolidar horas trabajadas
        total_hours = Decimal("0")
        for row in events_rows:
            records = row.get("clock_records")
            if isinstance(records, list):
                total_hours += _parse_clock_records_hours(records)

        # Edge: sin clock_records o 0 horas → incomplete_data
        if total_hours == Decimal("0"):
            return CalcResult(
                metric="sales_per_labor_hour",
                value=None,
                unit="MXN/hora",
                status="incomplete_data",
                context=(
                    f"Sin registros de clock_records (o 0 horas) para {business_id} el {date}. "
                    "No se puede calcular ventas por hora laboral."
                ),
            )

        # --- 2. Obtener total_sales del día ---
        pos_resp = (
            db.table("pos_inputs")
            .select("total_sales")
            .eq("business_id", business_id)
            .eq("date", date)
            .execute()
        )
        pos_rows = pos_resp.data or []

        total_sales = Decimal("0")
        for pr in pos_rows:
            val = pr.get("total_sales")
            if val is not None:
                total_sales += Decimal(str(val))

        # Edge: total_sales = 0 → value: 0, status: "ok"
        if total_sales == Decimal("0"):
            return CalcResult(
                metric="sales_per_labor_hour",
                value=Decimal("0"),
                unit="MXN/hora",
                status="ok",
                context=(
                    f"Ventas totales: 0 MXN con {total_hours:.2f} horas trabajadas. "
                    f"Productividad laboral: 0 MXN/hora."
                ),
            )

        # --- 3. Calcular sales_per_hour ---
        sales_per_hour = (total_sales / total_hours).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return CalcResult(
            metric="sales_per_labor_hour",
            value=sales_per_hour,
            unit="MXN/hora",
            status="ok",
            context=(
                f"Productividad laboral: {sales_per_hour} MXN/hora. "
                f"Ventas totales: {total_sales:.2f} MXN / "
                f"{total_hours:.2f} horas trabajadas el {date}."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="sales_per_labor_hour",
            value=None,
            unit="MXN/hora",
            status="incomplete_data",
            context=f"Error al calcular sales_per_labor_hour para {business_id}: {exc}",
        )


# ===========================================================================
# FUNCIONES DE CÁLCULO — NIVEL INVENTARIO
# Spec: s3_motor_calculo.md §Funciones — Nivel Inventario
# Fuente: tabla inventory_daily (migración 005)
# ===========================================================================


def calc_waste_cost(business_id: str, date: str, db: Any) -> CalcResult:
    """
    Calcula el costo monetario de la merma del día en pesos mexicanos.

    Fórmula:
        waste_cost = Σ(waste_recorded × unit_cost)
                     WHERE business_id AND date

    Fuente de datos:
        - inventory_daily: waste_recorded, unit_cost

    Unidad: "MXN"
    Status: siempre "ok" (sin umbrales definidos aún).
    Edge: sin registros en inventory_daily → status: "incomplete_data".
    Edge: waste_recorded = 0 en todos → value: 0, status: "ok".
    """
    try:
        # --- 1. Obtener registros de inventory_daily para el día ---
        resp = (
            db.table("inventory_daily")
            .select("ingredient_id, ingredient_name, waste_recorded, unit_cost")
            .eq("business_id", business_id)
            .eq("date", date)
            .execute()
        )
        rows = resp.data or []

        if not rows:
            return CalcResult(
                metric="waste_cost",
                value=None,
                unit="MXN",
                status="incomplete_data",
                context=(
                    f"Sin registros de inventario diario para {business_id} el {date}."
                ),
            )

        # --- 2. Calcular costo total de merma ---
        total_waste_cost = Decimal("0")
        desglose: list[str] = []
        worst_status: CalcStatus = "ok"

        for row in rows:
            waste = Decimal(str(row.get("waste_recorded") or 0))
            unit_cost = Decimal(str(row.get("unit_cost") or 0))
            costo_linea = waste * unit_cost
            total_waste_cost += costo_linea

            if waste > Decimal("0"):
                nombre = row.get("ingredient_name") or row.get("ingredient_id", "?")
                desglose.append(f"{nombre}: {waste} × {unit_cost} = {costo_linea:.2f}")

            # Derive status from waste percentage (same thresholds as calc_waste_analysis)
            consumo_teorico = Decimal(str(row.get("consumo_teorico") or 0))
            if consumo_teorico > Decimal("0"):
                waste_pct = waste / consumo_teorico * Decimal("100")
                if waste_pct > Decimal("10"):
                    worst_status = "critical"
                elif waste_pct > Decimal("5") and worst_status != "critical":
                    worst_status = "warning"

        total_waste_cost = total_waste_cost.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # --- 3. Construir contexto ---
        if desglose:
            detalle = "; ".join(desglose[:5])  # Máx 5 líneas para legibilidad
            if len(desglose) > 5:
                detalle += f" (+{len(desglose) - 5} más)"
            context_str = (
                f"Costo de merma del {date}: {total_waste_cost} MXN. "
                f"Desglose: {detalle}."
            )
        else:
            context_str = (
                f"Sin merma registrada para {business_id} el {date}. "
                f"Costo de merma: 0 MXN."
            )

        return CalcResult(
            metric="waste_cost",
            value=total_waste_cost,
            unit="MXN",
            status=worst_status,
            context=context_str,
        )

    except Exception as exc:
        return CalcResult(
            metric="waste_cost",
            value=None,
            unit="MXN",
            status="incomplete_data",
            context=f"Error al calcular costo de merma para {business_id}: {exc}",
        )


def calc_stock_days_remaining(business_id: str, date: str, db: Any) -> CalcResult:
    """
    Calcula los días de stock restantes por ingrediente.

    Fórmula (por ingrediente):
        consumo_diario_promedio = AVG(consumo_teorico) de los últimos 7 días
                                 (solo días con consumo_teorico > 0)
        days_remaining = current_stock / consumo_diario_promedio

    Retorna como value el MÍNIMO de days_remaining entre todos los ingredientes
    (alerta temprana: el ingrediente que se agotará primero).

    Fuente de datos:
        - inventory_daily: current_stock (del día actual), consumo_teorico (últimos 7 días)

    Unidad: "días"
    Umbrales:
        - critical : days_remaining < 3
        - warning  : days_remaining < 7
        - ok       : days_remaining >= 7
    Edge: sin historial → status: "incomplete_data".
    Edge: consumo_diario_promedio = 0 para un ingrediente → se omite (no se consume).
    """
    try:
        # --- 1. Obtener stock actual del día ---
        resp_hoy = (
            db.table("inventory_daily")
            .select("ingredient_id, ingredient_name, current_stock")
            .eq("business_id", business_id)
            .eq("date", date)
            .execute()
        )
        rows_hoy = resp_hoy.data or []

        if not rows_hoy:
            return CalcResult(
                metric="stock_days_remaining",
                value=None,
                unit="días",
                status="incomplete_data",
                context=(
                    f"Sin registros de inventario diario para {business_id} el {date}."
                ),
            )

        # --- 2. Calcular rango de últimos 7 días para consumo promedio ---
        dt = datetime.strptime(date, "%Y-%m-%d")
        start_7d = (dt - timedelta(days=6)).strftime("%Y-%m-%d")

        resp_hist = (
            db.table("inventory_daily")
            .select("ingredient_id, consumo_teorico, date")
            .eq("business_id", business_id)
            .gte("date", start_7d)
            .lte("date", date)
            .execute()
        )
        rows_hist = resp_hist.data or []

        if not rows_hist:
            return CalcResult(
                metric="stock_days_remaining",
                value=None,
                unit="días",
                status="incomplete_data",
                context=(
                    f"Sin historial de consumo en los últimos 7 días para {business_id}."
                ),
            )

        # --- 3. Agrupar consumo histórico por ingrediente ---
        # Solo contar días con consumo_teorico > 0
        consumo_por_ing: dict[str, list[Decimal]] = {}
        for row in rows_hist:
            ing_id = row["ingredient_id"]
            consumo = Decimal(str(row.get("consumo_teorico") or 0))
            if consumo > Decimal("0"):
                consumo_por_ing.setdefault(ing_id, []).append(consumo)

        # --- 4. Calcular days_remaining por ingrediente ---
        resultados_ing: list[dict] = []
        min_days: Decimal | None = None

        for row_hoy in rows_hoy:
            ing_id = row_hoy["ingredient_id"]
            nombre = row_hoy.get("ingredient_name") or ing_id
            stock = Decimal(str(row_hoy.get("current_stock") or 0))

            # Si no hay historial de consumo para este ingrediente, omitir
            if ing_id not in consumo_por_ing:
                continue

            valores_consumo = consumo_por_ing[ing_id]
            consumo_promedio = sum(valores_consumo) / Decimal(str(len(valores_consumo)))

            # Si el promedio es 0 (todos los días tienen consumo 0), omitir
            if consumo_promedio == Decimal("0"):
                continue

            days_rem = (stock / consumo_promedio).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            resultados_ing.append({
                "ingredient_id": ing_id,
                "ingredient_name": nombre,
                "current_stock": float(stock),
                "consumo_diario_promedio": float(consumo_promedio),
                "days_remaining": float(days_rem),
            })

            if min_days is None or days_rem < min_days:
                min_days = days_rem

        # --- 5. Evaluar resultado ---
        if not resultados_ing:
            return CalcResult(
                metric="stock_days_remaining",
                value=None,
                unit="días",
                status="incomplete_data",
                context=(
                    f"Ningún ingrediente tiene consumo registrado en los últimos 7 días "
                    f"para {business_id}."
                ),
            )

        # Encontrar el ingrediente con menor days_remaining para el contexto
        ingrediente_critico = min(resultados_ing, key=lambda x: x["days_remaining"])
        resumen_top = "; ".join(
            f"{r['ingredient_name']}: {r['days_remaining']:.1f}d"
            for r in sorted(resultados_ing, key=lambda x: x["days_remaining"])[:5]
        )

        # --- 6. Evaluar umbrales ---
        status: CalcStatus = "ok"
        if min_days < Decimal("3"):
            status = "critical"
        elif min_days < Decimal("7"):
            status = "warning"

        return CalcResult(
            metric="stock_days_remaining",
            value=min_days,
            unit="días",
            status=status,
            context=(
                f"Ingrediente más crítico: {ingrediente_critico['ingredient_name']} "
                f"con {ingrediente_critico['days_remaining']:.1f} días de stock. "
                f"Top 5 urgentes: {resumen_top}. "
                f"Total ingredientes evaluados: {len(resultados_ing)}."
            ),
        )

    except Exception as exc:
        return CalcResult(
            metric="stock_days_remaining",
            value=None,
            unit="días",
            status="incomplete_data",
            context=f"Error al calcular días de stock para {business_id}: {exc}",
        )


def calc_contribution_margin_by_channel(
    business_id: str,
    date: str,
    db: Any,
) -> CalcResult:
    """
    Margen de contribución por canal de venta (Comedor, Para llevar, UberEats, Rappi, etc.)
    más un nivel "dia_blended" con el promedio del día completo.

    Formula por canal:
        margen = (subtotal_canal - costo_ingredientes_canal - comision_canal) / subtotal_canal

    costo_ingredientes_canal: suma del costo de recetas (tabla recipes) de los productos
    vendidos en ese canal, usando product_id de cada línea de producto en raw_metadata.

    comision_canal: 0 para Comedor/Para llevar. Para canales de delivery, la comisión de
    ese canal específico (misma lógica que calc_delivery_commission_cost usa para calcular
    commission por plataforma).

    dia_blended: mismo cálculo pero con subtotal/costo/comisión sumados de TODO el día,
    todos los canales.

    Status: siempre "ok" (informativo, sin umbral propio).
    value: None (el desglose va en context como JSON).
    unit: "ratio"
    """
    import json as _json

    try:
        # --- Mapeo de claves delivery en PaymentBreakdown → nombre canal ---
        DELIVERY_KEY_TO_CHANNEL = {
            "uber_eats": "UberEats",
            "rappi": "Rappi",
            "didi_food": "DiDiFood",
        }
        CHANNEL_TO_PLATFORM = {
            "UberEats": "UberEats",
            "Rappi": "Rappi",
            "DiDiFood": "DiDiFood",
        }

        # --- 1. Obtener todas las recetas del negocio → mapa product_id → costo ---
        recetas_resp = (
            db.table("recipes")
            .select("id, sale_price, ingredients")
            .eq("business_id", business_id)
            .execute()
        )
        recetas_rows = recetas_resp.data or []

        # Calcular costo de cada receta
        product_cost_map: dict[str, Decimal] = {}
        for receta in recetas_rows:
            product_id = receta["id"]
            ingredientes: dict = receta.get("ingredients") or {}
            costo_total = Decimal("0")

            for ing_id, qty_raw in ingredientes.items():
                qty = Decimal(str(qty_raw))
                # Obtener último precio unitario del ingrediente
                tx_resp = (
                    db.table("transactions")
                    .select("unit_price")
                    .eq("ingredient_id", ing_id)
                    .order("transaction_date", desc=True)
                    .limit(1)
                    .execute()
                )
                tx_rows = tx_resp.data or []
                if tx_rows and tx_rows[0].get("unit_price") is not None:
                    precio_unitario = Decimal(str(tx_rows[0]["unit_price"]))
                    costo_total += qty * precio_unitario

            product_cost_map[product_id] = costo_total

        # --- 2. Obtener tickets del día ---
        resp = (
            db.table("transactions")
            .select("raw_metadata")
            .eq("business_id", business_id)
            .eq("type", "ingreso")
            .eq("category", "venta")
            .eq("transaction_date", date)
            .execute()
        )
        rows = resp.data or []

        if not rows:
            return CalcResult(
                metric="contribution_margin_by_channel",
                value=None,
                unit="ratio",
                status="ok",
                context=f"Sin transacciones para {business_id} el {date}.",
            )

        # --- 3. Clasificar ordenes por canal y acumular subtotal + costo ---
        # Estructura: channel → {subtotal, costo, comision}
        channel_data: dict[str, dict[str, Decimal]] = {}

        for row in rows:
            metadata = row.get("raw_metadata") or {}
            order_type = metadata.get("order_type", "")
            subtotal = Decimal(str(metadata.get("subtotal", 0) or 0))
            payment_breakdown = metadata.get("PaymentBreakdown") or {}
            items = metadata.get("items") or []

            # Determinar canal
            if order_type == "Comedor":
                channel = "Comedor"
            elif order_type == "Para llevar":
                channel = "Para llevar"
            elif order_type == "Delivery App":
                # Determinar plataforma desde PaymentBreakdown keys
                channel = None
                for key in payment_breakdown:
                    if key in DELIVERY_KEY_TO_CHANNEL:
                        channel = DELIVERY_KEY_TO_CHANNEL[key]
                        break
                if channel is None:
                    # Fallback: tratar como delivery genérico
                    channel = "Delivery"
            else:
                channel = order_type or "Otro"

            # Inicializar canal
            if channel not in channel_data:
                channel_data[channel] = {
                    "subtotal": Decimal("0"),
                    "costo": Decimal("0"),
                    "comision": Decimal("0"),
                }

            channel_data[channel]["subtotal"] += subtotal

            # Calcular costo de ingredientes para esta orden
            order_cost = Decimal("0")
            if items:
                for item in items:
                    item_id = item.get("item_id", "")
                    qty = Decimal(str(item.get("quantity", 1)))
                    if item_id in product_cost_map:
                        order_cost += product_cost_map[item_id] * qty
            else:
                # Sin detalle de items: estimar usando producto representativo del canal
                # Usar el costo promedio de todos los productos conocidos ponderado
                # por el subtotal de la orden vs precio promedio
                if product_cost_map:
                    # Buscar un producto cuyo sale_price coincida con el subtotal
                    matched = False
                    for receta in recetas_rows:
                        sale_price = Decimal(str(receta.get("sale_price", 0)))
                        if sale_price > 0 and sale_price == subtotal:
                            pid = receta["id"]
                            if pid in product_cost_map:
                                order_cost = product_cost_map[pid]
                                matched = True
                                break
                    if not matched:
                        # Usar ratio promedio costo/precio de todos los productos
                        total_sale = sum(
                            Decimal(str(r.get("sale_price", 0)))
                            for r in recetas_rows
                            if Decimal(str(r.get("sale_price", 0))) > 0
                        )
                        total_cost = sum(product_cost_map.values())
                        if total_sale > 0:
                            avg_ratio = total_cost / total_sale
                            order_cost = (subtotal * avg_ratio).quantize(
                                Decimal("0.01"), rounding=ROUND_HALF_UP
                            )

            channel_data[channel]["costo"] += order_cost

        # --- 4. Calcular comisiones por canal de delivery ---
        for channel, platform_name in CHANNEL_TO_PLATFORM.items():
            if channel not in channel_data:
                continue
            sales = channel_data[channel]["subtotal"]
            if sales == Decimal("0"):
                continue

            # Buscar tasa vigente para la plataforma
            config_resp = (
                db.table("delivery_platform_config")
                .select("commission_rate")
                .eq("business_id", business_id)
                .eq("platform", platform_name)
                .lte("effective_date", date)
                .order("effective_date", desc=True)
                .limit(1)
                .execute()
            )
            config_rows = config_resp.data or []
            if config_rows:
                commission_rate = Decimal(str(config_rows[0]["commission_rate"]))
                channel_data[channel]["comision"] = (
                    sales * commission_rate
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # --- 5. Calcular margen por canal ---
        channel_margins: dict[str, float] = {}
        total_subtotal = Decimal("0")
        total_costo = Decimal("0")
        total_comision = Decimal("0")

        for channel, data in channel_data.items():
            sub = data["subtotal"]
            cos = data["costo"]
            com = data["comision"]

            total_subtotal += sub
            total_costo += cos
            total_comision += com

            if sub > Decimal("0"):
                margen = ((sub - cos - com) / sub).quantize(
                    Decimal("0.001"), rounding=ROUND_HALF_UP
                )
                channel_margins[channel] = float(margen)

        # --- 6. dia_blended ---
        if total_subtotal > Decimal("0"):
            margen_blended = (
                (total_subtotal - total_costo - total_comision) / total_subtotal
            ).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
            channel_margins["dia_blended"] = float(margen_blended)

        # --- 7. Retornar resultado ---
        context_json = _json.dumps(channel_margins)

        return CalcResult(
            metric="contribution_margin_by_channel",
            value=None,
            unit="ratio",
            status="ok",
            context=context_json,
        )

    except Exception as exc:
        return CalcResult(
            metric="contribution_margin_by_channel",
            value=None,
            unit="ratio",
            status="incomplete_data",
            context=f"Error al calcular margen por canal para {business_id}: {exc}",
        )