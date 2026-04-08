# Raw Sources

**Pattern:** Karpathy LLM Knowledge Base — `raw/` layer

## Purpose

Immutable source documents (papers, exports, court rulings, competitor materials, web clips, images) z których LLM kompiluje wiki articles w `docs/wiki/`.

**Reguła:** raw/ = read-only z perspektywy LLM. Nigdy nie edytuj plików po dodaniu. Jeśli source się zmienił — dodaj nowy plik z nową datą, oznacz stary jako superseded.

**Przepływ:** raw/ (sources) → LESSONS.md/DECISIONS.md (synthesized observations) → docs/wiki/ (LLM-compiled articles).

## Struktura

```
raw/
├── README.md             ← ten plik
├── papers/               ← PDFy/HTMLs z arXiv, ACL, NeurIPS, blogs research
├── exports/              ← exports z innych tools (NotebookLM, Google Docs, etc.)
├── competitors/          ← screenshoty, blog posts, marketing materials konkurencji
├── court-rulings/        ← (jeśli legal) anonimizowane orzeczenia, public domain
├── assets/               ← images, diagrams, screenshots referenced from wiki/
└── web-clips/            ← Obsidian Web Clipper output, full article snapshots
```

## Konwencje nazewnictwa

`YYYY-MM-DD_<source>_<short-title>.<ext>`

Przykłady:
- `papers/2024-08-19_legalbench-rag_zeroentropy.pdf`
- `papers/2026-04-02_gemma4_google-blog.html`
- `exports/2026-04-15_partner-X_export.zip` (po anonimizacji!)
- `competitors/2026-04-07_competitor-name_pricing-page.png`
- `assets/2026-04-07_pipeline-diagram.png`
- `web-clips/2026-04-07_author_article-title.md`

## Kiedy plik trafia do raw/

**Tak (commit do raw/):**
- Papers które chcemy referencować w wiki articles
- Exports od partnerów (po anonimizacji)
- Konkretne screenshoty konkurencji z konkretnej daty
- Public-domain documents jako test corpus
- Web articles które mogą zniknąć (web-clips/ via Obsidian Web Clipper)
- Images używane w wiki articles (assets/)

**Nie (NIE commitować):**
- Real client / sensitive documents (privacy violation)
- Binary files >10 MB (use git-lfs jeśli koniecznie potrzebne)
- Generated outputs które są w wiki/ (one source of truth)
- Tymczasowe pliki, draftsy

## Anonimizacja sensitive documents

Zanim sensitive document trafi do raw/:
1. Zmień imiona / nazwiska / company names na placeholders
2. Zmień kwoty / dane finansowe na approximate
3. Zmień daty istotne (zachowaj rok, zmień miesiąc/dzień)
4. Sprawdź dwukrotnie nagłówki/stopki/metadane

**Real client data NIGDY nie trafia do gitowego repo.** Zostaje wyłącznie lokalnie u właściciela lub w user-specified secure location.

## Powiązania z wiki

Wiki articles odnoszą się do raw/ przez relative paths:
```markdown
Source: [paper title](../raw/papers/2024-08-19_paper-title.pdf)
Diagram: ![Pipeline](../raw/assets/diagram-name.png)
```

`wiki-health-check.md` automatycznie sprawdza czy referenced raw/ files istnieją.

## Reference

- `docs/wiki/karpathy-kb-alignment.md` — pełna dyskusja Karpathy KB pattern
- `docs/wiki/wiki-health-check.md` — lint pass dla wiki+raw consistency
- Karpathy Gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
