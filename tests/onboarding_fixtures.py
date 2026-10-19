"""Datos de prueba mutables de N10. Sin red, secretos ni servicios reales."""
from copy import deepcopy
from types import SimpleNamespace
from uuid import uuid4

from api.onboarding import OnboardingIdentityPayload, _upsert_onboarding
from tests.test_chat_api import DB


DEFAULT_ONBOARDING = {
    "brand_identity": {"brand_voice": "Asesoría clara y práctica, basada en los datos disponibles del negocio.",
                       "prohibited_recommendations": [], "priority_focus": "efficiency"},
    "audit_tolerances": {"max_cash_discrepancy_pct": 0.02, "max_cash_discrepancy_abs": 150,
                         "margin_warning_threshold": 0.15, "margin_critical_threshold": 0.08,
                         "cost_spike_threshold_pct": 0.1},
    "expected_cost_structure": [],
    "audit_rules": {"red_alert_triggers": [], "ignored_anomaly_types": [], "audit_frequency": "daily"},
}


class MutableQuery:
    def __init__(self, rows):
        self.rows, self.filters, self.columns, self.action, self.payload = rows, [], None, None, None

    def select(self, columns): self.columns = columns; return self
    def eq(self, key, value): self.filters.append((key, value)); return self
    def update(self, data): self.action, self.payload = "update", data; return self
    def insert(self, data): self.action, self.payload = "insert", data; return self
    def upsert(self, data, **_kwargs): self.action, self.payload = "upsert", data; return self

    def execute(self):
        selected = [row for row in self.rows if all(row.get(key) == value for key, value in self.filters)]
        if self.action == "upsert":
            existing = next((row for row in self.rows if row.get("business_id") == self.payload.get("business_id")), None)
            if existing is None:
                existing = {"id": str(uuid4())}; self.rows.append(existing)
            existing.update(deepcopy(self.payload)); selected = [existing]
        elif self.action == "update":
            for row in selected: row.update(deepcopy(self.payload))
        elif self.action == "insert":
            values = self.payload if isinstance(self.payload, list) else [self.payload]
            selected = [{"id": str(uuid4()), **deepcopy(row)} for row in values]
            self.rows.extend(selected)
        if self.columns and self.columns != "*":
            selected = [{key: row[key] for key in self.columns.split(",") if key in row} for row in selected]
        return SimpleNamespace(data=deepcopy(selected))


class OnboardingDB(DB):
    def __init__(self):
        super().__init__()
        self.settings = {"business_onboarding": [], "business_fixed_costs": [], "mepia_memory": []}

    def table(self, name):
        if name not in self.settings:
            return super().table(name)
        self.calls.append(name)
        if self.fail == name:
            raise RuntimeError("synthetic-private-key-must-not-leak")
        return MutableQuery(self.settings[name])


def seed_settings(db, business_id, *, tolerance=0.005):
    payload = deepcopy(DEFAULT_ONBOARDING)
    payload["brand_identity"]["priority_focus"] = "quality"
    payload["expected_cost_structure"] = [{"concept": "Renta sintética", "expected_monthly_amount": 12000,
                                           "tolerance_pct": tolerance, "expense_behavior": "FIXED"}]
    _upsert_onboarding(db, business_id, OnboardingIdentityPayload.model_validate(payload), "2026-10-15T12:00:00Z")
