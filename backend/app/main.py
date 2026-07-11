from datetime import date, datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app import models
from app.database import Base, engine, get_db

app = FastAPI(
    title="Duolingo Clone API",
    description="Backend API for Duolingo Clone",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


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


@app.get("/")
def root():
    return {
        "message": "Duolingo Clone Backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "database": "connected"
    }


def normalize_answer(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def serialize_learner(learner: models.Learner):
    return {
        "id": learner.id,
        "name": learner.name,
        "totalXp": learner.total_xp,
        "todayXp": learner.today_xp,
        "dailyXpGoal": learner.daily_xp_goal,
        "currentStreak": learner.current_streak,
        "longestStreak": learner.longest_streak,
        "hearts": learner.hearts,
        "maxHearts": learner.max_hearts,
        "gems": learner.gems,
        "lastActivityDate": learner.last_activity_date.isoformat()
        if learner.last_activity_date
        else None,
    }


def serialize_option(option: models.ExerciseOption):
    return {
        "id": option.id,
        "text": option.option_text,
        "pairKey": option.pair_key,
    }


def serialize_exercise(exercise: models.Exercise):
    return {
        "id": exercise.id,
        "type": exercise.type,
        "question": exercise.question,
        "prompt": exercise.prompt,
        "explanation": exercise.explanation,
        "orderIndex": exercise.order_index,
        "options": [serialize_option(option) for option in exercise.options],
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
            serialize_exercise(exercise)
            for exercise in sorted(lesson.exercises, key=lambda item: item.order_index)
        ],
    }


@app.get("/api/learners/{learner_id}")
def get_learner(learner_id: int = 1, db: Session = Depends(get_db)):
    learner = db.get(models.Learner, learner_id)
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")
    return serialize_learner(learner)


@app.get("/api/lessons/next")
def get_next_lesson(learner_id: int = 1, db: Session = Depends(get_db)):
    progress = (
        db.query(models.LearnerProgress)
        .filter(
            models.LearnerProgress.learner_id == learner_id,
            models.LearnerProgress.is_unlocked == True,
            models.LearnerProgress.is_completed == False,
        )
        .join(models.Level)
        .order_by(models.Level.id)
        .first()
    )

    lesson_query = (
        db.query(models.Lesson)
        .options(
            joinedload(models.Lesson.level)
            .joinedload(models.Level.unit)
            .joinedload(models.Unit.section),
            joinedload(models.Lesson.exercises).joinedload(models.Exercise.options),
        )
    )

    if progress:
        lesson = (
            lesson_query.filter(models.Lesson.level_id == progress.level_id)
            .order_by(models.Lesson.order_index)
            .first()
        )
    else:
        lesson = lesson_query.order_by(models.Lesson.id).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="No lessons available")

    return serialize_lesson(lesson)


@app.get("/api/lessons/{lesson_id}")
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = (
        db.query(models.Lesson)
        .options(
            joinedload(models.Lesson.level)
            .joinedload(models.Level.unit)
            .joinedload(models.Unit.section),
            joinedload(models.Lesson.exercises).joinedload(models.Exercise.options),
        )
        .filter(models.Lesson.id == lesson_id)
        .first()
    )
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return serialize_lesson(lesson)


