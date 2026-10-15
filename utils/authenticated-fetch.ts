"use client";
import { getSupabaseBrowser } from "@/utils/supabase-browser";

/** Envía la sesión de esta pestaña solo a la API de MEPIA. */
export async function authenticatedFetch(path: string, init: RequestInit = {}) {
  if (!path.startsWith("/api/")) throw new Error("Destino de MEPIA inválido.");
  const { data: { session }, error } = await getSupabaseBrowser().auth.getSession();
  if (error || !session) throw new Error("Inicia sesión en MEPIA.");
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${session.access_token}`);
  return fetch(path, { ...init, headers, cache: "no-store" });
}
