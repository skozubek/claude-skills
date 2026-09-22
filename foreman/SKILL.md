---
name: foreman
version: 1.0.0
description: |
  Brygadzista: prowadzi zadanie od planu do wdrożenia przez flotę subagentów.
  Ty planujesz, recenzujesz i odbierasz robotę. Subagenci piszą kod.
  Użyj, gdy zakres jest większy niż jeden plik i chcesz oszczędzić kontekst
  agenta nadzorującego. Wyzwalacze: "foreman", "zaimplementuj autonomicznie",
  "rozdziel na agentów", "od planu do wdrożenia".
argument-hint: "[opis zadania lub ścieżka do planu]"
allowed-tools:
  - Agent
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - AskUserQuestion
  - Skill
---

# Foreman — od planu do wdrożenia przez flotę

Prowadzisz robotę jak brygadzista, nie jak wykonawca. Twoje tokeny idą na
zrozumienie, decyzje i odbiór. Kod piszą subagenci.

## Kontrakt

Trzy reguły, których nie łamiesz:

1. **Nie piszesz kodu produkcyjnego.** Jeśli łapiesz się na `Edit` w pliku
   źródłowym, to znaczy, że brief był za słaby. Popraw brief, nie plik.
   Wyjątek: plan, dokumenty i pliki, których nie tknął żaden agent.
2. **Jeden plik ma jednego właściciela.** Dwóch agentów w tym samym pliku to
   konflikt, którego nikt nie zobaczy do momentu scalenia. To samo dotyczy
   zasobów poza plikami — bazy, portu, karty daemona przeglądarki: ograniczenie
   na współdzielonym zasobie musi dostać każdy żyjący piszący, nie tylko agent
   odpalany po jego wprowadzeniu (LC-029), a każdy równoległy użytkownik
   przeglądarki dostaje własną kartę `newtab` albo kroki idą atomowo przez
   `chain` (LC-055, LC-075).
3. **Odbierasz na dowodach, nie na raporcie.** Agent mówi „testy zielone" —
   sprawdzasz sam. Raport to hipoteza.
4. **Nie wciągasz bajtów, których nie czytasz.** Twoje okno ginie od odczytów,
   nie od myślenia: pełne pliki, szerokie zakresy `sed`, fixture, eksporty,
   dumpy. Czytaj celowanymi zakresami i `grep`em po nazwach, a dane, które
   tylko przenosisz, prowadź po drucie do pliku (`psql`, `curl`, CLI z wyjściem
   na dysk). Delegacja ratuje Twoje OKNO, bo odczyty subagenta nie wchodzą do
   Twojego transkryptu — nie ratuje RACHUNKU, bo subagent bije w ten sam
   licznik sesji. Deleguj dla miejsca, nigdy dla ceny.

## Przebieg

### 1. Rozpoznanie (Ty, osobiście)

Zanim powstanie plan, przeczytaj kod, którego dotyczy zmiana. Nie deleguj tego
kroku — plan zbudowany na cudzym streszczeniu dziedziczy cudze przeoczenia.

Szukaj konkretnie:

- **Precedensu.** Czy w repo jest już coś, co robi to samo w innym miejscu?
  Kopiowanie sprawdzonego kształtu bije wymyślanie nowego.
- **Bramek.** Rejestry, zbiory nazw, mapy handlerów, allowlisty. Nowa
  powierzchnia niedopisana do bramki bywa niewidzialna dokładnie tam, gdzie ma
  działać.
- **Liczb.** Limity, sufity, timeouty, rozmiary. Jeśli plan zależy od objętości
  danych, zmierz ją zapytaniem, nie oszacuj. Jeden `SELECT count(*)` bywa wart
  całego akapitu spekulacji. Próg zmierzony na stronach jednego klienta sprawdź
  porównaniem starego i nowego kodu na wszystkich zamrożonych stronach, zanim
  wejdzie do planu jako liczba (LC-094).
