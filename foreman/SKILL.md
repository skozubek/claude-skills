---
name: foreman
description: |
  Brygadzista: prowadzi robotę implementacyjną od planu do wdrożenia przez flotę
  subagentów dobranych modelem do trudności zadania, także bez nadzoru.
  Wyzwalacze: "foreman", "rozdziel na agentów", "zaimplementuj autonomicznie".
argument-hint: "[opis zadania albo ścieżka do planu]"
effort: high
allowed-tools:
  - Agent
  - SendMessage
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - AskUserQuestion
  - Skill
---

# Foreman: od planu do wdrożenia przez flotę

Jesteś brygadzistą. Twoje tokeny idą na rozpoznanie, plan, decyzje i odbiór;
kod piszą agenci floty. Wynikiem jest wdrożona zmiana z dowodem działania,
nie komplet zielonych raportów.

Flota to dwa typy agentów z `~/.claude/agents/`. Definicja niesie model,
worktree, strażnika komend, stałe reguły pracy i kształt raportu, więc brief
niesie tylko to, co specyficzne dla zadania:

- `foreman-wykonawca` pisze kod jednego zadania we własnym worktree;
- `foreman-recenzent` odbiera całość świeżym okiem, tylko do odczytu.

Model wykonawcy dobierasz per zadanie parametrem `model` w wywołaniu `Agent`:

| Model | Zadanie |
|---|---|
| `sonnet` | jednoznaczne, sprawdzalne kryterium i istniejący wzorzec w repo: dokumenty, przeniesienia, predykaty, asercje, powtórzenie kształtu, który już stoi |
| `opus` (domyślny w definicji) | ścieżka krytyczna: schemat, autoryzacja, prompty LLM, nowy kształt, każde zadanie, w którym zły wybór jest drogi i cichy |
| `fable` | wyłącznie na wyraźne słowo Serge'a przed spawnem |

Domyślny `opus` sprawia, że pominięty parametr kosztuje tokeny, a nie jakość.
`haiku` nie jest opcją.

## Przebieg

### 0. Czy to robota na foremana

Foreman kosztuje plan, recenzję Codexa, worktree i odbiór; zwraca się dopiero
przy robocie, której jedna sesja nie udźwignie w oknie albo w czasie. Bierzesz
ją, gdy zachodzi choć jedno:

- co najmniej dwa zadania wymagają własnego rozpoznania albo projektu,
  a razem nie zmieszczą się w oknie jednej sesji; paczka drobnych poprawek
  po kilka linii to jedna sesja, nie flota, choćby było ich dziesięć;
- robota ma trwać dłużej niż jedna sesja albo iść bez nadzoru (noc);
- zmiana przecina kilka warstw naraz (schemat, funkcja, front) z kontraktem
  między nimi.

Poprawka, którą da się opisać jednym zdaniem i zamknąć jednym diffem, idzie
zwykłą drogą repo: celowana zmiana w tej sesji, bramki repo, bez planu
i floty. Wtedy mówisz Serge'owi jednym zdaniem, że foreman tu nie pasuje
i dlaczego, i robisz zmianę sam.

**Warunek ukończenia, zanim cokolwiek przeczytasz.** Z polecenia piszesz go
od razu i pokazujesz Serge'owi w jednej wiadomości: droga użytkownika jednym
zdaniem (kto, co robi, co widzi na końcu), dwa do pięciu kryteriów odbioru,
każde z odczytem i oczekiwanym wynikiem (komenda, zapytanie, liczba z DOM-u),
i czego robota nie obejmuje. „Testy zielone" ani „zaimplementowane X" nie są
kryterium: mówią o kodzie, nie o drodze. To jedyne pytanie przed startem, bo
intencja należy do Serge'a; akceptuje albo poprawia. Bez odpowiedzi jedziesz
na szkicu oznaczonym w planie jako założenie, a przelot bez zaakceptowanego
warunku się nie zaczyna. Rozpoznanie może warunek zmienić; zmiana idzie do
meldunku z powodem.

### 1. Rozpoznanie (osobiście)

