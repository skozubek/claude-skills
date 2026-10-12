---
name: verify-admotiv
description: |
  Przejście AdMotiv ścieżką użytkownika w działającej aplikacji i dowód, że
  zmiana działa: serwer dla checkoutu, logowanie kontem bez klikania, sterowanie
  przeglądarką headless, skutek odczytany w bazie, mapa funkcji modułu.
  Używaj przed „gotowe” przy każdej zmianie ekranu AdMotiv, przy odbiorze
  w foremanie, przy odtwarzaniu zgłoszonego błędu i przed pracą w module, który
  ma plik w mapie. Wyzwalacze: "zweryfikuj w aplikacji", "przejdź ścieżkę",
  "verify-admotiv", "odbiór ekranu".
---

# Weryfikacja AdMotiv

Czytasz to na zimno, w środku zadania, bez znajomości aplikacji. Mechanika
siedzi w skryptach `bin/` (ścieżki względem katalogu tego skilla), tobie
zostaje osąd: co przejść, czy dowód dowodzi, czy zmiana działa.

Narzędzie jest prywatne (Serge + jego agenci). Repo AdMotiv o nim nie wie:
nic z tego skilla nie trafia do repo ani do PR-ów.

## Zakres i koszt

Budżet to jedna subskrypcja na miesiąc, więc weryfikacja idzie za diffem:
- przechodzisz **tylko obszary, których dotyka zmiana**; listę podaje
  `bin/doctor` (pliki zmienione na gałęzi i w drzewie roboczym zestawione ze
  ścieżkami obszarów w `przejscia.tsv`), a w obszarze tylko kroki, których
  zachowanie zmiana może ruszyć;
- ekran czytasz wąsko: `$B js` z selektorem i wynikiem w kilkudziesięciu
  znakach albo `snapshot -i -s '<kontener>'`; pełny `snapshot` strony i
  `text` całej strony tylko przy diagnozie;
- zrzuty idą na dysk i zostają nieobejrzane; otwierasz je dopiero, gdy odczyt
  tekstowy jest niejasny;
- bez subagentów do weryfikacji jednej zmiany; pełny przegląd modułu tylko
  przy jego odbiorze.

## Start

```bash
# z katalogu repo AdMotiv albo jego worktree; Bash z run_in_background
<skill>/bin/start
```

Port wynika ze ścieżki checkoutu (8100–8199), więc dwa worktree nie dzielą
serwera. Worktree bez `node_modules`: najpierw `bun install`. Gotowe znaczy:
`bin/doctor` mówi „zdatna do sterowania”, nie że proces wystartował.

Dev serwer czyta **produkcyjną bazę** (`.env` repo). Każdy klik zapisujący
pisze na produkcji. Stąd konta i marki testowe z mapy i sekcja „Skutki
zewnętrzne” niżej.

## Logowanie

```bash
<skill>/bin/sesja <email>      # tylko konto z warunków wstępnych mapy
<skill>/bin/sesja --wyloguj
```

Bez hasła i bez klikania: link logowania generowany kluczem serwisowym,
sesja wstrzyknięta przez klienta Supabase aplikacji. Odmawia, gdy: konta nie
ma w tabeli kont README mapy, projekt CLI nie zgadza się z `.env` aplikacji,
na porcie nie słucha serwer tego checkoutu, konto nie istnieje (skrypt kont
nie zakłada), sesja w przeglądarce należy do innego użytkownika niż
zamówiony. Sekrety nie trafiają na wyjście ani do argumentów procesów.
Wylogowanie jest lokalne: sesje konta na innych urządzeniach zostają.
Tokenów nigdy nie wpisujesz do `$B js` ani do argumentów: gstack zapisuje
treść komend w swoim dzienniku audytu. Kod z sekretem idzie przez plik
i `$B eval <plik>`, jak w `bin/sesja`.

## Kontrola instancji

```bash
<skill>/bin/doctor [moduł]
```

