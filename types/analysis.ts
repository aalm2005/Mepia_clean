import type { PipelineStatus } from "./audit";
export interface AnalysisSummary {
  run_id: string; date: string; created_at: string | null; status: PipelineStatus | "unknown";
}
export interface AnalysisTrend {
  business_id: string; run_id: string; periods: number; limited: boolean; ignored_results: number; policy: string;
  series: Array<{ metric: string; unit: string; label: string; valid_periods: number; missing_periods: number;
    points: Array<{ date: string; value: string | null; run_id: string | null }> }>;
}
