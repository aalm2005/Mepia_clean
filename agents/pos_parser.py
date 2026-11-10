"""
agents/pos_parser.py — N01 POS PDF Input Parser
Extrae datos de tickets de ventas POS desde bytes de PDF.
Spec: .kiro/specs/mepia/n01_pos_pdf_input.md
"""
import hashlib
import re
from datetime import date as date_type
from decimal import Decimal, InvalidOperation
from typing import Optional, Union

import pdfplumber
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Modelos Pydantic
# ---------------------------------------------------------------------------

class POSTotals(BaseModel):
    cash: Decimal
    card: Decimal
    total: Decimal


class POSPaymentMethods(BaseModel):
    cash: Decimal
    card: Decimal
    other: Decimal = Decimal("0.00")


class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: Decimal


class OCRConfidence(BaseModel):
    totals: Optional[float] = None
    payment_methods: Optional[float] = None
    line_items: Optional[float] = None


class POSExtractResult(BaseModel):
    sha256: str
    date: Union[date_type, None] = None
    totals: Optional[POSTotals] = None
    payment_methods: Optional[POSPaymentMethods] = None
    line_items: Optional[list[LineItem]] = None
    ocr_confidence: OCRConfidence = OCRConfidence()
    needs_human_review: bool = False
    missing_fields: Optional[list[str]] = None


# ---------------------------------------------------------------------------
# Constantes de confianza simulada (V1 — best-effort regex)
# ---------------------------------------------------------------------------
_CONFIDENCE_EXTRACTED = 0.92   # campo extraído exitosamente
_CONFIDENCE_MISSING = 0.0      # campo no encontrado
_THRESHOLD_REQUIRED = 0.90     # umbral para campos obligatorios
_THRESHOLD_LINE_ITEMS = 0.80   # umbral permisivo para líneas


# ---------------------------------------------------------------------------
# Patrones regex
# ---------------------------------------------------------------------------
_DATE_PATTERNS = [
    # DD/MM/YYYY
    re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b"),
    # YYYY-MM-DD
    re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"),
    # DD-MM-YYYY
    re.compile(r"\b(\d{2})-(\d{2})-(\d{4})\b"),
]

# Patrones para totales — busca etiqueta seguida de monto
_TOTAL_PATTERN = re.compile(
    r"(?:total|venta\s*total|gran\s*total)[^\d]*(\d[\d,]*\.?\d*)",
    re.IGNORECASE,
)
_CASH_PATTERN = re.compile(
    r"(?:efectivo|cash|contado)[^\d]*(\d[\d,]*\.?\d*)",
    re.IGNORECASE,
)
_CARD_PATTERN = re.compile(
    r"(?:tarjeta|card|cr[eé]dito|d[eé]bito)[^\d]*(\d[\d,]*\.?\d*)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------

def calculate_sha256(data: bytes) -> str:
    """Calcula el hash SHA-256 de los bytes dados."""
    return hashlib.sha256(data).hexdigest()


def _parse_decimal(raw: str) -> Optional[Decimal]:
    """Convierte string de monto a Decimal, eliminando comas."""
    try:
        cleaned = raw.replace(",", "")
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def _extract_dates_from_text(text: str) -> list[date_type]:
    """Extrae todas las fechas únicas del texto usando los patrones definidos."""
    found: list[date_type] = []
    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text):
            groups = match.groups()
            try:
                # Determinar orden según el patrón
                if len(groups[0]) == 4:
                    # YYYY-MM-DD
                    d = date_type(int(groups[0]), int(groups[1]), int(groups[2]))
                elif len(groups[2]) == 4:
                    # DD/MM/YYYY o DD-MM-YYYY
                    d = date_type(int(groups[2]), int(groups[1]), int(groups[0]))
                else:
                    continue
                if d not in found:
                    found.append(d)
            except (ValueError, IndexError):
                continue
    return found


def _extract_totals_from_text(text: str) -> Optional[POSTotals]:
    """Intenta extraer totales (total, efectivo, tarjeta) del texto."""
    total_match = _TOTAL_PATTERN.search(text)
    cash_match = _CASH_PATTERN.search(text)
    card_match = _CARD_PATTERN.search(text)

    total = _parse_decimal(total_match.group(1)) if total_match else None
    cash = _parse_decimal(cash_match.group(1)) if cash_match else None
    card = _parse_decimal(card_match.group(1)) if card_match else None

    if total is None and cash is None and card is None:
        return None

    # Inferir valores faltantes si es posible
    if cash is not None and card is not None and total is None:
        total = cash + card
    if total is not None and cash is not None and card is None:
        card = total - cash
    if total is not None and card is not None and cash is None:
        cash = total - card

    # Valores por defecto seguros
    cash = cash or Decimal("0.00")
    card = card or Decimal("0.00")
    total = total or (cash + card)

    return POSTotals(cash=cash, card=card, total=total)


