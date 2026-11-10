# MEPIA — Mapa de especificaciones

## Pipeline

```text
S1 (POS PDF, factura XML/PDF, API y entradas humanas)
 → S2 integridad → S3 cálculo → S4 diagnóstico → N05 síntesis
 → N06 paralelo: N09 gastos; N07/N08 omitidos en v1
 → N10 contexto → N11 consultoría → N13 revisión → N14 informe
N12 omitido en v1. N15 consulta S3/N14; las vistas consultan N05 guardado.
```

## Nodos y contratos

| Área | Especificaciones | Alcance |
|---|---|---|
| S1 | [Ingesta](s1_ingesta.md), [API](s1b_ingesta_api.md), [POS](n01_pos_pdf_input.md), [facturas](n02_facturas_input.md), [entradas humanas](n03_human_input_endpoints.md) | Importación de detalle POS adjunto S1B e idempotencia verificadas localmente; conectores externos separados |
| S2–S4 | [Integridad](s2_gatekeeper.md), [cálculo](s3_motor_calculo.md), [forense](s4_auditoria_ia.md) | Implementados |
| N05 | [Orquestador](n05_ceo_orchestrator.md) | Síntesis y persistencia |
| N06/N09 | [Paralelo](n06_orchestrator_adk.md), [gastos](n09_gastos.md) | Implementados; N07/N08 omitidos |
| N10/N11 | [Contexto](n10_context_builder.md), [consultoría](n11_consultor.md) | Implementados; N12 omitido |
| N13/N14 | [Revisión](n13_revisor.md), [informe](n14_informe_final.md) | Implementados |
| Layer 3 | [Grafo](layer3_graph.md), [ejecución](layer3_execution.md), [API](api_layer3.md) | Guardado y fallo terminal |
| N15 | [Consulta](n15_chat_consulta.md), [datos](n15_chat_consulta_datos.md), [herramientas](n15_chat_consulta_tools.md), [catálogo](n15_chat_consulta_catalogo.md), [saludos](n15_chat_consulta_saludos.md) | Pasos 1–4 aceptados; persistencia durante navegación interna y selección N05 exacta verificadas localmente; aceptación humana pendiente |
| Historial | [Consulta](analysis_history.md), [tendencias](analysis_history_trends.md), [contratos](analysis_history_contracts.md), [selección](analysis_history_ui.md) | Implementado y verificado localmente |
| Transversal | [Auth](_auth_strategy.md), [memoria](mem_memory_layer.md), [ajustes](n10_onboarding_identidad.md), [costos](cost_strategy.md), [evaluación](eval_offline.md) | Permisos del backend legado y producción pendientes |
| Datos | [Glosario](_glossary.md), [esquema](db_schema.md), [contrato SQL](db_schema_pipeline_contract.md) | Sin migración por historial |
| Interfaz | [Diseño](design.md), [componentes](design_components.md), [flujos](design_flows.md), [wireframes](design_wireframes.md), [sistema visual](design_system.md) | Tutorial Q6 verificado localmente; adaptación móvil integral pendiente |
| Pruebas locales | [Infraestructura y demo](local_testing.md) | Simulaciones verificadas; aceptación manual/real pendiente |
| Plan | [Tareas](tasks.md), [frontend](tasks_phase3.md), [backend](tasks_backend.md) | Distingue implementación de validación real |

## Carga de contexto

Leer `_index.md`, `_glossary.md`, el nodo específico y su código relacionado.
Para continuidad N15 cumplir primero `AGENTS.md` y su lectura obligatoria completa.
El [estado actual](../../../docs/estado_actual_mepia.md) y la
[bitácora fuente de verdad](../../../docs/chatbot_corrections.md) separan el corte
publicado, los avances locales y los pendientes. Un nodo implementado no certifica
un despliegue ni una evaluación con servicios reales.


[Versión anterior conservada](../../../docs/history/documentation_before_sync_20261019/.kiro/specs/mepia/_index.md). Sus estados y cifras describen su fecha original.

[Documento maestro Q6–Q7](../../../docs/documento_maestro_mepia_v1_6.md) · [Verificación de publicación](../../../docs/cierre_q6_q7_20261110.md).
