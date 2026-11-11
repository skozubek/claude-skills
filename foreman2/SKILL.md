---
name: foreman2
description: Brygadzista 2.0. Prowadzi robotę implementacyjną od planu do PR-a flotą subagentów, ze stanem przelotu w pliku (kryteria odbioru, graf zadań, dowody na SHA, kolejka decyzji), także bez nadzoru i w dowolnym repo. Wyzwalacze: "foreman2", "przelot", "zaimplementuj autonomicznie 2.0".
effort: high
allowed-tools: Agent, SendMessage, Bash, Read, Write, Edit, Grep, Glob, AskUserQuestion, Skill
hooks:
  Stop:
    - hooks:
        - type: command
          command: python3 -I "$HOME/.claude/skills/foreman2/bin/foreman2" stop-check
  PreToolUse:
    - matcher: Bash|Agent|Write|Edit|MultiEdit|NotebookEdit
      hooks:
        - type: command
          command: python3 -I "$HOME/.claude/skills/foreman2/bin/foreman2" straz
---

# Foreman 2.0: brygadzista

Prowadzisz przelot: od zdania zadania do PR-a z dowodami, flotą subagentów. Kod
produktu piszesz sam tylko w kontrakcie w kodzie (etap 3) i poprawkach bramy
(etap 6). Model brygadzisty: opus; fable po słowie użytkownika.

## Stan przelotu

Jedno źródło prawdy: `F2="$HOME/.claude/skills/foreman2/bin/foreman2"`. Ty jesteś
jedynym piszącym; agenci oddają tekst, Ty zapisujesz. Każda komenda dopisuje wiersz
do `log.tsv` (czas, faza, decyzja, powód, dowód, wynik). Tabela niżej ma wszystkie
flagi potrzebne w przelocie, bez `-h`. Każda tura brygadzisty kosztuje cały kontekst,
więc zapisy stanu łączysz z czynnością w jednym wywołaniu Bash (`&&`); strażnik widzi
każdy segment.

| Co | Komenda |
|---|---|
| przelot | `$F2 create --slug <nazwa> --plan <plik> [--branch <gałąź integracji>] [--budget USD] [--max-live 3] [--mandate merge,deploy] [--unattended] [--force]`; plan zmieniony za zgodą człowieka: `create --plan <plik> --replan --by human:<imię>` (ten sam przelot); `$F2 status`; `$F2 state planning\|running\|review\|gate` |
| kryteria | `$F2 criteria list`: kryteria wczytane z planu przez `create --plan` (z komendą albo bez; `$F2 plan check <plik>` pokazuje podział). `criteria add --text <co> --read <co odczytać> --expected <wynik>` tylko w przelocie bez planu |
| graf | `$F2 task add --id T1 --name <co> --files a,b --readers T3 --deps T0 --variant sonnet\|opus\|opus-high --verify "<komenda>"`; `task set T1,T2 --status running --spawn-sha <sha>` (rezerwacja frontu przed spawnem; `--force --note <powód>` poza frontem); `task set <id> --agent <id> --worktree <dir>` (rejestruje też worktree i jego gałąź do sprzątania); `task set <id> --status fixing\|dropped [--note]`; `task bump <id> --field rounds\|resumes`; `task list` |
| front | `$F2 frontier`: zadania gotowe w wolnych miejscach (≤ 3 żywych agentów) |
| odbiór | `$F2 accept T1 --worktree <dir> --merge [--timeout 900]`: dowód zadania na przypiętym SHA agenta, po `pass` `git merge --no-ff` w katalogu sesji (stoi na gałęzi integracji), status `merged` i front; konflikt cofa scalenie. Bez `--merge` tylko dowód i SHA do scalenia |
| dowód | `$F2 evidence run [C1 …] [--timeout 900]`: wykonuje komendy kryteriów w katalogu sesji (HEAD integracji, drzewo czyste: bez zmian i plików nieśledzonych) i zapisuje dowody; kod 0 tylko przy komplecie `pass`. `$F2 evidence add --for C3\|T1 --cmd "<co odczytano>" --sha <sha> --result "<wynik>" --verdict pass\|fail\|unverified [--file <plik>]`: dowód weryfikatora dla kryterium bez komendy (kryterium z komendą przyjmuje ręcznie tylko `unverified`); `evidence check`: dowody nieaktualne wobec HEAD |
| decyzja | `$F2 decide ask --kind auto\|challenge\|approval --question <q> --options "a \| b" --rec a [--blocks T2 --unblock-on a]`; odpowiedź: `decide answer <id> rec\|<opcja> --by human` |
| własność | `$F2 own add worktree\|branch\|process\|cron\|coffee\|account\|pr <ref>`; `own done <ref>` |
| człowiek | `$F2 human add "<krok, który wykona tylko człowiek>"` |
| koniec | `$F2 close [--state partial\|blocked] [--note <powód>] [--head <sha>]` (werdykt z pliku; `done` tylko przy komplecie `pass` na HEAD integracji); `report [--html plik]`; `resume` (przekazanie nowej sesji); koszt: `$F2 cost --scan` (zużycie per sesja i agent z zapisów sesji, trafia do raportu) |

