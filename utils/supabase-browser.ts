"use client";
import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let client: SupabaseClient | undefined;
export function getSupabaseBrowser() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) throw new Error("Falta configurar el inicio de sesión de Supabase.");
  if (typeof window === "undefined") throw new Error("La sesión requiere el navegador.");
  let tab = window.sessionStorage.getItem("mepia.tab.id");
  if (!tab || !/^[0-9a-f-]{36}$/i.test(tab)) {
    tab = window.crypto.randomUUID();
    window.sessionStorage.setItem("mepia.tab.id", tab);
  }
  // Pertenece a la pestaña y sobrevive a recargas, sin recuperar cookies antiguas.
  // La clave distinta también aísla el BroadcastChannel que utiliza el SDK.
  client ??= createClient(url, key, { auth: {
    storageKey: "mepia.auth." + tab,
    storage: window.sessionStorage, persistSession: true, autoRefreshToken: true,
    detectSessionInUrl: false,
  } });
  return client;
}
