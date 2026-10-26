"""
G11 · Sinh tập podcast học tiếng Anh bằng AI.

Output follows `services/media_library.EPISODES` (bilingual lines, key words,
comprehension questions). Admin reviews every draft before learners see it.
"""
from __future__ import annotations

from app.agents.contracts import PodcastEpisodeOutput
from app.services.llm_client import get_llm_response, parse_and_validate

_LENGTH = {"A2": "9–12 short lines, simple present/past, everyday words", "B1": "10–14 lines, some linking words and opinions",
           "B2": "12–16 lines, natural idioms and reasons/contrast", "C1": "12–18 lines, nuanced vocabulary and longer turns"}


def generate_episode(level: str = "B1", topic: str = "", style: str = "conversation", seed: int = 0) -> dict:
    shape = ("a natural conversation between two or three named people (Vietnamese or international names)"
             if style == "conversation" else "a short podcast talk by one host (speaker \"Host\") with one guest question in the middle")
    focus = f"Topic: {topic}." if topic else "Pick a fresh, useful everyday, study or workplace topic that Vietnamese learners care about."
    prompt = f"""You write short English listening episodes for Vietnamese learners at CEFR {level}. {focus} Variation seed: {seed}.

The episode is {shape}; {_LENGTH.get(level, _LENGTH["B1"])}. Each line has the English "text" and a natural Vietnamese translation "vi".
Choose 4–6 useful words or phrases that appear verbatim in the text for "vocab" (definition in Vietnamese, short).
Write 4–5 multiple-choice comprehension questions in English, 3 options each; "answer" is the 0-based index of the correct option;
every answer must be supported by the text; "explanation_vi" quotes the evidence in one Vietnamese sentence.
No brand names, no stereotypes, no sensitive topics.

Return ONLY JSON:
{{
  "title": "<short English title>",
  "title_vi": "<tên tiếng Việt>",
  "description_vi": "<1–2 câu tiếng Việt: học được gì từ tập này>",
  "topic": "<chủ đề ngắn tiếng Việt, ví dụ Du lịch>",
  "lines": [{{"speaker": "Lan", "text": "...", "vi": "..."}}],
  "vocab": [{{"word": "...", "definition": "..."}}],
  "questions": [{{"prompt": "...", "options": ["...", "...", "..."], "answer": 1, "explanation_vi": "..."}}]
}}"""
    raw = get_llm_response(prompt)
    return parse_and_validate(raw, PodcastEpisodeOutput)
