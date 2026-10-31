# 04 — API Specification

Base URL: `/api/v1`. JSON in/out. Auth: `Authorization: Bearer <access_token>`. Errors use `{ "error": { "code": "...", "message": "...", "details": {} } }` with proper HTTP status codes. Lists use `?page=1&page_size=20` and return `{ items, total, page, page_size }`.

## 1. Permission matrix

Legend: ✔ allowed, 🔸 scoped (own institution / own region / assigned), ✖ denied.

| Resource / action | INSTITUTION | SCRUTINY | REGIONAL | BUREAU | ADMIN |
|---|---|---|---|---|---|
| View institutions | 🔸 own | 🔸 region | 🔸 region | 🔸 limited | ✔ |
| Create application | 🔸 own | ✖ | ✖ | ✖ | ✔ |
| Transition application | ✖ (can respond when awaiting) | 🔸 stage owner | 🔸 stage owner | ✖ | ✔ |
| View applications | 🔸 own | ✔ | 🔸 region | ✖ | ✔ |
| Upload documents | 🔸 own | ✔ | ✔ | ✖ | ✔ |
| Confirm OCR suggestion | 🔸 own | ✔ | ✔ | ✖ | ✔ |
| View obligations | 🔸 own | ✔ | 🔸 region | 🔸 complaint SLA | ✔ |
| Fulfil / waive obligation | fulfil own docs only | ✔ fulfil | ✔ fulfil, ✔ waive | ✖ | ✔ |
| Schedule EVC | ✖ | ✖ | ✔ | ✖ | ✔ |
| Register complaint | ✖ | ✖ | ✔ | ✔ | ✔ |
| View complaint (full) | ✖ | ✖ | 🔸 masked | 🔸 bureau / linked | ✔ |
| Assign / transfer complaint | ✖ | ✖ | ✖ | 🔸 own bureau | ✔ |
| Confirm / dismiss overlap | ✖ | ✖ | ✖ | 🔸 involved bureau | ✔ |
| Institution profile | 🔸 own (filtered) | ✔ | 🔸 region | 🔸 complaint view | ✔ |
| Risk view | ✖ | ✖ | ✔ | ✖ | ✔ |
| Dashboards | own summary | pendency | pendency + compliance | complaints | all |
| Config (stages, ladders, categories) | ✖ | ✖ | ✖ | ✖ | ✔ |
| Audit log, verify, clock | ✖ | ✖ | ✖ | ✖ | ✔ |

## 2. Endpoints

### 2.1 Auth
| Method | Path | Notes |
|---|---|---|
| POST | `/auth/login` | `{email,password}` → `{access_token, refresh_token, user}` |
| POST | `/auth/refresh` | refresh token → new access token |
| GET | `/auth/me` | current user |
| PATCH | `/auth/me` | update `language` |

### 2.2 Institutions
| Method | Path | Notes |
|---|---|---|
| GET | `/institutions` | filters: `q` (name), `aicte_id` (AICTE Permanent ID, exact or prefix), `state`, `region_id`, `type`, `has_overdue`, `risk_band` |
| GET | `/institutions/{id}` | summary, programs, counts |
| GET | `/institutions/{id}/timeline` | `?types=&from=&to=`; visibility filtered by role |
| GET | `/institutions/{id}/profile` | aggregated: open applications, obligations by status, complaints summary, latest risk snapshot (officers only) |
| POST | `/institutions` | Admin |
| POST | `/institutions/{id}/programs` | Admin, Institution own |

### 2.3 Applications and workflow
| Method | Path | Notes |
|---|---|---|
| GET | `/applications` | filters: `status`, `stage_id`, `region_id`, `institution_id`, `breaching`, `assigned_to_me` |
| POST | `/applications` | create and submit. Body: `institution_id, workflow_key, program_id?, title, description, document_ids[]` |
| GET | `/applications/{id}` | detail incl. stage instances, documents, obligations, EVC |
| POST | `/applications/{id}/transition` | `{action: FORWARD|RETURN|APPROVE|REJECT|ESCALATE, note}` (note required for RETURN/REJECT/ESCALATE) |
| POST | `/applications/{id}/respond` | Institution responds to a return; resumes SLA |
| GET | `/applications/{id}/forecast` | heuristic breach probability with factors |
| GET | `/workflows` | list workflow keys and stages |
| GET/POST/PATCH | `/admin/stage-definitions` | Admin CRUD; changes apply to new stage instances only |

### 2.4 EVC
| Method | Path | Notes |
|---|---|---|
| GET | `/evc` | filters: `status`, `from`, `to`, `region_id` |
| POST | `/evc` | `{application_id, scheduled_for, members[], venue_note}` creates `EVC_VISIT` obligation |
| PATCH | `/evc/{id}` | status changes, reschedule, attach report |