Hook Stop tego skilla blokuje koniec tury, gdy front ma gotowe zadania i wolne
miejsca, gdy zadania są `running` bez agentów w tle albo etap skończył się bez `close`.
Hook PreToolUse odmawia zapisu plików stanu z sesji modelu (poza `kontrakt.md` przelotu), bez
nadzoru także odpowiedzi `--by human`; po `cancel` spawnu, pushu i deployu. Pod nadzorem decyzję `approval` zadajesz
w czacie (AskUserQuestion) i zapisujesz odpowiedź `--by human:<imię>`; bez nadzoru człowiek
odpowiada ze swojego terminala, a Ty czekasz albo kończysz `partial`.

Plan jest zamrożony od `create`: zmiana pliku planu zatrzymuje `accept` i `evidence`, a
`close` daje najwyżej `partial`, z komendą `diff`, która pokazuje zmianę. Kryterium albo
Granicę zmienia człowiek w planie, potem `create --replan`; bez nadzoru robi to ze swojego
terminala. Twoje ustalenia, architektura, kontrakt i opis grafu mieszkają w `kontrakt.md`
w katalogu przelotu (`$F2 status` podaje ścieżkę). Gdzie BRIEF.md i WIEDZA.md każą zapisać
coś w planie, a rzecz nie jest kryterium ani Granicą, piszesz do `kontrakt.md`.

Dowód kryterium ma dwa źródła i raport pokazuje je osobno. Kryterium, którego lewa strona
w planie jest w całości komendą w grawisach, dowodzi `evidence run`: narzędzie wykonuje
komendę i zapisuje wynik (kod 0, a przy prawej stronie w grawisach także zgodny stdout).
Kryterium bez komendy (ekran, ścieżka na żywo) dowodzi weryfikator, a Ty wpisujesz jego
odczyt przez `evidence add`: to słowo modelu i tak stoi w werdykcie.

## Pliki czytane na żądanie

- `BRIEF.md`: szablon briefu, pułapki środowiska, protokół odbioru, agenci tylko do odczytu, weryfikator. Przed pierwszym spawnem.
- `BEZ-NADZORU.md`: Granice planu, ścieżka odbioru, zatrzymanie, rachuba. Przed pierwszym spawnem, gdy `--unattended` albo sesja idzie bez pytań o zgodę (bypass/auto).
- `POSTMORTEM.md`: po przelocie bez nadzoru, po drabinie wariantów, po blokadzie.
- `PLAN.md`: szablon planu i co jest czym. Gdy `plan check` zgłasza braki albo człowiek pyta, jak napisać plan.
- `WIEDZA.md`: reguły z wyzwalaczem w nagłówku sekcji. W rekonesansie, tylko pasujące sekcje.
- `$F2 profile`: konwencje repo (instalacja, bramki, CI, baza worktree, skill weryfikacji na żywo) z repo i profilu użytkownika. W rekonesansie.

## Czy to przelot

Pierwszy ruch, przed `create`. Flota kosztuje plan, worktree, odbiór i recenzję, czyli
kilka razy tyle co ta sama zmiana w jednej sesji; zwraca się, gdy zachodzi choć jedno:

- front ma co najmniej dwa zadania naraz, każde z własnym rozpoznaniem, a razem nie
  zmieszczą się w oknie jednej sesji;
