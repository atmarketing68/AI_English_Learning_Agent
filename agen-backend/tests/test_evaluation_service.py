"""Unit tests for the rule-based AI evaluation framework (Master Plan §29).

Covers all four scoring dimensions, the blocklist, agent-specific completeness
rules, curriculum alignment, and edge cases. No LLM / DB required.
"""
import pytest

from app.services.evaluation_service import (
    FLAG_THRESHOLD,
    EvaluationResult,
    evaluate_output,
)


def _good_lesson():
    return {
        "title": "Daily Greetings",
        "summary": "Learn how to greet people in English.",
        "skill": "vocabulary",
        "level": "A1",
        "exercises": [
            {"type": "flashcard", "order": 0, "content": {"word": "hello", "definition": "a greeting"}},
            {"type": "flashcard", "order": 1, "content": {"word": "goodbye", "definition": "a farewell"}},
            {
                "type": "multiple_choice",
                "order": 2,
                "content": {
                    "question": "Which word is a greeting?",
                    "options": {"A": "hello", "B": "table", "C": "run", "D": "blue"},
                    "correct_answer": "A",
                },
            },
        ],
    }


# ── Happy path ────────────────────────────────────────────────────────────────
def test_good_lesson_scores_perfect_and_not_flagged():
    result = evaluate_output("lesson", _good_lesson(), {"skill": "vocabulary", "level": "A1"})
    assert isinstance(result, EvaluationResult)
    assert result.overall_score == 100.0
    assert result.flagged is False
    assert result.flags == []
    assert set(result.scores) == {
        "english_accuracy",
        "age_appropriate",
        "completeness",
        "curriculum_alignment",
    }


def test_good_placement_question_perfect():
    payload = {
        "skill": "grammar",
        "level": "A2",
        "question": "She ___ to school every day.",
        "options": {"A": "go", "B": "goes", "C": "going", "D": "gone"},
        "correct_answer": "B",
        "explanation": "Present simple third person singular takes -s.",
    }
    result = evaluate_output("placement_question", payload, {"skill": "grammar"})
    assert result.overall_score == 100.0
    assert result.flagged is False


# ── Age-appropriateness / blocklist ────────────────────────────────────────────
def test_blocklist_flags_sensitive_words():
    payload = _good_lesson()
    payload["summary"] = "A lesson about how to kill time and drink beer."
    result = evaluate_output("lesson", payload, {"skill": "vocabulary"})
    assert result.scores["age_appropriate"] < 100
    assert result.flagged is True
    assert any("age" in f for f in result.flags)


def test_blocklist_is_whole_word_only():
    # "classic" contains "ass"-like fragments but no blocklisted whole word;
    # "skill" contains "kill" as a substring and must NOT trigger.
    payload = _good_lesson()
    payload["summary"] = "This lesson builds a useful skill for classroom talk."
    result = evaluate_output("lesson", payload, {"skill": "vocabulary"})
    assert result.scores["age_appropriate"] == 100.0


def test_blocklist_case_insensitive():
    payload = _good_lesson()
    payload["title"] = "GUNS and BLOOD"
    result = evaluate_output("lesson", payload, {"skill": "vocabulary"})
    assert result.scores["age_appropriate"] < 100
    assert any("gun" in f or "blood" in f for f in result.flags)


def test_multiple_blocklist_hits_reduce_score_further():
    one = _good_lesson()
    one["summary"] = "We talk about a gun."
    two = _good_lesson()
    two["summary"] = "We talk about a gun and blood and death."
    r1 = evaluate_output("lesson", one, {"skill": "vocabulary"})
    r2 = evaluate_output("lesson", two, {"skill": "vocabulary"})
    assert r2.scores["age_appropriate"] < r1.scores["age_appropriate"]


# ── Completeness ────────────────────────────────────────────────────────────────
def test_lesson_with_too_few_exercises_flagged():
    payload = _good_lesson()
    payload["exercises"] = payload["exercises"][:1]
    result = evaluate_output("lesson", payload, {"skill": "vocabulary"})
    assert result.scores["completeness"] == 50.0
    assert result.flagged is True
    assert any("exercise" in f for f in result.flags)


