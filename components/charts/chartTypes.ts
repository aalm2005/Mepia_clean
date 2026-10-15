/**
 * Filas tabulares genéricas — listas para mapear Excel/CSV parseado
 * o arrays de CalcResult del orquestador.
 */
export type TabularValue = string | number | null;

export interface TabularRow {
  [key: string]: TabularValue;
}

export interface ChartSeries {
  dataKey: string;
  name: string;
  color?: string;
}

export const CHART_COLORS = {
  emerald: "rgba(0, 229, 255, 0.95)",
  emeraldSoft: "rgba(0, 229, 255, 0.35)",
  sky: "rgba(85, 199, 255, 0.9)",
  skySoft: "rgba(85, 199, 255, 0.3)",
  amber: "rgba(37, 139, 255, 0.9)",
} as const;
