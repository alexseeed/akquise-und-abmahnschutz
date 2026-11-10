#!/usr/bin/env node
/**
 * SUBCATEGORY HARVESTER — extends the discovery surface of amazon_seller_scraper.mjs.
 *
 * Why: every main category has many subcategories with their own "new arrivals" lists.
 * How: product pages contain their category path. The harvester takes products from an
 * earlier scraper run (state_<KAMPAGNE>.json), reads the category node numbers and writes
 * subkategorien.json. The scraper uses that file as soon as SUB_SEITEN is set.
 *
 * Cost: category paths already captured by stage 2 of the scraper are reused for free;
 * only products without a stored path are fetched (at most STICHPROBE requests).
 *
 * Safeguards:
 *   - a node must occur at least MIN_TREFFER times per area (single hits = noise)
 *   - nodes that occur in more than 60 % of all areas are dropped (global navigation)
 *   - nodes that are top-level categories (kategorien.json) are dropped (would repeat the main lists)
 *   - every node is written once; the alias of its main category is carried over (i=<alias> URL)
 *
 * Run (in the same folder as the scraper run):
 *   OXYLABS_USER=... OXYLABS_PASS='...' node ernter_unterkategorien.mjs
 *   (OXYLABS_USERNAME / OXYLABS_PASSWORD are accepted as well)
 *
 * API errors: same retry rule as the scraper (wiederholen.mjs, MAX_RETRIES attempts with exponential backoff);
 * a product that still fails is skipped, the count is printed at the end.
 */
