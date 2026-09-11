# InfraDB Assist - Configuration Management

## Overview

Application configuration must be separated from source code and managed independently for each environment.

## Configuration Areas

- Application settings
- Database connections
- Ollama / LLM configuration
- RAG configuration
- Tool configuration
- Keycloak configuration
- Redis / Valkey configuration
- Logging and monitoring settings

## Environment Separation

```text
Development
     │
     ▼
Test
     │
     ▼
Production


Secrets
=========
Sensitive values must be stored in HashiCorp Vault.

Examples:

Database credentials
Keycloak secrets
Enterprise API credentials
Service account credentials
Encryption keys

Secrets must never be committed to Git.


Kubernetes
    │
    ├── ConfigMap ──► Non-sensitive configuration
    │
    └── Vault ──────► Secrets
                         │
                         ▼
                    FastAPI / Tools




Principles
==========
No hardcoded credentials.
No secrets in Git.
Environment-specific configuration.
Centralized secret management.
Configuration changes must be auditable.
