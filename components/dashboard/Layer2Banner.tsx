"use client";

import { useState } from "react";

interface Layer2BannerProps {
  layer2Status: "running" | "completed" | "failed";
  onDismiss?: () => void;
}

function Spinner() {
  return (
    <svg
      className="animate-spin h-4 w-4 shrink-0"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z"
      />
    </svg>
  );
}

export function Layer2Banner({ layer2Status, onDismiss }: Layer2BannerProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  function handleDismiss() {
    setDismissed(true);
    onDismiss?.();
  }

  return (
    <div className="bg-amber-950/30 border border-amber-700 rounded p-3 flex items-center justify-between">
      <div className="flex items-center gap-2">
        {layer2Status === "running" && (
          <>
            <Spinner />
            <span className="text-sm font-mono text-amber-400">
              Preparando el informe avanzado…
            </span>
          </>
        )}
        {layer2Status === "completed" && (
          <span className="text-sm font-mono text-accent">
            Informe avanzado guardado.
          </span>
        )}
        {layer2Status === "failed" && (
          <span className="text-sm font-mono text-red-400">
            No fue posible guardar el informe avanzado. Los indicadores guardados siguen disponibles.
          </span>
        )}
      </div>
      <button
        onClick={handleDismiss}
        className="text-amber-400 hover:text-amber-200 transition-colors ml-4 text-base leading-none font-mono shrink-0"
        aria-label="Cerrar banner"
      >
        ×
      </button>
    </div>
  );
}
