---
name: wiki-compile
description: |
  Recompile the LLM knowledge base wiki (docs/wiki/) from raw sources.
  Follows Karpathy's KB pattern: raw inputs → LLM-compiled articles → CLAUDE.md router.
  Works in any project with the standard docs/ structure.
  Use when asked to "recompile wiki", "update wiki", "wiki compile",
  "refresh knowledge base", or "sync wiki".
  Proactively suggest when new LESSONS.md or DECISIONS.md entries are detected.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# Wiki Compile (Global)

Recompile the `docs/wiki/` knowledge base from raw sources following the
[Karpathy LLM Knowledge Base pattern](https://x.com/karpathy/status/2039805659525644595).

**Principle:** Raw inputs and compiled knowledge are separate layers. Humans write
raw sources (LESSONS.md, DECISIONS.md, research/). LLM maintains the wiki. The wiki
is LLM-native documentation — never manually edited.

**Works across any project** with the standard structure (supports two layouts):

```
Legacy layout (CB-style):
docs/
├── LESSONS.md          ← raw append-only, format: ## L-NNN: Title
├── DECISIONS.md        ← raw append-only, format: ## AD-NNN: Title
├── research/           ← raw research documents
└── wiki/
    ├── INDEX.md         ← master index with source coverage
    ├── HEALTH.md        ← compile tracking, staleness, gaps
    └── *.md             ← topic-based compiled articles

Karpathy-current layout (HORACY-style, recommended for new projects):
docs/
├── LESSONS.md          ← format: ## [YYYY-MM-DD] L-NNN: Title (Karpathy log.md)
├── DECISIONS.md        ← format: ## [YYYY-MM-DD] AD-NNN: Title
├── raw/                ← Karpathy raw layer (immutable source documents)
│   ├── README.md       ← naming conventions, anonymization rules
│   ├── papers/         ← arXiv, ACL, blog research
│   ├── exports/        ← NotebookLM exports, etc. (anonymized!)
│   ├── competitors/    ← screenshots, marketing materials
│   ├── court-rulings/  ← public domain test corpus
│   ├── assets/         ← images, diagrams referenced by wiki/
│   └── web-clips/      ← Obsidian Web Clipper output
└── wiki/
    ├── INDEX.md             ← master index with source coverage
    ├── HEALTH.md            ← current health snapshot + integrity status
    ├── manifest.json        ← repo-local wiki contract (counts, metadata, tracked files)
    ├── wiki-health-check.md ← semantic review procedure (optional)
    ├── karpathy-kb-alignment.md ← KB pattern audit (optional)
    └── *.md                 ← topic-based compiled articles

scripts/
└── wiki/
    └── validate.mjs         ← mechanical integrity validator
```

This skill **auto-detects** which layout the project uses and adapts.

## Step 0: Compatibility Check

Before doing anything, verify this project supports wiki-compile.

```bash
echo "=== WIKI COMPATIBILITY CHECK ==="
_HAS_WIKI="no"
_HAS_LESSONS="no"
_HAS_DECISIONS="no"
_HAS_RESEARCH="no"
_HAS_RAW="no"
_HAS_ARCHITECTURE="no"
_HAS_CLAUDE="no"
_HAS_HEALTH="no"
_HAS_HEALTH_CHECK="no"
_HAS_KARPATHY_DOC="no"
_LAYOUT="unknown"
_DATE_FORMAT="legacy"

[ -d "docs/wiki" ] && _HAS_WIKI="yes"
[ -f "docs/LESSONS.md" ] && _HAS_LESSONS="yes"
[ -f "docs/DECISIONS.md" ] && _HAS_DECISIONS="yes"
[ -d "docs/research" ] && _HAS_RESEARCH="yes"
[ -d "docs/raw" ] && _HAS_RAW="yes"
[ -f "ARCHITECTURE.md" ] && _HAS_ARCHITECTURE="yes"
[ -f "CLAUDE.md" ] && _HAS_CLAUDE="yes"
[ -f "docs/wiki/HEALTH.md" ] && _HAS_HEALTH="yes"
[ -f "docs/wiki/wiki-health-check.md" ] && _HAS_HEALTH_CHECK="yes"
[ -f "docs/wiki/karpathy-kb-alignment.md" ] && _HAS_KARPATHY_DOC="yes"

# Detect layout
if [ "$_HAS_RAW" = "yes" ] && [ "$_HAS_KARPATHY_DOC" = "yes" ]; then
  _LAYOUT="karpathy-current"
elif [ "$_HAS_RAW" = "yes" ]; then
  _LAYOUT="karpathy-current"
elif [ "$_HAS_RESEARCH" = "yes" ]; then
  _LAYOUT="legacy"
fi

# Detect date format in LESSONS.md (Karpathy log.md pattern uses [YYYY-MM-DD])
if [ "$_HAS_LESSONS" = "yes" ]; then
  if grep -q '^## \[20[0-9][0-9]-[01][0-9]-[0-3][0-9]\]' docs/LESSONS.md 2>/dev/null; then
    _DATE_FORMAT="karpathy"
  fi
fi

echo "docs/wiki/:               $_HAS_WIKI"
echo "docs/LESSONS.md:          $_HAS_LESSONS"
echo "docs/DECISIONS.md:        $_HAS_DECISIONS"
echo "docs/raw/:                $_HAS_RAW"
echo "docs/research/:           $_HAS_RESEARCH"
echo "ARCHITECTURE.md:          $_HAS_ARCHITECTURE"
echo "CLAUDE.md:                $_HAS_CLAUDE"
echo "docs/wiki/HEALTH.md:      $_HAS_HEALTH (legacy compile tracker)"
echo "wiki-health-check.md:     $_HAS_HEALTH_CHECK (Karpathy lint methodology)"
echo "karpathy-kb-alignment.md: $_HAS_KARPATHY_DOC"
echo "Layout:                   $_LAYOUT"
echo "Date format:              $_DATE_FORMAT"

# Count existing wiki articles
if [ "$_HAS_WIKI" = "yes" ]; then
  _ARTICLE_COUNT=$(find docs/wiki -name "*.md" -not -name "INDEX.md" -not -name "HEALTH.md" -not -name "wiki-health-check.md" -not -name "karpathy-kb-alignment.md" | wc -l | tr -d ' ')
  echo "Wiki articles:            $_ARTICLE_COUNT"
fi

# Count raw source entries — regex handles BOTH legacy and Karpathy date-prefix formats
# Legacy:   ## L-001: Title
# Karpathy: ## [2026-04-04] L-001: Title
if [ "$_HAS_LESSONS" = "yes" ]; then
  _LESSON_COUNT=$(grep -cE '^## (\[[0-9-]+\] )?L-' docs/LESSONS.md 2>/dev/null || echo "0")
  echo "Lessons:                  $_LESSON_COUNT"
fi
if [ "$_HAS_DECISIONS" = "yes" ]; then
  _DECISION_COUNT=$(grep -cE '^## (\[[0-9-]+\] )?AD-' docs/DECISIONS.md 2>/dev/null || echo "0")
  echo "Decisions:                $_DECISION_COUNT"
fi
```

### If NOT compatible:

If `docs/wiki/` does not exist, tell the user:

> "This project doesn't have a wiki yet. The wiki follows the Karpathy KB pattern:
> raw sources (LESSONS.md, DECISIONS.md) → LLM-compiled articles (docs/wiki/).
>
> Want me to initialize the wiki structure?"

Options via AskUserQuestion:
- A) Initialize wiki — create docs/wiki/, INDEX.md, HEALTH.md, LESSONS.md, DECISIONS.md
- B) Skip — this project doesn't need a wiki

