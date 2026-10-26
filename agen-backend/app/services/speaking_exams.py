"""
G9 · Thi thử Speaking theo định dạng thật.

IELTS Speaking: Part 1 (câu hỏi quen thuộc), Part 2 (cue card: 1 phút chuẩn bị,
nói 1–2 phút), Part 3 (thảo luận). TOEIC Speaking: Q1–2 đọc to, Q5–7 trả lời
câu hỏi, Q11 nêu ý kiến. Each task says how long to prepare and to speak; the
web app records the learner with the microphone and sends the transcript. The
band comes from the LLM (`speaking_exam_evaluation`) with a word-count /
pace heuristic as the fallback so an attempt always ends with a result.
"""
from __future__ import annotations

from copy import deepcopy

EXAM_IELTS = "ielts"
EXAM_TOEIC = "toeic"

XP_PER_TASK = 6
XP_CAP = 40
GEMS_GOOD = 8            # ≥ band 6.0 / ≥ 130
FREE_DAILY_ATTEMPTS = 1


def _q(tid: str, part: str, prompt: str, answer_seconds: int, prep_seconds: int = 0, tip_vi: str = "", kind: str = "question", reference: str | None = None, cue: list[str] | None = None) -> dict:
    return {"id": tid, "part": part, "kind": kind, "prompt": prompt, "prep_seconds": prep_seconds, "answer_seconds": answer_seconds, "tip_vi": tip_vi, "reference": reference, "cue": cue or []}


EXAMS: list[dict] = [
    {
        "id": "ielts-speaking-1", "exam": EXAM_IELTS, "minutes": 12,
        "title": "IELTS Speaking · Mini Test 1",
        "description": "Part 1 (3 câu hỏi quen thuộc), Part 2 (cue card: 1 phút chuẩn bị, nói 1–2 phút), Part 3 (2 câu thảo luận). Giám khảo AI đọc câu hỏi, bạn trả lời bằng micro.",
        "tasks": [
            _q("t1", "Part 1", "Let's talk about your hometown. Where is it, and what do you like about living there?", 40, tip_vi="Trả lời 2–3 câu: ở đâu, có gì đặc biệt, bạn thích điểm gì."),
            _q("t2", "Part 1", "Do you prefer studying in the morning or in the evening? Why?", 40, tip_vi="Nêu lựa chọn rồi giải thích lý do bằng 'because' / 'so that'."),
            _q("t3", "Part 1", "What kind of music do you usually listen to?", 40, tip_vi="Thể loại, khi nào nghe, cảm giác thế nào."),
            _q("t4", "Part 2", "Describe a skill you learned that has been useful to you.", 120, prep_seconds=60, kind="cue_card",
               cue=["what the skill is", "how you learned it", "when you use it", "and explain why it has been useful to you"],
               tip_vi="Dùng đủ 4 gợi ý trên thẻ, nối ý bằng 'Firstly… After that… What's more… That's why…'."),
            _q("t5", "Part 3", "Do you think schools should teach more practical skills? Why or why not?", 60, tip_vi="Nêu quan điểm, 1–2 lý do, 1 ví dụ cụ thể."),
            _q("t6", "Part 3", "How has technology changed the way people learn new skills?", 60, tip_vi="So sánh trước đây và bây giờ: 'In the past… whereas nowadays…'."),
        ],
    },
    {
        "id": "toeic-speaking-1", "exam": EXAM_TOEIC, "minutes": 10,
        "title": "TOEIC Speaking · Mini Test 1",
        "description": "Q1–2 đọc to đoạn văn (chấm phát âm), Q5–7 trả lời câu hỏi, Q11 nêu ý kiến — bối cảnh công sở như đề thật.",
        "tasks": [
            _q("t1", "Q1 · Read aloud", "Read the text aloud.", 45, prep_seconds=45, kind="read_aloud",
               reference="Thank you for calling Harbor City Dental. Our office is open Monday through Friday, from eight in the morning until six in the evening. To schedule an appointment, press one. To speak with a member of our staff, please stay on the line.",
               tip_vi="Đọc rõ, ngắt ở dấu phẩy, lên giọng cuối câu hỏi, nhấn các từ chính."),
            _q("t2", "Q2 · Read aloud", "Read the text aloud.", 45, prep_seconds=45, kind="read_aloud",
               reference="Attention, shoppers. For the next thirty minutes, all winter jackets, scarves, and gloves on the second floor are twenty percent off. Visit our customer service desk for a free gift with any purchase over fifty dollars.",
               tip_vi="Liệt kê 'jackets, scarves, and gloves' lên giọng ở hai từ đầu, xuống giọng ở từ cuối."),
            _q("t5", "Q5 · Respond to questions", "Imagine that a market research firm is doing a survey about eating habits. How often do you eat out, and where do you usually go?", 15, prep_seconds=3, tip_vi="Trả lời ngay, 1–2 câu, không cần suy nghĩ lâu."),
            _q("t6", "Q6 · Respond to questions", "What is the most important thing for you when choosing a restaurant: the price, the food, or the location?", 15, prep_seconds=3, tip_vi="Chọn một và nói lý do thật ngắn."),
            _q("t7", "Q7 · Respond to questions", "Some people prefer to cook at home rather than eat at restaurants. What are the advantages of cooking at home?", 30, prep_seconds=3, tip_vi="Nêu 2 lợi ích, mỗi lợi ích một câu giải thích."),
            _q("t11", "Q11 · Express an opinion", "Do you agree or disagree with the following statement? Employees should be allowed to work from home at least two days a week. Give reasons or examples to support your opinion.", 60, prep_seconds=45, kind="opinion",
               tip_vi="Mở bài nêu quan điểm, 2 lý do có ví dụ, kết lại bằng 'For these reasons…'."),
        ],
    },
]

