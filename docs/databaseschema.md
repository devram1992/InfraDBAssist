# InfraDB Assist - Database Schema

## Overview

InfraDB Assist uses **PostgreSQL + pgvector** as the primary application and knowledge store.

```text
PostgreSQL
│
├── users
├── conversations
├── messages
├── knowledge_documents
├── knowledge_chunks
├── audit_logs
└── tool_executions
Core Tables
Table	Purpose
users	Application users, roles and status
conversations	Chat sessions
messages	User and AI messages
knowledge_documents	RAG document metadata
knowledge_chunks	Document chunks and embeddings
audit_logs	User and system activity
tool_executions	AI Orchestrator tool execution history
Key Data
users
    id, username, email, role, status, created_at

conversations
    id, user_id, title, created_at, updated_at

messages
    id, conversation_id, role, content, created_at

knowledge_documents
    id, title, source, document_type, version, status

knowledge_chunks
    id, document_id, chunk_text, embedding, metadata

audit_logs
    id, user_id, action, resource, status, details, created_at

tool_executions
    id, user_id, tool_name, input, output, status, execution_time
Relationships
users
 ├── conversations ──► messages
 ├── audit_logs
 └── tool_executions

knowledge_documents
 └── knowledge_chunks ──► embedding (pgvector)
