"""
AGEN — Speech practice scoring (transcript-based).

The client captures speech with the browser Web Speech API (STT) and sends the
recognized transcript plus the target sentence. This service scores transcript
alignment as a speaking-practice proxy; it does not measure phoneme-level
pronunciation accuracy (that needs an audio-based provider — see
docs/G2_CHAM_PHAT_AM_SO_SANH.md).

Dimensions (0-100):
  - accuracy : word-level similarity between transcript and target (order-aware)
  - coverage : fraction of target words the learner actually produced
  - fluency  : words-per-minute vs an expected band (if duration provided)

G2 adds a per-word verdict (`words`) and Vietnamese-speaker sound tips
(`sound_tips`) derived from the words that were missed or misheard.

Deterministic, no LLM.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field


def _normalize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split into word tokens."""
    cleaned = re.sub(r"[^a-z0-9'\s]", " ", (text or "").lower().replace("’", "'"))
    return [w for w in cleaned.split() if w]


@dataclass
class PronunciationResult:
    overall_score: float
    accuracy: float
    coverage: float
    fluency: float
    target_word_count: int
    said_word_count: int
    missed_words: list[str] = field(default_factory=list)
    extra_words: list[str] = field(default_factory=list)
    feedback_vi: str = ""
    # G2: per-word verdict in target order: {word, status: ok|wrong|missed, heard?}
    words: list[dict] = field(default_factory=list)
    # G2: {sound, tip_vi, words}
    sound_tips: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "overall_score": round(self.overall_score, 1),
            "accuracy": round(self.accuracy, 1),
            "coverage": round(self.coverage, 1),
            "fluency": round(self.fluency, 1),
            "target_word_count": self.target_word_count,
            "said_word_count": self.said_word_count,
            "missed_words": self.missed_words,
            "extra_words": self.extra_words,
            "feedback_vi": self.feedback_vi,
            "words": self.words,
            "sound_tips": self.sound_tips,
        }


# Expected comfortable speaking pace band (words per minute).
_WPM_MIN = 60
_WPM_IDEAL_LOW = 90
_WPM_IDEAL_HIGH = 160


def _fluency_score(said_words: int, duration_seconds: float | None) -> float:
    if not duration_seconds or duration_seconds <= 0 or said_words == 0:
        return 100.0  # no timing info → don't penalise
    wpm = said_words / (duration_seconds / 60.0)
    if _WPM_IDEAL_LOW <= wpm <= _WPM_IDEAL_HIGH:
        return 100.0
    if wpm < _WPM_IDEAL_LOW:
        # Linear from _WPM_MIN (50) up to ideal-low (100).
        if wpm <= _WPM_MIN:
            return 50.0
        return 50.0 + (wpm - _WPM_MIN) / (_WPM_IDEAL_LOW - _WPM_MIN) * 50.0
    # Too fast: gentle penalty, floor 70.
    over = wpm - _WPM_IDEAL_HIGH
    return max(70.0, 100.0 - over * 0.5)


# ── Per-word alignment ───────────────────────────────────────────────────────
def _similar(a: str, b: str) -> bool:
    """A misheard word that is close to the target (e.g. 'tree' / 'three')."""
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.6


