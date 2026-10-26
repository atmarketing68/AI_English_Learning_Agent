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
from app.models.speaking_club import ROOM_ACTIVE, ROOM_FINISHED, ROOM_WAITING, RoomMember, RoomMessage, SpeakingRoom

MAX_MEMBERS = 4
TURNS_PER_MEMBER = 3
XP_PER_TURN = 5
WAITING_ROOM_TTL_MIN = 60          # waiting rooms older than this drop out of the lobby
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


def create_room(db: Session, host: LearnerProfile, topic_id: str, is_public: bool = True) -> SpeakingRoom:
    if not get_topic(topic_id):
        raise ClubError("Chủ đề không tồn tại.")
    room = SpeakingRoom(code=_new_code(db), topic_id=topic_id, host_learner_id=host.id, is_public=1 if is_public else 0)
    db.add(room)
    db.flush()
    db.add(RoomMember(room_id=room.id, learner_id=host.id))
    add_message(db, room, "system", f"{host.display_name} đã tạo phòng.")
    return room


def join_room(db: Session, learner: LearnerProfile, code: str) -> SpeakingRoom:
    room = db.query(SpeakingRoom).filter(SpeakingRoom.code == (code or "").strip().upper()).first()
    if not room or room.status == ROOM_FINISHED:
        raise ClubError("Không tìm thấy phòng hoặc phòng đã kết thúc.")
    if membership(db, room.id, learner.id):
        return room
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
    since = _now() - timedelta(minutes=WAITING_ROOM_TTL_MIN)
    return (db.query(SpeakingRoom).filter(SpeakingRoom.status == ROOM_WAITING, SpeakingRoom.is_public == 1, SpeakingRoom.created_at >= since)
            .order_by(SpeakingRoom.created_at.desc()).limit(20).all())


def fallback_reply(transcript: str) -> dict:
    words = len(transcript.split())
    tip = "Câu trả lời khá đầy đủ, thử thêm một ví dụ cụ thể nhé." if words >= 15 else "Hãy nói dài hơn một chút: nêu ý kiến + lý do + ví dụ."
    return {"feedback_vi": tip, "corrected": "", "reply": ""}
