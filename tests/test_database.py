import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.db import Base, Job, Override

TEST_DB_URL = "postgresql://compliance:compliance@localhost:5432/compliance"


@pytest.fixture
def db_session():
    engine = create_engine(TEST_DB_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def test_job_creation(db_session):
    job = Job(filename_hash="abc123", uploaded_by="user@example.com")
    db_session.add(job)
    db_session.commit()
    assert job.id is not None
    assert job.status == "pending"


def test_override_append_only(db_session):
    """Override rows must not have updated_at — enforced by schema design."""
    job = Job(filename_hash="abc123", uploaded_by="user@example.com")
    db_session.add(job)
    db_session.commit()
    override = Override(
        job_id=job.id,
        reviewer_id="officer@example.com",
        original_score="RED",
        override_reason="Reviewed with legal team, mitigating controls in place.",
        mitigating_controls=["existing_security_policy", "dpa_in_progress"],
        findings_snapshot=[],
    )
    db_session.add(override)
    db_session.commit()
    assert override.created_at is not None
    assert not hasattr(Override, "updated_at")
