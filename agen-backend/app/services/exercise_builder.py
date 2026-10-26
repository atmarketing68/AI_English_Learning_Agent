"""
Six interactive exercise types (G1 · dạng bài tập mới), built from content a
lesson already has, so no extra LLM call or prompt change is needed and the
same builder works for freshly generated and cached curriculum lessons.

  word_bank       Ghép câu từ kho chữ     grammar examples {en, vi}
  match_pairs     Nối cặp từ – nghĩa       vocabulary list
  listen_choose   Nghe chọn nghĩa đúng     vocabulary list
  dictation       Nghe – chép              vocabulary examples / listening script
  speak_repeat    Nói lặp lại có chấm      vocabulary examples
  dialogue_order  Sắp xếp hội thoại        listening script lines

Content schemas (stored on Exercise.content):
  word_bank:      { prompt_vi, answer, tokens: [str] }          tokens = answer words + distractors
  match_pairs:    { pairs: [{left, right}] }
  listen_choose:  { audio_text, options: {A..D}, correct_answer }
  dictation:      { text, hint? }
  speak_repeat:   { text, hint? }
  dialogue_order: { lines: [{speaker, text}] }                  stored in the correct order
"""
from __future__ import annotations

import difflib
import json
import random
import re
import zlib

NEW_TYPES = ("word_bank", "match_pairs", "listen_choose", "dictation", "speak_repeat", "dialogue_order")
SKIP_ANSWER = "__skip__"            # speak_repeat without a microphone: not graded
DICTATION_PASS = 0.9
SPEAK_PASS = 0.7
GENERIC_DISTRACTORS = ("is", "are", "was", "the", "a", "to", "do", "does", "did", "have", "has", "will")


