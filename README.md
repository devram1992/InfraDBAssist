#DBCopilot
Enterprise AI Assistant for Database Operations

## Overview
InfraDB Assist is an internal AI-powered assistant designed to support Database and Infra Operations teams by providing a unified interface for documentation search, incident analysis, infrastructure monitoring, log analysis, capacity planning, and operational intelligence.
Built entirely on open source technologies, InfraDB Assist leverages Retrieval-Augmented Generation (RAG), AI agents, and enterprise integrations to help engineers troubleshoot issues faster, access operational knowledge, and improve incident resolution.

## Vision
To provide a single intelligent platform that enables database and Infra engineers to interact with enterprise knowledge, monitoring systems, logs, incidents, and operational data using natural language.


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


Key Capabilities
Enterprise Knowledge Search
Search runbooks, SOPs, architecture documents, troubleshooting guides, and technical documentation using natural language.
Incident Analysis
Analyze incidents, errors, alerts, and historical resolutions to identify potential causes and recommended actions.
Database Intelligence
Assist with database health checks, performance analysis, capacity planning, backup validation, replication checks, and operational troubleshooting.
Infrastructure Intelligence
Analyze server health, CPU, memory, storage, network, Kubernetes resources, and infrastructure alerts.
Log Analysis
Correlate and analyze application, database, system, and infrastructure logs.
Monitoring Integration
Query monitoring and observability platforms to provide operational insights through natural language.
AI-Assisted Troubleshooting
Use AI agents and enterprise tools to investigate issues and provide evidence-based recommendations.
Operational Knowledge
Learn from existing documentation, incidents, resolutions, and operational procedures to improve troubleshooting consistency.
