# AdaptLearn - Project State

**Last updated:** 2026-10-26
**Current phase:** Phase 15 complete (Onboarding UI) - Phase 16 (Dashboard UI) up next
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
| 15 | Onboarding UI | Done | latest |
| 16 | Dashboard UI | Next | - |
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
| Backend | FastAPI app on `8000`: settings, PostgreSQL + Neo4j connections, CORS, consistent errors, JWT auth. Routes: `GET /`, `GET /api/health`, `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`, `GET /api/topics/all`, `GET /api/topics/graph`, `GET /api/topics/learning-path`, `POST /api/topics/mark-known`, `GET /api/quiz/generate/{topic_id}`, `GET /api/quiz/active`, `POST /api/quiz/{id}/next`, `POST /api/quiz/{id}/answer`, `POST /api/quiz/{id}/events`, `POST /api/quiz/submit`, `GET /api/progress/dashboard`, `GET /api/progress/all`, Swagger at `/docs` |
| Backend venv | `backend/venv` (Python 3.13.5) with `requirements.txt` installed |
| Backend config | `backend/.env` created locally from `.env.example` with a generated `JWT_SECRET_KEY` (git-ignored) |
| Database tables | `users`, `topic_progress`, `quiz_attempts`, `quiz_sessions`, plus (Phase 12.5) `quiz_responses`, `proctoring_events`, `quiz_integrity` - all created automatically on backend startup (`create_all`; the new tables were added to the existing dev database without a reset) |
| Groq | API key set in `backend/.env`; model `openai/gpt-oss-120b` (reasoning effort low). Live quizzes generate in ~1.7-2.0s; without Groq the curated fallback bank is used |
| Demo account | `demo@adaptlearn.dev` in the local dev database only (password shared outside the repo; not a real credential): onboarded with HTML Basics, then 6 real AI quizzes (CSS 3/3, Git 2/3, JavaScript 1/3, SQL 0/3, 1/3, 0/3), so the dashboard has real data and SQL Basics needs attention. Log in with it in Swagger (`/api/auth/login`, then Authorize). Remove with: `docker exec adaptlearn-postgres psql -U postgres -d adaptlearn -c "delete from users where email='demo@adaptlearn.dev'"` |
| Frontend | `frontend/`: React 19.3 + Vite 8 + Tailwind CSS 4.3 + shadcn/ui (Radix, Nova preset) + React Router 8 + Axios, all versions pinned exactly. Dev server on `5173` (`npm run dev`). Built so far: palette theme, routing with protected/public-only guards, Axios client (Bearer token, session-ending 401 handling, error messages, Retry-After), AuthProvider/useAuth (session restore via `/auth/me`, cross-tab sync), AppShell/Navbar/AuthLayout, shared loaders/error/empty states/progress bar/status badge. Phase 14: working login and register forms (validation matching the backend, server errors on the right field, show/hide password, confirm password) and the post-sign-in redirect (remembered page, else onboarding or dashboard by `onboarded`). Phase 15: onboarding screen (topics by difficulty, prerequisites ticked automatically with an explanation, live counter, returning learners see completed topics, save to `mark-known`, dashboard confirmation). Dashboard, quiz and graph pages are placeholders until Phases 16-18 |
| Tests | Backend: 393 passing (`pytest` from `backend/`): 33 auth, 21 curriculum data/validator, 8 Neo4j seeder (isolated `pytest-seed` domain), 21 topics API, 28 onboarding/frontier, 17 learning path, 87 BKT, 116 quiz generation + submission (mostly parametrized), 17 dashboard/progress, 41 proctoring, 4 CORS. Tests never call the real Groq API. PostgreSQL tests use the separate `adaptlearn_test` database. Frontend: 174 passing (`npm test` from `frontend/`): 22 API client, 14 auth provider, 33 routing, 1 crash screen, 22 shared components/helpers, 23 validation and server-error mapping, 14 login page, 12 register page, 17 topic helpers, 16 onboarding page; no backend needed |

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

