# Diseño Frontend — Árbol Completo de Componentes

**Alcance al 15-oct-2026:** [estado y recorrido actual](../../../docs/estado_actual_mepia.md). El negocio propio se carga automáticamente tras login. Los esquemas inferiores conservan contratos/diseño base; el tutorial didáctico sigue pendiente y la adaptación móvil es parcial.

**Referenciado desde:** `design_components.md`

## Componentes incorporados del frontend del equipo — 14-oct-2026

RootLayout conserva MepiaAuthProvider/MepiaShell y agrega GlassBackground.
Inicio muestra WelcomeSplash después del login; Dashboard y Reportes usan
AuditReportView (KpiGrid/MetricsCharts/AuditTable); Salud usa KpiGrid/MetricsCharts.
Todas son páginas cliente dentro del mismo marco, con módulos de gráficas
cargados dinámicamente. useAuditPolling limpia contexto/cancela peticiones y
verifica negocio/corrida antes de mostrar resultado. Se conserva el backend.
El árbol anterior debajo conserva el detalle de los componentes base.

## Árbol por ruta

```
app/
├── layout.tsx                    # RootLayout → MepiaAuthProvider → MepiaShell
│                                 # menú/negocio/sesión comunes; middleware valida entrada
├── login/
│   └── page.tsx                  # MepiaLogin — único acceso antes de MEPIA
├── chat/
│   └── page.tsx                  # ChatPanel — contexto común, sin login propio
│                                 # mensajes, compositor inferior, fuentes e historial
│
├── onboarding/
│   └── page.tsx                  # OnboardingPage (Server Component)
│       └── OnboardingForm        # "use client" — 4 pasos
│           ├── BrandIdentityStep # brand_voice, prohibited_recommendations, priority_focus
│           ├── AuditTolerancesStep # discrepancia, margen warning/crítico, spike
│           ├── CostStructureStep # lista ExpectedCostStructure (add/remove)
│           └── AuditRulesStep    # red_alert_triggers, ignored_anomaly_types
│
├── upload/
│   └── page.tsx                  # UploadPage (Server Component)
│       └── UploadForm            # "use client"
│           ├── OnboardingGate    # Verifica onboarding_complete antes de mostrar form
│           ├── ArchetypeSelector # 3 tarjetas: Operative | Purist | Hacker
│           ├── DocumentDropzone  # POS — drag & drop + click, acepta .pdf
│           ├── DocumentDropzone  # Factura — drag & drop + click, acepta .pdf,.xml
│           ├── UploadStatusBadge # idle | uploading | done | error
│           └── ReviewAlert       # Visible si needs_human_review: true
│
└── dashboard/
    └── page.tsx                  # DashboardPage (Client Component → AuditReportView)
        ├── AuditHeader           # Título + risk_level badge global
        ├── PipelineStatusBar     # S1→S2→S3→S4→N05 [→L2 si escalated]
        ├── Layer2Banner          # Solo si pipeline_status: "escalated"
        ├── AuditTable            # Tabla forense principal
        │   ├── AuditRow          # módulo | raw_result | copilot_phrase | alert_level
        │   └── ArchetypeBadge    # Badge por arquetipo CEO
        ├── ForensicSummary       # Panel lateral 35%
        │   └── AnomalyCard       # quantified_impact + severity + data_points
        └── DormantMetricsList    # Métricas sin datos suficientes
```

## Contratos de props clave

### `AuditTable`
```typescript
interface AuditTableProps {
  rows: AuditInsight[] | AuditRow[]
  isLoading?: boolean
  emptyMessage?: string
}
```

Columnas: Módulo (15%) · Resultado Forense (30%) · Insight CEO (35%) · Nivel (10%) · Acción (10%)

Fila `critical`: `border-l-2 border-red-500 bg-red-950/20`

## Archivos relacionados de este nodo

- `design_components.md` — especificación de componentes nuevos
- `design_wireframes.md` — posición en el layout
