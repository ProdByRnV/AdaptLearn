# AdaptLearn — Architecture & Engineering Specification

**Purpose:** This document tells the coding agent exactly how the system should be structured and how the parts communicate.

---

# 1. System Architecture

```mermaid
flowchart LR
    U[Student Browser] --> FE[React 18 + Vite + Tailwind]
    FE -->|REST + JWT| API[FastAPI]

    API --> PG[(PostgreSQL)]
    API --> NEO[(Neo4j 5)]
    API --> GROQ[Groq LLM API]

    PG -->|users, progress, quiz history| API
    NEO -->|topics, prerequisites, resources| API
    GROQ -->|3 MCQs JSON| API

    FE --> GRAPH[react-force-graph-2d]
```

### Responsibilities

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | React 18 + Vite + Tailwind | SPA, pages, forms, graph UI, state |
| Graph UI | react-force-graph-2d | Interactive topic network |
| API | FastAPI | REST endpoints, auth, orchestration, business logic |
| Auth | JWT + bcrypt | Stateless authentication |
| Relational DB | PostgreSQL + SQLAlchemy | Users, user progress, quiz history, quiz sessions |
| Graph DB | Neo4j 5 | Topic metadata and prerequisite edges |
| AI | Groq | Structured quiz generation |
| Algorithm | BKT | Mastery estimation per user/topic |

---

# 2. Repository Structure

Build exactly this logical structure. Small helper files may be added when needed, but do not collapse responsibilities into one huge file.

```text
adaptlearn/
├── README.md
├── PRD.md
├── ROADMAP.md
├── ARCHITECTURE.md
├── UI.md
├── .gitignore
├── docker-compose.yml
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── config.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── postgres.py
│   │   └── neo4j_db.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── topics.py
│   │   ├── quiz.py
│   │   └── progress.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── topics.py
│   │   ├── quiz.py
│   │   └── progress.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── bkt.py
│   │   ├── llm_quiz.py
│   │   ├── learning_path.py
│   │   └── quiz_service.py
│   │
│   ├── seed/
│   │   ├── curriculum.py
│   │   └── fallback_questions.py
│   │
│   └── tests/
│       ├── test_auth.py
│       ├── test_bkt.py
│       ├── test_learning_path.py
│       └── test_quiz.py
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── .env.example
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css
        │
        ├── api/
        │   └── client.js
        │
        ├── hooks/
        │   └── useAuth.jsx
        │
        ├── components/
        │   ├── layout/
        │   │   ├── AppShell.jsx
        │   │   └── Navbar.jsx
        │   ├── common/
        │   │   ├── Button.jsx
        │   │   ├── Card.jsx
        │   │   ├── Loader.jsx
        │   │   ├── EmptyState.jsx
        │   │   ├── ErrorState.jsx
        │   │   └── ProgressBar.jsx
        │   ├── topics/
        │   │   ├── TopicCard.jsx
        │   │   ├── TopicStatusBadge.jsx
        │   │   └── TopicDetailPanel.jsx
        │   └── quiz/
        │       ├── QuestionCard.jsx
        │       └── QuizResult.jsx
        │
        └── pages/
            ├── Login.jsx
            ├── Register.jsx
            ├── Onboarding.jsx
            ├── Dashboard.jsx
            ├── QuizPage.jsx
            ├── GraphPage.jsx
            └── NotFound.jsx
```

---

# 3. Environment Variables

## Backend `.env.example`

```env
APP_ENV=development
FRONTEND_URL=http://localhost:5173
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/adaptlearn
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
JWT_SECRET_KEY=replace_me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
GROQ_API_KEY=
GROQ_MODEL=llama3-8b-8192
QUIZ_SESSION_TTL_MINUTES=30
```

## Frontend `.env.example`

```env
VITE_API_URL=http://localhost:8000/api
```

In local development, the Vite proxy may allow `VITE_API_URL=/api`.

---

# 4. Docker Compose

Local `docker-compose.yml` should start:

1. PostgreSQL 15
2. Neo4j 5

Expected ports:

