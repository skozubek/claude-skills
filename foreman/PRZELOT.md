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
- stop i raport („czego brakuje, co próbowano”), gdy trzeba zmienić kontrakt
  albo zakres poza planem, gdy pojawia się ustalenie dotyczące
  bezpieczeństwa, gdy to samo CI jest czerwone po dwóch próbach naprawy,
  gdy produkcja zachowuje się inaczej, niż zakłada plan, i gdy limit kosztu
  się wyczerpał;
- merge, wdrożenie i odbiór na produkcji to trzy osobne kamienie meldunku.

## Droga odbioru, sprawdzona przed startem

Przejdź ją jako operator, odczytem, nie z pamięci:

- sesja biegnie w trybie uprawnień, który nie pyta (bypass albo `auto`);
  agent w tle przekazuje pytanie o zgodę do głównej sesji, gdzie bez człowieka
  wisi do rana; próbny wykonawca puszcza raz każdą klasę komend z planu
  (instalacja, testy, commit) i wraca bez pytania;

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

Gotowe, gdy każde kryterium odbioru z planu ma przypisaną komendę, konto
i miejsce odczytu.

## Rachuba w trakcie

- **Licznik płatnych wywołań per obiekt** (strona, klient, dokument) w notatce
  stanu, od pierwszego wywołania. Zadania, smoke i porównania biją w ten sam
  limit z trzech miejsc. Limit z granic sumujesz z całym planem briefu przed
  pierwszym wywołaniem: plan potrafi go przekroczyć, choć każdy etap z osobna
  się mieści (LC-099).
- **Limit sesji nie kończy przelotu.** Zwykła sesja sama czeka na reset
  i rusza dalej (`autoContinueAtUsageLimit`). Dwie pułapki: po dwóch
  odcięciach z rzędu się poddaje, a gdy Mac przespał ponad 30 minut, czeka
  na Enter. Dlatego sesja nocna startuje od `/coffee` (LC-038), a budzik
  zapasowy (`CronCreate`, godzina po zgłoszonym resecie) podnosi przelot,
  który się poddał. Tryb `claude -p` na reset nie czeka wcale; wznawia go
  skrypt startowy (wzór: `campaign-builder/scripts/night-loop.sh`).
- **Sędzia próbki** tam, gdzie próg mówi „ocena człowieka": model spoza rodziny
  wykonawcy (Codex; przy dużej próbce `-m gpt-6-luna`, jeśli na kilku
  przypadkach z oczywistym werdyktem zgadza się z Sol), zanonimizowana próbka, status ustalony przed pokazaniem werdyktu,
  ten sam przydział i kontekst decyzyjny, który miał audytor (LC-093).
- **Progi ogłaszane przed liczbami.** Kryterium zaliczenia stoi w planie przed
  pierwszym wynikiem; próg dopisany po zobaczeniu liczb to opis.
- **Blokada zatrzymuje zadanie, nie przelot.** Zablokowane zadanie kończy się
  wpisem „czego brakuje, co próbowano", pozostałe gałęzie grafu idą dalej.
