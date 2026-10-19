# Correcciones del ensayo de MEPIA

**Correcciones del ensayo — 15-oct-2026:** INC-051/052/053 resueltas
localmente. Fecha inferida desde ventas o selección compatible; selección del
análisis conservada en el menú para la misma sesión/negocio; N05 guarda el
resultado completo. Históricos recuperados solo por su S3 explícito compatible,
con estado S2 desconocido cuando no se conservó. Regresión: **226 pruebas y
41 subpruebas**, dos advertencias, 58.42 s, código 0. Edge: **23/23 controles**,
cero errores; fechas 11/11 y presentación 16/16; tipos código 0.
Lectura principal por API local: HTTP 200, cuatro métricas recuperadas de la
corrida de enero; cero escrituras externas y cero llamadas del agente a modelos.
Servidor local actualizado. **53 incidencias: 50 resueltas, dos mitigadas,
una pendiente externa y cero abiertas.** Ensayo real del 14-oct y revisión humana
del Paso 5 siguen pendientes. Rama `codex/chatbot-q4`, HEAD `f9cfddc84721a9ea32f8e56ba804f0ed8dc77f09`;
sin commit/push ni despliegue. Sigue ejecutar una vez el ensayo con fecha 14-oct.


## Cambios

- INC-051: fecha inicialmente vacía; las fechas del lote se reciben directamente,
  sin leer estado React pendiente. Un único día POS manda sobre compras de otras
  fechas. Una selección contradictoria o POS de varios días detiene el análisis;
  sin día inferible debe elegirse. La ocupación cubre carga/análisis y evita doble clic.
- INC-052: selección de corrida en memoria por usuario/negocio. Menú y logo
  conservan run_id para Dashboard/Salud/Reportes; cambiar negocio o salir limpia
  la selección. Recargar el enlace conserva el análisis; no se añade historial
  durable ni se deshace la limpieza de INC-036.
- INC-053: N05 guarda exactamente el resultado devuelto y conserva los campos
  planos usados por lectores anteriores. Incluye cálculos decimales, S2 y linaje.
  Si guardar falla, error fijo/503. El GET histórico recupera S3 únicamente por
  raíz explícita y compatible, sin recalcular ni escribir. Ausencia de estado S2
  queda desconocida. La pantalla distingue falta de análisis, desconocido,
  indicadores sin datos y revisión humana; solo un estado completo conocido
  sin pendientes permite afirmar activación total.

## Verificaciones reales de esta corrección

- Python dirigido: 12 aprobadas, dos advertencias, 11.14 s, código 0.
- Regresión: 226 aprobadas, 41 subpruebas, dos advertencias FastAPI, 58.42 s, código 0.
- Node: fechas 11/11 y presentación 16/16; tipos código 0.
- Edge: 23/23 controles, cero errores de página, sin servicios externos.
  Fecha contradictoria no solicita análisis; fecha inferida solicita 2026-10-14;
  caja textual 0.00 aparece como cero, se muestra el dato faltante, se navega al
  chat y regresa/recarga sin otro análisis. Se conservan controles de aislamiento.
- Servidor completo local reiniciado. OpenAPI 200; GET de la corrida histórica
  recupera cuatro cálculos y marca estado S2 desconocido. Esta consulta usa
  MEPIA principal en solo lectura, con cero escrituras y cero llamadas del agente
  a modelos. No se modificaron auditorías, conteos, archivos, ajustes ni SQL real.
- Un primer helper Node falló por objetivo de compilación ES5; corregido el arnés
  a ES2020. El primer Edge se detuvo al buscar texto exacto 0 sin la unidad MXN;
  captura inspeccionada muestra 0 MXN correcto. Selector corregido y segundo
  recorrido guardado aparte; el primero se conserva fallido. La comprobación
  de whitespace con autocrlf desactivado produjo falsos
  avisos sobre CRLF; el diff normal de Git terminó con código 0. Se preservan logs
  de ejecución; no se presenta el fallo como una prueba de producto aprobada.

## Archivos de producto y pruebas

- `utils/audit-date.ts`, `components/upload/UploadForm.tsx`.
- `components/auth/MepiaAuthProvider.tsx`, `components/layout/MepiaShell.tsx`,
  `hooks/useAuditPolling.ts`.
- `agents/ceo_orchestrator.py`, `api/audit_results.py`, `api/main.py`.
- `types/audit.ts`, `components/dashboard/AuditReportView.tsx`,
  `components/dashboard/DormantMetricsList.tsx`.
- `tests/test_dashboard_results.py`, `tests/audit_date.cjs`, `tests/chat_step5_e2e.cjs`.

Se sincronizan bitácoras, diseño maestro, estado, README, guía del video, glosario,
contrato N05, componentes y tareas relacionadas. El JSON asociado contiene las
rutas exactas y huellas. [Evidencia](evaluations/dashboard_demo_fix_20261015.json).

## Siguiente acción

En Documentos, usar los mismos PDF/XML y dejar la fecha vacía o elegir 14/10/2026;
analizar una sola vez. Verificar fecha y diferencia de caja esperada 0 MXN.
Después volver desde Chat IA y preguntar por la conciliación para ese mismo día.
Todavía no se ha validado esta corrida real del 14-oct ni una respuesta nueva de
los proveedores. No se reabren Pasos 1–4. Tutorial, móvil y controles de producción
mantienen su alcance; permisos de recursos legados de INC-023 siguen pendientes.
No hubo commit, push ni despliegue.