- PostgreSQL `5432`
- Neo4j browser `7474`
- Neo4j Bolt `7687`

Use persistent named volumes.

Backend and frontend may run outside Docker for easier development.

---

# 5. PostgreSQL Data Model

The guide defines three core tables. This build adds `quiz_sessions` as a security-hardening table so the browser never needs the answer key.

## 5.1 `users`

```text
id                SERIAL PRIMARY KEY
username          VARCHAR(80) NOT NULL
email             VARCHAR(255) UNIQUE NOT NULL
hashed_password   VARCHAR(255) NOT NULL
created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```

Indexes:

- unique index on `email`

---

## 5.2 `topic_progress`

One row per `(user_id, topic_id)`.

```text
id                SERIAL PRIMARY KEY
user_id           INTEGER FK users.id NOT NULL
topic_id          VARCHAR(100) NOT NULL
status            VARCHAR(20) NOT NULL DEFAULT 'locked'
p_know            FLOAT NOT NULL DEFAULT 0.10
p_learn           FLOAT NOT NULL DEFAULT 0.40
p_slip            FLOAT NOT NULL DEFAULT 0.10
p_guess           FLOAT NOT NULL DEFAULT 0.20
attempts          INTEGER NOT NULL DEFAULT 0
correct           INTEGER NOT NULL DEFAULT 0
needs_attention   BOOLEAN NOT NULL DEFAULT FALSE
created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```

Constraint:

```text
UNIQUE(user_id, topic_id)
```

Index:

```text
(user_id, topic_id)
```

Allowed status values:

- locked
- unlocked
- in_progress
- completed

---

## 5.3 `quiz_attempts`

```text
id                SERIAL PRIMARY KEY
user_id           INTEGER FK users.id NOT NULL
topic_id          VARCHAR(100) NOT NULL
score             INTEGER NOT NULL
passed            BOOLEAN NOT NULL
questions         JSONB NOT NULL
submitted_answers JSONB NOT NULL
p_know_before     FLOAT NOT NULL
p_know_after      FLOAT NOT NULL
created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```

Index:

```text
(user_id, created_at DESC)
```

`questions` may contain the full question snapshot after submission for history/audit.

---

## 5.4 `quiz_sessions`

Security-hardening extension.

```text
id                UUID PRIMARY KEY
user_id           INTEGER FK users.id NOT NULL
topic_id          VARCHAR(100) NOT NULL
questions         JSONB NOT NULL
created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
expires_at        TIMESTAMP WITH TIME ZONE NOT NULL
submitted_at      TIMESTAMP WITH TIME ZONE NULL
```

`questions` here contains correct answer indices but is never returned directly to the browser.

Session can be submitted once only.

---

# 6. Neo4j Graph Model

## Node

```cypher
(:Topic {
  id: 'js_fundamentals',
  name: 'JavaScript Fundamentals',
  description: '...',
  difficulty: 2,
  domain: 'web-development',
  resources: '[...]'
})
```

Implementation note: Neo4j supports lists/maps, but keep `resources` in a representation that the official Python driver can return consistently. A list of maps is acceptable if supported by the chosen driver usage; JSON string is also acceptable if parsing is centralized.

## Relationship

```cypher
(:Topic)-[:PREREQUISITE_OF]->(:Topic)
```

Meaning:

`left topic must be learned/completed before right topic becomes unlocked`.

---

# 7. Seed Topic IDs

Use stable snake_case IDs.

