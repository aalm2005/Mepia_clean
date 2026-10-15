"""Integración HTTP protegida de N15. Proveedores y credenciales solo en servidor."""
from dataclasses import dataclass
from datetime import date
from typing import Callable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

from agents.chat_conversation import ChatAnswer, ChatConversationNode
from agents.chat_grounding import ChatGroundingService
from agents.chat_response import ChatJsonCompletionAdapter
from agents.chat_provider_gemini import GeminiCompletion
from api.core.auth import AuthService
from api.core.chat_history import ChatHistoryStore


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=2000)
    requested_date: date | None = None
    conversation_id: UUID | None = None


class ChatResponse(BaseModel):
    conversation_id: UUID
    answer: ChatAnswer


@dataclass
class BusinessAccess:
    user_id: str
    business_id: str
    db: object


def gemini_node_factory(api_key: str, model: str) -> Callable[[], ChatConversationNode]:
    def create():
        if not api_key.strip() or not model.strip():
            raise HTTPException(503, "Chat no configurado")
        try:
            import logging
            # El SDK no debe emitir detalles de peticiones bajo DEBUG global de dev.
            logging.getLogger("openai").setLevel(logging.WARNING)
            # Un presupuesto independiente por petición, sin clasificación ni reintentos.
            adapter = ChatJsonCompletionAdapter(GeminiCompletion(api_key=api_key, model=model, max_calls=2))
            return ChatConversationNode(writer=adapter, verifier=adapter)
        except Exception:
            raise HTTPException(503, "Chat no disponible") from None
    return create


def create_chat_router(*, auth: AuthService, db_factory: Callable,
                       node_factory: Callable, history: ChatHistoryStore | None = None) -> APIRouter:
    router = APIRouter(tags=["Chat IA"])
    store = history if history is not None else ChatHistoryStore()
    bearer = HTTPBearer(auto_error=False)

    def get_current_user_id(credentials: HTTPAuthorizationCredentials | None = Security(bearer)):
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(401, "Inicia sesión", headers={"WWW-Authenticate": "Bearer"})
        return auth.user_id(credentials.credentials)

    def get_db():
        try:
            return db_factory()
        except Exception:
            raise HTTPException(503, "Datos no disponibles") from None

    def verify_business_access(business_id: UUID, user_id: str = Depends(get_current_user_id)):
        db = get_db()  # Solo después de verificar firma, claims y expiración.
        bid = str(business_id)
        auth.verify_business_access(db, user_id, bid)
        return BusinessAccess(user_id, bid, db)

    def private(response: Response):
        response.headers["Cache-Control"] = "no-store"

    @router.get("/me/businesses")
    def my_businesses(response: Response, user_id: str = Depends(get_current_user_id)):
        private(response)
        try:
            rows = (get_db().table("businesses").select("id,business_name,owner_id")
                    .eq("owner_id", user_id).order("id").limit(100).execute()).data
            if not isinstance(rows, list) or any(str(row.get("owner_id")) != user_id for row in rows):
                raise ValueError()
            return {"businesses": [{"id": str(UUID(row["id"])), "business_name": row["business_name"]}
                                   for row in rows]}
        except Exception:
            raise HTTPException(503, "Negocios no disponibles") from None

    @router.post("/business/{business_id}/chat", response_model=ChatResponse)
    def chat(payload: ChatRequest, response: Response,
             access: BusinessAccess = Depends(verify_business_access)):
        private(response)
        with store.use(access.user_id, access.business_id,
                       str(payload.conversation_id) if payload.conversation_id else None) as conversation:
            try:
                # Existencia y ámbito del historial comprobados antes de evidencia/modelo.
                node = node_factory()
                packet = ChatGroundingService(access.db).build_packet(
                    access.business_id, payload.requested_date.isoformat() if payload.requested_date else None)
                answer = node.answer(payload.question, packet, business_id=access.business_id,
                                     history=store.writing_context(conversation, packet.resolved_date))
                store.append(conversation, payload.question, answer)
            except HTTPException:
                raise
            except Exception:
                # Evitar el handler global legado que imprime la excepción cruda.
                raise HTTPException(503, "No fue posible consultar la evidencia") from None
            return ChatResponse(conversation_id=conversation.id, answer=answer)

    @router.get("/business/{business_id}/chat/{conversation_id}")
    def get_history(conversation_id: UUID, response: Response,
                    access: BusinessAccess = Depends(verify_business_access)):
        private(response)
        with store.use(access.user_id, access.business_id, str(conversation_id)) as conversation:
            return {"conversation_id": conversation.id, "turns": list(conversation.turns)}

    @router.delete("/business/{business_id}/chat/{conversation_id}", status_code=204)
    def delete_history(conversation_id: UUID, response: Response,
                       access: BusinessAccess = Depends(verify_business_access)):
        private(response)
        with store.use(access.user_id, access.business_id, str(conversation_id)) as conversation:
            store.delete(access.user_id, access.business_id, conversation)
    return router
