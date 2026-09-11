# InfraDB Assist - Tool Architecture

## Overview

Tools provide controlled access to enterprise database and infrastructure systems.

The AI Orchestrator selects and invokes tools based on the user's request.

## Database Tools

```text
Database Tools
├── Oracle
├── PostgreSQL
├── MySQL
├── MongoDB
├── SingleStore
└── Cloudera


Infrastructure Tools
Infrastructure Tools
├── Linux / OS
└── Kubernetes / OpenShift
Tool Execution
AI Orchestrator
       ↓
Tool Registry
       ↓
Permission Check
       ↓
Input Validation
       ↓
Tool Execution
       ↓
Structured Result
       ↓
AI Orchestrator
