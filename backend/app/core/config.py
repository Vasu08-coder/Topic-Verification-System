import logging
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@localhost:5432/topic_verifier")
    JWT_SECRET: str = Field(default="dev-jwt-secret")
    SIMILARITY_THRESHOLD: float = Field(default=0.75)
    ENVIRONMENT: str = Field(default="dev")
    SMTP_HOST: str = Field(default="localhost")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM_EMAIL: str = Field(default="noreply@example.com")
    EMAIL_BACKEND: str = Field(default="console")
    ALLOWED_ORIGINS: str = Field(default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000")
    UPLOAD_DIR: str = Field(default="uploads")
    MAX_UPLOAD_SIZE_BYTES: int = Field(default=10 * 1024 * 1024)

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

if "localhost" in settings.DATABASE_URL.lower():
    logger.warning(
        "DATABASE_URL resolves to localhost (%s); this should not be used for the production Supabase database.",
        settings.DATABASE_URL,
    )