**If A:** Run the initialization procedure (Step 0B below).
**If B:** Exit with: "No wiki initialized. Run `/wiki-compile` when you're ready."

### Step 0B: Initialize Wiki Structure (new projects only)

**For NEW projects use Karpathy-current layout** (raw/ + date prefixes). Existing projects keep their layout.

This step uses **template files** stored alongside the skill. Templates are in:

```
$HOME/.claude/skills/wiki-compile/templates/
  ├── LESSONS.md
  ├── DECISIONS.md
  ├── README.md (placeholder: {PROJECT_NAME}, {PROJECT_DESCRIPTION})
  ├── CLAUDE.md (placeholder: {PROJECT_NAME}, {PROJECT_DESCRIPTION})
  ├── gitignore (note: copies to .gitignore — leading dot stripped to avoid macOS hidden file in iCloud)
  ├── wiki/INDEX.md (placeholders: {PROJECT_NAME}, {PROJECT_DESCRIPTION}, {DATE})
  ├── wiki/HEALTH.md (placeholders: {PROJECT_NAME}, {DATE})
  ├── wiki/manifest.json
  ├── wiki/karpathy-kb-alignment.md (placeholders: {PROJECT_NAME}, {DATE})
  ├── wiki/wiki-health-check.md
  ├── raw/README.md
  ├── scripts/wiki/validate.mjs
  ├── scripts/wiki/check.sh
  ├── raw/{papers,exports,competitors,court-rulings,assets,web-clips}/.gitkeep
  └── .obsidian/{app,core-plugins,community-plugins,graph,app-exclude}.json
```

