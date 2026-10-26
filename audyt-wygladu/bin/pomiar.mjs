// Pomiar wyliczonych stylów żywego ekranu: każdy węzeł tekstu i każdy
// element interaktywny, na kilku szerokościach. Wynik JSON na stdout.
//
//   node pomiar.mjs --baza https://x.pl --strony strony.txt [--szerokosci 390,1440]
//        [--stan storageState.json] [--kanarek h1] [--tekst] > pomiar.json
//
// strony.txt: jedna linia na pomiar, `#` to komentarz. Linia to ścieżka, a po
// niej opcjonalnie kroki rozdzielone ` | `, wykonywane po załadowaniu strony
// (okno otwierane klikiem, stan pusty albo błąd, próbka czułości):
//   klik <selektor>          klik w pierwszy pasujący element (selektor Playwrighta)
//   wpisz <selektor> = <t>   wypełnia pole
//   klawisz <klawisz>        np. Escape
//   czekaj <selektor>        czeka na widoczny element (stan końcowy, nie sen)
//   blokuj <wzorzec>         od tej chwili odrzuca żądania pasujące do wzorca (stan błędu)
//   wstrzyknij <próbka>      dokłada znane naruszenie (lista PROBKI niżej)
// Prefiks `@1440 ` ogranicza linię do jednej szerokości (akcja, która na
// telefonie siedzi w menu, ma tam inną drogę).
// Kluczem wyniku jest „<szerokość> <cała linia>”.
//
// --stan: sesja zalogowana z logowania drogą repo (Playwright storageState).
// Treść tekstu NIE trafia do wyniku, chyba że --tekst (tylko strony publiczne:
// za logowaniem są dane osobowe).
// playwright-core szuka od katalogu bieżącego, więc odpalasz z repo, które go ma.
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";

const arg = (n, d) => { const i = process.argv.indexOf(`--${n}`); return i < 0 ? d : process.argv[i + 1]; };
const flaga = (n) => process.argv.includes(`--${n}`);
const baza = arg("baza"); const plikStron = arg("strony");
if (!baza || !plikStron) { console.error("wymagane: --baza i --strony"); process.exit(2); }
const linie = readFileSync(plikStron, "utf8").split("\n").map((s) => s.trim()).filter((s) => s && !s.startsWith("#"));
const szerokosci = arg("szerokosci", "390,1440").split(",").map(Number);
const kanarek = arg("kanarek", "h1");
const zTekstem = flaga("tekst");

// Próbki czułości progów: każda to jedno znane naruszenie, wstawione stylem
// inline, bo miernik czyta wyliczony styl, a klasa użyta tylko w próbce nie
// istnieje w zbudowanym CSS.
const PROBKI = {
  pismo10: `<p data-probka="pismo10" style="font-size:10px">Próbka pisma 10 px</p>`,
  "bialy-na-secondary": `<button data-probka="bialy-na-secondary" style="background:hsl(var(--secondary));color:#fff;height:32px;padding:0 12px">Próbka</button>`,
  cel16: `<button data-probka="cel16" aria-label="Próbka celu" style="display:inline-block;width:16px;height:16px;border:1px solid"></button>`,
  niebieski: `<p data-probka="niebieski" style="color:rgb(37,99,235)">Próbka koloru blue-600</p>`,
  "wybrany-obcy": `<button data-probka="wybrany-obcy" aria-pressed="true" style="background:hsl(var(--primary));color:#fff;height:32px;padding:0 12px">Próbka wybranego</button>`,
};

async function krok(p, tekst) {
  const [polecenie, ...reszta] = tekst.split(" "); const r = reszta.join(" ");
  if (polecenie === "klik") return p.locator(r).first().click();
  if (polecenie === "wpisz") { const [sel, ...t] = r.split(" = "); return p.locator(sel).first().fill(t.join(" = ")); }
  if (polecenie === "klawisz") return p.keyboard.press(r);
  if (polecenie === "czekaj") return p.locator(r).first().waitFor({ state: "visible", timeout: 20000 });
  if (polecenie === "blokuj") return p.route(r, (route) => route.abort());
  if (polecenie === "wstrzyknij") {
    if (r === "skok-h1-h3") return p.evaluate(() => document.querySelector("h1").insertAdjacentHTML("afterend", `<h3 data-probka="skok-h1-h3">Próbka skoku</h3>`));
    if (!PROBKI[r]) throw new Error(`nieznana próbka: ${r}`);
    return p.evaluate((html) => (document.querySelector("main main") ?? document.querySelector("main")).insertAdjacentHTML("afterbegin", html), PROBKI[r]);
  }
  throw new Error(`nieznany krok: ${tekst}`);
}

const req = createRequire(process.cwd() + "/");
let pw; for (const m of ["playwright-core", "playwright"]) { try { pw = req(m); break; } catch {} }
if (!pw) { console.error("brak playwright-core/playwright w katalogu bieżącym"); process.exit(2); }

