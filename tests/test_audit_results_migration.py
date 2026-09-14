"""Pruebas de regresion para la normalizacion legacy de audit_results."""
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATHS = (
    ROOT / "supabase" / "migrations" / "008_audit_results_runtime_contract.sql",
    ROOT / "supabase" / "migrations" / "APPLY_ALL.sql",
)

EXPECTED_MAPPINGS = {
    "success": "success",
    "completed": "success",
    "complete": "success",
    "approved": "success",
    "approved_with_warning_cortafuegos": "success",
    "partial": "partial",
    "rejected": "partial",
    "pending": "partial",
    "failed": "failed",
    "timeout": "timeout",
    "error": "error",
}


def _normalization_statement(sql: str) -> str:
    match = re.search(
        r"UPDATE audit_results\s+SET node_status = CASE.*?WHERE node_status IS NOT NULL;",
        sql,
        flags=re.DOTALL,
    )
    if match is None:
        raise AssertionError("No se encontro el UPDATE de normalizacion")
    return match.group(0)


class AuditResultsMigrationTests(unittest.TestCase):
    def test_normalizes_before_installing_status_constraint(self):
        for path in MIGRATION_PATHS:
            with self.subTest(path=path.name):
                sql = path.read_text(encoding="utf-8")
                drop_position = sql.index(
                    "DROP CONSTRAINT IF EXISTS audit_results_node_status_check"
                )
                update_position = sql.index("UPDATE audit_results", drop_position)
                add_position = sql.index(
                    "ADD CONSTRAINT audit_results_node_status_check", update_position
                )

                self.assertLess(drop_position, update_position)
                self.assertLess(update_position, add_position)

    def test_both_scripts_use_the_same_legacy_mapping(self):
        statements = []

        for path in MIGRATION_PATHS:
            sql = path.read_text(encoding="utf-8")
            statement = _normalization_statement(sql)
            statements.append(statement)

            for old_status, new_status in EXPECTED_MAPPINGS.items():
                self.assertIn(
                    f"WHEN '{old_status}' THEN '{new_status}'",
                    statement,
                    msg=f"Falta el mapeo {old_status} -> {new_status} en {path.name}",
                )

            self.assertIn("ELSE 'error'", statement)

        self.assertEqual(statements[0], statements[1])


if __name__ == "__main__":
    unittest.main()
