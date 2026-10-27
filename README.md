# AdaptLearn

An adaptive learning platform that builds a personalised learning path instead of pushing every learner through the same fixed sequence.

- **Neo4j knowledge graph** - topics and their prerequisites decide what a learner can study next.
- **Bayesian Knowledge Tracing (BKT)** - a per-user, per-topic mastery probability updated after every quiz answer.
- **Groq LLM** - generates fresh 3-question multiple-choice quizzes, with a curated fallback bank.
- **PostgreSQL** - users, progress, quiz sessions and attempt history.
- **React** - dashboard, quizzes and an interactive knowledge graph (in progress: the app foundation is built; the screens follow).

The first fully seeded domain is **Web Development** (30 topics).

See [PROJECT-STATE.md](PROJECT-STATE.md) for current progress. The specification documents (PRD, architecture and roadmap) are kept privately and are not part of this repository.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite + Tailwind CSS v4 + shadcn/ui (Radix), React Router, Axios |
| Backend | FastAPI (Python) |
| Relational DB | PostgreSQL 15 + SQLAlchemy |
| Graph DB | Neo4j 5 |
| AI | Groq API |
| Auth | JWT + bcrypt |

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with Docker Compose v2)
- Python 3.11+
- Node.js 20+ (for the frontend)

## Local development

### 1. Start the databases

From the project root:

```bash
docker compose up -d
```

This starts:

| Service | URL / port | Default credentials |
|---|---|---|
| PostgreSQL 15 | `localhost:5432`, database `adaptlearn` | `postgres` / `postgres` |
| Neo4j Browser | http://localhost:7474 | `neo4j` / `password123` |
| Neo4j Bolt | `bolt://localhost:7687` | `neo4j` / `password123` |

Data is kept in named Docker volumes (`postgres_data`, `neo4j_data`, `neo4j_logs`), so it survives restarts.

Check that both containers are healthy:

```bash
docker compose ps
```

The default credentials are for local development only. To override them, create a `.env` file in the project root with `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `NEO4J_USER` and/or `NEO4J_PASSWORD`, and update `backend/.env` to match.

Useful commands:

```bash
docker compose stop        # stop containers, keep data
docker compose down        # remove containers, keep data
docker compose down -v     # remove containers AND wipe all data
```

### 2. Set up the backend environment

All Python code runs inside a virtual environment named `venv` in the `backend` folder, so nothing is installed into your system Python.

```bash
cd backend
python -m venv venv          # Windows without python on PATH: py -3 -m venv venv

# Activate it
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
cp .env.example .env
```

Then edit `backend/.env`:

- set `JWT_SECRET_KEY` to a random value, e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"` (run inside the activated venv)
- optionally set `GROQ_API_KEY`; without it, quizzes come from the fallback question bank

The local database hosts default to `127.0.0.1` rather than `localhost`. On Windows, `localhost` also tries IPv6 first, which doubles the time it takes to notice a stopped database.

### 3. Run the backend

With the venv activated, from `backend/`:

```bash
uvicorn main:app --reload --port 8000
```

| URL | What it shows |
|---|---|
| http://127.0.0.1:8000/ | API-running message |
| http://127.0.0.1:8000/api/health | API, PostgreSQL and Neo4j status (`200` when all are up, `503` if a database is down) |
| http://127.0.0.1:8000/docs | Swagger UI |

The API starts even if a database is down; the startup log and `/api/health` say which one is unreachable.

### 4. Run the frontend

From `frontend/`:

```bash
npm install
npm run dev
```

Then open http://localhost:5173. The app talks to the API at `VITE_API_URL` (default `http://127.0.0.1:8000/api`); copy `frontend/.env.example` to `frontend/.env` only if the API runs elsewhere. The backend's `FRONTEND_URL` must include the app's origin (`http://localhost:5173` by default) or the browser blocks the requests (CORS).

| Command (from `frontend/`) | What it does |
|---|---|
| `npm run dev` | Dev server with hot reload on port 5173 |
| `npm run build` | Production build into `frontend/dist` |
| `npm run preview` | Serve the production build locally |
| `npm test` | Run the frontend tests once (Vitest + Testing Library, no backend needed) |
| `npm run lint` | Lint with oxlint |

