# 03 — Data Model

Conventions: UUID primary keys (string), `created_at`/`updated_at` on all tables, all timestamps UTC, soft-delete not used. Enums stored as strings. Names below are SQLAlchemy model/table names.

## 1. Enums

| Enum | Values |
|---|---|
| `Role` | `INSTITUTION`, `SCRUTINY_OFFICER`, `REGIONAL_OFFICER`, `BUREAU_OFFICER`, `ADMIN` |
| `ApplicationStatus` | `DRAFT`, `IN_PROGRESS`, `AWAITING_INSTITUTION`, `APPROVED`, `REJECTED`, `WITHDRAWN` |
| `StageOutcome` | `FORWARDED`, `RETURNED`, `APPROVED`, `REJECTED`, `ESCALATED` |
| `ObligationType` | `DOCUMENT_EXPIRY`, `UNDERTAKING`, `FDR_MATURITY`, `EVC_VISIT`, `STAGE_SLA`, `COMPLAINT_SLA`, `CUSTOM` |
| `ObligationStatus` | `UPCOMING`, `DUE_SOON`, `OVERDUE`, `FULFILLED`, `WAIVED`, `PAUSED` |
| `ObligationSource` | `MANUAL`, `SYSTEM`, `OCR_CONFIRMED` |
| `ComplaintStatus` | `REGISTERED`, `ASSIGNED`, `UNDER_REVIEW`, `ACTION_INITIATED`, `TRANSFERRED`, `ESCALATED`, `RESOLVED`, `CLOSED`, `REJECTED_FRIVOLOUS` |
| `ComplaintGroup` (dashboard, derived) | Pending = `REGISTERED`, `ASSIGNED`; Under process = `UNDER_REVIEW`, `ACTION_INITIATED`, `ESCALATED`; Transferred = `TRANSFERRED` (shown until the receiving bureau accepts, then `ASSIGNED`); Disposed = `RESOLVED`, `CLOSED`, `REJECTED_FRIVOLOUS`. "Beyond timeline" is a flag (open and past `expected_disposal_date`), not a status |
| `ComplaintActionType` | `REGISTERED`, `ASSIGNED`, `TRANSFERRED`, `ESCALATED`, `STATUS_CHANGED`, `NOTE`, `LINKED`, `DISPOSED` |
| `LinkStatus` | `SUGGESTED`, `CONFIRMED`, `DISMISSED` |
| `EvcStatus` | `PLANNED`, `CONFIRMED`, `COMPLETED`, `REPORT_SUBMITTED`, `CANCELLED` |
| `NotificationChannel` | `IN_APP`, `EMAIL`, `SMS`, `WHATSAPP` |
| `SuggestionStatus` | `PENDING`, `CONFIRMED`, `DISMISSED` |
| `RiskBand` | `LOW`, `MODERATE`, `ELEVATED`, `HIGH` |