const b = await pw.chromium.launch({ channel: "chrome", headless: true });
const ctx = await b.newContext({ reducedMotion: "reduce", timezoneId: "Europe/Warsaw", locale: "pl-PL", ...(arg("stan") ? { storageState: arg("stan") } : {}) });
const wynik = { meta: { baza, szerokosci, kanarek, data: new Date().toISOString() }, strony: {} };
for (const szer of szerokosci) {
  const p = await ctx.newPage();
  await p.setViewportSize({ width: szer, height: 900 });
  for (const linia of linie) {
    const tylko = linia.match(/^@(\d+) /);
    if (tylko && Number(tylko[1]) !== szer) continue;
    const [s, ...kroki] = linia.replace(/^@\d+ /, "").split(" | ");
    await p.unrouteAll({ behavior: "ignoreErrors" });
    const odp = await p.goto(baza + s, { waitUntil: "networkidle" });
    await p.locator(kanarek).first().waitFor({ state: "attached", timeout: 20000 }).catch(() => {});
    for (const k of kroki) {
      try { await krok(p, k); } catch (e) { throw new Error(`krok „${k}” nie przeszedł: ${szer} ${linia}\n${e.message}`); }
    }
    if (kroki.length) await p.waitForLoadState("networkidle").catch(() => {});
    await p.evaluate(() => document.fonts.ready);
    // Okno w trakcie wejścia ma opacity < 1 i zaniża kontrast: pomiar dopiero po końcu animacji (nieskończone pomijamy).
    await p.evaluate(() => Promise.all(document.getAnimations().filter((a) => a.effect?.getTiming().iterations !== Infinity).map((a) => a.finished.catch(() => {}))));
    // Bez ruchu (reducedMotion) odsłony stoją w stanie końcowym; inaczej
    // pomiar bierze klatkę animacji za styl.
    const dane = await p.evaluate(({ kanarek, zTekstem }) => {
      // Okno (dialog, szuflada, popover) leży poza `main`; rama to powłoka aplikacji wokół treści.
      const strefa = (el) => el.closest("[role=dialog],[role=alertdialog],[data-radix-popper-content-wrapper]") ? "okno"
        : el.closest("main") ? "tresc" : el.closest("footer") ? "stopka" : "rama";
      // Kolor w dowolnym zapisie (rgb, oklab, color()) sprowadzony do RGBA pikselem płótna.
      const plotno = document.createElement("canvas").getContext("2d", { willReadFrequently: true });
      const pamiec = new Map();
      const rgba = (c) => {
        if (pamiec.has(c)) return pamiec.get(c);
        const m = c.match(/^rgba?\(([\d.]+),? ([\d.]+),? ([\d.]+)(?:,? \/? ?([\d.]+))?\)$/);
        let w;
        if (m) w = [+m[1], +m[2], +m[3], m[4] === undefined ? 1 : +m[4]];
        else { plotno.clearRect(0, 0, 1, 1); plotno.fillStyle = "#000"; plotno.fillStyle = c; plotno.fillRect(0, 0, 1, 1); const d = plotno.getImageData(0, 0, 1, 1).data; w = [d[0], d[1], d[2], +(d[3] / 255).toFixed(3)]; }
        pamiec.set(c, w); return w;
      };
      const naloz = (gora, dol) => { const a = gora[3]; return [0, 1, 2].map((i) => gora[i] * a + dol[i] * (1 - a)).concat(1); };
      // Tło pod elementem: warstwy przodków od pierwszej nieprzezroczystej w górę, złożone; bez żadnej biel strony.
      const tloPod = (el) => {
        const warstwy = []; let obraz = false; let przygaszenie = 1;
        for (let e = el; e; e = e.parentElement) {
          const cs = getComputedStyle(e);
          przygaszenie *= parseFloat(cs.opacity);
          if (cs.backgroundImage !== "none" && !cs.backgroundImage.startsWith("url(")) obraz = true;
          const c = rgba(cs.backgroundColor);
          if (c[3] > 0) { warstwy.push(c); if (c[3] >= 1) break; }
        }
        let wynik = [255, 255, 255, 1];
        for (const w of warstwy.reverse()) wynik = naloz(w, wynik);
        return { tlo: wynik, obraz, przygaszenie };
      };
      const lum = (c) => { const f = (x) => { x /= 255; return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
      const kontrast = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return +((x + 0.05) / (y + 0.05)).toFixed(2); };
      const zapis = (c) => `rgb(${c.slice(0, 3).map(Math.round).join(", ")})`;
      const wylaczony = (el) => !!el.closest(":disabled,[aria-disabled=true],[data-disabled]");
      // Element nagłówka standardowej tabeli (ikony filtra i sortu, plakietka liczby sortowań): wspólny klocek panelu.
      // Nazwane elementy standard-table poza progami: nagłówek kolumny i plakietka liczby na „Sortowanie”/„Grupowanie”.
      const PRZYCISK_STD = /^(Sortowanie|Grupowanie|Sorting|Grouping)/;
      const stdTh = (el) => !!el.closest("th[data-col-id]") || (el.tagName === "DIV" && PRZYCISK_STD.test(el.closest("button")?.textContent.trim() ?? ""));
      const wykres = (el) => !!el.closest(".recharts-wrapper,[data-wykres]");

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
        const { tlo, obraz, przygaszenie } = tloPod(el);
        const kol = rgba(cs.color);
        const widoczny = naloz([kol[0], kol[1], kol[2], kol[3] * przygaszenie], tlo);
        const fw = cs.fontWeight;
        tekst.push({ tag: el.tagName.toLowerCase(), kanarek: !!el.closest(kanarek), strefa: strefa(el),
          fs, lh: cs.lineHeight === "normal" ? null : +(parseFloat(cs.lineHeight) / fs).toFixed(2),
          fw, fst: cs.fontStretch, ls: cs.letterSpacing === "normal" ? "normal" : +(parseFloat(cs.letterSpacing) / fs).toFixed(3) + "em",
          ff: cs.fontFamily.split(",")[0].replace(/["']/g, ""), kol: cs.color,
          tlo: zapis(tlo), kr: kontrast(widoczny, tlo), tloObraz: obraz, duzy: fs >= 24 || (fs >= 18.66 && +fw >= 700),
          wyl: wylaczony(el), stdTh: stdTh(el), wykres: wykres(el), probka: el.closest("[data-probka]")?.dataset.probka ?? null,
          ...(zTekstem ? { txt: el.textContent.trim().slice(0, 40) } : {}) });
      }
      const akcje = [...document.querySelectorAll("a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[role=tab],[role=link],[role=radio],[role=checkbox],[role=switch]")]
        .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && !el.closest("[aria-hidden=true]"); })
        .map((el) => { const cs = getComputedStyle(el); let r = el.getBoundingClientRect();
          // Link rozciągnięty pseudo-elementem (`after:absolute after:inset-0`): celem jest blok, który pseudo wypełnia.
          const po = getComputedStyle(el, "::after");
          if (po.position === "absolute" && po.content !== "none" && cs.position === "static" && el.offsetParent) {
            const rb = el.offsetParent.getBoundingClientRect(); if (rb.width * rb.height > r.width * r.height) r = rb;
          }
          // Kontrolka w klikalnej komórce albo etykiecie (td/th z kursorem rączki, label) bez drugiej akcji: celem jest komórka.
          const kom = el.parentElement;
          if (kom && /^(TD|TH|LABEL)$/.test(kom.tagName) && (kom.tagName === "LABEL" || getComputedStyle(kom).cursor === "pointer")
              && kom.querySelectorAll("a[href],button,input:not([type=hidden]),select,textarea,[role=checkbox],[role=button]").length === 1) {
            const rk = kom.getBoundingClientRect(); if (rk.width * rk.height > r.width * r.height) r = rk;
          }
          // Link w zdaniu: WCAG 2.5.8 zwalnia go z minimum celu dotyku.
          const rodzic = el.parentElement; const wZdaniu = el.tagName === "A" && !!rodzic && /^(P|LI|DD|TD|SPAN|STRONG|EM)$/.test(rodzic.tagName)
            && rodzic.textContent.trim().length > el.textContent.trim().length + 3;
          // Stan wyboru opcji w grupie albo filtra; zakładka i włącznik to inne rzeczy (AD-403), więc idą osobnym polem.
          const rola = el.getAttribute("role") ?? "";
          const wybrany = el.getAttribute("aria-pressed") === "true" || el.getAttribute("data-state") === "on"
            || (rola === "radio" && el.getAttribute("aria-checked") === "true");
          return { tag: el.tagName.toLowerCase(), rola, strefa: strefa(el), wZdaniu, w: Math.round(r.width), h: Math.round(r.height),
            rad: cs.borderRadius, tlo: cs.backgroundColor, tloPod: zapis(tloPod(el).tlo), ramka: cs.borderTopWidth + " " + cs.borderTopColor,
            fs: parseFloat(cs.fontSize), fw: cs.fontWeight, kol: cs.color, wybrany, wyl: wylaczony(el), stdTh: stdTh(el),
            probka: el.closest("[data-probka]")?.dataset.probka ?? null }; });
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
    // (przekierowanie na logowanie, pusty render, zły selektor). W oknie
    // modalnym (otwartym krokiem albo adresem, np. panel rekordu na telefonie)
    // strona pod spodem jest aria-hidden, więc kanarkiem jest treść okna.
    const zKanarkiem = dane.tekst.some((e) => e.kanarek) || dane.tekst.some((e) => e.strefa === "okno");
    if (!zKanarkiem) throw new Error(`kanarek „${kanarek}” nie wszedł do pomiaru: ${szer} ${linia} (url: ${dane.url})`);
    wynik.strony[`${szer} ${linia}`] = dane;
  }
  await p.close();
}
await b.close();
console.log(JSON.stringify(wynik));
