# 07 — Build Plan

Work in order. Do not start a phase until the previous phase's acceptance criteria pass. Keep `docs/PROGRESS.md` updated (checklist of tasks below). Record any deviation in `docs/DECISIONS.md`.

Estimated effort is relative (S ≈ under 1h, M ≈ 1–3h, L ≈ 3–6h) for one focused builder using Claude Code.

---

## Phase 0 — Scaffold (S–M)

**Tasks**
- [x] `git init` (done)
- [ ] Generate frontend types from the FastAPI OpenAPI schema (`openapi-typescript`); Alembic in batch mode for SQLite; SQLite WAL on
- [ ] Set up module folders per DECISIONS D-03 (ports in `domain/`, adapters separate); Unit of Work + outbox helper
- [ ] Create repo layout from `CLAUDE.md §4`
- [ ] Backend: FastAPI app, config via env, SQLAlchemy base, Alembic init, `/health`
- [ ] Frontend: Next.js + Tailwind + shadcn/ui, API client with typed fetch, TanStack Query provider
- [ ] `docker-compose.yml`, `Makefile` (`dev`, `seed`, `test`, `lint`)
- [ ] `.env.example`, `.gitignore`, `storage/` folder
- [ ] CI-style script: `make test` runs backend and frontend tests

**Acceptance:** `make dev` starts both services; frontend shows a page that calls `/health`; `make test` passes (even if trivial).

---

## Phase 1 — Foundation: auth, roles, registry, audit (M–L)

**Tasks**
- [ ] Models + migrations: User, Region, Bureau, Institution, Program, SystemConfig, AuditLog
- [ ] Auth endpoints, bcrypt, JWT, `require_roles`, object-level scope helpers
- [ ] `core/clock.py` with simulated offset; admin clock endpoints
- [ ] Audit service (append in transaction, verify, dev tamper endpoint)
- [ ] Institution list/detail endpoints; seed regions, bureaus, 15 institutions, demo users
- [ ] Frontend: login, app shell (sidebar, top bar, role-based nav, language toggle skeleton, footer strip), institutions list

**Acceptance**
- Each demo role can log in and sees only its nav items
- Institution user can only fetch their own institution (403 otherwise; tested)
- Audit verify returns ok; after tamper endpoint it returns the first broken id (tested)
- Clock offset changes `clock.now()` (tested)

---

## Phase 2 — Obligation engine and alerts (L) ★ backbone

**Tasks**
- [ ] Models: Obligation, EscalationLadder, ObligationAlertLog, Notification
- [ ] `obligation_status()` pure function with unit tests (all branches)
- [ ] Ladder evaluation: given `now`, `due_at`, ladder, sent steps → steps to fire; tests for 90/60/30/0/+3/+10 and idempotency
- [ ] `alerts.run_cycle()`; APScheduler job (every 5 min in dev) and `POST /admin/alert-cycle/run`
- [ ] Notification dispatch via provider interfaces (in-app, email SMTP/console, SMS/WhatsApp stub logging)
- [ ] Obligations CRUD, fulfil, waive, extend (all audited), calendar endpoint
- [ ] Compliance dashboard endpoint
- [ ] Frontend: Obligations list + detail drawer with ladder timeline, compliance dashboard, notification bell and page, calendar view

**Acceptance**
- Creating an obligation due in 31 days, advancing the clock 1 day and running the cycle creates exactly one T-30 notification; running again creates none
- Overdue obligation triggers T0, T+3, T+10 steps at the correct simulated times
- Waive without reason is rejected; extension writes before/after audit
- Dashboard numbers match the DB (tested with a fixture)

---

## Phase 3 — Approval workflow (L) ★ core of SIH26262

**Tasks**
- [ ] Models: StageDefinition, Application, StageInstance, EvcVisit; seed workflows `NEW_PROGRAM`, `INTAKE_CHANGE`, `RENEWAL`
- [ ] `workflow.transition()` with validations, SLA obligation create/fulfil, pause/resume on RETURN/respond, audit, timeline events, notifications
- [ ] Endpoints: applications CRUD/list, transition, respond, workflows, admin stage definitions
- [ ] EVC endpoints + `EVC_VISIT` obligation
- [ ] Pendency dashboard endpoint (counts by stage/region/officer, ageing, breaching list)
- [ ] Frontend: new application wizard, applications list/detail (stepper, history, action panel dialogs), work queue, EVC calendar, pendency dashboard, admin stage editor

**Acceptance**
- Wrong-role transition returns 403 (tested)
- RETURN pauses the SLA obligation; respond resumes with remaining time (tested)
- Moving through all stages creates correct StageInstances and SLA obligations; final APPROVE requires note and the right role
- Admin SLA change affects only new stage instances (tested)
- Pendency dashboard on seed data shows at least 3 breaching and 4 at-risk applications

---

## Phase 4 — Documents and institution profile (M–L)

**Tasks**
- [ ] Models: Document, ObligationSuggestion, InstitutionEvent, RiskSnapshot (table only for now)
- [ ] Upload endpoint with validation, authenticated download
- [ ] `ocr.extract()` per `docs/06` §1 with fixtures and tests; suggestions confirm/dismiss endpoints
- [ ] Timeline event writers for all existing state changes (applications, stages, obligations, alerts, documents, EVC)
- [ ] Profile and timeline endpoints with role-based visibility filtering
- [ ] Frontend: documents page with upload and Suggestion card, institution profile (hero screen), institution self-service home

