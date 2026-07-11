from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Integer, Text, UniqueConstraint, text as sql_text
from sqlalchemy.orm import relationship

from app.database import Base


class LearnerStats(Base):
    __tablename__ = "learner_stats"
    __table_args__ = (
        CheckConstraint("total_xp >= 0", name="ck_stats_total_xp"),
        CheckConstraint("current_hearts >= 0", name="ck_stats_current_hearts"),
        CheckConstraint("max_hearts > 0", name="ck_stats_max_hearts"),
        CheckConstraint(
            "current_hearts <= max_hearts OR unlimited_hearts = 1",
            name="ck_stats_hearts_limit",
        ),
        CheckConstraint("unlimited_hearts IN (0, 1)", name="ck_stats_unlimited_hearts"),
        CheckConstraint("gems >= 0", name="ck_stats_gems"),
        CheckConstraint("current_streak >= 0", name="ck_stats_current_streak"),
        CheckConstraint("longest_streak >= current_streak", name="ck_stats_longest_streak"),
        CheckConstraint("daily_goal_xp > 0", name="ck_stats_daily_goal_xp"),
        CheckConstraint("streak_freezes >= 0", name="ck_stats_streak_freezes"),
    )

    learner_id = Column(Integer, ForeignKey("learners.id", ondelete="CASCADE"), primary_key=True)
    total_xp = Column(Integer, nullable=False, server_default="0")
    current_hearts = Column(Integer, nullable=False, server_default="5")
    max_hearts = Column(Integer, nullable=False, server_default="5")
    unlimited_hearts = Column(Integer, nullable=False, server_default="0")
    next_heart_at = Column(Text, nullable=True)
    heart_regen_seconds = Column(Integer, nullable=False, server_default="14400")
    gems = Column(Integer, nullable=False, server_default="0")
    current_streak = Column(Integer, nullable=False, server_default="0")
    longest_streak = Column(Integer, nullable=False, server_default="0")
    last_streak_date = Column(Text, nullable=True)
    daily_goal_xp = Column(Integer, nullable=False, server_default="20")
    streak_freezes = Column(Integer, nullable=False, server_default="0")
    updated_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))

    learner = relationship("Learner", back_populates="stats")


class XpEvent(Base):
    __tablename__ = "xp_events"
    __table_args__ = (
        UniqueConstraint("event_key"),
        Index("ix_xp_events_leaderboard", "occurred_at", "learner_id"),
        Index("ix_xp_events_learner_date", "learner_id", "local_date"),
        CheckConstraint(
            "source_type IN ('lesson_completion', 'practice', 'review', 'legendary', "
            "'achievement', 'bonus', 'seed', 'adjustment')",
            name="ck_xp_events_source",
        ),
        CheckConstraint("amount <> 0", name="ck_xp_events_amount"),
        CheckConstraint("json_valid(metadata_json)", name="ck_xp_events_metadata_json"),
    )

    id = Column(Integer, primary_key=True)
    learner_id = Column(Integer, ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    enrollment_id = Column(Integer, ForeignKey("course_enrollments.id"), nullable=True)
    lesson_attempt_id = Column(Integer, ForeignKey("lesson_attempts.id"), nullable=True)
    source_type = Column(Text, nullable=False)
    amount = Column(Integer, nullable=False)
    event_key = Column(Text, nullable=False)
    local_date = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=False, server_default="{}")
    occurred_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))


class HeartEvent(Base):
    __tablename__ = "heart_events"
    __table_args__ = (
        UniqueConstraint("event_key"),
        Index("ix_heart_events_learner", "learner_id", "occurred_at"),
        CheckConstraint(
            "event_type IN ('mistake', 'regeneration', 'practice_refill', 'gems_refill', "
            "'lesson_bonus', 'seed', 'adjustment')",
            name="ck_heart_events_type",
        ),
        CheckConstraint("delta <> 0", name="ck_heart_events_delta"),
        CheckConstraint("json_valid(metadata_json)", name="ck_heart_events_metadata_json"),
    )

    id = Column(Integer, primary_key=True)
    learner_id = Column(Integer, ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    lesson_attempt_id = Column(Integer, ForeignKey("lesson_attempts.id"), nullable=True)
    exercise_attempt_id = Column(Integer, ForeignKey("exercise_attempts.id"), nullable=True)
    event_type = Column(Text, nullable=False)
    delta = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    event_key = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=False, server_default="{}")
    occurred_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))


class LearnerDailyActivity(Base):
    __tablename__ = "learner_daily_activity"
    __table_args__ = (
        UniqueConstraint("learner_id", "local_date"),
        Index("ix_daily_activity_learner_date", "learner_id", "local_date"),
        CheckConstraint("xp_earned >= 0", name="ck_daily_activity_xp"),
        CheckConstraint("lessons_completed >= 0", name="ck_daily_activity_lessons"),
        CheckConstraint("exercises_answered >= 0", name="ck_daily_activity_exercises"),
        CheckConstraint("streak_qualified IN (0, 1)", name="ck_daily_activity_streak"),
        CheckConstraint("daily_goal_reached IN (0, 1)", name="ck_daily_activity_goal"),
    )

    id = Column(Integer, primary_key=True)
    learner_id = Column(Integer, ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    local_date = Column(Text, nullable=False)
    xp_earned = Column(Integer, nullable=False, server_default="0")
    lessons_completed = Column(Integer, nullable=False, server_default="0")
    exercises_answered = Column(Integer, nullable=False, server_default="0")
    streak_qualified = Column(Integer, nullable=False, server_default="0")
    daily_goal_reached = Column(Integer, nullable=False, server_default="0")
    first_activity_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))
    last_activity_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))
