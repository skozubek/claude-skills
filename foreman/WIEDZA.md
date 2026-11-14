# Wiedza brygadzisty

Czytasz w rekonesansie tylko sekcje, których wyzwalacz pasuje do planu. Reguła,
która zmienia graf albo brief, trafia do nich i do `kontrakt.md` przelotu przed pierwszym
spawnem; reguła, która zmienia kryterium, idzie do człowieka (plan jest zamrożony).

## Gdy przelot jest falą większego planu albo obiecuje ekran 1:1 lub moduł

- Każdemu wierszowi i zdaniu większego planu przypisanemu tej fali daj w planie werdykt „dowozi (kryterium)”, „przenosi (fala, pozycja)” albo „rezygnacja (wpis w dzienniku decyzji)”, a wiersz bez werdyktu traktuj jak brak planu, bo plan fali zawęża zakres po cichu, a każdy strażnik niżej pilnuje już zawężonego. <!-- LC-114 -->
- Drugiej opinii (etap 0) daj plan razem z tą księgą, bo zawężenie widać tylko obok oryginału.
- Obietnicę „1:1 z ekranem X” zacznij zadaniem inwentarza klocków oryginału (zakładki, kontrolki, drill, podpisy) z kryterium „każdy klocek jest albo celowo inaczej”, a zgodność liczb zapisz jako osobne kryterium, bo „te same liczby” po cichu zastępuje „ten sam ekran”.
- Obietnicę nazwaną modułem rozpisz na ekrany z menu wzorca, każdy z werdyktem, bo jedna ścieżka użytkownika zostawia resztę modułu bez werdyktu. <!-- LC-114 -->
- Ekranowi przenoszonemu z innego systemu wpisz w kryteria jego okresy, filtry i układ, bo „jak w X” nie jest kryterium.

## Gdy kryterium czeka na zdarzenia albo prawdziwy ruch

- Zdarzenie, którego kryterium potrzebuje (wejście rekordu, przebieg joba, upływ progu), wywołaj w przelocie: rekord testowy wejściem produkcji, ręczny start joba z crona, zegar przesunięty w teście, bo czekanie na ruch trzyma przelot otwarty bez końca.
- Okno ruchu (próg zapisany przed wynikiem, bez zdarzeń `unverified`) zostaw tylko kryterium, które mierzy rozkład prawdziwego ruchu, bo każde inne da się wywołać.
- Okno użyteczności puść w tle bez trzymania przelotu, a okno bezpieczeństwa (wyciek, zły adresat, prawdziwy rekord w spamie) traktuj jak blokadę, bo czekać warto tylko na szkodę cichą i trudną do cofnięcia.

## Gdy kryterium ma próg jakości, sędziego albo miernik różnic

- Próg jakości (klasyfikator, sędzia, dopasowanie) podziel na bezpieczeństwo, które blokuje, i użyteczność, której niezaliczenie idzie do człowieka jako `approval` z liczbami, bo jeden próg dla obu robi teatr z modelu bezpiecznego, ale mniej przydatnego.
- Miernikowi z listą oczekiwanych różnic daj w weryfikacji po jednym wstrzykniętym defekcie w kategorii każdej pozycji listy i wymagaj, by każdy wyszedł jako nieoczekiwany, bo lista tłumaczy usterkę z własnej kategorii, a kanarek spoza listy tego nie sprawdzi.
- Werdykt miernika „zgodne” przy dużej różnicy liczb przyjmij dopiero po obejrzeniu rozkładu rekordów różnicy po pozycjach listy, bo skrypt liczy kategorie, nie sens.
- Zmianę masową, której próbka wypadła poniżej progu, przenieś na opus-high przed całością, bo tańszy wariant przerobi wszystko z tym samym błędem.
- Status każdego elementu próbki zapisz przed pokazaniem werdyktu, bo zapis po werdykcie dopasowuje się do niego.
- Sędziemu daj dokładnie wejście modelu (te same pola, nie wycinek), bo sędzia z innym materiałem ocenia inne zadanie.
- Przed etykietami policz elementy każdej klasy, a kryterium z klasą poniżej progu oznacz `unverified`, bo próbka z bieżącego ruchu potrafi nie mieć ani jednego trudnego przypadku.
- Drugą rundę sędziego puść na tych samych elementach plus świeżej próbce wylosowanej przed poprawką, bo inaczej poprawka uczy się pod test.
- Wynik sędziego czytaj pole po polu także wtedy, gdy skrypt sprawdził słowa, bo poprawne słowo bywa w fałszywym zdaniu.

