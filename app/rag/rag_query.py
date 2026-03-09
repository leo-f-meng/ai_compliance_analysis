from sqlalchemy import select
from app.db.database import SessionLocal
from app.db.models import Chunk
from app.rag.rag_embeddings import embed_texts


def query_chunks(query: str, top_k: int = 5, doc_id: str | None = None) -> list[dict]:
    top_k = max(1, min(top_k, 20))

    qvec = embed_texts([query])[0]

    db = SessionLocal()

    try:
        stmt = (
            select(
                Chunk.id,
                Chunk.doc_id,
                Chunk.chunk_index,
                Chunk.content,
                (Chunk.embedding.l2_distance(qvec).label("distance")),
            )
            .order_by("distance")
            .limit(top_k)
        )

        if doc_id:
            stmt = stmt.where(Chunk.doc_id == doc_id)

        rows = db.execute(stmt).mappings().all()

        return [
            {
                "chunk_id": str(r["id"]),
                "doc_id": str(r["doc_id"]),
                "chunk_index": r["chunk_index"],
                "distance": float(r["distance"]) if r["distance"] is not None else None,
                "content": r["content"],
            }
            for r in rows
        ]

    finally:
        db.close()
