                                      ┌──────────────────────────────┐
                                      │          ENGINEERS           │
                                      │                              │
                                      │   DBA | Infra | Platform     │
                                      └──────────────┬───────────────┘
                                                     │
                                                     ▼
                                      ┌──────────────────────────────┐
                                      │          InfraDB AI           │
                                      │                              │
                                      │   Conversational Interface   │
                                      │      React / TypeScript      │
                                      └──────────────┬───────────────┘
                                                     │
                                                     ▼
                                      ┌──────────────────────────────┐
                                      │          FastAPI API          │
                                      │                              │
                                      │     Authentication | RBAC     │
                                      │            | Audit            │
                                      └──────────────┬───────────────┘
                                                     │
                                                     ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │                    AI ORCHESTRATOR                      │
                  │                                                         │
                  │        Understand → Plan → Investigate → Answer        │
                  └───────┬──────────────┬──────────────┬────────────┬─────┘
                          │              │              │            │
                          ▼              ▼              ▼            ▼
                 ┌──────────────┐ ┌──────────────┐ ┌────────────┐ ┌──────────────┐
                 │  KNOWLEDGE   │ │   DATABASE   │ │   INFRA    │ │ INCIDENT &   │
                 │     RAG      │ │    TOOLS     │ │   TOOLS    │ │ CASE ENGINE  │
                 │              │ │              │ │            │ │              │
                 │ Internal KB  │ │ Oracle       │ │ Linux / OS │ │ SMAX         │
                 │ Runbooks     │ │ PostgreSQL   │ │ Kubernetes │ │ Remedy       │
                 │ SOPs         │ │ MySQL        │ │ Servers    │ │ Vendor Cases │
                 │ RCA          │ │ MongoDB      │ │ Processes  │ │              │
                 │ Architecture │ │ SingleStore  │ │ Resources  │ │              │
                 │ Wiki         │ │ Cloudera     │ │ Health     │ │              │
                 └──────┬───────┘ └──────────────┘ └────────────┘ └──────────────┘
                        │
                        ▼
                 ┌─────────────────┐
                 │ PostgreSQL +    │
                 │    pgvector     │
                 │                 │
                 │ Knowledge       │
                 │ Embeddings      │
                 │ Conversations   │
                 │ Metadata        │
                 │ Audit           │
                 └─────────────────┘


                  ┌───────────────────────────────────────┐
                  │          LOCAL AI ENGINE              │
                  │                                       │
                  │                Ollama                 │
                  │                                       │
                  │              Local LLM                │
                  │        Qwen / Llama / Mistral         │
                  └───────────────────▲───────────────────┘
                                      │
                                      │ Question + Relevant Context
                                      │
                              ┌───────┴────────┐
                              │ AI ORCHESTRATOR│
                              └────────────────┘
                                      │
                                      ▼
                              Intelligent Answer
