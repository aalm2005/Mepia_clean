# Diseño Frontend — Flujos de Interacción

**Acceso e inicio — 15-oct-2026, validado localmente; sin commit:** sesión por pestaña (recargar conserva; cerrar/abrir pide login), Dashboard como inicio y bienvenida eliminada. API con Bearer y verificación de servidor; cookies antiguas no autentican. [Contrato, pruebas y límites](../../../docs/mepia_access_navigation.md). INC-042 resuelta localmente: Edge 24/24, cero errores; build y tipos código 0. 42 incidencias: 39 resueltas, dos mitigadas y una pendiente externa. Los informes fechados anteriores no validan este cambio.

**Estado documental al 15-oct-2026:** consultar [flujo, avance y pendientes](../../../docs/estado_actual_mepia.md). La sesión identifica y carga el negocio autorizado automáticamente; el selector con un solo negocio aún puede simplificarse. Tutorial guiado pendiente y adaptación móvil parcial. Los registros y conteos fechados siguientes conservan su alcance histórico; la publicación de código no equivale a despliegue.

**Automatización del 14-oct-2026 (histórica, anterior al acceso por pestaña):** ejecutor por capas implementado.
Final local: 43 capas por caso aprobadas, cinco pendientes, cero fallidas,
código 0; no equivale a 43 casos funcionales completos. Regresión 154 pruebas
y 41 subpruebas, dos advertencias, 22.73 s, código 0. Edge sintético: 18
controles, cero errores, código 0; carga 70 POST simulados. Gemini real con
datos/Auth en memoria: siete de ocho casos con controles mecánicos aprobados,
C02 detenido por HTTP 429; 17/18 intentos, código 1, sin reintentos ni juez.
Ocho respuestas validadas para revisión humana, aún sin calificaciones.
INC-040 resuelta localmente, 035 actualizada/resuelta, 041 pendiente externo.
41 incidencias: 38 resueltas, dos mitigadas, una pendiente externa, cero
abiertas. Supabase/cuentas/producción y preview del usuario sin cambios;
sin commit/push. Los avisos siguientes conservan sus registros históricos;
el diseño v1 y su plantilla permanecen intactos, anteriores al ejecutor.
Sigue disponibilidad/C02, revisión humana y ampliar solo lo pendiente.
Ver [ejecutor, resultados y revisión](../../../docs/chatbot_step5_automation.md).

**Ajuste de lenguaje — 14-oct-2026 (registro anterior a la automatización):** el usuario pidió respuestas
comprensibles sin conocimientos financieros y para diversos niveles de lectura.
Se ajustó la guía común de composición: palabras cotidianas, frases cortas,
tono respetuoso, respuesta directa y breve por defecto; detalles técnicos según
la pregunta. Una definición sencilla omite fórmulas, insumos y alias no pedidos,
conservando condiciones esenciales. Redacción libre, fuentes, cifras/unidades,
alertas y prohibición de calcular intactas. Backend local reiniciado, código 0.
115 pruebas y 41 subpruebas aprobadas, dos advertencias, 11.09 s, código 0;
proveedores simulados. El usuario repitió ticket promedio en una conversación
nueva y confirmó «Sí, ahora es clara»; Next registra POST 200. Es confirmación
humana de legibilidad en esa consulta, no un juicio semántico independiente ni
una medida universal de comprensión. INC-039 resuelta en este alcance;
INC-035 actualizada por atasco del ejecutor en sandbox y ejecución posterior
aprobada fuera de él. 39 incidencias: 37 resueltas, dos mitigadas (023/031),
cero abiertas. Un archivo de producto modificado: `agents/chat_response.py`.
Sin preguntas del agente al modelo, SQL, datos/usuarios, producción, commit
ni push. Evidencias anteriores conservadas; general/build/E2E no repetidos.
Evidencia `docs/evaluations/chatbot_step5_plain_language_20261014.json`.

**Referenciado desde:** `design.md`

## Índice de flujos

| Archivo | Flujo |
|---------|-------|
| `design_flows_main.md` | Diagrama de secuencia completo: onboarding → ingesta → análisis → pantalla |
| Este archivo | Estados de UI, flujos de control, errores, V1 auth |

## Estados de la UI por `pipeline_status`

| `pipeline_status` | PipelineStatusBar | AuditTable | Banner |
|-------------------|-------------------|------------|--------|
| `running` | Animación en nodo activo | Skeleton loader | — |
| `completed` | Todos verdes | Datos reales | Según `risk_level` |
| `partial` | Verdes + grises (dormant) | Datos parciales | Info: métricas faltantes |
| `escalated` | Verdes + nodo `[L2]` activo | Datos reales + nota escalación | `Layer2Banner` ámbar |
| `failed` | Rojo en nodo fallido | Error state | Error crítico |

## Flujo de onboarding

```
/login → sesión válida → carga automática del negocio propio → menú MEPIA → /upload
  │
  └─ OnboardingGate: GET /business/{id}/onboarding/status
        ├── onboarding_complete: true → UploadForm visible
        └── onboarding_complete: false
              → OnboardingRequiredBanner → CTA "Configurar negocio →"
              → /onboarding → 4 pasos → POST /business/{id}/onboarding
              → HTTP 201 → redirige a /upload → UploadForm visible
```

## Flujo de Layer 2 (escalation)

```
OrchestratorResult.escalation.triggered: true
  ├── Layer2Banner aparece (ámbar, colapsable)
  ├── PipelineStatusBar agrega nodo [L2] con spinner
  └── Polling sobre layer2_run_id
        ├── "running"   → spinner en [L2]
        ├── "completed" → checkmark verde + "Ver análisis profundo →"
        └── "failed"    → rojo en [L2] + mensaje de error
```

