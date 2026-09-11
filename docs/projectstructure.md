# InfraDB Assist - Project Structure

```text
InfraDBAssist/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── ai/
│   │   ├── rag/
│   │   ├── knowledge/
│   │   ├── incidents/
│   │   ├── support_cases/
│   │   ├── databases/
│   │   ├── infrastructure/
│   │   ├── tools/
│   │   │   ├── oracle/
│   │   │   ├── postgres/
│   │   │   ├── mysql/
│   │   │   ├── mongodb/
│   │   │   ├── singlestore/
│   │   │   ├── cloudera/
│   │   │   ├── linux/
│   │   │   └── kubernetes/
│   │   ├── audit/
│   │   └── config/
│   └── tests/
│
├── frontend/
│
├── ingestion/
│   ├── internal/
│   └── support_cases/
│
├── database/
│   ├── migrations/
│   └── seeds/
│
├── deployment/
│   ├── docker/
│   └── kubernetes/
│
├── docs/
│
├── docker-compose.yml
└── README.md


**| Directory                    | Purpose                                  |
| ---------------------------- | ---------------------------------------- |
| `backend/app/ai`             | AI Orchestrator and AI logic             |
| `backend/app/rag`            | RAG and retrieval                        |
| `backend/app/tools`          | Tool implementations                     |
| `backend/app/databases`      | Database integrations                    |
| `backend/app/infrastructure` | Infrastructure integrations              |
| `backend/app/incidents`      | Incident and case integrations           |
| `frontend`                   | React conversational interface           |
| `ingestion`                  | Knowledge and case ingestion             |
| `database`                   | Schema migrations and seed data          |
| `deployment`                 | Docker and Kubernetes configuration      |
| `docs`                       | Architecture and technical documentation |
**
