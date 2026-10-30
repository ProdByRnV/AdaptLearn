# AdaptLearn - Project State

**Last updated:** 2026-10-31
**Current phase:** Phase 24 complete (Multi-domain UI) - Phase 25 (Content verification tooling) up next. Phases 1-20 complete for local use; Phase 21 (deployment) deferred by the owner
**Repository:** https://github.com/ProdByRnV/AdaptLearn

---

## Phase progress

Phases follow the project roadmap (a private specification document, not in this repository). A phase is only ticked once its exit gate has been verified.

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
| 10 | Groq Quiz Generation | Done | `86ffdf0` |
| 11 | Quiz Submission & Progress Update | Done | `fcba616` |
| 12 | Dashboard API | Done | `480dd10` |
| 12.5 | Proctoring - server side (inserted) | Done | `15b0ed6` |
| 13 | React Foundation | Done | `ee21ad1` |
| 14 | Login & Register UI | Done | `a918786` |
| 15 | Onboarding UI | Done | `3c307b8` |
| 16 | Dashboard UI | Done | `14c3783` |
| 17 | Quiz UI | Done | `ed2ec8e` |
| 18 | Knowledge Graph UI | Done | `f96959e` |
| 19 | Error, Loading & Edge Cases | Done | `370c03f` |
| 20 | Testing & Cleanup | Done | `1501ee9` |
| 21 | Deployment Readiness | Deferred (local only); final demo passed locally | `1e3a5e7` |
| 22 | Multi-domain curriculum model | Done | `2dbaec6` |
| 23 | Domain enrolment & multi-domain APIs | Done | `db0165d` |
| 24 | Multi-domain UI | Done | latest |
| 25 | Content verification tooling | Next | - |
| 26-31 | Domain content batches | Planned | - |
| 32 | Multi-domain testing & cleanup | Planned | - |

---

## What exists right now

