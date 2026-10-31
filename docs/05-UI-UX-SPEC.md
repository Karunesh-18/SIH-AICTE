# 05 — UI/UX Specification

## 1. Design principles

- **Calm, dense, trustworthy.** A regulator tool for people who work in it all day: clear hierarchy, tables that scan well, minimal decoration.
- **Status first.** Color plus icon plus text for every status; never color alone.
- **Advisory is visible.** Anything computed (risk, overlap, forecast, OCR) has a small "Suggestion" tag with an info popover explaining how it was derived.
- **One next action.** Each detail page highlights the primary action for the viewer's role.
- **Responsive.** Works at 360 px; tables collapse to cards below 768 px.

## 2. Design tokens

| Token | Value |
|---|---|
| Font | Atkinson Hyperlegible (UI, per D-15), system fallback; Noto Sans Devanagari for Hindi |
| Base size | 14 px body, 12 px meta, 20/24/30 px headings |
| Radius | 8 px cards, 6 px inputs |
| Spacing scale | 4, 8, 12, 16, 24, 32 |
| Primary | `#1F4E8C` (deep blue) |
| Background | `#F7F8FA`, surfaces `#FFFFFF`, border `#E3E6EB` |
| Text | `#1B2430` primary, `#5B6675` secondary |
| Status: Upcoming | `#2F6FB3` blue |
| Status: Due soon | `#B7791F` amber |
| Status: Overdue | `#C0392B` red |
| Status: Fulfilled | `#2E7D4F` green |
| Status: Paused / Waived | `#6B7280` grey |
| Risk bands | Low green, Moderate blue, Elevated amber, High red; always with label |
| Dark mode | Optional; tokens defined as CSS variables from the start |

Contrast must meet WCAG AA. Focus rings visible. All icons have accessible labels.

## 3. Global layout

- Left sidebar (collapses to icon rail, drawer on mobile): navigation by role
- Top bar: global search (institutions, applications, complaints by reference), language toggle (EN/हिंदी), notification bell with unread count, user menu
- Content area with page header: title, breadcrumbs, primary action
- Footer strip on every page: "Prototype with synthetic data. Not an official AICTE system."

### Navigation by role

| Role | Items |
|---|---|
| INSTITUTION | Home, Applications, Documents, Obligations, Complaints (read-only), Notifications |
| SCRUTINY_OFFICER | Work queue, Applications, Documents, Obligations, Notifications |
| REGIONAL_OFFICER | Pendency, Compliance, Applications, EVC calendar, Institutions, Complaints (masked), Risk, Notifications |
| BUREAU_OFFICER | Complaint queue, Overlaps, Institutions, Complaint dashboard, Reports, Notifications |
| ADMIN | All of the above, plus Config, Users, Audit, Demo controls |

## 4. Screens

### 4.1 Login
Email/password, role-based demo account chips below the form (fills credentials for demos; only shown when `DEMO_MODE=true`).

### 4.2 Landing dashboard (officers)
KPI tiles: open applications, SLA breaches, obligations due in 30 days, overdue obligations, open complaints, suspected overlaps. Below: "Needs attention today" list (top 8 across types, each with status chip, institution, days remaining, owner), and a small trend chart of breaches over time.

### 4.3 Pendency dashboard
- Filters: region, workflow, officer
- Stacked bar: applications by stage, segmented on-track / at-risk / breached
- Ageing table: stage, count, average age, oldest, SLA days
- Table of breaching/at-risk applications with forecast chip (heuristic, popover explains)
- Row actions: Open, Escalate (opens note dialog)

### 4.4 Compliance dashboard
- Tiles by obligation type with overdue counts
- 30/60/90-day upcoming bars
- Top institutions by overdue count (click → profile)
- Calendar toggle: month grid with due-date dots; click a day for the list

### 4.5 Applications list and detail
**List:** filterable table with reference, institution, workflow, stage, owner, days left in stage, status.
**Detail:**
- Header: reference, institution, status, current stage chip, SLA countdown
- Horizontal stage stepper (completed, current, upcoming) with SLA days
- Tabs: Overview, History (stage instances with actor/outcome/note), Documents, Obligations, EVC, Audit (admin)
- Action panel (role-aware): Forward, Return for clarification, Escalate, Approve/Reject (final stage only). Each opens a dialog requiring a note where applicable.
- Forecast card: breach likelihood label (Low/Medium/High) with factors list

### 4.6 New application (Institution)
3-step form: Type and program → Description → Documents (upload or select existing) → Review and submit. Shows the stages and SLAs that will apply.

### 4.7 Documents
Table with type, validity, verification status, linked application. Upload dialog with type select. After upload, a **Suggestion card** shows the extracted expiry with a snippet highlighted in the text preview, confidence, and Confirm/Edit/Dismiss buttons.

