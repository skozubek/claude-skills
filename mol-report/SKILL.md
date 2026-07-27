---
name: mol-report
description: |
  Cross-project MOL work reporting for Serge's invoicing. Generates the weekly
  note and the monthly invoice text by git-scanning ALL repos under
  ~/Coding/MOL/ (campaign-builder + Hubi + AADC + …), not a single repo.
  Use when Serge says "notka tygodniowa", "weekly note", "wpis na fakturę",
  "faktura", "monthly summary", "combined retro", "MOL retro", or asks for a
  cross-project retro from inside any MOL repo.
  NOT the same as gstack /retro (which is single-repo). This is the cross-project
  layer that feeds invoicing.
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - AskUserQuestion
---

# /mol-report — cross-project MOL reporting

Serge bills MOL for work across several repos under `~/Coding/MOL/` in a given
week (campaign-builder, Hubi, AADC, Sales Assistant, …). A single-repo `/retro`
systematically undercounts multi-project weeks — repeatedly a "light CB week" was
actually a heavy Hubi week. This skill produces the **cross-project** artifacts.

## Modes

- `/mol-report weekly [WNN]` — weekly note for the current ISO week (Mon–Sun),
  or week `WNN` if given. Writes `_reports/weekly/2026-WNN.md`.
- `/mol-report monthly [YYYY-MM]` — monthly invoice summary for the current month
  (or the given one). Writes `_reports/monthly/2026-MM.md`.
- `/mol-report` (no arg) — default to `weekly` for the current week.

Both modes also write a combined snapshot to
`~/Coding/MOL/.claude/retros/<date>-combined.json`.

## Hard rules (learned the hard way)

- **Cross-project by default.** Scan every git repo under `~/Coding/MOL/`, not just
  the cwd repo. The billing unit is "Serge this week", not one product. Discover
  with `find -maxdepth 3 -name .git`, never a `*/` glob (see Step 2).
- **Panel internal material NEVER enters a report.** `MOL/Panel/meta/` (state
  review, findings, decision and collaboration notes) is internal-only. Report the
  fact a review happened and the effort it took; never the content. Keep out:
  findings and their counts, names of functions/endpoints/tables tied to an
  access-control gap, HTTP codes or config flags describing exposure, colleagues'
  names attached to commit counts and LOC (write "second developer"), and
  unresolved disputes framed as who-holds-what-position. Test each sentence against
  "does this survive the report being forwarded outside MOL". Exclude `Panel/meta/`
  from mtime scans too — the filenames alone leak.
- **Multi-author repos: split by author.** Panel has three (Serge, second dev,
  Lovable bot); only Serge-authored commits are billable hours, the rest is context.
  Author names differ per repo (`skozubek-mol` in campaign-builder, `Serge Kozubek`
  and `Serge` elsewhere), so `--author="Serge"` returns a silent 0 in CB. Run
  `git shortlog -sn` before trusting any author split.
- **NEVER use `/retro global`.** Its discovery binary fails EPERM under Claude
  Code (macOS TCC: the `claude` process lacks Full Disk Access; Warp's grant does
  not propagate). Use the git-scan below. Root cause: `~/Coding/MOL/.claude/RETRO-POLICY.md`.
- **Formats are NOT duplicated here.** Read the format READMEs as source of truth
  before writing: `_reports/weekly/README.md` and `_reports/monthly/README.md`.
  If they change, this skill follows — do not hardcode the format.
- **Don't fabricate.** A repo with 0 commits in the window gets no section / no
  table row. Skip dormant repos silently.
- **Honest partial weeks.** If the week is written early (e.g. Friday before
  vacation), say so in the header and base `Active days: N/M` on real working days,
  not 7.
- **`anchor today` from the session, not the clock.** Take "today" from the
  `currentDate` reminder in the session. The system clock can drift in containers.
  Use `date` only for arithmetic OFF that anchor.
- **Lovable / `gpt-engineer-app[bot]` commits in Hubi = Serge steering = count as
  hours.** External auto-commits elsewhere = context, not hours — note and exclude.
