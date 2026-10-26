"""
G8 · Bo — chatbot hỏi đáp ngữ pháp bằng tiếng Việt.

One LLM call per question with the last few turns as context. The output is a
short explanation in Vietnamese, example sentences with translations and the
rule in one line, validated by `TutorAnswerOutput`. The API layer keeps the
learning flow alive with a canned answer when the LLM is unavailable.
"""
from __future__ import annotations

from app.agents.contracts import TutorAnswerOutput
from app.services.llm_client import get_llm_response, parse_and_validate

MAX_HISTORY = 6
MAX_QUESTION_CHARS = 600


def answer_question(question: str, history: list[dict] | None = None, level: str = "A2", age: int | None = None) -> dict:
    history = (history or [])[-MAX_HISTORY:]
    tone = "Người học là trẻ em; dùng câu ngắn, ví dụ gần gũi (trường lớp, gia đình, trò chơi)." if age and age < 16 else "Người học là người lớn; giải thích gọn, chuyên nghiệp, ví dụ đời sống/công việc."
    convo = "\n".join(f"{'Học viên' if m['role'] == 'user' else 'Bo'}: {m['content'][:400]}" for m in history)
    prompt = f"""Bạn là Bo, trợ lý ngữ pháp tiếng Anh thân thiện của ứng dụng AI AGENT ENGLISH dành cho người Việt.
Trình độ học viên: CEFR {level}. {tone}
Chỉ trả lời câu hỏi về tiếng Anh (ngữ pháp, từ vựng, cách dùng, phát âm, cách diễn đạt). Nếu câu hỏi không liên quan đến tiếng Anh, lịch sự nói rằng Bo chỉ giúp về tiếng Anh và gợi ý một câu hỏi phù hợp.

Hội thoại trước đó (có thể trống):
{convo or "(không có)"}

Câu hỏi mới của học viên: "{question.strip()[:MAX_QUESTION_CHARS]}"

Trả lời bằng TIẾNG VIỆT, dễ hiểu, không dài dòng (tối đa ~120 từ cho phần answer_vi). Trả về CHỈ JSON đúng cấu trúc:
{{
  "answer_vi": "giải thích ngắn gọn bằng tiếng Việt, có thể xuống dòng bằng \\n",
  "rule": "quy tắc tóm tắt trong một câu (tiếng Việt), hoặc chuỗi rỗng nếu không có quy tắc",
  "examples": [{{"en": "câu ví dụ tiếng Anh", "vi": "nghĩa tiếng Việt"}}],
  "common_mistake": "lỗi người Việt hay mắc liên quan (tiếng Việt), hoặc chuỗi rỗng",
  "follow_ups": ["2-3 câu hỏi tiếp theo học viên có thể hỏi (tiếng Việt)"],
  "on_topic": true
}}
Cho 2–3 ví dụ. Dùng tiếng Anh tự nhiên, đúng trình độ {level}."""
    raw = get_llm_response(prompt)
    data = parse_and_validate(raw, TutorAnswerOutput)
    return data


def fallback_answer(question: str) -> dict:
    """Keeps the chat usable when the LLM is down or over quota."""
    return {
        "answer_vi": "Bo đang bận một chút, chưa trả lời được ngay. Bạn thử lại sau vài phút nhé. Trong lúc chờ, bạn có thể xem phần \"Vì sao sai?\" trong bài học hoặc tra từ trong Sổ từ vựng.",
        "rule": "",
        "examples": [],
        "common_mistake": "",
        "follow_ups": ["Khi nào dùng thì hiện tại hoàn thành?", "Phân biệt 'a' và 'the'?", "'Make' và 'do' khác nhau thế nào?"],
        "on_topic": True,
    }


def history_payload(messages: list) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in messages]

