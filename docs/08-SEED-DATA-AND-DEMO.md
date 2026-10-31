# 08 — Seed Data and Demo Script

All data is **fictional**. Institution names are invented; do not use real institutions, people or real complaint content. Seed script must be idempotent (`make seed`) and have a reset (`make reset`).

## 1. Reference data

**Regions:** Northern, Southern, Eastern, Western, Central (codes N, S, E, W, C)

**Bureaus/cells:** Regulation Bureau (RB), Public Grievance Redressal Cell (PGRC), Approval Bureau (AB), Quality Monitoring Cell (QMC). PGRC replaces the earlier "Grievance Cell (GC)"; wherever this pack still says GC, read PGRC.

**Complaint categories (with default bureau, SLA days):**

| Key | Label | Default bureau | SLA days |
|---|---|---|---|
| `FEE_REFUND` | Fee refund / fee irregularity | GC | 20 |
| `INTAKE_VIOLATION` | Admission beyond approved intake | RB | 30 |
| `FACULTY` | Faculty shortage / qualification | QMC | 30 |
| `INFRA` | Infrastructure deficiency | QMC | 30 |
| `UNAPPROVED_PROGRAM` | Unapproved program / course | RB | 30 |
| `HARASSMENT` | Harassment / discipline | GC | 15 |
| `OTHER` | Other | GC | 25 |

## 2. Institutions (15, fictional)

Use names like: *Northfield Institute of Technology, Kaveri Valley College of Engineering, Brahmaputra School of Management, Sahyadri Institute of Pharmacy, Thar Desert Polytechnic, Narmada Technical Campus, Lakeview Institute of Management, Deccan Plateau Engineering College, Vindhya Institute of Technology, Coastal Bay College of Engineering, Himalayan Foothills Institute, Gangetic Plains Management Institute, Malabar Pharmacy College, Aravalli Technical University College, Eastern Ghats Institute of Technology.* Fictional AICTE Permanent IDs `FX-1001` to `FX-1015`, each with a made-up address. Spread across regions and states.

**Featured institution (used in the demo):** *Kaveri Valley College of Engineering* (`FX-1002`, Southern region).

## 3. Users (demo accounts; passwords shown only for demo mode)

| Email | Role | Scope | Password |
|---|---|---|---|
| `inst.kaveri@demo.test` | INSTITUTION | Kaveri Valley College | `Demo@1234` |
| `inst.northfield@demo.test` | INSTITUTION | Northfield Institute | `Demo@1234` |
| `scrutiny1@demo.test` | SCRUTINY_OFFICER | Southern | `Demo@1234` |
| `scrutiny2@demo.test` | SCRUTINY_OFFICER | Northern | `Demo@1234` |
| `regional.south@demo.test` | REGIONAL_OFFICER | Southern | `Demo@1234` |
| `regional.north@demo.test` | REGIONAL_OFFICER | Northern | `Demo@1234` |
| `bureau.gc@demo.test` | BUREAU_OFFICER | Grievance Cell | `Demo@1234` |
| `bureau.rb@demo.test` | BUREAU_OFFICER | Regulation Bureau | `Demo@1234` |
| `admin@demo.test` | ADMIN | All | `Demo@1234` |

Show these as clickable chips on the login page only when `DEMO_MODE=true`.

## 4. Volume targets

- ~60 applications across workflows and stages
- ~25 completed historical applications (for forecast statistics, with realistic stage durations)
- ~200 obligations (documents, undertakings, FDR maturities, EVC visits, stage SLAs, complaint SLAs)
- ~40 complaints across bureaus and categories
- 6 sample documents (generated PDFs with text layers): lease deed with a duration clause, fire NOC with explicit expiry, FDR copy with maturity date, audited statement, a land-use certificate, an ambiguous multi-date document

## 5. Required scenarios (must exist in seed)

| # | Scenario | Purpose |
|---|---|---|
| 1 | Kaveri Valley has an **application breaching its stage SLA** (EVC scheduling, 4 days late) | Pendency, escalation |
| 2 | Kaveri Valley has a **lease obligation overdue by 12 days** with T0, T+3 alerts already logged and T+10 pending | Alert ladder |
| 3 | Kaveri Valley has a **fire NOC expiring in 31 days** | Clock-advance demo triggers T-30 |
| 4 | Kaveri Valley has **two open complaints at different bureaus (GC and RB)** on fee refund with similar wording | Overlap detection |
| 5 | A third, unrelated same-category complaint at Kaveri Valley (different issue) | Ensures no false link |
| 6 | Northfield has an application returned for clarification, SLA paused | Pause/resume |
| 7 | Three institutions with 2+ bureaus concurrently handling complaints | Multi-bureau table |
| 8 | One institution with a severe complaint and two overdue obligations | High risk band |
| 9 | One institution with everything on track | Low risk band |
| 10 | An application waiting at the final decision stage | Human decision demo |
| 11 | One suggested but unconfirmed OCR suggestion pending for Kaveri Valley | Suggestion card |
| 12 | One FDR maturity obligation due in 75 days (manual entry) | Shows FDR support without bank integration |
| 13 | Two public portal submissions: one `PENDING_REVIEW` for Kaveri Valley, one clearly frivolous to reject | Portal intake and review |
| 15 | One complaint with status `TRANSFERRED` (RB to PGRC, reason recorded) and one `ESCALATED` with a note | Transfer/escalation history |
| 16 | At least 5 open complaints past `expected_disposal_date`, spread over 2 bureaus and 3 regions | "Beyond timeline" tile and ageing report |
| 17 | One institution where an RB case and a PGRC case share no wording but have the same institution | Rule-based "Coordination Required" alert without text match |
| 14 | Scenario 8's institution must score 50+ and Kaveri 50+ (ELEVATED); scenario 9 scores 0 (LOW) | Risk bands match docs/06 |

