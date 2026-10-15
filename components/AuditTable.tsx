import { AuditInsight, AlertLevel } from "../types/audit";
import AlertLevelBadge from "./ui/AlertLevelBadge";
import ArchetypeBadge from "./ui/ArchetypeBadge";

export type Archetype = "Operative Genius" | "Product Purist" | "Growth Hacker";

export interface AuditRow {
  module: string;
  raw_result: string;
  copilot_phrase: string;
  archetype: Archetype;
}

interface AuditTableProps {
  rows: AuditInsight[] | AuditRow[];
  isLoading?: boolean;
  emptyMessage?: string;
}

function isAuditInsight(row: AuditInsight | AuditRow): row is AuditInsight {
  return "alert_level" in row;
}

function rowAlertLevel(row: AuditInsight | AuditRow): AlertLevel | null {
  return isAuditInsight(row) ? row.alert_level : null;
}

function rowClassName(row: AuditInsight | AuditRow): string {
  const base =
    "border-b border-white/5 last:border-0 hover:bg-emerald-500/5 transition-colors";
  if (!isAuditInsight(row)) return base;
  switch (row.alert_level) {
    case "critical":
      return `${base} border-l-2 border-red-500 bg-red-950/20`;
    case "warning":
      return `${base} border-l-2 border-amber-500`;
    default:
      return base;
  }
}

export default function AuditTable({
  rows,
  isLoading,
  emptyMessage,
}: AuditTableProps) {
  return (
    <div className="w-full overflow-x-auto rounded-2xl glass scrollbar-thin">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10 text-zinc-400 text-left">
            <th className="px-6 py-4 font-medium w-[15%]">Módulo</th>
            <th className="px-6 py-4 font-medium w-[30%]">Resultado Forense</th>
            <th className="px-6 py-4 font-medium w-[35%]">Insight CEO</th>
            <th className="px-6 py-4 font-medium w-[10%]">Nivel</th>
            <th className="px-6 py-4 font-medium w-[10%]">Acción</th>
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            <>
              {[0, 1, 2].map((i) => (
                <tr key={i} className="border-b border-white/5 last:border-0">
                  <td className="px-6 py-5">
                    <div className="bg-white/10 h-4 rounded animate-pulse" />
                  </td>
                  <td className="px-6 py-5">
                    <div className="bg-white/10 h-4 rounded animate-pulse" />
                  </td>
                  <td className="px-6 py-5">
                    <div className="bg-white/10 h-4 rounded animate-pulse" />
                  </td>
                  <td className="px-6 py-5">
                    <div className="bg-white/10 h-4 rounded animate-pulse" />
                  </td>
                  <td className="px-6 py-5">
                    <div className="bg-white/10 h-4 rounded animate-pulse" />
                  </td>
                </tr>
              ))}
            </>
          ) : rows.length === 0 ? (
            <tr>
              <td
                colSpan={5}
                className="px-6 py-10 text-center text-zinc-500"
              >
                {emptyMessage ?? "No hay resultados."}
              </td>
            </tr>
          ) : (
            rows.map((row, i) => {
              const level = rowAlertLevel(row);
              return (
                <tr key={i} className={rowClassName(row)}>
                  {/* Módulo */}
                  <td className="px-6 py-5 font-semibold text-zinc-100 align-top">
                    {row.module}
                  </td>

                  {/* Resultado Forense */}
                  <td className="px-6 py-5 text-zinc-300 align-top">
                    {row.raw_result}
                  </td>

                  {/* Insight CEO */}
                  <td className="px-6 py-5 align-top">
                    <ArchetypeBadge archetype={row.archetype} />
                    <p className="text-zinc-200 leading-relaxed mt-1">
                      &ldquo;{row.copilot_phrase}&rdquo;
                    </p>
                  </td>

                  {/* Nivel de alerta */}
                  <td className="px-6 py-5 align-top">
                    {level ? <AlertLevelBadge level={level} /> : null}
                  </td>

                  {/* Acción recomendada */}
                  <td className="px-6 py-5 text-zinc-400 align-top text-xs">
                    {isAuditInsight(row) ? row.recommended_action : null}
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
