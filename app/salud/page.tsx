"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useAuditPolling } from "@/hooks/useAuditPolling";
import KpiGrid from "@/components/dashboard/KpiGrid";
import MetricsCharts from "@/components/dashboard/MetricsCharts";
import {
  calcResultsToChartRows,
  mapCalcResultsToKpis,
} from "@/utils/mapCalcResultsToKpis";

function SaludContent() {
  const searchParams = useSearchParams();
  const runId = searchParams.get("run_id");
  const { result, error } = useAuditPolling(runId);

  const calcResults = result?.sequential_results.calc_results ?? [];
  const kpis = mapCalcResultsToKpis(calcResults);
  const barData = calcResultsToChartRows(calcResults);

  return (
    <div className="relative z-10 min-h-screen px-6 py-8 max-w-7xl mx-auto space-y-6">
      <header className="glass p-5">
        <h1 className="text-forensic-lg font-semibold text-zinc-100 uppercase tracking-widest text-glow">
          Salud del negocio
        </h1>
        <p className="text-sm text-zinc-400 mt-1">
          Visualización de métricas operativas a partir de calc_results o series tabulares (Excel/CSV).
        </p>
      </header>

      {error && (
        <div className="glass border border-red-500/30 text-red-400 rounded-2xl p-4 text-sm font-mono">
          {error}
        </div>
      )}

      <KpiGrid items={kpis} />

      <MetricsCharts barData={barData} lineData={[]} />
    </div>
  );
}

export default function SaludPage() {
  return (
    <Suspense fallback={<div className="text-muted text-sm p-10">Cargando...</div>}>
      <SaludContent />
    </Suspense>
  );
}
