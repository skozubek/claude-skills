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

Flota to trzy typy agentów z `~/.claude/agents/`. Definicja niesie model,
worktree, strażnika komend, stałe reguły pracy i kształt raportu, więc brief
niesie tylko to, co specyficzne dla zadania:

- `foreman-wykonawca` pisze kod jednego zadania we własnym worktree;
- `foreman-recenzent` odbiera całość świeżym okiem, tylko do odczytu;
- `foreman-weryfikator` przechodzi ekrany na żywo (AdMotiv, krok 6), bez edycji.

Brygadzista to sesja na `opus`. Jego kontekst rośnie przez cały przelot
i każda odpowiedź płaci za całość, więc najdroższy model w tej roli mnoży
koszt bez dowodu lepszej orkiestracji; `fable` tylko na słowo Serge'a.

Model wykonawcy dobierasz per zadanie parametrem `model` w wywołaniu `Agent`:

| Model | Zadanie |
|---|---|
| `sonnet` | jednoznaczne, sprawdzalne kryterium i istniejący wzorzec w repo: dokumentacja techniczna, przeniesienia, predykaty, asercje, powtórzenie kształtu, który już stoi |
| `opus` (domyślny w definicji) | ścieżka krytyczna: schemat, autoryzacja, prompty LLM, nowy kształt; tekst, który czyta klient albo ocenia sędzia; każde zadanie, w którym zły wybór jest drogi i cichy |
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

**Warunek ukończenia, zanim cokolwiek przeczytasz.** Z samego polecenia
piszesz go od razu i pokazujesz Serge'owi. Ma trzy części:

- **droga użytkownika** jednym zdaniem: kto, co robi, co widzi na końcu;
- **kryteria odbioru**, od dwóch do pięciu. Każde mówi, co odczytać (komenda,
  zapytanie, liczba na ekranie) i jaki wynik ma wyjść. „Testy zielone” to nie
  kryterium, bo mówi o kodzie, a nie o tym, co widzi użytkownik.
  Kryterium, które potrzebuje zdarzeń spoza przelotu (ruch użytkowników
  w systemie źródłowym), dostaje w planie okno i próg przed pierwszym wynikiem;
  bez zdarzeń w oknie jest „niezweryfikowane”, nie zaliczone, i zostaje
  blokadą z zadaniem;
- **czego robota nie obejmuje**.

To jedyne pytanie o zakres przed startem, bo to Serge wie, czego chce. Akceptuje albo
poprawia. Jeśli nie odpowie, jedziesz na swoim szkicu i zapisujesz go w planie
jako założenie. Przelot nocny bez zaakceptowanego warunku się nie zaczyna.
Jeśli rozpoznanie zmieni warunek, meldunek mówi, co się zmieniło i dlaczego.

### 1. Rozpoznanie (osobiście)

Plan zbudowany na cudzym streszczeniu dziedziczy cudze przeoczenia, więc kod,
którego dotyczy zmiana, czytasz sam: `grep` po nazwach, zakresy po kilkanaście
linii, dane przenoszone drutem do pliku. Szukasz:

- **precedensu**: czy repo już robi to samo gdzie indziej; sprawdzony kształt
  bije nowy. Klocek, na którym stawiasz kontrakt (zapis ustawień, panel,
  przekierowanie), sprawdzasz odczytem skutku na żywo (wiersz w bazie,
  szerokość na docelowym ekranie), nie lekturą: klocek w repo bywa martwy od
  miesięcy (CRM B1: zapis wyborów tabel bez wysłania żądania, 0 wierszy).
  Pole z obcego systemu, na którym plan opiera regułę (czas, status,
  identyfikator z synchronizacji), czytasz w kodzie, który je wylicza, i cytujesz
  `file:line`: nazwa pola to hipoteza (CRM B3: „wejście leada” z HubSpota to
  pierwsze NEW/OPEN w historii, nie ponowne, cztery rundy poprawek przejęcia);
- **bramek**: rejestry, allowlisty, mapy handlerów; nowa powierzchnia
  niedopisana do bramki jest niewidoczna dokładnie tam, gdzie ma działać;
- **liczb**: limity, sufity, objętości zmierzone zapytaniem; próg z jednego
  klienta sprawdzony starym i nowym kodem na całym zbiorze (LC-094); testy
  repo z twardym progiem czasu albo pamięci (`grep -rnE "toBeLessThan|performance\.now"`
  po plikach testów) z zapasem wobec `main`: test „czerwony pod obciążeniem,
  osobno przechodzi” to dług, który oblewa CI w następnym przelocie;
