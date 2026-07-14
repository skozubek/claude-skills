---
name: transcribe
version: 1.0.0
description: |
  Transcribe audio recordings from Obsidian vault using mlx_whisper (Apple Silicon)
  and create structured meeting/note from the transcript. Works from any directory.
argument-hint: "[all | latest | filename] — default: latest unprocessed recording"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# /transcribe — Audio to Meeting Note

Transcribe Obsidian audio recordings and create structured notes from them.

## User-invocable
When the user types `/transcribe`, run this skill.

## Arguments

- `/transcribe` — transcribe the latest unprocessed recording
- `/transcribe all` — transcribe all unprocessed recordings
- `/transcribe Recording 20260211124207.m4a` — transcribe specific file

## Step 0: Detect Vault Path

```bash
if [ -d "$HOME/Documents/Notes/Obsidian" ]; then
  echo "$HOME/Documents/Notes/Obsidian"
elif [ -d "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Documents/Notes/Obsidian" ]; then
  echo "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Documents/Notes/Obsidian"
fi
```

Use the result as `VAULT` for all subsequent operations.

## Step 1: Check Environment

Verify `mlx_whisper` is available:
```bash
which mlx_whisper 2>/dev/null || echo "NOT_FOUND"
```

If not found, tell the user:
```
mlx_whisper not installed. On Apple Silicon Mac, run:
  uv tool install mlx-whisper --python 3.12
This skill requires Apple Silicon. Intel Mac support (via OpenAI API) coming soon.
```

## Step 2: Find Recordings

**Unprocessed = the recording still sits in the vault root.** Step 5 moves every
processed recording into `$VAULT/Recordings/`, so the root is the single source
of truth. No timestamp-matching against note filenames, no `.done` markers —
if the `.m4a` is still in the root, it hasn't been done.

```bash
find "$VAULT" -maxdepth 1 -name "Recording *.m4a" | sort
```

Based on the argument:
- `latest` (default): the most recent file in the root
- `all`: every file in the root
- specific filename: that file

If the root has no `Recording *.m4a`, say so and stop.

## Step 3: Transcribe

For each recording to process:

```bash
mlx_whisper "$VAULT/Recording YYYYMMDDHHMMSS.m4a" --model mlx-community/whisper-large-v3-turbo --language pl --condition-on-previous-text False --output-dir /tmp/transcriptions
```

**`--condition-on-previous-text False` is mandatory.** Without it, large-v3-turbo falls into a repetition-loop hallucination on long audio with silence/crosstalk — it spews hundreds of identical lines (e.g. "Tak." or one repeated sentence) and silently eats the real content. With the flag off, each segment is transcribed independently and the loop can't propagate. (Burned a 2h14m meeting on 2026-06-22: first pass = ~640 junk "Tak." lines, ~2/3 of the meeting lost; re-run with the flag recovered everything.)

