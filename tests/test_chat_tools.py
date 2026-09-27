"""Pruebas de las herramientas deterministas de consulta del chatbot."""
import inspect
import unittest

from agents.gatekeeper import GatekeeperAgent
from agents.chat_grounding import ChatEvidenceReference, ChatGroundingPacket
from agents.chat_metric_catalog import (
    ENGINE_SUPPORT_METRIC_IDS,
    METRIC_CATALOG,
    PIPELINE_METRIC_IDS,
)
from agents.chat_tools import ChatQueryTools


S3_ID = "a452b0e2-c40a-42d5-8d90-901b56c7eed1"
N14_ID = "d0387b7d-4859-48ef-b188-bae602bcf860"


def _packet(
    *,
    metrics=None,
    final_report=None,
    include_s3_evidence=True,
    include_n14_evidence=True,
):
    evidence = []
    if include_s3_evidence:
        evidence.append(
            ChatEvidenceReference(
                audit_result_id=S3_ID,
                node_id="S3",
                date="2026-09-24",
                created_at="2026-09-24T18:00:00Z",
                source_s3_result_id=S3_ID,
            )
        )
    if include_n14_evidence:
        evidence.append(
            ChatEvidenceReference(
                audit_result_id=N14_ID,
                node_id="N14",
                date="2026-09-24",
                created_at="2026-09-24T18:05:00Z",
                source_s3_result_id=S3_ID,
            )
        )
    return ChatGroundingPacket(
        business_id="biz-a",
        resolved_date="2026-09-24",
        source_s3_result_id=S3_ID,
        metrics=metrics
        if metrics is not None
        else [
            {
                "metric": "avg_ticket",
                "value": 125,
                "unit": "MXN",
                "status": "ok",
                "context": "subtotal / tickets",
            },
            {
                "metric": "cash_reconciliation",
                "value": -420,
                "unit": "MXN",
                "status": "critical",
                "context": "faltante de caja",
            },
        ],
        final_report=final_report
        if final_report is not None
        else {
            "source_s3_result_id": S3_ID,
            "executive_summary": "Hay un faltante de caja.",
            "pragmatic_actions": [{"action": "Revisar el corte."}],
            "draft_status": "approved",
        },
        evidence=evidence,
        missing_data=[],
        built_at="2026-09-24T18:06:00Z",
    )


