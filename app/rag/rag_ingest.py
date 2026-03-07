from app.db.database import SessionLocal
from app.db.models import Document, Chunk

from app.rag.rag_chunking import chunk_text
from app.rag.rag_embeddings import embed_texts


def ingest_document(title: str | None, source: str | None, text_input: str) -> dict:
    chunks = chunk_text(text_input)
    if not chunks:
        raise ValueError("Empty text")

    vectors = embed_texts(chunks)

    db = SessionLocal()
    try:
        # Insert document record
        doc = Document(title=title, source=source)
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Insert chunks + embeddings
        for i, (content, vec) in enumerate(zip(chunks, vectors)):
            chunk = Chunk(doc_id=doc.id, chunk_index=i, content=content, embedding=vec)
            db.add(chunk)
            db.commit()
            db.refresh(chunk)

        return {
            "doc_id": str(doc.id),
            "chunks": len(chunks),
        }
    finally:
        db.close()
