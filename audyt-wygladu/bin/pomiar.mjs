// Pomiar wyliczonych stylów żywego ekranu: każdy węzeł tekstu i każdy
// element interaktywny, na kilku szerokościach. Wynik JSON na stdout.
//
//   node pomiar.mjs --baza https://x.pl --strony strony.txt [--szerokosci 390,1440]
//        [--stan storageState.json] [--kanarek h1] [--tekst] > pomiar.json
//
// strony.txt: jedna ścieżka w linii. --stan: sesja zalogowana z logowania
// drogą repo (Playwright storageState). Treść tekstu NIE trafia do wyniku,
// chyba że --tekst (tylko strony publiczne: za logowaniem są dane osobowe).
// playwright-core szuka od katalogu bieżącego, więc odpalasz z repo, które go ma.
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";

const arg = (n, d) => { const i = process.argv.indexOf(`--${n}`); return i < 0 ? d : process.argv[i + 1]; };
const flaga = (n) => process.argv.includes(`--${n}`);
const baza = arg("baza"); const plikStron = arg("strony");
if (!baza || !plikStron) { console.error("wymagane: --baza i --strony"); process.exit(2); }
const strony = readFileSync(plikStron, "utf8").split("\n").map((s) => s.trim()).filter((s) => s && !s.startsWith("#"));
const szerokosci = arg("szerokosci", "390,1440").split(",").map(Number);
const kanarek = arg("kanarek", "h1");
const zTekstem = flaga("tekst");

const req = createRequire(process.cwd() + "/");
let pw; for (const m of ["playwright-core", "playwright"]) { try { pw = req(m); break; } catch {} }
if (!pw) { console.error("brak playwright-core/playwright w katalogu bieżącym"); process.exit(2); }

const b = await pw.chromium.launch({ channel: "chrome", headless: true });
const ctx = await b.newContext({ reducedMotion: "reduce", ...(arg("stan") ? { storageState: arg("stan") } : {}) });
const wynik = { meta: { baza, szerokosci, kanarek, data: new Date().toISOString() }, strony: {} };
for (const szer of szerokosci) {
  const p = await ctx.newPage();
  await p.setViewportSize({ width: szer, height: 900 });
  for (const s of strony) {
    const odp = await p.goto(baza + s, { waitUntil: "networkidle" });
    await p.evaluate(() => document.fonts.ready);
    // Bez ruchu (reducedMotion) odsłony stoją w stanie końcowym; inaczej
    // pomiar bierze klatkę animacji za styl.
    const dane = await p.evaluate(({ kanarek, zTekstem }) => {
      const strefa = (el) => el.closest("footer") ? "stopka" : el.closest("header,nav,[role=banner],[role=navigation],aside") ? "rama" : "tresc";
      const tekst = []; const widziane = new Set();
      const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      for (let n = w.nextNode(); n; n = w.nextNode()) {
        const el = n.parentElement;
        if (!el || widziane.has(el) || !n.textContent.trim()) continue;
        if (el.closest("script,style,noscript,svg,template,[aria-hidden=true],.sr-only")) continue;
        widziane.add(el);
        const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
        if (r.height === 0 || cs.visibility === "hidden") continue;
        const fs = parseFloat(cs.fontSize);
        tekst.push({ tag: el.tagName.toLowerCase(), kanarek: !!el.closest(kanarek), strefa: strefa(el),
          fs, lh: cs.lineHeight === "normal" ? null : +(parseFloat(cs.lineHeight) / fs).toFixed(2),
          fw: cs.fontWeight, fst: cs.fontStretch, ls: cs.letterSpacing === "normal" ? "normal" : +(parseFloat(cs.letterSpacing) / fs).toFixed(3) + "em",
          ff: cs.fontFamily.split(",")[0].replace(/["']/g, ""), kol: cs.color,
          ...(zTekstem ? { txt: el.textContent.trim().slice(0, 40) } : {}) });
      }
      const akcje = [...document.querySelectorAll("a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[role=tab],[role=link]")]
        .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && !el.closest("[aria-hidden=true]"); })
        .map((el) => { const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
          // Link w zdaniu: WCAG 2.5.8 zwalnia go z minimum celu dotyku.
          const rodzic = el.parentElement; const wZdaniu = el.tagName === "A" && !!rodzic && /^(P|LI|DD|TD|SPAN|STRONG|EM)$/.test(rodzic.tagName)
            && rodzic.textContent.trim().length > el.textContent.trim().length + 3;
          return { tag: el.tagName.toLowerCase(), strefa: strefa(el), wZdaniu, w: Math.round(r.width), h: Math.round(r.height),
            rad: cs.borderRadius, tlo: cs.backgroundColor, ramka: cs.borderTopWidth + " " + cs.borderTopColor,
            fs: parseFloat(cs.fontSize), fw: cs.fontWeight, kol: cs.color }; });
      const pudla = { promienie: {}, cienie: {}, z: {} };
      for (const el of document.body.querySelectorAll("*")) {
        const cs = getComputedStyle(el);
        if (cs.borderRadius !== "0px") pudla.promienie[cs.borderRadius] = (pudla.promienie[cs.borderRadius] || 0) + 1;
        if (cs.boxShadow !== "none") pudla.cienie[cs.boxShadow] = (pudla.cienie[cs.boxShadow] || 0) + 1;
        if (cs.zIndex !== "auto" && cs.position !== "static") pudla.z[cs.zIndex] = (pudla.z[cs.zIndex] || 0) + 1;
      }
      const naglowki = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")].map((h) => +h.tagName[1]);
      return { tekst, akcje, pudla, naglowki, lang: document.documentElement.lang };
    }, { kanarek, zTekstem });
    dane.status = odp ? odp.status() : null; dane.url = p.url();
    // Kanarek: znany element musi wejść do pomiaru, inaczej skan jest ślepy
    // (przekierowanie na logowanie, pusty render, zły selektor).
    if (!dane.tekst.some((e) => e.kanarek)) throw new Error(`kanarek „${kanarek}” nie wszedł do pomiaru: ${szer} ${s} (url: ${dane.url})`);
    wynik.strony[`${szer} ${s}`] = dane;
  }
  await p.close();
}
await b.close();
console.log(JSON.stringify(wynik));
