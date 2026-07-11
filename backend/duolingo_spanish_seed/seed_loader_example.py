"""
Example loader for english_to_spanish_course_seed.json.

Adapt the model imports and attribute names to your SQLAlchemy project.
Use a single transaction and identify seed records by stable `key`/`seed_key`
so rerunning the seed is idempotent.
"""
from __future__ import annotations

import json
from pathlib import Path

SEED_FILE = Path(__file__).with_name("english_to_spanish_course_seed.json")


def load_seed_document() -> dict:
    with SEED_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_seed_document(document: dict) -> None:
    sections = document["sections"]
    assert len(sections) == 2

    units = [unit for section in sections for unit in section["units"]]
    levels = [level for unit in units for level in unit["levels"]]
    lessons = [lesson for level in levels for lesson in level["lessons"]]
    exercises = [
        exercise
        for lesson in lessons
        for exercise in lesson["exercises"]
    ]

    assert len(units) == 8
    assert len(levels) == 32
    assert len(lessons) == 128
    assert len(exercises) == 1024
    assert all(len(unit["path_items"]) == 5 for unit in units)
    assert all(len(level["lessons"]) == 4 for level in levels)
    assert all(len(lesson["exercises"]) == 8 for lesson in lessons)


def seed_course(session) -> None:
    """
    Recommended import order:

    1. languages
    2. course
    3. sections
    4. units
    5. rewards
    6. levels
    7. unit_path_items
    8. lessons
    9. exercises and subtype rows
    10. lesson_exercises

    Implement each insert as an upsert by stable key. Never delete learner
    attempts when reseeding published content.
    """
    document = load_seed_document()
    validate_seed_document(document)

    # Import your SQLAlchemy models here and map the JSON fields.
    # Keep the whole operation inside `with session.begin():`.
    raise NotImplementedError(
        "Map this loader to your project's SQLAlchemy model names."
    )


if __name__ == "__main__":
    seed = load_seed_document()
    validate_seed_document(seed)
    print("Seed document is valid.")
