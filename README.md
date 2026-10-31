# AdaptLearn

An adaptive learning platform that builds a personalised learning path instead of pushing every learner through the same fixed sequence.

- **Neo4j knowledge graph** - topics and their prerequisites decide what a learner can study next.
- **Bayesian Knowledge Tracing (BKT)** - a per-user, per-topic mastery probability updated after every quiz answer.
- **Groq LLM** - generates fresh 3-question multiple-choice quizzes, with a curated fallback bank.
- **PostgreSQL** - users, progress, quiz sessions and attempt history.
- **React** - sign-in, onboarding, a dashboard, proctored quizzes and an interactive knowledge graph.

The curriculum is organised into **domains** that share one pool of topics: **Foundations** (10 topics: how computers work and store data, programming ideas, the terminal and operating system, Git, data formats, the internet and security basics), **Web Development** (30 topics, sharing Git Basics with Foundations) and **Python** (20 topics, three of them building on Foundations). Learners join whichever domains they like and onboard in each; a home endpoint brings their progress across joined domains together. More domains are planned (see [PROJECT-STATE.md](PROJECT-STATE.md)).

AdaptLearn is complete for local use and runs on localhost (Docker for the databases, see **Local development**); it is not deployed. See [PROJECT-STATE.md](PROJECT-STATE.md) for current progress. The specification documents (PRD, architecture and roadmap) are kept privately and are not part of this repository.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite + Tailwind CSS v4 + shadcn/ui (Radix), React Router, Axios, react-force-graph-2d |
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

**Routes.** `/login` and `/register` are for signed-out visitors. Everything else needs a session: `/` (decides where to land), `/home`, `/domains` (the catalogue), and for each domain `/domains/:domainId` (its dashboard), `/domains/:domainId/graph` and `/domains/:domainId/onboarding`, plus `/map` (every domain on one graph) and `/quiz/:topicId`. The addresses from before there were several domains still work: `/dashboard` opens `/home`, `/onboarding` opens `/domains` and `/graph` opens `/map` (keeping `?topic=`). Without a session the learner goes to `/login`, and the page they wanted is remembered for after signing in (except after choosing to log out, so the next person on a shared computer starts fresh). Unknown paths show a 404 page, and a page that crashes shows an error screen instead of a blank page.

**Signing in.** The register form asks for a username, email, password and password confirmation (there is no password reset yet, so a typo would lock the account); the login form for email and password. Both check the backend's rules before sending (username up to 80 characters, a valid email, password 8 characters to 72 bytes), show each problem next to its field, and show server answers in plain language: "Incorrect email or password", "An account with this email already exists" on the email field, or "Can't reach the AdaptLearn server". After signing in the learner goes to the remembered page if there is one; otherwise to the catalogue (`/domains`) until they have joined a domain (always the case for a new account) and to `/home` after that, decided by `GET /api/home`.

