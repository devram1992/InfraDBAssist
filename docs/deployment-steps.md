# InfraDB Assist - Development Setup

## Prerequisites

- Git
- Docker Desktop
- Conda
- Python 3.12

## Conda Environment

```bash
conda create -n infradb-assist python=3.12 -y
conda activate infradb-assist

Verify:

python --version
Backend Setup
mkdir -p backend/app
touch backend/app/__init__.py
touch backend/app/main.py
Python Dependencies
python -m pip install fastapi uvicorn
FastAPI Application

Run from the project root:

python -m uvicorn backend.app.main:app --reload

Application:

http://127.0.0.1:8000

Health check:

curl http://127.0.0.1:8000/health

Expected:

{"status":"ok"}
Important

Use:

python -m uvicorn

instead of relying on the system uvicorn command, because multiple Python installations may exist on the development machine.

Add to git:
=======
git add docs/DEVELOPMENT_SETUP.md
git commit -m "Add development setup documentation"
git push origin main

Connect Orchestrator to FastAPI
===================
Open:

backend/app/main.py

Replace its contents with:

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

Save it.


Test the Chat API
=================

Keep Uvicorn running and, in another terminal, run:

curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the Oracle database status?"}'

Expected response:

{
  "question": "What is the Oracle database status?",
  "status": "received",
  "message": "AI Orchestrator received the request."



Save Dependencies:
======
We should record the exact Python packages before adding more components.
Run:
pip freeze > backend/requirements.txt
Then verify:
cat backend/requirements.txt


Implement the Common Tool Interface
=========
Open:
backend/app/tools/base.py

Put this:
from abc import ABC, abstractmethod
class Tool(ABC):
    name: str
    description: str
    permission: str
    read_only: bool = True

    @abstractmethod
    async def execute(self, request: dict) -> dict:
        """Execute the tool and return a structured result."""
        pass


