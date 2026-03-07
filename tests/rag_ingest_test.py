from app.db.rag_ingest import ingest_document

result = ingest_document(
    title="Test Policy",
    source="manual",
    text_input="This is a refund policy. Customers can request refunds within 14 days. "
    * 50,
)

print(result)
