"""Perfil local del chat y ajustes protegidos, sin claves del análisis completo."""
import pytest
from fastapi.testclient import TestClient

from api.chat_app import create_app
from api.core.chat_config import ChatSettings


def config(**changes):
    values = dict(SUPABASE_URL='https://synthetic-project.supabase.co',
                  SUPABASE_SERVICE_ROLE_KEY='synthetic-service-key',
                  SUPABASE_JWT_ALGORITHM='ES256')
    values.update(changes)
    return ChatSettings(_env_file=None, **values)


def test_chat_and_settings_routes_without_unrelated_model_keys(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail('No crear clientes DB antes de autenticar')
    monkeypatch.setattr('api.chat_app.create_client', forbidden)
    with TestClient(create_app(config())) as client:
        assert client.get('/me/businesses').status_code == 401
        assert client.get('/audit').status_code == 404
        assert client.get('/business/00000000-0000-4000-8000-000000000001/onboarding/status').status_code == 401
        paths = client.get('/openapi.json').json()['paths']
        assert set(paths) == {'/me/businesses', '/business/{business_id}/chat',
                             '/business/{business_id}/chat/{conversation_id}',
                             '/business/{business_id}/onboarding',
                             '/business/{business_id}/onboarding/status'}


@pytest.mark.parametrize('changes', [
    {'SUPABASE_SERVICE_ROLE_KEY':''},
    {'SUPABASE_JWT_ALGORITHM':'HS256', 'SUPABASE_JWT_SECRET':''},
    {'SUPABASE_URL':'http://unsafe.invalid'},
])
def test_invalid_configuration_stops_before_serving(changes):
    with pytest.raises(RuntimeError):
        with TestClient(create_app(config(**changes))):
            pass