**Routes.** `/login` and `/register` are for signed-out visitors. `/`, `/onboarding`, `/dashboard`, `/quiz/:topicId` and `/graph` need a session; without one the learner goes to `/login`, and the page they wanted is remembered for after signing in (except after choosing to log out, so the next person on a shared computer starts fresh). Unknown paths show a 404 page, and a page that crashes shows an error screen instead of a blank page.

**Signing in.** The register form asks for a username, email, password and password confirmation (there is no password reset yet, so a typo would lock the account); the login form for email and password. Both check the backend's rules before sending (username up to 80 characters, a valid email, password 8 characters to 72 bytes), show each problem next to its field, and show server answers in plain language: "Incorrect email or password", "An account with this email already exists" on the email field, or "Can't reach the AdaptLearn server". After signing in the learner goes to the remembered page if there is one; otherwise to `/onboarding` until they have onboarded (always the case for a new account) and to `/dashboard` after that, decided by `onboarded` from `GET /api/topics/learning-path`.

**Onboarding** (`/onboarding`). Shows the domain and the PRD's explanation, then every topic from `GET /api/topics/graph`, grouped by difficulty (Beginner, Intermediate, Advanced, Expert). Ticking a topic also ticks everything it depends on, marked "Included: needed for ...", because the server marks prerequisites of known topics as known too; the live counter ("7 topics selected (5 included as prerequisites)") therefore matches what will be saved. Topics a returning learner has already completed are shown ticked. Saving sends only the explicit choices to `POST /api/topics/mark-known` and opens the dashboard with a confirmation; saving with nothing ticked starts from the beginning. Loading shows a skeleton, a failed load offers a retry, and a failed save keeps the selection.

