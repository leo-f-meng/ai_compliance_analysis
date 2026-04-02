# Project Overview

## Problem

Organisations that onboard suppliers and service providers must ensure every contract involving personal data processing complies with GDPR before signing. This is typically done by a legal or compliance team reviewing contracts manually — a slow, error-prone process that creates a bottleneck in procurement, especially when the volume of suppliers is high or turnaround times are tight.

Key pain points:
- Manual review is inconsistent across reviewers
- Legal teams are expensive and scarce
- Requirements like "subprocessor approval" or "72-hour breach notification" are easy to miss in long contracts
- No structured audit trail for decisions made
- Nothing prevents a non-compliant contract from proceeding if review is skipped or deferred

## Solution

The Compliance Analysis Agent is an AI-powered pre-review tool that:

1. Accepts a supplier contract (PDF or DOCX) via upload
2. Extracts and analyses individual clauses using GPT-4o
3. Checks each clause against a structured GDPR Article 28/32 requirements checklist
4. Supplements analysis with a Pinecone vector knowledge base of GDPR articles, EDPB guidelines, and ICO guidance for grey-area clauses
5. Calculates a Red / Amber / Green risk score using deterministic Python rules
6. Hard-gates Red-scored documents — they cannot proceed without a named compliance officer override, logged with full reasoning

The system does not replace legal review. It acts as a first-pass filter that catches obvious gaps, flags ambiguities, and escalates to humans with structured evidence.

## Design Philosophy

**The LLM detects. Python decides.**
LLM calls classify each clause as Present / Absent / Unclear for each requirement. A pure Python scoring function converts those structured findings into a RAG score. No LLM is involved in the gate decision — that keeps it deterministic, auditable, and testable.

**Fail closed, not open.**
Any pipeline error, timeout, or low-confidence finding defaults to escalation (Amber), never to auto-clearance. The system cannot accidentally approve a contract due to a model failure.

**The system never says "compliant".**
Compliance is a legal determination made by humans. The system outputs: Present / Absent / Unclear / Needs Review. A vocabulary guard enforces this on every LLM output.

**Supplier data never enters the vector store.**
Pinecone contains only public regulatory text (GDPR articles, EDPB guidelines, ICO guidance). No contract content is ever embedded or stored there.

## Audience

| Role | How they interact |
|---|---|
| Procurement Manager | Uploads contracts, views RAG score, sees what to fix |
| Legal / Compliance Reviewer | Reviews Amber findings, signs off or escalates |
| Compliance Officer | Overrides Red-scored documents with documented reason |
| System Administrator | Manages the knowledge base, runs maintenance tasks |

## MVP Scope

- Regulatory framework: **GDPR only** (Articles 28, 32, transfer mechanisms)
- Document types: DPA, MSA, NDA, SOW, Supplier Privacy/Security Policies
- Output: Risk score (Red / Amber / Green) + per-requirement findings
- Intake: Manual file upload via REST API
- Deployment: Internal tool, single-tenant, Docker Compose

## Future Extensions

Once the MVP is validated, the architecture is designed to expand without pipeline changes:
- Additional regulations: SOC 2, CCPA, HIPAA — each as a new Pinecone namespace
- Additional document intakes: email, shared storage watch, CLM system API
- Richer outputs: executive summary, clause-level redline suggestions
- Multi-tenancy: per-client configuration and data isolation
- SSO / SAML authentication
