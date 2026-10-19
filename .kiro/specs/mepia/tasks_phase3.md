# Fase 3 — Dashboard + API Routes + Integración End-to-End

**Seguimiento INC-052/053 — 15-oct-2026:** enlaces del menú conservan la corrida
en el mismo usuario/negocio. El GET devuelve el resultado completo guardado o
recupera cálculos desde su S3 explícito compatible. Estado histórico ausente no
equivale a todas las métricas activas. Validación y límites en el seguimiento
del ensayo; no acredita producción ni sustituye la evaluación funcional N15.

## Tareas

- [x] 1. Crear `types/audit.ts` con contratos de datos del frontend
  - Exportar: `AuditInsight`, `OrchestratorResult`, `ForensicReport`, `AnomalyItem`
  - Exportar: `PipelineStatus`, `Archetype`, `AlertLevel`, `POSIngestResult`, `FacturaIngestResult`
  - Basarse estrictamente en `_glossary.md` — no inventar campos
  - _Requirements: _glossary.md contratos de datos_

- [x] 2. Extender `components/AuditTable.tsx`
  - Aceptar `AuditInsight[]` además de `AuditRow[]` (union type)
  - Agregar columnas `alert_level` (`AlertLevelBadge`) y `recommended_action`
  - Fila `critical`: `border-l-2 border-red-500 bg-red-950/20`; `warning`: `border-l-2 border-amber-500`
  - Prop `isLoading?: boolean` → skeleton de 3 filas con `animate-pulse`
  - _Requirements: design_components_tree.md §AuditTable, _glossary.md AuditInsight_

- [x] 3. Crear componentes de dashboard: `AuditHeader`, `PipelineStatusBar`, `Layer2Banner`
  - `AuditHeader`: título + badge `risk_level` (rojo fijo si `high`, ámbar si `medium`)
  - `PipelineStatusBar`: nodos S1→S2→S3→S4→N05; si `escalated` agrega `[L2]` con estado propio
  - `Layer2Banner`: banner ámbar colapsable; estados `running/completed/failed`; solo si `escalated`
  - _Requirements: design_components.md, design_wireframes.md, design_flows.md §layer2_

- [x] 4. Crear `components/dashboard/AnomalyCard.tsx`, `ForensicSummary.tsx`, `DormantMetricsList.tsx`
  - `AnomalyCard`: `quantified_impact` en `font-mono text-forensic-xl`; badge severidad; lista `data_points`
  - `ForensicSummary`: panel 35%; ordena anomalías por severidad; renderiza `AnomalyCard[]`
  - `DormantMetricsList`: lista muted de métricas sin datos con sus `missing[]`
  - _Requirements: design_wireframes.md §panel lateral, _glossary.md AnomalyItem_

- [x] 5. Crear `hooks/useAuditPolling.ts`
  - Parámetros: `runId: string | null`, `intervalMs?: number` (default 2000)
  - Retorna: `{ result, pipelineStatus, currentNode, layer2Status, error }`
  - Detiene polling cuando `status` es `completed | partial | escalated | failed`
  - Si `escalated`: inicia segundo polling sobre `layer2_run_id`
  - Limpia intervalos en cleanup de `useEffect`
  - _Requirements: design_flows_main.md §polling, design_flows.md §layer2_

- [x] 6. Actualizar `app/dashboard/page.tsx` con layout completo
  - Convertir a `"use client"`; leer `run_id` de `searchParams`
  - Usar `useAuditPolling(runId)` para datos reactivos
  - Layout: `AuditHeader` + `PipelineStatusBar` + `Layer2Banner` (condicional)
  - Grid 65/35: `AuditTable` (con skeleton) + `ForensicSummary` + `DormantMetricsList`
  - _Requirements: design_wireframes.md §dashboard, design_components_tree.md_

- [x] 7. Actualizar `app/api/audit/route.ts` y crear rutas dinámicas
  - `POST /api/audit`: proxy a `POST /orchestrator/run`
  - `app/api/audit/status/[run_id]/route.ts`: proxy a `GET /orchestrator/status/{run_id}`
  - `app/api/audit/result/[run_id]/route.ts`: proxy a `GET /orchestrator/result/{run_id}`
  - `app/api/audit/layer3/status/[layer2_run_id]/route.ts`: proxy a Layer 3 status
  - _Requirements: design_flows_main.md, _glossary.md OrchestratorResult_

- [x] 8. Checkpoint final — Verificar integración end-to-end
  - `next build` sin errores de TypeScript ni Tailwind
  - Verificar flujo completo: `/onboarding` → `/upload` → `/dashboard`
  - Verificar que `PipelineStatusBar` actualiza nodos activos durante polling
  - Verificar que `Layer2Banner` aparece solo cuando `escalation.triggered: true`
  - Verificar filas `critical` con borde rojo y fondo `red-950/20`
