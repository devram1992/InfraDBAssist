# InfraDB Assist - Development Setup

## 1. Prerequisites
- macOS
- Git
- Docker Desktop
- Conda
- Python 3.12

## 2. Repository Setup

```bash
git clone <repository>
cd InfraDBAssist


3. Conda Environment
conda create -n infradb-assist python=3.12 -y
conda activate infradb-assist

Verify:

python --version
4. Backend Setup
mkdir -p backend/app
5. Python Dependencies
pip install fastapi uvicorn
pip show fastapi uvicorn

6. Backend Structure
backend/
└── app/




steps : 1 Create the First FastAPI Application (From Visual studio or directly from python in backend) 

Open:
backend/app/main.py

Put this code in it:
from fastapi import FastAPI

app = FastAPI(
    title="InfraDB Assist",
    description="AI-powered assistant for Infrastructure and Database Engineering",
    version="0.1.0",
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

Save it.
Then start the application:

(infradb-assist) ananddev@Anands-MacBook-Air ~/InfraDBAssist % python -m uvicorn backend.app.main:app --reload
