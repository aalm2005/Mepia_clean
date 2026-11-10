# N01 — POS PDF Input (Ingesta de Ticket de Ventas)

## Extensión de detalle estructurado del 9-nov-2026

`POST /ingest/pos` reconoce adjuntos JSON con el contrato `APIIngestPayload`
de S1B. La respuesta conserva `POSIngestResult[]` y añade el campo opcional
`detailed_import`, con versión, estado y conteos de tickets, turnos e inventario.
El PDF convencional sigue utilizando la extracción de totales descrita abajo.

- El `business_id` de la solicitud prevalece sobre el incluido en el adjunto.
- Se importan únicamente fechas presentes en el texto del PDF. Los adjuntos
  de otros días y los complementos de recetas, gastos o configuración quedan fuera.
- Tickets y pagos deben ser únicos y corresponder al día y sucursal. Cuando
  hay una sola fecha visible, los totales deben coincidir con el detalle.
- Los ingresos individuales conservan `document_id`, timestamp, productos y
  ambas claves `payment` y `PaymentBreakdown`, compatibles con S1B y S3.
- Los registros se guardan en `transactions`, `pos_inputs`, `shift_audit_events`,
  `cash_counts` e `inventory_daily`. Solo un turno permite derivar un conteo
  diario inequívoco. Con varios turnos se requiere la captura diaria separada.
- El mismo SHA y negocio puede completar un documento antiguo que solo tenía
  totales. Conserva su ID y no duplica las ventas. Se rechazan totales, tickets
  o conteos diarios previos incompatibles mediante HTTP 409.
- El documento se marca pendiente antes de escribir el detalle y solo queda
  procesado al terminar todas las etapas. Un fallo devuelve HTTP 503 y el
  mismo PDF permite reanudar. La revisión manual de totales no completa una
  importación detallada pendiente.
- Los identificadores de documento y tickets son deterministas. La carga
  detallada se serializa en el proceso local y el archivo se guarda con upsert.
- Se reevalúa S2 y se verifica la lectura de sus estados antes de confirmar
  la respuesta. Los indicadores que requieren compras, recetas o configuración
  adicional conservan sus requisitos.
- Un formato POS inconsistente devuelve HTTP 422 antes de escribir datos.
- La lectura convencional de cantidades requiere un entero completo. Una
  hora como `12:30` se omite como cantidad.

La prueba de regresión usa el PDF de demostración como fixture y ejecuta el
endpoint real con DB simulada y red externa bloqueada.

**Capa:** Sequential | **Parte de:** S1 Ingesta | **Siguiente:** S2 Gatekeeper
**Archivo de implementación:** `api/main.py` → `POST /ingest/pos`
**Archivos relacionados:** `db_schema.md`, `s2_gatekeeper.md`, `_glossary.md`

---

## Input / Output

- **Input:** PDF multipart + `business_id` UUID
- **Output:** `POSIngestResult[]` — un objeto por día detectado en el PDF

---

## Endpoint

### `POST /ingest/pos`

**Request:** `multipart/form-data`

| Campo         | Tipo | Requerido | Descripción                        |
|---------------|------|-----------|------------------------------------|
| `file`        | File | ✅        | PDF del ticket POS                 |
| `business_id` | UUID | ✅        | Negocio propietario del ticket     |

**Manejo de múltiples días:** Si el PDF contiene datos de N días distintos, el backend
fragmenta el contenido y retorna un array de N objetos `POSIngestResult`, uno por día.
Cada objeto es independiente y se persiste por separado en `pos_inputs`.

**Response 200 — extracción exitosa (un día):**
```json
[
  {
    "file_id": "uuid-v4",
    "storage_path": "pos-tickets/{business_id}/2024-01-15/{file_id}.pdf",
    "extraction_status": "success",
    "needs_human_review": false,
    "uploaded_at": "2024-01-15T22:00:00Z",
    "date": "2024-01-15",
    "totals": {
      "cash": 3200.00,
      "card": 1950.00,
      "total": 5150.00
    },
    "payment_methods": {
      "cash": 3200.00,
      "card": 1950.00,
      "other": 0.00
    },
    "line_items": [
      { "description": "Café Latte", "quantity": 42, "unit_price": 65.00 }
    ],
    "ocr_confidence": {
      "totals": 0.97,
      "payment_methods": 0.95,
      "line_items": 0.83
    }
  }
]
```

**Response 200 — revisión humana requerida:**
```json
[
  {
    "file_id": "uuid-v4",
    "storage_path": "pos-tickets/{business_id}/2024-01-15/{file_id}.pdf",
    "extraction_status": "needs_human_review",
    "needs_human_review": true,
    "uploaded_at": "2024-01-15T22:00:00Z",
    "date": null,
    "totals": null,
    "payment_methods": null,
    "line_items": null,
    "ocr_confidence": { "totals": 0.71, "payment_methods": 0.68, "line_items": null },
    "missing_fields": ["totals", "payment_methods"]
  }
]
```

