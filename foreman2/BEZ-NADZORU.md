# Przelot bez nadzoru

Czytasz przed pierwszym spawnem, gdy przelot jest `--unattended` albo sesja idzie
w trybie bypass/auto. Człowiek nie odpowie; każde „zapytam” zamieniasz na
założenie (`decide ask --kind auto`), decyzję w kolejce (`approval`, reszta frontu
idzie) albo krok tylko-ludzki (`human add`). Przelot bez człowieka kończy się
`partial` z listą braków częściej niż `done`, i to jest poprawny wynik.

## Granice (sekcja planu; bez niej `create --unattended` odmawia, `plan check --unattended` wylicza braki)

- Zakres: zadania i pliki z grafu; poza grafem nic.
- Dane: które projekty, konta i marki wolno czytać, w które wolno pisać. Dev serwer
  czytający produkcję wymienia projekt, konto i zapisy, które po przelocie usuwasz.
- Tożsamość poświadczeń: która komenda daje klucz, która funkcja go przyjmuje,
  czego klucz nie otworzy (np. starter wymagający tokenu użytkownika) i jaki jest
  wtedy odbiór zastępczy.
- Koszt: budżet USD jako deklaracja w `create --budget` (nic go nie egzekwuje) i limit wywołań
  płatnych (sędzia, API) per obiekt, zsumowany z całym planem przed pierwszym
  wywołaniem i liczony w trakcie w pliku licznika w katalogu przelotu, bo zadania,
  smoke i porównania biją w ten sam limit. <!-- LC-099 -->
- Kroki tylko-ludzkie z odbiorem zastępczym; po przelocie lista w `human`.

Granice nie rosną w trakcie; bramek nie osłabiasz; sekretów nie wpisujesz do
kontekstu (klucz do pliku tymczasowego, kolumny poświadczeń wybierasz po nazwie).

## Zatrzymanie

Cały przelot staje (`close --state partial --note <powód>`) przy zmianie zakresu,
findingu bezpieczeństwa, produkcji zachowującej się inaczej niż plan zakładał
i wyczerpaniu limitu wywołań płatnych z Granic. Pojedyncze zadanie blokujesz przy tym samym czerwonym CI po
dwóch poprawkach albo zmianie kontraktu bez czytelników. Po merge'u nieudany krok
odbioru to PR poprawki, nie stop.

## Ścieżka odbioru przed startem

Sprawdzasz jako operator, zanim poleci pierwszy spawn:

- tryb uprawnień bypass/auto; próbny wykonawca (sonnet, zadanie bez zmian w kodzie)
  wykonuje po jednej komendzie każdej klasy z grafu (instalacja, test, build, odczyt);
- środowisko startuje raz (dev serwer, konto testowe) i każdy krok dostawy
  przechodzi pod hookami;
- konta ról: wywołanie z oczekiwaniem 200/4xx, nie 401, per kryterium z bramką;
- dane po drucie do pliku (`curl`, `psql`, CLI z `> plik`), do kontekstu liczby
  i wycinki; dane testowe bez SQL na produkcji;
- pobranie z przeglądarki i krok kończący się dialogiem to ślepa uliczka, a karta
  w tle dławi pętle, więc postęp czytasz z bazy; <!-- LC-106 -->
- odbiór ekranu niezależny od przeglądarki człowieka: skill z profilu albo `/browse`.

Krok, którego nie da się przejść → `human add` i kryterium `unverified` z góry.

## Rachuba i limity

- Codex dzieli limit z innymi sesjami: jedno wywołanie próbne przed planowaniem
  recenzji. Bez Codexa: recenzent Claude na delcie, PR z adnotacją „bez Codexa od
  <SHA>”, merge dopiero po Codexie na bieżącym SHA.
- Limit konta Claude: sesja czeka na reset; `CronCreate` budzik godzinę po resecie
  jako zapas. Sieć pada częściej niż limit, a sesja po awarii sieci nie wraca
  sama: drugi budzik `CronCreate` stawiasz na starcie, na porę, o której człowiek
  wstaje. `/coffee` na start sesji interaktywnej.
- Po odzyskaniu sieci: `git status` w każdym worktree z rejestru; SendMessage do
  żywych agentów „dokończ i raportuj”; agent bez odpowiedzi dostaje następcę z SHA
  z rejestru.
- Żywy w tle to nie pracujący: hook Stop widzi obecność agenta, nie postęp. Każdy
  budzik i każdy powrót do pętli sprawdza wiek ostatniego commitu i pliku wyjścia
  agentów `running`. Agent bez obu przez 60 min dostaje SendMessage o stan; bez
  odpowiedzi w 30 min: diff jego worktree do pliku, `TaskStop`, następca z SHA
  i łatką. Dwóch wykonawców jednego zadania naraz nie ma.
- Koszt: `foreman2 cost --scan` (zużycie per sesja i agent z zapisów sesji, w tokenach
  ważonych, nie w USD).

## Sędzia próbki (zmiana masowa oceniana modelem)

Etykiety z ludzkiego śladu najpierw; próbka ze stałym ziarnem, zanonimizowana;
kontrole, które muszą paść; punktacja per rodzaj pola; sędzia z innej rodziny
(Codex) z tym samym przydziałem, co audytor; druga runda na świeżej próbce. Próg
względem kontroli zmierzonej tym samym narzędziem, zapisany w planie przed
pierwszym wynikiem. <!-- LC-093 -->
