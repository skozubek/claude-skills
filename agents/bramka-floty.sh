#!/bin/bash
# PreToolUse (Bash) dla foreman-wykonawca: wypchnięcie, wdrożenie, procesy
# i zagnieżdżone agenty należą do brygadzisty. Łapie pomyłki agenta, nie
# każdą drogę do zdalnej zmiany: sekrety produkcji nie trafiają do worktree.
# Wejście nieczytelne = odmowa. Kontekst: ~/.claude/skills/foreman/.
deny() { printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"; exit 0; }
input=$(cat)
cmd=$(printf '%s' "$input" | jq -er '.tool_input.command' 2>/dev/null) || deny "Strażnik floty nie odczytał komendy (brak jq albo zmiana formatu wejścia hooka). Zgłoś to brygadziście w raporcie."

segs=$(printf '%s\n' "$cmd" | sed -E 's/&&|\|\||;|\||\$\(|`/\n/g')
while IFS= read -r seg; do
  seg=$(printf '%s' "$seg" | sed -E 's/^[ (]*((command|exec|sudo|env|eval|time) +)*//; s/^([A-Za-z_][A-Za-z0-9_]*=[^ ]* +)*//; s/^(bash|sh|zsh) +-c +["'"'"']?//; s#^/[^ ]*/##')
  if printf '%s' "$seg" | grep -qE '^git( +-[Cc] +[^ ]+)* +push\b|^gh( +--?[a-z-]+( +[^ -][^ ]*)?)* +pr +(merge|create|ready|close)\b'; then
    deny "Push i PR robi brygadzista po odbiorze. Skończ na commicie i opisz stan w raporcie."
  fi
  if printf '%s' "$seg" | grep -qE '^(npx( +-y| +--yes)? +)?(supabase +(functions +deploy|db +push|secrets +set)|vercel +(deploy|--prod)|netlify +deploy|npm +publish)'; then
    deny "Wdrożenie i zmiany na zdalnej bazie należą do brygadzisty. Weryfikuj lokalnie i opisz w raporcie, co trzeba wdrożyć."
  fi
  if printf '%s' "$seg" | grep -qE '^(kill|pkill|killall)\b'; then
    deny "Procesów nie zabijasz: mogą należeć do brygadzisty albo innego agenta. Długie komendy puszczaj z timeoutem; blokadę portu albo pliku opisz w raporcie."
  fi
  if printf '%s' "$seg" | grep -qE '^(claude|codex)\b'; then
    deny "Agenty zagnieżdżone spawnuje tylko brygadzista. Zrób robotę sam albo zgłoś w raporcie, czego brakuje."
  fi
done <<< "$segs"
exit 0
