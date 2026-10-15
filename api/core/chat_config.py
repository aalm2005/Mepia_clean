"""Configuración del servidor de Chat IA, independiente de claves del pipeline."""
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChatSettings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: SecretStr
    SUPABASE_JWT_ALGORITHM: Literal['HS256', 'ES256'] = 'HS256'
    SUPABASE_JWT_SECRET: SecretStr = SecretStr('')
    CHAT_GEMINI_API_KEY: SecretStr = SecretStr('')
    CHAT_MODEL: str = 'gemini-3.5-flash-lite'

    model_config = SettingsConfigDict(
        env_file=['api/.env', '.env'], env_file_encoding='utf-8',
        case_sensitive=True, extra='ignore',
    )
