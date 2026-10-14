# Foreman: pułapki środowiska

Czytasz przy przygotowaniu gałęzi (krok 4) i wtedy, gdy objaw z tabeli
pojawi się w pętli frontu. Każdy wiersz to mechanizm, który już raz kosztował
sesję.

## Worktree i git

- **Push z worktree** odpala `pre-push` z wyeksportowanym `GIT_DIR`, więc testy
  hooka robiące `git commit` w katalogu tymczasowym wpisują commity do
  prawdziwej gałęzi. Pushujesz z głównego klonu po scaleniu; gdy push z
  worktree jest nieunikniony, idzie `--no-verify` po pełnych bramkach z ręki,
  a `git log` sprawdzasz zaraz po nim (LC-058).
- **Turbopack w worktree** z dowiązanym `node_modules` pada na „points out of
  the filesystem root". Agent instaluje zależności we własnym worktree; dev
  serwer na dowiązaniu startuje z `--webpack` (LC-076).
- **Skrypt importujący kod ze ścieżki worktree** umiera razem z nim. Importuj
  z głównego klonu albo z kopii `git show <ref>:ścieżka` z zapisanym `ref`
  (LC-108).
- **Klon dzielony z innymi sesjami:** `git stash`, `reset`, `checkout --`
  i `restore` zabierają cudze niezacommitowane edycje (LC-095). Agenci floty
  pracują we własnych worktree, więc ryzyko zostaje po Twojej stronie
  w głównym klonie: tam robisz tylko checkout, merge i push.
- **Agent z powłoką widzi cudze zmiany** i potrafi uznać je za incydent,
  zabijając procesy orkiestratora. Typy floty mają zablokowane `kill`,
  `pkill`, forki i spawn podagentów w strażniku komend; agent spoza floty
  dostaje te zakazy w prompcie (LC-062).
- **PR zmergowany przez równoległą sesję** z tego samego konta: przed merge'em
  czytasz `state` i `mergedAt`, po cudzym merge'u weryfikujesz wdrożenie od
  zera, a PR zsynchronizowany z czymś jeszcze trzymasz jako draft (LC-105).

- **Skaner sekretów per commit na PR-ze z gałęzi integracyjnej** (gitleaks)
  widzi każdy commit pośredni; fałszywy alarm w commicie pośrednim nie znika
  poprawką w następnym. Po potwierdzeniu, że to nie sekret: gałąź z `main`
  z jednym commitem (`git merge --squash <integracja>`), pełne bramki na nowym
  SHA, stary PR zamknięty z odsyłaczem. Nie wyjątek w skanerze, nie force push
  (CRM fala A, UUID marki wzięty za klucz HubSpota).
- **Kopia lokalna bez kont użytkowników:** klucz obcy do `auth.users`
  przechodzi na kopii, pada na produkcji (profile skasowanych kont). Przed
  testem zapytanie na produkcji o anomalie w danych, które czyta zmiana
  (sieroty, puste, duplikaty), i te przypadki w teście (CRM fala A: import
  padł na właścicielu bez konta).

## Narzędzia i pomiar

- **Znak sterujący wpisany surowo do literału** przechodzi typy i testy, a plik
  staje się binarny dla `grep`. Liczenie bajtów NUL:
  `tr -cd '\000' < plik | wc -c` (LC-016). Sam przepis sprawdzasz najpierw
  na wzorcu, który MUSI trafić: powłoka nie przenosi NUL przez argv i licznik
  potrafi policzyć linie zamiast NUL-i (LC-039).
- **Daemon gstack `browse`** jest osobny per repo, a subagent startuje
  w katalogu sesji: komendy przeglądarki odpalasz z katalogu testowanego repo,
  każdy równoległy użytkownik przeglądarki dostaje własną kartę `newtab` albo
  kroki idą atomowo przez `chain` (LC-055, LC-075). To headless bez sesji
  użytkownika; po aktualizacji gstacka bywa bez swojej wersji Chromium
  (`npx playwright install chromium` z jego katalogu).
- **Sesja zalogowana dla gstack bez klikania** w AdMotiv: `verify-admotiv/bin/sesja
  <email>` (link logowania kluczem serwisowym, tokeny tylko w plikach 0600,
  nie zakłada kont; tylko konto z Granic). Po odbiorze `bin/sprzataj`.
- **Klik po referencji `@eN` gstacka w panelu bocznym (Sheet) trafia w inny
  przycisk** (ten sam napis w wielu wierszach, nakładki): „Zgłoś” przy
  adresie otworzyło okno „Zgłoś wszystkie”. Przyciski w panelach klikasz
  przez DOM (`$B eval` ze skryptem: znajdź link wiersza, w jego kontenerze
  przycisk po napisie, `.click()`), a pole Reacta wypełniasz natywnym
  setterem + `input`; wynik potwierdzasz w bazie, nie w tekście ekranu
  (przelot E2E MOL 11.10).
- **Test klawiatury** zaczyna się od nasłuchu `keydown` na elemencie: pusta
  lista zdarzeń znaczy, że klawisz nie dotarł, nie że komponent jest zepsuty
  (LC-103).
- **Proces w tle** odpalony `nohup … &` ginie z powłoką narzędzia; długa
  robota idzie przez `run_in_background` (LC-063, pilnuje hook).
- **Pomiar i `/code-review` w jednym klonie:** review na chwilę podmienia pliki,
  więc pomiar traci ważność. Rozdziel katalogi albo czas (LC-100).

## Objawy w pętli frontu

| Objaw | Przyczyna | Naprawa |
|---|---|---|
| Konflikt przy scaleniu | dwa zadania równoległe w jednym pliku | podział grafu po właścicielu pliku albo zależność między nimi |
| Test czerwony „pod obciążeniem”, osobno zielony | twardy próg czasu bez zapasu | próg i zapas wobec `main` w kroku 1, komenda pod obciążeniem w briefie |
| Agent „skończył", weryfikacja czerwona | brief bez dokładnych komend | komendy wprost w briefie |
| Agent obszedł warunek | warunek bez powodu | powód liczbowy albo `file:line` |
| Narzędzia tekstowe milkną na pliku | znak sterujący w źródle | liczenie NUL, patrz wyżej |
| Powierzchnia niewidoczna w runtime | pominięta bramka rejestru | rozpoznanie bramek w kroku 1 |
| Worktree agenta bez commitów poprzednika | `worktree.baseRef` na domyślnym `fresh` | `"head"` w `.claude/settings.local.json`, checkout gałęzi integracyjnej przed spawnem |
| Okno brygadzisty pełne w pierwszych minutach | rozpoznanie pełnymi odczytami | `grep` po nazwach, wąskie zakresy, drut do pliku |
| Po przeliczeniu danych psuje się coś nietkniętego | czytelnik pola stał na brudzie | czytelnicy na próbce przed i po, krok 1 |
| Naprawa regresji rośnie z wersji na wersję | trzecia propozycja w tym samym miejscu | naprawa wąska w miejscu wywołania; „porządnie dla całości" na listę powrotu |
| Agent zawiesił się przed syntezą z uciętym wynikiem | agent sam rozdelegował podzadania | typy floty nie mają narzędzia `Agent`; agent spoza floty dostaje `SendMessage` „dokończ w tej turze bez delegowania", najważniejszy obszar dostaje drugie przejście (LEKCJE.md 2026-07-16) |
