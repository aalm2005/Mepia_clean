# Diseño Frontend — Wireframe Onboarding

**Alcance al 15-oct-2026:** [estado y recorrido actual](../../../docs/estado_actual_mepia.md). El negocio propio se carga automáticamente tras login. Los esquemas inferiores conservan contratos/diseño base; el tutorial didáctico sigue pendiente y la adaptación móvil es parcial.

**Referenciado desde:** `design_wireframes.md`

## Layout `/onboarding`

```
┌─────────────────────────────────────────────────────────────┐
│ MEPIA — CONFIGURACIÓN INICIAL                               │
│ Define el lente de auditoría de tu negocio                  │
├─────────────────────────────────────────────────────────────┤
│ [1. Identidad]──[2. Umbrales]──[3. Costos]──[4. Reglas]    │
│       ●               ○              ○             ○        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PASO 1 — IDENTIDAD DE MARCA                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Describe el tono y valores de tu negocio            │   │
│  │ (textarea — max 500 chars)                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Recomendaciones prohibidas:                                │
│  [+ Agregar] [tag: "marketing agresivo" ×]                  │
│                                                             │
│  Foco principal:                                            │
│  ( ) Eficiencia  ( ) Calidad  (●) Crecimiento               │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                              [Siguiente →]                  │
└─────────────────────────────────────────────────────────────┘
```

## Paso 2 — Umbrales de Auditoría

```
│  Discrepancia de caja máxima:  [  2  ] %  o  [ 150 ] MXN   │
│  (se usa el más permisivo)                                  │
│                                                             │
│  Margen warning:   [ 15 ] %                                 │
│  Margen crítico:   [  8 ] %                                 │
│  Spike de costo:   [ 10 ] %                                 │
```

Inputs numéricos con validación inline. `margin_critical` no puede ser ≥ `margin_warning`.

## Paso 3 — Estructura de Costos Fijos

```
│  ┌──────────────────┬──────────┬──────────┬──────────┐     │
│  │ Concepto         │ Monto/mes│ Tolerancia│ Tipo     │     │
│  ├──────────────────┼──────────┼──────────┼──────────┤     │
│  │ Renta            │ $18,000  │ 0%       │ FIXED    │     │
│  │ Gas              │ $3,500   │ 10%      │ VARIABLE │     │
│  └──────────────────┴──────────┴──────────┴──────────┘     │
│  [+ Agregar costo]                                          │
```

Mínimo 1 fila requerida. Tipo: `FIXED` | `VARIABLE` | `CAPEX`.

## Paso 4 — Reglas de Auditoría

```
│  Alertas rojas automáticas:                                 │
│  [+ Agregar] [tag: "caja_negativa" ×] [tag: "ventas_cero" ×]│
│                                                             │
│  Anomalías ignoradas (normales para tu negocio):            │
│  [+ Agregar]                                                │
│                                                             │
│  Frecuencia de auditoría: (●) Diaria  ( ) Semanal          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  [← Anterior]              [Guardar configuración ✓]        │
└─────────────────────────────────────────────────────────────┘
```

## Comportamiento general

- 4 pasos lineales con indicador de progreso en la parte superior
- "Guardar configuración" solo aparece en el paso 4
- Si onboarding ya existe → campos pre-llenados con valores actuales (`PUT`)
- Tras guardar exitosamente → redirige a `/upload`
- Error 409 (ya existe) → cambia automáticamente a modo edición (`PUT`)

## Archivos relacionados de este nodo

- `design_components.md` — `OnboardingForm` y sus 4 pasos
- `design_flows.md` — flujo de onboarding completo
