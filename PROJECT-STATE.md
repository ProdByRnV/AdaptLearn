# AdaptLearn - Project State

**Last updated:** 2026-10-05
**Current phase:** Phase 10 complete - Phase 11 (Quiz Submission & Progress Update) up next
**Repository:** https://github.com/ProdByRnV/AdaptLearn

---

## Phase progress

Phases follow [ROADMAP.md](ROADMAP.md). A phase is only ticked once its exit gate has been verified.

| # | Phase | Status | Commit |
|---|---|---|---|
| 1 | Repository & Local Infrastructure | Done | `accb6cd` |
| 2 | FastAPI Foundation | Done | `12a9d53` |
| 3 | PostgreSQL Models | Done | `05cae53` |
| 4 | Authentication | Done | `e786514` |
| 5 | Neo4j Curriculum Seed | Done | `a314e72` |
| 6 | Topics APIs | Done | `242a2f0` |
| 7 | Onboarding & User Progress Initialization | Done | `d6df728` |
| 8 | Learning Path Service | Done | `2bb7850` |
| 9 | BKT Service | Done | `0f2e2fb` |
| 10 | Groq Quiz Generation | Done | latest |
| 11 | Quiz Submission & Progress Update | Next | - |
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
| Neo4j 5.26 Community | Running in Docker on `7474` / `7687`, healthy. Holds the Web Development curriculum: 30 topics, 37 prerequisite edges, seeded on every backend startup |
| Backend | FastAPI app on `8000`: settings, PostgreSQL + Neo4j connections, CORS, consistent errors, JWT auth. Routes: `GET /`, `GET /api/health`, `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`, `GET /api/topics/all`, `GET /api/topics/graph`, `GET /api/topics/learning-path`, `POST /api/topics/mark-known`, `GET /api/quiz/generate/{topic_id}`, Swagger at `/docs` |
| Backend venv | `backend/venv` (Python 3.13.5) with `requirements.txt` installed |
| Backend config | `backend/.env` created locally from `.env.example` with a generated `JWT_SECRET_KEY` (git-ignored) |
| Database tables | `users`, `topic_progress`, `quiz_attempts`, `quiz_sessions` - created automatically on backend startup (`create_all`), currently empty |
| Groq | API key set in `backend/.env`; model `openai/gpt-oss-120b` (reasoning effort low). Live quizzes generate in ~1.7-2.0s; without Groq the curated fallback bank is used |
| Frontend | Not started - the UI is being built last |
| Tests | 298 passing (`pytest` from `backend/`): 33 auth, 21 curriculum data/validator, 8 Neo4j seeder (isolated `pytest-seed` domain), 21 topics API, 28 onboarding/frontier, 17 learning path, 87 BKT, 83 quiz generation (mostly parametrized). Tests never call the real Groq API. PostgreSQL tests use the separate `adaptlearn_test` database |

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
6. **Groq model:** `GROQ_MODEL` defaults to `openai/gpt-oss-120b` with `GROQ_REASONING_EFFORT=low`. The spec's `llama3-8b-8192` and the originally agreed `llama-3.1-8b-instant` have both been retired by Groq; gpt-oss-120b was chosen in Phase 10 after comparing it with gpt-oss-20b and qwen3.8-27b on real quiz prompts.
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
| `GROQ_MODEL=llama3-8b-8192` | `openai/gpt-oss-120b` + `GROQ_REASONING_EFFORT=low` | Llama chat models are no longer offered by Groq; gpt-oss-120b gave the most precise questions at ~1-2s (vs gpt-oss-20b 0.9s but vaguer, qwen3.8-27b 1.2s) |
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
| `OAuth2PasswordBearer` | `HTTPBearer` | Same `Authorization: Bearer` header for the frontend, but Swagger's Authorize box accepts a pasted token. `OAuth2PasswordBearer`'s Swagger flow posts form data, which doesn't match the JSON login contract |
| Password: "required" | 8 characters minimum, 72 bytes maximum | Sensible minimum; 72 bytes is bcrypt's hard limit |
| - | Unknown-email logins run a dummy bcrypt check | Same response time whether or not an account exists, so emails can't be probed |
| - | Tests use a separate `adaptlearn_test` database | Dev data is never touched by test runs |
| Index on `Topic.id` | Unique constraint `topic_id_unique` (backed by a range index) | Same lookup speed, plus the database rejects duplicate topic ids |
| Seed with `MERGE` | `MERGE` + pruning of topics/edges no longer in `curriculum.py` (domain-scoped, one transaction) | Graph always mirrors the file exactly; editing the curriculum never leaves stale nodes |
| Topic descriptions/resources unspecified | Written for all 30 topics; 81 resources (MDN, web.dev, javascript.info, react.dev, official docs, 10 videos), every URL verified live, videos verified via YouTube oEmbed | PRD requires 1-3 curated resources per topic |
| - | `python -m seed.seed_graph` manual seed command | Seeding managed databases (Aura) without starting the API |
| Topics endpoints' auth unspecified | Both `/topics/all` and `/topics/graph` require a Bearer token | Only signed-in pages use them; keeps every non-auth endpoint protected |
| Graph node fields (ARCHITECTURE 13.7) | Adds `mastered` and `prerequisites`; both responses also carry `domain` | The UI needs the mastered style and the prerequisite list for the detail panel without re-deriving them |
| Graph query (ARCHITECTURE 9.2) | One query returns each topic with its prerequisite ids; links are built from it | One round trip serves both endpoints and the upcoming learning-path logic |
| Status before progress rows exist | Derived from the graph (roots `unlocked`, rest `locked`, mastery 10%) | Graph is correct even before onboarding; stored rows always win once they exist |
| Unknown topic ids "rejected" (status unspecified) | `400 Unknown topic ids: ...`, checked before any write | PRD lists 400 for business-rule errors; all-or-nothing keeps progress consistent |
| `mark-known` response `{message, known_count, recommended}` | Adds `added_prerequisites`; `known_count` includes implied prerequisites | Lets onboarding UI say which earlier topics were filled in automatically |
| Recommended item fields (ARCHITECTURE 13.6) | Adds `description` and `prerequisite_names` | Dashboard cards need the short description and a readable prerequisite summary (PRD section 9) |
| Two frontier queries (decision 1) | One full-frontier query (spec 9.3 without `LIMIT`); recommendations are its first 3 | Same result as a separate `LIMIT 3` query with one round trip |
| Onboarding re-submission unspecified | Additive and idempotent: never relocks, never lowers mastery, keeps `in_progress` | Safe against double submits and returning to onboarding |
| Learning-path response `{recommended}` (ARCHITECTURE 13.6) | Adds `domain`, `onboarded` and `curriculum_complete` | Frontend can route un-onboarded users to onboarding and show the curriculum-complete state (PRD section 10) without extra calls |
| Learning path before onboarding unspecified | Returns the starting topics and writes nothing | A GET shouldn't create data; rows are created by onboarding |
| - | Status sync recreates a missing row for a learnable topic | Self-heals if a topic is added to `curriculum.py` after a user onboarded |
| BKT constants location unspecified | `DEFAULT_P_*` and `MASTERY_THRESHOLD` live in `services/bkt.py`; models and services import them from there | One source for the algorithm, column defaults and DB server defaults, and `bkt.py` stays free of database imports (exit gate) |
| `update_bkt()` + `mastery_reached()` (ARCHITECTURE 11) | Also `update_bkt_sequence()` returning p_know after each answer | Phase 11 applies the 3 answers in order; the per-answer trail is useful for the result screen |
| Quiz generate response (ARCHITECTURE 13.8) | Adds `source` (`ai` / `fallback`) | The UI can tell learners when they're seeing the practice question bank instead of fresh AI questions (PRD 20: 503 fallback message) |
| Options in generated order | Options shuffled per quiz, answer index remapped (AI and fallback) | Removes LLM answer-position bias; fallback questions don't always have the same answer slot |
| Max 2 retries, ~10s timeout | Same, plus a 12s total budget; network/auth/rate-limit/5xx errors skip retries and use the fallback; Groq `400 json_validate_failed` counts as invalid output and is retried | Learner always gets a quiz inside the 15s browser timeout; retrying an unreachable service only adds waiting |
| Quiz before onboarding unspecified | Progress rows are created as if onboarding with nothing known | Phase 11 always has a row to update |
| Input handling unspecified | Probabilities outside 0..1 (and NaN) raise `ValueError`; a zero denominator (only possible at the extremes) leaves the belief unchanged before the learning step | Bad inputs fail loudly instead of producing silent nonsense; no division by zero |

