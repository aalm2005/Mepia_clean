"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useMepiaAuth } from "@/components/auth/MepiaAuthProvider";

export default function OnboardingGate({ children }: { children: React.ReactNode }) {
  const { business } = useMepiaAuth();
  const [complete, setComplete] = useState<boolean | null>(null);
  useEffect(() => {
    if (!business) return;
    const abort = new AbortController();
    setComplete(null);
    fetch("/api/onboarding?business_id=" + encodeURIComponent(business), { cache: "no-store", signal: abort.signal })
      .then(async response => {
        if (abort.signal.aborted) return;
        if (response.ok) { const data = await response.json(); if (!abort.signal.aborted) setComplete(data.onboarding_complete === true); }
        // Conservar el comportamiento previo frente a caída del pipeline; el backend
        // valida onboarding al operar. 401/403 nunca habilitan el formulario.
        else setComplete(![401, 403, 404].includes(response.status));
      }).catch(() => { if (!abort.signal.aborted) setComplete(true); });
    return () => abort.abort();
  }, [business]);
  if (!business) return <p className="text-sm text-zinc-400">Selecciona un negocio para continuar.</p>;
  if (complete === null) return <p className="text-sm text-zinc-400">Comprobando tu negocio…</p>;
  if (!complete) return <div className="flex items-center justify-between gap-4 rounded-xl border border-warning-border bg-warning-bg p-4 text-warning">
    <span className="text-sm font-medium">Configura tu negocio antes de continuar</span>
    <Link href="/onboarding" className="shrink-0 text-sm font-semibold hover:opacity-80">Configurar negocio →</Link>
  </div>;
  return <>{children}</>;
}
