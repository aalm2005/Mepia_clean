import type { KpiCardData } from "@/utils/mapCalcResultsToKpis";

const statusTone: Record<KpiCardData["status"], string> = {
  ok: "text-emerald-300",
  warning: "text-amber-300",
  critical: "text-red-400",
  incomplete_data: "text-zinc-400",
  unit_mismatch: "text-zinc-400",
  empty: "text-zinc-500",
};

export default function KpiGrid({ items }: { items: KpiCardData[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
      {items.map((kpi) => (
        <article key={kpi.id} className="glass-accent p-5 relative overflow-hidden">
          <div className="absolute inset-0 pointer-events-none bg-gradient-to-br from-emerald-400/8 to-transparent" />
          <p className="relative text-label uppercase tracking-widest text-zinc-400">
            {kpi.label}
          </p>
          <p className={`relative kpi-value text-2xl font-semibold mt-2 ${statusTone[kpi.status]}`}>
            {kpi.value}
            {kpi.unit ? <span className="text-sm text-zinc-400 ml-1">{kpi.unit}</span> : null}
          </p>
          <p className="relative text-[11px] text-zinc-500 mt-2 leading-snug line-clamp-2">
            {kpi.hint}
          </p>
        </article>
      ))}
    </div>
  );
}
