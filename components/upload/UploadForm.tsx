"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMepiaAuth } from "@/components/auth/MepiaAuthProvider";
import { authenticatedFetch } from "@/utils/authenticated-fetch";
import type { Archetype } from "../AuditTable";
import ArchetypeSelector from "./ArchetypeSelector";
import DocumentDropzone from "./DocumentDropzone";
import type { DropzoneStatus } from "./DocumentDropzone";
import UploadStatusBadge from "./UploadStatusBadge";
import ReviewAlert from "./ReviewAlert";

interface ReviewState {
  fileId: string;
  missingFields: string[];
}

/** Maps HTTP status codes to user-facing Spanish error messages. */
function getApiErrorMessage(status: number, body: unknown): string {
  if (status === 409) return "Faltan datos para iniciar el análisis.";
  if (status === 412) return "Completa el onboarding antes de auditar.";
  if (status === 503) return "El servicio no está disponible.";
  if (status === 422) {
    const detail = (body as { detail?: string } | null)?.detail;
    return detail ?? "Error de validación.";
  }
  return "Error inesperado. Intenta de nuevo.";
}

/**
 * Uploads a single file to the backend and returns the parsed response.
 */
async function uploadSingleFile(
  file: File,
  type: "pos" | "factura",
  business: string
): Promise<{ ok: boolean; status: number; data: unknown }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("type", type);
  formData.append("business_id", business);

  const res = await authenticatedFetch("/api/upload", { method: "POST", body: formData });
  const data = await res.json().catch(() => null);
  return { ok: res.ok, status: res.status, data };
}

