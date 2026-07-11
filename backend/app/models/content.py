from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Integer, Text, UniqueConstraint, text as sql_text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class Language(Base):
    __tablename__ = "languages"
    __table_args__ = (
        UniqueConstraint("code"),
        CheckConstraint("is_active IN (0, 1)", name="ck_languages_is_active"),
    )

    id = Column(Integer, primary_key=True)
    code = Column(Text(collation="NOCASE"), nullable=False)
    name = Column(Text, nullable=False)
    native_name = Column(Text, nullable=True)
    is_active = Column(Integer, nullable=False, server_default="1")
    created_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))


class Course(TimestampMixin, Base):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("slug"),
        CheckConstraint("source_language_id <> target_language_id", name="ck_courses_language_pair"),
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="ck_courses_status",
        ),
        CheckConstraint("content_version > 0", name="ck_courses_content_version"),
        CheckConstraint("is_featured IN (0, 1)", name="ck_courses_is_featured"),
    )

    id = Column(Integer, primary_key=True)
    slug = Column(Text, nullable=False)
    source_language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    target_language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Text, nullable=False, server_default="draft")
    content_version = Column(Integer, nullable=False, server_default="1")
    is_featured = Column(Integer, nullable=False, server_default="0")
    published_at = Column(Text, nullable=True)

    source_language = relationship("Language", foreign_keys=[source_language_id])
    target_language = relationship("Language", foreign_keys=[target_language_id])
    sections = relationship("Section", back_populates="course", cascade="all, delete-orphan")


class Section(TimestampMixin, Base):
    __tablename__ = "sections"
    __table_args__ = (
        UniqueConstraint("course_id", "position"),
        Index("ix_sections_course", "course_id", "position"),
        CheckConstraint("position > 0", name="ck_sections_position"),
        CheckConstraint("is_published IN (0, 1)", name="ck_sections_is_published"),
    )

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    cefr_level = Column(Text, nullable=True)
    is_published = Column(Integer, nullable=False, server_default="0")

    course = relationship("Course", back_populates="sections")
    units = relationship("Unit", back_populates="section", cascade="all, delete-orphan")


class Unit(TimestampMixin, Base):
    __tablename__ = "units"
    __table_args__ = (
        UniqueConstraint("section_id", "position"),
        Index("ix_units_section", "section_id", "position"),
        CheckConstraint("position > 0", name="ck_units_position"),
        CheckConstraint("is_published IN (0, 1)", name="ck_units_is_published"),
    )

    id = Column(Integer, primary_key=True)
    section_id = Column(Integer, ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    guidebook_text = Column(Text, nullable=True)
    is_published = Column(Integer, nullable=False, server_default="0")

    section = relationship("Section", back_populates="units")
    levels = relationship("Level", back_populates="unit", cascade="all, delete-orphan")
    rewards = relationship("UnitReward", back_populates="unit", cascade="all, delete-orphan")
    path_items = relationship("UnitPathItem", back_populates="unit", cascade="all, delete-orphan")


class UnitReward(TimestampMixin, Base):
    __tablename__ = "unit_rewards"
    __table_args__ = (
        UniqueConstraint("unit_id", "seed_key"),
        CheckConstraint(
            "reward_type IN ('quest_chest', 'bonus_chest')",
            name="ck_unit_rewards_type",
        ),
        CheckConstraint("gems_reward >= 0", name="ck_unit_rewards_gems"),
        CheckConstraint("is_repeatable IN (0, 1)", name="ck_unit_rewards_repeatable"),
        CheckConstraint("required_completed_levels >= 0", name="ck_unit_rewards_required"),
    )

    id = Column(Integer, primary_key=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    seed_key = Column(Text, nullable=False)
    reward_type = Column(Text, nullable=False, server_default="quest_chest")
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    gems_reward = Column(Integer, nullable=False, server_default="0")
    icon_key = Column(Text, nullable=False, server_default="chest")
    is_repeatable = Column(Integer, nullable=False, server_default="0")
    required_completed_levels = Column(Integer, nullable=False, server_default="0")

    unit = relationship("Unit", back_populates="rewards")
    claims = relationship("UnitRewardClaim", back_populates="reward", cascade="all, delete-orphan")


class UnitRewardClaim(Base):
    __tablename__ = "unit_reward_claims"
    __table_args__ = (
        UniqueConstraint("learner_id", "reward_id"),
    )

    learner_id = Column(Integer, ForeignKey("learners.id", ondelete="CASCADE"), primary_key=True)
    reward_id = Column(Integer, ForeignKey("unit_rewards.id", ondelete="CASCADE"), primary_key=True)
    gems_awarded = Column(Integer, nullable=False, server_default="0")
    claimed_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))

    reward = relationship("UnitReward", back_populates="claims")


