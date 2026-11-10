# Fase 3 — Dashboard, lecturas y navegación

Corte actual 19-oct-2026, rama `codex/quincena-5`, base `5ae4c86`;
avances de historial y documentación sin commit. Las tareas iniciales conservan
su terminación; se describen con su comportamiento vigente.

## Implementación realizada

- [x] Contratos frontend AuditInsight, OrchestratorResult, ForensicReport,
  AnomalyItem y estados; proyecciones de lectura en types/analysis.ts.
- [x] AuditTable con niveles, acciones y presentación de hallazgos.
- [x] AuditHeader, PipelineStatusBar y Layer2Banner: mensajes sencillos,
  riesgo desconocido separado y seguimiento avanzado sin enlace inexistente.
- [x] ForensicSummary, AnomalyCard y DormantMetricsList: disponibilidad
  diferenciada de listas vacías, desconocidas y faltantes.
- [x] useAuditPolling: lectura GET protegida por negocio/corrida; intervalo
  2000 ms mientras corre, estado avanzado por raíz autorizada; cleanup/abort.
  Retorna result, pipelineStatus, currentNode, layer3Status,
  layer3DraftStatus y error.
- [x] Dashboard, Salud y Reportes usan AuditReportView, con variantes de contenido.
- [x] Proxy de ejecución POST /api/audit y rutas legadas conservados; las vistas
  leen ahora /api/analyses/{business_id}/..., con Bearer y comprobación de dueño
  en FastAPI. Esta cobertura no se atribuye al backend legado completo.
- [x] Historial paginado, selección explícita/recordada/último terminado,
  navegación y recarga por pestaña/usuario/negocio; limpieza inmediata al salir
  o cambiar ámbito.
- [x] Tendencias reales: una corrida por fecha, indicadores diarios/unidades
  exactos, cero válido, huecos y datos insuficientes sin invención.
- [x] Mensajes separados de carga, ausencia, error, falta de datos y ausencia
  acreditada de anomalías. INC-050–053 conservadas; INC-055–057 resueltas.

## Verificación ya ejecutada del producto

- [x] Suite local: 452 aprobadas, 136 subpruebas, una opt-in omitida y dos avisos.
- [x] Edge: historial 11/11 y recorrido anterior 23/23, cero errores de página.
- [x] Presentación 16/16 y 8/8; fechas 11/11; build y tipos código 0.

[Informe, resultados exactos y límites](../../../docs/analysis_history_dashboard_20261019.md).
Son datos/Auth/proveedores simulados; esta revisión documental no repite pruebas.

## Trabajo separado pendiente

- [ ] Ensayo real de documentos, persistencia y respuesta del chat.
- [ ] Evaluación funcional/humana restante N15 y C02 por cuota externa.
- [x] Integración y pruebas locales del tutorial en Q6.
- [ ] Aceptación manual del tutorial, adaptación móvil integral y controles de producción.

[Diseño](design.md), [historial](analysis_history.md), [plan general](tasks.md).


[Versión anterior conservada](../../../docs/history/documentation_before_sync_20261019/.kiro/specs/mepia/tasks_phase3.md). Sus estados y cifras describen su fecha original.
