---
name: audyt-wygladu
description: Audyt spójności wyglądu modułu albo serwisu — populacja powierzchni i wymiarów, pomiar wyliczonych stylów na żywo, pochodzenie wartości, mechanizm rozjazdu. Tylko czyta.
disable-model-invocation: true
---

# Audyt spójności wyglądu

Odpowiada na pytanie „czy ten system wyglądu jest jeden i czy następny
autor (człowiek albo agent) nauczy się z kodu dobrego wzoru”. Tylko czyta
i mierzy; plan naprawy powstaje po lekturze wyniku przez Serge'a.

Rdzeń metody to **populacja przed filtrem**: najpierw wyliczasz wszystko, co
istnieje (powierzchnie, wymiary), potem szukasz rozjazdu w każdej komórce.
Filtr znajduje tylko to, co przewidziałeś; pokrycie dowodzi wyliczenie.

## Wejście

Z polecenia: moduł albo serwis, repo, właściciel. Moduł cudzy (np. moduły
Piotra w AdMotiv) przechodzi ten sam audyt, a wynik jest raportem dla
właściciela: bez planu, bez strażników, bez zmian w jego kodzie; przed
startem ustal z Serge'em, że właściciel raport chce.

Katalog roboczy: `research/audyt-wygladu-<modul>-<RRRR-MM>/` w repo albo
w meta projektu. Pierwsza linia `NOTATKA.md` to zdanie zadania dosłownie.
Surowe dane (JSON pomiaru, wyniki skanów) idą do plików; do kontekstu
wchodzą liczby i wycinki.

## Kroki

1. **Kanon.** Przeczytaj, co repo mówi o wyglądzie: DESIGN/UI w `docs/`,
   lista klocków w CLAUDE.md repo, tokeny (`:root`, `@theme`, config
   Tailwinda), `~/Coding/_context/UI-ZASADY.md`, dziennik decyzji (grep po
   „wygląd”, „skala”, „token”, „rola” i nazwach strażników). Rozjazd opisany
   decyzją jest zamierzony. Gotowe: wiesz, gdzie mieszka każda wartość
   kanoniczna albo że kanonu nie ma (to jest pierwsze znalezisko).

2. **Populacja powierzchni.** Wylicz komendą: każda trasa i plik specjalny
   frameworka (w Next: `git ls-files <app> | grep -E
   '/(page|layout|route|not-found|error|global-error|loading|opengraph-image|icon)\.'`),
   do tego kanały poza trasami: maile i ich szablony, PDF-y, eksporty, obrazy
   OG, modale i szuflady, stany puste, ładowania i błędu, strona 404.
   Komenda idzie do notatki. Gotowe: tabela powierzchni, w której znana
   powierzchnia (kanarek) jest na liście, a każdy wiersz ma lokalizację
   w kodzie i dyscyplinę (gdzie mieszkają jego wartości).

3. **Populacja wymiarów.** Każdy wymiar z listy niżej dostaje jeden stan:
   rozjazd (plik + funkcja/selektor + wartości + liczba wystąpień),
   sprawdzone i czysto (czym), nie dało się sprawdzić (dlaczego). Gotowe:
   żadna komórka pusta.

4. **Pomiar żywego ekranu.** `bin/pomiar.mjs` (nagłówek pliku mówi, jak):
   każdy węzeł tekstu i każdy element interaktywny, wyliczone style,
   emulacja ograniczonego ruchu, po załadowaniu fontów, kanarek. Szerokości
   co najmniej 390 i 1440, przy układzie z punktami łamania także ich
   granice. Za logowaniem: sesja z logowania drogą repo (AdMotiv:
   `verify-admotiv`) zapisana jako `storageState`; tekst nie trafia do
   wyniku. `bin/analiza.py pomiar.json` daje liczby kontrolne, a przy
   odbiorze `bin/progi.py` sześć progów przed i po (nagłówek pliku). Gotowe:
   pomiar każdej powierzchni z kroku 2, która ma ekran, i liczby kontrolne
   w notatce (to kontrola dla przyszłego odbioru).

5. **Pochodzenie.** Skan źródła: każda wartość wpisana na sztywno (style
   inline, dowolne wartości Tailwinda `text-[…]`, literały w CSS poza
   tokenami, kolory w szablonach maili) z `git blame`: autor, data, commit.
   Gotowe: rozkład w czasie i po autorach, z datą reguły, która miała to
   zatrzymać, jeśli była.

