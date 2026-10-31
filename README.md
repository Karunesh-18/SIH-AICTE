# Waymark — Spec Pack

A documentation pack for building **Waymark**, a unified approval-workflow, compliance-monitoring and complaint-tracking platform concept for an AICTE-style regulator.

- **Core:** SIH26262 — Integrated AICTE Approval Workflow Automation, Compliance Monitoring and Alert Management System
- **Add-on module:** SIH26264 — Integrated Institution Complaint Monitoring and Status Dashboard (complaint cases across AICTE Bureaus/Cells such as RB and PGRC). Our entry is SIH26262; this module extends it.

> Confirm the hackathon's rules on whether one entry may cover both problem statements before describing this as satisfying both. Check the official problem statement text for exact requirements; the docs here are based on summaries.

## Idea in one paragraph

Approvals, document renewals, financial instruments, inspections and complaints are all the same thing underneath: something with an owner, a due date and an escalation path. Waymark models them as **obligations** on a single **institution timeline**, runs one alert engine over them, and layers advisory intelligence (expiry extraction, duplicate-complaint detection, explainable risk, SLA-breach forecast) on top. Humans make every decision.

## Pack contents

| File | Purpose |
|---|---|
| `CLAUDE.md` | Entry point and rules for Claude Code |
| `docs/01-PRD.md` | Product requirements, personas, scope |
| `docs/02-ARCHITECTURE.md` | System design, flows, security |
| `docs/03-DATA-MODEL.md` | Entities, enums, audit chain |
| `docs/04-API-SPEC.md` | REST endpoints, permission matrix |
| `docs/05-UI-UX-SPEC.md` | Screens, components, design tokens |
| `docs/06-AI-MODULES.md` | OCR, similarity, risk, forecast |
| `docs/07-BUILD-PLAN.md` | Phased build tasks with acceptance criteria |
| `docs/08-SEED-DATA-AND-DEMO.md` | Fictional dataset, accounts, demo script |

## How to use with Claude Code

1. Create an empty repo folder named `waymark`.
2. Copy `CLAUDE.md`, `README.md` and the `docs/` folder into it.
3. Open Claude Code in that folder and say:
   *"Read CLAUDE.md and everything in docs/, then start Phase 0 of docs/07-BUILD-PLAN.md. Keep docs/PROGRESS.md updated."*
4. Review at the end of each phase before continuing.

## For teammates

Start with `docs/DECISIONS.md` (what changed and why), then `docs/PROGRESS.md` (what is done and where help is needed). Only one person writes code; everyone else can review stage names and SLAs against the real handbook, write Hindi strings, and prepare the roadmap slide and judge Q&A. Name: **Waymark** (see D-01).

## Honest limits

- No access to real AICTE systems, handbooks or data. Stage names, SLAs and rules are **illustrative defaults** that Admin can configure; verify against the real Approval Process Handbook.
- All institutions, users and complaints are fictional.
- Integrations (AICTE portal, bank APIs, SMS gateways) are represented by interfaces and stubs.
- The related problem statements SIH26261 (document verification), SIH26263 (student data) and SIH26265 (financial instruments) are **roadmap integration points**, not claimed features.
