"""G10 · Câu lạc bộ nói: lobby, create/join a room, poll its state, speak your turn, skip, leave."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.orchestrator import AgentRequest, execute
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.speaking_club import ROOM_ACTIVE, ROOM_FINISHED, RoomMember, RoomMessage, SpeakingRoom
from app.models.user import User
from app.services import speaking_club as club
from app.services.shop import avatar_of
from app.services.streak_service import record_activity
from app.services.trace_recorder import record_agent_trace

router = APIRouter(prefix="/club", tags=["Speaking club"])


class TopicOut(BaseModel):
    id: str
    title: str
    title_vi: str
    level: str
    emoji: str


class RoomCard(BaseModel):
    id: str
    code: str
    topic: TopicOut
    status: str
    members: int
    host_name: str
    created_at: datetime


class LobbyOut(BaseModel):
    topics: list[TopicOut]
    open_rooms: list[RoomCard]
    my_rooms: list[RoomCard]
    max_members: int


class MemberOut(BaseModel):
    learner_id: str
    name: str
    avatar: dict
    turns: int
    words: int
    is_host: bool
    is_me: bool


class MessageOut(BaseModel):
    seq: int
    role: str
    learner_id: Optional[str]
    name: Optional[str]
    text: str
    feedback_vi: Optional[str] = None
    corrected: Optional[str] = None
    to_learner_id: Optional[str] = None
    created_at: datetime


class RoomState(BaseModel):
    id: str
    code: str
    topic: TopicOut
    status: str
    members: list[MemberOut]
    messages: list[MessageOut]
    current_speaker_id: Optional[str]
    is_my_turn: bool
    is_host: bool
    turns_taken: int
    total_turns: int
    last_seq: int


class CreateIn(BaseModel):
    topic_id: str = Field(min_length=1, max_length=40)
    is_public: bool = True


class JoinIn(BaseModel):
    code: str = Field(min_length=4, max_length=12)


class SpeakIn(BaseModel):
    transcript: str = Field(min_length=1, max_length=2000)
    duration_seconds: Optional[float] = Field(default=None, ge=0, le=600)


def _learner(db: Session, user: User) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found")
    return learner


def _topic_out(topic_id: str) -> TopicOut:
    t = club.get_topic(topic_id) or club.TOPICS[0]
    return TopicOut(id=t["id"], title=t["title"], title_vi=t["title_vi"], level=t["level"], emoji=t["emoji"])


def _card(db: Session, room: SpeakingRoom) -> RoomCard:
    host = db.query(LearnerProfile).filter(LearnerProfile.id == room.host_learner_id).first()
    return RoomCard(id=room.id, code=room.code, topic=_topic_out(room.topic_id), status=room.status, members=len(club.active_members(db, room.id)),
                    host_name=(host.display_name if host else None) or "Học viên", created_at=room.created_at)


def _room_or_404(db: Session, room_id: str) -> SpeakingRoom:
    room = db.query(SpeakingRoom).filter(SpeakingRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng.")
    return room


def _state(db: Session, room: SpeakingRoom, learner: LearnerProfile, after: int = 0) -> RoomState:
    members = club.active_members(db, room.id)
    ids = [m.learner_id for m in members]
    msgs = db.query(RoomMessage).filter(RoomMessage.room_id == room.id, RoomMessage.seq > after).order_by(RoomMessage.seq).limit(200).all()
    ids += [m.learner_id for m in msgs if m.learner_id]
    profiles = {p.id: p for p in db.query(LearnerProfile).filter(LearnerProfile.id.in_(set(ids))).all()} if ids else {}
    speaker = club.current_speaker(db, room)
    last_seq = db.query(RoomMessage.seq).filter(RoomMessage.room_id == room.id).order_by(RoomMessage.seq.desc()).limit(1).scalar() or 0
    return RoomState(
        id=room.id, code=room.code, topic=_topic_out(room.topic_id), status=room.status,
        members=[MemberOut(learner_id=m.learner_id, name=(profiles[m.learner_id].display_name if m.learner_id in profiles else "Học viên"),
                           avatar=avatar_of(profiles[m.learner_id]) if m.learner_id in profiles else {}, turns=m.turns, words=m.words,
                           is_host=m.learner_id == room.host_learner_id, is_me=m.learner_id == learner.id) for m in members],
        messages=[MessageOut(seq=m.seq, role=m.role, learner_id=m.learner_id, name=(profiles[m.learner_id].display_name if m.learner_id in profiles else None),
                             text=m.text, feedback_vi=(m.extra or {}).get("feedback_vi"), corrected=(m.extra or {}).get("corrected") or None,
                             to_learner_id=(m.extra or {}).get("to_learner_id"), created_at=m.created_at) for m in msgs],
        current_speaker_id=speaker.learner_id if speaker else None, is_my_turn=bool(speaker and speaker.learner_id == learner.id),
        is_host=room.host_learner_id == learner.id, turns_taken=room.turns_taken, total_turns=club.total_turns(db, room) if room.status != ROOM_FINISHED else room.turns_taken,
        last_seq=last_seq,
    )


@router.get("", response_model=LobbyOut)
def lobby(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    mine = (db.query(SpeakingRoom).join(RoomMember, RoomMember.room_id == SpeakingRoom.id)
            .filter(RoomMember.learner_id == learner.id, RoomMember.left_at.is_(None), SpeakingRoom.status != ROOM_FINISHED)
            .order_by(SpeakingRoom.created_at.desc()).limit(5).all())
    mine_ids = {r.id for r in mine}
    return LobbyOut(topics=[_topic_out(t["id"]) for t in club.TOPICS],
                    open_rooms=[_card(db, r) for r in club.lobby(db) if r.id not in mine_ids],
                    my_rooms=[_card(db, r) for r in mine], max_members=club.MAX_MEMBERS)


@router.post("/rooms", response_model=RoomState)
def create(payload: CreateIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    try:
        room = club.create_room(db, learner, payload.topic_id, payload.is_public)
    except club.ClubError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return _state(db, room, learner)


@router.post("/rooms/join", response_model=RoomState)
def join(payload: JoinIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    try:
        room = club.join_room(db, learner, payload.code)
    except club.ClubError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return _state(db, room, learner)


@router.get("/rooms/{room_id}", response_model=RoomState)
def state(room_id: str, after: int = 0, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    room = _room_or_404(db, room_id)
    if not club.membership(db, room.id, learner.id) and room.status != ROOM_FINISHED:
        raise HTTPException(status_code=403, detail="Bạn chưa ở trong phòng này.")
    return _state(db, room, learner, after)


@router.post("/rooms/{room_id}/start", response_model=RoomState)
def start(room_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    room = _room_or_404(db, room_id)
    try:
        club.start_room(db, room, learner)
    except club.ClubError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return _state(db, room, learner)


@router.post("/rooms/{room_id}/speak", response_model=RoomState)
def speak(room_id: str, payload: SpeakIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    room = _room_or_404(db, room_id)
    if room.status != ROOM_ACTIVE:
        raise HTTPException(status_code=400, detail="Phòng chưa bắt đầu hoặc đã kết thúc.")
    speaker = club.current_speaker(db, room)
    if not speaker or speaker.learner_id != learner.id:
        raise HTTPException(status_code=409, detail="Chưa đến lượt bạn.")
    text = payload.transcript.strip()
    words = len(text.split())
    club.add_message(db, room, "learner", text, learner_id=learner.id)
    speaker.turns += 1
    speaker.words += words
    xp = club.XP_PER_TURN if words >= 3 else 0
    speaker.xp_earned += xp
    learner.total_xp = (learner.total_xp or 0) + xp
    db.add(LearningEvent(learner_id=learner.id, event_type="club_turn", skill="speaking", topic=club.get_topic(room.topic_id)["title"], activity_type="speaking_club",
                         correct=words >= 5, xp_earned=xp, duration_seconds=payload.duration_seconds, extra_data={"room_id": room.id, "words": words}))
    record_activity(learner, "speaking", db)

    # Who speaks next (for the AI's question) — same rule as advance_turn.
    members = club.active_members(db, room.id)
    last_turn = room.turns_taken + 1 >= club.total_turns(db, room)
    nxt = members[(room.turn_index + 1) % len(members)]
    nxt_name = (db.query(LearnerProfile.display_name).filter(LearnerProfile.id == nxt.learner_id).scalar() or "bạn")
    topic = club.get_topic(room.topic_id)
    last_msgs = db.query(RoomMessage).filter(RoomMessage.room_id == room.id, RoomMessage.role != "system").order_by(RoomMessage.seq.desc()).limit(6).all()[::-1]
    names = {p.id: p.display_name for p in db.query(LearnerProfile).filter(LearnerProfile.id.in_({m.learner_id for m in last_msgs if m.learner_id})).all()}
    recent = [{"who": "Host" if m.role == "ai" else names.get(m.learner_id, "Member"), "text": m.text} for m in last_msgs]
    hint = topic["questions"][room.question_index % len(topic["questions"])]
    result = execute(AgentRequest(agent="club_moderator", payload={
        "topic": topic["title"], "speaker_name": learner.display_name or "Learner", "transcript": text,
        "next_name": nxt_name, "recent": recent, "level": learner.overall_level or "B1", "next_question_hint": hint,
    }))
    record_agent_trace(db, learner.id, result.trace_id, result, {"room": room.id})
    data = result.data if result.status == "succeeded" else club.fallback_reply(text)
    feedback = {"feedback_vi": data.get("feedback_vi"), "corrected": data.get("corrected") or ""}
    # attach the tip to the learner's own message so everyone sees it under that turn
    mine = db.query(RoomMessage).filter(RoomMessage.room_id == room.id, RoomMessage.learner_id == learner.id).order_by(RoomMessage.seq.desc()).first()
    mine.extra = feedback
    reply = (data.get("reply") or "").strip()
    if reply and result.status == "succeeded" and not last_turn:
        room.question_index += 1        # the AI used (or replaced) the hinted question
    club.advance_turn(db, room, reply or None)
    db.commit()
    return _state(db, room, learner)


@router.post("/rooms/{room_id}/skip", response_model=RoomState)
def skip(room_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The current speaker passes (no microphone, shy…), or the host moves things along."""
    learner = _learner(db, current_user)
    room = _room_or_404(db, room_id)
    speaker = club.current_speaker(db, room)
    if room.status != ROOM_ACTIVE or not speaker:
        raise HTTPException(status_code=400, detail="Phòng chưa bắt đầu hoặc đã kết thúc.")
    if learner.id not in (speaker.learner_id, room.host_learner_id):
        raise HTTPException(status_code=403, detail="Chỉ người đang nói hoặc chủ phòng mới bỏ lượt được.")
    club.add_message(db, room, "system", "Bỏ qua lượt này.")
    club.advance_turn(db, room, None)
    db.commit()
    return _state(db, room, learner)


@router.post("/rooms/{room_id}/leave", response_model=LobbyOut)
def leave(room_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    room = _room_or_404(db, room_id)
    club.leave_room(db, room, learner)
    db.commit()
    return lobby(current_user, db)
