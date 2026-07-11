from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Integer, Text, UniqueConstraint, text as sql_text
from sqlalchemy.orm import relationship

from app.database import Base


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"
    __table_args__ = (
        UniqueConstraint("learner_id", "course_id"),
        Index(
            "ux_learner_selected_course",
            "learner_id",
            unique=True,
            sqlite_where=Column("is_selected") == 1,
        ),
        CheckConstraint(
            "status IN ('active', 'paused', 'completed')",
            name="ck_enrollments_status",
        ),
        CheckConstraint("is_selected IN (0, 1)", name="ck_enrollments_selected"),
    )

    id = Column(Integer, primary_key=True)
    learner_id = Column(Integer, ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    status = Column(Text, nullable=False, server_default="active")
    is_selected = Column(Integer, nullable=False, server_default="0")
    current_level_id = Column(Integer, ForeignKey("levels.id", ondelete="SET NULL"), nullable=True)
    current_lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))
    last_accessed_at = Column(Text, nullable=True)
    completed_at = Column(Text, nullable=True)

    learner = relationship("Learner", back_populates="enrollments")
    course = relationship("Course")
    current_level = relationship("Level", foreign_keys=[current_level_id])
    current_lesson = relationship("Lesson", foreign_keys=[current_lesson_id])
    level_progress = relationship(
        "LearnerLevelProgress",
        back_populates="enrollment",
        cascade="all, delete-orphan",
    )
    lesson_progress = relationship(
        "LearnerLessonProgress",
        back_populates="enrollment",
        cascade="all, delete-orphan",
    )
    lesson_attempts = relationship("LessonAttempt", back_populates="enrollment")


class LearnerLevelProgress(Base):
    __tablename__ = "learner_level_progress"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "level_id"),
        Index("ix_level_progress_enrollment", "enrollment_id", "level_id"),
        CheckConstraint("crown_count BETWEEN 0 AND 5", name="ck_level_progress_crowns"),
        CheckConstraint("is_completed IN (0, 1)", name="ck_level_progress_completed"),
        CheckConstraint("is_legendary IN (0, 1)", name="ck_level_progress_legendary"),
        CheckConstraint(
            "best_score_percent BETWEEN 0 AND 100",
            name="ck_level_progress_best_score",
        ),
    )

    id = Column(Integer, primary_key=True)
    enrollment_id = Column(
        Integer,
        ForeignKey("course_enrollments.id", ondelete="CASCADE"),
        nullable=False,
    )
    level_id = Column(Integer, ForeignKey("levels.id", ondelete="CASCADE"), nullable=False)
    crown_count = Column(Integer, nullable=False, server_default="0")
    is_completed = Column(Integer, nullable=False, server_default="0")
    is_legendary = Column(Integer, nullable=False, server_default="0")
    best_score_percent = Column(Integer, nullable=False, server_default="0")
    started_at = Column(Text, nullable=True)
    completed_at = Column(Text, nullable=True)
    last_practiced_at = Column(Text, nullable=True)
    updated_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))

    enrollment = relationship("CourseEnrollment", back_populates="level_progress")
    level = relationship("Level", back_populates="progress")


class LearnerLessonProgress(Base):
    __tablename__ = "learner_lesson_progress"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "lesson_id"),
        Index("ix_lesson_progress_enrollment", "enrollment_id", "lesson_id"),
        CheckConstraint("times_started >= 0", name="ck_lesson_progress_started"),
        CheckConstraint("times_completed >= 0", name="ck_lesson_progress_completed_count"),
        CheckConstraint(
            "best_score_percent BETWEEN 0 AND 100",
            name="ck_lesson_progress_best_score",
        ),
    )

    id = Column(Integer, primary_key=True)
    enrollment_id = Column(
        Integer,
        ForeignKey("course_enrollments.id", ondelete="CASCADE"),
        nullable=False,
    )
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    times_started = Column(Integer, nullable=False, server_default="0")
    times_completed = Column(Integer, nullable=False, server_default="0")
    best_score_percent = Column(Integer, nullable=False, server_default="0")
    first_started_at = Column(Text, nullable=True)
    first_completed_at = Column(Text, nullable=True)
    last_completed_at = Column(Text, nullable=True)
    updated_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))

    enrollment = relationship("CourseEnrollment", back_populates="lesson_progress")
    lesson = relationship("Lesson")


