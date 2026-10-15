"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useMepiaAuth } from "@/components/auth/MepiaAuthProvider";
import { MepiaIcon, type MepiaIconName } from "@/components/ui/MepiaIcon";

const navigation: { href: string; label: string; icon: MepiaIconName }[] = [
  { href: "/dashboard", label: "Dashboard", icon: "dashboard" },
  { href: "/upload", label: "Documentos", icon: "upload" }, { href: "/chat", label: "Chat IA", icon: "chat" },
  { href: "/salud", label: "Salud del Negocio", icon: "health" }, { href: "/reportes", label: "Reportes", icon: "reports" },
  { href: "/onboarding", label: "Configuración", icon: "settings" },
];
export function MepiaShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const { session, ready, businesses, business, selectBusiness, businessesLoading, error, reloadBusinesses, signOut } = useMepiaAuth();
  const [menu, setMenu] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const [logoutError, setLogoutError] = useState("");
  useEffect(() => { setMenu(false); }, [path]);
  useEffect(() => {
    if (path !== "/login" && ready && !session && !leaving) router.replace(`/login?next=${encodeURIComponent(path + window.location.search)}`);
  }, [path, ready, session, leaving, router]);
  if (path === "/login") return <>{children}</>;
  if (!ready || !session) return <div className="grid min-h-dvh place-items-center text-sm text-zinc-400">Cargando MEPIA…</div>;
  const name = session.user.email?.split("@")[0] ?? "Mi cuenta";
  async function logout() {
    setLeaving(true); setLogoutError("");
    try { await signOut(); window.location.replace("/login"); }
    catch { setLogoutError("No fue posible cerrar sesión. Intenta de nuevo."); setLeaving(false); }
  }
  return <div className="relative min-h-dvh">
    {menu && <button aria-label="Cerrar menú" className="fixed inset-0 z-30 bg-black/60 md:hidden" onClick={() => setMenu(false)} />}
    <aside className={`sidebar-glass fixed inset-y-0 left-0 z-40 w-64 flex-col px-3 py-5 ${menu ? "flex" : "hidden md:flex"}`} aria-label="Menú de MEPIA">
      <Link href="/dashboard" className="mb-8 flex items-center gap-3 px-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-emerald-400/15 text-emerald-300 font-semibold">M</span><span className="text-lg font-semibold tracking-wide">MEPIA</span></Link>
      <p className="px-3 pb-3 text-[11px] uppercase tracking-widest text-zinc-500">Tu espacio</p>
      <nav aria-label="Navegación principal" className="space-y-1">
        {navigation.map(item => <Link key={item.href} href={item.href} aria-current={path === item.href ? "page" : undefined}
          className={`nav-item ${path === item.href ? "is-active" : ""}`}>
          <MepiaIcon name={item.icon} /><span>{item.label}</span>{item.href === "/chat" && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-400"/>}</Link>)}
      </nav>
      <div className="mt-auto border-t border-white/10 pt-4">
        <div className="flex items-center gap-3 px-3 py-3"><span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-zinc-700 text-xs uppercase">{name.slice(0,2)}</span><div className="min-w-0"><p className="truncate text-sm">{name}</p><p className="text-xs text-zinc-500">Mi cuenta</p></div></div>
        <button disabled={leaving} onClick={logout} className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm text-zinc-400 hover:bg-white/5 disabled:opacity-50"><MepiaIcon name="logout"/>Cerrar sesión</button>
        {logoutError && <p role="alert" className="px-3 pt-2 text-xs text-red-300">{logoutError}</p>}
      </div>
    </aside>
    <div className="md:pl-64">
      <header className="sidebar-glass sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-white/5 px-4 sm:px-6">
        <button aria-label="Abrir menú" aria-expanded={menu} onClick={() => setMenu(true)} className="rounded-lg p-2 text-zinc-400 hover:bg-white/5 md:hidden"><MepiaIcon name="menu"/></button>
        <div className="flex min-w-0 flex-1 items-center gap-3"><label htmlFor="mepia-business" className="hidden text-xs text-zinc-500 sm:block">Negocio</label>
          <select id="mepia-business" aria-label="Negocio" value={business} disabled={businessesLoading || !businesses.length}
            onChange={event => { selectBusiness(event.target.value); if (["/dashboard", "/salud", "/reportes"].includes(path)) router.replace(path); }}
            className="min-w-0 max-w-full rounded-lg border border-white/10 bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-400 disabled:opacity-50 sm:max-w-[240px]">
            {!businesses.length && <option value="">{businessesLoading ? "Cargando negocios…" : "Sin negocio asignado"}</option>}
            {businesses.map(item => <option key={item.id} value={item.id}>{item.business_name}</option>)}
          </select></div>
        <span aria-label="Sesión iniciada" className="ml-auto flex shrink-0 items-center gap-2 text-xs text-zinc-500"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400"/><span className="hidden sm:inline">Sesión iniciada</span></span>
      </header>
      {error && <div role="alert" className="flex items-center gap-3 border-b border-red-900/40 bg-red-950/20 px-6 py-3 text-sm text-red-300">{error}<button onClick={reloadBusinesses} className="ml-auto shrink-0 underline">Intentar de nuevo</button></div>}
      <main key={`${session.user.id}:${business}`} className={path === "/chat" ? "h-[calc(100dvh-4rem)]" : "min-h-[calc(100dvh-4rem)]"}>{children}</main>
    </div>
  </div>;
}
