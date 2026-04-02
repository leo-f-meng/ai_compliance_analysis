# RAG Data Strategy

## Overview

The system uses a two-layer approach to GDPR compliance checking:

- **Layer A — Static Checklist**: ~40 GDPR requirements in `data/requirements.yaml`. Deterministic coverage — every requirement is always checked, regardless of document content.
- **Layer B — RAG (Retrieval-Augmented Generation)**: A Pinecone vector knowledge base of public regulatory text. Used for grey-area clauses where the checklist alone cannot determine adequacy.

The two layers complement each other. The checklist ensures nothing is missed. RAG provides depth of reasoning for ambiguous cases.

---

## What Goes Into Pinecone

### Included (Public Regulatory Text Only)

| Source | Content | Namespace |
|---|---|---|
| GDPR full text | Articles 4, 5, 6, 9, 24, 28, 32, 44–49 with recitals | `gdpr` |
| EDPB Guidelines | Controller-processor relations (07/2020), International transfers (01/2020), BCRs (01/2022), Art. 6 lawful basis (01/2019) | `gdpr` |
| ICO Guidance | Data sharing code, Controller/processor guide, International transfers guide | `gdpr` |
| Art. 28 DPA Templates | Anonymised template clause examples (not from real contracts) | `gdpr` |

**Future namespaces (not in MVP):**

| Namespace | Planned Content |
|---|---|
| `soc2` | AICPA Trust Service Criteria, SOC 2 audit guidance |
| `ccpa` | California Consumer Privacy Act, CPRA amendments, AG regulations |
| `hipaa` | HIPAA Privacy Rule, Security Rule, Breach Notification Rule |
| `internal_policy` | Organisation's own procurement policy, standard contract playbook |

### Never Included

- Supplier contract content (any kind — text, clauses, excerpts)
- Customer or employee personal data
- Confidential commercial terms
- Any document uploaded by users

This is enforced architecturally: the ingestion endpoint (`POST /admin/knowledge/ingest`) is admin-only and requires a `namespace` from a predefined allowlist. The analysis pipeline never writes to Pinecone.

---

## How RAG Is Used During Analysis

The `check_gdpr` LangGraph node runs GPT-4o as a tool-calling agent with two tools:

### Tool 1: `ChecklistLookupTool`
- Queries `data/requirements.yaml` by requirement ID
- Returns: requirement description, GDPR article reference, severity
- Always called first for every requirement

### Tool 2: `PineconeRetrieverTool`
- Queries Pinecone `gdpr` namespace with a natural language query
- Returns top-3 semantically relevant regulatory passages with source labels
- Called when the agent needs regulatory context to assess an ambiguous clause

**Example reasoning flow:**

```
Requirement: ART28_SUBPROCESSORS_APPROVAL

Step 1: ChecklistLookupTool("ART28_SUBPROCESSORS_APPROVAL")
→ "Processor must obtain prior written authorisation before engaging subprocessors. Art. 28(2). Severity: critical."

Step 2: Read clause: "Acme Corp may engage subcontractors to assist with service delivery."

Step 3: Ambiguous — "subcontractors" may or may not mean subprocessors. Use RAG.

Step 4: PineconeRetrieverTool("subprocessor authorisation prior written consent")
→ [1] EDPB 07/2020 §4.2.4: "The processor must obtain specific or general written authorisation of the controller..."
→ [2] GDPR Art. 28(2): "The processor shall not engage another processor without prior specific or general written authorisation of the controller..."

Step 5: Assessment — clause says "may engage subcontractors" without authorisation requirement.
→ status: absent, severity: critical, confidence: 0.88,
   reasoning: "Clause permits subcontracting without controller authorisation. Art. 28(2) requires prior written consent."
```

---

## Embedding Configuration

| Setting | Value |
|---|---|
| Model | `text-embedding-3-small` (OpenAI) |
| Dimensions | 1536 |
| Chunk size | 500 tokens |
| Chunk overlap | 50 tokens |
| Splitter | `RecursiveCharacterTextSplitter` |
| Retrieval | `similarity_search`, top-k=3 |

The 500-token chunk size is calibrated to GDPR article paragraphs — most individual obligation statements fit within one chunk, preserving semantic coherence.

---

## Knowledge Base Maintenance

### Initial Ingestion
Run once via `POST /admin/knowledge/ingest` (compliance_officer role required):

```json
{
  "texts": ["Article 28 full text...", "EDPB Guidelines 07/2020..."],
  "sources": ["GDPR Art. 28", "EDPB-07/2020"],
  "namespace": "gdpr"
}
```

### Updates
When EDPB publishes new guidelines or GDPR interpretation evolves:
1. Ingest the new document via the admin endpoint
2. No pipeline code changes required
3. The agent automatically retrieves the new content during analysis

### What Does Not Require a Re-Ingest
- Changes to GDPR requirements checklist (`requirements.yaml`) — this is read at runtime
- Changes to scoring thresholds — these are environment variables
- Pipeline logic changes — these are code changes, not knowledge changes

---

## Data Isolation Guarantee

The analysis pipeline has two distinct data paths:

```
Supplier document → [parse → extract → check] → findings (PostgreSQL)
                                    ↑
                              Pinecone read-only
                              (regulatory text only)
```

The `PineconeRetrieverTool` performs **read-only** similarity search. The analysis pipeline has no write access to Pinecone. Supplier contract text is never sent to Pinecone in any form — it is only sent to the OpenAI API for LLM analysis (via the existing OpenAI data processing agreement).

---

## Why Not RAG Alone?

A pure RAG approach — embed the GDPR corpus and retrieve relevant passages for every clause — was considered and rejected for MVP for three reasons:

1. **Retrieval is not exhaustive.** A retrieval step might miss a requirement if the query doesn't match the chunk well. The checklist ensures every one of the ~40 requirements is always evaluated.

2. **Hard-gate requires determinism.** The gate decision must be fully traceable. "The model retrieved these passages and concluded X" is less auditable than "Requirement ART28_DPA_EXECUTED: Absent, confidence 0.92."

3. **GDPR is a fixed, known body of law.** The requirements don't change without legislative process. A static checklist is more reliable than retrieval for known, fixed obligations.

RAG adds value at the *depth* layer — reasoning about whether a clause *adequately* satisfies a requirement — not at the *coverage* layer, which the checklist owns.
