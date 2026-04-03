from app.models.domain import (
    AnalysisState, RagScore, GateAction, DocType
)
from app.pipeline.nodes.gate_decision import gate_decision


def test_red_score_gives_blocked():
    state = AnalysisState(job_id="test-001", doc_type=DocType.DPA, rag_score=RagScore.RED)
    result = gate_decision(state)
    assert result.gate_decision.action == GateAction.BLOCKED


def test_amber_score_gives_escalated():
    state = AnalysisState(job_id="test-002", doc_type=DocType.DPA, rag_score=RagScore.AMBER)
    result = gate_decision(state)
    assert result.gate_decision.action == GateAction.ESCALATED


def test_green_score_gives_cleared():
    state = AnalysisState(job_id="test-003", doc_type=DocType.DPA, rag_score=RagScore.GREEN)
    result = gate_decision(state)
    assert result.gate_decision.action == GateAction.CLEARED


def test_none_score_gives_failed():
    state = AnalysisState(job_id="test-004", doc_type=DocType.DPA, rag_score=None)
    result = gate_decision(state)
    assert result.gate_decision.action == GateAction.FAILED
