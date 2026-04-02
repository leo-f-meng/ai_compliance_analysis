# Scope

## MVP Scope (What Is Built Now)

### Regulatory Coverage
- **GDPR only**: Articles 4, 5, 6, 9, 24, 28, 32, 44–49
- ~40 specific requirements encoded in `data/requirements.yaml`
- Covers: controller-processor obligations, lawful basis, security measures, breach notification, transfer mechanisms, data subject rights, subprocessor management

### Document Types Supported
| Type | Description |
|---|---|
| DPA | Data Processing Agreement — primary GDPR instrument |
| MSA | Master Service Agreement — commercial contract with embedded data clauses |
| NDA | Non-Disclosure Agreement — checks personal data scope and duration |
| SOW | Statement of Work / Order — processing purposes and retention |
| POLICY | Supplier Privacy / Security Policy — adequacy against Art. 28 requirements |

### Output
- **Risk score**: Red / Amber / Green for the whole document
- **Findings list**: per-requirement assessment (Present / Absent / Unclear), severity, confidence, reasoning
- **Clause excerpt**: up to 500 chars of the triggering contract text, available for 30 days to reviewers

### Intake
- Manual file upload via `POST /jobs/upload`
- Accepted formats: PDF (text-based), DOCX
- Maximum file size: 20 MB

### Deployment
- Internal tool (single-tenant)
- Docker Compose: `api` container (FastAPI) + `db` container (PostgreSQL 16)
- Pinecone: cloud-hosted, no container needed
- Clean REST API from day one — ready for integration without UI changes

---

## Out of MVP Scope

These are explicitly excluded from the first release:

### Additional Regulations
- SOC 2 / ISO 27001
- CCPA / US state privacy laws
- HIPAA
- Internal policy checklists
- Sector-specific frameworks (PCI, DORA, FCA)

The system is architecturally ready for these (namespaced Pinecone index, configurable requirements), but the GDPR checklist and knowledge corpus must be validated before expanding.

### Additional Outputs
- **Executive summary**: plain-language paragraph for non-lawyers
- **Redline suggestions**: AI-generated alternative clause language (requires additional human-review gate before use — high liability risk)
- **Side-by-side comparison**: contract vs. ideal DPA template

### Alternative Intakes
- Email monitoring (attachment extraction from a monitored mailbox)
- Shared storage watch (S3, SharePoint, Google Drive folder polling)
- CLM / procurement system integration (Ironclad, Coupa, Jira Service Management)

### Authentication
- JWT / SSO / SAML — MVP uses header-based identity (`X-User-Id`, `X-User-Role`)
- Role management UI
- Multi-tenant user management

### UI
- No web frontend is in scope — API only
- Reviewers interact via the REST API or any HTTP client (curl, Postman, a future frontend)

---

## Scope Boundaries — What the System Will Not Do

- **Not provide legal advice.** The system flags potential issues; a lawyer determines compliance.
- **Not assert compliance.** The system never outputs "compliant", "legal", "valid", or "approved". Only: Present / Absent / Unclear / Needs Review.
- **Not replace the human gate.** Red contracts require a named human override. The system cannot auto-approve anything at Red.
- **Not store raw contract text.** Files are deleted after parsing; only structured findings are persisted.
- **Not guarantee exhaustive analysis.** Findings are probabilistic; confidence scores are always shown. Low-confidence findings are surfaced as Unclear, not suppressed.

---

## Thresholds (Configurable)

All scoring thresholds are environment-variable configurable, not hardcoded. Default values:

| Threshold | Default | Environment Variable |
|---|---|---|
| Confidence floor | 0.60 | `CONFIDENCE_FLOOR` |
| Critical findings → RED | ≥ 1 | `RED_THRESHOLD_CRITICAL` |
| High findings → RED | ≥ 2 | `RED_THRESHOLD_HIGH` |
| High findings → AMBER | ≥ 1 | `AMBER_THRESHOLD_HIGH` |
| Medium findings → AMBER | ≥ 3 | `AMBER_THRESHOLD_MEDIUM` |
| Unclear findings → AMBER | ≥ 5 | `AMBER_THRESHOLD_UNCLEAR` |
| Clause excerpt retention | 30 days | `EXCERPT_RETENTION_DAYS` |
| Job metadata retention | 3 years | `JOB_RETENTION_YEARS` |