## Gdy zmiana wciąga dane z obcego systemu albo czyści pole (import, sync, lustro)

- Pole z obcego systemu, na którym plan stawia regułę (czas, status, identyfikator), przeczytaj w kodzie, który je wylicza, i wskaż w planie plik i funkcję, bo nazwa pola to hipoteza.
- W kryterium wejścia danych odczytaj rozkład wszystkiego, co weszło w pierwszym przebiegu (liczba, zakres dat, źródła), nie tylko rekord testowy, bo synchronizacja wciąga obok testu cały śmietnik źródła.
- Zapisz w planie, co import przenosi (treść notatek, maili, załączników) i kto to zobaczy po stronie docelowej i w raportach, bo dane dostępowe z notatek lądują u całej roli.
- Usunięcie albo archiwizację na podstawie nieobecności rekordu uruchom dopiero po dowodzie, że źródło oddaje komplet, bo brak na liście to nie sygnał usunięcia.
- Przy czyszczeniu albo przeliczaniu pola puść każdego czytelnika tego pola na próbce przed i po, najpierw tych, którzy na słabym sygnale tworzą dane, bo konsument stojący na brudzie psuje się po cichu. <!-- LC-104 -->

## Gdy zmiana dodaje powierzchnię albo zmienia sposób wywołania

- Nową powierzchnię (endpoint, funkcję, typ zdarzenia, rolę) dopisz do każdej bramki, która ją filtruje (rejestr, allowlista, mapa handlerów), i wpisz tę bramkę do plików zadania, bo niedopisana powierzchnia jest niewidoczna dokładnie tam, gdzie ma działać.
- Zmianę wywołania z przeglądarki (nagłówek, region, adres funkcji) dowiedź zapytaniem wstępnym `OPTIONS` z nagłówkami, które wyśle SDK, bo curl POST i atrapa klienta nie widzą CORS.

## Gdy plan stoi na liczbie albo pomiar biegnie na produkcji

- Limity, sufity i objętości, na których stoi plan, zmierz zapytaniem i wpisz do planu z komendą, bo liczba z pamięci rozjeżdża się z produkcją.
- Testy repo z twardym progiem czasu albo pamięci (`grep -rnE "toBeLessThan|performance\.now"` po testach) sprawdź z zapasem wobec gałęzi domyślnej, bo test czerwony pod obciążeniem oblewa CI następnego przelotu.
- W pętli „napraw → zmierz ponownie” zapisz w planie, co jest materiałem pomiaru, kto go odświeża i czy użytkownik ma ten krok na ekranie, bo fakt spoza kodu nie wyjdzie z żadnej recenzji. <!-- LC-111 -->
- Przebiegowi pomiarowemu na funkcji produkcyjnej policz w planie zużycie jej dobowego limitu i kolejki, bo dzieli je z ruchem użytkowników.
- Ograniczenie na wspólnym zasobie (baza, port, karta przeglądarki, limit i kolejka funkcji) przekaż każdemu żyjącemu piszącemu, nie tylko następnemu spawnowi, bo żyjący agent nie czyta nowego briefu. <!-- LC-029 -->
- Gdy zmiana ma migrację, a środowisko odbioru czyta produkcyjną bazę, przed merge'em przechodź tylko kroki odczytu, zapis dowodź testami SQL na kopii, a kroki zapisu przejdź po merge'u i migracji na rekordach z Granic, bo migracja trafia na produkcję dopiero z merge'em.

## Gdy zmiana dotyka zdarzeń, kolejki, maszyny stanów albo crona

