"""Regresión del recorrido PDF → registros → métricas, sin DB ni modelos externos."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient
from pdfminer.pdftypes import PDFStream
import pdfplumber
import pytest

from agents.pos_document import extract_document_payloads, ingest_pos_document
from agents.pos_parser import calculate_sha256, extract_pos_data
from agents.calc_engine import run_calc_engine
from agents.gatekeeper import GatekeeperAgent

PDF = Path(__file__).parent / "fixtures/pos_pdfs/pos_detallado_demo.pdf"
BIZ = "00000000-0000-4000-8000-000000000061"
DAY = "2026-11-03"


class Query:
    def __init__(self, db, table):
        self.db, self.table = db, table
        self.filters = []
        self.action = "select"
        self.values = None
        self.conflict = "id"
        self.one = False
        self.inverse = False

    def select(self, _columns):
        return self

    def eq(self, field, value):
        self.filters.append(lambda row: row.get(field) == value)
        return self

    def gte(self, field, value):
        self.filters.append(lambda row: row.get(field, "") >= value)
        return self

    def lte(self, field, value):
        self.filters.append(lambda row: row.get(field, "") <= value)
        return self

    @property
    def not_(self):
        self.inverse = True
        return self

    def is_(self, field, value):
        assert value == "null"
        inverse = self.inverse
        self.filters.append(lambda row: (row.get(field) is None) != inverse)
        self.inverse = False
        return self

    def single(self):
        self.one = True
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, _limit):
        return self

    def insert(self, values):
        self.action, self.values = "insert", values
        return self

    def upsert(self, values, on_conflict="id"):
        self.action, self.values, self.conflict = "upsert", values, on_conflict
        return self

    def update(self, values):
        self.action, self.values = "update", values
        return self

    def execute(self):
        rows = self.db.rows.setdefault(self.table, [])
        selected = [row for row in rows if all(check(row) for check in self.filters)]
        if self.action == "select":
            return SimpleNamespace(data=deepcopy(selected[0] if self.one and selected else selected))
        if self.db.fail_table == self.table:
            self.db.fail_table = None
            raise RuntimeError("simulated write failure")
        values = self.values if isinstance(self.values, list) else [self.values]
        for value in values:
            if self.action == "update":
                for row in selected:
                    row.update(deepcopy(value))
                continue
            keys = self.conflict.split(",")
            matches = [row for row in rows if all(row.get(key) == value.get(key) for key in keys)]
            if self.action == "upsert" and matches:
                matches[0].update(deepcopy(value))
            else:
                rows.append({"id": str(uuid4()), **deepcopy(value)})
        return SimpleNamespace(data=deepcopy(rows))


class DB:
    def __init__(self):
        self.rows = {"businesses": [{"id": BIZ}], "documents": [], "transactions": []}
        self.fail_table = None

    def table(self, name):
        return Query(self, name)

    def rpc(self, name, params):
        assert name == "upsert_pos_daily"
        return self.table("pos_inputs").upsert(params["p_record"], on_conflict="business_id,date")


@pytest.fixture
def setup(monkeypatch):
    from api import main
    db = DB()
    monkeypatch.setattr(main, "get_supabase", lambda: db)
    uploads = []

    def upload(_db, path, blob, **_options):
        uploads.append((path, len(blob)))
        return path

    monkeypatch.setattr(main, "_upload_to_storage", upload)
    return TestClient(main.app), db, uploads


def send(client, business=BIZ):
    return client.post("/ingest/pos", data={"business_id": business},
                       files={"file": ("pos.pdf", PDF.read_bytes(), "application/pdf")})


def test_real_pdf_imports_only_visible_date_and_selected_business():
    payloads = extract_document_payloads(PDF.read_bytes(), BIZ)
    assert len(payloads) == 1
    payload = payloads[0]
    assert str(payload.business_id) == BIZ and payload.date.isoformat() == DAY
    assert len(payload.tickets) == len(payload.payments) == 15
    assert sum(len(audit.shifts) for audit in payload.shift_audit) == 1
    assert all(item.quantity == 1 for ticket in payload.tickets for item in ticket.items)
    assert extract_pos_data(PDF.read_bytes())[0].line_items is None


def test_upload_entrypoint_produces_metrics_and_retries_without_duplicates(setup):
    client, db, uploads = setup
    response = send(client)
    assert response.status_code == 200, response.text
    data = response.json()[0]
    assert data["detailed_import"] == {"version": 1, "status": "complete", "tickets": 15, "shifts": 1, "inventory": 1}
    assert data["payment_methods"]["other"] == "895.00"
    assert len(db.rows["transactions"]) == 15
    assert all(row["document_id"] == data["file_id"] for row in db.rows["transactions"])
    assert len(db.rows["cash_counts"]) == len(db.rows["inventory_daily"]) == 1
    assert {row["date"] for row in db.rows["pos_inputs"]} == {DAY}
    result = GatekeeperAgent(db).get_status(BIZ, DAY)
    assert {"cash_reconciliation", "avg_ticket", "ticket_volume", "hourly_sales_pattern", "waste_cost"} <= set(result.active_metrics)
    calculations = run_calc_engine(result, db, DAY, BIZ)
    by_metric = {item.metric: item for item in calculations.results}
    assert by_metric["conciliacion_caja"].value == -180
    assert by_metric["ticket_promedio"].value == 120
    assert by_metric["volumen_tickets"].value == 15
    assert by_metric["waste_cost"].value == 8
    assert by_metric["payment_mix"].status == "ok"
    assert by_metric["loyalty_redemption_cost"].value == 15
    assert by_metric["patron_horario_ventas"].status != "incomplete_data"
    assert len([item for item in calculations.results if item.value is not None]) == 22
    repeat = send(client)
    assert repeat.status_code == 200
    assert repeat.json()[0]["file_id"] == data["file_id"]
    assert len(db.rows["transactions"]) == 15 and len(db.rows["documents"]) == len(uploads) == 1
    assert db.rows["pos_inputs"][0]["num_transactions"] == 15


def test_previously_uploaded_summary_is_completed_in_place(setup):
    client, db, uploads = setup
    doc_id = str(uuid4())
    db.rows["documents"].append({"id": doc_id, "business_id": BIZ, "storage_path": "saved.pdf",
        "ocr_status": "processed", "needs_human_review": False,
        "extracted_data": {"sha256": calculate_sha256(PDF.read_bytes()), "date": DAY}})
    db.rows["pos_inputs"] = [{"business_id": BIZ, "date": DAY, "total_sales": 2058, "cash_sales": 492, "card_sales": 671}]
    response = send(client)
    assert response.status_code == 200, response.text
    assert response.json()[0]["file_id"] == doc_id
    assert len(db.rows["documents"]) == len(db.rows["pos_inputs"]) == 1
    assert len(db.rows["transactions"]) == 15 and uploads == []


@pytest.mark.parametrize("table", ["transactions", "shift_audit_events", "cash_counts", "inventory_daily"])
def test_interrupted_import_blocks_analysis_and_resumes(setup, table):
    client, db, _uploads = setup
    db.fail_table = table
    response = send(client)
    assert response.status_code == 503
    doc = db.rows["documents"][0]
    assert doc["needs_human_review"] is True
    assert doc["extracted_data"]["detailed_import"]["status"] == "pending"
    review = client.patch(f"/ingest/pos/{doc['id']}/review", json={"date": DAY, "totals": {}})
    assert review.status_code == 409
    response = send(client)
    assert response.status_code == 200, response.text
    assert len(db.rows["transactions"]) == 15
    assert db.rows["documents"][0]["needs_human_review"] is False


def test_failed_metric_refresh_is_retried(setup):
    client, db, _uploads = setup
    db.fail_table = "metric_status"
    assert send(client).status_code == 503
    assert send(client).status_code == 200
    assert len(GatekeeperAgent(db).get_status(BIZ, DAY).active_metrics) >= 19


def test_matching_manual_count_keeps_its_author(setup):
    client, db, _uploads = setup
    db.rows["cash_counts"] = [{"business_id": BIZ, "date": DAY, "initial_float": 300,
                              "actual_counted": 612, "cash_payouts": 0, "recorded_by": "manual-user"}]
    assert send(client).status_code == 200
    assert db.rows["cash_counts"][0]["recorded_by"] == "manual-user"


def test_conventional_pdf_keeps_summary_flow(setup):
    client, db, _uploads = setup
    conventional = PDF.with_name("pos_ticket_01_20240115.pdf").read_bytes()
    response = client.post("/ingest/pos", data={"business_id": BIZ},
                           files={"file": ("ticket.pdf", conventional, "application/pdf")})
    assert response.status_code == 200, response.text
    assert response.json()[0]["date"] == "2024-01-15"
    assert response.json()[0]["detailed_import"] is None
    assert len(db.rows["pos_inputs"]) == 1 and not db.rows["transactions"]


def test_existing_cash_count_is_preserved_on_conflict(setup):
    client, db, uploads = setup
    db.rows["cash_counts"] = [{"business_id": BIZ, "date": DAY, "initial_float": 300,
                              "actual_counted": 999, "cash_payouts": 0}]
    response = send(client)
    assert response.status_code == 409
    assert db.rows["cash_counts"][0]["actual_counted"] == 999
    assert not db.rows["documents"] and not db.rows["transactions"] and not uploads


def test_storage_failure_does_not_import_unarchived_data(setup, monkeypatch):
    from api import main
    client, db, _uploads = setup
    monkeypatch.setattr(main, "_upload_to_storage", lambda *_args, **_kwargs: "local/missing.pdf")
    assert send(client).status_code == 503
    assert not db.rows["documents"] and not db.rows["transactions"]


def test_parallel_retries_do_not_duplicate_data():
    db = DB()
    blob = PDF.read_bytes()
    payloads = extract_document_payloads(blob, BIZ)
    def run(_index):
        return ingest_pos_document(db, blob, BIZ, "pos.pdf", payloads, lambda *_args: "saved.pdf")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, range(2)))
    assert results[0][0]["file_id"] == results[1][0]["file_id"]
    assert len(db.rows["transactions"]) == 15 and len(db.rows["documents"]) == 1


@pytest.mark.parametrize("problem", ["payments", "duplicate", "date", "tax", "totals"])
def test_invalid_detail_is_rejected_before_writes(setup, monkeypatch, problem):
    client, db, uploads = setup
    payload = extract_document_payloads(PDF.read_bytes(), BIZ)[0].model_dump(mode="json")
    if problem == "payments":
        payload["payments"] = []
    elif problem == "duplicate":
        payload["tickets"][1]["order_id"] = payload["tickets"][0]["order_id"]
    elif problem == "date":
        payload["tickets"][0]["timestamp"] = "2026-11-04T12:30:00-06:00"
    elif problem == "tax":
        payload["tickets"][0]["tax"] = "999"
    else:
        payload["tickets"][0].update(subtotal="91", tax="14.56", total_net="95.56")
        payload["payments"][0]["efectivo"] = "95.56"
    original_open = pdfplumber.open
    def modified_pdf(*args, **kwargs):
        pdf = original_open(*args, **kwargs)
        stream = PDFStream({}, json.dumps(payload).encode())
        pdf.doc.catalog["Names"] = {"EmbeddedFiles": {"Names": [b"pos.json", {"EF": {"F": stream}}]}}
        return pdf
    monkeypatch.setattr(pdfplumber, "open", modified_pdf)
    assert send(client).status_code == 422
    assert not db.rows["documents"] and not db.rows["transactions"] and not uploads
