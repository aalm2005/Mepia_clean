"use client";
import {useEffect, useRef, useState} from "react";
import {usePathname, useRouter, useSearchParams} from "next/navigation";
import {useMepiaAuth} from "@/components/auth/MepiaAuthProvider";
import {authenticatedFetch} from "@/utils/authenticated-fetch";
import type {AnalysisSummary, AnalysisTrend} from "@/types/analysis";
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export async function analysisJson(path: string, signal: AbortSignal) {
  let res: Response;
  let data;
  try {
    res = await authenticatedFetch(path, {signal});
    data = await res.json();
  } catch {
    throw new Error("No fue posible conectar con MEPIA. Revisa tu conexión e intenta de nuevo.");
  }
  if (!res.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "No fue posible cargar el análisis. Intenta de nuevo.");
  return data;
}
export function useAnalysisHistory() {
  const {session,business,auditRunId,rememberAudit} = useMepiaAuth();
  const search = useSearchParams(), router = useRouter(), path = usePathname();
  const explicit = search.has("run_id"), queryRun = search.get("run_id")?.toLowerCase() ?? null;
  const runId = explicit ? queryRun : auditRunId;
  const scope = `${session?.user.id ?? ""}:${business}`;
  const current = useRef(scope); current.current = scope;
  const [page,setPage] = useState(0), [reload,setReload] = useState(0);
  const [state,setState] = useState<{scope:string;items:AnalysisSummary[];next:number|null;loading:boolean;error:string}>({scope:"",items:[],next:null,loading:true,error:""});
  const [latest,setLatest] = useState<{scope:string;loading:boolean;error:string}>({scope:"",loading:true,error:""});
  useEffect(() => {setPage(0);},[scope]);
  useEffect(() => {
    if (!session || !business) return;
    const abort=new AbortController();
    setState(s=>({scope,items:s.scope===scope?s.items:[],next:null,loading:true,error:""}));
    analysisJson(`/api/analyses/${business}?page=${page}`,abort.signal).then(data=>{
      if (abort.signal.aborted || current.current!==scope) return;
      if(data.business_id!==business) throw new Error("El historial no corresponde al negocio seleccionado.");
      setState(s=>({scope,items:Array.from(new Map((page && s.scope===scope?[...s.items,...data.items]:data.items).map((i:AnalysisSummary)=>[i.run_id,i])).values()) as AnalysisSummary[],
        next:data.next_page,loading:false,error:""}));
    }).catch(error=>{if(!abort.signal.aborted && current.current===scope) setState(s=>({...s,scope,loading:false,error:error.message}));});
    return ()=>abort.abort();
  },[scope,business,session?.user.id,page,reload]);
  useEffect(()=>{
    if (!session || !business || explicit || auditRunId) return;
    const abort=new AbortController();
    setLatest({scope,loading:true,error:""});
    analysisJson(`/api/analyses/${business}/latest`,abort.signal).then(data=>{
      if(abort.signal.aborted || current.current!==scope) return;
      if(data.business_id!==business) throw new Error("El análisis no corresponde al negocio seleccionado.");
      if(data.analysis) {rememberAudit(data.analysis.run_id);router.replace(`${path}?run_id=${encodeURIComponent(data.analysis.run_id)}`,{scroll:false});}
      setLatest({scope,loading:false,error:data.limited?"No se encontró un análisis terminado entre los últimos 10 000. Busca uno en el historial.":""});
    }).catch(error=>{if(!abort.signal.aborted && current.current===scope) setLatest({scope,loading:false,error:error.message});});
    return ()=>abort.abort();
  },[scope,business,session?.user.id,explicit,auditRunId,path,router,rememberAudit,reload]);
  // Hacer explícita en el enlace la selección recordada para soportar recarga/copiar enlace.
  useEffect(()=>{if(!explicit && auditRunId) router.replace(`${path}?run_id=${encodeURIComponent(auditRunId)}`,{scroll:false});},[explicit,auditRunId,path,router]);
  const visible=state.scope===scope?state:{scope,items:[],next:null,loading:true,error:""};
  return {runId,items:visible.items,loading:visible.loading,historyError:visible.error,
    resolving:!explicit&&!auditRunId&&(latest.scope!==scope||latest.loading),
    selectionError:explicit && !uuid.test(queryRun??"")?"La referencia del análisis no es válida. Elige uno del historial.":latest.scope===scope&&!explicit&&!auditRunId?latest.error:"",
    more:visible.next===null?null:()=>setPage(visible.next!),retry:()=>setReload(n=>n+1),
    select:(run:string)=>{rememberAudit(run);router.replace(`${path}?run_id=${encodeURIComponent(run)}`,{scroll:false});}};
}
export function useAnalysisTrends(runId:string|null, enabled:boolean) {
  const {session,business}=useMepiaAuth();
  const key=`${session?.user.id}:${business}:${runId}`;
  const [state,setState]=useState<{key:string;data:AnalysisTrend|null;loading:boolean;error:string}>({key:"",data:null,loading:false,error:""});
  useEffect(()=>{
    if(!enabled||!session||!business||!runId) return;
    const abort=new AbortController();setState({key,data:null,loading:true,error:""});
    analysisJson(`/api/analyses/${business}/${runId}/trends`,abort.signal).then(data=>{
      if(abort.signal.aborted) return;
      if(data.business_id!==business||data.run_id!==runId) throw new Error("Las tendencias no corresponden al análisis seleccionado.");
      setState({key,data,loading:false,error:""});
    }).catch(error=>{if(!abort.signal.aborted)setState({key,data:null,loading:false,error:error.message});});
    return ()=>abort.abort();
  },[key,enabled,session?.user.id,business,runId]);
  return enabled&&state.key===key?state:{data:null,loading:enabled,error:""};
}