- Łączeniu albo deduplikacji zdarzeń z kilku źródeł daj w planie definicję tożsamości zdarzenia i test każdej kolejności przybycia, bo reguła pisana per kolejność odsłania przy każdej poprawce następną.
- W tabeli przejść maszyny stanów zapisz przy każdym przejściu, kto zapisuje i które stany zajmują albo zwalniają tożsamość, bo bez tego dwaj wykonawcy czytają kontrakt inaczej.
- Wypisz w planie wszystkie drogi w kodzie, które zmieniają stan wejściowy (grep po zapisie), nie tylko drogę z historyjki, bo poprawka omija drogę, której nikt nie spisał.
- Gdy kilka z tych dróg (zapis sesji, funkcje bazy, lustro, formularz) blokuje te same rekordy, `kontrakt.md` dostaje przed spawnem jeden model blokad: tryb i kolejność w każdej drodze. Bez niego recenzja znajduje wyścigi pojedynczo, a każda łatka odsłania następny.
- Zadaniu wymagającemu atomowości (odczyt i zapis w osobnych krokach, warunek zależny od cudzych zdarzeń, ponowienie) wskaż istniejący mechanizm (funkcja transakcyjna, zapis warunkowy) i test współbieżności albo ponowienia, bo wariant obok bazy przechodzi testy i pada na recenzji.
- Zadanie, którego mechanizmu atomowości nie ma, a dodanie wychodzi poza zakres, zatrzymaj poza grafem do decyzji `approval` (poszerzyć albo wyciąć), bo bez mechanizmu nie ma poprawnej implementacji.
- Wdrożenie w kilku krokach pod zadaniem cyklicznym puść jednym ciągiem między przebiegami, z odczytem przebiegów przed pierwszym krokiem i po ostatnim, bo przebieg między krokami tworzy stan, którego nie zakłada żaden krok.
- Kod pod zadaniem cyklicznym pisz na kolejności możliwe także poza oknem wdrożenia (ponowienie, ruch użytkownika, opóźniony job), bo okno zamyka tylko kolejności samego wdrożenia.

## Gdy zmiana dotyka ekranu

- Do czytelników ekranu dopisz jego opakowanie (nagłówek i opis strony, pozycja menu, ścieżka, pomoc „?”), nawet gdy diff go nie dotyka, bo użytkownik czyta je razem z ekranem.
- W kryteriach ekranu wskaż wzorzec z repo (klocek tabeli, panelu, filtrów) i sąsiednie ekrany, z którymi ma być spójny, bo „ładnie” nie jest rozstrzygalne.
- Zmianę zachowania ekranu domknij poprawką jego pomocy w tym samym przelocie i podaj recenzentowi ścieżki plików pomocy wprost, bo pomoc leży poza diffem.
- Błąd zgłoszony zrzutem albo opisem zacznij od jednego pytania o warunki, których zrzut nie niesie (zoom, szerokość okna, co rozwinięte, produkcja czy lokalnie), bo wykonawca bez nich mierzy stan, w którym błędu nie ma.
- Odbiór na żywo karm danymi z tego samego źródła co produkcja, bo spreparowane dane omijają przypadki, które psują ekran.
- Przed spawnem weryfikatora sprawdź sam, tanio, że logowanie narzędzia przejścia i baza odpowiadają, bo weryfikator bez nich pali przebieg na niczym.
- Wolne zapytanie ekranu bez progu w kryteriach wpisz do meldunku jako decyzję człowieka z liczbą (czas ekranu z raportu weryfikatora, czas wywołania ze smoke), bo odłożone bez progu nie wraca.

## Gdy moduł ma słownik albo plan wprowadza pojęcia

- Plan, brief i nazwy w kodzie mówią słowami ze słownika modułu (`GLOSSARY.md`, `CONTEXT.md`) albo z sekcji „Pojęcia” planu, a brief wykonawcy i recenzenta dostaje ścieżkę słownika, bo agent bez niego sam wybiera słowo i idzie dalej.
- Nazwę ekranu, pozycji menu albo ścieżki ze słowem z listy „unikaj” w obszarze zmiany wpisz do grafu jako zadanie zmiany nazwy z przekierowaniem starej ścieżki i szukaj jej po całym ekranie, nie po diffie, bo stara nazwa leży poza diffem i przeżywa falę.
- Nowe pojęcie bez definicji w planie ani słowniku to pytanie do człowieka przed spawnem (bez nadzoru: `approval`, zadania z tym pojęciem czekają), nie założenie, bo słownik napisany przez agenta utrwala jego zgadywanie.

## Gdy graf ma pliki generowane, wspólne rejestry albo zadania tekstu

