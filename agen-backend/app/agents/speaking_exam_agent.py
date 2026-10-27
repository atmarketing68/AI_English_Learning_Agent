"""
G9 · Giám khảo AI cho thi thử Speaking.

One LLM call per finished attempt: all task transcripts in, an IELTS band
(0–9 by the four public criteria) or a TOEIC Speaking scaled score (0–200)
out, with Vietnamese feedback per task and corrected sentences.
"""
from __future__ import annotations

from app.agents.contracts import GeneratedSpeakingExamOutput, SpeakingExamEvaluationOutput
from app.services.llm_client import get_llm_response, parse_and_validate


def _rubric(exam: str) -> str:
    if exam == "ielts":
        return """Score as an IELTS Speaking examiner using the public band descriptors (0–9 in 0.5 steps):
"criteria": {"fluency_coherence": 6.0, "lexical_resource": 5.5, "grammatical_range": 6.0, "pronunciation": 6.0}.
Pronunciation can only be judged from the transcript (word choice, self-corrections, read-aloud accuracy where given), so keep it within 0.5 of the other criteria unless the pronunciation score given for a read-aloud task says otherwise.
"overall" = mean of the four rounded to the nearest 0.5 (round .25 up). Short or missing answers lower fluency and the overall band."""
    return """Score as an ETS TOEIC Speaking rater. Rate each criterion 0–5: "criteria": {"pronunciation": 4, "intonation": 3, "grammar": 4, "vocabulary": 3, "cohesion": 3, "content": 4}
(read-aloud tasks weigh pronunciation/intonation — use the pronunciation score given for them; respond-to-question tasks weigh content/relevance; the opinion task weighs cohesion and development).
Map the average to the TOEIC Speaking scaled score 0–200 (5 → 200, 4 → 160, 3 → 120, 2 → 80, 1 → 40, 0 → 0, interpolate) as "overall"."""


def evaluate_speaking_exam(exam: str, tasks: list[dict], responses: list[dict], level: str = "B1") -> dict:
    by_task = {r["task_id"]: r for r in responses}
    lines = []
    for t in tasks:
        r = by_task.get(t["id"], {})
        transcript = (r.get("transcript") or "").strip() or "(no answer)"
        extra = ""
        if t.get("reference"):
            extra = f"\n  Reference text: {t['reference']}"
            if r.get("pronunciation") is not None:
                extra += f"\n  Pronunciation score from the speech scorer: {r['pronunciation']}/100"
        dur = f" ({int(r['duration'])}s)" if r.get("duration") else ""
        lines.append(f"- {t['part']} [{t['id']}] Prompt: {t['prompt']}{extra}\n  Learner said{dur}: \"{transcript[:1200]}\"")
    prompt = f"""You are the examiner of a {exam.upper()} Speaking mock test for a Vietnamese learner (CEFR {level}).
The learner's answers were transcribed by speech recognition, so ignore punctuation and treat obvious recognition slips kindly.

{chr(10).join(lines)}

{_rubric(exam)}

Return ONLY JSON:
{{
  "exam": "{exam}",
  "overall": <number>,
  "criteria": {{...}},
  "task_feedback": [{{"task_id": "t1", "comment_vi": "nhận xét ngắn bằng tiếng Việt về câu trả lời này", "corrections": [{{"original": "câu học viên nói", "corrected": "câu tự nhiên hơn"}}]}}],
  "strengths": ["2 điểm mạnh (tiếng Việt)"],
  "improvements": ["2-3 điểm cần cải thiện (tiếng Việt)"],
  "next_band_tips": ["2-3 việc cụ thể để lên band/điểm tiếp theo (tiếng Việt)"]
}}
One task_feedback entry per task, in order; at most 2 corrections per task; keep every Vietnamese comment under 40 words."""
    raw = get_llm_response(prompt)
    return parse_and_validate(raw, SpeakingExamEvaluationOutput)


# ── G13 · Sinh đề Speaking mới (admin duyệt trước khi phát hành) ──────────────
_GEN_FORMATS = {
    "ielts": """Exactly 6 tasks like the real test:
- 3 tasks with "part": "Part 1", "kind": "question": everyday questions on ONE familiar topic (home, study, work, hobbies…).
- 1 task "part": "Part 2", "kind": "cue_card": "prompt" = "Describe …", "cue" = exactly 4 bullet points ("what …", "when …", "how …", "and explain why …").
- 2 tasks "part": "Part 3", "kind": "question": abstract discussion questions linked to the Part 2 theme.""",
    "toeic": """Exactly 6 tasks like the real test, workplace or daily-life settings:
- 2 tasks "part": "Q1 · Read aloud" / "Q2 · Read aloud", "kind": "read_aloud", "prompt": "Read the text aloud.", "reference" = a 40–60 word announcement, voicemail or advertisement with a list of three items.
- 3 tasks "part": "Q5 · Respond to questions" / "Q6 · …" / "Q7 · …", "kind": "question": one survey-style scenario ("Imagine that …") and three related questions.
- 1 task "part": "Q11 · Express an opinion", "kind": "opinion": an agree/disagree or preference statement ending with 'Give reasons or examples to support your opinion.'""",
}


def generate_speaking_exam(exam: str, topic: str = "", level: str = "B1", seed: int = 0) -> dict:
    fmt = _GEN_FORMATS.get(exam)
    if not fmt:
        raise ValueError("Unsupported exam")
    focus = f"Theme: {topic}." if topic else "Pick a fresh everyday theme."
    prompt = f"""You write {exam.upper()} Speaking mini mock tests for Vietnamese learners around CEFR {level}. {focus} Variation seed: {seed}.

Format (follow exactly): {fmt}

Rules: natural exam-style English; no sensitive, political or culturally stereotyped topics; each "tip_vi" is one short Vietnamese tip (under 30 words) on how to answer.

Return ONLY JSON:
{{
  "title": "{exam.upper()} Speaking · <short theme>",
  "description": "1–2 câu tiếng Việt mô tả đề",
  "tasks": [
    {{"part": "Part 1", "kind": "question", "prompt": "...", "tip_vi": "...", "reference": null, "cue": []}}
  ]
}}"""
    raw = get_llm_response(prompt)
    return parse_and_validate(raw, GeneratedSpeakingExamOutput)
