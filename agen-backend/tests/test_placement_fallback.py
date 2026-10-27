"""Placement questions fall back to the static bank when the LLM is busy, out of quota or returns junk."""
import pytest

from app.agents import assessment_agent
from app.agents.contracts import PlacementQuestionOutput
from app.services.llm_client import LLMError

SKILLS = ["vocabulary", "grammar", "reading", "listening"]


def _quota(_prompt):
    raise LLMError("Hệ thống AI đang bận hoặc đã hết giới hạn sử dụng hôm nay.", is_quota=True)


@pytest.mark.parametrize("skill", SKILLS)
def test_quota_error_returns_valid_bank_question(monkeypatch, skill):
    monkeypatch.setattr(assessment_agent, "get_llm_response", _quota)
    q = assessment_agent.generate_placement_question(skill, "A2", 3, previous_correct=True, skill_occurrence=1)
    PlacementQuestionOutput.model_validate(q)
    assert q["effective_level"] == "B1"          # adaptive step up is kept
    assert q["options"][q["correct_answer"]]
    if skill == "reading":
        assert q["passage"] and not q["audio_text"]
    if skill == "listening":
        assert q["audio_text"] and not q["passage"]


def test_bad_json_also_falls_back(monkeypatch):
    monkeypatch.setattr(assessment_agent, "get_llm_response", lambda _p: "not json at all")
    q = assessment_agent.generate_placement_question("grammar", "B1", 4, previous_correct=False)
    PlacementQuestionOutput.model_validate(q)
    assert q["effective_level"] == "A2"


def test_unseeded_levels_and_all_occurrences_are_valid(monkeypatch):
    monkeypatch.setattr(assessment_agent, "get_llm_response", _quota)
    for level in ["PRE_A1", "A1", "A2", "B1", "B2", "C1", "C2"]:
        for skill in SKILLS:
            for occ in range(5):
                q = assessment_agent.generate_placement_question(skill, level, occ, skill_occurrence=occ)
                PlacementQuestionOutput.model_validate(q)
