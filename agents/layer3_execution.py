"""Ejecución compartida: conserva fallos N14 sin depender de una DB caída.

Registro temporal del proceso, acotado a 128 ejecuciones y 30 minutos.
Solo conserva identificadores de corrida; nunca reportes, claves o excepciones.
"""
from collections import OrderedDict
from threading import RLock
from time import monotonic

from agents.n14_informe_final import N14PersistenceError

_failures: OrderedDict[str, tuple[float, str | None]] = OrderedDict()
_lock = RLock()
_FAILURE_TTL = 30 * 60
_FAILURE_CAPACITY = 128
_MESSAGE = "No fue posible guardar el informe final. Intenta de nuevo."


def _expire(now):
    while _failures and next(iter(_failures.values()))[0] <= now:
        _failures.popitem(last=False)


def get_layer3_failure(run_id: str):
    with _lock:
        _expire(monotonic())
        if run_id not in _failures:
            return None
    return {"layer3_run_id": run_id, "status": "failed",
            "current_node": "n14_informe_final",
            "error_code": "report_persistence_failed", "message": _MESSAGE}


def get_layer3_failure_by_parent(parent_id: str):
    with _lock:
        _expire(monotonic())
        for run_id, (_, parent) in reversed(_failures.items()):
            if parent == parent_id:
                return get_layer3_failure(run_id)
    return None


async def execute_layer3(graph, initial_state):
    run_id = initial_state["layer3_run_id"]
    parent_id = initial_state.get("layer2_run_id")
    with _lock:
        _expire(monotonic())
        # Un reintento del mismo padre no debe heredar el fallo anterior.
        for old_id, (_, old_parent) in list(_failures.items()):
            if old_id == run_id or (parent_id is not None and old_parent == parent_id):
                _failures.pop(old_id, None)
    try:
        return await graph.ainvoke(initial_state)
    except N14PersistenceError:
        with _lock:
            _expire(monotonic())
            _failures[run_id] = (monotonic() + _FAILURE_TTL, parent_id)
            _failures.move_to_end(run_id)
            while len(_failures) > _FAILURE_CAPACITY:
                _failures.popitem(last=False)
        return {"layer3_status": "failed", "final_response": None}
