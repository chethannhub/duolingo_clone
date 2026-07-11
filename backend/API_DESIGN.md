# Backend API Design

Base URL: `http://localhost:8000/api/v1`

Swagger/OpenAPI:

- `http://localhost:8000/docs`
- `http://localhost:8000/openapi.json`

## Current Learner

Learner-specific endpoints use `/me/...`. The backend resolves the seeded learner with `get_current_learner()`, so the frontend does not send `learner_id`.

## Endpoint Summary

Health:

- `GET /health/live`
- `GET /health/ready`

Content:

- `GET /courses`
- `GET /courses/{course_slug}`
- `GET /courses/{course_id}/sections`
- `GET /sections/{section_id}/units`
- `GET /units/{unit_id}`
- `GET /units/{unit_id}/guidebook`
- `GET /levels/{level_id}/lessons`
- `GET /lessons/{lesson_id}/preview`

Learning path:

- `GET /me/learning-path`
- `GET /me/learning-path?section_id={section_id}`

Lesson loop:

- `POST /lessons/{lesson_id}/attempts`
- `GET /lesson-attempts/{attempt_token}`
- `POST /lesson-attempts/{attempt_token}/answers`
- `POST /lesson-attempts/{attempt_token}/abandon`

Gamification:

- `GET /me/hearts`
- `POST /me/hearts/refill`
- `POST /me/rewards/{reward_id}/claim`
- `GET /me/profile`
- `GET /me/activity`
- `GET /me/achievements`
- `GET /me/daily-goal`
- `PATCH /me/daily-goal`
- `GET /leaderboards/weekly`
- `GET /me/settings`
- `PATCH /me/settings`

## Progression Rules

The backend computes all level and reward states. Level states are `locked`, `available`, `current`, and `completed`. Reward states are `locked`, `claimable`, and `claimed`.

A level is available when its prerequisites are complete. A reward chest is claimable when the configured number of levels in that unit are completed. The frontend should render returned states directly.

## Lesson Lifecycle

Starting a lesson regenerates hearts lazily, checks enrollment and availability, verifies hearts, creates a `lesson_attempt`, snapshots ordered exercises into `lesson_attempt_items`, and returns only the first frontend-safe exercise.

Answer submission uses discriminated answer payloads. The server evaluates correctness, records an `exercise_attempt`, deducts at most one heart for an incorrect answer, and returns feedback plus the next safe exercise. The final answer automatically completes the lesson, awards idempotent XP, updates lesson and level progress, daily activity, streak, current course position, and achievements.

Frontend-safe exercise responses never include `is_correct`, `correct_order`, accepted answers, normalized answers, or match-pair relationships.

## Idempotency

Send `Idempotency-Key` for:

- starting a lesson
- submitting an answer
- claiming a reward
- refilling hearts

Answer submissions also include `client_submission_id`. Retries return the stored response instead of creating duplicate attempts, deducting hearts twice, or awarding XP/gems twice.

## Error Format

All API errors use:

```json
{
  "error": {
    "code": "LEVEL_LOCKED",
    "message": "Complete the previous level before starting this lesson.",
    "details": {},
    "request_id": "request-id"
  }
}
```

Stable codes include `COURSE_NOT_FOUND`, `COURSE_NOT_ENROLLED`, `LEVEL_LOCKED`, `LESSON_NOT_FOUND`, `LESSON_NOT_AVAILABLE`, `OUT_OF_HEARTS`, `ATTEMPT_NOT_FOUND`, `ATTEMPT_NOT_ACTIVE`, `ATTEMPT_ALREADY_COMPLETED`, `EXERCISE_NOT_CURRENT`, `ANSWER_ALREADY_SUBMITTED`, `ANSWER_PAYLOAD_INVALID`, `REWARD_LOCKED`, `REWARD_ALREADY_CLAIMED`, `INSUFFICIENT_GEMS`, `VALIDATION_ERROR`, and `INTERNAL_ERROR`.

## Frontend Mapping

- `/learn` -> `GET /me/learning-path`
- `/sections/[sectionId]` -> `GET /me/learning-path?section_id=...`
- lesson start -> `POST /lessons/{lessonId}/attempts`
- lesson resume -> `GET /lesson-attempts/{attemptToken}`
- answer submit -> `POST /lesson-attempts/{attemptToken}/answers`
- reward chest -> `POST /me/rewards/{rewardId}/claim`
- hearts modal -> `GET /me/hearts`, `POST /me/hearts/refill`
- `/leaderboard` -> `GET /leaderboards/weekly`
- `/profile` -> `GET /me/profile`, `GET /me/achievements`, `GET /me/activity`
- `/settings` -> `GET /me/settings`, `PATCH /me/settings`

## Lesson Player States

Recommended frontend state machine:

`loading -> answering -> submitting -> correct_feedback | incorrect_feedback -> answering`

Terminal states:

- `completed`
- `out_of_hearts`
- `failed`

After completion, refresh learning path, profile, achievements, hearts, daily goal, and weekly leaderboard.

## Migration Note

This repository currently does not include Alembic configuration. The SQLite seed reset recreates the schema with the current SQLAlchemy models. If Alembic is added later, create migrations for `lesson_attempt_items`, `exercise_attempts.client_submission_id`, reward claims, and idempotency records.
