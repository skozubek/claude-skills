# Wiki Health Check — Procedure

**Status:** Procedure
**Updated:** {DATE}
**Source scope:** `docs/wiki/`, `docs/raw/`, `docs/LESSONS.md`, `docs/DECISIONS.md`

This document defines the manual semantic review pass for the wiki. Run it after the mechanical validator passes or when you want to audit staleness, contradictions, and coverage drift.

## Run Order

1. Run `node scripts/wiki/validate.mjs`.
2. If it fails, fix the mechanical issues first.
3. If it passes, review semantic quality and update `docs/wiki/HEALTH.md`.
4. If article scope changed materially, run `/wiki-compile` for the affected pages and validate again.

## Script-Owned Checks

`node scripts/wiki/validate.mjs` already verifies:

- duplicate lesson and decision IDs
- snapshot parity between `INDEX.md` and `HEALTH.md`
- required metadata headers on tracked wiki pages
- broken markdown links inside `docs/wiki/`
- presence of files declared in `docs/wiki/manifest.json`

## Manual Checklist

### A. Coverage drift
- [ ] Do recent lessons, decisions, or raw docs require wiki recompilation?
- [ ] Does `docs/wiki/INDEX.md` still reflect the real article set and source coverage?

### B. Staleness
- [ ] Do any articles make time-sensitive claims that now need re-verification?
- [ ] Has any high-churn area gone 30+ days without refresh?

### C. Contradictions
- [ ] Do articles still agree on the current product, architecture, and policy stance?
- [ ] Do new decisions supersede older wiki claims that still read as current guidance?

### D. Cross-reference quality
- [ ] Are the right neighboring articles linked where the reader needs them?
- [ ] Does `CLAUDE.md` still route work to the right wiki pages?

### E. Article hygiene
- [ ] Every tracked wiki page has `Status`, `Updated`, and `Source scope` near the top.
- [ ] Historical notes are framed as history, not as accidental current doctrine.
