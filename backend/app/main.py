from fastapi import FastAPI
from pydantic import BaseModel

from backend.app.ai.orchestrator import AIOrchestrator

app = FastAPI(
    title="InfraDB Assist",
    description="AI-powered assistant for Infrastructure and Database Engineering",
    version="0.1.0",
)

orchestrator = AIOrchestrator()


class ChatRequest(BaseModel):
    question: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    return await orchestrator.process(request.question)