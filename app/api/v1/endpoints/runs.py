from fastapi import APIRouter, HTTPException

from app.db.database import SessionLocal
from app.db.models import Run

router = APIRouter(tags=["V1"])


@router.get("/runs/{run_id}")
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
