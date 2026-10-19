# Ejecución y fallo terminal de Layer 3

**Capa:** infraestructura de aplicación. **Anterior:** N13. **Terminal:** N14.
**Implementación:** `agents/layer3_execution.py`, `agents/n14_informe_final.py`.

## Input / Output

`execute_layer3(graph, initial_state)` recibe el grafo y sus identificadores de
corrida. Devuelve su estado si termina; ante `N14PersistenceError`, estado failed
y `final_response=None`. No llama modelos ni reconstruye el informe perdido.

## Criterios de aceptación

- WHEN N14 confirma el guardado THEN devuelve `layer3_status=completed`, respuesta
  y calidad del borrador sin cambios; conserva linaje y proveedor.
- WHEN falta DB o falla el guardado THEN lanza `N14PersistenceError` saneado;
  nunca entrega un informe como si estuviera guardado.
- WHEN la API o el encadenamiento N05 ejecuta Layer 3 THEN usa el mismo wrapper.
- WHEN N14 falla THEN el registro temporal conserva únicamente el ID de Layer 3,
  el padre Layer 2 y vencimiento. No conserva datos del negocio, secretos ni
  mensajes del proveedor.
- WHEN se consulta status de un fallo conocido THEN devuelve failed, nodo N14 y
  `report_persistence_failed` sin consultar DB. Resultado devuelve HTTP 503.
- WHEN el proxy consulta `/layer3/status/{layer2_run_id}` THEN se resuelve el
  fallo registrado o el último N10 de ese padre; usa su verdadero layer3_run_id.
- WHEN aún no inició Layer 3 para ese padre THEN 404, sin fingir finalización.
- WHEN comienza un reintento del mismo padre THEN elimina su fallo anterior
  para no ocultar un éxito posterior.
- WHEN pasan 30 minutos o se exceden 128 fallos THEN se eliminan entradas
  vencidas/antiguas; el acceso está protegido con lock entre hilos.

## Límites

Registro en memoria de un solo proceso: reiniciar lo pierde y otras réplicas
no lo comparten. No sustituye estados durables ni los controles de producción
pendientes del backend legado. No se intenta guardar una fila failed en una DB
que ya falló. Los fallos ajenos a N14 conservan su manejo existente.

## Evidencia

INC-048/049: prueba con DB caída, polling HTTP, padre distinto de ID final,
grafo LangGraph real con nodos generativos simulados y cadena automática N05.
Ver [preparación y límites](../../../docs/demo_video_paso_a_paso.md).

## Relacionados

- [N14](n14_informe_final.md), [API](api_layer3.md), [grafo](layer3_graph.md).
