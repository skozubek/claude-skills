# Foreman: przelot bez nadzoru

Czytasz przed pierwszym spawnem każdego przelotu, przy którym bramek nie
pilnuje człowiek. Bez tego pliku bramki, które kosztują pieniądze albo
dotykają produkcji, agent pomija albo przyznaje je sobie sam.

## Mandat

Przelot startuje z mandatem spisanym w pliku projektu, przed startem.
Wzorzec: `~/Coding/MOL/Panel/meta/seo-geo/MANDAT-AUTONOMII.md`. Mandat wymienia
jawnie:

- zakres: które zadania, które pliki, a znalezisko spoza zakresu idzie do
  raportu;
- co wolno wydać: płatne evale, wywołania modeli, z limitem liczbowym;
- co wolno wypchnąć i wdrożyć: commit, push, gałąź kontra `main`, wdrożenie
  i na czym;
- zakres danych: projekty, konta, marki;
- z nazwy i miejsca sekrety, tożsamości i adres produkcji: który `.env`, która
  karta przeglądarki, którą funkcją się startuje; klasyfikator uprawnień odmówi
  wyciągnięcia tokenu z przeglądarki, więc tożsamość zostaje w karcie,
  a wywołania idą JS-em w niej;
- bramki z człowiekiem: miejsca, w których przelot staje i czeka.

Wszystko spoza mandatu jest poza zakresem. Mandatu sesja nie edytuje sama.

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
- każde kryterium odbioru z planu da się wykonać w kopercie mandatu; kryterium
  wymagające czynności spoza mandatu wychodzi na jaw przy odbiorze, gdy nie ma
  już kogo zapytać.

Gotowe, gdy każde kryterium odbioru z planu ma przypisaną komendę, konto
i miejsce odczytu.

## Rachuba w trakcie

- **Licznik płatnych wywołań per obiekt** (strona, klient, dokument) w notatce
  stanu, od pierwszego wywołania. Zadania, smoke i porównania biją w ten sam
  limit z trzech miejsc. Limit mandatu sumujesz z całym planem briefu przed
  pierwszym wywołaniem: plan potrafi go przekroczyć, choć każdy etap z osobna
  się mieści (LC-099).
- **Limit sesji nie kończy przelotu.** Sesja interaktywna czeka na reset
  i wznawia się sama (`autoContinueAtUsageLimit`), ale poddaje się po dwóch
  odcięciach z rzędu, a po ponad 30 minutach snu Maca czeka na Enter. Stąd
  sesja nocna startuje od `/coffee` (LC-038), a budzik zapasowy (`CronCreate`
  godzinę po zgłoszonym resecie) podnosi przelot, który się poddał. Tryb
  `claude -p` nie czeka wcale: wznowienie trzyma skrypt startowy (wzór
  `campaign-builder/scripts/night-loop.sh`).
- **Sędzia próbki** tam, gdzie próg mówi „ocena człowieka": model spoza rodziny
  wykonawcy (Codex; przy dużej próbce `-m gpt-6-luna`, jeśli na kilku
  przypadkach z oczywistym werdyktem zgadza się z Sol), zanonimizowana próbka, status ustalony przed pokazaniem werdyktu,
  ten sam przydział i kontekst decyzyjny, który miał audytor (LC-093).
- **Progi ogłaszane przed liczbami.** Kryterium zaliczenia stoi w planie przed
  pierwszym wynikiem; próg dopisany po zobaczeniu liczb to opis.
- **Blokada zatrzymuje zadanie, nie przelot.** Zablokowane zadanie kończy się
  wpisem „czego brakuje, co próbowano", pozostałe gałęzie grafu idą dalej.
