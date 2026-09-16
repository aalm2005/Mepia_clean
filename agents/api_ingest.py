"""
S1B — Ingesta API (Ruta Primaria)
Modelos Pydantic para los 5 niveles de ingesta y resultado de operación.
Sin LLM — 100% determinístico (validación + mapeo).
Spec: .kiro/specs/mepia/s1b_ingesta_api.md
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

_logger = logging.getLogger(__name__)

# Constante para la tasa de IVA en México
_IVA_RATE = Decimal("0.16")
# Tolerancia relativa para validación de IVA (±2%)
_TAX_TOLERANCE = Decimal("0.02")
# Tolerancia absoluta para validación de total_net (±$1 MXN)
_TOTAL_NET_TOLERANCE = Decimal("1.0")


# ---------------------------------------------------------------------------
# Nivel 2 — Detalle de Producto: ProductLine
# Spec: s1b_ingesta_api.md §Nivel 2
# ---------------------------------------------------------------------------

class ProductLine(BaseModel):
    """Línea de producto dentro de un ticket — detalle de cada item vendido."""

    item_id: str                        # ID del producto en catálogo POS
    product_name: str
    group: str                          # categoría principal (ej. "Bebidas calientes")
    subgroup: str | None = None         # subcategoría (ej. "Espresso")
    variant_modifier: str | None = None # modificadores (ej. "extra shot", "leche avena")
    unit_price: Decimal                 # precio unitario sin descuento
    quantity: int = Field(ge=1)         # cantidad — mínimo 1
    item_discount: Decimal = Decimal("0")


# ---------------------------------------------------------------------------
# Nivel 1 — Transacción/Ticket: TicketEvent
# Spec: s1b_ingesta_api.md §Nivel 1
# ---------------------------------------------------------------------------

class TicketEvent(BaseModel):
    """Evento de ticket/transacción individual del POS."""

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


# ---------------------------------------------------------------------------
# Nivel 3 — Formas de Pago: PaymentBreakdown
# Spec: s1b_ingesta_api.md §Nivel 3
# ---------------------------------------------------------------------------

class PaymentBreakdown(BaseModel):
    """Desglose de formas de pago por ticket."""

    order_id: str                       # FK lógico a TicketEvent.order_id
    efectivo: Decimal = Decimal("0")
    tarjeta_clip: Decimal = Decimal("0")
    uber_eats: Decimal = Decimal("0")
    rappi: Decimal = Decimal("0")
    didi_food: Decimal = Decimal("0")
    cortesia_staff: Decimal = Decimal("0")
    tarjetas_lealtad: Decimal = Decimal("0")


# ---------------------------------------------------------------------------
# Nivel 4 — Operación/Caja/Auditoría: ShiftAuditEvent (y sub-modelos)
# Spec: s1b_ingesta_api.md §Nivel 4
# ---------------------------------------------------------------------------

class CancellationRecord(BaseModel):
    """Registro de una cancelación de ticket."""

    order_id: str
    motivo: str
    responsable: str                    # cajero/mesero que canceló
    timing: Literal["pre_comanda", "post_comanda"]


class ReprintRecord(BaseModel):
    """Registro de una reimpresión de ticket."""

    order_id: str
    responsable: str                    # cajero/mesero que reimprimió
    hora: str                           # HH:MM, mismo formato que llega de la API


class ShiftData(BaseModel):
    """Datos de un turno de caja."""

    turno: str                          # ej. "matutino", "vespertino"
    apertura: Decimal                   # fondo de apertura del turno
    cierre_x: Decimal                   # lectura X (parcial)
    cierre_z: Decimal                   # lectura Z (cierre final)
    sobrante_faltante: Decimal          # positivo = sobrante, negativo = faltante


class ClockRecord(BaseModel):
    """Registro de entrada/salida de un empleado."""

    employee_id: str
    clock_in: datetime
    clock_out: datetime | None = None   # null si turno aún abierto


class ShiftAuditEvent(BaseModel):
    """Evento de auditoría operativa por turno — agrupa cancelaciones, turnos y asistencia."""

    sucursal_id: str
    date: date
    cancellations: list[CancellationRecord] = []
    reprints: list[ReprintRecord] = []  # reimpresiones de tickets (con responsable)
    shifts: list[ShiftData]             # al menos 1 turno por día
    clock_records: list[ClockRecord] = []


# ---------------------------------------------------------------------------
# Nivel 5 — Inventarios/Costos Teóricos: InventoryUsageEvent
# Spec: s1b_ingesta_api.md §Nivel 5
# ---------------------------------------------------------------------------

class InventoryUsageEvent(BaseModel):
    """Snapshot de consumo teórico e inventario diario de un insumo."""

    ingredient_id: str                  # ID del insumo en catálogo
    ingredient_name: str
    unit: str                           # unidad base (g, ml, unidad)
    consumo_teorico: Decimal            # consumo teórico del día por recetas vendidas
    waste_recorded: Decimal = Decimal("0")  # merma registrada manualmente
    current_stock: Decimal              # existencia actual
    unit_cost: Decimal                  # costo unitario de la última compra


# ---------------------------------------------------------------------------
# Payload de entrada — APIIngestPayload
# Spec: s1b_ingesta_api.md §Input — Contrato de Entrada
# ---------------------------------------------------------------------------

class APIIngestPayload(BaseModel):
    """
    Payload completo del endpoint POST /ingest/api-event.
    Contiene un batch de eventos de un mismo día y sucursal (5 niveles).
    """

    business_id: UUID
    date: date                          # YYYY-MM-DD
    sucursal_id: str                    # identificador de la sucursal origen

    tickets: list[TicketEvent]          # Nivel 1 — Transacciones
    payments: list[PaymentBreakdown]    # Nivel 3 — Formas de pago (1 por ticket)
    shift_audit: list[ShiftAuditEvent]  # Nivel 4 — Operación/Caja
    inventory: list[InventoryUsageEvent]# Nivel 5 — Inventarios/Costos Teóricos


# ---------------------------------------------------------------------------
# Output — APIIngestResult
# Spec: s1b_ingesta_api.md §Output
# ---------------------------------------------------------------------------

class APIIngestResult(BaseModel):
    """
    Resultado de la operación de ingesta.
    Nunca lanza excepción — errores se expresan como status.
    """

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


# ---------------------------------------------------------------------------
# Validation Result — Resultado de validaciones de integridad
# Spec: s1b_ingesta_api.md §Heurísticas — Reglas de validación de integridad
# ---------------------------------------------------------------------------

class ValidationResult(BaseModel):
    """
    Resultado de las 10 reglas de validación de integridad.
    Controles silenciosos — flagean issues pero no generan hallazgos de negocio.
    Se ejecutan antes de persistir datos a la base de datos.
    """

    is_rejected: bool = False
    """True si el payload completo debe rechazarse (reglas 9, 10)."""

    reject_reason: str | None = None
    """Razón del rechazo (solo si is_rejected=True)."""

    ticket_flags: dict[str, list[str]] = Field(default_factory=dict)
    """Mapping de order_id → lista de flag names (tax_mismatch, total_inconsistency, etc.)."""

    rejected_items: dict[str, list[int]] = Field(default_factory=dict)
    """Mapping de order_id → índices de ProductLine items rechazados (regla 4)."""

    rejected_shift_audits: list[int] = Field(default_factory=list)
    """Índices de ShiftAuditEvents rechazados (regla 6 — shifts vacío)."""

    inventory_flags: dict[str, list[str]] = Field(default_factory=dict)
    """Mapping de ingredient_id → lista de flag names (negative_stock, zero_cost)."""

    skipped_order_ids: list[str] = Field(default_factory=list)
    """order_ids saltados por idempotencia (regla 5)."""

    warnings: list[str] = Field(default_factory=list)
    """Mensajes de warning para incluir en la respuesta."""


# ---------------------------------------------------------------------------
# Funciones de validación de integridad (10 reglas)
# Spec: s1b_ingesta_api.md §Heurísticas
# ---------------------------------------------------------------------------

def validate_ticket(
    ticket: TicketEvent,
    payment: PaymentBreakdown | None,
) -> tuple[list[str], list[int]]:
    """
    Valida un ticket individual aplicando reglas 1–4.

    Args:
        ticket: Evento de ticket a validar.
        payment: PaymentBreakdown asociado (por order_id), o None si no existe.

    Returns:
        Tupla (flags, rejected_item_indices):
        - flags: lista de nombres de flag detectados para este ticket.
        - rejected_item_indices: índices de items en ticket.items que deben
          rechazarse (quantity < 1).

    Reglas aplicadas:
        1. tax ≈ subtotal × 0.16 (tolerancia ±2%) → flag 'tax_mismatch'
        2. total_net ≈ subtotal + tax - discounts (±$1 MXN) → flag 'total_inconsistency'
        3. Σ PaymentBreakdown == TicketEvent.total_net → flag 'payment_mismatch'
        4. quantity >= 1 en cada ProductLine → rechazar item
    """
    flags: list[str] = []
    rejected_indices: list[int] = []

    # --- Regla 1: tax ≈ subtotal × 0.16 (tolerancia relativa ±2%) ---
    expected_tax = ticket.subtotal * _IVA_RATE
    if expected_tax != Decimal("0"):
        tax_deviation = abs(ticket.tax - expected_tax) / expected_tax
        if tax_deviation > _TAX_TOLERANCE:
            flags.append("tax_mismatch")
    elif ticket.tax != Decimal("0"):
        # subtotal es 0 pero tax no — siempre es mismatch
        flags.append("tax_mismatch")

    # --- Regla 2: total_net ≈ subtotal + tax - discounts (±$1 MXN) ---
    expected_total = ticket.subtotal + ticket.tax - ticket.discounts
    if abs(ticket.total_net - expected_total) > _TOTAL_NET_TOLERANCE:
        flags.append("total_inconsistency")

    # --- Regla 3: Σ PaymentBreakdown fields == TicketEvent.total_net ---
    if payment is not None:
        payment_sum = (
            payment.efectivo
            + payment.tarjeta_clip
            + payment.uber_eats
            + payment.rappi
            + payment.didi_food
            + payment.cortesia_staff
            + payment.tarjetas_lealtad
        )
        if payment_sum != ticket.total_net:
            flags.append("payment_mismatch")

    # --- Regla 4: quantity >= 1 en cada ProductLine ---
    # Pydantic ya valida ge=1, pero verificamos por si se construye
    # el modelo programáticamente sin validación (construct).
    for idx, item in enumerate(ticket.items):
        if item.quantity < 1:
            rejected_indices.append(idx)

    return flags, rejected_indices


def validate_inventory(item: InventoryUsageEvent) -> list[str]:
    """
    Valida un evento de inventario aplicando reglas 7–8.

    Args:
        item: Evento de inventario/costo teórico a validar.

    Returns:
        Lista de flag names detectados para este item.

    Reglas aplicadas:
        7. current_stock >= 0 → flag 'negative_stock'
        8. unit_cost > 0 → flag 'zero_cost'
    """
    flags: list[str] = []

    # --- Regla 7: current_stock >= 0 ---
    if item.current_stock < Decimal("0"):
        flags.append("negative_stock")

    # --- Regla 8: unit_cost > 0 ---
    if item.unit_cost <= Decimal("0"):
        flags.append("zero_cost")

    return flags


def validate_payload(
    payload: APIIngestPayload,
    existing_order_ids: set[str],
    business_exists: bool = True,
) -> ValidationResult:
    """
    Ejecuta las 10 reglas de validación de integridad sobre un payload completo.

    Esta función es pura — no accede a la base de datos. El caller pasa
    `existing_order_ids` (para idempotencia) y `business_exists` (para regla 10).

    Args:
        payload: Payload completo de ingesta API.
        existing_order_ids: Set de order_ids que ya existen en DB para
            el mismo (business_id, date) — para regla 5 de idempotencia.
        business_exists: True si el business_id existe en la tabla businesses.

    Returns:
        ValidationResult con todos los flags, rechazos y warnings.

    Reglas (orden de ejecución):
        9.  date no en el futuro → rechazar payload completo
        10. business_id existe en businesses → rechazar payload completo
        5.  order_id único por (business_id, date) → skip duplicados
        1.  tax ≈ subtotal × 0.16 (±2%) → flag tax_mismatch
        2.  total_net ≈ subtotal + tax - discounts (±$1) → flag total_inconsistency
        3.  Σ PaymentBreakdown == total_net → flag payment_mismatch
        4.  quantity >= 1 → rechazar item individual
        6.  shifts no vacío en ShiftAuditEvent → rechazar evento completo
        7.  current_stock >= 0 → flag negative_stock
        8.  unit_cost > 0 → flag zero_cost
    """
    result = ValidationResult()

    # === Reglas de rechazo total (se evalúan PRIMERO) ===

    # --- Regla 9: date no en el futuro ---
    if payload.date > date.today():
        result.is_rejected = True
        result.reject_reason = (
            f"Fecha {payload.date.isoformat()} está en el futuro — "
            "payload rechazado (HTTP 422)"
        )
        return result

    # --- Regla 10: business_id existe en businesses ---
    if not business_exists:
        result.is_rejected = True
        result.reject_reason = (
            f"business_id {payload.business_id} no existe en businesses — "
            "payload rechazado (HTTP 404)"
        )
        return result

    # === Validación de tickets (reglas 1–5) ===

    # Indexar payments por order_id para lookup O(1)
    payments_by_order: dict[str, PaymentBreakdown] = {
        p.order_id: p for p in payload.payments
    }

    for ticket in payload.tickets:
        # --- Regla 5: Idempotencia — order_id único por (business_id, date) ---
        if ticket.order_id in existing_order_ids:
            result.skipped_order_ids.append(ticket.order_id)
            continue

        # Aplicar reglas 1–4 al ticket
        payment = payments_by_order.get(ticket.order_id)
        flags, rejected_indices = validate_ticket(ticket, payment)

        if flags:
            result.ticket_flags[ticket.order_id] = flags

        if rejected_indices:
            result.rejected_items[ticket.order_id] = rejected_indices

    # === Regla 6: shifts no vacío en ShiftAuditEvent ===

    for idx, audit in enumerate(payload.shift_audit):
        if not audit.shifts:
            result.rejected_shift_audits.append(idx)

    # === Validación de inventario (reglas 7–8) ===

    for item in payload.inventory:
        flags = validate_inventory(item)
        if flags:
            result.inventory_flags[item.ingredient_id] = flags

    # === Generar warnings según política documentada ===

    # Tax mismatch warnings
    tax_mismatch_count = sum(
        1 for flags in result.ticket_flags.values()
        if "tax_mismatch" in flags
    )
    if tax_mismatch_count > 0:
        result.warnings.append(
            f"IVA inconsistente detectado en {tax_mismatch_count} tickets"
        )

    # Payment mismatch warnings
    payment_mismatch_count = sum(
        1 for flags in result.ticket_flags.values()
        if "payment_mismatch" in flags
    )
    if payment_mismatch_count > 0:
        result.warnings.append(
            "Descuadre entre formas de pago y total_net"
        )

    # Negative stock warnings
    negative_stock_count = sum(
        1 for flags in result.inventory_flags.values()
        if "negative_stock" in flags
    )
    if negative_stock_count > 0:
        result.warnings.append(
            "Stock negativo reportado — posible error de conteo"
        )

    # Zero cost warnings
    zero_cost_count = sum(
        1 for flags in result.inventory_flags.values()
        if "zero_cost" in flags
    )
    if zero_cost_count > 0:
        result.warnings.append(
            f"Costo unitario cero o negativo en {zero_cost_count} insumos"
        )

    # Skipped tickets warning
    if result.skipped_order_ids:
        result.warnings.append(
            f"{len(result.skipped_order_ids)} tickets duplicados ignorados (idempotencia)"
        )

    # Rejected shift audits warning
    if result.rejected_shift_audits:
        result.warnings.append(
            "Evento de turno sin datos de shift — rechazado"
        )

    return result


# ---------------------------------------------------------------------------
# Persistence Layer — Mapeo a tablas de db_schema.md
# Spec: s1b_ingesta_api.md §Mapeo a tablas existentes
# ---------------------------------------------------------------------------

# Tamaño de chunk para batch processing (>500 tickets → procesar en chunks de 100)
_BATCH_CHUNK_SIZE = 100


def _decimal_to_float(value: Decimal) -> float:
    """Convierte Decimal a float para serialización Supabase."""
    return float(value)


def _persist_pos_inputs(
    business_id: UUID,
    date_val: date,
    tickets: list[TicketEvent],
    payments: list[PaymentBreakdown],
    db: Any,
) -> None:
    """
    Agrega todos los tickets en un solo registro pos_inputs por (business_id, date).

    Mapping:
    - total_sales = Σ(total_net de todos los tickets)
    - cash_sales = Σ(PaymentBreakdown.efectivo)
    - card_sales = Σ(PaymentBreakdown.tarjeta_clip)
    - refunds = 0 (no proporcionado por S1B)
    - num_transactions = COUNT(tickets)

    UPSERT: si pos_inputs ya existe para (business_id, date), actualiza totales.
    """
    if not tickets:
        return

    # Indexar payments por order_id
    payments_by_order: dict[str, PaymentBreakdown] = {
        p.order_id: p for p in payments
    }

    total_sales = Decimal("0")
    cash_sales = Decimal("0")
    card_sales = Decimal("0")

    for ticket in tickets:
        total_sales += ticket.total_net
        payment = payments_by_order.get(ticket.order_id)
        if payment:
            cash_sales += payment.efectivo
            card_sales += payment.tarjeta_clip

    row = {
        "business_id": str(business_id),
        "date": date_val.isoformat(),
        "total_sales": _decimal_to_float(total_sales),
        "cash_sales": _decimal_to_float(cash_sales),
        "card_sales": _decimal_to_float(card_sales),
        "refunds": 0,
        "num_transactions": len(tickets),
    }

    try:
        db.table("pos_inputs").upsert(
            row,
            on_conflict="business_id,date",
        ).execute()
    except Exception as exc:
        _logger.error("Error persisting pos_inputs: %s", exc)


def _persist_transactions(
    business_id: UUID,
    tickets: list[TicketEvent],
    payments: list[PaymentBreakdown],
    ticket_flags: dict[str, list[str]],
    rejected_items: dict[str, list[int]],
    db: Any,
) -> int:
    """
    Crea 1 registro en transactions por ticket.

    Cada registro:
    - type = "ingreso"
    - category = "venta"
    - amount = total_net
    - transaction_date = ticket.timestamp.date()
    - raw_metadata incluye: items, order_type, cajero_id, mesero_id,
      sucursal_id, discounts, subtotal, validation flags

    Returns: count of persisted transactions.
    """
    if not tickets:
        return 0

    payments_by_order: dict[str, PaymentBreakdown] = {
        p.order_id: p for p in payments
    }

    persisted = 0

    # Process in chunks if large batch
    for chunk_start in range(0, len(tickets), _BATCH_CHUNK_SIZE):
        chunk = tickets[chunk_start:chunk_start + _BATCH_CHUNK_SIZE]
        rows: list[dict] = []

        for ticket in chunk:
            # Build items list, excluding rejected items
            rejected_indices = rejected_items.get(ticket.order_id, [])
            items_data = []
            for idx, item in enumerate(ticket.items):
                if idx in rejected_indices:
                    continue
                items_data.append({
                    "item_id": item.item_id,
                    "product_name": item.product_name,
                    "group": item.group,
                    "subgroup": item.subgroup,
                    "variant_modifier": item.variant_modifier,
                    "unit_price": _decimal_to_float(item.unit_price),
                    "quantity": item.quantity,
                    "item_discount": _decimal_to_float(item.item_discount),
                })

            # Build raw_metadata
            payment = payments_by_order.get(ticket.order_id)
            raw_metadata: dict[str, Any] = {
                "order_id": ticket.order_id,
                "order_type": ticket.order_type,
                "cajero_id": ticket.cajero_id,
                "mesero_id": ticket.mesero_id,
                "sucursal_id": ticket.sucursal_id,
                "subtotal": _decimal_to_float(ticket.subtotal),
                "tax": _decimal_to_float(ticket.tax),
                "discounts": _decimal_to_float(ticket.discounts),
                "items": items_data,
            }

            # Add payment breakdown if available
            if payment:
                raw_metadata["payment"] = {
                    "efectivo": _decimal_to_float(payment.efectivo),
                    "tarjeta_clip": _decimal_to_float(payment.tarjeta_clip),
                    "uber_eats": _decimal_to_float(payment.uber_eats),
                    "rappi": _decimal_to_float(payment.rappi),
                    "didi_food": _decimal_to_float(payment.didi_food),
                    "cortesia_staff": _decimal_to_float(payment.cortesia_staff),
                    "tarjetas_lealtad": _decimal_to_float(payment.tarjetas_lealtad),
                }

            # Add validation flags if any
            flags = ticket_flags.get(ticket.order_id, [])
            if flags:
                raw_metadata["validation_flags"] = flags

            rows.append({
                "business_id": str(business_id),
                "type": "ingreso",
                "category": "venta",
                "amount": _decimal_to_float(ticket.total_net),
                "tax_amount": _decimal_to_float(ticket.tax),
                "transaction_date": ticket.timestamp.date().isoformat(),
                "document_reference": ticket.order_id,
                "raw_metadata": raw_metadata,
            })

        # Batch insert the chunk
        if rows:
            try:
                db.table("transactions").insert(rows).execute()
                persisted += len(rows)
            except Exception as exc:
                # Per-record fallback: try one by one so one failure doesn't block others
                _logger.warning(
                    "Batch insert failed for %d transactions, falling back to per-record: %s",
                    len(rows), exc,
                )
                for row in rows:
                    try:
                        db.table("transactions").insert(row).execute()
                        persisted += 1
                    except Exception as inner_exc:
                        _logger.error(
                            "Error persisting transaction (order_id=%s): %s",
                            row.get("document_reference"), inner_exc,
                        )

    return persisted


def _persist_shift_audit_events(
    business_id: UUID,
    shift_audits: list[ShiftAuditEvent],
    rejected_indices: list[int],
    db: Any,
) -> int:
    """
    Persiste shift audit events y actualiza cash_counts.

    Por cada ShiftAuditEvent no rechazado:
    - 1 registro en shift_audit_events por cada ShiftData en shifts[]
    - 1 registro en cash_counts por cada ShiftData (apertura → initial_float, cierre_z → actual_counted)

    UPSERT: shift_audit_events por (business_id, date, sucursal_id, turno)

    Returns: count of shift records persisted.
    """
    persisted = 0

    for idx, audit in enumerate(shift_audits):
        # Skip rejected shift audits (regla 6 — shifts vacío)
        if idx in rejected_indices:
            continue

        # Serialize cancellations and clock_records as JSONB
        cancellations_json = [
            {
                "order_id": c.order_id,
                "motivo": c.motivo,
                "responsable": c.responsable,
                "timing": c.timing,
            }
            for c in audit.cancellations
        ]

        clock_records_json = [
            {
                "employee_id": cr.employee_id,
                "clock_in": cr.clock_in.isoformat(),
                "clock_out": cr.clock_out.isoformat() if cr.clock_out else None,
            }
            for cr in audit.clock_records
        ]

        reprints_json = [
            reprint.model_dump(mode="json")
            for reprint in audit.reprints
        ]

        for shift in audit.shifts:
            # --- shift_audit_events: upsert por (business_id, date, sucursal_id, turno) ---
            shift_row = {
                "business_id": str(business_id),
                "sucursal_id": audit.sucursal_id,
                "date": audit.date.isoformat(),
                "turno": shift.turno,
                "apertura": _decimal_to_float(shift.apertura),
                "cierre_x": _decimal_to_float(shift.cierre_x),
                "cierre_z": _decimal_to_float(shift.cierre_z),
                "sobrante_faltante": _decimal_to_float(shift.sobrante_faltante),
                "cancellations": cancellations_json,
                "reprints": reprints_json,
                "clock_records": clock_records_json,
            }

            try:
                db.table("shift_audit_events").upsert(
                    shift_row,
                    on_conflict="business_id,date,sucursal_id,turno",
                ).execute()
                persisted += 1
            except Exception as exc:
                _logger.error(
                    "Error persisting shift_audit_event (turno=%s, date=%s): %s",
                    shift.turno, audit.date, exc,
                )

            # --- cash_counts: upsert por (business_id, date) ---
            # apertura → initial_float, cierre_z → actual_counted
            cash_row = {
                "business_id": str(business_id),
                "date": audit.date.isoformat(),
                "initial_float": _decimal_to_float(shift.apertura),
                "actual_counted": _decimal_to_float(shift.cierre_z),
                "cash_payouts": 0,
                "recorded_by": None,
            }

            try:
                db.table("cash_counts").upsert(
                    cash_row,
                    on_conflict="business_id,date",
                ).execute()
            except Exception as exc:
                _logger.error(
                    "Error persisting cash_counts (date=%s): %s",
                    audit.date, exc,
                )

    return persisted


def _persist_inventory_daily(
    business_id: UUID,
    date_val: date,
    inventory_items: list[InventoryUsageEvent],
    inventory_flags: dict[str, list[str]],
    db: Any,
) -> int:
    """
    Persiste snapshot diario de inventario/costos teóricos.

    1 registro por ingredient por (business_id, date).
    UPSERT por (business_id, date, ingredient_id).

    Returns: count of records persisted.
    """
    if not inventory_items:
        return 0

    persisted = 0

    for item in inventory_items:
        row = {
            "business_id": str(business_id),
            "date": date_val.isoformat(),
            "ingredient_id": item.ingredient_id,
            "ingredient_name": item.ingredient_name,
            "unit": item.unit,
            "consumo_teorico": _decimal_to_float(item.consumo_teorico),
            "waste_recorded": _decimal_to_float(item.waste_recorded),
            "current_stock": _decimal_to_float(item.current_stock),
            "unit_cost": _decimal_to_float(item.unit_cost),
        }

        try:
            db.table("inventory_daily").upsert(
                row,
                on_conflict="business_id,date,ingredient_id",
            ).execute()
            persisted += 1
        except Exception as exc:
            _logger.error(
                "Error persisting inventory_daily (ingredient=%s): %s",
                item.ingredient_id, exc,
            )

    return persisted


def persist_ingestion(
    payload: APIIngestPayload,
    validation: ValidationResult,
    db: Any,
) -> APIIngestResult:
    """
    Orquesta la persistencia del payload validado a todas las tablas destino.

    Flujo:
    1. Si validation.is_rejected → retorna status "rejected" inmediatamente
    2. Filtra tickets válidos (excluye skipped_order_ids por idempotencia)
    3. Persiste a pos_inputs (agregado diario)
    4. Persiste a transactions (1 por ticket)
    5. Persiste a shift_audit_events + cash_counts
    6. Persiste a inventory_daily
    7. Determina status final (success/partial/rejected)

    Args:
        payload: Payload completo validado.
        validation: Resultado de validate_payload().
        db: Supabase client.

    Returns:
        APIIngestResult con conteos y status.
    """
    business_id = payload.business_id
    date_val = payload.date
    sucursal_id = payload.sucursal_id

    # --- Rejected payload: no persistir nada ---
    if validation.is_rejected:
        return APIIngestResult(
            business_id=business_id,
            date=date_val,
            sucursal_id=sucursal_id,
            tickets_received=len(payload.tickets),
            tickets_persisted=0,
            tickets_skipped=0,
            validation_flags=validation.warnings,
            inventory_records=0,
            shift_records=0,
            status="rejected",
        )

    # --- Filter valid tickets (exclude skipped by idempotency) ---
    skipped_ids = set(validation.skipped_order_ids)
    valid_tickets = [
        t for t in payload.tickets if t.order_id not in skipped_ids
    ]

    # --- Filter valid payments (only for valid tickets) ---
    valid_order_ids = {t.order_id for t in valid_tickets}
    valid_payments = [
        p for p in payload.payments if p.order_id in valid_order_ids
    ]

    # --- 1. Persist pos_inputs (aggregate) ---
    _persist_pos_inputs(business_id, date_val, valid_tickets, valid_payments, db)

    # --- 2. Persist transactions (1 per ticket) ---
    tickets_persisted = _persist_transactions(
        business_id,
        valid_tickets,
        valid_payments,
        validation.ticket_flags,
        validation.rejected_items,
        db,
    )

    # --- 3. Persist shift_audit_events + cash_counts ---
    shift_records = _persist_shift_audit_events(
        business_id,
        payload.shift_audit,
        validation.rejected_shift_audits,
        db,
    )

    # --- 4. Persist inventory_daily ---
    inventory_records = _persist_inventory_daily(
        business_id,
        date_val,
        payload.inventory,
        validation.inventory_flags,
        db,
    )

    # --- Determine final status ---
    tickets_received = len(payload.tickets)
    tickets_skipped = len(validation.skipped_order_ids)

    # Collect all validation flags for the response
    all_flags: list[str] = []
    for flags in validation.ticket_flags.values():
        all_flags.extend(flags)
    for flags in validation.inventory_flags.values():
        all_flags.extend(flags)
    # Deduplicate flag names
    unique_flags = list(dict.fromkeys(all_flags))

    # Determine status
    has_rejections = (
        bool(validation.rejected_shift_audits)
        or bool(validation.rejected_items)
        or tickets_skipped > 0
    )

    if tickets_persisted == 0 and inventory_records == 0 and shift_records == 0:
        status: Literal["success", "partial", "rejected"] = "rejected"
    elif has_rejections or unique_flags:
        status = "partial"
    else:
        status = "success"

    return APIIngestResult(
        business_id=business_id,
        date=date_val,
        sucursal_id=sucursal_id,
        tickets_received=tickets_received,
        tickets_persisted=tickets_persisted,
        tickets_skipped=tickets_skipped,
        validation_flags=unique_flags,
        inventory_records=inventory_records,
        shift_records=shift_records,
        status=status,
    )
