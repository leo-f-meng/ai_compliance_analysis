from typing import Literal
import uuid
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import text as sql_text
from pgvector.sqlalchemy import Vector

RunStatus = Literal["queued", "processing", "done", "failed"]


class Base(DeclarativeBase):
    pass


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )

    status: Mapped[RunStatus] = mapped_column(String(20), default="done")

    input_text: Mapped[str] = mapped_column(Text)

    # store validated output (or partial output)
    result_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # store as integer micro-dollars to avoid float issues (optional); here keep simple int cents? we keep integer microdollars
    cost_usd_micros: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"Run(id={self.id}, status={self.status}, latency_ms={self.latency_ms}, model={self.model}, input_tokens={self.input_tokens}, output_tokens={self.output_tokens}, total_tokens={self.total_tokens}, cost_usd_micros={self.cost_usd_micros})"


### RAG related models: Document and Chunk ###


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sql_text("NOW()")
    )

    def __repr__(self) -> str:
        return f"Document(id={self.id}, title={self.title}, source={self.source})"


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    doc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE")
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sql_text("NOW()")
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)

    def __repr__(self) -> str:
        return f"Chunk(id={self.id}, doc_id={self.doc_id}, chunk_index={self.chunk_index}, content={self.content})"
