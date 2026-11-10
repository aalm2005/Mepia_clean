# DaAx Coffee - cinco pruebas manuales de Q7

Preparado el 10 de noviembre de 2026. Todos los datos de operación son ficticios.
El negocio existente fue renombrado de MEPIA Dev a DaAx Coffee, conservando su identificador, usuarios y registros.
La preparación no cargó archivos ni creó ventas o análisis de Q7 en la base principal. La ejecución manual no consta en la evidencia.

## Archivos que debes subir

Sube únicamente los cinco PDF numerados 01 a 05, uno por prueba y en ese orden.
Cada PDF contiene una sola jornada, varias ventas, pagos, corte de caja, operación e inventario.
El detalle estructurado va adjunto dentro del mismo PDF; no necesitas extraerlo.
Son cinco casos para cinco análisis distintos. Los 132 tickets contenidos no sustituyen el objetivo posterior de 50 análisis.

## Resultados de control comprobados sin IA

La tabla siguiente procede de una ejecución local del endpoint real de carga y del motor determinista, con base en memoria y red externa bloqueada.
No son resultados de aceptación de la base principal ni interpretaciones de IA.
Los valores de cobertura de existencias suponen que se cargan los casos en orden; el motor usa los días disponibles en su ventana, no exige siete días completos.

| Caso | Fecha | Escenario | Tickets | Importe final registrado | Diferencia de caja | Costo de merma | Menor cobertura (días) |
|---|---|---|---:|---:|---:|---:|---:|
| 01 | 2026-11-04 | Jornada habitual | 18 | $1,822.00 | $0.00 | $21.52 | 7.16 |
| 02 | 2026-11-05 | Promociones y lealtad | 30 | $3,326.00 | $0.00 | $7.08 | 4.34 |
| 03 | 2026-11-06 | Ventas por reparto | 26 | $2,702.00 | $0.00 | $24.64 | 3.12 |
| 04 | 2026-11-07 | Incidencias de caja | 22 | $2,265.00 | $-180.00 | $44.08 | 2.23 |
| 05 | 2026-11-08 | Merma y existencias | 36 | $3,855.00 | $20.00 | $132.47 | 0.07 |

En los cinco casos se verificaron 22 resultados numéricos del grupo operativo, además de una importación repetida sin duplicar ventas.
También se ejecutó la carga en memoria con una copia de las recetas y configuraciones consultadas en principal.
Los resultados completos y los indicadores pendientes se conservan en `Resultados_esperados_validacion_local.json`.

## Cómo hacer cada prueba

1. Inicia sesión en MEPIA y recarga la página para ver el nombre actualizado. Selecciona **DaAx Coffee**.
2. Abre **Documentos** y añade solamente el PDF del caso que vas a probar en el apartado POS.
3. Selecciona la fecha de operación del propio archivo. La fecha de subida no es la fecha del análisis.
4. Ejecuta **Analizar**. Estas cinco pruebas sí tienen autorizado consumir tokens de los proveedores configurados.
5. Espera a que termine; conserva el identificador del análisis, la fecha y cualquier aviso. No pulses Analizar otra vez mientras siga trabajando.
6. Comprueba los tickets importados y compara caja y merma con esta tabla. El ticket promedio del motor se expresa antes de IVA y puede diferir del promedio del importe final.
7. Revisa Dashboard, Salud y Reportes. Guarda capturas de resultados, indicadores incompletos y errores reales, si aparecen.
8. Anota qué ocurrió antes de pasar al siguiente caso. Carga 01, después 02, 03, 04 y 05 para conservar la secuencia del inventario.

Si vuelves a subir el mismo PDF, la validación local no duplicó ventas; ejecutar otra vez el análisis sí puede crear otra corrida y consumir tokens.
Si aparece conflicto por datos existentes, detente y conserva el mensaje. No cambies la fecha de un archivo ni borres registros para forzar la carga.

## Información que el PDF importa y referencias que siguen pendientes

