"use client";

import { useState } from "react";

export interface AuditRulesData {
  red_alert_triggers: string[];
  ignored_anomaly_types: string[];
  audit_frequency: "daily" | "weekly";
}

interface Props {
  data: AuditRulesData;
  onChange: (data: AuditRulesData) => void;
}

const FREQUENCY_OPTIONS: { value: AuditRulesData["audit_frequency"]; label: string }[] = [
  { value: "daily",  label: "Diaria" },
  { value: "weekly", label: "Semanal" },
];

interface TagInputProps {
  label: string;
  tags: string[];
  onAdd: (tag: string) => void;
  onRemove: (tag: string) => void;
  placeholder?: string;
}

function TagInput({ label, tags, onAdd, onRemove, placeholder }: TagInputProps) {
  const [input, setInput] = useState("");

  function handleAdd() {
    const trimmed = input.trim();
    if (!trimmed) return;
    if (tags.includes(trimmed)) {
      setInput("");
      return;
    }
    onAdd(trimmed);
    setInput("");
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAdd();
    }
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm text-zinc-300">{label}</label>
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="glass-input flex-1 px-3 py-2 text-sm"
        />
        <button
          type="button"
          onClick={handleAdd}
          className="glass-btn-ghost px-3 py-2 text-sm"
        >
          Agregar
        </button>
      </div>
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {tags.map((tag) => (
            <span
              key={tag}
              className="glass-strong border border-white/10 text-zinc-300 text-xs px-2 py-0.5 rounded-sm flex items-center gap-1"
            >
              {tag}
              <button
                type="button"
                onClick={() => onRemove(tag)}
                className="text-muted hover:text-zinc-100 transition-colors leading-none"
                aria-label={`Eliminar ${tag}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function AuditRulesStep({ data, onChange }: Props) {
  function handleAddRedAlert(tag: string) {
    onChange({
      ...data,
      red_alert_triggers: [...data.red_alert_triggers, tag],
    });
  }

  function handleRemoveRedAlert(tag: string) {
    onChange({
      ...data,
      red_alert_triggers: data.red_alert_triggers.filter((t) => t !== tag),
    });
  }

  function handleAddIgnored(tag: string) {
    onChange({
      ...data,
      ignored_anomaly_types: [...data.ignored_anomaly_types, tag],
    });
  }

  function handleRemoveIgnored(tag: string) {
    onChange({
      ...data,
      ignored_anomaly_types: data.ignored_anomaly_types.filter((t) => t !== tag),
    });
  }

  function handleFrequencyChange(value: AuditRulesData["audit_frequency"]) {
    onChange({ ...data, audit_frequency: value });
  }

  return (
    <div className="space-y-6">
      <h2 className="text-label text-muted uppercase tracking-widest">
        Paso 4 — Reglas de Auditoría
      </h2>

      {/* Red alert triggers */}
      <TagInput
        label="Alertas rojas automáticas"
        tags={data.red_alert_triggers}
        onAdd={handleAddRedAlert}
        onRemove={handleRemoveRedAlert}
        placeholder="Ej. caja_negativa"
      />

      {/* Ignored anomaly types */}
      <TagInput
        label="Anomalías ignoradas (normales para tu negocio)"
        tags={data.ignored_anomaly_types}
        onAdd={handleAddIgnored}
        onRemove={handleRemoveIgnored}
        placeholder="Ej. ventas_bajas_lunes"
      />

      {/* Audit frequency radio group */}
      <div className="space-y-2">
        <label className="block text-sm text-zinc-300">Frecuencia de auditoría</label>
        <div className="flex gap-6">
          {FREQUENCY_OPTIONS.map((option) => {
            const isSelected = data.audit_frequency === option.value;
            return (
              <label
                key={option.value}
                className={[
                  "flex items-center gap-2 cursor-pointer text-sm transition-colors",
                  isSelected ? "text-accent" : "text-muted",
                ].join(" ")}
              >
                <input
                  type="radio"
                  name="audit_frequency"
                  value={option.value}
                  checked={isSelected}
                  onChange={() => handleFrequencyChange(option.value)}
                  className="accent-accent"
                />
                {option.label}
              </label>
            );
          })}
        </div>
      </div>
    </div>
  );
}
