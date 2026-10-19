"""Servidor sintético para las pruebas N10; nunca usar para una demostración real."""
from fastapi import Query

from api.onboarding import create_onboarding_router
from tests.chat_step5_server import app, AUTH, BIZ_A, BIZ_B, BIZ_C
from tests.onboarding_fixtures import OnboardingDB, seed_settings

settings_db = OnboardingDB()
seed_settings(settings_db, BIZ_B)
app.include_router(create_onboarding_router(auth=AUTH, db_factory=lambda: settings_db))


@app.get('/__test__/onboarding')
def state():
    return {'business_a': BIZ_A, 'business_b': BIZ_B, 'business_c': BIZ_C,
            'tables': settings_db.settings}


@app.post('/__test__/onboarding/seed-own')
def seed_own(percent: float = Query(default=0.5, ge=0, le=100)):
    seed_settings(settings_db, BIZ_A, tolerance=percent / 100)
    return {'ok': True}
