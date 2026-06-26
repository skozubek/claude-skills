---
name: wiki-brief
description: |
  Morning push briefing of the project wiki + raw sources. Generates a self-contained
  HTML artifact (tables, badges, timeline, color-coded triage) and saves it to the
  Obsidian inbox, then opens it. Surfaces what changed, what's stale, which FINDINGS
  need triage, and cross-links the user might've missed across LESSONS/DECISIONS/wiki.
  Sister to /wiki-query (pull) — this is the proactive push.
  Use when asked to "wiki brief", "morning brief", "brief me on the project",
  "what changed in the wiki", or run via /schedule for daily delivery.
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Wiki Brief

Push briefing for the project wiki + raw sources. The opinionated complement to `/wiki-query`.

**Output**: a self-contained HTML file in `~/Documents/Notes/Obsidian/00 Inbox/wiki-brief-YYYY-MM-DD.html`, opened automatically. Plus a 3-line terminal summary so you get signal even if you don't open the file.

**Inputs harvested**:

- `docs/wiki/*.md` + `docs/wiki/manifest.json` + `docs/wiki/HEALTH.md`
- `docs/LESSONS.md` — entries from the last 14 days
- `docs/DECISIONS.md` — entries from the last 14 days
- `docs/FINDINGS.md` — all currently-open entries
- `git log --since="14 days ago"` — what actually shipped
- `scripts/wiki/check.sh` — mechanical integrity gate (if present)

## Run order

### 1. Sanity-check the project layout

```bash
[ -d docs/wiki ] || { echo "No docs/wiki/ — wiki-brief needs a Karpathy-pattern repo. Run /wiki-compile first or skip this skill."; exit 1; }
```

### 2. Harvest sources in parallel

```bash
# Wiki manifest + health
MANIFEST=$(cat docs/wiki/manifest.json 2>/dev/null)
HEALTH=$(cat docs/wiki/HEALTH.md 2>/dev/null)

# Wiki article freshness — file mtime + Updated metadata
for f in docs/wiki/*.md; do
  UPDATED=$(grep -m1 '^\*\*Updated:\*\*' "$f" | sed 's/.*Updated:\*\* //; s/  *$//')
  MTIME=$(stat -f '%Sm' -t '%Y-%m-%d' "$f" 2>/dev/null)
  echo "$f|$UPDATED|$MTIME"
done

# Recent LESSONS / DECISIONS (last 14 days, Karpathy date-prefix format)
CUTOFF=$(date -v-14d +%Y-%m-%d 2>/dev/null || date -d '14 days ago' +%Y-%m-%d)
awk -v cutoff="$CUTOFF" '
  /^## \[/ { in_block=1; date=substr($2,2,10); buf=$0"\n"; next }
  in_block && /^## / { if (date >= cutoff) print buf; in_block=0; buf="" }
  in_block { buf=buf $0"\n" }
  END { if (in_block && date >= cutoff) print buf }
' docs/LESSONS.md
# Same for DECISIONS

# Open FINDINGS — top-of-file is newest by convention
awk '/^## \[/ {date=substr($2,2,10); print date "|" $0}' docs/FINDINGS.md

# Recent commits — what actually shipped
git log --since="14 days ago" --pretty=format:"%h|%ad|%s" --date=short

# Mechanical integrity gate
[ -x scripts/wiki/check.sh ] && scripts/wiki/check.sh 2>&1 | tail -20
```

### 3. Compute metrics

- **Freshness score (0-10)**: fraction of wiki articles whose `Updated:` is within 30 days, scaled to 10. If `manifest.json` lists tracked files, use that set; otherwise all `docs/wiki/*.md` excluding `INDEX.md`/`HEALTH.md`/`manifest.json`.
- **FINDINGS open**: count of `## [` headings in `docs/FINDINGS.md`. Each gets an age bucket: `<7d=fresh`, `7-14d=warm`, `>14d=stale`.
- **LESSONS this period / DECISIONS this period**: count from awk output above.
- **Commits**: total, plus files-touched count from `git log --shortstat`.

### 4. Curate "Connections you missed"

**This is the killer feature. Treat it as the most important section.**

Read the harvested LESSONS/DECISIONS/FINDINGS bodies and the wiki INDEX. Look for 2-5 cross-links that *aren't yet captured*:

- Two LESSONS in different domains sharing a root cause
- A FINDING that should trigger `/wiki-compile` of a specific article
- A DECISION that contradicts or updates an older wiki article
- A pattern across 3+ FINDINGS suggesting a missing wiki section
- A wiki article whose `Updated:` predates a related new LESSON/DECISION

Rules:

- Each connection cites specific IDs (`L-NNN`, `AD-NNN`, `F-NNN`, `docs/wiki/<file>.md`)
- Each proposes a concrete next action (`/wiki-compile`, triage F-NNN, write L-NNN, archive, ignore)
- **Quality over quantity. 2 real ones beats 5 generic ones.**
- **If no genuine connections found, write `No new cross-links this brief` — DO NOT manufacture.**

