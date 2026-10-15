# Diseño Frontend — Árbol de Componentes

**Acceso e inicio — 15-oct-2026, validado localmente; sin commit:** sesión por pestaña (recargar conserva; cerrar/abrir pide login), Dashboard como inicio y bienvenida eliminada. API con Bearer y verificación de servidor; cookies antiguas no autentican. [Contrato, pruebas y límites](../../../docs/mepia_access_navigation.md). INC-042 resuelta localmente: Edge 24/24, cero errores; build y tipos código 0. 42 incidencias: 39 resueltas, dos mitigadas y una pendiente externa. Los informes fechados anteriores no validan este cambio.

**Alcance al 15-oct-2026:** [estado y recorrido actual](../../../docs/estado_actual_mepia.md). El negocio propio se carga automáticamente tras login. Los esquemas inferiores conservan contratos/diseño base; el tutorial didáctico sigue pendiente y la adaptación móvil es parcial.

**Referenciado desde:** `design.md`
**Árbol completo:** `design_components_tree.md`

## Acceso y navegación común de MEPIA (Paso 5)

`MepiaAuthProvider` comparte sesión, negocios propios y selección; `MepiaShell`
contiene menú común adaptable, selector y cierre de sesión. El proveedor verifica
al usuario de la pestaña antes de mostrar páginas; middleware verifica Bearer
para APIs legadas y Chat mantiene sus permisos de servidor. `MepiaLogin` en `/login` precede a toda MEPIA;
`ChatPanel` dentro de `/chat` consume contexto y presenta conversación/compositor
inferior, sin formulario propio de login. Iconos SVG de MepiaIcon conservan
identidad MEPIA. Dataset/turnos siguen con permisos/guardas del motor.
Frontend del equipo integrado el 14-oct; al 15-oct se retira WelcomeSplash.
Se mantienen GlassBackground y
AuditReportView/KpiGrid/MetricsCharts en Dashboard, Salud y Reportes, bajo el
MepiaShell común. Hook cancela datos anteriores y verifica negocio/corrida.
E2E final 15/15, presentación 12/12, cero errores, build final código 0.

## Componentes nuevos (v1.1)

### `ArchetypeSelector.tsx`

```typescript
type Archetype = "Operative Genius" | "Product Purist" | "Growth Hacker"
interface ArchetypeSelectorProps {
  value: Archetype
  onChange: (archetype: Archetype) => void
}
```

3 tarjetas seleccionables. Activa: `border-emerald-500 bg-zinc-800`.
Inactivas: `border-zinc-700 opacity-60`. Default: `"Operative Genius"`.

### `ReviewAlert.tsx`

```typescript
interface ReviewAlertProps {
  documentType: "pos" | "factura"
  fileId: string
  missingFields: string[]
  onReviewed: () => void
}
```

Reutilizable para ambos tipos de documento. Muestra los `missing_fields` como lista
editable. Al confirmar llama:
- POS: `PATCH /ingest/pos/{file_id}/review`
- Factura: `PATCH /ingest/factura/{file_id}/review`

El endpoint se selecciona automáticamente según `documentType`.

### `OnboardingGate.tsx`

Server Component. Llama `GET /business/{id}/onboarding/status`.
`onboarding_complete: false` → `OnboardingRequiredBanner` con link a `/onboarding`.
`onboarding_complete: true` → renderiza `children`.

### `Layer2Banner.tsx`

Banner ámbar colapsable. Solo visible cuando `pipeline_status: "escalated"`.
`running` → spinner · `completed` → "Ver análisis profundo →" · `failed` → error.

### `PipelineStatusBar.tsx` (extendido)

```typescript
interface PipelineStatusBarProps {
  status: "idle"|"running"|"completed"|"partial"|"escalated"|"failed"
  currentNode?: string
  layer2Status?: "running"|"completed"|"failed"
}
```

Pasos: S1 → S2 → S3 → S4 → N05. Si `escalated`, agrega nodo `[L2]` al final.

### `OnboardingForm.tsx` (nuevo)

4 pasos lineales: `BrandIdentityStep` → `AuditTolerancesStep` →
`CostStructureStep` → `AuditRulesStep`. Botón "Guardar" solo en paso 4.

## Componentes existentes (sin cambios de interfaz)

- `AuditTable` — se extiende con columna `alert_level` y `recommended_action`
- `AnomalyCard` — `quantified_impact` en `font-mono text-2xl`
- `DocumentDropzone` — valida MIME antes de enviar

Ver `design_components_tree.md` para el árbol completo con todas las rutas.

## Archivos relacionados de este nodo

- `design_components_tree.md` — árbol completo de componentes por ruta
- `design_system.md` — tokens de color para badges y bordes
- `design_wireframes.md` — posición de cada componente en el layout
