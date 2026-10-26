"""
G10 · Câu lạc bộ nói: 2–4 học viên vào một phòng, AI làm người dẫn.

The host picks a topic and starts. The AI asks each member in turn; the member
speaks (browser speech recognition → transcript) and the AI replies with a
short Vietnamese tip, a corrected sentence and the next question to the next
member. Clients poll for new messages (seq numbers). Without the LLM the AI
falls back to the topic's scripted questions, so a session always continues.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.learner_profile import LearnerProfile
from app.models.speaking_club import ROOM_ACTIVE, ROOM_FINISHED, ROOM_WAITING, GroupClubSchedule, RoomMember, RoomMessage, SpeakingRoom

MAX_MEMBERS = 4
TURNS_PER_MEMBER = 3
XP_PER_TURN = 5
WAITING_ROOM_TTL_MIN = 60          # waiting rooms older than this drop out of the lobby
# G11 · scheduled sessions
SCHEDULE_MIN_LEAD_MIN = 10         # book at least this far ahead
SCHEDULE_MAX_DAYS = 14
EARLY_START_MIN = 10               # the host may open a booked room this many minutes early
REMIND_BEFORE_MIN = 15             # "starts soon" reminder window (scheduler runs every ~10 minutes)
REMIND_WINDOW_MIN = 25
SCHEDULED_EXPIRE_MIN = 120         # a booked room nobody started is closed this long after its time
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

TOPICS: list[dict] = [
    {"id": "hobbies", "title": "Hobbies & free time", "title_vi": "Sở thích & thời gian rảnh", "level": "A2", "emoji": "🎨",
     "opener": "Welcome to today's speaking club! Our topic is hobbies and free time. Let's start easy.",
     "questions": ["What do you usually do at the weekend?", "Is there a hobby you would like to try? Why?", "Do you prefer spending free time alone or with friends?",
                   "How has your favourite hobby changed since you were a child?", "If you had one free day tomorrow, how would you spend it?"]},
    {"id": "food", "title": "Food & cooking", "title_vi": "Ẩm thực & nấu ăn", "level": "A2", "emoji": "🍜",
     "opener": "Hello everyone! Today we're talking about food. I hope you're not too hungry!",
     "questions": ["What is your favourite Vietnamese dish, and why?", "Can you cook? What can you make?", "Do you prefer eating at home or eating out?",
                   "Describe a meal you will never forget.", "What food from another country would you like to try?"]},
    {"id": "travel", "title": "Travel stories", "title_vi": "Chuyện du lịch", "level": "B1", "emoji": "✈️",
     "opener": "Welcome, travellers! Today we share travel stories. Remember to use the past simple.",
     "questions": ["Tell us about the best trip you have taken.", "Do you prefer the beach or the mountains? Why?", "What's something that went wrong on a trip?",
                   "Where would you go if money were no problem?", "Is it better to travel alone or in a group?"]},
    {"id": "technology", "title": "Technology in our lives", "title_vi": "Công nghệ trong cuộc sống", "level": "B1", "emoji": "📱",
     "opener": "Hi all! Today's topic is technology. Let's talk about how it changes our daily lives.",
     "questions": ["How many hours a day do you spend on your phone?", "Which app could you not live without?", "Has technology made people closer or more distant?",
                   "Should children have smartphones? At what age?", "What technology do you think will change the most in ten years?"]},
    {"id": "work", "title": "Work & career", "title_vi": "Công việc & sự nghiệp", "level": "B1", "emoji": "💼",
     "opener": "Good evening, professionals! Today we talk about work and careers.",
     "questions": ["What do you do, or what would you like to do?", "What makes a good boss?", "Would you rather work from home or in an office?",
                   "What skill would help you most in your career?", "Describe a challenge you solved at work or at school."]},
    {"id": "environment", "title": "Protecting the environment", "title_vi": "Bảo vệ môi trường", "level": "B2", "emoji": "🌱",
     "opener": "Welcome! Today we discuss the environment. Try to give reasons and examples for your opinions.",
     "questions": ["What is the biggest environmental problem in your city?", "Should plastic bags be banned completely?", "What do you personally do to reduce waste?",
                   "Is it the job of governments or individuals to protect the environment?", "Would you pay more for products that are better for the planet?"]},
    {"id": "education", "title": "Education & learning", "title_vi": "Giáo dục & học tập", "level": "B2", "emoji": "🎓",
     "opener": "Hello learners! Today's topic is education. A perfect topic for a learning club!",
     "questions": ["What was your favourite subject at school, and why?", "Is online learning as good as learning in a classroom?", "Should university be free for everyone?",
                   "What is the best way to learn a language, in your experience?", "What would you change about the school system?"]},
    {"id": "ielts-part3", "title": "IELTS Part 3 practice", "title_vi": "Luyện IELTS Speaking Part 3", "level": "B2", "emoji": "🎯",
     "opener": "Welcome to IELTS discussion practice. Give a clear opinion, a reason and an example in each answer.",
     "questions": ["Why do some people prefer living in big cities?", "How has the way people shop changed in recent years?", "Do you think advertising influences children too much?",
                   "What are the advantages of working for a large company?", "Will people read fewer books in the future?"]},
]
_TOPICS = {t["id"]: t for t in TOPICS}


class ClubError(ValueError):
    pass


def get_topic(topic_id: str) -> dict | None:
    return _TOPICS.get(topic_id)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _new_code(db: Session) -> str:
    for _ in range(20):
        code = "CLB-" + "".join(secrets.choice(CODE_ALPHABET) for _ in range(4))
        if not db.query(SpeakingRoom).filter(SpeakingRoom.code == code).first():
            return code
    raise ClubError("Không tạo được mã phòng, thử lại.")


def active_members(db: Session, room_id: str) -> list[RoomMember]:
    return (db.query(RoomMember).filter(RoomMember.room_id == room_id, RoomMember.left_at.is_(None))
            .order_by(RoomMember.joined_at, RoomMember.id).all())


def membership(db: Session, room_id: str, learner_id: str) -> RoomMember | None:
    return db.query(RoomMember).filter(RoomMember.room_id == room_id, RoomMember.learner_id == learner_id, RoomMember.left_at.is_(None)).first()


def add_message(db: Session, room: SpeakingRoom, role: str, text: str, learner_id: str | None = None, extra: dict | None = None) -> RoomMessage:
    seq = (db.query(func.max(RoomMessage.seq)).filter(RoomMessage.room_id == room.id).scalar() or 0) + 1
    msg = RoomMessage(room_id=room.id, seq=seq, role=role, text=text[:2000], learner_id=learner_id, extra=extra)
    db.add(msg)
    room.updated_at = _now()
    db.flush()
    return msg


def local_label(moment: datetime) -> str:
    """'19:30 · 28/10' in Vietnam time for a UTC-naive moment."""
    from app.core.timeutil import LEARNER_TZ
    return moment.replace(tzinfo=timezone.utc).astimezone(LEARNER_TZ).strftime("%H:%M · %d/%m")


def normalize_schedule(scheduled_at: datetime | None) -> datetime | None:
    """Aware or UTC-naive → UTC naive, validated against the booking window."""
    if scheduled_at is None:
        return None
    when = scheduled_at.astimezone(timezone.utc).replace(tzinfo=None) if scheduled_at.tzinfo else scheduled_at
    now = _now()
    if when < now + timedelta(minutes=SCHEDULE_MIN_LEAD_MIN):
        raise ClubError(f"Hãy hẹn giờ cách bây giờ ít nhất {SCHEDULE_MIN_LEAD_MIN} phút.")
    if when > now + timedelta(days=SCHEDULE_MAX_DAYS):
        raise ClubError(f"Chỉ hẹn trước tối đa {SCHEDULE_MAX_DAYS} ngày.")
    return when.replace(second=0, microsecond=0)


def create_room(db: Session, host: LearnerProfile, topic_id: str, is_public: bool = True, scheduled_at: datetime | None = None) -> SpeakingRoom:
    if not get_topic(topic_id):
        raise ClubError("Chủ đề không tồn tại.")
    when = normalize_schedule(scheduled_at)
    room = SpeakingRoom(code=_new_code(db), topic_id=topic_id, host_learner_id=host.id, is_public=1 if is_public else 0, scheduled_at=when)
    db.add(room)
    db.flush()
    db.add(RoomMember(room_id=room.id, learner_id=host.id))
    note = f" Hẹn bắt đầu lúc {local_label(when)}." if when else ""
    add_message(db, room, "system", f"{host.display_name} đã tạo phòng.{note}")
    return room


def join_room(db: Session, learner: LearnerProfile, code: str) -> SpeakingRoom:
    room = db.query(SpeakingRoom).filter(SpeakingRoom.code == (code or "").strip().upper()).first()
    if not room or room.status == ROOM_FINISHED:
        raise ClubError("Không tìm thấy phòng hoặc phòng đã kết thúc.")
    if membership(db, room.id, learner.id):
        return room
    if room.group_id:
        from app.models.group import GroupMember
        if not db.query(GroupMember).filter(GroupMember.group_id == room.group_id, GroupMember.learner_id == learner.id).first():
            raise ClubError("Phòng này dành cho thành viên của lớp.")
    if room.status != ROOM_WAITING:
        raise ClubError("Phòng đã bắt đầu, hãy chờ phòng sau hoặc tạo phòng mới.")
    if len(active_members(db, room.id)) >= MAX_MEMBERS:
        raise ClubError(f"Phòng đã đủ {MAX_MEMBERS} người.")
    old = db.query(RoomMember).filter(RoomMember.room_id == room.id, RoomMember.learner_id == learner.id).first()
    if old:
        old.left_at = None
        old.joined_at = _now()
    else:
        db.add(RoomMember(room_id=room.id, learner_id=learner.id))
    if room.host_learner_id is None:        # G12 · first person in a class session hosts it
        room.host_learner_id = learner.id
    add_message(db, room, "system", f"{learner.display_name} đã vào phòng.")
    return room


def current_speaker(db: Session, room: SpeakingRoom) -> RoomMember | None:
    if room.status != ROOM_ACTIVE:
        return None
    members = active_members(db, room.id)
    if not members:
        return None
    return members[room.turn_index % len(members)]


def _names(db: Session, ids: list[str]) -> dict[str, str]:
    return {p.id: p.display_name or "Học viên" for p in db.query(LearnerProfile).filter(LearnerProfile.id.in_(ids)).all()} if ids else {}


def next_question(room: SpeakingRoom) -> str:
    topic = get_topic(room.topic_id) or TOPICS[0]
    q = topic["questions"][room.question_index % len(topic["questions"])]
    room.question_index += 1
    return q


def total_turns(db: Session, room: SpeakingRoom) -> int:
    return TURNS_PER_MEMBER * max(1, len(active_members(db, room.id)))


def start_room(db: Session, room: SpeakingRoom, learner: LearnerProfile) -> None:
    if room.host_learner_id != learner.id:
        raise ClubError("Chỉ chủ phòng mới bắt đầu được.")
    if room.status != ROOM_WAITING:
        raise ClubError("Phòng đã bắt đầu.")
    if room.scheduled_at and _now() < room.scheduled_at - timedelta(minutes=EARLY_START_MIN):
        raise ClubError(f"Phòng hẹn lúc {local_label(room.scheduled_at)}; mở được trước {EARLY_START_MIN} phút.")
    members = active_members(db, room.id)
    if len(members) < 1:
        raise ClubError("Phòng chưa có ai.")
    topic = get_topic(room.topic_id)
    room.status = ROOM_ACTIVE
    room.started_at = _now()
    room.turn_index = 0
    first = members[0]
    name = _names(db, [first.learner_id]).get(first.learner_id, "bạn")
    add_message(db, room, "ai", f"{topic['opener']} {name}, {next_question(room)}", extra={"to_learner_id": first.learner_id})


def advance_turn(db: Session, room: SpeakingRoom, ai_text: str | None, extra: dict | None = None) -> None:
    """Move to the next member and post the AI's next prompt (or finish the session)."""
    room.turns_taken += 1
    members = active_members(db, room.id)
    if not members or room.turns_taken >= total_turns(db, room):
        room.status = ROOM_FINISHED
        room.finished_at = _now()
        closing = (ai_text + " " if ai_text else "") + "That's all for today. Great job, everyone — see you at the next club!"
        add_message(db, room, "ai", closing, extra={**(extra or {}), "closing": True})
        return
    room.turn_index = (room.turn_index + 1) % len(members)
    nxt = members[room.turn_index]
    name = _names(db, [nxt.learner_id]).get(nxt.learner_id, "bạn")
    text = ai_text or f"Thank you! {name}, {next_question(room)}"
    add_message(db, room, "ai", text, extra={**(extra or {}), "to_learner_id": nxt.learner_id})


