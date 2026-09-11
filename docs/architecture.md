ENGINEERS(DB,Infra)
    │
    ▼
InfraDB AI
(Conversational Interface)
    │
    ▼
FastAPI
(Authentication | RBAC | Audit)
    │
    ▼
AI ORCHESTRATOR
(Understand | Plan | Select Tools | Investigate | Consolidate)
    │
    ├──────────► Knowledge RAG
    │            (Internal KB | Runbooks | SOPs | RCA | Architecture | Confluence page )
    │                         │
    │                         ▼
    │                  PostgreSQL + pgvector
    │                  (Knowledge | Embeddings |
    │                   Conversations | Metadata)
    │
    ├──────────► Database Tools
    │            (Oracle | PostgreSQL | MySQL |
    │             MongoDB | SingleStore | Cloudera)
    │
    ├──────────► Infrastructure Tools
    │            (Linux/OS | Kubernetes/OpenShift)
    │ 
    │
    └──────────► Incident & Case Engine
                 (SMAX | Remedy | Vendor Cases)
                         │
                         ▼
                   Results Return
                         │
                         ▼
                  AI ORCHESTRATOR
                         │
                         │ Question + Relevant Context
                         ▼
                      Ollama
                   (Local LLM)
                         │
                         ▼
                INTELLIGENT ANSWER
                (Findings | Evidence |
                 Recommendations)



                 
