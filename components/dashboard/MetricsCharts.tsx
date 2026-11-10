"use client";
import dynamic from "next/dynamic";
import {CHART_COLORS,type TabularRow} from "@/components/charts/chartTypes";
import type {AnalysisTrend} from "@/types/analysis";
import {metricLabel} from "@/utils/analysis-presentation";
const MetricBarChart=dynamic(()=>import("@/components/charts/MetricBarChart"),{ssr:false});
const MetricLineChart=dynamic(()=>import("@/components/charts/MetricLineChart"),{ssr:false});
export default function MetricsCharts({barData,trends,loading,error}:{barData:TabularRow[];trends:AnalysisTrend|null;loading:boolean;error:string}) {
  const units=Array.from(new Set(barData.map(row=>String(row.unit??"Sin unidad"))));
  return <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
    {(units.length?units:["Sin datos"]).map(unit=><section key={unit} className="glass p-5">
      <h2 className="text-label uppercase tracking-widest text-zinc-400 mb-3">Métricas calculadas · {unit}</h2>
      {barData.length>0&&barData.every(row=>row.value===0)&&<p className="text-sm text-zinc-400 mb-2">Los valores de esta gráfica son cero. Es un resultado válido del análisis.</p>}
      {!barData.length?<p className="text-sm text-zinc-400 py-8">El análisis seleccionado no conserva valores suficientes para esta gráfica. Revisa los indicadores pendientes y los documentos de esa fecha.</p>
      :<MetricBarChart data={barData.filter(r=>String(r.unit??"Sin unidad")===unit).map(r=>({...r,metric:metricLabel(String(r.metric))}))} xKey="metric"
        series={[{dataKey:"value",name:"Valor guardado",color:CHART_COLORS.emerald}]}/>}
    </section>)}
    <section className="glass p-5 xl:col-span-2" aria-label="Evolución de indicadores diarios">
      <h2 data-tour="tendencias" className="text-label uppercase tracking-widest text-zinc-300 mb-3">Evolución de indicadores diarios</h2>
      {loading?<p role="status" className="text-sm text-zinc-400">Cargando resultados de otras fechas…</p>:error?<p role="alert" className="text-sm text-red-300">{error}</p>
      :!trends?.series.length?<p className="text-sm text-zinc-400">No hay indicadores diarios comparables. Se necesitan resultados del mismo indicador y unidad en al menos dos fechas distintas.</p>:<>
        <p className="text-xs text-zinc-400 mb-4">{trends.policy} Las fechas o valores ausentes dejan espacios en la gráfica.</p>
        {trends.series.map(series=><div className="mb-6" key={`${series.metric}:${series.unit}`}>
          <h3 className="text-sm text-zinc-200 mb-2">{series.label} · {series.unit}</h3>
          {series.valid_periods<2?<p className="text-sm text-zinc-400">Datos insuficientes: hay {series.valid_periods} fecha(s) con valor válido. Hace falta el mismo indicador y unidad en otra fecha.</p>
          :<MetricLineChart data={series.points.map(p=>({periodo:p.date,value:p.value===null?null:Number(p.value)}))} xKey="periodo"
            series={[{dataKey:"value",name:`${series.label} (${series.unit})`,color:CHART_COLORS.sky}]}/>}
          {series.missing_periods>0&&<p className="text-xs text-zinc-400">Hay fechas sin análisis o sin un valor comparable de este indicador; no se sustituyen por cero.</p>}
        </div>)}
      </>}
      {trends?.limited&&<p className="text-sm text-amber-300">Vista limitada a las últimas 300 ejecuciones y 90 fechas disponibles hasta la fecha seleccionada. Puede haber análisis anteriores en el historial.</p>}
      {Boolean(trends?.ignored_results)&&<p className="text-xs text-zinc-400">Algunos indicadores no se comparan porque no conservan el detalle necesario para asegurar que midan lo mismo entre fechas.</p>}
    </section>
  </div>;
}
