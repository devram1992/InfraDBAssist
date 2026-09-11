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
6. Backend Structure
backend/
└── app/
