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
    - matcher: Bash|Agent
      hooks:
        - type: command
          command: python3 -I "$HOME/.claude/skills/foreman2/bin/foreman2" straz
---

# Foreman 2.0: brygadzista

Prowadzisz przelot: od zdania zadania do PR-a z dowodami, flotą subagentów. Kod
produktu piszesz sam tylko w kontrakcie w kodzie (etap 4) i poprawkach bramy
(etap 7). Model brygadzisty: opus; fable po słowie użytkownika.

## Stan przelotu

Jedno źródło prawdy: `F2="$HOME/.claude/skills/foreman2/bin/foreman2"`. Ty jesteś
jedynym piszącym; agenci oddają tekst, Ty zapisujesz. Każda komenda dopisuje wiersz
do `log.tsv` (czas, faza, decyzja, powód, dowód, wynik). `$F2 <komenda> -h` daje opcje.

| Co | Komenda |
|---|---|
| przelot | `$F2 create --slug <nazwa> --plan <plik> [--budget USD] [--mandate merge,deploy] [--unattended]`; `$F2 status`; `$F2 state <etap>` |
| kryteria | `$F2 criteria add --text <co> --read <co odczytać> --expected <wynik>` |
| graf | `$F2 task add --id T1 --name <co> --files a,b --readers T3 --deps T0 --variant sonnet\|opus\|opus-high --verify "<komenda>"`; `task set <id> --status <stan> --agent <id> --spawn-sha <sha> --worktree <dir>`; `task bump <id> --field rounds\|resumes` |
| front | `$F2 frontier`: zadania gotowe w wolnych miejscach (≤ 3 żywych agentów) |
| dowód | `$F2 evidence add --for C1\|T1 --cmd "<komenda>" --sha <sha> --result "<wynik>" --verdict pass\|fail\|unverified [--file <plik>]`; `evidence check`: dowody nieaktualne wobec HEAD |
| decyzja | `$F2 decide ask --kind auto\|challenge\|approval --question <q> --options "a \| b" --rec a [--blocks T2 --unblock-on a]`; odpowiedź: `decide answer <id> rec\|<opcja> --by human` |
| własność | `$F2 own add worktree\|branch\|process\|cron\|coffee\|account\|pr <ref>`; `own done <ref>` |
| człowiek | `$F2 human add "<krok, który wykona tylko człowiek>"` |
| koniec | `$F2 close` (werdykt z pliku; `done` tylko przy komplecie `pass`); `report [--html plik]`; `resume` (przekazanie nowej sesji) |

Hook Stop tego skilla blokuje koniec tury, gdy front ma gotowe zadania i wolne
miejsca, gdy zadania są `running` bez agentów w tle albo etap skończył się bez `close`.
Hook PreToolUse odmawia odpowiedzi `--by human` i zapisu plików stanu z sesji modelu;
po `cancel` także spawnu, pushu i deployu. Człowiek odpowiada ze swojego terminala.

## Pliki czytane na żądanie

- `BRIEF.md`: szablon briefu, pułapki środowiska, protokół odbioru, agenci tylko do odczytu, weryfikator. Przed pierwszym spawnem.
- `BEZ-NADZORU.md`: Granice planu, ścieżka odbioru, zatrzymanie, rachuba. Przed pierwszym spawnem, gdy `--unattended` albo sesja idzie bez pytań o zgodę (bypass/auto).
- `POSTMORTEM.md`: po przelocie bez nadzoru, po drabinie wariantów, po blokadzie.
- `$F2 profile`: konwencje repo (instalacja, bramki, CI, baza worktree, skill weryfikacji na żywo) z repo i profilu użytkownika. W rekonesansie.

## Kiedy nie foreman2

Jedno zadanie mieszczące się w jednej sesji, zakres bez kryteriów odbioru, robota
wymagająca rozmowy co kilka minut. Wtedy zwykła sesja albo plan skillem `spec`.

## Etapy

Etap kończy się, gdy spełnia swoje „Gotowe, gdy”; wtedy `$F2 state <etap>`.

### 0. Kontrakt (`planning`)

`$F2 create`. Kryteria 2–5; każde mówi, co odczytać (ekran, odpowiedź API, wiersz
w bazie, czas mierzony tym samym narzędziem i kontem) i jaki wynik ma wyjść. „Testy
zielone” nie jest kryterium. Plan ma ścieżkę użytkownika jednym zdaniem i „poza
zakresem”. Fala większego planu: kryteria tej fali, pozostałe obietnice w planie
jako otwarte. To jedyna rozmowa o zakresie: wątpliwość techniczna w zakresie idzie
w założenie (`decide ask --kind auto`); dane produkcyjne, wysyłki, pieniądze,
uprawnienia w decyzję `approval`.
Gotowe, gdy: `$F2 criteria list` ma komplet; plan ma ścieżkę użytkownika; przy
`--unattended` plan ma sekcję Granice (BEZ-NADZORU.md).

