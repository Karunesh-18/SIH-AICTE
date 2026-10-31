# Decisions log

Newest at the bottom. Anyone on the team can read this to see why the spec differs from a naive reading.

## D-01 Name: Waymark
"Setu" (previous name) is Hindi/Sanskrit. Renamed to **Waymark** everywhere. Hindi UI toggle is unaffected.

## D-02 Scope
SIH26262 is the main entry; SIH26264 ("Integrated Institution Complaint Monitoring and Status Dashboard") is an add-on module built after the core is demo-ready. The statement's weight on the complaint dashboard did not change this order (see D-16). The complaint module must be removable without breaking the core. Confirm with organisers whether a combined entry is allowed.

## D-03 Architecture: modular monolith, ports and adapters
- One FastAPI deployable; modules `identity, institutions, obligations, workflow, documents, complaints, intelligence, notifications, audit`. Modules call each other only through service interfaces.
- Layers: api -> services (use cases) -> domain (pure rules) -> adapters (DB, mail, OCR, storage). Domain code never imports SQLAlchemy or FastAPI.
- SOLID: SRP per service; OCP via DB-configured stages/ladders and pluggable scorers; ISP/LSP via small ports (`NotificationProvider`, `OcrExtractor`, `SimilarityScorer`); DIP via FastAPI dependency injection.
- Rejected: microservices / message broker (solo builder, demo scale). Boundaries are kept so a module can be extracted later.

## D-04 ACID rules
- One Unit of Work = one DB transaction per use case: state change + audit append + timeline event + obligation changes commit or roll back together.
- Notifications use a **transactional outbox**: rows are written in the same transaction and dispatched after commit.
- Optimistic locking (`version` int) on Application, Obligation, Complaint; stale write returns 409.
- Constraints in the DB (FKs, CHECKs, unique `(obligation_id, step_key)`), not only in code.
- SQLite in WAL mode for demo; schema stays PostgreSQL-compatible. Audit appends are serialised.

## D-05 Complaint intake: officer + public portal
Public form (no login) creates a `PortalSubmission` with a tracking ID, status `PENDING_VERIFICATION` (email verification is mocked). An officer reviews it and either registers it as a `Complaint` or rejects it as frivolous with a reason. Institutions see a redacted version. Rate limit only; no spam filtering. CSV/bulk import is deferred to the roadmap slide.

## D-06 Roles
ADMIN keeps config, final decision and audit access. Separation of duties (read-only AUDITOR, distinct decision-maker) is Phase 2. Scrutiny officers are scoped by region.

## D-07 Risk score (rules-v1) corrected
The original max-cap normalisation made the featured institution score about 20 (LOW). New rule: `score = min(100, sum(contribution))` with raised weights (see docs/06). The spec has 9 factors. Seed must produce Kaveri = ELEVATED, healthy institution = LOW; a test asserts the bands.

## D-08 Overlap scoring corrected
Category, recency and bureau bonuses apply only if `text_sim >= 0.15`. TF-IDF is fitted on the whole complaint corpus (cached), not 2-3 documents. Before a link is confirmed, the panel shows only reference, category, bureau and score; shared terms appear after confirmation (avoids leaking another bureau's narrative). Embeddings option kept for Hindi/Hinglish.

## D-09 Alert ladder behaviour
If time jumps past several steps, only the latest due step fires; earlier ones are logged `SKIPPED`. The ladder is snapshotted onto each obligation at creation. Recipients are scoped to the institution's region. Extending a due date recalculates future steps and keeps sent ones. Fulfilling a recurring document obligation can create the next one (renewal).

## D-10 Time handling
SLA days are business days (holiday table in `system_config`). Document expiry is stored as a `date` and evaluated in IST. Pause state lives only on `StageInstance` (`paused_at`, `paused_seconds`); the stage-SLA obligation mirrors it.

## D-11 Single event writer
`events.record()` writes the AuditLog entry and the InstitutionEvent in one transaction. Timeline is a projection of that write, not a separate code path.

## D-12 Deferred
Field-level encryption of complainant PII, CSV import, AUDITOR role: roadmap.

## D-13 Local build environment (Windows dev box)
No `make` or `docker` installed locally, so `Makefile`/`docker-compose.yml` are written to spec but unverified here; `scripts/dev.ps1` and `scripts/test.ps1` are the tested equivalents. Repo layout is flat (`backend/`, `frontend/` beside `docs/`), no `waymark/` nesting. shadcn/ui CLI not run; plain Tailwind components with the docs/05 tokens until a component is worth copying in. Frontend `lib/api-types.ts` is generated on demand via `npm run gen:api` (needs the API running).

## D-14 Phase 2 implementation notes
`Obligation.ladder_snapshot` (JSON) stores the ladder copied at creation (D-09). Optimistic locking uses SQLAlchemy `version_id_col`. Notification outbox is the `QUEUED` status on `Notification` rows (IN_APP is written inside the use-case transaction; EMAIL/SMS/WHATSAPP are dispatched after commit by `notify.dispatch_queued`), so the generic `Outbox` table is unused for now. Scheduler is off unless `SCHEDULER_ENABLED=true`. Institution users may fulfil only their own `INSTITUTION`-owned document-type obligations; waive/extend need REGIONAL_OFFICER or ADMIN. Calendar view (Compliance page toggle) and top-bar notification bell shipped with the UI redesign. Event timeline write (D-11) arrives with the institution profile in Phase 4.

## D-15 Visual redesign
Direction from ui-ux-pro-max "Accessible & Ethical": keeps the docs/05 palette, adds a dark navy sidebar, Atkinson Hyperlegible (Devanagari fallback kept) instead of Inter/Geist, lucide-react icons (new dependency), dark mode via `prefers-color-scheme`, status = colour + icon + text (`components/ui.tsx`). Shared `StatusChip`, `KpiTile`, `PageHeader`, `EmptyState`, `ErrorState`, `Skeleton`. Native `prompt()` calls in Obligations replaced by an accessible dialog.

## D-16 SIH26264 statement refresh (docs only)
The updated SIH26264 text asks for a status dashboard across bureaus/cells (RB, PGRC, others). Added to the spec: AICTE Permanent ID naming and search (D-17 covers the column), case tracking fields (`last_action`, `last_action_at`, `next_action_required`, `expected_disposal_date`), `TRANSFERRED`/`ESCALATED` statuses with a derived dashboard grouping, a `ComplaintAction` history table, transfer and escalate endpoints, dashboard tiles (total, pending, under process, disposed, transferred, beyond timeline), full search filters, a reports section with CSV export, and PGRC as a seeded bureau (replaces "Grievance Cell"). Build order is unchanged: core first, complaints in Phase 5. M-06 overlap alert and M-11/M-12 are Must for the add-on. No code changed.

## D-17 AICTE Permanent ID and overlap visibility
The `Institution.aicte_code` column keeps its name; the UI/API label is "AICTE Permanent ID" and it gets its own filter (`aicte_id`). Overlap alerts now have a rule-based trigger (2+ bureaus open on one institution) shown with the exact text "Potential Overlapping Cases - Coordination Required". Before confirmation, involved bureaus see the other case's bureau, officer, status, reference and score (needed to coordinate); narrative and shared terms still wait for confirmation, so D-08's leak concern stands for text only. Complainant identity stays masked. Linking is always an officer click.
