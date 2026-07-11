from fastapi import APIRouter, Depends, Header
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models
from app.api.dependencies import get_current_learner
from app.database import get_db
from app.v1_schemas import (
    DailyGoalRequest,
    RefillHeartsRequest,
    SettingsUpdateRequest,
    StartAttemptRequest,
    SubmitAnswerRequest,
)
from app.services import v1_learning_service as service

router = APIRouter(prefix="/api/v1")


@router.get("/health/live")
def live():
    return {"status": "ok"}


@router.get("/health/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@router.get("/courses")
def list_courses(db: Session = Depends(get_db)):
    return service.list_courses(db)


@router.get("/courses/{course_slug}")
def get_course(course_slug: str, db: Session = Depends(get_db)):
    return service.get_course_by_slug(db, course_slug)


@router.get("/courses/{course_id}/sections")
def get_course_sections(course_id: int, db: Session = Depends(get_db)):
    return service.get_course_sections(db, course_id)


@router.get("/sections/{section_id}/units")
def get_section_units(section_id: int, db: Session = Depends(get_db)):
    return service.get_section_units(db, section_id)


@router.get("/units/{unit_id}")
def get_unit(unit_id: int, db: Session = Depends(get_db)):
    return service.get_unit(db, unit_id)


@router.get("/units/{unit_id}/guidebook")
def get_unit_guidebook(unit_id: int, db: Session = Depends(get_db)):
    return service.get_unit_guidebook(db, unit_id)


@router.get("/levels/{level_id}/lessons")
def get_level_lessons(level_id: int, db: Session = Depends(get_db)):
    return service.get_level_lessons(db, level_id)


@router.get("/lessons/{lesson_id}/preview")
def get_lesson_preview(lesson_id: int, db: Session = Depends(get_db)):
    return service.get_lesson_preview(db, lesson_id)


@router.get("/me/learning-path")
def get_learning_path(
    section_id: int | None = None,
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    return service.learning_path(db, learner, section_id)


@router.post("/lessons/{lesson_id}/attempts")
def start_lesson_attempt(
    lesson_id: int,
    payload: StartAttemptRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    return service.start_lesson_attempt(db, learner, lesson_id, payload.mode, idempotency_key)


@router.get("/lesson-attempts/{attempt_token}")
def get_lesson_attempt(
    attempt_token: str,
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    attempt = service.get_attempt_by_token(db, learner, attempt_token)
    return service.attempt_response(db, learner, attempt)


@router.post("/lesson-attempts/{attempt_token}/answers")
def submit_answer(
    attempt_token: str,
    payload: SubmitAnswerRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    return service.submit_answer(db, learner, attempt_token, payload, idempotency_key)


@router.post("/lesson-attempts/{attempt_token}/abandon")
def abandon_attempt(
    attempt_token: str,
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    return service.abandon_attempt(db, learner, attempt_token)


@router.get("/me/hearts")
def get_hearts(
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    return service.hearts(db, learner)


@router.post("/me/hearts/refill")
def refill_hearts(
    payload: RefillHeartsRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    return service.refill_hearts(db, learner, payload.method, payload.cost, idempotency_key)


@router.post("/me/rewards/{reward_id}/claim")
def claim_reward(
    reward_id: int,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    return service.claim_reward(db, learner, reward_id, idempotency_key)


@router.get("/me/profile")
def profile(
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    return service.learner_summary(db, learner)


@router.get("/me/activity")
def activity(
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    return service.activity(db, learner)


@router.get("/me/achievements")
def achievements(
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    return service.achievements(db, learner)


@router.get("/me/daily-goal")
def daily_goal(
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    return service.daily_goal(db, learner)


@router.patch("/me/daily-goal")
def update_daily_goal(
    payload: DailyGoalRequest,
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    return service.update_daily_goal(db, learner, payload.daily_goal_xp)


@router.get("/leaderboards/weekly")
def weekly_leaderboard(limit: int = 20, db: Session = Depends(get_db)):
    return service.weekly_leaderboard(db, limit)


@router.get("/me/settings")
def get_settings(
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


@router.patch("/me/settings")
def update_settings(
    payload: SettingsUpdateRequest,
    learner: models.Learner = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    settings = learner.settings or models.LearnerSettings(learner_id=learner.id)
    db.add(settings)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if value is not None:
            setattr(settings, field, int(value) if isinstance(value, bool) else value)
    db.commit()
    return get_settings(learner, db)