### 2.5 Documents and suggestions
| Method | Path | Notes |
|---|---|---|
| POST | `/documents` | multipart: `file`, `institution_id`, `doc_type`, `application_id?`, optional `valid_until`. Runs OCR/extraction and may create a suggestion |
| GET | `/documents` | filters |
| GET | `/documents/{id}/file` | authenticated download |
| GET | `/suggestions` | pending obligation suggestions (scoped) |
| POST | `/suggestions/{id}/confirm` | `{due_at, title?}` → creates obligation |
| POST | `/suggestions/{id}/dismiss` | `{reason}` |

### 2.6 Obligations and alerts
| Method | Path | Notes |
|---|---|---|
| GET | `/obligations` | filters: `status`, `type`, `institution_id`, `region_id`, `due_before`, `owner_me`; sort by `due_at` |
| POST | `/obligations` | manual create (undertaking, FDR maturity, custom) |
| GET | `/obligations/{id}` | incl. alert log |
| POST | `/obligations/{id}/fulfil` | `{note, evidence_document_id?}` |
| POST | `/obligations/{id}/waive` | `{reason}` (reason required, regional+ only) |
| POST | `/obligations/{id}/extend` | `{new_due_at, reason}` writes audit |
| GET | `/obligations/calendar` | `?month=YYYY-MM` grouped by date |
| GET | `/notifications` | current user; `?unread=true` |
| POST | `/notifications/{id}/read` | mark read |

### 2.7 Complaints
| Method | Path | Notes |
|---|---|---|
| GET | `/complaints` | filters: `q` (institution name), `aicte_id`, `case_id` (reference_no), `institution_id`, `bureau_id`, `region_id`, `status`, `group` (`PENDING|UNDER_PROCESS|TRANSFERRED|DISPOSED`), `category_id`, `beyond_timeline` (bool), `aged_over_days`, `received_from`, `received_to`; masked per role |
| POST | `/complaints` | register. Triggers SLA obligation, `expected_disposal_date`, and overlap check |
| GET | `/complaints/{id}` | masked per role; includes `last_action`, `last_action_at`, `next_action_required`, `expected_disposal_date`, `overlap_alert` |
| GET | `/complaints/{id}/actions` | chronological action history (actor, bureau, timestamp, remarks, document, from/to bureau) |
| PATCH | `/complaints/{id}/status` | `{status, note, next_action_required?}` |
| PATCH | `/complaints/{id}/expected-disposal` | `{date, reason}`; audited |
| POST | `/complaints/{id}/assign` | `{bureau_id, officer_id?, reason}` (first assignment, or officer change inside a bureau) |
| POST | `/complaints/{id}/transfer` | `{to_bureau_id, officer_id?, reason}` (reason required; status `TRANSFERRED` until accepted; writes `ComplaintAction`) |
| POST | `/complaints/{id}/escalate` | `{to_role_or_user, note}` (note of 10+ characters; status `ESCALATED`) |
| POST | `/complaints/{id}/notes` | internal note |
| GET | `/complaints/{id}/overlaps` | suggested and confirmed links with explanations |
| POST | `/complaint-links/{id}/confirm` | confirm overlap |
| POST | `/complaint-links/{id}/dismiss` | `{reason}` |
| POST | `/complaints/{id}/review-flag` | officer raises advisory review flag toward an application or institution |
| GET | `/institutions/{id}/complaints` | consolidated cross-bureau view |
| GET | `/complaint-categories` | list |

### 2.7a Public portal (no auth, rate limited)
| Method | Path | Notes |
|---|---|---|
| POST | `/public/complaints` | submit; returns `tracking_id`; sends mocked verification email |
| POST | `/public/complaints/verify` | `{tracking_id, token}` marks email verified |
| POST | `/public/complaints/status` | `{tracking_id, email}` returns status and category only |
| GET | `/portal-submissions` | Bureau/Admin; pending review queue |
| POST | `/portal-submissions/{id}/register` | creates the Complaint (links `complaint_id`) |
| POST | `/portal-submissions/{id}/reject` | `{reason}` required |

### 2.8 Dashboards
| Method | Path | Returns |
|---|---|---|
| GET | `/dashboards/pendency` | counts and ageing by stage, region, officer; list of breaching/at-risk applications |
| GET | `/dashboards/compliance` | obligations by type and status, 30/60/90-day upcoming, top overdue institutions |
| GET | `/dashboards/complaints` | `?region_id=&bureau_id=&from=&to=`. Returns `totals` (total, pending, under_process, disposed, transferred, beyond_timeline), `by_bureau` (workload per bureau/cell with the same counts), `by_institution` (status counts per institution, with `bureaus_involved`), `by_region`, ageing buckets, category counts, workload per officer, overlap counts, institutions handled by 2+ bureaus |

