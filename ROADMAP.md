# AdaptLearn — Build Roadmap

**Goal:** Build the full MVP in a controlled order so every layer is verified before the next layer depends on it.

This roadmap is written for a coding agent. Do not jump directly to styling before the backend and data contracts work.

---

# 0. Build Strategy

Use the following order:

```text
Repository
→ Databases
→ Backend foundation
→ Auth
→ Curriculum graph
→ User progress
→ Learning path
→ BKT
→ Quiz generation
→ Quiz submission
→ Dashboard APIs
→ Frontend auth
→ Onboarding
→ Dashboard
→ Quiz UI
→ Graph UI
→ Testing
→ Deployment readiness
```

Every phase has an exit gate. Do not proceed with broken dependencies.

---

# Phase 1 — Repository & Local Infrastructure

## Tasks

- [ ] Create repository structure from `ARCHITECTURE.md`.
- [ ] Add `.gitignore` for Python, Node, `.env`, caches, build folders.
- [ ] Create `docker-compose.yml`.
- [ ] Configure PostgreSQL 15.
- [ ] Configure Neo4j 5.
- [ ] Add persistent volumes.
- [ ] Add backend and frontend `.env.example`.
- [ ] Create initial `README.md` with local startup commands.

## Exit gate

- [ ] `docker compose up -d` succeeds.
- [ ] PostgreSQL accepts connection on 5432.
- [ ] Neo4j browser loads on 7474.
- [ ] Neo4j Bolt works on 7687.

---

# Phase 2 — FastAPI Foundation

## Tasks

- [ ] Create FastAPI app.
- [ ] Configure CORS.
- [ ] Add `/` route.
- [ ] Add `/api/health` route.
- [ ] Configure settings/environment loader.
- [ ] Create PostgreSQL engine and `get_db()` dependency.
- [ ] Create Neo4j driver wrapper.
- [ ] Register routers.
- [ ] Add consistent error handling.

## Exit gate

- [ ] `uvicorn main:app --reload --port 8000` works.
- [ ] `GET /` returns API-running message.
- [ ] `GET /api/health` confirms API + database connectivity.
- [ ] Swagger opens at `/docs`.

---

# Phase 3 — PostgreSQL Models

## Tasks

Create:

- [ ] `users`
- [ ] `topic_progress`
- [ ] `quiz_attempts`
- [ ] `quiz_sessions`

Add:

- [ ] unique email,
- [ ] unique `(user_id, topic_id)`,
- [ ] required indexes,
- [ ] timestamps,
- [ ] appropriate foreign keys.

For MVP, either:

- use `Base.metadata.create_all()` for initial setup, or
- add Alembic if convenient.

Document the choice in README.

## Exit gate

- [ ] tables are created from a clean database,
- [ ] backend can insert/read a test user in development,
- [ ] no plain-text passwords are ever stored.

---

# Phase 4 — Authentication

## Backend tasks

- [ ] bcrypt hashing utility,
- [ ] JWT creation,
- [ ] JWT decode/verification,
- [ ] `get_current_user`,
- [ ] register endpoint,
- [ ] login endpoint,
- [ ] `/auth/me` endpoint.

## Tests

- [ ] register works,
- [ ] duplicate email rejected,
- [ ] password verifies,
- [ ] wrong password rejected,
- [ ] invalid token rejected,
- [ ] expired token rejected.

## Exit gate

Using Swagger or an API client:

```text
register → token → /auth/me
login → token → /auth/me
```

must both work.

---

# Phase 5 — Neo4j Curriculum Seed

## Tasks

- [ ] Create all 30 topic definitions.
- [ ] Add descriptions.
- [ ] Add difficulty 1–4.
- [ ] Add Web Development domain.
- [ ] Add resource links.
- [ ] Add prerequisite edges from `ARCHITECTURE.md`.
- [ ] Use `MERGE` for idempotent startup seed.
- [ ] Add Neo4j indexes on `Topic.id` and `Topic.domain`.

## Exit gate

- [ ] Neo4j contains exactly 30 Web Development topic nodes after repeat startup.
- [ ] repeated startup does not duplicate nodes or edges.
- [ ] graph query returns correct prerequisite direction.

---

# Phase 6 — Topics APIs

Implement:

- [ ] `GET /api/topics/all`
- [ ] `GET /api/topics/graph`

## Exit gate

