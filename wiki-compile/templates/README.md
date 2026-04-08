# {PROJECT_NAME}

{PROJECT_DESCRIPTION}

## Stage

Pre-code → research / planning. See `docs/wiki/INDEX.md` for knowledge base.

## Documentation

This project follows the [Karpathy LLM Knowledge Base pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f):

- **`CLAUDE.md`** (root) — project instructions, schema file
- **`docs/wiki/INDEX.md`** — wiki articles index
- **`docs/LESSONS.md`** — append-only debugging insights (chronological, date-prefixed)
- **`docs/DECISIONS.md`** — append-only architectural decisions (AD-001..)
- **`docs/raw/`** — Karpathy KB raw layer (papers, exports, court rulings, assets)
- **`docs/wiki/karpathy-kb-alignment.md`** — KB pattern audit
- **`docs/wiki/wiki-health-check.md`** — lint pass methodology

## Workflow

1. **Capture** lessons/decisions in `docs/LESSONS.md` / `docs/DECISIONS.md` z date prefix `## [YYYY-MM-DD]`
2. **Drop** source documents into `docs/raw/<subfolder>/`
3. **Compile** wiki: `/wiki-compile`
4. **Browse** in Obsidian: open project folder as vault
5. **Audit** weekly: wiki-health-check methodology

## License

TBD
