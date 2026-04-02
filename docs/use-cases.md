# Use Cases

## UC-01: New Supplier Onboarding — DPA Review

**Actor:** Procurement Manager  
**Trigger:** A new SaaS vendor is being onboarded and has submitted a DPA for signature.

**Flow:**
1. Procurement manager uploads the DPA via `POST /jobs/upload` with their user ID.
2. The system parses the document, extracts clauses, and runs GDPR checks.
3. Result: 🟡 AMBER — 1 High finding (subprocessor list exists but no approval mechanism).
4. System escalates: a compliance reviewer is notified (via external process; notification is out of scope).
5. Reviewer inspects the finding, sees the clause excerpt: *"The Processor may engage subprocessors at its discretion."*
6. Reviewer requires the supplier to add a written approval clause before the DPA is signed.
7. Supplier submits a revised DPA. Procurement re-uploads.
8. Result: 🟢 GREEN — cleared and logged to audit trail.

**Value delivered:** Caught a High finding before signature. No legal involvement required.

---

## UC-02: MSA with Embedded Data Clauses — Pre-Signature Review

**Actor:** Compliance Officer  
**Trigger:** Legal team has received a 60-page Master Service Agreement from a cloud infrastructure provider. Data clauses are buried in Schedule 4.

**Flow:**
1. Compliance officer uploads the MSA.
2. Clause extractor identifies 8 data-relevant clauses across Sections 4, 11, and Schedule 4.
3. GDPR checker finds: no lawful basis stated (Critical), breach notification clause present but window is 10 business days (High — exceeds 72 hours).
4. Result: 🔴 RED — 1 Critical + 1 High finding.
5. Contract is hard-blocked. System records gate decision and findings snapshot.
6. Compliance officer reviews findings, negotiates with supplier on the two points.
7. Supplier provides an amended agreement. Re-uploaded.
8. Amended agreement scores AMBER (one medium finding remains — retention period vague).
9. Compliance officer overrides AMBER (as compliance_officer role allows), records reason: *"Retention period governed by the supplier's data deletion policy, provided separately and reviewed by legal on 2026-04-02. Mitigating control: deletion certification required annually."*
10. Override logged immutably. Contract proceeds.

**Value delivered:** Critical missing lawful basis caught pre-signature. Override decision fully documented.

---

## UC-03: High-Volume NDA Review

**Actor:** Procurement Team (automated batch)  
**Trigger:** 20 NDAs submitted by workshop attendees need data-protection spot-checks before signing.

**Flow:**
1. Each NDA uploaded by the procurement coordinator.
2. NDAs are short documents — pipeline completes in ~30–60 seconds each.
3. 17 score GREEN (no significant data protection concerns beyond best-practice gaps).
4. 2 score AMBER (data categories not enumerated, retention period vague).
5. 1 scores RED (no breach notification clause at all — the NDA covers employee data).
6. RED document is blocked. A reviewer is assigned.
7. AMBER documents are reviewed and signed off by a reviewer.
8. Coordinator sees final status via `GET /jobs` for all 20 job IDs.

**Value delivered:** Batch review at scale. Human attention focused only on the 3 documents that need it.

---

## UC-04: Supplier Security Policy Adequacy Check

**Actor:** Compliance Reviewer  
**Trigger:** A supplier has submitted their standalone Information Security Policy instead of a DPA. The procurement team needs to know if it meets Art. 28 adequacy standards.

**Flow:**
1. Policy document uploaded; system classifies it as `POLICY` type.
2. Checker applies a subset of requirements relevant to security policies (Art. 32 security measures, incident response, access controls).
3. Result: AMBER — security measures referenced but not specified (Medium), no encryption-at-rest requirement stated (High).
4. Reviewer sees findings with clause excerpts. The excerpt for the High finding shows: *"The supplier shall implement appropriate security measures as per industry standards."*
5. Reviewer requests the supplier provide a more specific technical security specification.

**Value delivered:** Structured gap analysis replaces a manual read-through of a dense policy document.

---

## UC-05: Re-Review After Supplier Amendment

**Actor:** Procurement Manager  
**Trigger:** A supplier has amended their DPA in response to a previous RED finding.

**Flow:**
1. Manager uploads the amended DPA.
2. System detects a matching SHA-256 hash — wait, this is a new document (different content), so it is processed as a new job.
3. The original job (RED) remains in the audit trail with its original findings snapshot.
4. New job scores GREEN.
5. Audit trail shows two jobs for the same supplier: the original RED and the new GREEN. The remediation history is clear.

**Value delivered:** Audit-ready history of the supplier's compliance journey without any manual record-keeping.

---

## UC-06: Compliance Officer Override with Full Accountability

**Actor:** Compliance Officer  
**Trigger:** A critical supplier's contract scores RED, but the organisation needs to proceed urgently while a DPA amendment is negotiated.

**Flow:**
1. Contract scores RED (Critical: no lawful basis explicitly stated in the MSA — it references a separate DPA that is being finalised).
2. Contract is hard-blocked.
3. Compliance officer reviews the finding. The separate DPA is under negotiation and expected in 5 days.
4. Compliance officer calls `POST /jobs/{job_id}/override` with:
   - `reason`: *"Lawful basis is defined in the parallel DPA currently under negotiation (ref: legal/2026-04-DPA-AcmeCorp). Processing will not commence until the DPA is executed. Temporary exception approved for contract signature only."* (93 characters — passes the 50-char minimum)
   - `mitigating_controls`: `["existing_dpa_under_negotiation", "legal_team_reviewed"]`
5. Self-override check passes (different user from uploader).
6. Override logged: reviewer_id, timestamp, reason, original_score (RED), findings snapshot at time of override.
7. Contract status changes to `overridden`. Gate decision changes to `CLEARED`.

**Value delivered:** Emergency overrides are possible but fully documented. No way to approve without a named officer, a reason, and a permanent audit record.

---

## UC-07: Knowledge Base Expansion (Future)

**Actor:** System Administrator / Compliance Officer  
**Trigger:** The team wants to add SOC 2 Type II controls checking to the pipeline.

**Flow:**
1. Admin calls `POST /admin/knowledge/ingest` with SOC 2 Trust Service Criteria text, namespace `soc2`.
2. Corpus is chunked and embedded into Pinecone under the `soc2` namespace.
3. A new `requirements.yaml` section (or separate file) is added with SOC 2 requirement IDs.
4. The `check_gdpr` node is renamed/extended to `check_compliance`, which accepts a `namespace` parameter.
5. No pipeline changes required — the same graph handles the new regulation.

**Value delivered:** Adding a new regulatory framework is a data + config operation, not a code operation.
