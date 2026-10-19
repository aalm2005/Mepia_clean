"""N10 protegido: propiedad, persistencia y valores iniciales sin gastos inventados."""
from copy import deepcopy
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.onboarding import create_onboarding_router
from tests.onboarding_fixtures import DEFAULT_ONBOARDING, OnboardingDB, seed_settings
from tests.test_chat_api import AUTH, BIZ_A, BIZ_B, BIZ_C, USER_A, USER_B, headers, token


@pytest.fixture
def setup():
    db = OnboardingDB()
    factory_calls = []
    def factory():
        factory_calls.append(1)
        return db
    app = FastAPI()
    app.include_router(create_onboarding_router(auth=AUTH, db_factory=factory))
    with TestClient(app) as client:
        yield client, db, factory_calls


def request(client, method="GET", bid=BIZ_A, authorization=None, payload=None):
    path = f"/business/{bid}/onboarding" + ("/status" if method == "GET" else "")
    return client.request(method, path, headers=authorization or {},
                          json=payload if method != "GET" else None)


@pytest.mark.parametrize("method", ["GET", "POST", "PUT"])
@pytest.mark.parametrize("authorization", [None, {"Authorization": "Basic invalid"},
                                           {"Authorization": "Bearer invalid"},
                                           {"Authorization": "Bearer " + token(exp=1)},
                                           {"Authorization": "Bearer " + token(role="anon")}])
def test_anonymous_or_invalid_session_never_creates_db(setup, method, authorization):
    client, db, factory = setup
    response = request(client, method, authorization=authorization, payload=deepcopy(DEFAULT_ONBOARDING))
    assert response.status_code == 401
    assert db.calls == factory == []
    assert all(not rows for rows in db.settings.values())


@pytest.mark.parametrize("method", ["GET", "POST", "PUT"])
@pytest.mark.parametrize("bid", [BIZ_B, str(uuid4()), BIZ_C])
def test_foreign_missing_and_ownerless_business_rejected_before_settings(setup, method, bid):
    client, db, _ = setup
    db.businesses[2]["owner_id"] = None
    response = request(client, method, bid=bid, authorization=headers(), payload=deepcopy(DEFAULT_ONBOARDING))
    assert response.status_code == 403
    assert db.calls == ["businesses"]
    assert all(not rows for rows in db.settings.values())


def test_defaults_save_without_costs_and_load_in_display_units(setup):
    client, db, _ = setup
    empty = request(client, authorization=headers()).json()
    assert empty["onboarding_complete"] is False and empty["settings"] is None
    created = request(client, "POST", authorization=headers(), payload=deepcopy(DEFAULT_ONBOARDING))
    assert created.status_code == 201
    assert created.headers["cache-control"] == "private, no-store"
    loaded = request(client, authorization=headers())
    assert loaded.status_code == 200
    assert loaded.json()["settings"] == DEFAULT_ONBOARDING
    assert loaded.json()["onboarding_complete"] is True and loaded.json()["has_cost_structure"] is False
    assert db.settings["business_fixed_costs"] == [] and len(db.settings["mepia_memory"]) == 1


def test_repeated_defaults_preserve_customized_business(setup):
    client, db, _ = setup
    seed_settings(db, BIZ_A)
    before = deepcopy(db.settings)
    response = request(client, "POST", authorization=headers(), payload=deepcopy(DEFAULT_ONBOARDING))
    assert response.status_code == 409 and db.settings == before
    loaded = request(client, authorization=headers()).json()["settings"]
    assert loaded["brand_identity"]["priority_focus"] == "quality"
    assert loaded["expected_cost_structure"][0]["tolerance_pct"] == 0.5


@pytest.mark.parametrize("percent", [0, 0.1, 0.5, 1, 5, 100])
def test_settings_read_and_update_preserve_percentage_contract(setup, percent):
    client, db, _ = setup
    seed_settings(db, BIZ_A, tolerance=percent/100)
    form = request(client, authorization=headers()).json()["settings"]
    assert form["expected_cost_structure"][0]["tolerance_pct"] == pytest.approx(percent)
    form["expected_cost_structure"] = [{"concept": row["concept"], "expected_monthly_amount": row["amount_per_month"],
                                         "tolerance_pct": row["tolerance_pct"]/100, "expense_behavior": row["expense_behavior"]}
                                        for row in form["expected_cost_structure"]]
    assert request(client, "PUT", authorization=headers(), payload=form).status_code == 200
    active = [row for row in db.settings["business_fixed_costs"] if row["is_active"]]
    assert len(active) == 1 and active[0]["tolerance_pct"] == pytest.approx(percent/100)


@pytest.mark.parametrize("method", ["GET", "POST", "PUT"])
def test_revoked_ownership_denies_all_operations_without_data_or_mutation(setup, method):
    client, db, _ = setup
    seed_settings(db, BIZ_A)
    db.businesses[0]["owner_id"] = USER_B
    before = deepcopy(db.settings)
    db.calls.clear()
    response = request(client, method, authorization=headers(), payload=deepcopy(DEFAULT_ONBOARDING))
    assert response.status_code == 403 and "Renta" not in response.text
    assert db.calls == ["businesses"] and db.settings == before


def test_inverted_thresholds_and_extra_identity_fields_never_write(setup):
    client, db, _ = setup
    for changes in ("thresholds", "identity"):
        payload = deepcopy(DEFAULT_ONBOARDING)
        if changes == "thresholds": payload["audit_tolerances"]["margin_critical_threshold"] = .4
        else: payload["owner_id"] = USER_B
        assert request(client, "POST", authorization=headers(), payload=payload).status_code == 422
        assert all(not rows for rows in db.settings.values())


@pytest.mark.parametrize("table", ["businesses", "business_onboarding"])
def test_data_errors_are_closed_and_sanitized(setup, table):
    client, db, _ = setup
    db.fail = table
    response = request(client, authorization=headers())
    assert response.status_code == 503 and "synthetic-private-key" not in response.text


def test_invalid_business_id_never_creates_db(setup):
    client, db, factory = setup
    response = request(client, bid="not-a-business", authorization=headers())
    assert response.status_code == 422 and db.calls == factory == []