Odpowiada, czy instancję warto sterować: checkout i gałąź, serwer na porcie
tego checkoutu z tego katalogu (nie cudzy), strona 200, jeden daemon
przeglądarki, karta na właściwym adresie, kto jest zalogowany, błędy konsoli.
Z nazwą modułu pokazuje commity w jego kodzie od ostatniego pełnego przejścia
mapy, z autorem. Cudza zmiana w module oznacza: najpierw przejście wpisów mapy
tych obszarów, których dotykają te commity, potem twoja robota. Wtedy regresja
wychodzi jako znalezisko, nie jako „mój kod zepsuł”. Pełny przegląd modułu
tylko przy jego odbiorze.

Kolejność: `bin/start`, `bin/sesja <email>`, `bin/doctor`. Bez sesji, bez
karty na tym serwerze i z cudzym procesem na porcie wynik to błąd.
Uruchamiasz przed pierwszym sterowaniem, po każdym nieudanym kroku i zawsze,
gdy coś wygląda dziwnie. Nigdy nie sterujesz instancją, której nie
sprawdziłeś od ostatniej niespodzianki. Gdy kontrola nie widzi problemu
(zawieszony ekran na zdrowym procesie), przeładowujesz albo restartujesz,
zamiast liczyć na szczęście.

## Sterowanie

Przeglądarka to gstack browse w trybie headless:
`B=~/.claude/skills/gstack/browse/dist/browse`, komendy z katalogu
testowanego checkoutu (daemon jest per repo). `$B --help` jest kanoniczne.
Najczęściej: `goto`, `snapshot -i` (drzewo z referencjami `@eN`), `click`,
`fill`, `press`, `wait`, `text`, `js`, `eval <plik>`, `console --errors`,
`network`, `screenshot <ścieżka>`.

- Uchwyty: rola i dostępna nazwa, `aria-label`, `data-*`, dokładny tekst
  przycisku. Klasy CSS i pozycja w ostateczności. Brak stabilnego uchwytu
  zapisujesz w „Pułapkach” pliku mapy.
- Czekasz na obserwowalny stan końcowy (`wait <selektor>`, tekst, wiersz
  w bazie), nigdy na stały sen.
- `$B eval` zwraca wynik tylko z wyrażenia: kod z `await` owijasz w
  `(async () => { …; return x; })()`.
- Klikasz jak użytkownik: `click` po roli i nazwie albo `@eN`, klawiatura
  przez `press`. Klik i wypełnienie przez DOM (`eval` z `.click()`, natywny
  setter pola Reacta) omijają nakładki i zablokowane przyciski, które
  zatrzymałyby człowieka, więc to diagnostyka: krok tak przejęty ma w dowodzie
  dopisek „klik DOM, dowód niepełny” i powód (np. `@eN` w panelu bocznym trafił
  w inny przycisk o tym samym napisie).
- Okna potwierdzeń: gstack domyślnie je zatwierdza. Przed krokiem, który może
  otworzyć `confirm`, ustawiasz politykę jawnie (`dialog-dismiss` albo
  `dialog-accept`), a po kroku czytasz `$B dialog`: treść okna jest częścią
  dowodu. Akcja niszcząca nigdy nie przechodzi na domyślnym zatwierdzeniu.
- `eval` służy do odczytu stanu po przejściu ścieżki użytkownika, nie do
  wywoływania wewnętrznych funkcji aplikacji jako dowodu.
- Równoległy agent bierze własną kartę (`newtab`) albo kroki idą atomowo
  przez `chain`.
- Skutek w bazie czytasz `supabase db query --linked "<SELECT …>"`
  z katalogu repo. Kolumny z poświadczeniami wybierasz po nazwie, nigdy
  `select *` na tabelach kont, skrzynek i OAuth.

## Dowód

Poprzeczka: dowód przechodzi prawdziwą drogę użytkownika i pokazuje wynik,
który przyjąłby sceptyczny recenzent. Zrzut „otwiera się” nie jest dowodem.

- Przeczytaj plik mapy pasujący do zmiany. Przejdź **każde** wejście, które
  wymienia, każdy tryb i każdą ścieżkę, której zmiana może dotknąć: sukces,
  anulowanie, błąd, pusto, trwałość (przeładowanie albo przejście na inny
  ekran i powrót). Dowód z jednego wygodnego wejścia jest niepełny, gdy mapa
  wymienia inne.
- Pokaż akcję i stabilny stan końcowy, nie sam ekran końcowy.
- Skutki, nie piksele: wiersz w bazie, wartość pola po przeładowaniu, żądanie
  w `network`, plik. Napis w toaście bez zapisu w bazie niczego nie dowodzi.