import { readFileSync, writeFileSync, existsSync, renameSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { abrufen, schlafen, ApiFehler } from "./wiederholen.mjs";

// optional .env (working folder first, then script folder); variables already set in the shell always win
for (const d of [process.cwd(), dirname(fileURLToPath(import.meta.url))]) {
  const f = join(d, ".env"); if (!existsSync(f)) continue;
  for (const z of readFileSync(f, "utf8").split(/\r?\n/)) {
    const m = z.match(/^\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=\s*(.*?)\s*$/); if (!m || m[1] in process.env) continue;
    const v = /^(['"]).*\1$/.test(m[2]) ? m[2].slice(1, -1) : m[2].replace(/\s+#.*$/, "");
    if (v !== "") process.env[m[1]] = v;
  }
}
const env = process.env;
const fail = (m) => { console.error(`FEHLER: ${m}`); process.exit(1); };
const num = (k, def, min = 0) => { const raw = String(env[k] ?? "").trim(); if (!raw) return def; const v = Number(raw.replace(/_/g, ""));
  if (!Number.isInteger(v) || v < min) fail(`${k}=${raw} ist ungültig (ganze Zahl ≥ ${min}, ohne Tausenderpunkt).`); return v; };

const U = env.OXYLABS_USER ?? env.OXYLABS_USERNAME;
const P = env.OXYLABS_PASS ?? env.OXYLABS_PASSWORD;
const OX_URL = env.OXYLABS_URL || "https://realtime.oxylabs.io/v1/queries";
const KAMPAGNE = String(env.KAMPAGNE || "standard").trim();
const STICHPROBE = num("STICHPROBE", 600);
const MAX_JE_BEREICH = num("MAX_JE_BEREICH", 40, 1);
const MIN_TREFFER = num("MIN_TREFFER", 2, 1);
const MIN_SUBS = num("MIN_SUBS", 40, 1);
const RATE = num("RATE", 30, 1), CONC = num("CONC", 25, 1);
const MAX_RETRIES = num("MAX_RETRIES", 5, 1);

const STATE = `state_${KAMPAGNE}.json`;
if (!existsSync(STATE)) fail(`${STATE} nicht gefunden — erst einen Scraper-Lauf (gleiche KAMPAGNE) machen und im selben Ordner starten.`);
let S; try { S = JSON.parse(readFileSync(STATE, "utf8")); } catch (e) { fail(`${STATE} ist beschädigt: ${e.message}`); }
const katDatei = existsSync("kategorien.json") ? "kategorien.json" : join(dirname(fileURLToPath(import.meta.url)), "kategorien.json");
if (!existsSync(katDatei)) fail("kategorien.json nicht gefunden.");
const KAT = JSON.parse(readFileSync(katDatei, "utf8"));
const ALIAS = new Map(KAT.map((k) => [k.name, k.alias ?? null]));
// top-level nodes incl. the old root nodes that redirect to the store page (never useful as subcategory)
const ROOTS = new Set([...KAT.map((k) => Number(k.node)), 10925241, 12950661, 16435121, 64257031, 80085031, 192417031, 213084031, 340850031]);

// products per area (= main category name); keyword hits carry no category and are skipped
const proBereich = new Map();
// a stored category path is never overwritten by an entry without one (main products are stored without their path)
const add = (k) => { if (!k?.kat || !k?.asin || !ALIAS.has(k.kat)) return; if (!proBereich.has(k.kat)) proBereich.set(k.kat, new Map());
  const m = proBereich.get(k.kat), alt = m.get(k.asin); if (!(Array.isArray(alt) && alt.length)) m.set(k.asin, k.nodes ?? alt ?? null); };
for (const k of (S.kandidaten ?? [])) add(k);
for (const s of Object.values(S.seller ?? {})) add(s.hp);
const bereiche = [...proBereich.keys()];
if (!bereiche.length) fail("Keine Produkte aus Kategorien im Zustand gefunden.");

const gratis = [], auswahl = [];
for (const [kat, m] of proBereich) for (const [asin, nodes] of m) if (Array.isArray(nodes) && nodes.length) gratis.push({ kat, nodes });
const listen = bereiche.map((n) => ({ n, asins: [...proBereich.get(n)].filter(([, nodes]) => !(Array.isArray(nodes) && nodes.length)).map(([a]) => a) }));
for (let i = 0; auswahl.length < STICHPROBE; i++) {
  let neu = false;
  for (const l of listen) { if (auswahl.length >= STICHPROBE) break; if (l.asins[i]) { auswahl.push({ kat: l.n, asin: l.asins[i] }); neu = true; } }
  if (!neu) break;
}
console.log(`Ernte Kategoriepfade: ${gratis.length} Produkte mit gespeichertem Pfad (0 Abfragen) + ${auswahl.length} Produktseiten abrufen (${bereiche.length} Bereiche) …`);
if (auswahl.length && (!U || !P)) fail("Oxylabs-Zugang fehlt: OXYLABS_USER und OXYLABS_PASS setzen (oder OXYLABS_USERNAME / OXYLABS_PASSWORD).");

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
class Lim { constructor(r) { this.rps = r; this.t = r; this.last = Date.now(); }
  async take() { for (;;) { const n = Date.now(); this.t = Math.min(this.rps, this.t + ((n - this.last) / 1000) * this.rps); this.last = n; if (this.t >= 1) { this.t -= 1; return; } await sleep(40); } } }
const lim = new Lim(RATE); let used = 0, STOP = null, fehlgeschlagen = 0;
// retry rule: wiederholen.mjs. Access/quota errors stop the harvester, anything else only skips this product.
async function ox(body) {
  try {
    const a = await abrufen(OX_URL, { method: "POST", headers: { "Content-Type": "application/json", Authorization: "Basic " + Buffer.from(`${U}:${P}`).toString("base64") },
      body: JSON.stringify(body) }, { label: "Oxylabs", maxVersuche: MAX_RETRIES, timeoutMs: 180000, schlafen: (ms) => schlafen(ms, () => !!STOP),
      vorVersuch: async () => { if (STOP) throw new ApiFehler("gestoppt"); await lim.take(); },
      nachVersuch: (x) => { if (x.http >= 200 && x.http < 300) used += x.status ? Math.max(1, x.j?.results?.length ?? 1) : 1; } });
    return a.j;
  } catch (e) {
    if (!(e instanceof ApiFehler)) throw e;
    if ([401, 402, 403].includes(e.status)) { STOP ??= `${e.message} — Zugangsdaten/Kontingent prüfen.`; return null; }
    if (!STOP && ++fehlgeschlagen <= 5) console.error(`\n  ${e.message}`);
    return null;
  }
}
function nummern(c) {
  const treffer = new Set();
  const scan = (text) => { for (const re of [/node%3D(\d{4,12})/g, /node=(\d{4,12})/g, /"node"\s*:\s*"?(\d{4,12})/g, /\/b\/[^"]*?node=(\d{4,12})/g]) for (const m of text.matchAll(re)) treffer.add(Number(m[1])); };
  scan(JSON.stringify([c?.category, c?.categories, c?.breadcrumbs, c?.ladder, c?.category_path, c?.sales_rank]));
  if (!treffer.size) scan(JSON.stringify(c ?? "").slice(0, 40000));            // fallback: raw text (may contain related links)
  return [...treffer];
}

const zaehler = new Map(); let mitPfad = 0, fertig = 0, idx = 0;
const zaehle = (kat, nn) => { if (!nn.length) return; mitPfad++; if (!zaehler.has(kat)) zaehler.set(kat, new Map()); const m = zaehler.get(kat); for (const n of new Set(nn)) m.set(n, (m.get(n) ?? 0) + 1); };
for (const g of gratis) zaehle(g.kat, g.nodes);
await Promise.all(Array.from({ length: Math.min(CONC, Math.max(1, auswahl.length)) }, async () => {
  while (!STOP) {
    const i = idx++; if (i >= auswahl.length) return;
    const { kat, asin } = auswahl[i];
    const c = (await ox({ source: "amazon_product", domain: "de", query: asin, parse: true }))?.results?.[0]?.content;
    fertig++;
    if (fertig % 50 === 0 || fertig === auswahl.length) process.stdout.write(`\r  ${fertig}/${auswahl.length} · ${mitPfad} mit Pfad · ${used} Abfragen  `);
    if (c) zaehle(kat, nummern(c));
  }
}));
process.stdout.write("\n");
if (STOP) fail(STOP);
if (fehlgeschlagen) console.log(`Fehler: ${fehlgeschlagen} von ${auswahl.length} Produktseiten ohne Ergebnis (nach je bis zu ${MAX_RETRIES} Versuchen bzw. dauerhafter Fehler) — übersprungen.`);

const roh = [];
for (const [kat, m] of zaehler) {
  const top = [...m.entries()].filter(([n, c]) => c >= MIN_TREFFER && !ROOTS.has(n)).sort((a, b) => b[1] - a[1]).slice(0, MAX_JE_BEREICH);
  top.forEach(([node, c]) => roh.push({ n: kat, node, c }));
  console.log(`  ${kat}: ${top.length} Unterkategorien`);
}
// global navigation: node appears in >= 60 % of all areas (at least 3)
const bereicheJeNode = new Map(); for (const e of roh) { if (!bereicheJeNode.has(e.node)) bereicheJeNode.set(e.node, new Set()); bereicheJeNode.get(e.node).add(e.n); }
const global = new Set([...bereicheJeNode].filter(([, b]) => b.size >= Math.max(3, bereiche.length * 0.6)).map(([n]) => n));
// one entry per node: the area where it occurs most often
const best = new Map();
for (const e of roh) if (!global.has(e.node) && (!best.has(e.node) || e.c > best.get(e.node).c)) best.set(e.node, e);
const sauber = [...best.values()].map(({ n, node }) => (ALIAS.get(n) ? { n, node, alias: ALIAS.get(n) } : { n, node }));

console.log(`\nRoh ${roh.length} · globale Navigation verworfen ${roh.filter((e) => global.has(e.node)).length} · doppelt ${roh.length - sauber.length - roh.filter((e) => global.has(e.node)).length} · verwendbar ${sauber.length}`);
console.log(`Verbrauch: ${used} Abfragen`);
if (sauber.length < MIN_SUBS) {
  console.log(`\nZU WENIG (${sauber.length} < MIN_SUBS=${MIN_SUBS}) — subkategorien.json wurde NICHT geschrieben.`);
  console.log(`Tipp: erst einen größeren Scraper-Lauf (mehr NEU_SEITEN oder Kategorien) machen und dann erneut ernten, oder STICHPROBE erhöhen.`);
  process.exit(0);
}
writeFileSync("subkategorien.json.tmp", JSON.stringify(sauber, null, 1)); renameSync("subkategorien.json.tmp", "subkategorien.json");
console.log(`\nsubkategorien.json geschrieben: ${sauber.length} Unterkategorien.`);
console.log(`Der Scraper nutzt sie, sobald SUB_SEITEN gesetzt ist, z. B. mit SUB_SEITEN=5 und einem höheren ZIEL.`);
console.log(`Die Unterkategorien vergrößern nur die Auswahl: abgerufen wird weiterhin nur, was für ZIEL nötig ist (Budget wie gewohnt: ZIEL × requests_je_lead aus dem Bericht).`);