**Códigos de error:**

| HTTP | Condición |
|------|-----------|
| 404  | `business_id` no existe en `businesses` |
| 413  | Archivo > 20 MB |
| 422  | MIME ≠ `application/pdf`, 0 bytes, PDF corrupto o con contraseña |
| 503  | Supabase Storage no disponible |

---

## Contrato de Campos Obligatorios

Los siguientes campos son **obligatorios** para que el Gatekeeper S2 active la métrica
`calc_cash_reconciliation`. Si alguno falta, `needs_human_review: true`.

| Campo | Umbral de confianza OCR | Consecuencia si falla |
|---|---|---|
| `date` | 90% | `needs_human_review: true` |
| `totals.total` | 90% | `needs_human_review: true` |
| `totals.cash` | 90% | `needs_human_review: true` |
| `totals.card` | 90% | `needs_human_review: true` |
| `payment_methods.*` | 90% | `needs_human_review: true` |
| `line_items[*]` | 80% | Línea omitida, resto continúa |

**Regla de líneas individuales:** La confianza del 80% para `line_items` es intencional.
El CFO Forense (S4) valida matemáticamente que la suma de líneas coincida con `totals.total`.
Si no coincide, S4 lo registra como anomalía `source_discrepancy`.

---

## Contrato `POSIngestResult` (actualización del glosario)

```
file_id: UUID                    → documents.id
storage_path: string             → documents.storage_path
extraction_status: "success" | "needs_human_review"
needs_human_review: bool
uploaded_at: datetime (UTC ISO-8601)
date: date | null                → fecha de operación del ticket
totals: {
  cash: Decimal
  card: Decimal
  total: Decimal
} | null
payment_methods: {
  cash: Decimal
  card: Decimal
  other: Decimal                 → default 0.00
} | null
line_items: LineItem[] | null
ocr_confidence: {
  totals: float | null           → 0.0–1.0
  payment_methods: float | null
  line_items: float | null
}
missing_fields: string[] | null  → campos que no alcanzaron el umbral
```

### `LineItem`
```
description: string
quantity: int
unit_price: Decimal
```

---

## Persistencia

| Campo del resultado | Tabla destino | Columna |
|---|---|---|
| `file_id` | `documents` | `id` |
| `storage_path` | `documents` | `storage_path` |
| `extraction_status` | `documents` | `ocr_status` |
| `ocr_confidence.totals` | `documents` | `ocr_confidence` |
| `needs_human_review` | `documents` | `needs_human_review` |
| `date`, `totals`, `payment_methods` | `pos_inputs` | campos estructurados |
| `line_items` | `documents` | `extracted_data` (JSONB) |

---

## Acceptance Criteria

- WHEN PDF con un solo día → retornar array de 1 `POSIngestResult`
- WHEN PDF con N días → retornar array de N objetos, uno por día, cada uno persistido en `pos_inputs`
- WHEN confianza de `totals` < 90% → `needs_human_review: true`, `extraction_status: "needs_human_review"`
- WHEN confianza de `line_items` < 80% → omitir esa línea, continuar con el resto
- WHEN `line_items` presentes → S4 puede validar que su suma ≈ `totals.total` (tolerancia 1%)
- WHEN mismo SHA-256 + `business_id` → retornar resultado original sin duplicar en Storage
- WHEN PDF con contraseña → HTTP 422

---

## Edge Cases

- PDF multi-página: extraer de todas las páginas, agrupar por fecha detectada
- Ticket sin desglose de métodos de pago: `payment_methods: null`, `needs_human_review: true`
- `totals.cash + totals.card ≠ totals.total` (discrepancia en el propio PDF): registrar en `extracted_data.raw_metadata`, continuar
- Fecha ambigua (ej. "15/01" sin año): inferir año del contexto del archivo, si no es posible → `needs_human_review: true`

---

## Correctness Properties (PBT)

| ID | Propiedad |
|----|-----------|
| P1 | `file_id`, `storage_path`, `uploaded_at`, `extraction_status` siempre presentes en todo resultado |
| P2 | `needs_human_review: true` ↔ al menos un campo obligatorio con confianza < 90% |
| P3 | PDF con N días → array de exactamente N objetos, cada uno con `date` distinto |
| P4 | `deserialize(serialize(result)) == result` (round-trip JSON) |
| P5 | Mismo SHA-256 + `business_id` → exactamente 1 objeto en Storage |
| P6 | `line_items` con confianza < 80% → nunca aparecen en el resultado |
| P7 | `ocr_confidence.totals >= 0.90` → `needs_human_review: false` (si no hay otros campos faltantes) |

[Cinco PDF ficticios para la prueba manual Q7](../../../output/pdf/MEPIA_Q7_DaAx_Coffee/LEEME_Pruebas_manuales_Q7.md). Cada jornada combina ventas, pagos, caja e inventario; el detalle adjunto no se debe separar del PDF.
