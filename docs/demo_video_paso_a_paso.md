# Ensayo de MEPIA para el video

**Entrega de la quincena 5:** Git conserva los bytes del paquete de demostración
al clonarlo en Windows (INC-054), incluidos PDF y XML. No edites sus cantidades
ni conviertas los archivos antes del ensayo; así se conserva su identificación
por contenido. La guía de publicación registra la verificación de integridad.

**Correcciones verificadas:** INC-051/052/053 resueltas localmente. La fecha
puede quedar vacía para inferir 14-oct-2026 desde los documentos; si eliges otra
distinta a las ventas, se solicita corregirla antes de analizar. El menú conserva
la corrida dentro de la misma sesión/negocio y el Dashboard recupera los cálculos.
El análisis anterior del 15-ene-2024 se conserva como tal; no demuestra el caso
de octubre. [Verificación y límites](dashboard_demo_fix_20261015.md).

Preparado el 15-oct-2026. Los datos son ficticios y pertenecen al **14 de octubre
de 2026**. Este documento describe el ensayo; no afirma que el análisis real de
IA ya haya terminado. [Evidencia local](evaluations/demo_preparation_20261015.json).

## Antes de iniciar

- OpenAI está configurado en privado; Claude puede quedar vacío porque N11 tiene
  respaldo OpenAI, comprobado aquí con un proveedor simulado. Gemini sigue a cargo
  del chat. Todavía falta validar las respuestas de los servicios reales.
