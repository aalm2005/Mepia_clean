# Diseño Frontend — Wireframing Lógico

**Alcance al 15-oct-2026:** [estado y recorrido actual](../../../docs/estado_actual_mepia.md). El negocio propio se carga automáticamente tras login. Los esquemas inferiores conservan contratos/diseño base; el tutorial didáctico sigue pendiente y la adaptación móvil es parcial.

**Referenciado desde:** `design.md`

## Acceso general y Chat IA integrado

Sin sesión: pantalla de bienvenida MEPIA, correo/contraseña e Iniciar sesión.
Después del acceso: bienvenida del equipo y menú lateral común (Inicio,
Dashboard, Documentos, Chat IA, Salud del Negocio, Reportes, Configuración), selector de negocio en cabecera y cierre de sesión en el menú.
Chat IA ocupa el área central: bienvenida/sugerencias al estar vacío, mensajes
de usuario a la derecha y respuestas MEPIA con fuentes a la izquierda;
compositor redondeado inferior y nueva conversación/fecha en cabecera.
Marco azul y superficies de vidrio del equipo; conversación similar a ChatGPT. En móvil, el menú
se abre desde su icono y el compositor permanece disponible mientras se desplazan
mensajes/sugerencias. El chat no presenta otro login. E2E sintético final 15/15; bienvenida visible
y gráficas por unidad verificadas en la integración del 14-oct.

## Layout `/dashboard`

```
┌─────────────────────────────────────────────────────────────┐
│ MEPIA                              [risk_level: HIGH ●]     │  ← AuditHeader
│ Reporte de Auditoría Forense       Última auditoría: hoy    │
├─────────────────────────────────────────────────────────────┤
│ Pipeline: [S1 ✓]──[S2 ✓]──[S3 ✓]──[S4 ✓]──[N05 ✓]──[L2⟳] │  ← PipelineStatusBar
├─────────────────────────────────────────────────────────────┤
│ ▲ Análisis profundo en curso (Layer 2) — Ver resultados →   │  ← Layer2Banner (si escalated)
├──────────────────────────────────┬──────────────────────────┤
│                                  │  ANOMALÍAS CRÍTICAS      │
│  TABLA FORENSE PRINCIPAL         │  ┌────────────────────┐  │
│  ┌──────┬──────────┬──────────┐  │  │ margin_leak        │  │
│  │Módulo│Resultado │Insight   │  │  │ -10% margen        │  │
│  │      │Forense   │CEO       │  │  │ ~$1,200 MXN        │  │
│  ├──────┼──────────┼──────────┤  │  └────────────────────┘  │
│  │ ●    │ raw_res  │ frase +  │  │  ┌────────────────────┐  │
│  │ crit │ número   │ badge    │  │  │ source_discrepancy │  │
│  ├──────┼──────────┼──────────┤  │  │ -320 MXN           │  │
│  │ ▲    │ raw_res  │ frase +  │  │  └────────────────────┘  │
│  │ warn │ número   │ badge    │  │                          │
│  ├──────┼──────────┼──────────┤  │  MÉTRICAS DORMANT        │
│  │ ─    │ raw_res  │ frase +  │  │  · inventory_variance    │
│  │ info │ número   │ badge    │  │    falta: recipes        │
│  └──────┴──────────┴──────────┘  │                          │
│                                  │                          │
└──────────────────────────────────┴──────────────────────────┘
```

**Proporciones:** tabla principal 65% · panel lateral 35%

`Layer2Banner` solo aparece cuando `pipeline_status: "escalated"`. Es colapsable.
El nodo `[L2]` muestra spinner si Layer 2 corre, checkmark verde si completó, rojo si falló.

### Jerarquía visual

1. Banner `risk_level: "high"` — barra roja fija, imposible ignorar
2. Filas `critical` — borde izquierdo rojo + fondo `red-950/20`
3. `AnomalyCard` — `quantified_impact` en `font-mono text-2xl`
4. Filas `warning` — borde ámbar
5. Filas `info` — estilo base

Panel lateral: `low` → solo dormant · `medium` → warnings · `high` → critical primero

---

## Layout `/upload`

```
┌─────────────────────────────────────────────────────────────┐
│ INGESTA — Subir Documentos de Auditoría                     │
├─────────────────────────────────────────────────────────────┤
│ ARQUETIPO CEO                                               │
│ [Operative Genius ✓]  [Product Purist]  [Growth Hacker]    │
├──────────────────────────┬──────────────────────────────────┤
│  TICKET POS              │  FACTURA DE PROVEEDOR            │
│  ┌────────────────────┐  │  ┌────────────────────────────┐  │
│  │  Arrastra tu PDF   │  │  │  Arrastra PDF o XML        │  │
│  │  [Seleccionar PDF] │  │  │  [Seleccionar archivo]     │  │
│  └────────────────────┘  │  └────────────────────────────┘  │
│  Estado: idle            │  Estado: idle                    │
├──────────────────────────┴──────────────────────────────────┤
│  [Analizar con Agentes IA →]                                │
│  ⚠ needs_human_review: true → ReviewAlert aparece aquí     │
└─────────────────────────────────────────────────────────────┘
```

**Selector de arquetipo:** 3 tarjetas horizontales. La seleccionada tiene `border-emerald-500`.
El arquetipo se envía en el payload de `POST /orchestrator/run`.

### Estados del formulario de upload

| Estado | Visual |
|--------|--------|
| `idle` | Dropzone con borde `border-dashed border-zinc-700` |
| `uploading` | Spinner + texto "Procesando OCR..." |
| `done` | Borde `border-emerald-500` + checkmark |
| `error` | Borde `border-red-500` + mensaje de error |
| `needs_human_review` | `ReviewAlert` con campos faltantes listados |

## Archivos relacionados de este nodo

- `design_components.md` — especificación de cada componente del wireframe
- `design_flows.md` — lógica de transición entre estados
- `design_wireframes_onboarding.md` — wireframe de `/app/onboarding`
