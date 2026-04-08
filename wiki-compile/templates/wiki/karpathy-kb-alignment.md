# Karpathy KB Alignment — How {PROJECT_NAME} Implements LLM Knowledge Bases

**Date:** {DATE}
**Source:** Andrej Karpathy "LLM Knowledge Bases" tweet thread (April 2-4, 2026) + Gist `llm-wiki.md`
**Status:** Initialized via `/wiki-compile` (extended Step 0B)

## TL;DR

`{PROJECT_NAME}` `docs/` struktura jest **świadomą implementacją Karpathy LLM Knowledge Base pattern**.

**Compliance score on init: ~85%**.

## Co Karpathy mówi (synthesized)

Karpathy 2 kwietnia 2026 wypuścił viral tweet (51K likes) opisujący jak buduje personal knowledge bases z LLM. Pełna metodyka w jego Gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

### Karpathy's principles

**Data ingest:**
- `raw/` directory = immutable source documents
- LLM incrementally compiles raw → wiki = collection of `.md` files
- Wiki includes summaries, backlinks, cross-linked articles

**IDE:**
- Obsidian as frontend, LLM writes/maintains wiki, user rarely touches it directly

**Q&A:**
- Once wiki >100 articles, ask LLM agent complex questions
- Auto-maintained index files do większości heavy lifting

**Filing:**
- Q&A outputs back into wiki for future queries — explorations compound

**Linting:**
- LLM "health checks" → find inconsistent data, impute missing, find new article candidates

**File over app:**
- Markdown + images, universal formats, agents apply Unix toolkit

**Future:**
- Synthetic data + finetune so LLM knows data in weights, not just context

## Implementation w {PROJECT_NAME}

### Layer architecture

```
docs/
├── raw/                          ← immutable source documents (Karpathy raw layer)
│   ├── README.md                 ← naming conventions
│   ├── papers/                   ← arXiv, research papers
│   ├── exports/                  ← exports z innych narzędzi
│   ├── competitors/              ← competitive intelligence
│   ├── court-rulings/            ← (jeśli legal) public domain test corpus
│   ├── assets/                   ← images, diagrams
│   └── web-clips/                ← Obsidian Web Clipper output
├── LESSONS.md                    ← append-only synthesized debugging insights
│                                    Format: ## [YYYY-MM-DD] L-NNN: Title
├── DECISIONS.md                  ← append-only architectural decisions
│                                    Format: ## [YYYY-MM-DD] AD-NNN: Title
└── wiki/
    ├── INDEX.md                  ← content-oriented catalog
    ├── wiki-health-check.md      ← lint pass methodology
    ├── karpathy-kb-alignment.md  ← (this file)
    └── *.md                       ← topic-organized LLM-compiled articles

CLAUDE.md                          ← schema file (per Karpathy: routing table)
README.md                          ← project entry point
```

### Compliance audit (initial state)

| Karpathy principle | {PROJECT_NAME} implementation | Status |
|---|---|---|
| 3-warstwowa struktura raw → wiki → schema | docs/raw/, docs/wiki/, CLAUDE.md | ✅ |
| Date prefixes (Karpathy log.md) | LESSONS.md + DECISIONS.md format `## [YYYY-MM-DD]` | ✅ |
| LLM owns wiki | wiki-compile skill via `/wiki-compile` | ✅ |
| Topic-organized articles | docs/wiki/*.md (LLM-compiled) | ⏳ (populate via wiki-compile) |
| `index.md` content catalog | docs/wiki/INDEX.md | ✅ |
| Append-only raw sources | LESSONS.md + DECISIONS.md | ✅ |
| Lint/health check methodology | docs/wiki/wiki-health-check.md | ✅ |
| Memory hygiene rule | CLAUDE.md "verify before recommending from wiki >14 dni" | ⏳ (add manually if needed) |
| Git repo | _(check `git rev-parse --is-inside-work-tree`)_ | ⏳ |
| Obsidian as IDE | _(open project folder as Obsidian vault)_ | ⏳ |

### Workflow

1. **Capture raw observations** → append do `docs/LESSONS.md` lub `docs/DECISIONS.md` z date prefix
2. **Add source documents** → drop do `docs/raw/<subfolder>/`
3. **Compile wiki** → `/wiki-compile` (incremental, auto-detects what changed)
4. **Health check** → manual lint pass via `docs/wiki/wiki-health-check.md`
5. **Browse in Obsidian** → open project folder as vault, graph view + backlinks

## Implementation log

| Date | Action | Files |
|---|---|---|
| {DATE} | Initialized via `/wiki-compile` Step 0B | All Karpathy-current structure |

## Powiązane

- `docs/raw/README.md` — raw layer conventions
- `docs/wiki/wiki-health-check.md` — lint pass methodology
- `docs/wiki/INDEX.md` — wiki index
- Karpathy Gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