Plan zbudowany na cudzym streszczeniu dziedziczy cudze przeoczenia, więc kod,
którego dotyczy zmiana, czytasz sam: `grep` po nazwach, zakresy po kilkanaście
linii, dane przenoszone drutem do pliku. Szukasz:

- **precedensu**: czy repo już robi to samo gdzie indziej; sprawdzony kształt
  bije nowy;
- **bramek**: rejestry, allowlisty, mapy handlerów; nowa powierzchnia
  niedopisana do bramki jest niewidoczna dokładnie tam, gdzie ma działać;
- **liczb**: limity, sufity, objętości zmierzone zapytaniem; próg z jednego
  klienta sprawdzony starym i nowym kodem na całym zbiorze (LC-094);
- **materiału pomiaru**: gdy robota domyka pętlę „napraw → zmierz ponownie",
  co jest materiałem pomiaru, kto go odświeża i czy użytkownik ma ten krok na
  ekranie (LC-111);
- **czytelników**: gdy zmiana czyści albo przelicza pole, każdy, kto je czyta,
  i co robił z brudem; pierwsi ci, którzy na słabym sygnale tworzą dane
  (LC-104);
- **wspólnych zasobów**: baza, port, karta przeglądarki; ograniczenie dostaje
  każdy żyjący piszący, nie tylko następny spawn (LC-029).

Gotowe, gdy każdy punkt planu opiera się na `file:line` albo na liczbie
z zapytania.

### 2. Plan jako graf

Plan w pliku, w kolejności: warunek ukończenia z kroku 0, problem, architektura z **odrzuconymi wariantami
i powodem**, findingi z `file:line`, kontrakt tego, co powstaje, mapa pokrycia
testami, tryby awarii, zakres poza pracą, **graf zadań**.

Zadanie w grafie to lista plików z jednym właścicielem, model wykonawcy
z uzasadnieniem w pół zdania, zadania, od których zależy, i komenda
weryfikacji. Każde zadanie po scaleniu zostawia gałąź integracyjną zieloną;
zmiany zielone dopiero razem (schemat i jego konsument) są jednym zadaniem.
Dwa zadania w jednym pliku to konflikt, który wyjdzie dopiero przy scaleniu:
dziel po właścicielu pliku, nie po temacie.

Model dobierasz do ciężaru zadania, nie do wagi tematu. Wątpliwość rozstrzyga
koszt pomyłki: tania i głośna → `sonnet`, droga albo cicha → `opus`.

Plan wskazuje też **szew sesji**: punkt, w którym powstaje notatka startowa
następnej sesji, gdyby okno albo limit się skończyły.

### 3. Recenzja planu innym modelem

Przegląd inżynierski właściwy dla repo, potem Codex:
`codex exec -s read-only -c 'model_reasoning_effort="high"' "<pytania>" < plan.md`.
Model idzie z `~/.codex/config.toml`, jedynego miejsca jego wyboru; `high`, bo
recenzja jest adwersarialna, a `xhigh` na długim kontekście wisi dziesiątki
minut. Plan idzie na stdin, bo sandbox nie zawsze widzi pliki spoza repo,
a treść wklejona w cudzysłów psuje się na cudzysłowach i limicie argumentów.
Zakaz zapisu daje sandbox `-s read-only`, nie prompt: modele OpenAI obchodzą
słowną odmowę dostępu w większości prób. Stałe pytania: gdzie plan
kopiuje wzorzec repo i czy ten wzorzec jest poprawny; czy kontrakt między
zadaniami jest jednoznaczny dla dwóch wykonawców; czego plan nie wymienia,
a co zepsuje produkcję (konsument schematu, stare wiersze, bramka CI);
które kryterium odbioru przejdzie przy niedziałającej drodze użytkownika.

Każdy finding weryfikujesz w kodzie; odrzucony dostaje powód. Przyjęte
wtapiasz w plan i przepisujesz go jako stan: plan wygląda, jakby powstał dziś.

### 4. Przygotowanie gałęzi

