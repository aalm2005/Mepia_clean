"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import GlassTooltip from "./GlassTooltip";
import { CHART_COLORS, type ChartSeries, type TabularRow } from "./chartTypes";

interface MetricBarChartProps {
  data: TabularRow[];
  xKey: string;
  series: ChartSeries[];
  height?: number;
}

const AXIS = { fill: "#A8BED8", fontSize: 12 };

export default function MetricBarChart({
  data,
  xKey,
  series,
  height = 260,
}: MetricBarChartProps) {
  return (
    <div style={{ width: "100%", height }} className="relative z-10">
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
          <XAxis dataKey={xKey} tick={AXIS} stroke="rgba(255,255,255,0.08)" />
          <YAxis tick={AXIS} stroke="rgba(255,255,255,0.08)" />
          <Tooltip
            content={GlassTooltip as never}
            cursor={{ fill: "rgba(22,119,255,0.08)" }}
          />
          {series.map((s, i) => (
            <Bar
              key={s.dataKey}
              dataKey={s.dataKey}
              name={s.name}
              fill={s.color ?? (i === 0 ? CHART_COLORS.emeraldSoft : CHART_COLORS.skySoft)}
              stroke={s.color ?? (i === 0 ? CHART_COLORS.emerald : CHART_COLORS.sky)}
              radius={[6, 6, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
