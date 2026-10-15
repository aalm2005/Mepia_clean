"use client";

import { useRef, useState } from "react";

export type DropzoneStatus = "idle" | "uploading" | "done" | "error" | "needs_human_review";

interface DocumentDropzoneProps {
  label: string;
  accept: string[]; // MIME types, e.g. ["application/pdf", "text/xml"]
  status: DropzoneStatus;
  onFiles: (files: File[]) => void;
  errorMessage?: string;
  /** Progress text shown during upload, e.g. "3 / 5 archivos" */
  progressText?: string;
}

function Spinner() {
  return (
    <svg
      className="animate-spin h-6 w-6 text-zinc-400 mx-auto"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      className="h-6 w-6 text-emerald-500 mx-auto"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2.5}
      aria-hidden="true"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}

function ErrorIcon() {
  return (
    <svg
      className="h-6 w-6 text-red-500 mx-auto"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2.5}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
      />
    </svg>
  );
}

export default function DocumentDropzone({
  label,
  accept,
  status,
  onFiles,
  errorMessage,
  progressText,
}: DocumentDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [mimeError, setMimeError] = useState<string | null>(null);
  const [fileCount, setFileCount] = useState(0);

  const isInteractive = status === "idle" || status === "error";

  function validateAndDispatch(fileList: FileList | File[]) {
    setMimeError(null);
    const files = Array.from(fileList);
    const valid: File[] = [];
    for (const file of files) {
      // Allow files whose MIME matches OR whose extension matches common types
      const ext = file.name.toLowerCase();
      const mimeOk = accept.includes(file.type);
      const extOk =
        (accept.includes("application/pdf") && ext.endsWith(".pdf")) ||
        (accept.includes("text/xml") && (ext.endsWith(".xml"))) ||
        (accept.includes("application/xml") && (ext.endsWith(".xml")));
      if (mimeOk || extOk) {
        valid.push(file);
      }
    }
    if (valid.length === 0) {
      setMimeError(
        `Ningún archivo tiene tipo permitido. Se acepta: ${accept.join(", ")}`
      );
      return;
    }
    setFileCount(valid.length);
    onFiles(valid);
  }

  function handleClick() {
    if (!isInteractive) return;
    inputRef.current?.click();
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (!isInteractive) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      inputRef.current?.click();
    }
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (files && files.length > 0) validateAndDispatch(files);
    e.target.value = "";
  }

  function handleDragOver(e: React.DragEvent<HTMLDivElement>) {
    if (!isInteractive) return;
    e.preventDefault();
    setIsDragOver(true);
  }

  function handleDragLeave(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragOver(false);
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragOver(false);
    if (!isInteractive) return;
    const files = e.dataTransfer.files;
    if (files && files.length > 0) validateAndDispatch(files);
  }

  const borderClass =
    status === "done"
      ? "border-emerald-500/60"
      : status === "error"
      ? "border-red-500/60"
      : status === "needs_human_review"
      ? "border-amber-500/60"
      : isDragOver
      ? "border-emerald-400/60 bg-emerald-500/5"
      : "border-dashed border-white/15";

  const cursorClass = isInteractive ? "cursor-pointer" : "cursor-default";
  const displayError = mimeError ?? (status === "error" ? errorMessage : null);

  return (
    <div
      role="button"
      tabIndex={isInteractive ? 0 : -1}
      aria-label={label}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`glass-strong border-2 rounded-2xl p-6 text-center transition-all duration-300 ${borderClass} ${cursorClass} select-none hover:border-emerald-400/30`}
    >
      <input
        ref={inputRef}
        type="file"
        hidden
        multiple
        accept={accept.join(",")}
        onChange={handleInputChange}
        aria-hidden="true"
        tabIndex={-1}
      />

      <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-zinc-500">
        {label}
      </p>

      {status === "idle" && (
        <div className="space-y-2">
          <svg
            className="h-8 w-8 text-zinc-600 mx-auto"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
            />
          </svg>
          <p className="text-sm text-zinc-400">
            Arrastra tus archivos o haz clic para seleccionar
          </p>
          <p className="text-xs text-zinc-600">
            {accept.join(", ")} — múltiples archivos permitidos
          </p>
        </div>
      )}

      {status === "uploading" && (
        <div className="space-y-2">
          <Spinner />
          <p className="text-sm text-zinc-400">
            {progressText ?? "Procesando..."}
          </p>
        </div>
      )}

      {status === "done" && (
        <div className="space-y-2">
          <CheckIcon />
          <p className="text-sm text-emerald-400">
            {fileCount > 1 ? `${fileCount} archivos cargados ✓` : "Archivo cargado ✓"}
          </p>
        </div>
      )}

      {status === "error" && (
        <div className="space-y-2">
          <ErrorIcon />
          <p className="text-sm text-red-400">
            {displayError ?? "Error al cargar el archivo"}
          </p>
        </div>
      )}

      {status === "needs_human_review" && (
        <div className="space-y-2">
          <p className="text-2xl mx-auto text-center">⚠</p>
          <p className="text-sm text-amber-400">Revisión requerida</p>
        </div>
      )}

      {status === "idle" && mimeError && (
        <p className="mt-2 text-xs text-red-400">{mimeError}</p>
      )}
    </div>
  );
}
