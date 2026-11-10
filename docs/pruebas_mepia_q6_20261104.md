# Revisión de integración de MEPIA Q6

El 4 de noviembre de 2026 se revisó la rama `codex/quincena-6`, base `5ae4c86`.
El tutorial de 26 pasos se integra con el historial, los indicadores y las
tendencias. El botón **Tutorial** en la barra superior permite repetirlo.

## Resultados con datos simulados

| Comprobación | Resultado |
|---|---|
| Python | 467 pruebas y 136 subpruebas aprobadas. 1 integración real omitida. 2 avisos de FastAPI |
| Fechas, presentación, historial y restauración | Cuatro ejecutores aprobados |
| Cálculos del motor | 8/8 escenarios y 95/95 comprobaciones |
| Chat offline | Cobertura 22/22, cero fallos mecánicos y 36 revisiones semánticas pendientes |
| Matriz automatizada del chat | Código 0. Las comprobaciones manuales o reales conservan su estado |
| Edge · Interfaz general y chat | 26/26 controles aprobados |
| Edge · Historial y gráficas | 11/11 controles aprobados |
| Edge · Configuración | 14/14 controles aprobados |
| Edge · Tutorial guiado | 12/12 controles aprobados |
| Edge · Demostración PDF/XML | 5/5 controles aprobados |
| Compilación y TypeScript | Código 0 en ambos. Configuración de Next restaurada |

La demo recorrió la carga de PDF/XML, el guardado de un análisis ficticio
con cero válido, la consulta en el chat y el cambio a un negocio vacío.
El tutorial se recorrió en escritorio y a 390 × 844. Se comprobó el avance
por cuenta y negocio, la continuidad del análisis seleccionado, los enlaces
directos y la ausencia de solicitudes de escritura del tutorial.

## Ubicación de los avisos del Dashboard

Se verificó que los cinco avisos del Dashboard resalten su propio objetivo
y muestren una flecha en escritorio y móvil. En un negocio vacío, los
avisos que requieren resultados señalan el estado del análisis. Edge
aprobó 12/12 controles, compilación y tipos con código 0.
Evidencia en .test_tmp/q6_dashboard_anchors_20261104/browser_tutorial/report.json y .test_tmp/q6_20261030/dashboard_anchors_build_20261104/build/report.json.

## Cómo repetir la validación

```powershell
python scripts/test_mepia_local.py --playwright 'RUTA_AL_MODULO_PLAYWRIGHT'
python scripts/test_mepia_local.py --phase tutorial --playwright 'RUTA_AL_MODULO_PLAYWRIGHT'
& .\scripts\iniciar_demo_mepia.ps1
```

El primer comando incluye el tutorial. El segundo ejecuta solo ese recorrido.
La demo abre en [127.0.0.1:3037](http://127.0.0.1:3037/__demo__).

## Evidencia local

El primer intento del recorrido general se detuvo porque la segunda pestaña
no tenía registrado el cierre del tutorial. Se corrigió ese paso de la prueba
y se repitió el recorrido completo.

- `.test_tmp/q6_revision_20261104/report.json` y sus informes por recorrido.
- `.test_tmp/q6_general_recheck_20261104/browser/e2e.json` (repetición).
- `.test_tmp/q6_tutorial_suite_20261104/browser_tutorial/report.json`.
- `.test_tmp/q6_demo_20261104/browser/report.json`.

Quedan pendientes la aceptación manual, la evaluación semántica del chat
y el ensayo con servicios reales. Q6 sigue como avance local sin commit
ni publicación.
