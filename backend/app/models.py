from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Learner(Base):
    __tablename__ = "learners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    avatar_url = Column(String, nullable=True)

    total_xp = Column(Integer, default=0)
    today_xp = Column(Integer, default=0)
    daily_xp_goal = Column(Integer, default=30)

    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(Date, nullable=True)

    hearts = Column(Integer, default=5)
    max_hearts = Column(Integer, default=5)
    gems = Column(Integer, default=500)
    last_heart_refill_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    progress = relationship("LearnerProgress", back_populates="learner")
    lesson_attempts = relationship("LessonAttempt", back_populates="learner")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source_language = Column(String, nullable=False)
    target_language = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    sections = relationship("Section", back_populates="course")


class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)

    course = relationship("Course", back_populates="sections")
    units = relationship("Unit", back_populates="section")


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)

    section = relationship("Section", back_populates="units")
    levels = relationship("Level", back_populates="unit")


class Level(Base):
    __tablename__ = "levels"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)

    title = Column(String, nullable=False)
    type = Column(String, default="lesson")  
    icon = Column(String, nullable=True)
    order_index = Column(Integer, nullable=False)

    required_level_id = Column(Integer, ForeignKey("levels.id"), nullable=True)

    unit = relationship("Unit", back_populates="levels")
    lessons = relationship("Lesson", back_populates="level")
    progress = relationship("LearnerProgress", back_populates="level")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    level_id = Column(Integer, ForeignKey("levels.id"), nullable=False)

    title = Column(String, nullable=False)
    order_index = Column(Integer, nullable=False)
    xp_reward = Column(Integer, default=10)

    level = relationship("Level", back_populates="lessons")
    exercises = relationship("Exercise", back_populates="lesson")
    attempts = relationship("LessonAttempt", back_populates="lesson")


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)

    type = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    prompt = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)

    lesson = relationship("Lesson", back_populates="exercises")
    options = relationship("ExerciseOption", back_populates="exercise")
    attempts = relationship("ExerciseAttempt", back_populates="exercise")


class ExerciseOption(Base):
    __tablename__ = "exercise_options"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)

    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)

    # Used for match-pairs exercise
    pair_key = Column(String, nullable=True)

    exercise = relationship("Exercise", back_populates="options")


class LearnerProgress(Base):
    __tablename__ = "learner_progress"

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), nullable=False)
    level_id = Column(Integer, ForeignKey("levels.id"), nullable=False)

    completed_lessons = Column(Integer, default=0)
    total_lessons = Column(Integer, default=0)

    crown_level = Column(Integer, default=0)
    is_unlocked = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    learner = relationship("Learner", back_populates="progress")
    level = relationship("Level", back_populates="progress")


class LessonAttempt(Base):
    __tablename__ = "lesson_attempts"

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)

    status = Column(String, default="in_progress")

    correct_count = Column(Integer, default=0)
    wrong_count = Column(Integer, default=0)
    xp_earned = Column(Integer, default=0)

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    learner = relationship("Learner", back_populates="lesson_attempts")
    lesson = relationship("Lesson", back_populates="attempts")
    exercise_attempts = relationship("ExerciseAttempt", back_populates="lesson_attempt")


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"

    id = Column(Integer, primary_key=True, index=True)
    lesson_attempt_id = Column(Integer, ForeignKey("lesson_attempts.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)

    learner_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=False)

    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    lesson_attempt = relationship("LessonAttempt", back_populates="exercise_attempts")
    exercise = relationship("Exercise", back_populates="attempts")


class LeaderboardEntry(Base):
    __tablename__ = "leaderboard_entries"

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), nullable=False)

    weekly_xp = Column(Integer, default=0)
    rank = Column(Integer, nullable=True)


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)

    condition_type = Column(String, nullable=False)
    condition_value = Column(Integer, nullable=False)


class LearnerAchievement(Base):
    __tablename__ = "learner_achievements"

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("learners.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)

    unlocked_at = Column(DateTime(timezone=True), server_default=func.now())