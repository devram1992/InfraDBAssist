from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header
from pydantic import BaseModel

from backend.app.ai.orchestrator import AIOrchestrator
from backend.app.api.auth_dependency import get_authenticated_user
from backend.app.auth.authentication import AuthenticationService
from backend.app.auth.keycloak_auth_factory import (
    create_keycloak_authentication_service,
)
from backend.app.auth.keycloak_settings import load_keycloak_config
from backend.app.auth.user_context import UserContext


@asynccontextmanager
async def lifespan(application: FastAPI):
    config = load_keycloak_config()

    application.state.authentication_service = (
        create_keycloak_authentication_service(
            config
        )
    )

    yield


app = FastAPI(
    title="InfraDB Assist",
    description=(
        "AI-powered Infrastructure "
        "and Database Engineering"
    ),
    version="0.1.0",
    lifespan=lifespan,
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
