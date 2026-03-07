from typing import Annotated, List, Optional, Literal
from pydantic import BaseModel, Field

EntityType = Literal["company", "individual", "unknown"]


class Citation(BaseModel):
    doc_id: str
    chunk_id: str
    chunk_index: int
    content: str = Field(..., description="The text content of the cited chunk")


class ProcessRequest(BaseModel):
    text: str = Field(
        ..., min_length=10, description="Unstructured business text to process"
    )


class ExtractionResult(BaseModel):
    entity_type: EntityType
    entity_name: str = Field(..., min_length=1)
    location: Optional[str] = None
    people: List[str] = Field(default_factory=list)
    intent: Optional[str] = None

    # Filled by either LLM or rule engine; we will re-score in risk.py
    risk_flags: List[str] = Field(default_factory=list)
    risk_score: Annotated[int, Field(ge=0, le=10, strict=True)] = 0
    summary: str = Field(..., min_length=5, description="1-2 sentence summary")
    citations: list[Citation] = Field(default_factory=list)


class RAGIngestRequest(BaseModel):
    title: str | None = None
    source: str | None = None
    text: str = Field(..., min_length=20)


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=5)
    top_k: int = 5
    doc_id: str | None = None