def align_words(target: list[str], said: list[str]) -> list[dict]:
    """Verdict per target word, in order. Uses the same matcher as `accuracy`."""
    out: list[dict] = []
    matcher = difflib.SequenceMatcher(a=target, b=said, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            out.extend({"word": w, "status": "ok"} for w in target[i1:i2])
        elif tag == "delete":
            out.extend({"word": w, "status": "missed"} for w in target[i1:i2])
        elif tag == "replace":
            heard = said[j1:j2]
            for k, w in enumerate(target[i1:i2]):
                h = heard[k] if k < len(heard) else None
                if h is None:
                    out.append({"word": w, "status": "missed"})
                elif _similar(w, h):
                    out.append({"word": w, "status": "wrong", "heard": h})
                else:
                    out.append({"word": w, "status": "missed", "heard": h})
        # "insert" = extra words said; they do not belong to any target word
    return out


# ── Sound tips for Vietnamese speakers ───────────────────────────────────────
# (id, Vietnamese tip, regex on the spelling of a missed/misheard word)
_SOUND_RULES: list[tuple[str, str, str, re.Pattern[str]]] = [
    ("th", "/θ/ – /ð/", "Đặt đầu lưỡi giữa hai hàm răng rồi thổi hơi ra (think, this, thanks).", re.compile(r"th")),
    ("ending", "Âm cuối", "Người Việt hay nuốt âm cuối: phát âm rõ -s, -t, -d, -k, -p ở cuối từ (books, want, need).",
     re.compile(r"[a-z]{2,}(s|es|ed|t|d|k|p|ks|ts)$")),
    ("r", "/r/", "Cong nhẹ đầu lưỡi về sau, không chạm vòm miệng; không đọc thành /z/ hay /g/ (right, rice, very).",
     re.compile(r"r")),
    ("sh_ch_j", "/ʃ/ – /tʃ/ – /dʒ/", "Chu môi về phía trước, hơi bật ra (she, cheap, job, juice).",
     re.compile(r"(sh|ch|tch|j|ge$|dge)")),
    ("w_v", "/w/ – /v/", "/w/ tròn môi không chạm răng (we, water); /v/ răng trên chạm môi dưới (very, have).",
     re.compile(r"(^w|v)")),
    ("cluster", "Cụm phụ âm", "Đọc đủ từng phụ âm đứng liền nhau, không chèn nguyên âm (street, please, school).",
     re.compile(r"(^|[^aeiou])[bcdfgkpst][lr]|^s[tpkmnlw]|^str|^spr|^scr")),
    ("long_vowel", "Nguyên âm dài /iː/ /uː/", "Kéo dài hơn một chút: sheep ≠ ship, food ≠ foot (eat, see, two).",
     re.compile(r"(ee|ea|oo|ie)")),
    ("l_n", "/l/ – /n/", "/l/ đầu lưỡi chạm nướu trên, luồng hơi ra hai bên; đừng lẫn với /n/ (like, lunch, line).",
     re.compile(r"^l")),
]


def sound_tips(words: list[dict], limit: int = 3) -> list[dict]:
    """Up to `limit` tips, ordered by how many problem words each rule explains."""
    problems = [w["word"] for w in words if w["status"] != "ok"]
    if not problems:
        return []
    hits: list[tuple[int, str, str, str, list[str]]] = []
    for idx, (_id, sound, tip, pattern) in enumerate(_SOUND_RULES):
        matched = [w for w in problems if pattern.search(w)]
        if matched:
            hits.append((-len(matched), idx, sound, tip, matched[:4]))
    hits.sort()
    return [{"sound": s, "tip_vi": t, "words": ws} for _, _, s, t, ws in hits[:limit]]


def score_pronunciation(
    target_text: str,
    transcript: str,
    duration_seconds: float | None = None,
) -> PronunciationResult:
    """Score a spoken attempt against a target sentence."""
    target = _normalize(target_text)
    said = _normalize(transcript)

    if not target:
        return PronunciationResult(
            overall_score=0.0, accuracy=0.0, coverage=0.0, fluency=0.0,
            target_word_count=0, said_word_count=len(said),
            feedback_vi="Không có câu mẫu để so sánh.",
        )

    # Accuracy: order-aware similarity ratio over word sequences.
    matcher = difflib.SequenceMatcher(a=target, b=said, autojunk=False)
    accuracy = matcher.ratio() * 100.0

    # Coverage + missed/extra words via set difference (case/punct-normalized).
    target_set = set(target)
    said_set = set(said)
    matched = target_set & said_set
    coverage = (len(matched) / len(target_set)) * 100.0
    missed_words = [w for w in target if w not in said_set]
    # Preserve order + dedupe for missed
    seen: set[str] = set()
    missed_words = [w for w in missed_words if not (w in seen or seen.add(w))]
    extra_words = [w for w in said if w not in target_set]
    seen2: set[str] = set()
    extra_words = [w for w in extra_words if not (w in seen2 or seen2.add(w))]

    fluency = _fluency_score(len(said), duration_seconds)

    overall = accuracy * 0.55 + coverage * 0.30 + fluency * 0.15

    words = align_words(target, said)
    tips = sound_tips(words)

    # Simple Vietnamese feedback.
    if overall >= 85:
        feedback = "Tuyệt vời! Phát âm của bạn rất rõ và chính xác."
    elif overall >= 70:
        feedback = "Tốt! Hãy chú ý phát âm rõ hơn một vài từ còn thiếu."
    elif overall >= 50:
        feedback = "Khá ổn. Hãy luyện lại và nói chậm, rõ từng từ."
    else:
        feedback = "Hãy thử lại — đọc to, chậm và rõ từng từ trong câu mẫu."
    if missed_words:
        preview = ", ".join(missed_words[:5])
        feedback += f" Từ cần luyện thêm: {preview}."

    return PronunciationResult(
        overall_score=overall,
        accuracy=accuracy,
        coverage=coverage,
        fluency=fluency,
        target_word_count=len(target),
        said_word_count=len(said),
        missed_words=missed_words,
        extra_words=extra_words,
        feedback_vi=feedback,
        words=words,
        sound_tips=tips,
    )