- **materiału pomiaru**: gdy robota domyka pętlę „napraw → zmierz ponownie",
  co jest materiałem pomiaru, kto go odświeża i czy użytkownik ma ten krok na
  ekranie (LC-111);
- **czytelników**: gdy zmiana czyści albo przelicza pole, każdy, kto je czyta,
  i co robił z brudem; pierwsi ci, którzy na słabym sygnale tworzą dane
  (LC-104);
- **wspólnych zasobów**: baza, port, karta przeglądarki; ograniczenie dostaje
  każdy żyjący piszący, nie tylko następny spawn (LC-029).
- **danych przenoszonych**: zmiana, która kopiuje dane z obcego systemu
  (import, lustro), ma w planie odpowiedź, co przenosi (treść notatek, maili,
  załączników) i kto zobaczy to po stronie docelowej i w raportach; dane
  dostępowe klientów i dane wrażliwe to decyzja Serge'a przed pierwszym
  odczytem na produkcji (CRM fala A: hasła klientów z notatek HubSpota na osi
  czasu dla całej roli sprzedaży, stop przelotu po wdrożeniu).
- **mapy funkcji** (AdMotiv): plik modułu z `MOL/Panel/meta/mapa/` przed kodem,
  `verify-admotiv/bin/doctor <moduł>` pokazuje cudze zmiany od ostatniego
  przejścia; kryteria odbioru planu to wpisy mapy, a nowe zachowanie ekranu
  dostaje w grafie zadanie „dopisz wpis mapy”; czytelnicy ekranu to też
  jego opakowanie (strona z h1 i opisem pod tytułem, pozycja menu, ścieżka,
  pomoc „?”), nawet gdy diff ich nie dotyka; wznawiając cudzy plan, przed
  pierwszym spawnem sprawdzasz graf wobec tego punktu i czytelników, a nazwy
  tabel i pól kontraktu jednym zapytaniem do schematu (CRM B3: kontrakt
  z kolumnami, których nie ma);
- **słownika**: gdy zmiana dotyka modelu danych albo pojęć, które widzi
  użytkownik, moduł ma `CONTEXT.md` (skill `domain-modeling`: definicja
  w dwóch zdaniach, lista „unikaj”, zero implementacji) zrobiony PRZED planem,
  po researchu, z Serge'em w pętli; sam wybierasz złe słowo i idziesz dalej
  (CRM 13.10: „zgłoszenie” zamiast „lead”). Scenariusze z nazwiskiem
  i godziną wyciągają decyzje, których research nie da (upsell bez leada,
  kto zamyka przypomnienie). Nazwa ekranu, pozycji menu albo ścieżki ze słowem z listy „unikaj” to
  zadanie w grafie (zmiana nazwy z przekierowaniem starej ścieżki), a nie
  uwaga recenzenta: grep idzie po całym ekranie, nie po diffie (CRM fala A:
  ekran „Zapytania” przeżył falę, choć słownik mówi „lead”). Plan i brief
  używają słów ze słownika, a
  `AGENTS.md` modułu każe go czytać każdemu agentowi przed zmianą modelu.

Błąd ze zrzutu albo opisu człowieka: przed spawnem jedno pytanie o warunki,
których zrzut nie niesie (zoom, szerokość okna, co było rozwinięte, produkcja
czy lokalnie); wykonawca bez nich mierzy stan, w którym błędu nie ma (CRM B2:
przewijanie strony od zoomu, 20 min pomiaru bez odtworzenia).

Gotowe, gdy każdy punkt planu opiera się na `file:line` albo na liczbie
z zapytania.

### 2. Plan jako graf

Plan w pliku, w kolejności: warunek ukończenia z kroku 0, problem, architektura z **odrzuconymi wariantami
i powodem**, findingi z `file:line`, kontrakt tego, co powstaje, mapa pokrycia
testami, tryby awarii, zakres poza pracą, **graf zadań**.

Łączenie albo deduplikacja zdarzeń z kilku źródeł ma w planie jawną
definicję tożsamości zdarzenia (co czyni dwa wejścia tym samym) i test każdej
kolejności przybycia; reguła rozpisana na gałęzie per kolejność odsłania przy
każdej poprawce następną kolejność (CRM B3).

