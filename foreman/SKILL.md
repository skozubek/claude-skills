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

Wariant wykonawcy (model i effort) dobierasz per zadanie parametrami `model`
i `effort` w wywołaniu `Agent`; definicja niesie `opus` z effortem `medium`:

| Wariant | Parametry | Zadanie |
|---|---|---|
| sonnet | `model: "sonnet"` | jednoznaczne, sprawdzalne kryterium i istniejący wzorzec w repo: dokumentacja techniczna, przeniesienia, predykaty, asercje, powtórzenie kształtu, który już stoi |
| opus medium | bez parametrów | domyślny: logika w istniejącym kształcie, komponent wg kontraktu, testy, poprawki z recenzji |
| opus high | `effort: "high"` | schemat, RLS i uprawnienia, prompty LLM, nowy kontrakt, logika stanu albo współbieżności; tekst, który czyta klient albo ocenia sędzia; kryterium, które rozstrzyga zgodność sensu (wniosek a reguła, obietnica a ekran), a nie trafienie grepa; każde zadanie, w którym zły wybór jest drogi i cichy |
| fable | `model: "fable"` | wyłącznie na wyraźne słowo Serge'a przed spawnem |

Tańszy wariant, który kręci się w kółko, kosztuje więcej niż mocniejszy,
który kończy, więc wariant ocenia rejestr przelotu, nie intuicja: każde
zadanie zapisuje wariant, liczbę rund poprawek (niezaliczone odbiory
i wznowienia po odbiorze), liczbę findingów recenzji i E całego zadania
z `koszty.py` (wszyscy jego wykonawcy). Reguła ustalona przed pierwszym
wynikiem, oceniana od trzech zadań wariantu w kategorii (schemat, logika,
ekran, teksty, dokumentacja): kategoria, w której opus medium ma wyższe
średnie E zadania albo więcej findingów recenzji niż opus high, wraca na
high; kategoria, w której sonnet kosztuje średnio więcej dolarów na zadanie
niż opus medium (E razy cena za mln wejścia: sonnet 3, opus 5) albo ma
więcej findingów, wraca na opus. Wnioski idą do tej tabeli.

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

- **księga obietnic**, gdy przelot jest falą planu nadrzędnego (plan budowy,
  tabela „X → w naszym systemie”): każdy wiersz i każde zdanie planu
  nadrzędnego przypisane do tej fali dostaje werdykt „dowozi (kryterium nr)”,
  „przenosi do fali X (z pozycją tam)” albo „rezygnacja (wpis AD)”. Wiersz bez
  werdyktu blokuje plan; Codex recenzuje plan razem z księgą. Obietnica „1:1
  z ekranem X” dostaje jako pierwsze zadanie inwentarz klocków oryginału
  (zakładki, kontrolki, drill, podpisy) i kryterium „każdy klocek jest albo
  celowo inaczej”; liczby to osobne kryterium. (CRM C: plan fali przepisał
  „ekran 1:1” na „te same liczby”, pięć obietnic planu budowy zniknęło bez
  śladu, a każdy strażnik niżej pilnował już zawężonego zakresu.)
  Obietnica nazwana modułem („klient ma CRM”) rozpisuje się w księdze na
  ekrany modułu z menu wzorca, każdy z werdyktem (fala RASC: droga „biuro
  otwiera Leady” zostawiła bez werdyktu Dziś, Raporty i Ustawienia). <!-- LC-114 -->

