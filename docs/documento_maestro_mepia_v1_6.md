# MEPIA | Documento maestro V1.6

**Proyecto Integrador 2 · UANL · FIME · Corte del 10 de noviembre de 2026**

Esta edición consolida los avances acumulados hasta Q7 y actualiza el estado de V1.5 (30-oct-2026). El documento académico anterior se conserva en su ubicación original. Esta edición para el repositorio omite nombres y matrículas.

## 1. Problema, objetivo y alcance

Una cafetería puede tener ventas, costos, pagos e inventario en distintas fuentes. MEPIA reúne datos de operación, calcula indicadores con reglas verificables y presenta resultados, alertas e informes para que la persona responsable pueda actuar. El chat explica resultados ya calculados y señala información faltante. DaAx Coffee es el caso de prueba de Q7; sus cinco jornadas preparadas son ficticias.

El sistema cubre documentos POS, facturas compatibles, ajustes del negocio, cálculo, diagnóstico, análisis guardados, tendencias, reportes y consulta. Un resultado ausente no equivale a cero. Para rentabilidad y comisiones se necesitan referencias de costos, gastos, recetas o tasas registradas según el indicador. Ver el [catálogo y diseño de métricas](mepia_v4_metricas_diseno.md) y los [contratos](../.kiro/specs/mepia/_index.md).

## 2. Arquitectura y recorrido

La interfaz Next.js/TypeScript maneja el acceso, los documentos y las vistas; FastAPI coordina la ingesta, el motor y el chat. Supabase autentica y guarda los datos del negocio; el servidor valida la propiedad antes de leer corridas. El flujo va de ingesta (S1) e integridad (S2) a cálculo (S3), diagnóstico (S4), síntesis y guardado (N05) e informe (N14). El chat (N15) consulta resultados guardados con permisos y linaje de origen.

1. Entrar, seleccionar el negocio autorizado y revisar la configuración inicial.
2. Cargar el POS de la fecha operativa y verificar datos y avisos antes de analizar.
3. Ejecutar el análisis. Consultar Dashboard, Salud y Reportes desde su referencia.
4. Seleccionar la corrida en el historial o en el chat para explicar sus resultados.
5. Registrar la evidencia con fecha, entorno, referencia del análisis y resultado esperado.

## 3. Avance acumulado

| Corte | Avance |
|---|---|
| Q1–Q4 | Definición del problema, arquitectura, métricas, cálculo, escenarios y evaluación del chat. Los registros de cada etapa permanecen como evidencia histórica. |
| Q5 | Acceso por sesión, configuración inicial, persistencia de análisis e informe, correcciones de recuperación y publicación de su propia rama. |
| Q6 | Historial por corrida, tendencias, demostración local aislada y tutorial integrado de 26 pasos en seis vistas. Se conserva la selección entre Dashboard, Salud y Reportes. |
| Q7 | PDF POS con detalle, cinco casos de DaAx Coffee, guía de 35 preguntas y mejoras de conversación y selección en el chat. |

El tutorial se puede volver a abrir desde la barra superior. El historial distingue fecha operativa y hora de guardado; abrir un análisis guardado es una lectura. Las tendencias requieren fechas comparables y mantienen la distinción entre cero y falta de datos.

## 4. Q7: ingesta, resultados y chat

El PDF POS estructurado trae ventas, productos, pagos, turnos, caja e inventario. Se importa el adjunto S1B para las fechas visibles y el negocio autorizado. Repetir una carga compatible no duplica ventas; un conflicto de datos requiere revisión. Un PDF sin ese detalle no aporta por sí solo todas las métricas.

El chat conserva mensajes, borrador y respuesta en curso al navegar internamente en el mismo usuario y negocio. El historial conversacional no se recupera tras recarga, cierre de pestaña o reinicio; el servidor mantiene hasta ocho turnos durante treinta minutos. El selector de análisis recientes y el botón **Usar análisis del Dashboard** envían la referencia N05 exacta. El servidor valida propietario, estado y origen S3 antes de responder. Cambiar de análisis abre una conversación nueva.

| Fecha | Escenario | Tickets | Importe final MXN | Diferencia de caja MXN |
|---|---|---:|---:|---:|
| 04-nov | Jornada habitual | 18 | 1,822 | 0 |
| 05-nov | Promociones y lealtad | 30 | 3,326 | 0 |
| 06-nov | Ventas por reparto | 26 | 2,702 | 0 |
| 07-nov | Incidencias de caja | 22 | 2,265 | −180 |
| 08-nov | Merma y existencias | 36 | 3,855 | +20 |

Los cinco PDF contienen 132 tickets y preparan cinco corridas. El cálculo local produjo 22 métricas operativas numéricas en cada caso. El ticket promedio del motor es previo a IVA. Los precios y costos se estimaron a partir de referencias públicas de Monterrey y su zona metropolitana; representan una muestra, no un promedio estadístico. Las recetas y comisiones propuestas son material de referencia, sin aplicación automática al negocio.

## 5. Validación y entrega

| Entregable | Estado al corte |
|---|---|
| Historial, reportes y tutorial | Implementados y verificados con datos simulados. |
| Importación de detalle POS | Verificada localmente, incluida recarga sin duplicación. |
| Chat con corrida exacta | Verificado localmente en API, proxy y navegador. |
| Meta de 50 análisis | Cinco casos preparados. La evidencia de ejecución manual y las 45 corridas restantes siguen pendientes. |
| Acceso del equipo | Cinco integrantes; la aplicación autoriza por propietario y no ofrece un negocio compartido por membresías ni cinco roles distintos. El cambio de nombre a DaAx Coffee conserva el negocio existente. |
| Evidencia móvil | Navegación y tutorial en navegador emulado (390 × 844). Queda por documentar la prueba Q7 en un teléfono físico. |
| Publicación | Código y documentación versionados en la rama del corte. La publicación de la rama no instala ni despliega MEPIA. |

Para Q7, subir los cinco PDF uno a uno, en orden. Ejecutar los análisis manuales autorizados con IA, comparar las cifras de control y guardar la referencia de cada corrida. Revisar Dashboard, Salud y Reportes. Ejecutar siete preguntas por caso y registrar respuesta, cifra esperada y evidencia. En el teléfono, documentar carga, selección de análisis, lectura de reportes y regreso al chat.

Las áreas de oportunidad son gestionar acceso compartido si vuelve a solicitarse, completar evidencias en teléfono, documentar la aceptación con IA y revisar datos de catálogo, modificadores, comisiones y gastos antes de exigir métricas de rentabilidad. La ampliación a 50 análisis necesita variar los escenarios y preservar la trazabilidad de cada corrida.

## 6. Fuentes y anexos

- [Estado del producto y pendientes](estado_actual_mepia.md)
- [Pruebas de integración de Q6](pruebas_mepia_q6_20261104.md)
- [Contrato y pruebas de importación POS](pos_pdf_importacion_detallada_20261109.md)
- [Mejoras y evidencia del chat de Q7](q7_chat_navigation_20261110.md)
- [Cinco PDF, resultados de control y 35 preguntas](../output/pdf/MEPIA_Q7_DaAx_Coffee/LEEME_Pruebas_manuales_Q7.md)
- [Verificación del corte Q6–Q7](cierre_q6_q7_20261110.md)