| # | Topic | ID | Difficulty |
|---|---|---|---:|
| 1 | HTML Basics | `html_basics` | 1 |
| 2 | Semantic HTML | `semantic_html` | 1 |
| 3 | Forms & Accessibility | `forms_accessibility` | 2 |
| 4 | CSS Basics | `css_basics` | 1 |
| 5 | Flexbox | `flexbox` | 2 |
| 6 | CSS Grid | `css_grid` | 2 |
| 7 | Responsive Design | `responsive_design` | 2 |
| 8 | JavaScript Fundamentals | `javascript_fundamentals` | 1 |
| 9 | Functions & Scope | `functions_scope` | 2 |
| 10 | Arrays & Objects | `arrays_objects` | 2 |
| 11 | DOM Manipulation | `dom_manipulation` | 2 |
| 12 | Browser Events | `browser_events` | 2 |
| 13 | Async JavaScript | `async_javascript` | 3 |
| 14 | Fetch & HTTP APIs | `fetch_http_apis` | 3 |
| 15 | ES Modules | `es_modules` | 2 |
| 16 | Git Basics | `git_basics` | 1 |
| 17 | Node.js Basics | `nodejs_basics` | 2 |
| 18 | npm & Packages | `npm_packages` | 2 |
| 19 | Express.js Basics | `express_basics` | 3 |
| 20 | REST API Design | `rest_api_design` | 3 |
| 21 | Authentication Basics | `authentication_basics` | 4 |
| 22 | SQL Basics | `sql_basics` | 2 |
| 23 | PostgreSQL Basics | `postgresql_basics` | 3 |
| 24 | React Fundamentals | `react_fundamentals` | 2 |
| 25 | Props & State | `props_state` | 2 |
| 26 | React Hooks | `react_hooks` | 3 |
| 27 | React Router | `react_router` | 3 |
| 28 | API Integration in React | `react_api_integration` | 3 |
| 29 | Testing Basics | `testing_basics` | 4 |
| 30 | Deployment Basics | `deployment_basics` | 4 |

---

# 8. Required Prerequisite Edges

This edge list is an **implementation design decision** so the graph is deterministic.

```text
html_basics -> semantic_html
semantic_html -> forms_accessibility
html_basics -> css_basics
css_basics -> flexbox
css_basics -> css_grid
flexbox -> responsive_design
css_grid -> responsive_design

javascript_fundamentals -> functions_scope
javascript_fundamentals -> arrays_objects
functions_scope -> dom_manipulation
arrays_objects -> dom_manipulation
dom_manipulation -> browser_events
functions_scope -> async_javascript
async_javascript -> fetch_http_apis
javascript_fundamentals -> es_modules

git_basics -> nodejs_basics
javascript_fundamentals -> nodejs_basics
nodejs_basics -> npm_packages
npm_packages -> express_basics
express_basics -> rest_api_design
rest_api_design -> authentication_basics

sql_basics -> postgresql_basics
rest_api_design -> postgresql_basics

javascript_fundamentals -> react_fundamentals
html_basics -> react_fundamentals
css_basics -> react_fundamentals
react_fundamentals -> props_state
props_state -> react_hooks
react_hooks -> react_router
fetch_http_apis -> react_api_integration
react_hooks -> react_api_integration
react_router -> react_api_integration

rest_api_design -> testing_basics
react_api_integration -> testing_basics
postgresql_basics -> testing_basics

testing_basics -> deployment_basics
authentication_basics -> deployment_basics
```

Seed operation must be **idempotent** using `MERGE`, not blind `CREATE` on every startup.

---

# 9. Neo4j Queries

## 9.1 All topics

```cypher
MATCH (t:Topic {domain: $domain})
RETURN t
ORDER BY t.difficulty, t.name
```

## 9.2 Graph data

```cypher
MATCH (t:Topic {domain: $domain})
OPTIONAL MATCH (t)-[:PREREQUISITE_OF]->(next:Topic {domain: $domain})
RETURN t, next
```

Transform backend response into:

```json
{
  "nodes": [],
  "links": []
}
```

## 9.3 Learnable frontier

Use the user's completed topic IDs from PostgreSQL.

```cypher
MATCH (t:Topic {domain: $domain})
WHERE NOT t.id IN $completed_ids
OPTIONAL MATCH (pre:Topic)-[:PREREQUISITE_OF]->(t)
WITH t, collect(pre.id) AS prereqs
WHERE ALL(p IN prereqs WHERE p IN $completed_ids OR p IS NULL)
RETURN t, prereqs
ORDER BY t.difficulty ASC, t.name ASC
LIMIT 3
```

---

# 10. Initialization / User Progress Strategy

On first onboarding for a domain:

