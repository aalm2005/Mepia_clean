"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import GlassTooltip from "./GlassTooltip";
import { CHART_COLORS, type ChartSeries, type TabularRow } from "./chartTypes";

interface MetricLineChartProps {
  data: TabularRow[];
  xKey: string;
  series: ChartSeries[];
  height?: number;
}

const AXIS = { fill: "#A8BED8", fontSize: 12 };

export default function MetricLineChart({
  data,
  xKey,
  series,
  height = 260,
}: MetricLineChartProps) {
  return (
    <div style={{ width: "100%", height }} className="relative z-10">
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
          <XAxis dataKey={xKey} tick={AXIS} stroke="rgba(255,255,255,0.08)" />
          <YAxis tick={AXIS} stroke="rgba(255,255,255,0.08)" />
          <Tooltip
            content={GlassTooltip as never}
            cursor={{ stroke: "rgba(85,199,255,0.32)" }}
          />
          {series.map((s, i) => (
            <Line
              key={s.dataKey}
              type="monotone"
              dataKey={s.dataKey}
              name={s.name}
              stroke={s.color ?? (i === 0 ? CHART_COLORS.emerald : CHART_COLORS.sky)}
              strokeWidth={2.2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
