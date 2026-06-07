---
name: wiki-query
description: |
  Answer questions against the project wiki knowledge base. Use when the user
  asks about project architecture, past decisions, design rationale, competitive
  landscape, domain knowledge, or "what do we know about X". Works with the
  Karpathy KB pattern (docs/wiki/, LESSONS.md, DECISIONS.md).
  Triggers: "what do we know about", "how does X work in our project",
  "why did we choose", "what's our plan for", "wiki query", "query wiki",
  "search wiki", "what does the wiki say".
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - AskUserQuestion
---

# Wiki Query

Answer questions by searching and synthesizing knowledge from the project wiki.

This is a **project wiki** — it tracks architecture decisions, design rationale,
competitive intelligence, domain knowledge, and build plans. Queries are usually
"how should we build X" or "why did we choose Y", not "what is X" in the abstract.

## Search Strategy

### Step 1: CLAUDE.md routing table first

Read `CLAUDE.md` and find the `Knowledge Base` routing table (the `| Working on... | Read |`
section). This table is the **authoritative index** — it maps topics to wiki articles
and is maintained by humans. Use it as the primary lookup.

```bash
# Extract routing table entries
grep -A200 '| Working on' CLAUDE.md | grep '^\|' | head -50
```

Match the user's question to routing table entries. If the question touches multiple
domains (e.g., "how do privacy constraints affect our architecture?"), pull articles
from ALL matching rows.

### Step 2: INDEX.md for coverage gaps

If the routing table doesn't cover the question, or for broader queries, read
`docs/wiki/INDEX.md` for the full article catalog. Scan for articles related to
the question.

### Step 3: Read relevant articles

Read the wiki articles identified in Steps 1-2. **Most answers require 2-4 articles**
— project queries almost always span multiple topics. Follow cross-references
(`[[wikilinks]]` or markdown links) to pull in related context.

Priority order for reading:
1. Articles named in the CLAUDE.md routing table
2. Articles cross-referenced from those (one hop)
3. `docs/DECISIONS.md` entries relevant to the question (grep by keyword)
4. `docs/LESSONS.md` entries relevant to the question (grep by keyword)
5. `docs/raw/` files — last resort, only if wiki articles are insufficient

```bash
# Find relevant DECISIONS
grep -n -i "keyword" docs/DECISIONS.md | head -20

# Find relevant LESSONS
grep -n -i "keyword" docs/LESSONS.md | head -20
```

### Step 4: Check freshness

Before answering, check if the information might be stale:

- Look at `**Updated:**` or `**Date:**` metadata in wiki articles
- If article date > 14 days old AND the answer involves prices, model versions,
  competitor features, or tool availability — **warn the user** that this may need
  verification
- If the question is about current state (not historical decisions), prefer
  `docs/DECISIONS.md` and `docs/LESSONS.md` recent entries over older wiki articles

## Synthesize the Answer

### Format

Match the answer format to the question type:

- **"Why did we choose X?"** → decision rationale with AD-NNN reference, alternatives
  considered, trade-offs. Cite the DECISIONS.md entry.
- **"How does X work?"** → architecture explanation with component relationships.
  Reference the relevant wiki article sections.
- **"What do we know about X?"** → synthesis from multiple articles. Surface
  contradictions if any exist between articles.
- **"What's our plan for X?"** → roadmap/phasing from wiki + any relevant
  LESSONS learned. Flag if plan may be outdated.
- **Comparison** → table format. Pull from multiple competitive/technical articles.
- **"Can we do X?"** → constraints from privacy, architecture, and domain rules.
  Cross-reference Critical Rules from CLAUDE.md.

### Citations

Always cite wiki sources inline. Use the format that matches the source:

- Wiki article: `(see [[article-name]])` or `(see docs/wiki/article-name.md)`
- Decision: `(AD-NNN in docs/DECISIONS.md)`
- Lesson: `(L-NNN in docs/LESSONS.md)`
- Raw source: `(source: docs/raw/subfolder/filename)`
- CLAUDE.md rule: `(Critical Rule: "never send real client docs...")`

### Language

Follow the user's language. If they ask in Polish, answer in Polish.
Polish legal terminology must be correct (see Domain Rules in CLAUDE.md).

## After Answering

### Offer to save valuable synthesis

If the answer produced a non-obvious synthesis — a new connection between topics,
a resolved contradiction, a cross-cutting analysis — offer to save it:

> "This synthesis connects [X] and [Y] in a way that isn't in any single wiki article.
> Want me to save the key insight to LESSONS.md?"

If the user agrees:
- Append to `docs/LESSONS.md` in the standard format:
  `## [YYYY-MM-DD] L-NNN: {title}`
- Follow the project's Anti-Bloat Write Rule — only save if it passes the test:
  "Will this be signal in 6 months, or will it force re-verification?"
- Do NOT create new wiki articles from a query — that's `/wiki-compile`'s job

### Flag wiki gaps

If the question couldn't be fully answered from the wiki, tell the user:

> "The wiki doesn't cover [specific gap]. Consider adding a note to LESSONS.md
> or DECISIONS.md and running `/wiki-compile` to close this gap."

### Suggest deeper exploration

If the answer opens up adjacent questions the user might want to explore:

> "Related threads you might want to pull: [1-2 specific questions with pointers
> to which wiki articles would be starting points]"

## Conventions

- **Search the wiki first.** Only go to `docs/raw/` if the wiki doesn't have the answer.
- **Cite your sources.** Every factual claim links to the wiki page it came from.
- **Cross-article synthesis is the norm.** Single-article answers are the exception.
- **Respect Anti-Bloat.** Don't propose saving trivial lookups. Only offer to save
  synthesis that genuinely compounds the wiki.
- **Freshness warnings are mandatory.** If an answer depends on data that may have
  changed (prices, versions, competitor features, model capabilities), say so.
- **Never fabricate wiki content.** If the wiki doesn't say it, don't pretend it does.
  Say "the wiki doesn't cover this" and suggest where to look.

## Related Skills

- `/wiki-compile` — recompile wiki from raw sources (when gaps are found)
- `/wiki-health` — audit wiki quality and freshness