---

## Open items

- **Frontend React version:** recommended UI uses shadcn/ui, which targets React 19 + Tailwind v4, while the spec says React 18. Decide before Phase 13 (recommendation: React 19).
- **BKT calibration (built as specified; now confirmed by tests):** with the PRD's fixed values, `p_know` can't fall below 0.40 after any answer and repeated wrong answers level off at 16/35 ≈ 0.457; the same 2/3 score ends at 0.76 or 0.98 depending on which answer was wrong; one 3/3 quiz takes a new topic to 0.989 (mastered). Knock-on for Phase 11: the confusion rule (`attempts > 2 and p_know < 0.50`) can only fire while a learner keeps getting most answers wrong, because almost any recent correct answer lifts `p_know` above 0.5. Revisit only if it feels wrong in testing.
- **Groq model churn:** Groq has retired two Llama models during this project. If `openai/gpt-oss-120b` is retired, quizzes keep working via the fallback bank (logged as HTTP 4xx); switch `GROQ_MODEL` in `.env` - no code change needed.
- **Fallback bank repeats:** it has exactly 3 questions per topic, so a learner who retakes a topic while Groq is down sees the same questions (options are reshuffled). Adding more questions per topic and sampling 3 would fix this.
- **Expired quiz sessions accumulate:** `quiz_sessions` rows are never deleted. Harmless at MVP scale; a periodic cleanup of expired, unsubmitted sessions would keep the table small.
- **Rate limiting:** login/register have no rate limit yet. Recommended by the PRD before public deployment (Phase 21).
- **No migrations:** schema changes need the dev reset above. Move to Alembic before any deployment holds real user data.
- **Recommendation ranking (built as specified, worth revisiting):** the spec ranks the frontier by difficulty then name, so easy side topics always come first. In the live check, a learner who marked React Hooks as known was recommended Git Basics, Semantic HTML and Arrays & Objects ahead of React Router, the same top 3 as a learner who only knew HTML/CSS/JS. A track-aware ranking (e.g. prefer topics that unlock what the learner just finished) could be a later enhancement.
- **Resource links can rot:** all 81 URLs were live on 2026-10-04. Re-check them before deployment (Phase 21).
- **Dev auto-reload under the assistant:** `uvicorn --reload` hangs on Windows when started without a console (the reloader can't deliver Ctrl+C to the worker). Doesn't affect running it in a normal terminal; the assistant restarts the server manually instead.

---

## Next step

**Phase 11 - Quiz Submission & Progress Update:** `POST /api/quiz/submit` - verify the session belongs to the user, is not expired and was not already submitted; score the 3 answers server-side; run BKT sequentially; increment `attempts`/`correct`; save a `quiz_attempts` row; mark the topic `completed` on 2/3 or better; recalculate the frontier; set or clear `needs_attention`; return feedback with explanations, resources and next topics.

Exit gate: a real quiz submission changes persisted progress and recommendations.
