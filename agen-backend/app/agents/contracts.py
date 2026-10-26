"""Typed contracts for outputs produced by AGEN agents."""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RecommendedTopic(BaseModel):
    skill: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class CoachAdviceOutput(BaseModel):
    weak_skills: list[str] = Field(default_factory=list)
    strong_skills: list[str] = Field(default_factory=list)
    focus_area: str = Field(min_length=1)
    recommended_topics: list[RecommendedTopic] = Field(min_length=2, max_length=2)
    study_plan_today: str = Field(min_length=1)
    motivational_message: str = Field(min_length=1)


class WeeklyReportOutput(BaseModel):
    sessions_count: int = Field(ge=0)
    xp_earned_this_week: int = Field(ge=0)
    best_skill: str = Field(min_length=1)
    most_practiced_skill: str = Field(min_length=1)
    highlight: str = Field(min_length=1)
    areas_to_improve: list[str] = Field(min_length=1)
    next_week_goal: str = Field(min_length=1)
    encouragement: str = Field(min_length=1)


class PlacementQuestionOutput(BaseModel):
    skill: str = Field(min_length=1)
    level: str = Field(min_length=1)
    passage: str = ""
    # G2 · listening questions: the learner only hears this text (client TTS).
    audio_text: str = ""
    question: str = Field(min_length=1)
    options: dict[str, str]
    correct_answer: Literal["A", "B", "C", "D"]
    explanation: str = Field(min_length=1)
    # Added by the agent after validation (adaptive difficulty); declared so the
    # orchestrator preserves it when dumping the validated payload.
    effective_level: str | None = None

    @model_validator(mode="after")
    def has_four_options(self) -> "PlacementQuestionOutput":
        if set(self.options) != {"A", "B", "C", "D"}:
            raise ValueError("Placement question options must contain exactly A, B, C and D")
        if any(not value.strip() for value in self.options.values()):
            raise ValueError("Placement question options cannot be empty")
        return self


class LessonExerciseOutput(BaseModel):
    type: str = Field(min_length=1)
    order: int = Field(ge=0)
    content: dict[str, Any]


class LessonOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    exercises: list[LessonExerciseOutput] = Field(min_length=1)
    skill: str | None = None
    topic: str | None = None
    level: str | None = None
    xp_value: int | None = Field(default=None, ge=0)
    vocabulary: list[dict[str, Any]] | None = None
    passage: dict[str, Any] | None = None


class RoleplayScenarioOutput(BaseModel):
    system_prompt: str = Field(min_length=1)
    ai_first_message: str = Field(min_length=1)


class SpeakingTurnOutput(BaseModel):
    ai_reply: str = Field(min_length=1)
    feedback: str = ""
    is_correct: bool
    score: float = Field(ge=0, le=100)
    # G2 · AI Coach: natural version of the learner's line and a suggestion for the next turn.
    corrected: str = ""
    hint_en: str = ""


class GrammarErrorOutput(BaseModel):
    original: str = Field(min_length=1)
    corrected: str = Field(min_length=1)
    explanation_vi: str = Field(min_length=1)


class WritingScoresOutput(BaseModel):
    grammar: float = Field(ge=0, le=100)
    vocabulary: float = Field(ge=0, le=100)
    coherence: float = Field(ge=0, le=100)
    task_achievement: float = Field(ge=0, le=100)


class WritingPromptOutput(BaseModel):
    title: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    genre: str = Field(min_length=1)
    word_target: str = Field(min_length=1)
    guide_steps: list[str] = Field(min_length=3)
    useful_phrases: list[str] = Field(min_length=1)
    example_opening: str = Field(min_length=1)
    # Added by the agent after LLM validation; declared so the orchestrator
    # preserves them when dumping the validated payload.
    level: str | None = None
    topic: str | None = None


