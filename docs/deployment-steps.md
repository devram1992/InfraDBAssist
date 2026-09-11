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
