"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const SESSION_KEY = "mepia_splash_seen";

/**
 * Pantalla de bienvenida de sesión.
 * Se muestra una sola vez por pestaña/sesión; "Iniciar" hace fade-out
 * y entra al dashboard sin recargar la app.
 */
export default function WelcomeSplash() {
  const router = useRouter();
  const [leaving, setLeaving] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      if (sessionStorage.getItem(SESSION_KEY) === "1") {
        router.replace("/dashboard");
        return;
      }
    } catch {
      // sessionStorage puede fallar en modo restringido; se muestra el splash.
    }
    setReady(true);
  }, [router]);

  function handleStart() {
    if (leaving) return;
    setLeaving(true);
    try {
      sessionStorage.setItem(SESSION_KEY, "1");
    } catch {
      /* ignore */
    }
    window.setTimeout(() => {
      router.push("/dashboard");
    }, 520);
  }

  if (!ready) {
    return <div className="min-h-screen" />;
  }

  return (
    <div className={`splash-screen ${leaving ? "is-leaving" : ""}`}>
      <div className="relative z-10 flex flex-col items-center text-center max-w-xl">
        <p className="splash-subtitle text-emerald-400 text-sm tracking-[0.35em] uppercase mb-4 font-medium text-glow">
          Mise En Place AI
        </p>

        <h1 className="splash-title text-shine text-6xl md:text-7xl font-bold tracking-tight mb-4">
          MEPIA
        </h1>

        <p className="splash-subtitle text-zinc-400 text-lg leading-relaxed max-w-md mb-10">
          Copiloto financiero para restaurantes.
          <br />
          <span className="text-emerald-300/80">
            Auditoría forense con agentes de IA.
          </span>
        </p>

        <button
          type="button"
          onClick={handleStart}
          className="splash-cta glass-btn-start px-12 py-3.5 text-sm font-semibold uppercase"
        >
          Iniciar
        </button>
      </div>
    </div>
  );
}
