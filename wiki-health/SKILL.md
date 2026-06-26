---
name: wiki-health
description: |
  Run a semantic and operational health review for a project wiki. Use when asked
  to audit wiki quality, run a stale audit, check if the knowledge base is up to date,
  or review wiki consistency after wiki-compile. Works with both docs/raw and docs/research
  layouts. Prefer this over ad-hoc wiki review prompts.
---

# Wiki Health

Audit a project wiki after `/wiki-compile` or when freshness is in doubt.

## Modes

- **`health-pass`**: full review. Mechanical check first, then semantic review, then update `docs/wiki/HEALTH.md`.
- **`stale-audit`**: focus on freshness, outdated claims, and whether recompilation is needed.
- **`integrity-only`**: run only the mechanical gate (`npm run lint:wiki` or `node scripts/wiki/validate.mjs`) and report results.

Default to `health-pass` unless the user clearly asks for only freshness or only integrity.

## Run Order

1. Detect the wiki layout.
2. Run the mechanical validator if present:
   - prefer `npm run lint:wiki` when `package.json` has `lint:wiki`
   - otherwise run `node scripts/wiki/validate.mjs` when present
3. Identify the freshness anchors:
   - `docs/wiki/HEALTH.md` `**Updated:**`
   - `docs/wiki/INDEX.md` `**Updated:**` or `Last compiled:`
   - newest mtimes among `docs/LESSONS.md`, `docs/DECISIONS.md`, `docs/raw/`, `docs/research/`, and `ARCHITECTURE.md` if present
4. Compare freshness:
   - if raw sources are newer than `INDEX.md` or `HEALTH.md`, recommend `/wiki-compile`
   - if `HEALTH.md` is older than 30 days, recommend a health pass
   - if tracked articles lack `Status`, `Updated`, or `Source scope`, flag as structural drift
5. For `health-pass` and `stale-audit`, review semantic quality:
   - stale claims: “latest”, “current”, “recent”, vendor versions, prices, benchmarks, legal/compliance status
   - contradictions between wiki articles and newer lessons/decisions
   - missing cross-references where related articles should link
   - article bloat that should be split
6. Update `docs/wiki/HEALTH.md` when the task is a full health pass and the repo expects that file.

## Layout Detection

- **Karpathy-current**: `docs/raw/` exists
- **Legacy**: `docs/research/` exists
- Some repos may have both; respect the repo-local contract if `docs/wiki/manifest.json` exists.

## Repo-Local Contract

If `docs/wiki/manifest.json` exists:

- treat it as the structural source of truth
- use it to infer tracked files, metadata requirements, and snapshot labels
- do not invent alternative counters or required files

If no manifest exists:

- fall back to the repo’s existing wiki conventions
- report that the repo is missing the contract layer

## Timestamp Heuristics

Use these to decide what to suggest:

- `raw newer than INDEX/HEALTH` → suggest `/wiki-compile`
- `HEALTH updated > 30 days ago` → suggest `/wiki-health`
- `INDEX updated > 30 days ago` and raw changed recently → suggest both `/wiki-compile` then `/wiki-health`
- `validator passes but freshness is stale` → semantic issue, not structural issue
- `validator fails` → fix mechanical issues before doing semantic review

## Output

Keep the report short and operational:

- overall status: `green`, `yellow`, or `red`
- mechanical integrity result
- freshness result
- top findings ordered by severity
- exact next action:
  - `/wiki-compile`
  - `/wiki-health`
  - both, in order
  - or “no action needed”

When updating `docs/wiki/HEALTH.md`, ensure snapshot counts match the validator output rather than hand-counted estimates.
