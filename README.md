# AdaptLearn

An adaptive learning platform that builds a personalised learning path instead of pushing every learner through the same fixed sequence.

- **Neo4j knowledge graph** - topics and their prerequisites decide what a learner can study next.
- **Bayesian Knowledge Tracing (BKT)** - a per-user, per-topic mastery probability updated after every quiz answer.
- **Groq LLM** - generates fresh 3-question multiple-choice quizzes, with a curated fallback bank.
- **PostgreSQL** - users, progress, quiz sessions and attempt history.
- **React** - dashboard, quizzes and an interactive knowledge graph.

The first fully seeded domain is **Web Development** (30 topics).

See [PRD.md](PRD.md), [ARCHITECTURE.md](ARCHITECTURE.md) and [ROADMAP.md](ROADMAP.md) for the full specification, and [PROJECT-STATE.md](PROJECT-STATE.md) for current progress.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + Tailwind CSS, react-force-graph-2d |
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

### Quizzes

#### Generating a quiz: `GET /api/quiz/generate/{topic_id}`

Returns `{quiz_id, topic: {id, name}, questions: [{id, question, options}], expires_in_seconds, source}`: exactly 3 questions with 4 options each. **The response never contains the correct answers or explanations.** Those are stored server-side in `quiz_sessions` and only revealed when the quiz is submitted.

| Status | When |
|---|---|
| `200` | Quiz created. `source` is `ai` (Groq) or `fallback` (curated question bank) |
| `403` | The topic is still locked for this user |
| `404` | Unknown topic id |
| `503` | Groq failed and no fallback questions exist (cannot happen for the seeded curriculum) |

How questions are produced ([`services/llm_quiz.py`](backend/services/llm_quiz.py)):

1. **Groq** is asked for exactly 3 multiple-choice questions in JSON mode, with the topic's name, description, difficulty and domain in the prompt.
2. The output is validated: valid JSON (accidental code fences stripped), exactly 3 distinct questions, exactly 4 distinct non-empty options each, `correct` a real integer 0-3, and a non-empty explanation.
3. **Invalid output is retried** up to 2 more times. That includes Groq's own `400 json_validate_failed`.
4. **Groq unavailable** (no API key, network error, timeout, auth error, rate limit or 5xx) skips straight to the **fallback bank** ([`seed/fallback_questions.py`](backend/seed/fallback_questions.py): 3 hand-written questions per topic). Each request times out after 10s, and retries stop after 12s in total, so the learner always gets a quiz before the browser times out.
5. **Options are shuffled** for every quiz and the answer index is remapped, so the answer's position reveals nothing and LLM position bias disappears.

Generating a quiz for an `unlocked` topic marks it `in_progress`. Completed topics can be retaken and stay completed. A learner who requests a quiz before onboarding gets their progress rows created first, as if they had onboarded with nothing selected.

Model settings in `backend/.env`:

| Variable | Default | Notes |
|---|---|---|
| `GROQ_API_KEY` | empty | Empty means every quiz comes from the fallback bank |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | The spec's `llama3-8b-8192` and its successor `llama-3.1-8b-instant` are no longer offered by Groq. gpt-oss-120b produced the most precise questions in a comparison with gpt-oss-20b and qwen3.8-27b, at about 1-2s per quiz |
| `GROQ_REASONING_EFFORT` | `low` | Only sent to reasoning models such as gpt-oss; leave empty for other models |

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

### Database tables

On startup the backend creates any missing PostgreSQL tables with SQLAlchemy's `Base.metadata.create_all()`:

| Table | Holds |
|---|---|
| `users` | Accounts (email stored lowercase, password stored only as a bcrypt hash) |
| `topic_progress` | One row per user and topic: status, BKT probabilities, attempt counters, `needs_attention` flag |
| `quiz_attempts` | Submitted quizzes with the full question snapshot, answers and mastery before/after |
| `quiz_sessions` | Generated quizzes awaiting submission, including the server-side answer key |

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

Frontend run instructions will be added when the UI is built.

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
└── frontend/            # React application (built last)
```

## Security notes

- Never commit `.env` files; only `.env.example` (names and safe defaults) is tracked.
- JWTs are stored in `localStorage` to match the reference design. For production hardening, move to secure HttpOnly cookies with refresh tokens.
- Login and registration are not rate-limited yet; add rate limiting before a public deployment.
