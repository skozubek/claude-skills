# Foreman 2.0

Brygadzista: prowadzi robotę implementacyjną od planu do PR-a flotą subagentów
Claude Code, ze stanem przelotu w pliku. Wersja 2.0 żyje w tym katalogu obok
foremana 1.x (`../foreman`), który zostaje punktem powrotu.

## Układ

| Plik | Rola |
|---|---|
| `SKILL.md` | rdzeń: etapy z warunkami „gotowe, gdy”, tabela komend stanu, drabina decyzji |
| `BRIEF.md` | szablon briefu wykonawcy, pułapki środowiska, protokół odbioru |
| `BEZ-NADZORU.md` | przelot bez człowieka: Granice, ścieżka odbioru, zatrzymanie, rachuba |
| `POSTMORTEM.md` | sekcja zwłok przelotu |
| `agents/` | definicje floty: wykonawca, recenzent, weryfikator |
| `bin/bramka-floty.sh` | strażnik komend floty (hook PreToolUse wykonawcy i weryfikatora; po `cancel` także brygadzisty) |
| `bin/foreman2` | stan przelotu (python3, bez zależności) |
| `bin/run` | przelot bez terminala: `claude -p` z agentami, hookami brygadzisty (Stop, PreToolUse), budżetem; preflight (`claude`, `jq`, strażnik) |
| `bin/agents-json` | `agents/*.md` → JSON dla `claude --agents` |
| `tests/` | `python3 -I -m unittest discover -s foreman2/tests` z katalogu repo |
| `DECYZJE.md` | macierz źródeł: co wołamy z zewnątrz, co trzymamy, co odrzucamy |

## Instalacja (wykonana 2026-11-08)

Skill: `~/.claude/skills/foreman2 → ~/Coding/claude-skills/foreman2`, wpina
`~/Coding/_context/wepnij-claude.sh` (razem z 1.x i verify-admotiv; `--status`
sprawdza). Agenci: `agents/foreman2-*.md` w tym repo to dowiązania do
`foreman2/agents/` (jedno źródło dla `~/.claude/agents` i dla `bin/run`, który
buduje `--agents` z `foreman2/agents/`); świeża sesja widzi sześć typów agentów,
trzy 1.x i trzy 2.0. Hooki skilla i agentów oczekują `~/.claude/skills/foreman2/bin/`
(foreman2, bramka-floty.sh).

Decyzje `approval` człowiek odpowiada ze swojego terminala
(`foreman2 --run <id> decide answer <D> rec --by human`), nie z sesji
brygadzisty: jej hook PreToolUse odmawia `--by human`.

Rollback: usunięcie dowiązania skilla, trzech dowiązań w `agents/` i katalogu
`~/.foreman2` (stan przelotów i profile). Foreman 1.x nie jest przez 2.0 dotykany.
Narzędzie kosztu `koszty.py` zostaje w `../foreman/` i jest wołane stamtąd; przy
zdjęciu 1.x przechodzi do `bin/`.

## Stan przelotu

`~/.foreman2/runs/<data>-<slug>/` (`FOREMAN2_HOME` zmienia dom):

- `run.json`: repo, baza, gałąź, etap, mandat, kryteria z dowodami, graf zadań
  z agentami i SHA spawnu, rejestr własności, kroki tylko-ludzkie, sesje, koszt,
  wersje źródeł (foreman2, claude, codex, gstack) w chwili `create`;
- `decisions.jsonl`: decyzje `auto` | `challenge` | `approval` ze statusem
  `pending` | `approved` | `overridden` | `rejected` | `auto_kept`;
- `evidence/E*.json`: dowód = komenda + SHA + wynik + werdykt (+ plik);
- `log.tsv`: czas, faza, decyzja, powód, dowód, wynik (append-only).

