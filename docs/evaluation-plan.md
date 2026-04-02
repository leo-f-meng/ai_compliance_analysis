# Evaluation Plan

## Purpose

Before trusting the system in a hard-gate capacity, the compliance analysis pipeline must be evaluated against real or realistic documents to establish:

1. **Precision and recall** on known-good and known-bad documents
2. **Confidence calibration** — does a confidence of 0.90 actually mean the finding is correct 90% of the time?
3. **False negative rate** for Critical findings — the most dangerous failure mode
4. **Threshold tuning** — are the default Red/Amber/Green thresholds appropriate for the document corpus?
5. **LLM consistency** — does the same document always produce the same score?

The system should not be used as a hard gate until evaluation benchmarks are met.

---

## Test Dataset

### Document Types Needed

| Type | Count | Source |
|---|---|---|
| Fully compliant DPAs (Art. 28 complete) | 10 | Legal team — verified gold standard |
| DPAs with known Critical gaps | 10 | Synthetic: remove key clauses from compliant templates |
| DPAs with known High gaps | 10 | Synthetic: weaken specific clauses |
| MSAs with embedded data clauses | 5 | Real supplier MSAs (anonymised) |
| NDAs covering personal data | 5 | Real NDAs (anonymised) |
| Supplier Security Policies | 5 | Real policies (anonymised) |
| Edge cases: very short documents | 3 | 1–2 page summaries |
| Edge cases: very long documents (50+ pages) | 3 | Full commercial agreements |
| Documents in good faith but with vague language | 5 | Real-world ambiguous contracts |

**Total: ~56 documents minimum**

Ground truth labels must be established by a qualified legal reviewer before running evaluation.

### Ground Truth Format

For each document, a human reviewer records:

```yaml
document_id: doc-001
doc_type: DPA
reviewer: legal@example.com
review_date: 2026-04-15
expected_score: RED
expected_critical_absent:
  - ART28_DPA_EXECUTED
  - ART28_BREACH_NOTIFICATION
expected_high_absent:
  - ART28_BREACH_72H
notes: "Missing DPA execution clause entirely. Breach clause references 'reasonable time', not 72h."
```

---

## Metrics

### Primary Metrics (Critical)

**False Negative Rate on Critical Findings**
The most dangerous failure: the system marks a Critical requirement as Present when it is actually Absent.

```
FNR_critical = Critical findings incorrectly marked Present / Total Critical absent findings
```

Target: **FNR_critical ≤ 5%** before using as a hard gate.

**Red Score Precision**
Of all documents scored Red, what fraction actually had Critical or ≥2 High issues?

```
Red Precision = True Red / All Scored Red
```

Target: **≥ 90%**

**Green Score Recall**
Of all documents that are genuinely clean, what fraction score Green?

```
Green Recall = True Green / All Genuinely Clean
```

Target: **≥ 85%** (some false Ambers are acceptable; false Greens on critical docs are not)

### Secondary Metrics

**Finding-Level Precision/Recall** (per severity)

For each severity level (Critical, High, Medium, Low):
```
Precision = Correctly identified as absent / All flagged as absent
Recall    = Correctly identified as absent / All actually absent
```

**Confidence Calibration**
Group findings by confidence band and check accuracy:

| Confidence Band | Expected Accuracy | Actual Accuracy |
|---|---|---|
| 0.90–1.00 | ≥ 95% | TBD |
| 0.75–0.90 | ≥ 85% | TBD |
| 0.60–0.75 | ≥ 70% | TBD |
| < 0.60 | — (forced Unclear) | N/A |

**LLM Consistency (Determinism Check)**
Run each test document 3 times. Measure:
- Score consistency: same RAG score all 3 runs? Target: 100% (temperature=0)
- Finding status consistency: same status for each requirement? Target: ≥ 95%

---

## Evaluation Protocol

### Phase 1: Offline Benchmark (Before Hard-Gate Deployment)

1. Run all 56 test documents through the pipeline.
2. Compare findings against ground truth labels.
3. Calculate all primary and secondary metrics.
4. If FNR_critical > 5% or Red Precision < 90%: investigate, adjust prompts or thresholds, re-run.
5. Document results in `docs/evaluation-results/YYYY-MM-DD-benchmark.md`.

### Phase 2: Shadow Mode (Advisory Only, First 4 Weeks)

Deploy in production but set the gate to **advisory only** (log gate decisions but don't block). Compare system decisions against human reviewer decisions on the same documents.

Track:
- Cases where system says Red but human says Green (false positive — costly friction)
- Cases where system says Green but human says Red (false negative — dangerous)
- Override rate (what % of Red decisions are overridden by compliance officers)

High override rate → system is too aggressive (thresholds too low)  
Zero override rate → system may be too lenient (thresholds too high) or not being used critically

### Phase 3: Soft Gate (Weeks 5–8)

Enable AMBER as a soft gate (reviewer sign-off required) but keep RED advisory only. Build reviewer familiarity with findings before full hard-gate activation.

### Phase 4: Full Hard Gate

Enable RED as a hard gate only after:
- Phase 1 FNR_critical ≤ 5%
- Phase 2 false negative rate < 2% on real documents
- Compliance team has reviewed and approved the threshold configuration
- Override workflow is confirmed working end-to-end

---

## Known Failure Modes to Watch

### Clause Splitting Errors
The `extract_clauses` node may split a single obligation across two clauses, causing the checker to see incomplete text. Watch for: requirements marked Unclear that are actually Present in a neighbouring clause.

**Mitigation:** Allow the checker to receive overlapping context (adjacent clause text) if confidence is below 0.75.

### Implicit vs Explicit Requirements
Some contracts satisfy GDPR requirements implicitly (e.g. "GDPR-compliant practices" without specifying them). The system will mark these as Absent or Unclear. Ground truth labelling must decide how to handle implicit compliance.

**Recommendation:** Implicit is Unclear, not Present, unless the specific obligation is explicitly addressed.

### Document Type Misclassification
A DPA embedded in an MSA schedule may be classified as MSA, not DPA. This affects which requirements are considered most relevant.

**Mitigation:** The checklist checks all ~40 requirements regardless of document type. Misclassification affects UX and reporting, not coverage.

### Very Long Documents
Documents over 30 pages may hit GPT-4o context limits during clause extraction. The `extract_clauses` prompt must handle chunked input.

**Mitigation:** Split documents over a configurable page threshold before sending to `extract_clauses`. Track token usage in evaluation.

---

## Threshold Tuning

After Phase 2 (shadow mode), the following thresholds may need adjustment based on observed override rates and false negative rates:

```env
CONFIDENCE_FLOOR=0.60         # Raise if too many Unclear findings on clear-cut clauses
RED_THRESHOLD_CRITICAL=1      # Do not lower below 1
RED_THRESHOLD_HIGH=2          # Can raise to 3 if override rate on 2-High docs is high
AMBER_THRESHOLD_MEDIUM=3      # Lower to 2 if reviewers say Medium gaps are being missed
AMBER_THRESHOLD_UNCLEAR=5     # Lower if Unclear findings correlate with actual problems
```

All changes must be documented with the rationale and the evaluation evidence that motivated them.