_BY_ID = {e["id"]: e for e in EXAMS}


def list_exams() -> list[dict]:
    return EXAMS


def get_exam(exam_id: str) -> dict | None:
    return _BY_ID.get(exam_id)


def public_exam(exam: dict) -> dict:
    return deepcopy(exam)


def task_count(exam: dict) -> int:
    return len(exam["tasks"])


def _words(text: str) -> int:
    return len([w for w in (text or "").split() if w.strip()])


def heuristic_estimate(exam: dict, responses: list[dict]) -> dict:
    """Band from how much was said and how fast — only when the LLM is unavailable."""
    by_task = {r["task_id"]: r for r in responses}
    total_words = 0
    expected_words = 0
    answered = 0
    for t in exam["tasks"]:
        r = by_task.get(t["id"])
        words = _words(r.get("transcript", "")) if r else 0
        total_words += words
        expected_words += int(t["answer_seconds"] * 2)      # ~120 words/minute at a comfortable pace
        answered += 1 if words >= 5 else 0
    ratio = min(1.0, total_words / expected_words) if expected_words else 0.0
    coverage = answered / max(1, len(exam["tasks"]))
    score01 = 0.6 * ratio + 0.4 * coverage
    if exam["exam"] == EXAM_IELTS:
        band = round((3.0 + score01 * 4.0) * 2) / 2            # 3.0 … 7.0
        criteria = {k: band for k in ("fluency_coherence", "lexical_resource", "grammatical_range", "pronunciation")}
    else:
        band = float(int((40 + score01 * 120) / 10) * 10)      # 40 … 160
        criteria = {k: round(score01 * 5) for k in ("pronunciation", "intonation", "grammar", "vocabulary", "cohesion", "content")}
    return {
        "exam": exam["exam"], "overall": band, "criteria": criteria,
        "task_feedback": [{"task_id": t["id"], "comment_vi": "Chưa chấm chi tiết được lúc này — bản ước tính dựa trên độ dài câu trả lời.", "corrections": []} for t in exam["tasks"]],
        "strengths": ["Bạn đã hoàn thành " + str(answered) + "/" + str(len(exam["tasks"])) + " phần."],
        "improvements": ["Nói đủ thời gian cho mỗi câu, mỗi ý nên có một câu giải thích."],
        "next_band_tips": ["Luyện Part 2 / Q11 với đồng hồ để quen nói liền 1–2 phút."],
    }


def xp_for(responses: list[dict]) -> int:
    return min(XP_CAP, sum(XP_PER_TASK for r in responses if _words(r.get("transcript", "")) >= 5))


def good_score(exam: str, overall: float) -> bool:
    return overall >= (6.0 if exam == EXAM_IELTS else 130)
