"""Importación determinista de datos POS incluidos como adjuntos JSON en un PDF."""
import io
import json
from datetime import datetime, timezone
from decimal import Decimal
from threading import Lock
from uuid import UUID, NAMESPACE_URL, uuid5

import pdfplumber
from pdfminer.pdftypes import resolve1
from pydantic import ValidationError

from agents.api_ingest import (
    APIIngestPayload, POSPersistenceError, validate_payload,
    _persist_inventory_daily, _persist_pos_inputs,
    _persist_shift_audit_events, _persist_transactions,
)
from agents.gatekeeper import GatekeeperAgent
from agents.pos_parser import calculate_sha256, extract_pos_data

_IMPORT_LOCK = Lock()
_VERSION = 1


class POSDocumentConflict(ValueError):
    """Los datos existentes no permiten completar esta importación sin reemplazarlos."""


def extract_document_payloads(pdf_bytes: bytes, business_id: str) -> list[APIIngestPayload]:
    """Solo importa días visibles y usa el negocio elegido, nunca el del adjunto."""
    UUID(business_id)
    candidates = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        names = resolve1(pdf.doc.catalog.get("Names", {}))
        pending = [resolve1(names.get("EmbeddedFiles", {}))]
        visited = 0
        while pending:
            visited += 1
            if visited > 64:
                raise ValueError("El PDF contiene demasiados adjuntos.")
            node = resolve1(pending.pop())
            pending.extend(resolve1(node.get("Kids", [])))
            entries = resolve1(node.get("Names", []))
            for name, reference in zip(entries[::2], entries[1::2]):
                filename = name.decode("latin-1") if isinstance(name, bytes) else str(name)
                if not filename.lower().endswith(".json"):
                    continue
                spec = resolve1(reference)
                files = resolve1(spec.get("EF", {}))
                stream = resolve1(files.get("UF", files.get("F")))
                if stream is None:
                    continue
                raw = stream.get_data()
                if len(raw) > 5 * 1024 * 1024:
                    raise ValueError("Un adjunto POS supera el límite de 5 MB.")
                try:
                    data = json.loads(raw)
                except (ValueError, UnicodeError):
                    raise ValueError("Un adjunto JSON del PDF no es válido.") from None
                if isinstance(data, dict) and "tickets" in data:
                    candidates.append(data)
    if not candidates:
        return []

    visible = {result.date: result for result in extract_pos_data(pdf_bytes) if result.date}
    payloads = []
    for data in candidates:
        try:
            payload = APIIngestPayload.model_validate({**data, "business_id": business_id})
        except ValidationError:
            raise ValueError("El detalle POS del PDF tiene campos incompletos o inválidos.") from None
        if payload.date not in visible:
            continue
        _validate_document_payload(payload)
        if len(visible) == 1:
            totals = visible[payload.date].totals
            cash = sum((p.efectivo for p in payload.payments), Decimal(0))
            card = sum((p.tarjeta_clip for p in payload.payments), Decimal(0))
            total = sum((t.total_net for t in payload.tickets), Decimal(0))
            if totals is None or (total, cash, card) != (totals.total, totals.cash, totals.card):
                raise ValueError("El detalle POS no coincide con los totales visibles del PDF.")
        payloads.append(payload)
    if not payloads:
        raise ValueError("Las fechas de los datos POS no coinciden con las fechas visibles del PDF.")
    if len({payload.date for payload in payloads}) != len(payloads):
        raise ValueError("El PDF contiene más de un reporte POS para la misma fecha.")
    return payloads


def _validate_document_payload(payload: APIIngestPayload) -> None:
    orders = [ticket.order_id for ticket in payload.tickets]
    payments = [payment.order_id for payment in payload.payments]
    if not orders or len(orders) > 10000 or len(set(orders)) != len(orders):
        raise ValueError("El detalle POS debe contener tickets únicos, hasta un máximo de 10,000.")
    if len(set(payments)) != len(payments) or set(payments) != set(orders):
        raise ValueError("Cada ticket debe tener un desglose de pagos único.")
    if any(ticket.timestamp.date() != payload.date or ticket.sucursal_id != payload.sucursal_id
           for ticket in payload.tickets):
        raise ValueError("Los tickets deben corresponder al día y la sucursal del reporte.")
    if any(audit.date != payload.date or audit.sucursal_id != payload.sucursal_id
           for audit in payload.shift_audit):
        raise ValueError("Los turnos deben corresponder al día y la sucursal del reporte.")
    turns = [shift.turno for audit in payload.shift_audit for shift in audit.shifts]
    ingredients = [item.ingredient_id for item in payload.inventory]
    if len(set(turns)) != len(turns) or len(set(ingredients)) != len(ingredients):
        raise ValueError("El reporte contiene turnos o insumos duplicados.")
    validation = validate_payload(payload, set())
    if (validation.is_rejected or validation.ticket_flags or validation.rejected_items
            or validation.rejected_shift_audits or validation.inventory_flags):
        raise ValueError("El detalle POS contiene inconsistencias de fecha, importes, turnos o inventario.")


