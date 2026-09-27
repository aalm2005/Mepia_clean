# N15 — Catalogo financiero y prohibicion de calculo

**Capa:** Aplicacion | **Anterior:** S3 | **Consumidor:** nodo conversacional
**Archivos relacionados:** `n15_chat_consulta.md`,
`n15_chat_consulta_tools.md`, `agents/chat_metric_catalog.py`

## Alcance

El chatbot explica exclusivamente metricas del motor determinista y conceptos
necesarios para comprenderlas. El catalogo cubre las 31 metricas despachadas por
`GatekeeperAgent.METRICS` y cuatro calculos auxiliares reales del motor:
`contribution_margin`, `waste_analysis`, `burn_rate` y `price_inflation`.
No es un glosario financiero general.

Cada `MetricDefinition` declara identificador, nombre visible, definicion,
interpretacion, explicacion conceptual de la formula, entradas, unidades, alias,
nombres reales de `CalcResult`, conceptos relacionados, limitaciones,
disponibilidad y `calculation_owner="deterministic_engine"`.

## Regla absoluta

`calculation_allowed=false`. N15 puede recuperar resultados existentes,
explicarlos y parafrasearlos. No puede calcular, recalcular, sumar, promediar,
agregar, derivar comparaciones numericas, proyectar ni simular. Una formula del
catalogo es texto educativo, nunca una interfaz ejecutable. Si el motor no emitio
un resultado, el chatbot debe declararlo ausente y no reconstruirlo a partir de
otros valores.

Toda solicitud de calculo produce `status="not_allowed"` y
`missing_data=["calculation_not_allowed"]`. La negativa no incluye evidencia ni
un valor calculado.

## Casos historicos que deben explicarse con precision

- `operative_cost_margin` es un promedio diario de costos, no un margen
  porcentual, pese a su identificador legado.
- `health_score` es el promedio monetario de margenes de contribucion
  calculables; no es una puntuacion compuesta de salud.
- `inventory_variance` puede emitir varias salidas con prefijo
  `inventory_variance_`; no es una unica variacion global.

## Acceptance Criteria

- WHEN cambia `GatekeeperAgent.METRICS` THEN una prueba de igualdad exacta falla
  hasta actualizar y revisar el catalogo.
- WHEN se solicita una metrica por identificador, alias o nombre real de salida
  THEN la coincidencia es normalizada exacta, nunca difusa.
- WHEN se consulta un concepto ajeno al motor THEN retorna `not_found`.
- WHEN se entrega cualquier `ChatToolResult` THEN declara
  `knowledge_scope="engine_metric_domain"` y `calculation_allowed=false`.
- WHEN se explica una formula THEN se identifica como explicacion solamente.

## Fuente de verdad

La fuente implementada es `agents/chat_metric_catalog.py`, contrastada con
`agents/gatekeeper.py` y `agents/calc_engine.py`. No usa RAG, Supabase ni LLM.