@app.post("/api/lesson-attempts")
def start_lesson_attempt(payload: StartAttemptRequest, db: Session = Depends(get_db)):
    learner = db.get(models.Learner, payload.learner_id)
    lesson = db.get(models.Lesson, payload.lesson_id)
    if not learner or not lesson:
        raise HTTPException(status_code=404, detail="Learner or lesson not found")
    if learner.hearts <= 0:
        raise HTTPException(status_code=400, detail="No hearts remaining")

    attempt = models.LessonAttempt(
        learner_id=learner.id,
        lesson_id=lesson.id,
        status="in_progress",
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return {
        "id": attempt.id,
        "status": attempt.status,
        "learner": serialize_learner(learner),
    }


@app.post("/api/lesson-attempts/{attempt_id}/answer")
def answer_exercise(
    attempt_id: int,
    payload: AnswerRequest,
    db: Session = Depends(get_db),
):
    attempt = db.get(models.LessonAttempt, attempt_id)
    learner = db.get(models.Learner, payload.learner_id)
    exercise = db.get(models.Exercise, payload.exercise_id)

    if not attempt or not learner or not exercise:
        raise HTTPException(status_code=404, detail="Attempt, learner, or exercise not found")
    if attempt.status != "in_progress":
        raise HTTPException(status_code=400, detail="Attempt is not active")

    expected = normalize_answer(exercise.correct_answer)
    provided = normalize_answer(payload.answer)
    is_correct = expected == provided

    if exercise.type in {"multiple_choice", "fill_blank"}:
        correct_option = next((option.option_text for option in exercise.options if option.is_correct), None)
        is_correct = normalize_answer(correct_option) == provided
    elif exercise.type == "word_bank":
        is_correct = expected == provided
    elif exercise.type == "match_pairs":
        expected_pairs = sorted(pair.strip().lower() for pair in exercise.correct_answer.split(","))
        provided_pairs = sorted(pair.strip().lower() for pair in payload.answer.split(","))
        is_correct = expected_pairs == provided_pairs

    previous = (
        db.query(models.ExerciseAttempt)
        .filter(
            models.ExerciseAttempt.lesson_attempt_id == attempt.id,
            models.ExerciseAttempt.exercise_id == exercise.id,
        )
        .first()
    )
    if previous:
        previous.learner_answer = payload.answer
        previous.is_correct = is_correct
    else:
        db.add(
            models.ExerciseAttempt(
                lesson_attempt_id=attempt.id,
                exercise_id=exercise.id,
                learner_answer=payload.answer,
                is_correct=is_correct,
            )
        )

    if is_correct:
        attempt.correct_count += 1
    else:
        attempt.wrong_count += 1
        learner.hearts = max(0, learner.hearts - 1)

    db.commit()

    return {
        "correct": is_correct,
        "correctAnswer": exercise.correct_answer,
        "explanation": exercise.explanation,
        "learner": serialize_learner(learner),
        "attempt": {
            "id": attempt.id,
            "correctCount": attempt.correct_count,
            "wrongCount": attempt.wrong_count,
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
        .options(joinedload(models.LessonAttempt.lesson).joinedload(models.Lesson.level))
        .filter(models.LessonAttempt.id == attempt_id)
        .first()
    )
    learner = db.get(models.Learner, payload.learner_id)

    if not attempt or not learner:
        raise HTTPException(status_code=404, detail="Attempt or learner not found")
    if attempt.status == "completed":
        return {"attemptId": attempt.id, "learner": serialize_learner(learner)}

    answered_count = (
        db.query(models.ExerciseAttempt)
        .filter(models.ExerciseAttempt.lesson_attempt_id == attempt.id)
        .count()
    )
    exercise_count = (
        db.query(models.Exercise)
        .filter(models.Exercise.lesson_id == attempt.lesson_id)
        .count()
    )
    if exercise_count and answered_count < exercise_count:
        raise HTTPException(status_code=400, detail="Lesson still has unanswered exercises")

    xp_earned = max(5, attempt.lesson.xp_reward + attempt.correct_count * 2 - attempt.wrong_count)
    today = date.today()
    yesterday = today - timedelta(days=1)

    if learner.last_activity_date == today:
        pass
    elif learner.last_activity_date == yesterday:
        learner.current_streak += 1
    else:
        learner.current_streak = 1

    learner.longest_streak = max(learner.longest_streak, learner.current_streak)
    learner.last_activity_date = today
    learner.total_xp += xp_earned
    learner.today_xp += xp_earned

    attempt.status = "completed"
    attempt.xp_earned = xp_earned
    attempt.completed_at = datetime.utcnow()

    progress = (
        db.query(models.LearnerProgress)
        .filter(
            models.LearnerProgress.learner_id == learner.id,
            models.LearnerProgress.level_id == attempt.lesson.level_id,
        )
        .first()
    )
    if progress:
        progress.completed_lessons = min(progress.total_lessons, progress.completed_lessons + 1)
        progress.is_completed = progress.completed_lessons >= progress.total_lessons
        progress.crown_level = max(progress.crown_level, 1 if progress.is_completed else progress.crown_level)

        next_level = (
            db.query(models.Level)
            .filter(models.Level.required_level_id == attempt.lesson.level_id)
            .first()
        )
        if next_level:
            next_progress = (
                db.query(models.LearnerProgress)
                .filter(
                    models.LearnerProgress.learner_id == learner.id,
                    models.LearnerProgress.level_id == next_level.id,
                )
                .first()
            )
            if next_progress:
                next_progress.is_unlocked = True

    db.commit()
    db.refresh(learner)

    return {
        "attemptId": attempt.id,
        "xpEarned": xp_earned,
        "correctCount": attempt.correct_count,
        "wrongCount": attempt.wrong_count,
        "learner": serialize_learner(learner),
    }


@app.post("/api/learners/regain-heart")
def regain_heart(payload: RegainHeartRequest, db: Session = Depends(get_db)):
    learner = db.get(models.Learner, payload.learner_id)
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")
    if learner.hearts >= learner.max_hearts:
        return serialize_learner(learner)
    if learner.gems < payload.cost:
        raise HTTPException(status_code=400, detail="Not enough gems")

    learner.gems -= payload.cost
    learner.hearts += 1
    learner.last_heart_refill_at = datetime.utcnow()
    db.commit()
    db.refresh(learner)
    return serialize_learner(learner)