- Plik generowany z innego (kopia pomocy, typy) przy konflikcie scalenia odtwórz generatorem, nie scalaj, bo ręcznie scalona kopia rozjeżdża się ze źródłem.
- Zadaniu zmieniającemu źródło generowanej kopii daj w weryfikacji generator i `git diff` kopii, a w grafie wdrożenie funkcji, które kopię importują, bo inaczej CI czerwienieje, a te funkcje chodzą na starej kopii.
- Wspólnemu rejestrowi (lista konsumentów, manifest) daj w grafie jednego właściciela w każdym PR-ze, który go dotyka, bo dwa zadania dopisujące równolegle gubią wpis.
- Zadaniu tekstu (pomoc, opisy ekranów, komunikaty) daj w briefie listę „działa po tym PR-ze / przychodzi później”, bo bez niej tekst opisuje plan zamiast kodu.
- Zadanie tekstu uzależnij od każdego zadania, które opisywane zachowanie zmienia, i puść je po scaleniu ich poprawek, bo tekst pisany obok rund kodu wraca z każdą rundą.
- Zadanie tekstu otwórz na nowo przy każdej późniejszej zmianie opisanego zachowania, bo scalony tekst przestaje być prawdą bez żadnego sygnału.
- Nie każ w briefie redagować plików, których mandat przelotu nie pozwala zmienić, tylko zapisz rozjazd wierszem do zadań, bo gotowe zdania bez prawa zapisu to spalony koszt.

## Gdy graf ma kontrakt dla kolejnych frontów albo kilka PR-ów

- Zmiany zielone dopiero razem (schemat i jego konsument) złącz w jedno zadanie, bo każde scalenie ma zostawić integrację zieloną.
- Po scaleniu zadania, które dotknęło plików albo kontraktu innego scalonego, puść pełną weryfikację od razu, bo regresja znaleziona po zamknięciu frontu nie ma już winnego.
- Zadaniu ustalającemu kontrakt, z którego biorą następne fronty, daj recenzenta świeżym okiem zaraz po scaleniu i licz go do żywych agentów, bo błąd kontraktu mnoży się w każdym zadaniu, które na nim stoi.
- Robocie idącej kilkoma PR-ami zapisz w planie ich granice (zadanie, front albo całość) i zależności, bo każdy merge przesuwa bazę i numery migracji reszty.

## Gdy przelot wznawia cudzy plan albo przekazaną sesję

- Przed pierwszym spawnem sprawdź graf wobec czytelników i mapy funkcji repo, gdy ją ma, bo cudzy plan nie zna zmian od chwili, gdy go pisano.
- Nazwy tabel i pól kontraktu sprawdź jednym zapytaniem do schematu, bo plan potrafi stać na kolumnach, których nie ma.
- Zadania agentów poprzedniej sesji oddaj nowym wykonawcom z SHA, raportem i worktree poprzednika jako wejściem, bo `SendMessage` nie sięga agentów innej sesji, a ich niezacommitowana robota leży w worktree.

## Gdy przelot coś kasuje, zostawia materiał albo sprząta

- Wariant wycięty przed merge'em, który ma przeżyć, commitnij na gałęzi `material/<temat>` i podaj w rejestrze i meldunku jej nazwę, SHA i powód, bo gałąź z nazwą agenta ginie przy sprzątaniu po wzorcu. <!-- LC-117 -->
- Worktree bez wpisu w rejestrze nazwij cudzym dopiero, gdy jego ścieżki nie ma w zapisach subagentów przelotu (`<sesja>/subagents/agent-*.jsonl`), bo rejestr bywa niepełny po przekazaniu sesji.
- Werdykt „kasuj” (agenta odczytu albo własny) wykonaj dopiero po grepie nazwy pliku w całym katalogu notatek i w skillach, bo plik bywa czytany przez narzędzie spoza repo.

## Gdy Codex zawodzi albo równolegle biegnie inny przelot

- Wyczerpanie limitu Codexa rozpoznaj tylko po jawnym komunikacie narzędzia, a każdy inny błąd diagnozuj osobno, bo pomyłka zamienia awarię w czekanie na limit.
- Wymień w planie recenzje Codexa (plan, PR), nie każdą rundę, i wpisuj zużycie do jednego pliku wspólnego dla równoległych przelotów z tego konta, bo dzielą one jeden limit i tracą drugie oko w tej samej minucie. <!-- LC-118 -->
