"use client";

import { useState } from "react";

export interface CostStructureItem {
  concept: string;
  amount_per_month: number;
  tolerance_pct: number;
  expense_behavior: "FIXED" | "VARIABLE" | "CAPEX";
}

interface Props {
  data: CostStructureItem[];
  onChange: (data: CostStructureItem[]) => void;
}

const EXPENSE_BEHAVIOR_OPTIONS: CostStructureItem["expense_behavior"][] = [
  "FIXED",
  "VARIABLE",
  "CAPEX",
];

// Shared class for inputs and select inside table cells
const CELL_INPUT_CLASS =
  "bg-transparent border-0 text-zinc-100 text-sm w-full focus:outline-none focus:bg-white/5 px-2 py-1";

function emptyRow(): CostStructureItem {
  return { concept: "", amount_per_month: 0, tolerance_pct: 0, expense_behavior: "FIXED" };
}

export default function CostStructureStep({ data, onChange }: Props) {
  const [touched, setTouched] = useState(false);

  const isEmpty = data.length === 0;
  const showError = touched && isEmpty;

  function handleAdd() {
    setTouched(true);
    onChange([...data, emptyRow()]);
  }

  function handleDelete(index: number) {
    setTouched(true);
    onChange(data.filter((_, i) => i !== index));
  }

  function handleChange<K extends keyof CostStructureItem>(
    index: number,
    field: K,
    value: CostStructureItem[K]
  ) {
    const updated = data.map((row, i) => (i === index ? { ...row, [field]: value } : row));
    onChange(updated);
  }

  function handleNumberChange(
    index: number,
    field: "amount_per_month" | "tolerance_pct",
    raw: string
  ) {
    const parsed = parseFloat(raw);
    handleChange(index, field, isNaN(parsed) ? 0 : parsed);
  }

  return (
    <div className="space-y-3">
      <h2 className="text-label text-muted uppercase tracking-widest">
        Paso 3 — Estructura de Costos Fijos
      </h2>

      <div className="border border-white/10 rounded-xl overflow-hidden glass-strong">
        {/* Header row */}
        <div className="grid grid-cols-[1fr_140px_100px_120px_36px] bg-white/5">
          <div className="text-label text-muted uppercase tracking-widest text-xs px-3 py-2">
            Concepto
          </div>
          <div className="text-label text-muted uppercase tracking-widest text-xs px-2 py-2 text-right">
            Monto/mes
          </div>
          <div className="text-label text-muted uppercase tracking-widest text-xs px-2 py-2 text-right">
            Tolerancia
          </div>
          <div className="text-label text-muted uppercase tracking-widest text-xs px-2 py-2">
            Tipo
          </div>
          {/* Delete column — empty header */}
          <div />
        </div>

        {/* Data rows */}
        {data.map((row, index) => (
          <div
            key={index}
            className="grid grid-cols-[1fr_140px_100px_120px_36px] border-t border-white/10 items-center"
          >
            {/* Concepto */}
            <div>
              <input
                type="text"
                value={row.concept}
                onChange={(e) => handleChange(index, "concept", e.target.value)}
                placeholder="Ej. Renta"
                className={CELL_INPUT_CLASS}
                aria-label={`Concepto fila ${index + 1}`}
              />
            </div>

            {/* Monto/mes */}
            <div>
              <input
                type="number"
                min="0"
                step="1"
                value={row.amount_per_month === 0 ? "" : row.amount_per_month}
                onChange={(e) => handleNumberChange(index, "amount_per_month", e.target.value)}
                placeholder="0"
                className={`${CELL_INPUT_CLASS} font-mono text-right`}
                aria-label={`Monto por mes fila ${index + 1}`}
              />
            </div>

            {/* Tolerancia */}
            <div>
              <input
                type="number"
                min="0"
                max="100"
                step="1"
                value={row.tolerance_pct === 0 ? "" : row.tolerance_pct}
                onChange={(e) => handleNumberChange(index, "tolerance_pct", e.target.value)}
                placeholder="0"
                className={`${CELL_INPUT_CLASS} font-mono text-right`}
                aria-label={`Tolerancia fila ${index + 1}`}
              />
            </div>

            {/* Tipo */}
            <div>
              <select
                value={row.expense_behavior}
                onChange={(e) =>
                  handleChange(
                    index,
                    "expense_behavior",
                    e.target.value as CostStructureItem["expense_behavior"]
                  )
                }
                className={CELL_INPUT_CLASS}
                aria-label={`Tipo de gasto fila ${index + 1}`}
              >
                {EXPENSE_BEHAVIOR_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>

            {/* Delete button */}
            <div className="flex items-center justify-center">
              <button
                type="button"
                onClick={() => handleDelete(index)}
                className="text-muted hover:text-zinc-100 transition-colors text-base leading-none px-1"
                aria-label={`Eliminar fila ${index + 1}`}
              >
                ×
              </button>
            </div>
          </div>
        ))}

        {/* Empty state row */}
        {data.length === 0 && (
          <div className="border-t border-white/10 px-3 py-3 text-sm text-muted text-center">
            Sin costos registrados
          </div>
        )}
      </div>

      {/* Inline validation error */}
      {showError && (
        <p className="text-xs text-critical" role="alert">
          Se requiere al menos un costo
        </p>
      )}

      {/* Add row button */}
      <button
        type="button"
        onClick={handleAdd}
        className="text-sm text-accent hover:text-accent/80 transition-colors mt-3"
      >
        + Agregar costo
      </button>
    </div>
  );
}
