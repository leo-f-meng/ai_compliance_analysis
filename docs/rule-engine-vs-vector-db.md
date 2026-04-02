# Rule Engine vs Vector DB — Design Decision

## The Core Question

How should the system know what GDPR requires, and how should it decide whether a contract clause satisfies a requirement?

This document explains why the system uses a **hybrid architecture** — a static rule engine for coverage and a vector database for depth — and why neither alone is sufficient.

---

## Option A: Pure Rule Engine (Static Checklist Only)

A `requirements.yaml` file defines ~40 GDPR requirements. For each requirement, the LLM is given the requirement text and the contract clause and asked: "Is this requirement Present, Absent, or Unclear?"

**Strengths:**
- Every requirement is always checked — no retrieval gaps
- Deterministic: the same input always triggers the same check
- Auditable: every finding maps to a numbered requirement
- Fast: no embedding lookup, no retrieval latency
- Safe for hard-gate use: the gate is a pure Python function over structured findings

**Weaknesses:**
- The LLM must reason about grey areas using only the requirement definition — no regulatory context
- Cannot handle nuance: "is 'subcontractors' the same as 'subprocessors'?"
- Prompt must be updated manually when regulatory interpretation evolves
- Cannot reason about EDPB opinions or ICO enforcement positions

**Verdict:** Sufficient for obvious gaps (missing clauses). Insufficient for ambiguous adequacy assessments.

---

## Option B: Pure Vector DB / RAG

Embed the full GDPR corpus, EDPB guidelines, and template DPAs into Pinecone. For each clause, retrieve the most relevant regulatory passages and ask the LLM to assess compliance.

**Strengths:**
- Rich regulatory context for every assessment
- Self-updating: add a new EDPB opinion by ingesting it, no prompt changes
- Better at grey-area reasoning
- Scales to new regulations without changing the pipeline

**Weaknesses:**
- **Retrieval is not exhaustive.** If the query doesn't match a chunk, the requirement is silently skipped. There is no guarantee that "ART28_SUBPROCESSORS_APPROVAL" is checked for every document.
- **Hard to audit.** "The system retrieved these 3 passages and concluded X" is harder to trace than a numbered checklist.
- **Retrieval quality is unpredictable.** For a hard-gate system, retrieval failures are gate failures.
- **Over-engineered for known requirements.** GDPR Article 28 is a 400-word article. We do not need vector search to "find" what it says — we know exactly what it says.

**Verdict:** Good at depth. Dangerous as the sole coverage mechanism for a hard-gate system.

---

## Option C: Hybrid (Chosen Architecture)

**Layer A — Static Checklist (coverage):** Every requirement in `requirements.yaml` is always evaluated for every document. Coverage is deterministic.

**Layer B — RAG (depth):** For grey-area clauses, the LangChain agent calls `PineconeRetrieverTool` to retrieve relevant regulatory guidance before making its assessment.

```
For each requirement in checklist:
    1. Look up requirement definition (ChecklistLookupTool) → always runs
    2. Assess clause against requirement
    3. If ambiguous → retrieve regulatory guidance (PineconeRetrieverTool) → conditional
    4. Return structured finding: status, severity, confidence, reasoning
```

**Why this works:**

| Concern | How Addressed |
|---|---|
| "Will every requirement be checked?" | Yes — the checklist loop is deterministic |
| "Is the gate decision auditable?" | Yes — gate = Python function over requirement findings |
| "Can it handle ambiguous clauses?" | Yes — RAG provides regulatory context on demand |
| "What if retrieval fails?" | Findings fall back to Unclear (confidence floor) — never to Absent |
| "Can we add new regulations?" | Yes — new Pinecone namespace + new requirements section |

---

## Where the LLM vs Python Boundary Falls

This is the most consequential design decision in the system:

```
┌─────────────────────────────────────────────────────────┐
│  LLM (GPT-4o)                                           │
│  check_gdpr node                                        │
│                                                         │
│  Input:  clause text + requirement definition + RAG     │
│  Output: {status, confidence, reasoning, excerpt}       │
│                                                         │
│  Job: natural language understanding + legal reasoning  │
└────────────────────────┬────────────────────────────────┘
                         │ structured Finding objects
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Pure Python                                            │
│  aggregate_risk + gate_decision nodes                   │
│                                                         │
│  Input:  list[Finding] with status, severity, conf      │
│  Output: RagScore (RED | AMBER | GREEN) + GateAction    │
│                                                         │
│  Job: deterministic scoring rules from config           │
└─────────────────────────────────────────────────────────┘
```

**The LLM never decides the gate.** It produces evidence. Python applies rules to that evidence. This boundary is critical for:

- **Testability**: the scoring function has 100% unit test coverage with no mocking
- **Auditability**: the gate decision is a pure function — given the same findings, always the same score
- **Trustworthiness**: you can inspect and tune the scoring rules without touching the LLM
- **Safety**: a model failure produces an Unclear finding, which can escalate to Amber, but cannot produce a false Green

---

## Scoring Rules (Python, Not LLM)

```python
def calculate_rag_score(findings, settings) -> RagScore:
    absent_critical = count(f for f where severity=CRITICAL and status=ABSENT)
    absent_high     = count(f for f where severity=HIGH and status=ABSENT)
    absent_medium   = count(f for f where severity=MEDIUM and status=ABSENT)
    unclear_count   = count(f for f where status=UNCLEAR)

    if absent_critical >= 1:    return RED
    if absent_high >= 2:        return RED
    if absent_high >= 1:        return AMBER
    if absent_medium >= 3:      return AMBER
    if unclear_count >= 5:      return AMBER
    return GREEN
```

All thresholds are configurable. No LLM is consulted. No probabilistic element. The same findings always produce the same score.

---

## Summary

| Capability | Checklist | RAG | Hybrid |
|---|---|---|---|
| Exhaustive coverage | ✅ | ❌ | ✅ |
| Handles ambiguity | ❌ | ✅ | ✅ |
| Auditable gate | ✅ | ❌ | ✅ |
| Updatable without code change | ❌ | ✅ | ✅ (both layers) |
| Safe for hard-gate use | ✅ | ❌ | ✅ |
| Scales to new regulations | ❌ | ✅ | ✅ |

The hybrid is strictly better than either alone for this use case.
