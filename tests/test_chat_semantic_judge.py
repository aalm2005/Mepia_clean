"""El juez externo conserva los fallos y enlaza cada juicio al informe exacto."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from tests.chat_semantic_judge import (
    SemanticBatch, SemanticJudgment, judge_reports, merge_review_runs, review_payload,
    render_summary, split_report, summarize_reviews, validate_batch,
    safe_provider_error_details,
    diagnose_judge,
)


def sample_report():
    return {"mode": "real", "model_calls": 2, "failures": [], "cases": [{
        "id": "result", "question": "¿Cuál fue el ticket promedio?", "model_calls": 2,
        "semantic_expectations": ["S3 emitió 125 MXN"],
        "packet": {"business_id": "biz-a", "resolved_date": "2026-09-24"},
        "parts": [{"index": 0, "question_part": "Cuál fue el ticket promedio",
                   "expected": {"kind": "result", "status": "ok", "answerable": True},
                   "actual": {"kind": "result", "status": "ok", "generation_status": "validated",
                              "message": "El ticket promedio fue 125 MXN.", "review_digest": "digest-1",
                              "claims": [{"text": "El ticket promedio fue 125 MXN.",
                                          "sources": [{"path": "/metrics/0/value", "value": 125,
                                                       "unit": "MXN", "evidence": ["s3-id"]}]}],
                              "generation_diagnostics": ["internal-secret"]},
                   "checks": [{"name": "classification", "passed": True}],
                   "semantic": {"status": "not_reviewed"}}]}]}


class SemanticJudgeTests(unittest.TestCase):
    def test_503_records_safe_provider_hints_without_retry_or_verdict(self):
        import httpx
        from openai import InternalServerError

        secret = "sk-test-secret-do-not-record"
        body = {"error": {"status": "UNAVAILABLE", "code": 503,
                          "message": f"This model is overloaded. Try again later. {secret}"}}
        error = InternalServerError(
            f"private exception {secret}", body=body,
            response=httpx.Response(503, request=httpx.Request(
                "POST", f"https://example.invalid/?key={secret}",
                headers={"Authorization": f"Bearer {secret}"})))

        class FailingParse:
            calls = 0

            def parse(self, **_kwargs):
                self.calls += 1
                raise error

        parse = FailingParse()
        client = SimpleNamespace(beta=SimpleNamespace(chat=SimpleNamespace(completions=parse)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(sample_report()), encoding="utf-8")
            original_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            reviews = judge_reports([path], client=client, model="fake-independent", max_calls=1)
            self.assertEqual(parse.calls, 1)
            self.assertEqual(reviews["judge_calls"], 1)
            self.assertEqual(reviews["reviews"], [])
            diagnostic = reviews["batch_errors"][0]
            self.assertEqual(diagnostic["http_status"], 503)
            self.assertEqual(diagnostic["provider_status"], "UNAVAILABLE")
            self.assertTrue(diagnostic["provider_message_present"])
            self.assertEqual(diagnostic["diagnostic_hints"], ["provider_message_mentions_overload"])
            summary = summarize_reviews([path], reviews)
            self.assertEqual(summary["summary"]["not_reviewed"], 1)
            self.assertEqual(summary["summary"]["fail"], 0)
            self.assertFalse(summary["step4_validated"])
            rendered = render_summary(summary)
            self.assertIn("Estado del proveedor: UNAVAILABLE", rendered)
            self.assertNotIn(secret, json.dumps(reviews) + json.dumps(summary) + rendered)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), original_hash)

    def test_safe_diagnostics_accept_flat_body_and_omit_unknown_values(self):
        class ProviderError(Exception):
            pass

        secret = "private-key-or-source-text"
        cases = [
            ({"status": "UNAVAILABLE", "message": f"Service unavailable; schema {secret}"},
             "UNAVAILABLE", True,
             ["provider_message_mentions_unavailable", "provider_message_mentions_schema"]),
            ({"status": secret, "code": secret, "message": secret}, None, True, []),
            (secret, None, True, []),
        ]
        for body, status, present, hints in cases:
            with self.subTest(body_type=type(body).__name__, status=status):
                error = ProviderError(secret)
                error.body = body
                details = safe_provider_error_details(error)
                self.assertEqual(details["provider_status"], status)
                self.assertEqual(details["provider_message_present"], present)
                self.assertEqual(details["diagnostic_hints"], hints)
                self.assertNotIn(secret, json.dumps(details))

    def test_safe_diagnostics_accept_array_and_cached_response_text(self):
        import httpx

        secret = "private-response-content"
        cases = [
            (SimpleNamespace(body=[{"error": {"status": "UNAVAILABLE",
              "message": f"Model overloaded {secret}"}}]), "array", "UNAVAILABLE",
             ["provider_message_mentions_overload"]),
            (SimpleNamespace(body=None, response=httpx.Response(
                503, text=f"Service unavailable {secret}")), "absent", None,
             ["provider_message_mentions_unavailable"]),
        ]
        for error, kind, status, hints in cases:
            with self.subTest(kind=kind):
                details = safe_provider_error_details(error)
                self.assertEqual(details["provider_error_body_kind"], kind)
                self.assertEqual(details["provider_status"], status)
                self.assertEqual(details["diagnostic_hints"], hints)
                self.assertTrue(details["provider_message_present"])
                self.assertNotIn(secret, json.dumps(details))

    def test_diagnostic_control_counts_calls_and_never_counts_as_a_review(self):
        class ProviderError(Exception):
            status_code = 503
            body = "Model overloaded private-content"

        for control_fails, judge_fails in ((False, True), (True, True),
                                          (False, False), (True, False)):
            with self.subTest(control_fails=control_fails, judge_fails=judge_fails):
                calls = []

                def create(**kwargs):
                    calls.append(("control", kwargs))
                    if control_fails:
                        raise ProviderError()
                    return SimpleNamespace(private_content="not-a-judgment")

                def parse(**kwargs):
                    calls.append(("judge", kwargs))
                    if judge_fails:
                        raise ProviderError()
                    result = SemanticBatch(judgments=[SemanticJudgment(
                        case_id="result", part_index=0, supported=True,
                        addresses_question=True, correct_scope=True,
                        no_calculation=True, reason="fuente exacta")])
                    return SimpleNamespace(choices=[SimpleNamespace(
                        finish_reason="stop", message=SimpleNamespace(parsed=result))])

                client = SimpleNamespace(
                    chat=SimpleNamespace(completions=SimpleNamespace(create=create)),
                    beta=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(parse=parse))))
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "report.json"
                    report = sample_report()
                    report["model"] = "generator"
                    path.write_text(json.dumps(report), encoding="utf-8")
                    original = path.read_bytes()
                    result = diagnose_judge(path, client=client, model="other", max_calls=2)
                    self.assertEqual([name for name, _ in calls], ["control", "judge"])
                    self.assertEqual([data["model"] for _, data in calls], ["other", "other"])
                    self.assertNotIn("response_format", calls[0][1])
                    self.assertIs(calls[1][1]["response_format"], SemanticBatch)
                    self.assertEqual(result["judge_calls"], 1)
                    self.assertEqual(result["total_api_calls"], 2)
                    self.assertEqual(result["diagnostic_control"]["calls"], 1)
                    self.assertEqual(len(result["reviews"]), 0 if judge_fails else 1)
                    summary = summarize_reviews([path], result)
                    self.assertEqual(summary["summary"]["parts"], 1)
                    self.assertEqual(summary["summary"]["not_reviewed"], int(judge_fails))
                    self.assertFalse(summary["step4_validated"])
                    self.assertIn("Control mínimo de acceso", render_summary(summary))
                    self.assertNotIn("private-content", json.dumps(result) + render_summary(summary))
                    self.assertEqual(path.read_bytes(), original)
                    run = Path(directory) / "reviews.json"
                    run.write_text(json.dumps(result), encoding="utf-8")
                    merged = merge_review_runs([run])
                    self.assertEqual(merged["judge_calls"], 1)
                    self.assertEqual(merged["total_api_calls"], 2)
                    self.assertEqual(merged["attempts"][0]["diagnostic_control"],
                                     result["diagnostic_control"])
                    for limit in (0, 1, 3):
                        with self.assertRaises(ValueError):
                            diagnose_judge(path, client=client, model="other", max_calls=limit)
                    with self.assertRaises(ValueError):
                        diagnose_judge(path, client=client, model="generator", max_calls=2)
                    multiple = json.loads(json.dumps(report))
                    multiple["cases"][0]["parts"].append(multiple["cases"][0]["parts"][0])
                    path.write_text(json.dumps(multiple), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        diagnose_judge(path, client=client, model="other", max_calls=2)
                    altered = sample_report()
                    altered["mode"] = "simulated"
                    path.write_text(json.dumps(altered), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        diagnose_judge(path, client=client, model="other", max_calls=2)
                    self.assertEqual(len(calls), 2)

    def test_render_limits_describe_actual_review_independence(self):
        base = {'cases': [], 'judge_calls': 0, 'mechanical_failures': [],
                'known_harness_false_positives': [], 'judge_conflicts': [],
                'step4_validated': False, 'attempts': [],
                'summary': {'parts': 12, 'generation_calls': 13, 'covered': 3,
                            'answerable': 7, 'pass': 8, 'fail': 4, 'not_reviewed': 0,
                            'independent_model_judgments': 12, 'independent_model_pass': 8,
                            'same_model_judgments': 0}}
        text = render_summary(base)
        self.assertIn('Todas las partes recibieron juicio de un modelo distinto', text)
        self.assertNotIn('Hay 0 juicios', text)
        base['summary']['same_model_judgments'] = 3
        base['summary']['independent_model_judgments'] = 9
        self.assertIn('Hay 3 juicios del mismo modelo generador', render_summary(base))
        base['batch_errors'] = [{'report': 'saved.json', 'error_type': 'InternalServerError',
                                 'http_status': 503, 'case_ids': ['result']}]
        text = render_summary(base)
        self.assertIn('Errores del juez en esta corrida: 1.', text)
        self.assertIn('saved.json: InternalServerError, HTTP 503; casos: result.', text)
        base['attempts'] = [{'file': 'previous_reviews.json', 'model': 'model-a',
                             'calls': 1, 'errors': base['batch_errors']}]
        text = render_summary(base)
        self.assertIn('Errores en intentos previos conservados: 1.', text)
        self.assertIn('previous_reviews.json: revisor model-a, 1 llamadas, 1 errores.', text)

    def test_payload_blinds_judge_to_internal_diagnostics_and_checks(self):
        payload = review_payload(sample_report())
        serialized = json.dumps(payload)
        self.assertIn("125 MXN", serialized)
        self.assertNotIn("internal-secret", serialized)
        self.assertNotIn("generation_status", serialized)
        self.assertNotIn("classification", serialized)

    def test_batch_rejects_missing_or_duplicate_judgments(self):
        report = sample_report()
        item = SemanticJudgment(case_id="result", part_index=0, supported=True,
                                addresses_question=True, correct_scope=True,
                                no_calculation=True, reason="fuente exacta")
        self.assertEqual(len(validate_batch(report, [item])), 1)
        with self.assertRaises(ValueError):
            validate_batch(report, [])
        with self.assertRaises(ValueError):
            validate_batch(report, [item, item])

    def test_large_report_splits_by_parts_before_calls(self):
        report = sample_report()
        other = json.loads(json.dumps(report["cases"][0]))
        other["id"] = "result_two"
        report["cases"].append(other)
        groups = split_report(report, 1)
        self.assertEqual([[case["id"] for case in group["cases"]] for group in groups],
                         [["result"], ["result_two"]])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaises(ValueError):
                judge_reports([path], client=None, model="fake", max_calls=1,
                              max_parts_per_call=1)

    def test_saved_judgment_requires_unchanged_report_hash_and_digest(self):
        class FakeParse:
            def parse(self, **_kwargs):
                result = SemanticBatch(judgments=[SemanticJudgment(
                    case_id="result", part_index=0, supported=True,
                    addresses_question=True, correct_scope=True,
                    no_calculation=True, reason="fuente exacta")])
                return SimpleNamespace(choices=[SimpleNamespace(
                    finish_reason="stop", message=SimpleNamespace(parsed=result))])

        client = SimpleNamespace(beta=SimpleNamespace(chat=SimpleNamespace(
            completions=FakeParse())))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(sample_report()), encoding="utf-8")
            reviews = judge_reports([path], client=client, model="fake-independent", max_calls=1)
            self.assertEqual(reviews["judge_calls"], 1)
            self.assertEqual(len(reviews["reviews"]), 1)
            self.assertEqual(reviews["source_reports"][0]["sha256"],
                             hashlib.sha256(path.read_bytes()).hexdigest())
            summary = summarize_reviews([path], reviews)
            self.assertEqual(summary["summary"]["pass"], 1)
            altered = sample_report()
            altered["cases"][0]["parts"][0]["actual"]["message"] = "Otro texto"
            path.write_text(json.dumps(altered), encoding="utf-8")
            summary = summarize_reviews([path], reviews)
            self.assertEqual(summary["summary"]["not_reviewed"], 1)
            fallback = sample_report()
            fallback["cases"][0]["parts"][0]["actual"]["generation_status"] = "fallback"
            fallback["cases"][0]["parts"][0]["actual"]["message"] = "Este es el resultado de S3."
            path.write_text(json.dumps(fallback), encoding="utf-8")
            contradictory = judge_reports([path], client=client, model="fake-independent", max_calls=1)
            summary = summarize_reviews([path], contradictory)
            self.assertEqual(summary["summary"]["fail"], 1)
            self.assertEqual(len(summary["judge_conflicts"]), 1)

    def test_merge_preserves_attempts_and_prioritizes_first_matching_judgment(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            base = {"schema_version": 1, "reviewer_model": "model-a", "judge_calls": 1,
                    "source_reports": [{"name": "report.json", "sha256": "hash"}],
                    "reviews": [{"case_id": "result", "part_index": 0,
                                 "digest": "digest", "source_report_sha256": "hash",
                                 "reviewer": "independent-model:model-a"}],
                    "batch_errors": [{"error_type": "InternalServerError", "http_status": 503}]}
            first.write_text(json.dumps(base), encoding="utf-8")
            another = json.loads(json.dumps(base))
            another["reviewer_model"] = "model-b"
            another["reviews"][0]["reviewer"] = "independent-model:model-b"
            another["batch_errors"] = []
            second.write_text(json.dumps(another), encoding="utf-8")
            merged = merge_review_runs([first, second])
            self.assertEqual(merged["judge_calls"], 2)
            self.assertEqual(len(merged["reviews"]), 1)
            self.assertEqual(merged["reviews"][0]["reviewer"], "independent-model:model-a")
            self.assertEqual(len(merged["attempts"][0]["errors"]), 1)

    def test_human_review_is_not_counted_as_a_model_judgment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            report = sample_report()
            report['model'] = 'gemini-3.5-flash-lite'
            path.write_text(json.dumps(report), encoding='utf-8')
            item = {'case_id': 'result', 'part_index': 0, 'digest': 'digest-1',
                    'source_report_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'reviewer': 'human:user', 'supported': True, 'addresses_question': True,
                    'correct_scope': True, 'no_calculation': True, 'reason': 'Revisión humana explícita.'}
            data = {'judge_calls': 0, 'batch_errors': [], 'reviews': [item]}
            summary = summarize_reviews([path], data)
            self.assertEqual(summary['summary']['pass'], 1)
            self.assertEqual(summary['summary']['independent_model_judgments'], 0)
            self.assertEqual(summary['summary']['independent_human_judgments'], 1)
            self.assertEqual(summary['summary']['independent_human_pass'], 1)
            self.assertFalse(summary['step4_validated'])
            self.assertIn('Revisión humana independiente: 1/1 partes', render_summary(summary))
            self.assertIn('Todas las partes recibieron revisión humana', render_summary(summary))
            item['reviewer'] = 'independent-model:gemini-3.5-flash-lite'
            summary = summarize_reviews([path], data)
            self.assertEqual(summary['summary']['same_model_judgments'], 1)
            self.assertEqual(summary['summary']['independent_model_judgments'], 0)
            self.assertEqual(summary['summary']['independent_human_judgments'], 0)
            item['reviewer'] = 'unknown-reviewer'
            summary = summarize_reviews([path], data)
            self.assertEqual(summary['summary']['not_reviewed'], 1)
            self.assertEqual(summary['summary']['independent_model_judgments'], 0)
            self.assertEqual(summary['summary']['independent_human_judgments'], 0)


if __name__ == "__main__":
    unittest.main()