Zadanie w grafie to lista plików z jednym właścicielem, model wykonawcy
z uzasadnieniem w pół zdania, zadania, od których zależy, spodziewany czas,
komenda weryfikacji i **czytelnicy** jego pól poza jego plikami (komponent
renderujący, eksport, drugi dom tej samej reguły). Każde zadanie po scaleniu
zostawia gałąź integracyjną zieloną; zmiany zielone dopiero razem (schemat
i jego konsument) są jednym zadaniem. Dwa zadania równoległe w jednym pliku
to konflikt przy scaleniu: dziel po właścicielu pliku; kolejne w tym samym
pliku rozdziela zależność. Numery migracji i wpisów decyzji w grafie są
robocze: ostateczne nadajesz w kroku 7, po wciągnięciu `main`. Zadanie, które
pisze pomoc, opisy ekranów albo komunikaty, ma w grafie listę „działa po tym
PR-ze / przychodzi później”, a brief ją niesie; zależy od każdego zadania,
które opisywane zachowanie zmienia, nie tylko od tego, które je buduje (CRM
B2: dokumenty równolegle z wpięciem list opisały plan zamiast kodu).

Model dobierasz do ciężaru zadania, nie do wagi tematu. Wątpliwość rozstrzyga
koszt pomyłki: tania i głośna → `sonnet`, droga albo cicha → `opus`. Masowa
zmiana oceniana sędzią (setki tekstów) zaczyna od próbki: wynik poniżej
progu na próbce przenosi zadanie na `opus`, zanim tańszy model przerobi
całość.

Plan ustala też **granice PR-ów** (zadanie, front albo całość) i zależności
między nimi, a zadanie ustalające kontrakt, z którego biorą następne fronty,
dostaje recenzenta świeżym okiem zaraz po scaleniu, nie dopiero na końcu.

### 3. Recenzja planu innym modelem

Plan zmieniający wygląd albo układ ekranów ma w kryteriach odbioru wzorzec
z repo (klocek tabeli, panelu, filtrów) i sąsiednie ekrany, z którymi ma być
spójny; „jak w systemie X” bez tego nie jest kryterium. Przegląd inżynierski
właściwy dla repo, potem Codex:
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
które kryterium odbioru przejdzie przy niedziałającej drodze użytkownika;
czy źródło gwarantuje kompletność odczytu, zanim nieobecność rekordu
uruchomi usunięcie albo archiwum (brak na liście to nie sygnał usunięcia).

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

Zadania równoległe, które dzielą typy albo komponent, dostają kontrakt
w kodzie: przed spawnem wstawiasz na gałąź integracyjną typy (np. funkcji
bazy) i szkielet komponentu z sygnaturą z planu, osobnym commitem; właściciel
szkieletu go wypełnia, reszta kompiluje się na nim od pierwszej minuty (CRM
B2: baza, środek i rekord ruszyły razem). Recenzent świeżym okiem idzie zaraz
po scaleniu pierwszych implementacji kontraktu, przed zadaniami, które z nich
biorą.

Porównaj cwd sesji z katalogiem repo planu i powiedz wynik na głos: sesja
spoza repo nie ma jego hooków (LC-084). Pułapki worktree i środowiska:
[PULAPKI.md](PULAPKI.md).

### 5. Pętla frontu

**Front** to zadania, których zależności są scalone. Pętla:

1. Każde zadanie frontu dostaje spawn: `Agent` z
   `subagent_type: "foreman-wykonawca"`, `model` z grafu,
   `run_in_background: true`, wszystkie w jednym komunikacie. Naraz żyje
   najwyżej trzech agentów; reszta frontu czeka na wolne miejsce. SHA
   gałęzi integracyjnej przy spawnie, nazwę gałęzi i worktree agenta
   zapisujesz w pliku sesji w katalogu tymczasowym: to rejestr własności
   tego przelotu, z którego korzysta odbiór i sprzątanie. Ten sam plik
   dostaje każdą inną rzecz, którą przelot stawia (budzik, `/coffee`,
   proces w tle, konto testowe, gałąź PR), w chwili jej postawienia.
