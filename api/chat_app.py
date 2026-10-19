"""Servidor de Chat IA y ajustes protegidos, independiente del pipeline de análisis."""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from supabase import create_client

from api.chat import create_chat_router, gemini_node_factory
from api.core.auth import AuthService
from api.core.chat_config import ChatSettings
from api.onboarding import create_onboarding_router


def create_app(config: ChatSettings | None = None) -> FastAPI:
    settings = config if config is not None else ChatSettings()
    auth = AuthService(settings.SUPABASE_URL, settings.SUPABASE_JWT_SECRET.get_secret_value(),
                       algorithm=settings.SUPABASE_JWT_ALGORITHM)

    @asynccontextmanager
    async def lifespan(_app):
        auth.validate_configuration()
        if not settings.SUPABASE_SERVICE_ROLE_KEY.get_secret_value().strip():
            raise RuntimeError('Configura la clave de servidor del proyecto')
        yield

    # Evitar datos de peticiones en los logs del perfil local.
    for name in ('httpx', 'httpcore', 'supabase', 'gotrue', 'openai'):
        logging.getLogger(name).setLevel(logging.WARNING)
    app = FastAPI(title='MEPIA Chat IA', lifespan=lifespan)
    app.include_router(create_chat_router(
        auth=auth,
        db_factory=lambda: create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY.get_secret_value()),
        node_factory=gemini_node_factory(settings.CHAT_GEMINI_API_KEY.get_secret_value(), settings.CHAT_MODEL),
    ))
    app.include_router(create_onboarding_router(
        auth=auth,
        db_factory=lambda: create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY.get_secret_value()),
    ))
    return app