### 4.8 Obligations
List with status chips, type, due date, days remaining, owner. Detail drawer shows the escalation ladder as a vertical timeline: each step marked sent / upcoming with date. Actions: Fulfil (with evidence), Extend (reason), Waive (reason, regional+).

### 4.9 EVC calendar
Month and list views; create visit dialog (application, date, members, venue). Status chips. Clicking opens the linked application.

### 4.10 Institution profile (hero screen)
- Header: name, code, type, location, status, programs count
- Top strip: open applications, overdue obligations, open complaints (officers), risk badge (officers)
- **Unified timeline** (center): filter chips per event type; each item has icon, title, actor, time; links to the entity
- Right column cards: Upcoming obligations (next 5), Open applications, Complaints summary (officers/bureau), Risk factors (officers)
- Institution users see a filtered version: no complaint details, no risk

### 4.11 Complaint queue (Bureau)
Table: case ID, institution (with AICTE Permanent ID), category, bureau/cell, officer, status, last action (date), next action, expected disposal date, SLA chip, overlap badge. Search box: institution name, AICTE Permanent ID or case ID. Filters: bureau/cell, region, category, status group, beyond timeline, date range. Row opens detail. Export CSV.

### 4.12 Complaint detail
- Header with reference, status, SLA countdown, bureau/officer
- Left: narrative, complainant block (masked unless permitted, with a lock icon and tooltip), notes
- Tracking strip: current bureau/cell, assigned officer, last action and date, next action required, expected disposal date
- Right: **Overlap panel**, headed "Potential Overlapping Cases - Coordination Required" when triggered, listing the other cases with bureau/cell, officer, status and a score label (High/Medium); shared terms appear after confirmation; buttons Link cases / Dismiss
- Actions: Change status, Assign, Transfer (reason required), Escalate (note required), Add note, Raise advisory review flag
- Action history timeline: chronological, with officer/bureau, date and time, remarks, attached documents, transfer and escalation entries

### 4.13 Complaint dashboard
Tiles: total, pending, under process, disposed, transferred, beyond timeline. Below: bureau/cell-wise workload (grouped bar), institution-wise status table (search by name or AICTE Permanent ID), ageing buckets, category bar, region filter, workload per officer, overlap counts, and the table "Institutions handled by 2+ bureaus". Filters: region, bureau/cell, date range.

### 4.13a Reports
Report picker: bureau-wise, region-wise, institution-wise history, pending ageing, disposal rate, overlapping cases, monthly/quarterly performance. Table plus chart per report, CSV download. Role-scoped; no complainant fields.

### 4.14 Institution self-service home
"What needs your attention": next due items (with ladder step reached), applications needing a response, documents expiring soon, complaints raised against the institution (category and status only). A clear Upload button on each expiring item.

### 4.15 Risk view (officers)
Gauge or bar with band label, factor breakdown table (factor, value, weight, contribution), history sparkline, disclaimer text. No automated actions.

### 4.16 Admin
- Stage definitions editor (reorder, SLA, owner role)
- Escalation ladder editor (steps with offsets and recipients)
- Complaint categories
- Users
- Audit viewer with filters and **Verify chain** button (green banner or red banner with first broken entry)
- Demo controls: advance clock by N days, run alert cycle, tamper-audit (dev only)

## 5. Components to build

`StatusChip`, `SlaCountdown`, `StageStepper`, `LadderTimeline`, `SuggestionCard` (with info popover), `MaskedField`, `DataTable` (sortable, paginated, card fallback), `FilterBar`, `KpiTile`, `TimelineList`, `ConfirmDialogWithNote`, `FileUpload`, `EmptyState`, `ErrorState`, `LanguageToggle`, `NotificationBell`.

## 6. Content and i18n

- All user-visible strings in `lib/i18n/{en,hi}.json`
- Hindi coverage required for: navigation, dashboards headings, status labels, notification templates, institution self-service screen
- Dates formatted `DD MMM YYYY`; relative labels ("in 12 days", "3 days overdue")
- Plain language; avoid jargon in institution-facing text

## 7. States and accessibility

- Every list/table: loading skeleton, empty state with guidance, error state with retry
- Dialogs trap focus, ESC closes, destructive actions confirmed
- Keyboard-operable tables and menus
- Announce toasts via `aria-live`
- Test with 200% zoom and 360 px viewport

## 8. Demo polish checklist

- Landing dashboard has no empty tiles on the seeded dataset
- Institution profile for the featured institution shows an overdue obligation, an in-progress application breaching SLA, and two overlapping complaints at different bureaus
- Notification bell shows alerts after advancing the clock
- Footer strip and Suggestion tags visible
