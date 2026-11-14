# Brief, odbiór, agenci

## Brief wykonawcy

```
Zadanie <id> <nazwa>; plan <ścieżka> (Granice, kryteria), kontrakt <ścieżka kontrakt.md>, sekcja <nagłówek>.
Zacznij od `git merge --ff-only <SHA ze spawnu>`.
Twoje pliki: <lista>. Pozostałe pliki należą do innych zadań.
Czytelnicy Twoich pól poza Twoimi plikami: <lista z grafu>.
Warunki:
- <warunek> — bo <powód>
- wzorzec: <plik, funkcja>
- pułapka: <co kusi i czemu nie działa>
Weryfikacja: <dokładne komendy, uruchamialne z worktree>
```

Komenda weryfikacji zadania (`task add --verify` i linia „Weryfikacja” briefu) to kroki CI,
które odpalą się na plikach zadania, z tymi samymi parametrami: `profile.verify` i każdy
workflow z pasującym filtrem ścieżek (odczyt pliku workflowu i skryptów, które woła), bez
kroków publikacji i zapisu na produkcji. Podzbiór przepuszcza czerwień do CI na PR-ze,
gdzie runda kosztuje kilka minut zegara.

Brief wskazuje zakresy do przeczytania (plik i funkcja), nie całe pliki. Każdy
warunek niesie powód: warunek bez powodu wykonawca „poprawia”. Dowód ekranu: jeden
skrypt `$B js` z `/browse` albo komenda skilla z profilu. Spawn:
`Agent(subagent_type="foreman-wykonawca", model=<sonnet|opus>, run_in_background=true)`;
wariant opus-high to `model=opus` z `effort: high` w wywołaniu. SHA ze spawnu
to HEAD integracji (`git -C <katalog integracji> rev-parse HEAD`), także gdy integracja
stoi w osobnym worktree, a sesja w głównym klonie: worktree agentów wyrastają z HEAD
katalogu sesji i wykonawca dociąga je `merge --ff-only` do SHA ze spawnu; rezerwacja
`$FM task set <ids> --status running --spawn-sha <sha>`. Po spawnie `$FM task set <id>
--agent <id> --worktree <dir>` (rejestruje worktree i gałąź do sprzątania).

## Pułapki środowiska (do briefu, gdy dotyczą zadania)

- Push z worktree odpala `pre-push` z `GIT_DIR` worktree: push idzie z głównego
  klonu po scaleniu.
- Klon dzielony z innymi sesjami: bez `stash`, `reset`, `checkout --`, `restore`
  (zabierają cudze niezacommitowane edycje); w głównym klonie tylko checkout,
  merge, push i poprawki bramy. <!-- LC-095 -->
- Agent widzi cudze zmiany w głównym klonie i uznaje je za incydent: pracuje
  w worktree, procesów nie zabija (strażnik komend `bramka-floty.sh` odmawia). <!-- LC-062 -->
- Zależności w worktree z lockfile'a (`profile.install`); dev serwer na dowiązanym
  `node_modules` może wymagać trybu bez Turbopacka. <!-- LC-076 -->
- Skanery per commit (gitleaks, strażnik dokumentów) widzą commity pośrednie: dane
  testowe słownikowe, dokument w tym samym commicie co kod. Trafienie na integracji
  po potwierdzeniu, że to nie sekret: gałąź z jednym commitem (`merge --squash`),
  bramki na nowym SHA, stary PR zamknięty; nie wyjątek w skanerze, nie force push.
- Merge gałęzi domyślnej po squashu PR-a: plik dopisywany na końcu (dziennik
  decyzji) traci linie; po merge'u `git diff origin/<domyślna> -- <dziennik>` ma
  same dodane linie.
- Znak NUL w literale przechodzi testy i psuje `grep`: `tr -cd '\000' < plik | wc -c`,
  przepis sprawdzony na wzorcu, który musi trafić. <!-- LC-016 LC-039 -->
- Pomiar i `/code-review` w jednym klonie: review podmienia pliki; rozdziel katalog
  albo czas. <!-- LC-100 -->
- Skrypt importujący kod ze ścieżki worktree umiera razem z worktree: import
  z głównego klonu albo z kopii `git show <ref>:ścieżka`. <!-- LC-108 -->