1. fetch all topic IDs from Neo4j,
2. create missing `topic_progress` rows for user,
3. mark selected known topics `completed`,
4. assign known topics `p_know = 0.95`,
5. calculate learnable frontier,
6. set frontier rows `unlocked`,
7. keep remaining rows `locked`.

Whenever a topic becomes completed:

1. recalculate the frontier,
2. set newly eligible locked topics to `unlocked`,
3. never relock a completed topic.

---

# 11. BKT Algorithm

## Defaults

```text
p_know = 0.10
p_learn = 0.40
p_guess = 0.20
p_slip = 0.10
mastery_threshold = 0.95
```

## Correct answer

```text
posterior = p_know * (1 - p_slip)
            -----------------------------------------------
            p_know*(1-p_slip) + (1-p_know)*p_guess
```

## Wrong answer

```text
posterior = p_know * p_slip
            ---------------------------------------------------
            p_know*p_slip + (1-p_know)*(1-p_guess)
```

## Learning transition

After the Bayesian update:

```text
p_know_new = posterior + (1 - posterior) * p_learn
```

Clamp numeric result to `[0.0, 1.0]`.

Update sequentially for each of the 3 answers.

### Service contract

```python
def update_bkt(
    p_know: float,
    correct: bool,
    p_learn: float = 0.40,
    p_guess: float = 0.20,
    p_slip: float = 0.10,
) -> float:
    ...


def mastery_reached(p_know: float) -> bool:
    return p_know >= 0.95
```

---

# 12. Authentication Architecture

## Registration

```text
React form
  -> POST /api/auth/register
  -> Pydantic validation
  -> check unique email
  -> bcrypt hash password
  -> insert user
  -> issue JWT
  -> frontend stores token
  -> redirect /onboarding
```

## Login

```text
POST /api/auth/login
  -> locate user by email
  -> bcrypt verify
  -> JWT {sub: user_id, exp: ...}
  -> return access_token
```

## Protected request

Axios request interceptor:

```text
Authorization: Bearer <JWT>
```

FastAPI dependency:

```text
OAuth2PasswordBearer -> decode JWT -> resolve current user -> endpoint
```

If invalid/expired:

- backend `401`,
- frontend clears token,
- redirect `/login`.

---

# 13. API Contracts

All API routes use `/api` prefix except root health route.

## 13.1 `POST /api/auth/register`

Request:

```json
{
  "username": "Puja",
  "email": "puja@example.com",
  "password": "StrongPassword123"
}
```