| Component | State |
|---|---|
| PostgreSQL 15 | Running in Docker on `5432`, database `adaptlearn`, healthy |
| Neo4j 5.26 Community | Running in Docker on `7474` / `7687`, healthy. Holds the curriculum as domains sharing one pool of topics (Phase 22): Foundations (3 topics) and Web Development (30 topics), 32 distinct topics (Git Basics is in both), 33 domain memberships and 37 prerequisite edges, seeded on every backend startup |
| Backend | FastAPI app on `8000`: settings, PostgreSQL + Neo4j connections (Neo4j fails fast during an outage), CORS, consistent errors, JWT auth. Routes: `GET /`, `GET /api/health`, `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`, `GET /api/topics/all`, `GET /api/topics/graph`, `GET /api/topics/map`, `GET /api/topics/learning-path`, `POST /api/topics/mark-known`, `GET /api/domains`, `POST /api/domains/{domain_id}/join`, `GET /api/home`, `GET /api/quiz/generate/{topic_id}`, `GET /api/quiz/active`, `POST /api/quiz/{id}/next`, `POST /api/quiz/{id}/answer`, `POST /api/quiz/{id}/events`, `POST /api/quiz/submit`, `GET /api/progress/dashboard`, `GET /api/progress/all`, Swagger at `/docs` |
| Backend venv | `backend/venv` (Python 3.13.5) with `requirements.txt` installed |
| Backend config | `backend/.env` created locally from `.env.example` with a generated `JWT_SECRET_KEY` (git-ignored) |
| Database tables | `users`, `topic_progress`, `quiz_attempts`, `quiz_sessions`, plus (Phase 12.5) `quiz_responses`, `proctoring_events`, `quiz_integrity` and (Phase 23) `domain_enrolments` - all created automatically on backend startup (`create_all`; new tables were added to the existing dev database without a reset). When `domain_enrolments` was first created, existing learners with progress were enrolled in Web Development as onboarded, in the same transaction (a one-time step) |
| Groq | API key set in `backend/.env`; model `openai/gpt-oss-120b` (reasoning effort low). Live quizzes generate in ~1.7-2.0s; without Groq the curated fallback bank is used |
| Demo account | `demo@adaptlearn.dev` in the local dev database only (password shared outside the repo; not a real credential): onboarded with HTML Basics, then 6 real AI quizzes (CSS 3/3, Git 2/3, JavaScript 1/3, SQL 0/3, 1/3, 0/3), so the dashboard has real data and SQL Basics needs attention. Log in with it in Swagger (`/api/auth/login`, then Authorize). Remove with: `docker exec adaptlearn-postgres psql -U postgres -d adaptlearn -c "delete from users where email='demo@adaptlearn.dev'"` |
| Frontend | `frontend/`: React 19.3 + Vite 8 + Tailwind CSS 4.3 + shadcn/ui (Radix, Nova preset) + React Router 8 + Axios + react-force-graph-2d 1.29 (with d3-force-3d), all versions pinned exactly. Dev server on `5173` (`npm run dev`). Built so far: palette theme, routing with protected/public-only guards, Axios client (Bearer token, session-ending 401 handling, error messages, Retry-After), AuthProvider/useAuth (session restore via `/auth/me`, cross-tab sync), AppShell/Navbar/AuthLayout, shared loaders/error/empty states/progress bar/status badge. Phase 14: working login and register forms (validation matching the backend, server errors on the right field, show/hide password, confirm password) and the post-sign-in redirect (remembered page, else onboarding or dashboard by `onboarded`). Phase 15: onboarding screen (topics by difficulty, prerequisites ticked automatically with an explanation, live counter, returning learners see completed topics, save to `mark-known`, dashboard confirmation). Phase 16: dashboard from `GET /progress/dashboard` (stat cards, Up next with Start/Continue/Retry, Needs attention with resources, recent quizzes with integrity badges, mastery bars, onboarding prompt, curriculum-complete, loading/error). Phase 17: the proctored quiz on `/quiz/:topicId` (intro, server rules, fullscreen, one question at a time with the server countdown, lock-in after a 3 s reading time, timeouts, heartbeats and browser signals with on-screen notices, leave guard, resume, result with integrity verdict, explanations, resources, unlocked topics and next topics; 403/409/410/429/503 handling; code blocks in AI questions). Phase 18: the knowledge graph on `/graph` (canvas laid out by prerequisite depth, arrows, status colours plus marks, legend with counts, zoom/pan/fit, readable start view on phones, side panel with lock-aware action, prerequisites, unlocks and resources, selection in the URL, list view for keyboard and screen readers; the graph library loads only on this page). Phase 24: several domains in the UI: a home page (`/home`: joined domains with progress and next topic, up next across domains, suggested domains with a head start and a Join button, recent quizzes from any domain), the domain catalogue (`/domains`: every domain with its size, progress, badges and head start; Join leads into that domain's onboarding), each domain's dashboard, graph and onboarding under `/domains/:id`, a domain switcher, prerequisites and shared domains as links between graphs, and the full map (`/map`: every topic on one graph, each domain in its own band, named large when zoomed out); quizzes lead back to the page they were opened from; the old addresses redirect |
| Tests | Backend: 527 passing (`pytest` from `backend/`, 99% statement coverage with `pytest --cov=.`, lint with `python -m ruff check .`): 36 auth, 39 curriculum data/validator, 16 Neo4j seeder (isolated `pytest-seed` catalog), 22 multi-domain (isolated `pytest-domains` catalog: shared topics, cross-domain prerequisites, status across domains, domain completion, quizzes, head starts and locked messages across domains, the map), 35 enrolment (joining, per-domain onboarding, catalogue, home, per-domain dashboard, the one-time migration), 25 topics API (including the whole map), 30 onboarding/frontier, 17 learning path, 87 BKT, 133 quiz generation + submission (mostly parametrized), 17 dashboard/progress, 41 proctoring, 4 CORS, 8 Neo4j fail-fast, 17 resilience (health, 503/500 handlers, startup with databases down, deployment settings, the Groq request). Tests never call the real Groq API. PostgreSQL tests use the separate `adaptlearn_test` database. Frontend: 432 passing (`npm test` from `frontend/`): 22 API client, 14 auth provider, 45 routing (landing, navbar, old addresses), 1 crash screen, 22 shared components/helpers, 23 validation and server-error mapping, 14 login page, 12 register page, 19 topic helpers, 13 domain paths and the way back from a quiz, 22 onboarding page, 30 formatting, topic actions and quiz text, 27 dashboard page, 19 home page, 11 domain catalogue, 12 proctoring reporter and browser helpers, 54 quiz page, 38 graph helpers and drawing (including the map's bands), 34 graph and map pages; no backend needed (a guard fails any test that would make a real HTTP request) |

### Start the local environment

```bash
docker compose up -d     # from the project root
docker compose ps        # both services should show "healthy"

cd backend
venv\Scripts\activate    # Windows (macOS/Linux: source venv/bin/activate)
uvicorn main:app --reload --port 8000
# then open http://127.0.0.1:8000/api/health

cd frontend              # second terminal, from the project root
npm install              # first time only
npm run dev              # then open http://localhost:5173
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
8. **Frontend stack:** React 19 + Vite + Tailwind CSS v4 + shadcn/ui (decided 2026-10-26; the spec says React 18). Current shadcn/ui targets React 19 and Tailwind v4, and React 19 is a minor-version change that the PRD's "do not replace React + Vite" rule doesn't forbid.
9. **Colour palette:** the whole UI follows `AdaptLearn.pdf` (local-only design reference, git-ignored). Exact values are in **Design palette** below.
10. **Proctoring:** every quiz is proctored with layer 1 (server-enforced: one question at a time, per-question deadlines, locked answers, rate limits, one active quiz) and layer 2 (browser signals scored by the server). A flagged attempt doesn't count. Webcam/microphone checks (layer 3) are deferred until the owner decides. Decided 2026-10-26.
11. **Multiple domains, shared topics** (decided 2026-10-30): AdaptLearn grows from one domain to many (Foundations, Web Development, App Development, Python, Data Science, AI & ML, Cybersecurity, Blockchain & Web3, Cloud & DevOps, Databases, Computer Science Core, Game Development, UI/UX Design). Topics form one shared pool with one prerequisite graph, and prerequisites may cross domains; a domain is a curated collection of topics, and a topic can belong to several. Progress stays per topic, so a topic mastered in one domain counts in every domain that uses it.
12. **No domain has priority** (2026-10-30): learners join any domains they like, in any order, and can start any topic whose prerequisites are met. Content is built in dependency order (Foundations first, since most domains build on it), not by importance.
13. **Home and navigation** (2026-10-30): a domain catalogue; joining a domain runs onboarding for that domain only (already-known shared topics pre-ticked); a home page showing every joined domain with its progress and "Up next" across them; a dashboard and graph per domain with a domain switcher; prerequisites from other domains shown as links; an optional whole-map view.
14. **Content verified by the assistant, not the owner** (2026-10-30): every link checked live (videos via oEmbed), descriptions and questions checked against authoritative sources, every fallback question passing the quiz validator with one unambiguous answer, sample AI quizzes generated and reviewed for every topic, and the graph checked for cycles and reachability. Cybersecurity content stays conceptual and defensive (enforced in the quiz prompt).

### Working conventions

- All Python runs inside `backend/venv`; nothing is installed into the system Python.
- Each completed phase is committed and pushed with a detailed write-up in the commit message.
- `.env` files are created locally when needed and never committed.
- `AdaptLearn.pdf` (the design reference for the colour palette) stays local and is git-ignored.
- A detailed phase-by-phase record, `SO-FAR.docx`, is kept locally and updated after every phase. It and its generator (`.so-far/`) are git-ignored and never pushed.

---

## Design palette

Extracted exactly from the drawing commands in `AdaptLearn.pdf` (not eyeballed from screenshots). Every value is a Tailwind default colour, so the frontend can use Tailwind classes directly.

| Role | Tailwind | Hex | Used in the PDF for |
|---|---|---|---|
| Ink / dark background | slate-900 | `#0F172A` | Headings, cover background |
| Body text | slate-700 | `#334155` | Paragraph text |
| Muted text, lines | slate-500 | `#64748B` | Captions, footers, graph edges |
| Border | slate-300 | `#CBD5E1` | Card and table borders |
| Subtle border | slate-200 | `#E2E8F0` | Dividers |
| Surface | slate-100 | `#F1F5F9` | Panels, table stripes |
| Card | slate-50 | `#F8FAFC` | Card backgrounds |
| Primary | teal-700 | `#0F766E` | Buttons, headers, chart bars, number badges |
| Primary dark | teal-900 | `#134E4A` | Callout bars, inner boxes |
| Accent light | teal-100 | `#CCFBF1` | Light highlights |
| Accent on dark | teal-200 | `#99F6E4` | Subtitle text on the dark cover |

**Topic status colours** (the cover's legend - these replace the spec's graph colours):

| Status | Tailwind | Hex |
|---|---|---|
| Completed | teal-500 | `#14B8A6` |
| In progress | amber-500 | `#F59E0B` |
| Unlocked | teal-200 | `#99F6E4` |
| Locked | slate-500 | `#64748B` |

Notes for the frontend:

- The only red in the PDF is inside an embedded chart image, so it can't be read exactly. Errors use red-700 `#B91C1C` (Phase 20; red-600 until then): red-600 drops to 4.1:1 on its own light tints, below WCAG AA, while red-700 stays above 4.5:1 on white and on those tints.
- Amber, mint (teal-200) and teal-500 are too light for text on white (contrast below WCAG AA). Use them as fills (graph nodes, badges with dark text) or as text only on the dark slate-900 background, as the PDF's cover does.

## Deviations from the spec

| Spec says | Actual | Why |
|---|---|---|
| Neo4j `5` | Neo4j `5.26-community` (pinned) | Same version in every environment |
| `GROQ_MODEL=llama3-8b-8192` | `openai/gpt-oss-120b` + `GROQ_REASONING_EFFORT=low` | Llama chat models are no longer offered by Groq; gpt-oss-120b gave the most precise questions at ~1-2s (vs gpt-oss-20b 0.9s but vaguer, qwen3.8-27b 1.2s) |
| `frontend/.env.example` in Phase 1 | Added in Phase 13 | UI is being built last |
| `UI.md` required | Not present - ignored for now | UI design to be decided at the frontend stage |
| Graph colours (ARCHITECTURE 19: completed `#0F766E`, in progress `#0EA5E9`, unlocked `#5EEAD4`, locked `#94A3B8`) | `AdaptLearn.pdf` palette: `#14B8A6` / `#F59E0B` / `#99F6E4` / `#64748B` | Owner decision: the whole UI follows the PDF palette |
| React 18 | React 19 (+ Tailwind v4, shadcn/ui) | Current shadcn/ui targets React 19; owner delegated the choice |
| `tailwind.config.js` + `postcss.config.js` (ARCHITECTURE 2) | Neither: Tailwind v4 is configured in CSS (`@theme` in `src/index.css`) and runs through the `@tailwindcss/vite` plugin | Tailwind v4 has no JS config file or PostCSS step by default |
| `components/common/Button.jsx`, `Card.jsx` | shadcn/ui `components/ui/button.jsx`, `card.jsx` (plus badge, alert, input, label, progress, skeleton, separator, dropdown-menu) | Decision 8; the spec's own Loader, ErrorState, EmptyState and ProgressBar are built in `components/common/` on top of them |
| `hooks/useAuth.jsx` holding the context | `context/AuthProvider.jsx` + `context/auth-context.js` + `hooks/useAuth.js` | React Fast Refresh needs component files to export only components |
| Response interceptor: "on 401 clear auth and redirect to login" | Only a 401 for a request that carried the **current** token ends the session; it then redirects through the router with a "session expired" message and remembers the page | A wrong password also returns 401 and must not log anyone out; a late 401 for an old token must not end a new session |
| Boot: "if 401 clear token" | Also: if `/auth/me` fails for another reason (server down), keep the token and show a retry | Not logging people out just because the API was briefly unreachable |
| - | Cross-tab session sync (`storage` event), `/` redirects to the dashboard, signed-in users are sent away from `/login`/`/register`, route error screen | Expected app behaviour the spec doesn't list |
| `VITE_API_URL=http://localhost:8000/api` | Default `http://127.0.0.1:8000/api` | Same reason as the database hosts: avoids the IPv6 `localhost` detour on Windows |
| CORS exposes no headers | `expose_headers=["Retry-After"]` | Browsers hide response headers from cross-origin pages; the quiz page needs Retry-After from 429s |
| Font not specified (the PDF's font names aren't readable) | Geist Variable, self-hosted via `@fontsource-variable/geist` (shadcn Nova preset) | No external font requests; neutral sans that matches the PDF's clean style |
| Phase 14: "build exactly according to `UI.md`" | `UI.md` doesn't exist; the forms follow the palette and the Phase 13 auth layout | Owner said to ignore the missing UI.md |
| Register fields: username, email, password (US-01) | Adds a "Confirm password" field (client-only, not sent) and show/hide toggles on password fields | No password reset exists, so a typo would lock the learner out |
| `/` → `/dashboard` if authenticated (PRD 16) | `/` and sign-in go to the catalogue (`/domains`) until the learner has joined a domain, then `/home` (Phase 24; before that `/onboarding`, then `/dashboard`) | With several domains a new account first chooses what to learn; joining leads straight into that domain's onboarding (US-01) |
| Redirect after login unspecified beyond US-02 | Back to the page that required login; never after a voluntary logout | Convenience, without sending the next person on a shared computer to the previous learner's page |
| Onboarding grid source unspecified (ROADMAP: "known-topic selectable grid") | `GET /topics/graph` instead of `/topics/all` (since Phase 24 `GET /topics/map`, showing the domain's topics); topics grouped by difficulty | The graph includes prerequisites and status, so the screen can tick prerequisites as the server will and show completed topics |
| Selected counter | Counts explicit choices plus the prerequisites they bring along, and says how many are prerequisites | Agreed decision 3: the count matches what the server saves |
| "User is sent to dashboard" (US-04) | Sent with a confirmation of how many topics were marked known and which prerequisites were added | The learner sees that onboarding worked |
| Primary action `Start Topic` / `Continue` / `Retry Quiz` (PRD 9) | Start topic = unlocked; Continue = in progress; Retry quiz = latest counted quiz on it failed, or it needs attention; a completed topic would show "Practise again" | The PRD names the labels but not when each applies; flagged attempts are ignored because they didn't count |
| Dashboard elements (PRD 9) | Adds a flagged-attempts note on the attempts card, integrity badges on recent quizzes, and a prompt for learners who haven't onboarded; the mastery list shows reachable topics with locked ones behind a toggle | Proctoring (decision 10) needs to be visible; a 30-row list would bury the topics that matter early on |
| Quiz contract (ARCHITECTURE 13.8 / 13.9): generate returns all 3 questions; submit takes `{quiz_id, answers}` | Generate returns no questions; `POST /quiz/{id}/next` serves one at a time with a deadline, `POST /quiz/{id}/answer` locks each answer, `POST /quiz/{id}/events` takes proctoring signals, `GET /quiz/active` resumes; submit takes only `{quiz_id}` and adds `integrity` | Proctoring (decision 10): a page holding all questions at once could be answered with outside help and no timing control |
| No proctoring in the PRD | Integrity score (start 100, penalties per signal, verified at 80+); flagged attempts saved but change no progress; abandoned quizzes never count | Owner decision |
| Quiz UI "previous/next navigation" and "submit confirmation" (ROADMAP Phase 17) | No going back; each answer has an explicit **Lock in** step instead of a final confirmation, and the last one reads "Lock in and finish" | Proctoring (decision 10): the server locks answers and never reopens an earlier question, so back navigation can't exist; confirming each answer replaces confirming the whole quiz |
| Quiz start | Two steps: **Prepare quiz** (generates, shows the server's rules) then **Enter fullscreen and start**; no quiz is created on page load | Fullscreen needs a fresh click, the rules come from the generate response, and opening the page never abandons an unfinished quiz by accident |
| Knowledge graph (ROADMAP Phase 18) | Adds a List view, clickable prerequisites/unlocks in the panel, the selection in the URL, fading of unrelated topics, and a readable first view on phones instead of fitting the whole graph | The canvas can't be used by keyboard or screen readers; on a phone the whole graph only fits at an unreadable, untappable size |
| Timeouts | When a question's time runs out, an option the learner selected but didn't lock in is sent; otherwise the question times out | Losing a chosen answer to the clock would be harsh; the server still enforces the deadline |
| No generation limits in the PRD | 5 quizzes per topic and 30 overall per user per hour (`429` + `Retry-After`), checked before the AI call | Stops regenerate-until-easy and protects Groq quota |
| Dashboard stats | Adds `flagged_attempts`; recent attempts add `counted`, `integrity_verdict`, `integrity_score` | Learners and the UI can see which attempts counted |
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
| Quiz before onboarding unspecified | The quizzed topic gets a progress row, and so does every topic currently open to the learner; the rest stay derived from the graph (Phase 22; before that, rows for the whole domain) | Phase 11 always has a row to update; a quiz belongs to a topic, not a domain, so there is no single domain to initialise |
| One domain: `Topic.domain` property, `topic_domain` index, queries filtered by domain (ARCHITECTURE 6, 9) | `(:Domain)` nodes and `(:Topic)-[:IN_DOMAIN]->(:Domain)` memberships; topics carry `home_domain` and a seed `catalog`; constraint `domain_id_unique`; the index and property are removed by the seeder | Decision 11: a topic can belong to several domains |
| Frontier and ancestor queries within one domain (ARCHITECTURE 9.3) | Computed over every supported domain; each domain's learning path, graph and dashboard filter the result | A prerequisite in another domain must count, and opening one domain must never lock another domain's topics |
| `curriculum_complete` when the frontier is empty | When every topic in the domain is completed | Within one domain, an empty frontier can also mean a topic is waiting on another domain |
| Git Basics in Web Development | Defined in Foundations and shared with Web Development (same id, so progress is kept) | It is foundational to most domains |
| `onboarded` = the learner has progress rows | Per domain: true once the learner has onboarded in that domain (`domain_enrolments.onboarded_at`) | Several domains, each with its own onboarding; existing learners were migrated as onboarded in Web Development |
| - | `domain_enrolments` table, `GET /api/domains`, `POST /api/domains/{id}/join`, `GET /api/home` | Decision 13 (catalogue, joining, home across domains); joining is idempotent (`201` new, `200` already joined) |
| Dashboard counts every quiz | Attempt counts, needs-attention and recent quizzes cover the domain's topics; `GET /api/home` shows recent quizzes across all | A dashboard belongs to one domain |
| Locked quiz: `403` "Complete its prerequisites first." | The message names the unfinished prerequisites, adding the domain for one from another domain | Learners need to know what to finish, and where |
| Routes `/dashboard`, `/onboarding`, `/graph` (ARCHITECTURE 18) | `/home`, `/domains`, `/domains/:id` (dashboard), `/domains/:id/graph`, `/domains/:id/onboarding`, `/map`; the old addresses redirect (`/dashboard` to `/home`, `/onboarding` to `/domains`, `/graph` to `/map` keeping `?topic=`) | Decision 13: a page per domain, a home page across them and an optional whole map |
| - | `GET /api/topics/map` (every topic once, every prerequisite as a link); graph and dashboard responses add `domain_name`, graph nodes add `home_domain`, the graph adds every domain's `{id, name}` | The whole-map view, quizzes and onboarding need topics and prerequisites from any domain; screens show the API's domain names |
| Onboarding with nothing new chosen goes straight to the dashboard | Always saves (`mark-known` with no topics) | Saving is what records that the domain has been set up |
| Quiz result: "Back to dashboard" | Back to the page the quiz was opened from (a domain's dashboard or graph, the map, or home), kept when moving on to the next topic | With several dashboards, "the dashboard" is ambiguous |
| Quiz "next topics": the learning path's top 3 | The top 3 open topics in the domains the quizzed topic belongs to; "newly unlocked" lists only topics that build on the quizzed topic | Keeps suggestions in context; a topic merely getting its first stored row wasn't unlocked by the quiz |
| Dashboard response (ARCHITECTURE 13.10) | Adds `domain`, `onboarded`, `curriculum_complete`; stats add `in_progress_topics` and `progress_percent`; `needs_attention` items include resources; recent attempts include topic name and mastery before/after; `mastery` lists every topic | One call covers every dashboard element in PRD section 9 (overall progress, attention resources, curriculum-complete state) |
| `average_mastery` "across initialized topic progress" | Mean over the learner's progress rows; 0.0 before onboarding | Literal reading of the spec; avoids showing a made-up 10% for a learner with no data |
| Wrong user's quiz "rejected" (status unspecified) | `404 Quiz not found`, same as an unknown id | Doesn't reveal that another user's quiz id exists |
| Expired / already-submitted status unspecified | `410 Gone` for expired, `409 Conflict` for already submitted | Distinct, standard codes let the UI say "start a new quiz" vs "already submitted" |
| Submit response (ARCHITECTURE 13.9) | Adds `newly_unlocked`; each feedback item adds `options` | UI can celebrate unlocked topics and render the result screen even after a page refresh |
| Concurrency unspecified | Session and progress rows locked with `SELECT ... FOR UPDATE`; whole submission is one transaction | Concurrent double submit verified live: one 200, one 409, one stored attempt; a mid-way failure saves nothing so the quiz can be resubmitted |
| Failing after completion unspecified | A failed retake updates mastery and counters but keeps `completed` | ARCHITECTURE 10: never relock a completed topic |
| Input handling unspecified | Probabilities outside 0..1 (and NaN) raise `ValueError`; a zero denominator (only possible at the extremes) leaves the belief unchanged before the learning step | Bad inputs fail loudly instead of producing silent nonsense; no division by zero |

---

## Open items

- **Proctoring layer 3 (webcam/microphone) deferred:** owner will decide later whether to add it. Layers 1-2 are built.
- **Layer 2 trusts the page to report events:** a modified client could suppress tab/fullscreen/paste events. The server-measured checks (deadlines, answer timing, heartbeat gaps, missing monitoring) still apply, and a client that sends no heartbeats is flagged. Heartbeat gaps can also come from a flaky connection (15 s tolerance).
- **Second-screen detection is Chromium-only:** `screen.isExtended` exists in Chrome and Edge; Firefox and Safari can't tell, so no event is sent there. Fullscreen is unavailable on iPhone Safari; the quiz then continues in the window with a notice (leaving the page is still caught as a tab switch).
- **Reading time mirrors a server constant:** lock-in waits 3 s (`MIN_ANSWER_SECONDS` in `src/lib/proctoring.js`) to match `MIN_PLAUSIBLE_ANSWER_SECONDS`; the API doesn't expose it. Change both together. The quiz format text (3 questions, pass with 2) also mirrors the PRD.
- **AI question quality:** Groq sometimes double-escaped line breaks in code or wrote options like "B" that pointed at choices inside the question. The prompt asks for fenced code and self-contained options; the validator repairs the line breaks and rejects letter-only options (the quiz is then retried or falls back). Phase 22 made the prompt domain-neutral (code blocks tagged with their real language, `text` for output) and added rules for exactly one correct option that satisfies every condition in the question; the validator now also removes empty or comment-only placeholder code blocks.
- **AI answer accuracy (found reviewing live quizzes in Phase 22):** in two rounds of real Groq quizzes on Command Line Basics, How the Internet Works and Git Basics, about 4 of 9 questions had a real flaw: two correct options (`git checkout -b feature` vs `git branch feature && git checkout feature`; `git push origin HEAD` vs `git push origin bugfix`), an answer key contradicting its own explanation (an IP-header arithmetic question), a correct option that ignored a condition in the question, or commands that would fail as written. Prompt wording alone doesn't prevent this. Planned for Phase 25: an automatic answer check (a second model pass answers each question independently; a disagreement with the key or more than one defensible answer rejects the question, which is regenerated or replaced from the fallback bank), weighed against the extra Groq call (about 1-2 s and roughly double the tokens per quiz).
- **BKT calibration (built as specified; now confirmed by tests):** with the PRD's fixed values, `p_know` can't fall below 0.40 after any answer and repeated wrong answers level off at 16/35 ≈ 0.457; the same 2/3 score ends at 0.76 or 0.98 depending on which answer was wrong; one 3/3 quiz takes a new topic to 0.989 (mastered). Seen live in Phase 12: a **failed** 1/3 SQL quiz (wrong, wrong, right) raised mastery from 45.5% to 87.5%, so a learner can see a failed quiz next to a high mastery bar. Knock-on for Phase 11: the confusion rule (`attempts > 2 and p_know < 0.50`) can only fire while a learner keeps getting most answers wrong, because almost any recent correct answer lifts `p_know` above 0.5. Revisit only if it feels wrong in testing.
- **Groq free-tier limits:** 1,000 requests/day and 8,000 tokens/minute (checked live 2026-10-05). A quiz uses about 800 tokens, so roughly 9-10 quizzes per minute across all users before Groq rate-limits; learners then get fallback questions automatically. Fine for development and demos; a paid tier is needed for real traffic.
- **Groq model churn:** Groq has retired two Llama models during this project. If `openai/gpt-oss-120b` is retired, quizzes keep working via the fallback bank (logged as HTTP 4xx); switch `GROQ_MODEL` in `.env` - no code change needed.
- **Fallback bank repeats:** it has exactly 3 questions per topic, so a learner who retakes a topic while Groq is down sees the same questions (options are reshuffled). Adding more questions per topic and sampling 3 would fix this.
- **Expired quiz sessions accumulate:** `quiz_sessions` rows are never deleted. Harmless at MVP scale; a periodic cleanup of expired, unsubmitted sessions would keep the table small.
- **Rate limiting:** quiz generation is now limited per user (Phase 12.5); login/register still have no rate limit. Recommended by the PRD before any public deployment.
- **Spec documents in git history:** PRD/ROADMAP/ARCHITECTURE were untracked on 2026-10-26 but remain readable in the Phase 1 commit (`accb6cd`); the owner chose not to rewrite history.
- **No migrations:** schema changes need the dev reset above. Move to Alembic before any deployment holds real user data.
- **Recommendation ranking (built as specified, worth revisiting):** the spec ranks the frontier by difficulty then name, so easy side topics always come first. In the live check, a learner who marked React Hooks as known was recommended Git Basics, Semantic HTML and Arrays & Objects ahead of React Router, the same top 3 as a learner who only knew HTML/CSS/JS. A track-aware ranking (e.g. prefer topics that unlock what the learner just finished) could be a later enhancement.
- **Resource links can rot:** the original 81 URLs were live on 2026-10-04 and the 5 Foundations links on 2026-10-30 (a Cloudflare page that blocks automated checks was left out). Re-check them before any deployment.
- **Leaving a domain isn't possible:** not in the plan, and the owner hasn't asked for it. Joining only records interest, so leaving would just remove the enrolment (progress stays with the topics); it would be a small addition to the home page or catalogue.
- **Every domain's starting topics get a stored row:** status is computed over all domains, so a learner's rows include other domains' starting topics as `unlocked`. Harmless since Phase 23: the home page shows joined domains only, and each domain's pages show that domain.
- **No prerequisite crosses into Web Development's view yet:** since Phase 24 the screens show one (the topic panel lists it with its domain and links to it there; the map draws it as a link), but the real curriculum has none until the content phases add them.
- **No password reset or change:** not in the PRD. The register form asks for the password twice and has show/hide toggles to limit typos; an account with a forgotten password can only be recreated.
- **JWT in `localStorage`** (as the spec designs it): readable by any script on the page, so an XSS bug would expose the token. Acceptable for the MVP; HttpOnly cookies with refresh tokens are the hardening path (README security notes).
- **The graph canvas is visual only:** screen readers get a text summary and the List view, which has the same detail panel. Zoom and fit buttons work from the keyboard; topics on the canvas can only be picked with a pointer or touch.
- **Graph status colours are read from CSS:** the canvas reads the palette tokens (`--status-*`) at load; a theme change at runtime would need a reload. Only the light theme exists.
- **Graph library size:** `react-force-graph-2d` and its d3 modules are about 60 KB gzipped. They sit in their own chunk, loaded only by the graph page (checked: not requested on the dashboard).
- **A slow AI costs the learner ~11 s:** when Groq doesn't answer, the backend waits for its 10 s request timeout before using the curated bank (no retry). The page explains the wait after 5 s. Lowering `REQUEST_TIMEOUT_SECONDS` would shorten it at the cost of giving up on slow-but-working answers.
- **Neo4j fail-fast window:** for 5 s after a Neo4j failure, every graph request gets an immediate 503 even if Neo4j has just come back; the learner's next **Try again** after that works. A single process holds this state; with several backend workers each has its own.
- **Mid-quiz outages can flag an attempt:** if the connection or the backend is down for more than 15 s during a quiz, heartbeats stop reaching the server and the gap counts against integrity (as designed). The attempt can be retaken.
- **Frontend coverage isn't measured:** the 432 frontend tests and the mutation checks show what is guarded, but there is no line-coverage figure; it would need `@vitest/coverage-v8` (not installed).
- **Unused but specified API routes:** `GET /api/topics/all` and `GET /api/progress/all` aren't called by the frontend; they are in the PRD's API list and covered by tests, so they stay.
- **"Retry quiz" uses the last five attempts:** the dashboard response only carries the latest 5 quizzes, so a failed quiz older than that falls back to "Continue" (topics needing attention always show "Retry quiz"). Accurate enough for the action label; a per-topic `last_passed` field would make it exact.
- **The full map on a phone:** it opens fitted, so on a 360 px screen the domains are readable but the topics are small dots until zoomed in (as intended: the List view gives the same detail as text). With about 250 topics after the content phases, the map's layout and speed need another look (Phase 32).
- **Open menus aren't audited by axe:** with the domain switcher open, Radix hides the rest of the page from assistive technology on purpose, which axe reports as page-level problems; the menu was checked with the keyboard instead (Tab, Enter, arrow keys).
- **Dev auto-reload under the assistant:** `uvicorn --reload` hangs on Windows when started without a console (the reloader can't deliver Ctrl+C to the worker). Doesn't affect running it in a normal terminal; the assistant restarts the server manually instead.

---

## Where it stands

**AdaptLearn is complete for local use.** The backend API (Phases 1-12, proctoring in 12.5), the frontend (Phases 13-18), error and edge-case handling (Phase 19) and testing and cleanup (Phase 20) are done: 427 backend tests (99% coverage) and 335 frontend tests pass, and live browser checks covered every phase.

**Multi-domain curriculum (Phase 22, 2026-10-30):** the curriculum is now domains sharing one pool of topics, with prerequisites that may cross domains and status computed across all of them; Web Development is unchanged for learners, and a starter Foundations domain shares Git Basics with it. The 15-step demo below was re-run against the Phase 22 backend: 36/36.

**Domain enrolment (Phase 23, 2026-10-30):** learners can join any domain and onboard in each; a catalogue shows every domain with its size and the learner's head start there (topics completed through other domains, and topics they have opened), suggesting domains they are partly ready for; a home endpoint brings progress, up next and recent quizzes across joined domains together; each domain's dashboard covers its own quizzes; and a locked quiz names the prerequisites to finish, including their domain. API only: the screens come in Phase 24. The 15-step demo was re-run against the Phase 23 backend: 36/36.

**Multi-domain UI (Phase 24, 2026-10-31):** the screens now cover several domains: new learners choose a domain from the catalogue and go straight into its onboarding; a home page brings every joined domain together with up next across them and suggestions where they already have a head start; each domain has its own dashboard, graph and onboarding, with a switcher between domains; prerequisites from other domains and the other domains of a shared topic link between graphs; and the full map shows every topic grouped by domain. The demo was extended to the cross-domain journey (register, choose Web Development, onboard, quizzes, graph, a Foundations suggestion, joining it with Git Basics already ticked, switching domains, home across both, the map, old addresses and refreshes): 67/67 on the dev server and the production build. Every new screen fits 360, 768 and 1280 px and has no axe violations.

**Final demo, run locally (2026-10-30):** the roadmap's 15-step demo script was run through the UI in Edge with real Groq quizzes, against both the dev server and the production build (`vite build` served by `vite preview`): open the login screen, register, onboard with known topics (prerequisites ticked automatically), the personalised dashboard, why locked topics aren't recommended (every recommendation has its prerequisites completed; a locked topic names what to finish first), start a topic, the AI loading state, a failed quiz (resources shown) then a passed retake (mastery 46% -> 100%, five topics unlocked), the updated recommendation, the graph (every topic drawn in its status colour, 37 prerequisite links, a click opens the detail panel), and logout with protected routes redirecting to login. Refreshing nested routes (`/graph?topic=...`, `/quiz/...`, `/onboarding`, `/dashboard`) keeps the learner signed in on that page. No console errors or failed requests. All 36 checks passed on both.

**Phase 21 - Deployment Readiness (deferred by the owner, 2026-10-30):** AdaptLearn runs on localhost only for now. If it is deployed later, the remaining work is: production services (Neo4j Aura, Neon PostgreSQL, a Railway backend, a Vercel frontend, a Groq key), production environment variables (`APP_ENV=production` refuses the placeholder JWT secret; `postgres://` URLs from Neon are converted; `FRONTEND_URL` takes the Vercel origin for CORS), a rewrite of every path to `index.html` on Vercel so nested routes refresh, HTTPS, the curriculum seed (`python -m seed.seed_graph`), and the same demo script on the live site. Before real users: rate-limit login/register, move to Alembic migrations, and re-check the resource links (see Open items). This needs accounts on those services in the owner's name.

## Next: multi-domain expansion (planned 2026-10-30; Phases 22-24 done)

Beyond the original specification; follows agreed decisions 11-14. Existing topic ids and learner progress are kept throughout.

- **Phase 22 - Multi-domain curriculum model (done):** domains as their own nodes; topics in one shared pool, each belonging to one or more domains; one prerequisite graph whose edges may cross domains; the curriculum split into one data file per domain; the validator extended (no cycles across domains, every topic reachable and in at least one domain); the seeder handling shared topics without pruning another domain's. Web Development moves over unchanged, plus a small Foundations domain to prove sharing.
- **Phase 23 - Domain enrolment & multi-domain APIs (done):** which domains each learner has joined (new table); a catalogue endpoint with each domain's size and how much the learner already knows there; join a domain; onboarding, learning path, graph and dashboard per domain; a home endpoint with progress per joined domain and "Up next" across them; locked topics naming prerequisites in other domains; suggestions for domains the learner is already partly ready for.
- **Phase 24 - Multi-domain UI (done):** domain catalogue, join flow, onboarding per domain (known shared topics pre-ticked), home page, domain switcher, dashboard and graph per domain with cross-domain prerequisites as links, and an optional whole-map view (grouped by domain when zoomed out).
- **Phase 25 - Content verification tooling:** automated checks for new content (links live, videos via oEmbed, fallback questions through the quiz validator, description and resource rules, graph sanity), batch generation of sample AI quizzes for review within Groq's daily limit, maths rendering in quiz text (AI/ML and blockchain need formulas), a quiz-prompt rule keeping cybersecurity conceptual and defensive, and an automatic answer check for live AI quizzes (see Open items: AI answer accuracy).
- **Phases 26-31 - Domain content, in dependency order:** (26) Foundations and Python; (27) Data Science and AI & ML; (28) Databases and Computer Science Core; (29) Cybersecurity and Cloud & DevOps; (30) Blockchain & Web3 and App Development; (31) Game Development and UI/UX Design. Each topic gets a description, 1-3 verified resources and 3 validated fallback questions; every topic's sample AI quiz is reviewed.
- **Phase 32 - Multi-domain testing & cleanup:** regression across domains, accessibility and screen sizes again, graph performance at roughly 250 topics, and the demo script extended to cross-domain journeys.

Open question for the owner: whether to add in-app study pages (a lesson per topic, readable regardless of quiz results); if yes, they fit as a phase between 25 and 26 so every new domain gets lessons from the start.
