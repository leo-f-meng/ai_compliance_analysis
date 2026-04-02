# Guardrails

The system is used in a hard-gate capacity: Red-scored contracts cannot proceed until overridden. This means failures, hallucinations, or misuse must be caught before they produce incorrect gate decisions. Guardrails are implemented at four layers.

---

## Layer 1 — LLM Output Guardrails

### Structured Output Enforcement

Every LLM call uses LangChain structured output with a Pydantic schema. The model cannot return free-form text — it must emit a typed `Finding` object:

```python
class Finding(BaseModel):
    requirement_id: str
    severity: Severity
    status: FindingStatus      # present | absent | unclear
    confidence: float          # 0.0–1.0
    reasoning: str
    clause_excerpt: str
```

If the model output cannot be parsed into this schema, the finding is automatically set to `status=unclear, confidence=0.0` — never to `absent`. A parse failure cannot trigger a Red gate.

### Confidence Floor

Any finding with `confidence < 0.60` is forced to `status=unclear` before entering the scoring function, regardless of what the model returned:

```python
def apply_confidence_floor(findings, confidence_floor=0.60):
    for f in findings:
        if f.confidence < confidence_floor:
            f.status = FindingStatus.UNCLEAR
```

`Unclear` findings can only contribute to Amber (≥5 Unclear), not Red. A model that is uncertain about a Critical requirement cannot hard-block a contract.

### Vocabulary Guard

A post-generation regex check runs on every LLM output (reasoning field) before it enters the pipeline. Forbidden words:

> `compliant`, `compliance`, `legal`, `legally`, `valid`, `validity`, `approved`, `approval`

If any forbidden word is found, the finding is quarantined:

```python
def check_vocabulary(text: str) -> None:
    if FORBIDDEN_PATTERN.search(text):
        raise VocabularyViolationError(...)
```

Quarantined findings become `status=unclear, confidence=0.0`. The system never asserts that a contract is "legally compliant" — that is a human determination.

### Temperature = 0

All compliance-path LLM calls use `temperature=0`. This makes the model deterministic: the same input always produces the same output. Non-determinism in a hard-gate system is a defect.

---

## Layer 2 — Pipeline Guardrails

### Fail Closed

Any unhandled exception, timeout, or LLM API failure sets the job status to `failed` and the gate decision to `ESCALATED` (Amber). The pipeline never fails to Green.

```python
except Exception as e:
    job.status = "failed"
    job.rag_score = RagScore.AMBER.value
    job.gate_decision = GateAction.ESCALATED.value
```

A reviewer must still sign off a failed job — it cannot auto-proceed.

### Idempotent Jobs

Each job is identified by the SHA-256 hash of the uploaded file content. Re-uploading the same document returns the existing job result — no duplicate processing, no duplicate findings.

```python
existing = db.query(Job).filter(
    Job.filename_hash == file_hash,
    Job.uploaded_by == user_id,
).first()
if existing:
    return {"job_id": str(existing.id), "status": existing.status, "existing": True}
```

### File Validation

Before any processing begins:

1. **Size check**: file must be ≤ 20 MB (configurable via `MAX_UPLOAD_MB`).
2. **Magic bytes check**: file must start with `%PDF` (PDF) or `PK\x03\x04` (DOCX/ZIP). Extension is not trusted.
3. **Text extraction check**: PDFs that yield no text after extraction are rejected with an actionable error message ("may be a scanned image-only document"). They are not silently passed to the pipeline with empty text.

### Rate Limiting

FastAPI middleware enforces per-user limits:

- Max 10 concurrent jobs per user
- Max 50 jobs per day per user

Both limits are configurable via environment variables. Exceeding either returns HTTP 429.

### LangGraph Checkpointing

LangGraph `MemorySaver` checkpointing is enabled on the pipeline. If a node fails mid-run, the graph resumes from the last successfully completed node on retry — it does not restart from the beginning. This prevents partial re-analysis and inconsistent findings.

---

## Layer 3 — Gate & Override Guardrails

### Role-Based Override

| Gate Score | Who Can Override |
|---|---|
| RED | `compliance_officer` role only |
| AMBER | `reviewer` or `compliance_officer` role |

Role is re-verified against the PostgreSQL `users` context on every override submission. A JWT claim alone is not sufficient — the role must be confirmed in the database at the time of the override.

### Override Reason Required

The override form enforces:
- Minimum 50-character reason text (Pydantic `field_validator`)
- At least one mitigating control selected from a predefined list

```python
_VALID_MITIGATING_CONTROLS = [
    "existing_dpa_under_negotiation",
    "legal_team_reviewed",
    "compensating_security_controls",
    "dpia_completed",
    "transfer_impact_assessment_done",
    "supplier_security_audit_completed",
    "contractual_amendment_in_progress",
    "data_minimisation_implemented",
    "encryption_deployed",
]
```

A blank reason or a one-word justification cannot be submitted.

### No Self-Override

The user who uploaded the document cannot override its gate result:

```python
if job.uploaded_by == user_id:
    raise HTTPException(status_code=403, detail="The document uploader cannot override their own document.")
```

This enforces separation of duties. The person with a business interest in the contract proceeding cannot also be the compliance gatekeeper.

### Append-Only Audit Trail

The `overrides` table has no `updated_at` column. The application database user has no `UPDATE` or `DELETE` grants on this table. Every override is a permanent, immutable record containing:

- `reviewer_id` — who made the decision
- `original_score` — what the system found
- `override_reason` — why the override was made
- `mitigating_controls` — what compensating controls were cited
- `findings_snapshot` — the full findings list at the time of override (JSONB)
- `created_at` — timestamp

Override records cannot be edited or deleted, even by administrators.

---

## Layer 4 — Data Guardrails

### Raw Document Not Persisted

The uploaded file is written to `/tmp`, processed in memory, and deleted immediately after the `parse_document` node completes. Raw contract text is never written to the database.

### Clause Excerpts: Encrypted + Short-Lived

Clause excerpts (up to 500 characters of contract text stored to give reviewers context) are:

1. **Encrypted at rest** using AES-256-GCM with a per-job key
2. **Short-lived**: a nightly maintenance task nulls out excerpts where `excerpt_expires_at < NOW()` (default: 30 days after job creation)
3. **Structurally isolated**: the `clause_excerpt` column is nulled, but the finding row (severity, status, confidence, reasoning) remains for the full 3-year audit retention period

After the review window closes, there is no contract text in the database — only structured assessments.

### Pinecone: Public Text Only

The vector store contains only public regulatory documents. The analysis pipeline has read-only access to Pinecone. No supplier contract content is ever embedded or ingested into the vector store. This is enforced by:

1. The ingestion endpoint (`POST /admin/knowledge/ingest`) being admin-only
2. The analysis nodes (`check_gdpr`) having no write access to Pinecone
3. The namespace allowlist in the admin endpoint preventing arbitrary namespace creation

### Event Log

Every significant system action is recorded to an append-only `event_log` table:

| Event Type | Trigger |
|---|---|
| `upload` | Document uploaded |
| `analysis_complete` | Pipeline completed, score assigned |
| `gate` | Gate decision recorded |
| `override` | Compliance officer or reviewer override |
| `pipeline_error` | Exception during analysis |
| `purge` | (Future) Triggered when a job's retention period expires |

Each event includes: `job_id`, `actor` (user ID or "system"), `event_type`, `detail` (JSONB), `created_at`.
