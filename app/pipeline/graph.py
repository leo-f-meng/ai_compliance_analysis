from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.models.domain import AnalysisState, GateAction
from app.pipeline.nodes.parse_document import parse_document
from app.pipeline.nodes.extract_clauses import extract_clauses
from app.pipeline.nodes.check_gdpr import check_gdpr
from app.pipeline.nodes.aggregate_risk import aggregate_risk
from app.pipeline.nodes.gate_decision import gate_decision


def _route_gate(state: AnalysisState) -> str:
    """Conditional edge: all gate outcomes currently end the graph.
    Extend here to add post-gate notification nodes."""
    if state.error:
        return "end"
    return "end"


def build_graph(checkpointer=None):
    builder = StateGraph(AnalysisState)

    # Nodes — parse_document takes extra args; wrap it for graph compatibility
    builder.add_node("extract_clauses", extract_clauses)
    builder.add_node("check_gdpr", check_gdpr)
    builder.add_node("aggregate_risk", aggregate_risk)
    builder.add_node("gate_decision", gate_decision)

    # Edges
    builder.set_entry_point("extract_clauses")
    builder.add_edge("extract_clauses", "check_gdpr")
    builder.add_edge("check_gdpr", "aggregate_risk")
    builder.add_edge("aggregate_risk", "gate_decision")
    builder.add_conditional_edges("gate_decision", _route_gate, {"end": END})

    cp = checkpointer or MemorySaver()
    return builder.compile(checkpointer=cp)


# Singleton for use in API — parse_document runs outside graph (pre-upload validation)
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
