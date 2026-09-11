# InfraDB Assist - Security & RBAC

## Overview

Security is enforced at the application, tool, database, and infrastructure levels.

```text
Engineer
   │
   ▼
Keycloak
(Authentication)
   │
   ▼
FastAPI
(RBAC | Authorization)
   │
   ▼
AI Orchestrator
   │
   ▼
Controlled Tools
   │
   ├── Database
   ├── Infrastructure
   ├── RAG
   └── Incident / Cases



Authentication
Keycloak provides user authentication.
Users are mapped to roles and permissions.
Authentication is required before accessing InfraDB Assist.
RBAC

Example roles:

Role	Access
DBA	Database tools and relevant knowledge
Infra	Infrastructure tools and relevant knowledge
Admin	Administrative functions
ReadOnly	Read-only investigation

Actual permissions will be configurable based on organizational requirements.

Tool Authorization

Every tool execution must pass authorization checks.




User Request
     ↓
Authentication
     ↓
RBAC Check
     ↓
Tool Permission Check
     ↓
Execute Tool



roduction Safety
Production access is read-only by default.
No arbitrary SQL or OS commands from the LLM.
Tools expose only approved operations.
Future remediation actions require explicit human approval.
Secrets

HashiCorp Vault will manage:

Database credentials
API credentials
Service credentials
Other sensitive secrets

Secrets must never be stored in source code, Git, prompts, logs, or database tables.

Audit

The system records:

User
Request
Tool invoked
Execution status
Timestamp
Result metadata

Audit logs must not contain passwords, tokens, or other sensitive secrets.
