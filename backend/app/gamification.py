import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_text() -> str:
    return utc_now().replace(tzinfo=None).isoformat()


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def learner_timezone(learner) -> timezone:
    try:
        return ZoneInfo(learner.timezone or "UTC")
    except ZoneInfoNotFoundError:
        if learner.timezone == "Asia/Kolkata":
            return timezone(timedelta(hours=5, minutes=30))
        return timezone.utc


def learner_local_date(learner, at: datetime | None = None) -> str:
    return (at or utc_now()).astimezone(learner_timezone(learner)).date().isoformat()


def regenerate_hearts(db: Session, learner, stats) -> int:
    if stats.unlimited_hearts:
        return 0
    if stats.current_hearts >= stats.max_hearts:
        stats.next_heart_at = None
        return 0

    now = utc_now()
    interval = max(1, stats.heart_regen_seconds)
    next_heart_at = parse_utc(stats.next_heart_at)
    if next_heart_at is None:
        stats.next_heart_at = (now + timedelta(seconds=interval)).replace(tzinfo=None).isoformat()
        stats.updated_at = utc_now_text()
        return 0
    if now < next_heart_at:
        return 0

    intervals = int((now - next_heart_at).total_seconds() // interval) + 1
    missing_hearts = stats.max_hearts - stats.current_hearts
    regenerated = min(intervals, missing_hearts)
    if regenerated <= 0:
        return 0

    stats.current_hearts += regenerated
    if stats.current_hearts >= stats.max_hearts:
        stats.next_heart_at = None
    else:
        stats.next_heart_at = (
            next_heart_at + timedelta(seconds=intervals * interval)
        ).replace(tzinfo=None).isoformat()
    stats.updated_at = utc_now_text()
    db.add(
        models.HeartEvent(
            learner_id=learner.id,
            event_type="regeneration",
            delta=regenerated,
            balance_after=stats.current_hearts,
            event_key=f"heart-regeneration:{learner.id}:{next_heart_at.replace(tzinfo=None).isoformat()}",
            metadata_json=json.dumps({"intervals": intervals}),
        )
    )
    return regenerated


def schedule_next_heart_if_needed(stats):
    if stats.unlimited_hearts or stats.current_hearts >= stats.max_hearts:
        stats.next_heart_at = None
        return
    if stats.next_heart_at is None:
        stats.next_heart_at = (
            utc_now() + timedelta(seconds=max(1, stats.heart_regen_seconds))
        ).replace(tzinfo=None).isoformat()
        stats.updated_at = utc_now_text()


def apply_streak_for_qualifying_lesson(learner, stats, local_date: str):
    current_date = datetime.fromisoformat(local_date).date()
    previous_date = datetime.fromisoformat(stats.last_streak_date).date() if stats.last_streak_date else None

    if previous_date == current_date:
        return
    if previous_date == current_date - timedelta(days=1):
        stats.current_streak += 1
    else:
        stats.current_streak = 1

    stats.longest_streak = max(stats.longest_streak, stats.current_streak)
    stats.last_streak_date = local_date
    stats.updated_at = utc_now_text()


def get_or_create_daily_activity(db: Session, learner, local_date: str):
    activity = (
        db.query(models.LearnerDailyActivity)
        .filter(
            models.LearnerDailyActivity.learner_id == learner.id,
            models.LearnerDailyActivity.local_date == local_date,
        )
        .first()
    )
    if activity:
        return activity

    now = utc_now_text()
    activity = models.LearnerDailyActivity(
        learner_id=learner.id,
        local_date=local_date,
        first_activity_at=now,
        last_activity_at=now,
    )
    db.add(activity)
    return activity


def metric_value(db: Session, learner_id: int, metric_type: str) -> int:
    stats = db.get(models.LearnerStats, learner_id)
    if metric_type == "total_xp":
        return stats.total_xp if stats else 0
    if metric_type == "current_streak":
        return stats.current_streak if stats else 0
    if metric_type == "longest_streak":
        return stats.longest_streak if stats else 0
    if metric_type == "lessons_completed":
        return (
            db.query(func.coalesce(func.sum(models.LearnerLessonProgress.times_completed), 0))
            .join(models.CourseEnrollment)
            .filter(models.CourseEnrollment.learner_id == learner_id)
            .scalar()
        )
    if metric_type == "levels_completed":
        return (
            db.query(models.LearnerLevelProgress)
            .join(models.CourseEnrollment)
            .filter(
                models.CourseEnrollment.learner_id == learner_id,
                models.LearnerLevelProgress.is_completed == 1,
            )
            .count()
        )
    if metric_type == "perfect_lessons":
        return (
            db.query(models.LessonAttempt)
            .join(models.CourseEnrollment)
            .filter(
                models.CourseEnrollment.learner_id == learner_id,
                models.LessonAttempt.status == "completed",
                models.LessonAttempt.wrong_answers == 0,
            )
            .count()
        )
    return 0


def check_and_unlock_achievements(db: Session, learner, local_date: str):
    unlocked = []
    achievements = (
        db.query(models.Achievement)
        .filter(models.Achievement.is_active == 1)
        .all()
    )
    for achievement in achievements:
        progress_value = metric_value(db, learner.id, achievement.metric_type)
        learner_achievement = db.get(
            models.LearnerAchievement,
            {
                "learner_id": learner.id,
                "achievement_id": achievement.id,
            },
        )
        if not learner_achievement:
            learner_achievement = models.LearnerAchievement(
                learner_id=learner.id,
                achievement_id=achievement.id,
            )
            db.add(learner_achievement)
        learner_achievement.progress_value = progress_value
        learner_achievement.updated_at = utc_now_text()
        if progress_value >= achievement.threshold_value and not learner_achievement.unlocked_at:
            learner_achievement.unlocked_at = utc_now_text()
            unlocked.append(achievement)
    return unlocked