### 5. Render the HTML

Single self-contained file. Inline CSS, no JS, no external assets, no CDN. Use the template below — fill the placeholders.

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wiki Brief — {{PROJECT}} — {{DATE}}</title>
<style>
:root {
  --bg: #fafaf9; --fg: #1c1917; --muted: #78716c; --border: #e7e5e4;
  --card: #ffffff; --accent: #0891b2;
  --fresh: #16a34a; --warm: #eab308; --stale: #dc2626;
  --mono: ui-monospace, "SF Mono", Menlo, monospace;
  --sans: -apple-system, BlinkMacSystemFont, "Inter", system-ui, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #0c0a09; --fg: #fafaf9; --muted: #a8a29e; --border: #292524; --card: #1c1917; }
}
* { box-sizing: border-box; }
body { font-family: var(--sans); background: var(--bg); color: var(--fg); margin: 0; padding: 2rem; max-width: 1100px; margin-inline: auto; line-height: 1.55; }
h1 { font-size: 1.75rem; margin: 0 0 .25rem; letter-spacing: -0.02em; }
h2 { font-size: 1.15rem; margin: 2.5rem 0 .75rem; letter-spacing: -0.01em; border-bottom: 1px solid var(--border); padding-bottom: .35rem; }
h3 { font-size: 0.95rem; margin: 1.25rem 0 .5rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
.hero { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; margin: 1.5rem 0; }
.hero .punch { font-size: 1.1rem; line-height: 1.5; }
.muted { color: var(--muted); font-size: 0.85rem; }
.grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: .75rem; margin: 1rem 0; }
.tile { background: var(--card); border: 1px solid var(--border); border-radius: 6px; padding: 1rem; }
.tile .label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
.tile .value { font-size: 1.75rem; font-weight: 600; margin-top: .25rem; line-height: 1; }
.tile .delta { font-size: 0.8rem; color: var(--muted); margin-top: .35rem; }
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; margin: .5rem 0 1rem; }
th, td { text-align: left; padding: .5rem .75rem; border-bottom: 1px solid var(--border); }
th { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); font-weight: 600; }
td.mono, code { font-family: var(--mono); font-size: 0.85em; }
.badge { display: inline-block; padding: .15rem .55rem; border-radius: 999px; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.02em; }
.badge.fresh { background: color-mix(in srgb, var(--fresh) 15%, transparent); color: var(--fresh); }
.badge.warm  { background: color-mix(in srgb, var(--warm) 18%, transparent); color: var(--warm); }
.badge.stale { background: color-mix(in srgb, var(--stale) 15%, transparent); color: var(--stale); }
.connection { background: var(--card); border-left: 3px solid var(--accent); padding: .75rem 1rem; margin: .5rem 0; border-radius: 0 6px 6px 0; }
.connection .ids { font-family: var(--mono); font-size: 0.8rem; color: var(--accent); }
.connection .action { display: inline-block; margin-top: .35rem; font-size: 0.8rem; color: var(--muted); }
.connection .action::before { content: "→ "; color: var(--accent); }
.timeline { font-family: var(--mono); font-size: 0.85rem; }
.timeline-row { display: grid; grid-template-columns: 90px 60px 1fr; gap: .75rem; padding: .35rem 0; border-bottom: 1px dashed var(--border); }
.timeline-row .date { color: var(--muted); }
.timeline-row .kind { font-weight: 600; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--accent); }
footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--border); color: var(--muted); font-size: 0.8rem; }
.empty { color: var(--muted); font-style: italic; padding: .5rem 0; }
@media (max-width: 700px) { .grid { grid-template-columns: repeat(2, 1fr); } body { padding: 1rem; } }
</style>
</head>
<body>

<h1>Wiki Brief — {{PROJECT}}</h1>
<div class="muted">{{DATE_LONG}} · {{BRANCH}}</div>

<div class="hero">
  <div class="punch">{{HERO_PUNCH}}</div>
</div>

<div class="grid">
  <div class="tile"><div class="label">Wiki Freshness</div><div class="value">{{FRESHNESS}}/10</div><div class="delta">{{FRESHNESS_DELTA}}</div></div>
  <div class="tile"><div class="label">FINDINGS Open</div><div class="value">{{FINDINGS_COUNT}}</div><div class="delta">{{FINDINGS_STALE}} stale</div></div>
  <div class="tile"><div class="label">LESSONS · 14d</div><div class="value">{{LESSONS_COUNT}}</div><div class="delta">{{LESSONS_NEW_IDS}}</div></div>
  <div class="tile"><div class="label">DECISIONS · 14d</div><div class="value">{{DECISIONS_COUNT}}</div><div class="delta">{{DECISIONS_NEW_IDS}}</div></div>
