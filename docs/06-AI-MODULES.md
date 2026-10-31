# 06 — Advisory Intelligence Modules

General rules for all modules:
- Outputs are **suggestions** stored with status and explanation; humans confirm.
- Return the factors behind every output.
- Label the method plainly in the UI and API (`method` field).
- Fail safe: if a module errors, the core workflow still works.
- Each module sits behind a service interface so it can be swapped later.

---

## 1. Document expiry extraction (OCR-assisted)

**Purpose:** Suggest an expiry/validity date and obligation from an uploaded document.

**Pipeline**
1. Detect type: PDF with a text layer → extract text with `pdfplumber` or `pypdf`. Image or scanned PDF → `pdf2image` + `pytesseract` (if available). If OCR is not installed, skip and record `extraction_method="none"`.
2. Normalise text (lowercase copy for matching, keep original for snippets).
3. Guess `doc_type` from keywords:

| doc_type | Keywords (any) |
|---|---|
| `LEASE_DEED` | lease, lessor, lessee, demised premises |
| `LAND_USE_CERT` | land use, conversion certificate, zoning |
| `FIRE_NOC` | fire, no objection certificate, fire safety |
| `AUDITED_STATEMENT` | audited, balance sheet, income and expenditure |
| `FDR_COPY` | fixed deposit, FDR, maturity date |
| `AFFIDAVIT` | affidavit, solemnly affirm |

4. Find date candidates with regexes near **cue phrases**:
   - Cues: `valid until`, `valid up to`, `valid till`, `expires on`, `expiry date`, `date of expiry`, `maturity date`, `lease period`, `for a term of`, `till`
   - Date formats: `DD/MM/YYYY`, `DD-MM-YYYY`, `DD Month YYYY`, `Month DD, YYYY`, `YYYY-MM-DD`
   - Duration forms: `for a period of N years from <date>` → compute end date
5. Score confidence: base 0.5; +0.25 if a strong cue (`valid until`, `expiry`, `maturity`) is within 40 characters; +0.15 if doc type matched; −0.2 if multiple conflicting future dates; clamp 0 to 1.
6. Return up to 3 candidates with `{date, confidence, snippet, cue}`.

**Output record:** `ObligationSuggestion` with `suggested_type` (`DOCUMENT_EXPIRY` or `FDR_MATURITY`), `suggested_due_at`, `confidence`, `evidence`.

**Rules**
- Never create the obligation without confirmation.
- Display the snippet with the date highlighted.
- If confidence < 0.4, show "Low confidence; please enter the date manually".

**Tests:** at least 8 fixture texts (lease with duration, fire NOC with explicit expiry, FDR with maturity date, ambiguous multi-date, no date, Hindi numeral edge case skipped with graceful fallback).

---

## 2. Complaint overlap detection

**Purpose:** Help bureaus see that different cases concern the same issue at the same institution.

**Rule-based trigger (no scoring needed):** if the same institution has open complaints at 2 or more different bureaus/cells, every involved bureau sees the banner "Potential Overlapping Cases - Coordination Required" with the other cases' bureau, officer and status. This works even when the descriptions share no wording. It is an alert only; the similarity score below ranks which pairs are probably the same issue.

**Candidate set:** other complaints for the **same institution**, status not in (`CLOSED`, `REJECTED_FRIVOLOUS`), any bureau, received within a configurable window (default 365 days).

**Method (default): TF-IDF + cosine similarity**
1. Text = `title + " " + narrative`, lowercased, punctuation stripped, English stop-words removed (small built-in list plus Hinglish common words).
2. Fit `TfidfVectorizer(ngram_range=(1,2), min_df=1, sublinear_tf=True)` on the **whole complaint corpus** (cached, refit when it changes by more than 10%), not just the 2 to 3 candidates, so IDF is meaningful (D-08).
3. `text_sim` = cosine similarity.
4. Combined score. The bonuses apply only if `text_sim >= 0.15`; otherwise `score = 0`:
```
score = 0.70 * text_sim
      + 0.15 * (1 if same_category else 0)
      + 0.10 * recency_factor     # 1 if within 30 days, linearly down to 0 at 180 days
      + 0.05 * (1 if different_bureau else 0)
```
Reason: without the gate, two unrelated same-category complaints in the same month score 0.30, one word short of the 0.35 threshold.
5. Create `ComplaintLink(status=SUGGESTED)` when `score >= threshold` (default 0.35, configurable).
6. `explanation` (stored in full; the API returns `shared_terms` only after the link is CONFIRMED, D-08): top 5 shared terms by combined tf-idf weight, `same_category`, `days_apart`, `different_bureau`, `method="tfidf_cosine"`, `threshold`.

**Optional method:** `sentence-transformers` (e.g. `all-MiniLM-L6-v2`) behind flag `USE_SENTENCE_TRANSFORMERS`; same output shape, `method="embeddings"`. Default stays TF-IDF so the prototype runs offline with no heavy downloads.

