import json
import uuid
from datetime import datetime, timedelta

from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload

from app import models
from app.core.exceptions import ApiError, ErrorCode
from app.evaluators import EVALUATORS
from app.gamification import (
    apply_streak_for_qualifying_lesson,
    check_and_unlock_achievements,
    get_or_create_daily_activity,
    learner_local_date,
    regenerate_hearts,
    schedule_next_heart_if_needed,
    utc_now,
    utc_now_text,
)
from app.path_status import get_completed_level_ids, get_level_lesson_counts, get_level_status


def normalize_answer(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def get_stats(learner: models.Learner) -> models.LearnerStats:
    if not learner.stats:
        learner.stats = models.LearnerStats(learner_id=learner.id)
    return learner.stats


def get_selected_enrollment(db: Session, learner_id: int) -> models.CourseEnrollment:
    enrollment = (
        db.query(models.CourseEnrollment)
        .options(joinedload(models.CourseEnrollment.course))
        .filter(
            models.CourseEnrollment.learner_id == learner_id,
            models.CourseEnrollment.is_selected == 1,
            models.CourseEnrollment.status == "active",
        )
        .first()
    )
    if not enrollment:
        raise ApiError(404, ErrorCode.COURSE_NOT_ENROLLED, "No active course enrollment was found.")
    return enrollment


def idempotency_get(db: Session, learner_id: int, scope: str, key: str | None):
    if not key:
        return None
    record = (
        db.query(models.IdempotencyRecord)
        .filter_by(learner_id=learner_id, scope=scope, idempotency_key=key)
        .first()
    )
    return json.loads(record.response_json) if record else None


def idempotency_store(db: Session, learner_id: int, scope: str, key: str | None, response: dict):
    if not key:
        return
    if idempotency_get(db, learner_id, scope, key):
        return
    db.add(
        models.IdempotencyRecord(
            learner_id=learner_id,
            scope=scope,
            idempotency_key=key,
            response_json=json.dumps(response),
        )
    )


def learner_summary(db: Session, learner: models.Learner):
    stats = get_stats(learner)
    today = learner_local_date(learner)
    today_activity = (
        db.query(models.LearnerDailyActivity)
        .filter_by(learner_id=learner.id, local_date=today)
        .first()
    )
    return {
        "id": learner.id,
        "username": learner.username,
        "displayName": learner.display_name,
        "avatarUrl": learner.avatar_url,
        "timezone": learner.timezone,
        "locale": learner.locale,
        "streak": stats.current_streak,
        "totalXp": stats.total_xp,
        "todayXp": today_activity.xp_earned if today_activity else 0,
        "dailyGoalXp": stats.daily_goal_xp,
        "hearts": stats.current_hearts,
        "maxHearts": stats.max_hearts,
        "nextHeartAt": stats.next_heart_at,
        "gems": stats.gems,
    }


def frontend_safe_exercise(link: models.LessonExercise | models.LessonAttemptItem):
    exercise = link.exercise
    position = getattr(link, "position", None) or getattr(link, "presentation_order", None)
    options = []
    if exercise.exercise_type == "match_pairs":
        for pair in exercise.match_pairs:
            options.append({"id": f"left-{pair.id}", "text": pair.left_text, "side": "left"})
            options.append({"id": f"right-{pair.id}", "text": pair.right_text, "side": "right"})
    else:
        options = [
            {"id": option.id, "text": option.option_text}
            for option in sorted(exercise.options, key=lambda item: item.position)
        ]
    return {
        "id": exercise.id,
        "type": exercise.exercise_type,
        "instruction": exercise.instruction_text,
        "prompt": exercise.prompt_text,
        "hint": exercise.hint_text,
        "audioUrl": exercise.audio_url,
        "imageUrl": exercise.image_url,
        "orderIndex": position,
        "options": options,
    }


def course_summary(course: models.Course):
    return {
        "id": course.id,
        "slug": course.slug,
        "title": course.title,
        "description": course.description,
        "sourceLanguage": course.source_language.code if course.source_language else None,
        "targetLanguage": course.target_language.code if course.target_language else None,
        "contentVersion": course.content_version,
    }


def list_courses(db: Session):
    courses = (
        db.query(models.Course)
        .options(joinedload(models.Course.source_language), joinedload(models.Course.target_language))
        .filter(models.Course.status == "published")
        .order_by(models.Course.id)
        .all()
    )
    return {"courses": [course_summary(course) for course in courses]}


def get_course_by_slug(db: Session, slug: str):
    course = (
        db.query(models.Course)
        .options(joinedload(models.Course.source_language), joinedload(models.Course.target_language))
        .filter(models.Course.slug == slug)
        .first()
    )
    if not course:
        raise ApiError(404, ErrorCode.COURSE_NOT_FOUND, "Course not found.")
    return course_summary(course)


def get_course_sections(db: Session, course_id: int):
    sections = (
        db.query(models.Section)
        .filter_by(course_id=course_id, is_published=1)
        .order_by(models.Section.position)
        .all()
    )
    return {
        "sections": [
            {
                "id": section.id,
                "courseId": section.course_id,
                "position": section.position,
                "title": section.title,
                "description": section.description,
                "cefrLevel": section.cefr_level,
            }
            for section in sections
        ]
    }


def get_section_units(db: Session, section_id: int):
    units = (
        db.query(models.Unit)
        .filter_by(section_id=section_id, is_published=1)
        .order_by(models.Unit.position)
        .all()
    )
    return {"units": [serialize_unit_shell(unit) for unit in units]}


def serialize_unit_shell(unit: models.Unit):
    return {
        "id": unit.id,
        "sectionId": unit.section_id,
        "position": unit.position,
        "title": unit.title,
        "description": unit.description,
        "guidebookText": unit.guidebook_text,
    }


def get_unit(db: Session, unit_id: int):
    unit = db.get(models.Unit, unit_id)
    if not unit:
        raise ApiError(404, ErrorCode.LESSON_NOT_FOUND, "Unit not found.")
    return serialize_unit_shell(unit)


def get_unit_guidebook(db: Session, unit_id: int):
    unit = db.get(models.Unit, unit_id)
    if not unit:
        raise ApiError(404, ErrorCode.LESSON_NOT_FOUND, "Unit not found.")
    return {"unitId": unit.id, "title": unit.title, "guidebookText": unit.guidebook_text}


def get_level_lessons(db: Session, level_id: int):
    lessons = (
        db.query(models.Lesson)
        .filter_by(level_id=level_id, is_published=1)
        .order_by(models.Lesson.position)
        .all()
    )
    return {
        "lessons": [
            {
                "id": lesson.id,
                "levelId": lesson.level_id,
                "position": lesson.position,
                "title": lesson.title,
                "xpReward": lesson.xp_reward,
                "estimatedMinutes": lesson.estimated_minutes,
            }
            for lesson in lessons
        ]
    }


def get_lesson_preview(db: Session, lesson_id: int):
    lesson = (
        db.query(models.Lesson)
        .options(joinedload(models.Lesson.lesson_exercises).joinedload(models.LessonExercise.exercise))
        .filter_by(id=lesson_id)
        .first()
    )
    if not lesson:
        raise ApiError(404, ErrorCode.LESSON_NOT_FOUND, "Lesson not found.")
    return {
        "id": lesson.id,
        "title": lesson.title,
        "xpReward": lesson.xp_reward,
        "estimatedMinutes": lesson.estimated_minutes,
        "exerciseCount": len(lesson.lesson_exercises),
    }


def learning_path(db: Session, learner: models.Learner, section_id: int | None = None):
    enrollment = get_selected_enrollment(db, learner.id)
    stats = get_stats(learner)
    regenerate_hearts(db, learner, stats)
    progress_rows = (
        db.query(models.LearnerLevelProgress)
        .filter_by(enrollment_id=enrollment.id)
        .all()
    )
    progress_by_level = {row.level_id: row for row in progress_rows}
    completed_level_ids = get_completed_level_ids(progress_rows)
    lesson_progress = {
        row.lesson_id: row
        for row in db.query(models.LearnerLessonProgress)
        .filter_by(enrollment_id=enrollment.id)
        .all()
    }
    claimed_rewards = {
        row.reward_id
        for row in db.query(models.UnitRewardClaim)
        .filter_by(learner_id=learner.id)
        .all()
    }
    section_query = (
        db.query(models.Section)
        .options(
            joinedload(models.Section.units).joinedload(models.Unit.path_items).joinedload(models.UnitPathItem.level).joinedload(models.Level.lessons),
            joinedload(models.Section.units).joinedload(models.Unit.path_items).joinedload(models.UnitPathItem.reward),
            joinedload(models.Section.units).joinedload(models.Unit.levels).joinedload(models.Level.prerequisites),
        )
        .filter(models.Section.course_id == enrollment.course_id, models.Section.is_published == 1)
    )
    if section_id:
        section_query = section_query.filter(models.Section.id == section_id)
    sections = section_query.order_by(models.Section.position).all()

    response_sections = []
    for section in sections:
        response_units = []
        for unit in sorted((item for item in section.units if item.is_published), key=lambda item: item.position):
            path_items = []
            completed_in_unit = sum(
                1
                for level in unit.levels
                if progress_by_level.get(level.id) and progress_by_level[level.id].is_completed
            )
            for item in sorted(unit.path_items, key=lambda row: row.position):
                if item.item_type == "level" and item.level:
                    progress = progress_by_level.get(item.level_id)
                    status = get_level_status(db, enrollment, item.level, progress, completed_level_ids)
                    state = status["status"]
                    if state == "in_progress" or status["isCurrent"]:
                        state = "current"
                    path_items.append(
                        {
                            "id": item.id,
                            "type": "level",
                            "position": item.position,
                            "state": state,
                            "level": {
                                "id": item.level.id,
                                "title": item.level.title,
                                "iconKey": item.level.icon_key,
                                "type": item.level.level_type,
                                "completedLessons": status["completedLessons"],
                                "totalLessons": status["totalPublishedLessons"],
                                "progressPercent": status["progressPercent"],
                                "crownCount": progress.crown_count if progress else 0,
                                "lessons": [
                                    {
                                        "id": lesson.id,
                                        "title": lesson.title,
                                        "position": lesson.position,
                                        "completed": bool(
                                            lesson_progress.get(lesson.id)
                                            and lesson_progress[lesson.id].times_completed
                                        ),
                                    }
                                    for lesson in sorted(
                                        (lesson for lesson in item.level.lessons if lesson.is_published),
                                        key=lambda row: row.position,
                                    )
                                ],
                            },
                        }
                    )
                elif item.item_type == "reward" and item.reward:
                    claimed = item.reward.id in claimed_rewards
                    unlocked = completed_in_unit >= item.reward.required_completed_levels
                    path_items.append(
                        {
                            "id": item.id,
                            "type": "reward",
                            "position": item.position,
                            "state": "claimed" if claimed else "claimable" if unlocked else "locked",
                            "reward": {
                                "id": item.reward.id,
                                "title": item.reward.title,
                                "description": item.reward.description,
                                "iconKey": item.reward.icon_key,
                                "gemsReward": item.reward.gems_reward,
                            },
                        }
                    )
            response_units.append({**serialize_unit_shell(unit), "pathItems": path_items})
        response_sections.append(
            {
                "id": section.id,
                "title": section.title,
                "position": section.position,
                "description": section.description,
                "units": response_units,
            }
        )

    db.commit()
    return {
        "learner": learner_summary(db, learner),
        "activeCourse": course_summary(enrollment.course),
        "topBar": {
            "streak": stats.current_streak,
            "totalXp": stats.total_xp,
            "hearts": stats.current_hearts,
            "maxHearts": stats.max_hearts,
            "gems": stats.gems,
        },
        "dailyGoal": {
            "targetXp": stats.daily_goal_xp,
            "todayXp": learner_summary(db, learner)["todayXp"],
            "reached": learner_summary(db, learner)["todayXp"] >= stats.daily_goal_xp,
        },
        "sections": response_sections,
    }


def get_attempt_by_token(db: Session, learner: models.Learner, attempt_token: str):
    attempt = (
        db.query(models.LessonAttempt)
        .options(
            joinedload(models.LessonAttempt.enrollment),
            joinedload(models.LessonAttempt.items).joinedload(models.LessonAttemptItem.exercise).joinedload(models.Exercise.options),
            joinedload(models.LessonAttempt.items).joinedload(models.LessonAttemptItem.exercise).joinedload(models.Exercise.match_pairs),
            joinedload(models.LessonAttempt.items).joinedload(models.LessonAttemptItem.exercise).joinedload(models.Exercise.accepted_answers),
        )
        .filter(models.LessonAttempt.attempt_token == attempt_token)
        .first()
    )
    if not attempt or attempt.enrollment.learner_id != learner.id:
        raise ApiError(404, ErrorCode.ATTEMPT_NOT_FOUND, "Lesson attempt not found.")
    return attempt


def attempt_response(db: Session, learner: models.Learner, attempt: models.LessonAttempt):
    answered_positions = {
        row.presentation_order
        for row in db.query(models.ExerciseAttempt)
        .filter_by(lesson_attempt_id=attempt.id)
        .all()
    }
    next_item = next(
        (
            item
            for item in sorted(attempt.items, key=lambda row: row.position)
            if item.position not in answered_positions
        ),
        None,
    )
    return {
        "attemptToken": attempt.attempt_token,
        "status": attempt.status,
        "mode": attempt.attempt_mode,
        "lessonId": attempt.lesson_id,
        "currentExerciseIndex": attempt.current_exercise_index,
        "totalExercises": attempt.total_exercises,
        "correctCount": attempt.correct_answers,
        "wrongCount": attempt.wrong_answers,
        "learner": learner_summary(db, learner),
        "currentExercise": frontend_safe_exercise(next_item) if next_item and attempt.status == "in_progress" else None,
    }


def start_lesson_attempt(
    db: Session,
    learner: models.Learner,
    lesson_id: int,
    mode: str,
    idempotency_key: str | None,
):
    cached = idempotency_get(db, learner.id, "start_lesson", idempotency_key)
    if cached:
        return cached
    lesson = (
        db.query(models.Lesson)
        .options(
            joinedload(models.Lesson.level).joinedload(models.Level.unit).joinedload(models.Unit.section),
            joinedload(models.Lesson.lesson_exercises).joinedload(models.LessonExercise.exercise).joinedload(models.Exercise.options),
            joinedload(models.Lesson.lesson_exercises).joinedload(models.LessonExercise.exercise).joinedload(models.Exercise.match_pairs),
        )
        .filter(models.Lesson.id == lesson_id)
        .first()
    )
    if not lesson:
        raise ApiError(404, ErrorCode.LESSON_NOT_FOUND, "Lesson not found.")
    enrollment = get_selected_enrollment(db, learner.id)
    stats = get_stats(learner)
    regenerate_hearts(db, learner, stats)
    if lesson.level.unit.section.course_id != enrollment.course_id or not lesson.is_published:
        raise ApiError(400, ErrorCode.LESSON_NOT_AVAILABLE, "Lesson is not available in the active course.")
    progress_rows = db.query(models.LearnerLevelProgress).filter_by(enrollment_id=enrollment.id).all()
    progress = next((row for row in progress_rows if row.level_id == lesson.level_id), None)
    status = get_level_status(db, enrollment, lesson.level, progress, get_completed_level_ids(progress_rows))
    if status["status"] == "locked" and mode == "standard":
        raise ApiError(403, ErrorCode.LEVEL_LOCKED, "Complete the previous level before starting this lesson.")
    if stats.current_hearts <= 0 and not stats.unlimited_hearts:
        raise ApiError(400, ErrorCode.OUT_OF_HEARTS, "You are out of hearts.")

    links = sorted((link for link in lesson.lesson_exercises if link.is_required), key=lambda row: row.position)
    if not links:
        raise ApiError(400, ErrorCode.LESSON_NOT_AVAILABLE, "Lesson has no exercises.")
    now = utc_now_text()
    attempt = models.LessonAttempt(
        attempt_token=str(uuid.uuid4()),
        enrollment_id=enrollment.id,
        lesson_id=lesson.id,
        attempt_mode=mode,
        total_exercises=len(links),
        starting_hearts=stats.current_hearts,
        last_activity_at=now,
    )
    db.add(attempt)
    db.flush()
    for link in links:
        db.add(
            models.LessonAttemptItem(
                lesson_attempt_id=attempt.id,
                lesson_exercise_id=link.id,
                exercise_id=link.exercise_id,
                position=link.position,
            )
        )
    lesson_progress = (
        db.query(models.LearnerLessonProgress)
        .filter_by(enrollment_id=enrollment.id, lesson_id=lesson.id)
        .first()
    )
    if not lesson_progress:
        lesson_progress = models.LearnerLessonProgress(enrollment_id=enrollment.id, lesson_id=lesson.id)
        db.add(lesson_progress)
    lesson_progress.times_started += 1
    lesson_progress.first_started_at = lesson_progress.first_started_at or now
    lesson_progress.updated_at = now
    enrollment.current_level_id = lesson.level_id
    enrollment.current_lesson_id = lesson.id
    enrollment.last_accessed_at = now
    db.flush()
    db.refresh(attempt)
    response = attempt_response(db, learner, attempt)
    idempotency_store(db, learner.id, "start_lesson", idempotency_key, response)
    db.commit()
    return response


def complete_attempt(db: Session, learner: models.Learner, attempt: models.LessonAttempt):
    if attempt.status != "in_progress":
        return None
    stats = get_stats(learner)
    exercise_count = max(1, attempt.total_exercises)
    xp_earned = max(5, attempt.lesson.xp_reward + attempt.correct_answers * 2 - attempt.wrong_answers)
    local_date = learner_local_date(learner, utc_now())
    apply_streak_for_qualifying_lesson(learner, stats, local_date)
    xp_event_key = f"lesson-attempt:{attempt.id}:completion-xp"
    if not db.query(models.XpEvent).filter_by(event_key=xp_event_key).first():
        stats.total_xp += xp_earned
        db.add(
            models.XpEvent(
                learner_id=learner.id,
                enrollment_id=attempt.enrollment_id,
                lesson_attempt_id=attempt.id,
                amount=xp_earned,
                source_type="lesson_completion",
                event_key=xp_event_key,
                local_date=local_date,
            )
        )
    attempt.status = "completed"
    attempt.xp_awarded = xp_earned
    attempt.ending_hearts = stats.current_hearts
    attempt.completed_at = utc_now_text()
    attempt.last_activity_at = utc_now_text()

    lesson_progress = (
        db.query(models.LearnerLessonProgress)
        .filter_by(enrollment_id=attempt.enrollment_id, lesson_id=attempt.lesson_id)
        .first()
    )
    score = round((attempt.correct_answers / exercise_count) * 100)
    if lesson_progress:
        lesson_progress.times_completed += 1
        lesson_progress.best_score_percent = max(lesson_progress.best_score_percent, score)
        lesson_progress.first_completed_at = lesson_progress.first_completed_at or utc_now_text()
        lesson_progress.last_completed_at = utc_now_text()
        lesson_progress.updated_at = utc_now_text()

    progress = (
        db.query(models.LearnerLevelProgress)
        .filter_by(enrollment_id=attempt.enrollment_id, level_id=attempt.lesson.level_id)
        .first()
    )
    if not progress:
        progress = models.LearnerLevelProgress(enrollment_id=attempt.enrollment_id, level_id=attempt.lesson.level_id)
        db.add(progress)
        db.flush()
    completed_lessons, total_lessons = get_level_lesson_counts(db, attempt.enrollment_id, attempt.lesson.level_id)
    level_completed = total_lessons > 0 and completed_lessons >= total_lessons
    progress.crown_count = max(progress.crown_count, 1 if level_completed else 0)
    progress.is_completed = 1 if level_completed else 0
    progress.best_score_percent = max(progress.best_score_percent, score)
    progress.started_at = progress.started_at or attempt.started_at
    progress.completed_at = utc_now_text() if level_completed else progress.completed_at
    progress.updated_at = utc_now_text()

    activity = get_or_create_daily_activity(db, learner, local_date)
    activity.xp_earned += xp_earned
    activity.lessons_completed += 1
    activity.exercises_answered += attempt.total_exercises
    activity.streak_qualified = 1
    activity.daily_goal_reached = 1 if activity.xp_earned >= stats.daily_goal_xp else 0
    activity.last_activity_at = utc_now_text()
    unlocked = check_and_unlock_achievements(db, learner, local_date)
    return {
        "xpEarned": xp_earned,
        "levelCompleted": level_completed,
        "unlockedAchievements": [{"key": item.key, "name": item.name} for item in unlocked],
    }


def submit_answer(db: Session, learner: models.Learner, attempt_token: str, payload, idempotency_key: str | None):
    cached = idempotency_get(db, learner.id, "submit_answer", idempotency_key)
    if cached:
        return cached
    attempt = get_attempt_by_token(db, learner, attempt_token)
    if attempt.status == "completed":
        raise ApiError(400, ErrorCode.ATTEMPT_ALREADY_COMPLETED, "Attempt is already completed.")
    if attempt.status != "in_progress":
        raise ApiError(400, ErrorCode.ATTEMPT_NOT_ACTIVE, "Attempt is not active.")
    duplicate = (
        db.query(models.ExerciseAttempt)
        .filter_by(lesson_attempt_id=attempt.id, client_submission_id=payload.client_submission_id)
        .first()
    )
    if duplicate:
        response = attempt_response(db, learner, attempt)
        response["alreadySubmitted"] = True
        return response

    answered_positions = {
        row.presentation_order
        for row in db.query(models.ExerciseAttempt)
        .filter_by(lesson_attempt_id=attempt.id)
        .all()
    }
    item = next(
        (
            row
            for row in sorted(attempt.items, key=lambda entry: entry.position)
            if row.position not in answered_positions
        ),
        None,
    )
    if not item or item.exercise_id != payload.exercise_id:
        raise ApiError(409, ErrorCode.EXERCISE_NOT_CURRENT, "Submit the current exercise before moving on.")
    if item.exercise.exercise_type != payload.answer.type:
        raise ApiError(422, ErrorCode.ANSWER_PAYLOAD_INVALID, "Answer type does not match exercise type.")

    evaluator = EVALUATORS.get(item.exercise.exercise_type)
    if not evaluator:
        raise ApiError(422, ErrorCode.ANSWER_PAYLOAD_INVALID, "Unsupported exercise type.")
    result = evaluator.evaluate(item.exercise, payload.answer)
    stats = get_stats(learner)
    heart_lost = False
    if result.is_correct:
        attempt.correct_answers += 1
    else:
        attempt.wrong_answers += 1
        if not stats.unlimited_hearts:
            stats.current_hearts = max(0, stats.current_hearts - 1)
            schedule_next_heart_if_needed(stats)
            heart_lost = True

    submission = models.ExerciseAttempt(
        lesson_attempt_id=attempt.id,
        lesson_exercise_id=item.lesson_exercise_id,
        presentation_order=item.position,
        submission_number=1,
        client_submission_id=payload.client_submission_id,
        response_json=payload.model_dump_json(),
        is_correct=1 if result.is_correct else 0,
        heart_lost=1 if heart_lost else 0,
        feedback_text=item.exercise.explanation_text,
        response_time_ms=payload.response_time_ms,
    )
    db.add(submission)
    attempt.current_exercise_index = item.position
    attempt.last_activity_at = utc_now_text()
    if heart_lost:
        db.flush()
        db.add(
            models.HeartEvent(
                learner_id=learner.id,
                lesson_attempt_id=attempt.id,
                exercise_attempt_id=submission.id,
                event_type="mistake",
                delta=-1,
                balance_after=stats.current_hearts,
                event_key=f"exercise-attempt:{submission.id}:heart-mistake",
            )
        )
        if stats.current_hearts <= 0:
            attempt.status = "failed"
            attempt.ending_hearts = 0
            attempt.completed_at = utc_now_text()

    answered_after = len(answered_positions) + 1
    completion = None
    if answered_after >= attempt.total_exercises and attempt.status == "in_progress":
        completion = complete_attempt(db, learner, attempt)

    response = attempt_response(db, learner, attempt)
    response.update(
        {
            "result": "correct" if result.is_correct else "incorrect",
            "feedbackTitle": "Correct!" if result.is_correct else "Not quite",
            "feedbackMessage": item.exercise.explanation_text,
            "correctAnswer": result.correct_answer,
            "heartLost": heart_lost,
            "currentHearts": stats.current_hearts,
            "completion": completion,
        }
    )
    idempotency_store(db, learner.id, "submit_answer", idempotency_key, response)
    db.commit()
    return response


def abandon_attempt(db: Session, learner: models.Learner, attempt_token: str):
    attempt = get_attempt_by_token(db, learner, attempt_token)
    if attempt.status == "in_progress":
        attempt.status = "abandoned"
        attempt.ending_hearts = get_stats(learner).current_hearts
        attempt.completed_at = utc_now_text()
        db.commit()
    return attempt_response(db, learner, attempt)


def hearts(db: Session, learner: models.Learner):
    stats = get_stats(learner)
    regenerate_hearts(db, learner, stats)
    db.commit()
    return {
        "hearts": stats.current_hearts,
        "maxHearts": stats.max_hearts,
        "nextHeartAt": stats.next_heart_at,
        "unlimited": bool(stats.unlimited_hearts),
    }


def refill_hearts(db: Session, learner: models.Learner, method: str, cost: int, idempotency_key: str | None):
    cached = idempotency_get(db, learner.id, "refill_hearts", idempotency_key)
    if cached:
        return cached
    stats = get_stats(learner)
    regenerate_hearts(db, learner, stats)
    if stats.current_hearts >= stats.max_hearts:
        response = hearts(db, learner)
        idempotency_store(db, learner.id, "refill_hearts", idempotency_key, response)
        db.commit()
        return response
    if method == "gems" and stats.gems < cost:
        raise ApiError(400, ErrorCode.INSUFFICIENT_GEMS, "Not enough gems to refill hearts.")
    if method == "gems":
        stats.gems -= cost
    stats.current_hearts = stats.max_hearts if method in {"mock", "practice"} else stats.current_hearts + 1
    stats.next_heart_at = None if stats.current_hearts >= stats.max_hearts else stats.next_heart_at
    stats.updated_at = utc_now_text()
    db.add(
        models.HeartEvent(
            learner_id=learner.id,
            event_type="gems_refill" if method == "gems" else "practice_refill",
            delta=1,
            balance_after=stats.current_hearts,
            event_key=f"heart-refill:{learner.id}:{method}:{uuid.uuid4()}",
        )
    )
    response = hearts(db, learner)
    idempotency_store(db, learner.id, "refill_hearts", idempotency_key, response)
    db.commit()
    return response


def claim_reward(db: Session, learner: models.Learner, reward_id: int, idempotency_key: str | None):
    cached = idempotency_get(db, learner.id, "claim_reward", idempotency_key)
    if cached:
        return cached
    reward = db.get(models.UnitReward, reward_id)
    if not reward:
        raise ApiError(404, ErrorCode.REWARD_LOCKED, "Reward not found.")
    existing = db.get(models.UnitRewardClaim, {"learner_id": learner.id, "reward_id": reward.id})
    if existing and not reward.is_repeatable:
        response = {"rewardId": reward.id, "claimed": True, "gemsAwarded": 0, "learner": learner_summary(db, learner)}
        idempotency_store(db, learner.id, "claim_reward", idempotency_key, response)
        db.commit()
        return response
    enrollment = get_selected_enrollment(db, learner.id)
    completed_count = (
        db.query(models.LearnerLevelProgress)
        .join(models.Level)
        .filter(
            models.LearnerLevelProgress.enrollment_id == enrollment.id,
            models.Level.unit_id == reward.unit_id,
            models.LearnerLevelProgress.is_completed == 1,
        )
        .count()
    )
    if completed_count < reward.required_completed_levels:
        raise ApiError(403, ErrorCode.REWARD_LOCKED, "Reward is not unlocked.")
    stats = get_stats(learner)
    stats.gems += reward.gems_reward
    stats.updated_at = utc_now_text()
    db.add(models.UnitRewardClaim(learner_id=learner.id, reward_id=reward.id, gems_awarded=reward.gems_reward))
    response = {
        "rewardId": reward.id,
        "claimed": True,
        "gemsAwarded": reward.gems_reward,
        "learner": learner_summary(db, learner),
    }
    idempotency_store(db, learner.id, "claim_reward", idempotency_key, response)
    db.commit()
    return response


def activity(db: Session, learner: models.Learner):
    rows = (
        db.query(models.LearnerDailyActivity)
        .filter_by(learner_id=learner.id)
        .order_by(models.LearnerDailyActivity.local_date.desc())
        .limit(30)
        .all()
    )
    return {
        "days": [
            {
                "date": row.local_date,
                "xpEarned": row.xp_earned,
                "lessonsCompleted": row.lessons_completed,
                "exercisesAnswered": row.exercises_answered,
                "dailyGoalReached": bool(row.daily_goal_reached),
            }
            for row in rows
        ]
    }


def daily_goal(db: Session, learner: models.Learner):
    summary = learner_summary(db, learner)
    return {
        "targetXp": summary["dailyGoalXp"],
        "todayXp": summary["todayXp"],
        "reached": summary["todayXp"] >= summary["dailyGoalXp"],
    }


def update_daily_goal(db: Session, learner: models.Learner, target_xp: int):
    stats = get_stats(learner)
    stats.daily_goal_xp = target_xp
    stats.updated_at = utc_now_text()
    db.commit()
    return daily_goal(db, learner)


def achievements(db: Session, learner: models.Learner):
    rows = (
        db.query(models.Achievement, models.LearnerAchievement)
        .outerjoin(
            models.LearnerAchievement,
            and_(
                models.LearnerAchievement.achievement_id == models.Achievement.id,
                models.LearnerAchievement.learner_id == learner.id,
            ),
        )
        .filter(models.Achievement.is_active == 1)
        .order_by(models.Achievement.id)
        .all()
    )
    return {
        "achievements": [
            {
                "id": achievement.id,
                "key": achievement.key,
                "name": achievement.name,
                "description": achievement.description,
                "iconKey": achievement.icon_key,
                "thresholdValue": achievement.threshold_value,
                "rewardGems": achievement.reward_gems,
                "progressValue": learner_achievement.progress_value if learner_achievement else 0,
                "unlockedAt": learner_achievement.unlocked_at if learner_achievement else None,
                "claimedAt": learner_achievement.claimed_at if learner_achievement else None,
            }
            for achievement, learner_achievement in rows
        ]
    }


def weekly_leaderboard(db: Session, limit: int = 20):
    now = utc_now().replace(tzinfo=None)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    rows = (
        db.query(
            models.Learner.id,
            models.Learner.display_name,
            models.Learner.avatar_url,
            func.coalesce(func.sum(models.XpEvent.amount), 0).label("weekly_xp"),
        )
        .outerjoin(
            models.XpEvent,
            and_(
                models.XpEvent.learner_id == models.Learner.id,
                models.XpEvent.occurred_at >= week_start.isoformat(),
                models.XpEvent.occurred_at < week_end.isoformat(),
            ),
        )
        .filter(models.Learner.is_active == 1)
        .group_by(models.Learner.id)
        .order_by(func.coalesce(func.sum(models.XpEvent.amount), 0).desc(), models.Learner.id.asc())
        .limit(min(max(limit, 1), 50))
        .all()
    )
    return {
        "weekStart": week_start.isoformat(),
        "weekEnd": week_end.isoformat(),
        "leaders": [
            {
                "learnerId": row.id,
                "displayName": row.display_name,
                "avatarUrl": row.avatar_url,
                "weeklyXp": row.weekly_xp,
            }
            for row in rows
        ],
    }