- [ ] all endpoint returns 30 topics,
- [ ] graph endpoint returns nodes + links,
- [ ] response schemas match `ARCHITECTURE.md`.

---

# Phase 7 — Onboarding & User Progress Initialization

## Tasks

- [ ] create progress rows for all domain topics,
- [ ] `POST /api/topics/mark-known`,
- [ ] validate topic IDs,
- [ ] mark selected known topics completed,
- [ ] set known topic `p_know = 0.95`,
- [ ] calculate unlocked frontier,
- [ ] leave non-eligible topics locked.

## Tests

- [ ] no-known-topics case,
- [ ] some-known-topics case,
- [ ] all-known-topics case,
- [ ] invalid topic ID rejected.

## Exit gate

A user with different onboarding selections must get a different starting frontier.

---

# Phase 8 — Learning Path Service

## Tasks

- [ ] query completed topic IDs from PostgreSQL,
- [ ] query Neo4j frontier,
- [ ] return max 3 learnable topics,
- [ ] order by difficulty then name,
- [ ] sync newly unlocked statuses.

Endpoint:

- [ ] `GET /api/topics/learning-path`

## Tests

- [ ] topic with unmet prerequisite excluded,
- [ ] topic with all prerequisites completed included,
- [ ] completed topic excluded,
- [ ] maximum 3 returned.

## Exit gate

Learning path is stable and deterministic for the same user state.

---

# Phase 9 — BKT Service

## Tasks

- [ ] implement correct-answer Bayesian update,
- [ ] implement wrong-answer Bayesian update,
- [ ] apply learning transition,
- [ ] clamp 0..1,
- [ ] implement mastery threshold,
- [ ] unit tests with known numerical examples.

Defaults:

```text
p_know=0.10
p_learn=0.40
p_guess=0.20
p_slip=0.10
```

## Exit gate

- [ ] all BKT unit tests pass,
- [ ] function is independent of database code.

---

# Phase 10 — Groq Quiz Generation

## Tasks

- [ ] create Groq client,
- [ ] configurable model via env,
- [ ] strict JSON system prompt,
- [ ] Pydantic quiz schema,
- [ ] business validation,
- [ ] retry invalid output,
- [ ] fallback question bank,
- [ ] request timeout,
- [ ] create quiz session with answer key,
- [ ] sanitize browser response.

Endpoint:

- [ ] `GET /api/quiz/generate/{topic_id}`

## Exit gate

Browser/API response contains:

- quiz ID,
- 3 questions,
- 4 options each,

and **does not contain the correct answers**.

Test Groq-unavailable case as well.

---

# Phase 11 — Quiz Submission & Progress Update

## Tasks

- [ ] create submit schema,
- [ ] validate ownership,
- [ ] validate expiry,
- [ ] validate one-time submission,
- [ ] score answers server-side,
- [ ] run BKT sequentially,
- [ ] increment counts,
- [ ] save quiz attempt,
- [ ] mark status completed on score >=2,
- [ ] recalculate frontier,
- [ ] compute `needs_attention`,
- [ ] return feedback + resources + next topics.

Endpoint:

- [ ] `POST /api/quiz/submit`

## Exit gate

A real quiz submission changes persisted progress and recommendations.

---

# Phase 12 — Dashboard API

Implement:

- [ ] `GET /api/progress/dashboard`
- [ ] `GET /api/progress/all`

Dashboard response must include:

- [ ] total topics,
- [ ] completed,
- [ ] mastered,
- [ ] average mastery,
- [ ] total attempts,
- [ ] next topics,
- [ ] needs attention,
- [ ] recent attempts,
- [ ] mastery list.

## Exit gate

Swagger response contains real data for a user who has taken quizzes.

---

# Phase 13 — React Foundation

## Tasks

- [ ] initialize React 18 + Vite,
- [ ] Tailwind CSS,
- [ ] React Router,
- [ ] Axios client,
- [ ] AuthContext/useAuth,
- [ ] request JWT interceptor,
- [ ] 401 response handling,
- [ ] AppShell/Navbar,
- [ ] reusable loaders/errors/cards/buttons.

## Exit gate

- [ ] app boots,
- [ ] routes render,
- [ ] protected routes redirect correctly.

---

# Phase 14 — Login & Register UI

Build exactly according to `UI.md`.

## Exit gate

