"""Adaptador opt-in de OpenAI para la evaluación offline de N15.

No crea un endpoint, no lee la base de datos y no carga archivos .env. El
consumidor proporciona la clave y el modelo; el nodo N15 sigue independiente.
"""
from __future__ import annotations

from typing import Any

from agents.chat_provider_schemas import OUTPUT_TYPES


class OpenAIResponsesCompletion:
    """Callback para ``ChatJsonCompletionAdapter`` con presupuesto estricto.

    ``responses.parse`` aplica un esquema Pydantic compacto. Después, el
    adaptador de N15 valida el contrato completo, incluidas fuentes, digest y
    prohibiciones. Cada intento se cuenta antes de llamar; el SDK no reintenta.
    """

    def __init__(self, *, api_key: str, model: str, max_calls: int,
                 client: Any | None = None) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("Se requiere una clave de OpenAI")
        if not model or not model.strip():
            raise ValueError("Se requiere un modelo explícito")
        if max_calls < 1:
            raise ValueError("El límite de llamadas debe ser positivo")
        if client is None:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, max_retries=0, timeout=30.0)
        self._client = client
        self.model = model.strip()
        self.max_calls = max_calls
        self.calls = 0

    def __call__(self, system_prompt: str, data_json: str,
                 schema: dict[str, Any]) -> dict[str, Any]:
        output_type = OUTPUT_TYPES.get(schema.get("title", ""))
        if output_type is None:
            raise ValueError("Esquema de salida no autorizado")
        if self.calls >= self.max_calls:
            raise RuntimeError("Límite de llamadas alcanzado")
        self.calls += 1
        response = self._client.responses.parse(
            model=self.model,
            instructions=system_prompt,
            input=[{"role": "user", "content": data_json}],
            text_format=output_type,
            store=False,
        )
        if getattr(response, "status", "completed") != "completed" or response.output_parsed is None:
            raise RuntimeError("El proveedor no devolvió una salida estructurada completa")
        return response.output_parsed.model_dump(mode="json")