- Atrapa liczy się tylko za tą samą granicą, którą produkcja izoluje system
  zewnętrzny. Nie liczy się, gdy omija ekran, funkcję edge, RLS albo zapis.
- Gdy bezpieczna droga to tryb próbny, sprawdzasz obserwacją, co naprawdę
  pomija (sieć, wiersze, wysłane wiadomości), a nie po nazwie trybu.
- Ścieżka nie do przejścia: nazywasz ją, mówisz, co blokuje (konto,
  uprawnienie, dane, OAuth, system zewnętrzny), przechodzisz najbliższą
  prawdziwą drogę i nie raportujesz pominiętego wejścia jako sprawdzonego
  inną drogą.
- **Nigdy nie osłabiasz ścieżki, żeby przeszła.** Brak warunku wstępnego
  w danych to porażka przejścia z powodem, a powód idzie do „Pułapek” pliku
  mapy.

Artefakty: `~/Coding/MOL/Panel/dowody/<RRRR-MM-DD>-<temat>/`. Zrzut przez
`bin/zrzut <katalog> <ID-kroku-stan>`, który dopisuje metrykę (czas, HEAD,
adres, konto z id). Obok: odczyt ekranu w tekście (`snapshot` albo `js`)
i każde zapytanie SQL **razem z jego treścią** i identyfikatorami wierszy, nie
same liczby. Liczba zgodna z ekranem dowodzi tylko wtedy, gdy zapytanie
liczy tę samą regułę co ekran (widok „Spam” to werdykt człowieka albo agenta,
nie sam status). Krok mapy oznaczasz „przeszło na żywo <data>” dopiero, gdy
przeszły jego akcja i jego stan końcowy, nie sam odczyt liczników. Meldunek cytuje odczyty liczbami i podaje
katalog. Katalog żyje do odbioru na produkcji, potem kasujesz.

## Skutki zewnętrzne

Akcje, których nie da się cofnąć, przechodzisz na produkcji tylko wtedy, gdy
plan albo Serge w tej sesji je wymienia, i tylko na koncie i marce testowej:
wysyłka maila i SMS-a, wysyłka konwersji do platform reklamowych, publikacja
reklam, wywołania płatnych modeli AI (z limitem liczbowym), wszystko, co
pisze do systemu klienta. Plik mapy oznacza takie kroki. W każdym innym
przypadku ścieżka kończy się przed akcją, a dowodem jest stan tuż przed nią
plus odczyt, że akcja nie poszła.

## Dane testowe

Kroki zapisu na produkcji idą tylko w cyklu: (1) identyfikator przebiegu
w danych, które da się nim odnaleźć (np. adres `test-verify+<RRRRMMDD-HHMM>@…`
w zapytaniu), (2) odczyt stanu przed, (3) przebieg, (4) sprzątanie według
przepisu SQL z pliku mapy, (5) odczyt, że po przebiegu nie zostało nic z jego
identyfikatorem. Plik obszaru bez przepisu sprzątania ma kroki zapisu
oznaczone jako zablokowane. Prawdziwych danych (etapy lejka, ustawienia
agencji) przebieg nie zmienia bez planu i słowa Serge’a.

## Sprzątanie

```bash
<skill>/bin/sprzataj
```

Wylogowuje przeglądarkę lokalnie i zatrzymuje serwer uruchomiony przez
`bin/start` dla tego checkoutu: po pid z własnego stanu i tylko wtedy, gdy ten
proces wciąż pracuje w tym checkoucie (nigdy po nazwie procesu). Dowodów nie rusza.
Dane testowe, które przebieg zapisał, sprzątasz według „Pułapek” pliku mapy.
Sprzątasz też po każdej nieudanej iteracji, żeby nie zostawiać serwerów
i portów.

## Mapa funkcji

