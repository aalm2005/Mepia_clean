import { AnomalyItem } from "../../types/audit";
import { AnomalyCard } from "./AnomalyCard";

interface ForensicSummaryProps {
  anomalies: AnomalyItem[];
  available?: boolean;
}

const severityOrder: Record<AnomalyItem["severity"], number> = {
  high:   0,
  medium: 1,
  low:    2,
};

export function ForensicSummary({ anomalies, available = false }: ForensicSummaryProps) {
  const sorted = [...anomalies].sort(
    (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
  );

  return (
    <div className="glass p-panel flex flex-col gap-3">
      <h2 className="text-label uppercase tracking-widest text-muted">
        Anomalías del análisis
      </h2>

      {sorted.length === 0 ? (
        <p className="text-zinc-400 text-sm">{available ? "Sin anomalías detectadas en los indicadores evaluados." : "Este análisis no conserva información suficiente para confirmar si hubo anomalías. Revisa los datos e indicadores pendientes."}</p>
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