class ChatQueryToolsTests(unittest.TestCase):
    def test_lists_metrics_and_filters_by_valid_status(self):
        tools = ChatQueryTools(_packet())

        all_metrics = tools.list_metrics()
        critical = tools.list_metrics("CRITICAL")

        self.assertEqual(all_metrics.status, "ok")
        self.assertEqual(all_metrics.data["count"], 2)
        self.assertEqual(critical.status, "ok")
        self.assertEqual(critical.data["count"], 1)
        self.assertEqual(critical.data["metrics"][0]["metric"], "cash_reconciliation")
        self.assertEqual([item.node_id for item in critical.evidence], ["S3"])

    def test_invalid_or_empty_metric_selectors_are_explicit(self):
        tools = ChatQueryTools(_packet())

        invalid_status = tools.list_metrics("urgent")
        empty_name = tools.get_metric("   ")

        self.assertEqual(invalid_status.status, "invalid_request")
        self.assertEqual(invalid_status.missing_data, ["invalid_metric_status"])
        self.assertEqual(empty_name.status, "invalid_request")
        self.assertEqual(empty_name.missing_data, ["metric_name_required"])

    def test_get_metric_supports_exact_canonical_name_and_curated_alias(self):
        tools = ChatQueryTools(_packet())

        canonical = tools.get_metric("avg_ticket")
        alias = tools.get_metric("Tícket promedio")
        partial = tools.get_metric("tick")

        self.assertEqual(canonical.status, "ok")
        self.assertEqual(alias.status, "ok")
        self.assertEqual(alias.data["metrics"][0]["metric"], "avg_ticket")
        self.assertEqual(partial.status, "not_found")
        self.assertEqual(partial.data["metrics"], [])

    def test_metric_tools_reapply_allowlist_and_never_return_n14_evidence(self):
        packet = _packet(
            metrics=[
                {
                    "metric": "avg_ticket",
                    "value": 125,
                    "unit": "MXN",
                    "status": "ok",
                    "context": "subtotal / tickets",
                    "internal_prompt": "dato no autorizado",
                }
            ]
        )

        result = ChatQueryTools(packet).get_metric("avg_ticket")
        serialized = str(result.model_dump())

        self.assertEqual(result.status, "ok")
        self.assertNotIn("internal_prompt", serialized)
        self.assertNotIn("dato no autorizado", serialized)
        self.assertEqual([item.node_id for item in result.evidence], ["S3"])

    def test_metrics_without_s3_evidence_are_not_exposed(self):
        result = ChatQueryTools(
            _packet(include_s3_evidence=False)
        ).list_metrics()

        self.assertEqual(result.status, "missing_data")
        self.assertEqual(result.data, {})
        self.assertEqual(result.missing_data, ["metric_evidence_not_found"])

    def test_metrics_with_evidence_from_another_root_are_not_exposed(self):
        packet = _packet()
        packet.evidence[0].audit_result_id = (
            "4ba5991e-90dc-41d6-b3b6-a45e20141179"
        )

        result = ChatQueryTools(packet).list_metrics()

        self.assertEqual(result.status, "missing_data")
        self.assertEqual(result.data, {})
        self.assertEqual(result.missing_data, ["metric_evidence_not_found"])

    def test_report_can_return_full_allowlisted_payload_or_one_section(self):
        packet = _packet()
        packet.final_report["internal_notes"] = "no autorizado"
        tools = ChatQueryTools(packet)

        full_report = tools.get_final_report()
        summary = tools.get_final_report("Resumen ejecutivo")

        self.assertEqual(full_report.status, "ok")
        self.assertNotIn("internal_notes", str(full_report.model_dump()))
        self.assertEqual(summary.status, "ok")
        self.assertEqual(summary.data["section"], "executive_summary")
        self.assertEqual(summary.data["value"], "Hay un faltante de caja.")
        self.assertEqual([item.node_id for item in summary.evidence], ["N14"])

    def test_invalid_missing_or_unverified_report_sections_are_explicit(self):
        tools = ChatQueryTools(_packet())

        invalid = tools.get_final_report("secreto interno")
        absent = tools.get_final_report("advertencias")
        unverified = ChatQueryTools(
            _packet(include_n14_evidence=False)
        ).get_final_report()

        self.assertEqual(invalid.status, "invalid_request")
        self.assertEqual(absent.status, "not_found")
        self.assertEqual(
            absent.missing_data,
            ["report_section_not_found:quality_warnings"],
        )
        self.assertEqual(unverified.status, "missing_data")
        self.assertEqual(unverified.data, {})
        self.assertEqual(unverified.missing_data, ["report_evidence_not_found"])

    def test_report_with_evidence_from_another_root_is_not_exposed(self):
        packet = _packet()
        packet.evidence[1].source_s3_result_id = (
            "4ba5991e-90dc-41d6-b3b6-a45e20141179"
        )

        result = ChatQueryTools(packet).get_final_report()

        self.assertEqual(result.status, "missing_data")
        self.assertEqual(result.data, {})
        self.assertEqual(result.missing_data, ["report_evidence_not_found"])

    def test_report_uses_packet_lineage_instead_of_conflicting_payload_copy(self):
        packet = _packet()
        conflicting_id = "4ba5991e-90dc-41d6-b3b6-a45e20141179"
        packet.final_report["source_s3_result_id"] = conflicting_id

        result = ChatQueryTools(packet).get_final_report("linaje")

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data["value"], S3_ID)
        self.assertNotIn(conflicting_id, str(result.model_dump()))

    def test_glossary_is_curated_accent_insensitive_and_not_business_evidence(self):
        tools = ChatQueryTools(_packet())

        entry = tools.lookup_glossary("Margen de contribución")
        catalog = tools.lookup_glossary()
        unknown = tools.lookup_glossary("utilidad magica")

        self.assertEqual(entry.status, "ok")
        self.assertEqual(entry.data["entry"]["term"], "margen_contribucion")
        self.assertEqual(entry.evidence, [])
        self.assertEqual(
            entry.data["source"], "mepia_engine_concept_glossary_v2"
        )
        self.assertGreaterEqual(catalog.data["count"], 35)
        self.assertEqual(unknown.status, "not_found")

    def test_catalog_covers_every_gatekeeper_metric_without_drift(self):
        self.assertEqual(PIPELINE_METRIC_IDS, frozenset(GatekeeperAgent.METRICS))
        self.assertEqual(len(PIPELINE_METRIC_IDS), 31)
        self.assertEqual(
            ENGINE_SUPPORT_METRIC_IDS,
            {"contribution_margin", "waste_analysis", "burn_rate", "price_inflation"},
        )

    def test_every_metric_definition_is_explainable_and_engine_owned(self):
        for definition in METRIC_CATALOG:
            with self.subTest(metric=definition.metric_id):
                self.assertTrue(definition.definition)
                self.assertTrue(definition.interpretation)
                self.assertTrue(definition.formula_explanation)
                self.assertTrue(definition.inputs)
                self.assertTrue(definition.units)
                self.assertTrue(definition.result_metric_names)
                self.assertEqual(
                    definition.calculation_owner, "deterministic_engine"
                )

    def test_catalog_is_scoped_and_distinguishes_pipeline_from_support(self):
        tools = ChatQueryTools(_packet())

        full = tools.list_metric_catalog()
        pipeline = tools.list_metric_catalog("pipeline")
        support = tools.list_metric_catalog("engine support")
        invalid = tools.list_metric_catalog("externa")

        self.assertEqual(full.status, "ok")
        self.assertEqual(full.data["count"], 35)
        self.assertEqual(pipeline.data["count"], 31)
        self.assertEqual(support.data["count"], 4)
        self.assertEqual(invalid.status, "invalid_request")
        self.assertEqual(full.evidence, [])

    def test_describe_metric_exposes_formula_as_text_not_an_executor(self):
        result = ChatQueryTools(_packet()).describe_metric("ticket promedio")

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.data["definitions"][0]["metric_id"], "avg_ticket")
        self.assertTrue(result.data["formula_is_explanatory_only"])
        self.assertFalse(result.calculation_allowed)
        self.assertEqual(result.knowledge_scope, "engine_metric_domain")

    def test_legacy_metric_names_have_honest_limitations(self):
        tools = ChatQueryTools(_packet())

        operative = tools.describe_metric("operative_cost_margin")
        health = tools.describe_metric("health_score")
        inventory = tools.describe_metric("inventory_variance")

        self.assertIn("no un porcentaje", operative.data["definitions"][0]["limitations"][0])
        self.assertIn("No combina", health.data["definitions"][0]["limitations"][0])
        self.assertTrue(inventory.data["definitions"][0]["result_metric_prefixes"])

    def test_metric_aliases_match_actual_and_dynamic_engine_result_names(self):
        packet = _packet(
            metrics=[
                {"metric": "ticket_promedio", "value": 125, "unit": "MXN", "status": "ok", "context": {}},
                {"metric": "conciliacion_caja", "value": -420, "unit": "MXN", "status": "critical", "context": {}},
                {"metric": "inventory_variance_merma", "value": 3, "unit": "%", "status": "warning", "context": {}},
            ]
        )
        tools = ChatQueryTools(packet)

        self.assertEqual(tools.get_metric("avg_ticket").data["count"], 1)
        self.assertEqual(tools.get_metric("cash reconciliation").data["count"], 1)
        self.assertEqual(tools.get_metric("variacion de inventario").data["count"], 1)

    def test_glossary_rejects_general_finance_outside_engine_domain(self):
        tools = ChatQueryTools(_packet())

        self.assertEqual(tools.lookup_glossary("bitcoin").status, "not_found")
        self.assertEqual(tools.lookup_glossary("hipoteca").status, "not_found")

    def test_calculation_requests_have_a_deterministic_absolute_refusal(self):
        result = ChatQueryTools(_packet()).refuse_calculation(
            "Suma las ventas y proyecta el proximo mes"
        )

        self.assertEqual(result.status, "not_allowed")
        self.assertEqual(result.missing_data, ["calculation_not_allowed"])
        self.assertEqual(result.evidence, [])
        self.assertFalse(result.calculation_allowed)
        self.assertIn("calculate", result.data["prohibited_operations"])
        self.assertIn("project", result.data["prohibited_operations"])

    def test_public_tools_do_not_accept_numeric_operands(self):
        forbidden_parameter_names = {
            "value", "amount", "operand", "numerator", "denominator", "rate"
        }
        for method_name in (
            "list_metrics", "get_metric", "get_final_report",
            "list_metric_catalog", "describe_metric", "lookup_glossary",
            "refuse_calculation",
        ):
            with self.subTest(method=method_name):
                parameters = set(
                    inspect.signature(getattr(ChatQueryTools, method_name)).parameters
                )
                self.assertFalse(parameters & forbidden_parameter_names)

    def test_every_tool_result_declares_calculation_is_disabled(self):
        tools = ChatQueryTools(_packet())
        results = (
            tools.list_metrics(),
            tools.get_metric("avg_ticket"),
            tools.get_final_report(),
            tools.list_metric_catalog(),
            tools.describe_metric("avg_ticket"),
            tools.lookup_glossary("ticket"),
            tools.refuse_calculation(),
        )
        for result in results:
            with self.subTest(tool=result.tool):
                self.assertFalse(result.calculation_allowed)
                self.assertEqual(result.knowledge_scope, "engine_metric_domain")

    def test_tools_copy_packet_and_results_to_prevent_cross_call_mutation(self):
        packet = _packet()
        tools = ChatQueryTools(packet)
        packet.metrics[0]["value"] = 999999

        first = tools.get_metric("avg_ticket")
        first.data["metrics"][0]["value"] = -1
        second = tools.get_metric("avg_ticket")

        self.assertEqual(second.data["metrics"][0]["value"], 125)


if __name__ == "__main__":
    unittest.main()
