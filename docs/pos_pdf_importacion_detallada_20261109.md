# Importación detallada del PDF POS

Cambio solicitado el 9-nov-2026 en `MEPIA_Quincena_6`, rama `codex/quincena-6`,
HEAD `5ae4c868be6843513a3b8a4f0be2962762c6442d`, sin commit.
Incidencia INC-20261109-059 resuelta para el alcance local verificado.

## Comportamiento

El PDF de demostración incluye datos POS en adjuntos JSON. N01 ahora los
valida usando el contrato S1B y registra tickets individuales, productos,
pagos, turnos, caja e inventario. Para el documento de una página se usa
únicamente el 3-nov-2026, aunque el archivo incluya adjuntos de días contiguos.
El negocio se toma del selector de la aplicación.

La nueva carga del mismo archivo completa el documento que antes solo tenía
totales. Conserva su identificador, evita duplicados y actualiza el estado
de las métricas. Si hay una interrupción, se conserva una marca pendiente y
se puede reintentar. Los datos diarios existentes incompatibles se presentan
como conflicto y los conteos manuales compatibles conservan su autor.

Las horas se conservan como timestamp y dejan de interpretarse como cantidades.
Los pagos mantienen el formato anterior y el campo que utiliza S3. La interfaz
informa cuántos tickets fueron registrados.

## Validación

La prueba usa el endpoint real con el PDF de demostración, el motor S3 real,
una base en memoria y bloqueo de red externa. Verifica 15 tickets, ticket
promedio de 120 MXN antes de IVA, faltante de caja de 180 MXN y costo de merma
registrada de 8 MXN. Incluye reintento, actualización del documento anterior,
fallos en cada etapa, rechazo de inconsistencias, concurrencia de dos cargas
en el proceso local y compatibilidad con el PDF convencional.

El motor produjo 22 resultados numéricos con los datos del PDF y el esquema
simulado. La prueba comprueba también pagos, lealtad de 15 MXN y ventas por hora.
Las 18 pruebas nuevas aprobaron. La regresión dirigida final terminó con
74 aprobadas y una fallida en `test_p1_campos_obligatorios_siempre_presentes`
por tiempo de generación de Hypothesis, reproducida también por separado.
Se conservaron sus aserciones y controles. La generación anterior y las
pruebas de datos no acreditan una ejecución nueva en principal.

Compilación y tipos aprobaron con código 0. Se restauraron los archivos
generados de TypeScript. El servidor local se reinició con la compilación
`.test_tmp/principal_q6_pdf_20261109/build`, el login respondió HTTP 200 y
OpenAPI confirmó `POSIngestResult.detailed_import`.

Evidencia de trabajo en `MEPIA 3/tmp/importacion_pdf_q6/pytest_confirmacion.xml`,
`compilacion.log` y `metricas_verificadas.json`. Los intentos anteriores se
conservan en el mismo directorio con sus nombres originales.

## Alcance operativo

La nueva carga en la base principal la realizará el usuario. Las comprobaciones
del cambio utilizan DB en memoria y no llaman a modelos reales. El resultado
guardado antes del cambio sigue siendo una ejecución histórica. Para comprobar
la mejora se debe recargar Documentos, elegir el negocio, cargar el mismo PDF
y ejecutar un análisis nuevo del 3-nov-2026.

El detalle completo requiere el contrato S1B adjunto al PDF. Las imágenes y
los diseños arbitrarios de reportes conservan el flujo convencional de
extracción y revisión. Los adjuntos complementarios de recetas, gastos y
configuración mantienen sus vías de captura. El bloqueo de concurrencia es
del proceso local. Un despliegue con varios workers requiere coordinación
transaccional de importaciones entre procesos.

[Paquete manual Q7](../output/pdf/MEPIA_Q7_DaAx_Coffee/LEEME_Pruebas_manuales_Q7.md): cinco jornadas ficticias preparadas para ensayar el mismo contrato de detalle y comprobar sus métricas.