class LessonAttempt(Base):
    __tablename__ = "lesson_attempts"
    __table_args__ = (
        UniqueConstraint("attempt_token"),
        Index("ix_lesson_attempts_active", "enrollment_id", "status"),
        CheckConstraint(
            "attempt_mode IN ('standard', 'practice', 'review', 'legendary')",
            name="ck_lesson_attempts_mode",
        ),
        CheckConstraint(
            "status IN ('in_progress', 'completed', 'failed', 'abandoned')",
            name="ck_lesson_attempts_status",
        ),
        CheckConstraint("current_exercise_index >= 0", name="ck_attempts_current_index"),
        CheckConstraint("total_exercises > 0", name="ck_attempts_total_exercises"),
        CheckConstraint("correct_answers >= 0", name="ck_attempts_correct_answers"),
        CheckConstraint("wrong_answers >= 0", name="ck_attempts_wrong_answers"),
        CheckConstraint("xp_awarded >= 0", name="ck_attempts_xp_awarded"),
    )

    id = Column(Integer, primary_key=True)
    attempt_token = Column(Text, nullable=False)
    enrollment_id = Column(
        Integer,
        ForeignKey("course_enrollments.id", ondelete="CASCADE"),
        nullable=False,
    )
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="RESTRICT"), nullable=False)
    attempt_mode = Column(Text, nullable=False, server_default="standard")
    status = Column(Text, nullable=False, server_default="in_progress")
    current_exercise_index = Column(Integer, nullable=False, server_default="0")
    total_exercises = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False, server_default="0")
    wrong_answers = Column(Integer, nullable=False, server_default="0")
    starting_hearts = Column(Integer, nullable=False)
    ending_hearts = Column(Integer, nullable=True)
    xp_awarded = Column(Integer, nullable=False, server_default="0")
    started_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))
    last_activity_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))
    completed_at = Column(Text, nullable=True)

    enrollment = relationship("CourseEnrollment", back_populates="lesson_attempts")
    lesson = relationship("Lesson", back_populates="attempts")
    exercise_attempts = relationship(
        "ExerciseAttempt",
        back_populates="lesson_attempt",
        cascade="all, delete-orphan",
    )
    items = relationship(
        "LessonAttemptItem",
        back_populates="lesson_attempt",
        cascade="all, delete-orphan",
    )


class LessonAttemptItem(Base):
    __tablename__ = "lesson_attempt_items"
    __table_args__ = (
        UniqueConstraint("lesson_attempt_id", "position"),
        UniqueConstraint("lesson_attempt_id", "lesson_exercise_id"),
        Index("ix_lesson_attempt_items_attempt", "lesson_attempt_id", "position"),
        CheckConstraint("position > 0", name="ck_attempt_items_position"),
    )

    id = Column(Integer, primary_key=True)
    lesson_attempt_id = Column(
        Integer,
        ForeignKey("lesson_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    lesson_exercise_id = Column(
        Integer,
        ForeignKey("lesson_exercises.id", ondelete="RESTRICT"),
        nullable=False,
    )
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False)
    position = Column(Integer, nullable=False)
    created_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))

    lesson_attempt = relationship("LessonAttempt", back_populates="items")
    lesson_exercise = relationship("LessonExercise")
    exercise = relationship("Exercise")


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"
    __table_args__ = (
        UniqueConstraint("lesson_attempt_id", "presentation_order", "submission_number"),
        UniqueConstraint("lesson_attempt_id", "client_submission_id"),
        Index("ix_exercise_attempts_attempt", "lesson_attempt_id", "presentation_order"),
        CheckConstraint("json_valid(response_json)", name="ck_exercise_attempts_response_json"),
        CheckConstraint("is_correct IN (0, 1)", name="ck_exercise_attempts_correct"),
        CheckConstraint("heart_lost IN (0, 1)", name="ck_exercise_attempts_heart_lost"),
        CheckConstraint("presentation_order > 0", name="ck_exercise_attempts_order"),
        CheckConstraint("submission_number > 0", name="ck_exercise_attempts_submission"),
        CheckConstraint(
            "response_time_ms IS NULL OR response_time_ms >= 0",
            name="ck_exercise_attempts_response_time",
        ),
    )

    id = Column(Integer, primary_key=True)
    lesson_attempt_id = Column(
        Integer,
        ForeignKey("lesson_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    lesson_exercise_id = Column(
        Integer,
        ForeignKey("lesson_exercises.id", ondelete="RESTRICT"),
        nullable=False,
    )
    presentation_order = Column(Integer, nullable=False)
    submission_number = Column(Integer, nullable=False, server_default="1")
    response_json = Column(Text, nullable=False)
    client_submission_id = Column(Text, nullable=True)
    is_correct = Column(Integer, nullable=False)
    heart_lost = Column(Integer, nullable=False, server_default="0")
    feedback_text = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    answered_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))

    lesson_attempt = relationship("LessonAttempt", back_populates="exercise_attempts")
    lesson_exercise = relationship("LessonExercise")
