"""
G14 · Phân tích giữ chân cho admin: học viên quay lại sau 1 / 7 / 30 ngày theo tuần đăng ký,
phễu đăng ký → kiểm tra đầu vào → bài học đầu tiên → học ≥ 3 ngày → trả phí, và hiệu quả theo nguồn.

Only registered learner accounts are counted (guests who never saved their account are left out).
"Active on a day" = at least one LearningEvent that local (Vietnam) day. A retention window only
counts learners whose window has fully passed, so young cohorts show "—" instead of a low number.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.timeutil import LEARNER_TZ, local_date, local_today
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.payment_order import STATUS_PAID, PaymentOrder
from app.models.user import User

# (label, first day after sign-up, last day) — inclusive windows
WINDOWS = (("d1", 1, 1), ("d7", 7, 13), ("d30", 30, 36))
NO_SOURCE = "(trực tiếp / không rõ)"


def _day_start(d: date) -> datetime:
    """Local (Vietnam) midnight of `d` as naive UTC, comparable with DB columns."""
    return datetime.combine(d, time.min, tzinfo=LEARNER_TZ).astimezone(timezone.utc).replace(tzinfo=None)


def _learners_since(db: Session, since: date):
    start = _day_start(since)
    return (
        db.query(User, LearnerProfile)
        .join(LearnerProfile, LearnerProfile.user_id == User.id)
        .filter(User.role == "learner", User.is_guest.isnot(True), User.created_at >= start)
        .all()
    )


def _active_days(db: Session, learner_ids: list[str], since: date) -> dict[str, set[date]]:
    out: dict[str, set[date]] = defaultdict(set)
    if not learner_ids:
        return out
    start = _day_start(since)
    for i in range(0, len(learner_ids), 500):
        chunk = learner_ids[i:i + 500]
        rows = db.query(LearningEvent.learner_id, LearningEvent.recorded_at).filter(
            LearningEvent.learner_id.in_(chunk), LearningEvent.recorded_at >= start).all()
        for lid, at in rows:
            if at is not None:
                out[lid].add(local_date(at))
    return out


def _paid_users(db: Session, user_ids: list[str]) -> set[str]:
    if not user_ids:
        return set()
    return {uid for (uid,) in db.query(PaymentOrder.user_id).filter(PaymentOrder.user_id.in_(user_ids), PaymentOrder.status == STATUS_PAID).distinct().all()}


def _rate(hit: int, base: int) -> float | None:
    return round(hit / base * 100, 1) if base else None


def cohorts(db: Session, weeks: int = 8, today: date | None = None) -> list[dict]:
    """One row per sign-up week (Monday, Vietnam time), newest first."""
    today = today or local_today()
    this_monday = today - timedelta(days=today.weekday())
    first_monday = this_monday - timedelta(weeks=weeks - 1)
    pairs = _learners_since(db, first_monday)
    days = _active_days(db, [lp.id for _, lp in pairs], first_monday)
    by_week: dict[date, list[tuple[User, LearnerProfile]]] = defaultdict(list)
    for u, lp in pairs:
        signup = local_date(u.created_at)
        by_week[signup - timedelta(days=signup.weekday())].append((u, lp))
    out = []
    for w in range(weeks):
        monday = this_monday - timedelta(weeks=w)
        members = by_week.get(monday, [])
        row = {"week_start": monday.isoformat(), "signups": len(members)}
        for key, lo, hi in WINDOWS:
            eligible = hit = 0
            for u, lp in members:
                signup = local_date(u.created_at)
                if today < signup + timedelta(days=hi):
                    continue          # window not over yet
                eligible += 1
                if any(signup + timedelta(days=d) in days.get(lp.id, ()) for d in range(lo, hi + 1)):
                    hit += 1
            row[key] = _rate(hit, eligible)
            row[f"{key}_eligible"] = eligible
        out.append(row)
    return out


def funnel(db: Session, days: int = 30, today: date | None = None) -> dict:
    """Sign-ups of the last `days` days and how far they got."""
    today = today or local_today()
    since = today - timedelta(days=days - 1)
    pairs = _learners_since(db, since)
    active = _active_days(db, [lp.id for _, lp in pairs], since)
    paid = _paid_users(db, [u.id for u, _ in pairs])
    steps = [
        ("registered", "Đăng ký", len(pairs)),
        ("placement", "Làm kiểm tra đầu vào", sum(1 for _, lp in pairs if (lp.placement_completed or "none") != "none")),
        ("first_lesson", "Học xong bài đầu tiên", sum(1 for _, lp in pairs if (lp.total_lessons_completed or 0) >= 1)),
        ("active3", "Học ≥ 3 ngày khác nhau", sum(1 for _, lp in pairs if len(active.get(lp.id, ())) >= 3)),
        ("paid", "Trả phí", sum(1 for u, _ in pairs if u.id in paid)),
    ]
    base = steps[0][2]
    return {"days": days, "steps": [{"key": k, "label": label, "count": n, "pct": _rate(n, base)} for k, label, n in steps]}


def sources(db: Session, days: int = 90, today: date | None = None) -> list[dict]:
    """Sign-ups by first-touch source with activation (≥ 1 lesson) and payment, biggest first."""
    today = today or local_today()
    pairs = _learners_since(db, today - timedelta(days=days - 1))
    paid = _paid_users(db, [u.id for u, _ in pairs])
    agg: dict[str, dict] = {}
    for u, lp in pairs:
        key = u.signup_source or NO_SOURCE
        row = agg.setdefault(key, {"source": key, "signups": 0, "activated": 0, "paid": 0})
        row["signups"] += 1
        row["activated"] += 1 if (lp.total_lessons_completed or 0) >= 1 else 0
        row["paid"] += 1 if u.id in paid else 0
    out = sorted(agg.values(), key=lambda r: (-r["signups"], r["source"]))
    for r in out:
        r["activation_pct"] = _rate(r["activated"], r["signups"])
        r["paid_pct"] = _rate(r["paid"], r["signups"])
    return out


def summary(db: Session, weeks: int = 8, today: date | None = None) -> dict:
    today = today or local_today()
    return {
        "generated_for": today.isoformat(),
        "cohorts": cohorts(db, weeks, today),
        "funnel": funnel(db, 30, today),
        "sources": sources(db, 90, today),
        "windows": {"d1": "ngày 1", "d7": "ngày 7–13", "d30": "ngày 30–36"},
    }

