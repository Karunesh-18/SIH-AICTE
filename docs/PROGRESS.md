# Progress

Updated by the builder after each task. Teammates: read `CLAUDE.md`, then `docs/DECISIONS.md`, then the numbered docs.

## Spec revision
- [x] Renamed to Waymark (D-01)
- [x] `git init`
- [x] DECISIONS.md written
- [x] Docs 01-08 updated to match D-02..D-12
- [x] Docs 01-08 and README updated for the refreshed SIH26264 statement (D-16, D-17). Spec only, code unchanged. Seed script still needs PGRC and the new scenarios 15-17 when Phase 5 starts
- [ ] New pitch deck (SIH 26262 + 26264 add-on) in the old deck's theme

## Build (see docs/07-BUILD-PLAN.md)
- [x] Phase 0 Scaffold (make/docker unverified, see D-13)
- [x] Phase 1 Foundation (19 backend tests green; browser nav check not done)
- [x] Phase 2 Obligation engine (backend + 10 tests green, migration fa45ffbf679c, list/detail/notifications/compliance UI; calendar and top-bar bell added in the UI redesign, see D-14)
- [ ] Phase 3 Approval workflow
- [ ] Phase 4 Documents + profile
- [ ] Phase 5 Complaints (officer + public portal)
- [ ] Phase 6 Advisory intelligence
- [ ] Phase 7 Polish, Hindi, demo

## Where teammates can help (no coding required)
- Review stage names/SLAs against the real Approval Process Handbook
- Write Hindi strings for `lib/i18n/hi.json`
- Draft the roadmap slide and judge Q&A
- Write the sample complaint texts and fictional institution details
