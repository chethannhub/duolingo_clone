from app.database import Base, SessionLocal, engine
from app import models
from app.content_validator import validate_seed_content
from app.seed_helpers import (
    create_activity_and_achievements,
    create_course_path,
    create_exercises,
    create_learners,
    create_progress,
)


def reset_schema():
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        Base.metadata.drop_all(bind=connection)
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")


def seed_database(reset: bool = True):
    if reset:
        reset_schema()
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(models.Learner).first():
            print("Database already seeded.")
            return

        learners = create_learners(db)
        course, levels, lessons = create_course_path(db)
        create_exercises(db, lessons)
        create_progress(db, learners, course, levels, lessons)
        create_activity_and_achievements(db, learners)
        db.flush()
        validate_seed_content(db)

        db.commit()
        print("Database seeded successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
