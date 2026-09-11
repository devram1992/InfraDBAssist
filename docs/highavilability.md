# InfraDB Assist - High Availability

## Objective

InfraDB Assist must remain available during individual component failures and support production workloads.

## Architecture

```text
Users
  │
  ▼
Load Balancer / Ingress
  │
  ├── Frontend Pod
  └── Frontend Pod
          │
          ▼
     FastAPI Pods
     ┌────┴────┐
     │         │
     ▼         ▼
 Orchestrator Orchestrator
     │
     ├── Database Tools
     ├── Infrastructure Tools
     ├── RAG
     └── Case Tools
     │
     ▼
PostgreSQL + pgvector
     │
     ▼
Ollama / Local LLM
