"""
G11 · Content Factory cho podcast: AI sinh bản nháp, admin duyệt, học viên mới thấy.

`normalize_episode` reshapes the validated agent output into the exact shape of
`media_library.EPISODES` (question ids, answer bounds, vocab that really occurs
in the transcript). Approved rows are merged into the library by
`media_library.list_episodes(db)` under ids "gen-<uuid>". An admin can attach a
YouTube clip whose speech matches the transcript; the episode then shows as video.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agents.orchestrator import AgentRequest, execute
from app.models.generated_episode import STATUS_APPROVED, STATUS_DRAFT, STATUS_REJECTED, GeneratedEpisode

LEVELS = ("A2", "B1", "B2", "C1")
WORDS_PER_MINUTE = 120
YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_YT_PATTERNS = (re.compile(r"(?:v=|/embed/|youtu\.be/|/shorts/|/live/)([A-Za-z0-9_-]{11})"),)


class PodcastGenerationError(RuntimeError):
    pass


def normalize_episode(data: dict, level: str) -> dict:
    """Validate and reshape an agent episode; raises PodcastGenerationError when it would not work in the player."""
    lines = []
    for l in data.get("lines", []):
        text, vi = str(l.get("text", "")).strip(), str(l.get("vi", "")).strip()
        if text:
            lines.append({"speaker": (str(l.get("speaker", "")).strip() or "Host")[:40], "text": text, "vi": vi or "—"})
    if len(lines) < 6:
        raise PodcastGenerationError("Lời thoại quá ngắn (cần ít nhất 6 câu).")
    transcript = " ".join(l["text"] for l in lines).lower()
    vocab = [{"word": str(v["word"]).strip(), "definition": str(v["definition"]).strip()}
             for v in data.get("vocab", []) if str(v.get("word", "")).strip().lower() in transcript]
    questions = []
    for i, q in enumerate(data.get("questions", []), start=1):
        options = [str(o).strip() for o in q.get("options", []) if str(o).strip()]
        if len(options) < 3:
            raise PodcastGenerationError(f"Câu {i}: cần ít nhất 3 lựa chọn.")
        if len(set(o.lower() for o in options)) != len(options):
            raise PodcastGenerationError(f"Câu {i}: có lựa chọn trùng nhau.")
        try:
            answer = int(q["answer"])
        except (KeyError, TypeError, ValueError):
            raise PodcastGenerationError(f"Câu {i}: đáp án phải là chỉ số.")
        if not 0 <= answer < len(options):
            raise PodcastGenerationError(f"Câu {i}: chỉ số đáp án ngoài phạm vi.")
        questions.append({"id": f"q{i}", "prompt": str(q["prompt"]).strip(), "options": options, "answer": answer,
                          "explanation_vi": str(q.get("explanation_vi", "")).strip() or "Nghe lại đoạn tương ứng."})
    if len(questions) < 3:
        raise PodcastGenerationError("Cần ít nhất 3 câu hỏi.")
    words = len(transcript.split())
    return {
        "kind": "podcast", "level": level, "minutes": max(2, min(8, round(words / WORDS_PER_MINUTE) + 1)),
        "topic": str(data.get("topic", "")).strip()[:40] or "Đời sống",
        "title": str(data.get("title", "")).strip()[:80], "title_vi": str(data.get("title_vi", "")).strip()[:100],
        "description_vi": str(data.get("description_vi", "")).strip()[:300],
        "youtube_id": None, "lines": lines, "vocab": vocab, "questions": questions,
    }


def generate_episode_draft(db: Session, level: str = "B1", topic: str = "", style: str = "conversation", auto_approve: bool = False,
                           auto: bool = False) -> GeneratedEpisode:
    """One LLM call → one GeneratedEpisode row (draft unless auto_approve). Caller commits."""
    if level not in LEVELS:
        raise PodcastGenerationError("Trình độ không hợp lệ.")
    seed = db.query(GeneratedEpisode).filter(GeneratedEpisode.level == level).count() + 1
    result = execute(AgentRequest(agent="podcast_generation", payload={"level": level, "topic": topic, "style": style, "seed": seed}))
    if result.status != "succeeded" or not result.data:
        raise PodcastGenerationError(result.error or "Không sinh được tập podcast.")
    episode = normalize_episode(result.data, level)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    row = GeneratedEpisode(level=level, topic=topic[:120] or None, title=episode["title"] or "Untitled", content=episode, auto=auto,
                           eval_score=result.eval_score, eval_flagged=bool(result.eval_flagged),
                           status=STATUS_APPROVED if auto_approve else STATUS_DRAFT, approved_at=now if auto_approve else None)
    db.add(row)
    db.flush()
    return row


def set_status(row: GeneratedEpisode, status: str) -> GeneratedEpisode:
    if status not in (STATUS_APPROVED, STATUS_DRAFT, STATUS_REJECTED):
        raise PodcastGenerationError("Trạng thái không hợp lệ.")
    row.status = status
    row.approved_at = datetime.now(timezone.utc).replace(tzinfo=None) if status == STATUS_APPROVED else None
    return row


def parse_youtube(value: str | None) -> str | None:
    """Accept a bare 11-char id or any common YouTube URL; None clears; raises on anything else."""
    value = (value or "").strip()
    if not value:
        return None
    if YOUTUBE_ID.match(value):
        return value
    for pattern in _YT_PATTERNS:
        m = pattern.search(value)
        if m:
            return m.group(1)
    raise PodcastGenerationError("Link YouTube không hợp lệ.")


def set_video(row: GeneratedEpisode, youtube: str | None, start: int | None = None, end: int | None = None) -> GeneratedEpisode:
    vid = parse_youtube(youtube)
    if start is not None and start < 0 or end is not None and end < 0:
        raise PodcastGenerationError("Thời điểm bắt đầu/kết thúc không hợp lệ.")
    if start is not None and end is not None and end <= start:
        raise PodcastGenerationError("Thời điểm kết thúc phải sau thời điểm bắt đầu.")
    row.youtube_id = vid
    row.video_start = start if vid else None
    row.video_end = end if vid else None
    return row


def public_id(row: GeneratedEpisode) -> str:
    return f"gen-{row.id}"


def as_episode(row: GeneratedEpisode) -> dict:
    ep = dict(row.content)
    ep["id"] = public_id(row)
    if row.youtube_id:
        ep.update(kind="video", youtube_id=row.youtube_id, start=row.video_start, end=row.video_end)
    return ep


def approved_episodes(db: Session) -> list[dict]:
    rows = db.query(GeneratedEpisode).filter(GeneratedEpisode.status == STATUS_APPROVED).order_by(GeneratedEpisode.approved_at.desc()).all()
    return [as_episode(r) for r in rows]


def episode_by_public_id(db: Session, episode_id: str) -> dict | None:
    if not episode_id.startswith("gen-"):
        return None
    row = db.query(GeneratedEpisode).filter(GeneratedEpisode.id == episode_id[4:], GeneratedEpisode.status == STATUS_APPROVED).first()
    return as_episode(row) if row else None


# ── G12 · Bản nháp tự động theo lịch ─────────────────────────────────────────
AUTO_TOPICS = [
    "ordering food delivery", "a job interview", "planning a weekend trip", "healthy habits", "learning a new skill online",
    "renting an apartment", "a day at the office", "shopping for clothes", "protecting the environment", "using public transport",
    "a family celebration", "talking to a doctor", "working from a café", "social media habits", "saving money",
    "a volunteer project", "Tet holiday traditions", "a customer complaint", "choosing a university course", "a team meeting",
]
AUTO_SPACING_HOURS = 20          # at most one new auto draft per level per ~day


def auto_levels() -> list[str]:
    from app.core.config import settings
    return [l.strip().upper() for l in settings.PODCAST_AUTO_LEVELS.split(",") if l.strip().upper() in LEVELS]


def run_auto_drafts(db: Session, now: datetime | None = None, max_new: int = 1) -> dict:
    """Content Factory hook: top up the review queue to PODCAST_AUTO_DRAFTS drafts per level.

    At most `max_new` AI calls per run and one draft per level every ~20 hours, so the AI quota stays
    free for learners. Drafts still need an admin to approve them. Never raises.
    """
    import logging

    from app.core.config import settings

    target = settings.PODCAST_AUTO_DRAFTS
    out = {"enabled": target > 0, "created": [], "errors": 0}
    if target <= 0:
        return out
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    from datetime import timedelta
    attempts = 0
    for level in auto_levels():
        if attempts >= max_new:           # failed calls count too: one AI call per run keeps the quota for learners
            break
        pending = db.query(GeneratedEpisode).filter(GeneratedEpisode.level == level, GeneratedEpisode.status == STATUS_DRAFT).count()
        if pending >= target:
            continue
        recent = (db.query(GeneratedEpisode).filter(GeneratedEpisode.level == level, GeneratedEpisode.auto.is_(True),
                                                    GeneratedEpisode.created_at >= now - timedelta(hours=AUTO_SPACING_HOURS)).count())
        if recent:
            continue
        made = db.query(GeneratedEpisode).filter(GeneratedEpisode.level == level).count()
        topic = AUTO_TOPICS[(made + LEVELS.index(level) * 7) % len(AUTO_TOPICS)]
        style = "talk" if made % 3 == 2 else "conversation"
        attempts += 1
        try:
            row = generate_episode_draft(db, level, topic, style, auto=True)
            db.commit()
            out["created"].append({"id": row.id, "level": level, "title": row.title})
        except Exception:
            db.rollback()
            out["errors"] += 1
            logging.getLogger("agen.podcast").warning("Auto podcast draft failed for %s", level, exc_info=True)
    if out["created"]:
        _email_admins_new_drafts(out["created"])
    return out


def _email_admins_new_drafts(created: list[dict]) -> None:
    """Tell admins there is something to review (only when e-mail is configured)."""
    import html

    from app.core.config import settings
    from app.services.reminders import deliver_email

    if not settings.email_enabled or not settings.admin_emails_list:
        return
    items = "".join(f"<li>{html.escape(c['level'])} · {html.escape(c['title'])}</li>" for c in created)
    body = (f"<div style=\"font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:520px;margin:0 auto;padding:24px;color:#1d1d1f\">"
            f"<p style=\"font-size:13px;color:#86868b\">AI AGENT ENGLISH · quản trị</p><h1 style=\"font-size:20px\">Có tập podcast mới chờ duyệt</h1>"
            f"<ul>{items}</ul><p><a href=\"{html.escape(settings.app_url)}/admin\">Mở /admin → Podcast AI để nghe thử và duyệt</a></p></div>")
    text = "Có tập podcast mới chờ duyệt:\n" + "\n".join(f"- {c['level']} · {c['title']}" for c in created) + f"\n{settings.app_url}/admin"
    for email in settings.admin_emails_list:
        deliver_email(email, "Podcast mới chờ duyệt", body, text)
