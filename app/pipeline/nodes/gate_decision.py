from app.models.domain import AnalysisState, GateDecision, GateAction, RagScore


def gate_decision(state: AnalysisState) -> AnalysisState:
    score = state.rag_score
    if score == RagScore.RED:
        action = GateAction.BLOCKED
    elif score == RagScore.AMBER:
        action = GateAction.ESCALATED
    elif score == RagScore.GREEN:
        action = GateAction.CLEARED
    else:
        action = GateAction.FAILED  # pipeline error, fail closed

    decision = GateDecision(action=action, rag_score=score or RagScore.RED)
    return state.model_copy(update={"gate_decision": decision})
