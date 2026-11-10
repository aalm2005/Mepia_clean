# Diseño Frontend — MEPIA

Estado al 19-oct-2026: frontend integrado y consulta histórica verificada
localmente, sin commit. Base publicada `codex/quincena-5`, `5ae4c86`.
[Avances, evidencia y pendientes](../../../docs/estado_actual_mepia.md).

## Rutas

| Ruta | Raíz / propósito |
|---|---|
| `/login` | MepiaLogin, acceso común |
| `/` | Redirección a Dashboard |
| `/dashboard` | AuditReportView, indicadores y hallazgos |
| `/salud` | AuditReportView en variante health, indicadores y gráficas |
| `/reportes` | AuditReportView, hallazgos sin bloque de métricas |
| `/upload` | Documentos POS PDF y facturas XML/PDF; fecha y enfoque |
| `/onboarding` | Configuración avanzada opcional; Documentos crea defaults si faltan |
| `/chat` | ChatPanel, consulta fundamentada S3/N14 |

## Decisiones vigentes

- MepiaAuthProvider y MepiaShell comparten sesión, negocios propios y referencia
  de análisis. Dashboard es el inicio; bienvenida independiente retirada.
- Las tres vistas usan una corrida N05. Prioridad: `run_id` explícito,
  selección de la pestaña por usuario/negocio, último análisis terminado.
  Un enlace inválido muestra error, sin sustituirlo por otro análisis.
- Historial y resultados se recuperan mediante GET protegidos en Next/FastAPI;
  firma de sesión y propietario se verifican en servidor antes de auditorías.
  La guarda visual descarta respuestas tardías y limpia inmediatamente el ámbito.
- Consultar no ejecuta el motor ni consume IA. Crear un análisis desde Documentos
  es una operación distinta, con persistencia y posible consumo de proveedores.
- Las tarjetas y gráficas muestran los indicadores de la corrida, con significado
  y unidad reales. No se inventan ingresos, margen ni salud del negocio.
- Tendencias: una corrida terminada por fecha, métricas diarias comparables,
  orden cronológico y faltantes explícitos; nunca suma de corridas repetidas.
- Se distinguen carga, historial vacío, falta de datos, error y evaluación sin
  anomalías. El último mensaje exige evidencia forense del análisis cargado.
- La visita al chat conserva la selección visual; N15 mantiene fuentes por
  fecha/linaje S3 y no adopta automáticamente la corrida N05 como evidencia.

## Documentos de diseño

[Componentes](design_components.md), [árbol](design_components_tree.md),
[flujos](design_flows.md), [secuencia](design_flows_main.md),
[wireframes](design_wireframes.md), [onboarding](design_wireframes_onboarding.md),
[sistema visual](design_system.md), [historial](analysis_history.md).

## Límites y pendientes

El [tutorial guiado de Q6](design_flows.md#tutorial-guiado-en-quincena-6)
pasó las pruebas locales en escritorio y móvil. Siguen pendientes la aceptación
manual, el ensayo real con documentos y modelos, la evaluación humana de N15,
la adaptación móvil integral y los controles de producción.
Las consultas nuevas tienen autorización por recurso; no se atribuye esa cobertura
a todos los endpoints FastAPI legados. Reportes no acredita un visor integral N14.
La configuración generada de compilación se restauró tras las verificaciones.


[Versión anterior conservada](../../../docs/history/documentation_before_sync_20261019/.kiro/specs/mepia/design.md). Sus estados y cifras describen su fecha original.
