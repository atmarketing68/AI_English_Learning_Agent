from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    APP_NAME: str = "AGEN API"
    APP_VERSION: str = "1.0.0"

    # Security — MUST be changed in production
    SECRET_KEY: str = "changeme-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite:///./agen_dev.db"

    # CORS — comma-separated list of allowed origins
    # e.g. ALLOWED_ORIGINS="http://localhost:3000,https://agen.yourdomain.com"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # AI Services
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Distributed worker. Empty means local FastAPI BackgroundTasks fallback.
    REDIS_URL: str = ""
    WORKER_MODE: str = "local"

    # Admin allowlist — comma-separated emails granted access to /admin/* quality
    # views. Empty means no admin (endpoints return 403 for everyone).
    ADMIN_EMAILS: str = ""

    # Free-tier daily lesson allowance. Set high (or 0 = unlimited) for the pilot
    # so testers are never blocked; lower it when monetization goes live.
    FREE_DAILY_LESSON_LIMIT: int = 1000

    @field_validator("SECRET_KEY")
    @classmethod
    def warn_default_secret(cls, v: str) -> str:
        if v == "changeme-in-production":
            import warnings
            warnings.warn(
                "⚠️  SECRET_KEY is using the default insecure value. "
                "Set a strong random key in .env before deploying to production.",
                stacklevel=2,
            )
        return v

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list, stripping whitespace."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def admin_emails_list(self) -> List[str]:
        """Parse ADMIN_EMAILS into a normalized (lowercased) list."""
        return [e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        if not self.is_production:
            return self

        if self.SECRET_KEY == "changeme-in-production":
            raise ValueError("SECRET_KEY must be explicitly configured in production")
        if self.DATABASE_URL.startswith("sqlite"):
            raise ValueError("Production requires PostgreSQL; SQLite is development-only")
        if not (self.GEMINI_API_KEY or self.OPENAI_API_KEY):
            raise ValueError("Production requires GEMINI_API_KEY or OPENAI_API_KEY")
        if not self.allowed_origins_list:
            raise ValueError("ALLOWED_ORIGINS must contain at least one origin in production")
        if self.WORKER_MODE == "distributed" and not self.REDIS_URL:
            raise ValueError("REDIS_URL is required when WORKER_MODE=distributed")
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"   # ignore unknown env vars (e.g. FRONTEND_URL from old .env)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