**Note on path:** `~/.claude/skills/wiki-compile/` is a symlink to `~/Coding/claude-skills/wiki-compile/` (private git repo, synced between machines via `git pull`). Templates resolve transparently through the symlink.

#### Sub-step 0B.1: Gather project metadata

Use AskUserQuestion to gather:
1. **Project name** (e.g., "horacy", "campaign-builder", "myproject")
2. **Project description** (1-line, e.g., "Privacy-first AI document analysis for Polish lawyers")
3. **Setup level** (radio):
   - **Minimal** — just LESSONS, DECISIONS, INDEX, raw/ structure (5 files)
   - **Standard** — + wiki-health-check.md, karpathy-kb-alignment.md (8 files)
   - **Full** — + `docs/.obsidian/` vault config (scoped to docs/, no code indexing), .gitignore, README.md, CLAUDE.md (recommended for new projects, ~17 files)

Default to **Full**.

#### Sub-step 0B.2: Copy templates with placeholder substitution

```bash
TEMPLATES="$HOME/.claude/skills/wiki-compile/templates"
DATE="$(date +%Y-%m-%d)"

# Verify templates available
if [ ! -d "$TEMPLATES" ]; then
  echo "ERROR: Templates not found at $TEMPLATES"
  echo "Symlink may be broken. Check: ls -la ~/.claude/skills/wiki-compile"
  exit 1
fi

# Helper to substitute placeholders
substitute() {
  local src="$1"
  local dst="$2"
  sed -e "s|{PROJECT_NAME}|$PROJECT_NAME|g" \
      -e "s|{PROJECT_DESCRIPTION}|$PROJECT_DESCRIPTION|g" \
      -e "s|{DATE}|$DATE|g" \
      "$src" > "$dst"
}

# Always create core Karpathy structure (Minimal level and above)
mkdir -p docs/wiki
mkdir -p docs/raw/{papers,exports,competitors,court-rulings,assets,web-clips}

[ -f docs/LESSONS.md ] || cp "$TEMPLATES/LESSONS.md" docs/LESSONS.md
[ -f docs/DECISIONS.md ] || cp "$TEMPLATES/DECISIONS.md" docs/DECISIONS.md
[ -f docs/raw/README.md ] || cp "$TEMPLATES/raw/README.md" docs/raw/README.md
[ -f docs/wiki/INDEX.md ] || substitute "$TEMPLATES/wiki/INDEX.md" docs/wiki/INDEX.md
[ -f docs/wiki/HEALTH.md ] || substitute "$TEMPLATES/wiki/HEALTH.md" docs/wiki/HEALTH.md
[ -f docs/wiki/manifest.json ] || cp "$TEMPLATES/wiki/manifest.json" docs/wiki/manifest.json
mkdir -p scripts/wiki
[ -f scripts/wiki/validate.mjs ] || cp "$TEMPLATES/scripts/wiki/validate.mjs" scripts/wiki/validate.mjs
[ -f scripts/wiki/check.sh ] || cp "$TEMPLATES/scripts/wiki/check.sh" scripts/wiki/check.sh
chmod +x scripts/wiki/check.sh

for sub in papers exports competitors court-rulings assets web-clips; do
  touch "docs/raw/$sub/.gitkeep"
done

# Standard level — add Karpathy KB methodology articles
if [ "$SETUP_LEVEL" = "standard" ] || [ "$SETUP_LEVEL" = "full" ]; then
  [ -f docs/wiki/wiki-health-check.md ] || cp "$TEMPLATES/wiki/wiki-health-check.md" docs/wiki/wiki-health-check.md
  [ -f docs/wiki/karpathy-kb-alignment.md ] || substitute "$TEMPLATES/wiki/karpathy-kb-alignment.md" docs/wiki/karpathy-kb-alignment.md
fi

# Full level — Obsidian config + .gitignore + README + CLAUDE.md
if [ "$SETUP_LEVEL" = "full" ]; then
  # Obsidian vault scoped to docs/ — keeps code out of the index, fast graph,
  # cross-layer backlinks between wiki/ and raw/ work because both are under vault root.
  # (Legacy Horacy-style put .obsidian/ at repo root; new projects should NOT do that.)
  mkdir -p docs/.obsidian
  for f in app.json core-plugins.json community-plugins.json graph.json app-exclude.json; do
    [ -f "docs/.obsidian/$f" ] || cp "$TEMPLATES/.obsidian/$f" "docs/.obsidian/$f"
  done

  # .gitignore (note: template stored as 'gitignore' to avoid hidden file issues in iCloud)
  [ -f .gitignore ] || cp "$TEMPLATES/gitignore" .gitignore

  # README.md (skip if exists — don't overwrite user content)
  [ -f README.md ] || substitute "$TEMPLATES/README.md" README.md

  # CLAUDE.md (skip if exists — don't overwrite user content)
  [ -f CLAUDE.md ] || substitute "$TEMPLATES/CLAUDE.md" CLAUDE.md
fi

echo "=== Karpathy KB structure initialized ==="
echo "Setup level: $SETUP_LEVEL"
find docs -type f | sort
```

