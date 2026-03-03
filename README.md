# FlowMind – AI-First Async Workflow Engine

FlowMind is a production-style AI workflow backend that converts unstructured business text into structured, validated, and auditable outputs.

Unlike simple chatbot demos, this project demonstrates how to integrate LLMs into deterministic, persistent, and observable systems.

---
## What This Project Demonstrates

This system is designed around real-world SaaS concerns:

- Structured extraction with strict schema validation
- Deterministic business guardrails
- Asynchronous processing
- Persistent run storage
- Cost tracking per request
- Observability & error handling
- Background task execution

This is not a prompt experiment.
This is an AI-native backend architecture.

---
## System Architecture

MindFlow is designed as an AI-first backend system that separates
probabilistic AI components from deterministic business logic.

1. API Layer
* FastAPI endpoints
* Sync + Async processing
* UUID-based run tracking

2. Orchestration Layer
* Background task execution
* Status transitions (queued → processing → done/failed)
* Failure persistence

3. AI Layer
* LLM structured extraction
* Strict JSON output
* Low-temperature inference

4. Guardrail Layer
* Schema validation (Pydantic)
* Deterministic business overrides
* Fail-fast error handling

5. Infrastructure Layer
* PostgreSQL (Dockerized)
* JSONB result storage
* Token tracking
* Cost estimation
* Structured logging
---
## End-to-End Flow

```text
User Input (Unstructured Text)
            │
            ▼
POST /process/async
            │
            ▼
Create Run Record (status=queued)
Persist to PostgreSQL
            │
            ▼
Background Task Triggered
(status=processing)
            │
            ▼
LLM Structured Extraction (JSON only)
            │
            ▼
Schema Validation (Pydantic)
            │
            ▼
Deterministic Risk Engine
            │
            ▼
Token Usage + Cost Estimation
            │
            ▼
Persist Result (status=done / failed)
            │
            ▼
GET /runs/{run_id}
Return:
- status
- structured result
- latency
- tokens
- cost
- error
```
---


## Quickstart (30 seconds)

### 1) Set env vars

Create `.env` and add OpenAI API key in the global envrionment:

```bash
OPEN_AI_KEY=your_key_here
OPEN_AI_MODEL=gpt-5-nano
```

Run the application:

```bash
pip install -e .
uvicorn app.main:app --reload
```

Open Swagger:

```bash
http://127.0.0.1:8000/docs
```
---

## Endpoints

### POST /process
Synchronous processing (returns result immediately).

### POST /process/async
Creates a run and immediately returns:

```json
{
  "run_id": "uuid",
  "status": "queued"
}
```

Background task processes the request.

### GET /runs/{run_id}
Returns:
```json
status (queued / processing / done / failed)
result_json
latency_ms
token usage
estimated cost
error (if any)
```

### GET /examples
Sample inputs for testing.