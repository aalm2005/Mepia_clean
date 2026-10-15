"""
MEPIA — Configuración centralizada del backend Python.

Uso en cualquier módulo:
    from core.config import settings

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

Patrón obligatorio para agentes futuros (n13_revisor, core_auditor, forensic_cfo, etc.):
    - NUNCA usar os.environ.get() directamente.
    - NUNCA hardcodear keys o URLs.
    - SIEMPRE importar `settings` desde este módulo.

Variables de entorno:
    - Se leen desde `api/.env` (backend Python).
    - El archivo `.env.local` en la raíz es EXCLUSIVO del frontend Next.js.
    - En producción, las variables se inyectan directamente en el entorno del
      proceso (Railway, Render, etc.) — no se usa ningún archivo .env.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import Literal


class Settings(BaseSettings):
    # ── LLMs ──────────────────────────────────────────────────────────────────
    # Usamos keys distintas para dev y prod.
    # N11 Consultor usa Anthropic como primario; OpenAI como fallback.
    # N13 Revisor, S4 Forensic CFO y N05 CEO Orchestrator usan OpenAI.
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str

    # ── Supabase ───────────────────────────────────────────────────────────────
    # El backend usa SERVICE_ROLE_KEY (privilegios absolutos, bypass RLS).
    # El frontend Next.js usa ANON_KEY — definida en .env.local, no aquí.
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_ALGORITHM: Literal["HS256", "ES256"] = "HS256"
    SUPABASE_JWT_SECRET: SecretStr = SecretStr("")

    # N15: configuración propia; no reutiliza claves ni cambia el resto del pipeline.
    CHAT_GEMINI_API_KEY: SecretStr = SecretStr("")
    CHAT_MODEL: str = "gemini-3.5-flash-lite"

    # ── Entorno ────────────────────────────────────────────────────────────────
    ENVIRONMENT: str = "dev"  # "dev" | "prod"

    model_config = SettingsConfigDict(
        env_file=["api/.env", ".env"],  # funciona tanto desde raíz como desde api/
        env_file_encoding="utf-8",
        case_sensitive=True,        # las keys son case-sensitive por convención
        extra="ignore",             # ignora variables no declaradas en el modelo
    )


# Singleton — importar este objeto, no instanciar Settings() directamente.
settings = Settings()
