from app.models.domain import (
    AnalysisState, Finding, FindingStatus, Severity, RagScore, DocType
)
from app.pipeline.nodes.aggregate_risk import aggregate_risk


def _finding(severity, status=FindingStatus.ABSENT):
    return Finding(
        requirement_id="TEST_01", severity=severity, status=status,
        confidence=0.95, reasoning="test", clause_excerpt="",
    )


def test_aggregate_risk_sets_rag_score():
    state = AnalysisState(
        job_id="test-001",
        doc_type=DocType.DPA,
        findings=[_finding(Severity.CRITICAL)],
    )
    result = aggregate_risk(state)
    assert result.rag_score == RagScore.RED


def test_aggregate_risk_green():
    state = AnalysisState(
        job_id="test-002",
        doc_type=DocType.DPA,
        findings=[_finding(Severity.LOW)],
    )
    result = aggregate_risk(state)
    assert result.rag_score == RagScore.GREEN
