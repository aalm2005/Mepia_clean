"""El arnés debe detectar negativas excesivas y conservar límites de medición."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agents.chat_conversation import ChatConversationNode
from agents.chat_response import ChatReviewRequest, ChatWritingRequest
from tests.chat_offline_eval import (
    BoundedCompletion, FileSemanticReviewer, SimulatedVerifier, SimulatedWriter,
    SyntheticDiagnosticCompletion, build_packet, evaluate, fixture_id, load_fixture,
    main, render_markdown, review_digest,
)


class OfflineChatEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_fixture()

    def test_fixture_covers_required_families_and_exact_lineage(self):
        cases = {item["id"]: item for item in self.fixture["cases"]}
        required = {"concept", "formula", "result", "result_paraphrase", "report",
                    "two_runs_result", "two_runs_report", "no_report_latest", "no_data",
                    "wrong_business", "outside", "explicit_calculation", "implicit_calculation",
                    "mixed", "question_injection", "retrieved_injection", "cash_warning",
                    "explicit_date_result", "same_day_result_and_report",
                    "available_result_missing_report", "result_and_projection",
                    "concept_and_outside", "arithmetic_division", "two_named_results",
                    "adversarial_metric_context"}
        self.assertTrue(required <= set(cases))
        packet = build_packet(self.fixture, cases["two_runs_report"])
        self.assertEqual(packet.source_s3_result_id, fixture_id("new-s3"))
        self.assertEqual([ref.audit_result_id for ref in packet.evidence],
                         [fixture_id("new-s3"), fixture_id("new-n14")])
        missing = build_packet(self.fixture, cases["no_report_latest"])
        self.assertIsNone(missing.final_report)
        self.assertEqual([ref.audit_result_id for ref in missing.evidence], [fixture_id("new-s3")])

    def test_new_mixed_cases_keep_answerable_parts_and_source_status(self):
        selected = {"cash_warning", "same_day_result_and_report",
                    "available_result_missing_report", "result_and_projection",
                    "concept_and_outside", "two_named_results", "adversarial_metric_context"}
        report = evaluate(self.fixture, ChatConversationNode(writer=SimulatedWriter(),
                          verifier=SimulatedVerifier()), case_ids=selected)
        self.assertEqual(report["summary"]["cases_total"], len(selected))
        self.assertEqual(report["summary"]["failure_count"], 0, report["failures"])
        self.assertEqual(report["summary"]["answerable_covered"], report["summary"]["answerable_total"])
        self.assertEqual(report["summary"]["checks"]["source_metric_status"], {"passed": 2, "total": 2})

    def test_two_distinct_valid_paraphrases_keep_coverage_without_literal_matching(self):
        messages = []
        for variant in (0, 1):
            writer, verifier = SimulatedWriter(variant), SimulatedVerifier()
            report = evaluate(self.fixture, ChatConversationNode(writer=writer, verifier=verifier))
            self.assertEqual(report["summary"]["failure_count"], 0, report["failures"])
            self.assertEqual(report["summary"]["answerable_covered"], report["summary"]["answerable_total"])
            self.assertFalse(report["acceptance"]["semantic"])
            self.assertFalse(report["acceptance"]["step4_validated"])
            self.assertEqual(report["summary"]["semantic_not_reviewed"], report["summary"]["parts_total"])
            self.assertGreater(writer.calls, 0)
            self.assertEqual(writer.calls, verifier.calls)
            result = next(case for case in report["cases"] if case["id"] == "result")
            messages.append(result["parts"][0]["actual"]["message"])
        self.assertNotEqual(*messages)
        self.assertIn("125 MXN", messages[0])
        self.assertIn("125 MXN", messages[1])

    def test_reject_everything_baseline_fails_coverage(self):
        report = evaluate(self.fixture, ChatConversationNode(), mode="fallback")
        self.assertEqual(report["summary"]["answerable_covered"], 0)
        self.assertGreater(report["summary"]["answerable_total"], 0)
        self.assertFalse(report["acceptance"]["coverage"])
        self.assertTrue(any(item["check"] == "answerable_coverage" for item in report["failures"]))

    def test_real_provider_fallback_on_calculation_denial_is_a_failure(self):
        report = evaluate(self.fixture, ChatConversationNode(),
                          case_ids={"explicit_calculation"}, mode="real")
        self.assertEqual(report["summary"]["answerable_total"], 0)
        self.assertEqual(report["summary"]["checks"]["provider_generation"],
                         {"passed": 0, "total": 1})
        self.assertFalse(report["acceptance"]["structural"])
        self.assertTrue(any(item["check"] == "provider_generation" for item in report["failures"]))
        self.assertIn("## Incidencias de generación", render_markdown(report))

    def test_real_business_mismatch_is_valid_preflight_without_provider(self):
        report = evaluate(self.fixture, ChatConversationNode(),
                          case_ids={"wrong_business"}, mode="real", call_counter=lambda: 0)
        self.assertEqual(report["summary"]["failure_count"], 0, report["failures"])
        self.assertEqual(report["summary"]["checks"]["preflight_no_provider"],
                         {"passed": 1, "total": 1})
        self.assertNotIn("provider_generation", report["summary"]["checks"])
        self.assertFalse(report["acceptance"]["real_model_run"])

    def test_report_contains_safe_per_part_generation_diagnostic(self):
        class FailingWriter:
            def compose(self, _request):
                raise RuntimeError("synthetic-secret-in-exception")
        report = evaluate(self.fixture, ChatConversationNode(writer=FailingWriter(),
                          verifier=SimulatedVerifier()), case_ids={"result"}, mode="real")
        actual = report["cases"][0]["parts"][0]["actual"]
        self.assertEqual(actual["generation_diagnostics"], ["draft:exception:RuntimeError"])
        self.assertIn("draft:exception:RuntimeError", render_markdown(report))
        self.assertNotIn("synthetic-secret", json.dumps(report))

    def test_output_write_permission_is_checked_before_evaluation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = str(Path(directory) / "report")
            with patch("sys.argv", ["chat_offline_eval", "--output", output]), \
                 patch("tests.chat_offline_eval.tempfile.TemporaryFile",
                       side_effect=PermissionError(13, "access denied")), \
                 patch("tests.chat_offline_eval.evaluate") as evaluate_mock:
                with self.assertRaises(SystemExit) as caught:
                    main()
                self.assertEqual(caught.exception.code, 2)
                evaluate_mock.assert_not_called()

    def test_real_case_selection_rejects_unknown_id_before_credential_check(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("sys.argv", ["chat_offline_eval", "--mode", "real",
                    "--real-case-ids", "cash_warning,missing_unknown", "--output",
                    str(Path(directory) / "report")]), \
                 patch("tests.chat_offline_eval.evaluate") as evaluate_mock:
                with self.assertRaises(SystemExit) as caught:
                    main()
                self.assertEqual(caught.exception.code, 2)
                evaluate_mock.assert_not_called()

    def test_seven_case_real_preflight_requires_environment_key_before_calls(self):
        ids = "report,mixed,catalog,outside,question_injection,concept_and_outside,two_named_results"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "directed"
            with patch.dict(os.environ, {"MEPIA_CHAT_EVAL_API_KEY": "", "GEMINI_API_KEY": ""}), \
                 patch("sys.argv", ["chat_offline_eval", "--mode", "real", "--provider", "gemini",
                                    "--real-case-ids", ids, "--max-calls", "14",
                                    "--output", str(output)]), \
                 patch("tests.chat_offline_eval.evaluate") as evaluate_mock:
                with self.assertRaises(SystemExit) as caught:
                    main()
                self.assertEqual(caught.exception.code, 2)
                evaluate_mock.assert_not_called()
                self.assertFalse(output.with_suffix(".json").exists())

    def test_unsupported_number_produces_fallback_and_concrete_failure(self):
        class BadWriter:
            def compose(self, request):
                parts = []
                for part in request.parts:
                    source = part.sources[0]
                    parts.append({"part_id": part.part_id, "claims": [{"text": "El valor es 999 MXN.",
                                  "source_ids": [source.source_id]}]})
                return {"parts": parts}
        report = evaluate(self.fixture, ChatConversationNode(writer=BadWriter(), verifier=SimulatedVerifier()),
                          case_ids={"result"})
        self.assertEqual(report["summary"]["answerable_covered"], 0)
        self.assertTrue(any(item["check"] == "answerable_coverage" for item in report["failures"]))
        self.assertNotIn("999", report["cases"][0]["parts"][0]["actual"]["message"])

    def test_independent_judgment_exposes_unsupported_claim_approved_by_mock_verifier(self):
        class UnsupportedWriter:
            def compose(self, request):
                part = request.parts[0]
                source = next(s for s in part.sources if s.path.endswith("/executive_summary"))
                return {"parts": [{"part_id": part.part_id, "claims": [{
                    "text": "El informe N14 confirma un robo del cajero.",
                    "source_ids": [source.source_id]}]}]}

        class IndependentReviewer:
            def review(self, _case, _index, _part):
                return {"status": "fail", "reason": "El resumen N14 no menciona un robo."}

        node = ChatConversationNode(writer=UnsupportedWriter(), verifier=SimulatedVerifier())
        unreviewed = evaluate(self.fixture, node, case_ids={"report"})
        self.assertEqual(unreviewed["summary"]["semantic_not_reviewed"], 1)
        self.assertFalse(unreviewed["acceptance"]["step4_validated"])
        reviewed = evaluate(self.fixture, node, reviewer=IndependentReviewer(), case_ids={"report"})
        self.assertEqual(reviewed["summary"]["semantic_fail"], 1)
        self.assertTrue(reviewed["acceptance"]["structural"])
        self.assertFalse(reviewed["acceptance"]["semantic"])
        self.assertTrue(any(item["check"] == "semantic" for item in reviewed["failures"]))

    def test_independent_review_requires_matching_digest_and_all_dimensions(self):
        case = next(item for item in self.fixture["cases"] if item["id"] == "result")
        node = ChatConversationNode(writer=SimulatedWriter(), verifier=SimulatedVerifier())
        part = node.answer(case["question"], build_packet(self.fixture, case), business_id="biz-a").parts[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.json"
            item = {"case_id": "result", "part_index": 0, "digest": review_digest(part),
                    "reviewer": "independent-reviewer", "supported": True,
                    "addresses_question": True, "correct_scope": True, "no_calculation": True}
            path.write_text(json.dumps({"schema_version": 1, "reviews": [item]}), encoding="utf-8")
            reviewer = FileSemanticReviewer(path)
            self.assertEqual(reviewer.review(case, 0, part)["status"], "pass")
            item["no_calculation"] = False
            path.write_text(json.dumps({"schema_version": 1, "reviews": [item]}), encoding="utf-8")
            self.assertEqual(FileSemanticReviewer(path).review(case, 0, part)["status"], "fail")
            item["digest"] = "stale"
            path.write_text(json.dumps({"schema_version": 1, "reviews": [item]}), encoding="utf-8")
            self.assertEqual(FileSemanticReviewer(path).review(case, 0, part)["status"], "not_reviewed")

    def test_report_has_denominators_cases_failures_and_limitations(self):
        report = evaluate(self.fixture, ChatConversationNode(writer=SimulatedWriter(),
                          verifier=SimulatedVerifier()))
        markdown = render_markdown(report)
        expected = report["summary"]["answerable_total"]
        self.assertIn(f"Cobertura de partes respondibles: {expected}/{expected}", markdown)
        self.assertIn("## Por caso y parte", markdown)
        self.assertIn("no validado", markdown)
        self.assertIn("not_reviewed", markdown)
        self.assertIn("## Alcance y límites", markdown)

    def test_real_adapter_requires_https_and_enforces_call_limit_before_network(self):
        with self.assertRaises(ValueError):
            BoundedCompletion("http://example.test", "secret", "model", 1)
        completion = BoundedCompletion("https://example.test", "secret", "model", 1)
        completion.calls = 1
        with self.assertRaisesRegex(RuntimeError, "Límite de llamadas"):
            completion("policy", "{}", {})
        self.assertEqual(completion.calls, 1)

    def test_synthetic_trace_requires_case_context_and_bounds_calls(self):
        calls = []
        raw = {"parts": [{"part_id": "p0", "claims": [{"text": "No calculo.", "source_ids": ["s0"]}]}]}
        trace = SyntheticDiagnosticCompletion(lambda *args: calls.append(args) or raw)
        request = json.dumps({"untrusted_data": {"parts": []}})
        with self.assertRaises(ValueError):
            trace("policy", request, {"title": "ChatModelDraft"})
        with self.assertRaises(ValueError):
            trace.begin_case("result")
        trace.begin_case("arithmetic_division")
        with self.assertRaises(ValueError):
            trace("policy", request, {"title": "Unknown"})
        self.assertEqual(calls, [])
        for _ in range(4):
            self.assertIs(trace("policy", request, {"title": "ChatModelDraft"}), raw)
        with self.assertRaises(ValueError):
            trace("policy", request, {"title": "ChatModelDraft"})
        self.assertEqual(len(calls), 4)
        self.assertEqual(len(trace.records()), 4)

    def test_synthetic_trace_does_not_copy_provider_error_details(self):
        def failing(*_args):
            raise RuntimeError("synthetic-key; private provider body and headers")
        trace = SyntheticDiagnosticCompletion(failing, secrets=("synthetic-key",))
        trace.begin_case("arithmetic_division")
        with self.assertRaises(RuntimeError):
            trace("policy", json.dumps({"untrusted_data": {"parts": []}}),
                  {"title": "ChatModelDraft"})
        records = trace.records()
        self.assertEqual(records[0]["diagnostics"], ["draft:exception:RuntimeError"])
        self.assertIsNone(records[0]["output"])
        serialized = json.dumps(records)
        self.assertNotIn("synthetic-key", serialized)
        self.assertNotIn("private provider", serialized)

    def test_synthetic_trace_redacts_active_key_without_changing_callback_result(self):
        raw = {"parts": [{"part_id": "p0", "claims": [{
            "text": "A synthetic active key: secret-for-redaction", "source_ids": ["s0"]}]}]}
        trace = SyntheticDiagnosticCompletion(lambda *_args: raw, secrets=("secret-for-redaction",))
        trace.begin_case("arithmetic_division")
        returned = trace("policy", json.dumps({"untrusted_data": {"parts": []}}),
                         {"title": "ChatModelDraft"})
        self.assertIs(returned, raw)
        self.assertIn("secret-for-redaction", json.dumps(raw))
        first = trace.records()
        self.assertNotIn("secret-for-redaction", json.dumps(first))
        self.assertIn("[REDACTED]", json.dumps(first))
        first[0]["phase"] = "modified"
        self.assertEqual(trace.records()[0]["phase"], "draft")

    def test_trace_cli_rejects_other_modes_cases_providers_and_budgets_before_client(self):
        allowed = "same_day_result_and_report,arithmetic_division"
        variants = [("simulated", "gemini", allowed, "4"),
                    ("real", "openai", allowed, "4"),
                    ("real", "gemini", "result,arithmetic_division", "4"),
                    ("real", "gemini", allowed, "14"),
                    ("real", "gemini", "arithmetic_division", "4")]
        with tempfile.TemporaryDirectory() as directory:
            for mode, provider, ids, budget in variants:
                with self.subTest(mode=mode, provider=provider, ids=ids, budget=budget), \
                     patch("sys.argv", ["chat_offline_eval", "--mode", mode, "--provider", provider,
                           "--real-case-ids", ids, "--max-calls", budget, "--synthetic-trace",
                           "--output", str(Path(directory) / "trace")]), \
                     patch("agents.chat_provider_gemini.GeminiCompletion") as client:
                    with self.assertRaises(SystemExit) as caught:
                        main()
                    self.assertEqual(caught.exception.code, 2)
                    client.assert_not_called()

    def test_trace_cli_keeps_rejected_draft_and_review_without_accepting_fallback(self):
        class Completion:
            def __init__(self, **_kwargs):
                self.calls = 0

            def __call__(self, _system, data, schema):
                self.calls += 1
                payload = json.loads(data)["untrusted_data"]
                if schema["title"] == "ChatModelDraft":
                    return SimulatedWriter().compose(ChatWritingRequest.model_validate(payload))
                request = ChatReviewRequest.model_validate(payload)
                output = SimulatedVerifier().verify(request)
                for claim, judgment in zip(request.claims, output["judgments"]):
                    if claim.kind in ("report", "calculation"):
                        judgment["supported"] = False
                        judgment["follows_policy"] = claim.kind != "calculation"
                return output

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / "diagnostic"
            with patch.dict(os.environ, {"GEMINI_API_KEY": "synthetic-cli-key",
                                        "MEPIA_CHAT_EVAL_API_KEY": "", "MEPIA_CHAT_EVAL_MODEL": ""}), \
                 patch("agents.chat_provider_gemini.GeminiCompletion", Completion), \
                 patch("sys.argv", ["chat_offline_eval", "--mode", "real", "--provider", "gemini",
                       "--real-case-ids", "same_day_result_and_report,arithmetic_division",
                       "--max-calls", "4", "--synthetic-trace", "--output", str(base)]):
                self.assertEqual(main(), 1)
            report = json.loads(base.with_suffix(".json").read_text(encoding="utf-8"))
            trace_text = base.with_name(base.name + "_synthetic_trace").with_suffix(".json").read_text(encoding="utf-8")
            trace = json.loads(trace_text)
            self.assertEqual(report["model_calls"], 4)
            self.assertEqual(report["summary"]["failure_count"], 3)
            self.assertEqual(report["summary"]["answerable_covered"], 1)
            self.assertFalse(report["acceptance"]["step4_validated"])
            self.assertEqual(trace["purpose"], "diagnostic_only_not_independent_review")
            self.assertEqual(trace["api_calls"], 4)
            self.assertEqual(trace["source_report_sha256"], hashlib.sha256(base.with_suffix(".json").read_bytes()).hexdigest())
            self.assertNotIn("synthetic-cli-key", trace_text)
            self.assertEqual([(r["case_id"], r["phase"]) for r in trace["records"]], [
                ("same_day_result_and_report", "draft"), ("same_day_result_and_report", "review"),
                ("arithmetic_division", "draft"), ("arithmetic_division", "review")])
            reviewed = trace["records"][1]
            self.assertEqual(len(reviewed["input"]["claims"]), 2)
            self.assertFalse(reviewed["output"]["judgments"][1]["supported"])
            self.assertTrue(trace["records"][0]["output"]["parts"][1]["claims"])
            self.assertEqual(report["cases"][0]["parts"][1]["actual"]["claims"], [])

    def test_ordinary_evaluation_does_not_write_diagnostic_trace(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / "ordinary"
            with patch("sys.argv", ["chat_offline_eval", "--output", str(base)]):
                self.assertEqual(main(), 0)
            self.assertTrue(base.with_suffix(".json").exists())
            self.assertFalse(base.with_name(base.name + "_synthetic_trace").with_suffix(".json").exists())


if __name__ == "__main__":
    unittest.main()
