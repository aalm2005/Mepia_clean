import type { AuditRulesData } from "./AuditRulesStep";
import type { AuditTolerancesData } from "./AuditTolerancesStep";
import type { BrandIdentityData } from "./BrandIdentityStep";
import type { CostStructureItem } from "./CostStructureStep";

export interface OnboardingFormData {
  brand_identity: BrandIdentityData;
  audit_tolerances: AuditTolerancesData;
  expected_cost_structure: CostStructureItem[];
  audit_rules: AuditRulesData;
}

export const DEFAULT_ONBOARDING_DATA: OnboardingFormData = {
  brand_identity: {
    brand_voice: "Asesoría clara y práctica, basada en los datos disponibles del negocio.",
    prohibited_recommendations: [],
    priority_focus: "efficiency",
  },
  audit_tolerances: {
    max_cash_discrepancy_pct: 0.02,
    max_cash_discrepancy_abs: 150,
    margin_warning_threshold: 0.15,
    margin_critical_threshold: 0.08,
    cost_spike_threshold_pct: 0.1,
  },
  expected_cost_structure: [],
  audit_rules: {
    red_alert_triggers: [],
    ignored_anomaly_types: [],
    audit_frequency: "daily",
  },
};