`~/Coding/MOL/Panel/meta/mapa/`: `README.md` (warunki wstępne, konta testowe,
konwencje, spis i kolejność pełnego przeglądu), jeden plik na obszar,
`<moduł>-sciezki-przekrojowe.md` (drogi przez kilka ekranów, zawsze na końcu
pełnego przeglądu), skrypty danych testowych modułu (np.
`crm-zapytanie-testowe.sh`, `crm-sprzatanie.sh`) i `przejscia.tsv` (obszar,
ścieżki kodu, SHA `origin/main` i data ostatniego przejścia ścieżki głównej
obszaru na żywo; czyta je `bin/doctor`).

Plik obszaru: tytuł, jeden akapit o tym, co widzi użytkownik, potem dokładnie
cztery sekcje w tej kolejności:

1. `Podfunkcje`: krótkie ID i jedna linia na zachowanie.
2. `Jak tam dojść (oczami użytkownika)`: każde wejście (menu, adres,
   przycisk, rola).
3. `Sterowanie`: zaczyna od `Warunki wstępne:`, potem etykietowane kroki:
   akcja użytkownika → uchwyt → obserwowalny wynik → skutek w bazie.
4. `Pułapki`: co kłamie albo unieważnia przebieg.

Bez implementacji: tylko drogi użytkownika, uchwyty, wymagany stan, komendy
i dowód. Wpis ma się dać wykonać bez czytania kodu. Plik dzielisz, gdy sekcja
zaczyna potrzebować własnych warunków wstępnych.

**Mapa rośnie za robotą, nie na zapas.** Zmiana poza mapą (doctor: „pliki
nie należą do żadnego obszaru”) przechodzi według tej samej poprzeczki
dowodu, a wejścia i uchwyty agent ustala z kodu. Drogę, którą przeszedł,
zapisuje od razu jako nowy plik obszaru: tylko przejęte kroki, każdy
z dopiskiem „przeszło na żywo <data>”, plus wiersz w `przejscia.tsv` ze
ścieżkami zmienionych plików. Obszarów, w których nikt z nas nie pracuje,
nie mapujesz.

**Moduł bez pliku mapy nie jest domknięty.** Plik powstaje przy domykaniu
modułu i jest definicją „działa”. Zmiana zachowania ekranu, którą sam
robisz, poprawia jego plik w tej samej robocie. Przejście ścieżki głównej obszaru
aktualizuje jego wiersz w `przejscia.tsv` (SHA `origin/main`, data). Nowy
plik obszaru dostaje wiersz od razu, z `-` zamiast SHA.

## Przegląd mapy

Kiedy: przed odbiorem modułu i na prośbę. Po cudzej zmianie wystarcza
przejście dotkniętych obszarów (sekcja „Kontrola instancji”). Przebieg:

1. Spis: martwe, brakujące i zdublowane wpisy w README i `przejscia.tsv`.
2. Źródło: tylko dla obszarów z commitami od ostatniego przejścia czytasz
   diff tych commitów (`git log -p <SHA>..origin/main -- <ścieżki>`), nie
   cały kod; nowa powierzchnia jest „brakująca” dopiero z konkretną ścieżką.
3. Przejście na żywo, obowiązkowe nawet przy czystym źródle: jedna instancja,
   sterowana szeregowo, każda funkcja co najmniej raz. Zawsze trzy
   niezmienniki: kontrola instancji przed pierwszym sterowaniem i po każdym
   niepowodzeniu; dowody przetrwały każde sprzątanie (sprawdzone na dysku);
   nic, co przebieg uruchomił, nie żyje dłużej, niż jest potrzebne.
4. Rozróżnienie: zły opis → rozjazd, poprawiasz mapę. Działające zachowanie,
   którego narzędzie nie umie przejść → luka narzędzia, poprawiasz `bin/`
   i przechodzisz ponownie. Zepsute zachowanie aplikacji → regresja,
   **raportujesz, nie zamazujesz w mapie** i nie ruszasz kodu produktu
   w tym przebiegu.
5. Wynik, jeden z trzech: **czysto** (pełne pokrycie), **zmiana** (poprawki
   mapy lub `bin/`, każda dowiedziona), **zablokowane** (co dokładnie).

## Dźwignia

Gdy agenci drugi raz piszą ten sam jednorazowy skrypt do przejścia czegoś,
ten skrypt trafia do `bin/`: wykonywalny, z wywołaniem pokazanym w tym pliku
i z komunikatem błędu, który mówi, co zrobić. Mechanika do skryptu, osąd do
agenta.
