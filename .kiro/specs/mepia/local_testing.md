# Pruebas locales y demostración sin proveedores reales

**Capa:** infraestructura de validación. Corte 26-oct-2026, categoría C solicitada.
No es una fase nueva de N15 ni reabre INC-050–057.

## Input / Output

`scripts/test_mepia_local.py` ejecuta suites por secciones con datos/Auth/SDK
simulados y salida nueva en `.test_tmp`. `scripts/start_mepia_demo.py` sirve la
interfaz existente con base de prueba en memoria. No modifica api.main/chat_app.

En Q6, `--phase browser` y `--phase all` incluyen el recorrido guiado en
escritorio y móvil. `--phase tutorial` ejecuta solo esa comprobación.
[Resultados de la integración](../../../docs/pruebas_mepia_q6_20261104.md).

## User Stories

- Como usuario, quiero probar pantallas y análisis ficticios sin gastar tokens.
- Como evaluador, quiero separar automatización de aceptación humana/real.
- Como desarrollador, quiero conservar resultados anteriores y datos compartidos.

## Acceptance Criteria

- WHEN se ejecuta la suite THEN bloquea conexiones externas de Python/Node,
  reemplaza credenciales del entorno y desactiva la integración Supabase opt-in.
- WHEN se inicia demo THEN solo escucha loopback: API 8025, Next 3036 y gateway
  3037; rechaza puertos ocupados sin detener servicios ajenos.
- WHEN se consulta historial/chat/ajustes THEN usa routers reales, JWT ficticio
  validado y propietario de la base en memoria. Conversación usa SDK simulado.
- WHEN se simula carga/análisis THEN el gateway reenvía Bearer a endpoints de
  demostración; extrae documentos localmente y guarda escenarios prefabricados
  en memoria. No acredita seguridad de endpoints legados ni análisis financiero real.
- WHEN se muestra demo THEN banda y nombres identifican datos ficticios;
  escenarios: completado, cero, anomalía, insuficiente y fallido.
- WHEN se reinicia/detiene THEN se pierde solo memoria de demo; no modifica
  documentos originales, configuración privada ni SQL/Storage externos.
- WHEN se verifica THEN guarda evidencia nueva y compara huellas previas;
  no suma controles/capas/subpruebas como una cantidad única de casos.
- WHEN falta evaluación humana/proveedor/DB real THEN conserva ese pendiente;
  no recalifica resultados históricos ni consume modelos para cerrarlo.

## Edge Cases

- Proxy de demo separado de la aplicación normal: entrar por 3037.
- Selección antigua tras reset: error legítimo y elegir otra corrida.
- Los importes prefabricados no se derivan de documentos cargados.
- Cero válido y ausencia de cálculo siguen contratos de historial existentes.
- Caché/generados Next se aíslan y restauran; los procesos propios se detienen
  al cerrar el lanzador, sin limpiar carpetas de evidencia.

## Archivos relacionados de este nodo

- [Plan y lista manual](../../../docs/plan_pruebas_mepia.md).
- [Informe del corte](../../../docs/pruebas_mepia_20261026.md).
- `tests/local_network_guard.py`, `tests/local_network_guard.cjs`.
- `tests/mepia_demo_server.py`, `tests/mepia_demo_gateway.py`.
- `tests/test_mepia_demo.py`, `tests/mepia_demo_e2e.cjs`.
- [Historial](analysis_history.md), [evaluación N15](n15_chat_consulta.md).
