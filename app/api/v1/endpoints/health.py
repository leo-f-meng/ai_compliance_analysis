from fastapi import APIRouter

router = APIRouter(tags=["Admin"])


@router.get("/health", tags=["Admin"])
def health():
    return {"status": "ok"}
