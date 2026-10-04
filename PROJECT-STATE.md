# AdaptLearn - Project State

**Last updated:** 2026-10-04
**Current phase:** Phase 3 complete - Phase 4 (Authentication) up next
**Repository:** https://github.com/ProdByRnV/AdaptLearn

---

## Phase progress

Phases follow [ROADMAP.md](ROADMAP.md). A phase is only ticked once its exit gate has been verified.

| # | Phase | Status | Commit |
|---|---|---|---|
| 1 | Repository & Local Infrastructure | Done | `accb6cd` |
| 2 | FastAPI Foundation | Done | `12a9d53` |
| 3 | PostgreSQL Models | Done | latest |
| 4 | Authentication | Next | - |
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
| Database tables | `users`, `topic_progress`, `quiz_attempts`, `quiz_sessions` - created automatically on backend startup (`create_all`), currently empty |
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

Reset the PostgreSQL schema after model changes (dev only - deletes all data), then restart the backend:

```bash
docker exec adaptlearn-postgres psql -U postgres -d adaptlearn -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
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
| `users.email` unique (case-sensitive) | Email trimmed + lowercased by the model before saving | `Puja@x.com` and `puja@x.com` must be one account |
| Plain columns in `topic_progress` / `quiz_attempts` | Added CHECK constraints (status values, probabilities in 0..1, non-negative counters/score) and `ON DELETE CASCADE` FKs | The database itself rejects impossible state |
| No index on `quiz_sessions.user_id` | Added | Supports per-user session lookups/cleanup |
| `(user_id, topic_id)` index listed separately | Covered by the unique constraint's index | A second identical index would only slow writes |
| `created_at` columns nullable | `NOT NULL` with `DEFAULT now()` | Every row always has a timestamp |

---

## Open items

- **Frontend React version:** recommended UI uses shadcn/ui, which targets React 19 + Tailwind v4, while the spec says React 18. Decide before Phase 13 (recommendation: React 19).
- **BKT calibration (no action planned):** with the spec's fixed values, `p_know` can't fall below 0.40 after any answer, answer order strongly affects the result, and a single 3/3 quiz takes a new topic to ~0.99. Built as specified; revisit only if behaviour feels wrong in testing.
- **Groq API key:** needed by Phase 10 for live quiz generation.
- **Test client:** Starlette now warns that `TestClient` with `httpx` is deprecated in favour of `httpx2`. Pick the test HTTP client when test dependencies are added in Phase 4.
- **bcrypt 72-byte limit:** `bcrypt` 5.x raises an error for passwords longer than 72 bytes instead of silently truncating. Phase 4 registration must validate password length so this becomes a clean 422, not a 500.
- **No migrations:** schema changes need the dev reset above. Move to Alembic before any deployment holds real user data.
- **Dev auto-reload under the assistant:** `uvicorn --reload` hangs on Windows when started without a console (the reloader can't deliver Ctrl+C to the worker). Doesn't affect running it in a normal terminal; the assistant restarts the server manually instead.

---

## Next step

**Phase 4 - Authentication:** bcrypt hashing utility, JWT creation and verification, `get_current_user` dependency, `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`, plus the first pytest suite (register, duplicate email, password verify, wrong password, invalid token, expired token).

Exit gate: in Swagger, register -> token -> `/auth/me` and login -> token -> `/auth/me` both work.
