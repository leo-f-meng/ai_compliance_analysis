from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from app.models.domain import AnalysisState, Clause
from app.config import settings


class ClauseList(BaseModel):
    clauses: list[Clause]


def _get_llm():
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=settings.openai_api_key,
    )


_SYSTEM_PROMPT = """You are a legal document analyst. Extract all distinct contractual clauses
from the provided document text. For each clause, identify:
- text: the exact clause text (verbatim)
- clause_type: a short label (e.g. breach_notification, subprocessor, retention, security, instructions)
- subject: a brief human-readable description of what the clause covers
- page: the approximate page number (1 if unknown)

Return only what is explicitly present in the document. Do not infer or add clauses."""


def extract_clauses(state: AnalysisState) -> AnalysisState:
    if not state.raw_text.strip():
        return state.model_copy(update={"clauses": []})

    llm = _get_llm()
    structured_llm = llm.with_structured_output(ClauseList)

    result = structured_llm.invoke([
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": f"Document type: {state.doc_type}\n\n{state.raw_text}"},
    ])
    return state.model_copy(update={"clauses": result.clauses})
