import logging
import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.database import Base, engine, get_db
from app.core.ratelimit import limiter
from app.api import auth_router, learner_router
from app.api.placement import router as placement_router
from app.api.lessons import router as lessons_router
from app.api.speaking import router as speaking_router
from app.api.analytics import router as analytics_router
from app.api.writing import router as writing_router
from app.api.gamification import router as gamification_router
from app.api.privacy import router as privacy_router
from app.api.curriculum import router as curriculum_router
from app.api.parent import router as parent_router
from app.api.admin import router as admin_router
from app.api.notifications import router as notifications_router
from app.api.billing import router as billing_router
from app.api.review import router as review_router
from app.api.engagement import router as engagement_router
from app.api.reminders import router as reminders_router
from app.services.gamification import seed_achievements
from app.services.curriculum_seed import seed_curriculum

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agen")

# ── Database setup ────────────────────────────────────────────────────────────
# Dev: auto-create tables if they don't exist (safe — won't drop existing data)
# Production: run `alembic upgrade head` before starting the server
if settings.APP_ENV != "production":
    logger.info("DEV mode: running Base.metadata.create_all() for convenience.")
    Base.metadata.create_all(bind=engine)
else:
    # Production: verify DB is reachable; Alembic migrations must run separately
    try:
        with engine.connect() as conn:
            conn.execute(Base.metadata.tables.get("users").select().limit(1))  # type: ignore[union-attr]
        logger.info("PRODUCTION: DB connection verified.")
    except Exception:
        # Table might not exist yet — that's fine, Alembic handles it
        logger.warning("PRODUCTION: DB check skipped — run `alembic upgrade head` before first start.")

# Seed achievements catalog + curriculum map
with next(get_db()) as db:
    seed_achievements(db)
    new_lessons = seed_curriculum(db)
    if new_lessons:
        logger.info("Seeded %d new curriculum lessons.", new_lessons)

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="AI English Learning Agent — Personalized English Learning for Vietnamese Learners",
    version=settings.APP_VERSION,
    docs_url="/docs" if not settings.is_production else None,   # hide docs in prod
    redoc_url="/redoc" if not settings.is_production else None,
)

# Attach limiter to app state (required by slowapi)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
# Applies the limiter's default per-IP limit to every route.
app.add_middleware(SlowAPIMiddleware)

# ── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,   # reads from ALLOWED_ORIGINS env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "microphone=(self)"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# ── Request logging middleware ────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.info(
        "%s %s → %d  (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response

# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all handler: log the full traceback, return a clean 500 JSON."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Đã xảy ra lỗi nội bộ. Vui lòng thử lại sau."},
    )

# ── API Routers ───────────────────────────────────────────────────────────────
PREFIX = "/api/v1"
app.include_router(auth_router,        prefix=PREFIX)
app.include_router(learner_router,     prefix=PREFIX)
app.include_router(placement_router,   prefix=PREFIX)
app.include_router(lessons_router,     prefix=PREFIX)
app.include_router(speaking_router,    prefix=PREFIX)
app.include_router(analytics_router,   prefix=PREFIX)
app.include_router(writing_router,     prefix=PREFIX)
app.include_router(gamification_router, prefix=PREFIX)
app.include_router(privacy_router, prefix=PREFIX)
app.include_router(curriculum_router, prefix=PREFIX)
app.include_router(parent_router, prefix=PREFIX)
app.include_router(admin_router, prefix=PREFIX)
app.include_router(notifications_router, prefix=PREFIX)
app.include_router(billing_router, prefix=PREFIX)
app.include_router(review_router, prefix=PREFIX)
app.include_router(engagement_router, prefix=PREFIX)
app.include_router(reminders_router, prefix=PREFIX)

# ── Root & Health ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
        "status": "running",
        "docs": "/docs" if not settings.is_production else "disabled",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
