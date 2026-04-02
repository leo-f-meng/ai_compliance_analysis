from fastapi import APIRouter

router = APIRouter(prefix="/jobs", tags=["overrides"])  # handles POST /jobs/{job_id}/override
