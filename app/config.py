from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    pinecone_api_key: str
    pinecone_index_name: str
    database_url: str

    # Thresholds (all configurable via env)
    confidence_floor: float = 0.60
    red_threshold_critical: int = 1   # any Critical → RED
    red_threshold_high: int = 2       # ≥2 High → RED
    amber_threshold_high: int = 1     # 1 High → AMBER
    amber_threshold_medium: int = 3   # ≥3 Medium → AMBER
    amber_threshold_unclear: int = 5  # ≥5 Unclear → AMBER

    # Data retention
    excerpt_retention_days: int = 30
    job_retention_years: int = 3

    # Upload limits
    max_upload_mb: int = 20

    # Rate limiting
    max_concurrent_jobs_per_user: int = 10
    max_daily_jobs_per_user: int = 50


settings = Settings()
