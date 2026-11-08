# Postmortem przelotu

Kiedy: każdy przelot bez nadzoru; drabina wariantów zadziałała; blokada; przelot
przerwany siecią albo limitem; poprawka droższa niż pierwotne zadanie.

1. Z pamięci, zanim otworzysz log: co poszło nie tak i dlaczego (hipoteza).
2. Koszt: `cost` z run.json albo `koszty.py`; jedna linia do meldunku.
3. Oś czasu z drutu: `log.tsv`, `decisions.jsonl`, `git log` integracji. Hipotezę
   z punktu 1 potwierdzasz albo odrzucasz.
4. Klasa przyczyny: (a) luka skilla, (b) luka planu, (c) środowisko, (d) wykonanie
   wbrew regule, (e) nieprzewidywalne.
5. Ściany nośne, których poprawka nie rusza: kryteria z dowodem na SHA, jeden
   piszący stan, `approval` tylko od człowieka, trzy kamienie dostawy.
6. Propozycje w kolejności usuń → zmień → dodaj; każda z miejscem (plik, sekcja),
   brzmieniem, incydentem, który by złapała, i czytelnikiem w chwili błędu. Reguła
   bez incydentu z historii nie wchodzi.
7. Druga opinia: `codex exec -s read-only -C <katalog skilla> --skip-git-repo-check
   -o <wynik> "<propozycje>" < /dev/null`.
8. Poprawka skilla jednym commitem jako stan (bez anegdoty); incydent idzie do
   LESSONS repo albo `_context/LESSONS.md` z linią `Dom:`.

Meldunek dostaje sekcję „Skill: co zmienione, co odrzucone i dlaczego”.
