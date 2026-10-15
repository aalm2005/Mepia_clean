export type AlertLevel = "critical" | "warning" | "info";

export const alertBadge: Record<AlertLevel, string> = {
  critical: "bg-red-950/40 text-red-400 border border-red-500/30 backdrop-blur",
  warning:  "bg-amber-950/40 text-amber-400 border border-amber-500/30 backdrop-blur",
  info:     "bg-white/5 text-zinc-400 border border-white/10 backdrop-blur",
};

interface Props {
  level: AlertLevel;
}

export default function AlertLevelBadge({ level }: Props) {
  return (
    <span
      className={`inline-block text-label uppercase tracking-widest px-2 py-0.5 rounded-sm font-mono ${alertBadge[level]}`}
    >
      {level}
    </span>
  );
}
