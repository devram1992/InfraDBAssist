# InfraDB Assist - API Design

## Overview

FastAPI provides the backend API between the conversational interface and the AI Orchestrator.

```text
React UI
   │
   ▼
FastAPI
   │
   ├── Authentication / RBAC
   ├── Conversation Management
   ├── AI Orchestrator
   ├── Tool Execution
   └── Audit


| Method | Endpoint                     | Purpose                           |
| ------ | ---------------------------- | --------------------------------- |
| POST   | `/api/v1/chat`               | Send a question to InfraDB Assist |
| GET    | `/api/v1/conversations`      | List conversations                |
| GET    | `/api/v1/conversations/{id}` | Get conversation history          |
| POST   | `/api/v1/conversations`      | Create conversation               |
| DELETE | `/api/v1/conversations/{id}` | Delete conversation               |
| GET    | `/api/v1/health`             | Application health check          |


API Principles
=============
REST API using FastAPI.
API versioning using /api/v1.
Authentication and RBAC enforced by the backend.
User input must be validated.
Tool permissions must be checked before execution.
API activity must be auditable.
Sensitive information must not be returned in API responses.
