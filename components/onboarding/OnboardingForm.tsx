"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMepiaAuth } from "@/components/auth/MepiaAuthProvider";
import BrandIdentityStep, { type BrandIdentityData } from "./BrandIdentityStep";
import AuditTolerancesStep, { type AuditTolerancesData } from "./AuditTolerancesStep";
import CostStructureStep, { type CostStructureItem } from "./CostStructureStep";
import AuditRulesStep, { type AuditRulesData } from "./AuditRulesStep";

// Full payload shape — mirrors OnboardingIdentityPayload from _glossary.md
interface FormData {
  brand_identity: BrandIdentityData;
  audit_tolerances: AuditTolerancesData;
  expected_cost_structure: CostStructureItem[];
  audit_rules: AuditRulesData;
}

const DEFAULT_FORM_DATA: FormData = {
  brand_identity: {
    brand_voice: "",
    prohibited_recommendations: [],
    priority_focus: "efficiency",
  },
  audit_tolerances: {
    max_cash_discrepancy_pct: 0.02,
    max_cash_discrepancy_abs: 150,
    margin_warning_threshold: 0.15,
    margin_critical_threshold: 0.08,
    cost_spike_threshold_pct: 0.10,
  },
  expected_cost_structure: [],
  audit_rules: {
    red_alert_triggers: [],
    ignored_anomaly_types: [],
    audit_frequency: "daily",
  },
};

const STEPS = [
  { id: 1, label: "1. Identidad" },
  { id: 2, label: "2. Umbrales" },
  { id: 3, label: "3. Costos" },
  { id: 4, label: "4. Reglas" },
];

export default function OnboardingForm() {
  const router = useRouter();
  const { business } = useMepiaAuth();
  const [activeStep, setActiveStep] = useState(1);
  const [formData, setFormData] = useState<FormData>(DEFAULT_FORM_DATA);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  function handleNext() {
    if (activeStep < 4) setActiveStep((s) => s + 1);
  }

  function handlePrev() {
    if (activeStep > 1) setActiveStep((s) => s - 1);
  }

  async function handleSave() {
    setIsSaving(true);
    setSaveError(null);

    const business_id = business;
    if (!business_id) { setSaveError("Selecciona un negocio para continuar."); setIsSaving(false); return; }

    // Mapear campos del formulario al contrato del backend:
    //   amount_per_month  → expected_monthly_amount
    //   tolerance_pct     → decimal (el usuario ingresa 10 = 10%, backend espera 0.10)
    const mappedCostStructure = formData.expected_cost_structure.map((item) => ({
      concept: item.concept,
      expected_monthly_amount: item.amount_per_month,
      tolerance_pct: item.tolerance_pct > 1 ? item.tolerance_pct / 100 : item.tolerance_pct,
      expense_behavior: item.expense_behavior,
    }));

    const body = {
      business_id,
      ...formData,
      expected_cost_structure: mappedCostStructure,
    };

    try {
      let response = await fetch("/api/onboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      // 409 Conflict — already exists, retry with PUT
      if (response.status === 409) {
        response = await fetch("/api/onboarding", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      }

      if (response.status === 201 || response.status === 200) {
        router.push("/upload");
        return;
      }

      if (response.status === 422) {
        const data = await response.json().catch(() => null);
        const message =
          data?.detail ?? data?.message ?? "Datos inválidos. Revisa los campos del formulario.";
        setSaveError(typeof message === "string" ? message : JSON.stringify(message));
        return;
      }

      // Any other non-success status
      const errData = await response.json().catch(() => null);
      const errMsg = errData?.detail ?? errData?.message ?? "Error al guardar la configuración. Intenta de nuevo.";
      setSaveError(typeof errMsg === "string" ? errMsg : JSON.stringify(errMsg));
    } catch {
      setSaveError("Error al guardar la configuración. Intenta de nuevo.");
    } finally {
      setIsSaving(false);
    }
  }

  function renderStep(step: number) {
    switch (step) {
      case 1:
        return (
          <BrandIdentityStep
            data={formData.brand_identity}
            onChange={(d) => setFormData((prev) => ({ ...prev, brand_identity: d }))}
          />
        );
      case 2:
        return (
          <AuditTolerancesStep
            data={formData.audit_tolerances}
            onChange={(d) => setFormData((prev) => ({ ...prev, audit_tolerances: d }))}
          />
        );
      case 3:
        return (
          <CostStructureStep
            data={formData.expected_cost_structure}
            onChange={(d) => setFormData((prev) => ({ ...prev, expected_cost_structure: d }))}
          />
        );
      case 4:
        return (
          <AuditRulesStep
            data={formData.audit_rules}
            onChange={(d) => setFormData((prev) => ({ ...prev, audit_rules: d }))}
          />
        );
      default:
        return null;
    }
  }

  return (
    <div className="glass-strong rounded-2xl">
      {/* Progress indicator */}
      <div className="flex items-center gap-0 border-b border-white/10 px-panel py-4">
        {STEPS.map((step) => {
          const isActive = step.id === activeStep;
          return (
            <span
              key={step.id}
              className={[
                "flex-1 text-center text-label pb-2 transition-colors",
                isActive
                  ? "text-accent border-b-2 border-accent"
                  : "text-muted",
              ].join(" ")}
            >
              {step.label}
            </span>
          );
        })}
      </div>

      {/* Step content */}
      <div className="px-panel py-8 min-h-[280px]">
        {renderStep(activeStep)}
      </div>

      {/* Navigation */}
      <div className="flex flex-col gap-3 border-t border-white/10 px-panel py-4">
        {saveError && (
          <p className="text-xs text-critical">{saveError}</p>
        )}
        <div className="flex items-center justify-end gap-3">
          {activeStep > 1 && (
            <button
              type="button"
              onClick={handlePrev}
              disabled={isSaving}
              className="px-4 py-2 text-sm text-muted hover:text-zinc-100 transition-colors disabled:opacity-50"
            >
              ← Anterior
            </button>
          )}

          {activeStep < 4 && (
            <button
              type="button"
              onClick={handleNext}
              className="glass-btn-ghost px-4 py-2 text-sm"
            >
              Siguiente →
            </button>
          )}

          {activeStep === 4 && (
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving}
              className="glass-btn-primary px-5 py-2 text-sm font-medium"
            >
              {isSaving ? "Guardando..." : "Guardar configuración ✓"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
