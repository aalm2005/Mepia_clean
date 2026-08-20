"""
MEPIA Eval Runner — Nivel 3b: Layer 3 completo (N10 -> N11 -> N13 -> N14)
Corre S3 -> S4 -> N05 (igual que Nivel 3a) y usa ese resultado para alimentar
el grafo real de Layer 3 (LangGraph), probando la consolidacion de hallazgos
que Nivel 2 no puede probar (S4 tiene prohibido consolidar).

Uso:
    python tests/eval_test/eval_runner_n3b.py --fake-llm   # solo cableado
    python tests/eval_test/eval_runner_n3b.py               # LLM real, gasta tokens

Requiere (ademas de lo que ya tenias para Nivel 3a):
    pip install langchain-anthropic langchain-openai langchain-core --break-system-packages
    OPENAI_API_KEY (Claude vía ANTHROPIC_API_KEY es opcional -- N11 cae a gpt-4o
    automaticamente si no esta o falla)
"""
from __future__ import annotations

import argparse
import asyncio
import glob
import json
import os
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tests.eval_test.eval_runner import build_mock_store, MockDB  # noqa: E402
from agents.ceo_orchestrator import N05CEOOrchestrator  # noqa: E402
from agents.layer3_graph import build_layer3_graph  # noqa: E402

CASES_DIR = Path(__file__).resolve().parent


def _install_fake_llm() -> None:
    """Mismo fake de Nivel 3a, para S4/N05. N11/N13/N14 usan LangChain (Claude
    + fallback GPT-4o) -- no se simulan aqui, requieren LLM real. Con
    --fake-llm, Layer 3 probablemente falle o produzca contenido de relleno
    en esos 3 nodos; sirve para confirmar que N10 (Python puro) arma bien el
    enriched_payload antes de gastar tokens reales en el resto."""
    import openai

    class _FakeMessage:
        def __init__(self, content: str) -> None:
            self.content = content

    class _FakeChoice:
        def __init__(self, content: str) -> None:
            self.message = _FakeMessage(content)

    class _FakeResponse:
        def __init__(self, content: str) -> None:
            self.choices = [_FakeChoice(content)]

    class FakeOpenAI:
        def __init__(self, api_key: str | None = None) -> None:
            self.chat = self

        @property
        def completions(self):
            return self

        def create(self, model, messages, response_format=None, **kwargs):
            schema_name = ""
            if response_format and "json_schema" in response_format:
                schema_name = response_format["json_schema"].get("name", "")
            if schema_name == "forensic_report":
                payload = {"anomalies": [], "evidence_sources": ["POS"]}
            elif schema_name == "audit_insight":
                payload = {
                    "copilot_phrase": "[FAKE LLM] relleno.",
                    "recommended_action": "[FAKE LLM] relleno.",
                }
            else:
                payload = {}
            return _FakeResponse(json.dumps(payload))

    openai.OpenAI = FakeOpenAI
    os.environ.setdefault("OPENAI_API_KEY", "fake-key-solo-cableado")


def _run_n05(case: dict, db: MockDB) -> dict:
    """Igual que eval_runner_n05.py -- corre S3->S4->N05 y regresa sequential_results."""
    orch = N05CEOOrchestrator(db)
    result = orch.run(
        business_id=case["input"]["negocio_id"],
        date=case["input"]["fecha"],
        archetype="Operative Genius",
        escalate_to_parallel=True,
        temporalidad="short",
    )
    forensic = result.sequential_results.forensic_report
    print(f"    [DEBUG] N05 forensic_report: risk_level={forensic.get('risk_level')} "
          f"anomalies={len(forensic.get('anomalies', []))} "
          f"insights={len(result.sequential_results.audit_insights)}")
    return {
        "forensic_report": forensic,
        "insights": [
            i.model_dump(mode="json") for i in result.sequential_results.audit_insights
        ],
    }


