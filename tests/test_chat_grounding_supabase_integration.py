"""Prueba integral opt-in de N15 contra el Data API de MEPIA - PRUEBAS.

La suite normal omite esta prueba. Para ejecutarla se deben definir de forma
explícita ``RUN_SUPABASE_INTEGRATION=1`` y ``MEPIA_TEST_PROJECT_REF``. El test
crea negocios y filas de auditoría con UUID nuevos y elimina exactamente esas
filas en un bloque ``finally``.
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import pytest
from dotenv import dotenv_values
from supabase import create_client

from agents.chat_grounding import ChatGroundingService


_ROOT = Path(__file__).resolve().parents[1]


def _integration_config() -> tuple[str, str, str]:
    if os.environ.get("RUN_SUPABASE_INTEGRATION") != "1":
        pytest.skip("prueba Supabase opt-in; RUN_SUPABASE_INTEGRATION != 1")

    file_config = dotenv_values(_ROOT / "api" / ".env")
    supabase_url = os.environ.get("SUPABASE_URL") or file_config.get("SUPABASE_URL")
    service_key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or file_config.get("SUPABASE_SERVICE_ROLE_KEY")
    )
    environment = os.environ.get("ENVIRONMENT") or file_config.get("ENVIRONMENT")
    expected_ref = os.environ.get("MEPIA_TEST_PROJECT_REF")

    assert supabase_url, "SUPABASE_URL no configurada"
    assert service_key, "SUPABASE_SERVICE_ROLE_KEY no configurada"
    assert environment == "dev", "la integración solo puede ejecutarse con ENVIRONMENT=dev"
    assert expected_ref, "MEPIA_TEST_PROJECT_REF es obligatorio"

    actual_ref = urlparse(str(supabase_url)).hostname.split(".")[0]
    assert actual_ref == expected_ref, (
        "SUPABASE_URL no corresponde al proyecto de pruebas autorizado"
    )
    return str(supabase_url), str(service_key), expected_ref


def test_grounding_integral_con_data_api_real() -> None:
    supabase_url, service_key, _ = _integration_config()
    db = create_client(supabase_url, service_key)
    grounding = ChatGroundingService(db)

    token = uuid4().hex[:12]
    business_a = str(uuid4())
    business_b = str(uuid4())
    business_empty = str(uuid4())
    business_ids = [business_a, business_b, business_empty]

    date_lineage = "2099-12-30"
    date_missing_latest_n14 = "2099-12-31"
    date_status_filter = "2099-12-29"

    s3_old = str(uuid4())
    s3_latest = str(uuid4())
    n14_old = str(uuid4())
    n14_latest = str(uuid4())
    s3_other_business = str(uuid4())
    n14_other_business = str(uuid4())
    s3_missing_old = str(uuid4())
    s3_missing_latest = str(uuid4())
    n14_missing_old = str(uuid4())
    s3_behind_failures = str(uuid4())
    failed_s3_ids = [str(uuid4()) for _ in range(5)]
    audit_ids = [
        s3_old,
        s3_latest,
        n14_old,
        n14_latest,
        s3_other_business,
        n14_other_business,
        s3_missing_old,
        s3_missing_latest,
        n14_missing_old,
        s3_behind_failures,
        *failed_s3_ids,
    ]

    businesses = [
        {
            "id": business_a,
            "business_name": f"__mepia_chat_integration_a_{token}",
            "industry_sector": "integration_test",
            "currency": "MXN",
        },
        {
            "id": business_b,
            "business_name": f"__mepia_chat_integration_b_{token}",
            "industry_sector": "integration_test",
            "currency": "MXN",
        },
        {
            "id": business_empty,
            "business_name": f"__mepia_chat_integration_empty_{token}",
            "industry_sector": "integration_test",
            "currency": "MXN",
        },
    ]

    s3_rows = [
        {
            "id": s3_old,
            "source_s3_result_id": s3_old,
            "business_id": business_a,
            "date": date_lineage,
            "pipeline_layer": "sequential",
            "node_id": "S3",
            "module": f"chat_grounding_integral_{token}",
            "node_status": "success",
            "created_at": "2099-12-30T08:00:00+00:00",
            "result_data": {
                "results": [
                    {
                        "metric": "integral_old_metric",
                        "value": 10,
                        "unit": "MXN",
                        "status": "ok",
                        "context": {"run": "old"},
                        "private_metric_field": "must_not_leak",
                    }
                ],
                "instructions": "must_not_leak",
            },
        },
        {
            "id": s3_latest,
            "source_s3_result_id": s3_latest,
            "business_id": business_a,
            "date": date_lineage,
            "pipeline_layer": "sequential",
            "node_id": "S3",
            "module": f"chat_grounding_integral_{token}",
            "node_status": "success",
            "created_at": "2099-12-30T10:00:00+00:00",
            "result_data": {
                "results": [
                    {
                        "metric": "integral_latest_metric",
                        "value": 222,
                        "unit": "MXN",
                        "status": "warning",
                        "context": {"run": "latest"},
                        "private_metric_field": "must_not_leak",
                    }
                ],
                "instructions": "must_not_leak",
            },
        },
        {
            "id": s3_other_business,
            "source_s3_result_id": s3_other_business,
            "business_id": business_b,
            "date": date_lineage,
            "pipeline_layer": "sequential",
            "node_id": "S3",
            "module": f"chat_grounding_integral_{token}",
            "node_status": "success",
            "created_at": "2099-12-30T11:00:00+00:00",
            "result_data": {
                "results": [
                    {
                        "metric": "other_business_metric",
                        "value": 999999,
                        "unit": "MXN",
                        "status": "critical",
                        "context": {"business": "other"},
                    }
                ]
            },
        },
        {
            "id": s3_missing_old,
            "source_s3_result_id": s3_missing_old,
            "business_id": business_a,
            "date": date_missing_latest_n14,
            "pipeline_layer": "sequential",
            "node_id": "S3",
            "module": f"chat_grounding_integral_{token}",
            "node_status": "success",
            "created_at": "2099-12-31T08:00:00+00:00",
            "result_data": {
                "results": [
                    {
                        "metric": "missing_old_metric",
                        "value": 1,
                        "unit": "MXN",
                        "status": "ok",
                        "context": {},
                    }
                ]
            },
        },
        {
            "id": s3_missing_latest,
            "source_s3_result_id": s3_missing_latest,
            "business_id": business_a,
            "date": date_missing_latest_n14,
            "pipeline_layer": "sequential",
            "node_id": "S3",
            "module": f"chat_grounding_integral_{token}",
            "node_status": "success",
            "created_at": "2099-12-31T10:00:00+00:00",
            "result_data": {
                "results": [
                    {
                        "metric": "missing_latest_metric",
                        "value": 2,
                        "unit": "MXN",
                        "status": "warning",
                        "context": {},
                    }
                ]
            },
        },
        {
            "id": s3_behind_failures,
            "source_s3_result_id": s3_behind_failures,
            "business_id": business_a,
            "date": date_status_filter,
            "pipeline_layer": "sequential",
            "node_id": "S3",
            "module": f"chat_grounding_integral_{token}",
            "node_status": "success",
            "created_at": "2099-12-29T01:00:00+00:00",
            "result_data": {
                "results": [
                    {
                        "metric": "success_behind_failures",
                        "value": 7,
                        "unit": "count",
                        "status": "ok",
                        "context": {},
                    }
                ]
            },
        },
    ]

    for index, failed_id in enumerate(failed_s3_ids, start=2):
        s3_rows.append(
            {
                "id": failed_id,
                "source_s3_result_id": failed_id,
                "business_id": business_a,
                "date": date_status_filter,
                "pipeline_layer": "sequential",
                "node_id": "S3",
                "module": f"chat_grounding_integral_{token}",
                "node_status": "failed",
                "created_at": f"2099-12-29T0{index}:00:00+00:00",
                "result_data": {"results": []},
            }
        )

    n14_rows = [
        {
            "id": n14_old,
            "source_s3_result_id": s3_old,
            "business_id": business_a,
            "date": date_lineage,
            "pipeline_layer": "loop",
            "node_id": "N14",
            "module": f"chat_grounding_integral_{token}",
            "node_status": "success",
            "created_at": "2099-12-30T12:00:00+00:00",
            "result_data": {
                "source_s3_result_id": s3_old,
                "executive_summary": "old report must not be selected",
                "instructions": "must_not_leak",
            },
        },
        {
            "id": n14_latest,
            "source_s3_result_id": s3_latest,
            "business_id": business_a,
            "date": date_lineage,
            "pipeline_layer": "loop",
            "node_id": "N14",
            "module": f"chat_grounding_integral_{token}",
            "node_status": "success",
            "created_at": "2099-12-30T10:30:00+00:00",
            "result_data": {
                "source_s3_result_id": s3_latest,
                "executive_summary": "latest exact lineage report",
                "operational_narrative_md": "verified narrative",
                "pragmatic_actions": ["verified action"],
                "draft_status": "approved",
                "instructions": "must_not_leak",
                "private_report_field": "must_not_leak",
            },
        },
        {
            "id": n14_other_business,
            "source_s3_result_id": s3_other_business,
            "business_id": business_b,
            "date": date_lineage,
            "pipeline_layer": "loop",
            "node_id": "N14",
            "module": f"chat_grounding_integral_{token}",
            "node_status": "success",
            "created_at": "2099-12-30T11:30:00+00:00",
            "result_data": {
                "source_s3_result_id": s3_other_business,
                "executive_summary": "other business must not leak",
            },
        },
        {
            "id": n14_missing_old,
            "source_s3_result_id": s3_missing_old,
            "business_id": business_a,
            "date": date_missing_latest_n14,
            "pipeline_layer": "loop",
            "node_id": "N14",
            "module": f"chat_grounding_integral_{token}",
            "node_status": "success",
            "created_at": "2099-12-31T12:00:00+00:00",
            "result_data": {
                "source_s3_result_id": s3_missing_old,
                "executive_summary": "older run must not be fallback",
            },
        },
    ]

    try:
        db.table("businesses").insert(businesses).execute()
        db.table("audit_results").insert(s3_rows).execute()
        db.table("audit_results").insert(n14_rows).execute()

        packet = grounding.build_packet(business_a, date_lineage)
        packet_other = grounding.build_packet(business_b, date_lineage)
        packet_missing = grounding.build_packet(
            business_a, date_missing_latest_n14
        )
        packet_filtered = grounding.build_packet(business_a, date_status_filter)
        packet_empty = grounding.build_packet(business_empty)

        assert packet.source_s3_result_id == s3_latest
        assert packet.metrics == [
            {
                "metric": "integral_latest_metric",
                "value": 222,
                "unit": "MXN",
                "status": "warning",
                "context": {"run": "latest"},
            }
        ]
        assert packet.final_report["source_s3_result_id"] == s3_latest
        assert packet.final_report["executive_summary"] == "latest exact lineage report"
        assert "instructions" not in packet.final_report
        assert "private_report_field" not in packet.final_report
        assert [item.audit_result_id for item in packet.evidence] == [
            s3_latest,
            n14_latest,
        ]
        assert packet.missing_data == []

        assert packet_other.source_s3_result_id == s3_other_business
        assert packet_other.metrics[0]["metric"] == "other_business_metric"
        assert packet_other.final_report["executive_summary"] == (
            "other business must not leak"
        )
        assert all(
            item.audit_result_id not in {s3_latest, n14_latest}
            for item in packet_other.evidence
        )

        assert packet_missing.source_s3_result_id == s3_missing_latest
        assert packet_missing.metrics[0]["metric"] == "missing_latest_metric"
        assert packet_missing.final_report is None
        assert "final_report_not_found" in packet_missing.missing_data
        assert [item.audit_result_id for item in packet_missing.evidence] == [
            s3_missing_latest
        ]

        assert packet_filtered.source_s3_result_id == s3_behind_failures
        assert packet_filtered.metrics[0]["metric"] == "success_behind_failures"

        assert packet_empty.metrics == []
        assert packet_empty.final_report is None
        assert packet_empty.evidence == []
        assert set(packet_empty.missing_data) == {
            "metrics_not_found",
            "final_report_not_found",
            "no_audit_results",
        }
    finally:
        db.table("audit_results").delete().in_("id", audit_ids).execute()
        db.table("businesses").delete().in_("id", business_ids).execute()

        remaining_audits = (
            db.table("audit_results").select("id").in_("id", audit_ids).execute()
        )
        remaining_businesses = (
            db.table("businesses").select("id").in_("id", business_ids).execute()
        )
        assert remaining_audits.data == []
        assert remaining_businesses.data == []
