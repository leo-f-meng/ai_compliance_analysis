from fastapi import APIRouter
from app.schema.examples import EXAMPLES


router = APIRouter(tags=["Support"])


@router.get("/examples")
def examples():
    return EXAMPLES