**Navigation.** The navbar has **Home**, **Domains** (marked on every domain's own pages too) and **Full map**; the logo goes home. Each domain's dashboard and graph have a **domain switcher**: a menu of the learner's joined domains with their progress, which keeps the same view (dashboard or graph), plus a link to the catalogue. A link to a domain that doesn't exist shows "We couldn't find that domain" with a way to the catalogue.

**Home** (`/home`). Everything the learner is studying, from one call (`GET /api/home`): a card per joined domain with its progress and next topic (or **Finish setting up** for a domain not onboarded yet, or "Every topic completed"); **Up next**, the next topics across domains, each saying which domains it counts towards when there are several (a shared topic appears once), with the same Start / Continue / Retry actions as the dashboard; **Suggested for you**, domains not joined yet where the learner already has a head start (topics completed through other domains, and topics those opened), each with a **Join** button; and **Recent quizzes** from any domain. A learner with no domain is invited to choose one.

**Domains** (`/domains`). The catalogue from `GET /api/domains`: every domain with what it covers, its size, the learner's progress there and a badge (Joined, Head start or Completed). A domain not joined shows the head start and offers **Join** and **Preview topics** (its knowledge graph); joining (`POST /api/domains/{id}/join`) opens that domain's onboarding, or its dashboard if it was already set up. A joined domain offers **Open**, or **Finish setting up** before onboarding. While a join is in flight every Join button waits, and a failure is shown on that domain's card.

**Onboarding** (`/domains/:domainId/onboarding`). One domain at a time. Shows the domain and the PRD's explanation, then the domain's topics (including those it shares) from `GET /api/topics/map`, grouped by difficulty (Beginner, Intermediate, Advanced, Expert). Ticking a topic also ticks everything it depends on, marked "Included: needed for ...", because the server marks prerequisites of known topics as known too; prerequisites from other domains have no card here, so they are listed under **Included from other domains** with their domain. The live counter ("7 topics selected (5 included as prerequisites)") therefore matches what will be saved. Topics already completed, here or through another domain, are shown ticked. Saving sends only the explicit choices to `POST /api/topics/mark-known` for this domain and opens its dashboard with a confirmation; saving with nothing ticked still saves, because it records that the domain has been set up. Loading shows a skeleton, a failed load offers a retry, and a failed save keeps the selection.

**Dashboard** (`/domains/:domainId`). One domain's dashboard, named after it, from one call (`GET /api/progress/dashboard?domain=...`); nothing on the page is hard-coded. It shows: stat cards for overall progress, completed topics (and how many are in progress), mastered topics (95% or more), average mastery and quiz attempts (noting flagged ones that didn't count); **Up next**, the three recommended topics with difficulty, status, description, prerequisites ("Builds on ..."), mastery and one action (**Start topic** for an unlocked topic, **Continue** for one in progress, **Retry quiz** when the latest counted quiz on it failed or it needs attention); **Needs attention**, topics with more than 2 attempts and under 50% mastery, listing their resources before a retry; **Recent quizzes**, the last five with score, result, mastery before and after, and a "Flagged, didn't count" badge for attempts that failed the integrity check; and **Mastery**, a compact bar per reachable topic with locked topics behind a toggle. It also covers a domain not set up yet (a prompt to choose known topics in it), the curriculum-complete state (with links to the graph and the catalogue), loading, and errors with a retry. Quiz counts and recent quizzes cover this domain's topics.

