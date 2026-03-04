from __future__ import annotations
import uuid
from sqlalchemy import text
from app.db import SessionLocal
from app.rag.rag_models import Document, Chunk
from app.rag.rag_chunking import chunk_text
from app.rag.rag_embeddings import embed_texts


def ingest_document(title: str | None, source: str | None, text_input: str) -> dict:
    chunks = chunk_text(text_input)
    if not chunks:
        raise ValueError("Empty text")

    vectors = embed_texts(chunks)

    db = SessionLocal()
    try:
        doc = Document(title=title, source=source)
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Insert chunks + embeddings (raw SQL for pgvector)
        for i, (content, vec) in enumerate(zip(chunks, vectors)):
            chunk_id = uuid.uuid4()
            db.execute(
                text(
                    """
                    INSERT INTO chunks (id, doc_id, chunk_index, content, embedding)
                    VALUES (:id, :doc_id, :chunk_index, :content, :embedding)
                    """
                ),
                {
                    "id": str(chunk_id),
                    "doc_id": str(doc.id),
                    "chunk_index": i,
                    "content": content,
                    # pgvector accepts string like '[0.1,0.2,...]'
                    "embedding": "[" + ",".join(str(x) for x in vec) + "]",
                },
            )

        db.commit()

        return {
            "doc_id": str(doc.id),
            "chunks": len(chunks),
        }
    finally:
        db.close()
