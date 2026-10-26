"""
Day boundaries in the learners' local time.

Streaks, daily challenges and the daily lesson quota all reset at local
midnight. Computing "today" in UTC would roll the day over at 07:00 in
Vietnam, so a learner studying at 23:00 and again at 06:00 the next morning
would be counted as studying on the same day.
"""
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings

LEARNER_TZ = ZoneInfo(settings.LEARNER_TIMEZONE)


def _as_utc(moment: datetime) -> datetime:
    # DB timestamps are stored as naive UTC.
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment


def local_date(moment: datetime) -> date:
    """Calendar date of `moment` in the learners' time zone."""
    return _as_utc(moment).astimezone(LEARNER_TZ).date()


def local_today() -> date:
    return local_date(datetime.now(timezone.utc))


def local_day_start_utc() -> datetime:
    """Start of today (local midnight), expressed as an aware UTC datetime."""
    return datetime.combine(local_today(), time.min, tzinfo=LEARNER_TZ).astimezone(timezone.utc)
