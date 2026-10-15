"use client";
import { createContext, useContext, useEffect, useRef, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { getSupabaseBrowser } from "@/utils/supabase-browser";

type Business = { id: string; business_name: string };
type AuthContext = { session: Session | null; ready: boolean; businesses: Business[]; business: string;
  selectBusiness: (id: string) => void; businessesLoading: boolean; error: string;
  reloadBusinesses: () => void; signOut: () => Promise<void> };
const Context = createContext<AuthContext | null>(null);

export function MepiaAuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [business, setBusiness] = useState("");
  const [businessesLoading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const activeUser = useRef<string>();

  useEffect(() => {
    let alive = true;
    try {
      const { data } = getSupabaseBrowser().auth.onAuthStateChange((_event, next) => {
        if (!alive) return;
        if (activeUser.current !== next?.user.id) { setBusinesses([]); setBusiness(""); setError(""); }
        activeUser.current = next?.user.id;
        setSession(next); setReady(true);
      });
      return () => { alive = false; data.subscription.unsubscribe(); };
    } catch { setError("Inicio de sesión no disponible. Intenta más tarde."); setReady(true); }
    return () => { alive = false; };
  }, []);

  const user = session?.user.id;
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
  }
  return <Context.Provider value={{ session, ready, businesses, business, businessesLoading, error,
    selectBusiness: id => { if (businesses.some(item => item.id === id)) setBusiness(id); },
    reloadBusinesses: () => setReload(value => value + 1), signOut }}>{children}</Context.Provider>;
}

export function useMepiaAuth() {
  const context = useContext(Context);
  if (!context) throw new Error("MEPIA Auth context missing");
  return context;
}