- **droga użytkownika** jednym zdaniem: kto, co robi, co widzi na końcu;
- **kryteria odbioru**, od dwóch do pięciu. Każde mówi, co odczytać (komenda,
  zapytanie, liczba na ekranie) i jaki wynik ma wyjść. „Testy zielone” to nie
  kryterium, bo mówi o kodzie, a nie o tym, co widzi użytkownik.
  Próg czasu mierzysz tym samym narzędziem i kontem, którym odbiór go
  odczyta (przeglądarka, rola z kryterium); pomiar kluczem serwisowym albo
  curl-em to dolna granica, nie próg (przelot po odbiorze CRM: Leady
  „< 0,8 s” z pomiaru kluczem, w przeglądarce 1,5–2,7 s).
  Kryterium, które potrzebuje zdarzeń (wejście leada, przebieg joba, upływ
  progu), dostaje je wywołane w przelocie: rekord testowy wejściem produkcji,
  ręczne uruchomienie joba, który i tak chodzi z crona, zegar przesunięty
  w teście. Wywołanie, które tworzy albo zmienia dane widoczne dla ludzi
  spoza Granic albo może im coś wysłać, idzie tylko z Granic. Okno ruchu
  (próg przed pierwszym wynikiem, bez zdarzeń „niezweryfikowane”) zostaje
  dla kryterium, które mierzy rozkład prawdziwego ruchu: okno użyteczności
  biegnie w tle i nie trzyma przelotu otwartego, okno bezpieczeństwa
  (wyciek, zły adresat, prawdziwy lead w spamie) blokuje (CRM C: odbiór stał
  tydzień na oknach użyteczności, a dostawę przypomnień na leadzie ręcznym
  odłożono razem z nimi);
  kryterium wejścia danych (synchronizacja, import, podłączenie źródła)
  odczytuje rozkład wszystkiego, co weszło w pierwszym przebiegu, nie tylko
  rekord testowy (CRM B: obok jednego spotkania testowego kalendarz wciągnął
  1457 wewnętrznych, rozpisanych do 2040);
  kryterium z progiem jakości (klasyfikator, sędzia, dopasowanie) dzieli
  próg na bezpieczeństwo (szkoda cicha i trudna do cofnięcia: blokuje) i
  użyteczność (niezaliczona to decyzja Serge'a z liczbami, nie blokada);
  jeden próg dla obu kończy się teatrem, gdy model jest bezpieczny, ale
  mniej przydatny, niż zakładano (CRM B3: 0 ze 117 prawdziwych leadów
  w spamie, 73% spamu przy progu 80%);
- **czego robota nie obejmuje**.

To jedyne pytanie o zakres przed startem, bo to Serge wie, czego chce. Akceptuje albo
poprawia. Jeśli nie odpowie, jedziesz na swoim szkicu i zapisujesz go w planie
jako założenie. Przelot nocny bez zaakceptowanego warunku się nie zaczyna.
Jeśli rozpoznanie zmieni warunek, meldunek mówi, co się zmieniło i dlaczego.

### 1. Rozpoznanie (osobiście)

Plan zbudowany na cudzym streszczeniu dziedziczy cudze przeoczenia, więc kod,
na którym stoi kontrakt (schemat, sygnatury, miejsca zapisu stanu), czytasz
sam: `grep` po nazwach, zakresy po kilkanaście linii, dane przenoszone
drutem do pliku. Przegląd wszerz (kto czyta pole, gdzie stoi precedens, które
ekrany dotyka zmiana) zlecasz agentowi `Explore` z `model: "sonnet"`, który
oddaje wnioski z `file:line`, nie treść plików; osobiście sprawdzasz tylko te
trafienia, na których opierasz kontrakt. Własne odczyty to ok. 55% kontekstu
brygadzisty (pomiar 12–20.10), a ten kontekst czyta każda jego następna
odpowiedź. Szukasz:

- **precedensu**: czy repo już robi to samo gdzie indziej; sprawdzony kształt
  bije nowy. Klocek, na którym stawiasz kontrakt (zapis ustawień, panel,
  przekierowanie), sprawdzasz odczytem skutku na żywo (wiersz w bazie,
  szerokość na docelowym ekranie), nie lekturą: klocek w repo bywa martwy od
  miesięcy (CRM B1: zapis wyborów tabel bez wysłania żądania, 0 wierszy).
  Zmianę sposobu wywołania z przeglądarki (nagłówek, region, adres funkcji)
  dowodzi zapytanie wstępne `OPTIONS` z nagłówkami, które wyśle SDK; curl
  POST i atrapa `invoke` tego nie widzą (czasy CRM: `x-region` poza CORS
  zablokowałby Raporty, złapała dopiero recenzja).
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
  i co robił z brudem, na próbce przed i po; pierwsi ci, którzy na słabym
  sygnale tworzą dane
  (LC-104);
- **wspólnych zasobów**: baza, port, karta przeglądarki, limit i kolejka
  funkcji produkcyjnej; ograniczenie dostaje każdy żyjący piszący, nie tylko
  następny spawn (LC-029). Przebieg pomiarowy na funkcji produkcyjnej dzieli
  jej dobowy limit i kolejkę z ruchem użytkowników, więc plan liczy jego
  zużycie wobec limitu (CRM: pomiar klasyfikatora na 333 zgłoszeniach
  wyczerpał limit dnia, a zadania prawdziwych leadów stały w kolejce).
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
każdej poprawce następną kolejność (CRM B3). Kontrakt maszyny stanów
(kolejka, wysyłka, synchronizacja) ma tabelę przejść: stan → zdarzenie →
stan, kto zapisuje, które stany zajmują tożsamość, a które ją zwalniają;
do tego listę wszystkich dróg w kodzie, które zmieniają stan wejściowy
(grep po zapisie), nie tylko drogę z historyjki (CRM D1: dwie rundy
poprawek w PR B i C, ok. 20 E, za brak obu).

Zadanie, które pisze miernik odbioru z listą oczekiwanych różnic, ma
w weryfikacji kontrolę czułości per pozycja listy: po jednym wstrzykniętym
defekcie w kategorii każdej pozycji (rekord, który pasuje do kanału albo pola
pozycji, a jest usterką: spam, zły kierunek, brak dowodu), i każdy wychodzi
jako nieoczekiwany. Kanarek spoza listy tego nie sprawdza: lista tłumaczy
usterkę, która wpada w jej kategorię (CRM C: dwa razy, ostatnio 25
leadów-spamu jako „lead tylko w CRM”).

Zadanie, którego poprawność wymaga atomowości w bazie (odczyt stanu i zapis
w osobnych krokach, warunek zależny od cudzych zdarzeń, ponowienie po
błędzie), wskazuje w grafie istniejący mechanizm, który ją daje (funkcja
transakcyjna, zapis warunkowy), i test współbieżności albo ponowienia. Gdy
mechanizmu brak, a jego dodanie przekracza Granice, zadanie nie wchodzi do
grafu: decyzja Serge'a przed startem (poszerzyć Granice albo wyciąć).
Wariant obok bazy przechodzi testy i pada na recenzji (CRM UI: automat
etapu po rezerwacji w funkcji edge, revert przed mergem).

Zadanie w grafie to jedna warstwa i kilka plików (zwykle 3–5) na około
100 tur wykonawcy. Koszt zadania to tury razy kontekst, więc rośnie
z kwadratem długości: zadania po 220–280 tur dochodziły do 300–450 tys.
kontekstu i ok. 23 $ każde (pomiar 12–20.10). Większe dzielisz po
właścicielu pliku albo po kroku (schemat, logika, ekran). Zadanie to lista
plików z jednym właścicielem, wariant wykonawcy
z uzasadnieniem w pół zdania, zadania, od których zależy, komenda
weryfikacji i **czytelnicy** jego pól poza jego plikami (komponent
renderujący, eksport, drugi dom tej samej reguły). Każde zadanie po scaleniu
zostawia gałąź integracyjną zieloną; zmiany zielone dopiero razem (schemat
i jego konsument) są jednym zadaniem. Dwa zadania równoległe w jednym pliku
to konflikt przy scaleniu: dziel po właścicielu pliku; kolejne w tym samym
pliku rozdziela zależność. Numery migracji i wpisów decyzji w grafie są
robocze: ostateczne nadajesz w kroku 7, po wciągnięciu `main`, także gdy
kilka PR-ów przelotu leci naraz (każdy merge przesuwa numery reszty). Plik
generowany z innego (kopia pomocy, typy) przy konflikcie scalenia
regenerujesz generatorem, nie scalasz, a zadanie zmieniające źródło takiej
kopii ma w weryfikacji generator i `git diff` kopii, w grafie zaś wdrożenie
funkcji, które ją importują (fala RASC: czerwone CI i dwie funkcje spoza
planu); wspólne rejestry (konsumenci,
manifesty portu) mają w grafie właściciela w każdym PR-ze. Zadanie, które
pisze pomoc, opisy ekranów albo komunikaty, ma w grafie listę „działa po tym
PR-ze / przychodzi później”, a brief ją niesie; zależy od każdego zadania,
które opisywane zachowanie zmienia, nie tylko od tego, które je buduje, i
startuje po scaleniu ich implementacji razem z otwartymi poprawkami; późniejsza
zmiana zachowania otwiera je na nowo (CRM B2: dokumenty równolegle z wpięciem
list opisały plan zamiast kodu; CRM C2: teksty puszczone obok rund kodu
wróciły trzy razy).

Masowa
zmiana oceniana sędzią (setki tekstów) zaczyna od próbki: wynik poniżej
progu na próbce przenosi zadanie na opus high, zanim tańszy wariant przerobi
całość.

Plan ustala też **granice PR-ów** (zadanie, front albo całość) i zależności
między nimi, a zadanie ustalające kontrakt, z którego biorą następne fronty,
dostaje recenzenta świeżym okiem zaraz po scaleniu, nie dopiero na końcu.

### 3. Recenzja planu innym modelem

Plan, który zmienia albo dodaje ekran, ma w kryteriach odbioru wzorzec
z repo (klocek tabeli, panelu, filtrów) i sąsiednie ekrany, z którymi ma być
spójny, a ekran przenoszony z innego systemu także jego okresy, filtry
i układ; „jak w systemie X” bez tego nie jest kryterium (CRM C: Raporty bez
okresów Hubiego). Przegląd inżynierski
właściwy dla repo, potem Codex:
`codex exec -s read-only -c 'model_reasoning_effort="high"' "<pytania>" < plan.md`.
`high`, bo
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

W głównym klonie: gałąź integracyjna z aktualnego `main`, checkout na nią;
w repo, którego klon jest dzielony z innymi sesjami (AGENTS.md: każda sesja we
własnym worktree), gałąź integracyjna żyje we własnym worktree, a scalenia
z kroku 5.3 robisz tam (agenci i tak zaczynają od `merge --ff-only <SHA>`).
Worktree agentów wyrastają z `HEAD`, więc repo potrzebuje w
`.claude/settings.local.json` wpisu `{"worktree": {"baseRef": "head"}}`,
a `.gitignore` wpisu `.claude/worktrees/`. Pliki gitignorowane, których
wymagają testy, wchodzą przez `.worktreeinclude`, wyłącznie w wersji lokalnej
albo testowej: sekrety produkcji zostają u Ciebie, bo strażnik komend łapie
pomyłki, a nie każdą drogę do zdalnej zmiany.

Zadania równoległe, które dzielą typy albo komponent, dostają kontrakt
w kodzie: przed spawnem wstawiasz na gałąź integracyjną typy i słowniki wartości
(np. funkcji bazy, kody z CHECK) i szkielet komponentu z sygnaturą z planu,
osobnym commitem; właściciel
szkieletu go wypełnia, reszta kompiluje się na nim od pierwszej minuty (CRM
B2: baza, środek i rekord ruszyły razem).

Porównaj cwd sesji z katalogiem repo planu i powiedz wynik na głos: sesja
spoza repo nie ma jego hooków (LC-084). Pułapki worktree i środowiska:
[PULAPKI.md](PULAPKI.md).

### 5. Pętla frontu

**Front** to zadania, których zależności są scalone. Pętla:

1. Każde zadanie frontu dostaje spawn: `Agent` z
   `subagent_type: "foreman-wykonawca"`, `model` i `effort` z wariantu
   w grafie, `run_in_background: true`, wszystkie w jednym komunikacie.
   Brief podaje zakresy do przeczytania (plik i funkcja z rozpoznania), nie
   każe szukać: przeszukiwanie repo robi wykonawca na Twój koszt w każdej
   następnej turze. Naraz żyje
   najwyżej trzech pracujących agentów, licząc wznowionych `SendMessage`,
   recenzentów i weryfikatorów (oczekujący miejsca nie zajmuje); reszta
   frontu i rundy poprawek czeka na wolne miejsce. Zadanie tekstów wchodzi do
   frontu według zależności z kroku 2 (po poprawkach zadań, które opisuje). SHA
   gałęzi integracyjnej przy spawnie, ID agenta, nazwę jego gałęzi i worktree,
   wariant oraz (na bieżąco) rundy poprawek i findingi recenzji
   zapisujesz w pliku sesji w katalogu tymczasowym: to rejestr własności
   tego przelotu, z którego korzysta odbiór i sprzątanie. Ten sam plik
   dostaje każdą inną rzecz, którą przelot stawia (budzik, `/coffee`,
   proces w tle, konto testowe, gałąź PR), w chwili jej postawienia.
2. Na powiadomienie o końcu zadania robisz **odbiór** w ścieżce worktree
   z wyniku agenta:
   - `git merge-base --is-ancestor <SHA ze spawnu> HEAD`: worktree wyrósł
     z integracji, nie z `main` (brief każe agentowi zacząć od
     `git merge --ff-only <SHA ze spawnu>`, bo worktree potrafi wyrosnąć ze
     starszego commita niż zapisany SHA); worktree wyrasta z HEAD katalogu,
     w którym stoi sesja, a ff-only nie cofa nowszego, więc przed spawnem cwd
     stoi tam, gdzie HEAD to SHA z briefu (sesja w worktree gałęzi E dała
     wykonawcy B jej commit);
   - `git diff --name-only <SHA ze spawnu>...HEAD` mieści się w liście plików
     zadania; plik spoza listy oblewa odbiór;
   - komenda weryfikacji z grafu i sekcja odejść od planu.
   Raport agenta to hipoteza (LC-077); dowodem jest Twój przebieg komend,
   zapisany jako komenda, SHA i wynik. Ten sam dowód na tym samym SHA nie
   biegnie drugi raz.
   Agent, który przekroczył swój limit tur, liczy się jako niezaliczony odbiór.
3. Odbiór zaliczony → `git merge --no-ff <gałąź agenta>` na gałęzi integracyjnej (w jej worktree z kroku 4),
   przeliczenie frontu, spawn. Pełna weryfikacja integracji biegnie po
   zamknięciu frontu i przed PR-em, a po pojedynczym scaleniu tylko wtedy,
   gdy zadanie dotknęło plików albo kontraktu innego scalonego zadania.
   Konflikt scalenia oznacza błąd w podziale grafu: przerywasz merge, ten sam
   agent przez `SendMessage` wciąga gałąź integracyjną do swojej i rozwiązuje
   konflikt skillem `resolving-merge-conflicts`, a plan dostaje poprawkę podziału.
   Worktree i gałąź agenta żyją do mergu PR-a, w którym jest jego zadanie:
   findingi recenzji, Codexa i `/code-review` wracają do tego samego agenta.
   `SendMessage` nie wznowi agenta bez worktree ani agenta innej sesji (nowej,
   nie wznowionej `--resume`), więc sesję przekazujesz po rundzie poprawek
   zadań w niej skończonych; inaczej przekazanie wymienia ich worktree jako
   wejście nowego wykonawcy (CRM C: trzy rundy poprawek od zera, ok. 3,7 E
   straty).
4. Odbiór niezaliczony → poprawka u **tego samego** agenta przez
   `SendMessage` z dowodem (wynik komendy, `file:line`). Kontekst pierwszego
   przebiegu jest wart więcej niż świeży start. Osobno liczysz wznowienia
   po zaliczonym odbiorze (findingi recenzji, Codexa, odbioru na żywo):
   trzecie wznowienie tego samego agenta jest ostatnie, kolejną poprawkę
   bierze nowy wykonawca z aktualnym SHA, raportem i dowodami poprzednika,
   bo każda odpowiedź czyta cały kontekst od nowa; zmiana wykonawcy nie zeruje
   licznika niezaliczonych odbiorów z drabiny niżej. Nowego wykonawcę
   dostaje poprawka także wtedy, gdy kontekst agenta przekroczył ok. 200 tys.
   (`python3 <katalog skilla>/koszty.py --kontekst=<id agenta>`): wznowienie powyżej tego progu
   kosztuje więcej niż świeży start z raportem poprzednika. Próg trzech
   wznowień to limit organizacyjny bez pomiaru (LC-115: siedem wznowień,
   najdroższe zadanie przelotu). <!-- LC-115 -->
5. **Drabina wariantu:** zadanie na sonnet albo opus medium po dwóch
   niezaliczonych odbiorach idzie do nowego wykonawcy na opus high z oboma
   raportami i dowodami; licznik niezaliczonych liczy się per wariant, więc
   opus high zaczyna od zera. Opus high po dwóch niezaliczonych kończy zadanie
   jako **blokadę**: wpis w planie „czego
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

Twój kontekst rośnie przez cały przelot, a każda odpowiedź czyta go od nowa.
Wyniki komend (odbiór, testy, diff) idą drutem do pliku, a do rozmowy
liczby; raport agenta czytasz, transkryptu nie. Od ok. 250 tys. kontekstu
nie spawnujesz nowego frontu: domykasz rundę poprawek zadań skończonych
w tej sesji (krok 5.3) i przekazujesz przelot nowej sesji (PRZELOT.md): sesje brygadzisty dochodziły do 770 tys.,
a 65% ich kosztu przypadało na tury powyżej 300 tys. (pomiar 12–20.10).
`CLAUDE_CODE_AUTO_COMPACT_WINDOW` w ustawieniach to tylko siatka: kompakcja
streszcza, gubi dokładne błędy i powody decyzji, więc przekazanie robisz
sam, zanim ona przyjdzie.

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
uczyła „Stwórz zadania” po jego usunięciu). Recenzenta i Codexa puszczasz
na ten sam SHA, a ich findingi zbierasz razem i wysyłasz jedną rundą
poprawek (CRM D1: dwie rundy u tych samych wykonawców, bo Codex skończył
pierwszy). Ta recenzja jest drugim okiem z kroku 7: delta rundy poprawek
nie dostaje drugiego Codexa, chyba że zmienia migrację albo uprawnienia,
albo Codex nie widział aktualnego SHA (PRZELOT.md, „Codex w nocy”)
(przelot po odbiorze CRM: Codex na deltach trzech PR-ów dał same rzadkie
uwagi za ok. 4 E i godzinę). Teksty widoczne dla użytkownika (pomoc, opisy, zdania skutku) mają dwie
rundy poprawek, potem redagowanie staje: dla każdego pozostałego findingu
wskazujesz zdanie, gałąź kodu i niespełnioną obietnicę, zdanie bez pokrycia
wylatuje, a gdy jego brak łamie kryterium odbioru, to blokada; tekst
zmieniony po stopie przechodzi weryfikację prawdziwości jeszcze raz (CRM
UI: po cztery rundy na dwóch ekranach, blisko trzecia część kosztu). Findingi weryfikujesz w kodzie jak findingi Codexa; przyjęte wracają do agenta zadania, którego
dotyczą (krok 5.3); nowe zadanie dostaje tylko finding bez właściciela.

