from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models


def get_completed_level_ids(progress_rows):
    return {row.level_id for row in progress_rows if row.is_completed}


def level_prerequisites_completed(level, completed_level_ids: set[int]) -> bool:
    return all(
        prerequisite.prerequisite_level_id in completed_level_ids
        for prerequisite in level.prerequisites
    )


def get_level_lesson_counts(db: Session, enrollment_id: int, level_id: int):
    total_lessons = (
        db.query(func.count(models.Lesson.id))
        .filter(models.Lesson.level_id == level_id, models.Lesson.is_published == 1)
        .scalar()
    )
    completed_lessons = (
        db.query(func.count(models.LearnerLessonProgress.id))
        .join(models.Lesson, models.Lesson.id == models.LearnerLessonProgress.lesson_id)
        .filter(
            models.LearnerLessonProgress.enrollment_id == enrollment_id,
            models.Lesson.level_id == level_id,
            models.Lesson.is_published == 1,
            models.LearnerLessonProgress.times_completed > 0,
        )
        .scalar()
    )
    return completed_lessons or 0, total_lessons or 0


def get_level_status(db: Session, enrollment, level, progress, completed_level_ids: set[int]):
    completed_lessons, total_lessons = get_level_lesson_counts(db, enrollment.id, level.id)
    progress_percent = round((completed_lessons / total_lessons) * 100) if total_lessons else 0
    has_started = (
        db.query(models.LearnerLessonProgress.id)
        .join(models.Lesson, models.Lesson.id == models.LearnerLessonProgress.lesson_id)
        .filter(
            models.LearnerLessonProgress.enrollment_id == enrollment.id,
            models.Lesson.level_id == level.id,
            models.LearnerLessonProgress.times_started > 0,
        )
        .first()
        is not None
    )
    prerequisites_completed = level_prerequisites_completed(level, completed_level_ids)

    if progress and progress.is_completed:
        status = "completed"
    elif has_started:
        status = "in_progress"
    elif prerequisites_completed:
        status = "available"
    else:
        status = "locked"

    return {
        "status": status,
        "isCurrent": enrollment.current_level_id == level.id,
        "completedLessons": completed_lessons,
        "totalPublishedLessons": total_lessons,
        "progressPercent": progress_percent,
    }


def get_first_available_level_progress(db: Session, enrollment):
    progress_rows = (
        db.query(models.LearnerLevelProgress)
        .join(models.Level)
        .filter(models.LearnerLevelProgress.enrollment_id == enrollment.id)
        .order_by(models.Level.id)
        .all()
    )
    progress_by_level_id = {row.level_id: row for row in progress_rows}
    completed_level_ids = get_completed_level_ids(progress_rows)

    for progress in progress_rows:
        status = get_level_status(
            db,
            enrollment,
            progress.level,
            progress,
            completed_level_ids,
        )
        if status["status"] in {"available", "in_progress"}:
            return progress

    return progress_rows[0] if progress_rows else None


def serialize_level_path_status(db: Session, enrollment, level, progress, completed_level_ids):
    status = get_level_status(db, enrollment, level, progress, completed_level_ids)
    return {
        "id": level.id,
        "title": level.title,
        "type": level.level_type,
        "position": level.position,
        "iconKey": level.icon_key,
        "status": status["status"],
        "isCurrent": status["isCurrent"],
        "completedLessons": status["completedLessons"],
        "totalPublishedLessons": status["totalPublishedLessons"],
        "progressPercent": status["progressPercent"],
        "isLegendary": bool(progress.is_legendary) if progress else False,
        "crownCount": progress.crown_count if progress else 0,
    }
