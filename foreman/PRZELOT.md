# Foreman: przelot bez nadzoru

Czytasz przed pierwszym spawnem każdego przelotu, przy którym bramek nie
pilnuje człowiek. Bez tego pliku bramki, które kosztują pieniądze albo
dotykają produkcji, agent pomija albo przyznaje je sobie sam.

## Granice

Przelot startuje dopiero, gdy plan ma sekcję „Granice”, spisaną przed startem.
Zasady repo (`AGENTS.md`/`CLAUDE.md`) obowiązują bez powtarzania. Granice
wymieniają jawnie:

- zakres: zadania i pliki z grafu; znalezisko spoza zakresu idzie do raportu;
- dane: na których kontach, markach i projektach przelot zapisuje na
  produkcji, a gdzie tylko czyta;
- tożsamość z nazwy i miejsca: która komenda daje klucz, która funkcja go
  przyjmuje, czego klucz nie otworzy (np. starter wymagający tokenu
  użytkownika) i jaki jest wtedy zastępczy odbiór;
- koszt: płatne wywołania z limitem liczbowym;
- kroki, których przelot nie wykona sam (publikacja przez przeglądarkę,
  wiadomość do człowieka, logowanie czyimś kontem): każdy ma zastępczy
  odbiór w przelocie i linię „do zrobienia po przelocie” w raporcie
  końcowym.

Granic sesja nie poszerza w trakcie. Zawsze, w każdym przelocie:

- nie osłabiasz bramek: bez pomijania testów, rozluźniania asercji,
  podnoszenia progów i wyjątków w kontrolach CI;
- stop całego przelotu i raport („czego brakuje, co próbowano”), gdy trzeba
  zmienić zakres poza planem, gdy pojawia się ustalenie dotyczące
  bezpieczeństwa, gdy produkcja zachowuje się inaczej, niż zakłada plan,
  i gdy limit kosztu się wyczerpał;
- blokada jednego zadania (reszta grafu idzie dalej), gdy to samo CI jest
  czerwone po dwóch próbach naprawy albo zadanie wymaga zmiany kontraktu,
  której czytelnicy nie są w grafie;
- merge, wdrożenie i odbiór na produkcji to trzy osobne kamienie meldunku.

## Droga odbioru, sprawdzona przed startem

Przejdź ją jako operator, odczytem, nie z pamięci:

- sesja biegnie w trybie uprawnień, który nie pyta (bypass albo `auto`);
  agent w tle przekazuje pytanie o zgodę do głównej sesji, gdzie bez człowieka
  wisi do rana; próbny wykonawca puszcza raz każdą klasę komend z planu
  (instalacja, testy, commit) i wraca bez pytania; każdy krok „Kolejności
  wdrożenia” z planu brygadzista sprawdza pod hookami sesji bez człowieka
  (zapis na żywej bazie poza migracją hook odrzuca), a krok bez drogi dostaje
  przed startem linię „do zrobienia po przelocie” i zastępczy odbiór;

- konto, które będzie wołać narzędzia, ma rolę, którą przepuści bramka z planu;
  plan z bramką „tylko admin" przy koncie pracownika staje na pierwszym
  wywołaniu;
- każdy rodzaj danych schodzi na dysk drutem bez gestu człowieka
  (`supabase db query --linked … > plik` po `supabase link` w worktree);
  pobranie z przeglądarki i każdy krok kończący się dialogiem to w przelocie
  ślepa uliczka; karta w tle dławi pętle, więc postęp czyta się z bazy (LC-106);
- każde kryterium odbioru z planu da się wykonać w granicach planu; kryterium
  wymagające czynności spoza granic wychodzi na jaw przy odbiorze, gdy nie ma
  już kogo zapytać.

- odbiór ekranu nie zależy od przeglądarki człowieka: rozszerzenie w Brave
  pada razem z siecią i wraca dopiero po jego ruchu. Sesję zalogowaną dla
  gstack mintuje się bez klikania (przepis w [PULAPKI.md](PULAPKI.md)), ale
  dev serwer na localhost czyta ten sam projekt Supabase co produkcja, więc
  Granice wymieniają projekt, konto, dozwolone zapisy i sposób zdjęcia
  dostępu po odbiorze; konto spoza Granic odbiera człowiek po przelocie;
- tożsamość jest sprawdzona dopiero po jednym prawdziwym wywołaniu każdej
  bramki z planu, z odpowiedzią, którą plan zapowiada (200 albo konkretny
  4xx z treścią bramki; 401 znaczy, że tożsamość nie działa), nie po
  odczycie, skąd wziąć klucz: funkcja porównuje Bearer z kluczem
  wstrzykniętym przez platformę (`sb_secret_…`), a lista kluczy CLI pokazuje
  też legacy `service_role`, który daje 401 (MOL/Panel/meta/LEKCJE.md
  2026-10-10).

Gotowe, gdy każde kryterium odbioru z planu ma przypisaną komendę, konto
i miejsce odczytu.

## Rachuba w trakcie

- **Licznik płatnych wywołań per obiekt** (strona, klient, dokument) w pliku
  rejestru przelotu, od pierwszego wywołania. Zadania, smoke i porównania biją w ten sam
  limit z trzech miejsc. Limit z granic sumujesz z całym planem briefu przed
  pierwszym wywołaniem: plan potrafi go przekroczyć, choć każdy etap z osobna
  się mieści (LC-099).
- **Sieć i limit.** Sieć pada częściej niż limit, a sesja po awarii sieci nie
  wraca sama. Przelot startuje od `/coffee` (LC-038) i budzika zapasowego
  (`CronCreate`) postawionego od razu, na porę, o której Serge wstaje; drugi
  budzik stawiasz godzinę po każdym zgłoszonym resecie limitu, bo sesja po
  dwóch odcięciach z rzędu się poddaje, a po ponad 30 minutach snu Maca
  czeka na Enter. Po podniesieniu: `git status` w worktree z rejestru,
  agenty floty wznawiasz `SendMessage` (worktree trzyma niezacommitowaną
  robotę), czas awarii nie liczy się do czasu zadania
  (MOL/Panel/meta/LEKCJE.md 2026-10-11). Tryb `claude -p` na reset nie
  czeka wcale; wznawia go skrypt startowy (wzór:
  `campaign-builder/scripts/night-loop.sh`).
- **Sędzia próbki** tam, gdzie próg mówi „ocena człowieka”. Procedura,
  ustalona przed pierwszą rundą (LC-093, MOL/Panel/meta/LEKCJE.md
  2026-10-11):
  1. losowanie próbki ze stałym ziarnem do pliku, zanonimizowanej, ze
     statusem każdego elementu zapisanym przed pokazaniem werdyktu;
  2. w próbce kontrola: elementy, o których wiesz, że muszą oblać; runda,
     w której kontrola przechodzi, jest nieważna;
  3. punktacja per rodzaj pola: pole z akcją ocenia „wiem, co zrobić”,
     pole bez akcji ocenia się po słowach (zrozumiałość bez żargonu);
  4. sędzia z innej rodziny niż wykonawca (Codex, model z `~/.codex/config.toml`,
     bez `-m`), z tym samym przydziałem i kontekstem, który miał autor;
  5. druga runda: te same elementy plus świeża próbka wylosowana przed
     poprawką, żeby poprawka nie uczyła się pod test; skrypt sprawdzający
     słowa nie zastępuje czytania pola po polu.
- **Progi ogłaszane przed liczbami.** Kryterium zaliczenia stoi w planie przed
  pierwszym wynikiem; próg dopisany po zobaczeniu liczb to opis.
