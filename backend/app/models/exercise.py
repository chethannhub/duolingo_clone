from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Integer, Text, UniqueConstraint, text as sql_text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class Exercise(TimestampMixin, Base):
    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint(
            "exercise_type IN ('multiple_choice', 'translate_word_bank', 'match_pairs', "
            "'fill_blank', 'type_answer', 'listen', 'speak')",
            name="ck_exercises_type",
        ),
        CheckConstraint(
            "answer_match_mode IN ('exact', 'case_insensitive', 'normalized')",
            name="ck_exercises_answer_match_mode",
        ),
        CheckConstraint("difficulty BETWEEN 1 AND 5", name="ck_exercises_difficulty"),
        CheckConstraint("version > 0", name="ck_exercises_version"),
        CheckConstraint("json_valid(metadata_json)", name="ck_exercises_metadata_json"),
        CheckConstraint("is_published IN (0, 1)", name="ck_exercises_is_published"),
    )

    id = Column(Integer, primary_key=True)
    exercise_type = Column(Text, nullable=False)
    instruction_text = Column(Text, nullable=False)
    prompt_text = Column(Text, nullable=False)
    hint_text = Column(Text, nullable=True)
    explanation_text = Column(Text, nullable=True)
    audio_url = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    answer_match_mode = Column(Text, nullable=False, server_default="normalized")
    difficulty = Column(Integer, nullable=False, server_default="1")
    metadata_json = Column(Text, nullable=False, server_default="{}")
    version = Column(Integer, nullable=False, server_default="1")
    is_published = Column(Integer, nullable=False, server_default="0")

    lesson_links = relationship("LessonExercise", back_populates="exercise")
    options = relationship("ExerciseOption", back_populates="exercise", cascade="all, delete-orphan")
    match_pairs = relationship(
        "ExerciseMatchPair",
        back_populates="exercise",
        cascade="all, delete-orphan",
    )
    accepted_answers = relationship(
        "ExerciseAcceptedAnswer",
        back_populates="exercise",
        cascade="all, delete-orphan",
    )


class LessonExercise(Base):
    __tablename__ = "lesson_exercises"
    __table_args__ = (
        UniqueConstraint("lesson_id", "position"),
        Index("ix_lesson_exercises_lesson", "lesson_id", "position"),
        CheckConstraint("position > 0", name="ck_lesson_exercises_position"),
        CheckConstraint("is_required IN (0, 1)", name="ck_lesson_exercises_required"),
    )

    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False)
    position = Column(Integer, nullable=False)
    is_required = Column(Integer, nullable=False, server_default="1")
    created_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))

    lesson = relationship("Lesson", back_populates="lesson_exercises")
    exercise = relationship("Exercise", back_populates="lesson_links")


class ExerciseOption(Base):
    __tablename__ = "exercise_options"
    __table_args__ = (
        UniqueConstraint("exercise_id", "position"),
        CheckConstraint("position > 0", name="ck_options_position"),
        CheckConstraint("is_correct IN (0, 1)", name="ck_options_is_correct"),
        CheckConstraint(
            "correct_order IS NULL OR correct_order > 0",
            name="ck_options_correct_order",
        ),
    )

    id = Column(Integer, primary_key=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(Text, nullable=False)
    position = Column(Integer, nullable=False)
    is_correct = Column(Integer, nullable=False, server_default="0")
    correct_order = Column(Integer, nullable=True)

    exercise = relationship("Exercise", back_populates="options")


class ExerciseMatchPair(Base):
    __tablename__ = "exercise_match_pairs"
    __table_args__ = (
        UniqueConstraint("exercise_id", "position"),
        CheckConstraint("position > 0", name="ck_match_pairs_position"),
    )

    id = Column(Integer, primary_key=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False)
    left_text = Column(Text, nullable=False)
    right_text = Column(Text, nullable=False)
    position = Column(Integer, nullable=False)

    exercise = relationship("Exercise", back_populates="match_pairs")


class ExerciseAcceptedAnswer(Base):
    __tablename__ = "exercise_accepted_answers"
    __table_args__ = (
        UniqueConstraint("exercise_id", "normalized_answer"),
        CheckConstraint("is_primary IN (0, 1)", name="ck_accepted_answers_primary"),
    )

    id = Column(Integer, primary_key=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False)
    answer_text = Column(Text, nullable=False)
    normalized_answer = Column(Text, nullable=False)
    is_primary = Column(Integer, nullable=False, server_default="0")
    created_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))

    exercise = relationship("Exercise", back_populates="accepted_answers")
