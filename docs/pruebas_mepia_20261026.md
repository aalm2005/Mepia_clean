# Pruebas locales de MEPIA — 26-oct-2026

**Resultado:** comprobaciones técnicas locales aprobadas, entorno de demostración
disponible y aceptación manual pendiente. Rama `codex/quincena-5`, HEAD
`5ae4c868be6843513a3b8a4f0be2962762c6442d`; avances **sin commit**.
Categoría C solicitada. INC-035 actualizada; sin incidencias nuevas de producto.
Se conservan INC-050–057 y los Pasos 1–4 aceptados.

## Resultados por sección

| Sección | Resultado y alcance |
|---|---|
| 1. Acceso y permisos | 67 pruebas API/Auth; JWT, propietarios y sesión. Navegador general extendido: 26/26 en todo su recorrido |
| 2. Interfaz y navegación | 12 pruebas de presentación del resultado; rutas/recarga/móvil acotado en el recorrido general; cero errores de página |
| 3. Documentos y configuración | 78 pruebas API/parsers/fixtures; N10 en Edge 14/14; fechas 11/11 |
| 4. Motor y guardado | 81 pruebas agrupadas; ocho escenarios deterministas con 95/95 comprobaciones numéricas; N14/linaje/fallos con DB/LLM simulados |
| 5. Historial | 62 pruebas de lecturas/migración; Edge historial 11/11; selección, varios análisis por día, vacío, cero y acceso ajeno |
| 6. Indicadores y gráficas | Presentación 16/16 + 8/8; API/tendencias en la sección anterior; fechas/unidades/huecos y ausencia de datos |
| 7. Chatbot | 119 pruebas agrupadas; evaluación simulada 28 casos/36 partes, cobertura 22/22, cero fallos mecánicos y 36 revisiones semánticas pendientes |
| 8. Errores y recuperación | 33 pruebas de proveedores/ejecutor; red, respaldo, tamaño, doble envío y respuestas tardías en Edge extendido |

La partición Python suma **452 aprobadas**, más **136 subpruebas** aprobadas,
**una integración real omitida y dos avisos** de deprecación FastAPI; 55.02 s,
código 0. Los controles de navegador y propiedades no se suman como una cantidad
única de casos. Los dos avisos preexistentes no son errores funcionales nuevos.

La demo nueva tiene **15 pruebas API aprobadas** y **5/5 controles de navegador**:
panel, login/historial/gráficas, PDF/XML → corrida ficticia → cero, consulta de
evidencia por chat y vuelta a selección, negocio vacío/logout. Cero errores de página.

Build Next 15.5.27 y TypeScript: código 0; tsconfig.json/next-env.d.ts restaurados
exactamente. Helper de restauración: 3/3. Node observado: 24.22.1; Python 3.12.14.
No se instalaron dependencias ni se tocaron configuraciones privadas.

## Matriz N15 y aceptación

El ejecutor por capas terminó **41 controles locales aprobados, siete no
ejecutados y cero fallidos**, código 0, sin modelos reales. El recorrido extendido
aporta C07/C08 y comprobaciones de respaldo/tamaño/doble envío/teclado parcial.
Consolidación: **43 controles locales con evidencia y cinco gates separados**
(P01/P03/P04/P05/P06). Esto no equivale a 43 casos funcionales integralmente
aceptados ni aprueba claridad humana, C02/cuota real o preparación de producción.

El informe offline nuevo marca revisión semántica pendiente para esta corrida
simulada. No revoca la aceptación histórica del Paso 4: son evidencias y alcances
distintos. La nueva lista manual contiene 30 acciones, todas pendientes de tu
confirmación, en el [plan por secciones](plan_pruebas_mepia.md).

## Incidencia del ejecutor e intentos preservados

INC-20261014-035 se actualiza sin duplicarla:

- El primer agregado terminó código 1: las cuatro comprobaciones Node no
  arrancaron por barras Windows en NODE_OPTIONS. Ruta corregida; repetición
  dirigida aprobada 11/11, 16/16, 8/8 y 3/3. Python/motor/chat ya habían pasado.
- El agregado de navegador terminó código 1 por su comprobación de preservación:
  detectó dos archivos nuevos de infraestructura editados intencionalmente
  durante la ejecución (`scripts/start_mepia_demo.py`, `tests/local_build.cjs`).
  Sus cuatro tareas funcionales/build terminaron código 0. La auditoría final
  coteja esos cambios previstos y confirma preservación de producto/evidencias.
- Demo, intento 1: aserción durante «Cargando negocios»; se espera la carga y
  se selecciona explícitamente el negocio del caso.
- Demo, intento 2: el selector esperaba solo «0» en un elemento con «0MXN».
  Captura demuestra cero y gráficas correctas; se exige cero y su unidad.
