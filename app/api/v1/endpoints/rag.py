from fastapi import APIRouter
from typing import List

from app.schema.schemas import RAGIngestRequest, RAGQueryRequest

from app.rag.rag_ingest import ingest_document
from app.rag.rag_query import query_chunks

router = APIRouter(tags=["Internal"])


@router.post("/rag/ingest")
def rag_ingest(req: List[RAGIngestRequest]):
    results = []
    for r in req:
        results.append(ingest_document(r.title, r.source, r.text))
    return results


@router.post("/rag/query")
def rag_query(req: RAGQueryRequest):
    rets = query_chunks(req.query, req.top_k, req.doc_id)
    return {"results": rets}