## Flujo de `risk_level` → UI

```
ForensicReport.risk_level
  ├── "high"   → Banner rojo fijo + filas critical + AnomalyCards
  ├── "medium" → Banner ámbar colapsable + filas warning
  └── "low"    → Sin banner, solo métricas dormant
```

## Flujo de `needs_human_review`

```
POST /ingest/pos → POSIngestResult
  ├── false → continuar al trigger del pipeline
  └── true  → ReviewAlert con missing_fields
               → PATCH /ingest/pos/{file_id}/review
               → 200 → continuar | error → mensaje específico
```

## Manejo de errores de API

| HTTP | Mensaje en UI | Componente |
|------|---------------|------------|
| 409 | "Faltan datos para iniciar el análisis." | Banner warning |
| 412 | "Completa el onboarding antes de auditar." | `OnboardingRequiredBanner` |
| 503 | "El servicio no está disponible." | Banner error |
| 422 | Mensaje del campo inválido | Inline en formulario |

## Flujos legados del pipeline — incorporación de permisos pendiente

La interfaz usa el negocio seleccionado desde los negocios propios de la sesión;
no utiliza `NEXT_PUBLIC_BUSINESS_ID`. Los proxies Next requieren sesión verificada
en servidor. Permisos por recurso y acceso directo de FastAPI legado siguen
pendientes como control de publicación, separados del login de la interfaz.

## Archivos relacionados de este nodo

- `design_flows_main.md` — diagrama de secuencia completo
- `design_components.md` — componentes que implementan cada estado
- `design_wireframes.md` — layouts donde ocurren las transiciones

## Chat IA — Paso 5
`/login` autentica antes de entrar a MEPIA. Menú común abre `/chat`, que reutiliza
sesión y negocio de MepiaAuthProvider desde GET /me/businesses.
No usa NEXT_PUBLIC_BUSINESS_ID como autorización. Next.js reenvía Bearer;
FastAPI verifica sesión/propiedad antes de grounding o modelo. GET/DELETE de
historial revalidan permisos. La interfaz maneja 401/403/404/409/422/429/503,
conserva fuentes/fecha/linaje, no calcula y limpia datos al cambiar usuario,
negocio o fecha. E2E local previo 8/8 con simulaciones. Acceso real posterior
en `MEPIA - PRUEBAS`: ES256/JWKS y migración 010, Auth/RLS/permisos/historial
29/29 con proveedor simulado; no equivale a navegador/modelo reales.
Producción separada. Negocios con dueño NULL deniegan acceso hasta verificarlo;
el negocio de pruebas ya está vinculado a la cuenta confirmada por el usuario.
Login/negocio confirmados por el usuario en Edge/Chrome; Auth registra login
reciente y Next listado 200. Contraseña solo introducida por el usuario.
Formulario real preparado en `127.0.0.1:3016/chat`; backend exclusivo
`api.chat_app` en `127.0.0.1:8016` solo publica rutas protegidas del chat/listado.
No necesita claves del pipeline para login. El 14-oct el usuario guardó la clave
Gemini en el servidor privado y se reinició exclusivamente Chat IA. Pregunta
conceptual confirmada con fuentes del catálogo y POST 200; accesos anónimos
continúan en 401. Los 503 previos por falta de clave se conservan como históricos.
Errores `AuthRetryableFetchError` muestran conexión fallida, sin pedir revisar
credenciales ni imprimir excepción privada. SDK/fetch simulado 3/3, tipos código 0.
Fallo inicial de navegador integrado no reproducido; INC-031 mitigada, no se
modifican sus protecciones. La confirmación conceptual no cubre todos los
recorridos reales de métricas/historial; se ampliarán como trabajo posterior.
Fecha 2099 visible comprobada por lectura como fixture histórico conservado
de MEPIA - PRUEBAS. Evidencia de conexión:
`docs/evaluations/chatbot_step5_gemini_activation_confirmation_20261014.json`.

### Flujo común vigente
Acceso a home/dashboard/upload/onboarding/chat sin sesión → `/login?next=...`.
Cuenta verificada → navegación completa a destino interno → menú MEPIA.
Icono Chat IA → conversación integrada; sin formulario propio de login.
Nueva conversación/cambio de usuario o negocio descartan la vista anterior;
fecha cambia contexto y cancela peticiones. Salida borra sesión local y navega
una vez al login; volver a enlace privado exige sesión. Menú lateral desktop,
menú desplegable móvil, compositor inferior y fuentes/estado conservados.
Acceso común inicial 13/13; frontend combinado del 14-oct 15/15 E2E simulado,
presentación 12/12, cero errores, build final código 0. Cambio de contexto
cancela peticiones/limpia análisis; resultado debe coincidir con negocio y run_id
antes de mostrarse. Salud/Reportes y bienvenida usan sesión/menú existentes. El 13-oct-2026 el usuario
confirmó ingreso general con su cuenta propia y Chat IA desde el menú sin otro
login; confirmación del usuario, sin inspección independiente del navegador.
Gemini configurado y una definición real confirmada clara por el usuario el
14-oct; ampliar métricas, lenguaje e historial según el
[plan del Paso 5](../../../docs/chatbot_step5_test_plan.md): 48 casos diseñados,
matriz local ejecutada (43 capas aprobadas), ocho respuestas reales validadas
guardadas y C02 pendiente externo por cuota. Revisar comprensión con dos lectores
y ampliar solo lo pendiente; publicación y OpenAI separados.