**Acceptance**
- Upload of the seeded sample lease PDF yields a suggestion with a highlighted snippet; confirming creates an obligation with `source=OCR_CONFIRMED` and the T-90/T-60/T-30 ladder
- Institution user's profile view omits complaint and risk data (tested)
- Timeline shows events from at least 5 different types for the featured institution

---

## Phase 5 — Complaints module (SIH26264 add-on) (L)

**Tasks**
- [ ] Models: Bureau (already; add PGRC), ComplaintCategory, Complaint (incl. last action, next action, expected disposal date), ComplaintAssignment, ComplaintAction, ComplaintNote, ReviewFlag
- [ ] Complaint endpoints, SLA obligation (`COMPLAINT_SLA`), assign / transfer / escalate with action history, status lifecycle incl. `TRANSFERRED`, `ESCALATED`
- [ ] Search and filters: institution name, AICTE Permanent ID, case ID, bureau/cell, region, category, status group, date range
- [ ] Masking serializer enforced server-side with tests per role
- [ ] Consolidated institution complaints view endpoint
- [ ] Complaint dashboard endpoint (total, pending, under process, disposed, transferred, beyond timeline; bureau workload; institution-wise status; ageing; multi-bureau institutions)
- [ ] Complaint reports endpoints with CSV export (bureau, region, institution, ageing, disposal rate, overlaps, monthly/quarterly) and Reports screen
- [ ] Public portal: `PortalSubmission` model, public endpoints (rate limited), officer review queue (register/reject), tracking-ID status page
- [ ] Frontend: complaint queue, detail (masked fields, assignment timeline), register form, consolidated institution view, complaint dashboard, public submit + status pages, portal review queue

**Acceptance**
- Regional officer response contains `complainant.masked=true` and redacted narrative (tested)
- Institution user cannot read complaint narrative or notes (tested)
- Transfer requires a reason and creates assignment history
- Complaint SLA alerts fire under the simulated clock using the same engine
- Dashboard shows at least 2 institutions handled by 2+ bureaus on seed data, and the six tiles (total, pending, under process, disposed, transferred, beyond timeline) add up consistently (tested)
- An RB case and a PGRC case on the same institution raise "Potential Overlapping Cases - Coordination Required" for both bureaus even when the texts differ (tested)
- Search by institution name, AICTE Permanent ID and case ID each return the expected complaint (tested)
- Transfer and escalate each write a `ComplaintAction` row and update last action / date (tested)
- Reports return CSV and contain no complainant fields (tested)
- Portal submission returns a tracking ID; status lookup needs ID + email and exposes no narrative or notes; rejecting requires a reason (tested)
- A failure mid-transition rolls back state, audit and outbox together (tested)
- Clock jump past several ladder steps fires only the latest and logs the rest `SKIPPED` (tested, Phase 2)

---

## Phase 6 — Advisory intelligence (M–L)

**Tasks**
- [ ] `overlap.find_candidates()`: rule-based multi-bureau trigger plus TF-IDF per `docs/06` §2, links, confirm/dismiss endpoints, panel in complaint detail; trigger on registration
- [ ] `risk.compute()` rules-v1 with config weights; nightly job; recompute endpoint; risk view UI; risk badge on profile and institutions list
- [ ] `forecast.estimate()` heuristic-v1; forecast card on application detail and chips on pendency table
- [ ] Review flag UI (M-09)
- [ ] "Suggestion" tag component with explanation popovers everywhere these appear

**Acceptance**
- Seeded cross-bureau duplicate pair is suggested with score ≥ threshold and shared terms listed; unrelated same-category pair is not
- Dismissed pair is never re-suggested (tested)
- Risk snapshot for the featured institution is ELEVATED or HIGH and the factor table sums to the displayed score (tested)
- Forecast returns each label on seeded fixtures (tested)

---

## Phase 7 — Polish, Hindi, demo readiness (M)

**Tasks**
- [ ] i18n EN/हिंदी for required areas (`docs/05` §6) including notification templates
- [ ] Empty/loading/error states audit across all screens
- [ ] Responsive pass at 360 px; keyboard and contrast pass
- [ ] Demo controls panel (advance clock, run cycle, tamper audit) in Admin
- [ ] Final seed script (`make seed`) idempotent and reproducible; reset script
- [ ] Playwright smoke test following the demo script in `docs/08`
- [ ] README for the built repo: setup, accounts, architecture summary, screenshots
- [ ] Roadmap slide content in `docs/ROADMAP.md` (integrations from `docs/06` §7)

**Acceptance**
- `make reset && make seed && make dev` yields a clean demo state in under 2 minutes
- Playwright demo test passes end to end
- Every screen at 360 px has no horizontal scroll
- All acceptance criteria from phases 1–6 still pass (`make test` green)

---

## Cross-cutting checklists

**Security**
- [ ] No endpoint without auth except `/health` and `/auth/login`
- [ ] Every object fetch checks scope
- [ ] Upload validation and authenticated downloads
- [ ] Secrets only in `.env`

**Quality**
- [ ] Type hints and Pydantic models everywhere; TypeScript strict mode
- [ ] Linting (ruff, eslint) clean
- [ ] Each new service has unit tests; each permission rule has a test

**Honesty**
- [ ] Footer strip visible on all pages
- [ ] Methods labelled (rule-based, TF-IDF, heuristic)
- [ ] No claims of integration that is only a stub