- Demo final: 5/5 y código 0. No se cambió el resultado del producto ni se
  descartaron los intentos iniciales para presentar una aprobación.

La clasificación inicial del resumen por archivos omitía clases de prueba
anidadas; se corrigió y se releyó el mismo XML, sin repetir la suite general.
No hay nueva regresión de producto demostrada en estas ejecuciones.

## Cómo usar la demostración

Abre **http://127.0.0.1:3037/__demo__**. La página explica las cuentas ficticias,
permite elegir escenario y crear/reiniciar corridas temporales. Entrar por el
gateway 3037 conserva la identificación de demostración y las escrituras simuladas.
Si el primer negocio está vacío, elige «DEMOSTRACIÓN · Restaurante A».

Cuenta A: `a@example.invalid`; cuenta B: `b@example.invalid`.
Contraseña ficticia de ambas: `synthetic-test-password`.
No usar credenciales reales en este entorno.

Puedes probar historial, gráficas, configuración y chat sin API real. Documentos
extrae localmente los PDF/XML de demo; **el resultado de análisis es prefabricado**,
independiente de sus importes. Los cálculos reales están comprobados en los
oráculos separados. Los endpoints de demostración verifican sesión/propietario,
pero el gateway no demuestra autorización de escrituras del backend legado.

La demo usa API 8025, interfaz 3036 y gateway 3037; mantiene separados los servicios
del usuario en 3016/8016. Todo es memoria: detener/reiniciar elimina únicamente
esos datos ficticios. El panel también borra conversación temporal al reiniciar.
Se bloquearon conexiones externas en procesos de prueba; el navegador automático
permitió solo los orígenes loopback de esta ejecución. No hubo uso de modelos,
lecturas/escrituras externas, commit/push ni despliegue.

Para iniciarla otro día desde la raíz, abre PowerShell y ejecuta:

```powershell
& .\scripts\iniciar_demo_mepia.ps1
```

El lanzador prepara su propia caché y restaura archivos generados; si un puerto
está ocupado se detiene antes de arrancar. Ctrl+C en su terminal detiene los
procesos propios. La demo iniciada durante esta tarea queda disponible para probar.

## Preservación y archivos de esta tarea

Auditoría final local: 777 archivos previos presentes,
133 archivos de producto y 465 evidencias históricas/demo
con huellas intactas; tsconfig.json/next-env.d.ts restaurados, diff código 0.
Las sondas Python/Node bloquearon destinos externos antes de contactar.
La revisión manual conserva 30 acciones pendientes; no acredita modelos ni SQL reales.

Infraestructura nueva: `scripts/test_mepia_local.py`, `scripts/start_mepia_demo.py`,
`scripts/iniciar_demo_mepia.ps1`, `tests/local_network_guard.py`,
`tests/local_network_guard.cjs`, `tests/local_build.cjs`, `tests/mepia_demo_server.py`,
`tests/mepia_demo_gateway.py`, `tests/test_mepia_demo.py`, `tests/mepia_demo_e2e.cjs`.
Los dos ejecutores existentes de historial admiten ahora salida elegible para
conservar sus evidencias históricas. Los archivos normales de la aplicación
no cambiaron. Especificación nueva: `.kiro/specs/mepia/local_testing.md`.
El inventario exacto de documentos/evidencias nuevos y actualizados está en la auditoría.

La captura final de gráficas espera corrida elegida, cero con unidad y puntos
visibles antes de exportar; su comprobación adicional terminó código 0 y cero
errores de página. Los intentos y capturas intermedios también se conservan.

## Evidencias y límites

[Resumen estructurado](evaluations/pruebas_mepia_20261026/resumen.json),
[regresión](evaluations/pruebas_mepia_20261026/regresion.log),
[matriz consolidada](evaluations/pruebas_mepia_20261026/matriz_consolidada.json),
[demo API](evaluations/pruebas_mepia_20261026/demo_api.log),
[demo navegador](evaluations/pruebas_mepia_20261026/demo_navegador.json),
[captura final de gráficas](evaluations/pruebas_mepia_20261026/demo_graficas_final.png),
[captura chat](evaluations/pruebas_mepia_20261026/demo_chat.png),
[auditoría de preservación y documentación](evaluations/pruebas_mepia_20261026/auditoria.json).

Los registros crudos e intentos están en `.test_tmp/qa_20261026/`, sin sobrescribir
evaluaciones previas. Pendientes: aceptación manual/claridad, dispositivos y
accesibilidad completos, respuesta real de proveedores, integración SQL/Storage
autorizada, carga/rendimiento representativo y controles de producción. El alcance
actual no permite declarar todas esas capas aprobadas.
