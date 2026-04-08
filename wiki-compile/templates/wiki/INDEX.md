# {PROJECT_NAME} — Wiki Index

**Status:** Master index
**Updated:** {DATE}
**Source scope:** `docs/raw/`, `docs/LESSONS.md`, `docs/DECISIONS.md`

LLM-compiled knowledge base. Maintained by LLM via `/wiki-compile`, not edited manually. Raw sources are human-written; the wiki is the synthesized reference layer.

## Snapshot

- Compiled articles: 0
- Raw documents: 1
- Lesson entries: 0
- Decision entries: 0

## Articles

### Meta / KB pattern

- [Karpathy KB Alignment](karpathy-kb-alignment.md) — how this project implements Karpathy LLM KB pattern
- [Wiki Health Check](wiki-health-check.md) — semantic review procedure

<!-- Topic articles will be added by /wiki-compile as knowledge accumulates. -->

## Integrity Rules

1. `docs/wiki/manifest.json` is the repo-local contract for wiki structure, counts, and metadata.
2. Run `node scripts/wiki/validate.mjs` after `/wiki-compile` or any manual wiki maintenance.
3. `docs/wiki/HEALTH.md` is the current health snapshot.
4. Keep raw knowledge in `docs/raw/`, `docs/LESSONS.md`, and `docs/DECISIONS.md`; keep compiled knowledge in `docs/wiki/`.
