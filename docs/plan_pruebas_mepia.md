# Pruebas de MEPIA por secciones

Plan local solicitado el 26-oct-2026. Categoría C: ampliación de validación,
sin reabrir los Pasos 1–4 aceptados ni INC-050–057. Se conserva el estado de Git
existente; no se hace commit/push ni despliegue.

La ejecución usa cuentas, base y proveedores simulados. Se bloquean conexiones
externas; la integración con Supabase real permanece omitida. Las respuestas de
demostración son prefabricadas y no acreditan la calidad de un modelo real.

## Secciones y criterios

| Sección | Qué comprobar | Evidencia automatizada |
|---|---|---|
| 1. Acceso y permisos | Login, sesión por pestaña, expiración, cierre, negocios propios; usuario ajeno/anónimo/revocado rechazado antes de datos/modelos | API/Auth ES256, recorrido general y demo |
| 2. Interfaz y navegación | Menú, rutas, Dashboard/Salud/Reportes/Chat, recarga, móvil acotado, teclado y respuestas tardías | Edge general extendido, historial, presentación |
| 3. Documentos y configuración | POS PDF/factura XML/PDF, revisión, fechas compatibles, defaults y tolerancias; sin costos inventados | Parsers reales de fixtures, fechas, N10 y demo |
| 4. Motor y guardado | Integridad, cálculos/unidades, umbrales, cero, escalación simulada, linaje y fallo N14 | Pruebas de propiedades, ocho oráculos deterministas y persistencia simulada |
| 5. Historial | Último terminado, explícito/recordado, varias corridas del día, paginación, recarga y negocio vacío | API de análisis y Edge historial |
| 6. Indicadores y gráficas | Cifras/unidades de la corrida, cero válido, orden, una corrida por fecha, huecos y datos insuficientes | Tendencias HTTP, presentación y Edge |
| 7. Chatbot | Conceptos, cifras/fuentes/fecha/linaje, seguimiento, historial, saludos, rechazo de cálculos y contenido ajeno | Suite N15, evaluación offline, matriz por capas y Edge |
| 8. Errores y recuperación | Red caída, DB/proveedor simulado fallido, reintento, doble envío, tamaño, limpieza por usuario/negocio/fecha | API, matriz y navegador extendido |

Build y TypeScript complementan las ocho secciones; no sustituyen la aceptación
funcional. Los casos pueden cubrir varias secciones: no sumar conteos de capas,
subpruebas, casos y controles de navegador como si fueran una sola cantidad.

## Entorno de demostración manual

El lanzador `scripts/start_mepia_demo.py` prepara tres procesos exclusivamente
en loopback: API en 8025, interfaz en 3036 y puerta de demostración en 3037.
Entrar por **http://127.0.0.1:3037/__demo__**. Usa puertos separados del servidor
del usuario (3016/8016); si alguno está ocupado, se detiene antes de iniciar.

| Cuenta ficticia | Contraseña ficticia | Uso |
|---|---|---|
| a@example.invalid | synthetic-test-password | Restaurante A y negocio vacío |
| b@example.invalid | synthetic-test-password | Negocio de otro propietario |

Los nombres de negocio y una banda visible identifican la demostración. El panel
permite elegir completado, cero, anomalía, insuficiente o fallido; crear una
corrida ficticia y reiniciar únicamente la memoria del proceso.

Documentos usa extracción local de los archivos de demostración. El análisis
devuelve el escenario prefabricado: sus importes no se calculan desde esos
documentos. Los cálculos reales se validan aparte con los oráculos y fixtures.
No hay Storage ni SQL externos. Chat usa grounding/validación reales con un SDK
simulado, no modelos. El gateway simula solo escrituras; no demuestra permisos
de los proxies/endpoints antiguos de ingesta/ejecución del producto.

El historial de análisis y los ajustes viven en memoria y se pierden al detener
o reiniciar. Los archivos originales no cambian. El reset no significa borrar
datos reales; una selección antigua puede requerir elegir otra corrida.

## Lista manual, en orden

Cada caso se registra como **pendiente**, **aprobado** o **fallido**, con captura
y observación. El resultado automático de un caso equivalente no sustituye tu
confirmación de comprensión y uso.

