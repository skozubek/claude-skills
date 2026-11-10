# Postmortem przelotu

Kiedy: każdy przelot bez nadzoru; drabina wariantów zadziałała; blokada; przelot
przerwany siecią albo limitem; poprawka droższa niż pierwotne zadanie. Robisz go
przed sprzątaniem, póki przelot jest w kontekście. Przelot gładki: punkty 1 i 4,
trzy linie w meldunku.

1. Z pamięci, zanim otworzysz log: tarcia, których nie ma w żadnym logu (gdzie
   skill był dwuznaczny, gdzie się wahałeś, czego szukałeś i nie znalazłeś, co
   obszedłeś, który krok był ceremonią), każde z miejscem w skillu, i hipoteza,
   co poszło nie tak.
2. Koszt: `foreman2 cost --scan` (per sesja i agent); jedna linia do meldunku.
3. Oś czasu z drutu: `log.tsv`, `decisions.jsonl`, `git log` integracji i zapisy
   sesji (błędy narzędzi, „Connection refused”, SendMessage do martwego agenta,
   agent z liczbą odpowiedzi ponad dwukrotność mediany, czerwone CI), bo `log.tsv`
   nie widzi błędów narzędzi. Hipotezę z punktu 1 potwierdzasz albo odrzucasz.
4. Klasa przyczyny: (a) luka skilla, (b) luka planu, (c) środowisko, (d) wykonanie
   wbrew regule, (e) nieprzewidywalne. Przy (d) piszesz, dlaczego reguła nie
   odpaliła w tej chwili (zwykle to też (a): stała tam, gdzie nikt nie patrzył).
   Rachunek: odsetek kosztu i zegara na (a) i (b).
5. Ściany nośne, których poprawka nie rusza: kryteria z dowodem na SHA, jeden
   piszący stan, `approval` tylko od człowieka, trzy kamienie dostawy, oraz każdy
   element skilla, który w tym przelocie coś złapał (incydent jako dowód).
6. Propozycje w kolejności usuń → zmień → dodaj; każda z miejscem (plik, sekcja),
   brzmieniem, incydentem, który by złapała, i czytelnikiem w chwili błędu. Reguła
   bez incydentu z historii nie wchodzi.
7. Druga opinia: `codex exec -s read-only -C <katalog skilla> --skip-git-repo-check
   -o <wynik> "<pytania: gdzie idą tokeny i co w skillu to wymusza; kroki zbędne
   i powtórzone; reguły martwe, sprzeczne, zdublowane; co z propozycji usunęłoby
   jedynego strażnika produkcji, cudzych danych albo merge'a>" < /dev/null`.
   Liczby Codexa przeliczasz jak jego findingi.
8. Poprawka skilla jednym commitem jako stan (bez anegdoty); incydent idzie do
   LESSONS repo albo `_context/LESSONS.md` z linią `Dom:`.

Meldunek dostaje sekcję „Skill: najdroższa luka z kwotą, odsetek kosztu na (a)
i (b), co zmienione, co odrzucone i dlaczego”.
