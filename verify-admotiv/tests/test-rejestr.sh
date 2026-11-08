#!/usr/bin/env bash
# Testy rejestru przejść (bin/przeszlo, bin/doctor sekcja 4) na tymczasowym repo w kształcie AdMotiv,
# z lokalnym origin, tymczasową mapą i atrapą przeglądarki. Bez sieci, bez dotykania prawdziwej mapy.
# Uruchomienie: bash verify-admotiv/tests/test-rejestr.sh
set -uo pipefail
BIN="$(cd "$(dirname "$0")/../bin" && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "${T:?}"' EXIT
PAD=0; ILE=0
sprawdz() { ILE=$((ILE+1)); if grep -q -E -- "$3" "$2"; then echo "ok   $1"; else echo "PADŁ $1: brak /$3/ w:"; sed 's/^/     | /' "$2"; PAD=$((PAD+1)); fi; }
sprawdz_brak() { ILE=$((ILE+1)); if grep -q -E -- "$3" "$2"; then echo "PADŁ $1: niechciane /$3/ w:"; sed 's/^/     | /' "$2"; PAD=$((PAD+1)); else echo "ok   $1"; fi; }

# repo w kształcie AdMotiv (plik klienta Supabase) + lokalne origin
git init -q --bare "$T/origin.git"
mkdir -p "$T/repo" && cd "$T/repo" && git init -q && git checkout -q -b main 2>/dev/null
git config user.name "Serge"; git config user.email "serge@przyklad.test"
mkdir -p src/integrations/supabase src/pages src/lib
echo "export const supabase = 1;" > src/integrations/supabase/client.ts
printf "import { x } from '@/lib/wspolny';\nexport default x;\n" > src/pages/A.tsx
printf "export const y = 1;\n" > src/pages/B.tsx
echo "export const x = 1;" > src/lib/wspolny.ts
git add -A && git commit -q -m "start" && git remote add origin "$T/origin.git" && git push -q -u origin main 2>/dev/null
REPO="$(git rev-parse --show-toplevel)"
HASZ=$(printf '%s' "$REPO" | cksum | cut -d' ' -f1); PORT=$(( 8100 + HASZ % 100 ))

export MAPA_DIR="$T/mapa" DOWODY_DIR="$T/dowody"; mkdir -p "$MAPA_DIR" "$DOWODY_DIR"
printf '# obszar\tprefiks\tścieżki\naaa\tAAA\tsrc/pages/A.tsx\nbbb\tBBB\tsrc/pages/B.tsx\n' > "$MAPA_DIR/przejscia.tsv"
printf '# Obszar A\n\n## Podfunkcje\n\n- AAA-01 jedno\n- AAA-02 drugie\n- AAA-03 trzecie\n' > "$MAPA_DIR/aaa.md"
printf '# Obszar B\n\n## Podfunkcje\n\n- BBB-01 jedno\n' > "$MAPA_DIR/bbb.md"
cat > "$T/atrapa-b" <<EOF2
#!/usr/bin/env bash
case "\$1" in url) echo "http://localhost:$PORT/sprzedaz";; eval) echo "/rest/v1/sales_contacts 120ms | /rest/v1/x 40ms";; *) :;; esac
EOF2
chmod +x "$T/atrapa-b"; export B="$T/atrapa-b"
DOW="$DOWODY_DIR/2026-11-08-test"

echo "# 1. przejście kroku: wiersz rejestru (HEAD = baza) i pomiar w czasy.tsv"
"$BIN/przeszlo" "$DOW" AAA-01 > "$T/o1" 2>&1; echo "exit=$?" >> "$T/o1"
sprawdz "przeszlo kończy się 0" "$T/o1" '^exit=0$'
HEAD_SHA=$(git rev-parse HEAD)
sprawdz "rejestr: wiersz aaa/AAA-01 z HEAD i bazą" "$MAPA_DIR/przejscia.log" "	aaa	AAA-01	$HEAD_SHA	$HEAD_SHA	-$"
sprawdz "czasy.tsv: pomiar kroku" "$DOW/czasy.tsv" '^AAA-01	.*sales_contacts 120ms'

echo "# 2. nieznany prefiks: odmowa bez wiersza"
"$BIN/przeszlo" "$DOW" ZZZ-01 > "$T/o2" 2>&1; echo "exit=$?" >> "$T/o2"
sprawdz "nieznany prefiks: exit 2 i wskazanie --obszar" "$T/o2" 'prefiks „ZZZ”.*--obszar'
sprawdz "nieznany prefiks: exit 2" "$T/o2" '^exit=2$'
sprawdz_brak "nieznany prefiks: nic nie dopisane" "$MAPA_DIR/przejscia.log" 'ZZZ-01'

echo "# 3. karta na cudzym serwerze: odmowa bez wiersza"
printf '#!/usr/bin/env bash\ncase "$1" in url) echo "http://localhost:8199/x";; esac\n' > "$T/atrapa-cudza"; chmod +x "$T/atrapa-cudza"
B="$T/atrapa-cudza" "$BIN/przeszlo" "$DOW" AAA-02 > "$T/o3" 2>&1; echo "exit=$?" >> "$T/o3"
sprawdz "cudza karta: powód" "$T/o3" 'karta przeglądarki na „http://localhost:8199/x”'
sprawdz "cudza karta: exit 2" "$T/o3" '^exit=2$'
sprawdz_brak "cudza karta: nic nie dopisane" "$MAPA_DIR/przejscia.log" 'AAA-02'

