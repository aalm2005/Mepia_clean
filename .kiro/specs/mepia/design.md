# Diseño Frontend — MEPIA Dashboard & Upload

**Estado:** frontend integrado en desarrollo al 15-oct-2026; validación integral y publicación pendientes
**Stack:** Next.js App Router · TypeScript · Tailwind CSS · Supabase · FastAPI

## Visión

Interfaz de auditoría financiera para restaurantes. El frontend azul del equipo
integra superficies de vidrio, bienvenida, indicadores, gráficas y conversación
Chat IA. La jerarquía conserva alertas, cifras y unidades del análisis.

## Rutas cubiertas

| Ruta | Componente raíz | Propósito |
|------|-----------------|-----------|
| `/login` | `MepiaLogin` | Acceso único previo a MEPIA |
| `/` | `WelcomeSplash` | Bienvenida de sesión |
| `/upload` | `UploadPage` | POS/facturas, fecha y enfoque |
| `/dashboard` | `AuditReportView` | Indicadores, gráficas y hallazgos por corrida |
| `/salud` | `SaludPage` | Indicadores y gráficas |
| `/reportes` | `AuditReportView` | Hallazgos sin bloque de métricas |
| `/onboarding` | `OnboardingForm` | Configuración de cuatro pasos |
| `/chat` | `ChatPanel` | Consulta fundamentada con la sesión común |

**Acceso vigente:** Supabase identifica al usuario y se carga un negocio propio
automáticamente. El selector aún visible solo incluye negocios autorizados.
Simplificarlo con un único negocio es una mejora pendiente. No hay negocio
fijo en configuración pública ni login exclusivo para el chat.

## Artefactos de diseño

Este documento es el índice. El detalle está distribuido en archivos hermanos:

| Archivo | Contenido |
|---------|-----------|
| `design_components.md` | Árbol de componentes React, props, contratos de UI |
| `design_system.md` | Design system: `tailwind.config.ts`, paleta, tipografía, tokens |
| `design_wireframes.md` | Wireframing lógico del dashboard, upload y onboarding |
| `design_flows.md` | Flujo de interacción completo: onboarding → ingesta → análisis → pantalla |

## Principios de diseño

1. **Datos forenses primero** — anomalías `critical` y `warning` resaltan sin acción del usuario
2. **Sin ruido** — cero decoración que no aporte información
3. **Diseño azul integrado** — superficies de vidrio, números legibles y alertas con significado conservado
4. **Arquetipo visible** — el badge de arquetipo CEO es parte del lenguaje visual, no un detalle

## Decisiones de arquitectura

- Server Components por defecto; auth/shell/chat y formularios de upload/onboarding usan `"use client"`
- Dashboard consume `OrchestratorResult` por polling y requiere `run_id`; tendencias históricas aún sin conexión
- `AuditTable.tsx` soporta `AuditInsight[]` (N05) y `AgentResult[]` (paralelos)
- **Acceso vigente — Paso 5:** `/login` previo a MEPIA, cookie verificada en servidor y menú común con Chat IA. La interfaz usa negocios propios/selección común, sin `NEXT_PUBLIC_BUSINESS_ID`. Permisos directos de FastAPI legado siguen pendientes antes de publicar.

## Contratos de UI relevantes

- `AuditInsight` — generado por N05, renderizado en `AuditTable`
- `ForensicReport.risk_level` — determina el banner de alerta global
- `OrchestratorResult.pipeline_status` — controla el estado de carga
- `OrchestratorResult.escalation` — activa `Layer2Banner` y nodo `[L2]`
- `POSIngestResult` / `FacturaIngestResult` — feedback post-upload
- `OnboardingStatusResponse.onboarding_complete` — controla `OnboardingGate`

Ver `_glossary.md` para los contratos completos.

## Archivos relacionados de este nodo

- `design_components.md` — cargar para implementar componentes React
- `design_system.md` — cargar para configurar Tailwind y tokens visuales
- `design_wireframes.md` — cargar para entender el layout antes de implementar
- `design_flows.md` — cargar para implementar la lógica de interacción y estados

## Gaps cubiertos (v1.1)

| Gap | Solución |
|-----|----------|
| `/app/onboarding` inexistente | Ruta, componentes, wireframe y flujo agregados |
| Selector de arquetipo CEO | `ArchetypeSelector` en `/app/upload` antes del CTA |
| Layer 2 sin representación | `Layer2Banner` + nodo `[L2]` en `PipelineStatusBar` |
| Auth vigente (Paso 5) | Login único antes de MEPIA; chat desde menú común; sesión/negocio compartidos. 15/15 E2E sintético del frontend combinado, presentación 12/12, build final código 0. |

## Pendientes de experiencia

Tutorial guiado, adaptación móvil completa y navegación/historial de análisis.
La autorización por recurso del backend legado sigue siendo gate de producción.
Ver [estado actual](../../../docs/estado_actual_mepia.md).

## Configuración de compilación

`tsconfig.json` excluye `.test_tmp` y no incluye rutas generadas de corridas
privadas. El caché `*.tsbuildinfo` queda fuera de Git y se conserva localmente.
La limpieza no modifica contratos ni comportamiento funcional de las pantallas.