#### Sub-step 0B.3: Initialize git (if not already a repo)

Per Karpathy KB pattern: git is critical for audit trail.

```bash
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "=== Git not initialized ==="
  echo "Karpathy KB pattern strongly recommends git from day 0:"
  echo "  - Version history of wiki changes"
  echo "  - Audit trail (especially for legal/compliance projects)"
  echo "  - Sync between machines via git remote"
  echo ""
  echo "Suggest user runs:"
  echo "  git init && git add . && git commit -m 'Initial Karpathy KB structure'"
fi
```

Use AskUserQuestion: "Initialize git now?" (Yes / No / Already plan to do it manually)

If yes, run init + initial commit. If no, exit Step 0B with reminder.

#### Sub-step 0B.4: Confirm next steps

```
✅ Karpathy KB structure initialized in {PROJECT_NAME}

Next steps:
1. Open the wiki as Obsidian vault: File → Open another vault → select the `docs/` folder (NOT project root — keeps code out of the vault index for speed)
2. Add your first lesson: docs/LESSONS.md (format: ## [YYYY-MM-DD] L-001: Title)
3. Add your first decision: docs/DECISIONS.md (format: ## [YYYY-MM-DD] AD-001: Title)
4. Drop source documents into docs/raw/<subfolder>/
5. Run /wiki-compile after accumulating raw content to generate topic articles
6. Optional: weekly health check using docs/wiki/wiki-health-check.md methodology

Karpathy KB compliance: ~85% (initial). Will reach 95%+ as you populate content + git history grows.
```

Exit Step 0B.

---

(Legacy mention — for reference, NOT used in new projects):

If user explicitly requests legacy CB-style layout:
- Use `docs/research/` instead of `docs/raw/`
- Use `## L-NNN` and `## AD-NNN` (no date prefix)
- Use `HEALTH.md` instead of `INDEX.md` for compile tracking

Default to Karpathy-current always.

Create `docs/wiki/HEALTH.md`:
```markdown
# Wiki Health Check — {date} (Initial)

## Overall Status: NEW

Wiki just initialized. No articles compiled yet.

## Coverage Audit

| Raw source | Covered? | Notes |
|------------|----------|-------|
| docs/LESSONS.md | ❌ | No entries yet |
| docs/DECISIONS.md | ❌ | No entries yet |

## Next Health Check

Trigger recompilation when:
- [ ] 5+ new LESSONS.md entries
- [ ] New research document added
- [ ] Major architectural decision
- [ ] 30 days since last health check
```

