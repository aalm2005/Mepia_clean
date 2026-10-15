export type UploadStatus =
  | "idle"
  | "uploading"
  | "done"
  | "error"
  | "needs_human_review";

interface UploadStatusBadgeProps {
  status: UploadStatus;
}

const badgeConfig: Record<
  Exclude<UploadStatus, "idle">,
  { classes: string; label: string }
> = {
  uploading: {
    classes: "bg-white/5 text-zinc-300 border border-white/10 backdrop-blur",
    label: "Procesando...",
  },
  done: {
    classes: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 backdrop-blur",
    label: "Cargado ✓",
  },
  error: {
    classes: "bg-red-950/40 text-red-400 border border-red-500/30 backdrop-blur",
    label: "Error",
  },
  needs_human_review: {
    classes: "bg-amber-950/40 text-amber-400 border border-amber-500/30 backdrop-blur",
    label: "Revisión requerida",
  },
};

export default function UploadStatusBadge({ status }: UploadStatusBadgeProps) {
  if (status === "idle") return null;

  const { classes, label } = badgeConfig[status];

  return (
    <span
      className={`inline-flex items-center gap-1.5 text-label uppercase tracking-widest px-2 py-0.5 rounded-sm font-mono ${classes}`}
    >
      {label}
    </span>
  );
}
