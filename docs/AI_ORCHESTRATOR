# AI Orchestrator Design

## 1. Purpose

The AI Orchestrator is the central decision-making component of InfraDB Assist.

It receives the engineer's question from the FastAPI API, determines what information is required, selects the appropriate capabilities, collects the results, consolidates the available evidence, and prepares the context for the local AI model.

The Orchestrator does not directly access databases, servers, Kubernetes, or enterprise systems. It interacts with them through controlled, read-only tools.

## 2. Core Responsibility

The Orchestrator follows this logical flow:

```text
Engineer Question
       ↓
Understand
       ↓
Plan
       ↓
Select Required Capabilities
       ↓
Execute Tools / RAG
       ↓
Collect Results
       ↓
Validate & Consolidate Evidence
       ↓
Prepare LLM Context
       ↓
Local AI Engine (Ollama)
       ↓
Intelligent Answer
```

## 3. Capabilities Controlled by the Orchestrator

The Orchestrator can use one or more of the following capabilities depending on the question:

* **Knowledge RAG**

  * Internal Knowledge
  * Runbooks
  * SOPs
  * RCA
  * Architecture
  * Wiki

* **Database Tools**

  * Oracle
  * PostgreSQL
  * MySQL
  * MongoDB
  * SingleStore
  * Cloudera

* **Infrastructure Tools**

  * Linux / OS
  * Kubernetes
  * Servers
  * Processes
  * Resources
  * Health

* **Incident & Case Engine**

  * SMAX
  * Remedy
  * Vendor Cases

The Orchestrator may invoke a single capability or multiple capabilities in parallel when required.

## 4. Example

For a question such as:

> "Why is PRODDB Oracle database slow?"

The Orchestrator may determine that it needs:

```text
Oracle Tool
    ↓
Database performance information

Infrastructure Tool
    ↓
Server CPU / Memory / I/O information

Knowledge RAG
    ↓
Relevant runbooks / previous RCA

Incident & Case Engine
    ↓
Similar historical cases
```

The results are then consolidated and passed as relevant context to the local AI engine.

## 5. Key Design Principle

The Orchestrator is the **central controller**, while the individual capabilities are controlled execution layers.

```text
                    AI ORCHESTRATOR
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
    Knowledge RAG    Database Tools    Infrastructure
                                           Tools
                           │
                           ↓
                 Incident & Case Engine
```

The local LLM must not have unrestricted access to enterprise systems.

All system access must happen through controlled tools with defined permissions and read-only access.

## 6. Primary Objective

The Orchestrator should ensure that InfraDB Assist provides:

* Relevant information
* Evidence-based analysis
* Controlled system access
* Traceable results
* Consistent responses
* Minimal unnecessary system calls

The Orchestrator is therefore the central coordination layer between the engineer, enterprise capabilities, and the local AI engine.
