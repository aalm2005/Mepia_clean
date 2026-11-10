import { NextRequest, NextResponse } from "next/server";
import { validChatId } from "@/utils/chat-proxy";
export const dynamic = "force-dynamic";
const API = process.env.AGENTS_API_URL ?? "http://localhost:8000";
const headers = { "Cache-Control": "private, no-store" };
export async function GET(req: NextRequest, { params }: {
  params: Promise<{ business_id: string; segments?: string[] }>;
}) {
  const { business_id, segments = [] } = await params;
  const auth = req.headers.get("authorization");
  if (!auth || !/^Bearer \S+$/i.test(auth)) return NextResponse.json({detail:"Inicia sesión en MEPIA."}, {status:401,headers});
  const validPath = segments.length === 0 || (segments.length === 1 && (segments[0] === "latest" || validChatId(segments[0])))
    || (segments.length === 2 && validChatId(segments[0]) && ["trends", "layer3"].includes(segments[1]));
  if (!validChatId(business_id) || !validPath) return NextResponse.json({detail:"La referencia del análisis o del negocio no es válida."}, {status:422,headers});
  const page = req.nextUrl.searchParams.get("page");
  if (page !== null && !/^\d{1,6}$/.test(page)) return NextResponse.json({detail:"Página de historial inválida."},{status:422,headers});
  const suffix = segments.length ? "/" + segments.join("/") : "";
  try {
    const response = await fetch(`${API}/business/${business_id}/analyses${suffix}${page === null ? "" : "?page="+page}`, {
      headers: {Authorization:auth}, cache:"no-store", signal:AbortSignal.timeout(20000),
    });
    if (!response.ok) {
      const messages: Record<number,string> = {401:"Tu sesión venció. Inicia sesión de nuevo.",403:"Sin acceso a este negocio.",
        404:"Este análisis no existe o no corresponde al negocio seleccionado.",422:"La referencia del análisis o del negocio no es válida."};
      const status = [401,403,404,422].includes(response.status) ? response.status : 503;
      return NextResponse.json({detail:messages[status] ?? "No fue posible recuperar los análisis guardados. Intenta de nuevo."}, {status,headers});
    }
    return NextResponse.json(await response.json(),{headers});
  } catch { return NextResponse.json({detail:"No fue posible recuperar los análisis guardados. Intenta de nuevo."},{status:503,headers}); }
}
