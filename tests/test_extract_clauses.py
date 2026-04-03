from unittest.mock import MagicMock, patch
from app.models.domain import AnalysisState, DocType, Clause
from app.pipeline.nodes.extract_clauses import extract_clauses


_SAMPLE_TEXT = """
3.1 Data Processing.
The Processor shall process personal data only on written instructions from the Controller.

3.2 Breach Notification.
The Processor shall notify the Controller without undue delay, and in any case within 72 hours,
after becoming aware of a personal data breach.

3.3 Subprocessors.
The Processor shall not engage subprocessors without prior written authorisation from the Controller.
"""


def _make_mock_llm(clauses: list[dict]):
    mock = MagicMock()
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = MagicMock(clauses=[
        Clause(**c) for c in clauses
    ])
    mock.with_structured_output.return_value = mock_structured
    return mock


def test_extract_clauses_returns_clauses():
    state = AnalysisState(job_id="test-001", raw_text=_SAMPLE_TEXT, doc_type=DocType.DPA)
    mock_clauses = [
        {"text": "The Processor shall process personal data only on written instructions.", "clause_type": "instructions", "subject": "processing instructions", "page": 1},
        {"text": "The Processor shall notify within 72 hours.", "clause_type": "breach_notification", "subject": "breach notification", "page": 1},
    ]
    mock_llm = _make_mock_llm(mock_clauses)

    with patch("app.pipeline.nodes.extract_clauses._get_llm", return_value=mock_llm):
        result = extract_clauses(state)

    assert len(result.clauses) == 2
    assert result.clauses[0].clause_type == "instructions"
    assert result.clauses[1].subject == "breach notification"


def test_extract_clauses_empty_text_returns_empty():
    state = AnalysisState(job_id="test-002", raw_text="", doc_type=DocType.DPA)
    mock_llm = _make_mock_llm([])
    with patch("app.pipeline.nodes.extract_clauses._get_llm", return_value=mock_llm):
        result = extract_clauses(state)
    assert result.clauses == []
