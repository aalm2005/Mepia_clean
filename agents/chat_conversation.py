"""Nodo N15 de consulta conversacional, aislado del motor y de la red.

Las herramientas recuperan los hechos; un proveedor puede redactar y parafrasear
libremente. La evidencia y la salida se validan antes de publicar esa redacción.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agents.chat_grounding import ChatEvidenceReference, ChatGroundingPacket
from agents.chat_metric_catalog import CONCEPT_CATALOG, METRIC_CATALOG
from agents.chat_tools import ChatQueryTools, ChatToolResult
from agents.chat_response import (
    ChatResponseGuard, ChatResponseVerifier, ChatResponseWriter,
    ChatValidatedClaim, build_writing_request,
)


PartKind = Literal["concept", "result", "report", "metrics", "catalog", "calculation", "outside", "greeting"]
PartStatus = Literal["ok", "not_found", "missing_data", "not_allowed", "outside_domain", "invalid_request"]

_GREETING_MESSAGE = "¡Hola! Puedo ayudarte a entender los resultados de tu negocio y explicar conceptos. ¿Qué te gustaría consultar?"
_GREETINGS = frozenset({
    "hola", "hola mepia", "buenas", "buen dia", "buenos dias", "buenas tardes",
    "buenas noches", "hola buen dia", "hola buenos dias", "hola buenas tardes",
    "hola buenas noches", "que tal", "hola que tal", "como estas", "hola como estas",
})

_FALLBACK_MESSAGES = frozenset({
    _GREETING_MESSAGE,
    "El negocio solicitado no coincide con el paquete de evidencia.",
    "Escribe una pregunta sobre las métricas de MEPIA.",
    "Esta es la definición del catálogo de MEPIA. La fórmula es solo explicativa.",
    "Este es el resultado que S3 emitió para la ejecución indicada.",
    "Este es el informe N14 enlazado a esa misma ejecución S3.",
    "Estos son los resultados que S3 emitió para la ejecución indicada.",
    "Estas son las métricas que el motor de MEPIA puede explicar.",
    "No puedo calcular, recalcular, agregar, comparar cifras, proyectar ni simular desde el chat.",
    "No hay evidencia verificable para esa parte de la pregunta.",
    "El motor no emitió ese resultado o el catálogo no contiene ese concepto.",
    "La solicitud no corresponde a un selector válido.",
    "Esa parte queda fuera de las métricas y conceptos del motor de MEPIA.",
})


class ChatModelDecision(BaseModel):
    """Salida de clasificación; la redacción usa un contrato independiente."""

    model_config = ConfigDict(extra="forbid")
    kind: Literal["concept", "result", "report", "metrics", "catalog", "outside"]
    selector: str | None = None


class ChatIntentProvider(Protocol):
    """Adaptador inyectable de clasificación; no requiere un SDK particular."""

    def classify(self, question_part: str, allowed_selectors: tuple[str, ...]) -> ChatModelDecision | dict[str, Any]: ...


class ChatAnswerPart(BaseModel):
    question_part: str
    kind: PartKind
    status: PartStatus
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    evidence: list[ChatEvidenceReference] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    claims: list[ChatValidatedClaim] = Field(default_factory=list)
    generation_status: Literal["fallback", "validated"] = "fallback"
    generation_issues: list[str] = Field(default_factory=list)
    generation_diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_published_part(self) -> "ChatAnswerPart":
        if self.kind == "greeting":
            if (self.status != "ok" or self.message != _GREETING_MESSAGE
                    or self.generation_status != "fallback" or self.data or self.evidence
                    or self.missing_data or self.claims or self.generation_issues
                    or self.generation_diagnostics):
                raise ValueError("Un saludo solo puede publicar la respuesta social fija, sin datos ni fuentes")
        elif self.message == _GREETING_MESSAGE:
            raise ValueError("La respuesta social solo corresponde a un saludo")
        if self.generation_status == "fallback":
            if self.message not in _FALLBACK_MESSAGES or self.claims:
                raise ValueError("El respaldo determinista no puede introducir texto generado")
        elif not self.claims or self.message != "\n\n".join(claim.text for claim in self.claims):
            raise ValueError("La redacción debe coincidir con sus afirmaciones verificadas")
        fixed_by_status = {
            "not_allowed": "No puedo calcular, recalcular, agregar, comparar cifras, proyectar ni simular desde el chat.",
            "missing_data": "No hay evidencia verificable para esa parte de la pregunta.",
            "not_found": "El motor no emitió ese resultado o el catálogo no contiene ese concepto.",
            "outside_domain": "Esa parte queda fuera de las métricas y conceptos del motor de MEPIA.",
        }
        if (self.generation_status == "fallback" and self.status in fixed_by_status
                and self.message != fixed_by_status[self.status]):
            raise ValueError("El mensaje no corresponde al estado")
        if self.status != "ok" and self.data:
            raise ValueError("Una parte sin resultado no puede contener datos")
        if self.status not in ("ok", "not_found") and self.evidence:
            raise ValueError("La evidencia no corresponde al estado")
        if self.status == "not_allowed" and self.kind != "calculation":
            raise ValueError("Solo un cálculo solicitado puede tener rechazo de cálculo")
        if self.kind == "calculation" and self.status != "not_allowed":
            raise ValueError("Un cálculo solicitado siempre se rechaza")
        if self.status == "ok" and self.kind in ("calculation", "outside"):
            raise ValueError("Una parte fuera de alcance no puede publicar resultados")
        return self


class ChatAnswer(BaseModel):
    business_id: str
    resolved_date: str | None = None
    parts: list[ChatAnswerPart]
    calculation_allowed: Literal[False] = False
    knowledge_scope: Literal["engine_metric_domain"] = "engine_metric_domain"


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _split_question(question: str) -> list[str]:
    # Separar primero los interrogativos y después conjunciones de peticiones.
    # El fragmento individual conserva su texto original para el rechazo.
    chunks = re.split(r"[?;\n]+", question)
    parts: list[str] = []
    for chunk in chunks:
        parts.extend(re.split(r"\s+(?:y|adem[aá]s|también)\s+", chunk, flags=re.I))
    return [part.strip(" ¿¡!,. ") for part in parts if part.strip(" ¿¡!,. ")]


def _calculation_requested(fragment: str) -> bool:
    q = _normalize(fragment)
    if not re.search(r"\d", q):
        # Esta formulación pide una explicación; el resto de la misma frase
        # todavía puede contener una solicitud de cálculo prohibida.
        q = re.sub(r"\b(?:como se calcula|cual es la formula)\b", "", q)
    patterns = (
        r"\b(?:calcula|calcular|recalcula|recalcular|suma|sumar|promedia|promediar|agrega|agregar|multiplica|multiplicar|divide|dividir)\b",
        r"\b(?:estima|estimar|proyecta|proyectar|simula|simular|extrapola|extrapolar)\b",
        r"\b(?:cuanto|cual)\s+(?:seria|serian|daria|darian|habria|habran|tendremos|deberia|ganariamos|obtendriamos|quedaria|sale|da)\b",
        r"\b(?:que pasaria si|que ocurriria si|si aument|si baj|si sub|si vend|si hubier|si tuvier)\w*",
        r"\b(?:diferencia entre|comparad[oa] con|comparacion de|en comparacion con|mas que|menos que)\b",
        r"\b(?:totaliza|totalizar|combina|combinar|a partir de|con estos datos|deduce|deriva)\b",
        r"\b(?:promedio de|media de|suma de|total de|porcentaje de)\b",
        r"\b(?:el mes|mensual|semanal|entre fechas|proximo|siguiente semana|manana)\b",
    )
    if any(re.search(pattern, q) for pattern in patterns):
        return True
    # Operandos explícitos o una fórmula solicitada; explicar una fórmula sin
    # operandos sigue siendo una consulta conceptual permitida.
    return bool(re.search(r"\d\s*(?:\+|\-|\*|/|% de)\s*\d", fragment))


def _candidate_selectors(fragment: str) -> tuple[str, ...]:
    q = f" {_normalize(fragment)} "
    matches: list[tuple[int, str]] = []
    for item in METRIC_CATALOG:
        for name in (item.metric_id, item.display_name, *item.aliases, *item.result_metric_names):
            normalized = _normalize(name)
            if normalized and f" {normalized} " in q:
                matches.append((len(normalized), item.metric_id))
    for item in CONCEPT_CATALOG:
        for name in (item.term, item.display_name, *item.aliases):
            normalized = _normalize(name)
            if normalized and f" {normalized} " in q:
                matches.append((len(normalized), item.term))
    matches.sort(reverse=True)
    return tuple(dict.fromkeys(name for _, name in matches))


def _intent_from_words(fragment: str, has_selector: bool) -> PartKind:
    q = _normalize(fragment)
    if re.search(r"\b(?:informe|reporte|resumen ejecutivo|narrativa operativa)\b", q):
        return "report"
    if re.search(r"\b(?:que es|que son|que significa|define|definicion|explica|formula|como se calcula|como funciona)\b", q):
        return "concept"
    if re.search(r"\b(?:catalogo|que metricas existen|lista de metricas)\b", q):
        return "catalog"
    if re.search(r"\b(?:metricas|resultados|semaforo)\b", q) and not has_selector:
        return "metrics"
    if has_selector:
        return "result"
    return "outside"


class ChatConversationNode:
    """Procesa una pregunta contra un único paquete ya aislado por negocio."""

    def __init__(self, provider: ChatIntentProvider | None = None, *,
                 writer: ChatResponseWriter | None = None,
                 verifier: ChatResponseVerifier | None = None) -> None:
        self._provider = provider
        self._writer = writer
        self._verifier = verifier

    def answer(self, question: str, packet: ChatGroundingPacket, *, business_id: str,
               history: list[dict[str, str]] | None = None) -> ChatAnswer:
        if not business_id or packet.business_id != business_id:
            return ChatAnswer(business_id=business_id, parts=[ChatAnswerPart(
                question_part="", kind="outside", status="invalid_request",
                message="El negocio solicitado no coincide con el paquete de evidencia.",
                missing_data=["business_mismatch"],
            )])
        if not isinstance(question, str) or not question.strip():
            return ChatAnswer(business_id=business_id, resolved_date=packet.resolved_date,
                parts=[ChatAnswerPart(question_part="", kind="outside", status="invalid_request",
                    message="Escribe una pregunta sobre las métricas de MEPIA.")])

        tools = ChatQueryTools(packet)
        # Referencias breves solo heredan un selector conocido de una pregunta
        # previa del mismo ámbito. El historial nunca aporta valores ni fuentes.
        if history and _normalize(question) in {
            "que significa", "que significa eso", "explica esa metrica", "cual es la formula"
        }:
            metric_ids = {item.metric_id for item in METRIC_CATALOG}
            candidates = set(_candidate_selectors(history[-1]["question"])) & metric_ids
            if len(candidates) == 1:
                question = question.rstrip("?¿ .") + " " + next(iter(candidates))
        parts: list[ChatAnswerPart] = []
        inherited_kind: PartKind | None = None
        previous_concept_selector: str | None = None
        for fragment in _split_question(question):
            if _calculation_requested(fragment):
                parts.append(self._from_tool(fragment, "calculation", tools.refuse_calculation()))
                previous_concept_selector = None
                continue
            if _normalize(fragment) in _GREETINGS:
                parts.append(ChatAnswerPart(question_part=fragment, kind="greeting",
                    status="ok", message=_GREETING_MESSAGE))
                continue
            candidates = _candidate_selectors(fragment)
            kind = _intent_from_words(fragment, bool(candidates))
            # Una conjunción puede omitir el verbo: "qué es X y Y".
            if candidates and kind == "result" and inherited_kind == "concept" and not re.search(
                r"\b(?:fue|salio|resultado|valor|cuanto|cual)\b", _normalize(fragment)
            ):
                kind = "concept"
            if kind != "outside":
                inherited_kind = kind

            decision = self._provider_decision(fragment, candidates)
            if (decision is not None and kind == "result" and candidates
                    and decision.kind == "concept" and not re.search(
                        r"\b(?:fue|salio|resultado|valor|cuanto|cual)\b", _normalize(fragment)
                    )):
                kind = "concept"
            if decision is not None and kind == "outside" and decision.kind in ("report", "metrics", "catalog"):
                # Solo se admite si el texto contiene el disparador correspondiente.
                kind = _intent_from_words(fragment, False)
            selector = candidates[0] if candidates else None
            if (kind == "outside" and not candidates and previous_concept_selector
                    and re.fullmatch(r"(?:explicame|explica) (?:el metodo|la formula)", _normalize(fragment))):
                kind, selector = "concept", previous_concept_selector
            if decision is not None and decision.selector in candidates:
                selector = decision.selector
            # Los indicios explícitos en la pregunta prevalecen sobre el modelo.
            if kind == "outside" and candidates:
                kind = decision.kind if decision and decision.kind in ("concept", "result") else "result"
            parts.append(self._resolve(fragment, kind, selector, tools))
            if kind == "concept" and selector:
                metric_candidates = set(candidates) & {item.metric_id for item in METRIC_CATALOG}
                previous_concept_selector = selector if len(metric_candidates or set(candidates)) <= 1 else None
            else:
                previous_concept_selector = None

        if not parts:
            parts.append(ChatAnswerPart(question_part="", kind="outside", status="invalid_request",
                message="Escribe una pregunta sobre las métricas de MEPIA."))
        answer = ChatAnswer(business_id=business_id, resolved_date=packet.resolved_date, parts=parts)
        # Los saludos son interacción social fija, nunca afirmaciones del negocio.
        # Se excluyen del redactor y revisor sin cambiar sus contratos factuales.
        domain_indexes = [index for index, part in enumerate(answer.parts) if part.kind != "greeting"]
        if not domain_indexes:
            return answer
        request = build_writing_request([answer.parts[index].model_dump(mode="json") for index in domain_indexes])
        request.history = list(history or [])[-4:]
        narrations = ChatResponseGuard().narrate(request, self._writer, self._verifier)
        for index, narration in zip(domain_indexes, narrations):
            data = answer.parts[index].model_dump()
            data["generation_issues"] = narration.issues
            data["generation_diagnostics"] = narration.diagnostics
            if narration.claims:
                data["message"] = "\n\n".join(claim.text for claim in narration.claims)
                data["claims"] = narration.claims
                data["generation_status"] = "validated"
            answer.parts[index] = ChatAnswerPart.model_validate(data)
        return answer

    def _provider_decision(self, fragment: str, candidates: tuple[str, ...]) -> ChatModelDecision | None:
        if self._provider is None:
            return None
        try:
            raw = self._provider.classify(fragment, candidates)
            decision = ChatModelDecision.model_validate(raw)
            if decision.selector is not None and decision.selector not in candidates:
                return None
            return decision
        except Exception:
            # Un proveedor no disponible o una respuesta malformada no puede
            # saltarse el ruteo determinista ni publicar texto no verificado.
            return None

    def _resolve(self, fragment: str, kind: PartKind, selector: str | None,
                 tools: ChatQueryTools) -> ChatAnswerPart:
        if kind == "concept" and selector:
            result = tools.describe_metric(selector)
            if result.status == "not_found":
                result = tools.lookup_glossary(selector)
            return self._from_tool(fragment, kind, result)
        if kind == "result" and selector:
            return self._from_tool(fragment, kind, tools.get_metric(selector))
        if kind == "report":
            return self._from_tool(fragment, kind, tools.get_final_report())
        if kind == "metrics":
            return self._from_tool(fragment, kind, tools.list_metrics())
        if kind == "catalog":
            return self._from_tool(fragment, kind, tools.list_metric_catalog())
        return ChatAnswerPart(question_part=fragment, kind="outside", status="outside_domain",
            message="Esa parte queda fuera de las métricas y conceptos del motor de MEPIA.")

    @staticmethod
    def _from_tool(fragment: str, kind: PartKind, result: ChatToolResult) -> ChatAnswerPart:
        # Respaldo disponible si la redacción falla. La ruta normal puede
        # sustituir este mensaje por afirmaciones libres ya verificadas.
        messages = {
            "concept": "Esta es la definición del catálogo de MEPIA. La fórmula es solo explicativa.",
            "result": "Este es el resultado que S3 emitió para la ejecución indicada.",
            "report": "Este es el informe N14 enlazado a esa misma ejecución S3.",
            "metrics": "Estos son los resultados que S3 emitió para la ejecución indicada.",
            "catalog": "Estas son las métricas que el motor de MEPIA puede explicar.",
            "calculation": "No puedo calcular, recalcular, agregar, comparar cifras, proyectar ni simular desde el chat.",
        }
        status: PartStatus = result.status
        if result.status == "ok":
            message = messages[kind]
        elif result.status == "not_allowed":
            message = messages["calculation"]
        elif result.status == "missing_data":
            message = "No hay evidencia verificable para esa parte de la pregunta."
        elif result.status == "not_found":
            message = "El motor no emitió ese resultado o el catálogo no contiene ese concepto."
        else:
            message = "La solicitud no corresponde a un selector válido."
        return ChatAnswerPart(question_part=fragment, kind=kind, status=status,
            message=message, data=result.data if status == "ok" else {},
            evidence=result.evidence if status in ("ok", "not_found") else [],
            missing_data=result.missing_data)
