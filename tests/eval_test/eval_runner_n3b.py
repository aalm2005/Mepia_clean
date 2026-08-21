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

# ---------------------------------------------------------------------------
# Chequeo de contenido: ¿el reporte final MENCIONA cada hallazgo esperado?
# Palabras clave por flag -- igual que _FLAG_TO_METRIC_HINTS de Nivel 2, pero
# para buscar en texto libre (el markdown de N14), no en metric_origin
# estructurado. Cualquier keyword del grupo presente cuenta como cubierto
# (OR, no AND) -- ver nota sobre "descuentos_cortesias_concentrados": tras la
# cortesía permitida (sesión de hoy), M-03 puede ya no tener anomalía de
# cortesía real, solo de descuento -- exigir ambas palabras penalizaría un
# reporte correcto. "insumo_critico_multi_senal" sí exige >=2 grupos, porque
# ese hallazgo es específicamente sobre consolidar varias señales.
# ---------------------------------------------------------------------------
_FLAG_TO_TEXT_KEYWORDS: dict[str, list[list[str]]] = {
    "faltante_de_caja": [["varianza", "efectivo", "caja"]],
    "sobrante_de_caja": [["varianza", "efectivo", "caja"]],
    "reprint_rate_alto": [["reimpres"]],
    "cancelacion_post_comanda_alta": [["cancelac"]],
    "patron_fraude_operativo": [["cancelac", "reimpres"]],
    "erosion_margen_canal_delivery": [["comisi", "delivery"]],
    "merma_excesiva": [["merma", "desperdici"]],
    "merma_inventario": [["merma", "desperdici"]],
    "descuentos_cortesias_concentrados": [["descuento", "cortes"]],
    "descuentos_zona_gris": [["descuento", "cortes"]],
    "inflacion_proveedor": [["inflaci"]],
    "stock_bajo": [["stock", "inventario"]],
    "insumo_critico_multi_senal": [
        ["merma", "desperdici"],
        ["stock", "inventario", "días", "dias"],
    ],
    "patron_concentrado_en_responsable": [["cancelac", "reimpres"]],
}


def _get_hallazgos(case_data: dict) -> list[dict]:
    """Igual que _expects_escalation de eval_runner_n05.py -- soporta los 3
    formatos de llave que existen en los 8 casos (caso_03 usa uno distinto)."""
    return (
        case_data.get("esperado_hallazgos")
        or case_data.get("esperado_hallazgos_con_desagregacion_por_responsable")
        or case_data.get("esperado_hallazgos_sin_desagregacion_por_responsable")
        or []
    )


def _report_covers_hallazgo(report_text: str, hallazgo: dict) -> bool:
    """¿El reporte final menciona este hallazgo esperado? Requiere >=1
    keyword de CADA grupo definido para ese flag (normalmente 1 solo grupo;
    insumo_critico_multi_senal tiene 2, exigiendo ambas señales presentes)."""
    flag = hallazgo.get("flag", "")
    groups = _FLAG_TO_TEXT_KEYWORDS.get(flag)
    if not groups:
        return False  # flag sin keywords definidas -- no se puede verificar, cuenta como no cubierto
    text_lower = report_text.lower()
    return all(
        any(kw in text_lower for kw in group)
        for group in groups
    )


def check_report_content(report_text: str, case_data: dict) -> dict:
    """Compara el reporte final completo contra esperado_hallazgos del caso."""
    hallazgos = _get_hallazgos(case_data)
    found = []
    missing = []
    for h in hallazgos:
        flag = h.get("flag", "?")
        if _report_covers_hallazgo(report_text, h):
            found.append(flag)
        else:
            missing.append(flag)
    return {"expected": len(hallazgos), "found": found, "missing": missing}


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
    report_text = final_response.get("report_markdown") or ""
    content_check = check_report_content(report_text, case)

    return {
        "case": case["id"],
        "draft_status": final_state.get("draft_status"),
        "intentos_critico": final_state.get("intentos_critico"),
        "tipos_falla_critico": final_state.get("tipos_falla_critico"),
        "historial_feedback": final_state.get("historial_feedback"),
        "report_status": final_response.get("status"),
        "has_warnings": final_response.get("has_warnings"),
        "report_markdown_preview": report_text[:400],
        "content_check": content_check,
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

    async def _run_case_with_retry(path: str, max_retries: int = 5) -> dict:
        """Reintenta con espera si OpenAI regresa 429 (rate limit) -- 8 casos
        seguidos por S4+N05+N11(+reintentos)+N14 puede rebasar fácil un tier
        con límite bajo de tokens por minuto."""
        for intento in range(max_retries):
            try:
                return await run_n3b_case(path)
            except Exception as exc:  # noqa: BLE001
                if "RateLimitError" in type(exc).__name__ or "rate_limit" in str(exc).lower():
                    espera = 15 * (intento + 1)
                    print(f"    [rate limit] esperando {espera}s antes de reintentar...")
                    await asyncio.sleep(espera)
                    continue
                return {"case": Path(path).stem, "error": f"{type(exc).__name__}: {exc}"}
        return {"case": Path(path).stem, "error": "rate limit persistente tras reintentos"}

    async def _run_all():
        total_expected = 0
        total_found = 0
        for path in sorted(glob.glob(pattern)):
            r = await _run_case_with_retry(path)
            if "error" in r:
                print(f"[ERROR] {r['case']}: {r['error']}")
                continue
            # Pausa breve entre casos para no rebasar tokens-por-minuto en
            # tiers con límite bajo.
            await asyncio.sleep(5)
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

            cc = r["content_check"]
            total_expected += cc["expected"]
            total_found += len(cc["found"])
            status = "OK" if not cc["missing"] else "FALTAN"
            print(
                f"    --- contenido vs esperado_hallazgos: [{status}] "
                f"{len(cc['found'])}/{cc['expected']} encontrados ---"
            )
            if cc["found"]:
                print(f"        encontrados: {cc['found']}")
            if cc["missing"]:
                print(f"        faltan: {cc['missing']}")

        recall = (total_found / total_expected * 100) if total_expected else 0
        print(f"\n=== Contenido del reporte final: {total_found}/{total_expected} "
              f"hallazgos mencionados ({recall:.1f}%) ===\n")

    asyncio.run(_run_all())


if __name__ == "__main__":
    main()