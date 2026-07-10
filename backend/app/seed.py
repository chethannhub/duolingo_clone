from datetime import datetime

from app.database import SessionLocal, Base, engine
from app.models import (
    Achievement,
    Course,
    Exercise,
    ExerciseOption,
    LeaderboardEntry,
    Learner,
    LearnerProgress,
    Lesson,
    Level,
    Section,
    Unit,
)


def seed_database():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        existing_learner = db.query(Learner).first()

        if existing_learner:
            print("Database already seeded.")
            return

        # -------------------------
        # Learners
        # -------------------------
        main_learner = Learner(
            name="Chethan",
            email="chethan@example.com",
            total_xp=120,
            today_xp=20,
            daily_xp_goal=30,
            current_streak=3,
            longest_streak=5,
            hearts=5,
            max_hearts=5,
            gems=500,
            last_heart_refill_at=datetime.utcnow(),
        )

        learner_2 = Learner(
            name="Aarav",
            email="aarav@example.com",
            total_xp=900,
            today_xp=50,
            daily_xp_goal=30,
            current_streak=10,
            longest_streak=15,
            hearts=5,
            gems=300,
            last_heart_refill_at=datetime.utcnow(),
        )

        learner_3 = Learner(
            name="Priya",
            email="priya@example.com",
            total_xp=750,
            today_xp=40,
            daily_xp_goal=30,
            current_streak=8,
            longest_streak=12,
            hearts=5,
            gems=450,
            last_heart_refill_at=datetime.utcnow(),
        )

        db.add_all([main_learner, learner_2, learner_3])
        db.commit()

        # -------------------------
        # Course
        # -------------------------
        course = Course(
            title="Spanish for English Speakers",
            source_language="English",
            target_language="Spanish",
            description="Learn basic Spanish words and phrases.",
        )

        db.add(course)
        db.commit()

        # -------------------------
        # Section
        # -------------------------
        section_1 = Section(
            course_id=course.id,
            title="Section 1: Rookie",
            description="Start with basic Spanish words and simple phrases.",
            order_index=1,
        )

        db.add(section_1)
        db.commit()

        # -------------------------
        # Units
        # -------------------------
        unit_1 = Unit(
            section_id=section_1.id,
            title="Unit 1",
            description="Learn basic words and greetings.",
            order_index=1,
        )

        unit_2 = Unit(
            section_id=section_1.id,
            title="Unit 2",
            description="Learn food, drinks, and simple sentences.",
            order_index=2,
        )

        db.add_all([unit_1, unit_2])
        db.commit()

        # -------------------------
        # Levels
        # -------------------------
        level_1 = Level(
            unit_id=unit_1.id,
            title="Basics",
            type="lesson",
            icon="star",
            order_index=1,
            required_level_id=None,
        )

        db.add(level_1)
        db.commit()

        level_2 = Level(
            unit_id=unit_1.id,
            title="Greetings",
            type="lesson",
            icon="message-circle",
            order_index=2,
            required_level_id=level_1.id,
        )

        db.add(level_2)
        db.commit()

        level_3 = Level(
            unit_id=unit_2.id,
            title="Food",
            type="lesson",
            icon="apple",
            order_index=1,
            required_level_id=level_2.id,
        )

        level_4 = Level(
            unit_id=unit_2.id,
            title="Drinks",
            type="lesson",
            icon="cup",
            order_index=2,
            required_level_id=level_3.id,
        )

        db.add_all([level_3, level_4])
        db.commit()

        # -------------------------
        # Lessons
        # -------------------------
        lesson_1 = Lesson(
            level_id=level_1.id,
            title="Basics Lesson 1",
            order_index=1,
            xp_reward=10,
        )

        lesson_2 = Lesson(
            level_id=level_2.id,
            title="Greetings Lesson 1",
            order_index=1,
            xp_reward=10,
        )

        lesson_3 = Lesson(
            level_id=level_3.id,
            title="Food Lesson 1",
            order_index=1,
            xp_reward=10,
        )

        lesson_4 = Lesson(
            level_id=level_4.id,
            title="Drinks Lesson 1",
            order_index=1,
            xp_reward=10,
        )

        db.add_all([lesson_1, lesson_2, lesson_3, lesson_4])
        db.commit()

        # -------------------------
        # Exercises for Lesson 1
        # -------------------------

        # Exercise 1: Multiple Choice
        ex1 = Exercise(
            lesson_id=lesson_1.id,
            type="multiple_choice",
            question="What does 'hola' mean?",
            prompt="Choose the correct meaning.",
            correct_answer="Hello",
            explanation="'Hola' means 'Hello'.",
            order_index=1,
        )
        db.add(ex1)
        db.commit()

        db.add_all(
            [
                ExerciseOption(exercise_id=ex1.id, option_text="Hello", is_correct=True),
                ExerciseOption(exercise_id=ex1.id, option_text="Goodbye", is_correct=False),
                ExerciseOption(exercise_id=ex1.id, option_text="Thanks", is_correct=False),
                ExerciseOption(exercise_id=ex1.id, option_text="Water", is_correct=False),
            ]
        )

        # Exercise 2: Fill Blank
        ex2 = Exercise(
            lesson_id=lesson_1.id,
            type="fill_blank",
            question="Yo ____ Chethan.",
            prompt="Fill in the blank.",
            correct_answer="soy",
            explanation="'Yo soy Chethan' means 'I am Chethan'.",
            order_index=2,
        )
        db.add(ex2)
        db.commit()

        db.add_all(
            [
                ExerciseOption(exercise_id=ex2.id, option_text="soy", is_correct=True),
                ExerciseOption(exercise_id=ex2.id, option_text="como", is_correct=False),
                ExerciseOption(exercise_id=ex2.id, option_text="bebo", is_correct=False),
            ]
        )

        # Exercise 3: Type Answer
        ex3 = Exercise(
            lesson_id=lesson_1.id,
            type="type_answer",
            question="Translate: I am a boy",
            prompt="Type in Spanish.",
            correct_answer="Yo soy un niño",
            explanation="'I am a boy' means 'Yo soy un niño'.",
            order_index=3,
        )
        db.add(ex3)

        # Exercise 4: Word Bank
        ex4 = Exercise(
            lesson_id=lesson_1.id,
            type="word_bank",
            question="Translate: I am Chethan",
            prompt="Tap the words in the correct order.",
            correct_answer="Yo soy Chethan",
            explanation="'I am Chethan' means 'Yo soy Chethan'.",
            order_index=4,
        )
        db.add(ex4)
        db.commit()

        db.add_all(
            [
                ExerciseOption(exercise_id=ex4.id, option_text="Yo", is_correct=True),
                ExerciseOption(exercise_id=ex4.id, option_text="soy", is_correct=True),
                ExerciseOption(exercise_id=ex4.id, option_text="Chethan", is_correct=True),
                ExerciseOption(exercise_id=ex4.id, option_text="como", is_correct=False),
                ExerciseOption(exercise_id=ex4.id, option_text="agua", is_correct=False),
            ]
        )

        # Exercise 5: Match Pairs
        ex5 = Exercise(
            lesson_id=lesson_1.id,
            type="match_pairs",
            question="Match the pairs.",
            prompt="Select matching English and Spanish words.",
            correct_answer="hello:hola,water:agua,bread:pan",
            explanation="Match each English word with the correct Spanish word.",
            order_index=5,
        )
        db.add(ex5)
        db.commit()

        db.add_all(
            [
                ExerciseOption(exercise_id=ex5.id, option_text="Hello", pair_key="hello"),
                ExerciseOption(exercise_id=ex5.id, option_text="Hola", pair_key="hello"),
                ExerciseOption(exercise_id=ex5.id, option_text="Water", pair_key="water"),
                ExerciseOption(exercise_id=ex5.id, option_text="Agua", pair_key="water"),
                ExerciseOption(exercise_id=ex5.id, option_text="Bread", pair_key="bread"),
                ExerciseOption(exercise_id=ex5.id, option_text="Pan", pair_key="bread"),
            ]
        )

        # -------------------------
        # Exercises for other lessons
        # -------------------------
        ex6 = Exercise(
            lesson_id=lesson_2.id,
            type="multiple_choice",
            question="What does 'adiós' mean?",
            prompt="Choose the correct meaning.",
            correct_answer="Goodbye",
            explanation="'Adiós' means 'Goodbye'.",
            order_index=1,
        )
        db.add(ex6)
        db.commit()

        db.add_all(
            [
                ExerciseOption(exercise_id=ex6.id, option_text="Hello", is_correct=False),
                ExerciseOption(exercise_id=ex6.id, option_text="Goodbye", is_correct=True),
                ExerciseOption(exercise_id=ex6.id, option_text="Please", is_correct=False),
                ExerciseOption(exercise_id=ex6.id, option_text="Apple", is_correct=False),
            ]
        )

        ex7 = Exercise(
            lesson_id=lesson_3.id,
            type="multiple_choice",
            question="What does 'pan' mean?",
            prompt="Choose the correct meaning.",
            correct_answer="Bread",
            explanation="'Pan' means 'Bread'.",
            order_index=1,
        )
        db.add(ex7)
        db.commit()

        db.add_all(
            [
                ExerciseOption(exercise_id=ex7.id, option_text="Water", is_correct=False),
                ExerciseOption(exercise_id=ex7.id, option_text="Bread", is_correct=True),
                ExerciseOption(exercise_id=ex7.id, option_text="Milk", is_correct=False),
                ExerciseOption(exercise_id=ex7.id, option_text="Hello", is_correct=False),
            ]
        )

        ex8 = Exercise(
            lesson_id=lesson_4.id,
            type="multiple_choice",
            question="What does 'agua' mean?",
            prompt="Choose the correct meaning.",
            correct_answer="Water",
            explanation="'Agua' means 'Water'.",
            order_index=1,
        )
        db.add(ex8)
        db.commit()

        db.add_all(
            [
                ExerciseOption(exercise_id=ex8.id, option_text="Bread", is_correct=False),
                ExerciseOption(exercise_id=ex8.id, option_text="Water", is_correct=True),
                ExerciseOption(exercise_id=ex8.id, option_text="Goodbye", is_correct=False),
                ExerciseOption(exercise_id=ex8.id, option_text="Boy", is_correct=False),
            ]
        )

        db.commit()

        # -------------------------
        # Learner Progress
        # -------------------------
        all_levels = [level_1, level_2, level_3, level_4]

        for level in all_levels:
            progress = LearnerProgress(
                learner_id=main_learner.id,
                level_id=level.id,
                completed_lessons=0,
                total_lessons=len(level.lessons),
                crown_level=0,
                is_unlocked=True if level.id == level_1.id else False,
                is_completed=False,
            )
            db.add(progress)

        db.commit()

        # -------------------------
        # Leaderboard
        # -------------------------
        db.add_all(
            [
                LeaderboardEntry(
                    learner_id=main_learner.id,
                    weekly_xp=120,
                    rank=3,
                ),
                LeaderboardEntry(
                    learner_id=learner_2.id,
                    weekly_xp=900,
                    rank=1,
                ),
                LeaderboardEntry(
                    learner_id=learner_3.id,
                    weekly_xp=750,
                    rank=2,
                ),
            ]
        )

        # -------------------------
        # Achievements
        # -------------------------
        db.add_all(
            [
                Achievement(
                    title="First Lesson",
                    description="Complete your first lesson.",
                    icon="star",
                    condition_type="completed_lessons",
                    condition_value=1,
                ),
                Achievement(
                    title="100 XP Club",
                    description="Earn 100 total XP.",
                    icon="zap",
                    condition_type="total_xp",
                    condition_value=100,
                ),
                Achievement(
                    title="3 Day Streak",
                    description="Maintain a 3 day streak.",
                    icon="flame",
                    condition_type="streak",
                    condition_value=3,
                ),
            ]
        )

        db.commit()

        print("Database seeded successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()