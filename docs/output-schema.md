# Output Schema

## Job Status Response

`GET /jobs/{job_id}`

```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "complete",
  "doc_type": "DPA",
  "rag_score": "RED",
  "gate_decision": "BLOCKED",
  "created_at": "2026-04-02T09:14:22Z",
  "completed_at": "2026-04-02T09:15:01Z"
}
```

### `status` Values

| Value | Meaning |
|---|---|
| `processing` | Pipeline is running |
| `complete` | Pipeline finished, score assigned |
| `failed` | Pipeline error — escalated to AMBER automatically |
| `overridden` | A compliance officer has overridden the gate decision |

### `rag_score` Values

| Value | Meaning |
|---|---|
| `RED` | One or more Critical findings, or ≥ 2 High findings |
| `AMBER` | 1 High finding, or ≥ 3 Medium, or ≥ 5 Unclear |
| `GREEN` | No significant findings |

### `gate_decision` Values

| Value | Meaning |
|---|---|
| `BLOCKED` | Contract cannot proceed. Compliance officer override required. |
| `ESCALATED` | Reviewer sign-off required before proceeding. |
| `CLEARED` | Auto-cleared. Logged to audit trail. No action required. |
| `FAILED` | Pipeline error. Treated as ESCALATED. |

---

## Findings List Response

`GET /jobs/{job_id}/findings`

```json
[
  {
    "requirement_id": "ART28_DPA_EXECUTED",
    "severity": "critical",
    "status": "present",
    "confidence": 0.97,
    "reasoning": "Document is titled 'Data Processing Agreement' and includes execution clause.",
    "has_excerpt": true
  },
  {
    "requirement_id": "ART28_BREACH_NOTIFICATION",
    "severity": "critical",
    "status": "present",
    "confidence": 0.94,
    "reasoning": "Section 7.2 explicitly states notification within 72 hours of awareness.",
    "has_excerpt": true
  },
  {
    "requirement_id": "ART28_BREACH_72H",
    "severity": "high",
    "status": "absent",
    "confidence": 0.91,
    "reasoning": "Section 7.2 states '10 business days' — materially exceeds the 72-hour GDPR requirement.",
    "has_excerpt": true
  },
  {
    "requirement_id": "ART28_SUBPROCESSORS_LIST",
    "severity": "high",
    "status": "unclear",
    "confidence": 0.54,
    "reasoning": "Contract references a 'subcontractor schedule' but the schedule is not included in this document.",
    "has_excerpt": false
  },
  {
    "requirement_id": "BP_DATA_MINIMISATION",
    "severity": "low",
    "status": "absent",
    "confidence": 0.88,
    "reasoning": "No explicit data minimisation statement. Not a legal requirement — best practice only.",
    "has_excerpt": false
  }
]
```

### Finding Fields

| Field | Type | Description |
|---|---|---|
| `requirement_id` | string | Identifier from `requirements.yaml` (e.g. `ART28_BREACH_72H`) |
| `severity` | enum | `critical` \| `high` \| `medium` \| `low` |
| `status` | enum | `present` \| `absent` \| `unclear` |
| `confidence` | float | 0.0–1.0. Below 0.60 → forced to `unclear` |
| `reasoning` | string | One-sentence LLM explanation. Never contains "compliant", "legal", "valid", "approved" |
| `has_excerpt` | boolean | Whether a clause excerpt is available (expires after 30 days) |

### `severity` Definitions

| Severity | Definition |
|---|---|
| `critical` | Mandatory GDPR Art. 28 element completely absent (e.g. no DPA, no lawful basis) |
| `high` | Required element present but materially deficient (e.g. breach notification > 72h) |
| `medium` | Element present but ambiguous or incomplete (e.g. vague retention period) |
| `low` | Best practice missing — not a legal requirement |

### `status` Definitions

| Status | Definition |
|---|---|
| `present` | The requirement is satisfied by a clause in the document |
| `absent` | The requirement is not addressed in the document |
| `unclear` | The document contains relevant text but it is ambiguous, incomplete, or the model's confidence is below 0.60 |

**Important:** The system never outputs "compliant". `present` means the agent found evidence the requirement is addressed — not that the document is legally compliant with GDPR. That determination is made by a human reviewer.

---

## Upload Response

`POST /jobs/upload`

```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "processing"
}
```

Or, if the same document was already submitted (idempotent):

```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "complete",
  "existing": true
}
```

---

## Override Response

`POST /jobs/{job_id}/override`

```json
{
  "status": "overridden",
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "reviewer": "officer@example.com"
}
```

---

## Error Responses

### 422 — Validation Error

```json
{
  "detail": "File size exceeds maximum allowed size of 20MB."
}
```

```json
{
  "detail": "Unsupported file type. Only PDF and DOCX files are accepted."
}
```

```json
{
  "detail": "Could not extract text from this PDF. It may be a scanned image-only document. Please provide a text-based PDF or DOCX."
}
```

### 403 — Forbidden

```json
{
  "detail": "Only a compliance officer can override a RED-scored document."
}
```

```json
{
  "detail": "The document uploader cannot override their own document."
}
```

### 429 — Rate Limit

```json
{
  "detail": "Too many concurrent jobs"
}
```

```json
{
  "detail": "Daily job limit reached"
}
```

---

## Internal Domain Types

These types flow through the LangGraph pipeline and are not directly exposed via the API. Documented here for developers implementing or extending the pipeline.

### `Clause`

```python
{
    "text": "The Processor shall notify the Controller within 72 hours.",
    "clause_type": "breach_notification",
    "subject": "breach notification",
    "page": 3
}
```

### `Finding`

```python
{
    "requirement_id": "ART28_BREACH_72H",
    "severity": "high",
    "status": "absent",
    "confidence": 0.91,
    "reasoning": "Contract states 10 business days — exceeds the 72-hour maximum.",
    "clause_excerpt": "notify within 10 business days"   # max 500 chars, encrypted at rest
}
```

### `AnalysisState`

```python
{
    "job_id": "3fa85f64-...",
    "raw_text": "",            # never persisted
    "doc_type": "DPA",
    "clauses": [...],          # list[Clause]
    "findings": [...],         # list[Finding]
    "rag_score": "RED",
    "gate_decision": {
        "action": "BLOCKED",
        "rag_score": "RED"
    },
    "error": null
}
```