echo "# 4. pełne przejście obszaru; krok bez pomiaru na brudnym drzewie"
"$BIN/przeszlo" --obszar aaa > "$T/o4" 2>&1
sprawdz "pełne przejście: krok „-”" "$MAPA_DIR/przejscia.log" "	aaa	-	$HEAD_SHA	$HEAD_SHA	-$"
sleep 1
echo "// brud" >> src/pages/B.tsx
B=/usr/bin/false "$BIN/przeszlo" --bez-czasu AAA-03 > "$T/o5" 2>&1; echo "exit=$?" >> "$T/o5"
sprawdz "--bez-czasu: bez przeglądarki, exit 0" "$T/o5" '^exit=0$'
sprawdz "brudne drzewo w uwadze" "$MAPA_DIR/przejscia.log" "	aaa	AAA-03	$HEAD_SHA	$HEAD_SHA	drzewo brudne$"
git checkout -q -- src/pages/B.tsx
"$BIN/przeszlo" --obszar nic > "$T/o6" 2>&1; echo "exit=$?" >> "$T/o6"
sprawdz "nieznany obszar: odmowa" "$T/o6" 'obszar „nic” nie ma wiersza'

echo "# 5. cudzy commit w module importowanym spoza wiersza, własny commit w wierszu"
git clone -q "$T/origin.git" "$T/cudzy" && cd "$T/cudzy" && git config user.name "Cudzy" && git config user.email "cudzy@przyklad.test"
echo "export const x = 2;" > src/lib/wspolny.ts && echo "export const y = 2;" > src/pages/B.tsx && git commit -q -am "feat: zmiana wspólna i B" && git push -q origin main 2>/dev/null
cd "$T/repo" && echo "// własna" >> src/pages/A.tsx && git commit -q -am "fix(A): własna poprawka" && git pull -q --rebase origin main 2>/dev/null && git push -q origin main 2>/dev/null && git fetch -q origin
"$BIN/doctor" aaa > "$T/d1" 2>&1
sprawdz "doctor: własny commit jedną liczbą, bez cudzych w wierszu" "$T/d1" 'aaa: bez cudzych zmian od pełnego przejścia [0-9-]+ \([0-9a-f]{8}\), własnych commitów: 1'
sprawdz "doctor: cudzy commit w module importowanym spoza wiersza" "$T/d1" 'aaa: cudze commity w modułach, które ekran importuje spoza wiersza mapy \(1\)'
sprawdz "doctor: autor, temat i plik modułu" "$T/d1" 'Cudzy: feat: zmiana wspólna i B \[src/lib/wspolny.ts\]'
sprawdz "doctor: kroki przeszłe po pełnym przejściu" "$T/d1" 'aaa: kroki przeszłe po pełnym przejściu: AAA-03'
"$BIN/doctor" bbb > "$T/d2" 2>&1
sprawdz "doctor: obszar bez przejść" "$T/d2" 'bbb: nigdy nie przeszedł na żywo'
sprawdz "doctor: kroki bez żadnego przejścia" "$T/d2" 'bbb: bez pełnego przejścia; kroków bez żadnego przejścia 1 z 1: BBB-01'
sprawdz "doctor: HEAD równy origin/main" "$T/d2" 'brak zmian względem origin/main'

echo "# 6. pomiar bez zaliczenia: doctor dopomina się o przeszlo"
"$BIN/czasy" "$DOW" AAA-02 > /dev/null 2>&1
"$BIN/doctor" aaa > "$T/d3" 2>&1
sprawdz "doctor: krok zmierzony bez wpisu w rejestrze" "$T/d3" 'czasy.tsv: kroki zmierzone bez wpisu w rejestrze: AAA-02 → przeszły\? bin/przeszlo'
sprawdz_brak "doctor: krok zaliczony nie jest dopominany" "$T/d3" 'bez wpisu w rejestrze: .*AAA-01'

echo "# 7. zmiana w drzewie roboczym wskazuje obszar; nieznany obszar to błąd"
echo "// robocza" >> src/pages/B.tsx
"$BIN/doctor" > "$T/d4" 2>&1
sprawdz "doctor: zmiana dotyka obszaru bbb" "$T/d4" 'zmiana dotyka obszarów: bbb \(przejdź tylko je\)'
sprawdz "doctor: cudzy commit w wierszu bbb nie ma bazy, więc raport o braku przejść" "$T/d4" 'bbb: nigdy nie przeszedł na żywo'
git checkout -q -- src/pages/B.tsx
"$BIN/doctor" nic > "$T/d5" 2>&1
sprawdz "doctor: nieznany obszar" "$T/d5" 'obszar „nic” nie ma wiersza'

echo; echo "testów $ILE, padło $PAD"; [ $PAD -eq 0 ]