La importación incorpora tickets, productos por ticket, pagos, turno, conteo de caja e inventario diario. El consumo teórico del inventario está calculado con las recetas propuestas.
La relación visible de inventario incluye saldo inicial y entradas como evidencia de control; el importador actual guarda consumo, merma, existencia final y costo, no crea facturas de compra por esas entradas.

`Referencias_DaAx_Q7.json` contiene recetas propuestas, precios de venta, costos por unidad y tasas de referencia. **Es un archivo de consulta, no un archivo que debas subir a Facturas.**
No se aplicaron esas recetas ni comisiones a la base principal. Durante el cotejo local se observó un catálogo previo con precios distintos. Los valores de los PDF son la referencia del caso ficticio.
Pueden aparecer alertas de precio cuando las referencias guardadas difieren de las del PDF. Los adicionales de leche o vainilla también pueden compararse contra un precio base sin adicionales.
No interpretes automáticamente ese aviso como un error de captura del PDF: registra que el catálogo y el esquema de modificadores requieren revisión.

No hay comisiones de reparto configuradas en principal. En especial el caso 03 permitirá documentar que una venta de reparto no basta para calcular comisiones sin las tasas guardadas.
La referencia propone Uber Eats 27% y DiDi Food 30% como tarifas base; no acredita una liquidación real ni incluye automáticamente publicidad, impuestos sobre la comisión u otros cargos.
Clip 3.6% más IVA se conserva como referencia; su comisión no se calcula por el mero hecho de identificar una venta con tarjeta.

Las métricas de punto de equilibrio, costos financieros y salud necesitan gastos clasificados y precios de compra compatibles, además de las recetas.
La relación costo laboral necesita nómina utilizable; los campos existentes y las etiquetas actuales no garantizan que esa métrica se active.
Estos datos pendientes se conservan como hallazgos de las pruebas, sin completar resultados con cifras inventadas.

## Recetas, precios y realismo de los documentos

Los productos y precios parten de menús públicos de Comore, Edén y Liminal. Se adoptan medias simples redondeadas de la muestra, con tamaños de referencia aproximados; no son un estudio estadístico del mercado de Monterrey.
Los gramajes son adaptaciones estandarizadas para DaAx, no recetas privadas obtenidas de esos negocios. La espuma procede de la leche utilizada y no se cuenta como ingrediente adicional.
La leche de avena y vainilla sustituyen o complementan el consumo físico del producto; las existencias continúan entre jornadas. Las conchas se almacenan congeladas y se hornean para servicio.

Las referencias locales de costos son cotizaciones individuales cuando no existe una muestra comparable. La leche se valora a 36/L como promedio de dos precios regulares de catálogo HEB de 34 y 38, sin sucursal confirmada.
La base de chocolate utiliza una referencia nacional de Cancún, documentada como sustituto de simulación y no como promedio local.
Los costos no incluyen de forma homogénea flete, impuestos recuperables, empaque, mano de obra ni servicios: no deben presentarse como costo total ni utilidad neta.
El adicional de avena de 15 es un supuesto comercial de DaAx; el adicional de sabor de 10 tiene referencia en Comore.

Los precios de las líneas son al público, con IVA incluido. El contrato actual de MEPIA representa IVA sobre la base y resta la bonificación al final; el caso 02 reproduce esa convención para comprobar el importador.
Los documentos son reportes internos de prueba, no CFDI ni comprobantes fiscales. La revisión fiscal de descuentos queda fuera de este paquete.

## Evidencia y registro de resultados

Para cada caso conserva: captura de la carga, fecha e identificador del análisis, indicadores obtenidos, reporte generado y observaciones.
En móvil comprueba el mismo análisis: menú, tarjetas, gráficas y Reportes. Anota dispositivo o tamaño de pantalla y captura cualquier corte, desbordamiento o dificultad de uso.
La evidencia móvil y la aceptación con IA siguen pendientes hasta que realices esas pruebas en la interfaz.
Puedes completar `Bitacora_pruebas_Q7.md` con lo observado. Sus filas comienzan como pendientes; no son pruebas aprobadas.

