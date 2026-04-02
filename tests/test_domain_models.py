from app.models.domain import (
    Clause, Finding, FindingStatus, Severity, RagScore,
    GateDecision, GateAction, AnalysisState,
)


def test_finding_status_values():
    assert FindingStatus.PRESENT == "present"
    assert FindingStatus.ABSENT == "absent"
    assert FindingStatus.UNCLEAR == "unclear"


def test_finding_creation():
    f = Finding(
        requirement_id="ART28_BREACH_01",
        severity=Severity.CRITICAL,
        status=FindingStatus.ABSENT,
        confidence=0.95,
        reasoning="No breach notification clause found.",
        clause_excerpt="This agreement covers data processing.",
    )
    assert f.requirement_id == "ART28_BREACH_01"
    assert f.clause_excerpt == "This agreement covers data processing."


def test_clause_creation():
    c = Clause(
        text="The processor shall notify the controller within 72 hours.",
        clause_type="breach_notification",
        subject="breach notification",
        page=3,
    )
    assert c.page == 3


def test_gate_decision_creation():
    gd = GateDecision(action=GateAction.BLOCKED, rag_score=RagScore.RED)
    assert gd.action == GateAction.BLOCKED


def test_analysis_state_creation():
    state = AnalysisState(job_id="abc-123")
    assert state.job_id == "abc-123"
    assert state.clauses == []
    assert state.findings == []
    assert state.rag_score is None
    assert state.gate_decision is None
    assert state.error is None
