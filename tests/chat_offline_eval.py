"""Evaluación reproducible y de solo lectura del nodo N15.

Los controles mecánicos no sustituyen la revisión humana del significado de las
afirmaciones. La salida conserva ambos denominadores por separado.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Protocol
from urllib.request import Request, urlopen
from uuid import NAMESPACE_URL, uuid5

from agents.chat_conversation import ChatConversationNode
from agents.chat_grounding import ChatGroundingPacket, ChatGroundingService
from agents.chat_response import (
    ChatJsonCompletionAdapter, ChatModelDraft, ChatReviewRequest, ChatReviewResult,
    ChatWritingRequest, _failure_diagnostics,
)


FIXTURES = Path(__file__).parent / "fixtures" / "chat_offline_cases.json"
DIAGNOSTIC_CASES = frozenset({"same_day_result_and_report", "arithmetic_division"})


class SyntheticDiagnosticCompletion:
    """Traza opt-in de objetos validados para dos casos del fixture sintético.

    Envuelve el callback sin añadir llamadas ni modificar sus solicitudes,
    respuestas o errores. Nunca guarda cuerpos HTTP, cabeceras o excepciones.
    No se utiliza en el nodo N15 de producto ni como revisión independiente.
    """

    def __init__(self, complete: Callable[[str, str, dict[str, Any]], Any], *,
                 secrets: tuple[str, ...] = ()) -> None:
        self._complete = complete
        self._secrets = tuple(secret for secret in secrets if secret)
        self._case_id: str | None = None
        self._records: list[dict[str, Any]] = []

    def begin_case(self, case_id: str) -> None:
        if case_id not in DIAGNOSTIC_CASES:
            raise ValueError("La traza solo admite los dos casos sintéticos de diagnóstico")
        self._case_id = case_id

    def __call__(self, system: str, data: str, schema: dict[str, Any]) -> Any:
        title = schema.get("title")
        if self._case_id is None or len(self._records) >= 4 or title not in (
                "ChatModelDraft", "ChatReviewResult"):
            raise ValueError("Llamada fuera del diagnóstico sintético acotado")
        phase = "draft" if title == "ChatModelDraft" else "review"
        input_type = ChatWritingRequest if phase == "draft" else ChatReviewRequest
        output_type = ChatModelDraft if phase == "draft" else ChatReviewResult
        parsed_input = input_type.model_validate(json.loads(data)["untrusted_data"])
        entry = {"case_id": self._case_id, "phase": phase,
                 "input": parsed_input.model_dump(mode="json"),
                 "output": None, "diagnostics": []}
        self._records.append(entry)
        try:
            raw = self._complete(system, data, schema)
        except Exception as error:
            entry["diagnostics"] = _failure_diagnostics(phase, error)
            raise
        try:
            entry["output"] = output_type.model_validate(raw).model_dump(mode="json")
        except Exception as error:
            entry["diagnostics"] = _failure_diagnostics(phase, error)
        return raw

    def records(self) -> list[dict[str, Any]]:
        def sanitized(value: Any) -> Any:
            if isinstance(value, str):
                for secret in self._secrets:
                    value = value.replace(secret, "[REDACTED]")
                return value
            if isinstance(value, list):
                return [sanitized(item) for item in value]
            if isinstance(value, dict):
                return {sanitized(key): sanitized(item) for key, item in value.items()}
            return value
        return sanitized(self._records)


def fixture_id(label: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"mepia-chat-offline:{label}"))


class _Result:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _Query:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.filters: list[tuple[str, Any]] = []
        self.orders: list[tuple[str, bool]] = []
        self.allowed_statuses: set[str | None] | None = None
        self.max_rows: int | None = None

    def select(self, _fields: str) -> _Query:
        return self

    def eq(self, field: str, value: Any) -> _Query:
        self.filters.append((field, value))
        return self

    def or_(self, expression: str) -> _Query:
        if expression != "node_status.is.null,node_status.in.(success,completed)":
            raise ValueError("Filtro de estados no reconocido")
        self.allowed_statuses = {None, "success", "completed"}
        return self

    def order(self, field: str, desc: bool = False) -> _Query:
        self.orders.append((field, desc))
        return self

    def limit(self, count: int) -> _Query:
        self.max_rows = count
        return self

    def execute(self) -> _Result:
        rows = [row for row in self.rows if all(row.get(k) == v for k, v in self.filters)]
        if self.allowed_statuses is not None:
            rows = [row for row in rows if row.get("node_status") in self.allowed_statuses]
        for field, desc in reversed(self.orders):
            rows.sort(key=lambda row: str(row.get(field) or ""), reverse=desc)
        return _Result(rows[:self.max_rows] if self.max_rows is not None else rows)


class _FixtureDB:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def table(self, name: str) -> _Query:
        if name != "audit_results":
            raise ValueError("La evaluación solo acepta audit_results sintético")
        return _Query(self.rows)


def load_fixture(path: Path = FIXTURES) -> dict[str, Any]:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    if fixture.get("schema_version") != 1:
        raise ValueError("Versión del conjunto de evaluación desconocida")
    case_ids = [case["id"] for case in fixture["cases"]]
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("Identificadores de casos duplicados")
    return fixture


def build_packet(fixture: dict[str, Any], case: dict[str, Any]) -> ChatGroundingPacket:
    rows = []
    for raw in fixture["datasets"][case["dataset"]]:
        row = dict(raw)
        row["id"] = fixture_id(raw["id"])
        row["source_s3_result_id"] = fixture_id(raw.get("source_s3_result_id", raw["id"])) if (
            raw["node_id"] == "S3" or raw.get("source_s3_result_id")
        ) else None
        rows.append(row)
    return ChatGroundingService(_FixtureDB(rows)).build_packet(
        case["packet_business_id"], case.get("requested_date")
    )


class SemanticReviewer(Protocol):
    def review(self, case: dict[str, Any], part_index: int, answer_part: Any) -> dict[str, Any]: ...


def review_digest(part: Any) -> str:
    claims = [{"text": claim.text, "sources": [
        {"path": source.path, "value": source.value,
         "evidence": [ref.model_dump(mode="json") for ref in source.evidence]}
        for source in claim.sources]} for claim in part.claims]
    payload = {"kind": part.kind, "status": part.status, "message": part.message,
               "missing_data": part.missing_data, "claims": claims}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


class FileSemanticReviewer:
    """Carga juicios humanos independientes atados a texto y fuentes exactos."""
    def __init__(self, path: Path) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1:
            raise ValueError("Versión de revisión desconocida")
        self.entries = {(item["case_id"], item["part_index"]): item for item in data["reviews"]}
        if len(self.entries) != len(data["reviews"]):
            raise ValueError("Juicios semánticos duplicados")

    def review(self, case: dict[str, Any], part_index: int, answer_part: Any) -> dict[str, Any]:
        item = self.entries.get((case["id"], part_index))
        if item is None:
            return {"status": "not_reviewed", "reason": "sin juicio independiente"}
        if item.get("digest") != review_digest(answer_part):
            return {"status": "not_reviewed", "reason": "juicio obsoleto: cambió texto o fuente"}
        required = ("supported", "addresses_question", "correct_scope", "no_calculation")
        if any(type(item.get(field)) is not bool for field in required) or not item.get("reviewer"):
            return {"status": "not_reviewed", "reason": "juicio incompleto"}
        passed = all(item[field] for field in required)
        return {"status": "pass" if passed else "fail", "reason": item.get("reason", ""),
                "reviewer": item["reviewer"], "digest": item["digest"],
                "dimensions": {field: item[field] for field in required}}


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(ok), "detail": detail if not ok else ""}


def _part_checks(case: dict[str, Any], expected: dict[str, Any], part: Any,
                 packet: ChatGroundingPacket, index: int) -> list[dict[str, Any]]:
    checks = [
        _check("classification", part.kind == expected["kind"], f"esperado={expected['kind']}, real={part.kind}"),
        _check("status", part.status == expected["status"], f"esperado={expected['status']}, real={part.status}"),
        _check("answerable_coverage", not expected["answerable"] or
               (part.status == "ok" and part.generation_status == "validated" and bool(part.claims)),
               f"generación={part.generation_status}; claims={len(part.claims)}"),
        _check("no_calculation", part.kind != "calculation" or
               (part.status == "not_allowed" and not part.data and not part.evidence), "el cálculo produjo datos"),
        _check("missing_or_outside", part.status == "ok" or
               (not part.data and (part.status == "not_found" or not part.evidence)),
               "una parte no respondible expuso datos o evidencia"),
    ]
    expected_sources = expected.get("evidence", [])
    actual_sources = [ref.audit_result_id for ref in part.evidence]
    checks.append(_check("source_lineage", actual_sources == [fixture_id(label) for label in expected_sources],
                         f"esperado={expected_sources}; real={actual_sources}"))
    metadata_ok = all(ref.date == packet.resolved_date and (
        (ref.node_id == "S3" and ref.audit_result_id == packet.source_s3_result_id) or
        (ref.node_id == "N14" and ref.source_s3_result_id == packet.source_s3_result_id)
    ) for ref in part.evidence)
    checks.append(_check("evidence_metadata", metadata_ok, "fecha o raíz S3 incorrecta en referencia"))
    if part.generation_status == "validated" and expected_sources and part.status == "ok":
        expected_ids = {fixture_id(label) for label in expected_sources}
        cited_ok = bool(part.claims) and all(
            {ref.audit_result_id for ref in claim.evidence} == expected_ids for claim in part.claims)
        checks.append(_check("claim_evidence", cited_ok, "una afirmación no cita la ejecución esperada"))
    checks.append(_check("date", packet.resolved_date == expected.get("resolved_date", packet.resolved_date),
                         f"fecha={packet.resolved_date}"))
    if expected.get("value") is not None:
        metrics = part.data.get("metrics", [])
        matching = [m for m in metrics if m.get("metric") == expected["metric"]]
        checks.append(_check("source_value_unit", len(matching) == 1 and
                             matching[0].get("value") == expected["value"] and
                             matching[0].get("unit") == expected["unit"],
                             f"métrica={expected['metric']}; valor/unidad={matching}"))
        if "metric_status" in expected:
            checks.append(_check("source_metric_status", len(matching) == 1 and
                                 matching[0].get("status") == expected["metric_status"],
                                 f"métrica={expected['metric']}; estado={matching}"))
        if part.generation_status == "validated":
            number_sources = [source for claim in part.claims for source in claim.sources
                              if source.path.endswith("/value") and source.value == expected["value"]]
            checks.append(_check("claimed_value_source", bool(number_sources), "la cifra no cita su campo"))
            checks.append(_check("claimed_value_literal", str(expected["value"]) in part.message,
                                 "la redacción omitió el literal esperado"))
            unit_aliases = {"MXN": ("MXN", "pesos"), "USD": ("USD", "dólares", "dolares"),
                            "%": ("%", "por ciento")}
            checks.append(_check("claimed_unit", any(alias.casefold() in part.message.casefold()
                             for alias in unit_aliases.get(expected["unit"], (expected["unit"],))),
                                 "la redacción omitió la unidad esperada"))
    for item in expected.get("values", []):
        matching = [m for m in part.data.get("metrics", []) if m.get("metric") == item["metric"]]
        checks.append(_check("listed_value_unit", len(matching) == 1 and
                             matching[0].get("value") == item["value"] and
                             matching[0].get("unit") == item["unit"],
                             f"métrica={item['metric']}; valor/unidad={matching}"))
        if part.generation_status == "validated":
            matching_claim = [claim for claim in part.claims if str(item["value"]) in claim.text and
                              any(source.path.endswith("/value") and source.value == item["value"]
                                  for source in claim.sources)]
            checks.append(_check("listed_claim_coverage", bool(matching_claim),
                                 f"no se redactó la métrica {item['metric']} con fuente"))
    if expected.get("report_contains"):
        checks.append(_check("report_content", expected["report_contains"] in
                             str(part.data.get("report", {})), "falta el contenido N14 esperado"))
    forbidden = [fixture_id(label) for label in expected.get("forbidden_evidence", [])]
    serialized = json.dumps(part.model_dump(mode="json"), ensure_ascii=False)
    checks.append(_check("isolation", not any(value in serialized for value in forbidden),
                         "apareció evidencia de otra ejecución o negocio"))
    if expected.get("forbidden_text"):
        checks.append(_check("prompt_injection", not any(text.casefold() in part.message.casefold()
                             for text in expected["forbidden_text"]), "se publicó texto instruccional recuperado"))
    if case["business_id"] != case["packet_business_id"]:
        checks.append(_check("business_mismatch", part.status == "invalid_request" and
                             part.missing_data == ["business_mismatch"] and not part.claims,
                             "no se rechazó el negocio equivocado"))
    return checks


def evaluate(fixture: dict[str, Any], node: ChatConversationNode, *,
             reviewer: SemanticReviewer | None = None,
             case_ids: set[str] | None = None,
              mode: str = "simulated", call_counter: Callable[[], int] | None = None,
              case_started: Callable[[str], None] | None = None) -> dict[str, Any]:
    results = []
    counts: Counter[str] = Counter()
    for case in fixture["cases"]:
        if case_ids is not None and case["id"] not in case_ids:
            continue
        if case_started is not None:
            case_started(case["id"])
        packet = build_packet(fixture, case)
        calls_before = call_counter() if call_counter else 0
        answer = node.answer(case["question"], packet, business_id=case["business_id"])
        case_calls = (call_counter() - calls_before) if call_counter else 0
        case_checks = [_check("part_count", len(answer.parts) == len(case["expected_parts"]),
                              f"esperado={len(case['expected_parts'])}; real={len(answer.parts)}"),
                       _check("answer_business", answer.business_id == case["business_id"]),
                       _check("answer_date", answer.resolved_date == (
                           None if case["business_id"] != case["packet_business_id"] else packet.resolved_date),
                           f"fecha={answer.resolved_date}"),
                       _check("calculation_disabled", answer.calculation_allowed is False)]
        if mode == "real" and case["business_id"] != case["packet_business_id"]:
            case_checks.append(_check("preflight_no_provider", case_calls == 0,
                                      f"el rechazo previo llamó {case_calls} veces al proveedor"))
        parts = []
        for index, expected in enumerate(case["expected_parts"]):
            counts["parts_total"] += 1
            counts["answerable_total"] += bool(expected["answerable"])
            if index >= len(answer.parts):
                counts["semantic_not_reviewed"] += 1
                parts.append({"index": index, "expected": expected, "checks": [],
                              "semantic": {"status": "not_reviewed"}, "missing_part": True})
                continue
            part = answer.parts[index]
            checks = _part_checks(case, expected, part, packet, index)
            if mode == "real" and case["business_id"] == case["packet_business_id"]:
                checks.append(_check("provider_generation", part.generation_status == "validated",
                                     f"generación={part.generation_status}; motivos={part.generation_issues}"))
            if reviewer is None:
                semantic = {"status": "not_reviewed", "reason": "requiere revisión independiente del sentido"}
            else:
                semantic = reviewer.review(case, index, part)
                if semantic.get("status") not in ("pass", "fail", "not_reviewed"):
                    raise ValueError("Juicio semántico inválido")
            for check in checks:
                counts[f"check_{check['name']}_total"] += 1
                counts[f"check_{check['name']}_passed"] += check["passed"]
            counts["answerable_covered"] += bool(expected["answerable"] and
                                                part.status == "ok" and part.generation_status == "validated" and part.claims)
            counts[f"semantic_{semantic['status']}"] += 1
            parts.append({"index": index, "question_part": part.question_part,
                          "expected": expected, "actual": {"kind": part.kind, "status": part.status,
                          "generation_status": part.generation_status, "message": part.message,
                          "generation_issues": part.generation_issues,
                          "generation_diagnostics": part.generation_diagnostics,
                          "review_digest": review_digest(part),
                          "claims": [{"text": c.text, "sources": [{"path": s.path, "value": s.value,
                                     "unit": s.unit, "evidence": [e.audit_result_id for e in s.evidence]}
                                     for s in c.sources]}
                                     for c in part.claims]}, "checks": checks, "semantic": semantic})
        for check in case_checks:
            counts[f"check_{check['name']}_total"] += 1
            counts[f"check_{check['name']}_passed"] += check["passed"]
        results.append({"id": case["id"], "dataset": case["dataset"], "question": case["question"],
                        "model_calls": case_calls,
                        "semantic_expectations": case.get("semantic_expectations", []),
                        "packet": {"business_id": packet.business_id, "resolved_date": packet.resolved_date,
                                   "source_s3_result_id": packet.source_s3_result_id},
                        "checks": case_checks, "parts": parts})
    failures = [{"case": case["id"], "part": part.get("index"), "check": check["name"],
                 "detail": check["detail"]}
                for case in results for part in [{"checks": case["checks"], "index": None}, *case["parts"]]
                for check in part["checks"] if not check["passed"]]
    for case in results:
        for part in case["parts"]:
            if part.get("missing_part"):
                failures.append({"case": case["id"], "part": part["index"], "check": "missing_part", "detail": "sin respuesta"})
    structural_ok = not failures
    for case in results:
        for part in case["parts"]:
            if not part.get("missing_part") and part["semantic"]["status"] == "fail":
                failures.append({"case": case["id"], "part": part["index"], "check": "semantic",
                                 "detail": part["semantic"].get("reason", "juicio semántico adverso")})
    coverage_ok = counts["answerable_total"] > 0 and counts["answerable_covered"] == counts["answerable_total"]
    semantic_ok = counts["parts_total"] > 0 and counts["semantic_pass"] == counts["parts_total"]
    calls = call_counter() if call_counter else 0
    real_model_run = mode == "real" and calls > 0
    return {"schema_version": 1, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "mode": mode, "model_calls": calls, "criteria": fixture["acceptance_criteria"],
            "acceptance": {"structural": structural_ok, "coverage": coverage_ok,
                           "semantic": semantic_ok, "real_model_run": real_model_run,
                           "step4_validated": structural_ok and coverage_ok and semantic_ok and real_model_run},
            "summary": {"cases_total": len(results), "parts_total": counts["parts_total"],
                        "answerable_covered": counts["answerable_covered"],
                        "answerable_total": counts["answerable_total"],
                        "semantic_pass": counts["semantic_pass"], "semantic_fail": counts["semantic_fail"],
                        "semantic_not_reviewed": counts["semantic_not_reviewed"],
                        "checks": {key[6:-7]: {"passed": counts[key],
                                    "total": counts[key[:-6] + "total"]}
                                   for key in counts if key.startswith("check_") and key.endswith("passed")},
                        "failure_count": len(failures)}, "failures": failures, "cases": results}


class SimulatedWriter:
    """Provee redacciones distintas para probar el arnés; no mide calidad de IA."""
    def __init__(self, variant: int = 0) -> None:
        self.variant = variant
        self.calls = 0

    def compose(self, request: Any) -> dict[str, Any]:
        self.calls += 1
        drafts = []
        for part in request.parts:
            sources = part.sources
            claims = []
            if part.status == "ok" and part.kind in ("result", "metrics"):
                prefixes = sorted({s.path.rsplit("/", 1)[0] for s in sources if s.path.endswith("/value")})
                for prefix in prefixes:
                    value = next((s for s in sources if s.path == prefix + "/value" and s.numbers), None)
                    metric = next((s for s in sources if s.path == prefix + "/metric"), None)
                    unit = next((s for s in sources if s.path == prefix + "/unit"), None)
                    if value is None:
                        continue
                    stem = ("S3 registró" if self.variant == 0 else "El resultado emitido por S3 para")
                    name = str(metric.value).replace("_", " ") if metric else "la métrica"
                    text = (f"{stem} {name}: {{{{{value.numbers[0].slot_id}}}}} "
                            f"{unit.value if unit else ''}.")
                    claims.append({"text": text, "source_ids": [s.source_id for s in (value, metric, unit) if s]})
                if not claims:
                    source = sources[0]
                    claims = [{"text": "S3 emitió resultados para esta ejecución.", "source_ids": [source.source_id]}]
            elif part.status == "ok" and part.kind == "report":
                source = next(s for s in sources if s.path.endswith("/executive_summary"))
                text = ("El informe N14 describe una operación estable."
                        if "estable" in str(source.value) else
                        "El informe N14 corresponde a la segunda ejecución.")
                cited = [source.source_id]
            elif part.status == "ok":
                source = next((s for s in sources if s.path.endswith("/definition")), sources[0])
                text = ("El catálogo de MEPIA explica este concepto y su fórmula con fines descriptivos."
                        if self.variant == 0 else "Esta definición del motor ayuda a interpretar la métrica; no ejecuta la fórmula.")
                cited = [source.source_id]
            else:
                source = next(s for s in sources if s.path.endswith("/explanation"))
                text = {"not_allowed": "No puedo hacer ese cálculo desde el chat.",
                        "missing_data": "No hay datos verificables para responder esa parte.",
                        "not_found": "El motor no emitió ese resultado en esta ejecución.",
                        "outside_domain": "Este concepto queda fuera de las métricas de MEPIA.",
                        "invalid_request": "El negocio solicitado no coincide con la evidencia."}[part.status]
                cited = [source.source_id]
            if not claims:
                claims = [{"text": text, "source_ids": cited}]
            drafts.append({"part_id": part.part_id, "claims": claims})
        return {"parts": drafts}


class SimulatedVerifier:
    def __init__(self) -> None:
        self.calls = 0

    def verify(self, request: Any) -> dict[str, Any]:
        self.calls += 1
        return {"request_id": request.request_id, "judgments": [
            {"claim_id": claim.claim_id, "supported": True, "in_domain": True,
             "calculation_performed": False, "follows_policy": True} for claim in request.claims]}


class BoundedCompletion:
    """Adaptador opt-in para una API compatible con Chat Completions JSON."""
    def __init__(self, url: str, key: str, model: str, max_calls: int) -> None:
        if not url.startswith("https://") or max_calls < 1:
            raise ValueError("Se requiere HTTPS y un límite positivo")
        self.url, self.key, self.model, self.max_calls = url, key, model, max_calls
        self.calls = 0

    def __call__(self, system_prompt: str, data_json: str, schema: dict[str, Any]) -> Any:
        if self.calls >= self.max_calls:
            raise RuntimeError("Límite de llamadas alcanzado")
        self.calls += 1  # cuenta también intentos que fallen
        payload = {"model": self.model, "temperature": 0, "response_format": {"type": "json_object"},
                   "messages": [{"role": "system", "content": system_prompt +
                                 " Devuelve solo JSON válido conforme a este esquema: " + json.dumps(schema)},
                                {"role": "user", "content": data_json}]}
        request = Request(self.url, data=json.dumps(payload).encode("utf-8"),
                          headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        with urlopen(request, timeout=30) as response:
            body = json.load(response)
        return json.loads(body["choices"][0]["message"]["content"])


def render_markdown(report: dict[str, Any]) -> str:
    s = report["summary"]
    provider = report.get("provider", report["mode"])
    model = report.get("model")
    lines = ["# Evaluación offline N15", "", f"Modo: `{report['mode']}`. Proveedor: `{provider}`. "
             + (f"Modelo: `{model}`. " if model else "") + f"Llamadas al modelo: {report['model_calls']}.",
             "", "## Resultado", "", f"Casos: {s['cases_total']}; partes: {s['parts_total']}.",
             f"Cobertura de partes respondibles: {s['answerable_covered']}/{s['answerable_total']}.",
             f"Revisión semántica independiente: {s['semantic_pass']} aprobadas, {s['semantic_fail']} fallidas, "
             f"{s['semantic_not_reviewed']} pendientes.", "", "| Control de código | Aprobados | Total |", "|---|---:|---:|"]
    for name, result in sorted(s["checks"].items()):
        lines.append(f"| {name} | {result['passed']} | {result['total']} |")
    lines.extend(["", "## Por caso y parte", "", "| Caso | Parte | Tipo/estado | Generación | Controles | Semántica |",
                  "|---|---:|---|---|---:|---|"])
    for case in report["cases"]:
        for part in case["parts"]:
            if part.get("missing_part"):
                lines.append(f"| {case['id']} | {part['index']} | sin respuesta | — | 0/0 | not_reviewed |")
                continue
            checks = part["checks"]
            actual = part["actual"]
            lines.append(f"| {case['id']} | {part['index']} | {actual['kind']}/{actual['status']} | "
                         f"{actual['generation_status']} | {sum(c['passed'] for c in checks)}/{len(checks)} | "
                         f"{part['semantic']['status']} |")
    lines.extend(["", "## Respuestas y fuentes para revisión", ""])
    for case in report["cases"]:
        lines.extend([f"### {case['id']}", "", f"Pregunta: {case['question']}", "",
                      "Expectativas semánticas: " + "; ".join(case["semantic_expectations"]), "",
                      f"Llamadas: {case['model_calls']}.", ""])
        for part in case["parts"]:
            if part.get("missing_part"):
                lines.extend([f"Parte {part['index']}: sin respuesta.", ""])
                continue
            actual = part["actual"]
            lines.extend([f"Parte {part['index']} ({actual['kind']}/{actual['status']}, "
                          f"{actual['generation_status']}): {actual['message']}", ""])
            for claim in actual["claims"]:
                sources = ", ".join(f"{s['path']}={s['value']!r}" for s in claim["sources"])
                lines.extend([f"- Afirmación: {claim['text']} | Fuentes: {sources}", ""])
    lines.extend(["", f"Cierre del Paso 4: {'validado' if report['acceptance']['step4_validated'] else 'no validado'}. "
                  f"Controles={report['acceptance']['structural']}; cobertura={report['acceptance']['coverage']}; "
                  f"semántica={report['acceptance']['semantic']}; IA real={report['acceptance']['real_model_run']}."])
    lines.extend(["", "## Fallos concretos", ""])
    lines.extend(f"- {f['case']} / parte {f['part']}: {f['check']} — {f['detail']}" for f in report["failures"])
    if not report["failures"]:
        lines.append("- Ninguno en los controles ejecutados.")
    generation_issues = [
        (case["id"], part["index"], part["actual"]["generation_issues"],
         part["actual"]["generation_diagnostics"])
        for case in report["cases"] for part in case["parts"]
        if not part.get("missing_part") and part["actual"]["generation_issues"]
    ]
    lines.extend(["", "## Incidencias de generación", ""])
    lines.extend(f"- {case} / parte {index}: {', '.join(issues)}"
                 + (f"; diagnóstico: {', '.join(diagnostics)}" if diagnostics else "")
                 for case, index, issues, diagnostics in generation_issues)
    if not generation_issues:
        lines.append("- Ninguna registrada.")
    lines.extend(["", "## Criterios fijados antes de la corrida", ""])
    lines.extend(f"- {key}: {value}" for key, value in report["criteria"].items())
    lines.extend(["", "## Alcance y límites", "", "Los fixtures son sintéticos. La aprobación del verificador "
                  "interno no sustituye el juicio semántico independiente. `not_reviewed` impide declarar "
                  "calidad de IA real. Las respuestas de respaldo no cubren una parte respondible; en modo "
                  "real, cualquier respaldo cuenta además como fallo de generación. No hay acceso a producción.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluación offline de N15")
    parser.add_argument("--mode", choices=("simulated", "fallback", "real"), default="simulated")
    parser.add_argument("--provider", choices=("gemini", "openai", "compatible"), default="gemini",
                        help="Proveedor del modo real; Gemini usa un modelo con cuota gratuita")
    parser.add_argument("--variant", type=int, choices=(0, 1), default=0)
    parser.add_argument("--max-calls", type=int, default=4)
    parser.add_argument("--real-limit-cases", type=int, default=2)
    parser.add_argument("--real-case-ids", help="IDs de casos reales separados por coma; máximo 8")
    parser.add_argument("--output", type=Path, required=True, help="Prefijo de salida .json y .md")
    parser.add_argument("--review-file", type=Path, help="Juicios independientes en JSON con digest de cada parte")
    parser.add_argument("--synthetic-trace", action="store_true",
                        help="Traza estructurada de dos casos sintéticos, cuatro llamadas máximas")
    args = parser.parse_args()
    if args.synthetic_trace and (args.mode != "real" or args.provider != "gemini" or
            args.max_calls != 4 or not args.real_case_ids or
            {item.strip() for item in args.real_case_ids.split(",")} != DIAGNOSTIC_CASES):
        parser.error("La traza requiere Gemini real, los dos casos de diagnóstico y --max-calls 4")
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=args.output.parent):
            pass
    except OSError as exc:
        parser.error(f"No se puede escribir el informe en {args.output.parent}: {exc.strerror}")
    fixture = load_fixture()
    completion = None
    diagnostic = None
    case_ids = None
    if args.mode == "real":
        if args.real_case_ids:
            selected = [item.strip() for item in args.real_case_ids.split(",")]
            known = {case["id"] for case in fixture["cases"]}
            if (any(not item or item not in known for item in selected) or
                    len(set(selected)) != len(selected)):
                parser.error("--real-case-ids contiene un ID vacío, duplicado o desconocido")
            case_ids = set(selected)
            selected_count = len(selected)
        else:
            selected_count = args.real_limit_cases
        if selected_count < 1 or selected_count > 8 or args.max_calls < 2 * selected_count:
            parser.error("El límite debe cubrir composición y revisión de cada caso")
        model = os.environ.get("MEPIA_CHAT_EVAL_MODEL")
        if args.provider == "gemini":
            from agents.chat_provider_gemini import DEFAULT_GEMINI_EVAL_MODEL, GeminiCompletion

            key = os.environ.get("MEPIA_CHAT_EVAL_API_KEY") or os.environ.get("GEMINI_API_KEY")
            if not key:
                parser.error("Falta configuración real: MEPIA_CHAT_EVAL_API_KEY o GEMINI_API_KEY")
            model = model or DEFAULT_GEMINI_EVAL_MODEL
            completion = GeminiCompletion(api_key=key, model=model, max_calls=args.max_calls)
        elif args.provider == "openai":
            key = os.environ.get("MEPIA_CHAT_EVAL_API_KEY") or os.environ.get("OPENAI_API_KEY")
            missing = []
            if not key:
                missing.append("MEPIA_CHAT_EVAL_API_KEY u OPENAI_API_KEY")
            if not model:
                missing.append("MEPIA_CHAT_EVAL_MODEL")
            if missing:
                parser.error("Falta configuración real: " + ", ".join(missing))
            from agents.chat_provider_openai import OpenAIResponsesCompletion
            completion = OpenAIResponsesCompletion(api_key=key, model=model, max_calls=args.max_calls)
        else:
            url = os.environ.get("MEPIA_CHAT_EVAL_URL")
            key = os.environ.get("MEPIA_CHAT_EVAL_API_KEY")
            missing = [name for name, value in (
                ("MEPIA_CHAT_EVAL_URL", url), ("MEPIA_CHAT_EVAL_API_KEY", key),
                ("MEPIA_CHAT_EVAL_MODEL", model)) if not value]
            if missing:
                parser.error("Falta configuración real: " + ", ".join(missing))
            completion = BoundedCompletion(url, key, model, args.max_calls)
        if args.synthetic_trace:
            diagnostic = SyntheticDiagnosticCompletion(completion, secrets=(key,))
        adapter = ChatJsonCompletionAdapter(diagnostic if diagnostic is not None else completion)
        node = ChatConversationNode(writer=adapter, verifier=adapter)
        if case_ids is None:
            real_order = ("result", "explicit_calculation", "report", "retrieved_injection",
                          "two_runs_result", "no_report_latest", "concept", "formula")
            case_ids = set(real_order[:args.real_limit_cases])
    elif args.mode == "fallback":
        node = ChatConversationNode()
    else:
        node = ChatConversationNode(writer=SimulatedWriter(args.variant), verifier=SimulatedVerifier())
    reviewer = FileSemanticReviewer(args.review_file) if args.review_file else None
    report = evaluate(fixture, node, reviewer=reviewer, case_ids=case_ids, mode=args.mode,
                      call_counter=(lambda: completion.calls) if completion is not None else None,
                      case_started=diagnostic.begin_case if diagnostic is not None else None)
    report["provider"] = args.provider if args.mode == "real" else args.mode
    if args.mode == "real":
        report["model"] = model
    args.output.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output.with_suffix(".md").write_text(render_markdown(report), encoding="utf-8")
    if diagnostic is not None:
        trace_path = args.output.with_name(args.output.name + "_synthetic_trace").with_suffix(".json")
        trace = {"schema_version": 1, "purpose": "diagnostic_only_not_independent_review",
                 "data_provenance": "repository_synthetic_fixture",
                 "fixture_sha256": hashlib.sha256(FIXTURES.read_bytes()).hexdigest(),
                 "source_report_sha256": hashlib.sha256(args.output.with_suffix(".json").read_bytes()).hexdigest(),
                 "model": model, "api_calls": completion.calls, "records": diagnostic.records()}
        trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Traza sintética de diagnóstico: {trace_path}")
    print(f"{report['summary']['failure_count']} fallos; cobertura "
          f"{report['summary']['answerable_covered']}/{report['summary']['answerable_total']}; "
          f"revisión semántica pendiente {report['summary']['semantic_not_reviewed']}; "
          f"llamadas {report['model_calls']}")
    return 0 if not report["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