Create `docs/wiki/INDEX.md`:
```markdown
# {Project Name} Wiki

LLM-compiled knowledge base. Maintained by LLM — do not edit manually.
Raw sources: `docs/LESSONS.md`, `docs/DECISIONS.md`.

Last compiled: {date} | Articles: 0

## Articles

<!-- No articles yet. Wiki will be populated as LESSONS and DECISIONS accumulate. -->

## How This Wiki Works

Follows Karpathy's LLM Knowledge Base pattern:
1. Raw sources (LESSONS.md, DECISIONS.md, research/) are human-edited
2. Wiki articles are LLM-compiled from raw sources
3. Health checks audit for staleness and gaps
4. Run `/wiki-compile` to recompile after adding raw source material
```

Then update CLAUDE.md if it exists — add or update the Knowledge Base section.
Exit with: "Wiki initialized. Add lessons and decisions, then run `/wiki-compile` to generate articles."

---

## Step 1: Assess What Changed

Read the **compile tracker** for last compile date and counts. Two possible locations:
- `docs/wiki/HEALTH.md` (legacy compile tracker, CB-style)
- `docs/wiki/INDEX.md` (Karpathy-current — INDEX has counter "**Articles:** N | **Last compiled:** YYYY-MM-DD")

Use whichever exists. If both exist, prefer INDEX.md as the source of truth and treat HEALTH.md as historical artifact.

Then discover what's new:

```bash
# Pick compile tracker file (INDEX.md preferred, HEALTH.md fallback)
if [ -f "docs/wiki/INDEX.md" ]; then
  COMPILE_TRACKER="docs/wiki/INDEX.md"
elif [ -f "docs/wiki/HEALTH.md" ]; then
  COMPILE_TRACKER="docs/wiki/HEALTH.md"
fi

# Find raw files modified since last compile (search both raw/ and research/)
if [ -n "$COMPILE_TRACKER" ]; then
  echo "=== FILES NEWER THAN LAST COMPILE ($COMPILE_TRACKER) ==="
  find docs/LESSONS.md docs/DECISIONS.md ARCHITECTURE.md docs/raw docs/research -newer "$COMPILE_TRACKER" -name "*.md" 2>/dev/null
fi
```

Count current raw source entries (regex handles BOTH date-prefix and legacy formats):

```bash
echo "=== CURRENT COUNTS ==="
echo "Lessons:   $(grep -cE '^## (\[[0-9-]+\] )?L-' docs/LESSONS.md 2>/dev/null || echo 0)"
echo "Decisions: $(grep -cE '^## (\[[0-9-]+\] )?AD-' docs/DECISIONS.md 2>/dev/null || echo 0)"

# Karpathy raw layer (preferred for new projects)
[ -d "docs/raw" ] && echo "Raw papers/exports: $(find docs/raw -name '*.md' -o -name '*.pdf' -o -name '*.txt' 2>/dev/null | grep -v '.gitkeep' | wc -l | tr -d ' ')"

# Legacy research layer (CB-style)
[ -d "docs/research" ] && echo "Research files: $(find docs/research -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
```

**Date-prefix queries (Karpathy log.md pattern, when format is date-prefixed):**
```bash
# Lessons added in last 7 days
grep -E '^## \[' docs/LESSONS.md | sort | tail -10

# Decisions added in current month
grep -E '^## \[2026-04' docs/DECISIONS.md
```

Read the new entries (diff since last compile). For LESSONS.md and DECISIONS.md,
read from the end to find entries added since the last known count in HEALTH.md.

**If nothing changed:** Tell the user "Wiki is up to date. No recompilation needed."
and exit. (Unless user explicitly asked to recompile — then do a full recompile anyway.)

---

## Step 2: Map Changes to Articles (Dynamic Routing)

**Do NOT use a hardcoded routing table.** Instead, use LLM reasoning:

1. Read `docs/wiki/INDEX.md` — specifically the source coverage table and article list
2. Read the new/changed raw source entries
3. For each new entry, determine which wiki article(s) it affects:
   - Read the topic/content of the new entry
   - Read the first 10 lines of each wiki article to understand its scope
   - Map by topic relevance, not by filename pattern

4. If a new entry doesn't fit any existing article:
   - Ask via AskUserQuestion: "New lesson/decision about [topic] doesn't fit existing articles. Create new article `{suggested-name}.md` or merge into `{closest-article}.md`?"

