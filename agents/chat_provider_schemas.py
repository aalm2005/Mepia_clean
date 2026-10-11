"""Esquemas compactos compartidos por proveedores de la evaluación N15."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from agents.chat_response import CHAT_MAX_CLAIMS_PER_PART, CHAT_MAX_SOURCES_PER_CLAIM


class _StrictOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _DraftClaim(_StrictOutput):
    text: str = Field(description="Paráfrasis fundamentada; usa {{slot_id}} para cualquier cifra de la fuente")
    source_ids: list[str] = Field(min_length=1, max_length=CHAT_MAX_SOURCES_PER_CLAIM,
                                description="IDs existentes de los hechos que sostienen el texto completo")


class _DraftPart(_StrictOutput):
    part_id: str = Field(description="Copia el ID de una parte de entrada")
    claims: list[_DraftClaim] = Field(min_length=1, max_length=CHAT_MAX_CLAIMS_PER_PART,
                                    description="Afirmaciones fundamentadas; agrupa entradas de catálogos extensos sin omitirlas")


class _Draft(_StrictOutput):
    parts: list[_DraftPart] = Field(min_length=1)


class _Judgment(_StrictOutput):
    claim_id: str = Field(description="Copia el ID de una afirmación de entrada")
    supported: bool = Field(description="Todo el sentido y las unidades tienen respaldo en las fuentes citadas")
    in_domain: bool = Field(description="Respeta el alcance de MEPIA; una negativa correcta a un tema fuera del motor también es true")
    calculation_performed: bool = Field(description="La afirmación hace una operación numérica no emitida por el motor")
    follows_policy: bool = Field(description="La afirmación respeta el estado y la política de la parte")


class _Review(_StrictOutput):
    request_id: str = Field(description="Copia exactamente el identificador de la revisión de entrada")
    judgments: list[_Judgment]


OUTPUT_TYPES: dict[str, type[BaseModel]] = {
    "ChatModelDraft": _Draft,
    "ChatReviewResult": _Review,
}
