# InfraDB Assist - Production Deployment

## Deployment Model

InfraDB Assist is designed for production deployment on Kubernetes.

```text
                         USERS
                           │
                           ▼
                  Load Balancer / Ingress
                           │
                           ▼
                  React Frontend Pods
                           │
                           ▼
                     FastAPI Pods
                           │
                           ▼
                    AI Orchestrator
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
      Knowledge        Database        Infrastructure /
         RAG             Tools          Case Tools
          │                │                │
          ▼                ▼                ▼
   PostgreSQL +       Enterprise       Enterprise
      pgvector         Databases         Systems
          │
          ▼
        Ollama
      (Local LLM)

Production Components:
======================

| Component          | Technology             |
| ------------------ | ---------------------- |
| Container Platform | Kubernetes             |
| Frontend           | React + TypeScript     |
| Backend            | FastAPI                |
| AI Orchestrator    | Python                 |
| Local AI Runtime   | Ollama                 |
| LLM                | Qwen / Llama / Mistral |
| Database           | PostgreSQL             |
| Vector Store       | pgvector               |
| Authentication     | Keycloak               |
| Secrets            | HashiCorp Vault        |
| Cache              | Redis / Valkey         |
| Monitoring         | Prometheus + Grafana   |
| Logging            | Loki / ELK             |




Kubernetes Structure:
=========
deployment/
└── kubernetes/
    ├── namespace/
    ├── frontend/
    ├── backend/
    ├── ollama/
    ├── postgresql/
    ├── ingress/
    ├── services/
    ├── configmaps/
    └── secrets/