- El servidor completo y la interfaz deben estar activos en esta computadora.
  Al terminar la preparación se comprueba su arranque. Abrir
  [MEPIA](http://localhost:3016/) en Edge o Chrome.
- El conteo ficticio de caja ya quedó preparado con tu autorización expresa:
  una fila insertada y verificada, sin duplicados ni cambios a gastos o ajustes.
  No necesitas ejecutar el script de preparación. El plan confirmó fecha libre,
  negocio con propietario y ningún documento anterior pendiente de revisión.
- El ensayo real creará dos documentos, una entrada POS, una compra y los
  resultados que genere el análisis. Los modelos pueden consumir cuota.

Las correcciones locales INC-048/049/050 están verificadas: guardado del informe,
seguimiento avanzado y presentación de decimales. 208 pruebas/41 subpruebas,
16 controles de presentación y tipos aprobados. Ensayo real aún pendiente.

## 1. Localiza los archivos

Carpeta: `output/pdf/demo_mepia_20261014/`, dentro de esta copia de MEPIA.

| Archivo | Uso |
|---|---|
| `01_ventas_demo_2026-10-14.pdf` | Cargar en el espacio de ventas POS |
| `02_compra_demo_2026-10-14.xml` | Cargar en el espacio de facturas |
| `03_compra_demo_REFERENCIA_NO_SUBIR.pdf` | Solo leer: muestra la misma compra del XML |
| `resultados_esperados.json` | Referencia para verificar las cantidades |

Sube **solo los dos primeros**. El PDF de compra y el XML representan la misma
operación: subir ambos registraría dos documentos distintos.

## 2. Entra a MEPIA

1. Abre el enlace local y entra con tu cuenta de la base principal.
2. Confirma que aparece **MEPIA Dev**.
3. Abre **Documentos** en el menú. Los ajustes iniciales ya se aplican
   automáticamente; no necesitas llenar el formulario avanzado para este ensayo.

## 3. Carga y analiza

1. Deja vacía la fecha para tomarla de los documentos, o elige **14/10/2026**. El valor interno es `2026-10-14`;
   el orden de día/mes/año puede verse diferente según Windows.
2. Conserva el perfil **Operative Genius** que aparece inicialmente.
3. En ventas POS selecciona `01_ventas_demo_2026-10-14.pdf`.
4. En facturas selecciona `02_compra_demo_2026-10-14.xml`.
5. Pulsa **Analizar 2 archivos con Agentes IA** una sola vez y espera. La fecha enviada debe ser 2026-10-14; una selección contradictoria se detiene con aviso.
6. Los parsers locales aceptaron ambos archivos sin revisión humana. Si en el
   ensayo real aparece una revisión o un error, anota el mensaje y la etapa;
   no agregues otros documentos para intentar continuar ni cambies cantidades.

Repetir los mismos archivos permite reutilizar sus documentos por SHA-256.
Volver a analizar sí puede generar otra corrida y consumo de modelos.

## 4. Comprueba el Dashboard

La página debe abrir el análisis correspondiente al 14/10/2026; comprueba la fecha del encabezado. Al volver desde Chat IA, el menú conserva esa corrida en la misma sesión y negocio. Conserva su enlace
con `run_id` para volver a mostrarlo. Los valores de referencia son:

| Dato | Cantidad |
|---|---:|
| Venta total del PDF | $2,900.00 |
| Venta en efectivo / tarjeta | $1,450.00 / $1,450.00 |
| Compra del XML, con IVA | $928.00 |
| Fondo inicial / efectivo contado | $200.00 / $1,650.00 |
| Diferencia de caja calculada | **$0.00 MXN, estado ok** |

La tarjeta de conciliación o el resultado `conciliacion_caja` debe mostrar cero:
el dinero contado coincide con el fondo inicial más lo vendido en efectivo.
Las otras tarjetas pueden aparecer con raya o datos insuficientes. Este conjunto
no contiene tickets individuales, recetas, nómina ni costos confirmados; no
demuestra ticket promedio, utilidad ni todos los indicadores del sistema.

## 5. Prueba Chat IA

1. Abre **Chat IA**, inicia una conversación nueva y selecciona **14/10/2026**.
2. Pregunta: **¿Cuál fue la conciliación de caja?**
3. Debe explicar en lenguaje sencillo el resultado disponible de **$0.00 MXN**.
   Comprueba que la fuente corresponde al mismo día y al análisis guardado.
4. Luego pregunta: **¿Qué es el ticket promedio?** Esta segunda pregunta comprueba
   una explicación conceptual, no un ticket promedio calculado para el negocio.

La cadena local probada es documentos → conciliación S3 → evidencia recuperable
por el chat. No hubo modelos reales ni escrituras externas en esa prueba. El
ensayo de la interfaz debe confirmar análisis, guardado y respuesta real.

## 6. Graba después de completar el ensayo

- 0:00-0:30: qué problema resuelve MEPIA y que se muestran datos de demostración.
- 0:30-1:15: login, negocio automático y Documentos con configuración inicial.
- 1:15-2:30: seleccionar fecha/archivos, analizar y explicar conciliación de caja.
- 2:30-3:45: consultar el resultado y un concepto en Chat IA.
- 3:45-4:30: avances y pendientes: tutorial guiado, adaptación móvil completa,
  más validaciones funcionales/humanas y controles para publicación.

El informe avanzado N14 solo aparece cuando el flujo correspondiente se ejecuta;
una corrida básica no garantiza que haya escalación. No hace falta forzarla para
demostrar este recorrido. Para grabar el login, cerrar y volver a abrir la pestaña
debe pedir sesión; recargar la misma pestaña la conserva.

## Preparación técnica del conteo

El agente ejecuta primero `scripts/prepare_video_demo.py` sin parámetros: solo
lectura. Con la autorización específica recibida, `--apply` insertó un conteo nuevo de $200
de fondo y $1,650 contados, con cero salidas, para la fecha indicada.
La consulta posterior confirmó una sola preparación y cero nuevas inserciones.
Es idempotente: si su fila ya existe idéntica, no inserta otra. Rechaza otro conteo,
datos anteriores del día, propietario ausente o documentos pendientes. No borra
ni sobrescribe registros. El paso no usa modelos ni sube los PDF/XML por ti.

Si necesitas iniciar MEPIA después de reiniciar Windows, sigue la
[guía de instalación y arranque](mepia_setup_video.md). En esta máquina se usó el
Python instalado para el proyecto; no es necesario reinstalar dependencias.
