"""
G2 · Tra từ nhanh khi bấm vào một từ trong transcript bài nghe.

One small LLM call per distinct (word, level), cached in-process. Any failure
raises LLMError / ValueError for the API layer to translate; the client then
shows "không tra được" and still offers to save the word.
"""
from __future__ import annotations

import re

from app.agents.contracts import WordLookupOutput
from app.services.llm_cache import ai_cache
from app.services.llm_client import get_llm_response, parse_and_validate


def clean_word(raw: str) -> str:
    """Strip punctuation around a tapped token; keep inner apostrophes/hyphens."""
    word = re.sub(r"^[^A-Za-z0-9']+|[^A-Za-z0-9']+$", "", (raw or "").strip())
    return word[:40].lower()


@ai_cache(maxsize=5000)
def lookup_word(word: str, context: str = "", level: str = "A2") -> dict:
    prompt = f"""You are a bilingual English–Vietnamese dictionary for a Vietnamese CEFR {level} learner.
Word: "{word}"
Context sentence (may be empty): "{context[:200]}"

Explain the word AS USED in the context (if given). Return ONLY JSON:
{{
  "word": "{word}",
  "phonetic": "IPA, e.g. /ˈwɔːtə/",
  "part_of_speech": "noun | verb | adjective | ...",
  "meaning_vi": "nghĩa tiếng Việt ngắn gọn, phù hợp ngữ cảnh",
  "definition_en": "simple English definition (max 15 words)",
  "example": "one short natural example sentence"
}}"""
    raw = get_llm_response(prompt)
    return parse_and_validate(raw, WordLookupOutput)