def leave_room(db: Session, room: SpeakingRoom, learner: LearnerProfile) -> None:
    m = membership(db, room.id, learner.id)
    if not m:
        return
    was_speaker = (cs := current_speaker(db, room)) is not None and cs.learner_id == learner.id
    members_before = active_members(db, room.id)
    idx = next((i for i, x in enumerate(members_before) if x.learner_id == learner.id), 0)
    m.left_at = _now()
    db.flush()
    add_message(db, room, "system", f"{learner.display_name} đã rời phòng.")
    remaining = active_members(db, room.id)
    if not remaining:
        if room.group_id and room.status == ROOM_WAITING:
            room.host_learner_id = None     # a class session stays open for the rest of the class
            return
        room.status = ROOM_FINISHED
        room.finished_at = _now()
        return
    if room.host_learner_id == learner.id:
        room.host_learner_id = remaining[0].learner_id
    if room.status == ROOM_ACTIVE:
        # keep the turn on the same position; the person after the leaver now sits there
        if idx < room.turn_index:
            room.turn_index -= 1
        room.turn_index %= len(remaining)
        if was_speaker:
            nxt = remaining[room.turn_index]
            name = _names(db, [nxt.learner_id]).get(nxt.learner_id, "bạn")
            add_message(db, room, "ai", f"{name}, {next_question(room)}", extra={"to_learner_id": nxt.learner_id})