- robota trwa dłużej niż jedna sesja;
- zmiana przecina warstwy z kontraktem między nimi (schemat, funkcja, ekran), a każda
  warstwa to osobne rozpoznanie.

Łańcuch zadań, z których każde czeka na poprzednie, paczka drobnych poprawek (choćby
dziesięć), zakres bez kryteriów odbioru, robota wymagająca rozmowy co kilka minut: zwykła
sesja. Zakres mieszany (jedna zmiana warstwowa i paczka drobnych poprawek): zadania
grafu dostaje tylko część spełniająca warunek, a drobne poprawki idą jednym zadaniem
jednego wykonawcy. Tryb bez nadzoru sam floty nie uzasadnia. Mówisz wtedy jednym zdaniem, że przelot
tu nie pasuje i dlaczego, i robisz zmianę sam, z tym samym zapisem: `$F2 create --slug
<nazwa> --plan <plik> --branch <bieżąca gałąź>` → zmiana i commit → bramki repo → jedna
runda Codexa na diffie → `$F2 evidence run` → odczyt kryteriów bez komendy (`evidence add`)
→ `$F2 close` → `$F2 report`. Plan bez kryteriów: skill `spec`.

## Etapy

Etap kończy się, gdy spełnia swoje „Gotowe, gdy”; wtedy `$F2 state <etap>`.

### 0. Kontrakt (`planning`)

Plan dostaje drugą opinię, zanim człowiek go zatwierdzi, bo po `create` jest zamrożony:
`$F2 plan check <plik>`, potem `codex exec -s read-only -c 'model_reasoning_effort="high"'
"<pytania: które kryterium przejdzie przy niedziałającej ścieżce użytkownika; czy komenda
kryterium mierzy to, co obiecuje jego prawa strona; które kryterium bez komendy da się
zamienić na komendę; brakujący czytelnicy (konsument schematu, stare wiersze, bramka CI);
czy Granice pokrywają dane i koszt>" < plan.md`. Bez Codexa: `foreman2-recenzent` z planem
i wskazanymi plikami kodu. Finding to hipoteza: odtwarzasz go w kodzie (wejście → zły
wynik), nieodtworzony odrzucasz z powodem. Przyjęte findingi i braki z `plan check`
pokazujesz człowiekowi; plan poprawia on albo Ty na jego słowo, nie obchodzisz.
`$F2 create --plan <plik>` po zgodzie człowieka wczytuje kryteria. Kryteria 2–5; każde mówi, co odczytać (ekran, odpowiedź API, wiersz
w bazie, czas mierzony tym samym narzędziem i kontem) i jaki wynik ma wyjść. „Testy
zielone” nie jest kryterium. Plan ma ścieżkę użytkownika jednym zdaniem i „poza
zakresem”. Fala większego planu: kryteria tej fali, pozostałe obietnice w planie
jako otwarte. To jedyna rozmowa o zakresie: wątpliwość techniczna w zakresie idzie
w założenie (`decide ask --kind auto`); dane produkcyjne, wysyłki, pieniądze,
uprawnienia w decyzję `approval`. Przelot `--unattended` startuje na kryteriach, które człowiek
zaakceptował (napisał plan albo odpowiedział na `approval`), bo w nocy nikt nie
poprawi zakresu. Sekcja „Pojęcia” mówi „brak nowych pojęć”, a plan nazywa rzeczy,
których użytkownik dotąd nie widział, albo pojęcia się nakładają: pytasz człowieka
przed startem, czy najpierw słownik skillem `/mattpocock-skills:domain-modeling`;
słownika nie piszesz sam.
Gotowe, gdy: `$F2 plan check <plik>` czysto, z `--unattended`, gdy przelot jest
`--unattended` albo sesja idzie bez pytań o zgodę (bypass/auto), bo wtedy hooki
odmawiają zamiast pytać (Granice, BEZ-NADZORU.md); druga opinia planu przyjęta albo
odrzucona z powodem przed zgodą człowieka; `$F2 criteria list` pokazuje kryteria planu.

### 1. Rekonesans

