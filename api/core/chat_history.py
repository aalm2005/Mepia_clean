"""Historial efímero acotado. No escribe auditorías, métricas ni memoria RAG."""
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Lock
from time import monotonic
from uuid import uuid4

from fastapi import HTTPException

from agents.chat_conversation import ChatAnswer


@dataclass
class Conversation:
    id: str
    touched: float
    turns: list[dict] = field(default_factory=list)
    lock: Lock = field(default_factory=Lock, repr=False)


class ChatHistoryStore:
    """Una instancia por proceso: 256 conversaciones, 8 turnos, 30 min inactivas."""
    def __init__(self, *, max_conversations=256, max_turns=8, ttl_seconds=1800, clock=monotonic):
        self.max_conversations = max_conversations
        self.max_turns = max_turns
        self.ttl_seconds = ttl_seconds
        self.clock = clock
        self._conversations: dict[tuple[str, str, str], Conversation] = {}
        self._lock = Lock()

    @contextmanager
    def use(self, user_id: str, business_id: str, conversation_id: str | None = None):
        with self._lock:
            now = self.clock()
            for key, item in list(self._conversations.items()):
                if now - item.touched >= self.ttl_seconds and not item.lock.locked():
                    del self._conversations[key]
            if conversation_id is None:
                if len(self._conversations) >= self.max_conversations:
                    raise HTTPException(429, "Límite de conversaciones alcanzado; espera o elimina una")
                conversation_id = str(uuid4())
                item = Conversation(conversation_id, now)
                self._conversations[(user_id, business_id, conversation_id)] = item
            else:
                item = self._conversations.get((user_id, business_id, conversation_id))
                if item is None:
                    raise HTTPException(404, "Conversación no disponible")
            if not item.lock.acquire(blocking=False):
                raise HTTPException(409, "La conversación está procesando otra solicitud")
            item.touched = now
        try:
            yield item
        finally:
            with self._lock:
                item.touched = self.clock()
                # Una solicitud fallida no reserva indefinidamente una conversación vacía.
                if not item.turns:
                    self._conversations.pop((user_id, business_id, conversation_id), None)
                item.lock.release()

    def append(self, conversation: Conversation, question: str, answer: ChatAnswer) -> None:
        turn = {"question": question, "answer": answer.model_dump(mode="json")}
        import json
        if len(json.dumps(turn, ensure_ascii=False)) > 60000:
            raise HTTPException(503, "Respuesta demasiado extensa para conservarla")
        conversation.turns.append(turn)
        del conversation.turns[:-self.max_turns]

    def delete(self, user_id: str, business_id: str, conversation: Conversation) -> None:
        with self._lock:
            self._conversations.pop((user_id, business_id, conversation.id), None)

    @staticmethod
    def writing_context(conversation: Conversation, resolved_date: str | None) -> list[dict]:
        # Nunca introducir resultados de otra fecha como evidencia de la actual.
        return [{"question": turn["question"], "answer": "\n".join(
            part["message"] for part in turn["answer"]["parts"]
            if part["generation_status"] == "validated")[:4000]}
            for turn in conversation.turns
            if turn["answer"]["resolved_date"] == resolved_date
            and any(part["kind"] != "greeting" for part in turn["answer"]["parts"])][-4:]
