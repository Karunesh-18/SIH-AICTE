# 02 — Architecture

## 1. Overview

```
 Browser (Next.js)
   │  REST/JSON + JWT
   ▼
 FastAPI app ───────────────────────────────────────────────┐
   ├─ api/        routers (auth, institutions, applications, │
   │              obligations, documents, evc, complaints,    │
   │              dashboards, notifications, admin, audit)    │
   ├─ services/   business logic                              │
   │    ├─ workflow      stage transitions, SLA clock          │
   │    ├─ obligations   status computation, ladders           │
   │    ├─ alerts        scheduler job, notification dispatch  │
   │    ├─ complaints    assignment, transfer, overlap         │
   │    ├─ risk          explainable score                     │
   │    ├─ forecast      heuristic breach probability          │
   │    ├─ ocr           text extraction, date extraction      │
   │    └─ audit         hash chain append and verify          │
   ├─ core/clock.py      real clock or simulated clock         │
   └─ db/                SQLAlchemy + Alembic ────────────────►  SQLite / PostgreSQL
 APScheduler (in-process) ─► alerts.run_cycle() every N minutes
 File store: ./storage/uploads (local disk, path stored in DB)
```

## 1a. Architectural style (see DECISIONS D-03, D-04)

Modular monolith with ports and adapters. Layers per module: `api` -> `services` (use cases, own the transaction) -> `domain` (pure functions: status, ladder, risk, overlap, forecast) -> `adapters` (repositories, mail, OCR, storage). Domain never imports SQLAlchemy/FastAPI. Cross-module calls go through service interfaces only.

ACID: each use case runs in one Unit of Work. Notification rows are written to an **outbox** inside the transaction and dispatched after commit. `version` columns give optimistic locking (409 on stale write). SQLite runs in WAL mode.

## 2. Key design decisions

1. **One `Obligation` table** for every time-bound item. Workflows create obligations; the alert engine only knows obligations.
2. **Computed status, stored for query.** Obligation status is a pure function of `(now, due_at, fulfilled_at, waived_at)`. The alert cycle recomputes and persists it so dashboards can filter in SQL.
3. **Simulated clock.** All time reads go through `core/clock.now()`. Admin can set an offset (`POST /admin/clock`). Tests set a fixed clock.
4. **Idempotent escalation.** `ObligationAlertLog(obligation_id, step_key)` has a unique constraint. The engine checks it before sending.
5. **Server-side masking.** Serialisers for complaints take the viewer's role and assignment, and strip complainant fields unless allowed.
6. **Hash-chained audit.** Each row stores `prev_hash` and `hash = SHA256(prev_hash + canonical_json(entry))`. Verification walks the chain.
7. **Advisory outputs are separate records.** Overlap suggestions, OCR suggestions and risk snapshots are stored as suggestions with status; humans confirm or dismiss.
8. **Provider interfaces** for notifications (`EmailProvider`, `SmsProvider`, `WhatsAppProvider`). Dev implementations write to `notifications` and log; only email uses SMTP.

## 3. Core flows

### 3.1 Application stage transition
1. Officer calls `POST /applications/{id}/transition` with `action` and `note`.
2. `workflow.transition()` validates: officer's role matches current stage owner role; action allowed for stage; application not terminal.
3. Closes current `StageInstance` (outcome, actor, timestamps), opens next one using `StageDefinition` (SLA days, owner role).
4. Fulfils the old stage-SLA obligation, creates a new one with `due_at = now + sla_days`.
5. Writes audit entry and institution timeline event; creates notifications.
6. "Return for clarification" sets status `AWAITING_INSTITUTION`, pauses the SLA obligation (`paused_at`), and resumes with remaining time when the institution responds.

### 3.2 Alert cycle
```
run_cycle(now):
  for each open obligation:
      recompute status
      for each step in its escalation ladder:
          if step is due at now and no AlertLog for (obligation, step):
              dispatch notifications to step.notify roles/users
              write AlertLog + audit + timeline event
```
Catch-up rule (D-09): if several steps are due at once (for example after a clock jump), only the latest fires; earlier ones are written to the alert log as `SKIPPED`. The ladder is snapshotted onto the obligation at creation; recipients are scoped to the institution's region.

Ladder example (`days_offset` relative to `due_at`): `-90 institution`, `-60 institution`, `-30 institution + scrutiny officer`, `0 officer`, `+3 regional officer`, `+10 admin`.

### 3.3 Document with OCR suggestion
Upload → store file → `ocr.extract(file)` returns `{text, doc_type_guess, expiry_candidates[]}` → create `ObligationSuggestion(status=PENDING)` → officer or institution confirms or edits the date → create `Obligation(source=OCR_CONFIRMED)`.

### 3.4 Complaint registration and overlap
Intake: officer registers directly, or a public `PortalSubmission` is reviewed by an officer and registered or rejected (D-05). Register → assign bureau (manual or rule-based suggestion by category) → create complaint SLA obligation → `overlap.find_candidates(complaint)` compares with other open complaints on the same institution (any bureau). Two triggers: (1) rule-based, the institution already has an open case at a different bureau, which raises "Potential Overlapping Cases - Coordination Required" to officers of every involved bureau even when the text differs; (2) TF-IDF similarity, which adds a score and explanation. Store `ComplaintLink(status=SUGGESTED, score, shared_terms)` → bureau officer confirms (links the cases) or dismisses → confirmed links are visible on both cases. Nothing is merged or closed automatically.

## 4. Security model

- **AuthN:** email + password, bcrypt; access JWT 30 min, refresh 7 days.
- **AuthZ:** FastAPI dependencies `require_roles(...)`, plus object-level checks (institution users only see their institution; bureau officers see complaints in their bureau plus masked cross-bureau summaries).
- **Complaint masking rules**
  - Complainant name/contact: visible to assigned bureau officer and Admin only
  - Narrative: visible to bureau officers of linked cases and Admin; regional officers see category, status, dates and a short redacted summary
  - Overlap suggestions: before confirmation, officers of the involved bureaus see the other case's reference, category, bureau/cell, assigned officer, status and score, so they can coordinate; narrative and shared terms appear only after confirmation (D-08, D-17). Complainant identity stays masked throughout
  - Institution users: see that a complaint exists and its category/status/stage, not the complainant or internal notes
- **Uploads:** allow PDF/PNG/JPG, max 10 MB, random filenames, no execution, served via authenticated endpoint.
- **Input validation:** Pydantic schemas; reject unknown fields.
- **Secrets:** `.env`, never committed. Provide `.env.example`.
- **Rate limiting:** basic login rate limit (in-memory) for the prototype.

## 5. Configuration

`system_config` rows (key/JSON value) for: escalation ladders per obligation type, notification templates (en/hi), overlap threshold (default 0.35), risk weights, clock offset, feature flags (`USE_SENTENCE_TRANSFORMERS`, `ENABLE_SMS_STUB`).

## 6. Observability

- Structured logging with request IDs
- `GET /health` and `GET /admin/alert-cycle/last` (last run, counts)
- Notifications table doubles as a delivery log for the demo

## 7. Deployment

- `docker compose up` runs `api` (uvicorn, port 8000) and `web` (Next.js, port 3000)
- SQLite file mounted as a volume; seed with `make seed`
- Production notes (for the slide): PostgreSQL, object storage, a job queue instead of in-process scheduler, SSO integration, encryption at rest, role-scoped data access
