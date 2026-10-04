# AdaptLearn — Product Requirements Document (PRD)

**Version:** 1.0  
**Status:** Build-ready specification  
**Product:** AdaptLearn — Adaptive Learning Platform  
**Primary build target:** Full-stack web application  
**Primary user:** Computer-science learner/student  

---

## 0. Instructions for Claude / Coding Agent

Read **all four specification files before writing code**:

1. `PRD.md` — product behavior and acceptance criteria
2. `ARCHITECTURE.md` — technical design, data models, APIs, flows
3. `UI.md` — exact frontend UX and visual behavior
4. `ROADMAP.md` — required implementation order and verification gates

### Non-negotiable build rules

- Do not change the primary stack unless absolutely blocked.
- Do not replace Neo4j with a relational graph implementation.
- Do not replace PostgreSQL with MongoDB/SQLite.
- Do not replace FastAPI with another backend framework.
- Do not replace React + Vite with Next.js.
- Do not expose quiz correct answers to the browser before submission.
- Do not hard-code fake dashboard values; dashboard data must come from APIs.
- Do not leave placeholder buttons, dead routes, TODO-only functions, or mock-only features in the final build.
- Keep secrets in environment variables only.
- Add graceful loading, empty, validation, and error states for every async screen.
- Build the project so that `docker compose up -d`, backend startup, and frontend startup are enough for local development.
- Prefer clear, maintainable code over premature optimization.

If a tiny implementation detail is not specified, choose the simplest production-sensible option while preserving the documented behavior.

---

# 1. Product Summary

AdaptLearn is a full-stack adaptive learning platform that creates a personalized learning path instead of forcing every learner through the same fixed sequence.

A learner:

1. creates an account,
2. chooses a learning domain,
3. marks topics already known,
4. receives the next topics they are ready to learn,
5. takes AI-generated quizzes,
6. gets a continuously updated mastery probability using Bayesian Knowledge Tracing (BKT),
7. receives resources when struggling,
8. unlocks later topics as prerequisites are completed,
9. sees the entire curriculum as an interactive knowledge graph.

The core differentiator is the combination of:

- **Neo4j knowledge graph** for prerequisite-aware learning paths,
- **Bayesian Knowledge Tracing (BKT)** for per-user per-topic mastery,
- **Groq LLM** for fresh quiz generation,
- **PostgreSQL** for users, progress, and attempt history,
- **React** for an interactive learner experience.

---

# 2. Problem Statement

Most learning products are linear. They assume that every learner:

- begins with the same prior knowledge,
- should study topics in the same order,
- learns at the same speed,
- can be represented using a simple pass/fail score.

This creates three problems:

1. **Advanced learners waste time** revisiting topics they already know.
2. **Beginners get overwhelmed** when prerequisite concepts are missing.
3. **A single quiz score is weak evidence of mastery** because a learner can guess correctly or make an accidental mistake.

AdaptLearn addresses these issues by maintaining a learning graph and a probabilistic mastery state for each learner/topic pair.

---

# 3. Product Goals

## 3.1 MVP goals

The MVP must:

- support registration and login,
- support one fully seeded learning domain: **Web Development**,
- seed a 30-topic prerequisite graph in Neo4j,
- let users mark known topics during onboarding,
- calculate the currently learnable topic frontier,
- recommend the next 3 topics,
- generate 3-question MCQ quizzes using Groq,
- update BKT mastery after every submitted answer,
- maintain quiz history and progress in PostgreSQL,
- identify struggling/confused topics,
- recommend curated resources after poor performance,
- render an interactive knowledge graph,
- work locally and be deployable to the documented cloud stack.

## 3.2 Success criteria

The MVP is considered successful when a new user can complete this full journey without developer intervention:

`Register → Onboard → Dashboard → Start Topic → Generate Quiz → Submit → View Result → Mastery Updates → Learning Path Updates → View Knowledge Graph`

---

# 4. Non-Goals for MVP

Do **not** build the following into the first stable release:

- payments/subscriptions,
- live classes,
- video hosting,
- instructor/admin portal,
- social feed,
- peer-to-peer chat,
- mobile native app,
- full LMS course-authoring system,
- code-execution sandbox,
- multi-tenant organization management,
- Deep Knowledge Tracing,
- complex gamification economy.

