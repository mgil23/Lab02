# SPDX-License-Identifier: AGPL-3.0-or-later
from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_PII_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "US_SSN",
    "CREDIT_CARD",
    "IBAN_CODE",
    "MEDICAL_LICENSE",
    "DATE_TIME",
    "IP_ADDRESS",
    "URL",
    "NRP",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    debug: bool = False
    allowed_origins: list[str] = ["http://localhost:3000"]
    frontend_url: str = "http://localhost:3000"

    # Database
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO / S3
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "openidp-documents"
    minio_secure: bool = False

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 30

    # OCR Engine
    ocr_engine_url: str = "http://localhost:8001"

    # AWS / Strands Agents
    aws_default_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    bedrock_model_id: str = "us.anthropic.claude-sonnet-4-6"

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_starter: str = "price_starter_monthly"
    stripe_price_professional: str = "price_professional_monthly"

    # OpenTelemetry
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "openidp-api"

    # Rate limiting
    rate_limit_requests_per_minute: int = 1000

    # ── PII Sanitization ──────────────────────────────────────────────────────
    pii_enabled: bool = True
    pii_language: str = "en"
    # Minimum Presidio confidence score to trigger redaction (0.0–1.0)
    pii_min_score: float = 0.5
    # Comma-separated list of entity types to detect
    pii_entities: list[str] = _DEFAULT_PII_ENTITIES

    # ── Extraction / AI ───────────────────────────────────────────────────────
    # Confidence >= this → auto-accepted green check
    extraction_confidence_valid: float = 0.85
    # Confidence >= this but < valid → yellow warning
    extraction_confidence_review: float = 0.65
    # Confidence < this → flagged for mandatory human review
    extraction_confidence_flag: float = 0.7
    extraction_temperature: float = 0.0
    extraction_max_tokens: int = 4096

    # ── Pipeline ──────────────────────────────────────────────────────────────
    pipeline_max_file_size_mb: int = 100
    pipeline_max_pages: int = 500
    pipeline_timeout_seconds: int = 120
    pipeline_ocr_workers: int = 4

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v

    @field_validator("pii_entities", mode="before")
    @classmethod
    def parse_entities(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [e.strip() for e in v.split(",") if e.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
