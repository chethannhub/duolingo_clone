from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Text, UniqueConstraint, text as sql_text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class Learner(TimestampMixin, Base):
    __tablename__ = "learners"
    __table_args__ = (
        UniqueConstraint("username", sqlite_on_conflict="ABORT"),
        UniqueConstraint("email", sqlite_on_conflict="ABORT"),
        CheckConstraint("is_active IN (0, 1)", name="ck_learners_is_active"),
    )

    id = Column(Integer, primary_key=True)
    username = Column(Text(collation="NOCASE"), nullable=False)
    email = Column(Text(collation="NOCASE"), nullable=True)
    display_name = Column(Text, nullable=False)
    avatar_url = Column(Text, nullable=True)
    timezone = Column(Text, nullable=False, server_default="UTC")
    locale = Column(Text, nullable=False, server_default="en")
    is_active = Column(Integer, nullable=False, server_default="1")

    settings = relationship(
        "LearnerSettings",
        back_populates="learner",
        cascade="all, delete-orphan",
        uselist=False,
    )
    stats = relationship(
        "LearnerStats",
        back_populates="learner",
        cascade="all, delete-orphan",
        uselist=False,
    )
    enrollments = relationship("CourseEnrollment", back_populates="learner")
    daily_activity = relationship("LearnerDailyActivity")


class LearnerSettings(Base):
    __tablename__ = "learner_settings"
    __table_args__ = (
        CheckConstraint("sound_effects_enabled IN (0, 1)", name="ck_settings_sound"),
        CheckConstraint("animations_enabled IN (0, 1)", name="ck_settings_animations"),
        CheckConstraint(
            "listening_exercises_enabled IN (0, 1)",
            name="ck_settings_listening",
        ),
        CheckConstraint(
            "motivational_messages_enabled IN (0, 1)",
            name="ck_settings_motivation",
        ),
        CheckConstraint("leaderboard_enabled IN (0, 1)", name="ck_settings_leaderboard"),
        CheckConstraint("dark_mode_enabled IN (0, 1)", name="ck_settings_dark_mode"),
    )

    learner_id = Column(Integer, ForeignKey("learners.id", ondelete="CASCADE"), primary_key=True)
    sound_effects_enabled = Column(Integer, nullable=False, server_default="1")
    animations_enabled = Column(Integer, nullable=False, server_default="1")
    listening_exercises_enabled = Column(Integer, nullable=False, server_default="1")
    motivational_messages_enabled = Column(Integer, nullable=False, server_default="1")
    leaderboard_enabled = Column(Integer, nullable=False, server_default="1")
    dark_mode_enabled = Column(Integer, nullable=False, server_default="0")
    daily_reminder_time = Column(Text, nullable=True)
    updated_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))

    learner = relationship("Learner", back_populates="settings")
