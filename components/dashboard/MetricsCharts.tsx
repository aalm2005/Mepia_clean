"use client";

import dynamic from "next/dynamic";
import { CHART_COLORS, type TabularRow } from "@/components/charts/chartTypes";

const MetricBarChart = dynamic(() => import("@/components/charts/MetricBarChart"), {
  ssr: false,
});
const MetricLineChart = dynamic(() => import("@/components/charts/MetricLineChart"), {
  ssr: false,
});

interface MetricsChartsProps {
  barData: TabularRow[];
  lineData: TabularRow[];
}

export default function MetricsCharts({ barData, lineData }: MetricsChartsProps) {
  const units = Array.from(new Set(barData.map(row => String(row.unit ?? "Sin unidad"))));
  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
      {(units.length ? units : ["Sin unidad"]).map(unit => <section key={unit} className="glass p-5">
        <h2 className="text-label uppercase tracking-widest text-zinc-400 mb-3">
          Métricas calculadas · {unit}
        </h2>
        {barData.length === 0 ? (
          <p className="text-sm text-zinc-500 py-10 text-center">
            Sin series aún. Los arrays tabulares se mapean desde calc_results o Excel/CSV.
          </p>
        ) : (
          <MetricBarChart
            data={barData.filter(row => String(row.unit ?? "Sin unidad") === unit)}
            xKey="metric"
            series={[{ dataKey: "value", name: "Valor", color: CHART_COLORS.emerald }]}
          />
        )}
      </section>)}

      <section className="glass p-5">
        <h2 className="text-label uppercase tracking-widest text-zinc-400 mb-3">
          Tendencia operativa
        </h2>
        {lineData.length === 0 ? (
          <p className="text-sm text-zinc-500 py-10 text-center">
            Sin historial. Acepta filas tabulares con periodo, ingresos y margen (Excel/CSV).
          </p>
        ) : (
          <MetricLineChart
            data={lineData}
            xKey="periodo"
            series={[
              { dataKey: "ingresos", name: "Ingresos", color: CHART_COLORS.emerald },
              { dataKey: "margen", name: "Margen", color: CHART_COLORS.sky },
            ]}
          />
        )}
      </section>
    </div>
  );
}
