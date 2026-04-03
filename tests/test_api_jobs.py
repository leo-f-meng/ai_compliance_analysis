import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, JSON, String, StaticPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from app.models.db import Base
from app.database import get_db
from main import app

# ── SQLite compatibility: patch PG-specific column types once at import time ──
for table in Base.metadata.tables.values():
    for col in table.columns:
        if isinstance(col.type, JSONB):
            col.type = JSON()
        elif isinstance(col.type, PGUUID):
            col.type = String(36)

# Use StaticPool so all connections in all threads share the same in-memory DB
_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(_engine)
_TestSession = sessionmaker(bind=_engine)


@pytest.fixture
def client():
    def override_db():
        db = _TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_upload_missing_user_header(client):
    response = client.post("/jobs/upload", files={"file": ("test.pdf", b"%PDF-1.4 test", "application/pdf")})
    assert response.status_code == 422  # missing required header


def test_upload_invalid_file_type(client):
    response = client.post(
        "/jobs/upload",
        files={"file": ("test.txt", b"just text, not a PDF", "text/plain")},
        headers={"x-user-id": "user@example.com"},
    )
    assert response.status_code == 422


def test_get_nonexistent_job(client):
    response = client.get(
        f"/jobs/{uuid.uuid4()}",
        headers={"x-user-id": "user@example.com"},
    )
    assert response.status_code == 404


def test_list_jobs_empty(client):
    response = client.get("/jobs", headers={"x-user-id": "user@example.com"})
    assert response.status_code == 200
    assert response.json() == []
