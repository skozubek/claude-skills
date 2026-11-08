# Wspólne zmienne skryptów verify-admotiv. Ładowane przez `source`, nie uruchamiane.
# Działa z katalogu repo AdMotiv albo jego worktree.

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Zmienne środowiska nadpisują ścieżki (tests/ podstawia katalog mapy, dowodów i atrapę przeglądarki).
MAPA_DIR="${MAPA_DIR:-$HOME/Coding/MOL/Panel/meta/mapa}"
DOWODY_DIR="${DOWODY_DIR:-$HOME/Coding/MOL/Panel/dowody}"
B="${B:-$HOME/.claude/skills/gstack/browse/dist/browse}"

REPO="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "BŁĄD: nie jesteś w repo AdMotiv ani w jego worktree" >&2; exit 2; }
[ -f "$REPO/src/integrations/supabase/client.ts" ] || { echo "BŁĄD: $REPO to nie repo AdMotiv" >&2; exit 2; }

# Port z ścieżki checkoutu: ten sam worktree zawsze dostaje ten sam port. Zakres to 100 portów, więc
# kolizja dwóch checkoutów jest możliwa: wtedy start odmawia, a doctor pokazuje, czyj proces trzyma port.
HASZ=$(printf '%s' "$REPO" | cksum | cut -d' ' -f1)
PORT=$(( 8100 + HASZ % 100 ))
URL="http://localhost:$PORT"
# Opublikowany front (Lovable): smoke po wdrożeniu (`bin/sesja --prod`).
PROD_URL="https://admotiv.marketingonline.pl"
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

# Rejestr przejść mapy (append-only TSV: czas UTC, obszar, krok, HEAD, baza na origin/main, uwaga).
# Pisze bin/przeszlo, czyta bin/doctor. Jeden checkout meta na maszynie, więc dopisanie krótkiego wiersza
# przez `>>` jest atomowe; dwa równoległe przebiegi nie potrzebują blokady.
REJESTR="$MAPA_DIR/przejscia.log"
TSV="$MAPA_DIR/przejscia.tsv"
# Autor commitów uznawany za własny (doctor grupuje własne commity w jedną linię): e-mail z konfiguracji repo.
WLASNY_EMAIL="$(git -C "$REPO" config user.email 2>/dev/null || true)"
# obszar dla prefiksu ID kroku (kolumna 2 przejscia.tsv); pusty, gdy prefiks nieznany
obszar_prefiksu() { awk -F'\t' -v p="$1" '!/^#/ && $2 == p { print $1; exit }' "$TSV"; }
# kolumny wiersza obszaru: obszar_wiersz <obszar> <nr kolumny>
obszar_wiersz() { awk -F'\t' -v o="$1" -v k="$2" '!/^#/ && $1 == o { print $k; exit }' "$TSV"; }