They may be listed as future scope only.

---

# 5. Target User

## Primary persona: Student learner

A computer-science learner who:

- already knows some topics but not all,
- wants to avoid repeating basics,
- wants a clear next step,
- wants quick assessment after a topic,
- wants visible progress and confidence/mastery tracking.

---

# 6. Canonical Product Rules

These rules are the source of truth for implementation.

## 6.1 Topic states

A user's topic can have one of these UI states:

- `locked` — at least one prerequisite is incomplete,
- `unlocked` — all prerequisites are complete; learner may begin,
- `in_progress` — learner has started/attempted the topic,
- `completed` — learner has passed at least one quiz for the topic.

Separately, the BKT mastery probability (`p_know`) is continuous from `0.0` to `1.0`.

A topic is displayed as **Mastered** when:

`p_know >= 0.95`

### Important distinction

- **Quiz pass** controls prerequisite completion/unlocking.
- **BKT mastery** measures confidence in actual knowledge.
- A topic may be `completed` but not yet `mastered`.

This keeps the discrete UI progression state and probabilistic BKT state separate.

## 6.2 Quiz rule

Each generated quiz has exactly **3 multiple-choice questions**.

Each question has exactly **4 options** and one correct answer.

Pass condition:

`score >= 2 out of 3`

## 6.3 Confusion rule

A topic is flagged as `needs_attention` when:

- `attempts > 2`, and
- `p_know < 0.50`.

The dashboard should surface these topics and provide learning resources before encouraging another attempt.

## 6.4 Initial BKT values

Use the following defaults per user/topic:

- `p_know = 0.10`
- `p_learn = 0.40`
- `p_guess = 0.20`
- `p_slip = 0.10`
- mastery threshold = `0.95`

Do not randomly change these values per request.

---

# 7. Core User Stories

## Authentication

### US-01 Register

As a new learner, I want to create an account so that my learning state is saved.

**Acceptance criteria**

- username required,
- valid email required,
- password required,
- duplicate email rejected,
- password stored only as bcrypt hash,
- successful registration returns an authenticated session/JWT,
- user is redirected to onboarding.

### US-02 Login

As a returning learner, I want to log in and continue where I stopped.

**Acceptance criteria**

- valid credentials return JWT,
- invalid credentials show a clear error,
- protected pages redirect unauthenticated users to `/login`,
- expired/invalid JWT clears local auth and redirects to `/login`.

---

# 8. Onboarding

### US-03 Choose domain

The MVP includes **Web Development** as the fully implemented domain.

The architecture may support more domains later, but no fake/empty domain should be shown as selectable.

### US-04 Mark known topics

User sees the domain's topics and selects topics they already know.

**Behavior**

- selected topics are marked `completed`,
- selected topics receive an initial onboarding mastery value defined in architecture,
- backend recalculates the user's unlocked frontier,
- user is sent to dashboard.

**UX requirement**

Onboarding must explain: "Choose topics you already feel comfortable with. AdaptLearn will skip them and start from the right place."

---

# 9. Dashboard Requirements

The dashboard is the learner's home screen.

It must include:

1. welcome header,
2. overall progress,
3. completed topics count,
4. mastered topics count,
5. average mastery,
6. total quiz attempts,
7. next 3 recommended topics,
8. topics needing attention,
9. recent quiz attempts,
10. compact mastery overview.

### Recommended topic cards

Each card must show:

- topic name,
- short description,
- difficulty,
- current status,
- mastery percentage,
- prerequisite summary,
- primary action: `Start Topic` / `Continue` / `Retry Quiz`.

No locked topic should appear as a primary recommendation.

---

# 10. Learning Path Requirements

The learning path is derived from Neo4j prerequisite relationships.

A topic is learnable only when **all of its prerequisites are completed** for the current user.

Recommended topics:

- must exclude completed topics,
- must exclude locked topics,
- should be ordered by difficulty ascending,
- return the first 3 learnable topics for the dashboard.

If no topics remain, show a curriculum-complete state.

---

# 11. Quiz Requirements

## 11.1 Generate quiz

When the user starts a topic:

1. frontend requests a quiz from backend,
2. backend validates that topic exists,
3. backend checks that topic is unlocked/completed for the user,
4. backend asks Groq to generate exactly 3 MCQs,
5. backend validates returned JSON,
6. backend stores the answer key server-side,
7. frontend receives only safe question data.

