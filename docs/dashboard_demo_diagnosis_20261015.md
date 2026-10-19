# Diagnóstico del Dashboard durante el ensayo

**Registro inicial, anterior a la corrección:** las incidencias abiertas que se
describen abajo quedaron resueltas localmente en el
[seguimiento del ensayo](dashboard_demo_fix_20261015.md). Se conserva la evidencia
original; la corrida real del 14-oct todavía requiere verificación del usuario.

Diagnóstico del 15-oct-2026, rama `codex/chatbot-q4`, HEAD
`f9cfddc84721a9ea32f8e56ba804f0ed8dc77f09`, sin commit/push.
Categoría C: integración y robustez de la demostración; no reabre los Pasos 1–4.
No se cambió código de producto ni se ejecutó un análisis nuevo.

## Causa de las cifras de las capturas

La consulta de solo lectura a MEPIA principal encontró una corrida para
**2024-01-15** que coincide con los cuatro resultados mostrados. Los documentos
de demostración sí dejaron ventas y compra para **2026-10-14**, pero en la
consulta no existe una auditoría para esta última fecha.

| Concepto | Datos del 2024-01-15 | Demostración 2026-10-14 |
|---|---:|---:|
| Fondo inicial | 1,500.00 | 200.00 |
| Ventas en efectivo | 4,961.29 | 1,450.00 |
| Salidas de efectivo | 200.00 | 0.00 |
| Devoluciones | 0.00 | 0.00 |
| Efectivo esperado | 6,261.29 | 1,650.00 |
| Efectivo contado | 6,100.00 | 1,650.00 |
| Diferencia | -161.29 | 0.00 esperado |

Los importes de octubre se verificaron por lectura; su cero sigue siendo un
resultado esperado y comprobado localmente con DB simulada. No se atribuye a
una ejecución real de octubre que todavía no figura en la consulta.

El formulario conserva `useState("2024-01-15")`. Esa fecha no vacía tiene
prioridad sobre `latestUploadDate` al solicitar el análisis. Por ello se pueden
cargar documentos de octubre y ejecutar el cálculo con los datos de enero.
INC-051 abierta; no se demostró qué interacción exacta hizo el usuario.

## Significado de los otros resultados

- `punto_equilibrio_diario = 53.93 unidades/día`: estimación con gastos fijos
  del mes y margen de contribución promedio de los productos calculables.
- `operative_cost_margin = 2916.82 MXN/día`: promedio diario de gastos fijos y
  variables confirmados del mes. El identificador legado no representa un
  porcentaje de margen ni una utilidad.
- `health_score = 49.65 MXN`: promedio monetario de los márgenes de contribución
  calculables; no es una puntuación compuesta de salud. Este significado ya está
  documentado en el catálogo N15; no se inventa una métrica nueva ni se cambia S3.

Las cifras se localizaron en S3 guardado; esta revisión no recalculó ni validó
independientemente todos los costos y recetas históricos. Frases como
«optimizado» o «saludable» no constituyen por sí solas una validación de negocio.

## Navegación y recuperación

INC-052 abierta: el menú abre `/dashboard` sin `run_id`; el hook limpia el
resultado al faltar ese parámetro. El usuario informó pérdida visual al ir al
chat. La corrida sigue en la base y su enlace privado permite recuperarla.
No se restaurará un resultado de otro negocio ni se deshará INC-036, que limpia
correctamente el análisis al cambiar negocio o retirar su identificador.

INC-053 abierta: N05 no persiste `sequential_results` ni `dormant_metrics`.
El GET local recupera cuatro insights, pero devuelve cero `calc_results`, cero
métricas activas y cero métricas dormant por sus valores predeterminados.
Así pueden quedar tarjetas vacías y el texto «Todas las métricas activas» sin
la evidencia de activación. No se debe inferir activación desde una lista ausente.

## Evidencia y siguiente acción

- Lectura principal: 65 filas de auditoría, solo del negocio autorizado.
- GET local del análisis coincidente: HTTP 200, fecha 2024-01-15, cuatro
  insights y tres listas vacías de resultados/activas/dormant.
- Los primeros intentos aislados no conectaron; las mismas lecturas terminaron
  correctamente fuera del aislamiento. No fueron fallos de análisis.
- Cero escrituras externas y cero llamadas del agente a modelos en el diagnóstico.
- No se repitieron suites, build ni E2E: no hubo corrección de producto.
- Evidencia saneada: [JSON del diagnóstico](evaluations/dashboard_demo_diagnosis_20261015.json).

Sigue corregir y probar 051/052/053 antes de aprobar el ensayo: fecha coherente
con documentos, recuperación del análisis en el mismo negocio y resultado
completo por linaje S3. Después ejecutar y verificar el análisis del 14-oct.
No repetir cargas o modelos para recuperar la corrida ya guardada.
