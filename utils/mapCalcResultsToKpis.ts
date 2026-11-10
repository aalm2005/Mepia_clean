import type { CalcResult } from "@/types/audit";

export interface KpiCardData {
  id: string;
  label: string;
  value: string;
  unit: string;
  status: CalcResult["status"] | "empty";
  hint: string;
}

const KPI_DEFS: Array<{
  id: string;
  label: string;
  match: RegExp;
}> = [
  { id: "ingresos", label: "Ingresos Totales", match: /^(ingresos_totales|total_sales|ventas_totales|revenue)$/i },
  { id: "margen", label: "Margen", match: /^(contribution_margin|margen_contribucion)$/i },
  { id: "merma", label: "Pérdida por Mermas", match: /merma|waste/i },
  { id: "salud", label: "Salud del Negocio", match: /^health_score$/i },
  { id: "caja", label: "Conciliación de Caja", match: /cash_reconcil|caja|cash/i },
];

function finiteValue(value: unknown): number | null {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value !== "string" || !/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(value)) return null;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function formatValue(result: CalcResult | undefined): string {
  if (!result || ["incomplete_data", "unit_mismatch"].includes(result.status)) return "—";
  const numeric = finiteValue(result.value);
  if (numeric === null) return "—";
  const value = numeric.toLocaleString("es-MX", { maximumFractionDigits: 20 });
  if (result.unit === "%" || result.unit === "pct") {
    return `${value}%`;
  }
  return value;
}

/**
 * Proyecta calc_results del orquestador a tarjetas KPI.
 * No inventa cifras: si no hay match, el valor queda "—".
 */
export function mapCalcResultsToKpis(results: CalcResult[] = []): KpiCardData[] {
  const cards: KpiCardData[] = KPI_DEFS.map((def) => {
    const match = results.find((r) => def.match.test(r.metric));
    return {
      id: def.id,
      label: match?.metric ?? def.label,
      value: formatValue(match),
      unit: match && match.value !== null ? (match.unit === "%" || match.unit === "pct" ? "" : match.unit) : "",
      status: match?.status ?? "empty",
      hint: match?.context ?? "Este análisis no conserva este indicador.",
    };
  });
  const represented = new Set(cards.filter(card => card.status !== "empty").map(card => card.label));
  return [...cards, ...results.filter(result=>!represented.has(result.metric)).map((result,index)=>({
    id:`${result.metric}:${index}`,label:result.metric,value:formatValue(result),
    unit:result.value===null||result.unit==="%"||result.unit==="pct"?"":result.unit,
    status:result.status,hint:result.context,
  }))];
}

/** Convierte calc_results a filas tabulares para Recharts. */
export function calcResultsToChartRows(results: CalcResult[] = []) {
  return results.flatMap((r) => {
    const value = finiteValue(r.value);
    if (value === null || ["incomplete_data", "unit_mismatch"].includes(r.status)) return [];
    return [{
      metric: r.metric,
      value,
      status: r.status,
      unit: r.unit,
    }];
  });
}
