"""G10 · Chứng nhận: my certificates + claimable tracks, claim a track certificate, public verification."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.certificate import Certificate
from app.models.learner_profile import LearnerProfile
from app.models.user import User
from app.services import certificates as svc
from app.services import goal_tracks

router = APIRouter(prefix="/certificates", tags=["Certificates"])


class CertificateOut(BaseModel):
    code: str
    kind: str
    title: str
    recipient_name: str
    issuer_name: str
    note: Optional[str]
    details: dict
    issued_at: datetime
    revoked: bool = False


class ClaimableTrack(BaseModel):
    track_id: str
    title: str
    completed: bool
    claimed_code: Optional[str]


class MyCertificates(BaseModel):
    certificates: list[CertificateOut]
    tracks: list[ClaimableTrack]


def cert_out(c: Certificate) -> CertificateOut:
    return CertificateOut(code=c.code, kind=c.kind, title=c.title, recipient_name=c.recipient_name, issuer_name=c.issuer_name,
                          note=c.note, details=c.details or {}, issued_at=c.issued_at, revoked=bool(c.revoked))


def _learner(db: Session, user: User) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found")
    return learner


@router.get("", response_model=MyCertificates)
def mine(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    certs = db.query(Certificate).filter(Certificate.learner_id == learner.id, Certificate.revoked.is_(False)).order_by(Certificate.issued_at.desc()).all()
    claimed = {c.ref_id: c.code for c in certs if c.kind == "track"}
    tracks = [ClaimableTrack(track_id=t["id"], title=t["title_vi"], completed=svc.track_completed(db, learner.id, t), claimed_code=claimed.get(t["id"]))
              for t in goal_tracks.list_tracks()]
    return MyCertificates(certificates=[cert_out(c) for c in certs], tracks=tracks)


@router.post("/tracks/{track_id}", response_model=CertificateOut)
def claim_track(track_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    try:
        cert = svc.claim_track(db, learner, track_id)
    except svc.CertificateError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return cert_out(cert)


@router.get("/verify/{code}", response_model=CertificateOut)
def verify(code: str, db: Session = Depends(get_db)):
    """Public: anyone with the code can check the certificate (no login)."""
    cert = db.query(Certificate).filter(Certificate.code == code.strip().upper()).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Không tìm thấy chứng nhận với mã này.")
    return cert_out(cert)