**Quiz** (`/quiz/:topicId`). The proctored quiz in the browser. The page first shows the topic and how the quiz works (a locked topic explains which prerequisites to finish; an unfinished quiz on another topic is flagged, since starting abandons it). **Prepare quiz** calls `GET /quiz/generate/{topic_id}` and shows the server's integrity rules, the time per question and a notice when some or all questions come from the curated fallback bank. **Enter fullscreen and start** serves one question at a time (`POST /quiz/{id}/next`) with the server's countdown; the learner picks an option and **locks it in** (`POST /quiz/{id}/answer`), which is possible after a 3-second reading time (faster answers are penalised). When time runs out, a selected answer is sent; otherwise the question times out and the page moves on. While the quiz runs, the navbar is hidden and the page sends a heartbeat every 5 s plus tab switches, window switches, leaving fullscreen, copy/cut/paste and right-click (all blocked) and a second screen (`screen.isExtended`) to `POST /quiz/{id}/events`; each recorded event is shown to the learner with its penalty, and leaving fullscreen offers a way back. The back button asks before leaving and a reload warns first; reopening the page resumes the quiz with its timer intact (`GET /quiz/active`). The result shows the score, pass or retry, mastery before and after, the integrity verdict with its reasons (a flagged attempt didn't count and changed nothing), newly unlocked topics, resources after a failed quiz, every answer with its explanation, and what to learn next. Code in AI questions is shown as code blocks, and maths is drawn with KaTeX (with MathML for screen readers); KaTeX is only downloaded when a question contains maths. The topic can be from any domain (the page reads `GET /api/topics/map`), and the way back leads to the page the quiz was opened from: "Back to dashboard", "Back to the knowledge graph" or "Back to home", kept when moving on to the next topic from the result. Errors are handled: 403 locked, 429 with a countdown from `Retry-After`, 503, expired (410) and already-submitted (409) quizzes, and network failures with a retry.

**Knowledge graph** (`/domains/:domainId/graph`). A domain's topics from `GET /api/topics/graph?domain=...`, drawn on a canvas with `react-force-graph-2d` and laid out left to right by prerequisite depth, with arrows from each prerequisite to the topic it unlocks. Each status has its palette colour and its own mark, so states don't rely on colour alone: completed (teal, tick), in progress (amber, with a mastery arc), unlocked (mint, outlined) and locked (slate, padlock); a legend gives the counts. Drag to pan, scroll or pinch to zoom, or use the zoom and fit buttons; on a narrow screen the first view starts at a readable zoom on the starting topics. Selecting a topic fades unrelated ones, highlights its links, and opens a side panel with its status, difficulty, description, mastery, a lock-aware action (Start topic / Continue / Practise again, or which prerequisites to complete first), clickable prerequisites and unlocks, the other domains a shared topic belongs to, and resources. A prerequisite from another domain isn't a node here: the panel lists it with its domain and whether it is done, linking to it in that domain's graph, and the locked message names it ("Complete Command Line Basics (Foundations) to unlock it."). The selection is kept in the URL (`?topic=react_hooks`), Escape or a click on the background closes it. A **List** view shows the same topics as text, grouped by status, for keyboard and screen-reader users. The graph library is loaded only on the graph pages.

**Full map** (`/map`). Every topic in every domain on one graph, from `GET /api/topics/map`, with every prerequisite drawn, across domains too. Topics are grouped by the domain that defines them: each domain has its own band, drawn as a shaded area named in its corner, and every topic is fixed to its own row there (columns follow prerequisite depth), so a prerequisite in a distant domain never pulls it out of its band; and when zoomed out (where topic labels are hidden) the domain names are drawn large, so the map reads as its domains. The panel lists every domain a topic belongs to, each linking to that domain's graph, and the List view names each topic's domain.

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

All need a Bearer token. `all` and `graph` take an optional `?domain=` (`web-development`, the default, or `foundations`; anything else is `404`); a domain includes the topics it shares from other domains.

| Endpoint | Returns |
|---|---|
| `GET /api/topics/all` | `{domain, topics}`: every topic with `id`, `name`, `description`, `difficulty` and `resources` (`[{title, url, type}]`), ordered by difficulty then name |
| `GET /api/topics/graph` | `{domain, domain_name, domains, nodes, links}` for a domain's knowledge graph (`domains` lists every domain's `{id, name}`, to name the others). Each node adds the current user's `status`, `mastery` (percentage), `mastered` (`p_know >= 0.95`), `prerequisites` (ids of prerequisites in this domain), `external_prerequisites` (`[{id, name, domain, domain_name, completed}]` for prerequisites from other domains, `completed` saying whether the learner has done it), `domains` (every domain the topic belongs to) and `home_domain` (the one that defines it). Each link is `{source, target}`, pointing from a prerequisite to the topic it unlocks, between topics of this domain |
| `GET /api/topics/map` | `{domains, nodes, links}`: the whole map. Every topic in every domain once, easiest first, with the same node fields; since every topic is a node, every prerequisite (across domains too) is a link and `external_prerequisites` is always empty |

#### Learning path: `GET /api/topics/learning-path`

Returns `{domain, onboarded, curriculum_complete, recommended}`. `recommended` holds at most 3 learnable topics from the domain: not completed, every prerequisite completed (including prerequisites from other domains), ordered by difficulty then name. Topics already in progress are included with status `in_progress`.

- **`onboarded` is per domain:** `false` until the learner has been through this domain's onboarding (`POST /api/topics/mark-known` for it). The frontend uses this to send the learner to onboarding.
- **A learner with no progress at all:** the starting topics are returned and nothing is written.
- **Otherwise** (onboarded here or in another domain): statuses are synced first, so any topic that has become learnable is stored as `unlocked`. A missing row for a learnable topic is recreated, and completed or in-progress topics are never changed.
- **Everything completed:** `curriculum_complete` is `true` (every topic in the domain is completed) and `recommended` is empty. An empty `recommended` alone isn't enough: a topic can still be waiting on a prerequisite from another domain.

The same user state always gives the same answer.

#### Onboarding: `POST /api/topics/mark-known`

