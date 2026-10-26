"""
G9 · Sinh đề thi thử IELTS / TOEIC (Listening hoặc Reading) bằng AI.

The output follows the schema of `services/mock_exams.EXAMS` so an approved
paper is served exactly like a hand-written one. Admin reviews drafts first.
"""
from __future__ import annotations

from app.agents.contracts import GeneratedExamOutput
from app.services.llm_client import get_llm_response, parse_and_validate

_FORMATS = {
    ("ielts", "listening"): """Three sections like the real test, 10 questions in total:
- Section 1: an everyday two-person conversation (booking, enquiry); 5 "gap" questions (form/notes completion, NO MORE THAN TWO WORDS AND/OR A NUMBER; every answer must appear verbatim in the audio).
- Section 2: a monologue (tour, announcement, talk); 3 "mc" questions with 3 options.
- Section 3: an academic discussion between two students or student and tutor; 2 "mc" questions with 3 options.
Each section has "audio": a list of lines [{"speaker": "Woman"|"Man"|"Receptionist"|<name>, "text": "..."}], 120–220 words per section, natural spoken English.""",
    ("ielts", "reading"): """One academic passage of 330–420 words (4 paragraphs, factual, neutral tone, a real-world topic) in "passage", then 12 questions:
- 5 "tfng" (options exactly ["TRUE","FALSE","NOT GIVEN"]; at least one of each),
- 4 "gap" (sentence completion, ONE WORD from the passage; the answer must appear verbatim in the passage),
- 3 "mc" with 3 options.""",
    ("toeic", "listening"): """Three parts, 10 questions in total, workplace settings:
- Part 2 Question–Response: 4 questions; each question has its own "audio" (one line with the question, then three lines "A. …", "B. …", "C. …" spoken by another voice) and "options" = the three responses; mark the section "per_question_audio": true; prompt = "Listen and choose the best response."
- Part 3 Conversation: one 6–8 line conversation in the section "audio" and 3 "mc" questions with 3 options.
- Part 4 Short talk: one 90–130 word talk (announcement, voicemail, briefing) in the section "audio" and 3 "mc" questions with 3 options.""",
    ("toeic", "reading"): """Three parts, 13 questions in total, business English:
- Part 5 Incomplete Sentences: 6 "mc" questions, 4 options each (grammar/vocabulary: tense, preposition, word form, connector).
- Part 6 Text Completion: one e-mail or notice in "passage" with three numbered blanks ___(7)___ ___(8)___ ___(9)___ and 3 "mc" questions (prompt "(7)" etc.) with 4 options.
- Part 7 Reading Comprehension: two short related documents in "passage" (a notice and an e-mail, separated by a line "— — —") and 4 "mc" questions with 3 options.""",
}


def generate_exam(exam: str, skill: str, topic: str = "", level: str = "B1", seed: int = 0) -> dict:
    fmt = _FORMATS.get((exam, skill))
    if not fmt:
        raise ValueError("Unsupported exam/skill")
    focus = f"Theme to build the content around: {topic}." if topic else "Pick a fresh everyday or workplace theme."
    prompt = f"""You write {exam.upper()} {skill} mini mock tests for Vietnamese learners around CEFR {level}. {focus} Variation seed: {seed}.

Format (follow exactly): {fmt}

Rules: every question must be answerable from the audio/passage only; distractors plausible; British or American spelling consistent; no cultural stereotypes; numbers spelled the way they are said in audio. "explanation_vi" is a one-sentence Vietnamese explanation quoting the evidence.

Return ONLY JSON:
{{
  "title": "{exam.upper()} {skill.capitalize()} · <short theme>",
  "description": "1–2 câu tiếng Việt mô tả đề",
  "minutes": <10–15>,
  "sections": [
    {{
      "title": "Section 1 · <theme>",
      "instructions": "<exam-style instructions in English>",
      "audio": [{{"speaker": "Woman", "text": "..."}}],          // listening only (omit for reading)
      "passage": "...",                                           // reading only (omit for listening)
      "per_question_audio": false,
      "questions": [
        {{"type": "gap", "prompt": "Name: Laura ______", "answer": ["Mitchell"], "explanation_vi": "..."}},
        {{"type": "mc", "prompt": "...", "options": ["...", "...", "..."], "answer": 0, "explanation_vi": "...",
          "audio": [{{"speaker": "Man", "text": "..."}}]}},       // only for Part 2 question–response items
        {{"type": "tfng", "prompt": "...", "options": ["TRUE", "FALSE", "NOT GIVEN"], "answer": 2, "explanation_vi": "..."}}
      ]
    }}
  ]
}}"""
    raw = get_llm_response(prompt)
    return parse_and_validate(raw, GeneratedExamOutput)