- The only red in the PDF is inside an embedded chart image, so it can't be read exactly. Use red-600 `#DC2626` for errors so it stays within Tailwind's palette.
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
| `/` → `/dashboard` if authenticated (PRD 16) | `/` and sign-in go to `/onboarding` until the learner has onboarded, then `/dashboard` | US-01 sends new accounts to onboarding; a learner who registered and left before onboarding should land there too |
| Redirect after login unspecified beyond US-02 | Back to the page that required login; never after a voluntary logout | Convenience, without sending the next person on a shared computer to the previous learner's page |
| Onboarding grid source unspecified (ROADMAP: "known-topic selectable grid") | `GET /topics/graph` instead of `/topics/all`; topics grouped by difficulty | The graph includes prerequisites and status, so the screen can tick prerequisites as the server will and show completed topics |
| Selected counter | Counts explicit choices plus the prerequisites they bring along, and says how many are prerequisites | Agreed decision 3: the count matches what the server saves |
| "User is sent to dashboard" (US-04) | Sent with a confirmation of how many topics were marked known and which prerequisites were added | The learner sees that onboarding worked |
| Quiz contract (ARCHITECTURE 13.8 / 13.9): generate returns all 3 questions; submit takes `{quiz_id, answers}` | Generate returns no questions; `POST /quiz/{id}/next` serves one at a time with a deadline, `POST /quiz/{id}/answer` locks each answer, `POST /quiz/{id}/events` takes proctoring signals, `GET /quiz/active` resumes; submit takes only `{quiz_id}` and adds `integrity` | Proctoring (decision 10): a page holding all questions at once could be answered with outside help and no timing control |
| No proctoring in the PRD | Integrity score (start 100, penalties per signal, verified at 80+); flagged attempts saved but change no progress; abandoned quizzes never count | Owner decision |
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
| Quiz before onboarding unspecified | Progress rows are created as if onboarding with nothing known | Phase 11 always has a row to update |
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
- **The Phase 17 quiz UI must implement layer 2:** fullscreen on start, Page Visibility and blur listeners, blocked copy/paste/context menu, `screen.isExtended` where supported, a heartbeat every 5 s, the one-question flow and resuming via `/quiz/active`.
- **BKT calibration (built as specified; now confirmed by tests):** with the PRD's fixed values, `p_know` can't fall below 0.40 after any answer and repeated wrong answers level off at 16/35 ≈ 0.457; the same 2/3 score ends at 0.76 or 0.98 depending on which answer was wrong; one 3/3 quiz takes a new topic to 0.989 (mastered). Seen live in Phase 12: a **failed** 1/3 SQL quiz (wrong, wrong, right) raised mastery from 45.5% to 87.5%, so a learner can see a failed quiz next to a high mastery bar. Knock-on for Phase 11: the confusion rule (`attempts > 2 and p_know < 0.50`) can only fire while a learner keeps getting most answers wrong, because almost any recent correct answer lifts `p_know` above 0.5. Revisit only if it feels wrong in testing.
- **Groq free-tier limits:** 1,000 requests/day and 8,000 tokens/minute (checked live 2026-10-05). A quiz uses about 800 tokens, so roughly 9-10 quizzes per minute across all users before Groq rate-limits; learners then get fallback questions automatically. Fine for development and demos; a paid tier is needed for real traffic.
- **Groq model churn:** Groq has retired two Llama models during this project. If `openai/gpt-oss-120b` is retired, quizzes keep working via the fallback bank (logged as HTTP 4xx); switch `GROQ_MODEL` in `.env` - no code change needed.
- **Fallback bank repeats:** it has exactly 3 questions per topic, so a learner who retakes a topic while Groq is down sees the same questions (options are reshuffled). Adding more questions per topic and sampling 3 would fix this.
- **Expired quiz sessions accumulate:** `quiz_sessions` rows are never deleted. Harmless at MVP scale; a periodic cleanup of expired, unsubmitted sessions would keep the table small.
- **Rate limiting:** quiz generation is now limited per user (Phase 12.5); login/register still have no rate limit. Recommended by the PRD before public deployment (Phase 21).
- **Spec documents in git history:** PRD/ROADMAP/ARCHITECTURE were untracked on 2026-10-26 but remain readable in the Phase 1 commit (`accb6cd`); the owner chose not to rewrite history.
- **No migrations:** schema changes need the dev reset above. Move to Alembic before any deployment holds real user data.
- **Recommendation ranking (built as specified, worth revisiting):** the spec ranks the frontier by difficulty then name, so easy side topics always come first. In the live check, a learner who marked React Hooks as known was recommended Git Basics, Semantic HTML and Arrays & Objects ahead of React Router, the same top 3 as a learner who only knew HTML/CSS/JS. A track-aware ranking (e.g. prefer topics that unlock what the learner just finished) could be a later enhancement.
- **Resource links can rot:** all 81 URLs were live on 2026-10-04. Re-check them before deployment (Phase 21).
- **Dashboard doesn't yet send un-onboarded learners to onboarding:** sign-in and `/` already do (via `onboarded` from `GET /topics/learning-path`), but opening `/dashboard` directly before onboarding shows the dashboard. Phase 16 should show an onboarding prompt using the dashboard response's own `onboarded` flag.
- **No password reset or change:** not in the PRD. The register form asks for the password twice and has show/hide toggles to limit typos; an account with a forgotten password can only be recreated.
- **JWT in `localStorage`** (as the spec designs it): readable by any script on the page, so an XSS bug would expose the token. Acceptable for the MVP; HttpOnly cookies with refresh tokens are the hardening path (README security notes).
- **Placeholder pages:** dashboard, quiz and graph pages currently say which phase builds them. The dashboard placeholder already shows the onboarding confirmation, which Phase 16 should keep.
- **Domain names come from the frontend:** the API returns the domain slug (`web-development`); `src/lib/topics.js` maps it to "Web Development" (title-casing unknown slugs). A `domain_name` field in the API would be cleaner once there is more than one domain.
- **Dev auto-reload under the assistant:** `uvicorn --reload` hangs on Windows when started without a console (the reloader can't deliver Ctrl+C to the worker). Doesn't affect running it in a normal terminal; the assistant restarts the server manually instead.

---

## Next step

**The backend API is complete** (Phases 1-12, plus proctoring in 12.5), covered by 393 tests. **The frontend foundation is in place** (Phase 13), **learners can register, log in and log out** (Phase 14) and **onboard from the browser** (Phase 15), covered by 174 frontend tests and live browser checks.

**Phase 16 - Dashboard UI:** `GET /progress/dashboard` drives a greeting, stat cards (overall progress, completed, mastered, average mastery, attempts, flagged attempts), the 3 recommended topic cards (name, description, difficulty, status, mastery, prerequisites, Start / Continue / Retry), topics needing attention with resources, recent attempts with their integrity verdict, compact mastery bars, the curriculum-complete state, and a prompt to onboard for learners who haven't. Keep the onboarding confirmation.

Exit gate: the dashboard shows no hard-coded numbers.

The quiz screens (Phase 17) must use the proctored flow and implement the layer 2 browser monitoring described in the open items.