Present the mapping before proceeding:

```
RECOMPILATION PLAN:
  New entries: L-012, L-013, AD-009
  Affected articles:
    - technical-architecture.md ← L-012 (RAGFlow config issue)
    - privacy-and-compliance.md ← AD-009 (new DPA template)
  New article needed:
    - deployment-guide.md ← L-013 (Docker deployment lesson)
  Unaffected articles: 5 (skipping)
```

AskUserQuestion: "This is the recompilation plan. Proceed?"
- A) Proceed with recompilation
- B) Adjust mapping (let me specify)

---

## Step 3: Recompile Affected Articles

For each affected article:

1. **Read** the current wiki article (full content)
2. **Read ALL raw sources** that feed into it (from INDEX.md source coverage + new entries)
3. **Rewrite** the article, following these rules:

### Article Rules

- **Max 300 lines** per article. If longer, split into two articles.
- **Structure:**
  ```markdown
  # {Title}

  {2-3 sentence overview}

  ## {Section 1}
  {Content with source references}

  ## {Section 2}
  ...

  ## Key Pitfalls
  {Lessons learned, common mistakes}

  ## Related
  - [{Other Article}]({other-article}.md)
  ```

- **Source references:** Inline as `(source: docs/DECISIONS.md AD-007)` or `(source: docs/LESSONS.md L-012)` or `(source: docs/research/filename.md)`
- **Cross-references:** As `[Title](filename.md)` linking to other wiki articles
- **No fluff.** This is developer reference material, not marketing.
- **Preserve accurate existing content.** Don't rewrite from scratch unless structure changed significantly. Add new information, update outdated sections.
- **Polish and English OK.** Match the language of the raw sources. If the project is bilingual, wiki can be bilingual.

### New Article Creation

If creating a new article:
1. Filename: `lowercase-kebab-case.md`
2. Write following the standard structure above
3. Add cross-references to/from related articles
4. Add to INDEX.md

---

## Step 4: Verify Cross-References

Check all wiki links are valid:

```bash
echo "=== CROSS-REFERENCE CHECK ==="
for f in docs/wiki/*.md; do
  grep -o '\[.*\]([a-z].*\.md)' "$f" 2>/dev/null | grep -o '([^)]*\.md)' | tr -d '()' | while read ref; do
    [ ! -f "docs/wiki/$ref" ] && echo "BROKEN: $f → $ref"
  done
done
echo "Done."
```

Fix any broken links.

---

## Step 5: Update HEALTH.md

Rewrite `docs/wiki/HEALTH.md` with:

```markdown
# Wiki Health Check — {date} (Recompile #{N})

## Overall Status: {GREEN / YELLOW / RED}

{One-line summary of what was recompiled and why}

## Coverage Audit

| Raw source | Covered? | Wiki article(s) |
|------------|----------|-----------------|
| docs/LESSONS.md ({N} entries) | ✅/❌ | {list} |
| docs/DECISIONS.md ({N} entries) | ✅/❌ | {list} |
| docs/research/*.md | ✅/❌ | {list} |
| ARCHITECTURE.md | ✅/❌ | {article} |

## Cross-Reference Integrity

{List all wiki articles, ✅ if links valid}

## Gaps Identified

| Gap | Severity | Action |
|-----|----------|--------|
| {description} | Low/Med/High | {what to do} |

## Staleness Risk

| Article | Risk | Why |
|---------|------|-----|
| {article} | Low/Med/High | {reason} |

## Next Health Check

Trigger recompilation when:
- [ ] 5+ new LESSONS.md entries since last compile
- [ ] New research document added
- [ ] Major architectural decision
- [ ] 30 days since last health check

Next scheduled: {date + 30 days} or on trigger, whichever comes first.
```

---

## Step 6: Update INDEX.md

Update `docs/wiki/INDEX.md`:
- Article count and last compiled date in header
- Add/remove articles from the article list
- Update cross-reference matrix if new links were added
- Update source coverage table with current raw source → article mapping

---

## Step 7: Run Mechanical Validator (if available)

If the repo has the new wiki contract + validator, run the mechanical gate after updating wiki files:

