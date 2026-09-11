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

Implement the Tool Registry
=======
Open:
backend/app/tools/registry.py

Put this:
from backend.app.tools.base import Tool

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())


(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist % cat backend/requirements.txt
annotated-doc==0.0.5
annotated-types==0.8.0
anyio==4.15.1
click==8.5.0
fastapi==0.141.1
h11==0.16.0
idna==3.19
packaging==26.3
pydantic==2.13.5
pydantic_core==2.46.5
setuptools==83.0.0
starlette==1.6.0
typing-inspection==0.4.4
typing_extensions==4.16.0
uvicorn==0.52.4
wheel==0.47.0
(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist % mkdir -p backend/app/tools
touch backend/app/tools/__init__.py
touch backend/app/tools/base.py
touch backend/app/tools/registry.py
(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist % 
(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist % 
(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist % find backend/app/tools -maxdepth 1 -type f
backend/app/tools/registry.py
backend/app/tools/__init__.py
backend/app/tools/base.py
(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist % 
(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist % mkdir -p backend/app/tools/oracle
touch backend/app/tools/oracle/__init__.py
touch backend/app/tools/oracle/tool.py
(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist % find backend/app/tools/oracle -maxdepth 1 -type f
backend/app/tools/oracle/__init__.py
backend/app/tools/oracle/tool.py
(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist % 
(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist % 
(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist % 
(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist % 
(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist % 
(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist % 
(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist %



We should test the framework before connecting to a real production database.

Create:

mkdir -p backend/app/tools/oracle
touch backend/app/tools/oracle/__init__.py
touch backend/app/tools/oracle/tool.py

Verify:

find backend/app/tools/oracle -maxdepth 1 -type f

Expected:

backend/app/tools/oracle/__init__.py
backend/app/tools/oracle/tool.py


Implement the Mock Oracle Tool

from backend.app.tools.base import Tool


class OracleTool(Tool):
    name = "oracle_database"
    description = "Read-only Oracle database diagnostics"
    permission = "database.read"
    read_only = True

    async def execute(self, request: dict) -> dict:
        return {
            "tool": self.name,
            "status": "success",
            "data": {
                "database": request.get("database", "UNKNOWN"),
                "status": "OPEN",
                "message": "Mock Oracle response"
            }
        }




# Initial Backend Implementation

The initial backend implementation includes:

- FastAPI application
- AI Orchestrator
- Tool Registry
- Common Tool interface
- Mock Oracle database tool
- Mock Linux infrastructure tool
- Rule-based tool selection
- Read-only tool execution model
- Git ignore configuration for Python cache files

### Current Tool Flow

```text
User Question
      ↓
FastAPI
      ↓
AI Orchestrator
      ↓
Tool Registry
      ↓
Selected Tool
      ↓
Structured Result
Current Tools
Tool	Name	Permission	Mode
Oracle	oracle_database	database.read	Read-only
Linux	linux	infrastructure.read	Read-only

The current tools return mock data for development and testing.

Real infrastructure and database connections will be added incrementally after the tool framework is validated.
