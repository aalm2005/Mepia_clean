"use client";
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { getSupabaseBrowser } from "@/utils/supabase-browser";

type Business = { id: string; business_name: string };
type AuthContext = { session: Session | null; ready: boolean; businesses: Business[]; business: string;
  selectBusiness: (id: string) => void; businessesLoading: boolean; error: string;
  reloadBusinesses: () => void; signOut: () => Promise<void>;
  auditRunId: string | null; rememberAudit: (runId: string) => void };
const Context = createContext<AuthContext | null>(null);

export function MepiaAuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [business, setBusiness] = useState("");
  const [lastAudit, setLastAudit] = useState<{ user: string; business: string; run: string } | null>(null);
  const [businessesLoading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const activeUser = useRef<string>();

  useEffect(() => {
    let alive = true;
    let revision = 0;
    let verificationTimer: ReturnType<typeof setTimeout> | undefined;
    try {
      const { data } = getSupabaseBrowser().auth.onAuthStateChange((_event, next) => {
        if (!alive) return;
        const current = ++revision;
        if (verificationTimer !== undefined) clearTimeout(verificationTimer);
        if (activeUser.current !== next?.user.id) {
          setLastAudit(null);
          setSession(null); setBusinesses([]); setBusiness(""); setError(""); setReady(false);
        }
        activeUser.current = next?.user.id;
        if (!next) { setSession(null); setReady(true); return; }
        // Ejecutar fuera de la notificación del SDK, una vez liberado su bloqueo.
        verificationTimer = setTimeout(() => {
        verificationTimer = undefined;
        if (!alive || current !== revision) return;
        void getSupabaseBrowser().auth.getUser(next.access_token).then(({ data: { user }, error: failure }) => {
          if (!alive || current !== revision) return;
          if (failure || !user || user.is_anonymous || user.aud !== "authenticated" || user.id !== next.user.id) {
            activeUser.current = undefined; setSession(null); setBusinesses([]); setBusiness("");
            setError("No fue posible comprobar tu sesión. Inicia sesión de nuevo.");
          } else { setSession({ ...next, user }); }
          setReady(true);
        }).catch(() => {
          if (!alive || current !== revision) return;
          activeUser.current = undefined; setSession(null); setBusinesses([]); setBusiness("");
          setError("Inicio de sesión no disponible. Intenta más tarde."); setReady(true);
        });
        }, 0);
      });
      return () => { alive = false; if (verificationTimer !== undefined) clearTimeout(verificationTimer); data.subscription.unsubscribe(); };
    } catch { setError("Inicio de sesión no disponible. Intenta más tarde."); setReady(true); }
    return () => { alive = false; };
  }, []);

  const user = session?.user.id;
  const auditRunId = lastAudit?.user === user && lastAudit?.business === business ? lastAudit.run : null;
  const rememberAudit = useCallback((runId: string) => {
    if (!user || !business || activeUser.current !== user) return;
    setLastAudit(current => current?.user === user && current.business === business && current.run === runId
      ? current : { user, business, run: runId });
  }, [user, business]);
  useEffect(() => {
    if (!user) return;
    const abort = new AbortController();
    setLoading(true); setError("");
    (async () => {
      try {
        const { data } = await getSupabaseBrowser().auth.getSession();
        if (!data.session || activeUser.current !== user) return;
        const response = await fetch("/api/chat/businesses", { headers: { Authorization: `Bearer ${data.session.access_token}` }, cache: "no-store", signal: abort.signal });
        if (!response.ok) throw new Error("No fue posible cargar tus negocios. Intenta de nuevo.");
        const result = await response.json();
        if (abort.signal.aborted || activeUser.current !== user) return;
        const own: Business[] = result.businesses;
        setBusinesses(own); setBusiness(current => own.some(item => item.id === current) ? current : own[0]?.id ?? "");
      } catch {
        if (!abort.signal.aborted && activeUser.current === user) { setBusinesses([]); setBusiness(""); setError("No fue posible cargar tus negocios. Intenta de nuevo."); }
      } finally { if (!abort.signal.aborted && activeUser.current === user) setLoading(false); }
    })();
    return () => abort.abort();
  }, [user, reload]);

  async function signOut() {
    const { error: failure } = await getSupabaseBrowser().auth.signOut({ scope: "local" });
    if (failure) throw new Error("No fue posible cerrar sesión. Intenta de nuevo.");
    setLastAudit(null);
  }
  return <Context.Provider value={{ session, ready, businesses, business, businessesLoading, error,
    auditRunId, rememberAudit,
    selectBusiness: id => { if (businesses.some(item => item.id === id)) { if (id !== business) setLastAudit(null); setBusiness(id); } },
    reloadBusinesses: () => setReload(value => value + 1), signOut }}>{children}</Context.Provider>;
}

export function useMepiaAuth() {
  const context = useContext(Context);
  if (!context) throw new Error("MEPIA Auth context missing");
  return context;
}