def lobby(db: Session) -> list[SpeakingRoom]:
    """Public rooms waiting right now (booked rooms join once their time is near)."""
    now = _now()
    since = now - timedelta(minutes=WAITING_ROOM_TTL_MIN)
    near = now + timedelta(minutes=EARLY_START_MIN)
    rooms = (db.query(SpeakingRoom).filter(SpeakingRoom.status == ROOM_WAITING, SpeakingRoom.is_public == 1)
             .filter(((SpeakingRoom.scheduled_at.is_(None)) & (SpeakingRoom.created_at >= since))
                     | ((SpeakingRoom.scheduled_at <= near) & (SpeakingRoom.scheduled_at >= now - timedelta(minutes=SCHEDULED_EXPIRE_MIN))))
             .order_by(SpeakingRoom.created_at.desc()).limit(20).all())
    return rooms


def upcoming(db: Session) -> list[SpeakingRoom]:
    """G11 · Public booked sessions later than the near window, soonest first."""
    near = _now() + timedelta(minutes=EARLY_START_MIN)
    return (db.query(SpeakingRoom).filter(SpeakingRoom.status == ROOM_WAITING, SpeakingRoom.is_public == 1, SpeakingRoom.scheduled_at > near)
            .order_by(SpeakingRoom.scheduled_at).limit(20).all())


