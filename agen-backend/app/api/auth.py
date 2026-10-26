import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core import get_db, get_password_hash, verify_password, create_access_token, settings
from app.models import AuthSession, User, LearnerProfile, ParentProfile


def _generate_invite_code(db: Session) -> str:
    """Generate a unique, human-friendly learner invite code, e.g. 'AGEN-7K2P'."""
    import secrets
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no ambiguous chars
    for _ in range(10):
        code = "AGEN-" + "".join(secrets.choice(alphabet) for _ in range(4))
        if not db.query(LearnerProfile).filter(LearnerProfile.invite_code == code).first():
            return code
    # Fallback with more entropy
    return "AGEN-" + "".join(secrets.choice(alphabet) for _ in range(6))

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Limiter instance — same key_func as main.py so slowapi shares state correctly
limiter = Limiter(key_func=get_remote_address)

# ── Password strength rules ────────────────────────────────────────────────────
_PASSWORD_MIN_LENGTH = 8


def _validate_password_strength(password: str) -> str:
    """
    Enforce minimum password security:
    - At least 8 characters
    - At least 1 letter
    - At least 1 digit
    """
    if len(password) < _PASSWORD_MIN_LENGTH:
        raise ValueError(f"Mat khau phai co it nhat {_PASSWORD_MIN_LENGTH} ky tu.")
    if not re.search(r"[A-Za-z]", password):
        raise ValueError("Mat khau phai chua it nhat 1 chu cai.")
    if not re.search(r"\d", password):
        raise ValueError("Mat khau phai chua it nhat 1 chu so.")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Mat khau khong duoc vuot qua 72 byte.")
    return password


# ── Schemas ───────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    display_name: str
    age: int | None = None
    grade: str | None = None
    role: str = "learner"   # learner | parent

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        if v not in ("learner", "parent"):
            raise ValueError("Vai tro khong hop le.")
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()

    @field_validator("age")
    @classmethod
    def valid_age(cls, v: int | None) -> int | None:
        if v is not None and not 5 <= v <= 120:
            raise ValueError("Tuoi phai nam trong khoang 5 den 120.")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)

    @field_validator("full_name", "display_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Ten khong duoc de trong.")
        return v.strip()


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str | None = None


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    is_verified: bool = False

    @classmethod
    def from_orm_safe(cls, user: "User") -> "UserOut":
        return cls(
            id=str(user.id), email=user.email, full_name=user.full_name,
            role=user.role or "learner", is_verified=bool(user.is_verified),
        )

    model_config = {"from_attributes": True}


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def register(request: Request, payload: UserRegister, db: Session = Depends(get_db)):
    """Register a new AGEN user and initialize their Learner Profile."""
    normalized_email = str(payload.email).lower()
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=normalized_email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(user)
    db.flush()

    if payload.role == "parent":
        # Parent account — create ParentProfile, no learner profile
        db.add(ParentProfile(
            user_id=user.id,
            display_name=payload.display_name,
        ))
    else:
        # Learner account — create LearnerProfile with a unique invite code
        db.add(LearnerProfile(
            user_id=user.id,
            display_name=payload.display_name,
            age=payload.age,
            grade=payload.grade,
            invite_code=_generate_invite_code(db),
        ))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unable to create account")
    db.refresh(user)
    return UserOut.from_orm_safe(user)


@router.post("/login", response_model=Token)
@limiter.limit("20/minute")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate and return JWT access token."""
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _issue_tokens(user, db)


def _issue_tokens(user: User, db: Session) -> dict:
    token_id = str(uuid4())
    refresh_expires = datetime.now(timezone.utc) + timedelta(days=30)
    access_token = create_access_token(
        data={"sub": str(user.id), "type": "access"},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_access_token(
        data={"sub": str(user.id), "type": "refresh", "jti": token_id},
        expires_delta=timedelta(days=30),
    )
    db.add(AuthSession(
        user_id=user.id,
        token_id=token_id,
        expires_at=refresh_expires.replace(tzinfo=None),
    ))
    db.commit()
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    from app.core.security import decode_access_token

    claims = decode_access_token(payload.refresh_token)
    token_id = claims.get("jti") if claims else None
    if not claims or claims.get("type") != "refresh" or not token_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    session = db.query(AuthSession).filter(AuthSession.token_id == token_id, AuthSession.revoked.is_(False)).first()
    if not session or session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired or revoked")
    user = db.query(User).filter(User.id == session.user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User is inactive")
    session.revoked = True
    session.revoked_at = datetime.utcnow()
    db.commit()
    return _issue_tokens(user, db)


from app.core.security import get_current_user


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user (id, email, full_name, role)."""
    return UserOut.from_orm_safe(current_user)


# ── Email verification ─────────────────────────────────────────────────────────
import logging as _logging
import secrets as _secrets

from app.models import EmailVerificationToken

_verif_logger = _logging.getLogger("agen.auth")
_VERIFICATION_TTL_HOURS = 24


class VerificationRequestOut(BaseModel):
    message: str
    # In non-production the token is returned so the flow is testable without SMTP.
    dev_token: str | None = None


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=8)


@router.post("/request-verification", response_model=VerificationRequestOut)
def request_email_verification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Issue a single-use email verification token for the current user.

    No SMTP is wired in the pilot: the token is logged, and returned in the
    response body outside production so the verification flow is usable/testable.
    """
    if current_user.is_verified:
        return VerificationRequestOut(message="Email đã được xác thực.")

    # Invalidate any prior unused tokens for this user.
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == current_user.id,
        EmailVerificationToken.used.is_(False),
    ).update({"used": True, "used_at": datetime.utcnow()})

    token = _secrets.token_urlsafe(32)
    db.add(EmailVerificationToken(
        user_id=current_user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=_VERIFICATION_TTL_HOURS),
    ))
    db.commit()

    _verif_logger.info("Email verification token issued for user_id=%s", current_user.id)
    dev_token = None if settings.is_production else token
    return VerificationRequestOut(
        message="Đã gửi liên kết xác thực đến email của bạn.",
        dev_token=dev_token,
    )


@router.post("/verify-email", response_model=UserOut)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Consume a verification token and mark the user's email as verified."""
    row = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token == payload.token,
    ).first()
    if not row or row.used:
        raise HTTPException(status_code=400, detail="Mã xác thực không hợp lệ hoặc đã dùng.")
    if row.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Mã xác thực đã hết hạn.")

    user = db.query(User).filter(User.id == row.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")

    row.used = True
    row.used_at = datetime.utcnow()
    user.is_verified = True
    db.commit()
    db.refresh(user)
    return UserOut.from_orm_safe(user)
