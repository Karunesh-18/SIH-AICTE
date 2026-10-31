# 01 — Product Requirements Document

## 1. Problem

**Approvals (SIH26262).** Institutions apply for approvals and changes that pass through multiple stages across regions. Stage pendency, EVC scheduling and time-bound conditions (undertakings, document renewals) are tracked through manual follow-up and spreadsheets. Result: missed deadlines, expiries noticed late, no single compliance view, weak accountability across handoffs.

**Complaints (SIH26264, "Integrated Institution Complaint Monitoring and Status Dashboard").** Complaints about the same institution reach different bureaus/cells (Regulation Bureau, Public Grievance Redressal Cell and others) with no shared, real-time view. Result: overlapping or conflicting actions, duplicated effort, slow disposal, nobody sure which bureau currently holds a case, no consolidated analytics. Expected outcome: one source of truth for institution-related complaints.

**Shared root cause:** time-bound items and case history are scattered, and there is no unified per-institution record.

## 2. Vision

A single platform where an officer can open any institution and see everything that is pending, upcoming, overdue or under complaint, with timely alerts and clear ownership, while keeping all regulatory decisions with authorised humans.

## 3. Personas

| Persona | Role key | Goals | Key screens |
|---|---|---|---|
| Institution Admin | `INSTITUTION` | See own pending approvals, expiring documents and complaints; upload documents; respond to requests | Institution home, applications, documents, obligations |
| Scrutiny Officer | `SCRUTINY_OFFICER` | Process applications at the scrutiny stage, validate documents | Work queue, application detail |
| Regional Officer | `REGIONAL_OFFICER` | Oversee applications and obligations in a region; schedule EVCs; handle escalations | Pendency dashboard, EVC calendar, escalations |
| Bureau Officer | `BUREAU_OFFICER` | Handle complaints assigned to their bureau/cell (RB, PGRC, others); spot overlaps with other bureaus and coordinate | Complaint queue, case detail, overlap review |
| Admin | `ADMIN` | Configure stages, SLAs, escalation ladders, categories; manage users; run demo clock | Config, users, audit viewer |

## 4. Scope

### 4.1 In scope — Core (SIH26262)

| ID | Requirement | Priority |
|---|---|---|
| C-01 | Role-based login for all personas | Must |
| C-02 | Institution registry with programs and intake | Must |
| C-03 | Application submission by institution (type, program, supporting documents) | Must |
| C-04 | Configurable multi-stage workflow with per-stage SLA and owner role | Must |
| C-05 | Stage-wise status tracking and full transition history | Must |
| C-06 | Officer actions per stage: accept, return for clarification, forward, record outcome. Final decision is recorded by an authorised human | Must |
| C-07 | EVC scheduling: create visit, assign members, date, status, report upload | Must |
| C-08 | Generic obligation engine: document expiry, undertakings, FDR maturity, EVC dates, stage SLAs | Must |
| C-09 | Alert/escalation engine with configurable ladders (for example 90/60/30 days before, on due date, +3 days overdue) | Must |
| C-10 | Pendency dashboard: by stage, region, officer; ageing; breached SLAs | Must |
| C-11 | Compliance dashboard: upcoming/overdue obligations by type, institution, region | Must |
| C-12 | In-app notifications plus email; SMS/WhatsApp stubbed and logged | Must |
| C-13 | Document upload, type tagging, validity dates; OCR-assisted expiry suggestion | Should |
| C-14 | Institution self-service view | Should |
| C-15 | Audit log, hash-chained, with verification endpoint | Must |

### 4.2 In scope — Add-on (SIH26264)

