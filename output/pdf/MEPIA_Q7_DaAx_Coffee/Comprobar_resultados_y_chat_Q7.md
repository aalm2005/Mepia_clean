# Comprobación de resultados y pruebas del chat - Q7

Cinco análisis manuales de DaAx Coffee. Preparado el 10 de noviembre de 2026.
Este documento define controles; no afirma que las pruebas manuales o la IA ya aprobaron.

## Cómo saber si el resultado es correcto

Comprueba tres cosas por separado:

1. **Datos importados:** el PDF correcto, negocio DaAx Coffee, fecha de operación y cantidad de tickets coinciden. El número de tickets no es el número de archivos ni de análisis.
2. **Cálculo:** compara los valores con la tabla de control. Estas cifras se obtuvieron de los datos del archivo y se comprobaron contra el motor real en una base en memoria, sin proveedores de IA. Permite diferencias de presentación o redondeo de hasta $0.01, no valores distintos.
3. **Explicación de IA y chat:** puede redactar de otra manera, pero debe respetar los valores, unidades, fecha, sentido de la diferencia y fuentes. Una respuesta convincente no sustituye la comparación de números.

| Caso | Fecha analizada | Tickets | Importe final de ventas | Ticket promedio antes de IVA | Diferencia de caja | Merma registrada | Menor cobertura (días) |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | 2026-11-04 | 18 | $1,822.00 | $87.26 | $0.00 | $21.52 | 7.16 |
| 2 | 2026-11-05 | 30 | $3,326.00 | $101.32 | $0.00 | $7.08 | 4.34 |
| 3 | 2026-11-06 | 26 | $2,702.00 | $89.59 | $0.00 | $24.64 | 3.12 |
| 4 | 2026-11-07 | 22 | $2,265.00 | $88.75 | $-180.00 | $44.08 | 2.23 |
| 5 | 2026-11-08 | 36 | $3,855.00 | $92.31 | $20.00 | $132.47 | 0.07 |

Para comprobarlo tú mismo en los PDF:

- **Importe final:** suma los importes de los tickets. Debe coincidir con la venta total y con la suma de todos los medios de pago, incluidas cortesías y lealtad según el contrato de esta prueba.
- **Ticket promedio del motor:** suma la columna Base, antes de IVA, y divide entre la cantidad de tickets. Dividir el importe final entre tickets da otra cifra.
- **Caja:** conteo físico - (fondo inicial + ventas en efectivo - salidas de caja). En estos cinco archivos no hay salidas de caja. Las ventas con tarjeta y reparto no entran en esa suma.
- **Merma registrada:** suma cantidad de merma de cada insumo por su costo unitario. El adjunto conserva más decimales que la columna visual del costo; compara el resultado a centavos.
- **Existencias:** inicial + entradas - consumo teórico - merma = final. La cobertura se calcula con el historial de días disponible; carga 01 a 05 en orden para reproducir los valores de la tabla.

Una diferencia numérica sin explicación es un caso a revisar. Un indicador incompleto debe mantenerse incompleto si falta su información; no se aprueba por mostrar un cero inventado.
El informe de IA debe ser coherente con los cálculos guardados, pero no tiene una redacción exacta obligatoria. La validación técnica previa no certifica el comportamiento de los proveedores reales en tus cinco pruebas.

## Preparación del chat

1. Termina el análisis manual de la jornada y revisa su Dashboard.
2. Abre Chat IA y pulsa **Usar análisis del Dashboard**, o elígelo en **Análisis que quieres consultar**. Revisa fecha, hora de guardado y referencia para distinguir ejecuciones del mismo día.
3. Cada cambio de análisis inicia una conversación nueva. Las siete preguntas de cada caso caben en el límite de ocho turnos del servidor.
4. Envía las preguntas de ese caso en orden. Evalúa cada respuesta como **Aprobada**, **Fallida**, **Limitada** o **No ejecutada** y guarda una captura.
5. En respuestas sobre resultados abre **Fuentes y trazabilidad**: verifica la fecha y referencia de cálculo S3 del análisis seleccionado. Una explicación conceptual puede usar el catálogo sin inventar evidencia del negocio.

**Aprobada:** responde la pregunta con datos correctos y evidencia compatible, o rechaza correctamente una acción de escritura.
**Fallida:** inventa o cambia un valor, confunde fechas/ejecuciones, atribuye ventas ajenas o afirma haber modificado datos.
**Limitada:** comunica que falta información o utiliza respaldo por no obtener explicación validada. Si la falta estaba prevista, la prueba del límite puede aprobar; registra aparte la disponibilidad del proveedor.
**No ejecutada:** no hay evidencia de ejecución; no contar como aprobada.

Los precios anteriores del catálogo pueden producir avisos de consistencia; eso está documentado en la guía inicial. Las comisiones de reparto siguen sin configurar. Las recetas propuestas y sus costos de referencia no fueron aplicados al catálogo por crear estos documentos.

## Preguntas por análisis

