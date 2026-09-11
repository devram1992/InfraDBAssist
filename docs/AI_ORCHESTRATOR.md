# 1.AI Orchestrator Design

## a. Purpose

The AI Orchestrator is the central decision-making component of InfraDB Assist.

It receives the engineer's question from the FastAPI API, determines what information is required, selects the appropriate capabilities, collects the results, consolidates the available evidence, and prepares the context for the local AI model.

The Orchestrator does not directly access databases, servers, Kubernetes, or enterprise systems. It interacts with them through controlled, read-only tools.

## b. Core Responsibility

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

## c. Capabilities Controlled by the Orchestrator

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

## d. Example

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

## e. Key Design Principle

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

## f. Primary Objective

The Orchestrator should ensure that InfraDB Assist provides:

* Relevant information
* Evidence-based analysis
* Controlled system access
* Traceable results
* Consistent responses
* Minimal unnecessary system calls

The Orchestrator is therefore the central coordination layer between the engineer, enterprise capabilities, and the local AI engine.


## 2. Tool Selection

The AI Orchestrator determines which capabilities are required to answer the engineer's question.

### Selection Flow

```text
Engineer Question
       ↓
AI Orchestrator
       ↓
Understand Intent
       ↓
Identify Required Information
       ↓
Select Capability / Tool(s)
```

### Examples

**Question:**

> What is the Oracle tablespace usage on PRODDB?

**Selected capability:**

```text
Database Tools → Oracle
```

**Question:**

> Show me the runbook for Oracle tablespace issues.

**Selected capability:**

```text
Knowledge RAG
```

**Question:**

> Why is PRODDB running out of space, and has this happened before?

**Selected capabilities:**

```text
Database Tools        → Oracle
Infrastructure Tools → Linux / OS
Knowledge RAG         → Previous RCA / Runbook
Incident & Case       → Similar Cases
```

### Selection Principles

* Select only the capabilities required for the question.
* Use multiple capabilities when the investigation requires information from different sources.
* Execute independent tools in parallel where possible.
* Verify user permissions before executing a tool.
* The LLM must not directly access enterprise systems.

