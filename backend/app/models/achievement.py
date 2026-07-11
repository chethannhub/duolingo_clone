from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Text, UniqueConstraint, text as sql_text

from app.database import Base


class Achievement(Base):
    __tablename__ = "achievements"
    __table_args__ = (
        UniqueConstraint("key"),
        CheckConstraint(
            "metric_type IN ('total_xp', 'current_streak', 'longest_streak', "
            "'lessons_completed', 'levels_completed', 'perfect_lessons')",
            name="ck_achievements_metric_type",
        ),
        CheckConstraint("reward_gems >= 0", name="ck_achievements_reward_gems"),
        CheckConstraint("is_active IN (0, 1)", name="ck_achievements_active"),
    )

    id = Column(Integer, primary_key=True)
    key = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    icon_key = Column(Text, nullable=False)
    metric_type = Column(Text, nullable=False)
    threshold_value = Column(Integer, nullable=False)
    reward_gems = Column(Integer, nullable=False, server_default="0")
    is_active = Column(Integer, nullable=False, server_default="1")
    created_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))


class LearnerAchievement(Base):
    __tablename__ = "learner_achievements"

    learner_id = Column(Integer, ForeignKey("learners.id", ondelete="CASCADE"), primary_key=True)
    achievement_id = Column(
        Integer,
        ForeignKey("achievements.id", ondelete="CASCADE"),
        primary_key=True,
    )
    progress_value = Column(Integer, nullable=False, server_default="0")
    unlocked_at = Column(Text, nullable=True)
    claimed_at = Column(Text, nullable=True)
    updated_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))
