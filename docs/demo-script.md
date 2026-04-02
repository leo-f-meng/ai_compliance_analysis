# Demo Script

A structured walkthrough for demonstrating the Compliance Analysis Agent to stakeholders. Estimated duration: 20–25 minutes.

**Prerequisites:**
- `docker compose up -d` running
- `alembic upgrade head` applied
- Pinecone `gdpr` namespace seeded with GDPR corpus
- Three sample documents prepared (see below)
- A REST client ready (curl, Postman, or a simple web UI wrapper)

---

## Sample Documents Needed

Prepare these three documents before the demo:

| File | Description |
|---|---|
| `demo/dpa-clean.pdf` | A well-drafted DPA with all Art. 28 requirements satisfied. Should score GREEN. |
| `demo/dpa-missing-breach.pdf` | Same DPA but with the breach notification clause removed. Should score RED. |
| `demo/msa-vague.pdf` | An MSA with data clauses present but vague (retention period undefined, security "as appropriate"). Should score AMBER. |

If you don't have real documents, the `tests/fixtures/` directory contains minimal synthetic PDFs usable for demonstration.

---

## Demo Flow

### Scene 1: The Problem (2 minutes)

**Say:** "Our procurement team receives supplier contracts that involve personal data processing. Today, reviewing a DPA manually takes 30–90 minutes of legal time per document, and we have no consistent checklist. Gaps are caught inconsistently, and there's no audit trail of review decisions.

This tool changes that. Let me show you."

---

### Scene 2: Upload a Clean DPA (5 minutes)

**Action:** Upload `demo/dpa-clean.pdf`

```bash
curl -X POST http://localhost:8000/jobs/upload \
  -H "x-user-id: procurement@example.com" \
  -F "file=@demo/dpa-clean.pdf"
```

**Response:**
```json
{"job_id": "aaa-111-...", "status": "processing"}
```

**Say:** "The document is being processed. Let me poll for the result."

```bash
curl http://localhost:8000/jobs/aaa-111-... \
  -H "x-user-id: procurement@example.com"
```

**Expected response:**
```json
{
  "job_id": "aaa-111-...",
  "status": "complete",
  "doc_type": "DPA",
  "rag_score": "GREEN",
  "gate_decision": "CLEARED"
}
```

**Say:** "Green — cleared. The pipeline checked all 40 GDPR requirements and found no significant gaps. Let's look at the detail."

```bash
curl http://localhost:8000/jobs/aaa-111-.../findings \
  -H "x-user-id: procurement@example.com"
```

**Point out:**
- Most findings are `present` with high confidence
- Any `low` severity absences are best practice gaps, not legal requirements
- The `has_excerpt: true` flag means reviewers can see the triggering clause text

---

### Scene 3: Upload a Red Contract (5 minutes)

**Action:** Upload `demo/dpa-missing-breach.pdf`

```bash
curl -X POST http://localhost:8000/jobs/upload \
  -H "x-user-id: procurement@example.com" \
  -F "file=@demo/dpa-missing-breach.pdf"
```

**Poll for result:**
```bash
curl http://localhost:8000/jobs/bbb-222-... \
  -H "x-user-id: procurement@example.com"
```

**Expected response:**
```json
{
  "rag_score": "RED",
  "gate_decision": "BLOCKED"
}
```

**Say:** "Red — blocked. This contract cannot move forward without a compliance officer override. Let's see what was found."

```bash
curl http://localhost:8000/jobs/bbb-222-.../findings \
  -H "x-user-id: procurement@example.com"
```

**Point out:**
- `ART28_BREACH_NOTIFICATION` → `absent`, `severity: critical`
- Reasoning: "No breach notification clause found in document."
- No legal jargon — just: present, absent, unclear

**Say:** "Notice: the system doesn't say 'non-compliant'. It says 'absent'. Whether that makes the contract non-compliant with GDPR is a legal determination — that's the reviewer's job. The system surfaces the gap."

---

### Scene 4: Upload an Amber Contract (3 minutes)

**Action:** Upload `demo/msa-vague.pdf`

**Expected result:**
```json
{
  "rag_score": "AMBER",
  "gate_decision": "ESCALATED"
}
```

**Say:** "Amber — escalated. The contract has data protection clauses, but they're vague. A reviewer needs to sign off before it can proceed. This is the common real-world case — suppliers who've tried to address GDPR but haven't been specific enough."

