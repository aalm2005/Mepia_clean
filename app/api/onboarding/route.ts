import { NextRequest, NextResponse } from "next/server";
import { validChatId } from "@/utils/chat-proxy";

const AGENTS_API = process.env.AGENTS_API_URL ?? "http://localhost:8000";
const privateHeaders = { "Cache-Control": "private, no-store" };

/** Solo transporta la sesión. Python verifica firma y propiedad del negocio. */
async function forward(req: NextRequest) {
  const authorization = req.headers.get("authorization") ?? "";
  if (!/^Bearer [^\s,]+$/i.test(authorization)) {
    return NextResponse.json({ detail: "Inicia sesión en MEPIA" },
      { status: 401, headers: { ...privateHeaders, "WWW-Authenticate": "Bearer" } });
  }
  let business: unknown = req.nextUrl.searchParams.get("business_id");
  let payload: Record<string, unknown> | undefined;
  if (req.method !== "GET") {
    try {
      const text = await req.text();
      if (text.length > 64000) {
        return NextResponse.json({ detail: "La configuración es demasiado extensa" }, { status: 413, headers: privateHeaders });
      }
      const body = JSON.parse(text);
      if (!body || typeof body !== "object" || Array.isArray(body)) throw new Error();
      const { business_id, ...rest } = body;
      business = business_id;
      payload = rest;
    } catch {
      return NextResponse.json({ detail: "Revisa los datos de la configuración" }, { status: 400, headers: privateHeaders });
    }
  }
  if (typeof business !== "string" || !validChatId(business)) {
    return NextResponse.json({ detail: "Selecciona un negocio válido" }, { status: 400, headers: privateHeaders });
  }
  try {
    const upstream = await fetch(`${AGENTS_API}/business/${business}/onboarding${req.method === "GET" ? "/status" : ""}`, {
      method: req.method,
      headers: { Authorization: authorization, "Content-Type": "application/json" },
      body: payload === undefined ? undefined : JSON.stringify(payload),
      cache: "no-store", signal: AbortSignal.timeout(30000),
    });
    if (!upstream.ok) {
      const messages: Record<number, string> = {
        401: "Tu sesión venció. Inicia sesión de nuevo.", 403: "Sin acceso a este negocio",
        404: "Configuración no disponible", 409: "La configuración ya existe",
        422: "Revisa los datos y los límites de alerta de la configuración",
      };
      const status = [401, 403, 404, 409, 422].includes(upstream.status) ? upstream.status : 503;
      return NextResponse.json({ detail: messages[status] ?? "Configuración no disponible. Intenta de nuevo." },
        { status, headers: privateHeaders });
    }
    return NextResponse.json(await upstream.json(), { status: upstream.status, headers: privateHeaders });
  } catch {
    return NextResponse.json({ detail: "Configuración no disponible. Intenta de nuevo." },
      { status: 503, headers: privateHeaders });
  }
}

export const GET = forward;
export const POST = forward;
export const PUT = forward;