Response `201`:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "Puja",
    "email": "puja@example.com"
  }
}
```

Errors:

- `409` email already exists
- `422` invalid input

---

## 13.2 `POST /api/auth/login`

Request:

```json
{
  "email": "puja@example.com",
  "password": "StrongPassword123"
}
```

Response `200`: same auth shape as registration.

Error: `401` invalid credentials.

---

## 13.3 `GET /api/auth/me`

Response:

```json
{
  "id": 1,
  "username": "Puja",
  "email": "puja@example.com"
}
```

---

## 13.4 `GET /api/topics/all?domain=web-development`

Response:

```json
{
  "domain": "web-development",
  "topics": [
    {
      "id": "html_basics",
      "name": "HTML Basics",
      "description": "...",
      "difficulty": 1,
      "resources": []
    }
  ]
}
```

---

## 13.5 `POST /api/topics/mark-known`

Request:

```json
{
  "domain": "web-development",
  "topic_ids": ["html_basics", "css_basics"]
}
```

Response:

```json
{
  "message": "Onboarding saved",
  "known_count": 2,
  "recommended": []
}
```

Must reject unknown topic IDs.

---

## 13.6 `GET /api/topics/learning-path`

Response:

```json
{
  "recommended": [
    {
      "id": "javascript_fundamentals",
      "name": "JavaScript Fundamentals",
      "difficulty": 1,
      "status": "unlocked",
      "mastery": 10.0,
      "prerequisites": []
    }
  ]
}
```

Return maximum 3 recommended topics.

---

## 13.7 `GET /api/topics/graph`

Response:

```json
{
  "nodes": [
    {
      "id": "html_basics",
      "name": "HTML Basics",
      "description": "...",
      "difficulty": 1,
      "status": "completed",
      "mastery": 95.0,
      "resources": []
    }
  ],
  "links": [
    {
      "source": "html_basics",
      "target": "semantic_html"
    }
  ]
}
```

---

## 13.8 `GET /api/quiz/generate/{topic_id}`

Response:

```json
{
  "quiz_id": "uuid",
  "topic": {
    "id": "javascript_fundamentals",
    "name": "JavaScript Fundamentals"
  },
  "questions": [
    {
      "id": 0,
      "question": "...",
      "options": ["...", "...", "...", "..."]
    }
  ],
  "expires_in_seconds": 1800
}
```

No `correct`, `correct_answer`, or equivalent field may be present.

Errors:

- `403` topic locked
- `404` topic not found
- `503` quiz generation failed and fallback unavailable

---

## 13.9 `POST /api/quiz/submit`

Request:

```json
{
  "quiz_id": "uuid",
  "answers": [0, 2, 1]
}
```

Response:

```json
{
  "topic_id": "javascript_fundamentals",
  "score": 2,
  "total": 3,
  "passed": true,
  "p_know_before": 0.10,
  "p_know_after": 0.78,
  "mastered": false,
  "status": "completed",
  "needs_attention": false,
  "feedback": [
    {
      "question": "...",
      "selected": 0,
      "correct": 0,
      "is_correct": true,
      "explanation": "..."
    }
  ],
  "recommended_resources": [],
  "next_topics": []
}
```

Rules:

- exactly 3 answers,
- quiz must belong to current user,
- session must not be expired,
- session may be submitted only once.

---

## 13.10 `GET /api/progress/dashboard`

Response:

```json
{
  "stats": {
    "total_topics": 30,
    "completed_topics": 6,
    "mastered_topics": 3,
    "average_mastery": 42.5,
    "total_attempts": 11
  },
  "recommended": [],
  "needs_attention": [],
  "recent_attempts": [],
  "mastery": []
}
```

This should be the main dashboard aggregation endpoint.

---

## 13.11 `GET /api/progress/all`

Response:

```json
{
  "topics": [
    {
      "topic_id": "html_basics",
      "status": "completed",
      "p_know": 0.95,
      "attempts": 1,
      "correct": 3,
      "needs_attention": false
    }
  ]
}
```

---

# 14. LLM Service

## Prompt requirements

System prompt must demand strict machine-readable output.

Recommended structure:

```text
You are a quiz generator for an adaptive learning platform.
Return ONLY valid JSON. Do not use markdown fences or prose outside JSON.
Generate exactly 3 multiple-choice questions for the topic provided.
Each question must contain:
- question: string
- options: exactly 4 strings
- correct: integer 0-3
- explanation: concise string
Questions should test understanding, not obscure trivia.
```

User prompt should include:

- topic name,
- topic description,
- difficulty,
- domain.

LLM settings:

- model from `GROQ_MODEL`,
- temperature about `0.7`,
- sufficient output token limit (~1500),
- timeout around 10 seconds.

## Validation flow

```text
Groq response
 -> strip accidental code fences only if necessary
 -> json.loads
 -> Pydantic schema
 -> business validation
 -> accept OR retry
 -> fallback question bank