**Dashboard** (`/dashboard`). Everything comes from one call, `GET /api/progress/dashboard`; nothing on the page is hard-coded. It shows: stat cards for overall progress, completed topics (and how many are in progress), mastered topics (95% or more), average mastery and quiz attempts (noting flagged ones that didn't count); **Up next**, the three recommended topics with difficulty, status, description, prerequisites ("Builds on ..."), mastery and one action (**Start topic** for an unlocked topic, **Continue** for one in progress, **Retry quiz** when the latest counted quiz on it failed or it needs attention); **Needs attention**, topics with more than 2 attempts and under 50% mastery, listing their resources before a retry; **Recent quizzes**, the last five with score, result, mastery before and after, and a "Flagged, didn't count" badge for attempts that failed the integrity check; and **Mastery**, a compact bar per reachable topic with locked topics behind a toggle. It also covers a learner who hasn't onboarded (a prompt to choose known topics), the curriculum-complete state, loading, and errors with a retry.

**Quiz** (`/quiz/:topicId`). The proctored quiz in the browser. The page first shows the topic and how the quiz works (a locked topic explains which prerequisites to finish; an unfinished quiz on another topic is flagged, since starting abandons it). **Prepare quiz** calls `GET /quiz/generate/{topic_id}` and shows the server's integrity rules, the time per question and a notice when the questions come from the curated fallback bank. **Enter fullscreen and start** serves one question at a time (`POST /quiz/{id}/next`) with the server's countdown; the learner picks an option and **locks it in** (`POST /quiz/{id}/answer`), which is possible after a 3-second reading time (faster answers are penalised). When time runs out, a selected answer is sent; otherwise the question times out and the page moves on. While the quiz runs, the navbar is hidden and the page sends a heartbeat every 5 s plus tab switches, window switches, leaving fullscreen, copy/cut/paste and right-click (all blocked) and a second screen (`screen.isExtended`) to `POST /quiz/{id}/events`; each recorded event is shown to the learner with its penalty, and leaving fullscreen offers a way back. The back button asks before leaving and a reload warns first; reopening the page resumes the quiz with its timer intact (`GET /quiz/active`). The result shows the score, pass or retry, mastery before and after, the integrity verdict with its reasons (a flagged attempt didn't count and changed nothing), newly unlocked topics, resources after a failed quiz, every answer with its explanation, and what to learn next. Code in AI questions is shown as code blocks. Errors are handled: 403 locked, 429 with a countdown from `Retry-After`, 503, expired (410) and already-submitted (409) quizzes, and network failures with a retry.

**Sessions.** The JWT is kept in `localStorage` and sent as `Authorization: Bearer ...` on every request. On load the app asks `/api/auth/me` who the token belongs to. If the server rejects the token (`401`), it is dropped and the learner sees "Your session has expired" on the login page; if the server can't be reached, the token is kept and the page offers a retry. Logging out (or in) in one tab applies to every open tab.

**Theme.** Colours come from the AdaptLearn design palette (slate ink, teal primary, and the topic status colours: completed teal-500, in progress amber-500, unlocked teal-200, locked slate-500), defined once as CSS variables in `frontend/src/index.css` and used through Tailwind classes such as `bg-primary`, `text-ink` and `bg-status-completed`. The light status colours are used as fills with dark text, never as text on white.

### Authentication

| Endpoint | Body | Returns |
|---|---|---|
| `POST /api/auth/register` | `{"username", "email", "password"}` | `201` with `{access_token, token_type, user}`; `409` if the email is taken |
| `POST /api/auth/login` | `{"email", "password"}` | `200` with the same shape; `401` for a wrong email or password |
| `GET /api/auth/me` | - (needs `Authorization: Bearer <token>`) | The current user; `401` if the token is missing, invalid or expired |

Rules:

- Emails are case-insensitive (stored lowercase).
- Passwords must be 8 characters to 72 bytes (bcrypt's limit) and are stored only as bcrypt hashes.
- Tokens are HS256 JWTs signed with `JWT_SECRET_KEY`, valid for `ACCESS_TOKEN_EXPIRE_MINUTES` (default 7 days).
- A failed login returns the same message whether or not the email exists.

**Trying it in Swagger:** call `register` or `login`, copy the `access_token` from the response, click **Authorize** (top right), paste the token, then call `/api/auth/me`.

### Topics

Both endpoints need a Bearer token and take an optional `?domain=` (default and only supported value: `web-development`; anything else is `404`).

| Endpoint | Returns |
|---|---|
| `GET /api/topics/all` | `{domain, topics}`: every topic with `id`, `name`, `description`, `difficulty` and `resources` (`[{title, url, type}]`), ordered by difficulty then name |
| `GET /api/topics/graph` | `{domain, nodes, links}` for the knowledge graph. Each node adds the current user's `status`, `mastery` (percentage), `mastered` (`p_know >= 0.95`) and `prerequisites` (ids). Each link is `{source, target}`, pointing from a prerequisite to the topic it unlocks |

#### Learning path: `GET /api/topics/learning-path`

Returns `{domain, onboarded, curriculum_complete, recommended}`. `recommended` holds at most 3 learnable topics: not completed, every prerequisite completed, ordered by difficulty then name. Topics already in progress are included with status `in_progress`.

- **Before onboarding** (no progress rows): `onboarded` is `false`, the starting topics are returned, and nothing is written. The frontend uses this to send the learner to onboarding.
- **After onboarding:** statuses are synced first, so any topic that has become learnable is stored as `unlocked`. A missing row for a learnable topic is recreated, and completed or in-progress topics are never changed.
- **Everything completed:** `curriculum_complete` is `true` and `recommended` is empty.

The same user state always gives the same answer.

#### Onboarding: `POST /api/topics/mark-known`

Body: `{"domain": "web-development", "topic_ids": ["html_basics", "css_basics"]}` (`topic_ids` may be empty; up to 100 ids).

1. Every id is checked first. Any unknown id rejects the whole request with `400 {"detail": "Unknown topic ids: ..."}` and nothing is written.
2. A known topic implies its prerequisites, so every ancestor of a selected topic (found with a variable-length Neo4j path query) is marked known too.
3. The user gets one `topic_progress` row per topic (created with `INSERT ... ON CONFLICT DO NOTHING`, so a double submit is harmless).
4. Known topics become `completed` with `p_know` of at least 0.95.
5. Every topic whose prerequisites are all completed becomes `unlocked`; the rest stay `locked`.

Response: `{message, known_count, added_prerequisites, recommended}`, where `recommended` holds the next 3 learnable topics (easiest first), each with `id`, `name`, `description`, `difficulty`, `status`, `mastery`, `prerequisites` and `prerequisite_names`.

Calling it again only adds knowledge: completed topics are never relocked, mastery is never lowered, and topics already in progress keep that status.

A topic's status and mastery come from the user's `topic_progress` row. For a topic without a row yet (for example before onboarding), status is derived from the graph: `unlocked` when every prerequisite is completed, otherwise `locked`, with the starting mastery of 10%. The whole curriculum is read in one Neo4j query, so there are no per-topic lookups.

### Quizzes (proctored)

Every quiz is proctored. The server enforces timing and order (layer 1) and scores integrity signals reported by the quiz page (layer 2). An attempt that fails the integrity check is recorded but **doesn't count**: mastery, progress and unlocks stay unchanged.

The flow:

| Step | Endpoint | What it does |
|---|---|---|
| 1 | `GET /api/quiz/generate/{topic_id}` | Creates the quiz and returns `{quiz_id, topic, total_questions, answered_questions, seconds_per_question, expires_in_seconds, source, proctoring}`. **No questions yet.** Starting a quiz abandons any unfinished one (abandoned quizzes never count) |
| 2 | `POST /api/quiz/{quiz_id}/next` | Serves the current question `{question_id, number, total, question, options, deadline, seconds_remaining}` and starts its timer (`QUIZ_SECONDS_PER_QUESTION`, default 60). Calling it again returns the **same** question with the time left, so reloading never resets the clock |
| 3 | `POST /api/quiz/{quiz_id}/answer` | `{"question_id": 0, "answer": 2}` locks in the answer. After the deadline (plus 2 s grace) the answer is refused and the question counts as wrong. Answers can't be changed and earlier questions can't be reopened |
| - | `POST /api/quiz/{quiz_id}/events` | The page reports proctoring signals, up to 100 per request: `heartbeat` (every 5 s), `tab_hidden`, `window_blur`, `fullscreen_exit`, `copy_attempt`, `paste_attempt`, `context_menu`, `multiple_screens` |
| 4 | `POST /api/quiz/submit` | `{"quiz_id": "..."}` scores the quiz, judges integrity and, if verified, updates progress |
| - | `GET /api/quiz/active` | `{active: ...}`: the learner's unfinished quiz, so the page can resume after a reload |

No response before submission ever contains an answer or explanation; the answer key stays in `quiz_sessions` on the server.

| Status | When |
|---|---|
| `403` | Generate: the topic is still locked for this user |
| `404` | Unknown topic, or a quiz id that is unknown **or belongs to another user** (same response, so ids can't be probed) |
| `409` | The quiz was already submitted; or `/next` after the last question; or `/answer` for a question that isn't open |
| `410` | The quiz session expired (`QUIZ_SESSION_TTL_MINUTES`, default 30) |
| `422` | Invalid input, e.g. an answer outside 0-3, an unknown event type, or an old-style `answers` list on submit |
| `429` | Generate: more than `QUIZ_MAX_PER_TOPIC_PER_HOUR` (5) quizzes for one topic or `QUIZ_MAX_PER_HOUR` (30) overall in the last hour. Includes a `Retry-After` header, and is checked **before** the AI is called |
| `503` | A database or the AI (with no fallback) is unavailable; on submit, nothing was saved |

#### Integrity scoring

Each submitted quiz starts at **100** and loses points per signal ([`services/proctoring.py`](backend/services/proctoring.py)):

| Signal | Penalty |
|---|---|
| Switched tab (`tab_hidden`) | 10 each |
| Switched window (`window_blur`) | 5 each |
| Left fullscreen | 15 each |
| Copy or paste attempt | 10 each |
| Right-click menu | 5 each |
| Second screen detected | 20 (once) |
| Answered in under 3 seconds (server-measured) | 10 each |
| Heartbeat silence over 15 seconds (server-measured) | 15 each |
| No heartbeat at all, i.e. monitoring wasn't running | 50 (once) |

**80 or more is verified** and counts. **Below 80 is flagged**: the attempt and its reasons are saved, the result and explanations are still shown, but progress doesn't change. The rules and the threshold are returned by `/generate` so the page can show them before the quiz starts.

#### How questions are produced

[`services/llm_quiz.py`](backend/services/llm_quiz.py):

1. **Groq** is asked for exactly 3 multiple-choice questions in JSON mode, with the topic's name, description, difficulty and domain in the prompt, preferring applied scenario or code questions over definitions that can be looked up quickly.
2. The output is validated: valid JSON (accidental code fences stripped), exactly 3 distinct questions, exactly 4 distinct non-empty options each, `correct` a real integer 0-3, and a non-empty explanation.
3. **Invalid output is retried** up to 2 more times. That includes Groq's own `400 json_validate_failed`.
4. **Groq unavailable** (no API key, network error, timeout, auth error, rate limit or 5xx) skips straight to the **fallback bank** ([`seed/fallback_questions.py`](backend/seed/fallback_questions.py): 3 hand-written questions per topic). Each request times out after 10s, and retries stop after 12s in total.
5. **Options are shuffled** for every quiz and the answer index is remapped, so the answer's position reveals nothing and LLM position bias disappears.

Generating a quiz for an `unlocked` topic marks it `in_progress`. Completed topics can be retaken and stay completed. A learner who requests a quiz before onboarding gets their progress rows created first, as if they had onboarded with nothing selected.

#### What submission does

In one transaction (the quiz session and progress rows are locked, so two simultaneous submits can't both be scored):

1. Answers are scored on the server against the stored key. Timed-out, unanswered and never-served questions count as wrong. The browser never sends a score.
2. Integrity is scored as above.
3. **If verified:** BKT updates `p_know` once per answer, in order; `attempts` goes up by 1 and `correct` by the score; **2/3 or better** completes the topic and unlocks what's now learnable (a failed retake never undoes a completion); `needs_attention` is set when `attempts > 2` and `p_know < 0.50`. **If flagged:** none of that happens.
4. A `quiz_attempts` row stores the question snapshot, answers and mastery before and after, and `quiz_integrity` stores the verdict.

If any step fails (for example Neo4j drops), nothing is saved and the quiz can be submitted again.

Response: `topic_id`, `score`, `total`, `passed`, `p_know_before`, `p_know_after`, `mastered`, `status`, `needs_attention`, `feedback` (per question: `question`, `options`, `selected` (null if unanswered), `correct`, `is_correct`, `timed_out`, `explanation`), `recommended_resources`, `newly_unlocked`, `next_topics` and `integrity` (`score`, `verdict`, `counted`, `reasons`).

Model settings in `backend/.env`:

| Variable | Default | Notes |
|---|---|---|
| `GROQ_API_KEY` | empty | Empty means every quiz comes from the fallback bank |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | The spec's `llama3-8b-8192` and its successor `llama-3.1-8b-instant` are no longer offered by Groq. gpt-oss-120b produced the most precise questions in a comparison with gpt-oss-20b and qwen3.8-27b, at about 1-2s per quiz |
| `GROQ_REASONING_EFFORT` | `low` | Only sent to reasoning models such as gpt-oss; leave empty for other models |

### Progress and dashboard

| Endpoint | Returns |
|---|---|
| `GET /api/progress/dashboard` | Everything the dashboard needs in one call (see below) |
| `GET /api/progress/all` | `{topics: [{topic_id, status, p_know, attempts, correct, needs_attention}]}`: the learner's raw progress rows, ordered by topic id (empty before onboarding) |

The dashboard response:

| Field | Contents |
|---|---|
| `onboarded`, `curriculum_complete` | Whether to send the learner to onboarding, or show the curriculum-complete state |
| `stats` | `total_topics`, `completed_topics`, `in_progress_topics`, `mastered_topics` (p_know >= 0.95), `average_mastery` (mean % over the learner's topics; 0 before onboarding), `total_attempts`, `flagged_attempts` (failed the integrity check; didn't count), `progress_percent` (completed / total) |
| `recommended` | The next 3 topics, the same cards as `/api/topics/learning-path` |
| `needs_attention` | Flagged topics with mastery, attempt count and their learning resources |
| `recent_attempts` | The latest 5 quizzes, newest first: topic name, score, pass/fail, mastery before → after, time, and `counted` / `integrity_verdict` / `integrity_score` (null verdict for attempts made before proctoring) |
| `mastery` | Every topic with status, mastery % and mastered flag, easiest first |

Topic names and resources come from a single Neo4j query joined in memory, so the dashboard makes exactly two Neo4j calls (topics + learning path) however much the learner has done. A test enforces this.

### Mastery tracking (Bayesian Knowledge Tracing)

[`backend/services/bkt.py`](backend/services/bkt.py) holds the mastery model as pure functions with no database imports. `p_know` is the estimated probability that the learner knows a topic. After each quiz answer:

1. **Bayesian update**: how likely is it that they knew it, given the answer?
   - correct: `p_know*(1-p_slip) / (p_know*(1-p_slip) + (1-p_know)*p_guess)`
   - wrong: `p_know*p_slip / (p_know*p_slip + (1-p_know)*(1-p_guess))`
2. **Learning transition**: they may have learned from the attempt: `posterior + (1-posterior)*p_learn`.

Fixed parameters for every user and topic: `p_know=0.10` to start, `p_learn=0.40`, `p_guess=0.20`, `p_slip=0.10`. A topic counts as **mastered** at `p_know >= 0.95`. The three answers of a quiz are applied in order with `update_bkt_sequence()`.

What these values mean in practice (starting from 0.10):

| Answers | p_know after each answer |
|---|---|
| ✓ ✓ ✓ | 0.60, 0.92, 0.99 (mastered after one perfect quiz) |
| ✓ ✓ ✗ | 0.60, 0.92, 0.76 |
| ✗ ✓ ✓ | 0.41, 0.85, 0.98 |
| ✗ ✗ ✗ | 0.41, 0.45, 0.46 |

The order of answers matters for the same score. Because `p_learn` is added after every answer, `p_know` never drops below 0.40 once a question has been answered, and repeated wrong answers level off at 16/35 ≈ 0.457.

### Running the tests

With the venv activated, from `backend/`:

```bash
pytest
```

Tests need the Docker PostgreSQL running. They use a separate database, `adaptlearn_test`, which is created automatically and rebuilt on every run, so your development data is never touched. Set `TEST_DATABASE_URL` to use a different test database.

Neo4j Community has only one database, so the seeder tests write to their own throwaway domain (`pytest-seed`) and delete it afterwards; the real curriculum is never modified. They are skipped if Neo4j is not running.

Frontend tests run with `npm test` from `frontend/`. They fake the HTTP layer, so they need neither the backend nor the databases; any request that would reach a real server fails the test.

### Database tables

On startup the backend creates any missing PostgreSQL tables with SQLAlchemy's `Base.metadata.create_all()`:

| Table | Holds |
|---|---|
| `users` | Accounts (email stored lowercase, password stored only as a bcrypt hash) |
| `topic_progress` | One row per user and topic: status, BKT probabilities, attempt counters, `needs_attention` flag |
| `quiz_attempts` | Submitted quizzes with the full question snapshot, answers and mastery before/after |
| `quiz_sessions` | Generated quizzes awaiting submission, including the server-side answer key |
| `quiz_responses` | One row per served question: when it was served, its deadline, the answer and whether it timed out |
| `proctoring_events` | Signals reported by the quiz page (heartbeats, tab switches, ...) with trusted server receive times |
| `quiz_integrity` | The integrity verdict per quiz: score, verified / flagged / abandoned, whether it counted, reasons |

`create_all()` only creates tables that don't exist yet; it never alters existing ones. This keeps the MVP setup to a single command, but it means **schema changes need a reset in development**:

```bash
docker exec adaptlearn-postgres psql -U postgres -d adaptlearn -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

Then restart the backend to recreate the tables. (Or `docker compose down -v` to wipe both databases.) Alembic migrations are the planned upgrade once real user data needs to survive schema changes.

If PostgreSQL is down when the backend starts, tables are not created - restart the backend once the database is up.

### Curriculum graph (Neo4j)

The Web Development curriculum lives in [`backend/seed/curriculum.py`](backend/seed/curriculum.py): 30 topics (name, description, difficulty 1-4, 1-3 curated resources each) and 37 prerequisite edges. It is the single source of truth for the graph.

On every backend startup it is validated (no duplicate ids, no edges to unknown topics, no prerequisite cycles, valid difficulty and resources) and written to Neo4j:

- topics and edges are `MERGE`d, so repeated startups never create duplicates;
- changed descriptions/resources are updated in place;
- topics or edges removed from the file are removed from the graph (only within that domain);
- everything happens in one transaction, so a failed seed never leaves a half-written graph;
- a unique constraint on `Topic.id` and an index on `Topic.domain` are created if missing.

To seed by hand (for example against Neo4j Aura), from `backend/` with the venv active:

```bash
python -m seed.seed_graph
```

To see the graph, open the Neo4j Browser at http://localhost:7474 (login `neo4j` / `password123`) and run:

```cypher
MATCH (t:Topic {domain: 'web-development'})
OPTIONAL MATCH (t)-[r:PREREQUISITE_OF]->(next:Topic)
RETURN t, r, next
```

Arrows point from a prerequisite to the topic it unlocks.

### Error responses

Every API error returns JSON in the shape `{"detail": "Human-readable message"}`:

| Status | When |
|---|---|
| `404` | Unknown route or resource |
| `422` | Request validation failed; also includes an `errors` list of `{field, message}` |
| `500` | Unexpected server error (details are logged, never sent to the client) |
| `503` | PostgreSQL or Neo4j unavailable |

## Project structure

```text
adaptlearn/
├── docker-compose.yml   # PostgreSQL + Neo4j for local development
├── backend/             # FastAPI application
│   ├── main.py          # App entry point: middleware, routers, lifespan
│   ├── config.py        # Settings loaded from .env
│   ├── errors.py        # Consistent {"detail": ...} error handling
│   ├── requirements.txt
│   ├── .env.example
│   ├── db/              # PostgreSQL + Neo4j connections
│   ├── models/          # SQLAlchemy models (users, topic_progress, quiz_attempts, quiz_sessions)
│   ├── schemas/         # Pydantic request/response schemas
│   ├── routers/         # API routes
│   ├── seed/            # Curriculum data + idempotent Neo4j seeder
│   ├── services/        # Business logic (auth, BKT, quiz, learning path)
│   └── tests/           # pytest suite (runs against adaptlearn_test)
└── frontend/            # React application
    ├── index.html
    ├── vite.config.js   # Vite, Tailwind, @ alias, chunking, Vitest
    ├── components.json  # shadcn/ui settings
    ├── .env.example
    └── src/
        ├── main.jsx, App.jsx, router.jsx   # entry, providers, route table
        ├── index.css    # Tailwind + AdaptLearn palette tokens
        ├── api/         # Axios client (token, 401 handling, error messages) + auth, topics, progress and quiz endpoints
        ├── context/     # AuthProvider (session state)
        ├── hooks/       # useAuth, useForm, useApiData, useQuizSession (quiz flow), useProctoring (browser monitoring), useNow
        ├── routes/      # ProtectedRoute, PublicOnlyRoute, PostAuthRedirect
        ├── components/
        │   ├── ui/      # shadcn/ui primitives (button, card, badge, alert, input, ...)
        │   ├── common/  # Loader, ErrorState, EmptyState, ProgressBar, PageHeader
        │   ├── dashboard/   # StatCard, RecommendedTopicCard, AttentionCard, RecentAttempts, MasteryOverview
        │   ├── forms/   # TextField, PasswordField, FormAlert, SubmitButton
        │   ├── onboarding/  # TopicOption, SelectionBar
        │   ├── layout/  # AppShell (with focus mode), Navbar, AuthLayout, Logo
        │   ├── quiz/    # QuizIntro, QuizReady, QuizRunner, QuestionCard, QuizResult, QuizEnded, LeaveQuizDialog, QuizText
        │   └── topics/  # TopicStatusBadge, ResourceList
        ├── lib/         # validation rules, server-error mapping, topic helpers (difficulty, prerequisites, actions), formatting (incl. code in quiz text), proctoring event reporter, status styles, redirect helper
        ├── pages/       # one component per route
        └── test/        # Vitest setup and helpers
```

## Security notes

- Never commit `.env` files; only `.env.example` (names and safe defaults) is tracked.
- JWTs are stored in `localStorage` to match the reference design. For production hardening, move to secure HttpOnly cookies with refresh tokens.
- Login and registration are not rate-limited yet; add rate limiting before a public deployment.
