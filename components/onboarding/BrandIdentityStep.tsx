"use client";

import { useState } from "react";

export interface BrandIdentityData {
  brand_voice: string;
  prohibited_recommendations: string[];
  priority_focus: "efficiency" | "quality" | "growth";
}

interface Props {
  data: BrandIdentityData;
  onChange: (data: BrandIdentityData) => void;
}

const PRIORITY_OPTIONS: { value: BrandIdentityData["priority_focus"]; label: string }[] = [
  { value: "efficiency", label: "Eficiencia" },
  { value: "quality",    label: "Calidad" },
  { value: "growth",     label: "Crecimiento" },
];

const MAX_VOICE_CHARS = 500;

export default function BrandIdentityStep({ data, onChange }: Props) {
  const [tagInput, setTagInput] = useState("");
  const [voiceTouched, setVoiceTouched] = useState(false);

  const voiceError = voiceTouched && data.brand_voice.trim() === "";

  function handleVoiceChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const value = e.target.value.slice(0, MAX_VOICE_CHARS);
    onChange({ ...data, brand_voice: value });
  }

  function handleAddTag() {
    const trimmed = tagInput.trim();
    if (!trimmed) return;
    if (data.prohibited_recommendations.includes(trimmed)) {
      setTagInput("");
      return;
    }
    onChange({
      ...data,
      prohibited_recommendations: [...data.prohibited_recommendations, trimmed],
    });
    setTagInput("");
  }

  function handleTagKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddTag();
    }
  }

  function handleRemoveTag(tag: string) {
    onChange({
      ...data,
      prohibited_recommendations: data.prohibited_recommendations.filter((t) => t !== tag),
    });
  }

  function handlePriorityChange(value: BrandIdentityData["priority_focus"]) {
    onChange({ ...data, priority_focus: value });
  }

  return (
    <div data-tour="advanced-config-brand" className="space-y-6">
      <h2 className="text-label text-muted uppercase tracking-widest">
        Paso 1 — Identidad de Marca
      </h2>

      {/* Brand voice textarea */}
      <div className="space-y-1.5">
        <label className="block text-sm text-zinc-300">
          Describe el tono y valores de tu negocio
        </label>
        <textarea
          value={data.brand_voice}
          onChange={handleVoiceChange}
          onBlur={() => setVoiceTouched(true)}
          rows={4}
          className="glass-input w-full p-3 text-sm resize-none"
          placeholder="Ej. Somos un café de especialidad con enfoque en calidad y experiencia del cliente..."
        />
        <div className="flex items-center justify-between">
          {voiceError ? (
            <span className="text-xs text-critical">Este campo es requerido</span>
          ) : (
            <span />
          )}
          <span className="text-xs text-muted ml-auto">
            {data.brand_voice.length}/{MAX_VOICE_CHARS}
          </span>
        </div>
      </div>

      {/* Prohibited recommendations tag input */}
      <div className="space-y-2">
        <label className="block text-sm text-zinc-300">
          Recomendaciones prohibidas
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={handleTagKeyDown}
            placeholder="Ej. marketing agresivo"
            className="glass-input flex-1 px-3 py-2 text-sm"
          />
          <button
            type="button"
            onClick={handleAddTag}
            className="glass-btn-ghost px-3 py-2 text-sm"
          >
            Agregar
          </button>
        </div>
        {data.prohibited_recommendations.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {data.prohibited_recommendations.map((tag) => (
              <span
                key={tag}
                className="glass-strong border border-white/10 text-zinc-300 text-xs px-2 py-0.5 rounded-sm flex items-center gap-1"
              >
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
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

      {/* Priority focus radio group */}
      <div className="space-y-2">
        <label className="block text-sm text-zinc-300">Foco principal</label>
        <div className="flex gap-6">
          {PRIORITY_OPTIONS.map((option) => {
            const isSelected = data.priority_focus === option.value;
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
                  name="priority_focus"
                  value={option.value}
                  checked={isSelected}
                  onChange={() => handlePriorityChange(option.value)}
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
