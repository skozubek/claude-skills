#!/usr/bin/env python3
"""Streszczenie pomiaru: liczby kontrolne na szerokość, stopnie nagłówków per
strona, cele dotyku, promienie, cienie, warstwy, kolejność nagłówków.

  python3 analiza.py pomiar.json [--przed kontrola.json]

--przed: ten sam pomiar zrobiony wcześniej (kontrola), drukuje obie liczby obok.
"""
import json, sys, collections, re

def kolor(c):
    """Jeden zapis koloru: oklab() i rgb() tej samej wartości liczą się raz."""
    m = re.match(r"oklab\(([-\d.e]+) ([-\d.e]+) ([-\d.e]+)(?: / ([\d.]+))?\)", c)
    if not m:
        return c
    L, a, b = (float(x) for x in m.groups()[:3]); al = float(m.group(4) or 1)
    l_, m_, s_ = (L + 0.3963377774*a + 0.2158037573*b)**3, (L - 0.1055613458*a - 0.0638541728*b)**3, (L - 0.0894841775*a - 1.2914855480*b)**3
    lin = (4.0767416621*l_ - 3.3077115913*m_ + 0.2309699292*s_, -1.2684380046*l_ + 2.6097574011*m_ - 0.3413193965*s_, -0.0041960863*l_ - 0.7034186147*m_ + 1.7076147010*s_)
    srgb = [round(255*max(0, min(1, (12.92*x if x <= 0.0031308 else 1.055*x**(1/2.4) - 0.055)))) for x in lin]
    return f"rgba({srgb[0]}, {srgb[1]}, {srgb[2]}, {round(al, 2)})" if al < 1 else f"rgb({srgb[0]}, {srgb[1]}, {srgb[2]})"

def rgba(c):
    """rgba(…, 1) i rgb(…) to ten sam kolor."""
    c = kolor(c)
    m = re.match(r"rgba\((\d+), (\d+), (\d+), ([\d.]+)\)", c)
    return f"rgb({m[1]}, {m[2]}, {m[3]})" if m and float(m[4]) == 1 else (f"rgba({m[1]}, {m[2]}, {m[3]}, {round(float(m[4]), 2)})" if m else c)

def liczby(d):
    out = {}
    for szer in sorted({int(k.split()[0]) for k in d["strony"]}):
        strony = [v for k, v in d["strony"].items() if int(k.split()[0]) == szer]
        t = [e for v in strony for e in v["tekst"]]
        a = [e for v in strony for e in v["akcje"]]
        prom = collections.Counter(); cien = collections.Counter(); z = collections.Counter()
        for v in strony:
            prom.update(v["pudla"]["promienie"]); cien.update(v["pudla"]["cienie"]); z.update(v["pudla"]["z"])
        out[szer] = {
            "elementy": len(t),
            "rozmiary": len({e["fs"] for e in t}),
            "kombinacje": len({(e["fs"], e["lh"], e["fw"], e["fst"], e["ls"]) for e in t}),
            "kolory tekstu": len({rgba(e["kol"]) for e in t}),
            "kroje": len({e["ff"] for e in t}),
            "promienie": len(prom), "cienie": len(cien), "warstwy z": len(z),
            "akcje": len(a),
            "akcje < 24 px (bez linków w zdaniu)": sum(1 for e in a if min(e["w"], e["h"]) < 24 and not e.get("wZdaniu")),
            "wygląd akcji": len({(e["rad"], rgba(e["tlo"]), e["ramka"], e["fs"], e["fw"], rgba(e["kol"])) for e in a if e["tag"] == "button" or e["tlo"] != "rgba(0, 0, 0, 0)"}),
        }
    return out

d = json.load(open(sys.argv[1]))
przed = json.load(open(sys.argv[sys.argv.index("--przed") + 1])) if "--przed" in sys.argv else None
L = liczby(d); P = liczby(przed) if przed else {}
print("== Liczby kontrolne" + (" (kontrola → teraz)" if przed else ""))
for szer, l in L.items():
    print(f"  {szer} px: " + ", ".join(f"{k} {P[szer][k]}→{v}" if szer in P else f"{k} {v}" for k, v in l.items()))

print("\n== Nagłówki per strona (najszersza szerokość): rozmiar/interlinia/waga ×liczba")
szer = max(L)
for k, v in d["strony"].items():
    if int(k.split()[0]) != szer: continue
    c = collections.Counter((e["tag"], e["fs"], e["lh"], e["fw"]) for e in v["tekst"] if e["tag"] in ("h1", "h2", "h3"))
    print(f"  {k.split(' ',1)[1]}: " + "  ".join(f"{t} {fs}/{lh}/{fw}×{n}" for (t, fs, lh, fw), n in sorted(c.items())))

print("\n== Kolejność nagłówków: przeskoki poziomu i liczba h1")
for k, v in d["strony"].items():
    n = v["naglowki"]; skoki = [f"h{a}→h{b}" for a, b in zip(n, n[1:]) if b > a + 1]
    if n.count(1) != 1 or skoki: print(f"  {k}: h1×{n.count(1)} {' '.join(skoki)}")

print("\n== Rozmiary pisma w całym serwisie (najszersza): px ×elementów")
c = collections.Counter(e["fs"] for k, v in d["strony"].items() if int(k.split()[0]) == szer for e in v["tekst"])
print("  " + "  ".join(f"{fs}×{n}" for fs, n in sorted(c.items())))
print("\n== Kolory tekstu: ×elementów")
c = collections.Counter(rgba(e["kol"]) for k, v in d["strony"].items() if int(k.split()[0]) == szer for e in v["tekst"])
print("  " + "\n  ".join(f"{k} ×{n}" for k, n in c.most_common()))
