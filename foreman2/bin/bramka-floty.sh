#!/bin/bash
# Strażnik floty foremana 2.0: hook PreToolUse (Bash) wykonawcy i weryfikatora; po
# `foreman2 cancel` także brygadzisty (przez `foreman2 straz`).
# Odmawia ruchów, których skutek jest zapłacony z chwilą wykonania: push, PR i zapis
# w GitHubie, deploy i publikacja, zapis do zdalnej bazy albo obcego API, zabijanie
# procesów, zagnieżdżone claude/codex. Komenda nieczytelna = odmowa (zamknięty na
# własnym błędzie). Chroni przed pomyłką agenta, nie przed wrogim poleceniem: obejść
# spreparowanych nie goni, to robota piaskownicy.
deny() { printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"; exit 0; }
input=$(cat)
cmd=$(printf '%s' "$input" | jq -er '.tool_input.command' 2>/dev/null) || deny "Strażnik floty nie odczytał komendy; przepisz ją prościej (bez zagnieżdżeń)."
segs=$(printf '%s\n' "$cmd" | sed -E 's/&&|\|\||;|\||\$\(|`/\n/g')
LOKALNY='(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|host\.docker\.internal|10\.[0-9]+\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)'
ZDALNY_HOST='(-h|--host)[= ]+[^ ]*\.[a-z]{2,}|@[^ /:]+\.[a-z]{2,}|\.(supabase\.(co|com)|amazonaws\.com|neon\.tech|render\.com|railway\.app)'
ZAPIS_HTTP=' (-X|--request)[ =]+["'"'"']?(POST|PUT|PATCH|DELETE)\b| -d | --data(-[a-z]+)?[ =]| -F | --form[ =]| --json[ =]| -T | --upload-file[ =]'
while IFS= read -r seg; do
  seg=$(printf '%s' "$seg" | sed -E 's/^[ (]*//; s/^([A-Za-z_][A-Za-z0-9_]*=[^ ]* +)*//; s/^((command|exec|sudo|env|eval|time|nohup|caffeinate( +-[a-z]+)*) +)*//; s/^([A-Za-z_][A-Za-z0-9_]*=[^ ]* +)*//; s/^(bash|sh|zsh) +-c +["'"'"']?//; s#^/[^ ]*/##')
  if printf '%s' "$seg" | grep -qE '^git( +(-[A-Za-z]( +[^ ]+)?|--[a-z-]+(=[^ ]*)?))* +push\b'; then
    deny "Push robi brygadzista z integracji (etap 7). Twoja robota zostaje w worktree; raport podaje SHA."
  fi
  if printf '%s' "$seg" | grep -qE '^gh( +--?[a-zA-Z-]+( +[^ -][^ ]*)?)* +(pr +(merge|create|ready|close|review|edit)|api( +.*)? +(-X|--method|-f|-F|--input|--field|--raw-field)|workflow +run|run +(rerun|cancel)|release +(create|delete|edit)|repo +(delete|edit|create))\b'; then
    deny "PR, merge, zapis przez API GitHuba i uruchamianie workflow należą do brygadzisty z mandatem."
  fi
  if printf '%s' "$seg" | grep -qE '^(npx( +-y| +--yes)? +|bunx +|pnpm +(dlx|exec) +)?(supabase +(functions +deploy|db +(push|reset)|secrets +set|link|projects +create)|vercel *$|vercel( +[^ ]+)* +(--prod|deploy)|netlify +deploy|wrangler +(deploy|publish)|fly(ctl)? +deploy|firebase +deploy|railway +up|gcloud +[a-z ]*deploy|aws +(s3 +(sync|cp|rm)|lambda +update|cloudformation +deploy))\b'; then
    deny "Deploy i zapis w cudzym systemie tylko z mandatem w run.json, przez brygadzistę."
  fi
  if printf '%s' "$seg" | grep -qE '^(npm|pnpm|yarn|bun)( +run)? +(publish|deploy|release)\b|^make +(deploy|publish|release)\b'; then
    deny "Skrypt publikacji albo deployu uruchamia brygadzista z mandatem."
  fi
  if printf '%s' "$seg" | grep -qE '^(kill|pkill|killall)\b|^launchctl +(bootout|unload|kill)\b'; then
    deny "Bez zabijania procesów: inne sesje dzielą maszynę. Własny proces zatrzymujesz narzędziem, którym go uruchomiłeś."
  fi
  if printf '%s' "$seg" | grep -qE '^(claude|codex)\b'; then
    deny "Agent nie uruchamia claude ani codex: zagnieżdżona sesja ucieka budżetowi i strażnikom."
  fi
  if printf '%s' "$seg" | grep -qE '^(psql|pgcli|pg_restore|pg_dump|mysql|mongosh)\b' && printf '%s' "$seg" | grep -qE "$ZDALNY_HOST" && ! printf '%s' "$seg" | grep -qE "$LOKALNY"; then
    deny "Zdalna baza z poziomu agenta: odczyt robi brygadzista, zapis dostaje decyzję approval."
  fi
  if printf '%s' "$seg" | grep -qE '^(curl|wget|http|https|xh)\b' && printf '%s' "$seg" | grep -qE "$ZAPIS_HTTP" && printf '%s' "$seg" | grep -qE 'https?://' && ! printf '%s' "$seg" | grep -qE "$LOKALNY"; then
    deny "Zapis do obcego API z poziomu agenta (wysyłka, zmiana danych) wymaga decyzji approval; adresy lokalne wolno."
  fi
done <<< "$segs"
exit 0
