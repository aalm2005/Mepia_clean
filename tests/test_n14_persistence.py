"""Guardado N14, grafo real y polling ante DB caída. Sin red/modelos."""
import asyncio
import importlib
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.n14_informe_final import N14PersistenceError, n14_informe_final_node
from agents import layer3_execution as execution


class CaptureDB:
    def __init__(self, fail=False):
        self.fail, self.rows = fail, []

    def table(self, name):
        assert name == "audit_results"
        return self

    def insert(self, row):
        self.rows.append(row)
        return self

    def execute(self):
        if self.fail:
            raise RuntimeError("synthetic-secret-must-not-leak")
        return SimpleNamespace(data=[self.rows[-1]])


def state(db, status="approved"):
    return {"layer3_run_id": str(uuid4()), "layer2_run_id": str(uuid4()),
            "sequential_run_id": str(uuid4()), "source_s3_result_id": str(uuid4()),
            "business_id": str(uuid4()), "date": "2026-10-14",
            "archetype": "Operative Genius", "enriched_payload": {},
            "draft_report": {"executive_summary": "Resumen sintético",
                             "operational_narrative": "Narrativa sintética",
                             "pragmatic_actions": [], "model_used": "OpenAI simulado"},
            "draft_status": status, "intentos_critico": 0,
            "historial_feedback": ["Advertencia sintética"] if status.endswith("warning") else [],
            "audit_results": [], "final_response": None, "_db": db}


@pytest.mark.parametrize("status", ["approved", "approved_with_warning"])
def test_success_requires_persistence_and_preserves_quality_and_lineage(status):
    db=CaptureDB(); original=state(db,status)
    result=n14_informe_final_node(original)
    assert result["layer3_status"] == "completed"
    assert result["final_response"]["status"] == status
    assert result["final_response"]["has_warnings"] == status.endswith("warning")
    assert len(db.rows) == 1
    row=db.rows[0]
    assert row["source_s3_result_id"] == original["source_s3_result_id"]
    assert row["result_data"]["model_used"] == "OpenAI simulado"
    assert row["result_data"]["executive_summary"] == "Resumen sintético"
    assert row["node_status"] == "success"


@pytest.mark.parametrize("db", [None, CaptureDB(fail=True)])
def test_no_final_response_when_persistence_fails(db):
    with pytest.raises(N14PersistenceError) as error:
        n14_informe_final_node(state(db))
    assert "synthetic-secret" not in str(error.value)


@pytest.mark.parametrize("fail", [False, True])
def test_compiled_graph_retains_terminal_status_and_records_safe_failure(monkeypatch,fail):
    import agents.layer3_graph as graph_module
    monkeypatch.setattr(graph_module,"n10_context_builder_node",lambda s:{})
    monkeypatch.setattr(graph_module,"n11_consultor_node",lambda s:{})
    monkeypatch.setattr(graph_module,"make_n13_node",lambda memory:lambda s:{"draft_status":"approved"})
    initial=state(CaptureDB(fail=fail))
    graph=graph_module.build_layer3_graph(None)
    result=asyncio.run(execution.execute_layer3(graph,initial))
    assert result["layer3_status"] == ("failed" if fail else "completed")
    failure=execution.get_layer3_failure(initial["layer3_run_id"])
    if fail:
        assert result["final_response"] is None and failure["status"] == "failed"
        assert "synthetic-secret" not in str(failure)
    else:
        assert failure is None and result["final_response"]["status"] == "approved"


def test_failure_registry_expires_and_has_bounded_capacity(monkeypatch):
    monkeypatch.setattr(execution,"_FAILURE_CAPACITY",2)
    monkeypatch.setattr(execution,"_FAILURE_TTL",10)
    clock=[100.0];monkeypatch.setattr(execution,"monotonic",lambda:clock[0])
    monkeypatch.setattr(execution,"_failures",execution.OrderedDict())
    graph=SimpleNamespace(ainvoke=AsyncMock(side_effect=N14PersistenceError()))
    for key in ("one","two","three"):
        asyncio.run(execution.execute_layer3(graph,{"layer3_run_id":key}))
    assert execution.get_layer3_failure("one") is None
    assert execution.get_layer3_failure("three")["status"] == "failed"
    clock[0]=111
    assert execution.get_layer3_failure("three") is None and not execution._failures


def test_retry_of_same_parent_does_not_inherit_old_failure():
    parent_id=str(uuid4());old_id=str(uuid4());new_id=str(uuid4())
    failed=SimpleNamespace(ainvoke=AsyncMock(side_effect=N14PersistenceError()))
    asyncio.run(execution.execute_layer3(failed,{'layer3_run_id':old_id,'layer2_run_id':parent_id}))
    assert execution.get_layer3_failure_by_parent(parent_id)['layer3_run_id']==old_id
    success=SimpleNamespace(ainvoke=AsyncMock(return_value={'layer3_status':'completed'}))
    result=asyncio.run(execution.execute_layer3(success,{'layer3_run_id':new_id,'layer2_run_id':parent_id}))
    assert result['layer3_status']=='completed'
    assert execution.get_layer3_failure_by_parent(parent_id) is None
    assert execution.get_layer3_failure(old_id) is None


