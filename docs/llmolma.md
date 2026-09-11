# InfraDB Assist - LLM / Ollama Architecture

## Overview

InfraDB Assist uses Ollama as the local AI runtime for hosting and serving open-source LLMs without external AI API dependencies.

## Architecture

```text
AI Orchestrator
      │
      │ Question + Relevant Context
      ▼
    Ollama
      │
      ▼
 Local LLM
(Qwen / Llama / Mistral)
      │
      ▼
 Generated Response
      │
      ▼
AI Orchestrator
      │
      ▼
Intelligent Answer
