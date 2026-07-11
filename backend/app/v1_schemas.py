from typing import Annotated, Literal

from pydantic import BaseModel, Field


class MultipleChoiceAnswer(BaseModel):
    type: Literal["multiple_choice"]
    selected_option_id: int


class WordBankAnswer(BaseModel):
    type: Literal["translate_word_bank"]
    selected_option_ids: list[int]


class MatchPairSelection(BaseModel):
    left_id: str
    right_id: str


class MatchPairsAnswer(BaseModel):
    type: Literal["match_pairs"]
    matches: list[MatchPairSelection]


class FillBlankAnswer(BaseModel):
    type: Literal["fill_blank"]
    text: str


class TypeAnswer(BaseModel):
    type: Literal["type_answer"]
    text: str


ExerciseAnswer = Annotated[
    MultipleChoiceAnswer | WordBankAnswer | MatchPairsAnswer | FillBlankAnswer | TypeAnswer,
    Field(discriminator="type"),
]


class SubmitAnswerRequest(BaseModel):
    exercise_id: int
    client_submission_id: str
    response_time_ms: int | None = Field(default=None, ge=0)
    answer: ExerciseAnswer


class StartAttemptRequest(BaseModel):
    mode: Literal["standard", "practice", "review", "legendary"] = "standard"


class RefillHeartsRequest(BaseModel):
    method: Literal["practice", "gems", "mock"] = "gems"
    cost: int = Field(default=50, ge=0)


class DailyGoalRequest(BaseModel):
    daily_goal_xp: int = Field(ge=1, le=500)


class SettingsUpdateRequest(BaseModel):
    sound_effects_enabled: bool | None = None
    animations_enabled: bool | None = None
    listening_exercises_enabled: bool | None = None
    motivational_messages_enabled: bool | None = None
    leaderboard_enabled: bool | None = None
    dark_mode_enabled: bool | None = None
    daily_reminder_time: str | None = None
