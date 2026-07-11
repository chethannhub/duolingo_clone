import json
import uuid
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload

from app import models
from app.api.dependencies import get_current_learner
from app.api.v1.router import router as v1_router
from app.core.exceptions import ApiError, api_error_handler, http_error_handler, validation_error_handler
from app.database import Base, SessionLocal, engine, get_db
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
from app.path_status import (
    get_completed_level_ids,
    get_first_available_level_progress,
    get_level_lesson_counts,
    get_level_status,
    serialize_level_path_status,
)

app = FastAPI(
    title="Duolingo Clone API",
    description="Backend API for Duolingo Clone",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.include_router(v1_router)

Base.metadata.create_all(bind=engine)


def ensure_seed_data():
    db = SessionLocal()
    try:
        has_learner = db.query(models.Learner.id).first() is not None
    finally:
        db.close()
    if not has_learner:
        from app.seed import seed_database

        seed_database(reset=False)


ensure_seed_data()


class StartAttemptRequest(BaseModel):
    learner_id: int = 1
    lesson_id: int


class AnswerRequest(BaseModel):
    learner_id: int = 1
    exercise_id: int
    answer: str


class CompleteAttemptRequest(BaseModel):
    learner_id: int = 1


class RegainHeartRequest(BaseModel):
    learner_id: int = 1
    cost: int = 50


class V1AnswerRequest(BaseModel):
    exercise_id: int
    answer: str


class SettingsUpdateRequest(BaseModel):
    sound_effects_enabled: int | None = None
    animations_enabled: int | None = None
    listening_exercises_enabled: int | None = None
    motivational_messages_enabled: int | None = None
    leaderboard_enabled: int | None = None
    dark_mode_enabled: int | None = None
    daily_reminder_time: str | None = None


class RefillHeartsRequest(BaseModel):
    cost: int = 50


class ClaimRewardRequest(BaseModel):
    reward_id: int


@app.get("/")
def root():
    return {"message": "Duolingo Clone Backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok", "database": "connected"}


def now_utc() -> str:
    return utc_now_text()


def sqlite_timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def normalize_answer(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def get_stats(learner: models.Learner) -> models.LearnerStats:
    if not learner.stats:
        learner.stats = models.LearnerStats(learner_id=learner.id)
    return learner.stats


def get_selected_enrollment(db: Session, learner_id: int) -> models.CourseEnrollment | None:
    return (
        db.query(models.CourseEnrollment)
        .filter(
            models.CourseEnrollment.learner_id == learner_id,
            models.CourseEnrollment.is_selected == 1,
            models.CourseEnrollment.status == "active",
        )
        .first()
    )


def serialize_learner(learner: models.Learner):
    stats = get_stats(learner)
    today = learner_local_date(learner)
    return {
        "id": learner.id,
        "username": learner.username,
        "name": learner.display_name,
        "displayName": learner.display_name,
        "timezone": learner.timezone,
        "locale": learner.locale,
        "totalXp": stats.total_xp,
        "todayXp": sum(
            item.xp_earned
            for item in getattr(learner, "daily_activity", [])
            if item.local_date == today
        ),
        "dailyXpGoal": stats.daily_goal_xp,
        "currentStreak": stats.current_streak,
        "longestStreak": stats.longest_streak,
        "hearts": stats.current_hearts,
        "maxHearts": stats.max_hearts,
        "gems": stats.gems,
        "lastActivityDate": stats.last_streak_date,
    }


def serialize_option(option: models.ExerciseOption):
    return {"id": option.id, "text": option.option_text, "pairKey": None}


def serialize_match_pair(pair: models.ExerciseMatchPair):
    return {
        "id": pair.id,
        "left": pair.left_text,
        "right": pair.right_text,
    }


def serialize_exercise_link(link: models.LessonExercise):
    exercise = link.exercise
    options = [serialize_option(option) for option in exercise.options]
    if exercise.exercise_type == "match_pairs":
        options = [
            {"id": pair.id * 2 - 1, "text": pair.left_text, "side": "left"}
            for pair in exercise.match_pairs
        ] + [
            {"id": pair.id * 2, "text": pair.right_text, "side": "right"}
            for pair in exercise.match_pairs
        ]

    return {
        "id": exercise.id,
        "type": exercise.exercise_type,
        "question": exercise.prompt_text,
        "prompt": exercise.instruction_text,
        "hint": exercise.hint_text,
        "explanation": exercise.explanation_text,
        "orderIndex": link.position,
        "options": options,
        "matchPairs": [],
    }


def serialize_lesson(lesson: models.Lesson):
    return {
        "id": lesson.id,
        "title": lesson.title,
        "xpReward": lesson.xp_reward,
        "level": {
            "id": lesson.level.id,
            "title": lesson.level.title,
            "unit": {
                "id": lesson.level.unit.id,
                "title": lesson.level.unit.title,
                "section": {
                    "id": lesson.level.unit.section.id,
                    "title": lesson.level.unit.section.title,
                },
            },
        },
        "exercises": [
            serialize_exercise_link(link)
            for link in sorted(lesson.lesson_exercises, key=lambda item: item.position)
        ],
    }


@app.get("/api/learners/{learner_id}")
def get_learner(learner_id: int = 1, db: Session = Depends(get_db)):
    learner = (
        db.query(models.Learner)
        .options(joinedload(models.Learner.stats))
        .filter(models.Learner.id == learner_id)
        .first()
    )
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")
    regenerate_hearts(db, learner, get_stats(learner))
    db.commit()
    db.refresh(learner)
    return serialize_learner(learner)


@app.get("/api/lessons/next")
def get_next_lesson(learner_id: int = 1, db: Session = Depends(get_db)):
    enrollment = get_selected_enrollment(db, learner_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Selected enrollment not found")

    progress = get_first_available_level_progress(db, enrollment)

    lesson_query = db.query(models.Lesson).options(
        joinedload(models.Lesson.level)
        .joinedload(models.Level.unit)
        .joinedload(models.Unit.section),
        joinedload(models.Lesson.lesson_exercises)
        .joinedload(models.LessonExercise.exercise)
        .joinedload(models.Exercise.options),
        joinedload(models.Lesson.lesson_exercises)
        .joinedload(models.LessonExercise.exercise)
        .joinedload(models.Exercise.match_pairs),
    )

    if progress:
        lesson = (
            lesson_query.filter(models.Lesson.level_id == progress.level_id)
            .order_by(models.Lesson.position)
            .first()
        )
    else:
        lesson = lesson_query.order_by(models.Lesson.id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="No lessons available")
    return serialize_lesson(lesson)


@app.get("/api/path")
def get_learning_path(learner_id: int = 1, db: Session = Depends(get_db)):
    enrollment = get_selected_enrollment(db, learner_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Selected enrollment not found")

    progress_rows = (
        db.query(models.LearnerLevelProgress)
        .filter(models.LearnerLevelProgress.enrollment_id == enrollment.id)
        .all()
    )
    progress_by_level_id = {row.level_id: row for row in progress_rows}
    completed_level_ids = get_completed_level_ids(progress_rows)
    sections = (
        db.query(models.Section)
        .options(
            joinedload(models.Section.units)
            .joinedload(models.Unit.levels)
            .joinedload(models.Level.prerequisites)
        )
        .filter(models.Section.course_id == enrollment.course_id, models.Section.is_published == 1)
        .order_by(models.Section.position)
        .all()
    )

    return {
        "enrollmentId": enrollment.id,
        "currentLevelId": enrollment.current_level_id,
        "currentLessonId": enrollment.current_lesson_id,
        "sections": [
            {
                "id": section.id,
                "title": section.title,
                "position": section.position,
                "units": [
                    {
                        "id": unit.id,
                        "title": unit.title,
                        "position": unit.position,
                        "levels": [
                            serialize_level_path_status(
                                db,
                                enrollment,
                                level,
                                progress_by_level_id.get(level.id),
                                completed_level_ids,
                            )
                            for level in sorted(
                                (item for item in unit.levels if item.is_published),
                                key=lambda item: item.position,
                            )
                        ],
                        "pathItems": [
                            {
                                "id": item.id,
                                "position": item.position,
                                "type": item.item_type,
                                "levelId": item.level_id,
                                "reward": (
                                    {
                                        "id": item.reward.id,
                                        "title": item.reward.title,
                                        "description": item.reward.description,
                                        "iconKey": item.reward.icon_key,
                                        "gemsReward": item.reward.gems_reward,
                                        "requiredCompletedLevels": item.reward.required_completed_levels,
                                        "claimed": bool(
                                            item.reward
                                            and any(
                                                claim.learner_id == learner_id
                                                for claim in item.reward.claims
                                            )
                                        ),
                                    }
                                    if item.reward
                                    else None
                                ),
                            }
                            for item in sorted(unit.path_items, key=lambda path_item: path_item.position)
                        ],
                    }
                    for unit in sorted(
                        (item for item in section.units if item.is_published),
                        key=lambda item: item.position,
                    )
                ],
            }
            for section in sections
        ],
    }


@app.get("/api/leaderboard")
def get_leaderboard(limit: int = 20, db: Session = Depends(get_db)):
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
                models.XpEvent.occurred_at >= sqlite_timestamp(week_start),
                models.XpEvent.occurred_at < sqlite_timestamp(week_end),
            ),
        )
        .filter(models.Learner.is_active == 1)
        .group_by(models.Learner.id)
        .order_by(func.coalesce(func.sum(models.XpEvent.amount), 0).desc(), models.Learner.id.asc())
        .limit(min(max(limit, 1), 20))
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


@app.get("/api/lessons/{lesson_id}")
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = (
        db.query(models.Lesson)
        .options(
            joinedload(models.Lesson.level)
            .joinedload(models.Level.unit)
            .joinedload(models.Unit.section),
            joinedload(models.Lesson.lesson_exercises)
            .joinedload(models.LessonExercise.exercise)
            .joinedload(models.Exercise.options),
            joinedload(models.Lesson.lesson_exercises)
            .joinedload(models.LessonExercise.exercise)
            .joinedload(models.Exercise.match_pairs),
        )
        .filter(models.Lesson.id == lesson_id)
        .first()
    )
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return serialize_lesson(lesson)


@app.post("/api/lesson-attempts")
def start_lesson_attempt(payload: StartAttemptRequest, db: Session = Depends(get_db)):
    learner = (
        db.query(models.Learner)
        .options(joinedload(models.Learner.stats))
        .filter(models.Learner.id == payload.learner_id)
        .first()
    )
    lesson = db.get(models.Lesson, payload.lesson_id)
    enrollment = get_selected_enrollment(db, learner.id) if learner else None
    if not learner or not lesson:
        raise HTTPException(status_code=404, detail="Learner or lesson not found")
    if not enrollment:
        raise HTTPException(status_code=404, detail="Selected enrollment not found")
    stats = get_stats(learner)
    regenerate_hearts(db, learner, stats)
    if lesson.is_published != 1 or lesson.level.is_published != 1:
        raise HTTPException(status_code=400, detail="Lesson is not published")
    if lesson.level.unit.section.course_id != enrollment.course_id:
        raise HTTPException(status_code=400, detail="Lesson is outside the selected course")

    progress_rows = (
        db.query(models.LearnerLevelProgress)
        .filter(models.LearnerLevelProgress.enrollment_id == enrollment.id)
        .all()
    )
    completed_level_ids = get_completed_level_ids(progress_rows)
    level_progress = next((row for row in progress_rows if row.level_id == lesson.level_id), None)
    level_status = get_level_status(db, enrollment, lesson.level, level_progress, completed_level_ids)
    if level_status["status"] == "locked":
        raise HTTPException(status_code=403, detail="Level is locked")
    if stats.current_hearts <= 0 and not stats.unlimited_hearts:
        raise HTTPException(status_code=400, detail="No hearts remaining")

    total_exercises = (
        db.query(models.LessonExercise)
        .filter(models.LessonExercise.lesson_id == lesson.id)
        .count()
    )
    if total_exercises <= 0:
        raise HTTPException(status_code=400, detail="Lesson has no exercises")

    now = now_utc()
    attempt = models.LessonAttempt(
        attempt_token=str(uuid.uuid4()),
        enrollment_id=enrollment.id,
        lesson_id=lesson.id,
        status="in_progress",
        total_exercises=total_exercises,
        starting_hearts=stats.current_hearts,
        last_activity_at=now,
    )
    db.add(attempt)
    lesson_progress = (
        db.query(models.LearnerLessonProgress)
        .filter(
            models.LearnerLessonProgress.enrollment_id == enrollment.id,
            models.LearnerLessonProgress.lesson_id == lesson.id,
        )
        .first()
    )
    if not lesson_progress:
        lesson_progress = models.LearnerLessonProgress(
            enrollment_id=enrollment.id,
            lesson_id=lesson.id,
        )
        db.add(lesson_progress)
    lesson_progress.times_started += 1
    lesson_progress.first_started_at = lesson_progress.first_started_at or now
    lesson_progress.updated_at = now
    enrollment.current_level_id = lesson.level_id
    enrollment.current_lesson_id = lesson.id
    enrollment.last_accessed_at = now
    db.commit()
    db.refresh(attempt)
    return {
        "id": attempt.id,
        "attemptToken": attempt.attempt_token,
        "status": attempt.status,
        "learner": serialize_learner(learner),
    }


def is_answer_correct(exercise: models.Exercise, answer: str) -> bool:
    provided = normalize_answer(answer)
    accepted = {item.normalized_answer for item in exercise.accepted_answers}
    if accepted and provided in accepted:
        return True
    if exercise.exercise_type in {"multiple_choice", "fill_blank"}:
        correct_option = next((option.option_text for option in exercise.options if option.is_correct), None)
        return normalize_answer(correct_option) == provided
    if exercise.exercise_type == "translate_word_bank":
        expected = " ".join(
            option.option_text
            for option in sorted(
                (option for option in exercise.options if option.correct_order is not None),
                key=lambda item: item.correct_order,
            )
        )
        return normalize_answer(expected) == provided
    if exercise.exercise_type == "match_pairs":
        expected = sorted(f"{pair.left_text}:{pair.right_text}".lower() for pair in exercise.match_pairs)
        provided_pairs = sorted(pair.strip().lower() for pair in answer.split(","))
        return provided_pairs == expected
    return False


@app.post("/api/lesson-attempts/{attempt_id}/answer")
def answer_exercise(attempt_id: int, payload: AnswerRequest, db: Session = Depends(get_db)):
    attempt = (
        db.query(models.LessonAttempt)
        .options(joinedload(models.LessonAttempt.enrollment))
        .filter(models.LessonAttempt.id == attempt_id)
        .first()
    )
    learner = (
        db.query(models.Learner)
        .options(joinedload(models.Learner.stats))
        .filter(models.Learner.id == payload.learner_id)
        .first()
    )
    exercise = (
        db.query(models.Exercise)
        .options(
            joinedload(models.Exercise.options),
            joinedload(models.Exercise.match_pairs),
            joinedload(models.Exercise.accepted_answers),
        )
        .filter(models.Exercise.id == payload.exercise_id)
        .first()
    )
    lesson_exercise = (
        None
        if not attempt
        else db.query(models.LessonExercise)
        .filter(
            models.LessonExercise.lesson_id == attempt.lesson_id,
            models.LessonExercise.exercise_id == payload.exercise_id,
        )
        .first()
    )
    if not attempt or not learner or not exercise:
        raise HTTPException(status_code=404, detail="Attempt, learner, or exercise not found")
    if attempt.enrollment.learner_id != learner.id:
        raise HTTPException(status_code=403, detail="Attempt does not belong to learner")
    if not lesson_exercise:
        raise HTTPException(status_code=404, detail="Exercise is not part of this lesson")
    if attempt.status != "in_progress":
        raise HTTPException(status_code=400, detail="Attempt is not active")

    stats = get_stats(learner)
    is_correct = is_answer_correct(exercise, payload.answer)
    submission_number = (
        db.query(func.count(models.ExerciseAttempt.id))
        .filter(
            models.ExerciseAttempt.lesson_attempt_id == attempt.id,
            models.ExerciseAttempt.presentation_order == lesson_exercise.position,
        )
        .scalar()
        + 1
    )
    heart_lost = 0

    if is_correct:
        attempt.correct_answers += 1
    else:
        attempt.wrong_answers += 1
        if not stats.unlimited_hearts:
            stats.current_hearts = max(0, stats.current_hearts - 1)
            schedule_next_heart_if_needed(stats)
            heart_lost = 1

    attempt.current_exercise_index = max(attempt.current_exercise_index, lesson_exercise.position)
    attempt.last_activity_at = now_utc()
    exercise_attempt = models.ExerciseAttempt(
        lesson_attempt_id=attempt.id,
        lesson_exercise_id=lesson_exercise.id,
        presentation_order=lesson_exercise.position,
        submission_number=submission_number,
        response_json=json.dumps({"text": payload.answer}),
        is_correct=1 if is_correct else 0,
        heart_lost=heart_lost,
        feedback_text=exercise.explanation_text,
    )
    db.add(exercise_attempt)
    db.flush()
    if heart_lost:
        db.add(
            models.HeartEvent(
                learner_id=learner.id,
                lesson_attempt_id=attempt.id,
                exercise_attempt_id=exercise_attempt.id,
                event_type="mistake",
                delta=-1,
                balance_after=get_stats(learner).current_hearts,
                event_key=f"exercise-attempt:{exercise_attempt.id}:heart-mistake",
            )
        )
        if stats.current_hearts <= 0:
            attempt.status = "failed"
            attempt.ending_hearts = 0
            attempt.completed_at = now_utc()
    db.commit()
    return {
        "correct": is_correct,
        "correctAnswer": next(
            (item.answer_text for item in exercise.accepted_answers if item.is_primary),
            None,
        ),
        "explanation": exercise.explanation_text,
        "learner": serialize_learner(learner),
        "attempt": {
            "id": attempt.id,
            "correctCount": attempt.correct_answers,
            "wrongCount": attempt.wrong_answers,
        },
    }


@app.post("/api/lesson-attempts/{attempt_id}/complete")
def complete_lesson_attempt(
    attempt_id: int,
    payload: CompleteAttemptRequest,
    db: Session = Depends(get_db),
):
    attempt = (
        db.query(models.LessonAttempt)
        .options(
            joinedload(models.LessonAttempt.enrollment),
            joinedload(models.LessonAttempt.lesson).joinedload(models.Lesson.level),
        )
        .filter(models.LessonAttempt.id == attempt_id)
        .first()
    )
    learner = (
        db.query(models.Learner)
        .options(joinedload(models.Learner.stats))
        .filter(models.Learner.id == payload.learner_id)
        .first()
    )
    if not attempt or not learner:
        raise HTTPException(status_code=404, detail="Attempt or learner not found")
    if attempt.enrollment.learner_id != learner.id:
        raise HTTPException(status_code=403, detail="Attempt does not belong to learner")
    if attempt.status == "completed":
        return {"attemptId": attempt.id, "learner": serialize_learner(learner)}
    if attempt.status != "in_progress":
        raise HTTPException(status_code=400, detail="Attempt cannot be completed")

    answered_count = (
        db.query(models.ExerciseAttempt)
        .join(models.LessonExercise)
        .filter(models.ExerciseAttempt.lesson_attempt_id == attempt.id)
        .filter(models.LessonExercise.is_required == 1)
        .with_entities(func.count(func.distinct(models.ExerciseAttempt.lesson_exercise_id)))
        .scalar()
    )
    exercise_count = (
        db.query(models.LessonExercise)
        .filter(
            models.LessonExercise.lesson_id == attempt.lesson_id,
            models.LessonExercise.is_required == 1,
        )
        .count()
    )
    if exercise_count and answered_count < exercise_count:
        raise HTTPException(status_code=400, detail="Lesson still has unanswered exercises")

    stats = get_stats(learner)
    xp_earned = max(5, attempt.lesson.xp_reward + attempt.correct_answers * 2 - attempt.wrong_answers)
    local_date = learner_local_date(learner, utc_now())
    apply_streak_for_qualifying_lesson(learner, stats, local_date)
    xp_event_key = f"lesson-attempt:{attempt.id}:completion-xp"
    existing_xp_event = (
        db.query(models.XpEvent)
        .filter(models.XpEvent.event_key == xp_event_key)
        .first()
    )
    if not existing_xp_event:
        stats.total_xp += xp_earned
    stats.updated_at = now_utc()

    attempt.status = "completed"
    attempt.xp_awarded = xp_earned
    attempt.ending_hearts = stats.current_hearts
    attempt.last_activity_at = now_utc()
    attempt.completed_at = now_utc()

    if not existing_xp_event:
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
    daily_activity = get_or_create_daily_activity(db, learner, local_date)
    daily_activity.xp_earned += xp_earned
    daily_activity.lessons_completed += 1
    daily_activity.exercises_answered += answered_count
    daily_activity.streak_qualified = 1
    daily_activity.daily_goal_reached = 1 if daily_activity.xp_earned >= stats.daily_goal_xp else 0
    daily_activity.last_activity_at = now_utc()

    lesson_progress = (
        db.query(models.LearnerLessonProgress)
        .filter(
            models.LearnerLessonProgress.enrollment_id == attempt.enrollment_id,
            models.LearnerLessonProgress.lesson_id == attempt.lesson_id,
        )
        .first()
    )
    if lesson_progress:
        score = round((attempt.correct_answers / max(1, exercise_count)) * 100)
        lesson_progress.times_completed += 1
        lesson_progress.best_score_percent = max(lesson_progress.best_score_percent, score)
        lesson_progress.first_completed_at = lesson_progress.first_completed_at or now_utc()
        lesson_progress.last_completed_at = now_utc()
        lesson_progress.updated_at = now_utc()
    else:
        score = round((attempt.correct_answers / max(1, exercise_count)) * 100)
        lesson_progress = models.LearnerLessonProgress(
            enrollment_id=attempt.enrollment_id,
            lesson_id=attempt.lesson_id,
            times_started=1,
            times_completed=1,
            best_score_percent=score,
            first_started_at=attempt.started_at,
            first_completed_at=now_utc(),
            last_completed_at=now_utc(),
            updated_at=now_utc(),
        )
        db.add(lesson_progress)

    db.flush()
    next_current_level_id = attempt.lesson.level_id
    next_current_lesson_id = attempt.lesson_id
    progress = (
        db.query(models.LearnerLevelProgress)
        .filter(
            models.LearnerLevelProgress.enrollment_id == attempt.enrollment_id,
            models.LearnerLevelProgress.level_id == attempt.lesson.level_id,
        )
        .first()
    )
    if not progress:
        progress = models.LearnerLevelProgress(
            enrollment_id=attempt.enrollment_id,
            level_id=attempt.lesson.level_id,
        )
        db.add(progress)
        db.flush()
    if progress:
        score = round((attempt.correct_answers / max(1, exercise_count)) * 100)
        completed_lessons, total_lessons = get_level_lesson_counts(
            db,
            attempt.enrollment_id,
            attempt.lesson.level_id,
        )
        level_completed = total_lessons > 0 and completed_lessons >= total_lessons
        progress.crown_count = max(progress.crown_count, 1 if level_completed else 0)
        progress.is_completed = 1 if level_completed else 0
        progress.best_score_percent = max(progress.best_score_percent, score)
        progress.started_at = progress.started_at or attempt.started_at
        progress.completed_at = now_utc() if level_completed else progress.completed_at
        progress.updated_at = now_utc()
        if level_completed:
            db.flush()
            next_progress = get_first_available_level_progress(db, attempt.enrollment)
            if next_progress:
                next_lesson = (
                    db.query(models.Lesson)
                    .filter(
                        models.Lesson.level_id == next_progress.level_id,
                        models.Lesson.is_published == 1,
                    )
                    .order_by(models.Lesson.position)
                    .first()
                )
                next_current_level_id = next_progress.level_id
                next_current_lesson_id = next_lesson.id if next_lesson else None

    attempt.enrollment.current_level_id = next_current_level_id
    attempt.enrollment.current_lesson_id = next_current_lesson_id
    attempt.enrollment.last_accessed_at = now_utc()
    db.flush()
    unlocked_achievements = check_and_unlock_achievements(db, learner, local_date)

    db.commit()
    db.refresh(learner)
    return {
        "attemptId": attempt.id,
        "xpEarned": xp_earned,
        "correctCount": attempt.correct_answers,
        "wrongCount": attempt.wrong_answers,
        "unlockedAchievements": [
            {"key": achievement.key, "name": achievement.name}
            for achievement in unlocked_achievements
        ],
        "learner": serialize_learner(learner),
    }


@app.post("/api/learners/regain-heart")
def regain_heart(payload: RegainHeartRequest, db: Session = Depends(get_db)):
    learner = (
        db.query(models.Learner)
        .options(joinedload(models.Learner.stats))
        .filter(models.Learner.id == payload.learner_id)
        .first()
    )
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    stats = get_stats(learner)
    regenerate_hearts(db, learner, stats)
    if stats.current_hearts >= stats.max_hearts:
        db.commit()
        return serialize_learner(learner)
    if stats.gems < payload.cost:
        raise HTTPException(status_code=400, detail="Not enough gems")

    stats.gems -= payload.cost
    stats.current_hearts += 1
    stats.updated_at = now_utc()
    db.add(
        models.HeartEvent(
            learner_id=learner.id,
            event_type="gems_refill",
            delta=1,
            balance_after=stats.current_hearts,
            event_key=f"heart-refill:learner:{learner.id}:{now_utc()}",
        )
    )
    db.commit()
    db.refresh(learner)
    return serialize_learner(learner)


def get_idempotency_response(
    db: Session,
    learner_id: int,
    scope: str,
    idempotency_key: str | None,
):
    if not idempotency_key:
        return None
    record = (
        db.query(models.IdempotencyRecord)
        .filter(
            models.IdempotencyRecord.learner_id == learner_id,
            models.IdempotencyRecord.scope == scope,
            models.IdempotencyRecord.idempotency_key == idempotency_key,
        )
        .first()
    )
    if not record:
        return None
    return JSONResponse(
        content=json.loads(record.response_json),
        status_code=record.status_code,
    )


def store_idempotency_response(
    db: Session,
    learner_id: int,
    scope: str,
    idempotency_key: str | None,
    response: dict,
    status_code: int = 200,
):
    if not idempotency_key:
        return
    existing = (
        db.query(models.IdempotencyRecord)
        .filter(
            models.IdempotencyRecord.learner_id == learner_id,
            models.IdempotencyRecord.scope == scope,
            models.IdempotencyRecord.idempotency_key == idempotency_key,
        )
        .first()
    )
    if existing:
        return
    db.add(
        models.IdempotencyRecord(
            learner_id=learner_id,
            scope=scope,
            idempotency_key=idempotency_key,
            status_code=status_code,
            response_json=json.dumps(response),
        )
    )
    db.commit()


@app.get("/api/v1/health")
def v1_health_check():
    return health_check()


@app.get("/api/v1/courses")
def v1_courses(db: Session = Depends(get_db)):
    courses = (
        db.query(models.Course)
        .options(
            joinedload(models.Course.source_language),
            joinedload(models.Course.target_language),
        )
        .filter(models.Course.status == "published")
        .order_by(models.Course.id)
        .all()
    )
    return {
        "courses": [
            {
                "id": course.id,
                "slug": course.slug,
                "title": course.title,
                "description": course.description,
                "sourceLanguage": course.source_language.code,
                "targetLanguage": course.target_language.code,
                "contentVersion": course.content_version,
                "isFeatured": bool(course.is_featured),
            }
            for course in courses
        ]
    }


@app.get("/api/v1/me/profile")
def v1_profile(
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    regenerate_hearts(db, learner, get_stats(learner))
    db.commit()
    return serialize_learner(learner)


@app.get("/api/v1/me/learning-path")
def v1_learning_path(
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    return get_learning_path(learner.id, db)


@app.get("/api/v1/me/lessons/next")
def v1_next_lesson(
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    return get_next_lesson(learner.id, db)


@app.get("/api/v1/lessons/{lesson_id}")
def v1_lesson(lesson_id: int, db: Session = Depends(get_db)):
    return get_lesson(lesson_id, db)


@app.post("/api/v1/me/lessons/{lesson_id}/attempts")
def v1_start_attempt(
    lesson_id: int,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    cached = get_idempotency_response(db, learner.id, "start_lesson", idempotency_key)
    if cached:
        return cached
    response = start_lesson_attempt(
        StartAttemptRequest(learner_id=learner.id, lesson_id=lesson_id),
        db,
    )
    store_idempotency_response(db, learner.id, "start_lesson", idempotency_key, response)
    return response


@app.post("/api/v1/me/attempts/{attempt_id}/answers")
def v1_submit_answer(
    attempt_id: int,
    payload: V1AnswerRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    cached = get_idempotency_response(db, learner.id, "submit_answer", idempotency_key)
    if cached:
        return cached
    response = answer_exercise(
        attempt_id,
        AnswerRequest(
            learner_id=learner.id,
            exercise_id=payload.exercise_id,
            answer=payload.answer,
        ),
        db,
    )
    store_idempotency_response(db, learner.id, "submit_answer", idempotency_key, response)
    return response


@app.post("/api/v1/me/attempts/{attempt_id}/complete")
def v1_complete_attempt(
    attempt_id: int,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    cached = get_idempotency_response(db, learner.id, "complete_attempt", idempotency_key)
    if cached:
        return cached
    response = complete_lesson_attempt(
        attempt_id,
        CompleteAttemptRequest(learner_id=learner.id),
        db,
    )
    store_idempotency_response(db, learner.id, "complete_attempt", idempotency_key, response)
    return response


@app.get("/api/v1/me/achievements")
def v1_achievements(
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
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
                "metricType": achievement.metric_type,
                "thresholdValue": achievement.threshold_value,
                "rewardGems": achievement.reward_gems,
                "progressValue": learner_achievement.progress_value if learner_achievement else 0,
                "unlockedAt": learner_achievement.unlocked_at if learner_achievement else None,
                "claimedAt": learner_achievement.claimed_at if learner_achievement else None,
            }
            for achievement, learner_achievement in rows
        ]
    }


@app.post("/api/v1/me/rewards/claim")
def v1_claim_reward(
    payload: ClaimRewardRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    cached = get_idempotency_response(db, learner.id, "claim_reward", idempotency_key)
    if cached:
        return cached

    reward = db.get(models.UnitReward, payload.reward_id)
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    existing_claim = db.get(
        models.UnitRewardClaim,
        {"learner_id": learner.id, "reward_id": reward.id},
    )
    if existing_claim and not reward.is_repeatable:
        response = {"rewardId": reward.id, "claimed": True, "learner": serialize_learner(learner)}
        store_idempotency_response(db, learner.id, "claim_reward", idempotency_key, response)
        return response

    enrollment = get_selected_enrollment(db, learner.id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Selected enrollment not found")
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
        raise HTTPException(status_code=403, detail="Reward is not unlocked")

    stats = get_stats(learner)
    stats.gems += reward.gems_reward
    stats.updated_at = now_utc()
    if not existing_claim:
        db.add(
            models.UnitRewardClaim(
                learner_id=learner.id,
                reward_id=reward.id,
                gems_awarded=reward.gems_reward,
            )
        )
    db.commit()
    response = {
        "rewardId": reward.id,
        "claimed": True,
        "gemsAwarded": reward.gems_reward,
        "learner": serialize_learner(learner),
    }
    store_idempotency_response(db, learner.id, "claim_reward", idempotency_key, response)
    return response


@app.post("/api/v1/me/hearts/refill")
def v1_refill_hearts(
    payload: RefillHeartsRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    cached = get_idempotency_response(db, learner.id, "refill_hearts", idempotency_key)
    if cached:
        return cached
    response = regain_heart(RegainHeartRequest(learner_id=learner.id, cost=payload.cost), db)
    store_idempotency_response(db, learner.id, "refill_hearts", idempotency_key, response)
    return response


@app.get("/api/v1/me/settings")
def v1_get_settings(
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    settings = learner.settings or models.LearnerSettings(learner_id=learner.id)
    if not learner.settings:
        db.add(settings)
        db.commit()
    return {
        "soundEffectsEnabled": bool(settings.sound_effects_enabled),
        "animationsEnabled": bool(settings.animations_enabled),
        "listeningExercisesEnabled": bool(settings.listening_exercises_enabled),
        "motivationalMessagesEnabled": bool(settings.motivational_messages_enabled),
        "leaderboardEnabled": bool(settings.leaderboard_enabled),
        "darkModeEnabled": bool(settings.dark_mode_enabled),
        "dailyReminderTime": settings.daily_reminder_time,
    }


@app.patch("/api/v1/me/settings")
def v1_update_settings(
    payload: SettingsUpdateRequest,
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    settings = learner.settings or models.LearnerSettings(learner_id=learner.id)
    db.add(settings)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(settings, field, value)
    settings.updated_at = now_utc()
    db.commit()
    return v1_get_settings(learner, db)


@app.get("/api/v1/leaderboard")
def v1_leaderboard(limit: int = 20, db: Session = Depends(get_db)):
    return get_leaderboard(limit, db)