def _build_initial_state(case: dict, db: MockDB, seq_ctx: dict) -> dict:
    """Arma Layer3State con el mismo patron que usa api/main.py, en modo
    aislado (pgr minimo, sin Layer 2 real -- N06 no esta conectado, ver
    mepia_v4_metricas_diseno.md decision #16)."""
    layer3_run_id = str(uuid4())
    return {
        "layer3_run_id": layer3_run_id,
        "layer2_run_id": f"isolated_{uuid4()}",
        "sequential_run_id": f"isolated_{uuid4()}",
        "business_id": case["input"]["negocio_id"],
        "date": case["input"]["fecha"],
        "archetype": "Operative Genius",
        "enriched_payload": {},
        "draft_report": None,
        "intentos_critico": 0,
        "feedback_critico": None,
        "historial_feedback": [],
        "tipos_falla_critico": [],
        "draft_status": "pending",
        "audit_results": [],
        "final_response": None,
        "_db": db,
        "_memory_service": None,
        "_parallel_gather_result": {
            "temporalidad": "short",
            "sequential_context": {
                "forensic_report": seq_ctx["forensic_report"],
                "insights": seq_ctx["insights"],
                "context_tags": {},
            },
            "node_results": [],
        },
    }


async def run_n3b_case(case_path: str) -> dict:
    case = json.load(open(case_path, encoding="utf-8"))
    db = MockDB(build_mock_store(case))

    seq_ctx = _run_n05(case, db)
    initial_state = _build_initial_state(case, db, seq_ctx)

    graph = build_layer3_graph(memory_service=None)
    try:
        final_state = await graph.ainvoke(initial_state)
    except Exception as exc:  # noqa: BLE001
        return {"case": case["id"], "error": f"{type(exc).__name__}: {exc}"}

    final_response = final_state.get("final_response") or {}
    ep = final_state.get("enriched_payload") or {}
    ep_forensic = ep.get("forensic_report") or {}
    print(f"    [DEBUG] enriched_payload tras N10: risk_level={ep_forensic.get('risk_level')} "
          f"anomalies={len(ep_forensic.get('anomalies', []))} "
          f"insights={len(ep.get('audit_insights', []))}")
    return {
        "case": case["id"],
        "draft_status": final_state.get("draft_status"),
        "intentos_critico": final_state.get("intentos_critico"),
        "tipos_falla_critico": final_state.get("tipos_falla_critico"),
        "historial_feedback": final_state.get("historial_feedback"),
        "report_status": final_response.get("status"),
        "has_warnings": final_response.get("has_warnings"),
        "report_markdown_preview": (final_response.get("report_markdown") or "")[:400],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fake-llm", action="store_true")
    parser.add_argument("--case", type=str, default=None)
    args = parser.parse_args()

    if args.fake_llm:
        _install_fake_llm()
    elif not os.environ.get("OPENAI_API_KEY"):
        print("[!] Nivel 3b requiere OPENAI_API_KEY, o usa --fake-llm para solo "
              "probar el cableado de N10.")
        return

    pattern = str(CASES_DIR / "mepia_ground_truth_caso_*.json")
    if args.case:
        pattern = str(CASES_DIR / f"mepia_ground_truth_caso_{args.case}_*.json")

    print("\n=== MEPIA Eval Runner - Nivel 3b (Layer 3: N10->N11->N13->N14) ===\n")

    async def _run_all():
        for path in sorted(glob.glob(pattern)):
            r = await run_n3b_case(path)
            if "error" in r:
                print(f"[ERROR] {r['case']}: {r['error']}")
                continue
            print(
                f"[{r['case']}] draft_status={r['draft_status']} "
                f"intentos_critico={r['intentos_critico']} "
                f"tipos_falla={r['tipos_falla_critico']} "
                f"report_status={r['report_status']} "
                f"warnings={r['has_warnings']}"
            )
            print(f"    preview: {r['report_markdown_preview']!r}")
            if r.get("historial_feedback"):
                print(f"    --- feedback de N13 (por qué rechazó) ---")
                for i, fb in enumerate(r["historial_feedback"], 1):
                    print(f"    [{i}] {fb}")

    asyncio.run(_run_all())


if __name__ == "__main__":
    main()