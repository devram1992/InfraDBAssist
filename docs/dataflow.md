# InfraDB Assist - End-to-End Data Flow

## Request Flow

```text
Engineer
   │
   ▼
React UI
   │
   ▼
Keycloak
(Authentication)
   │
   ▼
FastAPI
(RBAC | Validation | Audit)
   │
   ▼
AI Orchestrator
   │
   ├──► Knowledge RAG
   │
   ├──► Database Tools
   │
   ├──► Infrastructure Tools
   │
   └──► Incident & Case Engine
            │
            ▼
       Results / Evidence
            │
            ▼
      AI Orchestrator
            │
            ▼
          Ollama
         Local LLM
            │
            ▼
     Intelligent Answer
            │
            ▼
        React UI


Security Boundaries
=======
Users authenticate through Keycloak.
FastAPI enforces RBAC and authorization.
The Orchestrator can access only registered tools.
Tools enforce their permitted operations.
Production systems are read-only by default.
Secrets are retrieved from HashiCorp Vault.
The LLM has no direct access to enterprise systems.
Tool execution and important user activity are audited.



Data Principles:
======
Enterprise systems remain the systems of record.
Only required information is passed to the LLM.
Sensitive data must be protected throughout the flow.
RAG content must retain source information.
Historical information must be distinguished from live system data.
No external AI API is required.