### Overlap fixtures (complaint text, fictional)

- **CMP-A (GC):** "Student paid admission fee for the 2025 batch and was told the refund would be processed within 30 days of withdrawal. Two months later no refund has been received despite repeated requests to the accounts office."
- **CMP-B (RB):** "Fee refund after withdrawal from the 2025 admission cycle has not been paid by the college. Accounts office keeps delaying and no written reason was given."
- **CMP-C (GC, same institution):** "The laboratory in the mechanical block has no working equipment for the second-year practical sessions and students are sharing a single machine."

Expected: A↔B suggested (score above threshold, shared terms such as refund, fee, admission, 2025, accounts office), A↔C and B↔C not suggested.

## 6. Demo script (about 6 minutes)

1. **Intro (30s):** One platform, one backbone: everything time-bound is an obligation; humans make all decisions.
2. **Institution view (45s):** Log in as `inst.kaveri@demo.test`. Show "What needs attention": overdue lease, expiring fire NOC, one application needing response. Upload the sample lease; show the suggestion card with highlighted snippet; confirm; show the reminder ladder.
3. **Officer pendency (60s):** Log in as `regional.south@demo.test`. Pendency dashboard: the breaching application, forecast chip with explanation. Open it, escalate with a note.
4. **Workflow (45s):** As `scrutiny1@demo.test`, forward an application a stage; show the SLA obligation reset and timeline entry. Mention return-for-clarification pauses the clock.
5. **Live alert (45s):** As admin, advance the clock by 1 day and run the alert cycle. Bell shows the new T-30 reminder for the fire NOC; running again sends nothing (idempotent).
6. **Institution profile (60s):** Kaveri Valley profile: unified timeline, upcoming obligations, applications, complaints summary, risk factors.
7. **Complaints (75s):** As `bureau.gc@demo.test`, open CMP-A: complainant is visible to this bureau; overlap panel shows CMP-B at the Regulation Bureau with shared terms. Confirm the link. Switch to `regional.south@demo.test`: the same complaint shows masked complainant and redacted narrative.
7b. **Portal (30s, optional):** Open the public page, submit a complaint, note the tracking ID; as `bureau.gc@demo.test` register it from the review queue. Record a backup video of the whole demo in advance.
8. **Audit (30s):** Admin verifies the chain (green). Use tamper control, verify again (red, first broken entry).
9. **Close (30s):** Roadmap slide: document verification (SIH26261), APAAR student data (SIH26263), financial instruments (SIH26265). State that decisions stay human and data is synthetic.

## 7. Likely judge questions and prepared answers

| Question | Answer outline |
|---|---|
| How does this integrate with the existing AICTE portal? | Provider/adapters for data import and APIs; prototype uses seeded data; no access to real systems |
| Is the risk score going to penalise institutions? | No. It is a visible, weighted, rule-based prioritisation aid; no automated consequences; officers decide |
| What about false complaints? | Verification flag, reliability context, officer confirmation, no auto-rejection |
| How is complaint privacy protected? | Server-side masking by role and assignment; audit of access to restricted fields could be added |
| How does it scale? | PostgreSQL, job queue instead of in-process scheduler, object storage, horizontal API scaling |
| What is AI here and what is not? | OCR + regex extraction, TF-IDF similarity, heuristic forecast; everything else is rules; all labelled |
| What if rules change? | Stages, SLAs, ladders, categories are admin-configurable |
| Cost? | Open-source stack; cloud cost mainly hosting and SMS/email providers |
| Which problem statement does this satisfy? | Our entry is SIH26262. The complaint dashboard is built for SIH26264 as an add-on on the same backbone. Confirm with organisers how combined entries are treated |
| How do you tell which bureau holds a case? | Every complaint carries its current bureau/cell and officer; transfers and escalations are logged as actions with reasons |

## 8. Sample document generation

Seed script should generate the six sample PDFs with `reportlab` (text layer, no OCR needed) and one scanned-style PNG to exercise the OCR fallback if Tesseract is installed. Embed clear cue phrases, for example:
- Lease: "This lease is made for a term of 30 years from 1 April 2000" → expiry 31 March 2030 (note: for the demo set a more recent start so it falls within the future window, such as a 10-year term from a recent date).
- Fire NOC: "Valid up to 28/11/2026" (adjust so it is 31 days after the demo date).
- FDR: "Maturity date: 12 January 2027".
