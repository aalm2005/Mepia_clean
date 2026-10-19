"use client";

import { useState } from "react";

export interface AuditTolerancesData {
  max_cash_discrepancy_pct: number;   // 0–1 (stored as decimal, displayed as %)
  max_cash_discrepancy_abs: number;   // absolute MXN amount
  margin_warning_threshold: number;   // 0–1
  margin_critical_threshold: number;  // 0–1
  cost_spike_threshold_pct: number;   // 0–1
}

interface Props {
  data: AuditTolerancesData;
  onChange: (data: AuditTolerancesData) => void;
}

// Shared input class for all numeric inputs
const INPUT_CLASS =
  "glass-input px-3 py-2 text-sm w-24 text-right font-mono";

export default function AuditTolerancesStep({ data, onChange }: Props) {
  // Track which fields have been touched for validation
  const [touched, setTouched] = useState<Partial<Record<keyof AuditTolerancesData, boolean>>>({});

  function markTouched(field: keyof AuditTolerancesData) {
    setTouched((prev) => ({ ...prev, [field]: true }));
  }

  // Validation: margin_critical must be < margin_warning
  const marginConstraintViolated =
    !!touched.margin_critical_threshold &&
    !!touched.margin_warning_threshold &&
    data.margin_critical_threshold >= data.margin_warning_threshold;

  // Helpers: convert decimal ↔ display percentage
  function toDisplay(decimal: number): string {
    // Round to avoid floating-point noise (e.g. 0.15 → "15", not "14.999999...")
    return String(Math.round(decimal * 100 * 10) / 10);
  }

  function fromDisplay(displayValue: string): number {
    const parsed = parseFloat(displayValue);
    if (isNaN(parsed)) return 0;
    return parsed / 100;
  }

  function handlePctChange(
    field: keyof AuditTolerancesData,
    e: React.ChangeEvent<HTMLInputElement>
  ) {
    onChange({ ...data, [field]: fromDisplay(e.target.value) });
  }

  function handleAbsChange(e: React.ChangeEvent<HTMLInputElement>) {
    const parsed = parseFloat(e.target.value);
    onChange({ ...data, max_cash_discrepancy_abs: isNaN(parsed) ? 0 : parsed });
  }

  return (
    <div data-tour="advanced-config-thresholds" className="space-y-6">
      <h2 className="text-label text-muted uppercase tracking-widest">
        Paso 2 — Umbrales de Auditoría
      </h2>

      {/* Cash discrepancy row — two inputs: % and MXN */}
      <div className="space-y-1.5">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-sm text-zinc-300 w-56">
            Discrepancia de caja máxima:
          </span>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min="0"
              step="0.1"
              value={toDisplay(data.max_cash_discrepancy_pct)}
              onChange={(e) => handlePctChange("max_cash_discrepancy_pct", e)}
              onBlur={() => markTouched("max_cash_discrepancy_pct")}
              className={INPUT_CLASS}
              aria-label="Discrepancia de caja máxima en porcentaje"
            />
            <span className="text-sm text-zinc-300">%</span>
            <span className="text-sm text-muted px-1">o</span>
            <input
              type="number"
              min="0"
              step="1"
              value={data.max_cash_discrepancy_abs}
              onChange={handleAbsChange}
              onBlur={() => markTouched("max_cash_discrepancy_abs")}
              className={INPUT_CLASS}
              aria-label="Discrepancia de caja máxima en MXN"
            />
            <span className="text-sm text-zinc-300">MXN</span>
          </div>
        </div>
        <p className="text-xs text-muted pl-0">
          (se usa el más permisivo)
        </p>
      </div>

      {/* Margin warning threshold */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-zinc-300 w-56">Margen warning:</span>
        <div className="flex items-center gap-2">
          <input
            type="number"
            min="0"
            step="0.1"
            value={toDisplay(data.margin_warning_threshold)}
            onChange={(e) => handlePctChange("margin_warning_threshold", e)}
            onBlur={() => markTouched("margin_warning_threshold")}
            className={INPUT_CLASS}
            aria-label="Umbral de margen warning en porcentaje"
          />
          <span className="text-sm text-zinc-300">%</span>
        </div>
      </div>

      {/* Margin critical threshold */}
      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <span className="text-sm text-zinc-300 w-56">Margen crítico:</span>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min="0"
              step="0.1"
              value={toDisplay(data.margin_critical_threshold)}
              onChange={(e) => handlePctChange("margin_critical_threshold", e)}
              onBlur={() => markTouched("margin_critical_threshold")}
              className={[
                INPUT_CLASS,
                marginConstraintViolated ? "border-critical" : "",
              ].join(" ")}
              aria-label="Umbral de margen crítico en porcentaje"
              aria-invalid={marginConstraintViolated}
              aria-describedby={marginConstraintViolated ? "margin-critical-error" : undefined}
            />
            <span className="text-sm text-zinc-300">%</span>
          </div>
        </div>
        {marginConstraintViolated && (
          <p id="margin-critical-error" className="text-xs text-critical pl-0" role="alert">
            El margen crítico debe ser menor al margen de warning
          </p>
        )}
      </div>

      {/* Cost spike threshold */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-zinc-300 w-56">Spike de costo:</span>
        <div className="flex items-center gap-2">
          <input
            type="number"
            min="0"
            step="0.1"
            value={toDisplay(data.cost_spike_threshold_pct)}
            onChange={(e) => handlePctChange("cost_spike_threshold_pct", e)}
            onBlur={() => markTouched("cost_spike_threshold_pct")}
            className={INPUT_CLASS}
            aria-label="Umbral de spike de costo en porcentaje"
          />
          <span className="text-sm text-zinc-300">%</span>
        </div>
      </div>
    </div>
  );
}
