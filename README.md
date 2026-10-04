# AdaptLearn

An adaptive learning platform that builds a personalised learning path instead of pushing every learner through the same fixed sequence.

- **Neo4j knowledge graph** - topics and their prerequisites decide what a learner can study next.
- **Bayesian Knowledge Tracing (BKT)** - a per-user, per-topic mastery probability updated after every quiz answer.
- **Groq LLM** - generates fresh 3-question multiple-choice quizzes, with a curated fallback bank.
- **PostgreSQL** - users, progress, quiz sessions and attempt history.
- **React** - dashboard, quizzes and an interactive knowledge graph.

The first fully seeded domain is **Web Development** (30 topics).

See [PRD.md](PRD.md), [ARCHITECTURE.md](ARCHITECTURE.md) and [ROADMAP.md](ROADMAP.md) for the full specification.

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

### 2. Configure the backend

```bash
cd backend
cp .env.example .env
```

Then edit `backend/.env`:

- set `JWT_SECRET_KEY` to a random value, e.g. `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- optionally set `GROQ_API_KEY`; without it, quizzes come from the fallback question bank

> On Windows, if `python` is not on your PATH, use the launcher instead: `py -3`.

Backend and frontend run instructions will be added here as those parts are built.

## Project structure

```text
adaptlearn/
├── docker-compose.yml   # PostgreSQL + Neo4j for local development
├── backend/             # FastAPI application
│   ├── .env.example
│   ├── db/              # PostgreSQL + Neo4j connections
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic request/response schemas
│   ├── routers/         # API routes
│   └── services/        # Business logic (auth, BKT, quiz, learning path)
└── frontend/            # React application (built last)
```

## Security notes

- Never commit `.env` files; only `.env.example` (names and safe defaults) is tracked.
- JWTs are stored in `localStorage` to match the reference design. For production hardening, move to secure HttpOnly cookies with refresh tokens.