Zmiana dotykająca ekranu dostaje odbiór na żywo: dev serwer z osobnego
checkoutu przypiętego SHA gałęzi integracyjnej (`git worktree add <katalog
sesji>/odbior <SHA>`), nie z worktree, do którego w trakcie scalasz
poprawki, bo weryfikator nie wie wtedy, który punkt sprawdził na którym
kodzie (LC-116) <!-- LC-116 -->; poprawka scalona po tym SHA powtarza kroki,
których dotknęła; dane
z tego samego źródła co produkcja, kryteria odczytane
z DOM-u liczbami, a czas ekranu z raportu weryfikatora i czas wywołania ze
smoke: wolne zapytanie idzie do meldunku jako decyzja Serge'a z liczbą, nie
na listę „później” (CRM B: lista Leadów 2,6 s przeszła odbiór; CRM C: raport
4,6 s odłożony bez progu). Próg czasu ocenia pomiar opublikowanej wersji;
przed publikacją kryterium czasu czeka jako niezweryfikowane, bo dev serwer
nie daje ani wyniku, ani porażki (fala RASC: 3,5 s na dev serwerze,
1,0–1,7 s na produkcji). W AdMotiv odbiór robi agent `foreman-weryfikator`,
nie wykonawca, raz na PR, który zmienia ekran albo to, co ekran czyta
(uprawnienia, funkcja, schemat); PR bez wpływu na żaden scenariusz mapy ma
smoke, nie weryfikatora. Przed spawnem sprawdzasz sam, tanio, że logowanie
(`verify-admotiv/bin/sesja` na docelowym hoście) i Supabase odpowiadają: weryfikator bez
nich pali przebieg na niczym (2 z 26 przebiegów 12–20.10).
Weryfikator przechodzi
skillem `verify-admotiv` kroki mapy z obszarów, które wskazuje
`bin/doctor` dla gałęzi integracyjnej (tylko one, budżet idzie za diffem);
ten sam krok przechodzi smoke na produkcji. Weryfikator mapy nie edytuje:
dopiski „przeszło na żywo” i wiersz `przejscia.tsv` wpisuje się z jego raportu
(wpis mapy nowego zachowania pisze wykonawca zadania ekranu w raporcie,
blokiem „Wpis mapy” z `file:line` przy każdym zdaniu; brygadzista wkleja go
po sprawdzeniu, że wpisy pokrywają kryteria odbioru i obietnice planu, bo
wykonawca opisuje tylko to, co zbudował. Osobny agent przepisujący mapę po
scaleniu dopisywał zachowania z planu, których kod nie ma: CRM rekord HS,
226 odpowiedzi i 4,8 E, ok. 20 rozjazdów, jedna fałszywa regresja). Gdy zmiana ma migrację, a dev serwer czyta produkcyjną bazę,
migracja trafia tam dopiero po mergu: przed nim odbiór na żywo przechodzi
kroki odczytu, a zapis dowodzą testy SQL na kopii; kroki zapisu przechodzą
po mergu i migracji na rekordach testowych z Granic, a niezaliczony krok to
PR poprawkowy, nie cofnięcie (CRM B2).

