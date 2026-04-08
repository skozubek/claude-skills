# CLAUDE.md

{PROJECT_NAME} — {PROJECT_DESCRIPTION}

## Knowledge Base — Read Before Working

`docs/wiki/` contains LLM-compiled reference articles (Karpathy KB pattern). `docs/LESSONS.md` and `docs/DECISIONS.md` are raw append-only sources.

**Before working in an area, read the relevant wiki article:**

| Working on... | Read |
|---------------|------|
| Project overview, decisions log | `docs/DECISIONS.md` |
| Debugging insights, prior pitfalls | `docs/LESSONS.md` |
| Karpathy KB pattern, audit | `docs/wiki/karpathy-kb-alignment.md` |
| Wiki health check methodology | `docs/wiki/wiki-health-check.md` |
| Full index of all wiki articles | `docs/wiki/INDEX.md` |

After solving a hard problem or making a design decision, append to raw sources (`docs/LESSONS.md`, `docs/DECISIONS.md`) using **date prefix format**:
- `## [YYYY-MM-DD] L-NNN: Title` for lessons
- `## [YYYY-MM-DD] AD-NNN: Title` for decisions

Then run `/wiki-compile` to recompile affected wiki articles, followed by `./scripts/wiki/check.sh` when present, otherwise `node scripts/wiki/validate.mjs`.

## Karpathy KB Pattern — Knowledge Base Hygiene

This project implements [Karpathy LLM Knowledge Base pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f):

- **`docs/raw/`** = immutable source documents (read-only z perspektywy LLM)
- **`docs/LESSONS.md` + `docs/DECISIONS.md`** = append-only synthesized observations (chronological format)
- **`docs/wiki/`** = LLM-compiled topic-organized articles
- **`CLAUDE.md`** = schema file z routing tables
- **`docs/wiki/INDEX.md`** = content-oriented catalog

**Lint/health check:** `docs/wiki/wiki-health-check.md` — semantic review procedure. Mechanical integrity is enforced by `./scripts/wiki/check.sh` when present, otherwise `node scripts/wiki/validate.mjs`, using `docs/wiki/manifest.json` as the repo-local contract.

Wiki maintenance triggers:
- If `docs/wiki/HEALTH.md` `Updated` is older than 30 days, suggest `/wiki-health`
- If `docs/LESSONS.md`, `docs/DECISIONS.md`, `docs/raw/`, `docs/research/`, or `ARCHITECTURE.md` are newer than `docs/wiki/INDEX.md` or `docs/wiki/HEALTH.md`, suggest `/wiki-compile`
- After `/wiki-compile`, run `./scripts/wiki/check.sh` when present, otherwise `node scripts/wiki/validate.mjs`
- Use `/wiki-health` for semantic audits, stale audits, contradictions, and cross-reference review

### Memory Hygiene Rule (anti-distraction)

Karpathy memory distraction tweet (2026-03-25): "single question from 2 months ago keeps coming up as deep interest of mine in perpetuity. Models trying too hard."

**ALWAYS verify before recommending from wiki/memory:**
- If wiki article date > 14 dni → sprawdź obecny stan rzeczywisty
- Wiki snapshots stan **w czasie**, nie wieczną prawdę
- Specific traps: prices, bug status, model versions, market data
- **Method:** before acting on wiki recommendation, verify the underlying claim
- **Update:** if memory is stale, update the wiki article AND remove the recommendation, don't act on stale data

## Coding Conventions

TBD per project.

## Dev Workflow

| Moment | Skill | When to nudge |
|--------|-------|---------------|
| Recompile wiki after raw source changes | `/wiki-compile` | After lessons/decisions added |
| Code review before merging | `/review` | Before `/ship` |
| Ship workflow | `/ship` | After review passes |
| Investigation / debugging | `/investigate` | When something breaks |