def run_reminders(db: Session, now: datetime | None = None) -> dict:
    """G11 · Scheduler hook: remind members of booked rooms starting soon; close booked rooms nobody opened."""
    from app.models.user import User
    from app.services.notification_service import create_notification
    from app.services.reminders import ReminderMessage, push_to_learner, zalo_to_user

    now = now or _now()
    stats = {"rooms": 0, "reminded": 0, "push": 0, "expired": 0, "class_rooms": 0, "class_reminded": 0}
    try:
        stats["class_rooms"] = ensure_group_rooms(db, now)
    except Exception:
        import logging
        logging.getLogger("agen.club").exception("Creating class speaking-club rooms failed")
        db.rollback()
    soon = (db.query(SpeakingRoom).filter(SpeakingRoom.status == ROOM_WAITING, SpeakingRoom.scheduled_at.isnot(None),
                                          SpeakingRoom.scheduled_at > now - timedelta(minutes=5),
                                          SpeakingRoom.scheduled_at <= now + timedelta(minutes=REMIND_WINDOW_MIN)).all())
    for room in soon:
        topic = get_topic(room.topic_id) or TOPICS[0]
        mins = max(0, round((room.scheduled_at - now).total_seconds() / 60))
        message = ReminderMessage(title=f"Câu lạc bộ nói {('sau ' + str(mins) + ' phút') if mins else 'bắt đầu ngay'} 🎙️",
                                  body=f"{topic['emoji']} {topic['title_vi']} lúc {local_label(room.scheduled_at)}. Vào phòng {room.code} để nói cùng mọi người.",
                                  url=f"/club/{room.id}")
        stats["rooms"] += 1
        for m in active_members(db, room.id):
            if m.reminded_at:
                continue
            learner = db.query(LearnerProfile).filter(LearnerProfile.id == m.learner_id).first()
            if not learner:
                continue
            create_notification(db, learner.id, type="club_reminder", title=message.title, body=message.body, icon="🎙️")
            try:
                stats["push"] += push_to_learner(db, learner, message)
                user = db.query(User).filter(User.id == learner.user_id).first()
                if user:
                    zalo_to_user(db, user, message)
            except Exception:  # a broken push channel must not block the others
                import logging
                logging.getLogger("agen.club").warning("Club reminder push failed", exc_info=True)
            m.reminded_at = now
            stats["reminded"] += 1
        if room.group_id and room.group_reminded_at is None:
            # G12 · class session: also nudge classmates who have not registered yet (in-app only)
            joined = {m.learner_id for m in active_members(db, room.id)}
            from app.models.group import GroupMember
            for (lid,) in db.query(GroupMember.learner_id).filter(GroupMember.group_id == room.group_id).all():
                if lid not in joined:
                    create_notification(db, lid, type="club_reminder", title=message.title, body=message.body, icon="🎙️")
                    stats["class_reminded"] += 1
            room.group_reminded_at = now
    stale = (db.query(SpeakingRoom).filter(SpeakingRoom.status == ROOM_WAITING, SpeakingRoom.scheduled_at.isnot(None),
                                           SpeakingRoom.scheduled_at < now - timedelta(minutes=SCHEDULED_EXPIRE_MIN)).all())
    for room in stale:
        room.status = ROOM_FINISHED
        room.finished_at = now
        stats["expired"] += 1
    db.commit()
    return stats