Gdy moduł ma `CONTEXT.md`, recenzent grepuje etykiety ekranów, nazwy kolumn
i komunikaty po liście „unikaj” ze słownika: słowo stamtąd w kodzie to
rozjazd pojęć, nie styl.

### 7. Brama i wdrożenie

Brama repo w kolejności, którą repo definiuje: jego `verify` albo bramki
z `AGENTS.md`/`CLAUDE.md`, a bez `verify` kroki jego CI z `.github/workflows/`
z tymi samymi parametrami, nie wybór z pamięci (CRM C PR 3: pominięty
`check:mail-subject`), przegląd diffu, Codex jako drugie oko z innej
rodziny modeli (recenzja z kroku 6 na SHA gałęzi integracyjnej). Przed PR-em, po
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
jest odczyt żywego stanu (wersja funkcji, wiersz w bazie), a „`main`
zielony” to zielony przebieg na commicie mergu każdego workflowu, który
`.github/workflows/` puszcza na push do `main` (`gh run list --commit <sha>
--limit 50`); brak przebiegu to nie zieleń (CRM C: audyt uprawnień czerwony
na `main` prawie 6 h przy meldunku „CI zielone”).
Workflow, który puszczasz ręcznie (`gh workflow run`), czytasz przed
wywołaniem po krokach wyjścia (mail, Slack, webhook, `if: failure()`):
alarm wysłany ludziom spoza Granic jest zapłacony z chwilą startu,
anulowanie przychodzi za późno (kontakty CRM: ręczny audyt RLS na
zastanej czerwieni wysłał mail do właściciela repo mimo „żadnych wiadomości”). <!-- LC-121 -->

