"""
G13 · Content Factory cho đề thi thử Speaking: AI sinh bản nháp, admin duyệt, học viên mới thấy.

`normalize_exam` reshapes the agent output into the exact shape of
`speaking_exams.EXAMS` (task ids, real-exam timings decided here, not by the
model) and refuses tests that do not follow the format. Approved rows are
merged into the catalogue by `speaking_exams.list_exams(db)` under ids "gen-<uuid>".
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agents.orchestrator import AgentRequest, execute
from app.models.generated_exam import STATUS_APPROVED, STATUS_DRAFT, STATUS_REJECTED, GeneratedSpeakingExam
from app.services.speaking_exams import EXAM_IELTS, EXAM_TOEIC, _q


class SpeakingExamGenerationError(RuntimeError):
    pass


def _clean(text) -> str:
    return " ".join(str(text or "").split())


def _ielts_tasks(raw: list[dict]) -> list[dict]:
    part1 = [t for t in raw if t.get("kind") != "cue_card" and _clean(t.get("part")).lower().startswith("part 1")]
    cards = [t for t in raw if t.get("kind") == "cue_card" or _clean(t.get("part")).lower().startswith("part 2")]
    part3 = [t for t in raw if t.get("kind") != "cue_card" and _clean(t.get("part")).lower().startswith("part 3")]
    if len(part1) < 2 or not cards or not part3:
        raise SpeakingExamGenerationError("Đề IELTS cần ít nhất 2 câu Part 1, 1 cue card Part 2 và 1 câu Part 3.")
    card = cards[0]
    cue = [_clean(c) for c in card.get("cue") or [] if _clean(c)]
    if len(cue) < 3:
        raise SpeakingExamGenerationError("Cue card Part 2 cần 3–4 gợi ý.")
    tasks = [_q("", "Part 1", _clean(t["prompt"]), 40, tip_vi=_clean(t.get("tip_vi"))) for t in part1[:4]]
    tasks.append(_q("", "Part 2", _clean(card["prompt"]), 120, prep_seconds=60, kind="cue_card", cue=cue[:4], tip_vi=_clean(card.get("tip_vi"))))
    tasks += [_q("", "Part 3", _clean(t["prompt"]), 60, tip_vi=_clean(t.get("tip_vi"))) for t in part3[:3]]
    return tasks


def _toeic_tasks(raw: list[dict]) -> list[dict]:
    reads = [t for t in raw if t.get("kind") == "read_aloud"]
    questions = [t for t in raw if t.get("kind") in ("question", "cue_card")]
    opinions = [t for t in raw if t.get("kind") == "opinion"]
    if not reads or len(questions) < 2 or not opinions:
        raise SpeakingExamGenerationError("Đề TOEIC cần đoạn đọc to, ít nhất 2 câu trả lời câu hỏi và 1 câu nêu ý kiến.")
    tasks = []
    for i, t in enumerate(reads[:2], start=1):
        ref = _clean(t.get("reference"))
        if len(ref.split()) < 20:
            raise SpeakingExamGenerationError(f"Đoạn đọc to Q{i} quá ngắn.")
        tasks.append(_q("", f"Q{i} · Read aloud", "Read the text aloud.", 45, prep_seconds=45, kind="read_aloud", reference=ref, tip_vi=_clean(t.get("tip_vi"))))
    for i, t in enumerate(questions[:3]):
        tasks.append(_q("", f"Q{5 + i} · Respond to questions", _clean(t["prompt"]), 30 if i == 2 else 15, prep_seconds=3, tip_vi=_clean(t.get("tip_vi"))))
    t = opinions[0]
    tasks.append(_q("", "Q11 · Express an opinion", _clean(t["prompt"]), 60, prep_seconds=45, kind="opinion", tip_vi=_clean(t.get("tip_vi"))))
    return tasks


def normalize_exam(exam: str, data: dict) -> dict:
    """Validate and reshape an agent test; raises SpeakingExamGenerationError when the format is off."""
    raw = [t for t in data.get("tasks", []) if _clean(t.get("prompt"))]
    tasks = _ielts_tasks(raw) if exam == EXAM_IELTS else _toeic_tasks(raw)
    for i, t in enumerate(tasks, start=1):
        t["id"] = f"t{i}"
        if not t["tip_vi"]:
            t["tip_vi"] = "Trả lời đủ ý, nói liền mạch đến hết thời gian."
    return {
        "exam": exam, "title": _clean(data["title"])[:140], "description": _clean(data["description"]),
        "minutes": 12 if exam == EXAM_IELTS else 10, "tasks": tasks,
    }


def generate_draft(db: Session, exam: str, topic: str = "", level: str = "B1", auto_approve: bool = False) -> GeneratedSpeakingExam:
    """One LLM call → one GeneratedSpeakingExam row (draft unless auto_approve). Caller commits."""
    if exam not in (EXAM_IELTS, EXAM_TOEIC):
        raise SpeakingExamGenerationError("Chỉ sinh được đề IELTS hoặc TOEIC Speaking.")
    seed = db.query(GeneratedSpeakingExam).filter(GeneratedSpeakingExam.exam == exam).count() + 1
    result = execute(AgentRequest(agent="speaking_exam_generation", payload={"exam": exam, "topic": topic, "level": level, "seed": seed}))
    if result.status != "succeeded" or not result.data:
        raise SpeakingExamGenerationError(result.error or "Không sinh được đề.")
    content = normalize_exam(exam, result.data)
    row = GeneratedSpeakingExam(
        exam=exam, title=content["title"], topic=topic[:120] or None, content=content, tasks=len(content["tasks"]),
        eval_score=result.eval_score, eval_flagged=bool(result.eval_flagged),
        status=STATUS_APPROVED if auto_approve else STATUS_DRAFT,
        approved_at=datetime.now(timezone.utc).replace(tzinfo=None) if auto_approve else None,
    )
    db.add(row)
    db.flush()
    return row


def set_status(db: Session, row: GeneratedSpeakingExam, status: str) -> GeneratedSpeakingExam:
    if status not in (STATUS_APPROVED, STATUS_DRAFT, STATUS_REJECTED):
        raise SpeakingExamGenerationError("Trạng thái không hợp lệ.")
    row.status = status
    row.approved_at = datetime.now(timezone.utc).replace(tzinfo=None) if status == STATUS_APPROVED else None
    return row


def public_id(row: GeneratedSpeakingExam) -> str:
    return f"gen-{row.id}"


def _as_exam(row: GeneratedSpeakingExam) -> dict:
    exam = dict(row.content)
    exam["id"] = public_id(row)
    return exam


def approved_exams(db: Session) -> list[dict]:
    rows = db.query(GeneratedSpeakingExam).filter(GeneratedSpeakingExam.status == STATUS_APPROVED).order_by(GeneratedSpeakingExam.approved_at).all()
    return [_as_exam(r) for r in rows]


def exam_by_public_id(db: Session, exam_id: str) -> dict | None:
    if not exam_id.startswith("gen-"):
        return None
    row = db.query(GeneratedSpeakingExam).filter(GeneratedSpeakingExam.id == exam_id[4:], GeneratedSpeakingExam.status == STATUS_APPROVED).first()
    return _as_exam(row) if row else None
