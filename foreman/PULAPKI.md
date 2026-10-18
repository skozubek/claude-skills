# Foreman: pułapki środowiska

Czytasz przy przygotowaniu gałęzi (krok 4). Każdy wpis to mechanizm, który
już raz kosztował sesję.

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
  w głównym klonie: tam robisz tylko checkout, merge, push i poprawki bramy
  z kroku 7 (numery migracji i wpisów, odsyłacze) na gałęzi integracyjnej.
- **Agent z powłoką widzi cudze zmiany** i potrafi uznać je za incydent,
  zabijając procesy orkiestratora. Typy floty mają zablokowane `kill`,
  `pkill`, forki i spawn podagentów w strażniku komend; agent spoza floty
  dostaje te zakazy w prompcie (LC-062), a gdy sam rozdelegował i zawisł
  z uciętym wynikiem, `SendMessage` „dokończ w tej turze bez delegowania”
  (MOL/Panel/meta/LEKCJE.md 2026-07-16).
- **PR zmergowany przez równoległą sesję** z tego samego konta: po cudzym merge'u weryfikujesz wdrożenie od
  zera, a PR zsynchronizowany z czymś jeszcze trzymasz jako draft (LC-105).

- **Merge `main` po squashu PR-a z gałęzi integracyjnej:** squash nie jest
  przodkiem gałęzi, więc git scala od starej bazy: plik dopisywany na końcu
  (dziennik decyzji) potrafi wyjść z cicho zgubioną albo sklejoną linią,
  a plik zmieniony identycznie po obu stronach daje konflikt. Gdy `git diff
  <head zmergowanego PR-a> origin/main` jest pusty, plik bierzesz z `main`
  (`git checkout --theirs` albo `git show origin/main:plik`), a swoje dopiski
  doklejasz; dziennik decyzji porównujesz z `main` (`git diff origin/main --
  docs/DECISIONS.md` ma same dodane linie).
- **Skanery per commit** (gitleaks na PR-ze, strażnik meta w `pre-push`)
  widzą każdy commit pośredni; zapobiega temu definicja wykonawcy (dane
  testowe, lokalny skan przed raportem). Trafienie na gałęzi integracyjnej
  nie znika poprawką ani `gitleaks:allow` w następnym commicie. Po
  potwierdzeniu, że to nie sekret: gałąź z `main` z jednym commitem
  (`git merge --squash <integracja>`), pełne bramki na nowym SHA, stary PR
  zamknięty z odsyłaczem. Nie wyjątek w skanerze (wyjątek na SHA commitu,
  który nie wejdzie na `main`, zostaje martwy w konfiguracji), nie force push.
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
- **Test klawiatury** zaczyna się od nasłuchu `keydown` na elemencie: pusta
  lista zdarzeń znaczy, że klawisz nie dotarł, nie że komponent jest zepsuty
  (LC-103).
- **Pomiar i `/code-review` w jednym klonie:** review na chwilę podmienia pliki,
  więc pomiar traci ważność. Rozdziel katalogi albo czas (LC-100).

- **Migracja po mergu w AdMotiv:** `migration-drift` na pushu do `main` czeka
  10 minut na zastosowanie migracji, więc workflow „Zastosuj migrację” idzie
  zaraz po mergu, a czerwony po tym czasie to dryf. Audyt uprawnień porównuje
  rejestr założeń (`scripts/konsumenci.json`) z żywymi danymi, więc migracja zmieniająca
  zarejestrowany obiekt poprawia jego wpis w tym samym PR-ze (check na PR-ze to
  wymusza), a nowa wartość zapisana przez cudzy moduł zapala audyt na main
  bez żadnego PR-a.
