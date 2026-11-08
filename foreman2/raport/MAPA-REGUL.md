# Mapa reguł bezpieczeństwa: foreman 1.x → 2.0

Artefakt wdrożenia (ginie z rollout'em razem z katalogiem `raport/`). Każda reguła
1.x, która chroniła przed incydentem, ma dom w 2.0 albo świadome usunięcie.
Równoważność: **=** to samo brzmienie lub skutek; **+** mechanizm egzekwuje
(plik stanu, CLI) zamiast prosić; **profil** przeniesione poza rdzeń do profilu
użytkownika/AGENTS.md repo; **−** celowo usunięte (powód w kolumnie).

| Reguła 1.x (dom) | LC | Dom 2.0 | Równ. |
|---|---|---|---|
| test dopasowania (≥2 zadania własnego rekonesansu, dłużej niż sesja, wiele warstw) | — | SKILL „Kiedy nie foreman2” + etap 0 | = |
| warunek ukończenia: ścieżka użytkownika, 2–5 kryteriów z odczytem i wynikiem, „testy zielone” to nie kryterium, próg czasu tym samym narzędziem, poza zakresem | — | etap 0; kryteria w `run.json` (`criteria add --read --expected`); `close` odmawia `done` bez `pass` | + |
| księga obietnic dla fal planu-rodzica | — | etap 0 „obietnice w planie jako otwarte” | = |
| nocny przelot nie startuje bez przyjętego warunku | — | `--unattended` wymaga sekcji Granice (BEZ-NADZORU) i kompletu kryteriów | = |
| rekonesans osobiście, Explore sonnet do szerokości, precedens na żywo | — | etap 1 | = |
| dane wrażliwe = decyzja Serge'a przed pierwszym odczytem z produkcji | — | etap 1: `decide ask --kind approval`; odpowiedź tylko `--by human` | + |
| mapa funkcji AdMotiv + `bin/doctor` przed robotą w module | — | profil `live_verify_skill: verify-admotiv`; weryfikator woła skill, który sam zna mapę | profil |
| glosariusz CONTEXT.md przez `domain-modeling` | — | odłożone (DECYZJE) | − (brak incydentu, który by łapał) |
| sekcje planu: problem, architektura z odrzuconymi wariantami, ustalenia, kontrakt, mapa testów, tryby awarii, poza zakresem, graf | — | etap 1 „gotowe, gdy” | = (bez `plik:linia`, zgodnie z regułą dokumentów) |
| zadanie = warstwa, 3–5 plików, ~100 tur; jeden właściciel pliku; tekst po zachowaniu; zmiana masowa od próbki; tożsamość zdarzeń; tabela stanów; wrażliwość per element; atomowość | — | etap 2; `task add --files` (właściciel w stanie) | = |
| recenzja planu Codexem (`-s read-only`, `high`, stdin), findingi odtwarzane, plan jako stan | LC-028 | etap 3 | = |
| gałąź integracyjna z main; własny worktree przy klonie dzielonym; `baseRef: head`; `.gitignore` worktrees; `.worktreeinclude`; commit kontraktu przed spawnem | LC-084 LC-095 | etap 4; `profile` ostrzega o braku `baseRef`/`.gitignore` | + |
| spawn naraz w tle; ≤3 żywych agentów (wliczając wznowienia, recenzentów, weryfikatorów) | — | etap 5; `task set --status running` odmawia czwartego (`max_live`) | + |
| rejestr: SHA spawnu, id agenta, gałąź, worktree, wariant, rundy, findingi; wszystko posiadane (cron, coffee, proces, konto, PR) | LC-094 | `run.json` `tasks[]` + `owned[]`; `own add/done` | + |
| odbiór: przodek, pliki w zakresie, weryfikacja uruchomiona przez brygadzistę; raport = hipoteza; dowód = komenda+SHA+wynik; bez powtórki na tym samym SHA | — | BRIEF „Protokół odbioru”; `evidence add` idempotentny per (cel, komenda, SHA) | + |
| przekroczony limit tur = odbiór nieprzyjęty | — | BRIEF | = |
| `merge --no-ff`; pełna weryfikacja integracji po froncie, przed PR | — | etap 5 „gotowe, gdy” | = |
| konflikt = błąd podziału grafu; ten sam agent dociąga i rozwiązuje | — | BRIEF | = (wskaźnik na nieistniejący skill `resolving-merge-conflicts` usunięty) |
| worktree i gałąź żyją do merge'a PR-a | — | etap 8 | = |
| poprawka SendMessage z dowodem; 3. wznowienie ostatnie; nowy wykonawca przy >200k kontekstu (`koszty.py --kontekst`) | LC-111 | etap 5; liczniki `rounds`/`resumes` w stanie | + |
| drabina: sonnet/opus po 2 nieprzyjętych → opus high; opus high po 2 → blokada z wpisem „czego brakuje, co próbowano” | LC-114 | etap 5; `task set --status blocked --note`; `close` → `blocked` | + |
| zależne czekają, reszta frontu idzie | — | `frontier` liczy zależności ze stanu | + |
| odejście z powodem = poprawka planu; odejście kontraktu dostaje czytelników | LC-093 | etap 5 | = |
| robota > 2× zapowiedzianej wraca do decyzji | LC-036 | etap 5 `decide ask` | = |
| od ~250k kontekstu bez nowego frontu, przekazanie sesji | LC-106 | etap 5 `resume` (przekazanie z pliku, nie z pamięci) | + |
| recenzja na przypiętym SHA: diff do pliku, recenzent trzy osie, Codex na tym samym SHA, jedna runda poprawek, delta bez drugiego Codexa poza migracją/uprawnieniami, tekst ≤2 rundy | LC-100 LC-117 | etap 6; recenzent (agents/foreman2-recenzent.md) | = |
| odbiór na żywo z checkoutu przypiętego SHA; liczby z DOM; progi na opublikowanej wersji | LC-116 | etap 6 `git worktree add odbior $SHA`; weryfikator | = |
| weryfikator AdMotiv raz na PR z ekranem; `bin/sesja` + Supabase przed spawnem | — | BRIEF „Weryfikator” (raz na PR); sprawdzenia produktu w skillu `verify-admotiv` i `profile.notes` | profil |
| wpisy mapy funkcji pisane przez wykonawcę, wklejane przez brygadzistę | — | poza rdzeniem: reguła AdMotiv do AGENTS.md repo / verify-admotiv | profil (do dopisania przy wdrożeniu) |
| migracja stosowana dopiero po merge'u (workflow, `migration-drift` 10 min) | — | `profiles/admotiv.example.json` | profil |
| bramki repo (verify / AGENTS / CLAUDE), inaczej kroki CI z tymi samymi parametrami | — | etap 7 + `profile.verify` | = |
| push + PR kończą każdy przelot; PR z integracji, nigdy z gałęzi agenta; `gh pr create --body-file` osobno | — | etap 7 | = |
| merge/deploy tylko z granic planu albo słowa Serge'a w tej sesji, bez blokad | — | `mandate` w `run.json`; bez mandatu `partial` | + |
| smoke przez ścieżkę produkcyjną; „main zielony” per workflow na commicie merge'a; workflow ręczny czytany przed uruchomieniem | LC-121 | etap 7 | = |
| meldunek po kryteriach; „zgodne” po rozkładzie | LC-115 | etap 8 `report`; BEZ-NADZORU „Sędzia” | = |
| postmortem po przelocie bez nadzoru/drabinie/blokadzie; sprzątanie rejestru (worktree, gałęzie lokalne i zdalne, crony, coffee, procesy przed usunięciem worktree, plan) | LC-029 LC-105 | etap 8; `own list --open` ma być puste; POSTMORTEM.md | + |
| push repo notatek (meta) po sprzątaniu | — | poza rdzeniem (specyficzne dla stanowiska) | − |
| brief: zakresy nie całe pliki; warunek z powodem; dowód ekranu jednym skryptem; agenci tylko do odczytu z zakazami | LC-062 | BRIEF | = |
| PRZELOT: Granice (zakres, dane, tożsamość po nazwie, koszt, kroki ludzkie); nie rozszerzasz; nie osłabiasz bramek | LC-092 | BEZ-NADZORU „Granice” | = |
| stop całego przelotu: zmiana zakresu, finding bezpieczeństwa, produkcja inaczej, koszt; blokada zadania: ten sam czerwony CI po 2 poprawkach, kontrakt bez czytelników; po merge'u PR poprawki | — | BEZ-NADZORU „Zatrzymanie” | = |
| merge, deploy, odbiór produkcyjny = trzy kamienie | — | etap 7 + BEZ-NADZORU | = |
| ścieżka odbioru jako operator: bypass, próbny wykonawca per klasa komend, środowisko raz, hooki, konta ról 200/4xx, dane po drucie, dane testowe bez SQL prod, ekran bez przeglądarki człowieka, dev czyta prod | LC-077 LC-104 | BEZ-NADZORU „Ścieżka odbioru” | = |
| licznik wywołań płatnych per obiekt | LC-099 | BEZ-NADZORU „Granice/Koszt” + `--budget`/`--max-budget-usd` | + |
| Codex nocą dzieli limit: próbne wywołanie, recenzent na delcie, PR „bez Codexa od SHA”, merge po Codexie | LC-118 | BEZ-NADZORU „Rachuba” | = |
| sieć i limit: `/coffee`, budzik `CronCreate` po resecie, po powrocie `git status` worktree i SendMessage | LC-038 | BEZ-NADZORU; runner `caffeinate` | = (jeden budzik zamiast dwóch) |
| sędzia próbki: etykiety z ludzkiego śladu, stałe ziarno, kontrole, punktacja per pole, Codex z tym samym przydziałem, druga runda | LC-101 | BEZ-NADZORU „Sędzia” | = |
| wykonawca: tylko pliki briefu; commit per zielony wycinek; warunki niespełnione w raporcie; komentarze; lint z powodem; klucze słownikowe; bez imion; NUL i gitleaks; pliki tymczasowe; kontekst to koszt; nie kończy wcześnie; kształt raportu | LC-016 LC-039 | agents/foreman2-wykonawca.md | = |
| strażnik komend floty (push, PR, deploy, kill, claude, codex) | LC-062 | `bin/bramka-floty.sh` na wykonawcy **i weryfikatorze**: także opcje git przed `push`, `gh api`/`workflow run`, `npm run deploy`, zdalna baza, zapis HTTP poza localhost; test czułości | + |
| zgoda modeli nie autoryzuje; odpowiedź approval tylko od człowieka | brief | `decide answer` wymaga `--by human`; hook PreToolUse `straz` odmawia `--by human` i ręcznego zapisu plików stanu z sesji modelu | + (nowe) |
| odmowa człowieka zatrzymuje zadanie, nie odblokowuje go | Codex (recenzja 2.0) | `decide ask --blocks` wymaga `--unblock-on`; inna odpowiedź → zadania `blocked` z notą | + (nowe) |
| DONE tylko z dowodem na ostatnim SHA | LC-009 LC-015 | `close` liczy najnowszy pomiar `pass` per kryterium na HEAD integracji; `criteria set --status` zakazane | + |
| po `cancel` nic nie rusza | brief | `state`/`task set running` odmawiają; hook `straz` odmawia spawnu, pushu, deployu (te same wzorce co flota) | + (nowe) |
| cisza zamiast końca przelotu | LC-033 | hook Stop blokuje też zadania `running` bez agentów w tle i etap bez `close`; każde wywołanie w `log.tsv` | + |
| recenzent: trzy osie; finding = miejsce + scenariusz | — | agents/foreman2-recenzent.md (funkcja zamiast linii) | = |
| weryfikator AdMotiv (start, sesja, doctor, kroki, sprzątanie) | — | generyczny weryfikator + skill z profilu | profil |
| PULAPKI: pre-push z `GIT_DIR` worktree; klon dzielony; agent zabija procesy; PR zmergowany równolegle; merge po squashu gubi linie dziennika; skanery per commit; kopia bez `auth.users`; NUL; keydown; pomiar vs `/code-review`; skrypt z ścieżki worktree | LC-058 LC-095 LC-062 LC-105 LC-016 LC-039 LC-103 LC-100 LC-108 | BRIEF „Pułapki środowiska” | = |
| PULAPKI produktowe: Turbopack, `bun install --frozen-lockfile`, strażnik dokumentów, okno crona, `migration-drift`, `konsumenci.json`, `supabase link` | LC-076 | `profile.install` (lockfile) + `profiles/admotiv.example.json` | profil |
| „czego nie dokładać”: tdd, freeze, canary, bramka testu, zespoły agentów, Workflow | LC-092 | SKILL „Czego nie dokładać” (+ gstack review/ship) | = |
| warianty wykonawcy + reguła „od trzech zadań w kategorii” | — | tabela wariantów; reguła pomiaru usunięta | − (nigdy nie zmierzona; dane per przelot w `run.json`) |
| koszt w meldunku (`koszty.py`) | — | etap 8; runner zapisuje `cost` z `claude -p` | = |

Luki do zamknięcia przy wdrożeniu (nie w rdzeniu): profil użytkownika dla AdMotiv
(`~/.foreman2/profiles/<klucz>.json` z `profiles/admotiv.example.json`), wpis
o mapie funkcji w AGENTS.md AdMotiv albo w skillu `verify-admotiv`.
