# Diseño Frontend — Diagrama de Secuencia Principal

**Acceso e inicio — 15-oct-2026, validado localmente; sin commit:** sesión por pestaña (recargar conserva; cerrar/abrir pide login), Dashboard como inicio y bienvenida eliminada. API con Bearer y verificación de servidor; cookies antiguas no autentican. [Contrato, pruebas y límites](../../../docs/mepia_access_navigation.md). INC-042 resuelta localmente: Edge 24/24, cero errores; build y tipos código 0. 42 incidencias: 39 resueltas, dos mitigadas y una pendiente externa. Los informes fechados anteriores no validan este cambio.

**Alcance al 15-oct-2026:** [estado y recorrido actual](../../../docs/estado_actual_mepia.md). El negocio propio se carga automáticamente tras login. Los esquemas inferiores conservan contratos/diseño base; el tutorial didáctico sigue pendiente y la adaptación móvil es parcial.

**Referenciado desde:** `design_flows.md`

## Flujo completo: onboarding → ingesta → análisis → pantalla

```mermaid
sequenceDiagram
    participant U as Usuario
    participant UP as /upload
    participant API as Next.js API Route
    participant FA as FastAPI
    participant DB as Supabase

    Note over U,FA: Login previo e identificación automática del negocio propio
    Note over U,FA: OnboardingGate — al abrir /upload desde MEPIA
    UP->>FA: GET /business/{id}/onboarding/status
    alt onboarding_complete: false
        UP->>U: OnboardingRequiredBanner → /onboarding
        U->>FA: POST /business/{id}/onboarding
        FA-->>DB: Persiste en mepia_memory + business_fixed_costs
        FA-->>U: HTTP 201 → redirige a /upload
    end

    U->>UP: Selecciona arquetipo CEO (ArchetypeSelector)
    U->>UP: Selecciona PDF de POS + PDF/XML de factura
    U->>UP: Click "Analizar con Agentes IA"

    UP->>API: POST /api/upload (multipart: pos_file)
    API->>FA: POST /ingest/pos
    FA-->>DB: Persiste en documents + pos_inputs
    FA-->>API: POSIngestResult[]
    API-->>UP: { status, needs_human_review }

    alt needs_human_review: true
        UP->>U: ReviewAlert — campos faltantes
        U->>UP: Corrige campos manualmente
        UP->>API: PATCH /api/upload
        API->>FA: PATCH /ingest/pos/{file_id}/review
    end

    UP->>API: POST /api/audit { archetype, business_id, date }
    API->>FA: POST /orchestrator/run
    FA-->>API: { run_id, pipeline_status: "running" }
    UP->>U: Redirige a /dashboard?run_id=...

    loop Polling cada 2s
        UP->>API: GET /api/audit/status/{run_id}
        API->>FA: GET /orchestrator/status/{run_id}
        FA-->>API: { pipeline_status, current_node }
        UP->>U: PipelineStatusBar actualiza nodo activo
    end

    FA-->>DB: Persiste OrchestratorResult
    UP->>API: GET /api/audit/result/{run_id}
    FA-->>API: OrchestratorResult
    API-->>UP: { auditInsights, forensicReport, dormantMetrics, escalation }
    UP->>U: Renderiza AuditTable + ForensicSummary

    alt escalation.triggered: true
        UP->>U: Layer2Banner + nodo [L2] en PipelineStatusBar
        loop Polling Layer 2
            UP->>API: GET /api/audit/layer3/status/{layer2_run_id}
            UP->>U: Actualiza estado de [L2]
        end
    end
```

## Archivos relacionados de este nodo

- `design_flows.md` — estados de UI, flujos de control y errores
- `design_components.md` — componentes que implementan cada paso
