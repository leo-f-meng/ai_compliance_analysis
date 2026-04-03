import asyncio
from datetime import datetime, timezone, timedelta
from uuid import UUID
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, compute_file_hash, get_db
from app.models.db import Job, DBFinding, EventLog
from app.models.domain import AnalysisState, RagScore, GateAction
from app.pipeline.nodes.parse_document import parse_document
from app.pipeline.graph import get_graph
from app.encryption import generate_job_key, encrypt_excerpt
from app.config import settings
import json

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _log_event(db: Session, job_id, actor: str, event_type: str, detail: dict = None):
    db.add(EventLog(job_id=job_id, actor=actor, event_type=event_type, detail=detail or {}))
    db.commit()


async def _run_pipeline(job_id: str, state: AnalysisState, db: Session, user_id: str):
    """Background task: run the LangGraph pipeline and persist results."""
    try:
        graph = get_graph()
        config = {"configurable": {"thread_id": job_id}}
        final_state = await asyncio.to_thread(
            graph.invoke, state, config
        )

        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job_key = generate_job_key()
        excerpt_expires = datetime.now(timezone.utc) + timedelta(days=settings.excerpt_retention_days)

        for finding in final_state.findings:
            encrypted_excerpt = encrypt_excerpt(finding.clause_excerpt, job_key) if finding.clause_excerpt else None
            db.add(DBFinding(
                job_id=job_id,
                requirement_id=finding.requirement_id,
                severity=finding.severity.value,
                status=finding.status.value,
                confidence=finding.confidence,
                rag_sources=None,
                reasoning=finding.reasoning,
                clause_excerpt=encrypted_excerpt,
                excerpt_expires_at=excerpt_expires if encrypted_excerpt else None,
            ))

        score = final_state.rag_score.value if final_state.rag_score else "RED"
        gate = final_state.gate_decision.action.value if final_state.gate_decision else "FAILED"
        job.rag_score = score
        job.gate_decision = gate
        job.status = "complete"
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        _log_event(db, job.id, user_id, "analysis_complete", {"rag_score": score, "gate": gate})
        _log_event(db, job.id, "system", "gate", {"action": gate})

    except Exception as e:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.rag_score = RagScore.AMBER.value
            job.gate_decision = GateAction.ESCALATED.value
            db.commit()
        _log_event(db, job_id, "system", "pipeline_error", {"error": str(e)})


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_bytes = await file.read()
    file_hash = compute_file_hash(file_bytes)

    # Idempotency: return existing job if same document already processed
    existing = db.query(Job).filter(
        Job.filename_hash == file_hash,
        Job.uploaded_by == user_id,
    ).first()
    if existing:
        return {"job_id": str(existing.id), "status": existing.status, "existing": True}

    # Parse and validate (raises ValueError on bad files)
    try:
        initial_state = AnalysisState(job_id="pending")
        parsed_state = parse_document(initial_state, file_bytes=file_bytes, filename=file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    job_retention = datetime.now(timezone.utc) + timedelta(days=settings.job_retention_years * 365)
    job = Job(
        filename_hash=file_hash,
        uploaded_by=user_id,
        doc_type=parsed_state.doc_type.value if parsed_state.doc_type else None,
        status="processing",
        expires_at=job_retention,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    state = parsed_state.model_copy(update={"job_id": str(job.id)})
    _log_event(db, job.id, user_id, "upload", {"filename": file.filename, "doc_type": state.doc_type})

    background_tasks.add_task(_run_pipeline, str(job.id), state, db, user_id)
    return {"job_id": str(job.id), "status": "processing"}


@router.get("/{job_id}")
def get_job(
    job_id: UUID,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": str(job.id),
        "status": job.status,
        "doc_type": job.doc_type,
        "rag_score": job.rag_score,
        "gate_decision": job.gate_decision,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
    }


@router.get("/{job_id}/findings")
def get_findings(
    job_id: UUID,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    findings = db.query(DBFinding).filter(DBFinding.job_id == job_id).all()
    return [
        {
            "requirement_id": f.requirement_id,
            "severity": f.severity,
            "status": f.status,
            "confidence": f.confidence,
            "reasoning": f.reasoning,
            "has_excerpt": f.clause_excerpt is not None and f.excerpt_expires_at is not None,
        }
        for f in findings
    ]


@router.get("")
def list_jobs(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jobs = db.query(Job).filter(Job.uploaded_by == user_id).order_by(Job.created_at.desc()).limit(50).all()
    return [
        {"job_id": str(j.id), "status": j.status, "rag_score": j.rag_score, "created_at": j.created_at}
        for j in jobs
    ]
