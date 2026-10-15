"use client";
import { FormEvent, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useMepiaAuth } from "@/components/auth/MepiaAuthProvider";
import { getSupabaseBrowser } from "@/utils/supabase-browser";
import { chatLoginErrorMessage } from "@/utils/chat-login-error";
import { loginDestination } from "@/utils/login-destination";

export function MepiaLogin() {
  const params = useSearchParams();
  const { session, ready } = useMepiaAuth();
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  const destination = loginDestination(params.get("next"));
  useEffect(() => {
    if (!ready || !session) return;
    let alive = true;
    getSupabaseBrowser().auth.getUser().then(({ data: { user }, error: failure }) => {
      if (!alive) return;
      if (user && !failure && !user.is_anonymous) window.location.replace(destination);
      else setError("No fue posible comprobar tu sesión. Inicia sesión de nuevo.");
    }).catch(() => { if (alive) setError("Inicio de sesión no disponible. Intenta más tarde."); });
    return () => { alive = false; };
  }, [ready, session, destination]);
  async function login(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const { error: failure } = await getSupabaseBrowser().auth.signInWithPassword({ email, password });
      if (failure) setError(chatLoginErrorMessage(failure));
    } catch { setError("Inicio de sesión no disponible. Intenta más tarde."); }
    finally { setPassword(""); setBusy(false); }
  }
  return <div className="grid min-h-dvh place-items-center px-5 py-12">
    <div className="glass-strong w-full max-w-md p-7 sm:p-9">
      <div className="mb-10 text-center"><span className="mx-auto mb-5 grid h-12 w-12 place-items-center rounded-2xl border border-emerald-400/20 bg-emerald-400/10 text-xl font-semibold text-emerald-300">M</span>
        <p className="mb-3 text-xs uppercase tracking-[0.25em] text-zinc-500">Mise En Place AI</p>
        <h1 className="text-3xl font-semibold tracking-tight">Bienvenido a MEPIA</h1><p className="mt-3 text-sm text-zinc-400">Tu negocio, con una perspectiva más clara.</p></div>
      <form onSubmit={login} className="space-y-5">
        <div><label htmlFor="mepia-email" className="mb-2 block text-sm text-zinc-300">Correo</label><input id="mepia-email" type="email" autoComplete="username" required value={email} onChange={e => setEmail(e.target.value)} placeholder="tu@correo.com" className="w-full rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 outline-none focus:border-emerald-400"/></div>
        <div><label htmlFor="mepia-password" className="mb-2 block text-sm text-zinc-300">Contraseña</label><input id="mepia-password" type="password" autoComplete="current-password" required value={password} onChange={e => setPassword(e.target.value)} className="w-full rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 outline-none focus:border-emerald-400"/></div>
        <button disabled={busy || !ready} className="w-full rounded-xl bg-emerald-400 py-3 text-sm font-semibold text-zinc-950 transition-colors hover:bg-emerald-300 disabled:opacity-50">{busy ? "Entrando…" : "Iniciar sesión"}</button>
        {(error || params.get("error") === "session-unavailable") && <p role="alert" className="rounded-xl border border-red-900/50 bg-red-950/20 p-3 text-sm text-red-300">{error || "No fue posible comprobar tu sesión. Intenta de nuevo."}</p>}
      </form>
      <p className="mt-8 text-center text-xs leading-relaxed text-zinc-600">Una sola cuenta para tu dashboard, documentos y asistente.</p>
    </div>
  </div>;
}