**Language detection:** Default to `--language pl` (Serge's primary meeting language). If the transcript looks like English (check first few lines), re-run with `--language en`.

The output will be in `/tmp/transcriptions/` as `.txt`, `.srt`, `.vtt` files. Read the `.txt` file for the raw transcript.

**Sanity check before building the note:** count standalone repeated lines, e.g. `grep -c '^Tak\.$' "/tmp/transcriptions/Recording ....txt"`. A high count (dozens+) on a long recording means the loop still bit — re-run, optionally adding `--hallucination-silence-threshold 2`. Don't build a note from a looped transcript.

## Step 4: Create Meeting Note

Parse the recording filename for date/time: `Recording YYYYMMDDHHMMSS.m4a` → extract date and time.

**Note filename carries a topic slug** so the meeting is identifiable at a glance
in the file list. After reading the transcript, derive a 2-5 word topic from the
main subject (client, project, or theme) and build:

`$VAULT/10 Areas/Meetings/{DD.MM.YYYY} Meeting {Topic}.md`

Examples: `15.06.2026 Meeting Marceli.md`, `22.06.2026 Meeting CRM status raportu.md`.
Keep the slug short and filesystem-safe (no `/ : ?`). If the transcript is too thin
to name a clear topic, fall back to plain `{DD.MM.YYYY} Meeting.md`.

```yaml
---
date: DD.MM.YYYY
tags: [meeting, transcribed]
type: meeting
area:
source: "Recording YYYYMMDDHHMMSS.m4a"
---
```

Structure the note:

```markdown
# Meeting — DD.MM.YYYY HH:MM

**Source:** `Recording YYYYMMDDHHMMSS.m4a` (archived in `~/Obsidian-Recordings-Archive/`)

## Summary
<AI-generated 3-5 bullet point summary of key topics discussed>

## Key Decisions
<extract any decisions or conclusions from the transcript>

## Action Items
- [ ] <extract any commitments, tasks, or follow-ups mentioned>

## Transcript
<FULL verbatim transcript text — the whole thing, not a paraphrase or a
condensed version. Paste the raw whisper output as-is. It is the primary
artifact; the summary above is a convenience layer on top of it.>

---
Related: [[relevant hub links based on content]]
```

**Section order is deliberate:** scannable digest first (Summary → Key Decisions
→ Action Items), full raw transcript last. The transcript is the source of truth
and MUST be the complete verbatim text — never silently substitute a summarized
or paraphrased version. If a shorter transcript is ever wanted, that's a change
to this skill, not a per-note judgment call.

**Hub linking:** Read the transcript content and determine which hubs are relevant:
- If MOL/campaign/client topics → `[[MOL]]`
- If business ideas discussed → `[[Business Ideas]]`
- If trading mentioned → `[[Trading Psychology]]`
- If tools/tech discussed → `[[Tools & Workflows]]`
- Always search vault for cross-links based on transcript content (same as /capture Step 2)

## Step 5: Organize Files

Move the processed recording to the **off-sync audio archive** — a folder OUTSIDE
the vault so the large `.m4a` files don't churn through iCloud sync. The vault
(`~/Documents`) is iCloud-synced; `~/Obsidian-Recordings-Archive` (home root) is not.

```bash
ARCHIVE="$HOME/Obsidian-Recordings-Archive"
mkdir -p "$ARCHIVE"
mv "$VAULT/Recording YYYYMMDDHHMMSS.m4a" "$ARCHIVE/"
```

**Trade-off (accepted):** the note's `![[Recording...]]` embed no longer resolves
inside Obsidian, because the audio lives outside the vault. The transcript in the
note is the primary artifact; the archived `.m4a` is kept as raw evidence for
disputes or future re-transcription with better models. If you ever need playback,
the file is in `~/Obsidian-Recordings-Archive/`.

The root staying empty of `Recording *.m4a` is what Step 2 uses to mean "processed".

## Step 6: Report

```
Transcribed → 10 Areas/Meetings/DD.MM.YYYY Meeting {Topic}.md
Duration: ~Xm | Language: pl | Words: ~N
Summary: <one-line summary>
Links: [[Hub]] [[Cross-link]]
Audio archived → ~/Obsidian-Recordings-Archive/
```

If multiple recordings were processed, show a summary table.

## Rules

- ALWAYS create the Meetings folder if it doesn't exist: `mkdir -p "$VAULT/10 Areas/Meetings"`
- ALWAYS move audio to `~/Obsidian-Recordings-Archive/` (off-sync) after processing to keep the vault light
- Reference the audio by filename in the note's Source line (plain text, not an `![[embed]]`) — the file lives outside the vault so the embed won't resolve
- The topic slug (Step 4) normally keeps same-date notes distinct. If two recordings share a date AND topic, number them: `DD.MM.YYYY Meeting {Topic} 2.md`
- If transcript is very short (<50 words), skip Summary/Decisions/Actions sections — just save the transcript
- Keep the summary factual — don't invent details not in the transcript
- For the summary and action items, use the transcript language (Polish or English)