```

Retry maximum: 2 retries after initial attempt.

---

# 15. Quiz Session Security

This is required.

Generation:

1. LLM returns full questions with answer key.
2. Backend saves full data under `quiz_sessions.id`.
3. Backend sanitizes questions.
4. Only sanitized version goes to frontend.

Submission:

1. fetch session by quiz ID + current user ID,
2. reject if missing/expired/already submitted,
3. score server-side,
4. persist `quiz_attempts`,
5. mark session submitted.

Never trust a score sent by the browser.

---

# 16. Dashboard Aggregation Logic

Backend should calculate:

- `total_topics` from Neo4j domain count,
- `completed_topics` from PostgreSQL,
- `mastered_topics` where `p_know >= 0.95`,
- `average_mastery` across initialized topic progress,
- `total_attempts` from quiz attempts count,
- `recommended` from learning-path service,
- `needs_attention` from progress rows,
- `recent_attempts` latest 5,
- `mastery` list joined with topic names.

Avoid N+1 Neo4j lookups. Fetch topic metadata in one query and map by ID.

---

# 17. Confusion Detection

After every quiz submission:

```python
needs_attention = attempts > 2 and p_know < 0.50
```

If true:

- persist flag,
- show on dashboard,
- return resources in result.

If later performance improves above the threshold, clear the flag.

---

# 18. Frontend Architecture

## React Router

```text
/login
/register
/onboarding
/dashboard
/quiz/:topicId
/graph
*
```

`PrivateRoute` behavior:

- if checking auth → full-page loader,
- if no token/user → `/login`,
- else render protected page.

## Auth context

State:

```text
user
token
loading
isAuthenticated
```

Methods:

```text
register()
login()
logout()
refreshUser()
```

On app mount:

1. read JWT from localStorage,
2. call `/auth/me`,
3. if valid set user,
4. if 401 clear token.

## Axios client

Request interceptor:

- attach Bearer token.

Response interceptor:

- on 401 clear auth and redirect to login.

Set timeout, e.g. 15 seconds.

---

# 19. Graph Rendering Mapping

Backend returns status; frontend maps to UI properties.

```javascript
const colorByStatus = {
  completed: '#0F766E',
  in_progress: '#0EA5E9',
  unlocked: '#5EEAD4',
  locked: '#94A3B8'
};
```

If `p_know >= 0.95`, completed node may use a stronger completed/mastered style.

Suggested node size:

```text
locked: 4
unlocked: 6
in_progress: 7
completed: 8
mastered: 10
```

Use:

- `nodeCanvasObject` for labels,
- directional arrows on links,
- click handler to open detail panel.

---

# 20. Error Handling

Backend should raise explicit HTTP errors.

Examples:

```python
raise HTTPException(status_code=403, detail="Topic is still locked")
```

Frontend central behavior:

- network errors → retry-capable error card,
- 401 → login,
- 403 → explain prerequisite lock,
- 404 → topic/quiz unavailable,
- 503 → quiz generation fallback message.

Do not show raw stack traces in UI.

---

# 21. Local Development Commands

## Databases

```bash
docker compose up -d
```

## Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

## Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Verify:

- frontend: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`
- Neo4j browser: `http://localhost:7474`

---

# 22. Deployment Architecture

```text
Vercel (React)
   |
   v
Railway (FastAPI)
  /   |    \
 /    |     \
Neon  Aura   Groq
PG    Neo4j  API
```

Production requirements:

- set allowed CORS origin to Vercel URL,
- use HTTPS endpoints,
- set all secrets in platform env vars,
- use managed DB URLs,
- never use dev credentials,
- run seed safely/idempotently.

---

# 23. Backend Test Cases

## BKT

- correct answer increases/update p_know as formula dictates,
- wrong answer follows wrong-answer Bayes formula,
- result remains within 0..1,
- mastery is true at >=0.95.

## Auth

- register success,
- duplicate email rejected,
- wrong password rejected,
- protected route without token returns 401.

## Learning path

- root topics unlocked when no prerequisites,
- topic with missing prerequisite remains locked,
- topic unlocks when all prerequisites completed,
- completed topic excluded from recommendations.

## Quiz

- generation returns exactly 3 sanitized questions,
- answer key absent in API response,
- wrong user's quiz submission rejected,
- expired quiz rejected,
- second submission rejected,
- successful submission writes attempt and progress.

---

# 24. Engineering Quality Rules

- Use type hints in Python.
- Use Pydantic request/response schemas.
- Use dependency injection for DB sessions and current user.
- Keep routers thin; business logic belongs in services.
- Keep Neo4j queries centralized in DB/service layer.
- Do not concatenate user input into Cypher strings.
- Keep React pages focused on orchestration; reusable UI belongs in components.
- Avoid giant 500+ line components.
- No direct fetch calls scattered across pages; centralize in `api/client.js`.
- Include comments only where logic is non-obvious.
- All environment-sensitive values configurable.
