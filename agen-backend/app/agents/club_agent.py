"""
G10 · AI người dẫn câu lạc bộ nói.

Given the topic, the last few turns and what the current member just said,
returns: a one-line Vietnamese tip, a corrected version of their sentence (if
needed), and the host's next line — a short reaction plus a question for the
next member by name.
"""
from __future__ import annotations

from app.agents.contracts import ClubModeratorOutput
from app.services.llm_client import get_llm_response, parse_and_validate


def moderate_turn(topic: str, speaker_name: str, transcript: str, next_name: str, recent: list[dict] | None = None, level: str = "B1", next_question_hint: str = "") -> dict:
    convo = "\n".join(f"{m['who']}: {m['text'][:300]}" for m in (recent or [])[-6:])
    prompt = f"""You are the friendly host of an English speaking club for Vietnamese learners (around CEFR {level}).
Topic: {topic}

Recent conversation:
{convo or "(start)"}

{speaker_name} just said (speech recognition, ignore punctuation): "{transcript[:800]}"

Return ONLY JSON:
{{
  "feedback_vi": "one short, encouraging tip in Vietnamese for {speaker_name} (max 25 words) — grammar, word choice or how to extend the answer",
  "corrected": "a natural corrected version of their main sentence, or empty string if it was already fine",
  "reply": "your next line in simple English (max 35 words): react briefly to what {speaker_name} said, then ask {next_name} a question that keeps the topic going (you may use: {next_question_hint})"
}}"""
    raw = get_llm_response(prompt)
    return parse_and_validate(raw, ClubModeratorOutput)
