import { NextRequest, NextResponse } from "next/server";

const AGENTS_API = process.env.AGENTS_API_URL ?? "http://localhost:8000";

/**
 * POST /api/upload
 * Proxies to FastAPI based on document type.
 * Body: FormData with `file`, `type` ("pos" | "factura"), and optional `business_id`.
 * → POST /ingest/pos  (for POS PDFs)
 * → POST /ingest/factura  (for XML/PDF facturas, requires `document_type` field)
 */
export async function POST(req: NextRequest) {
  const form = await req.formData();
  const file = form.get("file") as File | null;
  const type = form.get("type") as string | null;
  const businessId = (form.get("business_id") as string | null) ?? "";

  if (!file) {
    return NextResponse.json({ error: "No file provided" }, { status: 400 });
  }
  if (type !== "pos" && type !== "factura") {
    return NextResponse.json(
      { error: 'Invalid type. Must be "pos" or "factura"' },
      { status: 400 }
    );
  }
  if (!businessId) {
    return NextResponse.json(
      { error: "business_id is required" },
      { status: 400 }
    );
  }

  const upstream = new FormData();
  upstream.append("file", file);
  upstream.append("business_id", businessId);

  // Facturas require document_type (XML or PDF) — infer from file extension/MIME
  if (type === "factura") {
    const filename = file.name?.toLowerCase() ?? "";
    const documentType = filename.endsWith(".xml") ? "XML" : "PDF";
    upstream.append("document_type", documentType);
  }

  const res = await fetch(`${AGENTS_API}/ingest/${type}`, {
    method: "POST",
    body: upstream,
  });

  const data = await res.json().catch(() => null);
  return NextResponse.json(data, { status: res.status });
}

/**
 * PATCH /api/upload
 * Proxies to FastAPI review endpoint for human-corrected documents.
 * Body: JSON { file_id, document_type ("pos" | "factura"), ...field_corrections }
 * → PATCH /ingest/pos/{file_id}/review
 * → PATCH /ingest/factura/{file_id}/review
 */
export async function PATCH(req: NextRequest) {
  const body = await req.json();
  const { file_id, document_type, ...field_corrections } = body;

  if (!file_id || !document_type) {
    return NextResponse.json(
      { error: "file_id and document_type are required" },
      { status: 400 }
    );
  }

  if (document_type !== "pos" && document_type !== "factura") {
    return NextResponse.json(
      { error: 'document_type must be "pos" or "factura"' },
      { status: 400 }
    );
  }

  const res = await fetch(
    `${AGENTS_API}/ingest/${document_type}/${file_id}/review`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(field_corrections),
    }
  );

  const data = await res.json().catch(() => null);
  return NextResponse.json(data, { status: res.status });
}