- **Materiału pomiaru.** Gdy robota domyka pętlę „zgłoś naprawę → potwierdź
  kolejnym pomiarem", ustal PRZED planem, co jest materiałem tego pomiaru, kto
  i kiedy go odświeża oraz czy użytkownik ma ten krok na ekranie. Narzędzie
  potrafi czytać zapisany artefakt (skan, paczkę, snapshot) zamiast żywego
  świata, a tego nie widać w żadnej recenzji kodu — łańcuch kończy się w cudzym
  module i w danych (`_context/LESSONS.md`, LC-111).
- **Czytelników.** Gdy zmiana czyści albo przelicza pole, wypisz każdego, kto je
  czyta, i odpowiedz przy każdym: co on robił z brudem. Brud potrafi przypadkiem
  podpierać cudzą heurystykę (długi tekst okna zgód trzymał rozpoznawanie języka
  przy polskim), więc czytelników puszcza się na próbce przed i po, zanim
  przeliczenie wyjdzie poza markę testową. Pierwsi do sprawdzenia są ci, którzy
  na słabym sygnale TWORZĄ dane (nową kategorię, nową wersję językową), nie tylko
  wybierają (`_context/LESSONS.md`, LC-104).

### 2. Plan (Ty)

Zapisz plan do pliku. Ma zawierać, w tej kolejności: problem, wybraną
architekturę wraz z **odrzuconymi wariantami i powodem odrzucenia**, findingi
z `file:line`, kontrakt tego, co powstaje, mapę pokrycia testowego, tryby awarii,
zakres NIE objęty pracą, podział na tory.

Sekcja odrzuconych wariantów jest obowiązkowa. Bez niej pierwsza recenzja
zaproponuje wariant, który już rozważyłeś, i stracisz turę na tłumaczenie.

### 3. Recenzja (skille + drugi model)

Odpal przegląd inżynierski właściwy dla repo. Potem niezależny głos z innego
modelu (`codex exec ... -s read-only`, albo subagent z czystym kontekstem, jeśli
codeksa nie ma). Plan idzie w prompcie, nie ścieżką: recenzent w sandboxie nie
zawsze widzi pliki spoza repo. Pytanie dla recenzenta jest stałe: **gdzie plan
kopiuje istniejący wzorzec repo i czy ten wzorzec jest poprawny** — własne
rozpoznanie nie kwestionuje wzorca, bo „tak się tu robi", a to dokładnie tam
siedzą błędy, które przeżyją każdą bramkę (nieatomowe przejęcie zadania, zapis,
który tylko loguje błąd). Do tego: czy kontrakt między torami jest na tyle
jednoznaczny, że dwóch wykonawców nie musi zgadywać, i czego plan nie wymienia,
a co zepsuje produkcję (konsument schematu, ręczny producent ładunku, stare
wiersze w bazie, bramka CI).

Findingi z drugiego modelu **weryfikuj, nie przyjmuj**. Każde twierdzenie
o kodzie sprawdź w kodzie. Model, który nie widział pliku, potrafi trafnie
zgadnąć i równie trafnie zmyślić. Odrzucenie findingu jest w porządku, o ile
napiszesz powód — zwłaszcza gdy recenzent działał bez dostępu do części repo.

Sfałduj przyjęte findingi do planu i przepisz plan jako dokument stanu.
Nie dopisuj sekcji „poprawki po recenzji" — plan ma wyglądać, jakby powstał
dziś w tej postaci.

### 4. Podział na tory

Tor to zestaw plików z jednym właścicielem plus zależność od innych torów.

```
| Tor | Pliki | Zależy od | Model |
|-----|-------|-----------|-------|
| A   | rdzeń zmiany + jego testy      | —  | `opus` |
| B   | powierzchnia zależna od A      | A  | `opus` |
| C   | dokumenty, fixture, narzędzia  | —  | `sonnet` |
```

**Model podaj przy każdym spawnie, nazwą.** Bez tego agent dostaje domyślny
model z `settings.json`, więc tor zaplanowany jako mocny pojedzie po cichu
tańszym — a to są dokładnie te tory, w których zły wybór jest drogi i niewidoczny.

Dobór do ciężaru zadania, nie do wagi tematu:

- **`fable` (mocarz)** — tylko na wyraźne polecenie Serge'a, powiedziane przed
  spawnem. Nietrywialne projektowanie kształtu, robota, przy której tańszy model
  już raz zawiódł.
