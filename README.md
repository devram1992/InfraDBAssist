#DBCopilot
Enterprise AI Assistant for Database Operations

## Overview
InfraDB Assist is an internal AI-powered assistant designed to support Database and Infra Operations teams by providing a unified interface for documentation search, incident analysis, infrastructure monitoring, log analysis, capacity planning, and operational intelligence.
Built entirely on open source technologies, InfraDB Assist leverages Retrieval-Augmented Generation (RAG), AI agents, and enterprise integrations to help engineers troubleshoot issues faster, access operational knowledge, and improve incident resolution.

## Vision
To provide a single intelligent platform that enables database and Infra engineers to interact with enterprise knowledge, monitoring systems, logs, incidents, and operational data using natural language.

## Key Capabilities

* **Enterprise Knowledge Search** - Search runbooks, SOPs, architecture documents, and technical documentation using natural language.
* **Incident Analysis** - Analyze incidents, alerts, errors, and historical resolutions.
* **Database Intelligence** - Database health, performance, capacity, backup, replication, and troubleshooting.
* **Infrastructure Intelligence** - Server, storage, network, Kubernetes/openshift, and infrastructure health analysis.
* **Log Analysis** - Analyze and correlate database, application, system, and infrastructure logs.
* **Monitoring and Observability** - Query metrics, investigate alerts, and analyze system health.
* **AI-Assisted Troubleshooting** - Investigate issues and provide evidence-based recommendations.
* **Operational Knowledge** - Use existing operational knowledge, runbooks, incidents, and resolutions to provide context-aware guidance.



## Technology Stack

| Requirement | Tool |
|---|---|
| LLM Runtime | **Ollama** |
| LLM | **Qwen / Llama / Mistral** |
| Embeddings | **BGE-M3** |
| Vector Database | **PostgreSQL + pgvector** |
| Backend | **Python + FastAPI** |
| RAG Framework | **LlamaIndex / LangChain** |
| UI | **Open WebUI / React** |
| Authentication | **Keycloak** |
| Cache | **Redis** |
| Monitoring | **Prometheus + Grafana** |
| Logs | **Loki** |
| Containers | **Docker** |
| Production Orchestration | **Kubernetes** |
| Secrets Management | **HashiCorp Vault** |