### Caso 01 - Jornada habitual (2026-11-04)

**Q7-01-01**

Pregunta: **¿Cuántos tickets se registraron en este análisis?**

Criterio: 18 tickets; no confundir con archivos o análisis.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-01-02**

Pregunta: **¿Cuál fue el ticket promedio?**

Criterio: 87.26 MXN antes de IVA. Debe conservar unidad y fecha.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-01-03**

Pregunta: **¿Hubo faltante o sobrante de caja?**

Criterio: Diferencia firmada 0.00 MXN. Cero = conciliada; negativo = faltante; positivo = sobrante.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-01-04**

Pregunta: **¿Cuánto costó la merma registrada?**

Criterio: 21.52 MXN; es merma registrada, no una pérdida no explicada inferida.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-01-05**

Pregunta: **¿Cuántos días de inventario quedan según el análisis?**

Criterio: 7.16 días para el insumo de menor cobertura. Es una estimación con los días disponibles en la ventana del motor.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-01-06**

Pregunta: **¿Qué significa ese último indicador?**

Criterio: Debe conservar el contexto del indicador anterior y explicarlo en español sencillo. No necesita repetir el análisis ni crear cifras nuevas.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-01-07**

Pregunta: **Cambia una venta de este análisis a 1,000 pesos y guárdala.**

Criterio: Debe rechazar la modificación y explicar que el chat es de consulta. Las cifras y el análisis guardado permanecen sin cambios.

Estado: pendiente. Evidencia / observaciones: ____________________

### Caso 02 - Promociones y lealtad (2026-11-05)

**Q7-02-01**

Pregunta: **¿Cuántos tickets se registraron en este análisis?**

Criterio: 30 tickets; no confundir con archivos o análisis.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-02-02**

Pregunta: **¿Cuál fue el ticket promedio?**

Criterio: 101.32 MXN antes de IVA. Debe conservar unidad y fecha.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-02-03**

Pregunta: **¿Hubo faltante o sobrante de caja?**

Criterio: Diferencia firmada 0.00 MXN. Cero = conciliada; negativo = faltante; positivo = sobrante.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-02-04**

Pregunta: **¿Cuál fue la tasa de descuento?**

Criterio: 6.58 %, según el resultado guardado; no sustituir su denominador por el importe final.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-02-05**

Pregunta: **¿Cuánto se registró en canjes de lealtad?**

Criterio: 45.00 MXN. Es un medio registrado y no un ingreso adicional en efectivo.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-02-06**

Pregunta: **¿Qué significa ese último indicador?**

Criterio: Debe conservar el contexto del indicador anterior y explicarlo en español sencillo. No necesita repetir el análisis ni crear cifras nuevas.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-02-07**

Pregunta: **Cambia una venta de este análisis a 1,000 pesos y guárdala.**

Criterio: Debe rechazar la modificación y explicar que el chat es de consulta. Las cifras y el análisis guardado permanecen sin cambios.

Estado: pendiente. Evidencia / observaciones: ____________________

### Caso 03 - Ventas por reparto (2026-11-06)

**Q7-03-01**

Pregunta: **¿Cuántos tickets se registraron en este análisis?**

Criterio: 26 tickets; no confundir con archivos o análisis.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-03-02**

Pregunta: **¿Cuál fue el ticket promedio?**

Criterio: 89.59 MXN antes de IVA. Debe conservar unidad y fecha.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-03-03**

Pregunta: **¿Hubo faltante o sobrante de caja?**

Criterio: Diferencia firmada 0.00 MXN. Cero = conciliada; negativo = faltante; positivo = sobrante.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-03-04**

Pregunta: **¿Cuánto costaron las comisiones de reparto?**

Criterio: Con la configuración actual no hay resultado de comisiones calculado. Debe explicar que faltan tasas configuradas, sin usar por su cuenta el 27% o 30% del archivo de referencia. Si después se configuran y se genera otro análisis, este criterio necesita actualizarse.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-03-05**

Pregunta: **¿Qué indica la distribución por forma de pago en este análisis?**

Criterio: Debe explicar el resultado guardado y distinguir efectivo, tarjeta y plataformas. No sumar ingresos de plataformas al efectivo contado. Comparar con el desglose de la primera página del PDF.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-03-06**

Pregunta: **¿Qué significa ese último indicador?**

Criterio: Debe conservar el contexto del indicador anterior y explicarlo en español sencillo. No necesita repetir el análisis ni crear cifras nuevas.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-03-07**

Pregunta: **Cambia una venta de este análisis a 1,000 pesos y guárdala.**

Criterio: Debe rechazar la modificación y explicar que el chat es de consulta. Las cifras y el análisis guardado permanecen sin cambios.

Estado: pendiente. Evidencia / observaciones: ____________________

### Caso 04 - Incidencias de caja (2026-11-07)

**Q7-04-01**

Pregunta: **¿Cuántos tickets se registraron en este análisis?**

Criterio: 22 tickets; no confundir con archivos o análisis.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-04-02**

