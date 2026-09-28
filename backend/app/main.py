from fastapi import Depends, FastAPI, Header

from pydantic import BaseModel

from backend.app.ai.orchestrator import AIOrchestrator
from backend.app.api.auth_dependency import get_authenticated_user
from backend.app.auth.authentication import AuthenticationService
from backend.app.auth.user_context import UserContext


app = FastAPI(
    title="InfraDB Assist",
    description=(
        "AI-powered assistant for Infrastructure "
        "and Database Engineering"
    ),
    version="0.1.0",
)

orchestrator = AIOrchestrator()
app.state.orchestrator = orchestrator


class ChatRequest(BaseModel):
    question: str


def get_authentication_service() -> AuthenticationService:
    return app.state.authentication_service


async def authenticated_user(
    authorization: str | None = Header(default=None),
    authentication_service: AuthenticationService = Depends(
        get_authentication_service
    ),
) -> UserContext:
    return await get_authenticated_user(
        authorization=authorization,
        authentication_service=authentication_service,
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/v1/chat")
async def chat(
    request: ChatRequest,
    user: UserContext = Depends(authenticated_user),
):
    return await app.state.orchestrator.process(
        request.question,
        user_context=user,
    )