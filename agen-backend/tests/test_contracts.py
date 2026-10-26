from pydantic import ValidationError
import pytest

from app.agents.contracts import LessonOutput, PlacementQuestionOutput, SpeakingTurnOutput
from app.services.llm_client import parse_and_validate


def test_lesson_contract_accepts_structured_output():
    result = parse_and_validate(
        '{"title":"Lesson","summary":"Summary","exercises":[{"type":"flashcard","order":0,"content":{"word":"hello"}}]}',
        LessonOutput,
    )
    assert result["exercises"][0]["type"] == "flashcard"


def test_placement_contract_rejects_missing_option():
    with pytest.raises(ValidationError):
        PlacementQuestionOutput(
            skill="grammar",
            level="A1",
            question="Choose",
            options={"A": "one"},
            correct_answer="A",
            explanation="Because",
        )


def test_speaking_contract_rejects_invalid_score():
    with pytest.raises(ValidationError):
        SpeakingTurnOutput(ai_reply="Reply", is_correct=True, score=101)
