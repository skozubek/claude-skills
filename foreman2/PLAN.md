# Plan pod foremana 2.0

Plan to kontrakt etapu 0: `create --plan` wczytuje z niego kryteria odbioru, a brygadzista
buduje na nim graf zadań i trzyma się jego Granic. Od `create` plan jest zamrożony: zmianę
wpisuje człowiek i zatwierdza `create --replan --by human:<imię>`. `foreman2 plan check <plik>
[--unattended]` wylicza braki, a `create --plan` odmawia startu z brakami, więc
plan niepełny nie kosztuje tokenów. Sekcje poznaje po nagłówkach (`## Kryteria
odbioru`, `## Poza zakresem`, `## Pojęcia`, `## Granice`), ścieżkę użytkownika po linii
„Ścieżka użytkownika:”.

## Szablon

```markdown
# <Co dostaje użytkownik, jednym zdaniem>

Ścieżka użytkownika: <kto> na <ekranie> robi <co> i widzi <co>.

## Kryteria odbioru
- `<komenda odczytu, np. curl -s localhost:3000/api/n>` → `<dokładny stdout>`
- `<komenda, której kod wyjścia 0 znaczy spełnione>` → <jaki wynik ma wyjść>
- <ekran albo ścieżka na żywo, której komenda nie odczyta> → <co widać>

## Poza zakresem
- <co świadomie zostaje na później>

## Otwarte
- <obietnice większego planu, nie tej fali>

## Pojęcia
- <nowa albo zmieniana nazwa widoczna dla użytkownika>: <definicja jednym zdaniem>; unikaj: <słowa>
  (albo: „słownik modułu: <ścieżka>”, albo: „brak nowych pojęć”)

## Granice
- Zakres: zadania i pliki z grafu; poza grafem nic.
- Dane: <które projekty, konta i marki wolno czytać; w które wolno pisać; zapisy do usunięcia po przelocie; skutki automatyczne zapisów testowych (etap startowy, triggery, sygnały, wysyłki, zadania w tle): które są dozwolone i jak je sprzątasz>. Skutek niewymieniony wymaga `approval` przed zapisem.
- Tożsamość poświadczeń: <komenda dająca klucz; funkcja, która go przyjmuje; czego nie otworzy; odbiór zastępczy>.
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
- Kryterium z komendą: lewa strona w całości w grawisach. `foreman2 evidence run`
  wykonuje ją w repo na końcowym SHA; spełnione = kod wyjścia 0, a gdy prawa strona
  też jest w całości w grawisach, także stdout równy jej treści (po obcięciu białych
  znaków z brzegów). Jedna linia; dłuższy odczyt to skrypt w repo. Kryterium bez
  komendy dowodzi weryfikator na żywo i raport nazywa je słowem modelu, więc
  komendę piszesz wszędzie, gdzie odczyt da się wykonać. `plan check` pokazuje
  podział.
- Poza zakresem: czego wykonawca nie dotknie, choćby kusiło. Co najmniej jeden punkt.
- Otwarte: opcjonalne; obietnice kolejnych fal, żeby nie wpadły do zakresu tej.
- Pojęcia: nazwy, które użytkownik zobaczy na ekranie, w menu albo w danych, każda
  z definicją; gdy moduł ma słownik (`GLOSSARY.md`, `CONTEXT.md`), wystarczy
  wskaźnik. Pojęcia, które się nakładają (osoba, lead, klient), albo moduł na lata
  dostają słownik przed planem, z człowiekiem, skillem `domain-modeling`; brygadzista
  słownika nie pisze, bo rozstrzygnięcie pojęcia to decyzja o biznesie, nie fakt
  z kodu. Sekcja wymagana zawsze, choćby „brak nowych pojęć”: autor planu
  rozstrzyga to jawnie, bo skrypt nie odgadnie, czy plan wprowadza pojęcia.
- Granice: wymagane przy `--unattended`, pięć punktów z BEZ-NADZORU.md; `plan check
  --unattended` wymaga wszystkich. W przelocie nadzorowanym sekcja może zostać,
  nie jest sprawdzana.
- Czego w planie nie ma: rozstrzygnięć technicznych w zakresie (brygadzista
  przyjmuje założenie, `decide ask --kind auto`) ani listy zadań (to graf, etap 2).
  Dane produkcyjne, wysyłki, pieniądze i uprawnienia idą w decyzję `approval`,
  w planie wystarczy je nazwać.