def load_synthetic_api(monkeypatch):
    config=SimpleNamespace(settings=SimpleNamespace(
        SUPABASE_URL="https://synthetic-project.supabase.co", SUPABASE_SERVICE_ROLE_KEY="synthetic-key",
        SUPABASE_JWT_ALGORITHM="HS256",SUPABASE_JWT_SECRET=SimpleNamespace(get_secret_value=lambda:""),
        CHAT_GEMINI_API_KEY=SimpleNamespace(get_secret_value=lambda:""),CHAT_MODEL="synthetic",
        ENVIRONMENT="dev",OPENAI_API_KEY="",ANTHROPIC_API_KEY=""))
    monkeypatch.setitem(sys.modules,"core.config",config)
    return importlib.import_module("api.main")


def test_http_polling_reports_failure_even_when_database_is_unavailable(monkeypatch):
    api=load_synthetic_api(monkeypatch)
    monkeypatch.setattr(api,"get_supabase",lambda:pytest.fail("No consultar DB para fallo registrado"))
    graph=SimpleNamespace(ainvoke=AsyncMock(side_effect=N14PersistenceError()))
    run_id=str(uuid4());parent_id=str(uuid4())
    asyncio.run(execution.execute_layer3(graph,{"layer3_run_id":run_id,"layer2_run_id":parent_id}))
    app=FastAPI();app.get("/status/{layer3_run_id}")(api.layer3_status)
    app.get("/result/{layer3_run_id}")(api.layer3_result)
    app.get("/layer3/status/{layer2_run_id}")(api.layer3_status_by_parent)
    client=TestClient(app)
    status=client.get("/status/"+run_id)
    assert status.status_code == 200 and status.json()["status"] == "failed"
    result=client.get("/result/"+run_id)
    assert result.status_code == 503
    assert result.json()["detail"]["error"] == "report_persistence_failed"
    assert "synthetic-secret" not in status.text+result.text
    parent=client.get('/layer3/status/'+parent_id)
    assert parent.status_code==200 and parent.json()['layer3_run_id']==run_id
    assert parent.json()['status']=='failed'


def test_parent_status_resolves_actual_layer3_id(monkeypatch):
    api=load_synthetic_api(monkeypatch)
    parent_id,run_id=str(uuid4()),str(uuid4())
    from tests.test_video_demo import DB
    db=DB();db.store['audit_results']=[
        {'node_id':'N10','created_at':'2026-10-15T10:00:00Z','result_data':{'layer2_run_id':parent_id,'layer3_run_id':run_id}},
        {'node_id':'N14','created_at':'2026-10-15T10:01:00Z','result_data':{'layer3_run_id':run_id,'draft_status':'approved'}}]
    monkeypatch.setattr(api,'get_supabase',lambda:db)
    app=FastAPI();app.get('/layer3/status/{layer2_run_id}')(api.layer3_status_by_parent)
    client=TestClient(app);response=client.get('/layer3/status/'+parent_id)
    assert response.status_code==200 and response.json()['layer3_run_id']==run_id
    assert response.json()['status']=='completed'
    assert client.get('/layer3/status/'+str(uuid4())).status_code==404


def test_ceo_automatic_chain_uses_same_failure_reporting(monkeypatch):
    import agents.ceo_orchestrator as ceo
    import agents.layer3_graph as graphs
    from agents.parallel_orchestrator import Layer2RunPayload, SequentialContext, ContextTags
    captured=[]
    async def failed_graph(initial):
        captured.append(initial["layer3_run_id"])
        raise N14PersistenceError()
    monkeypatch.setattr(graphs,"build_layer3_graph",lambda memory:SimpleNamespace(ainvoke=failed_graph))
    monkeypatch.setattr(ceo,"N06ParallelOrchestrator",lambda db:SimpleNamespace(run=AsyncMock(
        return_value=SimpleNamespace(gather_status="success",node_results=[]))))
    obj=object.__new__(ceo.N05CEOOrchestrator);obj._db=CaptureDB()
    bid=str(uuid4());payload=Layer2RunPayload(layer2_run_id=str(uuid4()),sequential_run_id=str(uuid4()),
        source_s3_result_id=str(uuid4()),business_id=bid,date="2026-10-14",archetype="Operative Genius",
        temporalidad="short",sequential_context=SequentialContext(business_id=bid,active_metrics=[],
        calc_results=[],forensic_report={},insights=[],context_tags=ContextTags()))
    asyncio.run(obj._run_layer2_then_layer3(payload))
    assert len(captured)==1 and execution.get_layer3_failure(captured[0])["status"]=="failed"