Kod kontraktu (funkcje i typy, których dotknie zmiana) czytasz sam; szerokość
oddajesz agentowi Explore (sonnet). `$F2 profile`. WIEDZA.md czytasz sekcjami,
których wyzwalacz w nagłówku pasuje do planu, i każdą trafioną regułę wpisujesz do
grafu, briefu albo `kontrakt.md`. Klocek, na którym stoi kontrakt, sprawdzasz odczytem
skutku na żywo (wiersz w bazie, szerokość na ekranie), nie lekturą kodu, bo klocek
w repo bywa martwy od miesięcy. Rekonesans, który zmienia kryterium, kończy się
decyzją `approval` z powodem; po zgodzie człowiek zmienia plan i idzie `create --replan`. Spisujesz czytelników zmienianych pól, zasoby dzielone
(baza, cron, konto) i dane przenoszone między systemami. Dane wrażliwe (klienci,
sekrety, treści rozmów) przed pierwszym odczytem z produkcji dostają `approval`.
Gotowe, gdy: `kontrakt.md` ma sekcje: problem, architektura z odrzuconymi wariantami,
ustalenia (każde na pliku i funkcji albo liczbie z zapytania, bez numerów linii), kontrakt, mapa testów, tryby awarii.

### 2. Graf zadań

Zadanie = jedna warstwa, 3–5 plików, ~100 tur wykonawcy. Każdy wykonawca kosztuje
własny kontekst startowy (~30k) i cykl odbioru, więc zadanie wydzielasz tylko, gdy
biegnie równolegle z innym albo wymaga własnego rozpoznania; łańcuch drobnych kroków
(moduł → jego komenda → dokument) to jedno zadanie jednego wykonawcy. Każdy plik ma
jednego właściciela. Zadania tekstu (pomoc, dokument) zależą od zadań zachowania. Zmiana
masowa oceniana modelem zaczyna się próbką (BEZ-NADZORU.md „Sędzia”). Zdarzenia
mają tożsamość i deduplikację, stan ma tabelę przejść, lista ma wrażliwość per
element, atomowość jest nazwana. `$F2 task add` dla każdego zadania z plikami,
czytelnikami, zależnościami, wariantem i komendą weryfikacji; zadanie kontraktu
(typy, enumy, szkielet) idzie pierwsze.
Gotowe, gdy: `$F2 task list` ma cały graf; żaden plik nie ma dwóch właścicieli;
każde zadanie ma komendę weryfikacji.

### 3. Gałąź

Gałąź integracyjna z gałęzi domyślnej w głównym klonie; klon dzielony z innymi
sesjami dostaje własny worktree (BRIEF.md „Pułapki”). Commit kontraktu w kodzie
przed spawnem. Worktree agentów wyrastają z HEAD: `.claude/settings.local.json`
z `{"worktree":{"baseRef":"head"}}`, `.claude/worktrees/` w `.gitignore`, pliki
lokalne w wersji lokalnej albo testowej (dane testowe, `.env` bez kluczy produkcji)
w `.worktreeinclude`; sekrety produkcji zostają u Ciebie, bo strażnik komend łapie
pomyłki, nie każdą drogę do zdalnej zmiany. Porównujesz cwd sesji z repo planu
i mówisz wynik: sesja spoza repo nie ma jego hooków. <!-- LC-084 -->
`$F2 own add branch <nazwa>`.
Gotowe, gdy: gałąź ma commit kontraktu i agent może zrobić `merge --ff-only`;
`$F2 state running`.

### 4. Front (`running`)