- **Non-git projects (AADC sometimes uncommitted).** Count by file mtime + Codex
  sessions, NOT git-scan. See "Non-git projects" below.
- **Invoice text rules (monthly):** business Polish, nominal form, **NO numbers,
  NO internal jargon (Sprint/AD-NNN/F-NNN), NO negatives** ("bug"→"stabilizacja").
  Numbers go to the separate "Liczby (kontekst)" section. Per `monthly/README.md`.

## Step 0 — resolve root + window

```bash
MOL="$HOME/Coding/MOL"
[ -d "$MOL/_reports" ] || { echo "No $MOL/_reports — wrong machine/layout?"; exit 1; }

# ANCHOR: today from the session currentDate reminder, e.g. 2026-06-26.
# Set TODAY to that value. Do NOT trust `date` for the anchor.
TODAY="<YYYY-MM-DD from session currentDate>"

# --- weekly window (ISO Mon–Sun) ---
DOW=$(date -j -f "%Y-%m-%d" "$TODAY" +%u)              # 1=Mon..7=Sun
MON=$(date -j -v-$((DOW-1))d -f "%Y-%m-%d" "$TODAY" +%Y-%m-%d)
SUN=$(date -j -f "%Y-%m-%d" "$MON" -v+6d +%Y-%m-%d)
WK=$(date -j -f "%Y-%m-%d" "$TODAY" +%V); YR=$(date -j -f "%Y-%m-%d" "$TODAY" +%G)
SINCE="${MON}T00:00:00"; UNTIL="$(date -j -f "%Y-%m-%d" "$SUN" -v+1d +%Y-%m-%d)T00:00:00"
echo "WEEKLY W${WK} (${MON} .. ${SUN}) -> _reports/weekly/${YR}-W${WK}.md"

# --- monthly window (calendar month) ---
YM="${TODAY%-*}"                                       # YYYY-MM  (or override from arg)
MSTART="${YM}-01"
MEND="$(date -j -v+1m -f "%Y-%m-%d" "${MSTART}" +%Y-%m-%d)"   # first of next month
echo "MONTHLY ${YM} (${MSTART} .. ${MEND}) -> _reports/monthly/${YM}.md"
```