2. Na powiadomienie o końcu zadania robisz **odbiór** w ścieżce worktree
   z wyniku agenta:
   - `git merge-base --is-ancestor <SHA ze spawnu> HEAD`: worktree wyrósł
     z integracji, nie z `main` (brief każe agentowi zacząć od
     `git merge --ff-only <SHA ze spawnu>`, bo worktree potrafi wyrosnąć ze
     starszego commita niż zapisany SHA);
   - `git diff --name-only <SHA ze spawnu>...HEAD` mieści się w liście plików
     zadania; plik spoza listy oblewa odbiór;
   - komenda weryfikacji z grafu i sekcja odejść od planu.
   Raport agenta to hipoteza (LC-077); dowodem jest Twój przebieg komend,
   zapisany jako komenda, SHA i wynik. Ten sam dowód na tym samym SHA nie
   biegnie drugi raz.
   Agent, który przekroczył swój limit tur albo pracuje dłużej niż dwukrotność
   czasu z grafu (bez przerw sieci i limitu), dostaje `TaskStop` i liczy się
   jako niezaliczony odbiór.
3. Odbiór zaliczony → `git merge --no-ff <gałąź agenta>` w głównym klonie,
   przeliczenie frontu, spawn. Pełna weryfikacja integracji biegnie po
   zamknięciu frontu i przed PR-em, a po pojedynczym scaleniu tylko wtedy,
   gdy zadanie dotknęło plików albo kontraktu innego scalonego zadania.
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
Odejście, które zmienia kontrakt (pole, nazwa, kardynalność), przyjmujesz
dopiero po wskazaniu czytelników tej części kontraktu w grafie i poprawieniu
ich briefów. Odejście bez powodu to robota do zwrotu. Mała prośba, która odsłania dług,
jest punktem decyzyjnym dla Serge'a, nie zleceniem na cały dług; robota
przekraczająca dwukrotność zapowiedzi wraca po decyzję (LC-036).

Pętla kończy się, gdy każde zadanie grafu jest scalone albo opisane jako
blokada, a pełna weryfikacja na gałęzi integracyjnej przechodzi.

Twój kontekst to największa pozycja kosztu przelotu: każda odpowiedź czyta
go od nowa. Wyniki komend idą drutem do pliku, a do rozmowy liczby; raport
agenta czytasz, transkryptu nie.

### 6. Odbiór świeżym okiem

`foreman-recenzent` ma tylko narzędzia odczytu, więc diff przygotowujesz Ty:
`git diff <SHA main>...<gałąź integracyjna> > <katalog sesji>/diff.patch`.
Dostaje wskaźniki: plan, plik diffu, katalog repo. Czyta diff bez transkryptów
wykonawców i ocenia trzy osie: zgodność
z planem, standardy repo, **prawdziwość tekstów widocznych dla użytkownika**
we wszystkich gałęziach kodu, które je produkują, **łącznie z pomocą „?”
i opisami ekranów, których dotyka diff** — pomoc leży poza diffem, więc
recenzent dostaje jej ścieżki wprost, a zmiana zachowania ekranu poprawia
jego pomoc w tym samym przelocie (fala 4 SEO/GEO: pomoc on-site dalej
uczyła „Stwórz zadania” po jego usunięciu). Findingi weryfikujesz
w kodzie jak findingi Codexa; przyjęte wracają do pętli frontu jako nowe
zadania.

Zmiana dotykająca ekranu dostaje odbiór na żywo: dev serwer z gałęzi
integracyjnej, dane z tego samego źródła co produkcja, kryteria odczytane
z DOM-u liczbami. W AdMotiv odbiór robi agent `foreman-weryfikator`, nie wykonawca:
skill `verify-admotiv` na krokach mapy z obszarów, które wskazuje
`bin/doctor` dla gałęzi integracyjnej (tylko one, budżet idzie za diffem);
ten sam krok przechodzi smoke na produkcji. Weryfikator mapy nie edytuje:
dopiski „przeszło na żywo” i wiersz `przejscia.tsv` wpisuje się z jego raportu
(treść kroków mapy może z kodu napisać osobny agent po scaleniu ostatniego
zadania ekranu). Gdy zmiana ma migrację, a dev serwer czyta produkcyjną bazę,
migracja trafia tam dopiero po mergu: przed nim odbiór na żywo przechodzi
kroki odczytu, a zapis dowodzą testy SQL na kopii; kroki zapisu przechodzą
po mergu i migracji na rekordach testowych z Granic, a niezaliczony krok to
PR poprawkowy, nie cofnięcie (CRM B2).

Gdy moduł ma `CONTEXT.md`, recenzent grepuje etykiety ekranów, nazwy kolumn
i komunikaty po liście „unikaj” ze słownika: słowo stamtąd w kodzie to
rozjazd pojęć, nie styl.

