from __future__ import annotations
from sqlalchemy import text
from app.db import SessionLocal
from app.rag.rag_embeddings import embed_texts


def _vec_to_pgvector_literal(vec: list[float]) -> str:
    # pgvector accepts: '[0.1,0.2,...]'
    return "[" + ",".join(str(x) for x in vec) + "]"


def query_chunks(query: str, top_k: int = 5, doc_id: str | None = None) -> list[dict]:
    top_k = max(1, min(top_k, 20))

    qvec = embed_texts([query])[0]
    qlit = _vec_to_pgvector_literal(qvec)

    db = SessionLocal()
    try:
        if doc_id:
            sql = text(
                """
                SELECT id, doc_id, chunk_index, content,
                       (embedding <-> :qvec) AS distance
                FROM chunks
                WHERE doc_id = :doc_id
                ORDER BY embedding <-> :qvec
                LIMIT :top_k
                """
            )
            rows = (
                db.execute(sql, {"qvec": qlit, "top_k": top_k, "doc_id": doc_id})
                .mappings()
                .all()
            )
        else:
            sql = text(
                """
                SELECT id, doc_id, chunk_index, content,
                       (embedding <-> :qvec) AS distance
                FROM chunks
                ORDER BY embedding <-> :qvec
                LIMIT :top_k
                """
            )
            rows = db.execute(sql, {"qvec": qlit, "top_k": top_k}).mappings().all()

        return [
            {
                "chunk_id": str(r["id"]),
                "doc_id": str(r["doc_id"]),
                "chunk_index": int(r["chunk_index"]),
                "distance": float(r["distance"]) if r["distance"] is not None else None,
                "content": r["content"],
            }
            for r in rows
        ]
    finally:
        db.close()
