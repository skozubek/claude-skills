# Przelot bez nadzoru

Czytasz przed pierwszym spawnem, gdy przelot jest `--unattended` albo sesja idzie
w trybie bypass/auto. Człowiek nie odpowie; każde „zapytam” zamieniasz na
założenie (`decide ask --kind auto`), decyzję w kolejce (`approval`, reszta frontu
idzie) albo krok tylko-ludzki (`human add`). Przelot bez człowieka kończy się
`partial` z listą braków częściej niż `done`, i to jest poprawny wynik.

## Granice (sekcja planu; bez niej przelot nie startuje)

- Zakres: zadania i pliki z grafu; poza grafem nic.
- Dane: które projekty, konta i marki wolno czytać, w które wolno pisać. Dev serwer
  czytający produkcję wymienia projekt, konto i zapisy, które po przelocie usuwasz.
- Tożsamość obiektów po nazwie i miejscu, nie po ID; odbiór zastępczy, gdy brak.
- Koszt: budżet USD (`create --budget`, runner `--max-budget-usd`) i limit wywołań
  płatnych (sędzia, API) per obiekt, liczony w planie i w `own`.
- Kroki tylko-ludzkie z odbiorem zastępczym; po przelocie lista w `human`.

Granice nie rosną w trakcie; bramek nie osłabiasz; sekretów nie wpisujesz do
kontekstu (klucz do pliku tymczasowego, kolumny poświadczeń wybierasz po nazwie).

## Zatrzymanie

Cały przelot staje (`close --state partial --note <powód>`) przy zmianie zakresu,
findingu bezpieczeństwa, produkcji zachowującej się inaczej niż plan zakładał
i wyczerpaniu budżetu. Pojedyncze zadanie blokujesz przy tym samym czerwonym CI po
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
- odbiór ekranu niezależny od przeglądarki człowieka: skill z profilu albo `/browse`.

Krok, którego nie da się przejść → `human add` i kryterium `unverified` z góry.

## Rachuba i limity

- Codex dzieli limit z innymi sesjami: jedno wywołanie próbne przed planowaniem
  recenzji. Bez Codexa: recenzent Claude na delcie, PR z adnotacją „bez Codexa od
  <SHA>”, merge dopiero po Codexie na bieżącym SHA.
- Limit konta Claude: sesja czeka na reset; `CronCreate` budzik godzinę po resecie
  jako zapas. `/coffee` na start sesji interaktywnej; runner daje `caffeinate`.
- Po odzyskaniu sieci: `git status` w każdym worktree z rejestru; SendMessage do
  żywych agentów „dokończ i raportuj”; agent bez odpowiedzi dostaje następcę z SHA
  z rejestru.
- Koszt: `cost` w run.json (runner zapisuje z `claude -p`); sesja interaktywna
  `koszty.py`.

## Sędzia próbki (zmiana masowa oceniana modelem)

Etykiety z ludzkiego śladu najpierw; próbka ze stałym ziarnem, zanonimizowana;
kontrole, które muszą paść; punktacja per rodzaj pola; sędzia z innej rodziny
(Codex) z tym samym przydziałem, co audytor; druga runda na świeżej próbce. Próg
względem kontroli zmierzonej tym samym narzędziem, zapisany w planie przed
pierwszym wynikiem.
