from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DocType(str, Enum):
    DPA = "DPA"
    MSA = "MSA"
    NDA = "NDA"
    SOW = "SOW"
    POLICY = "POLICY"
    UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FindingStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    UNCLEAR = "unclear"


class RagScore(str, Enum):
    RED = "RED"
    AMBER = "AMBER"
    GREEN = "GREEN"


class GateAction(str, Enum):
    BLOCKED = "BLOCKED"
    ESCALATED = "ESCALATED"
    CLEARED = "CLEARED"
    FAILED = "FAILED"


class Clause(BaseModel):
    text: str
    clause_type: str
    subject: str
    page: int


class Finding(BaseModel):
    requirement_id: str
    severity: Severity
    status: FindingStatus
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    clause_excerpt: str = ""   # max 500 chars, stored encrypted


class GateDecision(BaseModel):
    action: GateAction
    rag_score: RagScore


class AnalysisState(BaseModel):
    job_id: str
    raw_text: str = ""
    doc_type: Optional[DocType] = None
    clauses: list[Clause] = []
    findings: list[Finding] = []
    rag_score: Optional[RagScore] = None
    gate_decision: Optional[GateDecision] = None
    error: Optional[str] = None
