# Foreman: sekcja zwłok przelotu

Czytasz w kroku 8, zanim zdejmiesz worktree i skasujesz plan. Cel: skill po
każdym przelocie jest lepszy o to, co ten przelot kosztowało. Robisz to,
póki masz przelot w kontekście; po zamknięciu sesji zostają tylko zapisy,
a z nich nie widać, gdzie instrukcja była dwuznaczna.

## Kiedy

Zawsze po przelocie bez nadzoru i po każdym, w którym zadziałała drabina
modelu, padła blokada, sieć albo limit przerwały pracę, albo zadanie
poprawkowe po recenzji kosztowało więcej niż zadanie, które poprawiało.
Przelot gładki i krótki: same kroki 1 i 4, trzy linie w meldunku.

## Kroki

Materiał idzie do katalogu tymczasowego sesji, nie do repo.

0. **Z pamięci, przed zajrzeniem do plików:** tarcia, których nie ma w żadnym
   logu: gdzie skill był dwuznaczny i zgadywałeś, gdzie się wahałeś, czego
   szukałeś i nie znalazłeś, co obszedłeś, który krok był ceremonią. Każde
   jednym zdaniem z miejscem w skillu. Zapisujesz to pierwsze, bo po liczeniu
   pamięć układa się w gładszą historię.
1. **Koszt:** `python3 <katalog skilla>/koszty.py <zapisy sesji przelotu>`
   do pliku (zapisy: `~/.claude/projects/<katalog repo>/<id sesji>.jsonl`,
   subagenci wchodzą sami). Sesje sprzed kompakcji i poprzednie sesje tego
   przelotu też podajesz.
2. **Oś czasu incydentów** z zapisów, drutem: każde miejsce, gdzie robota
   stanęła, poszła drugi raz albo zboczyła. Sygnały: błędy narzędzi,
   „Connection refused”, `SendMessage` do martwego agenta, agent z liczbą
   odpowiedzi ponad dwukrotność mediany, czerwone CI, druga runda u tego
   samego wykonawcy. Każdy incydent: godzina, koszt (E z pliku, minuty
   zegara), jak się skończył.
3. **Klasa przyczyny**, jedna na incydent: (a) luka w skillu, (b) luka
   w planie, (c) środowisko, (d) błąd wykonania mimo dobrej reguły, (e) nie
   do przewidzenia. Przy (d) piszesz, dlaczego reguła nie odpaliła w tej
   chwili: zwykle to też (a), bo reguła stała tam, gdzie nikt wtedy nie
   patrzył. Rachunek: odsetek E i zegara na (a) i (b).
4. **Nośne ściany:** elementy skilla, które coś złapały, z incydentem jako
   dowodem. Aktualizacja ich nie wycina.
5. **Propozycje, najpierw drabina:** co skasować (zapis, którego nikt nie
   przeczytał; krok, który niczego nie złapał), potem co zmienić, na końcu
   co dodać. Każda: miejsce w skillu, brzmienie, incydent, który by
   uratowała, i kto ją przeczyta w chwili błędu. Bez reguł z jednego
   incydentu klasy (e).
6. **Drugie oko:** Codex na najmocniejszym modelu, tylko do odczytu, na
   skill, plik kosztów i Twoją sekcję zwłok:
   `codex exec -m gpt-6-astra -s read-only -C <katalog skilla> --skip-git-repo-check -o <wynik> "<pytania>" < /dev/null`.
   Pytania: gdzie idą tokeny i co w skillu to wymusza; kroki zbędne
   i powtórzone; reguły martwe, sprzeczne, zdublowane; co z propozycji
   usunęłoby jedynego strażnika produkcji, cudzych danych albo merge'a.
   Liczby Codexa sprawdzasz tak samo jak jego findingi: przeliczeniem.
7. **Poprawka skilla:** zestawiasz oba źródła, każdy finding weryfikujesz
   w skillu i w zapisach, odrzucony dostaje powód. Przyjęte wchodzą do
   skilla jednym commitem w jego repo, z listą zmian i incydentów w opisie;
   skill przepisany jako stan, bez dat i „wcześniej”. Mechanizm, który
   wykracza poza foremana, dostaje wpis lekcji z domem tam, gdzie go przeczyta
   następna sesja.
8. **Sprzątanie:** materiał z kroków 0–6 kasujesz po commicie. Zostaje
   commit skilla i ewentualny wpis lekcji.

Meldunek dostaje sekcję „Skill”: najdroższa luka z kwotą, odsetek kosztu na
klasy (a) i (b), lista wprowadzonych zmian, odrzucone findingi z powodem.