def _extract_line_items_from_tables(pages: list) -> list[LineItem]:
    """Extrae line items de tablas detectadas por pdfplumber."""
    items: list[LineItem] = []
    for page in pages:
        tables = page.extract_tables() or []
        for table in tables:
            for row in table:
                if not row or len(row) < 3:
                    continue
                # Intentar interpretar: descripción, cantidad, precio unitario
                try:
                    desc = str(row[0] or "").strip()
                    qty_raw = str(row[1] or "").strip()
                    price_raw = str(row[-1] or "").strip()

                    if not desc or not qty_raw or not price_raw:
                        continue

                    # Limpiar y convertir
                    # Una hora (12:30) o un código no son cantidades.
                    if not re.fullmatch(r"\d+", qty_raw):
                        continue
                    qty = int(qty_raw)
                    if qty < 1:
                        continue

                    price = _parse_decimal(re.sub(r"[^\d.,]", "", price_raw))
                    if price is None or price <= 0:
                        continue

                    items.append(LineItem(
                        description=desc[:255],
                        quantity=qty,
                        unit_price=price,
                    ))
                except (ValueError, TypeError, InvalidOperation):
                    continue
    return items


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def extract_pos_data(pdf_bytes: bytes) -> list[POSExtractResult]:
    """
    Extrae datos de un PDF de POS y retorna una lista de POSExtractResult.
    Un objeto por fecha detectada (soporte multi-día).
    Nunca lanza excepciones — captura todo y marca needs_human_review si falla.

    Args:
        pdf_bytes: Contenido del PDF en bytes.

    Returns:
        Lista de POSExtractResult, uno por día detectado.
        Si no se puede extraer nada → lista con 1 objeto con needs_human_review=True.
    """
    sha = calculate_sha256(pdf_bytes)

    try:
        all_text = ""
        all_pages = []

        with pdfplumber.open(__import__("io").BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                all_text += page_text + "\n"
                all_pages.append(page)

            # Las tablas necesitan el documento abierto para leer sus streams.
            line_items_raw = _extract_line_items_from_tables(all_pages)

        if not all_text.strip():
            return [_make_empty_result(sha)]

        # Extraer fechas únicas
        dates = _extract_dates_from_text(all_text)

        # Extraer totales
        totals = _extract_totals_from_text(all_text)

        # Si no hay fechas, crear un resultado único sin fecha
        if not dates:
            return [_build_result(sha, None, totals, line_items_raw)]

        # Soporte multi-día: un resultado por fecha distinta
        results = []
        for detected_date in dates:
            results.append(_build_result(sha, detected_date, totals, line_items_raw))

        return results

    except Exception:
        # Capturar cualquier error (PDF corrupto, contraseña, etc.)
        return [_make_empty_result(sha)]


def _make_empty_result(sha: str) -> POSExtractResult:
    """Crea un resultado vacío que requiere revisión humana."""
    return POSExtractResult(
        sha256=sha,
        date=None,
        totals=None,
        payment_methods=None,
        line_items=None,
        ocr_confidence=OCRConfidence(
            totals=_CONFIDENCE_MISSING,
            payment_methods=_CONFIDENCE_MISSING,
            line_items=None,
        ),
        needs_human_review=True,
        missing_fields=["date", "totals.total", "totals.cash", "totals.card"],
    )


def _build_result(
    sha: str,
    detected_date: Optional[date_type],
    totals: Optional[POSTotals],
    line_items_raw: list[LineItem],
) -> POSExtractResult:
    """Construye un POSExtractResult evaluando confianza y campos faltantes."""
    missing: list[str] = []

    # Evaluar confianza por sección
    date_confidence = _CONFIDENCE_EXTRACTED if detected_date is not None else _CONFIDENCE_MISSING
    totals_confidence = _CONFIDENCE_EXTRACTED if totals is not None else _CONFIDENCE_MISSING
    pm_confidence = _CONFIDENCE_EXTRACTED if totals is not None else _CONFIDENCE_MISSING
    li_confidence = _CONFIDENCE_EXTRACTED if line_items_raw else None

    # Determinar campos faltantes (obligatorios con umbral 90%)
    if date_confidence < _THRESHOLD_REQUIRED:
        missing.append("date")
    if totals_confidence < _THRESHOLD_REQUIRED:
        missing.extend(["totals.total", "totals.cash", "totals.card"])
    elif totals is not None:
        if totals.total == 0 and totals.cash == 0 and totals.card == 0:
            missing.extend(["totals.total", "totals.cash", "totals.card"])

    # Construir payment_methods desde totals si están disponibles
    payment_methods: Optional[POSPaymentMethods] = None
    if totals is not None:
        payment_methods = POSPaymentMethods(
            cash=totals.cash,
            card=totals.card,
            other=Decimal("0.00"),
        )

    # Filtrar line items con confianza < 80% (umbral permisivo)
    # En V1 simulado, si se extrajeron items los incluimos todos
    final_line_items: Optional[list[LineItem]] = None
    if li_confidence is not None and li_confidence >= _THRESHOLD_LINE_ITEMS:
        final_line_items = line_items_raw if line_items_raw else None

    needs_review = len(missing) > 0

    return POSExtractResult(
        sha256=sha,
        date=detected_date,
        totals=totals,
        payment_methods=payment_methods,
        line_items=final_line_items,
        ocr_confidence=OCRConfidence(
            totals=totals_confidence,
            payment_methods=pm_confidence,
            line_items=li_confidence,
        ),
        needs_human_review=needs_review,
        missing_fields=missing if missing else None,
    )
