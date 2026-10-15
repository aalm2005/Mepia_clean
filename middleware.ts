import { NextRequest, NextResponse } from "next/server";
import { createServerClient, type CookieOptions } from "@supabase/ssr";

export async function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  // Chat API verifica Bearer y propiedad en FastAPI, incluso para clientes sin cookies.
  if (path === "/login" || path.startsWith("/api/chat/")) return NextResponse.next();
  const api = path.startsWith("/api/");
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  const pending: { name: string; value: string; options: CookieOptions }[] = [];
  let valid = false;
  let unavailable = false;
  try {
    if (!url || !key) throw new Error("Auth configuration absent");
    const auth = createServerClient(url, key, { cookieOptions: { path: "/", sameSite: "lax", secure: process.env.NODE_ENV === "production" }, cookies: {
      get: (name: string) => request.cookies.get(name)?.value,
      set: (name: string, value: string, options: CookieOptions) => { request.cookies.set(name, value); pending.push({ name, value, options }); },
      remove: (name: string, options: CookieOptions) => { request.cookies.set(name, ""); pending.push({ name, value: "", options }); },
    } });
    // Verificación remota; no confiar en usuario/claims leídos de una cookie.
    const { data: { user }, error } = await auth.auth.getUser();
    valid = !!user && !error && !user.is_anonymous && user.aud === "authenticated";
    unavailable = !!error && (!error.status || error.status >= 500) && error.name !== "AuthSessionMissingError";
    if (!valid && !unavailable) {
      const prefix = "sb-" + new URL(url).hostname.split(".")[0] + "-auth-token";
      for (const cookie of request.cookies.getAll()) {
        if (cookie.name === prefix || cookie.name.startsWith(prefix + ".")) {
          request.cookies.set(cookie.name, "");
          pending.push({ name: cookie.name, value: "", options: { path: "/", maxAge: 0, sameSite: "lax" } });
        }
      }
    }
  } catch { unavailable = true; }
  let response: NextResponse;
  if (valid) response = NextResponse.next({ request });
  else if (api) response = NextResponse.json({ error: unavailable ? "Inicio de sesión no disponible." : "Inicia sesión en MEPIA." }, { status: unavailable ? 503 : 401 });
  else {
    const destination = request.nextUrl.clone();
    destination.pathname = "/login"; destination.search = "";
    destination.searchParams.set("next", request.nextUrl.pathname + request.nextUrl.search);
    if (unavailable) destination.searchParams.set("error", "session-unavailable");
    response = NextResponse.redirect(destination);
  }
  for (const cookie of pending) response.cookies.set(cookie.name, cookie.value, cookie.options);
  response.headers.set("Cache-Control", "private, no-store");
  return response;
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"] };