## Fuentes consultadas

- [menu_comore](https://www.comore.mx/): Menú local Monterrey. Americano 12 oz 55; latte 12 oz 75; capuchino 8 oz 65; flat white 8 oz 65; chai 75; matcha 85; chocolate 75; sabor adicional 10.
- [menu_eden](https://www.edenflorycafe.com/menu): Menú local Monterrey. Americano 54; latte 76; capuchino 80; flat white 76; chai 85; matcha 99; pan de canasta 53 o 63.
- [menu_liminal](https://liminalcafe.mx/products): Menú local Monterrey. Americano 300 ml 58; latte 300 ml 70; flat white 150 ml 64; chai 82; matcha 96; chocolate 68.
- [azucar_morena](https://cafeazucarmorena.com/pages/b2b): Cotización pública de proveedor de Monterrey, no promedio regional. Café 420/kg; vainilla 195/750 ml; avena 64/L; concha congelada 384/24; vaso kraft 215/50. Pedido mínimo y disponibilidad del proveedor aplican; no se realizan compras.
- [leche_borden](https://www.heb.com.mx/borden-leche-entera-1-l-451535/p): Precio de catálogo HEB, sin sucursal fijada. 34 por litro. Precio de referencia publicado; no cotización confirmada en una sucursal.
- [leche_lala](https://www.heb.com.mx/lala-leche-entera-1-l-1108/p): Precio regular de catálogo HEB, sin sucursal fijada. 38 por litro regular; se descarta la promoción de 30 para la base. Promedio de ambas referencias de leche = 36/L.
- [chai](https://cafesierranorte.com.mx/product/davinci-jarabe-te-chai/): Proveedor de Monterrey. Concentrado chai 250/L más IVA. Se adopta costo antes del IVA del proveedor, 0.25/ml.
- [matcha](https://fujiro.mx/): Proveedor con envíos desde Monterrey. Matcha puro 3600/kg mostrado; costo adoptado 3.60/g. Precio mostrado con promociones de vigencia no confirmada; referencia para simulación.
- [chocolate](https://kafensoluciones.com/categoria/bases-en-polvo/bases-de-sabores/): Referencia nacional de Cancún, no promedio de Monterrey. Base chocolate 380/1300 g, costo aproximado 0.29230769/g. Sustituto documentado al no obtener una cotización local pública comparable.
- [agua](https://waterdepotmx.com/precios): Proveedor que anuncia sucursales en Monterrey. Relleno de garrafón 20 L a 30; costo 0.0015/ml.
- [capuchino](https://www.starbucksathome.com/cam/recetas/capuccino): Receta pública de cafetería; no receta privada de Monterrey. Espresso con 150 ml de leche. La espuma procede de esa leche; no es un insumo adicional.
- [vainilla](https://www.starbucksathome.com/cam/recetas/latte-de-vainilla): Receta pública de cafetería; adaptación de gramajes DaAx. Espresso, leche y jarabe de vainilla.
- [uber](https://merchants.ubereats.com/mx/en/pricing/): Tarifas nacionales por plan, no promedio regional. Entrega 25/27/29%; se propone 27% para el escenario. Cargos de marketing, Uber One e impuestos se tratan por separado; no es costo total de liquidación.
- [didi](https://www.didi-food.com/es-MX/store?shopId=5764607669219100311&type=operation): Tarifa nacional, no promedio regional. Servicio con reparto 30%; se propone esa tarifa base.
- [clip](https://clip.mx/como-funciona-clip/calculadora-clip): Tarifa nacional. 3.6% más IVA; referencia informativa, no configura automáticamente una métrica de terminal.

Las referencias fueron consultadas el 10 de noviembre de 2026; pueden tener promociones, diferencias por sucursal o condiciones comerciales. Los documentos operativos de prueba no atribuyen ventas reales a esos proveedores.