Body: `{"domain": "web-development", "topic_ids": ["html_basics", "css_basics"]}` (`topic_ids` may be empty; up to 100 ids). Onboarding is per domain: the topics must belong to that domain, and saving joins the domain if needed and records that the learner has onboarded there (the first date is kept if they onboard again).

1. Every id is checked first. Any unknown id rejects the whole request with `400 {"detail": "Unknown topic ids: ..."}` and nothing is written.
2. A known topic implies its prerequisites, so every ancestor of a selected topic (found with a variable-length Neo4j path query) is marked known too.
3. The user gets one `topic_progress` row per topic (created with `INSERT ... ON CONFLICT DO NOTHING`, so a double submit is harmless).
4. Known topics become `completed` with `p_know` of at least 0.95.
5. Every topic whose prerequisites are all completed becomes `unlocked`; the rest stay `locked`.

Response: `{message, known_count, added_prerequisites, recommended}`, where `recommended` holds the next 3 learnable topics (easiest first), each with `id`, `name`, `description`, `difficulty`, `status`, `mastery`, `prerequisites` and `prerequisite_names`.

Calling it again only adds knowledge: completed topics are never relocked, mastery is never lowered, and topics already in progress keep that status.

A topic's status and mastery come from the user's `topic_progress` row. For a topic without a row yet (for example before onboarding), status is derived from the graph: `unlocked` when every prerequisite is completed, otherwise `locked`, with the starting mastery of 10%. A domain's topics are read in one Neo4j query, so there are no per-topic lookups.

### Domains and home

All three need a Bearer token.

| Endpoint | Returns |
|---|---|
| `GET /api/domains` | `{domains}`: the catalogue, every domain in curriculum order (see below) |
| `POST /api/domains/{domain_id}/join` | `201 {domain, domain_name, joined_at, onboarded}` when joined now; `200` with the same body if already joined (nothing changes); `404` for an unknown domain |
| `GET /api/home` | `{domains, up_next, suggestions, recent_attempts}`: the learner's home page in one call (see below) |

Joining only records interest: no domain has priority, learners join any in any order, and joining never changes a topic's status. Onboarding then records what the learner already knows there.

Each catalogue entry describes a domain and the learner's standing in it: `id`, `name`, `description`, `total_topics`, `completed_topics`, `in_progress_topics`, `available_topics` (learnable now), `progress_percent`, `curriculum_complete`, `joined`, `joined_at`, `onboarded`, `known_topics` (its completed topics), `ready_topics` (learnable topics that have prerequisites, i.e. opened by what the learner has already done) and `suggested`. Progress belongs to topics, so the numbers include topics completed through other domains: that is a learner's **head start**. A domain is `suggested` when it isn't joined and the learner has a head start there (a known or ready topic).

The home response:

| Field | Contents |
|---|---|
| `domains` | The joined domains, in the order they were joined, each a catalogue entry plus `up_next` (its next topic, or `null` before onboarding there or once it is complete) |
| `up_next` | The next 3 topics across the domains the learner has onboarded in, easiest first, each with `domains` (which of those domains it counts towards); a shared topic appears once |
| `suggestions` | Up to 3 suggested domains, the biggest head start (known + ready topics as a share of the domain) first |
| `recent_attempts` | The latest 5 quizzes in any domain, the same shape as the dashboard's |

Both read the curriculum and the learner's frontier once, so each makes two Neo4j calls however many domains there are (tests enforce this). Neither writes anything for a learner with no progress yet.

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
| `403` | Generate: the topic is still locked for this user. The message names the unfinished prerequisites, with the domain for one from another domain, for example "Topic is still locked. Complete its prerequisites first: HTML Basics, Command Line Basics (Foundations)." |
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

