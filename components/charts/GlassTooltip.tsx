"use client";

interface TooltipEntry {
  dataKey?: string | number;
  name?: string;
  value?: unknown;
  color?: string;
}

interface GlassTooltipProps {
  active?: boolean;
  payload?: readonly TooltipEntry[];
  label?: unknown;
}

export default function GlassTooltip({ active, payload, label }: GlassTooltipProps) {
  if (!active || !payload?.length) return null;

  return (
    <div className="chart-tooltip-glass">
      {label != null && (
        <p className="text-zinc-400 mb-1.5 font-mono text-[11px]">{String(label)}</p>
      )}
      <ul className="space-y-1">
        {payload.map((entry) => (
          <li key={String(entry.dataKey ?? entry.name)} className="flex items-center gap-2">
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{ background: String(entry.color) }}
            />
            <span className="text-zinc-300">{entry.name}</span>
            <span className="ml-auto font-mono text-emerald-300">
              {entry.value == null ? "—" : String(entry.value)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
