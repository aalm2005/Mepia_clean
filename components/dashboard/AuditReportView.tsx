"use client";

import { useSearchParams } from "next/navigation";
import { useAuditPolling } from "@/hooks/useAuditPolling";
import { AuditHeader } from "@/components/dashboard/AuditHeader";
import { PipelineStatusBar } from "@/components/dashboard/PipelineStatusBar";
import { Layer2Banner } from "@/components/dashboard/Layer2Banner";
import { ForensicSummary } from "@/components/dashboard/ForensicSummary";
import { DormantMetricsList } from "@/components/dashboard/DormantMetricsList";
import AuditTable from "@/components/AuditTable";
import KpiGrid from "@/components/dashboard/KpiGrid";
import MetricsCharts from "@/components/dashboard/MetricsCharts";
import {
  calcResultsToChartRows,
  mapCalcResultsToKpis,
} from "@/utils/mapCalcResultsToKpis";
import type { TabularRow } from "@/components/charts/chartTypes";

interface AuditReportViewProps {
  /** Muestra KPI + gráficas encima de la tabla forense */
  showMetrics?: boolean;
}

/**
 * Vista funcional de métricas/auditoría.
 * Conserva el mismo hook, tipos y flujo de polling; solo cambia la presentación.
 */
export default function AuditReportView({ showMetrics = true }: AuditReportViewProps) {
  const searchParams = useSearchParams();
  const runId = searchParams.get("run_id");

  const { result, pipelineStatus, currentNode, layer3Status, error } =
    useAuditPolling(runId);

  const riskLevel =
    result?.sequential_results.forensic_report.risk_level ?? "low";
  const date = result?.date;
  const isEscalated = result?.escalation.triggered === true;
  const calcResults = result?.sequential_results.calc_results ?? [];
  const kpis = mapCalcResultsToKpis(calcResults);
  const barData = calcResultsToChartRows(calcResults);

  // Historial: el orquestador actual es por corrida (un punto).
  // La gráfica de línea queda lista para un array tabular de periodos.
  const lineData: TabularRow[] = [];

  return (
    <div className="relative z-10 min-h-screen px-6 py-8 max-w-7xl mx-auto">
      <div className="mb-4">
        <AuditHeader riskLevel={riskLevel} date={date} />
      </div>

      <div className="mb-4">
        <PipelineStatusBar
          status={pipelineStatus ?? "idle"}
          currentNode={currentNode ?? undefined}
          layer2Status={layer3Status ?? undefined}
        />
      </div>

      {isEscalated && layer3Status && (
        <div className="mb-4">
          <Layer2Banner layer2Status={layer3Status} />
        </div>
      )}

      {error && (
        <div className="mb-4 glass border border-red-500/30 text-red-400 rounded-2xl p-4 text-sm font-mono">
          {error}
        </div>
      )}

      {pipelineStatus === null && !error && (
        <p className="text-muted text-sm mb-4">{runId ? "Iniciando análisis..." : "Aquí aparecerán los resultados cuando completes un análisis."}</p>
      )}

      {showMetrics && (
        <div className="mb-6 space-y-4">
          <KpiGrid items={kpis} />
          <MetricsCharts barData={barData} lineData={lineData} />
        </div>
      )}

      <div className="flex flex-col lg:flex-row gap-6 items-start">
        <div className="w-full lg:flex-[65]">
          <h2 className="text-label uppercase tracking-widest text-zinc-400 mb-3">
            Hallazgos forenses
          </h2>
          <AuditTable
            rows={result?.sequential_results.audit_insights ?? []}
            isLoading={Boolean(runId) && !result && !error}
            emptyMessage="Sin resultados de auditoría"
          />
        </div>

        <div className="w-full lg:flex-[35] flex flex-col gap-4">
          <ForensicSummary
            anomalies={result?.sequential_results.forensic_report.anomalies ?? []}
          />
          <DormantMetricsList metrics={result?.dormant_metrics ?? []}
            blocked={result?.blocked_metrics ?? []}
            available={result ? result.metric_status_available === true : undefined} />
        </div>
      </div>
    </div>
  );
}
