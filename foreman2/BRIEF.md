# Brief, odbiór, agenci

## Brief wykonawcy

```
Zadanie <id> <nazwa> z planu <ścieżka>, sekcja <nagłówek>.
Zacznij od `git merge --ff-only <SHA ze spawnu>`.
Twoje pliki: <lista>. Pozostałe pliki należą do innych zadań.
Czytelnicy Twoich pól poza Twoimi plikami: <lista z grafu>.
Warunki:
- <warunek> — bo <powód>
- wzorzec: <plik, funkcja>
- pułapka: <co kusi i czemu nie działa>
Weryfikacja: <dokładne komendy, uruchamialne z worktree>
```

Brief wskazuje zakresy do przeczytania (plik i funkcja), nie całe pliki. Każdy
warunek niesie powód: warunek bez powodu wykonawca „poprawia”. Dowód ekranu: jeden
skrypt `$B js` z `/browse` albo komenda skilla z profilu. Spawn:
`Agent(subagent_type="foreman2-wykonawca", model=<wariant>, run_in_background=true)`;
opus-high dostaje `effort: high` w wywołaniu. Przed spawnem `git rev-parse HEAD` na
integracji = SHA ze spawnu; po spawnie `$F2 task set <id> --status running --agent
<id> --spawn-sha <sha> --worktree <dir>` i `own add worktree <dir>`.

## Pułapki środowiska (do briefu, gdy dotyczą zadania)

- Push z worktree odpala `pre-push` z `GIT_DIR` worktree: push idzie z głównego
  klonu po scaleniu.
- Klon dzielony z innymi sesjami: bez `stash`, `reset`, `checkout --`, `restore`
  (zabierają cudze niezacommitowane edycje); w głównym klonie tylko checkout,
  merge, push i poprawki bramy.
- Agent widzi cudze zmiany w głównym klonie i uznaje je za incydent: pracuje
  w worktree, procesów nie zabija (strażnik komend `bramka-floty.sh` odmawia).
- Zależności w worktree z lockfile'a (`profile.install`); dev serwer na dowiązanym
  `node_modules` może wymagać trybu bez Turbopacka.
- Skanery per commit (gitleaks, strażnik dokumentów) widzą commity pośrednie: dane
  testowe słownikowe, dokument w tym samym commicie co kod. Trafienie na integracji
  po potwierdzeniu, że to nie sekret: gałąź z jednym commitem (`merge --squash`),
  bramki na nowym SHA, stary PR zamknięty; nie wyjątek w skanerze, nie force push.
- Merge gałęzi domyślnej po squashu PR-a: plik dopisywany na końcu (dziennik
  decyzji) traci linie; po merge'u `git diff origin/<domyślna> -- <dziennik>` ma
  same dodane linie.
- Znak NUL w literale przechodzi testy i psuje `grep`: `tr -cd '\000' < plik | wc -c`,
  przepis sprawdzony na wzorcu, który musi trafić.
- Pomiar i `/code-review` w jednym klonie: review podmienia pliki; rozdziel katalog
  albo czas.
- Skrypt importujący kod ze ścieżki worktree umiera razem z worktree: import
  z głównego klonu albo z kopii `git show <ref>:ścieżka`.
- Test klawiatury zaczyna się od nasłuchu `keydown` na elemencie: pusta lista zdarzeń
  znaczy, że klawisz nie dotarł, nie że komponent jest zepsuty.
- PR zmergowany przez równoległą sesję z tego konta: wdrożenie weryfikujesz od zera;
  PR zsynchronizowany z czymś jeszcze trzymasz jako draft.
- Kopia lokalna bez kont użytkowników: klucz obcy przechodzi na kopii, pada na
  produkcji; przed testem zapytanie o anomalie (sieroty, puste, duplikaty) w danych,
  które czyta zmiana.
- Pułapki produktu (migracje, crony, konta, strażniki dokumentów) mieszkają
  w AGENTS.md repo i w `profile.notes`: wklejasz te, które dotyczą zadania.

## Protokół odbioru (brygadzista, na integracji)

```
git merge-base --is-ancestor <SHA ze spawnu> <gałąź agenta>     # przodek
git diff --name-only <SHA ze spawnu>...<gałąź agenta>             # tylko pliki zadania
<komenda weryfikacji zadania, w worktree agenta albo odbioru>     # wynik liczbą
```

Każdy wynik → `$F2 evidence add --for <T> --cmd <komenda> --sha <HEAD agenta>
--result <wynik> --verdict pass|fail`. Ten sam dowód na tym samym SHA nie jest
powtarzany. Przekroczony limit tur = odbiór nieprzyjęty. Przyjęte: `git merge
--no-ff <gałąź>` na integracji, `task set --status merged`. Konflikt: SendMessage
„dociągnij <integracja>, rozwiąż, raport”; konflikt to błąd podziału grafu, który
zapisujesz w planie.

## Poprawka (SendMessage do tego samego agenta)

```
Odbiór nieprzyjęty na <SHA>: <komenda> → <wynik>, oczekiwane <wynik>.
Popraw w swoich plikach, powtórz weryfikację, raport w tym samym kształcie.
```

`task bump <id> --field rounds`. Nowy wykonawca (`resumes` = 3, kontekst > 200k,
drabina) dostaje SHA, poprzedni raport i dowód nieprzyjęcia; `task bump --field resumes`.

## Agenci tylko do odczytu

Triage, inwentarz, odczyt logów: `general-purpose` (sonnet) bez worktree, pisze
tylko raport do wskazanego pliku. Brief wymienia zakazy: bez edycji repo, bez
`kill`, bez forków i spawnu podagentów, dane po drucie do pliku, do raportu liczby
i wycinki.

## Weryfikator na żywo

`foreman2-weryfikator` dostaje: SHA i katalog odbioru, kryteria (odczyt →
oczekiwane), narzędzie (skill z `profile.live_verify_skill` albo `/browse <adres>`),
konto roli, listę zapisów zakazanych. Jeden weryfikator na PR dotykający ekranu;
raport → `evidence add --for <C>` per kryterium.