**Point out:**
- `ART28_RETENTION_PERIOD` → `unclear`, confidence 0.62 (just above the confidence floor)
- `ART32_SECURITY_MEASURES` → `medium` severity, `absent` — referenced but not specified
- This triggers AMBER (≥ 3 Medium findings)

---

### Scene 5: The Override Workflow (5 minutes)

**Say:** "Now let's say we need to proceed with the Red contract urgently — the DPA is being finalised separately. A compliance officer can override."

**Action:** Attempt override as the uploader (expect failure):

```bash
curl -X POST http://localhost:8000/jobs/bbb-222-.../override \
  -H "x-user-id: procurement@example.com" \
  -H "x-user-role: compliance_officer" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "We need this signed urgently.",
    "mitigating_controls": ["legal_team_reviewed"]
  }'
```

**Expected:** `403 Forbidden — "The document uploader cannot override their own document."`

**Say:** "Separation of duties: the person who uploaded the contract can't also approve it. Let's have the compliance officer do it."

**Action:** Override as a different compliance officer, with proper reason:

```bash
curl -X POST http://localhost:8000/jobs/bbb-222-.../override \
  -H "x-user-id: officer@example.com" \
  -H "x-user-role: compliance_officer" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Breach notification clause is being added via DPA amendment currently under legal review. Processing will not commence until the DPA amendment is countersigned. Exception approved for contract signature only.",
    "mitigating_controls": ["existing_dpa_under_negotiation", "legal_team_reviewed"]
  }'
```

**Expected:** `200 OK — {"status": "overridden", ...}`

**Say:** "The override is logged permanently — who approved it, when, why, what the findings were at the time. This is the audit trail your DPO needs."

---

### Scene 6: Idempotency (1 minute)

**Say:** "One more thing. If the same document is uploaded twice — say, by accident — the system detects the duplicate and returns the existing result."

```bash
curl -X POST http://localhost:8000/jobs/upload \
  -H "x-user-id: procurement@example.com" \
  -F "file=@demo/dpa-clean.pdf"
```

**Expected:**
```json
{"job_id": "aaa-111-...", "status": "complete", "existing": true}
```

**Say:** "No double processing, no duplicate findings, no wasted API calls."

---

### Scene 7: Architecture Summary (3 minutes)

**Say:** "Let me briefly explain how this works under the hood, because the architecture is where the trustworthiness comes from."

Walk through the pipeline diagram (show [docs/project-overview.md](project-overview.md) or [docs/rule-engine-vs-vector-db.md](rule-engine-vs-vector-db.md)):

1. **Parse** — PDF/DOCX text extraction, file validation
2. **Extract** — GPT-4o splits the document into logical clauses
3. **Check** — For each of 40 GDPR requirements, GPT-4o checks each clause. Grey-area clauses trigger a Pinecone lookup for regulatory guidance
4. **Score** — Pure Python applies deterministic rules to the structured findings. No LLM in the gate decision.
5. **Gate** — Red/Amber/Green. Blocked contracts require human override with full audit trail.

**Key point to emphasise:** "The LLM classifies clauses. Python decides the gate. The gate cannot be gamed by a clever prompt."

---

## Anticipated Questions

**Q: What if the LLM gets it wrong?**
The confidence score surfaces uncertainty. Findings below 60% confidence become "Unclear" — they can escalate to Amber but cannot trigger a Red block. All Red decisions require a Critical finding with ≥60% confidence, or multiple High findings. Even then, a compliance officer can always override with a documented reason.

**Q: Does the system store our contracts?**
No. The original file is deleted after text extraction. Only structured findings (Present/Absent/Unclear per requirement) are stored. Clause excerpts — short snippets of text — are stored encrypted for 30 days for reviewer context, then automatically deleted.

**Q: Can we add other regulations like SOC 2 or CCPA?**
Yes. The architecture uses namespaced Pinecone indices and a configurable requirements checklist. Adding a new regulation is a data operation (ingest the corpus, add requirements) not a code change.

**Q: How fast is the analysis?**
Depends on document length and complexity. For a typical 10-page DPA: approximately 60–90 seconds. The API is async — upload returns immediately with a job ID that you poll.

**Q: What about scanned PDFs?**
Rejected at upload with an actionable error message. The system requires text-extractable PDFs. Workaround: run the document through an OCR tool first.