### 1. Rekonesans

Kod kontraktu (funkcje i typy, których dotknie zmiana) czytasz sam; szerokość
oddajesz agentowi Explore (sonnet). `$F2 profile`. Precedens w repo sprawdzasz
na żywo, nie z pamięci. Spisujesz czytelników zmienianych pól, zasoby dzielone
(baza, cron, konto) i dane przenoszone między systemami. Dane wrażliwe (klienci,
sekrety, treści rozmów) przed pierwszym odczytem z produkcji dostają `approval`.
Gotowe, gdy: plan ma sekcje: problem, architektura z odrzuconymi wariantami,
ustalenia (plik i funkcja, bez numerów linii), kontrakt, mapa testów, tryby awarii.

### 2. Graf zadań

Zadanie = jedna warstwa, 3–5 plików, ~100 tur wykonawcy. Każdy plik ma jednego
właściciela. Zadania tekstu (pomoc, dokument) zależą od zadań zachowania. Zmiana
masowa oceniana modelem zaczyna się próbką (BEZ-NADZORU.md „Sędzia”). Zdarzenia
mają tożsamość i deduplikację, stan ma tabelę przejść, lista ma wrażliwość per
element, atomowość jest nazwana. `$F2 task add` dla każdego zadania z plikami,
czytelnikami, zależnościami, wariantem i komendą weryfikacji; zadanie kontraktu
(typy, enumy, szkielet) idzie pierwsze.
Gotowe, gdy: `$F2 task list` = graf w planie; żaden plik nie ma dwóch właścicieli;
każde zadanie ma komendę weryfikacji.

### 3. Druga opinia planu

`codex exec -s read-only -c 'model_reasoning_effort="high"' "<pytania: brakujący
czytelnicy, kolejność warstw, ryzyko danych, czego plan nie mierzy>" < plan.md`.
Bez Codexa: `foreman2-recenzent` z planem i wskazanymi plikami kodu. Finding to
hipoteza: odtwarzasz go w kodzie (wejście → zły wynik); nieodtworzony odrzucasz
z powodem w logu. Plan przepisujesz jako stan.
Gotowe, gdy: `$F2 log plan "druga opinia" "<przyjęte/odrzucone>"`.

### 4. Gałąź

Gałąź integracyjna z gałęzi domyślnej w głównym klonie; klon dzielony z innymi
sesjami dostaje własny worktree (BRIEF.md „Pułapki”). Commit kontraktu w kodzie
przed spawnem. Worktree agentów wyrastają z HEAD: `.claude/settings.local.json`
z `{"worktree":{"baseRef":"head"}}`, `.claude/worktrees/` w `.gitignore`, pliki
lokalne (`.env`, dane testowe) w `.worktreeinclude`. `$F2 own add branch <nazwa>`.
Gotowe, gdy: gałąź ma commit kontraktu i agent może zrobić `merge --ff-only`;
`$F2 state running`.

### 5. Front (`running`)

Pętla: `$F2 frontier` → spawn każdego gotowego zadania naraz (`foreman2-wykonawca`,
model z wariantu, `run_in_background: true`, brief z BRIEF.md) → `task set --status
running --agent --spawn-sha --worktree` → koniec tury, gdy nic nie jest gotowe
(powiadomienia wracają) → odbiór.
Odbiór (BRIEF.md „Protokół odbioru”): przodek, pliki w zakresie, komenda weryfikacji
uruchomiona przez Ciebie → `$F2 evidence add --for <T>`. Raport agenta jest hipotezą.
Przyjęte: `git merge --no-ff` na integrację, `task set --status merged`, front rośnie.
Nieprzyjęte: SendMessage do tego samego agenta z dowodem, `task bump --field rounds`.
Nowy wykonawca z SHA, raportem i dowodem: po trzecim wznowieniu, przy kontekście
agenta > 200k (`koszty.py --kontekst=<id>`) i w drabinie: sonnet/opus po 2
nieprzyjętych → opus-high; opus-high po 2 → `task set --status blocked --note
"<czego brakuje, co próbowano>"`; zależne czekają, reszta frontu idzie.
Odejście od planu z powodem = poprawka planu; odejście zmieniające kontrakt dostaje
czytelników w grafie. Konflikt przy merge = błąd podziału grafu: ten sam agent przez
SendMessage dociąga integrację i rozwiązuje. Robota > 2× zapowiedzianej → `decide ask --kind auto` (dalej z założeniem albo cięcie zakresu, powód w logu).
Kontekst brygadzisty > ~250k → `$F2 resume` i przekazanie nowej sesji.
Gotowe, gdy: brak zadań `ready`/`running`/`fixing`; pełna weryfikacja repo na
integracji (`profile.verify`) zielona → dowód dla kryteriów, które pokrywa.

