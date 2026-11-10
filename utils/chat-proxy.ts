import { NextRequest, NextResponse } from "next/server";

const API = process.env.AGENTS_API_URL ?? "http://localhost:8000";
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function validChatId(value: string) { return UUID.test(value); }

/** Reenvía solo la sesión; el servidor Python decide permisos y proveedor. */
export async function chatProxy(req: NextRequest, path: string) {
  const authorization = req.headers.get("authorization");
  if (!authorization || !/^Bearer \S+$/i.test(authorization)) {
    return NextResponse.json({ detail: "Inicia sesión" }, { status: 401, headers: { "Cache-Control": "no-store" } });
  }
  const body = req.method === "POST" ? await req.text() : undefined;
  if (body && body.length > 16000) {
    return NextResponse.json({ detail: "Pregunta demasiado extensa" }, { status: 413 });
  }
  try {
    const upstream = await fetch(`${API}${path}`, {
      method: req.method, headers: { Authorization: authorization, "Content-Type": "application/json" },
      body, cache: "no-store", signal: AbortSignal.timeout(135000),
    });
    const headers = { "Cache-Control": "no-store" };
    if (upstream.status === 204) return new NextResponse(null, { status: 204, headers });
    if (!upstream.ok) {
      const messages: Record<number, string> = {
        401: "Tu sesión venció. Inicia sesión de nuevo.", 403: "Sin acceso a este negocio",
        404: "Conversación no disponible", 409: "Espera a que termine la respuesta anterior",
        422: "Revisa la pregunta, fecha, análisis y negocio", 429: "Límite de conversaciones alcanzado",
      };
      const status = [401, 403, 404, 409, 422, 429].includes(upstream.status) ? upstream.status : 503;
      // Solo mensajes estáticos conocidos; jamás propagar excepciones crudas del backend.
      const allowed = new Set([
        "El análisis no existe o no corresponde a este negocio",
        "Elige un análisis terminado para consultar sus resultados",
        "El análisis no conserva una referencia de resultados válida",
        "Este análisis no conserva su referencia de cálculo; elige otro análisis",
        "Los cálculos de este análisis no están disponibles; elige otro análisis",
        "La fecha no coincide con el análisis seleccionado",
      ]);
      let detail = messages[status] ?? "Chat no disponible. Intenta más tarde.";
      if ([404,409,422].includes(status)) {
        const failure = await upstream.json().catch(() => null);
        if (typeof failure?.detail === "string" && allowed.has(failure.detail)) detail = failure.detail;
      }
      return NextResponse.json({ detail }, { status, headers });
    }
    return NextResponse.json(await upstream.json(), { headers });
  } catch {
    return NextResponse.json({ detail: "Chat no disponible. Intenta más tarde." }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }
}
