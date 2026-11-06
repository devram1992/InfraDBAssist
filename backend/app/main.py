from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    status,
)
from pydantic import BaseModel, Field

from backend.app.ai.ollamaclient import OllamaClient
from backend.app.ai.orchestrator import AIOrchestrator
from backend.app.api.auth_dependency import get_authenticated_user
from backend.app.audit.event import AuditEvent
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
        create_keycloak_authentication_service(config)
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


# --------------------------------------------------
# Application service initialization
# --------------------------------------------------

orchestrator = AIOrchestrator()
app.state.orchestrator = orchestrator

ollama_client = OllamaClient()
app.state.ollama_client = ollama_client


# --------------------------------------------------
# Request and response models
# --------------------------------------------------

class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
    )


class AuditEventResponse(BaseModel):
    user_id: str
    username: str
    roles: list[str]
    tool_name: str
    permission: str
    request: dict
    status: str
    timestamp: datetime


class AuditEventsResponse(BaseModel):
    items: list[AuditEventResponse]
    total: int
    limit: int
    offset: int


# --------------------------------------------------
# Authentication
# --------------------------------------------------

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


# --------------------------------------------------
# Health API
# --------------------------------------------------

@app.get("/health")
async def health_check():
    ollama_health = await app.state.ollama_client.health_check()

    return {
        "status": "ok",
        "components": {
            "api": {
                "status": "healthy"
            },
            "ollama": ollama_health
        }
    }


# --------------------------------------------------
# Readiness API
# --------------------------------------------------

@app.get("/ready")
async def readiness_check():
    ollama_health = await app.state.ollama_client.health_check()

    ollama_ready = (
        ollama_health.get("available") is True
        and ollama_health.get("model_available") is True
    )

    response = {
        "status": "ready" if ollama_ready else "not_ready",
        "components": {
            "api": {
                "status": "healthy"
            },
            "ollama": ollama_health
        }
    }

    if not ollama_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response,
        )

    return response


# --------------------------------------------------
# Chat API
# --------------------------------------------------

@app.post("/api/v1/chat")
async def chat(
    request: ChatRequest,
    user: UserContext = Depends(authenticated_user),
):
    process_kwargs = {"user_context": user}

    # Preserve compatibility with callers that do not yet send a
    # conversation ID, while forwarding it for conversation-aware chats.
    if request.conversation_id is not None:
        process_kwargs["conversation_id"] = request.conversation_id

    return await app.state.orchestrator.process(
        request.question,
        **process_kwargs,
    )


# --------------------------------------------------
# Audit API
# --------------------------------------------------

@app.get(
    "/api/v1/audit",
    response_model=AuditEventsResponse,
)
async def get_audit_events(
    user: UserContext = Depends(authenticated_user),
    user_id: str | None = Query(default=None, min_length=1),
    tool_name: str | None = Query(default=None, min_length=1),
    status: str | None = Query(default=None),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    # Check audit access permission.
    if not user.has_permission("audit.read"):
        raise HTTPException(
            status_code=403,
            detail="Permission denied: audit.read",
        )

    # Validate audit status.
    if (
        status is not None
        and status not in AuditEvent.VALID_STATUSES
    ):
        raise HTTPException(
            status_code=422,
            detail="Invalid audit status.",
        )

    # Require timezone-aware timestamps.
    if (
        start_time is not None
        and start_time.utcoffset() is None
    ):
        raise HTTPException(
            status_code=422,
            detail="start_time must include a timezone.",
        )

    if (
        end_time is not None
        and end_time.utcoffset() is None
    ):
        raise HTTPException(
            status_code=422,
            detail="end_time must include a timezone.",
        )

    # Validate time range.
    if (
        start_time is not None
        and end_time is not None
        and start_time > end_time
    ):
        raise HTTPException(
            status_code=422,
            detail="start_time must be before or equal to end_time.",
        )

    # Use the same audit service used by ToolExecutor.
    audit_service = app.state.orchestrator.audit_service
    events = audit_service.list_events()

    # Apply filters.
    if user_id is not None:
        events = [
            event for event in events
            if event.user_id == user_id
        ]

    if tool_name is not None:
        events = [
            event for event in events
            if event.tool_name == tool_name
        ]

    if status is not None:
        events = [
            event for event in events
            if event.status == status
        ]

    if start_time is not None:
        events = [
            event for event in events
            if event.timestamp >= start_time
        ]

    if end_time is not None:
        events = [
            event for event in events
            if event.timestamp <= end_time
        ]

    # Return newest events first.
    events.sort(
        key=lambda event: event.timestamp,
        reverse=True,
    )

    total = len(events)

    # Apply pagination.
    paginated_events = events[offset:offset + limit]

    return AuditEventsResponse(
        items=[
            AuditEventResponse(
                user_id=event.user_id,
                username=event.username,
                roles=sorted(event.roles),
                tool_name=event.tool_name,
                permission=event.permission,
                request=event.request,
                status=event.status,
                timestamp=event.timestamp,
            )
            for event in paginated_events
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