Meldunek idzie po kryteriach odbioru: przy każdym odczyt, który je
potwierdził, albo powód, dla którego nie przeszło. Werdykt miernika „zgodne”
przy dużej różnicy liczb uznajesz po obejrzeniu rozkładu rekordów różnicy po
pozycjach listy, nie po werdykcie skryptu (CRM C: 29 nowych leadów wobec 4
w Hubim „zgodne”, 25 z nich to spam).

### 8. Sekcja zwłok i sprzątanie

Przed sprzątaniem, póki przelot jest w kontekście: [POSTMORTEM.md](POSTMORTEM.md).
Wynik wchodzi do skilla jednym commitem i do meldunku sekcją „Skill”.

Robota kończy się meldunkiem według reguły globalnej i sprzątniętym
stanowiskiem. Meldunek niesie linię kosztu z `koszty.py` (E per model,
najdroższe zadanie z liczbą odpowiedzi i kontekstem) i warianty zadań
z rundami poprawek: to materiał reguły wariantów z tabeli floty. Przelot zostawia rzeczy, które przeżyją sesję albo ją obudzą,
więc rejestr własności wymienia każdą, a sprzątanie odhacza je po kolei:

- worktree i gałęzie agentów, gałąź integracyjna i gałęzie PR-ów, lokalnie
  i na zdalnym (merge z `--delete-branch`), po sprawdzeniu, że nie mają
  niezacommitowanej pracy; cudzych nie ruszasz, także w klonie dzielonym;
  materiał zachowany po przelocie (wariant wycięty przed mergem) commitujesz
  na gałęzi `material/<temat>`, która sprzątaniu nie podlega (jej worktree
  schodzi po sprawdzeniu czystego stanu), a rejestr i meldunek podają nazwę,
  SHA i powód; gałąź z nazwą agenta ginie przy sprzątaniu po wzorcu (LC-117);
  <!-- LC-117 -->
  worktree bez wpisu w rejestrze nazywasz cudzym dopiero, gdy jego ścieżki
  nie ma w zapisach subagentów przelotu (`<sesja>/subagents/agent-*.jsonl`);
