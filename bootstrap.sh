#!/usr/bin/env bash
# Bootstrap a fresh Mac to match this machine's Claude Code custom layer.
# Idempotent — safe to re-run. Run after `git pull` in this repo.
#
#   bash ~/Coding/claude-skills/bootstrap.sh
#
set -euo pipefail

REPO="$HOME/Coding/claude-skills"
SKILLS="$HOME/.claude/skills"
COMMANDS="$HOME/.claude/commands"
ICLOUD="$HOME/Library/Mobile Documents/com~apple~CloudDocs"

mkdir -p "$SKILLS" "$COMMANDS"

link() { # link <target> <linkpath>
  local target="$1" link="$2"
  if [ -L "$link" ]; then rm "$link"; fi
  if [ -e "$link" ] && [ ! -L "$link" ]; then
    echo "SKIP $link — real file/dir exists, not overwriting"; return
  fi
  ln -s "$target" "$link"
  echo "linked $link -> $target"
}

echo "== git-synced skills =="
link "$REPO/wiki-compile"    "$SKILLS/wiki-compile"
link "$REPO/wiki-query"      "$SKILLS/wiki-query"
link "$REPO/wiki-brief"      "$SKILLS/wiki-brief"
link "$REPO/wiki-health"     "$SKILLS/wiki-health"
link "$REPO/mol-report"      "$SKILLS/mol-report"
link "$REPO/devils-advocate" "$SKILLS/devils-advocate"
link "$REPO/reflect"         "$SKILLS/reflect"
link "$REPO/transcribe"      "$SKILLS/transcribe"
link "$REPO/verify-admotiv"  "$SKILLS/verify-admotiv"
link "$REPO/foreman"         "$SKILLS/foreman"
link "$REPO/audyt-wygladu"   "$SKILLS/audyt-wygladu"

echo "== git-synced agents =="
link "$REPO/agents"          "$HOME/.claude/agents"

echo "== git-synced commands =="
link "$REPO/commands/debrief.md" "$COMMANDS/debrief.md"

echo "== iCloud-synced learning workspace =="
# Content lives in iCloud; just relink home -> iCloud. iCloud must have synced first.
if [ -d "$ICLOUD/learning" ]; then
  link "$ICLOUD/learning" "$HOME/learning"
else
  echo "WAIT iCloud/learning not synced yet — re-run once iCloud catches up"
fi

echo "== Matt Pocock's teach skill (re-fetch latest, NOT vendored) =="
TEACH="$SKILLS/teach"
# Matt graduated teach from in-progress/ -> productivity/ on 2026-06-10. If this 404s again, he moved it.
BASE="https://raw.githubusercontent.com/mattpocock/skills/main/skills/productivity/teach"
mkdir -p "$TEACH"
for f in SKILL.md MISSION-FORMAT.md RESOURCES-FORMAT.md LEARNING-RECORD-FORMAT.md GLOSSARY-FORMAT.md; do
  curl -fsS "$BASE/$f" -o "$TEACH/$f" && echo "fetched teach/$f"
done

echo "== done =="