`~/.foreman2/active.json` wskazuje przelot aktywny per repo; `~/.foreman2/profiles/`
trzyma profil użytkownika per repo (klucz = sha1 adresu origin), gdy repo nie może
nieść własnej konfiguracji: `{"live_verify_skill": "verify-admotiv", "shared_clone":
true, "notes": ["..."]}`. `bin/foreman2 profile` pokazuje ścieżkę i to, co odczytał
z repo (skrypty, workflow, `settings.local.json`, AGENTS.md).

## Przelot bez terminala

```
bin/run --repo <dir> --slug <nazwa> --plan <plan.md> --budget 40 --unattended [--mandate merge]
bin/run --resume <run-id>
```

Runner tworzy przelot, pisze `agents.json` i `settings.json` (hooki Stop
i PreToolUse brygadzisty, gdy skill nie jest zainstalowany) do katalogu przelotu, odpala `claude -p` pod `caffeinate`, zapisuje pełny wynik do
`sessions/<ts>.json`, dopisuje koszt i drukuje `foreman2 status`. Gdy skill nie jest
zainstalowany w `~/.claude/skills`, treść `SKILL.md` idzie w promptcie: przelot
działa w dowolnym repo bez instalacji.

## Kontrakt dla sterowania z zewnątrz (ChatGPT, Mia, głos)

Ten sam plik stanu i te same komendy; sterownik nie potrzebuje sesji Claude:

| Operacja | Komenda | Idempotencja |
|---|---|---|
| create_task | `foreman2 create --slug … --plan …` (albo `bin/run`) | ten sam slug tego dnia = ten sam przelot |
| get_status | `foreman2 --run <id> status --json` | odczyt |
| list_decisions | `foreman2 --run <id> decisions --pending --json` | odczyt |
| provide_decision | `foreman2 --run <id> decide answer <D> rec\|<opcja> --by human:<kto>` | druga odpowiedź = no-op; `approval` tylko `--by human` |
| get_evidence | `foreman2 --run <id> evidence list` / `show <E>` / `check` | odczyt |
| cancel_task | `foreman2 --run <id> cancel --note …` | końcowy |

Autoryzacja: sterownik, który nie reprezentuje człowieka, nie odpowiada na
`approval`. Ślad audytu: `log.tsv` i `decisions.jsonl` (kto, kiedy, co). Wznowienie
przelotu po odpowiedzi: `bin/run --resume <id>`. Interfejs głosowy czyta `report`
i pisze `decide answer`; to warstwa UX poza tym katalogiem.

## Czego jeszcze nie ma

- Pierwszy przelot na repo z użytkownikami (AdMotiv): raport ma status PARTIAL,
  dopóki nie przejdzie nadzorowany. Profil użytkownika AdMotiv już leży
  w `~/.foreman2/profiles/` (z `profiles/admotiv.example.json`, klucz = sha1
  adresu origin; `bin/foreman2 profile --repo <klon>` pokazuje ścieżkę i treść).
  Mapa funkcji zostaje poza repo AdMotiv (narzędzie prywatne), wskaźnik do niej
  niesie profil, nie AGENTS.md.
- Most dla Mii, ChatGPT i głosu: proces, który czyta `status --json`
  i `decisions --pending`, pisze `decide answer` jako człowiek po jego słowie
  i woła `bin/run --resume`. Kontrakt wyżej jest kompletny, brakuje transportu
  (Remote Control, Channels albo cron na VM).
- Pilnowanie PR-a po przelocie (`/loop` z `gh pr checks`): po pomiarze, jak
  długo PR czeka na merge.
- Pamięć weryfikatora (`memory` agenta) dla powtarzalnych ścieżek odbioru.
- Hook Stop skilla w sesji interaktywnej (`/foreman2`): zmierzony tylko
  w `claude -p` przez runner.
- Koszt sesji zabitej w biegu: runner zapisuje koszt na końcu sesji, więc po
  zabiciu `run --resume` bez `--budget` dostaje pełną resztę budżetu. Do czasu
  liczenia kosztu z transkryptu podaje się `--budget` ręcznie.
