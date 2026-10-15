import { NextRequest, NextResponse } from "next/server";

const AGENTS_API = process.env.AGENTS_API_URL ?? "http://localhost:8000";

// GET /api/audit/layer3/status/{layer2_run_id} → GET /layer3/status/{layer2_run_id}
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ layer2_run_id: string }> }
) {
  const { layer2_run_id } = await params;

  const res = await fetch(`${AGENTS_API}/layer3/status/${layer2_run_id}`, {
    cache: "no-store",
  });

  const data = await res.json().catch(() => null);
  return NextResponse.json(data, { status: res.status });
}