### 7. Brama i wdrożenie

Brama repo w kolejności, którą repo definiuje: jego `verify` albo bramki
z `AGENTS.md`/`CLAUDE.md`, przegląd diffu, `/codex challenge` na diffie gałęzi
integracyjnej jako drugie oko z innej rodziny modeli. Przed PR-em, po
wciągnięciu `main`, nadajesz ostateczne numery migracji i wpisów decyzji
(wyższe niż na `main`) i poprawiasz ich odsyłacze. Flota, która
raportowała sukces, nie widziała kodu pozostałych zadań, więc brama biegnie
w całości.

Push i PR kończą każdy przebieg, w granicach PR-ów z planu. PR po squash
merge'ach poprzedników budujesz z gałęzi integracyjnej po wciągnięciu `main`
merge'em, nigdy z gałęzi agenta: ta niesie zmiany, które `main` ma już
w squashu, i daje konflikt na tych samych liniach (MOL/Panel/meta/LEKCJE.md
2026-10-11). Merge do `main` i wdrożenie idą dalej tylko
wtedy, gdy wymieniają je granice planu albo słowo Serge'a w tej sesji, a graf nie ma
blokad; w każdym innym przypadku przebieg kończy się na PR z listą blokad
i tym, co czeka na decyzję.

Smoke idzie drogą produkcji (ekran AdMotiv: `verify-admotiv/bin/sesja --prod`
na opublikowanym froncie): ten sam starter, ładunek z tego samego źródła,
odczyt wyniku z miejsca, w którym zapisuje go produkcja. Dowodem wdrożenia
jest odczyt żywego stanu (wersja funkcji, wiersz w bazie).

Meldunek idzie po kryteriach odbioru: przy każdym odczyt, który je
potwierdził, albo powód, dla którego nie przeszło.

### 8. Sekcja zwłok i sprzątanie

Przed sprzątaniem, póki przelot jest w kontekście: [POSTMORTEM.md](POSTMORTEM.md).
Wynik wchodzi do skilla jednym commitem i do meldunku sekcją „Skill”.

Robota kończy się meldunkiem według reguły globalnej i sprzątniętym
stanowiskiem. Przelot zostawia rzeczy, które przeżyją sesję albo ją obudzą,
więc rejestr własności wymienia każdą, a sprzątanie odhacza je po kolei:

- worktree i gałęzie agentów, gałąź integracyjna i gałęzie PR-ów, lokalnie
  i na zdalnym (merge z `--delete-branch`), po sprawdzeniu, że nie mają
  niezacommitowanej pracy; cudzych nie ruszasz, także w klonie dzielonym;
- budziki `CronCreate` usunięte (`CronDelete`): sesja zostaje otwarta i budzik
  odpalony po przelocie wznawia robotę, której już nie ma;
- `/coffee off`: zadanie launchd trzyma Maca bez snu po końcu sesji;
- procesy uruchomione przez przelot (dev serwer, daemon przeglądarki),
  sesje i dostępy nadane na czas odbioru;
- plan skasowany albo przepisany w dokumentację stanu, materiał sekcji zwłok
  i pliki w katalogu tymczasowym skasowane.

## Brief

Brief opisuje warunki, nie czynności: agent dochodzi do rozwiązania sam, Ty
zamykasz mu drogi do rozwiązań złych. Stałe reguły (commity, raport,
komentarze, zakazy) niesie definicja typu agenta; brief niesie tylko to:

```
Zadanie <nazwa z grafu> z planu <ścieżka>, sekcja <nagłówek>. Zacznij od
`git merge --ff-only <SHA ze spawnu>`. Przed pierwszą linijką kodu przeczytaj
w planie: Granice, kontrakt, swoje zadanie i zadania, od których zależysz.
Resztę planu czytasz, gdy jej potrzebujesz.

Twoje pliki: <lista>. Pozostałe pliki należą do innych zadań.
Czytelnicy Twoich pól poza Twoimi plikami: <lista z grafu>.

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

Gdy przy bramkach nie stoi człowiek albo sesja biegnie w trybie bypass lub
auto (hooki odmawiają wtedy zamiast pytać, także przy człowieku obok), przed
pierwszym spawnem przeczytaj [PRZELOT.md](PRZELOT.md): granice w planie,
droga odbioru sprawdzona jako operator, liczniki i budziki. Bez sekcji „Granice” w planie przelot się nie
zaczyna.

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