def fallback_reply(transcript: str) -> dict:
    words = len(transcript.split())
    tip = "Câu trả lời khá đầy đủ, thử thêm một ví dụ cụ thể nhé." if words >= 15 else "Hãy nói dài hơn một chút: nêu ý kiến + lý do + ví dụ."
    return {"feedback_vi": tip, "corrected": "", "reply": ""}



# ── G12 · Lịch câu lạc bộ nói hằng tuần của lớp ──────────────────────────────
WEEKDAYS_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ nhật"]
SCHEDULE_MIN_LEAD_FOR_ROOM_MIN = 15      # inside this window the next occurrence is the one a week later


def parse_time(value: str) -> tuple[int, int]:
    try:
        hh, mm = value.strip().split(":")
        h, m = int(hh), int(mm)
    except (ValueError, AttributeError):
        raise ClubError("Giờ phải có dạng HH:MM.")
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ClubError("Giờ phải có dạng HH:MM.")
    return h, m


def next_occurrence(schedule: GroupClubSchedule, now: datetime | None = None) -> datetime:
    """Next weekly slot (UTC naive) at least SCHEDULE_MIN_LEAD_FOR_ROOM_MIN minutes away."""
    from app.core.timeutil import LEARNER_TZ

    now = now or _now()
    h, m = parse_time(schedule.time_local)
    local_now = now.replace(tzinfo=timezone.utc).astimezone(LEARNER_TZ)
    days = (schedule.weekday - local_now.weekday()) % 7
    candidate = (local_now + timedelta(days=days)).replace(hour=h, minute=m, second=0, microsecond=0)
    if candidate <= local_now + timedelta(minutes=SCHEDULE_MIN_LEAD_FOR_ROOM_MIN):
        candidate += timedelta(days=7)
    return candidate.astimezone(timezone.utc).replace(tzinfo=None)


