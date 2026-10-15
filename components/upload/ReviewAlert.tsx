"use client";

import { useState } from "react";
import { authenticatedFetch } from "@/utils/authenticated-fetch";

interface ReviewAlertProps {
  documentType: "pos" | "factura";
  fileId: string;
  missingFields: string[];
  onReviewed: () => void;
}

export default function ReviewAlert({
  documentType,
  fileId,
  missingFields,
  onReviewed,
}: ReviewAlertProps) {
  const [fieldValues, setFieldValues] = useState<Record<string, string>>(
    () => Object.fromEntries(missingFields.map((field) => [field, ""]))
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFieldChange(field: string, value: string) {
    setFieldValues((prev) => ({ ...prev, [field]: value }));
  }

  /**
   * Builds the structured payload expected by FastAPI review endpoints.
   * POS  → POSReviewPayload:     { date, totals: { cash, card, total }, payment_methods? }
   * Factura → FacturaReviewPayload: { transaction_date, amount, tax_amount, supplier_name, concept, document_reference }
   */
  function buildReviewPayload(): Record<string, unknown> {
    if (documentType === "pos") {
      return {
        date: fieldValues["date"] ?? fieldValues["date"] ?? "",
        totals: {
          total: parseFloat(fieldValues["totals.total"] ?? fieldValues["totals"] ?? "0"),
          cash: parseFloat(fieldValues["totals.cash"] ?? "0"),
          card: parseFloat(fieldValues["totals.card"] ?? "0"),
        },
        payment_methods: {
          cash: parseFloat(fieldValues["totals.cash"] ?? fieldValues["payment_methods"] ?? "0"),
          card: parseFloat(fieldValues["totals.card"] ?? "0"),
          other: 0,
        },
      };
    }
    // Factura — campos planos directos
    return {
      transaction_date: fieldValues["transaction_date"] ?? "",
      amount: parseFloat(fieldValues["amount"] ?? "0"),
      tax_amount: parseFloat(fieldValues["tax_amount"] ?? "0"),
      supplier_name: fieldValues["supplier_name"] ?? "",
      concept: fieldValues["concept"] ?? "",
      document_reference: fieldValues["document_reference"] ?? "",
    };
  }

  async function handleConfirm() {
    setIsSubmitting(true);
    setError(null);

    try {
      const reviewPayload = buildReviewPayload();
      const res = await authenticatedFetch("/api/upload", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_id: fileId,
          document_type: documentType,
          ...reviewPayload,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(
          (data as { detail?: string }).detail ??
            `Error ${res.status}: no se pudo confirmar la revisión`
        );
      }

      onReviewed();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Error inesperado al confirmar"
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div
      className="glass-strong border border-amber-500/30 rounded-xl p-4 space-y-4"
      role="alert"
    >
      {/* Header */}
      <div>
        <h3 className="text-amber-400 text-sm font-semibold font-mono uppercase tracking-widest">
          ⚠ Revisión requerida
        </h3>
        <p className="mt-1 text-xs text-zinc-400">
          Los siguientes campos requieren revisión manual:
        </p>
      </div>

      {/* Editable field list */}
      <ul className="space-y-3">
        {missingFields.map((field) => (
          <li key={field} className="flex flex-col gap-1">
            <label
              htmlFor={`review-field-${field}`}
              className="text-label uppercase tracking-widest text-amber-400 font-mono"
            >
              {field}
            </label>
            <input
              id={`review-field-${field}`}
              type="text"
              value={fieldValues[field] ?? ""}
              onChange={(e) => handleFieldChange(field, e.target.value)}
              disabled={isSubmitting}
              placeholder={`Valor para ${field}`}
              className="glass-input px-3 py-1.5 text-sm text-zinc-200 disabled:opacity-50 font-mono"
            />
          </li>
        ))}
      </ul>

      {/* Inline error */}
      {error && (
        <p className="text-xs text-red-400" role="alert">
          {error}
        </p>
      )}

      {/* Confirm button */}
      <button
        type="button"
        onClick={handleConfirm}
        disabled={isSubmitting}
        className="w-full border border-amber-500/40 bg-amber-500/10 text-amber-400 text-label uppercase tracking-widest font-mono px-4 py-2.5 rounded-lg hover:bg-amber-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed backdrop-blur"
      >
        {isSubmitting ? "Enviando..." : "Confirmar revisión"}
      </button>
    </div>
  );
}