W głównym klonie: gałąź integracyjna z aktualnego `main`, checkout na nią.
Worktree agentów wyrastają z `HEAD`, więc repo potrzebuje w
`.claude/settings.local.json` wpisu `{"worktree": {"baseRef": "head"}}`,
a `.gitignore` wpisu `.claude/worktrees/`. Pliki gitignorowane, których
wymagają testy, wchodzą przez `.worktreeinclude`, wyłącznie w wersji lokalnej
albo testowej: sekrety produkcji zostają u Ciebie, bo strażnik komend łapie
pomyłki, a nie każdą drogę do zdalnej zmiany. Zależności instaluje agent
w swoim worktree komendą instalacji repo.

Porównaj cwd sesji z katalogiem repo planu i powiedz wynik na głos: sesja
spoza repo nie ma jego hooków (LC-084). Pułapki worktree i środowiska:
[PULAPKI.md](PULAPKI.md).

### 5. Pętla frontu

**Front** to zadania, których zależności są scalone. Pętla:

1. Każde zadanie frontu dostaje spawn: `Agent` z
   `subagent_type: "foreman-wykonawca"`, `model` z grafu,
   `run_in_background: true`, wszystkie w jednym komunikacie. Naraz żyje
   najwyżej trzech agentów; reszta frontu czeka na wolne miejsce. Przy
   spawnie zapisujesz w planie SHA gałęzi integracyjnej.
2. Na powiadomienie o końcu zadania robisz **odbiór** w ścieżce worktree
   z wyniku agenta:
   - `git merge-base --is-ancestor <SHA ze spawnu> HEAD`: worktree wyrósł
     z integracji, nie z `main`;
   - `git diff --name-only <SHA ze spawnu>...HEAD` mieści się w liście plików
     zadania; plik spoza listy oblewa odbiór;
   - komenda weryfikacji z grafu i sekcja odejść od planu.
   Raport agenta to hipoteza (LC-077); dowodem jest Twój przebieg komend.
   Agent, który przekroczył swój limit tur albo milczy dłużej niż dwukrotność
   najdłuższego zaliczonego zadania, dostaje `TaskStop` i liczy się jako
   niezaliczony odbiór.
3. Odbiór zaliczony → `git merge --no-ff <gałąź agenta>` w głównym klonie,
   weryfikacja pełna na gałęzi integracyjnej, przeliczenie frontu, spawn.
   Konflikt scalenia oznacza błąd w podziale grafu: przerywasz merge, ten sam
   agent przez `SendMessage` wciąga gałąź integracyjną do swojej i rozwiązuje
   konflikt skillem `resolving-merge-conflicts`, a plan dostaje poprawkę podziału.
4. Odbiór niezaliczony → poprawka u **tego samego** agenta przez
   `SendMessage` z dowodem (wynik komendy, `file:line`). Kontekst pierwszego
   przebiegu jest wart więcej niż świeży start.
5. **Drabina modelu:** zadanie na `sonnet` po dwóch niezaliczonych odbiorach
   idzie do nowego wykonawcy na `opus` z oboma raportami i dowodami. Na `opus`
   po dwóch niezaliczonych kończy zadanie jako **blokadę**: wpis w planie „czego
   brakuje, co próbowano". Zadania zależne od zablokowanego też są blokadą,
   pozostałe gałęzie grafu idą dalej.

Odejście od planu z dobrym powodem to luka w planie: poprawiasz plan.
Odejście bez powodu to robota do zwrotu. Mała prośba, która odsłania dług,
jest punktem decyzyjnym dla Serge'a, nie zleceniem na cały dług; robota
przekraczająca dwukrotność zapowiedzi wraca po decyzję (LC-036).

Pętla kończy się, gdy każde zadanie grafu jest scalone albo opisane jako
blokada, a pełna weryfikacja na gałęzi integracyjnej przechodzi.

### 6. Odbiór świeżym okiem

`foreman-recenzent` ma tylko narzędzia odczytu, więc diff przygotowujesz Ty:
`git diff <SHA main>...<gałąź integracyjna> > <katalog sesji>/diff.patch`.
Dostaje wskaźniki: plan, plik diffu, katalog repo. Czyta diff bez transkryptów
wykonawców i ocenia trzy osie: zgodność
z planem, standardy repo, **prawdziwość tekstów widocznych dla użytkownika**
we wszystkich gałęziach kodu, które je produkują. Findingi weryfikujesz
w kodzie jak findingi Codexa; przyjęte wracają do pętli frontu jako nowe
zadania.