def _norm(text: str) -> str:
    text = (text or "").lower().replace("’", "'")
    text = re.sub(r"[^\w\s']", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _words(text: str) -> list[str]:
    return _norm(text).split()


def _rng(*parts: str) -> random.Random:
    """Deterministic per lesson content, so a lesson looks the same on reload."""
    return random.Random(zlib.crc32("|".join(parts).encode("utf-8")))


def _short_sentences(candidates: list[str], low: int = 3, high: int = 12) -> list[str]:
    seen, out = set(), []
    for s in candidates:
        s = re.sub(r"\s+", " ", (s or "")).strip()
        n = len(_words(s))
        if low <= n <= high and _norm(s) not in seen:
            seen.add(_norm(s))
            out.append(s)
    return out


# ── Builders ─────────────────────────────────────────────────────────────────
def _vocabulary_exercises(vocab: list[dict]) -> list[dict]:
    items = [v for v in vocab if isinstance(v, dict) and v.get("word") and v.get("translation")]
    out: list[dict] = []
    if len(items) >= 3:
        pairs = [{"left": v["word"].strip(), "right": v["translation"].strip()} for v in items[:5]]
        out.append({"type": "match_pairs", "content": {"pairs": pairs}})
    if len(items) >= 4:
        target = items[min(5, len(items) - 1)]
        others = [v["translation"].strip() for v in items if v is not target]
        rng = _rng("listen", target["word"])
        choices = rng.sample(others, 3) + [target["translation"].strip()]
        rng.shuffle(choices)
        keys = "ABCD"
        out.append({"type": "listen_choose", "content": {
            "audio_text": target["word"].strip(),
            "options": {keys[i]: c for i, c in enumerate(choices)},
            "correct_answer": keys[choices.index(target["translation"].strip())],
        }})
    examples = _short_sentences([v.get("example", "") for v in items])
    if examples:
        word = next((v for v in items if v.get("example") and _norm(v["example"]) == _norm(examples[0])), None)
        out.append({"type": "speak_repeat", "content": {
            "text": examples[0],
            "hint": f"{word['word']} = {word['translation']}" if word else None,
        }})
    if len(examples) >= 2:
        out.append({"type": "dictation", "content": {"text": examples[1]}})
    return out


def _grammar_exercises(explanation: dict) -> list[dict]:
    examples = [e for e in explanation.get("examples") or [] if isinstance(e, dict) and e.get("en") and e.get("vi")]
    out: list[dict] = []
    all_words = {w for e in examples for w in _words(e["en"])}
    for ex in examples[:2]:
        answer = re.sub(r"\s+", " ", ex["en"]).strip()
        tokens = answer.split(" ")
        if not 3 <= len(tokens) <= 12:
            continue
        own = set(_words(answer))
        pool = sorted(all_words - own) or [w for w in GENERIC_DISTRACTORS if w not in own]
        rng = _rng("bank", answer)
        distractors = rng.sample(pool, min(2, len(pool)))
        out.append({"type": "word_bank", "content": {
            "prompt_vi": ex["vi"].strip(),
            "answer": answer,
            "tokens": tokens + distractors,
        }})
    return out


def _listening_exercises(passage: dict) -> list[dict]:
    lines = [l for l in passage.get("script_lines") or [] if isinstance(l, dict) and l.get("text")]
    out: list[dict] = []
    if len(lines) >= 3:
        out.append({"type": "dialogue_order", "content": {
            "lines": [{"speaker": (l.get("speaker") or "").strip(), "text": l["text"].strip()} for l in lines[:5]],
        }})
    sentences = _short_sentences([l["text"] for l in lines], low=4, high=12)
    if sentences:
        out.append({"type": "dictation", "content": {"text": sentences[0]}})
    return out


def extra_exercises(skill: str, data: dict) -> list[dict]:
    """New-type exercises for a lesson, as [{type, content}] (order is assigned by the caller)."""
    data = data if isinstance(data, dict) else {}
    try:
        if skill == "vocabulary":
            return _vocabulary_exercises(data.get("vocabulary") or [])
        if skill == "grammar" and isinstance(data.get("explanation"), dict):
            return _grammar_exercises(data["explanation"])
        if skill == "listening" and isinstance(data.get("passage"), dict):
            return _listening_exercises(data["passage"])
    except Exception:  # malformed AI content must never block the lesson
        return []
    return []


# ── Answer checking ──────────────────────────────────────────────────────────
def check_answer(ex_type: str, content: dict, answer: str) -> tuple[bool, str, str]:
    """Returns (is_correct, correct_answer_to_show, explanation) for the new types."""
    content = content if isinstance(content, dict) else {}
    if ex_type == "word_bank":
        expected = content.get("answer", "")
        ok = _norm(answer) == _norm(expected)
        return ok, expected, f"“{content.get('prompt_vi', '')}” → {expected}"

    if ex_type == "listen_choose":
        key = str(content.get("correct_answer", "")).upper()
        options = content.get("options") or {}
        ok = answer.strip().upper() == key
        return ok, key, f"Bạn vừa nghe: “{content.get('audio_text', '')}” = {options.get(key, '')}"

    if ex_type == "dictation":
        expected = content.get("text", "")
        ratio = difflib.SequenceMatcher(None, _norm(answer), _norm(expected)).ratio()
        ok = ratio >= DICTATION_PASS
        note = "Chính xác tuyệt đối!" if _norm(answer) == _norm(expected) else (
            "Gần đúng — để ý chính tả nhé." if ok else "Nghe lại chậm hơn và chép từng cụm từ.")
        return ok, expected, note

    if ex_type == "speak_repeat":
        expected = content.get("text", "")
        if answer == SKIP_ANSWER:
            return True, "", "Đã bỏ qua phần nói."
        ratio = difflib.SequenceMatcher(None, _words(answer), _words(expected)).ratio()
        pct = round(ratio * 100)
        ok = ratio >= SPEAK_PASS
        return ok, expected, f"Khớp {pct}% với câu mẫu. Máy nghe được: “{answer.strip()}”"

    if ex_type == "match_pairs":
        pairs = {p.get("left"): p.get("right") for p in content.get("pairs") or [] if isinstance(p, dict)}
        try:
            attempts = json.loads(answer)
        except (TypeError, ValueError):
            attempts = []
        attempts = [a for a in attempts if isinstance(a, (list, tuple)) and len(a) == 2]
        wrong = sum(1 for left, right in attempts if pairs.get(left) != right)
        matched = {left for left, right in attempts if pairs.get(left) == right}
        ok = bool(pairs) and matched == set(pairs) and wrong == 0
        return ok, "", ("Nối đúng tất cả ngay lần đầu!" if ok else f"Bạn nối nhầm {wrong} lần.")

    if ex_type == "dialogue_order":
        lines = content.get("lines") or []
        try:
            order = [int(i) for i in json.loads(answer)]
        except (TypeError, ValueError):
            order = []
        ok = order == list(range(len(lines)))
        right = " → ".join(f"{i + 1}. {l.get('text', '')}" for i, l in enumerate(lines))
        return ok, "", ("Đúng thứ tự!" if ok else f"Thứ tự đúng: {right}")

    return False, "", ""
