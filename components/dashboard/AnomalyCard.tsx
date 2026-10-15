import { AnomalyItem } from "../../types/audit";

interface AnomalyCardProps {
  anomaly: AnomalyItem;
}

const severityBadge: Record<AnomalyItem["severity"], string> = {
  high:   "bg-red-950/40  text-red-400  border border-red-500/30 backdrop-blur",
  medium: "bg-amber-950/40 text-amber-400 border border-amber-500/30 backdrop-blur",
  low:    "bg-white/5 text-zinc-300  border border-white/10 backdrop-blur",
};

export function AnomalyCard({ anomaly }: AnomalyCardProps) {
  return (
    <div className="glass-strong border border-white/10 rounded-xl p-4 flex flex-col gap-2">
      {/* Header: type + severity badge */}
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-zinc-500 font-mono uppercase tracking-widest">
          {anomaly.type}
        </span>
        <span
          className={`inline-block text-label uppercase tracking-widest px-2 py-0.5 rounded-sm font-mono ${severityBadge[anomaly.severity]}`}
        >
          {anomaly.severity}
        </span>
      </div>

      {/* Quantified impact — primary visual */}
      <p className="font-mono text-forensic-xl text-zinc-100">
        {anomaly.quantified_impact}
      </p>

      {/* Description */}
      <p className="text-sm text-zinc-300">{anomaly.description}</p>

      {/* Data points */}
      {anomaly.data_points.length > 0 && (
        <ul className="flex flex-col gap-0.5 mt-1">
          {anomaly.data_points.map((point, i) => (
            <li key={i} className="text-xs text-zinc-500 font-mono before:content-['·'] before:mr-1.5">
              {point}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
