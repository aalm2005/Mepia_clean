# Consulta de análisis guardados

Corte 19-oct-2026: categoría C solicitada, implementada y verificada localmente;
sin commit. No reabre los Pasos 1–4 ni INC-050–053. INC-055–057 resueltas.
[Evidencia del producto](../../../docs/analysis_history_dashboard_20261019.md).

## Lecturas protegidas

Router `api/analysis_history.py` registrado en api.main y api.chat_app.
Todos los GET `/business/{business_id}/analyses` verifican Bearer mediante
AuthService y `businesses.owner_id` antes de consultar auditorías.

| GET | Contrato |
|---|---|
| base `?page=0` | N05 propios, 25 por página; created_at/id descendente; next_page explícito |
| `/latest` | Último N05 terminado por orden de guardado, no por fecha analizada |
| `/{run_id}` | Resultado guardado de esa corrida/negocio; recuperación S3 explícita compatible de INC-053 |
| `/{run_id}/trends` | Indicadores diarios comparables hasta la fecha seleccionada |
| `/{run_id}/layer3` | Estado avanzado desde el padre guardado de ese N05 y del mismo negocio |

Latest admite completed/partial/escalated con node_status exitoso o legacy null;
excluye failed/running/unknown. Pagina 100 candidatos hasta 10 000; al alcanzar
el límite sin resultado devuelve limited=true y pide elegir manualmente, sin
afirmar historial vacío. El listado paginado es independiente.

401 sin DB; 403 ambiguo para negocio ajeno/inexistente/sin dueño; 404 ambiguo
para corrida ausente/ajena; 503 saneado ante DB/permisos. Next valida sesión,
identificadores y Bearer, reenvía la credencial, usa respuestas privadas sin
caché compartida y timeout de 20 segundos. Ninguna consulta ejecuta ingesta,
motor, modelos ni escrituras.

La lectura preserva restauración S3 por linaje exacto, no proximidad temporal.
El seguimiento avanzado conserva fallos de guardado N14 y sus límites previos.
No se agregan tablas, migraciones ni estados nuevos producidos por el motor.
unknown es únicamente lectura histórica sin evidencia de terminación.

## Especificaciones relacionadas

- [Selección, navegación y mensajes](analysis_history_ui.md).
- [Tendencias, unidades, repetidos y faltantes](analysis_history_trends.md).
- [Contratos de lectura](analysis_history_contracts.md).
- [Diseño común](design.md), [N05](n05_ceo_orchestrator.md),
  [datos N15](n15_chat_consulta_datos.md), [fallo N14](layer3_execution.md).

Pruebas simuladas cubren acceso ajeno/sesión revocada, vacío/paginación,
selección/recarga/chat, cambio de negocio, varios análisis por fecha, cero,
unidades, datos insuficientes y disponibilidad forense. No certifican DB/modelos
reales, revisión humana N15 ni producción. La autorización por recurso del
backend legado sigue siendo trabajo separado.


[Versión anterior conservada](../../../docs/history/documentation_before_sync_20261019/.kiro/specs/mepia/analysis_history.md). Sus estados y cifras describen su fecha original.