</div>

<h2>Connections you missed</h2>
{{CONNECTIONS_BLOCK}}
<!-- Each connection rendered as:
<div class="connection">
  <div class="ids">L-NNN ↔ AD-NNN ↔ docs/wiki/article.md</div>
  <div>One-line synthesis of the cross-link.</div>
  <div class="action">{{ACTION}}</div>
</div>
If none: <div class="empty">No new cross-links this brief.</div>
-->

<h2>FINDINGS triage</h2>
{{FINDINGS_TABLE}}
<!--
<table>
  <thead><tr><th>ID</th><th>Title</th><th>Age</th><th>Action</th></tr></thead>
  <tbody>
    <tr><td class="mono">F-030</td><td>...</td><td><span class="badge stale">23d</span></td><td>...</td></tr>
  </tbody>
</table>
-->

<h2>Wiki article freshness</h2>
{{WIKI_TABLE}}
<!-- Only include articles tracked by manifest.json. Sort by stalest first. Show top 8. -->

<h2>Recent activity · 14 days</h2>
{{TIMELINE_BLOCK}}
<!-- Interleaved LESSONS / DECISIONS / commits, newest first.
<div class="timeline">
  <div class="timeline-row"><span class="date">2026-05-08</span><span class="kind">L-178</span><span>Title here</span></div>
  <div class="timeline-row"><span class="date">2026-05-07</span><span class="kind">commit</span><span>de156e8 cycle 6 — drop urlSummary side-effects</span></div>
</div>
-->

<footer>
Generated {{TIMESTAMP}} · /wiki-brief · sources: docs/wiki, LESSONS.md, DECISIONS.md, FINDINGS.md, git log
</footer>

</body>
</html>
```

### 6. Save and open

```bash
DATE=$(date +%Y-%m-%d)
PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
DEST="$HOME/Documents/Notes/Obsidian/00 Inbox/wiki-brief-${PROJECT}-${DATE}.html"
# Write the rendered HTML to $DEST via the Write tool
open "$DEST"
```

Filename pattern: `wiki-brief-<project>-<date>.html` so multiple projects don't clobber each other.

### 7. Terminal summary

Print exactly this shape so the user gets the punch even without opening the file:

```
Wiki brief — {{PROJECT}} — {{DATE}}
Freshness {{N}}/10 · {{FINDINGS_OPEN}} FINDINGS open ({{STALE}} stale) · {{CONNECTIONS}} new cross-links
{{HERO_PUNCH_ONE_LINE}}
Brief: ~/Documents/Notes/Obsidian/00 Inbox/wiki-brief-{{PROJECT}}-{{DATE}}.html (opening)
```

## Conventions

- **Self-contained HTML only.** No CDN, no JS frameworks, no external fonts, no images. One file you can email, archive, diff against next week's.
- **System font stack + auto dark/light.** Don't ship a theme system; respect `prefers-color-scheme`.
- **Tables, not graphs, by default.** Tables are denser per pixel for small datasets (typical wiki: <100 entries). Add a relationship subgraph only if 4+ items genuinely converge — and even then, a curated bullet beats a node diagram.
- **Color-coded badges over decoration.** FINDING age uses `fresh/warm/stale`. Wiki freshness same. Don't invent more colors.
- **Omit empty sections entirely.** No "no findings this week" filler. If FINDINGS is empty, drop the section. Same for connections, timeline, etc.
- **`Connections you missed` is the killer section.** It's the difference between a TOC and a brief. Curate hard. 2 real connections beat 5 manufactured.
- **Sparklines need ≥5 data points.** Skip otherwise. (Default: skip — wiki briefs run weekly at most, you won't have history fast.)
- **Project-scoped filename.** Always include the repo name so multi-project users don't clobber.
- **Don't write to the repo.** This skill writes to the Obsidian inbox only. Repo stays clean.

## Modes

- `/wiki-brief` — full brief (default)
- `/wiki-brief stale-only` — only the wiki freshness table + FINDINGS triage. No connections, no timeline. Good for cron.
- `/wiki-brief connections-only` — only the curated cross-link section. Good when you've already seen today's diff and just want the synthesis.

## Related skills

- `/wiki-compile` — recompile wiki from raw sources (run when freshness flagged or stale articles surface in this brief)
- `/wiki-health` — full audit of wiki integrity + freshness (deeper than this brief)
- `/wiki-query` — pull-mode Q&A on demand (sister skill: pull vs push)
- `/briefing` — Twitter/external news briefing (sibling skill, same template philosophy)

## Scheduling

To run daily, pair with `/schedule`:

```
/schedule create wiki-brief-daily "0 8 * * *" /wiki-brief
```

The HTML lands in your Obsidian inbox each morning; `/tidy` will route it to `10 Areas/Weekly/` or `30 Archive/` based on age.
