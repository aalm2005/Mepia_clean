"""
Tests for the persistence layer in agents/api_ingest.py (Task 1.3).
Validates mapping from validated API payload to database tables with upsert/idempotency.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, call, patch
from uuid import uuid4

import pytest

from agents.api_ingest import (
    APIIngestPayload,
    APIIngestResult,
    CancellationRecord,
    ClockRecord,
    InventoryUsageEvent,
    PaymentBreakdown,
    ProductLine,
    ReprintRecord,
    ShiftAuditEvent,
    ShiftData,
    TicketEvent,
    ValidationResult,
    _persist_inventory_daily,
    _persist_pos_inputs,
    _persist_shift_audit_events,
    _persist_transactions,
    persist_ingestion,
    POSPersistenceError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_item(item_id: str = "P1", quantity: int = 1) -> ProductLine:
    return ProductLine(
        item_id=item_id,
        product_name="Cafe Latte",
        group="Bebidas calientes",
        subgroup="Espresso",
        unit_price=Decimal("50.00"),
        quantity=quantity,
    )


def _make_ticket(
    order_id: str = "T-001",
    subtotal: Decimal = Decimal("100.00"),
    tax: Decimal = Decimal("16.00"),
    discounts: Decimal = Decimal("0"),
    total_net: Decimal | None = None,
) -> TicketEvent:
    if total_net is None:
        total_net = subtotal + tax - discounts
    return TicketEvent(
        order_id=order_id,
        timestamp=datetime(2024, 6, 15, 10, 30, 0),
        sucursal_id="SUC-01",
        cajero_id="CAJ-01",
        mesero_id="MES-01",
        order_type="Comedor",
        subtotal=subtotal,
        tax=tax,
        discounts=discounts,
        total_net=total_net,
        items=[_make_item()],
    )


def _make_payment(order_id: str = "T-001", efectivo: Decimal = Decimal("116.00")) -> PaymentBreakdown:
    return PaymentBreakdown(order_id=order_id, efectivo=efectivo)


def _make_shift_audit(
    date_val: date = date(2024, 6, 15),
    turno: str = "matutino",
) -> ShiftAuditEvent:
    return ShiftAuditEvent(
        sucursal_id="SUC-01",
        date=date_val,
        cancellations=[
            CancellationRecord(
                order_id="T-999",
                motivo="Error de captura",
                responsable="CAJ-01",
                timing="pre_comanda",
            )
        ],
        reprints=[
            ReprintRecord(
                order_id="T-101",
                responsable="CAJ-01",
                hora="11:30",
            ),
            ReprintRecord(
                order_id="T-102",
                responsable="CAJ-02",
                hora="12:15",
            ),
        ],
        shifts=[
            ShiftData(
                turno=turno,
                apertura=Decimal("1000.00"),
                cierre_x=Decimal("5000.00"),
                cierre_z=Decimal("5200.00"),
                sobrante_faltante=Decimal("200.00"),
            )
        ],
        clock_records=[
            ClockRecord(
                employee_id="EMP-01",
                clock_in=datetime(2024, 6, 15, 7, 0, 0),
                clock_out=datetime(2024, 6, 15, 15, 0, 0),
            )
        ],
    )


def _make_inventory(ingredient_id: str = "ING-001") -> InventoryUsageEvent:
    return InventoryUsageEvent(
        ingredient_id=ingredient_id,
        ingredient_name="Café en grano",
        unit="g",
        consumo_teorico=Decimal("500.00"),
        waste_recorded=Decimal("20.00"),
        current_stock=Decimal("5000.00"),
        unit_cost=Decimal("0.85"),
    )


def _mock_db():
    """Creates a mock Supabase client with chained method support."""
    db = MagicMock()
    # Setup chained calls: db.table("x").upsert({}).execute()
    table_mock = MagicMock()
    table_mock.upsert.return_value = table_mock
    table_mock.insert.return_value = table_mock
    table_mock.execute.return_value = MagicMock(data=[{"id": "test-id"}])
    db.table.return_value = table_mock
    return db


# ---------------------------------------------------------------------------
# Tests: _persist_pos_inputs
# ---------------------------------------------------------------------------

class TestPersistPosInputs:
    def test_aggregates_tickets_correctly(self):
        db = _mock_db()
        business_id = uuid4()
        date_val = date(2024, 6, 15)

        tickets = [
            _make_ticket("T-001", total_net=Decimal("116.00")),
            _make_ticket("T-002", total_net=Decimal("200.00")),
        ]
        payments = [
            _make_payment("T-001", efectivo=Decimal("116.00")),
            PaymentBreakdown(order_id="T-002", tarjeta_clip=Decimal("200.00")),
        ]

        _persist_pos_inputs(business_id, date_val, tickets, payments, db)

        assert db.rpc.call_args[0][0] == "upsert_pos_daily"
        row = db.rpc.call_args[0][1]["p_record"]

        assert row["total_sales"] == 316.0  # 116 + 200
        assert row["cash_sales"] == 116.0
        assert row["card_sales"] == 200.0
        assert row["num_transactions"] == 2
        assert row["refunds"] == 0
        assert row["business_id"] == str(business_id)
        assert row["date"] == "2024-06-15"

    def test_empty_tickets_no_db_call(self):
        db = _mock_db()
        _persist_pos_inputs(uuid4(), date(2024, 6, 15), [], [], db)
        db.table.assert_not_called()
        db.rpc.assert_not_called()

    def test_persistence_failure_stops_before_other_tables(self):
        db = _mock_db()
        db.rpc.return_value.execute.side_effect = RuntimeError("private storage detail")
        with pytest.raises(POSPersistenceError, match="unavailable"):
            _persist_pos_inputs(uuid4(), date(2024, 6, 15), [_make_ticket()], [_make_payment()], db)
        db.table.assert_not_called()

    def test_ambiguous_legacy_date_is_a_safe_conflict(self):
        db = _mock_db()
        error = RuntimeError("private detail")
        error.message = "MEPIA_POS_DATE_AMBIGUOUS"
        db.rpc.return_value.execute.side_effect = error
        with pytest.raises(POSPersistenceError, match="conflict"):
            _persist_pos_inputs(uuid4(), date(2024, 6, 15), [_make_ticket()], [_make_payment()], db)
        db.table.assert_not_called()

    def test_failed_daily_total_prevents_transactions_shifts_and_inventory(self):
        db = _mock_db()
        db.rpc.return_value.execute.side_effect = RuntimeError("private failure")
        payload = APIIngestPayload(business_id=uuid4(), date=date(2024, 6, 15),
            sucursal_id="SUC-01", tickets=[_make_ticket()], payments=[_make_payment()],
            shift_audit=[_make_shift_audit()], inventory=[_make_inventory()])
        with pytest.raises(POSPersistenceError, match="unavailable"):
            persist_ingestion(payload, ValidationResult(), db)
        db.table.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: _persist_transactions
# ---------------------------------------------------------------------------

class TestPersistTransactions:
    def test_creates_one_transaction_per_ticket(self):
        db = _mock_db()
        business_id = uuid4()
        tickets = [_make_ticket("T-001"), _make_ticket("T-002")]
        payments = [_make_payment("T-001"), _make_payment("T-002")]

        count = _persist_transactions(business_id, tickets, payments, {}, {}, db)

        assert count == 2
        insert_call = db.table.return_value.insert.call_args
        rows = insert_call[0][0]
        assert len(rows) == 2
        assert all(r["type"] == "ingreso" for r in rows)
        assert all(r["category"] == "venta" for r in rows)

    def test_includes_validation_flags_in_metadata(self):
        db = _mock_db()
        business_id = uuid4()
        tickets = [_make_ticket("T-001")]
        payments = [_make_payment("T-001")]
        flags = {"T-001": ["tax_mismatch", "payment_mismatch"]}

        _persist_transactions(business_id, tickets, payments, flags, {}, db)

        insert_call = db.table.return_value.insert.call_args
        rows = insert_call[0][0]
        assert rows[0]["raw_metadata"]["validation_flags"] == ["tax_mismatch", "payment_mismatch"]

    def test_excludes_rejected_items_from_metadata(self):
        db = _mock_db()
        business_id = uuid4()
        ticket = _make_ticket("T-001")
        ticket.items = [_make_item("P1"), _make_item("P2"), _make_item("P3")]
        payments = [_make_payment("T-001")]
        rejected = {"T-001": [1]}  # P2 rejected

        _persist_transactions(business_id, [ticket], payments, {}, rejected, db)

        insert_call = db.table.return_value.insert.call_args
        rows = insert_call[0][0]
        items = rows[0]["raw_metadata"]["items"]
        assert len(items) == 2
        assert items[0]["item_id"] == "P1"
        assert items[1]["item_id"] == "P3"

    def test_empty_tickets_returns_zero(self):
        db = _mock_db()
        count = _persist_transactions(uuid4(), [], [], {}, {}, db)
        assert count == 0

    def test_transaction_has_correct_amount(self):
        db = _mock_db()
        ticket = _make_ticket("T-001", total_net=Decimal("250.50"))

        _persist_transactions(uuid4(), [ticket], [], {}, {}, db)

        insert_call = db.table.return_value.insert.call_args
        rows = insert_call[0][0]
        assert rows[0]["amount"] == 250.50


# ---------------------------------------------------------------------------
# Tests: _persist_shift_audit_events
# ---------------------------------------------------------------------------

class TestPersistShiftAuditEvents:
    def test_persists_one_record_per_shift(self):
        db = _mock_db()
        business_id = uuid4()
        audits = [_make_shift_audit()]

        count = _persist_shift_audit_events(business_id, audits, [], db)

        assert count == 1
        # Verify shift_audit_events upsert was called
        calls = db.table.call_args_list
        table_names = [c[0][0] for c in calls]
        assert "shift_audit_events" in table_names
        assert "cash_counts" in table_names

    def test_skips_rejected_indices(self):
        db = _mock_db()
        business_id = uuid4()
        audits = [_make_shift_audit(), _make_shift_audit(turno="vespertino")]

        count = _persist_shift_audit_events(business_id, audits, [0], db)

        # Only the second audit (index 1) should be persisted
        assert count == 1

    def test_cash_counts_maps_apertura_and_cierre(self):
        db = _mock_db()
        business_id = uuid4()
        audits = [_make_shift_audit()]

        _persist_shift_audit_events(business_id, audits, [], db)

        # Find the cash_counts upsert call
        cash_calls = [
            c for c in db.table.call_args_list
            if c[0][0] == "cash_counts"
        ]
        assert len(cash_calls) > 0

    def test_upsert_on_correct_conflict_key(self):
        db = _mock_db()
        audits = [_make_shift_audit()]

        _persist_shift_audit_events(uuid4(), audits, [], db)

        upsert_calls = db.table.return_value.upsert.call_args_list
        # First upsert should be shift_audit_events
        first_upsert = upsert_calls[0]
        assert first_upsert[1]["on_conflict"] == "business_id,date,sucursal_id,turno"

    def test_serializes_cancellations_and_clock_records(self):
        db = _mock_db()
        audits = [_make_shift_audit()]

        _persist_shift_audit_events(uuid4(), audits, [], db)

        upsert_call = db.table.return_value.upsert.call_args_list[0]
        row = upsert_call[0][0]
        assert isinstance(row["cancellations"], list)
        assert row["cancellations"][0]["order_id"] == "T-999"
        assert isinstance(row["reprints"], list)
        assert row["reprints"][0] == {
            "order_id": "T-101",
            "responsable": "CAJ-01",
            "hora": "11:30",
        }
        assert isinstance(row["clock_records"], list)
        assert row["clock_records"][0]["employee_id"] == "EMP-01"


# ---------------------------------------------------------------------------
# Tests: _persist_inventory_daily
# ---------------------------------------------------------------------------

class TestPersistInventoryDaily:
    def test_persists_one_record_per_ingredient(self):
        db = _mock_db()
        business_id = uuid4()
        items = [_make_inventory("ING-001"), _make_inventory("ING-002")]

        count = _persist_inventory_daily(business_id, date(2024, 6, 15), items, {}, db)

        assert count == 2

    def test_upsert_on_correct_conflict_key(self):
        db = _mock_db()
        items = [_make_inventory()]

        _persist_inventory_daily(uuid4(), date(2024, 6, 15), items, {}, db)

        upsert_call = db.table.return_value.upsert.call_args
        assert upsert_call[1]["on_conflict"] == "business_id,date,ingredient_id"

    def test_empty_items_returns_zero(self):
        db = _mock_db()
        count = _persist_inventory_daily(uuid4(), date(2024, 6, 15), [], {}, db)
        assert count == 0

    def test_maps_all_fields_correctly(self):
        db = _mock_db()
        items = [_make_inventory()]

        _persist_inventory_daily(uuid4(), date(2024, 6, 15), items, {}, db)

        upsert_call = db.table.return_value.upsert.call_args
        row = upsert_call[0][0]
        assert row["ingredient_id"] == "ING-001"
        assert row["ingredient_name"] == "Café en grano"
        assert row["unit"] == "g"
        assert row["consumo_teorico"] == 500.0
        assert row["waste_recorded"] == 20.0
        assert row["current_stock"] == 5000.0
        assert row["unit_cost"] == 0.85


# ---------------------------------------------------------------------------
# Tests: persist_ingestion (orchestrator)
# ---------------------------------------------------------------------------

class TestPersistIngestion:
    def test_rejected_payload_returns_immediately(self):
        db = _mock_db()
        payload = APIIngestPayload(
            business_id=uuid4(),
            date=date(2024, 6, 15),
            sucursal_id="SUC-01",
            tickets=[_make_ticket()],
            payments=[_make_payment()],
            shift_audit=[],
            inventory=[],
        )
        validation = ValidationResult(
            is_rejected=True,
            reject_reason="date in future",
        )

        result = persist_ingestion(payload, validation, db)

        assert result.status == "rejected"
        assert result.tickets_persisted == 0
        assert result.tickets_received == 1
        db.table.assert_not_called()

    def test_skips_idempotent_order_ids(self):
        db = _mock_db()
        payload = APIIngestPayload(
            business_id=uuid4(),
            date=date(2024, 6, 15),
            sucursal_id="SUC-01",
            tickets=[_make_ticket("T-001"), _make_ticket("T-002")],
            payments=[_make_payment("T-001"), _make_payment("T-002")],
            shift_audit=[],
            inventory=[],
        )
        validation = ValidationResult(
            skipped_order_ids=["T-001"],  # T-001 already exists
        )

        result = persist_ingestion(payload, validation, db)

        assert result.tickets_skipped == 1
        assert result.tickets_received == 2
        # Only T-002 should be persisted
        assert result.tickets_persisted == 1

    def test_success_status_when_no_issues(self):
        db = _mock_db()
        payload = APIIngestPayload(
            business_id=uuid4(),
            date=date(2024, 6, 15),
            sucursal_id="SUC-01",
            tickets=[_make_ticket()],
            payments=[_make_payment()],
            shift_audit=[],
            inventory=[],
        )
        validation = ValidationResult()

        result = persist_ingestion(payload, validation, db)

        assert result.status == "success"
        assert result.tickets_persisted == 1
        assert result.tickets_skipped == 0

    def test_partial_status_with_validation_flags(self):
        db = _mock_db()
        payload = APIIngestPayload(
            business_id=uuid4(),
            date=date(2024, 6, 15),
            sucursal_id="SUC-01",
            tickets=[_make_ticket()],
            payments=[_make_payment()],
            shift_audit=[],
            inventory=[],
        )
        validation = ValidationResult(
            ticket_flags={"T-001": ["tax_mismatch"]},
        )

        result = persist_ingestion(payload, validation, db)

        assert result.status == "partial"
        assert "tax_mismatch" in result.validation_flags

    def test_full_pipeline_with_all_data(self):
        db = _mock_db()
        business_id = uuid4()
        payload = APIIngestPayload(
            business_id=business_id,
            date=date(2024, 6, 15),
            sucursal_id="SUC-01",
            tickets=[_make_ticket("T-001"), _make_ticket("T-002")],
            payments=[_make_payment("T-001"), _make_payment("T-002")],
            shift_audit=[_make_shift_audit()],
            inventory=[_make_inventory("ING-001"), _make_inventory("ING-002")],
        )
        validation = ValidationResult()

        result = persist_ingestion(payload, validation, db)

        assert result.status == "success"
        assert result.tickets_persisted == 2
        assert result.tickets_skipped == 0
        assert result.shift_records == 1
        assert result.inventory_records == 2
        assert result.business_id == business_id
        assert result.date == date(2024, 6, 15)
        assert result.sucursal_id == "SUC-01"

    def test_rejected_status_when_nothing_persists(self):
        db = _mock_db()
        # Simulate all inserts failing
        db.table.return_value.insert.return_value.execute.side_effect = Exception("DB error")
        db.table.return_value.upsert.return_value.execute.side_effect = Exception("DB error")

        payload = APIIngestPayload(
            business_id=uuid4(),
            date=date(2024, 6, 15),
            sucursal_id="SUC-01",
            tickets=[_make_ticket()],
            payments=[_make_payment()],
            shift_audit=[],
            inventory=[],
        )
        validation = ValidationResult()

        result = persist_ingestion(payload, validation, db)

        # pos_inputs fails, transactions fail → 0 persisted
        assert result.tickets_persisted == 0
        assert result.status == "rejected"
