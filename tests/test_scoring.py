from app.models.domain import Finding, FindingStatus, Severity, RagScore
from app.scoring import calculate_rag_score, apply_confidence_floor
from app.config import Settings

_SETTINGS = Settings(
    openai_api_key="x", pinecone_api_key="x",
    pinecone_index_name="x", database_url="sqlite:///x",
)


def _finding(severity, status=FindingStatus.ABSENT, confidence=0.95):
    return Finding(
        requirement_id="TEST_01", severity=severity, status=status,
        confidence=confidence, reasoning="test", clause_excerpt="",
    )


def test_any_critical_is_red():
    findings = [_finding(Severity.CRITICAL, FindingStatus.ABSENT)]
    assert calculate_rag_score(findings, _SETTINGS) == RagScore.RED


def test_two_high_is_red():
    findings = [
        _finding(Severity.HIGH, FindingStatus.ABSENT),
        _finding(Severity.HIGH, FindingStatus.ABSENT),
    ]
    assert calculate_rag_score(findings, _SETTINGS) == RagScore.RED


def test_one_high_is_amber():
    findings = [_finding(Severity.HIGH, FindingStatus.ABSENT)]
    assert calculate_rag_score(findings, _SETTINGS) == RagScore.AMBER


def test_three_medium_is_amber():
    findings = [_finding(Severity.MEDIUM, FindingStatus.ABSENT)] * 3
    assert calculate_rag_score(findings, _SETTINGS) == RagScore.AMBER


def test_five_unclear_is_amber():
    findings = [_finding(Severity.MEDIUM, FindingStatus.UNCLEAR)] * 5
    assert calculate_rag_score(findings, _SETTINGS) == RagScore.AMBER


def test_green_clean():
    findings = [_finding(Severity.LOW, FindingStatus.ABSENT)]
    assert calculate_rag_score(findings, _SETTINGS) == RagScore.GREEN


def test_present_findings_dont_count():
    findings = [_finding(Severity.CRITICAL, FindingStatus.PRESENT)]
    assert calculate_rag_score(findings, _SETTINGS) == RagScore.GREEN


def test_confidence_floor_forces_unclear():
    f = _finding(Severity.CRITICAL, FindingStatus.ABSENT, confidence=0.55)
    result = apply_confidence_floor([f], confidence_floor=0.60)
    assert result[0].status == FindingStatus.UNCLEAR


def test_low_confidence_critical_cannot_trigger_red():
    f = _finding(Severity.CRITICAL, FindingStatus.ABSENT, confidence=0.55)
    floored = apply_confidence_floor([f], confidence_floor=0.60)
    assert calculate_rag_score(floored, _SETTINGS) == RagScore.AMBER


def test_parse_failure_forces_unclear():
    """A finding with None status (parse failure) becomes Unclear."""
    f = Finding(
        requirement_id="ART28_DPA_EXECUTED", severity=Severity.CRITICAL,
        status=FindingStatus.UNCLEAR, confidence=0.0,
        reasoning="parse failure", clause_excerpt="",
    )
    assert calculate_rag_score([f], _SETTINGS) == RagScore.AMBER