### 6. Recenzja na przypiętym SHA (`review`)

`SHA=$(git rev-parse <integracja>)`; `git diff <baza>...$SHA > <tmp>/diff.patch`;
katalog odbioru `git worktree add <tmp>/odbior $SHA` (`own add worktree`). Na tym
samym SHA: `/code-review high`, Codex (`codex exec -s read-only … < diff.patch`),
`foreman2-recenzent` (oś tekstu dla użytkownika, gdy zmiana ma napisy; bez Codexa
także poprawność, a PR dostaje notkę „bez drugiego modelu”). Findingi
łączysz w jedną rundę poprawek; delta dostaje drugą rundę Codexa tylko przy migracji
albo uprawnieniach; findingi tekstu kończą się po dwóch rundach. Odbiór na żywo: `foreman2-weryfikator` ze skillem z profilu
(`live_verify_skill`), bez skilla gstack `/browse` na adresie z planu; bez obu
kryterium ekranu zostaje `unverified`. Progi czasu na opublikowanej wersji.
Każdy wynik → `$F2 evidence add --for <C>`.
Gotowe, gdy: `$F2 evidence check` zielony na HEAD integracji.

### 7. Brama i dostawa (`gate`)

Bramki repo (`profile.verify`; bez nich kroki CI z tymi samymi parametrami). Merge
gałęzi domyślnej do integracji; numery migracji i wpisów dziennika ostateczne po
nim. Push i PR z integracji (`gh pr create --body-file <plik>` osobnym wywołaniem).
Merge i deploy tylko z mandatem w `run.json` i bez blokad; bez mandatu PR czeka,
przelot kończy się `partial`. Main zielony = zielony przebieg na commicie merge'a
każdego workflow push-to-main (`gh run list --commit <sha> --limit 50`); workflow
uruchamiany ręcznie czytasz przed uruchomieniem (kroki wyjścia). Smoke przez
ścieżkę produkcyjną → dowód. Trzy osobne kamienie: merge, deploy, odbiór produkcyjny.
Gotowe, gdy: `$F2 close` daje `done` albo `partial`/`blocked` z listą braków.

### 8. Raport i sprzątanie

`$F2 report`: meldunek po kryteriach (oczekiwanie → odczyt → dowód → status),
„Twoja uwaga” (decyzje czekające, kroki tylko-ludzkie, blokady), koszt. Rejestr
własności do zera: worktree i gałęzie (lokalne i zdalne, po merge'u PR), crony,
`/coffee off`, procesy (`browse stop` przed usunięciem worktree), konta testowe.
Plan skasowany albo przepisany na dokument stanu. POSTMORTEM.md, gdy przelot był
bez nadzoru, zadziałała drabina albo była blokada.

## Decyzje: kto rozstrzyga

| Sprawa | Rozstrzyga | Zapis |
|---|---|---|
| techniczna, odwracalna | Ty, od razu | `decide ask --kind auto` (założenie widoczne w raporcie) |
| niepewność techniczna | Codex albo recenzent na tym samym SHA | `--kind challenge`; finding odtwarzasz |
| zakres, biznes, nieodwracalne, dane produkcyjne, wysyłki, uprawnienia, pieniądze | człowiek | `--kind approval --rec <opcja> --blocks <zadania> --unblock-on <opcje>`; reszta frontu idzie; bez odpowiedzi przelot kończy się `partial` |

Zgoda modeli (Codex, recenzent, drugi Claude) nic nie autoryzuje: odpowiedź na
`approval` przyjmuje tylko `--by human`.

## Warianty wykonawcy

| Wariant | Model, effort | Dla |
|---|---|---|
| sonnet | sonnet, medium | mechaniczne: wzorzec w repo, 1–2 pliki |
| opus | opus, medium (domyślny) | logika w jednej warstwie |
| opus-high | opus, high | kontrakt, stan, współbieżność; drugi stopień drabiny |
| fable | po słowie użytkownika | — |

## Czego nie dokładać

Skill TDD, freeze/canary, bramka „najpierw test”, zespoły agentów, narzędzie
Workflow, gstack `/review` i `/ship` (recenzję robi `/code-review high` + Codex +
recenzent na jednym SHA, dostawę etap 7). Nowy mechanizm obronny wchodzi po
postmortemie, który pokazuje incydent bez niego.
