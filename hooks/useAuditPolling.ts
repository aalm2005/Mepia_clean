"use client";

import { useEffect, useRef, useState } from "react";
import type { OrchestratorResult, PipelineStatus } from "@/types/audit";
import { useMepiaAuth } from "@/components/auth/MepiaAuthProvider";
import { authenticatedFetch } from "@/utils/authenticated-fetch";

interface Layer3StatusResponse {
  layer3_run_id: string;
  status: "running" | "completed" | "failed";
  draft_status?: "approved" | "approved_with_warning";
  current_node?: string;
  intentos_critico?: number;
  started_at?: string;
  completed_at?: string;
}

interface UseAuditPollingResult {
  /** Full orchestrator result (available after pipeline reaches terminal status) */
  result: OrchestratorResult | null;
  /** Current pipeline status from polling */
  pipelineStatus: PipelineStatus | null;
  /** Current node being executed in the pipeline */
  currentNode: string | null;
  /** Layer 3 status (only when escalation triggered Layer 3) */
  layer3Status: "running" | "completed" | "failed" | null;
  /** Layer 3 draft status (approved / approved_with_warning) */
  layer3DraftStatus: string | null;
  /** Error message if any polling step fails */
  error: string | null;
}

/** Recupera resultados guardados del negocio autorizado y sigue únicamente estados en proceso. */
export function useAuditPolling(
  runId: string | null,
  intervalMs: number = 2000
): UseAuditPollingResult {
  const { session, business, rememberAudit } = useMepiaAuth();
  const user = session?.user.id;
  const scopeKey = `${user}:${business}:${runId}`;
  const [readKey,setReadKey] = useState("");
  const [result, setResult] = useState<OrchestratorResult | null>(null);
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(
    null
  );
  const [currentNode, setCurrentNode] = useState<string | null>(null);
  const [layer3Status, setLayer3Status] = useState<
    "running" | "completed" | "failed" | null
  >(null);
  const [layer3DraftStatus, setLayer3DraftStatus] = useState<string | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);

  const mainIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const layer3IntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    // Clear even when runId is removed; a business change also removes its query.
    setReadKey(scopeKey);
    setResult(null);
    setPipelineStatus(null);
    setCurrentNode(null);
    setLayer3Status(null);
    setLayer3DraftStatus(null);
    setError(null);
    if (!runId || !business || !user) return;
    const abort = new AbortController();
    let active = true;
    const isCurrent = () => active && !abort.signal.aborted;

    const clearMainInterval = () => {
      if (mainIntervalRef.current !== null) {
        clearInterval(mainIntervalRef.current);
        mainIntervalRef.current = null;
      }
    };

    const clearLayer3Interval = () => {
      if (layer3IntervalRef.current !== null) {
        clearInterval(layer3IntervalRef.current);
        layer3IntervalRef.current = null;
      }
    };

    /**
     * Fetch the full orchestrator result once pipeline reaches terminal status.
     * If escalated, start Layer 3 polling.
     */
    const fetchFinalResult = async () => {
      try {
        const res = await authenticatedFetch(`/api/analyses/${business}/${runId}`, { signal: abort.signal });
        const payload = await res.json();
        if (!res.ok) throw new Error(payload?.detail ?? "No fue posible recuperar el análisis guardado.");
        const data: OrchestratorResult = payload;
        if (!isCurrent()) return;
        if (data.business_id !== business || data.run_id !== runId) {
          throw new Error("Este análisis no corresponde al negocio seleccionado.");
        }
        setPipelineStatus(data.pipeline_status);
        setResult(data);
        rememberAudit(runId);
        if (data.pipeline_status !== "running") clearMainInterval();
        if (data.pipeline_status === "failed") setError("Este análisis falló. Elige otro del historial o revisa los documentos antes de iniciar uno nuevo.");

        // If escalated → start Layer 3 polling using layer2_run_id
        // The backend triggers Layer 3 automatically when escalation happens
        if (
          data.escalation.triggered &&
          data.escalation.layer2_run_id !== null
        ) {
          clearLayer3Interval();

          const pollLayer3 = async () => {
            try {
              const l3Res = await authenticatedFetch(
                `/api/analyses/${business}/${runId}/layer3`, { signal: abort.signal }
              );
              if (!l3Res.ok) {
                // 404 means Layer 3 hasn't started yet — not an error
                if (l3Res.status === 404) return;
                throw new Error(
                  "No fue posible consultar el informe avanzado. Intenta de nuevo."
                );
              }
              const l3Data: Layer3StatusResponse = await l3Res.json();
              if (!isCurrent()) return;
              setLayer3Status(l3Data.status);
              setLayer3DraftStatus(l3Data.draft_status ?? null);

              if (l3Data.current_node) {
                setCurrentNode(l3Data.current_node);
              }

              // Stop polling when Layer 3 reaches terminal status
              if (
                l3Data.status === "completed" ||
                l3Data.status === "failed"
              ) {
                clearLayer3Interval();
              }
            } catch (err) {
              if (!isCurrent()) return;
              setError(
                err instanceof Error
                  ? err.message
                  : "No fue posible consultar el informe avanzado."
              );
              clearLayer3Interval();
            }
          };

          // Poll immediately, then on interval
          layer3IntervalRef.current = setInterval(pollLayer3, intervalMs);
          await pollLayer3();
        }
      } catch (err) {
        if (!isCurrent()) return;
        clearMainInterval();
        setError(err instanceof TypeError || err instanceof SyntaxError ? "No fue posible conectar con MEPIA. Revisa tu conexión e intenta de nuevo." : err instanceof Error ? err.message : "No fue posible recuperar el análisis guardado.");
      }
    };

    /**
     * Main polling — polls orchestrator status until terminal.
     * Terminal statuses: completed, partial, escalated, failed
     */
    const pollStatus = async () => {
      await fetchFinalResult();
    };

    // Kick off immediately, then on interval
    mainIntervalRef.current = setInterval(pollStatus, intervalMs);
    void pollStatus();

    return () => {
      active = false;
      abort.abort();
      clearMainInterval();
      clearLayer3Interval();
    };
  }, [runId, intervalMs, business, user, rememberAudit]);

  const visible = readKey===scopeKey && result?.business_id === business && result?.run_id === runId;
  return {
    result: visible ? result : null,
    pipelineStatus: visible ? pipelineStatus : null,
    currentNode: visible ? currentNode : null,
    layer3Status: visible ? layer3Status : null,
    layer3DraftStatus: visible ? layer3DraftStatus : null,
    error: readKey===scopeKey ? error : null,
  };
}