def test_lesson_mcq_missing_answer_flagged():
    payload = _good_lesson()
    payload["exercises"][2]["content"].pop("correct_answer")
    result = evaluate_output("lesson", payload, {"skill": "vocabulary"})
    assert result.scores["completeness"] == 60.0
    assert any("MCQ" in f for f in result.flags)


def test_placement_missing_options_flagged():
    payload = {
        "skill": "grammar",
        "level": "A2",
        "question": "Pick one.",
        "correct_answer": "B",
    }
    result = evaluate_output("placement_question", payload, {"skill": "grammar"})
    assert result.scores["completeness"] == 50.0
    assert any("placement" in f for f in result.flags)


def test_writing_eval_missing_corrected_version_flagged():
    payload = {
        "skill": "writing",
        "overall_feedback": "Nice effort, keep practicing your sentences.",
        "score": 70,
    }
    result = evaluate_output("writing_evaluation", payload, {"skill": "writing"})
    assert result.scores["completeness"] == 60.0
    assert any("corrected_version" in f for f in result.flags)


def test_unknown_agent_defaults_complete():
    payload = {"skill": "vocabulary", "note": "Some perfectly fine content here."}
    result = evaluate_output("some_new_agent", payload, {"skill": "vocabulary"})
    assert result.scores["completeness"] == 100.0


# ── Curriculum alignment ────────────────────────────────────────────────────────
def test_skill_mismatch_flagged():
    payload = _good_lesson()
    payload["skill"] = "grammar"
    result = evaluate_output("lesson", payload, {"skill": "vocabulary"})
    assert result.scores["curriculum_alignment"] == 50.0
    assert any("skill mismatch" in f for f in result.flags)


def test_unknown_skill_flagged():
    payload = _good_lesson()
    payload["skill"] = "telepathy"
    # No expected skill mismatch (expected matches), but skill is not in the allowed set.
    result = evaluate_output("lesson", payload, {"skill": "telepathy"})
    assert result.scores["curriculum_alignment"] < 100
    assert any("unknown skill" in f for f in result.flags)


def test_unknown_level_flagged():
    payload = _good_lesson()
    payload["level"] = "Z9"
    result = evaluate_output("lesson", payload, {"skill": "vocabulary"})
    assert result.scores["curriculum_alignment"] < 100
    assert any("unknown level" in f for f in result.flags)


def test_no_expected_skips_alignment():
    result = evaluate_output("lesson", _good_lesson(), None)
    assert result.scores["curriculum_alignment"] == 100.0


# ── English accuracy / edge cases ───────────────────────────────────────────────
def test_empty_payload_scores_zero_english():
    result = evaluate_output("lesson", {}, None)
    assert result.scores["english_accuracy"] == 0.0
    assert result.flagged is True
    assert any("empty" in f for f in result.flags)


def test_placeholder_junk_flagged():
    payload = _good_lesson()
    payload["summary"] = "TODO: write the real summary here {{placeholder}}"
    result = evaluate_output("lesson", payload, {"skill": "vocabulary"})
    assert result.scores["english_accuracy"] < 100
    assert any("placeholder" in f for f in result.flags)


def test_repeated_char_garble_flagged():
    payload = _good_lesson()
    payload["summary"] = "greaaaaaaat lesson"
    result = evaluate_output("lesson", payload, {"skill": "vocabulary"})
    assert result.scores["english_accuracy"] < 100
    assert any("garble" in f for f in result.flags)


def test_to_dict_shape_and_rounding():
    result = evaluate_output("lesson", _good_lesson(), {"skill": "vocabulary"})
    d = result.to_dict()
    assert set(d) == {"overall_score", "scores", "flags", "flagged"}
    assert isinstance(d["scores"], dict)
    assert isinstance(d["flags"], list)
    assert isinstance(d["flagged"], bool)


def test_flag_threshold_is_reasonable():
    # Guardrail: keep the constant in the sane band the tests assume.
    assert 50 <= FLAG_THRESHOLD <= 80
