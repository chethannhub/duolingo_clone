import json
from datetime import date, datetime
from pathlib import Path

from app import models


def normalize_answer(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def create_learners(db):
    learners = [
        models.Learner(
            username="chethan",
            email="chethan@example.com",
            display_name="Chethan",
            timezone="Asia/Kolkata",
            locale="en-IN",
        ),
        models.Learner(
            username="aarav",
            email="aarav@example.com",
            display_name="Aarav",
            timezone="Asia/Kolkata",
            locale="en-IN",
        ),
        models.Learner(
            username="priya",
            email="priya@example.com",
            display_name="Priya",
            timezone="Asia/Kolkata",
            locale="en-IN",
        ),
        models.Learner(
            username="meera",
            email="meera@example.com",
            display_name="Meera",
            timezone="Asia/Kolkata",
            locale="en-IN",
        ),
        models.Learner(
            username="rohan",
            email="rohan@example.com",
            display_name="Rohan",
            timezone="Asia/Kolkata",
            locale="en-IN",
        ),
    ]
    db.add_all(learners)
    db.flush()

    stats = [
        models.LearnerStats(
            learner_id=learners[0].id,
            total_xp=120,
            current_hearts=5,
            max_hearts=5,
            gems=500,
            current_streak=3,
            longest_streak=5,
            last_streak_date=date.today().isoformat(),
            daily_goal_xp=20,
        ),
        models.LearnerStats(
            learner_id=learners[1].id,
            total_xp=900,
            current_hearts=5,
            max_hearts=5,
            gems=300,
            current_streak=10,
            longest_streak=15,
            last_streak_date=date.today().isoformat(),
            daily_goal_xp=20,
        ),
        models.LearnerStats(
            learner_id=learners[2].id,
            total_xp=750,
            current_hearts=5,
            max_hearts=5,
            gems=450,
            current_streak=8,
            longest_streak=12,
            last_streak_date=date.today().isoformat(),
            daily_goal_xp=20,
        ),
        models.LearnerStats(
            learner_id=learners[3].id,
            total_xp=620,
            current_hearts=5,
            max_hearts=5,
            gems=250,
            current_streak=6,
            longest_streak=9,
            last_streak_date=date.today().isoformat(),
            daily_goal_xp=20,
        ),
        models.LearnerStats(
            learner_id=learners[4].id,
            total_xp=410,
            current_hearts=5,
            max_hearts=5,
            gems=200,
            current_streak=2,
            longest_streak=4,
            last_streak_date=date.today().isoformat(),
            daily_goal_xp=20,
        ),
    ]
    db.add_all([models.LearnerSettings(learner_id=learner.id) for learner in learners])
    db.add_all(stats)
    return learners


def create_course_path(db):
    seed_path = (
        Path(__file__).resolve().parents[1]
        / "duolingo_spanish_seed"
        / "english_to_spanish_course_seed.json"
    )
    with seed_path.open("r", encoding="utf-8") as file:
        document = json.load(file)

    course_doc = document["course"]
    source_doc = course_doc["source_language"]
    target_doc = course_doc["target_language"]

    english = models.Language(
        code=source_doc["code"],
        name=source_doc["name"],
        native_name=source_doc.get("native_name"),
    )
    spanish = models.Language(
        code=target_doc["code"],
        name=target_doc["name"],
        native_name=target_doc.get("native_name"),
    )
    db.add_all([english, spanish])
    db.flush()

    course = models.Course(
        source_language_id=english.id,
        target_language_id=spanish.id,
        slug=course_doc["slug"],
        title=course_doc["title"],
        description=course_doc.get("description"),
        status=course_doc.get("status", "published"),
        content_version=course_doc.get("content_version", 1),
        is_featured=1,
        published_at=datetime.utcnow().isoformat(),
    )
    db.add(course)
    db.flush()

    levels = []
    lessons = []
    levels_by_key = {}
    rewards_by_key = {}
    previous_level = None

    for section_doc in document["sections"]:
        section = models.Section(
            course_id=course.id,
            position=section_doc["position"],
            title=section_doc["title"],
            description=section_doc.get("description"),
            cefr_level=section_doc.get("cefr_level"),
            is_published=1,
        )
        db.add(section)
        db.flush()

        for unit_doc in section_doc["units"]:
            unit = models.Unit(
                section_id=section.id,
                position=unit_doc["position"],
                title=unit_doc["title"],
                description=unit_doc.get("objective"),
                guidebook_text=unit_doc.get("guidebook_text"),
                is_published=1,
            )
            db.add(unit)
            db.flush()

            reward_doc = unit_doc.get("reward")
            if reward_doc:
                reward = models.UnitReward(
                    unit_id=unit.id,
                    seed_key=reward_doc["key"],
                    reward_type=reward_doc.get("reward_type", "quest_chest"),
                    title=reward_doc["title"],
                    description=reward_doc.get("description"),
                    gems_reward=reward_doc.get("gems_reward", 0),
                    icon_key=reward_doc.get("icon_key", "chest"),
                    is_repeatable=1 if reward_doc.get("is_repeatable") else 0,
                    required_completed_levels=reward_doc.get("required_completed_levels", 0),
                )
                db.add(reward)
                db.flush()
                rewards_by_key[reward_doc["key"]] = reward

            for level_doc in unit_doc["levels"]:
                level = models.Level(
                    unit_id=unit.id,
                    position=level_doc["position"],
                    level_type=level_doc.get("level_type", "skill"),
                    title=level_doc["title"],
                    description=level_doc.get("description"),
                    icon_key=level_doc.get("icon_key", "star"),
                    reward_gems=level_doc.get("reward_gems", 0),
                    is_published=1 if level_doc.get("is_published", True) else 0,
                )
                db.add(level)
                db.flush()
                if previous_level is not None:
                    db.add(
                        models.LevelPrerequisite(
                            level_id=level.id,
                            prerequisite_level_id=previous_level.id,
                        )
                    )
                previous_level = level
                levels.append(level)
                levels_by_key[level_doc["key"]] = level

                for lesson_doc in level_doc["lessons"]:
                    lesson = models.Lesson(
                        level_id=level.id,
                        position=lesson_doc["position"],
                        title=lesson_doc["title"],
                        xp_reward=lesson_doc.get("xp_reward", 10),
                        estimated_minutes=lesson_doc.get("estimated_minutes", 3),
                        is_published=1 if lesson_doc.get("is_published", True) else 0,
                    )
                    db.add(lesson)
                    db.flush()
                    lessons.append(lesson)

                    for exercise_doc in lesson_doc["exercises"]:
                        exercise = models.Exercise(
                            exercise_type=exercise_doc["exercise_type"],
                            instruction_text=exercise_doc["instruction_text"],
                            prompt_text=exercise_doc["prompt_text"],
                            hint_text=exercise_doc.get("hint_text"),
                            explanation_text=exercise_doc.get("explanation_text"),
                            audio_url=exercise_doc.get("audio_url"),
                            image_url=exercise_doc.get("image_url"),
                            answer_match_mode=exercise_doc.get("answer_match_mode", "normalized"),
                            difficulty=exercise_doc.get("difficulty", 1),
                            metadata_json=json.dumps(exercise_doc.get("metadata", {})),
                            version=exercise_doc.get("version", 1),
                            is_published=1 if exercise_doc.get("is_published", True) else 0,
                        )
                        db.add(exercise)
                        db.flush()
                        db.add(
                            models.LessonExercise(
                                lesson_id=lesson.id,
                                exercise_id=exercise.id,
                                position=exercise_doc["position"],
                            )
                        )
                        for option_doc in exercise_doc.get("options", []):
                            db.add(
                                models.ExerciseOption(
                                    exercise_id=exercise.id,
                                    option_text=option_doc["text"],
                                    position=option_doc["position"],
                                    is_correct=1 if option_doc.get("is_correct") else 0,
                                    correct_order=option_doc.get("correct_order"),
                                )
                            )
                        for pair_doc in exercise_doc.get("pairs", []):
                            db.add(
                                models.ExerciseMatchPair(
                                    exercise_id=exercise.id,
                                    left_text=pair_doc["left_text"],
                                    right_text=pair_doc["right_text"],
                                    position=pair_doc["position"],
                                )
                            )
                        for index, answer_doc in enumerate(exercise_doc.get("accepted_answers", []), start=1):
                            db.add(
                                models.ExerciseAcceptedAnswer(
                                    exercise_id=exercise.id,
                                    answer_text=answer_doc["answer_text"],
                                    normalized_answer=answer_doc.get(
                                        "normalized_answer",
                                        normalize_answer(answer_doc["answer_text"]),
                                    ),
                                    is_primary=1 if answer_doc.get("is_primary", index == 1) else 0,
                                )
                            )

            for path_item_doc in unit_doc.get("path_items", []):
                db.add(
                    models.UnitPathItem(
                        unit_id=unit.id,
                        position=path_item_doc["position"],
                        item_type=path_item_doc["item_type"],
                        level_id=(
                            levels_by_key[path_item_doc["level_key"]].id
                            if path_item_doc.get("level_key")
                            else None
                        ),
                        reward_id=(
                            rewards_by_key[path_item_doc["reward_key"]].id
                            if path_item_doc.get("reward_key")
                            else None
                        ),
                    )
                )

    return course, levels, lessons


def add_exercise(
    db,
    lesson,
    position,
    exercise_type,
    instruction_text,
    prompt_text,
    primary_answer=None,
    explanation_text=None,
    hint_text=None,
    options=None,
    pairs=None,
    accepted_answers=None,
):
    exercise = models.Exercise(
        exercise_type=exercise_type,
        instruction_text=instruction_text,
        prompt_text=prompt_text,
        hint_text=hint_text,
        explanation_text=explanation_text,
        is_published=1,
    )
    db.add(exercise)
    db.flush()

    db.add(
        models.LessonExercise(
            lesson_id=lesson.id,
            exercise_id=exercise.id,
            position=position,
        )
    )

    answer_values = accepted_answers or ([primary_answer] if primary_answer else [])
    for index, answer_text in enumerate(answer_values, start=1):
        db.add(
            models.ExerciseAcceptedAnswer(
                exercise_id=exercise.id,
                answer_text=answer_text,
                normalized_answer=normalize_answer(answer_text),
                is_primary=1 if index == 1 else 0,
            )
        )
    for index, option in enumerate(options or [], start=1):
        db.add(
            models.ExerciseOption(
                exercise_id=exercise.id,
                option_text=option["text"],
                position=index,
                is_correct=1 if option.get("correct") else 0,
                correct_order=option.get("correct_order"),
            )
        )
    for index, pair in enumerate(pairs or [], start=1):
        db.add(
            models.ExerciseMatchPair(
                exercise_id=exercise.id,
                left_text=pair["left"],
                right_text=pair["right"],
                position=index,
            )
        )
    return exercise


def create_exercises(db, lessons):
    return lessons


def create_progress(db, learners, course, levels, lessons):
    enrollment = models.CourseEnrollment(
        learner_id=learners[0].id,
        course_id=course.id,
        is_selected=1,
        current_level_id=levels[0].id,
        current_lesson_id=lessons[0].id,
        last_accessed_at=datetime.utcnow().isoformat(),
    )
    db.add(enrollment)
    db.flush()
    for level in levels:
        db.add(
            models.LearnerLevelProgress(
                enrollment_id=enrollment.id,
                level_id=level.id,
                started_at=datetime.utcnow().isoformat() if level.id == levels[0].id else None,
            )
        )
    for lesson in lessons:
        db.add(models.LearnerLessonProgress(enrollment_id=enrollment.id, lesson_id=lesson.id))


def create_activity_and_achievements(db, learners):
    today = date.today().isoformat()
    now = datetime.utcnow().isoformat()
    db.add_all(
        [
            models.LearnerDailyActivity(
                learner_id=learners[0].id,
                local_date=today,
                xp_earned=120,
                lessons_completed=3,
                exercises_answered=15,
                streak_qualified=1,
                daily_goal_reached=1,
                first_activity_at=now,
                last_activity_at=now,
            ),
            models.LearnerDailyActivity(
                learner_id=learners[1].id,
                local_date=today,
                xp_earned=900,
                lessons_completed=8,
                exercises_answered=40,
                streak_qualified=1,
                daily_goal_reached=1,
                first_activity_at=now,
                last_activity_at=now,
            ),
            models.LearnerDailyActivity(
                learner_id=learners[2].id,
                local_date=today,
                xp_earned=750,
                lessons_completed=6,
                exercises_answered=30,
                streak_qualified=1,
                daily_goal_reached=1,
                first_activity_at=now,
                last_activity_at=now,
            ),
            models.LearnerDailyActivity(
                learner_id=learners[3].id,
                local_date=today,
                xp_earned=620,
                lessons_completed=5,
                exercises_answered=25,
                streak_qualified=1,
                daily_goal_reached=1,
                first_activity_at=now,
                last_activity_at=now,
            ),
            models.LearnerDailyActivity(
                learner_id=learners[4].id,
                local_date=today,
                xp_earned=410,
                lessons_completed=4,
                exercises_answered=20,
                streak_qualified=1,
                daily_goal_reached=1,
                first_activity_at=now,
                last_activity_at=now,
            ),
        ]
    )
    seeded_xp = [120, 900, 750, 620, 410]
    db.add_all(
        [
            models.XpEvent(
                learner_id=learner.id,
                source_type="seed",
                amount=amount,
                event_key=f"seed-xp:learner:{learner.id}",
                local_date=today,
            )
            for learner, amount in zip(learners, seeded_xp)
        ]
        + [
            models.HeartEvent(
                learner_id=learners[0].id,
                event_type="seed",
                delta=5,
                balance_after=5,
                event_key="seed-hearts:learner:1",
            ),
        ]
    )
    achievements = [
        models.Achievement(
            key="first_steps",
            name="First Steps",
            description="Complete 1 lesson.",
            icon_key="footprints",
            metric_type="lessons_completed",
            threshold_value=1,
            reward_gems=5,
        ),
        models.Achievement(
            key="xp_hunter",
            name="XP Hunter",
            description="Earn 100 XP.",
            icon_key="zap",
            metric_type="total_xp",
            threshold_value=100,
            reward_gems=10,
        ),
        models.Achievement(
            key="on_fire",
            name="On Fire",
            description="Reach a 3-day streak.",
            icon_key="flame",
            metric_type="current_streak",
            threshold_value=3,
            reward_gems=10,
        ),
        models.Achievement(
            key="scholar",
            name="Scholar",
            description="Complete 5 levels.",
            icon_key="graduation-cap",
            metric_type="levels_completed",
            threshold_value=5,
            reward_gems=25,
        ),
        models.Achievement(
            key="perfect_lesson",
            name="Perfect Lesson",
            description="Complete a lesson with no mistakes.",
            icon_key="badge-check",
            metric_type="perfect_lessons",
            threshold_value=1,
            reward_gems=10,
        ),
    ]
    db.add_all(achievements)
    db.flush()

    progress_by_key = {
        "first_steps": (3, now),
        "xp_hunter": (120, now),
        "on_fire": (3, now),
        "scholar": (0, None),
        "perfect_lesson": (0, None),
    }
    db.add_all(
        [
            models.LearnerAchievement(
                learner_id=learners[0].id,
                achievement_id=achievement.id,
                progress_value=progress_by_key[achievement.key][0],
                unlocked_at=progress_by_key[achievement.key][1],
                updated_at=now,
            )
            for achievement in achievements
        ]
    )
