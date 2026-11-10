"use client";
import {analysisStatus} from "@/utils/analysis-presentation";
import {useAuditPolling} from "@/hooks/useAuditPolling";
import {useAnalysisHistory,useAnalysisTrends} from "@/hooks/useAnalysisHistory";
import AnalysisHistory from "./AnalysisHistory";
import {AuditHeader} from "./AuditHeader";
import {PipelineStatusBar} from "./PipelineStatusBar";
import {Layer2Banner} from "./Layer2Banner";
import {ForensicSummary} from "./ForensicSummary";
import {DormantMetricsList} from "./DormantMetricsList";
import AuditTable from "@/components/AuditTable";
import KpiGrid from "./KpiGrid";
import MetricsCharts from "./MetricsCharts";
import {calcResultsToChartRows,mapCalcResultsToKpis} from "@/utils/mapCalcResultsToKpis";
export default function AuditReportView({showMetrics=true,health=false}:{showMetrics?:boolean;health?:boolean}) {
  const history=useAnalysisHistory();
  const {result,pipelineStatus,currentNode,layer3Status,error}=useAuditPolling(history.selectionError?null:history.runId);
  const trends=useAnalysisTrends(history.runId,showMetrics&&Boolean(result)&&!error);
  const failure=history.selectionError||error;
  const report=result?.sequential_results.forensic_report;
  const values=result?.sequential_results.calc_results??[];
  return <div className="relative z-10 min-h-screen px-6 py-8 max-w-7xl mx-auto">
    {health?<header className="glass p-5 mb-4"><h1 className="text-forensic-lg font-semibold">Salud del negocio</h1><p className="text-sm text-zinc-400">Indicadores del análisis seleccionado y su evolución entre fechas.</p></header>
      :<div className="mb-4"><AuditHeader riskLevel={result?.forensic_status_available?report?.risk_level:undefined} date={result?.date}/></div>}
    <AnalysisHistory history={history}/>
    <div data-tour="estado">
      {failure&&<div role="alert" className="glass border border-red-500/30 text-red-300 p-4 mb-4 text-sm"><span>{failure}</span> <button className="underline" onClick={()=>window.location.reload()}>Reintentar</button></div>}
      {history.resolving&&!failure&&<p role="status" className="text-sm text-zinc-400 mb-4">Buscando el último análisis terminado…</p>}
      {history.runId&&!result&&!failure&&<p role="status" className="text-sm text-zinc-400 mb-4">Cargando el análisis guardado…</p>}
      {!history.runId&&!history.resolving&&!failure&&<p className="text-sm text-zinc-400 mb-4">Todavía no hay un análisis terminado para mostrar. Elige uno del historial o prepara uno nuevo en Documentos.</p>}
      {result&&<p role="status" className="mb-4 text-sm text-zinc-300">{analysisStatus[pipelineStatus??"unknown"]??analysisStatus.unknown} · Fecha analizada: {result.date} · Ref. {result.run_id.slice(0,8)}</p>}
    </div>
    {result&&<>
      <div className="mb-4"><PipelineStatusBar status={pipelineStatus??"idle"} currentNode={currentNode??undefined} layer2Status={layer3Status??undefined}/></div>
      {result.escalation.triggered&&layer3Status&&<div className="mb-4"><Layer2Banner layer2Status={layer3Status}/></div>}
      {showMetrics&&pipelineStatus!=="failed"&&<div className="mb-6 space-y-4">
        <h2 data-tour="kpis" className="text-label uppercase tracking-widest text-zinc-400">Indicadores clave</h2>
        <KpiGrid items={mapCalcResultsToKpis(values)}/>
        <MetricsCharts barData={calcResultsToChartRows(values)} trends={trends.data} loading={trends.loading} error={trends.error}/>
      </div>}
      <div className="flex flex-col lg:flex-row gap-6 items-start">
        <div className="w-full lg:flex-[65]"><h2 data-tour="hallazgos" className="text-label uppercase tracking-widest text-zinc-400 mb-3">Hallazgos del análisis</h2>
          <AuditTable rows={result.sequential_results.audit_insights??[]} isLoading={false} emptyMessage="Este análisis no conserva recomendaciones para mostrar."/></div>
        <div className="w-full lg:flex-[35] flex flex-col gap-4">
          <ForensicSummary anomalies={report?.anomalies??[]} available={result.forensic_status_available===true}/>
          <DormantMetricsList metrics={result.dormant_metrics??[]} blocked={result.blocked_metrics??[]} available={result.metric_status_available===true}/>
        </div>
      </div>
    </>}
  </div>;
}