1. **Groq** is asked for exactly 3 multiple-choice questions in JSON mode, with the topic's name, description, difficulty and home domain in the prompt, preferring applied scenario or code questions over definitions that can be looked up quickly. Maths is written in LaTeX between `\(` and `\)` (inline) or `\[` and `\]` (on its own line). Topics in some domains get extra rules: a cybersecurity topic's questions must stay conceptual and defensive (how attacks work, how to recognise, prevent and respond to them; never working exploits, payloads or intrusion steps).
2. The output is validated: valid JSON (accidental code fences stripped), exactly 3 distinct questions, exactly 4 distinct non-empty options each (letter case counts, so `DataScience` and `datascience` are different answers, but runs of spaces don't, because the page shows them as one), `correct` a real integer 0-3, a non-empty explanation, maths delimiters that pair up outside code, and no line break written as a literal `\n` outside code and maths in the question or an option (it would show as `\n`). LaTeX commands whose backslash JSON turned into a control character (`\frac` arriving as a form feed plus "rac", `\times` as a tab plus "imes") are repaired first.
3. **Invalid output is retried** up to 2 more times. That includes Groq's own `400 json_validate_failed`.
4. **The answer check.** A second call (temperature 0, `GROQ_CHECK_REASONING_EFFORT`) gets the questions and options without the key or explanations and answers each one independently, listing every option an expert would accept and whether the question is sound. A question passes only when it is sound and its key is the only correct option; one that fails is replaced from the fallback bank in place (`source: "mixed"`), and if every question fails the quiz comes from the bank. A quiz that can't be checked (no time left, an unusable answer, a Groq error) is never served: it comes from the bank too. Measured on real quizzes, the check reliably catches questions with more than one correct answer, the most common flaw; it can still miss a subtle factual slip, which is why sample quizzes are also reviewed by a person (see [Content](#content)). It adds about 2-3 s and 1,500 tokens per quiz; `QUIZ_ANSWER_CHECK=false` turns it off.
5. **Groq unavailable** (no API key, network error, timeout, auth error, rate limit or 5xx) skips straight to the **fallback bank** ([`seed/questions/`](backend/seed/questions/), one file per domain, gathered by [`seed/fallback_questions.py`](backend/seed/fallback_questions.py): 3 hand-written questions per topic). Each request times out after 10s, and everything (retries and the check) stops after 20s in total; the browser waits up to 25s for this request.
6. **Options are shuffled** for every quiz and the answer index is remapped, so the answer's position reveals nothing and LLM position bias disappears.

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
| `QUIZ_ANSWER_CHECK` | `true` | Check every AI question with a second call before it is served (see "How questions are produced") |
| `GROQ_CHECK_REASONING_EFFORT` | `medium` | Reasoning effort for the answer check. Medium caught questions with two correct options as reliably as high in a comparison, at a third of the time (about 2.5 s instead of 7-10 s) |

### Progress and dashboard

| Endpoint | Returns |
|---|---|
| `GET /api/progress/dashboard` | Everything one domain's dashboard needs in one call (see below), with the domain's `domain` id and `domain_name`; optional `?domain=` as for the topic endpoints |
| `GET /api/progress/all` | `{topics: [{topic_id, status, p_know, attempts, correct, needs_attention}]}`: the learner's raw progress rows, ordered by topic id (empty before onboarding) |

The dashboard response:

| Field | Contents |
|---|---|
| `onboarded`, `curriculum_complete` | Whether to send the learner to this domain's onboarding, or show the curriculum-complete state |
| `stats` | `total_topics`, `completed_topics`, `in_progress_topics`, `mastered_topics` (p_know >= 0.95), `average_mastery` (mean % over the learner's topics; 0 before onboarding), `total_attempts`, `flagged_attempts` (failed the integrity check; didn't count), `progress_percent` (completed / total) |
| `recommended` | The next 3 topics, the same cards as `/api/topics/learning-path` |
| `needs_attention` | Flagged topics with mastery, attempt count and their learning resources |
| `recent_attempts` | The latest 5 quizzes, newest first: topic name, score, pass/fail, mastery before → after, time, and `counted` / `integrity_verdict` / `integrity_score` (null verdict for attempts made before proctoring) |
| `mastery` | Every topic with status, mastery % and mastered flag, easiest first |

Everything is scoped to the domain: attempt counts, needs-attention topics and recent quizzes cover the domain's topics only (a quiz on a shared topic counts in every domain that uses it). Topic names and resources come from a single Neo4j query joined in memory, so the dashboard makes exactly two Neo4j calls (topics + learning path) however much the learner has done. A test enforces this.

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
pytest                                   # the whole suite
pytest --cov=. --cov-report=term-missing  # with line coverage (99% of statements)
python -m ruff check .                   # lint: unused imports, undefined names, likely bugs (ruff.toml)
```

Tests need the Docker PostgreSQL running. They use a separate database, `adaptlearn_test`, which is created automatically and rebuilt on every run, so your development data is never touched. Set `TEST_DATABASE_URL` to use a different test database.

Neo4j Community has only one database, so the seeder tests and the multi-domain tests seed their own throwaway catalogs (`pytest-seed`, `pytest-domains`) and delete them afterwards; the real curriculum is never modified. They are skipped if Neo4j is not running.

Frontend tests run with `npm test` from `frontend/` (lint with `npm run lint`). They fake the HTTP layer, so they need neither the backend nor the databases; any request that would reach a real server fails the test.

**Accessibility.** Every screen was checked in Edge at 360 px, 768 px and 1280 px wide (no sideways scrolling), audited with axe-core against WCAG 2.2 AA and best practices (no violations), and used with the keyboard alone: every control is reachable with Tab and shows a visible focus indicator, and a learner can register, onboard, take a whole quiz, browse the graph and log out without a mouse. The graph canvas itself is visual; its List view gives the same information as text.

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
| `domain_enrolments` | The domains each learner has joined: when they joined and when they first onboarded there |

`create_all()` only creates tables that don't exist yet; it never alters existing ones. One step runs alongside it: when `domain_enrolments` is first created, every existing learner with progress is enrolled in Web Development and marked onboarded there (dated from their first progress row), in the same transaction, so learners from before domains could be joined keep their place. It never runs again. This keeps the MVP setup to a single command, but it means **schema changes need a reset in development**:

```bash
docker exec adaptlearn-postgres psql -U postgres -d adaptlearn -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

Then restart the backend to recreate the tables. (Or `docker compose down -v` to wipe both databases.) Alembic migrations are the planned upgrade once real user data needs to survive schema changes.

If PostgreSQL is down when the backend starts, tables are not created - restart the backend once the database is up.

### Curriculum graph (Neo4j)

Each domain has its own file in [`backend/seed/domains/`](backend/seed/domains/), and [`backend/seed/curriculum.py`](backend/seed/curriculum.py) lists them; together they are the single source of truth for the graph.

- **Topics are shared.** A topic (name, description, difficulty 1-4, 1-3 curated resources) is defined once, in its home domain's file; other domains include it by id (`shared=`). Git Basics, for example, lives in Foundations and is shared with Web Development.
- **Prerequisites may cross domains.** An edge is written in the file of the topic it leads to; the prerequisite can come from any domain.
- **Progress belongs to the topic.** Mastering a topic counts in every domain that uses it, and a topic unlocks when all its prerequisites are completed, wherever they live.

| Domain | Topics | Prerequisite edges | Starting topics |
|---|---|---|---|
| Foundations | 10 | 6 | How Computers Work, Programming Concepts, Command Line Basics, Git Basics, How the Internet Works |
| Web Development | 30 (29 of its own plus Git Basics), as specified | 37, as specified | HTML Basics, JavaScript Fundamentals, Git Basics, SQL Basics |
| Python | 20 | 28, three from Foundations (Command Line Basics before virtual environments, Data Formats before files, How the Internet Works before web APIs) | Python Basics |

Nothing outside Web Development is a prerequisite of a Web Development topic, so its starting topics are the ones specified. Git Basics is the one Foundations topic with no link to the others there: making it depend on another Foundations topic would lock it for Web Development learners.

On every backend startup the curriculum is validated (unique domain and topic ids in the right format, each topic defined once, shared topics that exist, edges filed with their topic, no edges to unknown topics, no prerequisite cycles across all domains, valid difficulty and resources) and written to Neo4j as `(:Domain)`, `(:Topic)-[:IN_DOMAIN]->(:Domain)` and `(:Topic)-[:PREREQUISITE_OF]->(:Topic)`:

- everything is `MERGE`d, so repeated startups never create duplicates;
- changed descriptions/resources are updated in place;
- domains, topics, memberships or edges removed from the files are removed from the graph (only within the curriculum's own catalog, so other seeds are never touched);
- everything happens in one transaction, so a failed seed never leaves a half-written graph;
- unique constraints on `Topic.id` and `Domain.id` are created if missing.

To seed by hand (for example against Neo4j Aura), from `backend/` with the venv active:

```bash
python -m seed.seed_graph
```

To see the graph, open the Neo4j Browser at http://localhost:7474 (login `neo4j` / `password123`) and run:

```cypher
MATCH (t:Topic)-[:IN_DOMAIN]->(:Domain {id: 'web-development'})
OPTIONAL MATCH (t)-[r:PREREQUISITE_OF]->(next:Topic)
RETURN t, r, next
```

Arrows point from a prerequisite to the topic it unlocks.

### Content

Content is checked by machine before it ships, and sample AI quizzes are read by a person. From `backend/` with the venv active:

```bash
python -m seed.check_content                       # every domain, offline rules
python -m seed.check_content --online              # also open every link and look up every video
python -m seed.check_content --domain foundations  # one domain (repeat --domain for several)
python -m seed.sample_quizzes --domain foundations # one real AI quiz per topic, written up for review
```

**`check_content`** reports errors (which must be fixed; exit status 1) and warnings (worth a look):

| Area | Errors | Warnings |
|---|---|---|
| Curriculum | Everything the startup validator rejects | - |
| Descriptions | Shorter than 60 or longer than 300 characters, not a sentence ending in a full stop, placeholder text (TODO, TBD, ...), the same description as another topic | - |
| Resources | A link listed twice, a video not on YouTube or Vimeo (or a YouTube/Vimeo link not marked as a video), a YouTube link that isn't a single video | A link used by several topics |
| Fallback questions | Fewer than 3 for a topic, a question failing the same validation as AI questions (including maths delimiters), an all/none-of-the-above option, the same question in two topics, questions for a topic that doesn't exist | The answer is much longer than every wrong option (a giveaway) |
| Prerequisite graph | - | A prerequisite harder than its topic, a prerequisite already implied by another, a topic unconnected in a domain of 4 or more |
| Online (`--online`) | A dead link (404/410) or unreachable site, a video that is removed or private | A site that refuses automated checks (401/403/429), a server error, a link that now redirects to the site's home page, a video that can't be embedded |

Videos are looked up through YouTube's and Vimeo's oEmbed endpoints, which say whether a video exists and may be embedded. Links are opened a few at a time; the whole curriculum takes about 10 seconds.

**`sample_quizzes`** asks Groq for one quiz per topic of a domain, exactly as learners get it, runs the answer check, and writes a Markdown report to `content-review/` (not committed): every question with its options, key, explanation and the check's verdict. It pauses between topics (`--pause`, default 15 s) to stay within Groq's free tier (about 8,000 tokens a minute; a topic costs about 2,500), waits when Groq asks it to, and stops cleanly, keeping what it has, when a daily limit is reached. `--topic` limits it to some topics; `--out` sets the report file.

### Error responses

Every API error returns JSON in the shape `{"detail": "Human-readable message"}`:

| Status | When |
|---|---|
| `404` | Unknown route or resource |
| `422` | Request validation failed; also includes an `errors` list of `{field, message}` |
| `500` | Unexpected server error (details are logged, never sent to the client) |
| `503` | PostgreSQL or Neo4j unavailable |

**When things go wrong.** Each failure has a defined, recoverable outcome, checked end to end in the browser (Phase 19):

| Situation | What the learner sees |
|---|---|
| PostgreSQL down | The server's "Database is temporarily unavailable" message with **Try again**: on any page, at login (what was typed is kept), mid-quiz (the quiz carries on after the retry), or at startup (a branded page with **Try again** and **Log out**; the session is kept). Recovers without restarting the backend |
| Neo4j down | "Curriculum service is temporarily unavailable" with **Try again** on the dashboard, graph and quiz submit (nothing is saved, so retrying is safe). After one failure the backend answers 503 at once for 5 s, then lets one request check whether Neo4j is back, so requests don't pile up past the browser's 15 s timeout |
| Groq slow or down | No retry; after about 10 s the quiz comes from the curated bank, inside the browser's 15 s timeout. After 5 s the page says it is taking longer and explains the fallback |
| Groq returns malformed or wrong-shaped JSON | Retried twice, then the curated bank (under a second) |
| No connection | "Can't reach the AdaptLearn server" with **Try again**; during a quiz the timer keeps running on the server and nothing already locked in is lost |
| Expired login | Back to login with "Your session has expired"; after logging in, the page that was open |
| Locked or unknown topic by URL | What to complete first, or "Topic not found", with a way back |
| Quiz expired, or submitted in another tab | An end screen ("This quiz has expired" / "already submitted") with **Start a new quiz**; the server refuses a second submission (409) |

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
│   ├── models/          # SQLAlchemy models (users, topic_progress, quiz tables, domain_enrolments)
│   ├── schemas/         # Pydantic request/response schemas
│   ├── routers/         # API routes
│   ├── seed/            # Curriculum (one file per domain in domains/, fallback questions per domain in questions/), idempotent Neo4j seeder, content checker, sample-quiz review
│   ├── services/        # Business logic (auth, BKT, quiz, learning path, enrolment, catalogue and home)
│   └── tests/           # pytest suite (runs against adaptlearn_test)
└── frontend/            # React application
    ├── index.html
    ├── vite.config.js   # Vite, Tailwind, @ alias, chunking (React, vendor, graph), Vitest
    ├── components.json  # shadcn/ui settings
    ├── .env.example
    └── src/
        ├── main.jsx, App.jsx, router.jsx   # entry, providers, route table
        ├── index.css    # Tailwind + AdaptLearn palette tokens
        ├── api/         # Axios client (token, 401 handling, error messages) + auth, domains, topics, progress and quiz endpoints
        ├── context/     # AuthProvider (session state)
        ├── hooks/       # useAuth, useForm, useApiData, useJoinDomain, useBackLink, useQuizSession (quiz flow), useProctoring (browser monitoring), useNow
        ├── routes/      # ProtectedRoute, PublicOnlyRoute, PostAuthRedirect, Redirect (old addresses)
        ├── components/
        │   ├── ui/      # shadcn/ui primitives (button, card, badge, alert, input, ...)
        │   ├── common/  # Loader, ErrorState, EmptyState, ProgressBar, PageHeader, SectionHeading
        │   ├── dashboard/   # StatCard, RecommendedTopicCard, AttentionCard, RecentAttempts, MasteryOverview
        │   ├── domains/ # DomainCard, DomainSwitcher, JoinButton, HeadStart, DomainNotFound
        │   ├── home/    # HomeDomainCard, SuggestionCard
        │   ├── forms/   # TextField, PasswordField, FormAlert, SubmitButton
        │   ├── graph/   # KnowledgeGraph (canvas, lazy-loaded), TopicPanel, GraphLegend, TopicList
        │   ├── onboarding/  # TopicOption, SelectionBar
        │   ├── layout/  # AppShell (with focus mode), Navbar, AuthLayout, Logo
        │   ├── quiz/    # QuizIntro, QuizReady, QuizRunner, QuestionCard, QuizResult, QuizEnded, LeaveQuizDialog, QuizText
        │   └── topics/  # TopicStatusBadge, StatusDot, ResourceList, QuizLink (remembers the way back)
        ├── lib/         # validation rules, server-error mapping, topic helpers (difficulty, prerequisites, actions), formatting (incl. code in quiz text), proctoring event reporter, graph layout and drawing (with the map's domain bands), status styles, domain paths and the way back from a quiz, redirect helper
        ├── pages/       # one component per route
        └── test/        # Vitest setup and helpers
```

## Security notes

- Never commit `.env` files; only `.env.example` (names and safe defaults) is tracked.
- JWTs are stored in `localStorage` to match the reference design. For production hardening, move to secure HttpOnly cookies with refresh tokens.
- Login and registration are not rate-limited yet; add rate limiting before a public deployment.
