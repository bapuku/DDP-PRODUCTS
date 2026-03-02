"""
Configuration via Pydantic Settings.
Never hardcode secrets - use environment variables.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    ENVIRONMENT: str = Field(default="development", description="dev | staging | production")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    API_PORT: int = Field(default=8000, ge=1, le=65535)

    # Neo4j
    NEO4J_URI: str = Field(default="bolt://localhost:7687")
    NEO4J_AUTH: str = Field(default="neo4j/dpp-neo4j-dev")

    # Qdrant
    QDRANT_URL: str = Field(default="http://localhost:6333")

    # PostgreSQL (asyncpg URL)
    POSTGRES_USER: str = Field(default="dpp")
    POSTGRES_PASSWORD: str = Field(default="dpp-dev-secret")
    POSTGRES_DB: str = Field(default="dpp_platform")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432, ge=1, le=65535)

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:29092")
    SCHEMA_REGISTRY_URL: str = Field(default="http://localhost:8081")

    # CORS
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://127.0.0.1:3000"])

    # Auth
    SECRET_KEY: str = Field(default="dpp-dev-secret-change-in-production", min_length=16)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, le=1440)

    # EU AI Act
    AUDIT_RETENTION_YEARS: int = Field(default=10, ge=1, le=30)
    HUMAN_REVIEW_CONFIDENCE_THRESHOLD: float = Field(default=0.85, ge=0.0, le=1.0)

    @property
    def database_url(self) -> str:
        """Async PostgreSQL URL for SQLAlchemy/asyncpg."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync URL for LangGraph PostgresSaver (psycopg2-style)."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
