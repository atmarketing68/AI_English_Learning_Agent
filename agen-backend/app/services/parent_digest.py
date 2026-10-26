"""
G3 · Phụ huynh chủ động: the app writes to parents instead of waiting for them.

  - Weekly report e-mail every Sunday evening (local time) with each linked
    child's "what improved / what needs help / what to do".
  - Inactivity alert when a child has not studied for 2 days — once per
    quiet spell (no repeat until the child studies again).

Runs from the hourly scheduler hook (/reminders/cron/run). Needs the e-mail
channel (Resend); without it nothing is sent and the stats say so.
"""
from __future__ import annotations

import html
import logging
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.timeutil import LEARNER_TZ, local_date
from app.models.learner_profile import LearnerProfile
from app.models.parent import ParentChildLink, ParentProfile
from app.models.user import User
from app.services.engagement import week_key
from app.services.parent_reports import build_child_report
from app.services.reminders import ReminderMessage, deliver_email, push_to_user
from app.services.streak_service import effective_streak

logger = logging.getLogger("agen.parent_digest")

WEEKLY_SEND_WEEKDAY = 6      # Sunday
WEEKLY_SEND_HOUR = 18        # from 18:00 local; the hourly job catches it the same evening
INACTIVE_AFTER_DAYS = 2
# G7 · "streak at risk" push window (local hours): the child has a streak but has not studied today.
STREAK_ALERT_FROM_HOUR = 19
STREAK_ALERT_TO_HOUR = 21
STREAK_ALERT_MIN_STREAK = 3


def _report_html(report: dict) -> str:
    skills = " · ".join(f"{s['label']} {s['score']:.0f}%" for s in report["skills"])
    return f"""<div style="padding:16px 18px;border:1px solid #e5e5ea;border-radius:14px;margin:0 0 14px">
  <h2 style="font-size:17px;margin:0 0 6px">{html.escape(report['display_name'])} · {html.escape(report['overall_level'])}</h2>
  <p style="font-size:13px;color:#86868b;margin:0 0 10px">{report['sessions_this_week']} buổi học · {report['xp_this_week']} XP · chuỗi {report['current_streak']} ngày · chính xác {report['accuracy_pct']:.0f}%</p>
  <p style="margin:0 0 6px"><b>Tiến bộ:</b> {html.escape(report['what_improved'])}</p>
  <p style="margin:0 0 6px"><b>Cần hỗ trợ:</b> {html.escape(report['what_needs_help'])}</p>
  <p style="margin:0 0 6px"><b>Bố mẹ nên làm:</b> {html.escape(report['what_to_do'])}</p>
  <p style="font-size:12px;color:#86868b;margin:8px 0 0">{html.escape(skills)}</p>
</div>"""


def _wrap(title: str, body_html: str, cta_text: str = "Xem bảng theo dõi", path: str = "/parent") -> str:
    link = settings.app_url + path
    return f"""<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:520px;margin:0 auto;padding:24px;color:#1d1d1f">
  <p style="font-size:13px;color:#86868b;margin:0 0 16px">AI AGENT ENGLISH · Phụ huynh</p>
  <h1 style="font-size:22px;margin:0 0 16px">{html.escape(title)}</h1>
  {body_html}
  <a href="{html.escape(link)}" style="display:inline-block;background:#0071e3;color:#fff;text-decoration:none;padding:12px 22px;border-radius:999px;font-weight:600">{html.escape(cta_text)}</a>
  <p style="font-size:12px;color:#86868b;margin:32px 0 0">Bạn nhận email này vì đã liên kết với con trong AI AGENT ENGLISH. Tắt email báo cáo trong Bảng theo dõi phụ huynh.</p>
</div>"""


def _children(db: Session, parent: ParentProfile) -> list[tuple[ParentChildLink, LearnerProfile]]:
    rows = (
        db.query(ParentChildLink, LearnerProfile)
        .join(LearnerProfile, LearnerProfile.id == ParentChildLink.learner_id)
        .filter(ParentChildLink.parent_id == parent.id)
        .all()
    )
    return [(link, learner) for link, learner in rows]


def send_weekly_report(db: Session, parent: ParentProfile, user: User, now: datetime) -> bool:
    children = _children(db, parent)
    if not children or not user.email:
        return False
    reports = [build_child_report(db, learner, now) for _, learner in children]
    names = ", ".join(r["display_name"] for r in reports)
    title = f"Báo cáo tuần của {names}"
    body = "".join(_report_html(r) for r in reports)
    text = "\n\n".join(
        f"{r['display_name']} ({r['overall_level']}): {r['sessions_this_week']} buổi, {r['xp_this_week']} XP.\n"
        f"Tiến bộ: {r['what_improved']}\nCần hỗ trợ: {r['what_needs_help']}\nBố mẹ nên làm: {r['what_to_do']}"
        for r in reports
    )
    return deliver_email(user.email, title, _wrap(title, body), text + f"\n\n{settings.app_url}/parent")