class ExamBandOutput(BaseModel):
    """G5 · exam-style band for IELTS (0–9) or TOEIC Writing (0–200)."""
    exam: Literal["ielts", "toeic"]
    overall: float = Field(ge=0, le=200)
    criteria: dict[str, float] = Field(default_factory=dict)
    next_band_tips: list[str] = Field(default_factory=list, max_length=5)


class WritingEvaluationOutput(BaseModel):
    overall_score: float = Field(ge=0, le=100)
    grade: Literal["S", "A", "B", "C", "D"]
    word_count: int = Field(ge=0)
    scores: WritingScoresOutput
    grammar_errors: list[GrammarErrorOutput] = Field(default_factory=list, max_length=5)
    vocabulary_feedback: str = Field(min_length=1)
    coherence_feedback: str = Field(min_length=1)
    strengths: list[str] = Field(min_length=1)
    improvements: list[str] = Field(min_length=1)
    corrected_version: str = Field(min_length=1)
    encouragement: str = Field(min_length=1)
    exam_band: ExamBandOutput | None = None


class WordLookupOutput(BaseModel):
    """G2 · tap-a-word dictionary lookup (listening transcript)."""
    word: str = Field(min_length=1)
    phonetic: str = ""
    part_of_speech: str = ""
    meaning_vi: str = Field(min_length=1)
    definition_en: str = ""
    example: str = ""


class TutorExampleOutput(BaseModel):
    en: str = Field(min_length=1)
    vi: str = ""


class TutorAnswerOutput(BaseModel):
    """G8 · Bo's answer to a grammar / usage question, in Vietnamese."""
    answer_vi: str = Field(min_length=1)
    rule: str = ""
    examples: list[TutorExampleOutput] = Field(default_factory=list, max_length=5)
    common_mistake: str = ""
    follow_ups: list[str] = Field(default_factory=list, max_length=4)
    on_topic: bool = True


# ── G9 · Speaking mock test evaluation ───────────────────────────────────────
class SpeakingCorrectionOutput(BaseModel):
    original: str = Field(min_length=1)
    corrected: str = Field(min_length=1)


class SpeakingTaskFeedbackOutput(BaseModel):
    task_id: str = Field(min_length=1)
    comment_vi: str = Field(min_length=1)
    corrections: list[SpeakingCorrectionOutput] = Field(default_factory=list, max_length=3)


class SpeakingExamEvaluationOutput(BaseModel):
    exam: Literal["ielts", "toeic"]
    overall: float = Field(ge=0, le=200)
    criteria: dict[str, float] = Field(default_factory=dict)
    task_feedback: list[SpeakingTaskFeedbackOutput] = Field(default_factory=list, max_length=12)
    strengths: list[str] = Field(default_factory=list, max_length=4)
    improvements: list[str] = Field(default_factory=list, max_length=4)
    next_band_tips: list[str] = Field(default_factory=list, max_length=4)


# ── G9 · AI-generated mock exam paper (same shape as services/mock_exams.EXAMS) ──
class ExamAudioLineOutput(BaseModel):
    speaker: str = Field(min_length=1, max_length=40)
    text: str = Field(min_length=1)


class ExamQuestionOutput(BaseModel):
    type: Literal["mc", "gap", "tfng"]
    prompt: str = Field(min_length=1)
    options: list[str] | None = None
    answer: int | list[str]
    explanation_vi: str = Field(min_length=1)
    audio: list[ExamAudioLineOutput] | None = None


class ExamSectionOutput(BaseModel):
    title: str = Field(min_length=1)
    instructions: str = Field(min_length=1)
    audio: list[ExamAudioLineOutput] | None = None
    passage: str | None = None
    per_question_audio: bool = False
    questions: list[ExamQuestionOutput] = Field(min_length=1, max_length=20)


class GeneratedExamOutput(BaseModel):
    title: str = Field(min_length=1, max_length=140)
    description: str = Field(min_length=1)
    minutes: int = Field(ge=5, le=30)
    sections: list[ExamSectionOutput] = Field(min_length=1, max_length=5)