- [ ] register from browser works,
- [ ] login from browser works,
- [ ] auth persists across refresh,
- [ ] logout works.

---

# Phase 15 — Onboarding UI

## Tasks

- [ ] domain header,
- [ ] known-topic selectable grid,
- [ ] selected counter,
- [ ] submit onboarding,
- [ ] loading state,
- [ ] error state,
- [ ] redirect dashboard.

## Exit gate

Frontend onboarding changes actual backend learning path.

---

# Phase 16 — Dashboard UI

Build:

- [ ] greeting,
- [ ] stat cards,
- [ ] recommended topics,
- [ ] attention section,
- [ ] recent attempts,
- [ ] mastery bars,
- [ ] empty curriculum-complete state.

## Exit gate

Dashboard has no hard-coded fake numbers.

---

# Phase 17 — Quiz UI

Build:

- [ ] quiz generation loader,
- [ ] 3-question progress indicator,
- [ ] one question at a time,
- [ ] option selection,
- [ ] previous/next navigation,
- [ ] submit confirmation,
- [ ] result state,
- [ ] retry/error handling,
- [ ] resource recommendations.

## Exit gate

Entire quiz can be completed from browser without opening Swagger.

---

# Phase 18 — Knowledge Graph UI

## Tasks

- [ ] install `react-force-graph-2d`,
- [ ] fetch graph data,
- [ ] status colors,
- [ ] directional arrows,
- [ ] labels,
- [ ] zoom/pan,
- [ ] node click side panel,
- [ ] lock-aware action button,
- [ ] graph legend.

## Exit gate

The graph clearly distinguishes locked/unlocked/in-progress/completed states and opens topic detail panel.

---

# Phase 19 — Error, Loading & Edge Cases

Explicitly test:

- [ ] empty new user,
- [ ] user marks zero known topics,
- [ ] user marks all topics known,
- [ ] no recommendations remain,
- [ ] Groq timeout,
- [ ] malformed LLM JSON,
- [ ] PostgreSQL temporary failure,
- [ ] Neo4j temporary failure,
- [ ] expired JWT,
- [ ] locked topic direct URL,
- [ ] expired quiz session,
- [ ] double quiz submission,
- [ ] network disconnect during submit.

---

# Phase 20 — Testing & Cleanup

## Backend

Run complete tests.

- [ ] auth
- [ ] BKT
- [ ] learning path
- [ ] quiz security
- [ ] quiz persistence
- [ ] confusion detection

## Frontend/manual

- [ ] 360px mobile width
- [ ] tablet
- [ ] desktop
- [ ] keyboard navigation
- [ ] visible focus states
- [ ] no console errors
- [ ] no failed requests during normal flow

## Code cleanup

- [ ] remove debug logs,
- [ ] remove unused imports,
- [ ] remove dead routes,
- [ ] remove test credentials,
- [ ] no committed `.env`,
- [ ] no placeholder lorem ipsum.

---

# Phase 21 — Deployment Readiness

## Production services

- [ ] Neo4j Aura database,
- [ ] Neon PostgreSQL,
- [ ] Railway backend,
- [ ] Vercel frontend,
- [ ] Groq API key.

## Tasks

- [ ] configure production env variables,
- [ ] update CORS,
- [ ] verify HTTPS,
- [ ] verify database seed,
- [ ] verify login,
- [ ] verify one full quiz flow,
- [ ] verify graph page,
- [ ] verify frontend refresh on nested routes.

---

# Final Demo Script

Use this exact flow to confirm project readiness:

1. Open landing/login screen.
2. Register a new account.
3. Complete onboarding and mark a few known topics.
4. Show personalized dashboard.
5. Explain why locked topics are not recommended.
6. Start an unlocked topic.
7. Show AI quiz loading state.
8. Answer and submit the 3 questions.
9. Show BKT mastery change.
10. Show pass/fail and resources.
11. Return to dashboard and show updated recommendation.
12. Open Knowledge Graph.
13. Show status colors and prerequisite arrows.
14. Click a node and show topic detail panel.
15. Logout and verify protected-route redirect.

---

# Final Handoff Checklist for Claude

Before declaring the implementation finished, return a concise summary containing:

- files created,
- commands to run locally,
- required environment variables,
- database setup notes,
- test results,
- known limitations,
- deployment steps.

Do not claim completion if any core journey is still mocked or broken.
