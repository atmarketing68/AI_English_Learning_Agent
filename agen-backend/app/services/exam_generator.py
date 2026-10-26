"""
G9 · Content Factory cho đề thi thử: AI sinh bản nháp, admin duyệt, học viên mới thấy.

`normalize_paper` turns the validated agent output into the exact shape of
`mock_exams.EXAMS` (ids, fixed TFNG options, answer bounds) and refuses papers
that would not grade correctly. Approved rows are merged into the catalogue by
`mock_exams.list_exams(db)` under ids "gen-<uuid>".
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agents.orchestrator import AgentRequest, execute
from app.models.generated_exam import STATUS_APPROVED, STATUS_DRAFT, STATUS_REJECTED, GeneratedExam

TFNG = ["TRUE", "FALSE", "NOT GIVEN"]
MIN_QUESTIONS = 8


class ExamGenerationError(RuntimeError):
    pass


def normalize_paper(exam: str, skill: str, data: dict) -> dict:
    """Validate and reshape an agent paper; raises ExamGenerationError on anything that would not grade."""
    sections = []
    qn = 0
    for si, sec in enumerate(data.get("sections", []), start=1):
        questions = []
        for q in sec.get("questions", []):
            qn += 1
            qtype = q["type"]
            item = {"id": f"q{qn}", "type": qtype, "prompt": q["prompt"].strip(), "explanation_vi": q.get("explanation_vi", "").strip() or "Xem lại đoạn tương ứng."}
            if qtype == "gap":
                answers = q["answer"] if isinstance(q["answer"], list) else [str(q["answer"])]
                answers = [str(a).strip() for a in answers if str(a).strip()]
                if not answers:
                    raise ExamGenerationError(f"Câu {qn}: thiếu đáp án điền từ.")
                item["answer"] = answers
            else:
                options = [str(o).strip() for o in (q.get("options") or []) if str(o).strip()]
                if qtype == "tfng":
                    options = TFNG
                if len(options) < 3:
                    raise ExamGenerationError(f"Câu {qn}: cần ít nhất 3 lựa chọn.")
                try:
                    answer = int(q["answer"])
                except (TypeError, ValueError):
                    raise ExamGenerationError(f"Câu {qn}: đáp án trắc nghiệm phải là chỉ số.")
                if not 0 <= answer < len(options):
                    raise ExamGenerationError(f"Câu {qn}: chỉ số đáp án ngoài phạm vi.")
                item["options"] = options
                item["answer"] = answer
            if q.get("audio"):
                item["audio"] = [_line(l) for l in q["audio"]]
            questions.append(item)
        if not questions:
            continue
        section = {"id": f"s{si}", "title": sec["title"].strip(), "instructions": sec["instructions"].strip(), "questions": questions}
        if sec.get("audio"):
            section["audio"] = [_line(l) for l in sec["audio"]]
        if sec.get("passage"):
            section["passage"] = sec["passage"].strip()
        if sec.get("per_question_audio"):
            section["per_question_audio"] = True
        if skill == "listening" and not section.get("audio") and not all(q.get("audio") for q in questions):
            raise ExamGenerationError(f"Phần {si}: đề nghe thiếu lời thoại.")
        if skill == "reading" and not section.get("passage") and si > 1:
            # Part 5 (TOEIC) has no passage; everything else must
            if not all(q["type"] == "mc" and len(q["options"]) == 4 for q in questions):
                raise ExamGenerationError(f"Phần {si}: đề đọc thiếu bài đọc.")
        sections.append(section)
    if qn < MIN_QUESTIONS:
        raise ExamGenerationError(f"Đề chỉ có {qn} câu (tối thiểu {MIN_QUESTIONS}).")
    return {
        "exam": exam, "skill": skill, "title": data["title"].strip()[:140], "description": data["description"].strip(),
        "minutes": int(data.get("minutes") or 12), "sections": sections,
    }


def _line(l: dict) -> dict:
    speaker = str(l.get("speaker", "Woman")).strip()[:40] or "Woman"
    male = speaker.lower() in ("man", "male", "boy", "mr", "tom", "david", "ben", "mark", "peter", "james", "narrator")
    return {"speaker": speaker, "text": str(l.get("text", "")).strip(), "voice": "male" if male else "female"}


def generate_exam_draft(db: Session, exam: str, skill: str, topic: str = "", level: str = "B1", auto_approve: bool = False) -> GeneratedExam:
    """One LLM call → one GeneratedExam row (draft unless auto_approve). Caller commits."""
    if exam not in ("ielts", "toeic") or skill not in ("listening", "reading"):
        raise ExamGenerationError("Chỉ sinh được đề IELTS/TOEIC Listening hoặc Reading.")
    seed = db.query(GeneratedExam).filter(GeneratedExam.exam == exam, GeneratedExam.skill == skill).count() + 1
    result = execute(AgentRequest(agent="exam_generation", payload={"exam": exam, "skill": skill, "topic": topic, "level": level, "seed": seed}))
    if result.status != "succeeded" or not result.data:
        raise ExamGenerationError(result.error or "Không sinh được đề.")
    paper = normalize_paper(exam, skill, result.data)
    row = GeneratedExam(
        exam=exam, skill=skill, title=paper["title"], topic=topic[:120] or None, content=paper,
        questions=sum(len(s["questions"]) for s in paper["sections"]),
        eval_score=result.eval_score, eval_flagged=bool(result.eval_flagged),
        status=STATUS_APPROVED if auto_approve else STATUS_DRAFT,
        approved_at=datetime.now(timezone.utc).replace(tzinfo=None) if auto_approve else None,
    )
    db.add(row)
    db.flush()
    return row


def set_status(db: Session, row: GeneratedExam, status: str) -> GeneratedExam:
    if status not in (STATUS_APPROVED, STATUS_DRAFT, STATUS_REJECTED):
        raise ExamGenerationError("Trạng thái không hợp lệ.")
    row.status = status
    row.approved_at = datetime.now(timezone.utc).replace(tzinfo=None) if status == STATUS_APPROVED else None
    return row


def public_id(row: GeneratedExam) -> str:
    return f"gen-{row.id}"


def approved_papers(db: Session) -> list[dict]:
    rows = db.query(GeneratedExam).filter(GeneratedExam.status == STATUS_APPROVED).order_by(GeneratedExam.approved_at).all()
    out = []
    for r in rows:
        paper = dict(r.content)
        paper["id"] = public_id(r)
        out.append(paper)
    return out


def paper_by_public_id(db: Session, exam_id: str) -> dict | None:
    if not exam_id.startswith("gen-"):
        return None
    row = db.query(GeneratedExam).filter(GeneratedExam.id == exam_id[4:], GeneratedExam.status == STATUS_APPROVED).first()
    if not row:
        return None
    paper = dict(row.content)
    paper["id"] = public_id(row)
    return paper
