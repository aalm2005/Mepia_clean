# Diseño Frontend — Componentes y responsabilidades

Contrato vigente al 19-oct-2026. [Índice](design.md), [árbol](design_components_tree.md).

## Acceso y selección

`MepiaAuthProvider` verifica usuario y carga negocios propios; comparte sesión,
negocio y corrida con `MepiaShell`. Conserva referencias mínimas en memoria y
sessionStorage por pestaña/usuario/negocio; no copia resultados ni agrega tokens.
Recargar conserva la referencia; cambiar negocio o salir la elimina inmediatamente.

`AuditReportView` sirve Dashboard, Salud y Reportes. `useAnalysisHistory` resuelve
enlace explícito, selección recordada y último terminado; lista páginas y ofrece
reintento. `AnalysisHistory` distingue fecha analizada, hora de guardado, estado,
número de opción y referencia breve. Seleccionar solo ejecuta lecturas.

`useAuditPolling(runId, intervalMs=2000)` obtiene el resultado protegido y repite
únicamente mientras corre. Retorna result, pipelineStatus, currentNode,
layer3Status, layer3DraftStatus y error. Resuelve seguimiento avanzado mediante
el N05 autorizado, sin pedir al cliente un padre arbitrario. Aborta peticiones
y descarta estados/resultados de otro ámbito.

## Presentación

| Componente | Responsabilidad |
|---|---|
| AuditHeader | Fecha/corrida; riesgo desconocido no se muestra como bajo |
| PipelineStatusBar | Estado del análisis e informe avanzado en español; sin diagrama de nodos internos |
| Layer2Banner | Preparando / guardado / no pudo guardarse; sin enlace inexistente |
| KpiGrid | Solo indicadores conservados; cero válido visible, decimales textuales admitidos |
| MetricsCharts | Barras por unidad y evolución de indicadores diarios desde useAnalysisTrends |
| AuditTable | Hallazgos N05, nivel y acción; soporta contrato legado AuditRow |
| ForensicSummary | Anomalías y disponibilidad forense; no confunde ausencia de evidencia con ausencia de anomalías |
| DormantMetricsList | Faltantes y estado S2 conocido/desconocido; sin términos internos |

ForensicSummary recibe disponibilidad derivada del informe original, cálculos
válidos y estado terminado. Listas vacías o fallback visual no demuestran evaluación.
Los gráficos admiten finitos con estado válido; no convierten ausencia en cero.
[Contratos de lectura](analysis_history_contracts.md), [tendencias](analysis_history_trends.md).

## Documentos y configuración

UploadForm no exige el formulario avanzado: consulta ajustes y crea defaults
solo si faltan; costos inicialmente vacíos. OnboardingForm recupera ajustes y
ofrece cuatro pasos editables. GET/POST/PUT comprueban sesión y propietario.
ArchetypeSelector conserva los tres enfoques; DocumentDropzone valida tipos
admitidos. ReviewAlert permite corregir campos de POS/factura antes de continuar.
Fecha vacía se infiere del lote de ventas; una contradicción detiene el análisis.
La interfaz no promete carga Excel/CSV ni un OCR general.

INC-050–053 conservadas; INC-055–057 verificadas con servicios simulados.
[Evidencia](../../../docs/analysis_history_dashboard_20261019.md).


[Versión anterior conservada](../../../docs/history/documentation_before_sync_20261019/.kiro/specs/mepia/design_components.md). Sus estados y cifras describen su fecha original.
