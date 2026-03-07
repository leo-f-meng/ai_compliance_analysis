# FlowMind

**FlowMind** is a deterministic AI workflow engine that converts
unstructured business text into structured risk assessments.

The system combines:

-   LLM-based structured extraction
-   Retrieval of compliance knowledge (RAG)
-   Deterministic guardrails
-   Rule-based risk scoring
-   Background task execution
-   Observability & error handling
-   Persistent run storage
-   Asynchronous processing

The goal is to build **auditable AI pipelines** suitable for compliance,
fintech, and regulated environments.

------------------------------------------------------------------------
## Quickstart (30 seconds)

### 1) Set env vars

Create `.env` and add OpenAI API key in the global envrionment:

```bash
OPEN_AI_KEY=your_key_here
OPEN_AI_MODEL=gpt-5-nano
```
Start the database:

```bash
    docker compose up -d
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
------------------------------------------------------------------------
# System Architecture
    input text
         │
         ▼
    RAG policy lookup
         │
         ▼
    LLM extraction
         │
         ▼
    guardrails
         │
         ▼
    risk rules
         │
         ▼
    structured decision

### RAG

Retrieves relevant risk policies from the knowledge base.

### LLM

Extracts candidate facts from unstructured text.

### Guardrails

Validate extraction quality and consistency.

### Risk Rules

Deterministically compute risk scores.

------------------------------------------------------------------------

# API

## Process text (sync)

POST /process

Request:

``` json
{
  "text": "ACME Ltd based in the UK wants to onboard as a SaaS customer."
}
```

Response:

``` json
{
    "entity_type": "company",
    "entity_name": "Unknown",
    "location": "Cayman Islands",
    "people": [],
    "intent": "open a SaaS account",
    "risk_flags": [
        "offshore jurisdiction risk",
        "Offshore location"
    ],
    "risk_score": 3,
    "summary": "Company incorporated in Cayman Islands flagged for offshore jurisdiction risk as part of SaaS account onboarding.",
    "citations": [
        {
            "doc_id": "1bb4f235-2127-4608-b988-44b59506d5db",
            "chunk_id": "21253efd-5074-4b2d-8ca0-f395af32465f",
            "chunk_index": 0,
            "content": "Companies incorporated in offshore jurisdictions such as the British Virgin Islands, Cayman Islands, or Panama should be flagged as offshore jurisdiction risk."
        }
    ]
}
```

------------------------------------------------------------------------

## Process text (async)

POST /process/async

Response:

``` json
{
  "run_id": "uuid",
  "status": "queued"
}
```

------------------------------------------------------------------------

## Get run status

GET /runs/{run_id}

Response:

``` json
{
    "run_id": "46788a87-555f-4d57-a510-e9f41ffbe80f",
    "status": "done",
    "created_at": "2026-03-07T18:09:07.556036+00:00",
    "model": "gpt-5-nano",
    "latency_ms": 20251,
    "usage": {
        "input_tokens": 916,
        "output_tokens": 2123,
        "total_tokens": 3039,
        "cost_usd_micros": 1411200
    },
    "error": null,
    "result": {
        "intent": "open SaaS account",
        "people": [],
        "summary": "A company incorporated in the Cayman Islands (an offshore jurisdiction) wants to open a SaaS account; offshore jurisdiction risk is flagged.",
        "location": "Cayman Islands",
        "citations": [
            {
                "doc_id": "1bb4f235-2127-4608-b988-44b59506d5db",
                "content": "Companies incorporated in offshore jurisdictions such as the British Virgin Islands, Cayman Islands, or Panama should be flagged as offshore jurisdiction risk.",
                "chunk_id": "21253efd-5074-4b2d-8ca0-f395af32465f",
                "chunk_index": 0
            }
        ],
        "risk_flags": [
            "offshore jurisdiction risk",
            "Offshore location"
        ],
        "risk_score": 3,
        "entity_name": "Unknown",
        "entity_type": "company"
    }
}
```

------------------------------------------------------------------------

## Ingest knowledge

POST /rag/ingest

Request:

``` json
{
  "title": "Offshore Jurisdiction Risk",
  "text": "Companies incorporated in the Cayman Islands or BVI should trigger the risk flag offshore jurisdiction risk."
}
```

This adds policy knowledge to the vector database.

------------------------------------------------------------------------

# Knowledge Base (RAG)

FlowMind stores compliance knowledge in a vector database.

Example entries:

    Risk Flag: offshore jurisdiction risk
    Condition: company incorporated in BVI, Cayman Islands, or Panama

    Risk Flag: crypto payment exposure
    Condition: company primarily uses cryptocurrency payments

These entries are retrieved during risk evaluation.

------------------------------------------------------------------------

# Guardrails

Guardrails ensure AI output is safe and consistent.

Examples:

-   schema validation
-   required fields present
-   extraction confidence threshold
-   logical consistency checks

Example issues:

    missing_company_name
    invalid_entity_type
    low_confidence_extraction

------------------------------------------------------------------------

# Risk Rules

Risk scoring is deterministic and reproducible.

Example rules:

    offshore jurisdiction risk → +3
    crypto payment exposure → +2
    unknown beneficial owner → +3

Risk levels:

  Score   Risk Level
  ------- ------------
  0--1    low
  2--3    medium
  4+      high

------------------------------------------------------------------------

# Database Schema

### runs

Stores workflow execution metadata.

    id
    status
    input_text
    result_json
    latency_ms
    model
    input_tokens
    output_tokens
    cost_usd_micros
    created_at

### documents

RAG knowledge documents.

    id
    title
    source
    created_at

### chunks

Vectorized knowledge chunks.

    id
    doc_id
    chunk_index
    content
    embedding

------------------------------------------------------------------------

# Tech Stack

-   FastAPI
-   PostgreSQL
-   pgvector
-   SQLAlchemy
-   OpenAI Responses API
-   Pydantic
-   Docker

------------------------------------------------------------------------

# Design Principles

### Deterministic decisions

LLMs extract facts, but rules determine risk.

### Auditability

Every run records tokens, latency, and result.

### Separation of concerns

-   LLM: extraction
-   RAG: knowledge retrieval
-   Rules: decisions

### Production-oriented AI

FlowMind focuses on reliability rather than pure generation.

------------------------------------------------------------------------

# Potential Extensions

-   evaluation dataset for RAG retrieval
-   hybrid retrieval (vector + keyword)
-   rule configuration via YAML
-   policy versioning
-   human review queue
-   tool calling

------------------------------------------------------------------------

# License

MIT
