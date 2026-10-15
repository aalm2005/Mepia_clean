import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

export async function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  let response = NextResponse.next();

  // El HTML es el marco sin datos. AuthProvider verifica la sesión de la
  // pestaña antes de mostrar MEPIA. Las APIs exigen credenciales en servidor.
  // Chat conserva su verificación Bearer y propiedad en FastAPI.
  if (path.startsWith("/api/") && !path.startsWith("/api/chat/")) {
    const authorization = request.headers.get("authorization") ?? "";
    const token = /^Bearer ([^\s,]+)$/i.exec(authorization)?.[1];
    let valid = false;
    let unavailable = false;
    if (token) {
      try {
        if (!url || !key) throw new Error("Auth configuration absent");
        const auth = createClient(url, key, { auth: {
          persistSession: false, autoRefreshToken: false, detectSessionInUrl: false,
        } });
        const { data: { user }, error } = await auth.auth.getUser(token);
        valid = !!user && !error && !user.is_anonymous && user.aud === "authenticated";
        unavailable = !!error && (!error.status || error.status >= 500);
      } catch { unavailable = true; }
    }
    if (!valid) response = NextResponse.json({
      error: unavailable ? "Inicio de sesión no disponible." : "Inicia sesión en MEPIA.",
    }, { status: unavailable ? 503 : 401 });
  }

  // Las cookies de la versión anterior dejan de conceder acceso.
  // Eliminarlas no revoca las sesiones independientes de otras pestañas.
  if (url) {
    try {
      const prefix = "sb-" + new URL(url).hostname.split(".")[0] + "-auth-token";
      for (const cookie of request.cookies.getAll()) {
        if (cookie.name === prefix || cookie.name.startsWith(prefix + ".")) {
          response.cookies.set(cookie.name, "", { path: "/", maxAge: 0,
            sameSite: "lax", secure: process.env.NODE_ENV === "production" });
        }
      }
    } catch { /* La API y el proveedor informan configuración inválida. */ }
  }
  response.headers.set("Cache-Control", "private, no-store");
  return response;
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"] };
