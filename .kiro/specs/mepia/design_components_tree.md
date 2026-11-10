# Diseño Frontend — Árbol de componentes

Actualizado para Q6 el 4-nov-2026. [Contratos](design_components.md).

```text
RootLayout
 └ MepiaAuthProvider → MepiaShell + GlassBackground
    ├ MepiaTour → recorrido guiado y progreso por usuario y negocio
    ├ /login → MepiaLogin
    ├ /dashboard → AuditReportView
    ├ /salud → AuditReportView (view=health)
    ├ /reportes → AuditReportView (sin bloque de métricas)
    │   ├ useAnalysisHistory → AnalysisHistory
    │   ├ useAuditPolling → resultado guardado y estado avanzado protegido
    │   ├ AuditHeader + PipelineStatusBar + Layer2Banner condicional
    │   ├ KpiGrid + MetricsCharts (Dashboard/Salud)
    │   │   └ useAnalysisTrends → MetricLineChart + gráficas por unidad
    │   ├ AuditTable
    │   ├ ForensicSummary → AnomalyCard
    │   └ DormantMetricsList
    ├ /chat → ChatPanel
    │   └ conversación, fuentes, fecha y compositor inferior
    ├ /upload → UploadForm
    │   ├ ArchetypeSelector
    │   ├ DocumentDropzone POS PDF
    │   ├ DocumentDropzone factura XML/PDF
    │   ├ UploadStatusBadge + ReviewAlert
    │   └ enlace opcional a ajustes avanzados
    └ /onboarding → OnboardingForm
        ├ BrandIdentityStep
        ├ AuditTolerancesStep
        ├ CostStructureStep
        └ AuditRulesStep
```

Las tres vistas comparten selección y lógica, con diferencias de presentación.
El marco se remonta por usuario/negocio, y los hooks abortan respuestas antiguas.
Historial, métricas, errores y estados están ligados al mismo ámbito autorizado.
Cambiar negocio o cerrar sesión limpia datos sin esperar a la respuesta siguiente.

Las gráficas se cargan dinámicamente; el frontend conserva valores, unidades y
estados persistidos. Las tendencias consultan varios días, sin volver a ejecutar
el análisis ni sumar varias corridas del mismo día.

El menú y el logo conservan la selección al navegar y al volver del chat,
incluso tras recargar esa visita. La conversación N15 sigue siendo temporal y
distinta del historial persistido de análisis.

El diagrama representa responsabilidades, no proporciones exactas de pantalla
ni una certificación de todos los tamaños móviles.
[Flujos](design_flows.md), [wireframes](design_wireframes.md),
[selección y estados](analysis_history_ui.md).


[Versión anterior conservada](../../../docs/history/documentation_before_sync_20261019/.kiro/specs/mepia/design_components_tree.md). Sus estados y cifras describen su fecha original.
