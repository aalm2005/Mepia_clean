"""Servidor exclusivamente sintético para el E2E local. Nunca usar en despliegue."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from api.chat import create_chat_router
from api.core.chat_history import ChatHistoryStore
from agents.chat_conversation import ChatConversationNode
from agents.chat_provider_gemini import GeminiCompletion
from agents.chat_response import ChatJsonCompletionAdapter
from tests.test_chat_api import AUTH, DB, SimulatedSDK, token, USER_A, USER_B, BIZ_A, BIZ_B, BIZ_C

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:3015", "http://localhost:3015", "http://127.0.0.1:3018", "http://localhost:3018"],
                   allow_methods=["*"], allow_headers=["*"], allow_credentials=False)
db = DB()
sdk = SimulatedSDK()


def node():
    adapter = ChatJsonCompletionAdapter(GeminiCompletion(api_key="synthetic-chat-key", model="synthetic-model",
                                                       max_calls=2, client=sdk))
    return ChatConversationNode(writer=adapter, verifier=adapter)


app.include_router(create_chat_router(auth=AUTH, db_factory=lambda: db, node_factory=node, history=ChatHistoryStore()))


@app.get("/__test__/session/{who}")
def session(who: str):
    user = USER_A if who == "a" else USER_B
    return {"access_token": token(user), "token_type": "bearer", "expires_in": 300,
            "refresh_token": "synthetic-refresh-" + who, "user": {"id": user, "aud": "authenticated", "role": "authenticated",
             "email": f"{who}@example.invalid", "app_metadata": {}, "user_metadata": {},
             "created_at": "2026-10-12T00:00:00Z"}}


@app.post("/auth/v1/token")
async def auth_token(request: Request):
    body = await request.json()
    if request.query_params.get("grant_type") == "refresh_token":
        who = "a" if body.get("refresh_token") == "synthetic-refresh-a" else "b" if body.get("refresh_token") == "synthetic-refresh-b" else None
    else:
        who = "a" if body.get("email") == "a@example.invalid" else "b" if body.get("email") == "b@example.invalid" else None
        if body.get("password") != "synthetic-test-password":
            who = None
    if who is None:
        return JSONResponse({"msg": "Invalid login credentials", "code": "invalid_credentials"}, status_code=400)
    return session(who)


@app.get("/auth/v1/user")
def auth_user(request: Request):
    raw = request.headers.get("authorization", "")
    try:
        user = AUTH.user_id(raw.removeprefix("Bearer "))
    except Exception:
        return JSONResponse({"msg": "Invalid session"}, status_code=401)
    if user not in {USER_A, USER_B}:
        return JSONResponse({"msg": "Invalid session"}, status_code=401)
    return session("a" if user == USER_A else "b")["user"]


@app.post("/auth/v1/logout")
def auth_logout():
    return Response(status_code=204)


@app.get("/__test__/state")
def state():
    return {"business_a": BIZ_A, "business_b": BIZ_B, "business_c": BIZ_C,
            "model_calls": len(sdk.calls), "table_calls": list(db.calls)}
