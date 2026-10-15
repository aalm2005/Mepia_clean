import { AnomalyItem } from "../../types/audit";
import { AnomalyCard } from "./AnomalyCard";

interface ForensicSummaryProps {
  anomalies: AnomalyItem[];
}

const severityOrder: Record<AnomalyItem["severity"], number> = {
  high:   0,
  medium: 1,
  low:    2,
};

export function ForensicSummary({ anomalies }: ForensicSummaryProps) {
  const sorted = [...anomalies].sort(
    (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
  );

  return (
    <div className="glass p-panel flex flex-col gap-3">
      <h2 className="text-label uppercase tracking-widest text-muted">
        ANOMALÍAS CRÍTICAS
      </h2>

      {sorted.length === 0 ? (
        <p className="text-zinc-500 text-sm">Sin anomalías detectadas</p>
      ) : (
        <div className="flex flex-col gap-3">
          {sorted.map((anomaly) => (
            <AnomalyCard key={anomaly.anomaly_id} anomaly={anomaly} />
          ))}
        </div>
      )}
    </div>
  );
}