def send_inactivity_alert(db: Session, parent: ParentProfile, user: User, learner: LearnerProfile, days: int) -> bool:
    if not user.email:
        return False
    name = learner.display_name
    title = f"{name} đã nghỉ học {days} ngày"
    body = (
        f"<p style=\"margin:0 0 12px\">{html.escape(name)} chưa mở AI AGENT ENGLISH trong {days} ngày. "
        f"Chuỗi ngày học của con đang có nguy cơ bị mất.</p>"
        f"<p style=\"margin:0 0 20px\">Một bài 10 phút hôm nay là đủ để quay lại nhịp. Bố mẹ có thể nhắc con: "
        f"“Học một bài ngắn rồi mình đi chơi nhé.”</p>"
    )
    text = f"{name} chưa học trong {days} ngày. Một bài 10 phút hôm nay là đủ để quay lại nhịp.\n\n{settings.app_url}/parent"
    return deliver_email(user.email, title, _wrap(title, body, "Xem tiến bộ của con"), text)


def push_weekly_ready(db: Session, parent: ParentProfile, user: User, names: str) -> int:
    if not parent.push_alerts:
        return 0
    return push_to_user(db, user.id, ReminderMessage(title=f"📊 Báo cáo tuần của {names} đã sẵn sàng", body="Xem con tiến bộ gì, cần hỗ trợ gì và bố mẹ nên làm gì tuần tới.", url="/parent"), tag="parent-weekly")


def push_inactivity(db: Session, parent: ParentProfile, user: User, learner: LearnerProfile, days: int) -> int:
    if not parent.push_alerts:
        return 0
    return push_to_user(db, user.id, ReminderMessage(title=f"😴 {learner.display_name} đã nghỉ học {days} ngày", body="Một bài 10 phút hôm nay là đủ để quay lại nhịp. Nhắc con nhé!", url="/parent"), tag="parent-inactive")


def push_streak_at_risk(db: Session, parent: ParentProfile, user: User, learner: LearnerProfile, streak: int) -> int:
    if not parent.push_alerts:
        return 0
    return push_to_user(db, user.id, ReminderMessage(title=f"🔥 Chuỗi {streak} ngày của {learner.display_name} sắp mất", body="Con chưa học hôm nay. Một bài ngắn trước khi đi ngủ là giữ được chuỗi.", url="/parent"), tag="parent-streak")


def run_parent_digests(db: Session, now: datetime | None = None) -> dict:
    """Send what is due right now (e-mail and/or push). Returns counters for the scheduler log."""
    now = now or datetime.now(timezone.utc)
    now_local = now.astimezone(LEARNER_TZ)
    today: date = now_local.date()
    stats = {"email_enabled": settings.email_enabled, "push_enabled": settings.push_enabled, "parents": 0, "weekly_sent": 0, "alerts_sent": 0, "push_sent": 0}
    if not settings.email_enabled and not settings.push_enabled:
        return stats

    parents = (
        db.query(ParentProfile, User)
        .join(User, User.id == ParentProfile.user_id)
        .filter(User.is_active.isnot(False))
        .all()
    )
    weekly_window = now_local.weekday() == WEEKLY_SEND_WEEKDAY and now_local.hour >= WEEKLY_SEND_HOUR
    streak_window = STREAK_ALERT_FROM_HOUR <= now_local.hour < STREAK_ALERT_TO_HOUR
    this_week = week_key(today)

    for parent, user in parents:
        stats["parents"] += 1
        children = _children(db, parent)
        if weekly_window and parent.last_weekly_report_week != this_week and children:
            sent_email = settings.email_enabled and parent.weekly_report_email and send_weekly_report(db, parent, user, now)
            pushed = push_weekly_ready(db, parent, user, ", ".join(l.display_name for _, l in children)) if settings.push_enabled else 0
            if sent_email or pushed:
                parent.last_weekly_report_week = this_week
                stats["weekly_sent"] += 1 if sent_email else 0
                stats["push_sent"] += pushed
                db.commit()

        for link, learner in children:
            # Streak at risk tonight (push only, once per day per child).
            if settings.push_enabled and streak_window and parent.push_alerts and link.last_streak_alert_on != today.isoformat():
                active_today = learner.last_active_at is not None and local_date(learner.last_active_at) >= today
                streak = effective_streak(learner)
                if not active_today and streak >= STREAK_ALERT_MIN_STREAK:
                    pushed = push_streak_at_risk(db, parent, user, learner, streak)
                    if pushed:
                        link.last_streak_alert_on = today.isoformat()
                        stats["push_sent"] += pushed
                        db.commit()

            if not learner.last_active_at:
                continue
            last_active = local_date(learner.last_active_at)
            idle_days = (today - last_active).days
            if idle_days < INACTIVE_AFTER_DAYS:
                continue
            already = link.last_inactivity_alert_on
            if already and date.fromisoformat(already) >= last_active:
                continue            # alerted once for this quiet spell
            sent_email = settings.email_enabled and parent.weekly_report_email and send_inactivity_alert(db, parent, user, learner, idle_days)
            pushed = push_inactivity(db, parent, user, learner, idle_days) if settings.push_enabled else 0
            if sent_email or pushed:
                link.last_inactivity_alert_on = today.isoformat()
                stats["alerts_sent"] += 1 if sent_email else 0
                stats["push_sent"] += pushed
                db.commit()
    return stats