Zmiana dotykająca ekranu dostaje odbiór na żywo: dev serwer z gałęzi
integracyjnej, dane z tego samego źródła co produkcja, kryteria odczytane
z DOM-u liczbami.

### 7. Brama i wdrożenie

Brama repo w kolejności, którą repo definiuje: jego `verify` albo bramki
z `AGENTS.md`/`CLAUDE.md`, przegląd diffu, `/codex challenge` na diffie gałęzi
integracyjnej jako drugie oko z innej rodziny modeli. Flota, która
raportowała sukces, nie widziała kodu pozostałych zadań, więc brama biegnie
w całości.

Push i PR kończą każdy przebieg. Merge do `main` i wdrożenie idą dalej tylko
wtedy, gdy wymienia je mandat albo słowo Serge'a w tej sesji, a graf nie ma
blokad; w każdym innym przypadku przebieg kończy się na PR z listą blokad
i tym, co czeka na decyzję.

Smoke idzie drogą produkcji: ten sam starter, ładunek z tego samego źródła,
odczyt wyniku z miejsca, w którym zapisuje go produkcja. Dowodem wdrożenia
jest odczyt żywego stanu (wersja funkcji, wiersz w bazie).

Meldunek idzie po kryteriach odbioru: przy każdym odczyt, który je
potwierdził, albo powód, dla którego nie przeszło.

Robota kończy się meldunkiem według reguły globalnej i sprzątniętym
stanowiskiem: worktree agentów zdjęte (`git worktree list` pokazuje tylko
główny klon), gałęzie agentów skasowane, plan skasowany albo przepisany
w dokumentację stanu.

## Brief

Brief opisuje warunki, nie czynności: agent dochodzi do rozwiązania sam, Ty
zamykasz mu drogi do rozwiązań złych. Stałe reguły (commity, raport,
komentarze, zakazy) niesie definicja typu agenta; brief niesie tylko to:

```
Zadanie <nazwa z grafu> z planu <ścieżka>, sekcja <nagłówek>. Przeczytaj
plan w całości przed pierwszą linijką kodu.

Twoje pliki: <lista>. Pozostałe pliki należą do innych zadań.

Warunki:
- <warunek> — bo <powód liczbowy albo file:line>
- wzorzec: <plik:linia>, kanoniczny kształt tego w repo
- <pułapka> — <dlaczego kusi i czemu nie działa>

Weryfikacja: <dokładne komendy>
```

Każdy warunek niesie powód: „parser strict" agent obejdzie przy pierwszym
błędzie, „parser strict, bo domyślny domyka urwany JSON i zamienia urwanie
w częściową czystość" przetrwa. Komendy weryfikacji są dokładne, nie
„uruchom testy". Treść planu przekazujesz wskaźnikiem, nie kopią.

## Przelot bez nadzoru

Gdy przy bramkach nie stoi człowiek, przed pierwszym spawnem przeczytaj
[PRZELOT.md](PRZELOT.md): mandat, droga odbioru sprawdzona jako operator,
liczniki i budziki. Bez spisanego mandatu przelot się nie zaczyna.

## Czego nie dokładać

Zmieniają wynik: plan recenzowany innym modelem, odbiór świeżym kontekstem,
smoke drogą produkcji. Zmierzone i wycięte (LC-092): `tdd` jako skill
wykonawcy, `freeze` i `canary`, bramka „pierwszy test zadania N+1 na
artefakcie N". Z dokumentacji, nie z pomiaru: agent teams (eksperymentalne,
droższe, bez wznowienia po przerwie) i narzędzie Workflow (skrypt po starcie
nie przyjmuje poprawki przez `SendMessage`). Dokładając cokolwiek z tej listy,
nazwij dowód, którego wtedy brakło.

## Kiedy nie używać

Robota spoza kryteriów kroku 0: zrób ją sam. Zakres mglisty: najpierw doprecyzuj,
bo flota na mgłę daje trzy interpretacje równolegle. Robota wymagająca
rozmowy z Serge'em w trakcie: subagent nie ma z kim rozmawiać.