### Frontend question payload MUST NOT include

- correct option index,
- answer key,
- hidden system prompt.

## 11.2 Submit quiz

On submission:

1. verify quiz session belongs to current user,
2. compare answers server-side,
3. calculate score,
4. update BKT sequentially for all 3 answers,
5. increment attempt/correct counters,
6. create quiz history record,
7. set topic `completed` if score >= 2,
8. recalculate unlocked topics,
9. detect confusion state,
10. return result and explanations.

## 11.3 Quiz result

Result view must show:

- score out of 3,
- passed/needs retry message,
- old mastery → new mastery,
- mastery percentage,
- per-question correctness,
- explanation for each answer,
- recommended resources if failed/needs attention,
- next action.

---

# 12. AI Quiz Generation Requirements

Provider: **Groq**  
Model target from the project guide: `llama3-8b-8192`

If the exact model is unavailable in the connected Groq account, configure the model name through an environment variable rather than changing application logic.

## Required output schema

```json
{
  "questions": [
    {
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "correct": 0,
      "explanation": "..."
    }
  ]
}
```

Validation rules:

- exactly 3 questions,
- exactly 4 options each,
- `correct` must be integer `0..3`,
- all strings non-empty,
- duplicate questions rejected when practical,
- invalid JSON triggers retry,
- after retry exhaustion, use fallback questions.

### LLM failure behavior

The user must still be able to take a quiz if Groq is unavailable.

Backend therefore needs a small curated fallback question set for seeded topics or a generic safe fallback strategy.

---

# 13. Knowledge Graph Requirements

Route: `/graph`

The graph must display:

- all Web Development topic nodes,
- prerequisite links,
- directional arrows,
- topic labels,
- status-based colors,
- status-based node size,
- click-to-open topic details.

Clicking a node opens a detail side panel showing:

- topic name,
- description,
- difficulty,
- status,
- mastery,
- prerequisites,
- learning resources,
- action button if the topic is available.

Locked topics must not allow quiz start.

---

# 14. Resource Recommendation Requirements

Each topic node should contain at least 1–3 curated learning resources.

At minimum, store:

- title,
- URL,
- resource type (`docs`, `video`, `article`).

Resources should appear when:

- a quiz is failed,
- the topic is flagged `needs_attention`,
- the user opens topic details.

---

# 15. Seed Curriculum — Web Development

This 30-topic curriculum is an **implementation design decision** to make the build deterministic and complete.

1. HTML Basics
2. Semantic HTML
3. Forms & Accessibility
4. CSS Basics
5. Flexbox
6. CSS Grid
7. Responsive Design
8. JavaScript Fundamentals
9. Functions & Scope
10. Arrays & Objects
11. DOM Manipulation
12. Browser Events
13. Async JavaScript
14. Fetch & HTTP APIs
15. ES Modules
16. Git Basics
17. Node.js Basics
18. npm & Packages
19. Express.js Basics
20. REST API Design
21. Authentication Basics
22. SQL Basics
23. PostgreSQL Basics
24. React Fundamentals
25. Props & State
26. React Hooks
27. React Router
28. API Integration in React
29. Testing Basics
30. Deployment Basics

The exact prerequisite edges are specified in `ARCHITECTURE.md`.

---

# 16. Navigation / Routes

Public routes:

- `/login`
- `/register`

Protected routes:

- `/onboarding`
- `/dashboard`
- `/quiz/:topicId`
- `/graph`

Optional convenience route:

- `/` → redirect to `/dashboard` if authenticated, else `/login`

Unknown route:

- render a simple 404 page with link back to dashboard/login.

---

# 17. API Surface

The detailed contracts are in `ARCHITECTURE.md`.

Required groups:

### Auth

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Topics

- `GET /api/topics/all`
- `GET /api/topics/graph`
- `GET /api/topics/learning-path`
- `POST /api/topics/mark-known`

### Quiz

- `GET /api/quiz/generate/{topic_id}`
- `POST /api/quiz/submit`

### Progress

- `GET /api/progress/dashboard`
- `GET /api/progress/all`

### Health

- `GET /`
- `GET /api/health`

---

# 18. Data Ownership Rules