def _assert_compatible(db, payload: APIIngestPayload, document_id: str) -> tuple[set[str], bool]:
    """Evita reemplazar conteos, ventas o capturas previas que no coincidan."""
    business_id, day = str(payload.business_id), payload.date.isoformat()
    rows = (db.table("transactions").select("document_id,amount,raw_metadata")
            .eq("business_id", business_id).eq("transaction_date", day)
            .eq("type", "ingreso").eq("category", "venta").execute()).data or []
    incoming = {ticket.order_id: ticket for ticket in payload.tickets}
    skipped = set()
    existing_orders = [(row.get("raw_metadata") or {}).get("order_id") for row in rows]
    if len(set(existing_orders)) != len(existing_orders):
        raise POSDocumentConflict("Hay tickets duplicados para esa fecha. Revisa las ventas existentes.")
    for row in rows:
        metadata = row.get("raw_metadata") or {}
        ticket = incoming.get(metadata.get("order_id"))
        if ticket is None or Decimal(str(row["amount"])) != ticket.total_net:
            raise POSDocumentConflict("Ya hay otras ventas para esa fecha. Revisa el reporte antes de reemplazarlas.")
        if metadata.get("sucursal_id") != ticket.sucursal_id:
            raise POSDocumentConflict("Un ticket existente pertenece a otra sucursal.")
        if any(Decimal(str(metadata.get(key, 0))) != getattr(ticket, key)
               for key in ("subtotal", "tax", "discounts")):
            raise POSDocumentConflict("El desglose de un ticket existente es diferente al del PDF.")
        if row.get("document_id") != document_id:
            skipped.add(ticket.order_id)

    totals = {"total_sales": sum((t.total_net for t in payload.tickets), Decimal(0)),
              "cash_sales": sum((p.efectivo for p in payload.payments), Decimal(0)),
              "card_sales": sum((p.tarjeta_clip for p in payload.payments), Decimal(0))}
    daily = (db.table("pos_inputs").select("total_sales,cash_sales,card_sales,refunds")
             .eq("business_id", business_id).eq("date", day).execute()).data or []
    if (len(daily) > 1
            or any(any(Decimal(str(row[key])) != value for key, value in totals.items()) for row in daily)
            or any(Decimal(str(row.get("refunds") or 0)) != 0 for row in daily)):
        raise POSDocumentConflict("Los totales existentes no coinciden con este reporte. Revisa la fecha y las ventas.")

    shifts = [shift for audit in payload.shift_audit for shift in audit.shifts]
    counts = []
    if len(shifts) == 1:
        counts = (db.table("cash_counts").select("initial_float,actual_counted,cash_payouts")
                  .eq("business_id", business_id).eq("date", day).execute()).data or []
        if any(Decimal(str(row["initial_float"])) != shifts[0].apertura
               or Decimal(str(row["actual_counted"])) != shifts[0].cierre_z
               or Decimal(str(row.get("cash_payouts") or 0)) != 0 for row in counts):
            raise POSDocumentConflict("Ya existe un conteo de caja diferente para esa fecha.")
    return skipped, bool(counts)


def _extracted_data(payload: APIIngestPayload, sha: str) -> dict:
    cash = sum((p.efectivo for p in payload.payments), Decimal(0))
    card = sum((p.tarjeta_clip for p in payload.payments), Decimal(0))
    total = sum((ticket.total_net for ticket in payload.tickets), Decimal(0))
    return {
        "sha256": sha, "date": payload.date.isoformat(),
        "totals": {"cash": str(cash), "card": str(card), "total": str(total)},
        "payment_methods": {"cash": str(cash), "card": str(card), "other": str(total - cash - card)},
        "line_items": [{"description": item.product_name, "quantity": item.quantity,
                        "unit_price": str(item.unit_price)} for ticket in payload.tickets for item in ticket.items],
        "ocr_confidence": {"totals": 1.0, "payment_methods": 1.0, "line_items": 1.0},
        "missing_fields": None,
        "detailed_import": {"version": _VERSION, "status": "pending", "tickets": len(payload.tickets),
                            "shifts": sum(len(audit.shifts) for audit in payload.shift_audit),
                            "inventory": len(payload.inventory)},
    }


