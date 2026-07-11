# duolingo_clone

## Run The Backend

```bash
cd backend
.venv\Scripts\python.exe -m app.seed
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

FastAPI docs:

- `http://localhost:8000/docs`
- `http://localhost:8000/openapi.json`

API prefix:

- `http://localhost:8000/api/v1`

Useful health checks:

- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`

## Run The Frontend

```bash
cd frontend
npm install
npm run dev
```

Environment variable:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

## Generate Frontend API Types

Start the backend first, then run:

```bash
cd frontend
npm run generate:api
```

This writes OpenAPI types to `frontend/types/api.generated.ts`.

## API Design

See `backend/API_DESIGN.md` for endpoint details, lesson lifecycle, progression rules, error format, idempotency, and frontend page-to-endpoint mapping.

erDiagram
    LEARNERS ||--|| LEARNER_SETTINGS : has
    LEARNERS ||--|| LEARNER_STATS : has
    LEARNERS ||--o{ COURSE_ENROLLMENTS : enrolls
    LEARNERS ||--o{ XP_EVENTS : earns
    LEARNERS ||--o{ HEART_EVENTS : receives
    LEARNERS ||--o{ LEARNER_DAILY_ACTIVITY : records
    LEARNERS ||--o{ LEARNER_ACHIEVEMENTS : unlocks

    LANGUAGES ||--o{ COURSES : source_language
    LANGUAGES ||--o{ COURSES : target_language

    COURSES ||--o{ SECTIONS : contains
    SECTIONS ||--o{ UNITS : contains
    UNITS ||--o{ LEVELS : contains
    LEVELS ||--o{ LEVEL_PREREQUISITES : depends_on
    LEVELS ||--o{ LESSONS : contains

    LESSONS ||--o{ LESSON_EXERCISES : contains
    EXERCISES ||--o{ LESSON_EXERCISES : assigned_to
    EXERCISES ||--o{ EXERCISE_OPTIONS : has
    EXERCISES ||--o{ EXERCISE_MATCH_PAIRS : has
    EXERCISES ||--o{ EXERCISE_ACCEPTED_ANSWERS : accepts

    COURSE_ENROLLMENTS ||--o{ LEARNER_LEVEL_PROGRESS : tracks
    COURSE_ENROLLMENTS ||--o{ LEARNER_LESSON_PROGRESS : tracks
    COURSE_ENROLLMENTS ||--o{ LESSON_ATTEMPTS : starts

    LESSON_ATTEMPTS ||--o{ EXERCISE_ATTEMPTS : contains
    LESSON_ATTEMPTS ||--o| XP_EVENTS : awards
    EXERCISE_ATTEMPTS ||--o| HEART_EVENTS : causes

    ACHIEVEMENTS ||--o{ LEARNER_ACHIEVEMENTS : awarded_as
