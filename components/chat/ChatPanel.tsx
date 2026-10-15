"use client";
import { FormEvent, useEffect, useRef, useState } from "react";
import { getSupabaseBrowser } from "@/utils/supabase-browser";
import { useMepiaAuth } from "@/components/auth/MepiaAuthProvider";
import { MepiaIcon } from "@/components/ui/MepiaIcon";
import type { ChatTurn } from "@/types/chat";

function MetricStatuses({ data }: { data: Record<string, unknown> }) {
  if (!Array.isArray(data.metrics)) return null;
  const labels: Record<string, string> = { ok: "Resultado emitido", warning: "Advertencia",
    critical: "Alerta crítica", incomplete_data: "Datos incompletos", error: "Error" };
  return <div className="flex flex-wrap gap-2" aria-label="Estados emitidos por S3">
    {data.metrics.map((raw: unknown, index: number) => {
      if (!raw || typeof raw !== "object") return null;
      const metric = raw as Record<string, unknown>; const status = String(metric.status ?? "");
      const color = status === "critical" || status === "error" ? "text-red-300 border-red-800"
        : status === "warning" ? "text-amber-300 border-amber-800" : "text-zinc-300 border-zinc-700";
      return <span key={index} className={"rounded-lg border px-2.5 py-1 text-xs " + color}>
        {String(metric.metric ?? "Métrica")} · {labels[status] ?? status}
      </span>;
    })}
  </div>;
}