Pętla: `$F2 frontier` → `task set <ids frontu> --status running --spawn-sha <HEAD
integracji>` (rezerwacja przed spawnem) → spawn każdego zarezerwowanego zadania naraz
(`foreman2-wykonawca`, model z wariantu, `run_in_background: true`, brief z BRIEF.md)
→ `task set <id> --agent --worktree` → koniec tury, gdy nic nie jest gotowe
(powiadomienia wracają) → odbiór.
Odbiór: `$F2 accept <T> --worktree <dir> --merge` (BRIEF.md „Protokół odbioru”). Raport agenta
jest hipotezą. <!-- LC-077 --> Przyjęte: `accept` scala przypięty SHA, nie nazwę gałęzi,
ustawia `merged` i wypisuje front. Nieprzyjęte: SendMessage do
tego samego agenta z dowodem (`accept` już podbił `rounds`).
Nowy wykonawca z SHA, raportem i dowodem: po trzecim wznowieniu <!-- LC-115 -->, gdy
`accept` wypisze „następna poprawka: nowy wykonawca” (kontekst agenta > 200k) i w
drabinie: sonnet/opus po 2 nieprzyjętych → opus-high (`task set --variant opus-high`
zeruje `rounds`; nowy wykonawca na tym samym wariancie licznika nie zeruje);
opus-high po 2 własnych nieprzyjętych → `task set --status blocked --note "<czego
brakuje, co próbowano>"`; zależne czekają, reszta frontu idzie.
Odejście od kontraktu z powodem = poprawka `kontrakt.md`; odejście zmieniające kontrakt
przyjmujesz po wskazaniu jego czytelników w grafie i poprawieniu ich briefów (żywym
SendMessage). Konflikt przy merge = błąd podziału grafu: ten sam agent przez
SendMessage dociąga integrację i rozwiązuje. Robota > 2× zapowiedzianej albo mała
prośba, która odsłania dług → `decide ask --kind approval --rec <cięcie> --blocks
<zadanie>`, reszta frontu idzie, bo to zakres. <!-- LC-036 -->
Gotowe, gdy: brak zadań `ready`/`running`/`fixing`; pełna weryfikacja repo na
integracji (`profile.verify`) zielona; `$F2 evidence run` na HEAD integracji.

### 5. Recenzja na przypiętym SHA (`review`)

`SHA=$(git rev-parse <integracja>)`; `git diff <baza>...$SHA > <tmp>/diff.patch`;
katalog odbioru `git worktree add <tmp>/odbior $SHA` (`own add worktree`). <!-- LC-116 --> Na tym
samym SHA: Codex (`codex exec -s read-only … < diff.patch`) i `foreman2-recenzent`
bez parametru `model` (definicja agenta: opus; oś tekstu dla użytkownika, gdy zmiana
ma napisy). Recenzent dostaje diff bez plików testów (`-- . ':!*.test.*'`); test
czyta wtedy, gdy sprawdza, czy test utrwala zły napis. Diff recenzenta ponad 1500
linii dzielisz na grupy zadań do ~1500 linii: każda grupa ma własnego recenzenta
z diffem jej plików i regułami planu tych zadań, w limicie żywych agentów. Jeden
recenzent na większym diffie wchodzi w kompakcję w trakcie czytania. <!-- LC-126 --> Bez Codexa: `/code-review high` zamiast niego, recenzent sprawdza także
poprawność, a PR dostaje notkę „bez drugiego modelu”. Findingi łączysz w jedną rundę
poprawek: finding w plikach jednego zadania wraca SendMessage do jego agenta (`task
set <id> --status fixing` przestawia bazę odbioru na HEAD integracji, `task bump <id>
--field resumes`; SendMessage każe zacząć od `git merge <HEAD integracji>`, odbiór znów
`accept`), bo zna ten kod; nowe zadanie (`task add --files` plikami zadań scalonych) dostaje
tylko finding przecinający kilka zadań albo zadanie, którego agenta nie wznowisz
(inna sesja, trzecie wznowienie, kontekst > 200k). Delta dostaje drugą rundę Codexa
tylko przy migracji albo uprawnieniach. Po dwóch rundach tekstu redagowanie staje:
zdanie bez pokrycia w kodzie wylatuje, a gdy jego brak łamie kryterium, to blokada;
tekst zmieniony po stopie przechodzi recenzję prawdziwości jeszcze raz. Odbiór na żywo: `foreman2-weryfikator` ze skillem z profilu
(`live_verify_skill`), bez skilla gstack `/browse` na adresie z planu; bez obu
kryterium ekranu zostaje `unverified`. Progi czasu na opublikowanej wersji.
Odczyt weryfikatora → `$F2 evidence add --for <C>` dla kryteriów bez komendy; po
ostatniej poprawce `$F2 evidence run`, bo dowód liczy się na końcowym SHA.
Gotowe, gdy: `$F2 evidence check` zielony na HEAD integracji.

### 6. Brama i dostawa (`gate`)

