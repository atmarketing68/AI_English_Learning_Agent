from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from functools import lru_cache
from typing import List, Optional


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    APP_NAME: str = "AI AGENT ENGLISH API"
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

    # Mock "upgrade to Premium" without payment. Unset = allowed outside
    # production only; set ALLOW_DEMO_UPGRADE=true to keep it for a pilot.
    ALLOW_DEMO_UPGRADE: Optional[bool] = None

    # Read the client IP from X-Forwarded-For (set by the hosting proxy).
    TRUST_PROXY_HEADERS: bool = True

    # Time zone that defines a learner's "day" for streaks, daily challenges
    # and the daily lesson quota.
    LEARNER_TIMEZONE: str = "Asia/Ho_Chi_Minh"

    # Free-tier daily lesson allowance, as advertised on the landing page.
    # 0 = unlimited (e.g. for an internal test group).
    FREE_DAILY_LESSON_LIMIT: int = 3

    # Learning reminders — every part is optional and stays off until configured.
    # Public web app URL used in reminder links (defaults to the first ALLOWED_ORIGINS).
    APP_URL: str = ""
    # Web push (VAPID). Generate a pair with: python scripts/generate_vapid_keys.py
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_SUBJECT: str = "mailto:admin@example.com"
    # Email via Resend (https://resend.com); EMAIL_FROM must use a verified domain.
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = ""
    # Shared secret for the scheduler that calls POST /reminders/cron/run.
    REMINDER_CRON_SECRET: str = ""

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
    def app_url(self) -> str:
        url = self.APP_URL or (self.allowed_origins_list[0] if self.allowed_origins_list else "")
        return url.rstrip("/")

    @property
    def push_enabled(self) -> bool:
        return bool(self.VAPID_PUBLIC_KEY and self.VAPID_PRIVATE_KEY)

    @property
    def email_enabled(self) -> bool:
        return bool(self.RESEND_API_KEY and self.EMAIL_FROM)

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def demo_upgrade_enabled(self) -> bool:
        if self.ALLOW_DEMO_UPGRADE is not None:
            return self.ALLOW_DEMO_UPGRADE
        return not self.is_production

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
