# English → Spanish seed package

This package contains original beginner Spanish content for a Duolingo-style
full-stack assignment. It is inspired by communicative, bite-sized progression,
but does not reproduce Duolingo's proprietary lesson bank.

## Generated curriculum

- 2 sections
- 8 units
- 32 learning levels
- 8 quest-chest reward nodes
- 40 displayed path items
- 128 lessons
- 1,024 exercises
- Exactly 8 exercises per lesson
- All five required exercise types appear in every lesson

## Files

- `english_to_spanish_course_seed.json`: canonical application seed document.
- `english_to_spanish_seed.db`: inspectable SQLite database with content tables.
- `seed_loader_example.py`: model-agnostic SQLAlchemy integration outline.
- `seed_qa_report.json`: counts and integrity checks.

## Path order in every unit

1. Learning level 1
2. Learning level 2
3. Quest chest reward
4. Learning level 3
5. Learning level 4

The reward is not treated as a lesson level. Add `unit_rewards` and
`unit_path_items` to the earlier schema so heterogeneous path items have one
stable display order.

## Exercise progression

Every lesson contains:

- multiple choice
- translation with a word bank
- matching pairs
- fill in the blank
- typed answer

Later lessons contain more fill-in and typed-answer exercises than the first
lesson.

## Safe seeding strategy

Use `seed_key` as a stable natural identifier and upsert records. Wrap the full
seed in one transaction. Published exercises that already have learner attempts
should be versioned instead of overwritten or deleted.
