# MEPIA v4 — Documento Maestro de Diseño
*Documento vivo. Consolida todas las decisiones tomadas hasta ahora. Se actualiza cada vez que se cierra una discusión de diseño.*

**Documentos relacionados** (este archivo es el punto de entrada, no repite su contenido completo):
- `mepia_ground_truth_8_escenarios.md` — los 8 casos de ground truth formulados en detalle
- `kiro_prompt_ingesta_api_metricas.md` — prompt listo para pegar en Kiro (26 funciones nuevas de S3, ver decisión #16 para el conteo final confirmado)

---

## 0. Registro de decisiones (changelog)

| # | Decisión | Estado |
|---|---|---|
| 1 | `Contexto del día` sale del diseño, sin reemplazo | ✅ Cerrado |
| 2 | Fuente de datos primaria = API JSON a nivel línea (5 capas). PDF/OCR queda documentado como fallback, sin más inversión de tiempo | ✅ Cerrado |
| 3 | Catálogo de 31 métricas candidatas, clasificadas por tipo y aporte al LLM | ✅ Cerrado |
| 4 | Config de negocio: dos tipos — Tipo A (dato de catálogo, sin default posible) y Tipo B (umbral de materialidad, con default de arranque) | ✅ Cerrado |
| 5 | Prompt de Kiro corregido: de 16 a 25 funciones nuevas de S3 (se habían quedado 9 fuera sin razón declarada, incluyendo cancelaciones/reimpresiones por responsable, que resultó ser un requisito real, no opcional; "por responsable" terminó como dimensión estándar dentro de la misma función, no como funciones aparte). Nota: en la sesión de codificación se corrigió temporalmente a 24 por esta misma razón, pero al ejecutar el eval runner se encontró que `calc_commission_cost_ratio` faltaba del catálogo (`caso_04` la esperaba como métrica separada) — pasó a 25 de nuevo. Nota final (sesión Nivel 3, decisión #16): se agregó después `calc_contribution_margin_by_channel` (otra función nueva, no contemplada en ninguno de los conteos anteriores) — **el número correcto y final, confirmado por conteo directo del código, es 26** | ✅ Cerrado |
| 6 | Ground truth: unidad = **día completo**, método = mayoría sintético dirigido + un caso de revisión ciega. A futuro, el diario real de producción (`mepia_memory`/`audit_runs`) alimenta casos reales sin rediseño adicional | ✅ Cerrado |
| 7 | 8 escenarios de ground truth formulados **y con JSON real construido** (`tests/eval_test/`, nombres reales `mepia_ground_truth_caso_01...08_*.json`) | ✅ Cerrado (ver archivos aparte) |
| 8 | Paradigma de interfaz de salida: **híbrido** — pestañas tipo dashboard (Configuración, Métricas, Gráficas, otras) + pestaña "Chat IA" con semáforo + narrativa libre | ✅ Cerrado |
| 9 | Confirmado: 3 niveles de verdad para el ground truth, ninguno requiere rediseño adicional dado lo ya construido | ✅ Cerrado |
| 10 | Umbrales nuevos confirmados esta sesión: comisión delivery (8%), merma (5%/10%, con benchmark de industria) | ✅ Cerrado |
| 11 | "Por responsable" generalizado como dimensión estándar para cancelación, reimpresión, descuento y cortesía — no una excepción por función | ✅ Cerrado |
| — | Prioridad de hallazgos actualizada (ya no incluye "deducibilidad", heredado del diseño PLD anterior) — propuesta en `caso_08`: fraude > conciliación > zona gris > estadística | ✅ Cerrado — fraude va primero por severidad aunque sea de baja frecuencia, no por frecuencia |
| — | Revisión ciega del Caso 8 (segunda persona o segunda IA, sin ver `anomalias_inyectadas`) | ⏳ Pendiente — prompt listo en `caso_08_prompt_revision_ciega.md` |
| — | Campos exactos de Umbrales/Costos en la pantalla de Configuración | ⏳ Pendiente |
| 12 | Prompt de Kiro (Tareas 1–5) ejecutado sobre los specs (`.kiro/specs/mepia/`) y revisado contra este documento — sin discrepancias bloqueantes; corregido el conteo de funciones nuevas (25→24, ver decisión #5) | ✅ Cerrado — falta fase de codificación (ver sección 7) |
| 13 | Primer corrida del eval runner (Nivel 1, determinista): 69/95 métricas (72.6%) en bruto. Revisión contra los JSON de ground truth encontró que varias "categorías" del autodiagnóstico de Kiro estaban mal etiquetadas — ver detalle en sección 8. Tres decisiones de diseño resueltas: (a) `calc_commission_cost_ratio` se agrega como 25ª función de S3, separada de `calc_delivery_commission_cost` (mismo patrón que `calc_waste_analysis`/`calc_waste_cost`); necesita el subtotal del día completo (todos los canales) como denominador — mismo tipo de dependencia cruzada que ya tiene `calc_daily_break_even`; (b) base de `calc_avg_ticket` estandarizada a `subtotal` (no `total_net`) en los 8 casos de ground truth — el IVA es impuesto de traslado, no ingreso propio, mismo principio que ya aplicaba a los ratios "% de ventas"; (c) umbral de `staff_courtesy_ratio` grounded con benchmarks reales — RestaurantOwner.com (1-2% para comps+comidas de empleados+merma combinados) y SupplyClub (3-4% para "comps" con definición idéntica a la de MEPIA) — se fijó en 1% warning / 2% crítico, el extremo más estricto dado que la definición de MEPIA es más angosta que ambas fuentes | ✅ Cerrado |
| 14 | Revisión del código real (`agents/calc_engine.py`, `agents/api_ingest.py`, `tests/eval_test/eval_runner.py`, rama `feat/codificacion-session-s1b-s3-eval`) contra las decisiones de este documento. Corrección importante: el bug de `staff_courtesy_ratio` NO estaba en S3 (S3 ya usa `subtotal` correctamente) — estaba en el eval runner, que arma el dato de prueba usando `valor_cortesia` en vez de `subtotal`. También se confirmó que `by_responsable` para cortesía/descuento/cancelación YA está implementado en S3 — el eval runner simplemente nunca las invoca cuando `nivel="por_responsable"` (`return None # Not yet supported`). **Hallazgo nuevo**: `calc_reprint_rate` genuinamente no puede desagregarse por responsable — `ShiftAuditEvent.reprints` es un `int` (conteo), no una lista con responsable, a diferencia de `cancellations`. El ground truth (`caso_03`) ya trae `responsable` por evento de reimpresión — el dato existe desde la API, se decidió corregir el esquema de ingesta para preservarlo (`reprints: list[ReprintRecord]`, mismo patrón que `cancellations`). Umbral de `calc_labor_cost_ratio` grounded (30% warning / 35% crítico, ver sección 3). Lista completa de fixes pendientes en `docs/kiro_prompt_correccion_post_eval.md` | ✅ Cerrado — falta ejecutar el prompt de corrección |
| 15 | **Nivel 1 (S3, determinista) cerrado en 100% real (95/95 métricas, 8/8 casos)** — verificado corriendo el código directamente, no solo confiando en reportes: dos veces un reporte de "100%" resultó falso al correrlo (73.7% y 68.4% reales). Además de las causas ya documentadas, se recalibró `staff_courtesy_ratio` a un solo nivel (>5% crítico, sin warning) tras encontrar que el 1%/2% original mezclaba benchmarks **mensuales** con datos **diarios** — mucha más varianza natural a nivel día (fuente: Restaurant365/BreakingAC, "un swing de 2-3% diario es ruido normal, 5% es señal real"). También se corrigieron varios fixtures que tenían ruido de fondo no intencional (stock de `leche_entera`/`cafe_grano` por debajo del umbral en casos que no eran sobre inventario; una cortesía y una reimpresión incidentales que cruzaban umbral por casualidad de muestra chica) — mismo criterio en todos los casos: el dato se corrige cuando el "hallazgo" no es parte de la narrativa real del escenario, nunca se afloja el umbral para que el test pase. **Nivel 2 (S3→S4, con LLM real vía `--full-pipeline`) cerrado en 90.9% de recall (10/11), con los 7 "extra" restantes 100% explicados**: todos son consecuencia de que S4 tiene prohibido consolidar múltiples anomalías en un solo hallazgo (su propia Regla 5) mientras el ground truth espera algunos hallazgos ya consolidados (`insumo_critico_multi_senal`, `descuentos_cortesias_concentrados` con 2 señales) — esa consolidación es trabajo de N05/N11, que Nivel 2 no prueba (solo llega hasta S4). No es un defecto del pipeline, es el techo de alcance del harness tal como está diseñado hoy. En el camino se encontraron y corrigieron: (a) la tabla de matching del eval runner (`_FLAG_TO_METRIC_HINTS`) nunca coincidía con los nombres reales del campo `CalcResult.metric` (con prefijo `calc_` y en inglés cuando el campo real no tiene prefijo y a veces es español — `tasa_descuento`, `merma`) — todo el "recall" medido antes de este fix era ruido; (b) `calc_waste_analysis` crasheaba con `KeyError('unit')` cuando la tabla de transacciones traía un registro de referencia de precio (para `check_price_inflation`) en vez de una compra real — mismo problema de datos compartidos sin distinguir propósito que ya existía documentado para `check_price_inflation`; (c) el prompt de S4 no filtraba por `status` de S3 en absoluto — mandaba todo crudo y dejaba que el LLM re-juzgara, generando falsos positivos en 7/8 casos (`merma` en casi todos, incluyendo el "día limpio"); se resolvió separando el prompt en dos bloques físicos (accionable vs. referencia) en vez de una regla de texto más (una regla de texto no fue suficiente, confirmado en eval real); (d) un agregado del día puede diluir una señal individual real (ej. cortesía de un responsable en 9.63% escondida detrás de un agregado de 2.26% "ok") — se agregó un detector que revisa el desglose `by_responsable` embebido y promueve esos casos a "accionable" con una nota explícita, porque el campo `status` seguía diciendo "ok" y contradecía la regla de "nunca flaguear ok" si no se marcaba aparte | ✅ Cerrado |
| 16 | **Hallazgo crítico de arquitectura, Nivel 3a (N05 CEO Orchestrator)**: `run_calc_engine` — la función que usa producción real — solo sabía mapear las 5 métricas legacy (`cash_reconciliation`, `daily_break_even`, `operative_cost_margin`, `health_score`, `inventory_variance`) a una función. Ninguna de las **26 métricas nuevas** (confirmado por conteo real de `def calc_/check_` en `calc_engine.py` — el número final correcto, no 24 ni 25) tenía wiring en producción, y `GatekeeperAgent` tampoco las conocía para marcarlas "active". Todo Nivel 1/Nivel 2 se probó llamando las funciones de S3 directo, evitando este orquestador real — nunca se había probado si el punto de entrada de producción podía siquiera *llegar* a las funciones nuevas. Respuesta: no podía. Corregido: `GatekeeperAgent.METRICS` extendido a 30 (5 legacy + 25... **26** nuevas — ver nota de conteo arriba), con 9 métodos `_eval_` agrupados por requisito de datos compartido (no uno por métrica, mismo dato activa/desactiva varias a la vez) en vez de 26 checks individuales; `run_calc_engine` extendido con los 26 `elif` correspondientes. Verificado extremo a extremo contra los 8 casos: de "0 métricas nuevas llegan nunca a producción" a 17-21 de ~21-34 activas calculando bien por caso (el resto, incompletos legítimos: guardas de tamaño de muestra mínimo, o datos opcionales — `clock_records`, `recipes`, `business_fixed_costs` — que estos fixtures nunca tuvieron). Segundo hallazgo, más chico, del mismo Nivel 3a: probando con LLM real, `caso_06` escalaba a Layer 2 (`risk_level=high`) por un hallazgo de solo $130 MXN de cortesía concentrada en un responsable — desproporcionado frente al ground truth (que lo calificó "warning", no "critical"). Causa: no existía distinción entre cortesía normal (bebida gratis que el dueño ya autoriza para el staff) y cortesía anómala. Se agregó `business_courtesy_config` (Tipo B, tabla nueva, migración `007_business_courtesy_config.sql`) — permitido configurable por responsable/día (default: 1 ítem al precio del producto más caro del catálogo, o $100 MXN si no hay catálogo), con toggle explícito `activo` (boolean) para apagar la función completa si el negocio no la quiere. `calc_staff_courtesy_ratio` ahora evalúa el **excedente** sobre lo permitido, no la cortesía cruda. Verificado: `caso_06` pasa de `risk_level=high` (escalaba, mal) a `risk_level=medium` (no escala, coincide con lo esperado); Nivel 1 se mantiene en 100% tras el cambio. **Corrida final de Nivel 3a con ambos fixes juntos sobre los 8 casos: 8/8 coinciden en la decisión de escalar** (`caso_01/04/06/07` correctamente no escalan — 04/06/07 en `risk_level=medium`, 01 en `low`; `caso_02/03/05/08` correctamente escalan, todos en `risk_level=high`) | ✅ Cerrado |

---

## Cómo verificar el estado actual sin repetir esta sesión

```powershell
python tests/eval_test/eval_runner.py                  # Nivel 1 — debe dar 100.0% (95/95)
python tests/eval_test/eval_runner.py --full-pipeline   # Nivel 2 — debe dar 90.9% (10/11), 7 extra explicados
```

Si cualquiera de los dos da un número distinto, algo se revirtió — no asumir que el ground truth
o el código actuales coinciden con lo descrito arriba sin correrlo primero.

---

## 1. Cambios confirmados en la fuente de datos

- **`contexto del día` eliminado.** Generaba ruido, sin valor claro para el diseño final. No se reemplaza.
- **Nueva fuente**: API con JSON a nivel línea, 5 capas — Transacción/Ticket, Detalle de Producto, Formas de Pago, Operación/Caja/Auditoría, Inventarios/Costos Teóricos. Ver el detalle exacto de campos en `kiro_prompt_ingesta_api_metricas.md`, Tarea 2.
- Esto resuelve el problema de fondo señalado en el análisis original: *"el techo real es la confiabilidad del parseo"* — con datos de API estructurados, ese techo prácticamente desaparece.

---

## 2. Catálogo de métricas — resumen

31 métricas candidatas identificadas, distribuidas en 5 niveles de datos. Clasificación:

- **Passthrough** (sin cálculo): solo metadata de identidad (negocio, sucursal, periodo) y registros puntuales de excepción ya detectados por una regla determinista. Casi nada más debe llegar crudo al LLM — es la misma razón por la que el motor de Anthropic pasó de 21% a 95%: el ruido no es "mucha información", es información sin agregar.
- **Control** (validación de integridad, no insight de negocio): validación de IVA, cumplimiento de Cierre X/Z. Viven en `S2 Gatekeeper`, no en S3, y solo se exponen si fallan.
- **Calculado** (función determinista en S3): el resto — 26 funciones nuevas más las 3 que ya existían en el repo (`calc_contribution_margin`, `calc_waste_analysis`, `check_price_inflation`).

El listado completo, función por función, está en `kiro_prompt_ingesta_api_metricas.md`, Tarea 3 (ya corregido).

**Shortlist de mayor valor / menor ruido**: ticket promedio y volumen por turno, costo de comisión por canal delivery (el insight nuevo de mayor valor de todo el catálogo), tasa de descuento efectiva, top/bottom sellers + concentración Pareto, varianza de caja por turno, cancelación post-comanda, tasa de reimpresión, costo de merma en pesos, % de nómina sobre ventas, inflación de insumo clave.

---

## 3. Configuración de usuario — qué debe definir el negocio

### Tipo A — Dato de catálogo, sin el cual la métrica NO se calcula (sin default honesto posible)

| Métrica | Qué debe capturar el negocio |
|---|---|
| Consistencia de precio | Catálogo de precios esperados por producto |
| Costo de comisión por canal delivery | % de comisión por plataforma (UberEats/Rappi/DiDi) — varía por contrato, un default equivocado produce un margen *falso* |
| Costo de redención de lealtad | Valor/costo real del programa de lealtad |
| % de nómina sobre ventas | Costo por hora/salario del personal |

**Regla de diseño**: si el dato de config no está capturado, la métrica se queda `incomplete_data`/`dormant` — mismo patrón que ya usa `S2 Gatekeeper` para completitud de datos del día, extendido a completitud de config de negocio. Nunca inventar un default aquí.

### Tipo B — Umbral de materialidad (la métrica se calcula sola; el negocio solo ajusta la sensibilidad)

| Métrica | Default sugerido |
|---|---|
| Tasa de descuento | >10% del subtotal en un turno — fuente: RestaurantOwner.com |
| Cortesías de staff (`staff_courtesy_ratio`) | >5% (crítico único, sin warning intermedio) — recalibrado tras eval: el 1%/2% original venía de benchmarks **mensuales** (RestaurantOwner.com/SupplyClub) aplicados por error a datos **diarios**, con mucha más varianza natural. Fuente para el corte diario: Restaurant365/BreakingAC — "un swing de 2-3% diario en COGS es ruido normal, un salto de 5% significa que algo se rompió", más BarMagazine: "el % de comps importa cuando se desvía por responsable" — reforzando que la señal real vive en el nivel por-responsable, no en el agregado del día |
| Cancelaciones | >5% general; post-comanda: cualquier caso ya es flag |
| Reimpresión | >3% |
| Varianza de caja por turno | >1% o $100 MXN (flag), >3% o $500 MXN (crítico) |
| Merma vs. consumo teórico | >5% (warning), >10% (crítico) — alineado con benchmark de industria (4-10% promedio en restaurantes; 3.11% en servicio completo per estudio Univ. Arizona) |
| Días de inventario restante | <7 días (warning), <3 días (crítico) — ajustar por tipo de insumo |
| Inflación de insumo | >5% en 30 días |
| Costo de comisión delivery en pesos (`calc_delivery_commission_cost`) | Sin umbral — puramente informativo, el desglose por plataforma no dispara status |
| Ratio de comisión delivery sobre ventas (`calc_commission_cost_ratio`) | >8% de las ventas del día (base subtotal, todos los canales) |
| Costo de merma en pesos (`calc_waste_cost`) | Sin umbral MXN independiente — no existe benchmark de industria en pesos fijos (todo normaliza a %, confirmado por investigación). **Deriva su status del mismo umbral de `calc_waste_analysis`** (>5% warning, >10% crítico) aplicado al costo de compra del insumo en el período — mismo criterio, expresado en pesos |
| Margen de contribución por canal (`calc_contribution_margin_by_channel`) | Sin umbral propio — puramente informativo. La señal de alerta para erosión de margen por delivery ya la da `calc_commission_cost_ratio` (>8%); duplicarla aquí con un corte de puntos porcentuales inventado (solo 2 ejemplos, sin benchmark) era redundante y no grounded |
| % de nómina sobre ventas (`calc_labor_cost_ratio`) | >30% (warning), >35% (crítico) — fuente: consenso de múltiples fuentes de industria (25-35% rango sano típico; mediana de servicio completo 2026 en 36.5%, operadores rentables en 34.2% — National Restaurant Association 2026 vía WhippleWood) |
| Top/bottom sellers a mostrar | Top 10 |
| Validación de IVA | 16% (8% si aplica zona fronteriza — confirmar con contador) |

**⚠️ Base de cálculo estandarizada — encontrado en revisión ciega del Caso 8, y confirmado también para `avg_ticket` en la sesión del eval runner**: todo ratio "% de
ventas" (`discount_rate`, `staff_courtesy_ratio`, `commission_cost_ratio`, y cualquiera que se agregue después) usa
`subtotal` (antes de IVA, antes de cualquier descuento o cortesía de OTRAS órdenes) como
denominador. Nunca `total_net`. Razón: dos revisiones independientes del mismo día calcularon
`staff_courtesy_ratio` distinto (12.4% vs 9.63%) porque una usó `total_net` como base — que ya
trae restado el descuento de otras órdenes del mismo responsable, inflando artificialmente el
ratio de la segunda métrica cuando dos anomalías coinciden en la misma persona/periodo. Con
`subtotal` fijo como base, esa distorsión desaparece. **`avg_ticket` no es un ratio "% de ventas"
pero se decidió estandarizarlo también a `subtotal`**: el IVA es un impuesto de traslado que la
empresa retiene para el SAT, no ingreso propio, así que no debería inflar ningún indicador de
cuánto se vendió. Esto cambió el valor esperado de `avg_ticket` en los 8 casos de ground truth
(antes usaban `total_net` de facto, sin que la decisión estuviera documentada explícitamente).

Esta tabla mapea directo a las pestañas **"2. UMBRALES"** y **"3. COSTOS"** del prototipo de Figma — Umbrales = Tipo B, Costos = Tipo A. Coincidencia útil: el diseño de datos y el de UI ya están alineados sin haberlo planeado explícitamente.

---

## 4. Parseo OCR/PDF — veredicto

**No como ruta primaria. Sí como plan B, sin más inversión.**

`N01 POS PDF Input` ya está `✅ done` en el repo — no se pierde nada dejándolo así. La API elimina el techo de confiabilidad que tenía el PDF (ambigüedad de layout/OCR). Toda la inversión nueva de ingesta va al nodo de API. Documentar el PDF como *"ruta de respaldo si la integración API no está disponible."*

---

## 5. Ground truth — diseño acordado

### 5.1 Granularidad y método

| Opción evaluada | Ventaja principal | Desventaja principal |
|---|---|---|
| A — Un turno | Grano operativo natural, rápido | No sirve para métricas con baseline histórico |
| **B — Un día completo** ✅ elegida | Cubre casi todo nivel 1–4, coincide con el diseño original ("daily = unidad atómica") | Pierde algo de precisión turno-por-turno si hay varios turnos |
| C — Ventana de N días | Única forma de probar métricas con historial (inflación, Pareto estable) | Cara y lenta — se pospone, no bloquea el primer número de accuracy |
| **D — Sintético focalizado** ✅ método principal | Barato, preciso, controlas la respuesta correcta | No prueba el sistema completo por sí solo |
| **E — End-to-end real** ✅ método secundario, "un poco" | Única medida fiel del pipeline completo | Caro — se usa con revisión ciega en vez de con datos reales (que aún no existen) |

**Decisión**: unidad = día completo (B). Construcción = mayoría tipo D (anomalía inyectada y conocida de antemano), con el Escenario 8 usando revisión ciega (una persona construye, otra revisa sin ver la respuesta) como aproximación a E sin necesitar datos reales todavía. Cuando exista negocio piloto real, "el diario" de producción (`mepia_memory`/`audit_runs`, ya diseñado) se vuelve fuente natural de casos E reales — no requiere rediseño, el mecanismo ya existe.

### 5.2 Plantilla de caso

```
caso:
  id
  tipo: "dia_completo_sintetico"
  escenario_narrativo: "una o dos frases: qué pasa este día y por qué importa"
  anomalias_inyectadas:
    - donde, que, metrica_que_deberia_dispararse
  input: { ...json de 5 niveles }
  config_negocio: { comisiones, tarifas, umbrales usados }
  esperado_S3: [ {metric, value, status}, ... ]
  esperado_hallazgos: [ {flag, severidad, justificacion_corta}, ... ]
  esperado_narrativa: null   # pendiente — depende de la interfaz final, ver sección 6
  revisado_por: null
```

### 5.3 Los 8 escenarios

Formulados en detalle en `mepia_ground_truth_8_escenarios.md`: día limpio, faltante de caja, patrón de fraude operativo, erosión de margen por delivery, merma/inventario en riesgo, descuentos fuera de rango, ruidoso pero normal (frontera del umbral), multi-hallazgo (revisión ciega).

### 5.4 Hallazgo de diseño ya aplicado

`calc_cancellation_rate` y `calc_reprint_rate` deben calcularse **desagregadas por responsable** (cajero/mesero), no solo a nivel turno/día — si no, un patrón concentrado en una sola persona se diluye entre el resto del personal normal (surgió al construir el Escenario 3). Ya corregido en `kiro_prompt_ingesta_api_metricas.md`.

---

## 6. Paradigma de interfaz / salida

### 6.1 Opciones evaluadas

| Opción | A favor | En contra |
|---|---|---|
| 1 — Dashboard pasivo (recuadros por pestaña) | Rápido de escanear, ground truth barato | Desperdicia la síntesis multi-señal que ya construyeron (N05/N11/N13); rígido; no escala bien a 31 métricas |
| 2 — Chat con menú de botones | La síntesis multi-señal brilla; los 8 escenarios encajan sin cambios | Más fricción; texto largo = más riesgo de alucinación; ground truth de narrativa es caro |
| **3 — Híbrido** ✅ elegida | Lo mejor de ambos: semáforo casi gratis + narrativa solo cuando vale la pena | Requiere decidir bien la jerarquía de pantallas (ver 6.4) |

### 6.2 Decisión

Híbrido, confirmado. Interfaz imaginada: menú lateral (fijo o desplegable) con pestañas — Configuración, Métricas, Gráficas, otras por definir — más una pestaña **"Chat IA"** que contiene el semáforo, el área de prompt, y el área donde el LLM se explaya sobre lo que está pasando en el negocio.

### 6.3 Mapeo pestañas → tipo de ground truth

| Pestaña | Qué muestra | Ground truth necesario | ¿Requiere diseño nuevo? |
|---|---|---|---|
| Métricas / Gráficas | `CalcResult` de S3 tal cual | Número y `status` correctos | No — ya cubierto por PBT existentes |
| Chat IA — semáforo | Resumen visual de 3–5 `status` | Mismo `status` de arriba | No — mismo dato, sin trabajo extra |
| Chat IA — narrativa | Texto largo, síntesis multi-señal | Los 8 escenarios | No — tal como están |

### 6.4 Punto abierto — no bloquea nada, pero no olvidar

Si el semáforo vive *dentro* de la pestaña "Chat IA", el dueño tiene que entrar a esa pestaña para su primer vistazo del día — se pierde parcialmente la ventaja de "verlo en 2 segundos sin tocar nada". Puede estar bien si "Chat IA" termina siendo la pantalla de inicio de la app. Es una decisión de jerarquía de pantallas a resolver cuando diseñen las pantallas — no bloquea el trabajo de datos/ground truth de hoy.

---

## 7. Brecha actualizada hacia 90–95% accuracy

| # | Qué falta | Estado |
|---|---|---|
| 1 | Nodo de ingesta API | Spec listo y actualizado en `.kiro/specs/mepia/` (Tarea 2), falta codificar |
| 2 | Extender S3 con las 26 funciones nuevas (calc_commission_cost_ratio y calc_contribution_margin_by_channel agregadas tras revisión de caso_04 -- ver decisión #16 para el conteo final) | Spec listo y actualizado en `.kiro/specs/mepia/` (Tarea 3, corregida), falta codificar |
| 3 | Retirar `contexto del día` | Spec actualizado en `.kiro/specs/mepia/` (Tarea 1), falta codificar |
| 4 | Set de evaluación offline | Diseño de los 8 escenarios listo, falta construir el JSON real de cada uno |
| 5 | Capa de skills | Sigue sin diseñar — próximo tema pendiente después del eval set |
| 6 | Footer de procedencia/linaje en N14 | Sigue sin diseñar |
| 7 | Tabla de configuración Tipo A (comisiones, salarios, catálogo de precios) | Diseño listo (sección 3 de este documento + Tarea 4 del prompt Kiro) |

---

## 8. Primer eval runner (Nivel 1, determinista) — resultado y correcciones al autodiagnóstico

Primera corrida: 69/95 métricas (72.6%) en bruto, 3/8 casos pasando completos. Kiro reportó su
propio análisis de discrepancias atribuyendo la mayoría a "no es un fallo de S3, es el eval
runner". Revisado contra los JSON de ground truth directamente — algunas categorías estaban bien,
otras no:

| Categoría del reporte de Kiro | Veredicto tras verificar | Qué era en realidad |
|---|---|---|
| `staff_courtesy_ratio` "valor cercano" | ❌ Mal etiquetado | Bug real: sumaba `valor_cortesia` (con IVA) en vez de `subtotal` — 150.8/2470=6.11% vs 130/2470=5.26% esperado |
| `discount_rate` / `stock_days_remaining` "threshold no definido" | ❌ Mal etiquetado (2 de 4) | El umbral ya estaba documentado en este mismo doc (10%, y <7/<3 días) — el código simplemente no lo estaba leyendo |
| `staff_courtesy_ratio` / `waste_cost` "threshold no definido" | ✅ Correcto (2 de 4) | Sí eran decisiones pendientes de verdad — resueltas arriba (courtesy) y sigue pendiente (waste_cost en MXN) |
| `calc_commission_cost_ratio` "not mapped, no es función standalone" | ❌ Mal etiquetado | No era un problema de mapeo — la función nunca existió en el catálogo. Ground truth de `caso_04` la exige como métrica separada. Se agrega como 25ª función (ver decisión #13) |
| `calc_avg_ticket` "1.4% fuera de tolerancia" | ❌ Mal etiquetado | No era ruido de tolerancia — era una pregunta de diseño sin resolver (base subtotal vs total_net). Resuelto arriba: subtotal en los 8 casos |
| Per-responsable "not yet implemented in eval runner" | ⏳ Sin verificar | Creíble pero no comprobado — pedir a Kiro el `CalcResult.context` crudo de un caso antes de aceptarlo como solo-runner |
| Recetas/compras faltantes en el mock (`caso_04`/`caso_05`) | ✅ Probablemente correcto | Hueco de construcción del mock, no de S3 — sin verificar a fondo pero es plausible |

**No se acepta el "~85-90% legítimo" que propuso Kiro como el número honesto todavía.** Falta:
corregir el bug de `staff_courtesy_ratio`, cablear los 2 umbrales ya documentados, agregar
`calc_commission_cost_ratio`, aplicar la base `subtotal` a `avg_ticket`, verificar la afirmación
de per-responsable con evidencia, y arreglar los huecos de mock — recién después de eso el
siguiente número que salga del eval runner es el que cuenta.

---

## 9. Próximos pasos pendientes

1. ~~Construir el JSON real del Escenario 2 (faltante de caja)~~ — hecho.
2. Definir los campos exactos de las pestañas Umbrales/Costos en la pantalla de Configuración (ya tienen la lista de qué debe capturarse en la sección 3, falta el detalle de UI).
3. ~~Ejecutar el prompt de Kiro (Tareas 1–5) para generar/actualizar los specs~~ — hecho.
4. ~~Codificar lo que los specs describen~~ — hecho.
5. ~~Correr los 8 casos y registrar el primer número de accuracy honesto~~ — hecho. Nivel 1: 100% (95/95). Nivel 2 (S3→S4): 90.9% recall (10/11), techo real del harness (ver decisión #15).
6. **Nivel 3a cerrado: 8/8 coinciden en la decisión de escalar** (N05 CEO Orchestrator, `tests/eval_test/eval_runner_n05.py`, con LLM real). Sin diseñar todavía: Nivel 3b (N10→N14, Layer 3 — la consolidación de hallazgos que Nivel 2 no puede probar), y probar la integración N05→N06 (confirmado en el código que hoy es un stub, "N06 aún no está implementado" — solo se loguea el intent, hueco real pendiente de decisión).
7. Capa de skills y footer de procedencia en N14 — siguen sin diseñar, quedaron pendientes desde antes del eval set.
8. Pantalla de Configuración — le toca a otro miembro del equipo (frontend). Ya tiene un input nuevo que capturar: cortesía permitida por responsable (`business_courtesy_config` — activo/inactivo, items permitidos, monto por ítem opcional).