| ID | Requirement | Priority |
|---|---|---|
| M-01 | Register complaint against an institution (category, narrative, source, optional anonymity). Unique case ID and date of receipt | Must |
| M-02 | Assign to bureau/cell (RB, PGRC, others) and officer; transfer between bureaus with reason; escalate with note | Must |
| M-03 | Case tracking: status, assigned bureau/officer, last action and its date, next action required, expected disposal date, full action history with remarks and attachments | Must |
| M-04 | Complaint SLA obligations with the same alert engine (pending reminders, approaching/breached timeline, escalation alerts) | Must |
| M-05 | Institution-level consolidated complaint view across all bureaus, keyed by AICTE Permanent ID | Must |
| M-06 | Cross-bureau overlap detection: rule-based trigger (same institution handled by 2+ bureaus) plus TF-IDF text similarity; shows "Potential Overlapping Cases - Coordination Required" to involved bureaus; officer links or dismisses | Must (alert) / Should (text similarity) |
| M-07 | Real-time complaint dashboard: total, pending, under process, disposed, transferred, beyond timeline; institution-wise status; bureau/cell-wise workload; ageing | Must |
| M-11 | Search and filters: institution name, AICTE Permanent ID, case ID, bureau/cell, region, category, status, date range | Must |
| M-12 | Reports: bureau-wise, region-wise, institution-wise history, pending ageing, disposal rate, overlapping/duplicate cases, monthly/quarterly performance; CSV export | Must |
| M-08 | Complainant privacy masking enforced server-side | Must |
| M-09 | Complaint-to-approval review flag (advisory prompt for an officer, never automatic action) | Could |
| M-10 | Public complaint portal: submit without login, get a tracking ID, mocked email verification, look up status; officer registers or rejects as frivolous (see DECISIONS D-05) | Should |

### 4.3 In scope — Shared intelligence

| ID | Requirement | Priority |
|---|---|---|
| S-01 | Institution profile with unified timeline (applications, documents, obligations, complaints, EVCs, notes) | Must |
| S-02 | Explainable risk view per institution (advisory) | Should |
| S-03 | Heuristic SLA-breach forecast for open applications | Could |
| S-04 | Hindi UI toggle for core screens and notification templates | Could |

### 4.4 Out of scope

- Real AICTE data, handbook ingestion, authentication via government SSO
- Student-level data / APAAR integration (SIH26263), automated document authenticity verification against issuers (SIH26261), bank/FDR API integration (SIH26265). These appear only on the roadmap slide. FDR maturity is supported as a manually entered obligation type.
- Any automated regulatory decision or penalty
- Payment processing

## 5. Key user stories

1. As a **Regional Officer**, I open the pendency dashboard and see which applications are about to breach the stage SLA, sorted by days left, and escalate one with a note.
2. As an **Institution Admin**, I upload a lease deed; the system suggests an expiry date, I confirm it, and I receive reminders at 90/60/30 days.
3. As a **Scrutiny Officer**, I return an application for clarification; the stage SLA clock pauses and the institution is notified.
4. As a **Bureau Officer**, I register a complaint; the system shows two similar open complaints at another bureau for the same institution; I confirm one as overlapping and link the cases so both officers see it.
5. As a **Regional Officer**, I open an institution profile and see approvals, expiring documents, open complaints and risk factors on one timeline.
6. As an **Admin**, I change a stage's SLA from 10 to 7 days and the new value applies to newly created stage instances.
8. As a **member of the public**, I submit a complaint through the portal, receive a tracking ID, and see its status (not internal notes). An officer reviews it before it becomes a registered case.
7. As an **Admin**, I verify the audit chain and see it report intact; if a row was tampered with, it reports the first broken entry.

## 6. Non-functional requirements

| Area | Requirement |
|---|---|
| Security | Server-side RBAC, bcrypt, JWT expiry, input validation, upload type/size limits, no secrets in repo |
| Privacy | Complainant masking, need-to-know access to complaint narratives |
| Auditability | Hash-chained log of all state changes with actor, time, before/after |
| Performance | Dashboards render under 2 s for the seeded dataset (about 15 institutions, 60 applications, 200 obligations, 40 complaints) |
| Usability | Responsive down to 360 px; keyboard accessible; WCAG AA contrast; English plus Hindi toggle |
| Reliability | Alert jobs idempotent: the same escalation step never sends twice for the same obligation |
| Demo | Simulated clock lets the presenter advance time to trigger alerts live |

## 7. Success criteria

- A judge can log in as three roles and complete: submit application → advance stages → see SLA alert → open institution profile within 5 minutes
- Obligation alerts fire at the correct ladder steps under the simulated clock, verified by tests
- Complaint overlap detection surfaces a seeded cross-bureau duplicate with an explanation
- Audit verification passes, and fails visibly when a row is edited manually
- No feature takes an irreversible regulatory action without an explicit human step

## 8. Risks

| Risk | Mitigation |
|---|---|
| Real rules differ from our defaults | All rules configurable; label defaults as illustrative |
| Over-claiming AI | Label methods plainly; show explanations |
| Scope creep into related SIH statements | Roadmap slide only |
| False complaints | Complainant verification flag, reliability note, officer confirmation before linking |
| Risk score bias or misuse | Advisory label, visible factors, no automated consequences |
