# AdaptLearn - Project State

**Last updated:** 2026-10-04
**Current phase:** Phase 2 complete - Phase 3 (PostgreSQL Models) up next
**Repository:** https://github.com/ProdByRnV/AdaptLearn

---

## Phase progress

Phases follow [ROADMAP.md](ROADMAP.md). A phase is only ticked once its exit gate has been verified.

| # | Phase | Status | Commit |
|---|---|---|---|
| 1 | Repository & Local Infrastructure | Done | `accb6cd` |
| 2 | FastAPI Foundation | Done | latest |
| 3 | PostgreSQL Models | Next | - |
| 4 | Authentication | Pending | - |
| 5 | Neo4j Curriculum Seed | Pending | - |
| 6 | Topics APIs | Pending | - |
| 7 | Onboarding & User Progress Initialization | Pending | - |
| 8 | Learning Path Service | Pending | - |
| 9 | BKT Service | Pending | - |
| 10 | Groq Quiz Generation | Pending | - |
| 11 | Quiz Submission & Progress Update | Pending | - |
| 12 | Dashboard API | Pending | - |
| 13 | React Foundation | Pending | - |
| 14 | Login & Register UI | Pending | - |
| 15 | Onboarding UI | Pending | - |
| 16 | Dashboard UI | Pending | - |
| 17 | Quiz UI | Pending | - |
| 18 | Knowledge Graph UI | Pending | - |
| 19 | Error, Loading & Edge Cases | Pending | - |
| 20 | Testing & Cleanup | Pending | - |
| 21 | Deployment Readiness | Pending | - |

---

## What exists right now

| Component | State |
|---|---|
| PostgreSQL 15 | Running in Docker on `5432`, database `adaptlearn`, healthy |
| Neo4j 5.26 Community | Running in Docker on `7474` / `7687`, healthy, empty (no curriculum yet) |
| Backend | FastAPI app runs on `8000`: settings loader, PostgreSQL engine + `get_db()`, Neo4j driver wrapper, CORS, consistent error handling. Routes: `GET /`, `GET /api/health`, Swagger at `/docs` |
| Backend venv | `backend/venv` (Python 3.13.5) with `requirements.txt` installed |
| Backend config | `backend/.env` created locally from `.env.example` with a generated `JWT_SECRET_KEY` (git-ignored) |
| Database tables | None yet - created in Phase 3 |
| Groq | No API key set yet - not needed until Phase 10 (fallback bank covers it) |
| Frontend | Not started - the UI is being built last |
| Tests | None yet |

### Start the local environment

```bash
docker compose up -d     # from the project root
docker compose ps        # both services should show "healthy"

cd backend
venv\Scripts\activate    # Windows (macOS/Linux: source venv/bin/activate)
uvicorn main:app --reload --port 8000
# then open http://127.0.0.1:8000/api/health
```

---

## Agreed decisions

These resolve gaps found while reviewing the spec. They apply to all later phases.

1. **Frontier queries:** two Neo4j queries - the full learnable frontier (used to unlock topics) and a `LIMIT 3` version for recommendations.
2. **`in_progress` status:** set when a quiz is first generated for an `unlocked` topic; a failed submission keeps it `in_progress`.
3. **Known-topic consistency:** marking a topic known during onboarding also completes all of its prerequisites.
4. **Onboarding complete:** inferred from the user having any `topic_progress` rows - no schema change.
5. **Mastery units:** stored and computed as `0..1`; API fields named `mastery` are percentages.
6. **Groq model:** `GROQ_MODEL` defaults to `llama-3.1-8b-instant` (the spec's `llama3-8b-8192` is retired).
7. **Password hashing:** use the `bcrypt` library directly, not `passlib` (unmaintained, breaks on recent `bcrypt` and Python 3.13).

### Working conventions

- All Python runs inside `backend/venv`; nothing is installed into the system Python.
- Each completed phase is committed and pushed with a detailed write-up in the commit message.
- `.env` files are created locally when needed and never committed.

---

## Deviations from the spec

| Spec says | Actual | Why |
|---|---|---|
| Neo4j `5` | Neo4j `5.26-community` (pinned) | Same version in every environment |
| `GROQ_MODEL=llama3-8b-8192` | `llama-3.1-8b-instant` | Original model retired on Groq |
| `frontend/.env.example` in Phase 1 | Deferred to frontend phase | UI is being built last |
| `UI.md` required | Not present - ignored for now | UI design to be decided at the frontend stage |
| `localhost` in local DB URLs | `127.0.0.1` | On Windows, `localhost` also tries IPv6, doubling outage detection time |
| Health route not specified in file layout | Added `routers/health.py` + `schemas/health.py` | Keeps `main.py` thin; spec allows small helper files |
| Error handling location unspecified | Added `errors.py` | One place for the `{"detail": ...}` contract |

---

## Open items

- **Frontend React version:** recommended UI uses shadcn/ui, which targets React 19 + Tailwind v4, while the spec says React 18. Decide before Phase 13 (recommendation: React 19).
- **BKT calibration (no action planned):** with the spec's fixed values, `p_know` can't fall below 0.40 after any answer, answer order strongly affects the result, and a single 3/3 quiz takes a new topic to ~0.99. Built as specified; revisit only if behaviour feels wrong in testing.
- **Groq API key:** needed by Phase 10 for live quiz generation.
- **Test client:** Starlette now warns that `TestClient` with `httpx` is deprecated in favour of `httpx2`. Pick the test HTTP client when test dependencies are added in Phase 4.

---

## Next step

**Phase 3 - PostgreSQL Models:** SQLAlchemy models for `users`, `topic_progress`, `quiz_attempts` and `quiz_sessions`, with the unique email and `(user_id, topic_id)` constraints, indexes, timestamps and foreign keys. Tables created on startup with `Base.metadata.create_all()` (choice to be documented in the README).

Exit gate: tables are created from a clean database, a test user can be inserted and read back, and no plain-text password is ever stored.
