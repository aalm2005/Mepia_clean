"""Adaptador opt-in de Gemini para la evaluación offline de N15.

Usa la API compatible con OpenAI documentada por Google. Solo recibe datos
sintéticos del evaluador; no lee .env, bases de datos ni proveedores del motor.
"""
from __future__ import annotations

from typing import Any

from agents.chat_provider_schemas import OUTPUT_TYPES
from agents.chat_response import ChatCompletionFailure


GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_GEMINI_EVAL_MODEL = "gemini-3.5-flash-lite"
GEMINI_EVAL_TIMEOUT_SECONDS = 60.0


def _without_array_bounds(value: Any) -> Any:
    """Simplifica solo el esquema enviado, sin modificar validadores locales."""
    if isinstance(value, dict):
        return {key: _without_array_bounds(item) for key, item in value.items()
                if key not in ("minItems", "maxItems")}
    if isinstance(value, list):
        return [_without_array_bounds(item) for item in value]
    return value


def _request_schema_hint(error: Exception) -> str | None:
    """Clasifica menciones del error con códigos fijos; nunca devuelve su texto."""
    if getattr(error, "status_code", None) != 400:
        return None
    body = getattr(error, "body", None)
    if not isinstance(body, dict):
        return None
    details = body.get("error", body)
    if not isinstance(details, dict) or not isinstance(details.get("message"), str):
        return None
    message = details["message"].casefold()
    if "minitems" in message or "maxitems" in message:
        return "schema_bounds_error_hint_http_400"
    if any(term in message for term in ("schema", "response_format", "responseformat")):
        return "schema_error_hint_http_400"
    return None


class _GeminiDraft(OUTPUT_TYPES["ChatModelDraft"]):
    """Hereda los límites locales; evita cardinalidades anidadas en la solicitud.

    La corrida 034018 recibió HTTP 400 con el esquema que las incluía.
    El campo exacto rechazado no quedó guardado. Esta representación vuelve
    a la forma de listas anterior; la corrección requiere verificación real.
    """

    @classmethod
    def model_json_schema(cls, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return _without_array_bounds(super().model_json_schema(*args, **kwargs))


class GeminiCompletion:
    """Callback de ``ChatJsonCompletionAdapter`` con presupuesto estricto."""

    def __init__(self, *, api_key: str, model: str, max_calls: int,
                 client: Any | None = None) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("Se requiere una clave de Gemini")
        if not model or not model.strip():
            raise ValueError("Se requiere un modelo explícito")
        if max_calls < 1:
            raise ValueError("El límite de llamadas debe ser positivo")
        if client is None:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=GEMINI_OPENAI_BASE_URL,
                            max_retries=0, timeout=GEMINI_EVAL_TIMEOUT_SECONDS)
        self._client = client
        self.model = model.strip()
        self.max_calls = max_calls
        self.calls = 0

    def __call__(self, system_prompt: str, data_json: str,
                 schema: dict[str, Any]) -> dict[str, Any]:
        output_type = OUTPUT_TYPES.get(schema.get("title", ""))
        if output_type is None:
            raise ValueError("Esquema de salida no autorizado")
        if schema.get("title") == "ChatModelDraft":
            output_type = _GeminiDraft
        if self.calls >= self.max_calls:
            raise ChatCompletionFailure("budget_exceeded", "Límite de llamadas alcanzado")
        self.calls += 1  # cuenta también un intento fallido; el SDK no reintenta
        try:
            completion = self._client.beta.chat.completions.parse(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": data_json}],
                response_format=output_type,
            )
        except Exception as error:
            hint = _request_schema_hint(error)
            if hint is not None:
                raise ChatCompletionFailure(hint, "El proveedor rechazó la solicitud; pista de esquema.") from None
            raise
        if len(completion.choices) != 1:
            raise ChatCompletionFailure("choice_count", "Gemini no devolvió una única respuesta")
        choice = completion.choices[0]
        if str(choice.finish_reason).lower() != "stop":
            raise ChatCompletionFailure("incomplete_output", "Gemini no devolvió una salida estructurada completa")
        if getattr(choice.message, "refusal", None):
            raise ChatCompletionFailure("refusal", "Gemini no devolvió una salida estructurada completa")
        if choice.message.parsed is None:
            raise ChatCompletionFailure("unparsed_output", "Gemini no devolvió una salida estructurada completa")
        return choice.message.parsed.model_dump(mode="json")