def ingest_pos_document(db, pdf_bytes: bytes, business_id: str, filename: str,
                        payloads: list[APIIngestPayload], upload) -> list[dict]:
    """Reintentos idempotentes; el documento permanece bloqueado hasta completar todas las tablas."""
    with _IMPORT_LOCK:
        return _ingest_pos_document(db, pdf_bytes, business_id, filename, payloads, upload)


def _ingest_pos_document(db, pdf_bytes, business_id, filename, payloads, upload):
    sha = calculate_sha256(pdf_bytes)
    documents = (db.table("documents").select("*").eq("business_id", business_id).execute()).data or []
    output = []
    for payload in payloads:
        day = payload.date.isoformat()
        existing = [doc for doc in documents if (doc.get("extracted_data") or {}).get("sha256") == sha
                    and (doc.get("extracted_data") or {}).get("date") == day]
        if len(existing) > 1:
            raise POSDocumentConflict("Hay varios registros de este documento para la misma fecha.")
        doc = existing[0] if existing else None
        document_id = doc["id"] if doc else str(uuid5(NAMESPACE_URL, f"mepia-document:{business_id}:{sha}:{day}"))
        data = _extracted_data(payload, sha)
        imported = (doc or {}).get("extracted_data", {}).get("detailed_import", {})
        if imported.get("version") != _VERSION or imported.get("status") != "complete":
            skipped, has_cash_count = _assert_compatible(db, payload, document_id)
            storage_path = doc["storage_path"] if doc else upload(
                db, f"pos-tickets/{business_id}/{day}/{document_id}.pdf", pdf_bytes)
            if storage_path.startswith("local/"):
                if not doc:
                    raise POSPersistenceError("unavailable")
                storage_path = upload(db, f"pos-tickets/{business_id}/{day}/{document_id}.pdf", pdf_bytes)
                if storage_path.startswith("local/"):
                    raise POSPersistenceError("unavailable")
            row = {"id": document_id, "business_id": business_id, "storage_path": storage_path,
                   "filename": filename, "document_type": "PDF", "ocr_status": "error",
                   "ocr_confidence": 1.0, "needs_human_review": True, "extracted_data": data}
            db.table("documents").upsert(row, on_conflict="id").execute()
            # El snapshot completo se conserva incluso si algunos tickets ya existen.
            _persist_pos_inputs(payload.business_id, payload.date, payload.tickets, payload.payments, db)
            tickets = [ticket for ticket in payload.tickets if ticket.order_id not in skipped]
            _persist_transactions(payload.business_id, tickets, payload.payments, {}, {}, db,
                                  document_id=document_id)
            # Varios cierres de turno no equivalen a un conteo físico diario único.
            _persist_shift_audit_events(payload.business_id, payload.shift_audit, [], db,
                                       strict=True, write_cash_count=data["detailed_import"]["shifts"] == 1 and not has_cash_count)
            _persist_inventory_daily(payload.business_id, payload.date, payload.inventory, {}, db, strict=True)
            data["detailed_import"]["status"] = "complete"
            db.table("documents").update({"extracted_data": data, "ocr_status": "processed",
                                          "needs_human_review": False}).eq("id", document_id).execute()
            doc = row
        else:
            data = doc["extracted_data"]
        gatekeeper = GatekeeperAgent(db)
        expected = gatekeeper.evaluate(business_id, day).model_dump()
        saved = gatekeeper.get_status(business_id, day).model_dump()
        for field in ("active_metrics", "dormant_metrics", "blocked_metrics"):
            expected[field].sort(key=str)
            saved[field].sort(key=str)
        if expected != saved:
            raise POSPersistenceError("unavailable")
        output.append({"file_id": document_id, "storage_path": doc["storage_path"],
                       "uploaded_at": doc.get("uploaded_at") or datetime.now(timezone.utc).isoformat(),
                       "extraction_status": "success", "needs_human_review": False,
                       **{key: value for key, value in data.items() if key != "sha256"}})
    return output
