"use client";
import type { SupabaseClient } from "@supabase/supabase-js";
import { createBrowserClient } from "@supabase/ssr";

let client: SupabaseClient | undefined;
export function getSupabaseBrowser() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) throw new Error("Falta configurar el inicio de sesión de Supabase.");
  client ??= createBrowserClient(url, key, { cookieOptions: { path: "/", sameSite: "lax", secure: process.env.NODE_ENV === "production" } });
  return client;
}