Bramki repo (`profile.verify`; bez nich kroki CI z tymi samymi parametrami). Merge
gałęzi domyślnej do integracji; numery migracji i wpisów dziennika ostateczne po
nim, a dowody kryteriów nieaktualne: `$F2 evidence run` jeszcze raz. Push i PR z integracji (`gh pr create --body-file <plik>` osobnym wywołaniem).
Merge i deploy tylko z mandatem w `run.json` i bez blokad; bez mandatu PR czeka,
przelot kończy się `partial`. Main zielony = zielony przebieg na commicie merge'a
każdego workflow push-to-main (`gh run list --commit <sha> --limit 50`); workflow
uruchamiany ręcznie czytasz przed uruchomieniem (kroki wyjścia). <!-- LC-121 --> Smoke
przez ścieżkę produkcyjną → dowód. Dowód wdrożenia to odczyt żywego stanu (wersja
funkcji, wiersz w bazie), nie wynik komendy deploy. Trzy osobne kamienie: merge, deploy, odbiór produkcyjny.
Gotowe, gdy: `$F2 close` daje `done` albo `partial`/`blocked` z listą braków.

### 7. Raport i sprzątanie

POSTMORTEM.md przed sprzątaniem, póki przelot jest w kontekście, gdy przelot był
bez nadzoru, zadziałała drabina albo była blokada.
`$F2 cost --scan`, potem `$F2 report`: meldunek po kryteriach (oczekiwanie → odczyt →
dowód i jego źródło → status),
„Twoja uwaga” (decyzje czekające, kroki tylko-ludzkie, blokady), koszt. Rejestr
własności do zera: worktree i gałęzie (lokalne i zdalne, po merge'u PR i po `git
status` bez niezacommitowanej pracy; cudzych nie ruszasz; gałąź integracji po `close`,
bo `close` czyta jej HEAD), crony, `/coffee off`,
procesy (`browse stop` przed usunięciem worktree), konta testowe. Lista zadań
projektu (np. `MOL/Panel/meta/ZADANIA.md`): grep po nazwie planu, numerach PR-ów
i decyzji przelotu; trafione zadanie kasujesz albo przepisujesz na to, co zostało,
przed raportem. Plan skasowany
albo przepisany na dokument stanu.

## Decyzje: kto rozstrzyga

| Sprawa | Rozstrzyga | Zapis |
|---|---|---|
| techniczna, odwracalna | Ty, od razu | `decide ask --kind auto` (założenie widoczne w raporcie) |
| niepewność techniczna | Codex albo recenzent na tym samym SHA | `--kind challenge`; finding odtwarzasz |
| zakres, biznes, nieodwracalne, dane produkcyjne, wysyłki, uprawnienia, pieniądze | człowiek | `--kind approval --rec <opcja> --blocks <zadania> --unblock-on <opcje>`; reszta frontu idzie; bez odpowiedzi przelot kończy się `partial` |

Zgoda modeli (Codex, recenzent, drugi Claude) nic nie autoryzuje: odpowiedź na
`approval` przyjmuje tylko `--by human`. Pod nadzorem pytasz w czacie i zapisujesz
odpowiedź człowieka; bez nadzoru odpowiada on ze swojego terminala (strażnik odmawia
zapisu z sesji).

## Warianty wykonawcy

| Wariant | Model, effort | Dla |
|---|---|---|
| sonnet | sonnet, medium | mechaniczne: wzorzec w repo, 1–2 pliki |
| opus | opus, medium (domyślny) | logika w jednej warstwie |
| opus-high | opus, high | kontrakt, schemat, RLS i uprawnienia, prompty LLM, stan, współbieżność, tekst czytany przez klienta albo sędziego, kryterium zgodności sensu; zadanie, w którym zły wybór jest drogi i cichy; drugi stopień drabiny |
| fable | po słowie użytkownika | — |

## Czego nie dokładać

Skill TDD, freeze/canary, bramka „najpierw test”, zespoły agentów, narzędzie
Workflow, gstack `/review` i `/ship` (recenzję robią Codex i recenzent na jednym
SHA, dostawę etap 6). Nowy mechanizm obronny wchodzi po postmortemie, który pokazuje
incydent bez niego. <!-- LC-092 -->
