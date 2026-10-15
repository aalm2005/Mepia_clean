# Diseño Frontend — Design System (Tailwind)

**Referenciado desde:** `design.md`

## Tokens vigentes de `tailwind.config.ts` — 15-oct-2026

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas:   "#050B18",
        surface:  "#0C1B33",
        elevated: "#102744",
        border:   "#1B3657",
        muted:    "#A8BED8",
        accent: {
          DEFAULT: "#1677FF",
          dim:     "#081426",
        },
        critical: {
          DEFAULT: "#ef4444",
          bg:      "#450a0a",
          border:  "#b91c1c",
        },
        warning: {
          DEFAULT: "#f59e0b",
          bg:      "#451a03",
          border:  "#b45309",
        },
        info: {
          DEFAULT: "#A8BED8",
          bg:      "#102744",
        },
        archetype: {
          operative: { badge: "#0C1B33", text: "#55C7FF" },
          purist:    { badge: "#102744", text: "#258BFF" },
          hacker:    { badge: "#081426", text: "#00E5FF" },
        },
        emerald: {
          50: "#F0F7FF", 100: "#DCEBFA", 200: "#A8BED8", 300: "#55C7FF",
          400: "#55C7FF", 500: "#258BFF", 600: "#1677FF", 700: "#155CC2",
          800: "#102744", 900: "#0C1B33", 950: "#081426",
        },
        violet: {
          50: "#F0F7FF", 100: "#DCEBFA", 200: "#A8BED8", 300: "#7ECFFF",
          400: "#55C7FF", 500: "#258BFF", 600: "#1677FF", 700: "#155CC2",
          800: "#102744", 900: "#0C1B33", 950: "#081426",
        },
        zinc: {
          50: "#F0F7FF", 100: "#F0F7FF", 200: "#DCEBFA", 300: "#C2D4E8",
          400: "#A8BED8", 500: "#A8BED8", 600: "#7E9BB8", 700: "#52708F",
          800: "#1B3657", 900: "#0C1B33", 950: "#050B18",
        },
      },
      fontFamily: {
        sans:  ["Inter", "sans-serif"],
        mono:  ["JetBrains Mono", "Fira Code", "monospace"],
      },
      fontSize: {
        "forensic-xl": ["2.25rem", { lineHeight: "1", fontWeight: "700", letterSpacing: "-0.02em" }],
        "forensic-lg": ["1.5rem",  { lineHeight: "1.2", fontWeight: "600" }],
        "label":       ["0.6875rem", { lineHeight: "1", fontWeight: "500", letterSpacing: "0.1em" }],
      },
      spacing: {
        "panel": "1.5rem",
        "row":   "1.25rem",
      },
      borderWidth: {
        "alert": "2px",
      },
      boxShadow: {
        "panel": "0 0 0 1px #1B3657",
        "glow-critical": "0 0 12px 0 rgba(37,139,255,0.25)",
      },
    },
  },
  plugins: [],
};

export default config;
```

## Tokens de tipografía

| Uso | Clase | Fuente |
|-----|-------|--------|
| Títulos de sección | `text-forensic-lg font-semibold text-zinc-100` | Inter |
| Labels de columna | `text-label uppercase tracking-widest text-zinc-400` | Inter |
| Números forenses | `font-mono text-forensic-xl text-zinc-100` | JetBrains Mono |
| Texto de insight | `text-sm leading-relaxed text-zinc-200` | Inter |
| Texto muted | `text-xs text-zinc-500` | Inter |

## Tokens de badge por `alert_level`

```typescript
const alertBadge = {
  critical: "bg-red-950  text-red-400  border border-red-700",
  warning:  "bg-amber-950 text-amber-400 border border-amber-700",
  info:     "bg-zinc-800 text-zinc-400  border border-zinc-700",
}
```

## Tokens de badge por `archetype`

```typescript
const archetypeBadge = {
  "Operative Genius": "bg-emerald-900 text-emerald-300",
  "Product Purist":   "bg-violet-900  text-violet-300",
  "Growth Hacker":    "bg-amber-900   text-amber-300",
}
```

## Aplicación visual actual

- Diseño azul y superficies de vidrio recibidos del equipo; bordes redondeados y sombras definidos en CSS.
- Los alias `emerald`, `violet` y `zinc` se mapean a la paleta azul; consultar los tokens, no su nombre histórico.
- Estados críticos en rojo y advertencias en ámbar: conservan significado, cifras y unidades.
- Números legibles, gráficas por unidad y estados vacíos sin datos inventados.
- Menú móvil y distribuciones adaptables existentes; revisión completa de pantallas aún pendiente.
- Véase [estado actual](../../../docs/estado_actual_mepia.md).

## Archivos relacionados de este nodo

- `design_components.md` — qué componentes usan estos tokens
- `design_wireframes.md` — cómo se aplica el sistema visual en el layout
