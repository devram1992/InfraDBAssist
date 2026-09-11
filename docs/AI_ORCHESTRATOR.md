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


## 3. Tool Execution

After selecting the required capabilities, the AI Orchestrator executes the corresponding tools and collects their results.

### Execution Flow

```text id="3x6wqk"
Selected Tools
      ↓
Permission Check
      ↓
Tool Validation
      ↓
Execute Tool
      ↓
Collect Result
      ↓
Return Result to Orchestrator
```

### Example

For a database performance investigation:

```text id="9l0c5k"
AI Orchestrator
      │
      ├──► Oracle Tool
      │       └── Performance Data
      │
      ├──► Linux Tool
      │       └── Server Resource Data
      │
      └──► Knowledge RAG
              └── Previous RCA / Runbook
```

Independent tools can be executed **in parallel** to reduce response time.

## 4. Result Consolidation

The AI Orchestrator collects the results returned by the selected tools and consolidates them into a single, structured context.

### Consolidation Flow

```text
Tool Results
     ↓
Validate Results
     ↓
Remove Irrelevant Data
     ↓
Combine Evidence
     ↓
Build Context
     ↓
Send to Ollama
```

### Example

```text
Oracle Tool
   → Tablespace: 94%

Linux Tool
   → Filesystem: 65% used

Knowledge RAG
   → Previous RCA: Similar growth issue

Case Engine
   → Previous case: Tablespace expansion
```

The Orchestrator combines these results into:

```text
Consolidated Context
   ├── Current Database State
   ├── Infrastructure State
   ├── Historical Knowledge
   └── Previous Cases
```

## 5. Evidence & Response Generation

The Orchestrator sends the consolidated context and relevant evidence to the local AI engine through Ollama.

### Flow

```text id="c7m1ar"
Consolidated Context
        ↓
Evidence + Source Information
        ↓
Ollama / Local LLM
        ↓
Analyze & Generate Response
        ↓
Intelligent Answer
```

### Response Principles

* Base the response on the collected evidence.
* Clearly distinguish current data from historical information.
* Include relevant sources or evidence where available.
* Do not invent missing information.
* Clearly identify when required information could not be retrieved.
* Provide findings and practical recommendations.
* Maintain the read-only nature of the system.

### Example Response

```text id="k7lq1e"
Finding:
PRODDB USERS tablespace is at 94% utilization.

Evidence:
• Oracle: 94% tablespace utilization
• Linux: Filesystem has sufficient capacity
• Previous RCA: Similar growth issue identified

Recommendation:
Follow the approved tablespace management procedure.
```
## 6. Orchestrator Components

The AI Orchestrator is divided into focused components, with each component responsible for one part of the orchestration workflow.

```text id="2v8d4k"
AI Orchestrator
│
├── Intent Analyzer
│   └── Understands the engineer's question
│
├── Planner
│   └── Creates the investigation plan
│
├── Tool Selector
│   └── Selects required tools / capabilities
│
├── Tool Executor
│   └── Executes approved tools
│
├── Result Consolidator
│   └── Combines and validates tool results
│
└── Response Generator
    └── Prepares context and generates the final response
```

### Responsibilities

| Component           | Responsibility                                      |
| ------------------- | --------------------------------------------------- |
| Intent Analyzer     | Understand the user's request and intent            |
| Planner             | Determine the information required                  |
| Tool Selector       | Select appropriate capabilities/tools               |
| Tool Executor       | Execute authorized tools                            |
| Result Consolidator | Combine and validate results                        |
| Response Generator  | Send context to Ollama and prepare the final answer |

All components operate under the control of the **AI Orchestrator** and follow the system's security and read-only policies.

## 8. Tool Interface

All InfraDB Assist tools follow a common interface so that the AI Orchestrator can interact with different systems consistently.

### Tool Structure

```text id="x4g7j2"
Tool
├── Name
├── Description
├── Input Schema
├── Permission
├── Execute
└── Output Schema
```

### Example

```python id="5q7x2n"
class Tool:
    name: str
    description: str
    permission: str

    async def execute(self, request):
        ...
```

### Tool Categories

```text id="4k9b1m"
Knowledge Tools
 └── Knowledge Search

Database Tools
 ├── Oracle
 ├── PostgreSQL
 ├── MySQL
 ├── MongoDB
 ├── SingleStore
 └── Cloudera

Infrastructure Tools
 ├── Linux / OS
 └── Kubernetes

Incident & Case Tools
 ├── SMAX
 ├── Remedy
 └── Vendor Cases
```

### Design Principles

* Every tool exposes a defined set of permitted operations.
* Tools validate their inputs before execution.
* Production access is read-only.
* Tools return structured results.
* Tool execution is auditable.
* The Orchestrator does not depend on the internal implementation of a tool.

## 8. Error Handling

The AI Orchestrator must handle failures gracefully when a tool, database, infrastructure system, knowledge source, or external enterprise system is unavailable.

A failure in one capability should not automatically cause the entire investigation to fail.

### Error Handling Flow

```text
Tool Execution
      ↓
Check Result
      ↓
Success? ── Yes ──► Add Result to Context
   │
   No
   ↓
Capture Error
   ↓
Classify Error
   ↓
Continue / Retry / Stop
   ↓
Inform Orchestrator

## 9. Tool Registry & Tool Execution Framework

The Tool Registry provides a central mechanism for registering and discovering all tools available to the AI Orchestrator.

The Orchestrator uses the registry to determine:

- Which tools are available
- What each tool does
- What inputs are required
- What permissions are required
- Whether the tool is read-only
- How the tool should be executed
- What output format the tool returns

### Architecture

```text
                    AI ORCHESTRATOR
                           |
                           ▼
                    TOOL REGISTRY
                           |
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
     Database Tools   Infrastructure    Knowledge /
                      Tools             Case Tools
          │                │                │
     ┌────┼────┐       ┌───┴────┐       ┌──┴──────┐
     │    │    │       │        │       │         │
   Oracle MySQL ...   Linux  Kubernetes RAG      SMAX


## 10. RAG Architecture

RAG provides InfraDB Assist with relevant internal knowledge such as:

- Runbooks
- SOPs
- RCA
- Architecture Documents
- Wiki
- Internal Knowledge

### RAG Flow

```text
Engineer Question
       ↓
AI Orchestrator
       ↓
Knowledge Search
       ↓
Embedding
       ↓
PostgreSQL + pgvector
       ↓
Relevant Context
       ↓
AI Orchestrator
       ↓
Ollama / Local LLM
       ↓
Intelligent Answer
