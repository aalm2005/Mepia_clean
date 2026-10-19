# Fase 2 — Ruta `/upload`

**Seguimiento INC-051 — 15-oct-2026:** retirada fecha fija de 2024. Día inferido
desde el reporte de ventas, validación de selección contradictoria y días
mezclados; compras con otra fecha no desplazan ventas. Sin fecha inferible se
requiere elegirla. Validación de navegador registrada en el seguimiento del ensayo.

> Estado actual (15-oct-2026): el gate descrito en las tareas originales se retiró.
> `/upload` ya no exige onboarding; los defaults se crean en segundo plano y la
> configuración avanzada sigue disponible en `/onboarding`. Las verificaciones del
> gate en esta lista son históricas.

## Tareas

- [x] 1. Crear `components/upload/OnboardingGate.tsx`
  - Server Component: llama `GET /api/onboarding/status?business_id=...`
  - `onboarding_complete: false` → renderiza `OnboardingRequiredBanner` con CTA a `/onboarding`
  - `onboarding_complete: true` → renderiza `children`
  - _Requirements: design_components.md §OnboardingGate, design_flows.md §onboarding_

- [x] 2. Crear `components/upload/ArchetypeSelector.tsx`
  - Props: `value: Archetype`, `onChange: (a: Archetype) => void`
  - 3 tarjetas horizontales; activa: `border-emerald-500 bg-zinc-800`; inactiva: `border-zinc-700 opacity-60`
  - Default: `"Operative Genius"`
  - _Requirements: design_components.md §ArchetypeSelector, design_wireframes.md_

- [x] 3. Crear `components/upload/DocumentDropzone.tsx`
  - Props: `label`, `accept: string[]`, `status`, `onFile: (f: File) => void`
  - Estados: idle (dashed zinc-700) | uploading (spinner) | done (emerald + checkmark) | error (red + msg)
  - Validar MIME antes de aceptar; soporta drag & drop y click
  - _Requirements: design_wireframes.md §estados, design_components_tree.md_

- [x] 4. Crear `components/upload/UploadStatusBadge.tsx` y `ReviewAlert.tsx`
  - `UploadStatusBadge`: badge visual por estado incluyendo `needs_human_review` (ámbar)
  - `ReviewAlert` — props: `documentType`, `fileId`, `missingFields`, `onReviewed`
  - Lista editable de `missingFields`; al confirmar: `PATCH /api/upload/review`
  - Selecciona endpoint según `documentType: "pos" | "factura"`
  - _Requirements: design_components.md §ReviewAlert, _glossary.md POSIngestResult_

- [x] 5. Crear `components/upload/UploadForm.tsx` y actualizar `app/upload/page.tsx`
  - `UploadForm`: `"use client"`, estado: `archetype`, `posFile`, `facturaFile`, status por archivo
  - `page.tsx`: Server Component → `OnboardingGate` → `UploadForm`
  - Layout: título + `ArchetypeSelector` + 2 columnas `DocumentDropzone` + CTA
  - CTA deshabilitado si no hay archivos seleccionados
  - _Requirements: design_wireframes.md §upload, design_components_tree.md_

- [x] 6. Implementar flujo de upload en `UploadForm`
  - CTA: POST POS → si `needs_human_review` → `ReviewAlert` → POST factura → si review → `ReviewAlert`
  - Luego: `POST /api/audit` con `{ archetype, business_id, date }` → `router.push("/dashboard?run_id=...")`
  - Manejar errores HTTP 409, 412, 422, 503 con mensajes específicos
  - _Requirements: design_flows_main.md, design_flows.md §errores_

- [x] 7. Actualizar `app/api/upload/route.ts` y crear `app/api/onboarding/route.ts`
  - `upload/route.ts`: handlers `POST` para POS (`/ingest/pos`) y factura (`/ingest/factura`); `PATCH` para review
  - `onboarding/route.ts`: `GET` status, `POST` crear, `PUT` actualizar
  - Implementación histórica usaba `NEXT_PUBLIC_BUSINESS_ID`; reemplazada en el Paso 5 por el negocio propio seleccionado en la sesión común de MEPIA (ver `_auth_strategy.md`).
  - _Requirements: design_flows_main.md, requirements.md §9_

- [x] 8. Checkpoint — Verificar compilación de Fase 2
  - `next build` sin errores de TypeScript
  - Verificar que `OnboardingRequiredBanner` aparece cuando gate falla
  - Verificar los 5 estados visuales de `DocumentDropzone`
  - Verificar que `ReviewAlert` aparece solo cuando `needs_human_review: true`
