#!/usr/bin/env python3
"""Sześć progów odbioru na pomiarze z pomiar.mjs, liczone w strefach treść
i okno (powłoka aplikacji wokół treści nie należy do mierzonego modułu).

  python3 progi.py pomiar.json --css src/index.css [--przed kontrola.json] [--naruszenia 8]

1 kontrast tekstu ≥ 4,5:1 (duży 3:1), tło złożone, bez kontrolek wyłączonych
  i tekstu na gradiencie;
2 pismo: nic poniżej 11,2 px (rozmiar 2xs), 11 px tylko jako 11,2;
3 jeden wygląd „wybranego” (aria-pressed, data-state=on, radio aria-checked);
4 cele dotyku ≥ 24 px, bez linków w zdaniu i nagłówków standardowej tabeli;
5 jeden h1 na trasę, bez skoku poziomu;
6 kolory tekstu (bez kanału alfa) ≤ liczbie kolorów ról z --css; wykresy osobno.

Próbka czułości (krok `wstrzyknij <nazwa>`) zapala swój próg, gdy na swojej
trasie daje więcej naruszeń niż ta sama trasa bez próbki. Próg bez zapalonej
próbki nie liczy się jako zdany. Trasa, która przekierowała gdzie indziej
(np. widok mobilny pod 390 px), wypada z liczenia i stoi w wyniku jako
„pominięta, przekierowana”: zmierzony ekran nie jest tym z listy.
"""
import json, sys, re, collections, colorsys
from urllib.parse import urlparse

ARG = sys.argv
def opcja(n, d=None): return ARG[ARG.index(n) + 1] if n in ARG else d
STREFY = {"tresc", "okno"}
PROBKA_PROG = {"bialy-na-secondary": 1, "pismo10": 2, "wybrany-obcy": 3, "cel16": 4, "skok-h1-h3": 5, "niebieski": 6}
# Role tekstu z tabeli ról modułu; napis na pełnym kolorze to *-foreground (biały).
ROLE_TEKSTU = ["foreground", "muted-foreground", "accent-foreground", "warning", "success-strong", "destructive", "primary-foreground"]

def bez_alfy(c):
    m = re.match(r"rgba?\((\d+), (\d+), (\d+)", c)
    return f"rgb({m[1]}, {m[2]}, {m[3]})" if m else c

def kolory_rol(css):
    root = re.search(r":root\s*{(.*?)\n\s*}", open(css).read(), re.S)[1]
    tok = dict(re.findall(r"--([\w-]+):\s*([\d.]+ [\d.]+% [\d.]+%);", root))
    out = {}
    for n in ROLE_TEKSTU:
        h, s, l = (float(x.rstrip("%")) for x in tok[n].split())
        r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
        out.setdefault(f"rgb({round(r*255)}, {round(g*255)}, {round(b*255)})", []).append(n)
    return out

def rgb(c):
    m = re.match(r"rgba?\((\d+), (\d+), (\d+)", c)
    return tuple(int(x) for x in m.groups()) if m else None

def rola_koloru(k, role):
    """Kolor roli z tolerancją ±1 na kanał: przeglądarka zaokrągla HSL inaczej niż colorsys."""
    a = rgb(k)
    return a is not None and any((b := rgb(r)) and max(abs(x - y) for x, y in zip(a, b)) <= 1 for r in role)

def naruszenia(v, role):
    """Naruszenia jednej trasy: {próg: [opis, …]}; dla progu 3 i 6 lista wartości, nie elementów."""
    t = [e for e in v["tekst"] if e["strefa"] in STREFY]
    a = [e for e in v["akcje"] if e["strefa"] in STREFY]
    n = {i: [] for i in range(1, 7)}
    for e in t:
        if not e["wyl"] and not e["tloObraz"] and not e["stdTh"] and e["kr"] < (3 if e["duzy"] else 4.5):
            n[1].append(f"{e['tag']} {e['fs']}px {bez_alfy(e['kol'])} na {e['tlo']}: {e['kr']}")
        if not e["stdTh"] and round(e["fs"], 1) < 11.2:
            n[2].append(f"{e['tag']} {e['fs']}px")
    n[3] = sorted({f"tło {e['tlo']} / napis {e['kol']} / ramka {e['ramka']} / waga {e['fw']}" for e in a if e["wybrany"]})
    for e in a:
        if min(e["w"], e["h"]) < 24 and not e["wZdaniu"] and not e["stdTh"]:
            n[4].append(f"{e['tag']}{'[' + e['rola'] + ']' if e['rola'] else ''} {e['w']}×{e['h']}")
    h = v["naglowki"]
    if h.count(1) != 1: n[5].append(f"h1×{h.count(1)}")
    n[5] += [f"h{x}→h{y}" for x, y in zip(h, h[1:]) if y > x + 1]
    n[6] = sorted(k for k in {bez_alfy(e["kol"]) for e in t if not e["wykres"]} if not rola_koloru(k, role))
    return n

