from app.config import Settings


def test_settings_loads_defaults():
    s = Settings(
        openai_api_key="test-key",
        pinecone_api_key="test-key",
        pinecone_index_name="test-index",
        database_url="postgresql://x:x@localhost/x",
    )
    assert s.max_upload_mb == 20
    assert s.excerpt_retention_days == 30
    assert s.confidence_floor == 0.60
    assert s.red_threshold_critical == 1
    assert s.red_threshold_high == 2
    assert s.amber_threshold_high == 1
    assert s.amber_threshold_medium == 3
    assert s.amber_threshold_unclear == 5
