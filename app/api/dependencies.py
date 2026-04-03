import hashlib
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.db import Job


def get_current_user(x_user_id: str = Header(...)) -> str:
    """Minimal auth: read user identity from X-User-Id header.
    Replace with JWT validation when SSO is added."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header required")
    return x_user_id


def get_current_user_role(
    x_user_id: str = Header(...),
    x_user_role: str = Header(default="reviewer"),
) -> tuple[str, str]:
    """Returns (user_id, role). Role re-checked against DB in sensitive endpoints."""
    return x_user_id, x_user_role


def compute_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()