- budziki `CronCreate` usunięte (`CronDelete`): sesja zostaje otwarta i budzik
  odpalony po przelocie wznawia robotę, której już nie ma;
- `/coffee off`: zadanie launchd trzyma Maca bez snu po końcu sesji;
- procesy uruchomione przez przelot (dev serwer, daemon przeglądarki),
  sesje i dostępy nadane na czas odbioru; daemon `browse` zatrzymujesz
  (`browse stop` z katalogu worktree) przed `git worktree remove`, bo żywy
  odtwarza w usuniętej ścieżce katalog `.gstack/` i zostawia pusty katalog;
- plan skasowany albo przepisany w dokumentację stanu, materiał sekcji zwłok
  i pliki w katalogu tymczasowym skasowane;
- lista zadań projektu (np. `MOL/Panel/meta/ZADANIA.md`): grep po nazwie
  briefu, numerach PR-ów i decyzji przelotu; trafione zadanie kasujesz albo
  przepisujesz na to, co zostało (odbiór z człowiekiem, krok po publikacji),
  przed meldunkiem. Zadanie, które dalej każe zrobić wdrożoną robotę, wysyła
  następną sesję drugi raz w to samo miejsce;
- repo notatek, w którym przelot odhaczał postęp (np. `MOL/Panel/meta/`):
  commit i push, `git status -sb` bez „ahead”. Następna sesja i monitor
  czytają stan ze zdalnego, więc niewypchnięty commit to nieodhaczona
  pozycja.

