# Wspólne zmienne skryptów verify-admotiv. Ładowane przez `source`, nie uruchamiane.
# Działa z katalogu repo AdMotiv albo jego worktree.

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAPA_DIR="$HOME/Coding/MOL/Panel/meta/mapa"
DOWODY_DIR="$HOME/Coding/MOL/Panel/dowody"
B="$HOME/.claude/skills/gstack/browse/dist/browse"

REPO="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "BŁĄD: nie jesteś w repo AdMotiv ani w jego worktree" >&2; exit 2; }
[ -f "$REPO/src/integrations/supabase/client.ts" ] || { echo "BŁĄD: $REPO to nie repo AdMotiv" >&2; exit 2; }

# Port z ścieżki checkoutu: ten sam worktree zawsze dostaje ten sam port. Zakres to 100 portów, więc
# kolizja dwóch checkoutów jest możliwa: wtedy start odmawia, a doctor pokazuje, czyj proces trzyma port.
HASZ=$(printf '%s' "$REPO" | cksum | cut -d' ' -f1)
PORT=$(( 8100 + HASZ % 100 ))
URL="http://localhost:$PORT"
# Stan przebiegu poza repo (git status checkoutu zostaje czysty), kluczowany checkoutem, nie portem.
STAN_DIR="$HOME/Coding/MOL/Panel/.verify/$HASZ"

# Katalog z podpiętym projektem Supabase: checkout albo klon główny (worktree nie ma supabase/.temp).
SUPA_DIR="$REPO"
[ -f "$REPO/supabase/.temp/project-ref" ] || SUPA_DIR="$(cd "$(git rev-parse --git-common-dir)/.." && pwd)"

env_val() { grep "^$1=" "$REPO/.env" | head -1 | cut -d= -f2- | tr -d '"'; }

# pid procesu słuchającego na porcie tego checkoutu, pusty gdy nikt
pid_portu() { lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null | head -1; }
# katalog roboczy procesu
cwd_procesu() { lsof -a -p "$1" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p'; }
# 0, gdy na porcie słucha proces uruchomiony z tego checkoutu
serwer_nasz() { local p; p=$(pid_portu); [ -n "$p" ] && [ "$(cwd_procesu "$p")" = "$REPO" ]; }