**Human step:** Bureau officer confirms or dismisses. Dismissed pairs are never re-suggested. Confirmed links show on both cases and on the institution's consolidated complaint view with the label "Linked: coordinate with <bureau>".

**Anti-abuse (advisory):** Show `complainant_verified` status and a count of prior dismissed complaints from the same complainant contact as context for officers. Never auto-reject.

**Tests:** seeded pairs (true overlap across bureaus, same bureau near-duplicate, same category but different issue, different institution) and threshold behavior.

---

## 3. Explainable risk view

**Purpose:** Help officers prioritise which institutions to look at first. Not a finding, not a penalty trigger.

**Formula (`rules-v1`)**: sum of weighted capped factors, scaled to 0 to 100.

| Factor key | Definition | Weight per unit | Cap (units) |
|---|---|---|---|
| `overdue_obligations` | count of OVERDUE obligations | 12 | 4 |
| `long_overdue` | count overdue more than 30 days | 8 | 3 |
| `expired_documents` | count of expired required document types | 8 | 3 |
| `open_complaints` | count of open complaints | 8 | 4 |
| `severe_complaints` | open complaints with severity 3 | 10 | 2 |
| `repeat_category` | max count of complaints in one category in last 12 months, minus 1 | 6 | 3 |
| `multi_bureau` | number of bureaus concurrently handling the institution minus 1 | 8 | 2 |
| `sla_breaches` | stage SLA breaches in last 12 months | 8 | 4 |
| `rejected_returns` | applications returned for clarification 3+ times | 4 | 2 |

`contribution = min(value, cap) * weight`. `score = min(100, sum(contribution))`. No normalisation by the maximum possible sum (D-07): that made the featured institution score about 20. Check: Kaveri (1 overdue, 2 open complaints, repeat category 1, 2 bureaus, 1 SLA breach) = 12+16+6+8+8 = 50, ELEVATED. A fully on-track institution = 0, LOW. Tests assert the seeded bands; the seed for scenario 8 must reach 50+.

**Bands:** 0 to 24 LOW, 25 to 49 MODERATE, 50 to 74 ELEVATED, 75 to 100 HIGH.

**Output:** `RiskSnapshot` with `factors[]` (key, label, value, weight, contribution) and `method_version`.

**Rules**
- Recompute nightly and on demand; store history.
- UI always shows the factor table and the disclaimer.
- The score is not shown to institutions.
- Weights editable in `system_config`.
- Document in the UI footer: "Prioritisation aid only. Regulatory decisions are made by authorised officials."

**Tests:** known fixtures produce expected score and band; capping works; weights from config are respected.

---

## 4. SLA-breach forecast (heuristic)

**Purpose:** Warn early which open applications may breach the current stage SLA.

**Inputs**
- `elapsed` = business days in stage so far (excluding paused time)
- `sla` = stage SLA days
- `hist_mean` = mean actual duration of that stage from completed stage instances (seeded history; fall back to `sla` if fewer than 5 samples)
- `queue_factor` = (open items assigned to the owner/role in that stage) / (their 30-day average throughput), clamped 0.5 to 2.0
- `return_count` = times this application was returned previously

**Estimate**
```
expected_total = hist_mean * queue_factor * (1 + 0.15 * return_count)
projected_remaining = max(0, expected_total - elapsed)
projected_total = elapsed + projected_remaining
ratio = projected_total / sla
```
**Label:** `ratio < 0.8` LOW, `0.8 to 1.0` MEDIUM, `> 1.0` HIGH.

Return `{label, ratio, factors:{elapsed, sla, hist_mean, queue_factor, return_count}, method:"heuristic-v1"}`. Do not present as a probability percentage, and do not call it machine learning.

**Roadmap note (slide only):** replace with a trained survival or gradient-boosting model once real stage data exists.

**Tests:** table-driven cases for each label; fallback with insufficient history; paused time excluded.

---

## 5. Rule-based bureau routing suggestion

When registering a complaint, suggest `current_bureau_id` using `ComplaintCategory.default_bureau_id`. The registering officer can accept or change it. No ML.

---

## 6. Advisory complaint-to-approval review flag (M-09)

On a complaint detail page, a bureau officer may click "Suggest review of related approval". The system lists the institution's open or recent applications and lets the officer pick one and write a reason. This creates a `ReviewFlag` visible to the regional officer as a prompt. It changes no status and does not pause or block anything. Audit logged.

---

## 7. Roadmap integrations (documentation only, not built)

| Related problem statement | Possible integration |
|---|---|
| SIH26261 Document verification | Replace manual `OFFICER_CONFIRMED` with issuer/QR verification APIs |
| SIH26263 Student data (APAAR) | Enrollment vs approved-intake anomaly factor in risk view |
| SIH26265 Financial instruments | Bank API feed for FDR validity, replacing manual `FDR_MATURITY` entry |

Present these as a roadmap slide, not as delivered features.
