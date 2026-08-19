"""
MEPIA Eval Runner — Nivel 3a: N05 CEO Orchestrator
Prueba S3 -> S4 -> N05 (síntesis con arquetipo + decisión de escalar a Layer 2)
sobre los 8 casos de ground truth.

Uso:
    python tests/eval_test/eval_runner_n05.py                # LLM real (gasta tokens)
    python tests/eval_test/eval_runner_n05.py --fake-llm      # cableado, sin red real

Requiere OPENAI_API_KEY si no se usa --fake-llm.

Qué valida:
    - Gatekeeper corre sin tronar sobre el mock (dormant esperado, no bloqueante)
    - S3 -> S4 -> N05 producen un OrchestratorResult válido
    - risk_level se calcula correctamente desde las anomalías de S4
    - La decisión de escalar (risk_level == "high") es coherente con lo esperado
      por caso: los casos con hallazgo "critical" en esperado_hallazgos deberían
      escalar; los que no, no.

Qué NO valida (fuera de alcance, ver mepia_v4_metricas_diseno.md decisión N05->N06):
    - Que Layer 2 (N06) se ejecute de verdad -- hoy solo se loguea el intent,
      N06 no está conectado a N05 todavía. Este harness no puede probar eso.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tests.eval_test.eval_runner import build_mock_store, MockDB  # noqa: E402
from agents.ceo_orchestrator import N05CEOOrchestrator  # noqa: E402

CASES_DIR = Path(__file__).resolve().parent


def _install_fake_llm() -> None:
    """Reemplaza openai.OpenAI por un cliente falso -- valida el cableado del
    pipeline sin gastar tokens ni requerir red real. Las frases/insights que
    genera son texto de relleno, no evalúan calidad de redacción."""
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
                    "copilot_phrase": "[FAKE LLM] relleno para probar cableado.",
                    "recommended_action": "[FAKE LLM] relleno para probar cableado.",
                }
            else:
                payload = {}
            return _FakeResponse(json.dumps(payload))

    openai.OpenAI = FakeOpenAI
    os.environ.setdefault("OPENAI_API_KEY", "fake-key-solo-cableado")


def _expects_escalation(case_data: dict) -> bool:
    """Un caso 'debería' escalar si algún hallazgo esperado es severidad critical.
    Es una aproximación IMPERFECTA -- ver hallazgo en la sesión del 2026-08-17:
    la severidad del ground truth (warning/critical, escala de negocio) y la
    severity de AnomalyItem que realmente dispara risk_level='high' (low/medium/
    high, juicio de S4 por anomalía individual) son dos escalas distintas que
    nunca se mapearon entre si. Esta funcion es solo una señal aproximada para
    comparar, no la fuente de verdad de si "debería" escalar de verdad."""
    hallazgos = (
        case_data.get("esperado_hallazgos")
        or case_data.get("esperado_hallazgos_con_desagregacion_por_responsable")
        or case_data.get("esperado_hallazgos_sin_desagregacion_por_responsable")
        or []
    )
    for h in hallazgos:
        if h.get("severidad") == "critical":
            return True
    return False


def run_n05_case(case_path: str, archetype: str = "Operative Genius") -> dict:
    case = json.load(open(case_path, encoding="utf-8"))
    db = MockDB(build_mock_store(case))
    orch = N05CEOOrchestrator(db)

    try:
        result = orch.run(
            business_id=case["input"]["negocio_id"],
            date=case["input"]["fecha"],
            archetype=archetype,
            escalate_to_parallel=True,
            temporalidad="short",
        )
    except Exception as exc:  # noqa: BLE001
        return {"case": case["id"], "error": str(exc)}

    forensic = result.sequential_results.forensic_report
    return {
        "case": case["id"],
        "pipeline_status": result.pipeline_status,
        "dormant_metrics": [d.get("metric") for d in result.dormant_metrics],
        "risk_level": forensic.get("risk_level"),
        "num_anomalies": len(forensic.get("anomalies", [])),
        "anomalies": forensic.get("anomalies", []),
        "num_insights": len(result.sequential_results.audit_insights),
        "escalation_triggered": result.escalation.triggered,
        "escalation_expected": _expects_escalation(case),
        "escalation_match": (
            result.escalation.triggered == _expects_escalation(case)
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fake-llm", action="store_true")
    parser.add_argument("--case", type=str, default=None)
    args = parser.parse_args()

    if args.fake_llm:
        _install_fake_llm()
    elif not os.environ.get("OPENAI_API_KEY"):
        print("[!] Nivel 3a requiere OPENAI_API_KEY, o usa --fake-llm para solo "
              "probar el cableado.")
        return

    pattern = str(CASES_DIR / "mepia_ground_truth_caso_*.json")
    if args.case:
        pattern = str(CASES_DIR / f"mepia_ground_truth_caso_{args.case}_*.json")

    print("\n=== MEPIA Eval Runner - Nivel 3a (N05 CEO Orchestrator) ===\n")
    results = []
    mismatches = 0
    for path in sorted(glob.glob(pattern)):
        r = run_n05_case(path)
        results.append(r)
        if "error" in r:
            print(f"[ERROR] {r['case']}: {r['error']}")
            continue
        match_str = "OK" if r["escalation_match"] else "MISMATCH"
        if not r["escalation_match"]:
            mismatches += 1
        print(
            f"[{match_str}] {r['case']}: risk_level={r['risk_level']} "
            f"anomalies={r['num_anomalies']} insights={r['num_insights']} "
            f"pipeline={r['pipeline_status']} "
            f"escalate(got={r['escalation_triggered']}, "
            f"expected={r['escalation_expected']})"
        )
        if r["dormant_metrics"]:
            print(f"         dormant: {r['dormant_metrics']}")
        if not r["escalation_match"] and r["anomalies"]:
            print(f"         --- anomalías generadas por S4 en {r['case']} ---")
            for a in r["anomalies"]:
                print(f"         [{a.get('severity')}] {a.get('type')} / "
                      f"{a.get('metric_origin')}: {a.get('description')}")
                print(f"                   impacto: {a.get('quantified_impact')}")

    print(f"\n=== Resumen: {len(results) - mismatches}/{len(results)} "
          f"coinciden en la decisión de escalar ===\n")


if __name__ == "__main__":
    main()


    