Cross-cutting columns: `version` (int, optimistic lock) on Application, Obligation, Complaint. `Outbox` table (id, kind, payload JSON, created_at, dispatched_at?) feeds notifications after commit. `ObligationAlertLog.status` is `SENT` or `SKIPPED`. Document expiry (`valid_until`, document obligations' due date) is a `date` evaluated in IST; SLA days are business days using a holiday list in `system_config` (D-10).

## 2. Entities

### 2.1 Identity and organisation

**User**: `id`, `email` (unique), `password_hash`, `full_name`, `role`, `institution_id?` (for INSTITUTION), `region_id?`, `bureau_id?`, `language` (`en|hi`), `is_active`.

**Region**: `id`, `name` (for example "Southern", "Western"), `code`.

**Bureau**: `id`, `name` (for example "Regulation Bureau", "Public Grievance Redressal Cell"), `code` (`RB`, `PGRC`, ...), `kind` (`BUREAU|CELL`).

**Institution**: `id`, `aicte_code` (the **AICTE Permanent ID**; fictional, unique, searchable; column name kept, label everywhere is "AICTE Permanent ID"), `address`, `name`, `type` (`ENGINEERING|MANAGEMENT|PHARMACY|OTHER`), `state`, `city`, `region_id`, `contact_email`, `status` (`ACTIVE|UNDER_REVIEW`), `established_year`.

**Program**: `id`, `institution_id`, `name`, `level` (`UG|PG|DIPLOMA`), `approved_intake`, `start_year`.

### 2.2 Workflow

**StageDefinition** (configurable): `id`, `workflow_key` (for example `NEW_PROGRAM`, `INTAKE_CHANGE`, `RENEWAL`), `order`, `name`, `owner_role`, `sla_days`, `allowed_actions` (JSON list from `FORWARD`, `RETURN`, `APPROVE`, `REJECT`, `ESCALATE`), `is_final`.

**Application**: `id`, `reference_no` (unique, e.g. `APP-2026-0001`), `institution_id`, `program_id?`, `workflow_key`, `title`, `description`, `status`, `current_stage_id?`, `submitted_at`, `closed_at?`, `final_decision_by?`, `final_decision_note?`.

**StageInstance**: `id`, `application_id`, `stage_definition_id`, `opened_at`, `closed_at?`, `assigned_user_id?`, `outcome?`, `actor_id?`, `note?`, `sla_due_at`, `paused_seconds` (total pause time).

**EvcVisit**: `id`, `application_id`, `institution_id`, `scheduled_for`, `status`, `members` (JSON list of names/user ids), `venue_note?`, `report_document_id?`, `created_by`.

### 2.3 Obligations and alerts

**EscalationLadder**: `id`, `key` (unique, for example `DOCUMENT_EXPIRY_DEFAULT`), `obligation_type`, `steps` (JSON), e.g.
```json
[
  {"key":"T-90","days_offset":-90,"notify":["INSTITUTION"],"template":"expiry_reminder"},
  {"key":"T-60","days_offset":-60,"notify":["INSTITUTION"],"template":"expiry_reminder"},
  {"key":"T-30","days_offset":-30,"notify":["INSTITUTION","SCRUTINY_OFFICER"],"template":"expiry_reminder"},
  {"key":"T0","days_offset":0,"notify":["REGIONAL_OFFICER"],"template":"obligation_due"},
  {"key":"T+3","days_offset":3,"notify":["REGIONAL_OFFICER"],"template":"obligation_overdue"},
  {"key":"T+10","days_offset":10,"notify":["ADMIN"],"template":"obligation_escalated"}
]
```
Stage SLA and complaint SLA ladders use hour/day offsets suited to their shorter cycles (for example `-2d`, `0`, `+1d`).

**Obligation**: `id`, `institution_id`, `type`, `title`, `description?`, `due_at`, `status`, `owner_role`, `owner_user_id?`, `ladder_key`, `source`, `application_id?`, `complaint_id?`, `document_id?`, `fulfilled_at?`, `fulfilled_by?`, `waived_at?`, `waived_by?`, `waive_reason?`, `paused_at?`, `last_evaluated_at`.
Index: `(institution_id, status)`, `(due_at)`, `(type, status)`.

**ObligationAlertLog**: `id`, `obligation_id`, `step_key`, `sent_at`, `recipients` (JSON). **Unique `(obligation_id, step_key)`.**

**Notification**: `id`, `user_id`, `channel`, `subject`, `body`, `lang`, `related_type?`, `related_id?`, `status` (`QUEUED|SENT|FAILED|LOGGED`), `read_at?`, `sent_at?`.

### 2.4 Documents

**Document**: `id`, `institution_id`, `application_id?`, `doc_type` (for example `LEASE_DEED`, `LAND_USE_CERT`, `FIRE_NOC`, `AUDITED_STATEMENT`, `AFFIDAVIT`, `FDR_COPY`, `EVC_REPORT`, `OTHER`), `filename_original`, `storage_path`, `mime`, `size_bytes`, `uploaded_by`, `valid_from?`, `valid_until?`, `verification_status` (`UNVERIFIED|OFFICER_CONFIRMED|FLAGGED`), `extracted_text?`.

**ObligationSuggestion**: `id`, `document_id`, `suggested_type`, `suggested_title`, `suggested_due_at?`, `confidence` (0 to 1), `evidence` (JSON: matched snippet and method), `status`, `resolved_by?`, `resolved_at?`.

### 2.5 Complaints

**ComplaintCategory**: `id`, `key`, `label_en`, `label_hi`, `default_bureau_id?`, `sla_days`.

**Complaint**: `id`, `reference_no` (e.g. `CMP-2026-0001`), `institution_id`, `category_id`, `title`, `narrative`, `received_at`, `source` (`PORTAL|EMAIL|LETTER|OTHER`), `status`, `is_anonymous`, `complainant_name?`, `complainant_contact?`, `complainant_verified` (bool), `severity` (1 to 3), `current_bureau_id`, `current_officer_id?`, `last_action?` (text), `last_action_at?`, `next_action_required?` (text), `expected_disposal_date` (defaults to `received_at + category.sla_days` in business days; officer may revise with a reason, audited), `closed_at?`, `resolution_note?`. `region_id` is not stored; it is read from the institution.

**PortalSubmission** (public intake): `id`, `tracking_id` (unique, random, e.g. `PUB-7K3QX9`), `institution_id`, `category_id?`, `title`, `narrative`, `submitter_name?`, `submitter_email`, `email_verified` (bool, mocked), `status` (`PENDING_VERIFICATION|PENDING_REVIEW|REGISTERED|REJECTED`), `complaint_id?`, `rejection_reason?`, `reviewed_by?`. Public status lookup needs `tracking_id` + `submitter_email` and returns status only.

**ComplaintAssignment** (history): `id`, `complaint_id`, `bureau_id`, `officer_id?`, `assigned_at`, `assigned_by`, `reason?`, `ended_at?`.

**ComplaintNote**: `id`, `complaint_id`, `author_id`, `body`, `visibility` (`INTERNAL|BUREAU_ONLY`).

**ComplaintAction** (chronological action history; written by the same single event writer as the audit log, D-11): `id`, `complaint_id`, `action_type`, `actor_id`, `bureau_id`, `from_bureau_id?`, `to_bureau_id?`, `remarks?`, `document_id?` (supporting document), `occurred_at`. Updates `Complaint.last_action`, `last_action_at` in the same transaction.

**ComplaintLink**: `id`, `complaint_a_id`, `complaint_b_id`, `status`, `score`, `explanation` (JSON: shared terms, same category, date proximity), `resolved_by?`, `resolved_at?`. Unique on the unordered pair.

**ReviewFlag** (M-09): `id`, `institution_id`, `application_id?`, `complaint_id`, `reason`, `status` (`OPEN|ACKNOWLEDGED|DISMISSED`), `raised_by`, `resolved_by?`. Raised by a human officer from a complaint; the system only offers a "suggest flag" button.

### 2.6 Timeline, risk, audit, config

**InstitutionEvent** (timeline): `id`, `institution_id`, `event_type` (`APPLICATION`, `STAGE`, `DOCUMENT`, `OBLIGATION`, `ALERT`, `COMPLAINT`, `EVC`, `NOTE`, `RISK`), `title`, `detail?`, `related_type`, `related_id`, `occurred_at`, `actor_id?`, `visibility` (`ALL`, `OFFICERS`, `BUREAU`). Visibility is applied when listing.

**RiskSnapshot**: `id`, `institution_id`, `computed_at`, `score` (0 to 100), `band`, `factors` (JSON list of `{key,label,value,weight,contribution}`), `method_version`.

**AuditLog**: `id` (autoincrement int, for ordering), `occurred_at`, `actor_id?`, `actor_role?`, `action` (e.g. `APPLICATION.TRANSITION`), `entity_type`, `entity_id`, `before` (JSON), `after` (JSON), `prev_hash`, `hash`.

**SystemConfig**: `key` (PK), `value` (JSON), `updated_by`, `updated_at`.

## 3. Audit chain

```
canonical = json.dumps({id, occurred_at, actor_id, action, entity_type,
                        entity_id, before, after}, sort_keys=True, separators=(",", ":"))
hash = sha256(prev_hash + canonical)
```
- Genesis row uses `prev_hash = "0"*64`.
- `append()` runs inside the same DB transaction as the state change.
- `verify()` walks rows by `id`, recomputes, returns `{ok: true, count}` or `{ok: false, first_broken_id}`.
- Provide a dev-only endpoint/script that tampers with a row, so the demo can show verification failing.

## 4. Status computation (pure function)

```
def obligation_status(o, now, due_soon_days=30):
    if o.waived_at: return WAIVED
    if o.fulfilled_at: return FULFILLED
    if o.paused_at: return PAUSED
    if now > o.due_at: return OVERDUE
    if (o.due_at - now).days <= due_soon_days: return DUE_SOON
    return UPCOMING
```
`due_soon_days` is per-type config (default 30 for documents, 3 for stage SLA, 5 for complaints).

## 5. Relationships summary

```
Institution 1─* Program
Institution 1─* Application 1─* StageInstance *─1 StageDefinition
Application 1─* EvcVisit
Institution 1─* Document 1─* ObligationSuggestion
Institution 1─* Obligation 1─* ObligationAlertLog
Institution 1─* Complaint 1─* ComplaintAssignment, ComplaintAction
Complaint *─* Complaint (ComplaintLink)
Institution 1─* InstitutionEvent, RiskSnapshot
```

## 6. Seeded configuration (illustrative defaults, Admin-editable)

Workflow `NEW_PROGRAM` / `INTAKE_CHANGE` default stages:

| Order | Stage | Owner role | SLA (days) |
|---|---|---|---|
| 1 | Submission check | `SCRUTINY_OFFICER` | 3 |
| 2 | Document scrutiny | `SCRUTINY_OFFICER` | 10 |
| 3 | EVC scheduling | `REGIONAL_OFFICER` | 7 |
| 4 | EVC visit and report | `REGIONAL_OFFICER` | 15 |
| 5 | Committee review (SAC/SHC) | `REGIONAL_OFFICER` | 10 |
| 6 | Final decision (human) | `ADMIN` | 5 |

These numbers are placeholders for the prototype. Real values must come from the official handbook.
