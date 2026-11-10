# Consulta de análisis guardados, Dashboard y Salud — 19-oct-2026

**Validación local — 19-oct-2026:** historial/tendencias verificados con
452 pruebas y 136 subpruebas, una integración opt-in omitida, dos avisos; Edge
11/11 y 23/23, cero errores; build y tipos código 0. Proveedores/DB simulados;
sin commit/push ni producción. INC-055/056/057 resueltas y INC-017 actualizada.
[Evidencia y límites](../../../docs/analysis_history_dashboard_20261019.md).

Categoría C, ampliación solicitada; no es un paso nuevo de N15 ni reabre
INC-050–053. Implementación: `api/analysis_history.py`, proyección existente
`api/audit_results.py` y vistas comunes. No agrega migraciones, motores ni LLM.

## Lecturas protegidas

Todos los GET `/business/{business_id}/analyses` requieren Bearer validado por
AuthService (firma/claims/expiración). Verifican `businesses.owner_id` antes de
consultar auditorías y en cada lectura. 401 sin DB; 403 ambiguo para negocio
ajeno/inexistente/sin dueño; 404 ambiguo para corrida ausente/ajena. Error de
permisos o DB: 503 saneado. El proxy Next transmite Bearer, valida identificadores
y nunca publica excepciones privadas. Respuestas privadas, sin caché compartida.

| GET | Contrato |
| --- | --- |
| base `?page=0` | N05 del negocio, 25 por página, orden created_at/id descendente; next_page explícito; conserva todas las corridas del mismo día |
| `/latest` | Último N05 terminado por orden de guardado; completed/partial/escalated compatibles con node_status exitoso o legacy null; nunca failed/running/unknown |
| `/{run_id}` | Resultado persistido. Recuperación histórica de INC-053 solo por S3 explícito del mismo negocio/fecha/nodo/estado; jamás por cercanía |
| `/{run_id}/trends` | Indicadores de otras fechas hasta la seleccionada, sin calcular métricas de negocio ni sumar corridas |
| `/{run_id}/layer3` | Resuelve el padre guardado por N05 a N10/N14 del mismo negocio; conserva el fallo temporal de guardado de INC-048/049 |

La búsqueda automática pagina bloques de 100 hasta 10 000 registros candidatos;
si alcanza el límite sin resultado devuelve `limited=true`, no afirma historial
vacío y pide elegir uno. No confunde el límite de Data API con el fin de la lista.
El historial tiene paginación independiente para buscar corridas anteriores.
`unknown` solo representa un estado guardado sin evidencia de terminación;
no cambia los estados producidos por el motor.

## Selección y navegación

- Prioridad: run_id explícito (incluso vacío/inválido, con error sin fallback),
  selección de usuario/negocio en esta pestaña, último análisis terminado.
- Al recuperar automáticamente se incorpora run_id al enlace. Elegir historial
  solo ejecuta GET; no invoca ingesta, motor, generación ni guardado.
- Contexto en memoria y referencias mínimas en sessionStorage: usuario, negocio,
  corrida. Nunca guarda resultados ni un token adicional. Se revalida contra
  la sesión y los negocios propios antes de restaurar.
- Dashboard/Salud/Reportes y vuelta del chat conservan la selección, también
  tras recargar el chat. Cerrar sesión o cambiar negocio elimina inmediatamente
  el contexto anterior. Negocio nuevo puede recuperar su propio último análisis.
- El marco remonta la vista por usuario/negocio y los hooks abortan respuestas
  anteriores; valores, estados, errores e historial están ligados al ámbito.
- N15 conserva su consulta S3/N14 por fecha y linaje. Visitarlo no modifica la
  selección N05; este cambio no introduce N05 como fuente de respuestas del chat.

## Tendencias y unidades

Se consultan como máximo 300 N05 y se muestran hasta 90 fechas disponibles
anteriores o iguales a la elegida. Si se recorta el alcance se avisa en UI.
Una corrida por fecha: la elegida en su fecha si terminó; en las demás, la
última terminada por created_at/id. Fallos, estados desconocidos y procesos
en curso no desplazan una terminada. Los duplicados no se suman.

Allowlist de indicadores diarios escalares del negocio:

| Métrica exacta | Unidad exacta | Nombre visible |
| --- | --- | --- |
| conciliacion_caja | MXN | Diferencia de caja |
| punto_equilibrio_diario | unidades/día | Punto de equilibrio diario |
| ticket_promedio | MXN | Ticket promedio |
| volumen_tickets | tickets | Cantidad de tickets |
| tasa_descuento | % | Tasa de descuento |

No se equiparan alias por semejanza ni se agregan porcentajes, productos,
ingredientes o canales. CalcResult no conserva su identidad estructurada para
compararlos con certeza; se explica su exclusión. Nuevos indicadores requieren
definir su significado, unidad y ámbito antes de incorporarlos.

Se admiten valores finitos de status ok/warning/critical, incluido cero decimal.
Faltante, unidad distinta, incomplete_data/unit_mismatch, duplicado ambiguo o
valor inválido: null. Fechas ordenadas, espacios explícitos y líneas sin conectar
nulls; sin rellenar ceros, sumar ni interpolar. Cada punto conserva su run_id.
Se exigen dos fechas válidas para graficar y se explica el faltante si no alcanza.
El título es «Evolución de indicadores diarios»; no hay series fijas de ingresos
o margen. El gráfico seleccionado conserva valores/unidades de su propia corrida.

## Estados comprensibles

No hay tarjetas de ingresos/salud ficticias cuando esos indicadores no existen.
Las tarjetas muestran solo los indicadores conservados, incluidos los que tienen
datos insuficientes. Coste operativo no se anuncia como margen; health_score en
MXN se identifica como margen medio por producto, según el cálculo existente.

`forensic_status_available` es una proyección de lectura: exige informe original
con negocio/fecha/generated_at/anomalies, cálculo finito válido y corrida terminada.
El fallback visual nunca acredita evaluación. Solo entonces una lista vacía
permite «Sin anomalías detectadas en los indicadores evaluados». No equivale a
certificar indicadores no evaluados. Riesgo desconocido no se anuncia como bajo.
Se distinguen buscando último, cargando guardado, historial vacío, error,
análisis fallido, ausencia de cálculo y ausencia de evidencia forense.
No se anuncian arrays, calc_results ni un recorrido de Excel/CSV inexistente.

## Aceptación local

Pruebas con DB/Auth/proveedores simulados: acceso ajeno/sin sesión/revocado,
historial vacío/paginado, selección/recarga/navegación, varias corridas de la misma
fecha, cero válido, faltantes/unidades/duplicados, límites y ausencia de evidencia.
Evidencia y resultado final: `docs/analysis_history_dashboard_20261019.md`.
No se traslada la aprobación a una DB real, despliegue ni validación humana N15.