def ocena(d, role):
    """Na szerokość: wartość progu, przykłady naruszeń z trasą, zapalone próbki."""
    wyn = {}
    for klucz, v in d["strony"].items():
        szer, linia = klucz.split(" ", 1)
        w = wyn.setdefault(int(szer), {"n": {i: [] for i in range(1, 7)}, "wybrane": set(), "kolory": set(), "probki": {}})
        trasa = re.sub(r"^@\d+ ", "", linia).split(" ")[0].split("?")[0]
        dotarl = urlparse(v.get("url", "")).path
        if dotarl and dotarl != trasa:  # przekierowanie: zmierzony ekran nie jest tym z listy
            w.setdefault("obce", []).append(f"{trasa} → {dotarl}")
            continue
        n = naruszenia(v, role)
        probka = re.search(r"\| wstrzyknij (\S+)", linia)
        if probka:
            baza = re.sub(r" \| wstrzyknij \S+", "", linia)
            b = naruszenia(d["strony"][f"{szer} {baza}"], role)
            p = PROBKA_PROG[probka[1]]
            w["probki"][p] = (probka[1], len(n[p]) > len(b[p]))
            continue
        for i in (1, 2, 4, 5):
            w["n"][i] += [(linia, x) for x in n[i]]
        w["wybrane"] |= set(n[3]); w["kolory"] |= set(n[6])
    for w in wyn.values():
        w["wart"] = {1: len(w["n"][1]), 2: len(w["n"][2]), 3: len(w["wybrane"]), 4: len(w["n"][4]), 5: len(w["n"][5]),
                     6: len(role) + len(w["kolory"])}
    return wyn

d = json.load(open(ARG[1]))
role = kolory_rol(opcja("--css"))
ile = int(opcja("--naruszenia", 8))
W = ocena(d, role)
P = ocena(json.load(open(opcja("--przed"))), role) if "--przed" in ARG else {}
NAZWY = {1: "kontrast < 4,5:1 (duży 3:1)", 2: "pismo < 11,2 px", 3: "wyglądy „wybranego” (cel 1)", 4: "cele < 24 px",
         5: "h1 ≠ 1 albo skok poziomu", 6: f"kolory tekstu (cel ≤ {len(role)} ról)"}
CEL = {1: 0, 2: 0, 3: 1, 4: 0, 5: 0, 6: len(role)}
print("Role tekstu: " + ", ".join(f"{'/'.join(n)} {k}" for k, n in role.items()))
for szer, w in sorted(W.items()):
    print(f"\n== {szer} px")
    for o in sorted(set(w.get("obce", []))): print(f"  pominięta, przekierowana: {o}")
    for i in range(1, 7):
        wart = w["wart"][i]; przed = f"{P[szer]['wart'][i]} → " if szer in P else ""
        pr = w["probki"].get(i)
        stan = "ZDANY" if wart <= CEL[i] and pr and pr[1] else ("nie zdany" if wart > CEL[i] else "bez zapalonej próbki")
        print(f"  {i}. {NAZWY[i]}: {przed}{wart}  [{stan}; próbka {pr[0] + (' zapalona' if pr[1] else ' NIE zapalona') if pr else 'brak'}]")
        if i == 3: lista = [("", x) for x in sorted(w["wybrane"])]
        elif i == 6: lista = [("", x) for x in sorted(w["kolory"])]
        else: lista = w["n"][i]
        for linia, x in lista[:ile]:
            print(f"       {x}" + (f"   ({linia})" if linia else ""))
        if len(lista) > ile: print(f"       … i {len(lista) - ile} więcej")
