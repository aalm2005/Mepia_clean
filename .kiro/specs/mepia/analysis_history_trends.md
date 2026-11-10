# Tendencias de indicadores guardados

## Selección de periodos

El GET protegido `/{run_id}/trends` consulta hasta 300 N05 y muestra como máximo
90 fechas disponibles anteriores o iguales a la elegida; limited avisa recortes.
Conserva todas las corridas en el historial, pero solo una terminada por fecha
en cada serie. En la fecha elegida, la corrida seleccionada tiene prioridad si
terminó; en las demás, la última terminada por created_at/id. Failed, running y
unknown no desplazan una terminada. Nunca se suman análisis del mismo día.

## Indicadores admitidos

| Métrica exacta | Unidad exacta | Etiqueta |
|---|---|---|
| conciliacion_caja | MXN | Diferencia de caja |
| punto_equilibrio_diario | unidades/día | Punto de equilibrio diario |
| ticket_promedio | MXN | Ticket promedio |
| volumen_tickets | tickets | Cantidad de tickets |
| tasa_descuento | % | Tasa de descuento |

Solo escalares diarios del negocio. No se equiparan alias por semejanza ni se
agregan productos, ingredientes, canales o porcentajes. CalcResult no conserva
identidad estructurada suficiente para comparar esos ámbitos con certeza;
se informa su exclusión. Añadir series exige definir significado, unidad y ámbito.

Valores finitos con status ok/warning/critical son válidos, incluido cero decimal.
Ausencia, unidad distinta, incomplete_data/unit_mismatch, duplicado ambiguo o
valor inválido producen null. Las fechas disponibles se ordenan, cada punto
conserva run_id y las líneas no conectan nulls. No se sintetizan días sin análisis.
No se rellenan ceros, interpolan cifras ni calculan nuevas métricas de negocio.

Se requieren dos fechas válidas por serie para graficar. Si no alcanzan, se
explica que falta otro análisis comparable; más corridas del mismo día no bastan.
Título visible: «Evolución de indicadores diarios». No hay series fijas de
ingresos/margen. Las barras de «Métricas calculadas» corresponden exclusivamente
a la corrida seleccionada, con unidades separadas.

Los KPI conservan significado: costo operativo no es margen; health_score en
MXN representa margen medio por producto según el cálculo existente, no un
índice universal de salud. Concentración de ingresos no equivale a venta total.
La ausencia de un indicador no crea una tarjeta ficticia.

[Consulta y seguridad](analysis_history.md), [contratos](analysis_history_contracts.md),
[selección](analysis_history_ui.md),
[pruebas y límites](../../../docs/analysis_history_dashboard_20261019.md).