- Neo4j stores curriculum topology and topic metadata.
- PostgreSQL stores user-specific state and history.
- PostgreSQL references Neo4j topics using the topic's string `topic_id`.
- Never duplicate the full curriculum graph per user.
- Never store user passwords in Neo4j.
- Never store user-specific quiz history in Neo4j.

---

# 19. Security Requirements

MVP requirements:

- bcrypt password hashing,
- JWT signed using secret environment variable,
- protected FastAPI dependencies,
- user-scoped queries on every progress/history endpoint,
- parameterized SQLAlchemy queries,
- parameterized Neo4j queries,
- CORS restricted to configured frontend origin,
- no secrets committed to Git,
- `.env.example` must contain names, not real secrets,
- correct quiz answers never sent before submission,
- basic auth and quiz rate limits are recommended before public deployment.

The reference project uses JWT in `localStorage`. Keep that behavior for parity with the guide, but document that production-hardening should move tokens to secure HttpOnly cookies.

---

# 20. Reliability and Error Handling

Every API error must use a consistent response shape:

```json
{
  "detail": "Human-readable message"
}
```

Frontend must handle:

- 400 validation/business errors,
- 401 session expiry,
- 403 locked topic,
- 404 missing topic/quiz,
- 409 duplicate email,
- 422 FastAPI validation,
- 429 rate limiting if enabled,
- 500 backend failure,
- 503 Groq/DB service problem.

All async buttons must disable while submitting to avoid duplicate requests.

---

# 21. Performance Expectations

For MVP/local use:

- ordinary API requests should feel immediate,
- graph rendering should remain smooth for 30 nodes,
- dashboard should load with a single aggregated progress request plus curriculum/recommendation data,
- quiz generation can take ~1–3 seconds; UI must show a purposeful loader,
- do not block the UI without feedback.

---

# 22. Testing Requirements

Minimum backend tests:

- password hashing/login,
- JWT protected endpoint behavior,
- BKT correct-answer update,
- BKT wrong-answer update,
- mastery threshold,
- learning-path prerequisite logic,
- mark-known behavior,
- quiz JSON validation,
- quiz submission ownership,
- confusion detection.

Minimum frontend tests/manual verification:

- protected route redirect,
- onboarding selection,
- dashboard loading/error/empty states,
- quiz selection and submit states,
- graph node click panel,
- logout.

---

# 23. Deployment Target

Recommended deployment matching the guide:

- Frontend: **Vercel**
- FastAPI backend: **Railway**
- PostgreSQL: **Neon**
- Neo4j: **Neo4j Aura**
- LLM: **Groq API**

Local development:

- React/Vite: `5173`
- FastAPI/Uvicorn: `8000`
- PostgreSQL: `5432`
- Neo4j Bolt: `7687`
- Neo4j Browser: `7474`

---

# 24. Final Definition of Done

The project is finished only when:

- [ ] all required routes exist,
- [ ] frontend and backend run from clean setup instructions,
- [ ] PostgreSQL and Neo4j initialize correctly,
- [ ] 30 curriculum nodes and prerequisite edges are seeded idempotently,
- [ ] register/login works,
- [ ] protected routes work,
- [ ] onboarding changes the user's starting path,
- [ ] dashboard is fully data-driven,
- [ ] next 3 recommendations are prerequisite-aware,
- [ ] quizzes are generated or fall back gracefully,
- [ ] correct answers are not exposed before submit,
- [ ] BKT updates per answer,
- [ ] quiz history persists,
- [ ] pass state updates prerequisites,
- [ ] confusion detection works,
- [ ] graph is interactive and status-colored,
- [ ] loading/error/empty states exist,
- [ ] backend tests pass,
- [ ] no secrets are committed,
- [ ] `README.md` contains setup and deployment instructions,
- [ ] `.env.example` is complete.

---

# 25. Future Scope

After MVP stability:

- multiple learning domains,
- instructor/admin authoring portal,
- question difficulty calibration,
- Item Response Theory,
- spaced repetition,
- forgetting/decay model,
- Deep Knowledge Tracing,
- Redis caching,
- Celery/background quiz generation,
- refresh-token + HttpOnly-cookie auth,
- richer analytics,
- adaptive resource ranking,
- coding questions with sandboxed execution,
- AI tutor/chat over curriculum context.
