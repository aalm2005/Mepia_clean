# Diseño Frontend — MEPIA Dashboard & Upload

**Entorno verificado — 15-oct-2026:** interfaz y servidor completo usan
MEPIA principal; 009/010/011 aplicadas con autorización y datos preservados.
Regresión 178/41 subpruebas, código 0; SQL real 13/13 controles. Usuario confirmó
login y pantallas antes/después del retiro de claves heredadas y firma HS256.
INC-046/047 resueltas en su alcance; INC-048 y ensayo de análisis nuevo pendientes.
Las evaluaciones anteriores conservan su entorno original.
[Ejecución, archivos y límites](../../../docs/database_unification.md).

**Acceso e inicio — 15-oct-2026, validado localmente; sin commit:** sesión por pestaña (recargar conserva; cerrar/abrir pide login), Dashboard como inicio y bienvenida eliminada. API con Bearer y verificación de servidor; cookies antiguas no autentican. [Contrato, pruebas y límites](../../../docs/mepia_access_navigation.md). INC-042 resuelta localmente: Edge 24/24, cero errores; build y tipos código 0. 42 incidencias: 39 resueltas, dos mitigadas y una pendiente externa. Los informes fechados anteriores no validan este cambio.

**Estado:** frontend integrado en desarrollo al 15-oct-2026; validación integral y publicación pendientes
**Stack:** Next.js App Router · TypeScript · Tailwind CSS · Supabase · FastAPI

## Visión

Interfaz de auditoría financiera para restaurantes. El frontend azul del equipo
integra superficies de vidrio, indicadores, gráficas y conversación
Chat IA. La jerarquía conserva alertas, cifras y unidades del análisis.

## Rutas cubiertas

| Ruta | Componente raíz | Propósito |
|------|-----------------|-----------|
| `/login` | `MepiaLogin` | Acceso único previo a MEPIA |
| `/` | Redirección | Lleva a `/dashboard`, inicio único |
| `/upload` | `UploadPage` | POS/facturas, fecha y enfoque |
| `/dashboard` | `AuditReportView` | Indicadores, gráficas y hallazgos por corrida |
| `/salud` | `SaludPage` | Indicadores y gráficas |
| `/reportes` | `AuditReportView` | Hallazgos sin bloque de métricas |
| `/onboarding` | `OnboardingForm` | Personalización avanzada opcional de cuatro pasos; Documentos aplica valores iniciales si faltan |
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
- **Acceso vigente:** sesión por pestaña, usuario validado antes de mostrar MEPIA y Bearer verificado para APIs. Dashboard como inicio; sin bienvenida duplicada. Negocios propios y permisos directos de FastAPI legado con sus alcances previos.

## Contratos de UI relevantes

- `AuditInsight` — generado por N05, renderizado en `AuditTable`
- `ForensicReport.risk_level` — determina el banner de alerta global
- `OrchestratorResult.pipeline_status` — controla el estado de carga
- `OrchestratorResult.escalation` — activa `Layer2Banner` y nodo `[L2]`
- `POSIngestResult` / `FacturaIngestResult` — feedback post-upload
- `OnboardingStatusResponse.onboarding_complete` — decide si se crean defaults en segundo plano; nunca bloquea la carga
- `OnboardingStatusResponse.settings` — precarga valores guardados en el formulario avanzado

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
| Auth vigente (Paso 5) | Sesión por pestaña y Dashboard como inicio. Edge 24/24, cero errores, build/tipos código 0 el 15-oct. La integración original del 14-oct conserva sus 15/15 y presentación 12/12 como históricos. |

## Pendientes de experiencia

Tutorial guiado, adaptación móvil completa y navegación/historial de análisis.
La autorización por recurso del backend legado sigue siendo gate de producción.
Ver [estado actual](../../../docs/estado_actual_mepia.md).

## Configuración de compilación

`tsconfig.json` excluye `.test_tmp` y no incluye rutas generadas de corridas
privadas. El caché `*.tsbuildinfo` queda fuera de Git y se conserva localmente.
La limpieza no modifica contratos ni comportamiento funcional de las pantallas.