- Test klawiatury zaczyna się od nasłuchu `keydown` na elemencie: pusta lista zdarzeń
  znaczy, że klawisz nie dotarł, nie że komponent jest zepsuty. <!-- LC-103 -->
- PR zmergowany przez równoległą sesję z tego konta: wdrożenie weryfikujesz od zera;
  PR zsynchronizowany z czymś jeszcze trzymasz jako draft. <!-- LC-105 -->
- Kopia lokalna bez kont użytkowników: klucz obcy przechodzi na kopii, pada na
  produkcji; przed testem zapytanie o anomalie (sieroty, puste, duplikaty) w danych,
  które czyta zmiana.
- Pułapki produktu (migracje, crony, konta, strażniki dokumentów) mieszkają
  w AGENTS.md repo i w `profile.notes`: wklejasz te, które dotyczą zadania.

## Protokół odbioru (brygadzista, na integracji)

`$FM accept <T> --worktree <dir> --merge` przypina HEAD agenta, wymaga czystego drzewa,
sprawdza przodka i pełny diff od SHA spawnu (obie strony rename) wobec plików zadania,
uruchamia komendę weryfikacji w worktree z timeoutem i zapisuje dowód `--for <T>` na
przypiętym SHA. `rounds` podbija tylko fail komendy (exit, timeout); zakres, przodek
i drzewo zmienione w trakcie to porażka księgowa, którą naprawiasz grafem albo
SendMessage, bez rundy. Plik testu obok pliku zadania (`X.test.*`, `X.spec.*`,
`__tests__/X.test.*`, `test_X.py` przy `X.py`) przechodzi, gdy nie ma go inne zadanie,
i po `pass` trafia do plików zadania; plik wspólny dalej ma jednego właściciela.
Raport agenta podaje SHA weryfikacji: `--reported-sha <SHA>` (przelot z `create --gate`),
gdy SHA = HEAD worktree przy czystym drzewie, sprawdza zakres i przodka bez drugiego
przebiegu komendy; dowód `pass` stoi na słowie agenta, a pełne testy idą bramką repo
na integracji. Po `pass` scala przypięty SHA (`--no-ff`)
w katalogu sesji, który stoi na gałęzi integracji, ustawia `merged` i wypisuje front:
w tym samym wywołaniu Bash rezerwujesz następne zadanie (`&& $FM task set <T2> --status
running --spawn-sha $(git rev-parse HEAD)`). Przekroczony limit tur = odbiór nieprzyjęty.
Konflikt: scalenie cofnięte, SendMessage „dociągnij <integracja>, rozwiąż, raport”;
konflikt to błąd podziału grafu, który zapisujesz w `kontrakt.md`.

## Poprawka (SendMessage do tego samego agenta)

```
Odbiór nieprzyjęty na <SHA>: <komenda> → <wynik>, oczekiwane <wynik>.
Popraw w swoich plikach, powtórz weryfikację, raport w tym samym kształcie.
```

`rounds` podbija `accept` przy failu komendy. Nowy wykonawca (`resumes` = 3, kontekst > 200k,
drabina) dostaje SHA, poprzedni raport i dowód nieprzyjęcia; `task bump --field resumes`.

## Agenci tylko do odczytu

Triage, inwentarz, odczyt logów: `general-purpose` (sonnet) bez worktree, pisze
tylko raport do wskazanego pliku. Brief wymienia zakazy: bez edycji repo, bez
`kill`, bez forków i spawnu podagentów, dane po drucie do pliku, do raportu liczby
i wycinki. Agent, który rozdelegował i zawisł z uciętym wynikiem, dostaje
SendMessage „dokończ w tej turze bez delegowania”.

## Weryfikator na żywo

`foreman-weryfikator` dostaje: SHA i katalog odbioru, kryteria (odczyt →
oczekiwane), narzędzie (skill z `profile.live_verify_skill` albo `/browse <adres>`),
konto roli, listę zapisów zakazanych. Jeden weryfikator na PR, który zmienia ekran
albo to, co ekran czyta (uprawnienia, funkcja, schemat); PR bez wpływu na żaden
ekran ma smoke;
raport → `evidence add --for <C>` per kryterium bez komendy; kryteria z komendą
mierzy `evidence run`.
