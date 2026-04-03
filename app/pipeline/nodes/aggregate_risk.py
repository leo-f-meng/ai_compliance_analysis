from app.models.domain import AnalysisState
from app.scoring import calculate_rag_score
from app.config import settings


def aggregate_risk(state: AnalysisState) -> AnalysisState:
    rag_score = calculate_rag_score(state.findings, settings)
    return state.model_copy(update={"rag_score": rag_score})
