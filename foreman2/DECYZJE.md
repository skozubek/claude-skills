# Macierz źródeł foremana 2.0

Co wołamy z zewnątrz, co trzymamy lokalnie, co odrzucamy. Wersje z chwili decyzji;
`bin/foreman2 create` zapisuje wersje źródeł w `run.json` każdego przelotu.
Status: `obowiązuje` | `odłożone` (kandydat, warunek powrotu w powodzie) |
`uchylone` (edycja wpisu, nie nowy wiersz).

Źródła: gstack 1.94.19.0 (MIT, `~/.claude/skills/gstack`); pstack `6b03002`
(MIT, repo cursor/plugins, nieinstalowany); skille Matta Pococka: plugin 1.3.1
`49dd158` (zainstalowany), upstream `4ae2317` (MIT); Claude Code 2.1.319;
Codex CLI 0.159.3 (model z `~/.codex/config.toml`).

| Mechanizm | Źródło | Co robi | Decyzja | Powód | Status |
|---|---|---|---|---|---|
| `/browse` | gstack | przeglądarka headless, odczyt DOM `$B js` | **wołamy** (weryfikator, gdy repo nie ma własnego skilla) | jedyne niezależne od człowieka źródło dowodu ekranu; własna kopia zgniłaby | obowiązuje |
| kontrakt decyzji (`decisions.jsonl`: auto/approval/user_challenge, statusy, gramatyka `rec`/`<id><opcja>`) | gstack | kolejka decyzji dla trybu bez nadzoru | **adaptacja interfejsu**: te same rodzaje i statusy w `decisions.jsonl` przelotu, odpowiedź `rec \| <opcja> \| reject` | binaria gstack piszą do katalogu sesji gstack i telemetrii; nasz plik stanu jest jeden | obowiązuje |
| skill-contract (hook Stop blokujący raz) | gstack | wymusza domknięcie kontraktu skilla przed końcem tury | **adaptacja**: `foreman2 stop-check` z semantyką frontu (gotowe zadania + wolne miejsca + brak tła), najwyżej dwie blokady | kontrakt gstack nie zna grafu zadań | obowiązuje |
| `/verify` | gstack | odkrywa i uruchamia bramki repo | **odłożone**: `profile.verify` czyta skrypty i workflow wprost | preambuła i telemetria za jedną listę komend; wraca, gdy profil nie znajduje bramek w realnym repo | odłożone |
| `/codex` | gstack | opakowanie Codexa | **odrzucone**: `codex exec -s read-only …` jedną linią | opakowanie dodaje tryby i tekst, nie dowód | obowiązuje |
| `/review`, `/autoplan`, `plan-*-review`, `/ship` | gstack | recenzja PR, auto-decyzje planu, dostawa | **odrzucone** | recenzję robi natywny `/code-review high` + Codex + recenzent na jednym SHA; autoplan rozstrzyga pytania produktowe modelem (zgoda modeli nic nie autoryzuje); `/ship` ma własną ceremonię (VERSION, CHANGELOG) obok bramek repo | obowiązuje |
| `/investigate` | gstack | debugowanie do przyczyny | **odłożone**: wykonawca ma narzędzie Skill i może wołać sam | rdzeń nie przepisuje metody debugowania; wraca jako wskaźnik w briefie poprawki po postmortemie z czerwonym CI nieznanej przyczyny | odłożone |
| `/write-skill` | gstack | dieta i kontrola dryfu tekstu skilla | **odłożone**: niezależną kontrolę tekstu robi Codex | jedna kontrola wystarczy; wraca przy drugiej iteracji tekstu | odłożone |
| show-me-your-work (TSV `ts phase decision why evidence result`) | pstack | dziennik decyzji agenta | **adaptacja interfejsu**: `log.tsv` o tych samych 6 kolumnach | zgodny format pozwala czytać oba cudzymi narzędziami | obowiązuje |
| orchestrate, autonomous-run, never-block-on-the-human | pstack | świeży wykonawca per zadanie, weryfikator z innej rodziny, werdykt per SHA, dwa powtórzenia i porzucenie, pytanie tylko przy nieodwracalnym | **zachowane lokalnie** (etap 5, drabina, dowód na SHA, Codex jako inna rodzina) | zasady pokrywają się z 1.x; cytujemy źródło, nie kopiujemy playbooku | obowiązuje |
| session-pickup, pause-safely | pstack | przekazanie między sesjami | **adaptacja**: `foreman2 resume` z pliku stanu | stan w pliku zamiast prozy w kontekście | obowiązuje |
| swarm, reflect, correct, figure-it-out | pstack | równoległe agenty, refleksja, autokorekta | **odrzucone**; z reflect przyjęta zasada „regułę dowodzisz na incydencie z historii” (POSTMORTEM 6) | mamy postmortem i drabinę; Skill tool odmawia większości skilli pstack, slugi modeli nieprzenośne | obowiązuje |
| writing-for-agents | Pocock | wskaźniki kontekstu, hierarchia, progresywne ujawnianie, kryteria ukończenia, instrukcje pozytywne | **metodologia** tekstu 2.0 („gotowe, gdy” per etap, pliki na żądanie) | — | obowiązuje |
| implement-spec, to-tickets | Pocock | osobny orkiestrator: świeży implementer per ticket + tdd + merger; tickety pionowe z `Blocked by` | **odrzucone** jako konkurencyjny orkiestrator; przyjęty front zadań z zależnościami (`frontier`) | graf w `run.json` zamiast ticketów w plikach | obowiązuje |
| claude-handoff, loop-me | Pocock | `claude --bg --name`, pętle | **adaptacja**: runner `bin/run` z `--name`, `--session-id`, `--resume` | — | obowiązuje |
| tdd, code-review, grilling, domain-modeling | Pocock | test-first, recenzja dwuosiowa, przepytywanie, glosariusz | **odrzucone w przelocie** (tdd, grilling wymaga rozmowy; code-review natywny); domain-modeling **odłożone** (na żądanie w rekonesansie repo z GLOSSARY) | — | obowiązuje |
| `isolation: worktree`, `--agents`, `--max-budget-usd`, `--settings` z hookiem Stop, `--session-id`/`--resume`, `-p --output-format json` | Claude Code | izolacja agentów, flota bez instalacji, budżet, hook, wznowienie | **wołamy** (agenci, runner) | natywne i udokumentowane | obowiązuje |
| `/loop` (ScheduleWakeup) do pilnowania CI/PR | Claude Code | cykliczne sprawdzanie | **odłożone**: mapa drogowa | wymaga pomiaru, czy PR czeka dość długo, by było co pilnować | odłożone |
| pakowanie jako plugin (`--plugin-dir`) | Claude Code | skill + agenci bez instalacji | **odrzucone na teraz** | hooki z frontmatter agentów pluginu są ignorowane: strażnik komend floty znikałby | obowiązuje |
| pamięć agenta (`memory`) | Claude Code | trwała pamięć subagenta | **odłożone** | wykonawca ma być świeży per zadanie; kandydat dla weryfikatora | odłożone |
| `codex exec -s read-only` | Codex CLI | druga opinia planu, diffu, postmortemu | **wołamy** | inna rodzina modeli; model z konfiguracji, bez `-m` | obowiązuje |
| `verify-admotiv` | to repo | przejście AdMotiv ścieżką użytkownika | **wołamy przez profil** (`live_verify_skill`), rdzeń nie zna produktu | uniwersalność | obowiązuje |
| `bramka-floty.sh` | 1.x | odmowa push/PR/deploy/kill/claude/codex w Bash floty | **zachowane**, jedna kopia współdzielona z 1.x | sprawdzony strażnik przed ruchem; teraz także na weryfikatorze | obowiązuje |
| `koszty.py` | 1.x | koszt sesji i kontekst agenta | **zachowane**, wołane z `../foreman/` | przenosiny przy zdjęciu 1.x | obowiązuje |
| PULAPKI.md produktowe (strażnik dokumentów, migration-drift, `supabase link`, Turbopack, okno crona) | 1.x | pułapki AdMotiv | **przeniesione** do profilu użytkownika (`profiles/admotiv.example.json`) i AGENTS.md repo | rdzeń bez produktu | obowiązuje |
| reguła „wariant oceniany od trzech zadań w kategorii” | 1.x | pomiar wariantów | **usunięte** | nigdy nie zmierzona; dziennik przelotów (`run.json` per wariant) da pomiar, gdy będzie populacja | obowiązuje |
| wskaźnik na skill `resolving-merge-conflicts` | 1.x | — | **usunięte** | skill nie istnieje w żadnym katalogu | obowiązuje |
