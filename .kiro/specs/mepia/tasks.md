# Plan de Implementación — MEPIA

## Visión general

Implementación incremental de MEPIA. Las fases 1–3 (frontend) están completas.
Las fases 4–18 tienen implementación y sus tareas registradas como realizadas;
esto no certifica producción ni la integración completa con cada fuente real.
El [estado actual](../../../docs/estado_actual_mepia.md) separa código, pruebas y pendientes.

## Fases

| Archivo | Contenido | Estado |
|---------|-----------|--------|
| `tasks_phase1.md` | Design system + componentes base + rutas de onboarding | ✅ Completo |
| `tasks_phase2.md` | Ruta `/upload`: defaults automáticos, selector, dropzones, revisión y formulario; gate retirado | Implementado; ensayo integral con archivos nuevos pendiente |
| `tasks_phase3.md` | Ruta `/dashboard` + API routes + integración end-to-end | ✅ Completo |
| `tasks_backend.md` | S1→S2→S3→S4→N05→N06→N09→Layer3→PBT | Implementado en desarrollo; publicación y validación integral separadas |
| `n15_chat_consulta.md` | Chat Pasos 1–5 | 1–4 aceptados; integración implementada, validación funcional del Paso 5 pendiente |
| `design.md` | Experiencia general | Tutorial guiado pendiente; adaptación móvil parcial; simplificación del selector pendiente |

## Integración de entorno — 15-oct-2026

- [x] Registrar inventario posterior de principal y contraste estático sin tablas/columnas faltantes.
- [x] Registrar configuración privada de interfaz/backend hacia principal con respaldo previo.
- [x] INC-046: esquema, RPC, políticas y preservación verificados en principal.
- [x] Procesos completos, login y aislamiento verificados en principal.
- [x] INC-047: claves API antiguas desactivadas y firma anterior revocada con autorización; rechazo 401 y conexión moderna verificados.
- [x] Recuperar evidencia S3 existente: cuatro métricas; sin N14 enlazado.
- [ ] Ensayar análisis nuevo persistido y consulta posterior del chat en ese destino.
- [ ] Ensayar documentos del 14-oct con los proveedores configurados para la grabación.
- [x] INC-048: fallo de guardado N14 propagado y completado solo tras guardar.
- [x] INC-049: seguimiento por ID padre y ruta real corregidos; HTTP probado.
- [x] INC-050: presentación admite decimales textuales del motor; 16/16 controles y tipos código 0.
- [x] PDF/XML de demo y oráculo de conciliación local preparados.
- [x] Conteo ficticio autorizado, insertado una vez y verificado por lectura.
- [x] INC-051: fecha coherente con ventas y validación de discrepancias.
- [x] INC-052: menú conserva corrida dentro de sesión/negocio.
- [x] INC-053: resultado completo persistido y recuperación histórica por S3 explícito.
- [ ] Completar ensayo real del 14-oct con documentos, OpenAI y Gemini.

La conexión por `audit_results` ya está implementada; estos controles no
reabren los Pasos 1–4 aceptados. [Detalle](../../../docs/database_unification.md).

## Archivos de diseño de referencia

- `design_system.md` — tokens Tailwind y paleta azul integrada
- `design_components.md` — props y contratos de componentes
- `design_components_tree.md` — árbol completo por ruta
- `design_wireframes.md` — layouts de dashboard y upload
- `design_wireframes_onboarding.md` — wireframe de onboarding (4 pasos)
- `design_flows.md` — estados de UI y flujos de control
- `design_flows_main.md` — diagrama de secuencia completo
- `_glossary.md` — contratos de datos (AuditInsight, OrchestratorResult, etc.)

## Specs de referencia por fase

| Fase | Spec |
|------|------|
| 4 — S1 Ingesta | `n01_pos_pdf_input.md`, `n02_facturas_input.md`, `n03_human_input_endpoints.md`, `s1_ingesta.md` |
| 5 — S2 Gatekeeper | `s2_gatekeeper.md` |
| 6 — S3 Motor Cálculo | `s3_motor_calculo.md` |
| 7 — S4 Forensic CFO | `s4_auditoria_ia.md` |
| 8 — N05 CEO Orchestrator | `n05_ceo_orchestrator.md` |
| 9 — N06 Layer 2 | `n06_orchestrator_adk.md` |
| 10 — N09 Gastos | `n09_gastos.md` |
| 11 — MemoryService | `mem_memory_layer.md` |
| 12–16 — Layer 3 | `n10_context_builder.md`, `n11_consultor.md`, `n13_revisor.md`, `n14_informe_final.md`, `layer3_graph.md`, `api_layer3.md` |
| 17 — PBT | Todos los specs con sección "Correctness Properties" |
| 18 — Integración | `design_flows_main.md` |
