# InfraDB Assist - Tool Security

## Overview

All database, infrastructure, RAG, and case-management operations are executed through controlled tools.

## Execution Flow

```text
User Request
     ↓
Authentication
     ↓
RBAC
     ↓
AI Orchestrator
     ↓
Tool Permission Check
     ↓
Input Validation
     ↓
Tool Execution
     ↓
Audit



Security Controls
=========
No direct system access from the LLM.
No arbitrary SQL execution.
No arbitrary OS command execution.
Production tools are read-only by default.
Tool inputs are validated.
Tool permissions are enforced by the backend.
Database access uses dedicated service accounts.
Credentials are retrieved from Vault.
Every tool execution is auditable.
