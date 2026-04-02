import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, DateTime, Enum as SAEnum,
    ForeignKey, Text, Boolean
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _now():
    return datetime.now(timezone.utc)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_type = Column(String(16), nullable=True)
    filename_hash = Column(String(64), nullable=False)   # SHA-256 hex
    uploaded_by = Column(String(256), nullable=False)
    status = Column(String(16), nullable=False, default="pending")
    rag_score = Column(String(8), nullable=True)
    gate_decision = Column(String(16), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    findings = relationship("DBFinding", back_populates="job", cascade="all, delete-orphan")
    overrides = relationship("Override", back_populates="job", cascade="all, delete-orphan")
    events = relationship("EventLog", back_populates="job", cascade="all, delete-orphan")


class DBFinding(Base):
    __tablename__ = "findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    requirement_id = Column(String(64), nullable=False)
    severity = Column(String(16), nullable=False)
    status = Column(String(16), nullable=False)
    confidence = Column(Float, nullable=False)
    rag_sources = Column(JSONB, nullable=True)        # Pinecone chunk IDs
    reasoning = Column(Text, nullable=True)
    clause_excerpt = Column(Text, nullable=True)      # AES-256 encrypted
    excerpt_expires_at = Column(DateTime(timezone=True), nullable=True)

    job = relationship("Job", back_populates="findings")


class Override(Base):
    __tablename__ = "overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    reviewer_id = Column(String(256), nullable=False)
    original_score = Column(String(8), nullable=False)
    override_reason = Column(Text, nullable=False)
    mitigating_controls = Column(JSONB, nullable=False)  # list of selected items
    findings_snapshot = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    # No updated_at — append-only

    job = relationship("Job", back_populates="overrides")


class EventLog(Base):
    __tablename__ = "event_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    actor = Column(String(256), nullable=False)
    event_type = Column(String(64), nullable=False)   # upload|analysis_complete|gate|override|purge
    detail = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    job = relationship("Job", back_populates="events")
