"use client";
import {analysisLabel,analysisStatus} from "@/utils/analysis-presentation";
import type {useAnalysisHistory} from "@/hooks/useAnalysisHistory";
export default function AnalysisHistory({history}:{history:ReturnType<typeof useAnalysisHistory>}) {
  return <section className="glass p-5 mb-4 space-y-3" aria-label="Historial de análisis">
    <h2 className="text-label uppercase tracking-widest text-zinc-300">Historial de análisis</h2>
    <p className="text-sm text-zinc-400">Consulta resultados guardados sin volver a analizar los documentos.</p>
    <label data-tour="historial" className="block text-sm" htmlFor="analysis-history">Análisis guardado</label>
    <select id="analysis-history" className="w-full rounded-lg bg-surface border border-white/20 p-3 text-sm" value={history.runId??""}
      onChange={e=>{if(e.target.value)history.select(e.target.value);}}>
      <option value="" disabled>{history.loading?"Cargando historial…":"Elige un análisis"}</option>
      {history.runId&&!history.items.some(i=>i.run_id===history.runId)&&<option value={history.runId}>Análisis del enlace · Ref. {history.runId.slice(0,8)}</option>}
      {history.items.map((item,index)=><option key={item.run_id} value={item.run_id}>Análisis {index+1} · {analysisLabel(item)} · {analysisStatus[item.status]??analysisStatus.unknown}</option>)}
    </select>
    {history.loading&&<p role="status" className="text-sm text-zinc-400">Cargando historial…</p>}
    {!history.loading&&!history.historyError&&!history.items.length&&<p className="text-sm text-zinc-400">No hay análisis guardados para este negocio. En Documentos puedes preparar un análisis nuevo.</p>}
    {history.historyError&&<p role="alert" className="text-sm text-red-300">{history.historyError} <button className="underline" onClick={history.retry}>Reintentar</button></p>}
    {history.more&&<button disabled={history.loading} onClick={history.more} className="text-sm underline">Ver análisis anteriores</button>}
  </section>;
}
