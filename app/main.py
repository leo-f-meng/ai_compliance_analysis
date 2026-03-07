from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import List


from app.schema.schemas import (
    ExtractionResult,
    ProcessRequest,
    RAGIngestRequest,
    RAGQueryRequest,
)
from app.schema.examples import EXAMPLES

from app.workflow.processor import process_run_in_background

from app.db.database import engine
from app.db.models import Base
from app.db.database import SessionLocal
from app.db.models import Run

from app.rag.rag_ingest import ingest_document
from app.rag.rag_quary import query_chunks


app = FastAPI(title="Flow Mind - AI Workflow Engine", version="0.1.1")


# Database setup - create tables if not not exist
Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["Admin"])
def health():
    return {"status": "ok"}


@app.get("/examples", tags=["Support"])
def examples():
    return EXAMPLES


@app.post("/process", response_model=ExtractionResult, tags=["V1"])
def process(req: ProcessRequest):
    db = SessionLocal()
    try:
        run = Run(status="queued", input_text=req.text)
        db.add(run)
        db.commit()
        db.refresh(run)

        result = process_run_in_background(run.id, True)

        return result
    finally:
        db.close()


@app.post("/process/batch", response_model=List[ExtractionResult], tags=["V1"])
def process_batch(reqs: List[ProcessRequest]):
    results = []
    for r in reqs:
        results.append(process(r))
    return results


@app.post("/process/async", tags=["V1"])
def process_async(req: ProcessRequest, background_tasks: BackgroundTasks):
    db = SessionLocal()
    try:
        run = Run(status="queued", input_text=req.text)
        db.add(run)
        db.commit()
        db.refresh(run)

        background_tasks.add_task(process_run_in_background, run.id, True)

        return {"run_id": str(run.id), "status": run.status}
    finally:
        db.close()


@app.get("/runs/{run_id}", tags=["V1"])
def get_run(run_id: str):
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="run not found")

        return {
            "run_id": str(run.id),
            "status": run.status,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "model": run.model,
            "latency_ms": run.latency_ms,
            "usage": {
                "input_tokens": run.input_tokens,
                "output_tokens": run.output_tokens,
                "total_tokens": run.total_tokens,
                "cost_usd_micros": run.cost_usd_micros,
            },
            "error": run.error,
            "result": run.result_json,
        }
    finally:
        db.close()


@app.post("/rag/ingest", tags=["Internal"])
def rag_ingest(req: List[RAGIngestRequest]):
    results = []
    for r in req:
        results.append(ingest_document(r.title, r.source, r.text))
    return results


@app.post("/rag/query", tags=["Internal"])
def rag_query(req: RAGQueryRequest):
    rets = query_chunks(req.query, req.top_k, req.doc_id)
    return {"results": rets}
