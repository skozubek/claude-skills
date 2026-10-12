# Wspólne zmienne skryptów verify-admotiv. Ładowane przez `source`, nie uruchamiane.
# Działa z katalogu repo AdMotiv albo jego worktree.

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAPA_DIR="$HOME/Coding/MOL/Panel/meta/mapa"
DOWODY_DIR="$HOME/Coding/MOL/Panel/dowody"
B="$HOME/.claude/skills/gstack/browse/dist/browse"

REPO="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "BŁĄD: nie jesteś w repo AdMotiv ani w jego worktree" >&2; exit 2; }
[ -f "$REPO/src/integrations/supabase/client.ts" ] || { echo "BŁĄD: $REPO to nie repo AdMotiv" >&2; exit 2; }

# Port z ścieżki checkoutu: dwa worktree nigdy nie dzielą serwera, ten sam worktree zawsze dostaje ten sam port.
PORT=$(( 8100 + $(printf '%s' "$REPO" | cksum | cut -d' ' -f1) % 100 ))
URL="http://localhost:$PORT"
# Stan przebiegu poza repo, żeby git status checkoutu został czysty.
STAN_DIR="$HOME/Coding/MOL/Panel/.verify/$PORT"

env_val() { grep "^$1=" "$REPO/.env" | head -1 | cut -d= -f2- | tr -d '"'; }
