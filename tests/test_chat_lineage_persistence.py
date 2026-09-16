"""Pruebas del identificador de linaje persistido desde S3 hasta N14."""
import unittest
from types import SimpleNamespace
from uuid import uuid4

from agents.calc_engine import run_calc_engine
from agents.ceo_orchestrator import N05CEOOrchestrator
from agents.n14_informe_final import FinalReport, _persist_n14
from agents.parallel_orchestrator import (
    ContextTags,
    Layer2RunPayload,
    N06ParallelOrchestrator,
    NodeResult,
    SequentialContext,
)


class _Response:
    data = []


class _InsertQuery:
    def __init__(self, db, table_name):
        self._db = db
        self._table_name = table_name

    def insert(self, row):
        self._db.inserted.append((self._table_name, row))
        return self

    def execute(self):
        return _Response()


class _CaptureDB:
    def __init__(self):
        self.inserted = []

    def table(self, table_name):
        return _InsertQuery(self, table_name)


def _sequential_context():
    return SequentialContext(
        business_id=str(uuid4()),
        active_metrics=[],
        calc_results=[],
        forensic_report={},
        insights=[],
        context_tags=ContextTags(),
    )


class ChatLineagePersistenceTests(unittest.TestCase):
    def test_s3_row_uses_its_own_id_as_lineage_root(self):
        db = _CaptureDB()

        result = run_calc_engine(
            {
                "active_metrics": [],
                "dormant_metrics": [],
                "blocked_metrics": [],
            },
            db,
            "2026-09-02",
            str(uuid4()),
        )

        row = db.inserted[-1][1]
        self.assertEqual(row["node_id"], "S3")
        self.assertEqual(row["id"], result.run_id)
        self.assertEqual(row["source_s3_result_id"], result.run_id)

    def test_n05_passes_s3_root_into_layer2_trigger(self):
        source_s3_result_id = str(uuid4())
        captured = {}
        orchestrator = N05CEOOrchestrator.__new__(N05CEOOrchestrator)
        orchestrator._trigger_layer2 = lambda **kwargs: captured.update(kwargs)

        escalation = orchestrator._evaluate_escalation(
            forensic_report=SimpleNamespace(risk_level="high"),
            escalate_to_parallel=True,
            run_id=str(uuid4()),
            source_s3_result_id=source_s3_result_id,
            business_id=str(uuid4()),
            date="2026-09-02",
            archetype="Operative Genius",
            temporalidad="short",
            calc_results=[],
            audit_insights=[],
            active_metrics=[],
        )

        self.assertTrue(escalation.triggered)
        self.assertEqual(captured["source_s3_result_id"], source_s3_result_id)

    def test_n06_result_and_row_preserve_s3_root(self):
        source_s3_result_id = str(uuid4())
        payload = Layer2RunPayload(
            layer2_run_id=str(uuid4()),
            sequential_run_id=str(uuid4()),
            source_s3_result_id=source_s3_result_id,
            business_id=str(uuid4()),
            date="2026-09-02",
            archetype="Operative Genius",
            temporalidad="short",
            sequential_context=_sequential_context(),
        )
        node_results = [
            NodeResult(
                node_id=node_id,
                node_name=node_name,
                status="error",
                error_detail="test",
                duration_ms=0,
            )
            for node_id, node_name in (
                ("N07", "conciliacion"),
                ("N08", "pld"),
                ("N09", "gastos"),
            )
        ]
        db = _CaptureDB()
        orchestrator = N06ParallelOrchestrator(db)

        result = orchestrator._gather(payload, node_results)
        orchestrator._persist(result, payload.sequential_context)

        row = db.inserted[-1][1]
        self.assertEqual(result.source_s3_result_id, source_s3_result_id)
        self.assertEqual(row["source_s3_result_id"], source_s3_result_id)
        self.assertEqual(
            row["result_data"]["source_s3_result_id"],
            source_s3_result_id,
        )

    def test_n14_row_and_report_preserve_s3_root(self):
        source_s3_result_id = str(uuid4())
        db = _CaptureDB()
        report = FinalReport(
            layer3_run_id=str(uuid4()),
            business_id=str(uuid4()),
            date="2026-09-02",
            archetype="Operative Genius",
            temporalidad="short",
            executive_summary="Resumen verificable.",
            operational_narrative_md="Narrativa verificable.",
            pragmatic_actions=[],
            draft_status="approved",
            model_used="test",
            intentos_critico=0,
            quality_warnings=[],
            finalized_at="2026-09-02T21:00:00+00:00",
            layer3_duration_ms=1,
            source_s3_result_id=source_s3_result_id,
        )

        self.assertTrue(_persist_n14(db, report, report.layer3_run_id))

        row = db.inserted[-1][1]
        self.assertEqual(row["source_s3_result_id"], source_s3_result_id)
        self.assertEqual(
            row["result_data"]["source_s3_result_id"],
            source_s3_result_id,
        )


if __name__ == "__main__":
    unittest.main()
