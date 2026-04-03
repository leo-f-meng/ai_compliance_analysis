from unittest.mock import MagicMock, patch
from app.models.domain import (
    AnalysisState, DocType, Clause, Finding,
    FindingStatus, Severity,
)
from app.pipeline.nodes.check_gdpr import check_gdpr


_CLAUSE = Clause(
    text="The Processor shall notify the Controller within 72 hours of a breach.",
    clause_type="breach_notification",
    subject="breach notification",
    page=2,
)


def _mock_agent_response(findings: list[Finding]):
    mock = MagicMock()
    mock.invoke.return_value = {"findings": findings}
    return mock


def test_check_gdpr_returns_findings():
    state = AnalysisState(
        job_id="test-001",
        raw_text="...",
        doc_type=DocType.DPA,
        clauses=[_CLAUSE],
    )
    expected_finding = Finding(
        requirement_id="ART28_BREACH_NOTIFICATION",
        severity=Severity.CRITICAL,
        status=FindingStatus.PRESENT,
        confidence=0.95,
        reasoning="72-hour notification explicitly stated.",
        clause_excerpt="notify the Controller within 72 hours",
    )
    mock_agent = _mock_agent_response([expected_finding])

    with patch("app.pipeline.nodes.check_gdpr._build_agent", return_value=mock_agent):
        result = check_gdpr(state)

    assert len(result.findings) > 0


def test_vocabulary_guard_called_on_reasoning():
    """Any forbidden vocabulary in reasoning must raise before findings are accepted."""
    state = AnalysisState(
        job_id="test-002",
        doc_type=DocType.DPA,
        clauses=[_CLAUSE],
    )
    bad_finding = Finding(
        requirement_id="ART28_BREACH_NOTIFICATION",
        severity=Severity.CRITICAL,
        status=FindingStatus.PRESENT,
        confidence=0.95,
        reasoning="This contract is legally compliant.",  # FORBIDDEN
        clause_excerpt="",
    )
    mock_agent = _mock_agent_response([bad_finding])

    with patch("app.pipeline.nodes.check_gdpr._build_agent", return_value=mock_agent):
        with patch("app.pipeline.nodes.check_gdpr.check_vocabulary") as mock_guard:
            from app.vocabulary_guard import VocabularyViolationError
            mock_guard.side_effect = VocabularyViolationError("compliant")
            result = check_gdpr(state)
            # Finding with vocabulary violation becomes Unclear
            assert all(f.status == FindingStatus.UNCLEAR for f in result.findings)


def test_low_confidence_findings_forced_to_unclear():
    state = AnalysisState(
        job_id="test-003",
        doc_type=DocType.DPA,
        clauses=[_CLAUSE],
    )
    low_conf_finding = Finding(
        requirement_id="ART28_BREACH_NOTIFICATION",
        severity=Severity.CRITICAL,
        status=FindingStatus.ABSENT,
        confidence=0.45,  # below floor
        reasoning="Could not determine.",
        clause_excerpt="",
    )
    mock_agent = _mock_agent_response([low_conf_finding])

    with patch("app.pipeline.nodes.check_gdpr._build_agent", return_value=mock_agent):
        result = check_gdpr(state)

    assert result.findings[0].status == FindingStatus.UNCLEAR