6. **Mechanizm.** Dlaczego się rozjechało: piętro skali bez nazwy, strażnik
   po klasie zamiast po wartości, kopiowanie najbliższego wzoru, brak
   komponentu, osobna gramatyka powierzchni bez nazwanej skali. Siostry
   szukasz w populacji z kroków 2–3, nie wokół mechanizmu. Gotowe: jedno
   zdanie mechanizmu z dowodem i lista miejsc, w których działa.

7. **Druga opinia.** `codex exec --sandbox read-only "$(cat brief.md)"
   < /dev/null` w tle, z katalogu repo. Brief: zakres, lista tego, co już
   zinwentaryzowane (powierzchnie i wymiary), prośba o pominięte wymiary
   i powierzchnie z dowodem, tabela stanów i pięć najgroźniejszych. Gotowe:
   wynik Codexa w notatce, sporne punkty sprawdzone u źródła.

8. **Meldunek.** Liczby kontrolne, pięć najgroźniejszych rozjazdów z punktu
   widzenia „wzór, z którego uczy się następny autor”, mechanizm, czego nie
   dało się sprawdzić, co poza zakresem i dlaczego. Dalej idzie plan,
   osobno.

## Wymiary

- **Tokeny:** pismo (rozmiar, interlinia, waga, krój, szerokość kroju,
  rozstrzelenie), kolor tekstu i tła (także przezroczystości), odstępy
  (rytm sekcji, gap, padding), promienie, cienie, obramowania, warstwy
  z-index, punkty łamania, ruch (czasy, krzywe).
- **Komponenty:** przyciski i warianty, pola, tabele, karty, modale
  i szuflady, plakietki, komunikaty, ikony (rozmiar, grubość i końce
  kreski); duplikaty komponentów; ten sam ciąg klas skopiowany w wielu
  plikach.
- **Stany:** hover, focus-visible, disabled, aktywny, pusty, ładowanie,
  błąd, wynik akcji.
- **Układ:** szerokości kolumn i długość wiersza, gęstość, 320/390/768/
  1024/1440, powiększenie 200% (płynny stopień z samym `vw` nie rośnie),
  łamanie długich ciągów, `vw` w kartach.
- **Semantyka i dostępność:** jeden h1 i kolejność nagłówków, kontrast
  liczony (także świadome wyjątki w komentarzach), cel dotyku, etykiety
  i błędy pól, autouzupełnianie, ogłaszanie wyników, fokus w modalach,
  link „przejdź do treści”, `lang`, `reduced-motion` w każdym ruchu,
  `forced-colors`, druk.
- **Treść:** formaty dat (`<time dateTime>`), liczb i kwot, sieroty,
  cudzysłowy i półpauzy, elementy dopuszczane przez parser treści bez
  stylu (tabela, kod, `hr`).
- **Media:** wymiary i `sizes` obrazów zgodne z układem, formaty, alt,
  punkt kadru, wideo (napisy, ładowanie).

## Pułapki pomiaru

- Animacja wejścia przy scrollu udaje styl (krój, rozstrzelenie) bez
  emulacji ograniczonego ruchu.
- Lista selektorów gubi `<time>`, spany, nagłówek i stopkę; stąd TreeWalker.
- Ten sam kolor w `oklab()` i `rgba()` liczy się podwójnie; `analiza.py`
  sprowadza zapis do jednego.
- Przekierowanie na logowanie daje „czysty” pusty pomiar; kanarek go
  wywraca.
- Zapytanie o źródło mierzy magazyn, nie ekran: rozjazd potwierdzasz
  pomiarem, nie samym grepem.

## Po audycie

Plan naprawy żyje w repo projektu, nie tu. Kształt, który się sprawdził:
reguła odbioru i próg wobec kontroli z kroku 4 przed pierwszą poprawką;
kontrakt nazw (role z funkcjami, wartości w jednym pliku stylów); strażnik
listą dozwolonych z zapadką (wyjątki tylko maleją) i testem mutacyjnym;
przepięcie strona po stronie z podglądem dla Serge'a; ten sam pomiar jako
bramka po wdrożeniu.
