from fastapi import APIRouter
from app.api.v1 import endpoints

router = APIRouter()

router.include_router(endpoints.health.router)
router.include_router(endpoints.process.router)
router.include_router(endpoints.runs.router)
router.include_router(endpoints.example.router)
router.include_router(endpoints.rag.router)
