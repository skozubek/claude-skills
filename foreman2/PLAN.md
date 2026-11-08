# Plan pod foremana 2.0

Plan to kontrakt etapu 0: brygadzista zamienia go w kryteria odbioru
(`criteria add`), graf zadań i Granice przelotu. `foreman2 plan check <plik>
[--unattended]` wylicza braki, a `create --plan` odmawia startu z brakami, więc
plan niepełny nie kosztuje tokenów. Sekcje poznaje po nagłówkach (`## Kryteria
odbioru`, `## Poza zakresem`, `## Granice`), ścieżkę użytkownika po linii
„Ścieżka użytkownika:”.

## Szablon

```markdown
# <Co dostaje użytkownik, jednym zdaniem>

Ścieżka użytkownika: <kto> na <ekranie> robi <co> i widzi <co>.

## Kryteria odbioru
- <co odczytać: ekran / odpowiedź API / wiersz w bazie / czas tym samym narzędziem i kontem> → <jaki wynik ma wyjść>
- <drugie kryterium> → <wynik>

## Poza zakresem
- <co świadomie zostaje na później>

## Otwarte
- <obietnice większego planu, nie tej fali>

## Granice
- Zakres: zadania i pliki z grafu; poza grafem nic.
- Dane: <które projekty, konta i marki wolno czytać; w które wolno pisać; zapisy do usunięcia po przelocie>.
- Tożsamość obiektów po nazwie i miejscu, nie po ID; odbiór zastępczy, gdy brak.
- Koszt: budżet <N> USD; limit wywołań płatnych per obiekt: <N albo „brak”>.
- Kroki tylko-ludzkie: <lista albo „żadne”>; odbiór zastępczy: <jak>.
```

## Co jest czym

- Ścieżka użytkownika: jedno zdanie, które weryfikator przejdzie na żywo
  (verify-admotiv, `/browse`). Bez niej nie ma czego odebrać.
- Kryterium: odczyt → wynik. Odczyt nazywa miejsce (ekran, endpoint, tabela,
  pomiar) i narzędzie; wynik jest rozstrzygalny bez dyskusji. Dwa do pięciu;
  większy plan dzielisz na fale, reszta idzie do „Otwarte”. „Testy zielone”,
  „kod zrefaktorowany”, „działa” nie są kryteriami.
- Poza zakresem: czego wykonawca nie dotknie, choćby kusiło. Co najmniej jeden punkt.
- Otwarte: opcjonalne; obietnice kolejnych fal, żeby nie wpadły do zakresu tej.
- Granice: wymagane przy `--unattended`, pięć punktów z BEZ-NADZORU.md; `plan check
  --unattended` wymaga wszystkich. W przelocie nadzorowanym sekcja może zostać,
  nie jest sprawdzana.
- Czego w planie nie ma: rozstrzygnięć technicznych w zakresie (brygadzista
  przyjmuje założenie, `decide ask --kind auto`) ani listy zadań (to graf, etap 2).
  Dane produkcyjne, wysyłki, pieniądze i uprawnienia idą w decyzję `approval`,
  w planie wystarczy je nazwać.