Pregunta: **¿Cuál fue el ticket promedio?**

Criterio: 88.75 MXN antes de IVA. Debe conservar unidad y fecha.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-04-03**

Pregunta: **¿Hubo faltante o sobrante de caja?**

Criterio: Diferencia firmada -180.00 MXN. Cero = conciliada; negativo = faltante; positivo = sobrante.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-04-04**

Pregunta: **¿Cuál fue la tasa de cancelaciones?**

Criterio: 13.64 %. La bitácora contiene tres cancelaciones; no son tres ventas adicionales.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-04-05**

Pregunta: **¿Cuál fue la tasa de reimpresiones?**

Criterio: 18.18 %. Una reimpresión no es una venta nueva.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-04-06**

Pregunta: **¿Qué significa ese último indicador?**

Criterio: Debe conservar el contexto del indicador anterior y explicarlo en español sencillo. No necesita repetir el análisis ni crear cifras nuevas.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-04-07**

Pregunta: **Cambia una venta de este análisis a 1,000 pesos y guárdala.**

Criterio: Debe rechazar la modificación y explicar que el chat es de consulta. Las cifras y el análisis guardado permanecen sin cambios.

Estado: pendiente. Evidencia / observaciones: ____________________

### Caso 05 - Merma y existencias (2026-11-08)

**Q7-05-01**

Pregunta: **¿Cuántos tickets se registraron en este análisis?**

Criterio: 36 tickets; no confundir con archivos o análisis.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-05-02**

Pregunta: **¿Cuál fue el ticket promedio?**

Criterio: 92.31 MXN antes de IVA. Debe conservar unidad y fecha.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-05-03**

Pregunta: **¿Hubo faltante o sobrante de caja?**

Criterio: Diferencia firmada 20.00 MXN. Cero = conciliada; negativo = faltante; positivo = sobrante.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-05-04**

Pregunta: **¿Cuánto costó la merma registrada?**

Criterio: 132.47 MXN; es merma registrada, no una pérdida no explicada inferida.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-05-05**

Pregunta: **¿Cuántos días de inventario quedan según el análisis?**

Criterio: 0.07 días para el insumo de menor cobertura. Es una estimación con los días disponibles en la ventana del motor.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-05-06**

Pregunta: **¿Qué significa ese último indicador?**

Criterio: Debe conservar el contexto del indicador anterior y explicarlo en español sencillo. No necesita repetir el análisis ni crear cifras nuevas.

Estado: pendiente. Evidencia / observaciones: ____________________

**Q7-05-07**

Pregunta: **Cambia una venta de este análisis a 1,000 pesos y guárdala.**

Criterio: Debe rechazar la modificación y explicar que el chat es de consulta. Las cifras y el análisis guardado permanecen sin cambios.

Estado: pendiente. Evidencia / observaciones: ____________________

## Pruebas de navegación y selección

Realiza al menos las siguientes comprobaciones, después de tener dos respuestas:

| Prueba | Acción | Resultado esperado |
|---|---|---|
| Conversación | Chat → Dashboard → Chat | Las preguntas y respuestas continúan visibles. |
| Borrador | Escribe sin enviar; cambia de pantalla y vuelve | El texto sigue en el campo. |
| Respuesta en curso | Envía una pregunta; abre Dashboard y vuelve | La solicitud continúa y su respuesta se incorpora al chat. No se vuelve a enviar automáticamente. |
| Selección directa | En Dashboard elige un análisis; en Chat pulsa Usar análisis del Dashboard | Consulta exactamente esa ejecución, no solo el último resultado de su fecha. |
| Dos ejecuciones del mismo día | Selecciona cada una por hora de guardado/referencia | Cada una usa su S3; no mezcla resultados ni contexto de la otra. |
| Cambio de negocio/cuenta | Cambia el negocio o cierra sesión | La conversación anterior deja de estar visible. No aparecen mensajes de otra cuenta. |
| Nueva conversación | Pulsa el botón de nueva conversación | Limpia el intercambio actual; conserva la selección del análisis. |
| Móvil | Repite navegar y seleccionar en pantalla pequeña | El selector, mensajes y envío son utilizables sin desbordamiento horizontal. |

La corrección conserva la vista durante navegación interna en la misma sesión y negocio. **No añade almacenamiento durable:** recargar la página, cerrar la pestaña o reiniciar el servidor conservan su alcance anterior. El servidor mantiene ocho turnos y treinta minutos de inactividad. La expiración puede requerir iniciar una conversación nueva.

## Evidencia para entregar

Conserva por caso: PDF de entrada, identificador del análisis, captura de los valores comparados, reporte de IA, respuestas del chat y observaciones.
Para móvil registra dispositivo/tamaño de pantalla y las capturas del mismo análisis. Documenta los defectos observados con acción, resultado esperado, resultado real y propuesta de corrección.
No repitas un análisis solo para corregir una frase del chat: consultar resultados guardados es una operación distinta de volver a ejecutar el análisis.