If the user passed an explicit `WNN` or `YYYY-MM`, override the computed window.
If the target file already exists, read it first and treat this as an update
(don't blind-overwrite a hand-edited report — diff intent, ask if unsure).

## Step 1 — read the format (source of truth)

Read whichever applies before writing:
- weekly → `~/Coding/MOL/_reports/weekly/README.md`
- monthly → `~/Coding/MOL/_reports/monthly/README.md`
- always → `~/Coding/MOL/.claude/RETRO-POLICY.md` (git-scan method + EPERM rationale)

Also read the latest existing report of the same kind for tone + structure
(e.g. last `weekly/2026-WNN.md`). Match it; this is synthesis, not raw dump.

## Step 2 — git-scan every MOL repo in the window

Discover repos by finding `.git`, NEVER by globbing `"$MOL"/*/`. Some repos sit a
level deeper (`Panel/panel-manager-marki`, `Leads/lead-qualification-app`) and the
glob silently dropped Panel — the top-priority project — from every report until
2026-07-27. **Sanity check: the repo list must include `Panel/panel-manager-marki`.**

```bash
find "$MOL" -maxdepth 3 -name .git -type d -not -path '*/node_modules/*' 2>/dev/null \
| sed 's|/.git$||' | sort | while read -r d; do
  name="${d#$MOL/}"
  cnt=$(git -C "$d" log --since="$SINCE" --until="$UNTIL" --no-merges --oneline 2>/dev/null | wc -l | tr -d ' ')
  [ "$cnt" -eq 0 ] && continue
  echo "=== $name : $cnt non-merge commits ==="
  git -C "$d" log --since="$SINCE" --until="$UNTIL" --no-merges --numstat --format="" 2>/dev/null \
    | awk 'NF==3 {add+=$1; del+=$2; if ($3 ~ /\.(test|spec)\./) t+=$1} END {print "ins="add" del="del" net="add-del" test_ins="t}'
  echo -n "active days: "; git -C "$d" log --since="$SINCE" --until="$UNTIL" --format="%ad" --date=format:"%Y-%m-%d" 2>/dev/null | sort -u | wc -l | tr -d ' '
  echo "authors:"; git -C "$d" log --since="$SINCE" --until="$UNTIL" --no-merges --format="%aN" 2>/dev/null | sort | uniq -c
  echo "types:"; git -C "$d" log --since="$SINCE" --until="$UNTIL" --no-merges --format="%s" 2>/dev/null | grep -oE '^[a-z]+' | sort | uniq -c | sort -rn
  echo "versions:"; git -C "$d" log --since="$SINCE" --until="$UNTIL" --format="%s" 2>/dev/null | grep -oE "v?[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?" | sort -V -u | sed -n '1p;$p'
  echo "subjects:"; git -C "$d" log --since="$SINCE" --until="$UNTIL" --no-merges --format="%ad %s" --date=format:"%m-%d" --reverse 2>/dev/null
done
```

For monthly, swap `$SINCE`/`$UNTIL` for `${MSTART}T00:00:00` / `${MEND}T00:00:00`
and also count merged PRs: `git -C "$d" log --since=… --until=… --merges --format="%s" | grep -c "Merge pull request"`.

## Step 3 — non-git projects (AADC / BAIC)

Some work (Google Apps Script for AADC car-brand offline-conversions) is
Codex-driven and sometimes uncommitted. Git-scan misses it. Count differently:

```bash
# touched files by mtime in the window
find "$MOL/AADC" -type f -not -path '*/.git/*' -newermt "${SINCE}" ! -newermt "${UNTIL}" 2>/dev/null
# Codex sessions touching these themes (readable, outside TCC)
grep -iE "aadc|offline|lead|jetour|baic|customer.?list" ~/.codex/session_index.jsonl 2>/dev/null
```

In the table, for a non-git project report **files touched + Codex sessions**
instead of commits/LOC, with the note "brak commitów (praca niezacommitowana)".
If AADC has commits in the window, treat it as a normal git repo instead.

## Step 4 — synthesize + write

- **Weekly:** follow `weekly/README.md`. Frame the week (heavy ship / cleanup /
  blocked), per-project sections (skip empty), the "Liczby" cross-project table
  with a **Razem** row, product status, blockers (tag `[CB]`/`[HUBI]`/…),
  engineering insights, next-week plan. First person or impersonal, no hype.
- **Monthly:** follow `monthly/README.md`. Lead with "Tekst na fakturę" (3
  nominal business sentences, no numbers/jargon/negatives), then "Liczby
  (kontekst)", "Główne dostarczenia (po obszarach)", "Stan aplikacji na koniec
  miesiąca", "Mapowanie do kodu" (the only place AD-NNN/Sprint/PR live), "Linki".
- **Combined JSON snapshot** → `~/Coding/MOL/.claude/retros/<TODAY>-combined.json`
  (schema: `type:"mol-combined"`, `date`, `window`, `repos:{<name>:{commits,
  insertions, deletions, net_loc, test_loc, active_days, version_range, releases,
  type-mix, ship}}`, `totals`, `headline`, `tweetable`). Match the latest existing
  snapshot in that dir.

## Step 5 — report to the user

Print: which file(s) written, the headline (what kind of week), and the
cross-project table (Razem). For monthly, show the "Tekst na fakturę" verbatim so
Serge can copy-paste. Note any project you could NOT measure (EPERM, non-git) so
the disclosure rides in the output, not silently dropped.

## Notes

- Nothing here is auto-committed. The `_reports/` files live in `~/Coding/MOL/`
  (separate from any single product repo). Serge commits/handles them manually.
- This skill is git-synced via `~/Coding/claude-skills/` → symlinked into
  `~/.claude/skills/mol-report`. On a fresh Mac: clone claude-skills + run
  `bootstrap.sh`, and ensure the MOL repos are cloned under `~/Coding/MOL/`.
