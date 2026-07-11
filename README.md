# Duolingo Clone

A full-stack language-learning app inspired by Duolingo. The backend is a FastAPI service that manages lessons, progress, hearts, streaks, and gamification. The frontend is a Next.js app that renders the learning path, lesson flow, leaderboard, and related learner views.

## Features

- Interactive learning path with sections, units, and lessons
- Lesson player with multiple exercise types
- XP, hearts, streaks, and achievement tracking
- Leaderboard and learner progress views
- Seeded demo content for quick local development
- Generated frontend API types from the backend OpenAPI schema

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite, Uvicorn
- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Tooling: OpenAPI, ESLint

## Project Structure

```text
backend/
    app/                # FastAPI app, models, services, evaluators, API routes
    API_DESIGN.md       # Endpoint and domain design reference
    tests/              # Backend contract tests
frontend/
    app/                # Next.js app router pages and components
    hooks/              # Client-side data and interaction hooks
    lib/                # API client and shared frontend utilities
    types/              # Generated API types
```

## Prerequisites

- Python 3.12+ with the backend virtual environment already created, or a compatible local Python setup
- Node.js 18+ and npm

## Run The Backend

```bash
cd backend
.venv\Scripts\python.exe -m app.seed
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

The backend is available at:

- `http://localhost:8000`
- `http://localhost:8000/docs`
- `http://localhost:8000/openapi.json`

Useful API endpoints:

- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`

## Run The Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the API base URL in `frontend/.env`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

If you need to allow a different frontend origin in development or deployment, set `CORS_ORIGINS` for the backend, for example:

```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,https://duolingo-clone-navy.vercel.app
```

## Generate API Types

Start the backend first, then run:

```bash
cd frontend
npm run generate:api
```

This regenerates `frontend/types/api.generated.ts` from the backend OpenAPI spec.

## Testing

The backend includes contract-level tests under `backend/tests/`.

```bash
cd backend
.venv\Scripts\python.exe -m unittest
```

## API Design

See [backend/API_DESIGN.md](backend/API_DESIGN.md) for the backend contract, lesson lifecycle, progression rules, error format, idempotency, and page-to-endpoint mapping.

## Notes

- The backend seeds demo data automatically when no learner data exists.
- The frontend redirects `/` to `/learn`.
- If you run the frontend against a deployed backend, set `NEXT_PUBLIC_API_BASE_URL` accordingly before starting the app.
