# CLAUDE.md — Waymark build instructions

> Working name: **Waymark**. A unified compliance and approval platform concept for AICTE-style regulation, built for Smart India Hackathon problem statements **SIH26262** (core) and **SIH26264** (add-on module).
> This file is the entry point. Read it fully, then read the docs in `docs/` in the order given below before writing any code.

## 1. What you are building

One platform with a shared backbone and two workflows on top:

1. **Obligation engine (backbone):** every time-bound thing is one entity, an `Obligation` (document expiry, FDR maturity, undertaking, EVC visit, approval-stage SLA, complaint SLA). One alert engine, one calendar, one overdue dashboard.
2. **Approval workflow (SIH26262, CORE):** configurable stages, stage SLAs, EVC scheduling, pendency dashboard, escalation.
3. **Complaint tracking (SIH26264, ADD-ON):** register, assign to bureau/cell, cross-bureau overlap detection, SLA alerts, history.
4. **Institution profile:** one page per institution showing approvals, documents, obligations, complaints, inspections and a transparent risk view as a single timeline.
5. **Advisory intelligence:** OCR-assisted expiry extraction, duplicate-complaint similarity, explainable risk score, heuristic SLA-breach forecast.

## 2. Non-negotiable principles

1. **Advisory only.** The system recommends, flags and routes. It never auto-approves, auto-rejects, auto-penalises or auto-triggers an inspection. Every consequential action is a human click, recorded in the audit log. Every AI/heuristic output is labelled as a suggestion and carries a visible explanation.
2. **Core first.** SIH26262 features must be complete and demo-ready before any complaint work starts. Follow `docs/07-BUILD-PLAN.md` strictly in phase order.
3. **Synthetic data only.** Never use real institution names, real people or real complaints. Use the fictional dataset defined in `docs/08-SEED-DATA-AND-DEMO.md`. Never present the prototype as an official AICTE system or use official logos.
4. **Configurable, not hardcoded.** Stages, SLAs, escalation ladders, document types and complaint categories live in the database and are editable by Admin.
5. **Privacy by design.** Complainant identity is masked from everyone except the assigned bureau officer and Admin. Enforce this in the API layer, not only the UI.
6. **Auditability.** Every state change writes a hash-chained audit entry (see `docs/03-DATA-MODEL.md`).
7. **Explainability.** Risk score, overlap score and forecast must return their contributing factors, not just a number.
8. **Don't over-claim.** No blockchain, no "AI-powered" labels on rule-based features. Say "rule-based", "TF-IDF similarity", "heuristic".
9. **Architecture: modular monolith, ports and adapters** (see `docs/DECISIONS.md` D-03, D-04). SOLID: services hold use cases, domain rules are pure functions, adapters sit behind small interfaces, dependencies are injected.
10. **ACID:** one transaction per use case (state change + audit + timeline + obligations), notifications through a transactional outbox, optimistic locking on core entities, constraints enforced in the DB.
11. **Decisions log:** every deviation from these docs goes in `docs/DECISIONS.md`; progress in `docs/PROGRESS.md`. Teammates rely on both.

## 3. Tech stack (decided, do not re-debate)

| Layer | Choice |
|---|---|
| Frontend | Next.js (App Router) + TypeScript + Tailwind CSS + shadcn/ui + TanStack Query + Recharts |
| Backend | FastAPI (Python 3.11+) + Pydantic v2 + SQLAlchemy 2.x + Alembic |
| Database | SQLite for local dev and demo, schema kept PostgreSQL-compatible |
| Auth | JWT (access + refresh), bcrypt, role-based dependency guards |
| Scheduler | APScheduler in-process, plus a **simulated clock** for demos |
| AI/ML | scikit-learn TF-IDF + cosine similarity (default); optional `sentence-transformers` behind a feature flag |
| OCR | `pytesseract` + `pdf2image` (optional), with regex fallback on text PDFs/plain text |
| Notifications | Email via SMTP (console/mailhog in dev); SMS/WhatsApp as a stubbed provider interface that logs to the DB |
| Packaging | Docker Compose (`web`, `api`) plus a `make dev` shortcut |
| Tests | pytest (backend), Vitest + Playwright smoke test (frontend) |

## 4. Repository layout to create

```
waymark/
├── CLAUDE.md
├── README.md
├── docs/                      # copy of these spec docs
├── docker-compose.yml
├── Makefile
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/              # config, security, clock, audit
│   │   ├── db/                # session, base, migrations
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── api/               # routers per resource
│   │   ├── services/          # obligations, workflow, complaints, risk, ocr, notify
│   │   └── seed/              # seed script and sample documents
│   ├── tests/
│   └── pyproject.toml
└── frontend/
    ├── app/                   # routes per docs/05-UI-UX-SPEC.md
    ├── components/
    ├── lib/                   # api client, auth, i18n
    └── package.json
```

## 5. Reading order

1. `docs/01-PRD.md` — scope, users, requirements, what is in and out
2. `docs/02-ARCHITECTURE.md` — components, flows, security
3. `docs/03-DATA-MODEL.md` — entities, enums, constraints, audit chain
4. `docs/04-API-SPEC.md` — endpoints and permission matrix
5. `docs/05-UI-UX-SPEC.md` — screens, components, design tokens
6. `docs/06-AI-MODULES.md` — OCR, similarity, risk, forecast: algorithms and explanations
7. `docs/07-BUILD-PLAN.md` — phased tasks with acceptance criteria (**your task list**)
8. `docs/08-SEED-DATA-AND-DEMO.md` — dataset, demo accounts, demo script

## 6. How to work

- Work phase by phase from `docs/07-BUILD-PLAN.md`. Finish a phase's acceptance criteria before moving on. Keep a checklist in `docs/PROGRESS.md` and update it as you go.
- Commit-sized steps. After each phase the app must run end to end with `make dev`.
- Write tests for: obligation status computation, escalation ladder, workflow transitions, permission checks (especially complaint masking), audit chain verification, overlap scoring.
- If a doc is ambiguous, choose the simplest option consistent with the principles above, and record the decision in `docs/DECISIONS.md` rather than stopping.
- Do not add features that are not in the docs without recording them in `docs/DECISIONS.md` first.

## 7. Definition of done (per feature)

- Works through the UI, not only the API
- Permission-checked on the server
- Writes an audit entry for state changes
- Has seed data that makes it visible in the demo
- Has at least one automated test
- Empty, loading and error states handled

## 8. Cut line

If time runs short, ship in this order of priority and drop from the bottom:

1. Auth + roles, institution registry, obligation engine + alerts
2. Approval workflow + pendency dashboard
3. Institution profile timeline
4. Document upload with expiry extraction
5. Complaint module (basic: register, assign, status, SLA)
6. Overlap detection
7. Risk view, forecast, Hindi toggle, institution self-service polish
