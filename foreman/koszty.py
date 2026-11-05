#!/usr/bin/env python3
"""Zużycie przelotu foremana per agent, z zapisów sesji Claude Code.

Użycie: koszty.py [--od=ISO] [--do=ISO] <sesja.jsonl> [<sesja.jsonl> ...]  > koszty.txt
       koszty.py --kontekst=<id agenta>   (kontekst ostatniej odpowiedzi agenta)
--od/--do (UTC, np. 2026-10-16T07:51) liczą tylko odpowiedzi w oknie: sesja niosąca
dwa przeloty. Kolumna kontekst=ost/max to tokeny wejścia ostatniej i największej
odpowiedzi: próg nowego wykonawcy i przekazania sesji z SKILL.md.
Katalog `<sesja>/subagents/` obok każdego zapisu wchodzi sam.

Liczy ostatni `usage` każdej unikalnej odpowiedzi (`message.id`): ta sama
odpowiedź stoi w zapisie kilka razy z powtórzonym `usage`, więc suma po
rekordach zawyża koszt mniej więcej dwukrotnie. Odpowiedzi `<synthetic>`
pomija. E = input + 0,1*cache_read + 1,25*cache_write + 5*output, w mln
tokenów danego modelu (nie w dolarach).
"""
import collections
import glob
import json
import os
import sys

OD = next((a[5:] for a in sys.argv if a.startswith("--od=")), "")
DO = next((a[5:] for a in sys.argv if a.startswith("--do=")), "~")
POLA = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "output_tokens")


def zuzycie(sciezka):
    ostatni, modele, czasy, opis, ost = {}, set(), [], "", 0
    with open(sciezka) as f:
        for linia in f:
            try:
                d = json.loads(linia)
            except ValueError:
                continue
            if d.get("timestamp"):
                czasy.append(d["timestamp"])
            m = d.get("message") if isinstance(d.get("message"), dict) else {}
            if (d.get("type") == "assistant" and m.get("id") and m.get("model") != "<synthetic>"
                    and OD <= d.get("timestamp", "") < DO):
                u = m.get("usage")
                if u:
                    ostatni[m["id"]] = u
                    ost = sum(u.get(k) or 0 for k in POLA[:3])
                modele.add(m.get("model", "?"))
            if not opis and d.get("type") == "user":
                c = m.get("content")
                opis = (c if isinstance(c, str) else json.dumps(c, ensure_ascii=False))[:80].replace("\n", " ")
    suma = collections.Counter()
    for u in ostatni.values():
        for k in POLA:
            suma[k] += u.get(k) or 0
    e = (suma["input_tokens"] + 0.1 * suma["cache_read_input_tokens"]
         + 1.25 * suma["cache_creation_input_tokens"] + 5 * suma["output_tokens"]) / 1e6
    maks = max((sum(u.get(k) or 0 for k in POLA[:3]) for u in ostatni.values()), default=0)
    return len(ostatni), ",".join(sorted(modele)), e, suma, czasy, opis, (ost, maks)


KONTEKST = next((a[11:] for a in sys.argv if a.startswith("--kontekst=")), "")
if KONTEKST:
    trafienia = glob.glob(os.path.expanduser(f"~/.claude/projects/*/*/subagents/agent-{KONTEKST}.jsonl"))
    if not trafienia:
        sys.exit(f"brak zapisu agenta {KONTEKST}")
    p = max(trafienia, key=os.path.getmtime)
    ost, maks = zuzycie(p)[6]
    print(f"{os.path.basename(p)[:-6]} kontekst ostatniej odpowiedzi={ost} max={maks}")
    sys.exit()


razem = collections.defaultdict(float)
widziane = set()  # zapis subagenta podany obok sesji liczyłby się dwa razy
for sesja in [a for a in sys.argv[1:] if not a.startswith("--")]:
    if not os.path.isfile(sesja) or os.sep + "subagents" + os.sep in sesja:
        print(f"pomijam {sesja}: podaj zapis sesji, subagenci wchodzą sami", file=sys.stderr)
        continue
    print(f"=== {os.path.basename(sesja)}")
    pliki = [("BRYGADZISTA", sesja)] + [
        (os.path.basename(p)[:-6], p)
        for p in sorted(glob.glob(os.path.join(sesja[:-6], "subagents", "*.jsonl")))
    ]
    for nazwa, p in pliki:
        if os.path.realpath(p) in widziane:
            continue
        widziane.add(os.path.realpath(p))
        n, model, e, s, czasy, opis, (ost, maks) = zuzycie(p)
        razem[model] += e
        od, do = (czasy[0][11:16], czasy[-1][11:16]) if czasy else ("", "")
        print(f"{nazwa[:24]:24} {model[:20]:20} odp={n:4} E={e:6.2f} "
              f"kontekst={ost // 1000}k/{maks // 1000}k {od}-{do} UTC | {opis}")
print("\nE per model:", {k: round(v, 2) for k, v in razem.items()})