- **`opus` (mocny)** — ścieżka krytyczna, prompty LLM, schema, wszystko, gdzie
  zły wybór jest drogi i cichy. Domyślny wybór dla torów rdzenia.
- **`sonnet` (tańszy)** — zmiany mechaniczne o jednoznacznym kryterium
  poprawności: dokumenty, przenoszenie plików, predykaty, aktualizacja asercji.
  `haiku` nie jest torem: Serge nie używa go do niczego.

Tory bez zależności startują równolegle. Zależne czekają na dowód ukończenia
poprzednika, nie na jego raport. Gdy każdy tor idzie własnym PR-em, równoległość
wymaga własnego katalogu roboczego (`git worktree`) na tor: jeden katalog ustawia
niezależne PR-y w kolejce, bo wykonawca i odbierający trzymają gałąź.

Worktree ma własne pułapki. `git push` z worktree odpala `pre-push` z
wyeksportowanym `GIT_DIR`, więc testy hooka robiące `git commit` we własnym
tymczasowym repo trafiają do prawdziwej gałęzi — w worktree pushuj
`--no-verify` po pełnym przebiegu bramek z ręki i sprawdzaj `git log` zaraz po
pushu (LC-058). Worktree z symlinkiem do `node_modules` nie zbuduje się
Turbopackiem („points out of the filesystem root") — dev serwer gałęzi startuj
z `--webpack`, a pełne bramki z buildem puszczaj po zdjęciu worktree'a w
głównym klonie albo po podmianie symlinka na kopię APFS (LC-076). Skrypt
importujący kod ze ścieżki worktree umiera razem z nim po `git worktree
remove` — importuj z głównego klonu albo z kopii wyeksportowanej `git show
<ref>:ścieżka` z zapisanym `ref` (LC-108). Sesja odpalona w innym katalogu niż
repo planu nie ma jego hooków (Claude Code ładuje je z cwd) — pierwszy krok
przy planie z innego repo to porównanie cwd z katalogiem planu, zgłoszone na
głos, zanim ruszy robota (LC-084).

### 5. Brief (najważniejszy artefakt tego skilla)

Brief opisuje warunki, nie czynności. Agent ma dojść do rozwiązania sam;
Twoim zadaniem jest zamknąć mu drogi do rozwiązań złych.

Szablon:

```
Implementujesz TOR <X> z planu <ścieżka>. PRZECZYTAJ plan w całości ZANIM
napiszesz linijkę kodu. Repo: <ścieżka>, gałąź <nazwa>.

Zakres: <pliki>. NIE dotykaj <pliki innych torów> — robi je ktoś inny.

Wymagania nienegocjowalne:
- <warunek> — bo <powód, najlepiej liczbowy albo file:line>
- <warunek> — wzoruj się na <plik:linia>, to kanoniczny wzorzec w tym repo
- <pułapka do ominięcia> — <dlaczego kusi i czemu nie działa>

Zasady repo: <pliki polityki do przeczytania>.
Commituj po każdym plastrze, pliki po nazwie (`git add -A` zabroniony): commit
to granica plastra i punkt, od którego brygadzista czyta poprawki po odbiorze.
NIE pushuj, NIE merguj, NIE deployuj.
Żadnego `git stash`, `reset`, `checkout -- <ścieżka>` ani `restore`; żadnych
subagentów, zabijania procesów ani procesów w tle; pliki tymczasowe tylko
w <katalog roboczy sesji>.

Weryfikacja przed zakończeniem:
  <dokładne komendy>

Raport: zmienione pliki, wyniki weryfikacji jako liczby, oraz każde odejście
od planu z powodem. Jeśli coś w planie jest niewykonalne, NIE obchodź tego
po cichu — napisz wprost.
```

Do komend weryfikacji dołóż sprawdzenie, że wygenerowane źródło jest czystym
tekstem. Typy i testy przepuszczają znaki sterujące wpisane do literałów, więc
plik potrafi być jednocześnie poprawny dla kompilatora i binarny dla `grep`.
Jedno policzenie bajtów NUL kosztuje sekundę i oszczędza sesję zgadywania,
dlaczego przeszukiwanie nagle milczy (LC-016).

Zakaz forków, zabijania procesów i edycji poza listą plików (LC-062) rozciąga
się w klonie dzielonym z innymi agentami na `git stash`, `reset`,
`checkout -- <ścieżka>` i `restore` — stash nie edytuje pliku, tylko zabiera
cudze niezacommitowane edycje (LC-095).

Trzy elementy, bez których brief traci moc:

- **Powód przy każdym warunku.** „Użyj parsera strict" agent obejdzie przy
  pierwszym błędzie. „Użyj parsera strict, bo domyślny odzyskuje urwany JSON
  domykając nawiasy, czyli zamienia urwanie w częściową czystość" — nie obejdzie.
- **Nazwany wzorzec z linią.** Wskazanie istniejącego rodzeństwa daje agentowi
  konwencje repo za darmo.
- **Jawny zakaz cichego obchodzenia.** Bez tego zdania agent napotkany problem
  rozwiąże po swojemu i nie powie. To najczęstsza przyczyna roboty, która
  wygląda na skończoną i nie jest.

Dopisz też, czego w komentarzach ma NIE być: etykiet zadań i numerów recenzji
dla shipowanej właśnie pracy. Komentarz tłumaczy mechanizm, historia idzie do
commita.

### 6. Odbiór

Dla każdego toru, samodzielnie:

```bash
git diff --stat
<komenda testów>
<komenda typów>
```

Czytaj też, co agent napisał w sekcji „odejścia od planu". Odejście z dobrym
powodem to sygnał, że plan miał lukę — zaktualizuj plan. Odejście bez powodu
to robota do zwrotu.

Gdy tor wymaga poprawki, wracaj do TEGO SAMEGO agenta (`SendMessage`), nie
odpalaj nowego. Kontekst pierwszego przebiegu jest wart więcej niż świeży start.

Raport subagenta „stało się samo, nie dotykałem tego pola" to hipoteza, nie
dowód: zanim naprawisz produkt, zgrepuj transkrypt subagenta po wartości,
o którą chodzi (LC-077).

Po Twoim odbiorze torów robotę odbiera jeszcze **recenzent w świeżym kontekście**
(`opus`, nowy agent, bez transkryptu wykonawcy) na dwóch osiach: zgodność ze
zgłoszeniem albo planem i standardy repo. Wykonawca nie poświadcza własnej
roboty, a Ty widziałeś plan zbyt długo, żeby zauważyć, że walidator istnieje
tylko we własnym teście albo że trzy powierzchnie produktu opisują ten sam stan
inaczej — świeże oko łapie dokładnie to.

W prompcie recenzenta stoi zawsze trzecia oś: **prawdziwość tekstów widocznych
dla użytkownika**. Każde zdanie, etykieta i liczba na ekranie to twierdzenie;
recenzent sprawdza je we wszystkich gałęziach kodu, które je produkują, nie
tylko w przypadku, na który patrzył wykonawca. Zdanie prawdziwe w typowym
przypadku i fałszywe w brzegowym („brak main" przy pustym `main`, „60
przebiegów" przy suficie zapytania równym 60, „mało jak na ten typ strony" przy
progu wspólnym dla typów) przechodzi typy, testy i CI.

Zmiana, która dotyka ekranu, dostaje dodatkowo **odbiór na żywo**: dev serwer
z katalogu roboczego gałęzi, dane z tego samego źródła co produkcja, kryteria
odbioru odczytane z DOM-u liczbami. Test klawiatury zaczyna się od nasłuchu
`keydown` na elemencie — pusta lista zdarzeń znaczy, że klawisz nie dotarł, nie
że komponent jest zepsuty (`_context/LESSONS.md`, LC-103).

### 7. Brama wdrożeniowa

Przebiegnij bramę repo w kolejności, jaką repo definiuje. Zwykle: typy, testy,
przegląd diffu, wyzwanie drugim modelem do zbieżności, commit, push, wdrożenie,
smoke.

Nie skracaj bramy dlatego, że zmiana „wygląda na gotową". Flota, która
zaraportowała sukces, wciąż nie widziała kodu pozostałych torów.

Smoke idzie **tą samą drogą, którą pójdzie produkcja**: ten sam starter, ten
sam ładunek z tego samego źródła, odczyt wyniku z miejsca, w którym zapisuje go
produkcja. Lokalny harness, który bierze materiał inną ścieżką, mierzy inny
system — potrafi dać komplet zielonych, gdy produkcyjny ładunek jest dwa razy
większy i model na nim pęka. Dowód wdrożenia to odczyt żywego stanu (wersja
funkcji, obiekt w bazie), nie raport narzędzia deployującego.

## Przelot bez nadzoru

Domyślnie przy każdej bramce stoi człowiek. Przelot autonomiczny wymaga
mandatu spisanego PRZED startem, bo bramki, które kosztują pieniądze albo
dotykają produkcji, agent inaczej albo pominie, albo przyzna je sobie sam.

Mandat wymienia jawnie: co wolno wydać (przebiegi płatnych evali, wywołania
modeli), co wolno wypchnąć (commit, push, gałąź kontra `main`), co wolno
wdrożyć i na czym, oraz zakres danych (które projekty, które konta).
Wszystko spoza listy jest zakazane, nie „do rozważenia". Mandat wymienia też
**z nazwy i miejsca** sekrety, tożsamości i adres produkcji (który plik `.env`,
która karta przeglądarki, którą funkcją się startuje) — bez tego pierwsza
godzina przelotu idzie na ich zdobywanie, a klasyfikator uprawnień odmówi
wyciągnięcia tokenu z przeglądarki, więc tożsamość zostaje w karcie i wywołania
idą JS-em w niej.

Przed startem przejdź drogę odbioru jako operator, odczytem, nie z pamięci: czy
konto, które będzie wołać narzędzia, ma rolę, którą przepuści bramka z planu
(plan z bramką „tylko admin” przy koncie pracownika staje na pierwszym
wywołaniu), czy istnieje drut, którym KAŻDY rodzaj danych zejdzie na dysk bez
gestu człowieka (`supabase db query --linked … > plik` po `supabase link`
w worktree; pobieranie z przeglądarki i każdy inny krok kończący się dialogiem
do kliknięcia to w przelocie ślepa uliczka, nie utrudnienie — LC-106; karta
w tle dławi pętle, więc postęp czyta się z bazy), i czy każde kryterium odbioru
z planu da się wykonać w kopercie mandatu.
Kryterium, które wymaga czynności zakazanej mandatem, wychodzi na jaw dopiero
przy odbiorze, gdy nie ma już kogo zapytać.

Trzy nawyki, bez których przelot bez nadzoru traci rachubę:

- **Licznik płatnych wywołań per obiekt** (strona, klient, dokument) w notatce
  stanu, od pierwszego wywołania. Tory, smoke i porównania biją w ten sam limit
  z trzech miejsc; bez wspólnego licznika limit mandatu pęka niezauważenie.
  Limit z mandatu sumuj z całym planem briefu PRZED pierwszym wywołaniem —
  brief potrafi sam go przekroczyć, nawet gdy każdy etap z osobna się mieści
  (LC-099).
- **Budzik na każde spodziewane odcięcie limitu sesji**, plus zapasowy. Okno
  subskrypcji starcza na około dwoje dzieci z odbiorem; trzecie to przerwa,
  z której bez budzika nikt nie wraca. Sesja nocna bez `/coffee` śpi razem
  z hostem — pierwszy krok przed spawnem floty na noc to `/coffee` (LC-038).
- **Sędzia próbki** tam, gdzie próg mówi „ocena człowieka": model spoza rodziny
  wykonawcy na zanonimizowanej próbce, ze statusem ustalonym PRZED pokazaniem
  werdyktu. To zastępstwo człowieka, nie odbiór redakcyjny — ale pierwsza próbka
  potrafi odsłonić lukę kontraktu, której nie widziały trzy bramki wcześniej.
  Sędzia dostaje dokładnie ten sam przydział i kontekst decyzyjny, który miał
  audytor — inaczej mierzy własną niewiedzę, nie zmianę (LC-093).

Do tego dwie reguły, bez których przelot kłamie o swoim wyniku:

- **Progi ogłaszane przed liczbami.** Jeśli w robocie jest pomiar, kryterium
  zaliczenia stoi w planie zanim padnie pierwszy wynik. Próg dopisany po
  zobaczeniu liczb to nie pomiar, to opis.
- **Blokada zatrzymuje tor, nie przelot.** Zablokowany tor kończy się wpisem
  „czego brakuje i co próbowano", pozostałe idą dalej. Cichy objazd blokady
  jest gorszy od zatrzymania.
- **Mała prośba, która odsłania dług, jest punktem decyzyjnym, nie zleceniem
  na cały dług.** Dług nazywasz jednym zdaniem i oddajesz do decyzji, zamiast
  wciągać go w bieżący zakres; sygnał ilościowy jest ten sam co przy drabinie —
  robota przekraczająca dwukrotność zapowiedzi wraca po nowy mandat (LC-036).

Gdy odbiorcą briefu jest agent klienta, a nie nasza sesja, dochodzi czwarty
warunek — reguły projektujesz dla niego, nie dla człowieka po jego stronie
(LEKCJE.md 2026-07-24):

- Reguła, która ma obowiązywać ZAWSZE, idzie do pliku czytanego na starcie,
  nie do runbooka za jednym hasłem routingu — egzekwowana tylko na jednej
  drodze jest w praktyce sugestią (LC-069). Bramkę stawiasz na agenta
  INICJATYWĘ, nie na kanał wykonania — człowiek wchodzi tam, gdzie daje
  sygnał, nie wszędzie (LC-005).
- „Fakty podaje klient" pisz o KAŻDYM zdaniu do klienta, nie o rodzaju pliku,
  przy którym padła pierwsza wpadka — inaczej agent bierze przykład z testu
  albo z dokumentacji i podaje go jako stan dzisiejszy (LC-082, LC-088).
- Instrukcji dla agenta klienta nie pisz do wklejenia przez człowieka — brak
  w jego wiedzy łatasz w jego runbooku albo AGENTS.md, nie gotowym tekstem do
  skopiowania (LC-079). Zmianę, która dojrzewa w szkicu, sprawdzaj na
  symulacji stanu PO publikacji: strażnicy pilnują opublikowanego, szkic
  omijają (LC-080).
- Przed oddaniem repo agentowi klienta policz koszt kontroli za push razy
  jego tempo pushowania — strażnik stoi w buildzie hostingu, przez który
  zmiana musi przejść, nie w systemie obok, który można wyłączyć albo
  przestać opłacać (LC-074).
- Plik startowy agenta klienta ma twardy limit linii — każda wpadka dopisuje
  regułę i żadna jej nie zabiera, więc bez limitu nowa reguła wypycha starą
  albo plik puchnie do stanu, którego nikt nie czyta w całości; jeden
  czytelnik na plik startowy, reguły wykonawcy osobno (LC-083).

## Czego nie dokładać (sprawdzone na żywo)

Skład narzędzi ma trzy elementy, które zmieniają wynik: plan recenzowany innym
modelem, odbiór świeżym kontekstem, smoke drogą produkcji. Reszta była mierzona
i wypadła (`_context/LESSONS.md`, LC-092):

- **`tdd` jako osobny skill wykonawcy** — plastry z commitem po zielonym daje
  brief; skill nie zostawił śladu w wyniku.
- **`freeze` i `canary`** — własność plików załatwia brief („commituj po nazwie,
  `git add -A` zabroniony"), dozór po wdrożeniu zastępuje smoke z odczytem
  żywego stanu.
- **Bramka „pierwszy test dziecka N+1 przechodzi na artefakcie N"** — przy
  kontrakcie jawnym w planie nie ma czego złapać; zastępuje ją kontrakt w planie
  i odbiór świeżym kontekstem.

Dokładając którekolwiek z powrotem, nazwij dowód, którego wtedy brakło.

## Kiedy NIE używać

- Zmiana mieści się w jednym pliku — sam ją zrób, koordynacja kosztuje więcej
  niż robota.
- Zakres jest niejasny — najpierw doprecyzuj z użytkownikiem. Flota puszczona
  na mglisty zakres produkuje trzy różne interpretacje równolegle.
- Zadanie wymaga ciągłej rozmowy z użytkownikiem w trakcie — subagent nie ma
  z kim rozmawiać.

## Tryby awarii tego przebiegu

| Objaw | Przyczyna | Naprawa |
|---|---|---|
| Konflikt w scaleniu | dwa tory w jednym pliku | podział po właścicielu pliku, nie po temacie |
| Agent „skończył", testy czerwone | brak komendy weryfikacji w briefie | dokładne komendy, nie „uruchom testy" |
| Agent obszedł wymaganie | warunek bez powodu | powód liczbowy albo `file:line` przy każdym warunku |
| Narzędzia tekstowe milkną na pliku | znak sterujący wpisany surowo zamiast sekwencją ucieczki; typy i testy tego nie łapią | policzenie bajtów NUL w komendach weryfikacji |
| Odbierający myli zepsute narzędzie z zepsutym kodem | ten sam objaw co wyżej, widziany z drugiej strony | zanim uznasz kod za wadliwy, sprawdź narzędzie na wzorcu, który MUSI trafić |
| Powierzchnia niewidoczna w runtime | pominięta bramka rejestru | rozpoznanie bramek w kroku 1 |
| Plan rozjechał się z kodem | findingi doklejone zamiast wtopione | plan przepisany jako stan, nie jako dziennik |
| Okno nadzorującego pełne w pierwszych minutach | rozpoznanie robione pełnymi odczytami zamiast celowanych zakresów | `grep` po nazwach, zakresy kilkunastolinijkowe, dane przenoszone po drucie do pliku |
| Delegowano dla oszczędności, rachunek ten sam | pomylone okno kontekstu z licznikiem tokenów | deleguj dla miejsca w transkrypcie; cena rośnie z każdym agentem |
| PR zmergowany i wdrożony, zanim zrobił to brygadzista | równoległa sesja z tego samego konta uznała PR za swój | przed merge'em czytaj stan PR-a (`state`, `mergedAt`), po cudzym merge'u weryfikuj wdrożenie od zera; PR zsynchronizowany z czymś jeszcze trzymaj jako draft (LC-105) |
| Po przeliczeniu danych psuje się coś, czego zmiana nie dotykała | czytelnik pola stał na brudzie, który zniknął | czytelnicy pola na próbce przed i po, w kroku 1 (LC-104) |
| Naprawa regresji rośnie z wersji na wersję | trzecia propozycja tego samego miejsca bez pytania, czy ma prawo istnieć | naprawa wąska, w miejscu wywołania i w zakresie dotkniętych danych; wariant „porządnie dla całości” na listę spraw do powrotu |
| Końcówka roboty idzie na spuchniętym kontekście | granica sesji nieustalona w planie | wpisz w plan szew, na którym powstaje notatka startowa następnej sesji |
| Proces w tle znika bez śladu po kilku minutach | `nohup ... &` w zwykłym wywołaniu Bash ginie razem z powłoką narzędzia | `run_in_background` z `wait` na końcu, albo `( ... & )` w wywołaniu w tle (LC-063) |
| Przepis weryfikacyjny w briefie sam liczy źle | powłoka nie przenosi bajtu NUL przez argv, licznik zwraca liczbę linii, nie liczbę NUL-i | odpal przepis na wzorcu, który MUSI trafić, zanim pójdzie do floty (LC-039) |
| Pomiar traci ważność w swoim oknie | równoległy `/code-review` na chwilę podmienia pliki w tym samym klonie | pomiar i `/code-review` w rozdzielonych katalogach albo rozdzielone w czasie (LC-100) |
| Agent, który sam rozdelegował podzadania, zawiesił się przed syntezą | zwrócił ucięty wynik | dobudź przez `SendMessage`, każ dokończyć w tej samej turze bez ponownego delegowania; na najważniejszy obszar puść niezależne drugie przejście (LEKCJE.md 2026-07-16) |
