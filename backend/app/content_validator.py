from app import models


class ContentValidationError(ValueError):
    pass


def validate_seed_content(db):
    errors = []
    exercises = db.query(models.Exercise).all()

    for exercise in exercises:
        label = f"exercise {exercise.id} ({exercise.exercise_type})"
        if exercise.exercise_type == "multiple_choice":
            if len(exercise.options) < 2:
                errors.append(f"{label}: multiple_choice needs at least two options")
            correct_count = sum(1 for option in exercise.options if option.is_correct)
            if correct_count != 1:
                errors.append(f"{label}: multiple_choice needs exactly one correct option")
        elif exercise.exercise_type == "translate_word_bank":
            ordered = sorted(
                option.correct_order
                for option in exercise.options
                if option.correct_order is not None
            )
            if not ordered:
                errors.append(f"{label}: translate_word_bank needs ordered answer options")
            elif ordered != list(range(1, len(ordered) + 1)):
                errors.append(f"{label}: correct_order values must be continuous")
        elif exercise.exercise_type == "match_pairs":
            if len(exercise.match_pairs) < 2:
                errors.append(f"{label}: match_pairs needs at least two pairs")
        elif exercise.exercise_type == "fill_blank":
            if "{{blank}}" not in exercise.prompt_text:
                errors.append(f"{label}: fill_blank prompt_text must contain {{blank}}")
            if not exercise.accepted_answers:
                errors.append(f"{label}: fill_blank needs an accepted answer")
        elif exercise.exercise_type == "type_answer":
            if not exercise.accepted_answers:
                errors.append(f"{label}: type_answer needs an accepted answer")

    lessons = db.query(models.Lesson).all()
    for lesson in lessons:
        if not any(link.is_required for link in lesson.lesson_exercises):
            errors.append(f"lesson {lesson.id}: lesson needs at least one required exercise")

    published_levels = db.query(models.Level).filter(models.Level.is_published == 1).all()
    for level in published_levels:
        if not any(lesson.is_published for lesson in level.lessons):
            errors.append(f"level {level.id}: published level needs at least one published lesson")

    if errors:
        raise ContentValidationError("\n".join(errors))
