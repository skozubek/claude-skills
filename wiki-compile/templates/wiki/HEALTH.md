# {PROJECT_NAME} — Wiki Health Snapshot

**Status:** GREEN
**Updated:** {DATE}
**Source scope:** `docs/wiki/`, `docs/raw/`, `docs/LESSONS.md`, `docs/DECISIONS.md`

Mechanical wiki integrity is enabled from day 0. This project has a repo-local manifest, a validator, and a current health snapshot.

## Snapshot

- Compiled articles: 0
- Raw documents: 1
- Lesson entries: 0
- Decision entries: 0

## Mechanical Integrity

| Check | Status | Notes |
|-------|--------|-------|
| Unique lesson IDs | ✅ | No entries yet |
| Unique decision IDs | ✅ | No entries yet |
| Snapshot parity | ✅ | `INDEX.md` and `HEALTH.md` aligned at initialization |
| Metadata coverage | ✅ | Required metadata present on the scaffolded wiki files |
| Markdown link integrity | ✅ | Initial wiki files link cleanly |

## Workflow Guardrails

- `docs/wiki/manifest.json` is the repo-local contract for tracked wiki files, counts, and metadata.
- `node scripts/wiki/validate.mjs` is the mechanical integrity gate after `/wiki-compile`.
- `docs/wiki/wiki-health-check.md` is the semantic review procedure for staleness, contradictions, and coverage drift.

## Next Health Check

Trigger a deeper review when:

- [ ] `node scripts/wiki/validate.mjs` fails
- [ ] 5+ new lessons or decisions were added
- [ ] New raw documents materially change article scope
- [ ] 30 days pass without a wiki audit
