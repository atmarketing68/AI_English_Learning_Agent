"""
G10 · Chứng nhận hoàn thành.

Two kinds:
  - track: the learner finished every lesson of a goal track (IELTS / TOEIC /
    interview) and claims it; issuer is AI AGENT ENGLISH.
  - group: a teacher / company issues one to a member of their group.
Each certificate has a short public code; /certificates/verify/<code> (no login)
lets an employer or school check it. Details snapshot the learner's numbers
at issue time so the printed certificate never changes later.
"""
from __future__ import annotations

import secrets

from sqlalchemy.orm import Session

from app.models.certificate import Certificate
from app.models.goal_track import GoalTrackProgress
from app.models.learner_profile import LearnerProfile
from app.services import goal_tracks

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
APP_ISSUER = "AI AGENT ENGLISH"


class CertificateError(ValueError):
    pass


def new_code(db: Session) -> str:
    for _ in range(20):
        code = "AGEN-" + "".join(secrets.choice(ALPHABET) for _ in range(4)) + "-" + "".join(secrets.choice(ALPHABET) for _ in range(4))
        if not db.query(Certificate).filter(Certificate.code == code).first():
            return code
    raise CertificateError("Không tạo được mã chứng nhận.")


def snapshot(learner: LearnerProfile) -> dict:
    return {
        "level": learner.overall_level or "A1",
        "total_xp": learner.total_xp or 0,
        "lessons": learner.total_lessons_completed or 0,
        "longest_streak": learner.longest_streak or 0,
        "skills": {k: round(getattr(learner, f"{k}_score", 0) or 0) for k in ("listening", "speaking", "reading", "writing", "vocabulary", "grammar")},
    }


def track_completed(db: Session, learner_id: str, track: dict) -> bool:
    codes = set(goal_tracks.track_lesson_codes(track))
    done = {c for (c,) in db.query(GoalTrackProgress.lesson_code).filter(
        GoalTrackProgress.learner_id == learner_id, GoalTrackProgress.track_id == track["id"], GoalTrackProgress.status == "completed").all()}
    return bool(codes) and codes <= done


def issue(db: Session, learner: LearnerProfile, *, kind: str, ref_id: str | None, title: str, issuer_name: str,
          note: str | None = None, issued_by_user_id: str | None = None) -> Certificate:
    """Idempotent per (learner, kind, ref, title): issuing twice returns the existing certificate."""
    existing = db.query(Certificate).filter(Certificate.learner_id == learner.id, Certificate.kind == kind, Certificate.ref_id == ref_id,
                                            Certificate.title == title, Certificate.revoked.is_(False)).first()
    if existing:
        return existing
    cert = Certificate(code=new_code(db), learner_id=learner.id, kind=kind, ref_id=ref_id, title=title[:200],
                       recipient_name=(learner.display_name or "Học viên")[:120], issuer_name=issuer_name[:160], note=(note or None) and note[:300],
                       details=snapshot(learner), issued_by_user_id=issued_by_user_id)
    db.add(cert)
    db.flush()
    return cert


def claim_track(db: Session, learner: LearnerProfile, track_id: str) -> Certificate:
    track = goal_tracks.get_track(track_id)
    if not track:
        raise CertificateError("Không tìm thấy khoá học.")
    if not track_completed(db, learner.id, track):
        raise CertificateError("Hoàn thành tất cả bài của khoá để nhận chứng nhận.")
    total = len(goal_tracks.track_lesson_codes(track))
    return issue(db, learner, kind="track", ref_id=track_id, title=track.get("title_vi") or track.get("title_en") or track_id, issuer_name=APP_ISSUER,
                 note=f"Hoàn thành {total} bài của lộ trình")