## Brief

Brief opisuje warunki, nie czynności: agent dochodzi do rozwiązania sam, Ty
zamykasz mu drogi do rozwiązań złych. Stałe reguły (commity, raport,
komentarze, zakazy) niesie definicja typu agenta; brief niesie tylko to:

```
Zadanie <nazwa z grafu> z planu <ścieżka>, sekcja <nagłówek>. Zacznij od
`git merge --ff-only <SHA ze spawnu>`.

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

Zadanie z dowodem na ekranie zbiera dowody jednym skryptem (`$B js`
z kompletem odczytów), nie klik po kliku: limit tur jest twardy (przelot po
odbiorze CRM: wykonawca panelu leada stanął na 200 turach w środku
scenariusza, ok. 70 min). Zadanie na tekstach (mapa, dokumenty) dostaje
listę plików i fragmentów kodu do przeczytania, nie całe repo (mapa po
paczce UI: 6 E na sonnecie, trzy czwarte to odczyt kontekstu).

Przebieg odczytu (triaż notatek, różnica wobec odczytu bazowego, inwentarz)
nie pisze kodu, więc nie dostaje worktree: agent ogólny zapisuje tylko raport
w katalogu sesji, a wciela go brygadzista jako jedyny piszący. Strażnik
komend floty go nie chroni, więc brief wymienia zakazy z PULAPKI.md wprost.
Brief nie każe redagować poprawek w plikach, których mandat przelotu nie
pozwala zmienić: taki rozjazd idzie wierszem do zadań (zamknięcie budowy CRM:
ok. 2,6 E na gotowe zdania pomocy „?”, której PR dokumentacyjny nie mógł
ruszyć). Werdykt „kasuj” wymaga grepa nazwy pliku w całym katalogu notatek
i w skillach (tamże: plik SQL czytany przez krok mapy oznaczony do kasacji).

## Przelot bez nadzoru

Gdy przy bramkach nie stoi człowiek albo sesja biegnie w trybie bypass lub
auto (hooki odmawiają wtedy zamiast pytać, także przy człowieku obok), przed
pierwszym spawnem, także w sesji wznawiającej przelot, przeczytaj
[PRZELOT.md](PRZELOT.md): granice w planie,
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

Zakres mglisty: najpierw doprecyzuj,
bo flota na mgłę daje trzy interpretacje równolegle. Robota wymagająca
rozmowy z Serge'em w trakcie: subagent nie ma z kim rozmawiać.
