"""Lectura del Dashboard. Nunca recalcula ni modifica auditorías históricas."""
from copy import deepcopy
from uuid import UUID


def restore_result(row: dict, db) -> dict:
    data = deepcopy(row.get("result_data") or {})
    sequence = data.get("sequential_results")
    has_sequence = isinstance(sequence, dict) and isinstance(sequence.get("calc_results"), list)
    if not has_sequence:
        sequence = {
            "active_metrics": [], "calc_results": [],
            "forensic_report": data.get("forensic_report") or {
                "business_id": row["business_id"], "date": row["date"], "risk_level": "low",
                "anomalies": [], "evidence_sources": [], "observed_causality": None,
                "generated_at": row.get("created_at"),
            },
            "audit_insights": data.get("audit_insights") or [],
        }
        column = row.get("source_s3_result_id")
        payload = data.get("source_s3_result_id")
        source = column or payload
        # Un conflicto de linaje nunca se resuelve buscando otro análisis cercano.
        if source and not (column and payload and column != payload):
            try:
                source = str(UUID(source))
            except (ValueError, TypeError, AttributeError):
                source = None
            if source:
                records = (db.table("audit_results").select("result_data,node_status")
                    .eq("id", source).eq("node_id", "S3")
                    .eq("business_id", row["business_id"]).eq("date", row["date"])
                    .execute().data)
                if len(records) == 1 and records[0].get("node_status") in ("success", "completed"):
                    results = (records[0].get("result_data") or {}).get("results")
                    if isinstance(results, list):
                        sequence["calc_results"] = results

    # S3 histórico no conserva S2: no inventar faltantes ni consultar su estado actual.
    available = (has_sequence and isinstance(sequence.get("active_metrics"), list)
        and isinstance(data.get("dormant_metrics"), list)
        and isinstance(data.get("blocked_metrics"), list)
        and data.get("metric_status_available", True) is True)
    return {
        "run_id": row["id"], "business_id": row["business_id"], "date": row["date"],
        "archetype": data.get("archetype", row.get("archetype", "Operative Genius")),
        "pipeline_status": data.get("pipeline_status", "completed"),
        "sequential_results": sequence,
        "escalation": data.get("escalation") or {"triggered": False, "reason": None, "layer2_run_id": None},
        "dormant_metrics": data.get("dormant_metrics") or [],
        "blocked_metrics": data.get("blocked_metrics") or [],
        "metric_status_available": available,
        "completed_at": row.get("created_at"),
    }
