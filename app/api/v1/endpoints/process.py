from fastapi import APIRouter, BackgroundTasks
from typing import List

from app.schema.schemas import ExtractionResult, ProcessRequest
from app.workflow.processor import process_run_in_background
from app.db.database import SessionLocal
from app.db.models import Run


router = APIRouter(tags=["V1"])


@router.post("/process", response_model=ExtractionResult)
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


@router.post("/process/batch", response_model=List[ExtractionResult])
def process_batch(reqs: List[ProcessRequest]):
    results = []
    for r in reqs:
        results.append(process(r))
    return results


@router.post("/process/async")
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