def schedule_label(schedule: GroupClubSchedule) -> str:
    return f"{WEEKDAYS_VI[schedule.weekday]} {schedule.time_local}"


def _topic_for(db: Session, schedule: GroupClubSchedule) -> str:
    if schedule.topic_id and get_topic(schedule.topic_id):
        return schedule.topic_id
    held = db.query(SpeakingRoom).filter(SpeakingRoom.schedule_id == schedule.id).count()
    return TOPICS[held % len(TOPICS)]["id"]


def ensure_group_rooms(db: Session, now: datetime | None = None) -> int:
    """Make sure every active weekly slot has a room for its next occurrence; tell the class when one opens."""
    from app.models.group import Group, GroupMember
    from app.services.notification_service import create_notification

    now = now or _now()
    created = 0
    for sch in db.query(GroupClubSchedule).filter(GroupClubSchedule.is_active == 1).all():
        when = next_occurrence(sch, now)
        exists = db.query(SpeakingRoom).filter(SpeakingRoom.schedule_id == sch.id, SpeakingRoom.scheduled_at == when).first()
        if exists:
            continue
        group = db.query(Group).filter(Group.id == sch.group_id).first()
        if not group:
            continue
        topic_id = _topic_for(db, sch)
        room = SpeakingRoom(code=_new_code(db), topic_id=topic_id, host_learner_id=None, is_public=0, scheduled_at=when,
                            group_id=group.id, schedule_id=sch.id)
        db.add(room)
        db.flush()
        topic = get_topic(topic_id) or TOPICS[0]
        add_message(db, room, "system", f"Buổi nói hằng tuần của {group.name} · hẹn lúc {local_label(when)}.")
        for (lid,) in db.query(GroupMember.learner_id).filter(GroupMember.group_id == group.id).all():
            create_notification(db, lid, type="club_scheduled", title=f"{group.name}: câu lạc bộ nói {local_label(when)}",
                                body=f"{topic['emoji']} {topic['title_vi']}. Mở Câu lạc bộ nói để đăng ký, bạn sẽ được nhắc trước 15 phút.", icon="🎙️")
        created += 1
    if created:
        db.commit()
    return created


def create_schedule(db: Session, group, user, weekday: int, time_local: str, topic_id: str | None = None) -> GroupClubSchedule:
    if not 0 <= weekday <= 6:
        raise ClubError("Ngày trong tuần không hợp lệ.")
    h, m = parse_time(time_local)
    if topic_id and not get_topic(topic_id):
        raise ClubError("Chủ đề không tồn tại.")
    if db.query(GroupClubSchedule).filter(GroupClubSchedule.group_id == group.id, GroupClubSchedule.is_active == 1).count() >= 7:
        raise ClubError("Mỗi lớp tối đa 7 buổi nói mỗi tuần.")
    sch = GroupClubSchedule(group_id=group.id, weekday=weekday, time_local=f"{h:02d}:{m:02d}", topic_id=topic_id or None, created_by_user_id=user.id)
    db.add(sch)
    db.flush()
    return sch


def cancel_schedule(db: Session, sch: GroupClubSchedule) -> int:
    """Stop a weekly slot and close its upcoming rooms that nobody has started."""
    sch.is_active = 0
    closed = 0
    for room in db.query(SpeakingRoom).filter(SpeakingRoom.schedule_id == sch.id, SpeakingRoom.status == ROOM_WAITING).all():
        add_message(db, room, "system", "Giáo viên đã huỷ lịch buổi nói này.")
        room.status = ROOM_FINISHED
        room.finished_at = _now()
        closed += 1
    return closed


def group_upcoming_rooms(db: Session, group_ids: list[str]) -> list[SpeakingRoom]:
    if not group_ids:
        return []
    return (db.query(SpeakingRoom).filter(SpeakingRoom.group_id.in_(group_ids), SpeakingRoom.status == ROOM_WAITING,
                                          SpeakingRoom.scheduled_at >= _now() - timedelta(minutes=SCHEDULED_EXPIRE_MIN))
            .order_by(SpeakingRoom.scheduled_at).limit(20).all())
