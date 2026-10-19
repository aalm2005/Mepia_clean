// Contratos de datos del frontend — basados estrictamente en _glossary.md
// NO modificar sin actualizar _glossary.md primero.

export type Archetype = "Operative Genius" | "Product Purist" | "Growth Hacker";
export type AlertLevel = "info" | "warning" | "critical";
export type PipelineStatus = "completed" | "partial" | "escalated" | "failed" | "running";

export interface AnomalyItem {
  anomaly_id: string;
  type: "margin_leak" | "source_discrepancy" | "operational_ceiling" | "cost_spike" | "other";
  description: string;
  severity: "low" | "medium" | "high";
  quantified_impact: string;
  data_points: string[];
  metric_origin: string;
}

export interface ForensicReport {
  business_id: string;
  date: string;
  risk_level: "low" | "medium" | "high";
  anomalies: AnomalyItem[];
  evidence_sources: string[];
  observed_causality: Record<string, string | null> | null;
  generated_at: string;
}

export interface AuditInsight {
  anomaly_ref: string;
  copilot_phrase: string;
  archetype: Archetype;
  recommended_action: string;
  context_weight: "reducido" | "normal" | "amplificado";
  alert_level: AlertLevel;
  module: string;
  raw_result: string;
}

export interface CalcResult {
  metric: string;
  value: number | string | null;
  unit: string;
  status: "ok" | "warning" | "critical" | "incomplete_data" | "unit_mismatch";
  context: string;
}

export interface OrchestratorResult {
  run_id: string;
  business_id: string;
  date: string;
  archetype: Archetype;
  pipeline_status: PipelineStatus;
  sequential_results: {
    active_metrics: string[];
    calc_results: CalcResult[];
    forensic_report: ForensicReport;
    audit_insights: AuditInsight[];
  };
  escalation: {
    triggered: boolean;
    reason: string | null;
    layer2_run_id: string | null;
  };
  dormant_metrics: Array<{ metric: string; missing: string[] }>;
  blocked_metrics?: Array<{ metric: string; reason: string }>;
  metric_status_available?: boolean;
  completed_at: string;
}

export interface POSIngestResult {
  file_id: string;
  storage_path: string;
  extraction_status: "success" | "needs_human_review";
  needs_human_review: boolean;
  uploaded_at: string;
  date: string | null;
  totals: {
    cash: number;
    card: number;
    total: number;
  } | null;
  payment_methods: {
    cash: number;
    card: number;
    other: number;
  } | null;
  line_items: Array<Record<string, unknown>> | null;
  ocr_confidence: {
    totals: number | null;
    payment_methods: number | null;
    line_items: number | null;
  };
  missing_fields: string[] | null;
}

export interface FacturaIngestResult {
  file_id: string;
  storage_path: string;
  extraction_status: "success" | "needs_human_review";
  needs_human_review: boolean;
  ocr_confidence: number | null;
  transaction_id: string | null;
  extracted_fields: Record<string, unknown> | null;
  missing_fields: string[] | null;
}