export default function UploadForm() {
  const router = useRouter();
  const { business } = useMepiaAuth();

  const [archetype, setArchetype] = useState<Archetype>("Operative Genius");
  const [auditDate, setAuditDate] = useState("2024-01-15");
  const [posFiles, setPosFiles] = useState<File[]>([]);
  const [facturaFiles, setFacturaFiles] = useState<File[]>([]);

  const [posStatus, setPosStatus] = useState<DropzoneStatus>("idle");
  const [facturaStatus, setFacturaStatus] = useState<DropzoneStatus>("idle");

  const [posProgress, setPosProgress] = useState("");
  const [facturaProgress, setFacturaProgress] = useState("");

  const [posReview, setPosReview] = useState<ReviewState | null>(null);
  const [facturaReview, setFacturaReview] = useState<ReviewState | null>(null);

  const [posErrorMessage, setPosErrorMessage] = useState<string | null>(null);
  const [facturaErrorMessage, setFacturaErrorMessage] = useState<string | null>(null);
  const [auditError, setAuditError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  /** Tracks the most recent date from uploaded documents for the audit run */
  const [latestUploadDate, setLatestUploadDate] = useState<string | null>(null);

  // ── Derived state ──────────────────────────────────────────────────────────

  const isPosReviewPending = posStatus === "needs_human_review" && posReview !== null;
  const isFacturaReviewPending = facturaStatus === "needs_human_review" && facturaReview !== null;
  const isReviewPending = isPosReviewPending || isFacturaReviewPending;

  const noFilesSelected = posFiles.length === 0 && facturaFiles.length === 0;

  const isDisabled =
    !business ||
    noFilesSelected ||
    isAnalyzing ||
    isReviewPending ||
    posStatus === "uploading" ||
    facturaStatus === "uploading";

  // ── CTA label ──────────────────────────────────────────────────────────────

  function getCtaLabel(): string {
    if (isPosReviewPending) return "Esperando revisión POS...";
    if (isFacturaReviewPending) return "Esperando revisión Factura...";
    if (isAnalyzing) return "Analizando...";
    const total = posFiles.length + facturaFiles.length;
    if (total > 1) return `Analizar ${total} archivos con Agentes IA →`;
    return "Analizar con Agentes IA →";
  }

  // ── File handlers ──────────────────────────────────────────────────────────

  function handlePosFiles(files: File[]) {
    setPosFiles(files);
    setPosStatus("idle");
    setPosErrorMessage(null);
    setPosReview(null);
  }

  function handleFacturaFiles(files: File[]) {
    setFacturaFiles(files);
    setFacturaStatus("idle");
    setFacturaErrorMessage(null);
    setFacturaReview(null);
  }

  // ── Upload a batch of files sequentially ───────────────────────────────────

  async function uploadBatch(
    files: File[],
    type: "pos" | "factura",
    setStatus: (s: DropzoneStatus) => void,
    setProgress: (p: string) => void,
    setError: (e: string | null) => void,
    setReview: (r: ReviewState | null) => void,
  ): Promise<boolean> {
    if (files.length === 0) return true;

    setStatus("uploading");
    setError(null);

    let succeeded = 0;
    let lastReview: ReviewState | null = null;

    for (let i = 0; i < files.length; i++) {
      setProgress(`${i + 1} / ${files.length} archivos`);

      try {
        const { ok, status, data } = await uploadSingleFile(files[i], type, business);

        if (!ok) {
          const msg = getApiErrorMessage(status, data);
          setError(`Error en ${files[i].name}: ${msg}`);
          setStatus("error");
          return false;
        }

        // Check for human review needed
        const results: Array<{
          needs_human_review: boolean;
          file_id: string;
          missing_fields?: string[];
        }> = Array.isArray(data) ? data : [data];

        const reviewNeeded = results.find((r) => r.needs_human_review);
        if (reviewNeeded) {
          lastReview = {
            fileId: reviewNeeded.file_id,
            missingFields: reviewNeeded.missing_fields ?? [],
          };
        }

        // Track dates from successful uploads for the audit run
        for (const r of results) {
          const d = (r as Record<string, unknown>).date as string | undefined
            ?? ((r as Record<string, unknown>).extracted_fields as Record<string, unknown> | undefined)?.transaction_date as string | undefined;
          if (d && d !== "unknown" && d !== "null") {
            setLatestUploadDate((prev) => (!prev || d > prev) ? d : prev);
          }
        }

        succeeded++;
      } catch {
        setError(`Error inesperado en ${files[i].name}.`);
        setStatus("error");
        return false;
      }
    }

    // If any file needs review, pause on the last one
    if (lastReview) {
      setStatus("needs_human_review" as DropzoneStatus);
      setReview(lastReview);
      setProgress(`${succeeded} / ${files.length} — revisión pendiente`);
      return false;
    }

    setStatus("done");
    setProgress(`${succeeded} archivos procesados`);
    return true;
  }

  // ── Main upload + audit flow ───────────────────────────────────────────────

  async function handleAnalyze() {
    setAuditError(null);

    // Step 1: Upload all POS files
    const posOk = await uploadBatch(
      posFiles, "pos", setPosStatus, setPosProgress, setPosErrorMessage, setPosReview
    );
    if (!posOk) return;

    // Step 2: Upload all Factura files
    const facturaOk = await uploadBatch(
      facturaFiles, "factura", setFacturaStatus, setFacturaProgress, setFacturaErrorMessage, setFacturaReview
    );
    if (!facturaOk) return;

    // Step 3: Trigger audit
    setIsAnalyzing(true);

    try {
      const res = await authenticatedFetch("/api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          archetype,
          business_id: business,
          date: auditDate || latestUploadDate || new Date().toISOString().split("T")[0],
        }),
      });

      const body = await res.json().catch(() => null);

      if (!res.ok) {
        const msg = getApiErrorMessage(res.status, body);
        setAuditError(msg);
        if (res.status === 412) {
          router.push("/onboarding");
        }
        return;
      }

      const result = body as { run_id: string };
      router.push(`/dashboard?run_id=${result.run_id}`);
    } catch {
      setAuditError("Error inesperado. Intenta de nuevo.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  // ── ReviewAlert callbacks ──────────────────────────────────────────────────

  function handlePosReviewed() {
    setPosReview(null);
    setPosStatus("done");
  }

  function handleFacturaReviewed() {
    setFacturaReview(null);
    setFacturaStatus("done");
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div>
      <h1 className="text-forensic-lg font-semibold text-zinc-100 mb-6 uppercase tracking-widest">
        INGESTA — Subir Documentos de Auditoría
      </h1>

      <div className="mb-6">
        <ArchetypeSelector value={archetype} onChange={setArchetype} />
      </div>

      {/* Date picker for audit */}
      <div className="mb-6 flex items-center gap-3">
        <label
          htmlFor="audit-date"
          className="text-xs font-semibold uppercase tracking-widest text-zinc-500"
        >
          Fecha a auditar
        </label>
        <input
          id="audit-date"
          type="date"
          value={auditDate}
          onChange={(e) => setAuditDate(e.target.value)}
          className="glass-input px-3 py-1.5 text-sm text-zinc-200 font-mono"
        />
      </div>

      <div className="grid grid-cols-2 gap-6 mb-4">
        {/* POS column */}
        <div className="flex flex-col gap-2">
          <DocumentDropzone
            label="Ticket POS"
            accept={["application/pdf"]}
            status={posStatus}
            onFiles={handlePosFiles}
            errorMessage={posErrorMessage ?? undefined}
            progressText={posProgress || undefined}
          />
          <UploadStatusBadge status={posStatus} />
          {posFiles.length > 0 && posStatus === "idle" && (
            <p className="text-xs text-zinc-500 font-mono">
              {posFiles.length} archivo{posFiles.length > 1 ? "s" : ""} seleccionado{posFiles.length > 1 ? "s" : ""}
            </p>
          )}
          {posReview && (
            <ReviewAlert
              documentType="pos"
              fileId={posReview.fileId}
              missingFields={posReview.missingFields}
              onReviewed={handlePosReviewed}
            />
          )}
        </div>

        {/* Factura column */}
        <div className="flex flex-col gap-2">
          <DocumentDropzone
            label="Factura de Proveedor"
            accept={["application/pdf", "text/xml", "application/xml"]}
            status={facturaStatus}
            onFiles={handleFacturaFiles}
            errorMessage={facturaErrorMessage ?? undefined}
            progressText={facturaProgress || undefined}
          />
          <UploadStatusBadge status={facturaStatus} />
          {facturaFiles.length > 0 && facturaStatus === "idle" && (
            <p className="text-xs text-zinc-500 font-mono">
              {facturaFiles.length} archivo{facturaFiles.length > 1 ? "s" : ""} seleccionado{facturaFiles.length > 1 ? "s" : ""}
            </p>
          )}
          {facturaReview && (
            <ReviewAlert
              documentType="factura"
              fileId={facturaReview.fileId}
              missingFields={facturaReview.missingFields}
              onReviewed={handleFacturaReviewed}
            />
          )}
        </div>
      </div>

      {auditError && (
        <div
          className="mb-4 px-4 py-3 border border-red-500/40 bg-red-950/30 backdrop-blur rounded-xl text-sm text-red-400 font-mono"
          role="alert"
        >
          {auditError}
        </div>
      )}

      <button
        type="button"
        onClick={handleAnalyze}
        disabled={isDisabled}
        className="glass-btn-primary w-full mt-6 py-3.5 text-sm font-semibold uppercase tracking-widest"
      >
        {getCtaLabel()}
      </button>
    </div>
  );
}
