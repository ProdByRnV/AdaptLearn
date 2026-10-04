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

### Running the tests

With the venv activated, from `backend/`:

```bash
pytest
```

Tests need the Docker PostgreSQL running. They use a separate database, `adaptlearn_test`, which is created automatically and rebuilt on every run, so your development data is never touched. Set `TEST_DATABASE_URL` to use a different test database.

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
│   ├── services/        # Business logic (auth, BKT, quiz, learning path)
│   └── tests/           # pytest suite (runs against adaptlearn_test)
└── frontend/            # React application (built last)
```

## Security notes

- Never commit `.env` files; only `.env.example` (names and safe defaults) is tracked.
- JWTs are stored in `localStorage` to match the reference design. For production hardening, move to secure HttpOnly cookies with refresh tokens.
- Login and registration are not rate-limited yet; add rate limiting before a public deployment.
