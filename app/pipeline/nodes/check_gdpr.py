import json
import re
import yaml
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from app.models.domain import AnalysisState, Finding, FindingStatus, Severity
from app.tools.checklist_tool import ChecklistLookupTool
from app.tools.pinecone_tool import PineconeRetrieverTool
from app.vocabulary_guard import check_vocabulary, VocabularyViolationError
from app.scoring import apply_confidence_floor
from app.config import settings


_SYSTEM_PROMPT = """You are a GDPR compliance analyst. Your job is to check whether contract
clauses satisfy specific GDPR requirements.

For each requirement you are asked to check:
1. Use the checklist_lookup tool to retrieve the requirement definition.
2. Examine the provided clause text.
3. If the clause is ambiguous or the requirement is complex, use pinecone_retriever to get
   relevant GDPR regulatory guidance.
4. Return a structured assessment: status (present/absent/unclear), confidence (0.0-1.0),
   and reasoning (one sentence).

CRITICAL RULES:
- Never use the words: compliant, legal, legally, valid, approved, compliance.
- Only use: present, absent, unclear, needs review.
- If you cannot determine clearly, return status=unclear with low confidence.
- Base your assessment solely on what the clause explicitly states."""


def _load_requirement_ids() -> list[str]:
    with open("data/requirements.yaml") as f:
        data = yaml.safe_load(f)
    return [r["id"] for r in data["requirements"]]


def _build_agent():
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.openai_api_key)
    tools = [ChecklistLookupTool(), PineconeRetrieverTool()]
    return create_agent(llm, tools, system_prompt=_SYSTEM_PROMPT)


def _get_severity(req_id: str) -> Severity:
    try:
        with open("data/requirements.yaml") as f:
            data = yaml.safe_load(f)
        for r in data["requirements"]:
            if r["id"] == req_id:
                return Severity(r["severity"])
    except Exception:
        pass
    return Severity.MEDIUM


def _parse_agent_output(raw: dict, req_id: str) -> Finding:
    """Parse agent output into a Finding. Falls back to Unclear on parse failure."""
    # Support both legacy {"output": "..."} and new {"messages": [...]} formats
    output = raw.get("output", "")
    if not output:
        messages = raw.get("messages", [])
        if messages:
            last = messages[-1]
            output = last.content if hasattr(last, "content") else str(last)
    try:
        match = re.search(r"\{.*\}", output, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return Finding(
                requirement_id=req_id,
                severity=_get_severity(req_id),
                status=FindingStatus(data.get("status", "unclear")),
                confidence=float(data.get("confidence", 0.0)),
                reasoning=str(data.get("reasoning", ""))[:500],
                clause_excerpt=str(data.get("clause_excerpt", ""))[:500],
            )
    except Exception:
        pass

    return Finding(
        requirement_id=req_id,
        severity=_get_severity(req_id),
        status=FindingStatus.UNCLEAR,
        confidence=0.0,
        reasoning="Output parsing failed — manual review required.",
        clause_excerpt="",
    )


def check_gdpr(state: AnalysisState) -> AnalysisState:
    if not state.clauses:
        return state

    agent = _build_agent()
    requirement_ids = _load_requirement_ids()
    all_findings: list[Finding] = []

    for req_id in requirement_ids:
        clause_texts = "\n\n".join(
            f"[Clause {i+1}, page {c.page}]: {c.text}"
            for i, c in enumerate(state.clauses)
        )
        prompt = (
            f"Requirement to check: {req_id}\n\n"
            f"Document type: {state.doc_type}\n\n"
            f"Contract clauses:\n{clause_texts}\n\n"
            "Assess whether this requirement is satisfied. Return a single finding."
        )

        try:
            raw = agent.invoke({"messages": [{"role": "human", "content": prompt}]})
            finding = _parse_agent_output(raw, req_id)
            check_vocabulary(finding.reasoning)
        except VocabularyViolationError:
            finding = Finding(
                requirement_id=req_id,
                severity=_get_severity(req_id),
                status=FindingStatus.UNCLEAR,
                confidence=0.0,
                reasoning="Assessment quarantined: vocabulary constraint violated.",
                clause_excerpt="",
            )
        except Exception:
            finding = Finding(
                requirement_id=req_id,
                severity=_get_severity(req_id),
                status=FindingStatus.UNCLEAR,
                confidence=0.0,
                reasoning="Assessment failed due to processing error.",
                clause_excerpt="",
            )

        all_findings.append(finding)

    floored = apply_confidence_floor(all_findings, settings.confidence_floor)
    return state.model_copy(update={"findings": floored})
