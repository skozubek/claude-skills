#!/usr/bin/env python3
"""Zużycie przelotu foremana per agent, z zapisów sesji Claude Code.

Użycie: koszty.py [--od=ISO] [--do=ISO] <sesja.jsonl> [<sesja.jsonl> ...]  > koszty.txt
--od/--do (UTC, np. 2026-10-16T07:51) liczą tylko odpowiedzi w oknie: sesja niosąca
dwa przeloty.
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
    ostatni, modele, czasy, opis = {}, set(), [], ""
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
                ostatni[m["id"]] = m.get("usage") or {}
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
    return len(ostatni), ",".join(sorted(modele)), e, suma, czasy, opis


razem = collections.defaultdict(float)
for sesja in [a for a in sys.argv[1:] if not a.startswith("--")]:
    print(f"=== {os.path.basename(sesja)}")
    pliki = [("BRYGADZISTA", sesja)] + [
        (os.path.basename(p)[:-6], p)
        for p in sorted(glob.glob(os.path.join(sesja[:-6], "subagents", "*.jsonl")))
    ]
    for nazwa, p in pliki:
        n, model, e, s, czasy, opis = zuzycie(p)
        razem[model] += e
        od, do = (czasy[0][11:16], czasy[-1][11:16]) if czasy else ("", "")
        print(f"{nazwa[:24]:24} {model[:20]:20} odp={n:4} E={e:6.2f} "
              f"cache_read_na_odp={s['cache_read_input_tokens'] // max(n, 1):>7} {od}-{do} UTC | {opis}")
print("\nE per model:", {k: round(v, 2) for k, v in razem.items()})