### 2.8a Complaint reports
| Method | Path | Notes |
|---|---|---|
| GET | `/reports/complaints/bureau` | per bureau/cell: received, disposed, pending, disposal rate, average age |
| GET | `/reports/complaints/region` | same measures per region |
| GET | `/reports/complaints/institution/{id}` | institution-wise complaint history across bureaus |
| GET | `/reports/complaints/ageing` | pending cases in age buckets (0-15, 16-30, 31-60, 60+ days) |
| GET | `/reports/complaints/disposal-rate` | disposal rate over time |
| GET | `/reports/complaints/overlaps` | confirmed and suggested overlap/duplicate cases |
| GET | `/reports/complaints/periodic` | `?period=monthly|quarterly&year=` performance summary |

All report endpoints accept `?format=json|csv`, are scoped by role like the complaint list (masked fields never appear in reports), and write an audit entry on export.
| GET | `/dashboards/institution-home` | for INSTITUTION: next due items, open applications, open complaints (public fields) |
| GET | `/dashboards/summary` | headline KPIs for the landing page |

### 2.9 Risk
| Method | Path | Notes |
|---|---|---|
| GET | `/institutions/{id}/risk` | latest snapshot with factors and history |
| POST | `/institutions/{id}/risk/recompute` | Regional/Admin |

### 2.10 Admin
| Method | Path | Notes |
|---|---|---|
| GET/PATCH | `/admin/ladders` | escalation ladders |
| GET/PATCH | `/admin/config` | system config keys |
| GET/POST/PATCH | `/admin/users` | user management |
| GET/POST/PATCH | `/admin/complaint-categories` | CRUD |
| GET | `/admin/audit` | filters `entity_type`, `entity_id`, `actor_id`, `from`, `to` |
| POST | `/admin/audit/verify` | `{ok, count, first_broken_id?}` |
| POST | `/admin/dev/tamper-audit` | dev only; modifies one row to demonstrate failure |
| GET/POST | `/admin/clock` | read or set simulated-time offset; `POST {advance_days}` |
| POST | `/admin/alert-cycle/run` | run alert cycle now, returns counts |
| GET | `/admin/alert-cycle/last` | last run stats |
| GET | `/health` | liveness |

## 3. Key response shapes

**Obligation**
```json
{
  "id": "…", "institution": {"id":"…","name":"…"},
  "type": "DOCUMENT_EXPIRY", "title": "Lease deed validity",
  "due_at": "2027-01-15T00:00:00Z", "status": "DUE_SOON",
  "days_remaining": 80, "owner_role": "INSTITUTION",
  "source": "OCR_CONFIRMED",
  "next_alert": {"step":"T-60","at":"2026-11-16T00:00:00Z"},
  "alerts_sent": [{"step":"T-90","sent_at":"…"}]
}
```

**Complaint (masked for REGIONAL_OFFICER)**
```json
{
  "id":"…","reference_no":"CMP-2026-0007",
  "institution":{…}, "category":{…}, "status":"UNDER_REVIEW",
  "current_bureau":{…}, "received_at":"…", "age_days": 12,
  "title":"Fee refund not processed",
  "narrative":"[redacted for your role]",
  "complainant":{"masked":true},
  "linked_cases":[{"reference_no":"CMP-2026-0003","bureau":"Grievance Cell","status":"CONFIRMED"}]
}
```

**Overlap suggestion**
```json
{
  "alert":"Potential Overlapping Cases - Coordination Required",
  "trigger":"multi_bureau_same_institution",
  "id":"…","status":"SUGGESTED","score":0.62,
  "other_complaint":{"reference_no":"CMP-2026-0003","bureau":"Grievance Cell"},
  "explanation":{
    "method":"tfidf_cosine",
    "shared_terms":["refund","fee","admission","2025"],
    "same_category":true,
    "days_apart":9,
    "note":"Suggestion only. An officer must confirm."
  }
}
```

**Risk snapshot**
```json
{
  "score":58,"band":"ELEVATED","method_version":"rules-v1",
  "factors":[
    {"key":"overdue_obligations","label":"Overdue obligations","value":3,"weight":15,"contribution":30},
    {"key":"open_complaints","label":"Open complaints","value":2,"weight":8,"contribution":16}
  ],
  "disclaimer":"Advisory prioritisation aid. Not a regulatory finding."
}
```

## 4. Validation and rules to enforce server-side

- Transition: `RETURN`, `REJECT`, `ESCALATE` require a note of at least 10 characters
- Only the final stage's owner role can `APPROVE`/`REJECT`; both require a note
- `waive` requires reason and is denied for `INSTITUTION`
- Extending a due date writes before/after into the audit log
- Complaint masking applied in the serializer using `(viewer.role, viewer.bureau_id, link status)`
- Institution users never receive complaint narrative, complainant fields, internal notes, overlap suggestions or risk data
- Uploads: allowed mime types, 10 MB max