```bash
if [ -x "scripts/wiki/check.sh" ]; then
  ./scripts/wiki/check.sh
elif [ -f "docs/wiki/manifest.json" ] && [ -f "scripts/wiki/validate.mjs" ]; then
  if [ -f "package.json" ] && grep -q '"lint:wiki"' package.json 2>/dev/null && command -v npm >/dev/null 2>&1; then
    npm run lint:wiki
  elif command -v node >/dev/null 2>&1; then
    node scripts/wiki/validate.mjs
  else
    echo "WARNING: wiki validator present but node is unavailable; skipping mechanical check"
  fi
fi
```

Treat validator failures as blockers before committing.

---

## Step 8: Update CLAUDE.md Knowledge Base Table (if exists)

If `CLAUDE.md` has a `## Knowledge Base` section (or `## Knowledge Base — Read Before Working`):
- Add new wiki articles to the routing table
- Remove deleted articles
- Update descriptions if article scope changed

---

## Step 9: Commit (if in a git repo)

```bash
if git rev-parse --git-dir > /dev/null 2>&1; then
  # Stage wiki + raw layers (Karpathy-current and legacy)
  git add docs/wiki/ docs/LESSONS.md docs/DECISIONS.md CLAUDE.md
  [ -d "docs/raw" ] && git add docs/raw/
  [ -d "docs/research" ] && git add docs/research/
  git commit -m "docs: recompile wiki — {summary of changes}"
fi
```

If not a git repo, skip silently. If in a git repo BUT not yet initialized in HORACY-style (no `git init`), suggest user runs `git init` per Karpathy KB pattern (audit trail for wiki changes is critical, especially for legal/compliance projects).

## Karpathy-style cross-skill awareness

If the project has these Karpathy-current artifacts, reference them:

- **`docs/wiki/wiki-health-check.md`** — separate lint pass methodology with 9 categories (orphans, stale, contradictions, broken refs, Karpathy compliance score). Run health check **after** wiki-compile to verify integrity.
- **`docs/wiki/karpathy-kb-alignment.md`** — pattern audit + Obsidian integration plan + deferred decisions log.
- **`docs/wiki/monitoring-stack.md`** — cyclical monitoring of dependencies. New monitor #10 (weekly Sunday) runs wiki-health-check methodology.
- **Memory hygiene rule in CLAUDE.md** — "verify before recommending from wiki >14 dni". Wiki-compile should preserve `**Date:**` headers in articles so freshness check works.

---

## Integration with gstack Skills

This skill reads and writes files that other gstack skills depend on:

| gstack skill | Reads | wiki-compile impact |
|-------------|-------|---------------------|
| `/plan-ceo-review` | CLAUDE.md → KB table → wiki articles | KB table must be current |
| `/plan-eng-review` | CLAUDE.md, TODOS.md, ARCHITECTURE.md | ARCHITECTURE.md is a raw source |
| `/review` | CLAUDE.md | KB table routes reviewers to relevant wiki |
| `/ship` | TODOS.md, CHANGELOG.md, VERSION | May add LESSONS/DECISIONS entries → trigger recompile |
| `/document-release` | README, ARCHITECTURE, CONTRIBUTING, CLAUDE.md | Updates ARCHITECTURE.md → raw source changed |
| `/checkpoint` | Saves project state | Should note wiki health status |

### When to proactively suggest `/wiki-compile`:

- After `/ship` completes and LESSONS.md or DECISIONS.md were updated
- After `/document-release` updates ARCHITECTURE.md
- When HEALTH.md shows last compile > 30 days ago
- When user adds entries to LESSONS.md or DECISIONS.md manually
- When user says "is the wiki up to date?" or "refresh knowledge base"

---

## Modes

### Full Recompile
Recompile ALL wiki articles from scratch. Use when:
- First compile after initialization
- Major structural change (project pivot, new architecture)
- User explicitly asks for full recompile

### Incremental Recompile (default)
Only recompile articles affected by new raw source entries. Use when:
- New LESSONS.md or DECISIONS.md entries added
- New research document added
- Triggered by staleness check

### Health Check Only
Don't recompile — just assess staleness and report. Use when:
- User asks "is the wiki up to date?"
- Periodic check (30-day trigger)

Detect mode from user intent. Default to incremental.