class UnitPathItem(Base):
    __tablename__ = "unit_path_items"
    __table_args__ = (
        UniqueConstraint("unit_id", "position"),
        Index("ix_unit_path_items_unit", "unit_id", "position"),
        CheckConstraint("position > 0", name="ck_unit_path_items_position"),
        CheckConstraint(
            "item_type IN ('level', 'reward')",
            name="ck_unit_path_items_type",
        ),
    )

    id = Column(Integer, primary_key=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)
    item_type = Column(Text, nullable=False)
    level_id = Column(Integer, ForeignKey("levels.id", ondelete="CASCADE"), nullable=True)
    reward_id = Column(Integer, ForeignKey("unit_rewards.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))

    unit = relationship("Unit", back_populates="path_items")
    level = relationship("Level")
    reward = relationship("UnitReward")


class Level(TimestampMixin, Base):
    __tablename__ = "levels"
    __table_args__ = (
        UniqueConstraint("unit_id", "position"),
        Index("ix_levels_unit", "unit_id", "position"),
        CheckConstraint("position > 0", name="ck_levels_position"),
        CheckConstraint(
            "level_type IN ('skill', 'practice', 'review', 'story', 'chest', 'legendary')",
            name="ck_levels_type",
        ),
        CheckConstraint("reward_gems >= 0", name="ck_levels_reward_gems"),
        CheckConstraint("is_published IN (0, 1)", name="ck_levels_is_published"),
    )

    id = Column(Integer, primary_key=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)
    level_type = Column(Text, nullable=False, server_default="skill")
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    icon_key = Column(Text, nullable=False, server_default="star")
    reward_gems = Column(Integer, nullable=False, server_default="0")
    is_published = Column(Integer, nullable=False, server_default="0")

    unit = relationship("Unit", back_populates="levels")
    lessons = relationship("Lesson", back_populates="level", cascade="all, delete-orphan")
    prerequisites = relationship(
        "LevelPrerequisite",
        foreign_keys="LevelPrerequisite.level_id",
        back_populates="level",
        cascade="all, delete-orphan",
    )
    progress = relationship("LearnerLevelProgress", back_populates="level")


class LevelPrerequisite(Base):
    __tablename__ = "level_prerequisites"
    __table_args__ = (
        CheckConstraint("level_id <> prerequisite_level_id", name="ck_level_prerequisites_not_self"),
    )

    level_id = Column(Integer, ForeignKey("levels.id", ondelete="CASCADE"), primary_key=True)
    prerequisite_level_id = Column(
        Integer,
        ForeignKey("levels.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))

    level = relationship("Level", foreign_keys=[level_id], back_populates="prerequisites")
    prerequisite_level = relationship("Level", foreign_keys=[prerequisite_level_id])


class Lesson(TimestampMixin, Base):
    __tablename__ = "lessons"
    __table_args__ = (
        UniqueConstraint("level_id", "position"),
        Index("ix_lessons_level", "level_id", "position"),
        CheckConstraint("position > 0", name="ck_lessons_position"),
        CheckConstraint("xp_reward >= 0", name="ck_lessons_xp_reward"),
        CheckConstraint("estimated_minutes > 0", name="ck_lessons_estimated_minutes"),
        CheckConstraint("is_published IN (0, 1)", name="ck_lessons_is_published"),
    )

    id = Column(Integer, primary_key=True)
    level_id = Column(Integer, ForeignKey("levels.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    xp_reward = Column(Integer, nullable=False, server_default="10")
    estimated_minutes = Column(Integer, nullable=False, server_default="3")
    is_published = Column(Integer, nullable=False, server_default="0")

    level = relationship("Level", back_populates="lessons")
    lesson_exercises = relationship(
        "LessonExercise",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )
    attempts = relationship("LessonAttempt", back_populates="lesson")