| ID | Acción | Resultado esperado | Revisión del usuario |
|---|---|---|---|
| A01 | Abrir Dashboard sin sesión | Login; sin información del negocio | Pendiente |
| A02 | Entrar con cuenta A | Solo sus dos negocios, nombres de demostración | Pendiente |
| A03 | Recargar y después abrir pestaña nueva | Recarga conserva; pestaña nueva pide login | Pendiente |
| A04 | Salir y volver a enlace privado | Login, sin cifras anteriores | Pendiente |
| I01 | Navegar Dashboard → Salud → Reportes | Misma corrida; contenido según vista | Pendiente |
| I02 | Ir al chat, recargar y volver | Referencia de análisis conservada | Pendiente |
| I03 | Abrir menú a ancho de celular | Rutas utilizables, sin desbordamiento en los tamaños probados | Pendiente |
| D01 | Abrir Documentos sin ajustes previos | Defaults sin bloquear ni inventar gastos | Pendiente |
| D02 | Editar/guardar tolerancia y volver | Porcentaje/costos conservados | Pendiente |
| D03 | Cargar POS PDF y factura XML de demo | Fecha 14/10/2026; documentos legibles | Pendiente |
| D04 | Elegir una fecha contradictoria y analizar | Aviso previo; no nueva corrida | Pendiente |
| D05 | Aplicar cero y analizar los dos documentos | Nueva corrida ficticia; cero visible | Pendiente |
| H01 | Entrar sin run_id ni selección recordada | Último análisis terminado propio | Pendiente |
| H02 | Elegir dos análisis de la misma fecha | Referencias distinguibles; resultados propios de cada uno | Pendiente |
| H03 | Recargar después de elegir uno anterior | Selección conservada | Pendiente |
| H04 | Abrir un run_id inexistente | Error; no sustituye por el último | Pendiente |
| H05 | Cambiar al negocio vacío | Limpieza inmediata y ausencia clara | Pendiente |
| G01 | Revisar evolución de varios días | Fechas ordenadas; no suma corridas repetidas | Pendiente |
| G02 | Revisar unidades y cero | Cero visible; cantidades y porcentajes separados | Pendiente |
| G03 | Elegir la primera fecha disponible | Explica que falta otro periodo comparable | Pendiente |
| G04 | Elegir resultado insuficiente | Sin cifras ni ausencia de anomalías inventadas | Pendiente |
| C01 | Saludar | Bienvenida social sin fuentes de datos inventadas | Pendiente |
| C02 | Preguntar ticket/conciliación en fecha con datos | Cifra, unidad y fuente S3 de esa fecha | Pendiente |
| C03 | Preguntar qué significa el indicador | Explicación conceptual identificada | Pendiente |
| C04 | Pedir dividir/sumar datos | Rechazo de cálculo; sin cifra derivada | Pendiente |
| C05 | Cambiar fecha/negocio y recuperar historial | Contexto limpio; sin conversación ajena | Pendiente |
| C06 | Eliminar conversación | Desaparece; sin borrar análisis guardados | Pendiente |
| E01 | Elegir corrida fallida | Mensaje distinto de historial vacío | Pendiente |
| E02 | Elegir corrida con anomalía | Alerta, cifra y explicación ficticias claramente visibles | Pendiente |
| E03 | Reiniciar demo y volver a Dashboard | Historial temporal reiniciado, sin tocar datos reales | Pendiente |

El ID manual C02 de esta tabla no equivale al C02 del plan histórico N15:
se citan siempre con el nombre del plan para evitar confundir sus estados.

## Revisión manual del tutorial en Q6

Abre **Tutorial** en la barra superior y recorre los 26 pasos en escritorio y
celular. Comprueba que la explicación se entienda, que la selección de análisis
se conserve al volver al Dashboard y que cada negocio recupere su propio avance.
Esta revisión manual sigue pendiente.

## Ejecutar y detener

Para abrir la demo otro día, ejecuta `& .\scripts\iniciar_demo_mepia.ps1` desde
PowerShell en la raíz. Detecta las rutas locales registradas o acepta PythonPath/NodePath.

Para la suite, con Python/dependencias del proyecto:

```powershell
python scripts/test_mepia_local.py --playwright 'RUTA_AL_MODULO_PLAYWRIGHT'
python scripts/start_mepia_demo.py
```

`--node` permite indicar el ejecutable si no está en PATH. Cada ejecución crea
salida nueva en `.test_tmp`; la demostración se detiene con Ctrl+C. No ejecutar
`api.main` para esta demostración. El perfil normal conserva su configuración.

Resultados exactos, límites y evidencias del corte actual:
[informe de pruebas](pruebas_mepia_20261026.md).

## Aceptación pendiente fuera de la simulación

Revisión humana de las 30 acciones anteriores; accesibilidad y dispositivos
adicionales; claridad y respuestas reales N15; caso histórico C02/cuota;
persistencia SQL/Storage real en entorno autorizado; integración real completa;
carga/rendimiento representativo; permisos por recurso y demás gates de producción.
Ninguno se declara aprobado por ejecutar las simulaciones.

## Prueba dirigida Q7

Seguir la [guía de los cinco PDF](../output/pdf/MEPIA_Q7_DaAx_Coffee/LEEME_Pruebas_manuales_Q7.md) y el [set del chat](../output/pdf/MEPIA_Q7_DaAx_Coffee/Comprobar_resultados_y_chat_Q7.md). Registrar una fila por corrida con fecha, referencia, resultado, reporte y evidencia móvil; marcar por separado simulación, aceptación manual y consumo real.