export function ChatPanel() {
  const { session, business, businesses, businessesLoading } = useMepiaAuth();
  const [date, setDate] = useState("");
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [conversation, setConversation] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const epoch = useRef(0);
  const inflight = useRef<AbortController | null>(null);
  const end = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const activeUser = useRef(session?.user.id);
  activeUser.current = session?.user.id;

  useEffect(() => () => { epoch.current++; inflight.current?.abort(); }, []);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [turns.length, pending, busy]);

  async function request(path: string, method = "GET", body?: unknown, signal?: AbortSignal) {
    const { data } = await getSupabaseBrowser().auth.getSession();
    if (!data.session || data.session.user.id !== activeUser.current) throw new Error("Inicia sesión de nuevo.");
    const res = await fetch(path, {
      method, headers: { Authorization: "Bearer " + data.session.access_token, "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body), cache: "no-store", signal,
    });
    if (res.status === 204) return null;
    const result = await res.json();
    if (!res.ok) throw new Error(result.detail ?? "Chat no disponible");
    return result;
  }
  function resetScope() {
    epoch.current++; inflight.current?.abort();
    setTurns([]); setConversation(null); setQuestion(""); setPending(""); setError(""); setBusy(false);
  }
  async function send(event: FormEvent) {
    event.preventDefault();
    if (busy || !business || !question.trim()) return;
    const current = epoch.current; const submitted = question.trim();
    const abort = new AbortController(); inflight.current = abort;
    setBusy(true); setError(""); setPending(submitted); setQuestion("");
    try {
      const data = await request("/api/chat/" + business, "POST", {
        question: submitted, requested_date: date || null, conversation_id: conversation,
      }, abort.signal);
      if (current !== epoch.current) return;
      setConversation(data.conversation_id);
      setTurns(previous => [...previous, { question: submitted, answer: data.answer }].slice(-8));
    } catch (e) {
      if (!abort.signal.aborted && current === epoch.current) { setError((e as Error).message); setQuestion(submitted); }
    } finally { if (current === epoch.current) { setPending(""); setBusy(false); } }
  }
  async function historyAction(remove: boolean) {
    if (!conversation || busy) return;
    const current = epoch.current; setBusy(true); setError("");
    const abort = new AbortController(); inflight.current = abort;
    try {
      const data = await request("/api/chat/" + business + "/" + conversation, remove ? "DELETE" : "GET", undefined, abort.signal);
      if (current !== epoch.current) return;
      if (remove) resetScope(); else setTurns(data.turns);
    } catch (e) { if (!abort.signal.aborted && current === epoch.current) setError((e as Error).message); }
    finally { if (current === epoch.current) setBusy(false); }
  }
  const hasMessages = turns.length > 0 || !!pending;
  const ownName = businesses.find(item => item.id === business)?.business_name;
  return <section className="flex h-full min-h-0 flex-col bg-[#212121]" aria-label="Chat IA">
    <header className="flex flex-wrap items-center gap-3 px-5 py-4 sm:px-7">
      <div><h1 className="text-lg font-medium">Chat IA <span className="ml-2 text-xs font-normal text-zinc-500">MEPIA</span></h1>
        <p className="mt-0.5 text-xs text-zinc-500">Consulta resultados de tu negocio</p></div>
      <div className="ml-auto flex items-center gap-3">
        <label className="flex items-center gap-2 text-xs text-zinc-400">Fecha (opcional)<input type="date" value={date} onChange={e => { resetScope(); setDate(e.target.value); }}
          className="max-w-[145px] rounded-lg border border-white/10 bg-transparent px-2 py-1.5 text-xs text-zinc-300 [color-scheme:dark]"/></label>
        <button aria-label="Nueva conversación" title="Nueva conversación" onClick={() => { resetScope(); input.current?.focus(); }} className="rounded-lg p-2 text-zinc-400 hover:bg-white/5 hover:text-white"><MepiaIcon name="plus"/></button>
      </div>
    </header>
    <div className="min-h-0 flex-1 overflow-y-auto px-5 sm:px-8" aria-live="polite">
      {!hasMessages ? <div className="mx-auto flex min-h-full max-w-2xl flex-col items-center justify-center pb-10 text-center">
        <span className="mb-6 grid h-12 w-12 place-items-center rounded-2xl bg-emerald-400/10 text-emerald-300"><MepiaIcon name="chat" className="h-6 w-6"/></span>
        <h2 className="text-2xl font-medium tracking-tight sm:text-3xl">¿Qué quieres saber de tu negocio?</h2>
        <p className="mt-3 max-w-md text-sm leading-relaxed text-zinc-400">{ownName ? "Consulta tus métricas, explora los informes y entiende lo que significan." : businessesLoading ? "Estamos cargando tus negocios…" : "Selecciona un negocio para empezar."}</p>
        <div className="mt-8 grid w-full gap-3 sm:grid-cols-3">
          {["¿Cuál fue el ticket promedio?", "¿Qué dice el informe?", "¿Qué significa el margen bruto?"].map((suggestion, index) =>
            <button key={suggestion} disabled={!business} onClick={() => { setQuestion(suggestion); input.current?.focus(); }}
              className="rounded-2xl border border-white/10 p-4 text-left text-sm text-zinc-300 transition-colors hover:bg-white/5 disabled:opacity-40">
              <MepiaIcon name={index === 0 ? "dashboard" : index === 1 ? "upload" : "chat"} className="mb-3 h-5 w-5 text-zinc-500"/>{suggestion}
            </button>)}
        </div>
        {!businessesLoading && !businesses.length && <p className="mt-6 text-xs text-zinc-500">Tu cuenta aún no tiene un negocio asignado.</p>}
      </div> : <div className="mx-auto max-w-3xl space-y-9 pb-8 pt-5">
        {turns.map((turn, index) => <article key={index} className="space-y-6">
          <div className="flex justify-end"><div className="max-w-[85%] rounded-3xl bg-[#303030] px-5 py-3 text-[15px] leading-relaxed"><span className="sr-only">Tú: </span>{turn.question}</div></div>
          <div className="flex items-start gap-3 sm:gap-4">
            <span className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-full border border-emerald-400/20 text-emerald-300"><MepiaIcon name="chat" className="h-4 w-4"/></span>
            <div className="min-w-0 flex-1 space-y-4"><p className="text-xs font-medium text-zinc-400">MEPIA</p>
              {turn.answer.parts.map((part, p) => <div key={p} className="space-y-3">
                <p className="whitespace-pre-wrap text-[15px] leading-7 text-zinc-200">{part.message}</p>
                {(part.kind === "result" || part.kind === "metrics") && <MetricStatuses data={part.data}/>}
                {part.generation_status === "fallback" && part.status === "ok" && <div>
                  <p className="text-xs leading-relaxed text-amber-300">Mostramos los datos disponibles; no se obtuvo una explicación validada.</p>
                  <details className="mt-2 text-xs text-zinc-400"><summary className="cursor-pointer">Ver datos disponibles</summary><pre className="mt-2 overflow-auto whitespace-pre-wrap rounded-lg bg-black/10 p-3">{JSON.stringify(part.data, null, 2)}</pre></details>
                </div>}
                {!!part.missing_data.length && <p className="text-sm text-amber-300">Información faltante: {part.missing_data.join(", ")}</p>}
                <details className="rounded-xl border border-white/5 px-3 py-2 text-xs text-zinc-500"><summary className="cursor-pointer text-zinc-400">Fuentes y trazabilidad</summary>
                  <div className="mt-3 space-y-2 break-all"><p>Fecha de la evidencia: {turn.answer.resolved_date ?? "Sin resultados disponibles"}</p><p>Negocio: {turn.answer.business_id}</p>
                  {part.evidence.map(source => <p key={source.audit_result_id}>{source.node_id} · {source.date} · {source.audit_result_id}<br/>Ejecución S3: {source.source_s3_result_id ?? "No disponible"}</p>)}
                  {part.claims.flatMap(claim => claim.sources).map((source, s) => <p key={s}>{source.label} · {source.path}</p>)}</div>
                </details>
              </div>)}
            </div>
          </div>
        </article>)}
        {pending && <div className="flex justify-end"><p className="max-w-[85%] rounded-3xl bg-[#303030] px-5 py-3 text-[15px] leading-relaxed">{pending}</p></div>}
        {busy && <p role="status" className="flex items-center gap-3 text-sm text-zinc-400"><span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400"/>Consultando…</p>}
        <div ref={end}/>
      </div>}
    </div>
    <div className="shrink-0 px-5 pb-4 pt-3 sm:px-8">
      <div className="mx-auto max-w-3xl">
        {error && <p role="alert" className="mb-3 rounded-xl border border-red-900/50 bg-red-950/20 p-3 text-sm text-red-300">{error}</p>}
        {conversation && <div className="mb-3 flex gap-4 text-xs text-zinc-500">
          <button disabled={busy} onClick={() => historyAction(false)} className="hover:text-zinc-300 disabled:opacity-40">Recargar historial</button>
          <button disabled={busy} onClick={() => historyAction(true)} className="hover:text-zinc-300 disabled:opacity-40">Eliminar conversación</button>
        </div>}
        <form onSubmit={send} className="rounded-3xl border border-white/5 bg-[#303030] px-4 pb-3 pt-4 shadow-sm focus-within:border-white/15">
          <label htmlFor="question" className="sr-only">Pregunta sobre tus métricas</label>
          <textarea ref={input} id="question" maxLength={2000} rows={2} disabled={busy || !business} value={question}
            onChange={e => setQuestion(e.target.value)} onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); e.currentTarget.form?.requestSubmit(); } }}
            placeholder="Pregunta a MEPIA…" className="w-full resize-none bg-transparent px-1 text-[15px] leading-6 text-zinc-100 outline-none placeholder:text-zinc-500 disabled:opacity-40"/>
          <div className="flex items-center justify-between gap-3"><span className="text-[11px] text-zinc-500">Consulta resultados existentes</span>
            <button aria-label="Enviar pregunta" title="Enviar pregunta" disabled={busy || !business || !question.trim()} className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-zinc-100 text-zinc-950 transition-colors hover:bg-white disabled:bg-zinc-600 disabled:text-zinc-400"><MepiaIcon name="send" className="h-5 w-5"/></button>
          </div>
        </form>
        <p className="mt-3 text-center text-[10px] leading-relaxed text-zinc-500">MEPIA consulta y explica; no calcula ni modifica tu negocio. Historial temporal: ocho turnos y treinta minutos de inactividad.</p>
      </div>
    </div>
  </section>;
}
