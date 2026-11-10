#!/usr/bin/env node
/**
 * AMAZON SELLER SCRAPER (amazon.de)
 *
 * Finds third-party sellers on amazon.de and builds a lead list with company data,
 * portfolio metrics and (optionally) contact data. No target group is built in:
 * every filter is OFF by default (0 or empty = off) and can be switched on via env.
 *
 * Pipeline (resumable, progress in state_<KAMPAGNE>.json):
 *   1 Discovery      category "new arrivals" lists (+ optional subcategories / keywords),
 *                    dead lists (0 results on the first page) are detected and skipped
 *   2 Product pages  buy-box seller of every new ASIN (Amazon itself is never a lead)
 *   3 Seller profile company name, address, country
 *   4 Portfolio      storefront size + sample of 12 product pages: families, brand share, revenue
 *   5 Final check    seller still holds the buy box of its main product (ENDKONTROLLE=0 skips it)
 *   6 Contacts       Bright Data (optional): e-mail, phone, register, VAT id, legal form, managing director
 *   7 Export         master CSV (append only) + batch CSV of this run + JSON report
 *
 * Stages 1-4 run in demand-driven waves: each stage only produces what the next one still needs for ZIEL.
 *
 * Mechanics: Oxylabs realtime API (parse), worker pool + token bucket, hard BUDGET with a clean
 * stop (the stage counter never moves on a budget stop), quota/outage stop, checkpointed discovery
 * pages, shared ASIN memory + seller FACTS cache (facts, not verdicts: the current filters are
 * re-evaluated on cached facts), per-campaign delivery list, atomic file writes, Ctrl+C safe.
 * API errors (wiederholen.mjs): temporary ones (network, timeouts, 408/425/429/5xx, unreadable answers) are retried
 * with exponential backoff (MAX_RETRIES attempts), permanent ones fail at once; one seller's error never stops the run.
 *
 * Keys from the shell or from a .env file (working folder or script folder).
 * Setup check: node amazon_seller_scraper.mjs --pruefen · Quick test: SMOKE=1 node amazon_seller_scraper.mjs
 * Workflow for the AI: ABLAUF.md · All settings: README.md
 */
import { readFileSync, writeFileSync, existsSync, appendFileSync, renameSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { abrufen, holeJson, wartezeit, voruebergehend, meldungVon, schlafen, ApiFehler } from "./wiederholen.mjs";

const SKRIPT_DIR = dirname(fileURLToPath(import.meta.url));
// optional .env (working folder first, then script folder); variables already set in the shell always win
for (const d of [process.cwd(), SKRIPT_DIR]) {
  const f = join(d, ".env"); if (!existsSync(f)) continue;
  for (const z of readFileSync(f, "utf8").split(/\r?\n/)) {
    const m = z.match(/^\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=\s*(.*?)\s*$/); if (!m || m[1] in process.env) continue;
    const v = /^(['"]).*\1$/.test(m[2]) ? m[2].slice(1, -1) : m[2].replace(/\s+#.*$/, "");
    if (v !== "") process.env[m[1]] = v;
  }
}
const env = process.env;
const fail = (msg) => { console.error(`FEHLER: ${msg}`); process.exit(1); };

// ---------- env parsing (strict: a typo must never silently disable the budget) ----------
function num(k, def, { min = 0, max = Infinity, int = true } = {}) {
  const raw = env[k];
  if (raw == null || String(raw).trim() === "") return def;
  const s = String(raw).trim();
  if (/^\d{1,3}(\.\d{3})+$/.test(s)) fail(`${k}=${s}: bitte ohne Tausenderpunkt schreiben (z. B. ${k}=${s.replace(/\./g, "")}).`);
  const v = Number(s.replace(/_/g, "").replace(",", "."));
  if (!Number.isFinite(v) || v < min || v > max || (int && !Number.isInteger(v)))
    fail(`${k}=${s} ist ungültig (erwartet: ${int ? "ganze Zahl" : "Zahl"} ≥ ${min}${max < Infinity ? ` und ≤ ${max}` : ""}).`);
  return v;
}
function flag(k, def) {
  const v = String(env[k] ?? "").trim();
  if (v === "") return def;
  if (v === "0" || v === "1") return v === "1";
  fail(`${k}=${v} ist ungültig (erlaubt: 0 oder 1).`);
}
const liste = (k) => String(env[k] ?? "").split(",").map((s) => s.trim()).filter(Boolean);
const norm = (s) => String(s ?? "").toLowerCase().replace(/[^a-zäöüß0-9 ]/g, " ").replace(/\s+/g, " ").trim();

const SMOKE = flag("SMOKE", false);
// the smoke test is a fixed technical check: settings left over in the environment (PowerShell keeps $env: values) must not widen or narrow it
const SMOKE_IGNORIERT = SMOKE ? ["ZIEL", "BUDGET", "NEU_SEITEN", "SUB_SEITEN", "KAT_LIMIT", "KATEGORIEN", "KEYWORDS", "PREIS_MIN", "LAENDER", "LISTING_MAX_BEWERTUNGEN", "MAX_ANBIETER",
  "PORTFOLIO_MAX_BEWERTUNGEN", "MAX_PRODUKTE", "MIN_MARKENANTEIL", "UMSATZ_MAX", "FIRMEN_AUSSCHLUSS"].filter((k) => String(env[k] ?? "").trim() !== "") : [];
for (const k of SMOKE_IGNORIERT) delete env[k];
const ANREICHERUNG_AN = flag("ANREICHERUNG", true);
const U = env.OXYLABS_USER ?? env.OXYLABS_USERNAME;
const P = env.OXYLABS_PASS ?? env.OXYLABS_PASSWORD;
const BD = env.BRIGHTDATA_TOKEN ?? env.BRIGHTDATA_API_KEY ?? null;
const OX_URL = env.OXYLABS_URL || "https://realtime.oxylabs.io/v1/queries";
const BD_URL = (env.BRIGHTDATA_URL || "https://api.brightdata.com").replace(/\/+$/, "");
if (!U || !P) fail("Oxylabs-Zugang fehlt: OXYLABS_USER und OXYLABS_PASS setzen (oder OXYLABS_USERNAME / OXYLABS_PASSWORD).");

const KAMPAGNE = SMOKE ? "smoke" : String(env.KAMPAGNE || "standard").trim();
if (!/^[\w.-]{1,60}$/.test(KAMPAGNE)) fail(`KAMPAGNE=${KAMPAGNE}: nur Buchstaben, Ziffern, Punkt, Minus, Unterstrich.`);

const CFG = {
  KAMPAGNE,
  ZIEL: num("ZIEL", SMOKE ? 5 : 100),                        // 0 = no target, run in waves until budget/lists end
  BUDGET: num("BUDGET", SMOKE ? 300 : 5000, { min: 1 }),     // hard cap of Oxylabs requests for this state
  RATE: num("RATE", 40, { min: 1 }), CONC: num("CONC", 40, { min: 1 }), CONC_PF: num("CONC_PF", 12, { min: 1 }),
  NEU_SEITEN: num("NEU_SEITEN", SMOKE ? 2 : 75),
  SUB_SEITEN: num("SUB_SEITEN", 0),
  KW_SEITEN: num("KW_SEITEN", 2),
  KATEGORIEN: liste("KATEGORIEN"),                           // name fragments, empty = all active
  KAT_LIMIT: num("KAT_LIMIT", SMOKE ? 2 : 0),                // 0 = no limit
  PREIS_MIN: num("PREIS_MIN", 0, { int: false }),            // server-side price filter (p_36), 0 = off
  // ---- target-group filters: ALL OFF by default ----
  LAENDER: liste("LAENDER").map((s) => s.toUpperCase()),
  LISTING_MAX_BEWERTUNGEN: num("LISTING_MAX_BEWERTUNGEN", 0),
  MAX_ANBIETER: num("MAX_ANBIETER", 0),
  PORTFOLIO_MAX_BEWERTUNGEN: num("PORTFOLIO_MAX_BEWERTUNGEN", 0),
  MAX_PRODUKTE: num("MAX_PRODUKTE", 0),
  MIN_MARKENANTEIL: num("MIN_MARKENANTEIL", 0, { int: false, max: 1 }),
  UMSATZ_MAX: num("UMSATZ_MAX", 0),
  FIRMEN_AUSSCHLUSS: liste("FIRMEN_AUSSCHLUSS").map(norm).filter(Boolean),
  // ---- stages / data ----
  SORTIMENT: flag("SORTIMENT", true),
  MAX_KACHELN: num("MAX_KACHELN", 300, { min: 1 }),
  MAX_SEITEN: num("MAX_SEITEN", 20, { min: 1 }),
  PROBE: 12,
  SCHAETZ_KAEUFER: num("SCHAETZ_KAEUFER", 25),
  CACHE_TAGE: num("CACHE_TAGE", 90),
  ENDKONTROLLE: flag("ENDKONTROLLE", true),
  BD_TIMEOUT_MIN: num("BD_TIMEOUT_MIN", 30, { min: 1 }),
  MAX_RETRIES: num("MAX_RETRIES", 5, { min: 1, max: 20 }),  // attempts per request on temporary errors (backoff 2/4/8/16 s, 429: 5/10/20/40 s)
  OX_USD_JE_1000: num("OX_USD_JE_1000", 0.45, { int: false }),
  BD_USD_JE_1000: num("BD_USD_JE_1000", 1.5, { int: false }),
  BD_BATCH: 50, SAVE_MS: 20000,
};
const FILTER_AN = [
  CFG.LAENDER.length && `LAENDER=${CFG.LAENDER.join(",")}`,
  CFG.LISTING_MAX_BEWERTUNGEN && `LISTING_MAX_BEWERTUNGEN=${CFG.LISTING_MAX_BEWERTUNGEN}`,
  CFG.MAX_ANBIETER && `MAX_ANBIETER=${CFG.MAX_ANBIETER}`,
  CFG.PORTFOLIO_MAX_BEWERTUNGEN && `PORTFOLIO_MAX_BEWERTUNGEN=${CFG.PORTFOLIO_MAX_BEWERTUNGEN}`,
  CFG.MAX_PRODUKTE && `MAX_PRODUKTE=${CFG.MAX_PRODUKTE}`,
  CFG.MIN_MARKENANTEIL && `MIN_MARKENANTEIL=${CFG.MIN_MARKENANTEIL}`,
  CFG.UMSATZ_MAX && `UMSATZ_MAX=${CFG.UMSATZ_MAX}`,
  CFG.FIRMEN_AUSSCHLUSS.length && `FIRMEN_AUSSCHLUSS=${CFG.FIRMEN_AUSSCHLUSS.join(",")}`,
  CFG.PREIS_MIN && `PREIS_MIN=${CFG.PREIS_MIN}`,
].filter(Boolean);
const SORTIMENT_FILTER = CFG.PORTFOLIO_MAX_BEWERTUNGEN || CFG.MAX_PRODUKTE || CFG.MIN_MARKENANTEIL || CFG.UMSATZ_MAX;
if (!CFG.SORTIMENT && SORTIMENT_FILTER) console.warn("WARNUNG: SORTIMENT=0 — Sortiment-Filter greifen nur bei Verkäufern, deren Sortiment schon im Gedächtnis steht.");
if (!BD) console.warn("Hinweis: kein BRIGHTDATA_TOKEN — Leads ohne Kontaktdaten (E-Mail, Telefon, Register).");

// ---------- categories, subcategories, keywords ----------
const katDatei = existsSync("kategorien.json") ? "kategorien.json" : join(SKRIPT_DIR, "kategorien.json");
if (!existsSync(katDatei)) fail("kategorien.json nicht gefunden (gehört in denselben Ordner wie das Skript).");
let KAT_ALLE;
try { KAT_ALLE = JSON.parse(readFileSync(katDatei, "utf8")); } catch (e) { fail(`kategorien.json ist kein gültiges JSON: ${e.message}`); }
if (!Array.isArray(KAT_ALLE)) fail("kategorien.json muss eine Liste sein.");
for (const k of KAT_ALLE) if (!k?.name || !/^\d{3,12}$/.test(String(k.node))) fail(`kategorien.json: ungültiger Eintrag ${JSON.stringify(k)}`);
const ROOT_NODES = new Set(KAT_ALLE.map((k) => Number(k.node)));
let KATEGORIEN = KAT_ALLE.filter((k) => k.aktiv !== false);
if (CFG.KATEGORIEN.length) KATEGORIEN = KATEGORIEN.filter((k) => CFG.KATEGORIEN.some((f) => k.name.toLowerCase().includes(f.toLowerCase())));
if (CFG.KAT_LIMIT > 0) KATEGORIEN = KATEGORIEN.slice(0, CFG.KAT_LIMIT);
if (!KATEGORIEN.length && !CFG.SUB_SEITEN && !liste("KEYWORDS").length && !existsSync("keywords.txt")) fail("Keine Kategorie aktiv (kategorien.json / KATEGORIEN prüfen).");

let SUBS = [];
if (CFG.SUB_SEITEN > 0) {
  if (!existsSync("subkategorien.json")) console.warn("WARNUNG: SUB_SEITEN gesetzt, aber subkategorien.json fehlt — erst ernter_unterkategorien.mjs ausführen.");
  else {
    try { SUBS = JSON.parse(readFileSync("subkategorien.json", "utf8")); } catch (e) { fail(`subkategorien.json ist kein gültiges JSON: ${e.message}`); }
    SUBS = (Array.isArray(SUBS) ? SUBS : []).filter((s) => /^\d{3,12}$/.test(String(s?.node)) && !ROOT_NODES.has(Number(s.node)));
    if (CFG.KATEGORIEN.length) SUBS = SUBS.filter((s) => CFG.KATEGORIEN.some((f) => String(s.n ?? "").toLowerCase().includes(f.toLowerCase())));
  }
}
// a fragment that matches nothing is a typo or a mangled umlaut: stop instead of silently searching fewer categories
{
  const namen = [...KAT_ALLE.filter((k) => k.aktiv !== false).map((k) => k.name), ...SUBS.map((s) => String(s.n ?? ""))];
  const ohne = CFG.KATEGORIEN.filter((f) => !namen.some((n) => n.toLowerCase().includes(f.toLowerCase())));
  if (ohne.length) fail(`KATEGORIEN: kein Treffer für „${ohne.join("“, „")}“. Gültige Namen (ein Namensteil genügt): ${KAT_ALLE.filter((k) => k.aktiv !== false).map((k) => k.name).join(" · ")}`);
}
const KEYWORDS = CFG.KW_SEITEN > 0
  ? (liste("KEYWORDS").length ? liste("KEYWORDS")
    : existsSync("keywords.txt") ? readFileSync("keywords.txt", "utf8").split(/\r?\n/).map((s) => s.trim()).filter((s) => s && !s.startsWith("#")) : [])
  : [];

// ---------- files ----------
const MEM = SMOKE ? "smoke_" : "";   // smoke never touches the production memory
const F = {
  state: `state_${KAMPAGNE}.json`, deliv: `delivered_${KAMPAGNE}.json`,
  master: `leads_${KAMPAGNE}_MASTER.csv`, report: `report_${KAMPAGNE}.json`,
  seen: `${MEM}seen_asins.json`, facts: `${MEM}seller_cache.json`,
};
const writeAtomic = (f, s) => { writeFileSync(f + ".tmp", s); renameSync(f + ".tmp", f); };
function ladeJson(f, def) {
  if (!existsSync(f)) return def;
  try { return JSON.parse(readFileSync(f, "utf8")); }
  catch (e) { fail(`${f} ist beschädigt (${e.message}). Datei umbenennen, dann startet der Lauf ohne sie.`); }
}
const DEF = () => ({
  version: 1, stufe: 1, kandidaten: [], seller: {}, s1: {}, listen: {}, bd_jobs: {},
  usage: { ox: 0, bd: 0 },
  funnel: { discovery: 0, kandidaten: 0, pdp_done: 0, pdp_ok: 0, seller: 0, profil_ok: 0, profil_raus: 0, portfolio_ok: 0, sortiment_raus: 0, qa_ok: 0, final: 0, exportiert: 0 },
  ausschluss: {}, fehler: {}, land_stat: {}, feld_stat: { pricing_count_gefuellt: 0, pricing_count_leer: 0 },
  start: new Date().toISOString(), laeufe: 0,
});
const geladen = ladeJson(F.state, null);
const S = geladen
  ? { ...DEF(), ...geladen, usage: { ...DEF().usage, ...geladen.usage }, funnel: { ...DEF().funnel, ...geladen.funnel }, feld_stat: { ...DEF().feld_stat, ...geladen.feld_stat } }
  : DEF();
S.laeufe++;
let SEEN = ladeJson(F.seen, {});            // asin -> [seller_id | "" (no third-party seller), day]
if (Array.isArray(SEEN)) { console.warn(`Hinweis: ${F.seen} hat ein altes Format und wird ignoriert.`); SEEN = {}; }
const FACTS = ladeJson(F.facts, {});        // seller_id -> measured facts (never verdicts)
const DELIV = new Set(ladeJson(F.deliv, []));
// one CSV line (export writes no embedded line breaks), quoted fields may contain ";"
const csvFelder = (z) => { const out = []; let cur = "", q = false;
  for (let i = 0; i < z.length; i++) { const ch = z[i];
    if (q) { if (ch === '"') { if (z[i + 1] === '"') { cur += '"'; i++; } else q = false; } else cur += ch; }
    else if (ch === '"' && cur === "") q = true; else if (ch === ";") { out.push(cur); cur = ""; } else cur += ch; }
  out.push(cur); return out; };
const MASTER_IDS = new Set();               // self-healing duplicate guard: seller ids already in the master CSV
if (existsSync(F.master)) {
  const zeilen = readFileSync(F.master, "utf8").replace(/^﻿/, "").split(/\r?\n/);
  const sp = csvFelder(zeilen[0] ?? "").indexOf("Seller-ID");
  if (sp >= 0) for (const z of zeilen.slice(1)) { const id = z ? csvFelder(z)[sp] : null; if (id) MASTER_IDS.add(id); }
}
const save = () => writeAtomic(F.state, JSON.stringify(S));
const saveMem = () => { writeAtomic(F.seen, JSON.stringify(SEEN)); writeAtomic(F.facts, JSON.stringify(FACTS)); writeAtomic(F.deliv, JSON.stringify([...DELIV], null, 1)); };
let lastSave = 0;
const saveT = () => { const n = Date.now(); if (n - lastSave > CFG.SAVE_MS) { lastSave = n; save(); } };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const drop = (g) => { S.ausschluss[g] = (S.ausschluss[g] ?? 0) + 1; };
const raus = (s, g) => { s.status = "raus"; s.grund = g; drop(g); };
const heute = () => Math.floor(Date.now() / 864e5);
const frischTag = (d) => CFG.CACHE_TAGE > 0 && d != null && heute() - d < CFG.CACHE_TAGE;
const frischMs = (t) => CFG.CACHE_TAGE > 0 && !!t && Date.now() - t < CFG.CACHE_TAGE * 864e5;
const de = (n) => Number(n ?? 0).toLocaleString("de-DE");

// ---------- Oxylabs client: token bucket, hard budget, quota/outage stop ----------
class Lim {
  constructor(r) { this.rps = r; this.t = r; this.last = Date.now(); }
  async take() { for (;;) { const n = Date.now(); this.t = Math.min(this.rps, this.t + ((n - this.last) / 1000) * this.rps); this.last = n;
    if (this.t >= 1) { this.t -= 1; return; } await sleep(Math.max(20, Math.ceil(((1 - this.t) / this.rps) * 1000))); } }
}
const lim = new Lim(CFG.RATE);
class StopError extends Error {}           // clean, resumable stop (quota, outage, user abort, error rate)
class QuotaError extends StopError {}
class BudgetError extends Error {}
class AbortError extends Error {}          // another worker stopped the run: leave the item untouched
let ABORT = false, STOPGRUND = null, AKTIV = 1, inflight = 0, nullFolge = 0, BD_AUS = null, BD_STOPP = null, USER_ABBRUCH = false;
// Stages 1-4 stop early enough that the final check (stage 5) can still run for the hits found so far.
const QA_RESERVE = CFG.ENDKONTROLLE ? Math.min(Math.ceil(CFG.BUDGET * 0.05), CFG.ZIEL > 0 ? CFG.ZIEL + 10 : Infinity) : 0;
const limitJetzt = () => (AKTIV >= 5 ? CFG.BUDGET : CFG.BUDGET - QA_RESERVE);
const AUTH = "Basic " + Buffer.from(`${U}:${P}`).toString("base64");

const pause = (ms) => schlafen(ms, () => ABORT);   // backoff pauses end early on a stop
const API_FEHL = { ox: 0, bd: 0 };                 // calls of this start that failed for good (after all attempts or permanent)
const QUOTA_429 = /monthly|traffic limit|subscription|insufficient|balance/i, QUOTA = /no active subscription|insufficient|out of credits|quota exceeded|traffic limit/i;
// retry rule: wiederholen.mjs. The budget slot is reserved before any await, otherwise parallel workers overshoot the cap.
async function ox(body) {
  let a = null;
  try {
    a = await abrufen(OX_URL, { method: "POST", headers: { "Content-Type": "application/json", Authorization: AUTH }, body: JSON.stringify(body) }, {
      label: "Oxylabs", maxVersuche: CFG.MAX_RETRIES, timeoutMs: 180000, schlafen: pause,
      vorVersuch: async () => {
        if (ABORT) throw new AbortError();
        if (S.usage.ox + inflight >= limitJetzt()) throw new BudgetError(`Budget erreicht (${de(S.usage.ox)} von ${de(CFG.BUDGET)} Abfragen${AKTIV < 5 && QA_RESERVE ? `, ${de(QA_RESERVE)} für die Endkontrolle reserviert` : ""})`);
        inflight++;
        await lim.take();
        if (ABORT) { inflight--; throw new AbortError(); }
      },
      nachVersuch: (x) => {
        inflight--;
        // a 2xx answer is paid, also when its body is unreadable (counted as one request)
        if (x.http >= 200 && x.http < 300) S.usage.ox += x.status ? Math.max(1, x.j?.results?.length ?? 1) : 1;
        else if (x.http) {               // quota/access: the whole run stops cleanly (rate limit 429 without quota wording is retried)
          if ([401, 402, 403].includes(x.http) || (x.http === 429 ? QUOTA_429 : QUOTA).test(x.text)) throw new QuotaError(`Oxylabs HTTP ${x.http}: ${x.text.slice(0, 200)}`);
        }
      } });
  } catch (e) {
    if (!(e instanceof ApiFehler)) throw e;
    API_FEHL.ox++;
    if (API_FEHL.ox <= 5) console.error(`\n  ${e.message}`);       // permanent errors (400, 404, 422) and exhausted retries: this item only
  }
  if (a?.j?.results?.[0]?.content != null) { nullFolge = 0; return a.j; }
  // a 2xx without content is paid but unusable: not requested twice
  if (++nullFolge >= 30) throw new StopError("Ausfall: 30 Abrufe in Folge ohne Ergebnis — Internet/Oxylabs prüfen, dann denselben Befehl erneut starten.");
  return null;
}
const con = (j) => j?.results?.[0]?.content ?? null;
const organic = (c) => (Array.isArray(c?.results?.organic) ? c.results.organic : []);

// ---------- worker pool with error accounting and ETA ----------
async function pool(items, cc, fn, label) {
  const n = items.length; if (!n) return;
  let idx = 0, done = 0, fehler = null, err = 0; const t0 = Date.now();
  const zeig = () => { const s = (Date.now() - t0) / 1000, rate = done / Math.max(s, 0.001), rest = (n - done) / Math.max(rate, 0.01);
    process.stdout.write(`\r  ${label} ${de(done)}/${de(n)} · ${rate.toFixed(1)}/s · Rest ~${rest < 90 ? rest.toFixed(0) + " s" : (rest / 60).toFixed(0) + " min"} · ${de(S.usage.ox)}/${de(CFG.BUDGET)} Abfragen   `); };
  const w = async () => {
    while (!ABORT) {
      const i = idx++; if (i >= n) return;
      try { await fn(items[i]); done++; }
      catch (e) {
        if (e instanceof AbortError) return;
        if (e instanceof BudgetError || e instanceof StopError) { fehler ??= e; ABORT = true; return; }
        err++; done++; S.fehler[label] = (S.fehler[label] ?? 0) + 1;
        if (err <= 5) console.error(`\n[${label}] Programmfehler: ${e?.stack ?? e}`);
        if (err > Math.max(20, n * 0.05)) { fehler ??= new StopError(`${label}: zu viele Programmfehler (${err}) — Lauf angehalten`); ABORT = true; return; }
      }
      if (done % 50 === 0 || done === n) zeig();
    }
  };
  await Promise.all(Array.from({ length: Math.min(cc, n) }, w));
  process.stdout.write("\n");
  if (fehler) throw fehler;
  if (ABORT) throw new StopError(STOPGRUND ?? "Abbruch");
}
let sigints = 0;
const stop = (grund) => { if (++sigints > 1) { try { save(); saveMem(); } catch {} console.log("\nSofortiger Abbruch."); process.exit(130); }
  ABORT = true; USER_ABBRUCH = true; STOPGRUND = grund;
  console.log(`\n${grund} — laufende Abrufe werden beendet, der Stand wird gespeichert … (nochmal = sofort beenden)`); };
process.on("SIGINT", () => stop("Abbruch durch Benutzer (Strg+C)"));
process.on("SIGTERM", () => stop("Abbruch (SIGTERM)"));

// ---------- parsing helpers ----------
const clean = (v) => (v == null ? null : String(v).replace(/[\r\n\t\u00a0]+/g, " ").replace(/\s+/g, " ").trim() || null);
const markeClean = (s) => norm(s).replace(/^(marke|brand|hersteller|manufacturer)\s+/i, "").trim();
const PLATZHALTER = /^(generic|generisch|unbekannt|unknown|no brand|ohne marke|keine marke|n a|na|none|diverse)$/;
const AMAZON_IDS = new Set(["A3JWKAKR8XB7XF", "ATVPDKIKX0DER", "A1PA6795UKMFR9"]);
const istAmazon = (id, name) => AMAZON_IDS.has(id) || /^amazon(\.|\s|$)/i.test(String(name ?? "").trim());
// "50+ gekauft", "1.000+", "1K+", "1.5K+", "2 Tsd.+": with a k/Tsd/Mio suffix the separator is a decimal point
const kaeufer = (t) => {
  const m = String(t ?? "").match(/(\d[\d.,]*)\s*(k|tsd\.?|mio\.?)?\s*\+/i); if (!m) return null;
  const suf = (m[2] ?? "").toLowerCase();
  let n = suf ? Number(m[1].replace(",", ".")) : Number(m[1].replace(/[.,]/g, ""));
  if (suf.startsWith("k") || suf.startsWith("tsd")) n *= 1e3; else if (suf.startsWith("mio")) n *= 1e6;
  return Number.isFinite(n) && n > 0 ? Math.round(n) : null;
};
// best seller rank of the main category (= numerically largest entry) + its category name if delivered
const rangVon = (c) => {
  const roh = c?.sales_rank; if (!roh) return null; let best = null;
  for (const e of (Array.isArray(roh) ? roh : [roh])) {
    const m = String(typeof e === "object" ? (e?.rank ?? JSON.stringify(e)) : e).match(/(\d[\d.,]*)/);
    if (!m) continue; const r = Number(m[1].replace(/[.,]/g, ""));
    if (r > 0 && (!best || r > best.r)) best = { r, k: (typeof e === "object" && (e?.ladder?.[0]?.name ?? e?.category)) || null };
  }
  return best;
};
const nodesAus = (c) => {
  const t = JSON.stringify([c?.category, c?.categories, c?.breadcrumbs, c?.ladder, c?.category_path]); const set = new Set();
  for (const re of [/node%3D(\d{4,12})/g, /node=(\d{4,12})/g, /"node"\s*:\s*"?(\d{4,12})/g]) for (const m of t.matchAll(re)) set.add(Number(m[1]));
  return [...set].slice(0, 25);
};
const LAND_NAMEN = { deutschland: "DE", germany: "DE", "österreich": "AT", oesterreich: "AT", austria: "AT", schweiz: "CH", switzerland: "CH", suisse: "CH",
  svizzera: "CH", china: "CN", "hong kong": "HK", hongkong: "HK", polen: "PL", poland: "PL", italien: "IT", italy: "IT", frankreich: "FR", france: "FR",
  spanien: "ES", spain: "ES", niederlande: "NL", netherlands: "NL", "united kingdom": "GB", "vereinigtes königreich": "GB", "united states": "US",
  usa: "US", tschechien: "CZ", "czech republic": "CZ", belgien: "BE", belgium: "BE", luxemburg: "LU", luxembourg: "LU", liechtenstein: "LI" };
function landAus(adr) {
  const a = String(adr ?? "").replace(/\s+/g, " ").trim();
  const m = a.match(/(?:^|[\s,])([A-Za-z]{2})[\s.,;]*$/); if (m) return m[1].toUpperCase();
  const low = a.toLowerCase().replace(/[.,;\s]+$/, "");
  for (const [name, code] of Object.entries(LAND_NAMEN)) if (low.endsWith(name)) return code;
  return "?";
}
// managing director from the seller page text: titles skipped, stop words cut, 2-4 name parts
const GF_STOPP = new Set(("registergericht handelsregister amtsgericht verantwortlich verantwortliche telefon tel sitz geschäftsführer geschäftsführerin " +
  "geschäftsführung inhaber inhaberin email e-mail mail ust ust-id ust-idnr umsatzsteuer registernummer steuernummer adresse anschrift kontakt " +
  "vertreten vertretungsberechtigt gesellschafter managing director ceo firma gmbh ug ag kg ohg gbr straße strasse str business").split(" "));
function gfAus(blob) {
  const t = String(blob ?? "").replace(/\\[nrt]/g, " ").replace(/[\u00a0\u202f]/g, " ");
  const re = /(geschäftsführer(?:in)?|geschäftsführung|vertreten durch|vertretungsberechtigte?r?|inhaber(?:in)?|managing director|ceo)(?![a-zäöü])/gi;
  for (const m of t.matchAll(re)) {
    const rest = t.slice(m.index + m[0].length, m.index + m[0].length + 140)
      .replace(/^[\s:\-–"',]+/, "").replace(/^(?:(?:die|der|den)\s+)?(?:(?:geschäftsführer(?:in)?|inhaber(?:in)?)\s+)?/i, "");
    const out = [];
    for (const raw of rest.split(/\s+/)) {
      if (!raw) continue;
      const tok = raw.replace(/^["'(]+/, "").replace(/[,;:"()]+$/, ""), ende = /[,;:"()]$/.test(raw);
      if (!out.length && /^(herr|frau|hr\.|fr\.|dr\.|prof\.|dipl\.[\w.-]*|mag\.|ing\.)$/i.test(tok)) continue;
      if (GF_STOPP.has(tok.toLowerCase())) break;
      if (out.length && /^(von|van|de|zu|der|den|di|da|le|la|ten|mac)$/.test(tok)) { out.push(tok); continue; }
      if (!/^[A-ZÄÖÜ][a-zäöüßéèáàçñ]+(?:-[A-ZÄÖÜ][a-zäöüßéèáàçñ]+)*$/.test(tok)) break;
      out.push(tok);
      if (ende || out.length >= 4) break;
    }
    while (out.length && /^[a-z]/.test(out[out.length - 1])) out.pop();
    if (out.length >= 2) return out.join(" ");
  }
  return null;
}

// ---------- filters on facts (pure functions, re-evaluated every run against the current config) ----------
const pruefeProfil = (f) => {
  if (CFG.FIRMEN_AUSSCHLUSS.length && CFG.FIRMEN_AUSSCHLUSS.some((w) => norm(f.firma).includes(w))) return "firmen_ausschluss";
  if (CFG.LAENDER.length && !CFG.LAENDER.includes(f.land)) return f.land === "?" ? "land_unklar" : "land_nicht_im_filter";
  return null;
};
const pruefeSortiment = (f) => {
  if (CFG.MAX_PRODUKTE > 0 && f.kacheln != null && f.kacheln > CFG.MAX_PRODUKTE) return "zu_viele_produkte";
  if (CFG.PORTFOLIO_MAX_BEWERTUNGEN > 0) { const pr = f.partial ? f.s1rev_min : f.portfolio_rev; if (pr != null && pr > CFG.PORTFOLIO_MAX_BEWERTUNGEN) return "portfolio_bewertungen"; }
  if (!f.partial && CFG.MIN_MARKENANTEIL > 0) {
    // at least 3 sampled families with a real brand, otherwise the share is not decidable (no-name sellers never pass)
    if ((f.marken_n ?? 0) < Math.min(3, f.familien_probe ?? 3)) return "markenanteil_unklar";
    if ((f.dominanz ?? 0) < CFG.MIN_MARKENANTEIL * 100) return "markenanteil_zu_gering";
  }
  // only on a measured basis ("X+ gekauft" on >= 2 sampled families, scaled to all families); estimates never filter
  if (!f.partial && CFG.UMSATZ_MAX > 0 && f.umsatz_gem != null && f.umsatz_gem > CFG.UMSATZ_MAX) return "umsatz_ueber_max";
  return null;
};
// null = no fresh facts · {ok:false,grund} = fails a current filter · {ok:true} = all decidable and passed · {ok:null} = needs measuring
function bewerteFakten(f) {
  if (!f || !frischMs(f.t) || !f.land) return null;
  const g = pruefeProfil(f); if (g) return { ok: false, grund: g };
  if (!f.t_sortiment || !frischMs(f.t_sortiment)) return { ok: null };
  const g2 = pruefeSortiment(f); if (g2) return { ok: false, grund: g2 };
  return f.partial ? { ok: null } : { ok: true };
}

// ---------- demand planning (waves) ----------
// Stages 1-3 only produce what the next stage still needs for the current wave, based on the pass rates
// observed so far (+15 % margin). An unfiltered run therefore never pays for tens of thousands of product
// pages before the first lead, and a budget stop always finds the hits of earlier waves. ZIEL=0: waves
// continue until the budget or the lists end.
// The first wave stays small until the pass rates of stages 3 and 4 are measured (default rates are only guesses).
const WELLE = 100, START_WELLE = 20;
const kalibriert = () => S.funnel.profil_ok + S.funnel.profil_raus >= 20 && S.funnel.portfolio_ok + S.funnel.sortiment_raus >= 20;
const wellenZiel = () => { const w = S.funnel.portfolio_ok + (kalibriert() ? WELLE : START_WELLE); return CFG.ZIEL > 0 ? Math.min(CFG.ZIEL, w) : w; };
const quote = (ok, nein, def) => (ok + nein >= 20 ? Math.max(0.03, ok / (ok + nein)) : def);
function bedarf() {
  let neu = 0, profilOk = 0;
  for (const s of Object.values(S.seller)) { if (s.status === "neu") neu++; else if (s.status === "profil_ok") profilOk++; }
  const offenPdp = S.kandidaten.reduce((a, k) => a + (k.done ? 0 : 1), 0);
  const p4 = quote(S.funnel.portfolio_ok, S.funnel.sortiment_raus, SORTIMENT_FILTER ? 0.3 : 0.9);
  const p3 = quote(S.funnel.profil_ok, S.funnel.profil_raus, CFG.LAENDER.length || CFG.FIRMEN_AUSSCHLUSS.length ? 0.2 : 0.9);
  const p2 = S.funnel.pdp_done >= 50 ? Math.max(0.02, S.funnel.seller / S.funnel.pdp_done) : 0.5;   // new sellers per product page
  const mindest = (n, min) => (n > 0 ? Math.max(n, min) : 0);
  const profil = mindest(Math.ceil((Math.max(0, wellenZiel() - S.funnel.portfolio_ok) / p4) * 1.15) - profilOk, 5);
  const seller = mindest(Math.ceil((profil / p3) * 1.15) - neu, 10);
  const pdp = mindest(Math.ceil((seller / p2) * 1.15) - offenPdp, 50);
  return { profil, seller, pdp, p2, p3 };
}

// ---------- STAGE 1: DISCOVERY ----------
const PREIS_RH = CFG.PREIS_MIN > 0 ? `p_36%3A${Math.round(CFG.PREIS_MIN * 100)}-` : "";
const nodeUrl = (e) => (p) => `https://www.amazon.de/s?${e.alias ? `i=${encodeURIComponent(e.alias)}&` : ""}rh=n%3A${e.node}${PREIS_RH ? "%2C" + PREIS_RH : ""}&s=date-desc-rank&page=${p}`;
function baueListen() {
  const l = [];
  for (const k of KATEGORIEN) l.push({ id: `kat|${k.alias ?? ""}|${k.node}`, typ: "kategorie", kat: k.name, label: k.name, seiten: CFG.NEU_SEITEN, url: nodeUrl(k) });
  if (CFG.SUB_SEITEN > 0) for (const s of SUBS) l.push({ id: `sub|${s.alias ?? ""}|${s.node}`, typ: "unterkategorie", kat: s.n ?? "Unterkategorie", label: `${s.n ?? "?"} › ${s.node}`, seiten: CFG.SUB_SEITEN, url: nodeUrl(s) });
  for (const kw of KEYWORDS) l.push({ id: `kw|${kw.toLowerCase()}`, typ: "keyword", kat: `Keyword: ${kw}`, label: `Keyword „${kw}"`, seiten: CFG.KW_SEITEN,
    url: (p) => `https://www.amazon.de/s?k=${encodeURIComponent(kw)}${PREIS_RH ? `&rh=${PREIS_RH}` : ""}&page=${p}` });
  return [...new Map(l.filter((x) => x.seiten > 0).map((x) => [x.id, x])).values()];
}
const listSt = (l) => (S.listen[l.id] ??= { label: l.label, typ: l.typ, kat: l.kat, url: l.url(1), tot: false, ende: null, seiten: 0, treffer: 0, kandidaten: 0 });
const offeneSeiten = (l) => { const x = listSt(l); if (x.tot || x.leer_lauf === S.laeufe) return []; const out = [];
  for (let p = 1; p <= l.seiten; p++) { if (x.ende && p > x.ende) break; if (S.s1[`${l.id}|${p}`] == null) out.push(p); } return out; };
const stufe1Offen = () => baueListen().reduce((a, l) => a + offeneSeiten(l).length, 0);

async function stufe1() {
  AKTIV = 1;
  const listen = baueListen();
  const gesamt = listen.reduce((a, l) => a + offeneSeiten(l).length, 0);
  const n = (t) => listen.filter((l) => l.typ === t).length;
  console.log(`Stufe 1: Discovery — ${de(gesamt)} offene Listenseiten · ${n("kategorie")} Kategorien${n("unterkategorie") ? ` · ${n("unterkategorie")} Unterkategorien` : ""}${n("keyword") ? ` · ${n("keyword")} Keywords` : ""}`);
  console.log(`  Gedächtnis: ${de(Object.keys(SEEN).length)} ASINs · ${de(Object.keys(FACTS).length)} Verkäufer-Fakten · ${de(DELIV.size)} geliefert (${KAMPAGNE})`);
  const lokal = new Set(S.kandidaten.map((k) => k.asin));
  // sellers already planned in this state: a known seller costs at most one product page, not one per known ASIN
  const geplant = new Set(Object.keys(S.seller)); for (const k of S.kandidaten) if (k.seller_id || k.sid_hint) geplant.add(k.seller_id || k.sid_hint);
  let limit = Infinity, neuK = 0;
  const holen = async ({ l, p }) => {
    const key = `${l.id}|${p}`, x = listSt(l);
    if (neuK >= limit) return;                            // demand of this wave covered: page stays open
    if (x.tot || (x.ende && p > x.ende)) { S.s1[key] = -2; return; }
    if (x.leer_lauf === S.laeufe) return;
    const erste = x.seiten === 0;
    const c = con(await ox({ source: "amazon", url: l.url(p), parse: true }));
    if (!c) return;                                       // failed: page stays open for the next start
    const items = organic(c);
    if (!items.length && erste) {                         // empty first page: dead only if it is empty again on a later start
      x.leer = (x.leer ?? 0) + 1; x.leer_lauf = S.laeufe;
      if (x.leer >= 2) { x.tot = true; S.s1[key] = 0; }
      saveT(); return;
    }
    S.s1[key] = items.length; x.seiten++;
    if (!items.length) { if (!x.ende || p < x.ende) x.ende = p; saveT(); return; }
    for (const it of items) {
      S.funnel.discovery++; x.treffer++;
      const asin = it.asin; if (!asin) continue;
      if (lokal.has(asin)) { drop("dublette"); continue; }
      lokal.add(asin);
      const b = SEEN[asin];
      let hint = null;
      if (b && frischTag(b[1])) {                         // known ASIN: skip for free only if the outcome is already clear
        const sid = b[0];
        if (!sid) { drop("bekannt_ohne_drittanbieter"); continue; }
        if (DELIV.has(sid) || MASTER_IDS.has(sid)) { drop("bekannt_bereits_geliefert"); continue; }
        if (S.seller[sid]) { S.seller[sid].treffer = (S.seller[sid].treffer ?? 1) + 1; drop("bekannt_seller_schon_im_lauf"); continue; }
        const v = bewerteFakten(FACTS[sid]); if (v?.ok === false) { drop("cache_" + v.grund); continue; }
        if (geplant.has(sid)) { drop("bekannt_seller_schon_geplant"); continue; }
        hint = sid;
      }
      if (it.pricing_count != null) S.feld_stat.pricing_count_gefuellt++; else S.feld_stat.pricing_count_leer++;
      const rev = it.reviews_count ?? null;
      // listings without values (fresh listings) are never dropped by these filters
      if (CFG.LISTING_MAX_BEWERTUNGEN > 0 && rev != null && rev > CFG.LISTING_MAX_BEWERTUNGEN) { drop("listing_bewertungen"); continue; }
      if (CFG.MAX_ANBIETER > 0 && it.pricing_count != null && it.pricing_count > CFG.MAX_ANBIETER) { drop("zu_viele_anbieter"); continue; }
      if (hint) geplant.add(hint);
      S.kandidaten.push({ asin, titel: it.title ?? "", preis: Number(it.price) || null, reviews: rev, anbieter: it.pricing_count ?? null,
        kat: l.kat, quelle: l.typ, liste: l.id, url: `https://www.amazon.de/dp/${asin}`, ...(hint ? { sid_hint: hint } : {}) });
      S.funnel.kandidaten++; x.kandidaten++; neuK++;
    }
    saveT();
  };
  // Phase A: first page of every list not fetched yet -> dead lists cost exactly one request
  const ersteSeiten = listen.filter((l) => listSt(l).seiten === 0).map((l) => ({ l, p: offeneSeiten(l)[0] })).filter((x) => x.p != null);
  await pool(ersteSeiten, CFG.CONC, holen, "Discovery Seite 1");
  if (ersteSeiten.length && listen.every((l) => listSt(l).seiten === 0 && listSt(l).leer_lauf !== S.laeufe && !listSt(l).tot))
    throw new StopError("Discovery: keine einzige Listenseite abrufbar — Internet, Oxylabs-Zugang bzw. OXYLABS_URL prüfen, dann denselben Befehl erneut starten.");
  // Phase B: further pages, interleaved by page number, only as many as this wave still needs
  limit = bedarf().pdp; neuK = 0;
  const rest = listen.filter((l) => listSt(l).seiten > 0 && !listSt(l).tot).map((l) => ({ l, ps: offeneSeiten(l) }));
  const mix = []; const max = Math.max(0, ...rest.map((r) => r.ps.length));
  for (let i = 0; i < max; i++) for (const r of rest) if (r.ps[i] != null) mix.push({ l: r.l, p: r.ps[i] });
  if (limit > 0) await pool(mix, CFG.CONC, holen, "Discovery");
  const tote = Object.values(S.listen).filter((x) => x.tot), leer = Object.values(S.listen).filter((x) => !x.tot && x.leer_lauf === S.laeufe);
  if (tote.length) console.log(`  Tote Listen (zweimal 0 Treffer auf Seite 1, werden nicht mehr abgerufen): ${tote.map((x) => x.label).join(", ")}`);
  if (leer.length) console.log(`  Leer auf Seite 1 (wird beim nächsten Start einmal nachgeprüft): ${leer.map((x) => x.label).join(", ")}`);
  const nichtsDa = tote.length + leer.length;
  if (nichtsDa >= 5 && nichtsDa > Object.keys(S.listen).length * 0.8) console.log("  WARNUNG: fast alle Listen sind leer — Antwortformat oder Kategorie-Nodes prüfen (siehe report).");
  console.log(`  ${de(S.kandidaten.filter((k) => !k.done).length)} offene Kandidaten · Feld pricing_count gefüllt: ${de(S.feld_stat.pricing_count_gefuellt)}/${de(S.feld_stat.pricing_count_gefuellt + S.feld_stat.pricing_count_leer)}`);
}

// ---------- STAGE 2: PRODUCT PAGES (buy-box seller) ----------
async function stufe2() {
  AKTIV = 2;
  const b = bedarf(), neue = new Set();
  // only as many product pages as this wave needs (generous upper bound for the progress display, exact stop below)
  const offen = S.kandidaten.filter((k) => !k.done).slice(0, b.seller ? Math.ceil((b.seller / Math.max(0.05, b.p2)) * 2) + CFG.CONC : 0);
  console.log(`Stufe 2: bis zu ${de(offen.length)} Produktseiten (Bedarf dieser Welle: ~${de(b.seller)} neue Verkäufer) …`);
  await pool(offen, CFG.CONC, async (k) => {
    if (neue.size >= b.seller) return;                                 // demand covered: candidate stays open for a later wave
    const c = con(await ox({ source: "amazon_product", domain: "de", query: k.asin, parse: true }));
    if (!c) { k.fehl = (k.fehl ?? 0) + 1; if (k.fehl >= 3) { k.done = true; S.funnel.pdp_done++; drop("produktseite_fehler"); } saveT(); return; }
    k.done = true; S.funnel.pdp_done++;
    const fm = c.featured_merchant ?? {}, sid = fm.seller_id ?? null, amazon = sid && istAmazon(sid, fm.name);
    SEEN[k.asin] = [sid && !amazon ? sid : "", heute()];
    if (!sid) { drop("kein_drittanbieter"); return saveT(); }
    if (amazon) { drop("amazon_verkauft"); return saveT(); }
    S.funnel.pdp_ok++;
    const r = rangVon(c);
    Object.assign(k, { seller_id: sid, seller_name: clean(fm.name), preis: Number(c.price) || k.preis || null, parent: c.parent_asin ?? k.asin,
      bilder: Array.isArray(c.images) ? c.images.length : 0, bullets: String(c.bullet_points ?? "").split("\n").filter((x) => x.trim()).length,
      beschr: String(c.description ?? "").length, marke: clean(c.manufacturer), rang: r?.r ?? null, rang_kat: r?.k ?? null, nodes: nodesAus(c) });
    if (DELIV.has(sid) || MASTER_IDS.has(sid)) { k.raus = "bereits_geliefert"; drop("bereits_geliefert"); return saveT(); }
    const v = bewerteFakten(FACTS[sid]); if (v?.ok === false) { k.raus = "cache_" + v.grund; drop(k.raus); return saveT(); }
    if (!S.seller[sid]) neue.add(sid);
    saveT();
  }, "Produktseiten");
  // one seller = one lead; main product = listing with most reviews (most representative), then best rank
  const by = {};
  for (const k of S.kandidaten) if (k.done && k.seller_id && !k.raus) (by[k.seller_id] ??= []).push(k);
  for (const [id, ks] of Object.entries(by)) {
    ks.sort((a, b) => (b.reviews ?? -1) - (a.reviews ?? -1) || (a.rang ?? 1e12) - (b.rang ?? 1e12) || (b.bilder ?? 0) - (a.bilder ?? 0));
    const { nodes, ...hp } = ks[0];
    if (!S.seller[id]) S.seller[id] = { hp, status: "neu", treffer: ks.length, asins: ks.slice(0, 5).map((x) => x.asin) };
    else S.seller[id].treffer = Math.max(S.seller[id].treffer ?? 1, ks.length);
  }
  S.funnel.seller = Object.keys(S.seller).length;
  console.log(`  ${de(S.funnel.seller)} eindeutige Verkäufer`);
  saveMem();
}

// ---------- STAGE 3: SELLER PROFILE ----------
async function stufe3() {
  AKTIV = 3;
  const b = bedarf();
  const offen = Object.entries(S.seller).filter(([, s]) => s.status === "neu").slice(0, b.profil ? Math.ceil((b.profil / Math.max(0.05, b.p3)) * 2) + CFG.CONC : 0);
  let ausCache = 0, okJetzt = 0;
  console.log(`Stufe 3: bis zu ${de(offen.length)} Verkäuferprofile (Bedarf dieser Welle: ~${de(b.profil)}) …`);
  await pool(offen, CFG.CONC, async ([id, s]) => {
    if (okJetzt >= b.profil) return;                                   // demand covered: seller stays "neu" for a later wave
    try { await profilPruefen(id, s); } finally { if (s.status === "raus") S.funnel.profil_raus++; else if (s.status === "profil_ok") okJetzt++; }
  }, "Verkäuferprofile");
  console.log(`  ${de(S.funnel.profil_ok)} Profile ok${ausCache ? ` (${de(ausCache)} aus dem Gedächtnis, 0 Abfragen)` : ""}`);
  saveMem();
  async function profilPruefen(id, s) {
    let f = FACTS[id];
    if (f && frischMs(f.t) && f.land) ausCache++;
    else {
      let c = null;
      for (let v = 0; v < 2 && !c?.business_address; v++) c = con(await ox({ source: "amazon_sellers", domain: "de", query: id, parse: true })) ?? c;
      if (!c) { s.versuche = (s.versuche ?? 0) + 1; if (s.versuche >= 3) raus(s, "profil_fehler"); return saveT(); }
      if (!c.business_address) { raus(s, "keine_adresse"); return saveT(); }
      f = FACTS[id] = { ...(FACTS[id] ?? {}), firma: clean(c.business_name), adresse: clean(c.business_address), land: landAus(c.business_address), t: Date.now() };
    }
    Object.assign(s, { firma: f.firma, adresse: f.adresse, land: f.land });
    S.land_stat[f.land] = (S.land_stat[f.land] ?? 0) + 1;
    const g = pruefeProfil(f); if (g) { raus(s, g); return saveT(); }
    s.status = "profil_ok"; S.funnel.profil_ok++; saveT();
  }
}

// ---------- STAGE 4: PORTFOLIO (storefront + sample of 12) ----------
const zielErreicht = () => CFG.ZIEL > 0 && S.funnel.portfolio_ok >= CFG.ZIEL;
const stufe4Offen = () => (zielErreicht() ? 0 : Object.values(S.seller).filter((s) => s.status === "profil_ok").length);
const SORT_FELDER = ["kacheln", "gekappt", "familien", "familien_probe", "portfolio_rev", "marke", "dominanz", "marken_n", "umsatz", "umsatz_basis", "umsatz_gem", "rp"];

async function sortimentMessen(id, s) {
  const seite = async (p) => { for (let v = 0; v < 2; v++) { const c = con(await ox({ source: "amazon_search", domain: "de", query: " ", parse: true,
    start_page: p, pages: 1, context: [{ key: "merchant_id", value: id }] })); if (c) return c; } return null; };
  const fehler = () => { s.versuche = (s.versuche ?? 0) + 1; if (s.versuche >= 3) raus(s, "sortiment_fehler"); return null; };
  const c1 = await seite(1); if (!c1) return fehler();
  const o1 = organic(c1), g = typeof c1.total_results_count === "number" ? c1.total_results_count : null;
  if (!o1.length) { raus(s, "storefront_leer"); return null; }
  const basis = { ...(FACTS[id] ?? {}), t_sortiment: Date.now() };
  // unique review counts (variations share reviews|rating) = one-sided safe lower bound of portfolio reviews
  const uniq = new Map(); const addRev = (arr) => { for (const i of arr) if (i.reviews_count) uniq.set(`${i.reviews_count}|${i.rating ?? ""}`, i.reviews_count); };
  const revMin = () => [...uniq.values()].reduce((a, b) => a + b, 0);
  const teil = (kacheln) => (FACTS[id] = { ...basis, partial: true, kacheln, s1rev_min: revMin() });
  addRev(o1);
  // early aborts only when the matching filter is switched on (facts stay "partial" and are re-measured if the filter changes)
  if (CFG.MAX_PRODUKTE > 0 && g != null && g > CFG.MAX_PRODUKTE) return teil(g);
  if (CFG.PORTFOLIO_MAX_BEWERTUNGEN > 0 && revMin() > CFG.PORTFOLIO_MAX_BEWERTUNGEN) return teil(g);
  const items = [...o1]; let letzte = o1.length, natuerlichesEnde = false;
  const seitenGesamt = g != null ? Math.ceil(g / Math.max(1, o1.length)) : CFG.MAX_SEITEN;
  if (seitenGesamt <= 1 || (g == null && letzte < 6)) natuerlichesEnde = true;
  for (let p = 2; !natuerlichesEnde && p <= Math.min(seitenGesamt, CFG.MAX_SEITEN) && items.length < CFG.MAX_KACHELN; p++) {
    const c = await seite(p); if (!c) return fehler();
    const o = organic(c); items.push(...o); addRev(o); letzte = o.length;
    if (!o.length || (g == null && letzte < 6) || p >= seitenGesamt) natuerlichesEnde = true;
    if (CFG.MAX_PRODUKTE > 0 && items.length > CFG.MAX_PRODUKTE) return teil(Math.max(g ?? 0, items.length));
    if (CFG.PORTFOLIO_MAX_BEWERTUNGEN > 0 && revMin() > CFG.PORTFOLIO_MAX_BEWERTUNGEN) return teil(g);
  }
  if (items.length > CFG.MAX_KACHELN) items.length = CFG.MAX_KACHELN;
  const kacheln = Math.max(g ?? 0, items.length);
  const gekappt = kacheln > items.length || (!natuerlichesEnde && g == null);

  // sample: families (parent ASIN), brand, measured buyers ("X+ gekauft"), rank/price pairs for the rank model
  const probe = items.slice(0, CFG.PROBE), fam = new Set(), marken = [], orig = {}, rp = [];
  let ok = 0, umsatzGem = 0, famGem = 0, preisUngem = 0;
  for (const it of probe) {
    const c = con(await ox({ source: "amazon_product", domain: "de", query: it.asin, parse: true }));
    if (!c) continue;
    ok++;
    const pa = c.parent_asin ?? it.asin; if (fam.has(pa)) continue; fam.add(pa);
    const mRoh = c.manufacturer ?? c.brand ?? "", m = markeClean(mRoh);
    if (m && !PLATZHALTER.test(m)) { marken.push(m); orig[m] ??= clean(mRoh); }
    const u = kaeufer(c.sales_volume ?? it.sales_volume), pr = Number(c.price ?? it.price) || 0, r = rangVon(c);
    rp.push({ r: r?.r ?? null, k: r?.k ?? s.hp?.kat ?? null, p: pr || null, u: u ?? null });
    if (u && pr) { umsatzGem += u * pr; famGem++; } else if (pr) preisUngem += pr;
  }
  if (ok < Math.ceil(probe.length / 2)) return fehler();
  const kollaps = ok / Math.max(1, fam.size);                       // tiles per family, from successful PDPs only
  const familien = fam.size + Math.round(Math.max(0, kacheln - ok) / kollaps);
  const portfolio_rev = Math.max(revMin(), Math.round(items.reduce((a, i) => a + (i.reviews_count ?? 0), 0) / kollaps));
  // brand share = sampled families carrying the top brand / all sampled families (placeholders like "Generic" count as no brand)
  let marke = "", dominanz = null;
  if (marken.length) { const z = {}; for (const m of marken) z[m] = (z[m] ?? 0) + 1; const [m, n] = Object.entries(z).sort((a, b) => b[1] - a[1])[0]; marke = orig[m] ?? m; dominanz = Math.round((n / Math.max(1, fam.size)) * 100); }
  // revenue: measured families x price + SCHAETZ_KAEUFER for families under Amazon's display threshold, scaled to all families.
  // umsatz_gem = measured part only, scaled like the original M4 rule (>= 2 measured families) -> the only basis for UMSATZ_MAX.
  const skal = familien / Math.max(1, fam.size);
  const roh = umsatzGem + CFG.SCHAETZ_KAEUFER * preisUngem;
  const umsatz = roh > 0 ? Math.round(roh * skal) : null;
  const umsatz_basis = !umsatz ? "nicht messbar" : famGem && (!preisUngem || !CFG.SCHAETZ_KAEUFER) ? "gemessen" : famGem ? "gemessen + geschätzt" : "geschätzt";
  return (FACTS[id] = { ...basis, partial: false, s1rev_min: revMin(), kacheln, gekappt, familien, familien_probe: fam.size, portfolio_rev, marke, dominanz,
    marken_n: marken.length, umsatz, umsatz_basis, umsatz_gem: famGem >= 2 ? Math.round(umsatzGem * skal) : null, rp });
}

async function stufe4() {
  AKTIV = 4;
  const offen = Object.entries(S.seller).filter(([, s]) => s.status === "profil_ok");
  let ausCache = 0;
  console.log(`Stufe 4: ${de(offen.length)} Sortimente${CFG.SORTIMENT ? "" : " (SORTIMENT=0: ohne Messung)"}${CFG.ZIEL ? `, Stopp bei ${de(CFG.ZIEL)} Treffern` : ""} …`);
  let laufend = 0;
  await pool(offen, CFG.CONC_PF, async ([id, s]) => {
    // never measure more sellers in parallel than hits are still missing (no paid overshoot past ZIEL)
    while (CFG.ZIEL > 0 && laufend > 0 && S.funnel.portfolio_ok + laufend >= CFG.ZIEL) await sleep(200);
    if (zielErreicht()) return;
    laufend++;
    try { await sortimentPruefen(id, s); } finally { laufend--; if (s.status === "raus") S.funnel.sortiment_raus++; }
  }, "Sortimente");
  console.log(`  ${de(S.funnel.portfolio_ok)} Treffer${ausCache ? ` (${de(ausCache)} Sortimente aus dem Gedächtnis, 0 Abfragen)` : ""}`);
  saveMem();
  async function sortimentPruefen(id, s) {
    let f = FACTS[id], neu = false;
    const v = bewerteFakten(f);
    if (v?.ok === false) { raus(s, v.grund); return saveT(); }
    if (v?.ok === true) ausCache++;
    else if (CFG.SORTIMENT) { f = await sortimentMessen(id, s); if (!f) return saveT(); neu = true; }
    if (f?.t_sortiment && (neu || frischMs(f.t_sortiment))) {
      for (const k of SORT_FELDER) s[k] = f[k] ?? null;
      const g = pruefeSortiment(f); if (g) { raus(s, g); return saveT(); }
    }
    if (zielErreicht()) return saveT();                              // measured but target already met: stays open for a later run
    s.status = "portfolio_ok"; S.funnel.portfolio_ok++; saveT();
  }
}

// ---------- STAGE 5: FINAL CHECK (before paid contacts) ----------
async function stufe5() {
  AKTIV = 5;
  const offen = Object.entries(S.seller).filter(([, s]) => s.status === "portfolio_ok");
  if (!CFG.ENDKONTROLLE) { for (const [, s] of offen) { s.status = "qa_ok"; S.funnel.qa_ok++; } return; }
  if (!offen.length) return;
  console.log(`Stufe 5: Endkontrolle für ${de(offen.length)} Treffer …`);
  await pool(offen, CFG.CONC, async ([id, s]) => {
    const asins = [...new Set([s.hp.asin, ...(s.asins ?? [])])].slice(0, 2);
    let grund = null;
    for (const asin of asins) {
      const c = con(await ox({ source: "amazon_product", domain: "de", query: asin, parse: true }));
      if (!c) { grund = "fehler"; continue; }
      const fid = c.featured_merchant?.seller_id ?? null;
      if (fid !== id) { grund = fid ? "endkontrolle_buybox_anderer_verkaeufer" : "endkontrolle_kein_angebot"; continue; }
      const pr = Number(c.price) || null;
      if (CFG.PREIS_MIN > 0 && pr && pr < CFG.PREIS_MIN) { grund = "endkontrolle_preis_unter_min"; continue; }
      if (asin === s.hp.asin) { if (pr) s.hp.preis = pr; if (!s.hp.rang) s.hp.rang = rangVon(c)?.r ?? null; }
      grund = null; break;
    }
    if (grund === "fehler") { s.versuche_qa = (s.versuche_qa ?? 0) + 1; if (s.versuche_qa >= 3) raus(s, "endkontrolle_fehler"); return saveT(); }
    if (grund) { raus(s, grund); return saveT(); }
    s.status = "qa_ok"; S.funnel.qa_ok++; saveT();
  }, "Endkontrolle");
}

// ---------- STAGE 6: CONTACTS (Bright Data, optional) ----------
const BD_MAP = { "business name": "firma_bd", "business type": "rechtsform", "trade register number": "hrb", "vat number": "ustid",
  "phone number": "telefon", "email": "email", "business address": "adresse_bd" };
function finalisieren(s) {
  if (!s.firma && s.firma_bd) s.firma = s.firma_bd;
  if (CFG.FIRMEN_AUSSCHLUSS.length && [s.firma, s.firma_bd].some((n) => n && CFG.FIRMEN_AUSSCHLUSS.some((w) => norm(n).includes(w)))) { raus(s, "firmen_ausschluss_nach_kontakt"); return; }
  s.status = "final"; S.funnel.final++;
}
async function bdTrigger(chunk) {
  try {
    const a = await abrufen(`${BD_URL}/datasets/v3/trigger?dataset_id=gd_lhotzucw1etoe5iw1k&include_errors=true`, { method: "POST",
      headers: { Authorization: `Bearer ${BD}`, "Content-Type": "application/json" }, body: JSON.stringify(chunk.map((id) => ({ url: `https://www.amazon.de/sp?seller=${id}` }))) },
      { label: "Bright Data", maxVersuche: CFG.MAX_RETRIES, timeoutMs: 60000, schlafen: pause, log: (m) => console.log(`\n  ${m}`) });
    if (a.j?.snapshot_id) return a.j.snapshot_id;
    // 2xx without snapshot id: not triggered again (a second trigger could be charged twice)
    console.log(`\n  Bright Data: HTTP ${a.status} ohne Snapshot-ID ${a.text.slice(0, 160)}`); API_FEHL.bd++;
  } catch (e) {
    if (!(e instanceof ApiFehler)) throw e;
    console.log(`\n  ${e.message}`);
    if ([401, 402, 403].includes(e.status)) { BD_AUS = `bd_http_${e.status}`; return false; }
    API_FEHL.bd++;
  }
  for (const id of chunk) S.seller[id].bd_versuche = (S.seller[id].bd_versuche ?? 0) + 1;
  return null;
}
async function bdAbholen(snap, job) {
  const H = { Authorization: `Bearer ${BD}` }, ende = Date.now() + CFG.BD_TIMEOUT_MIN * 60000;
  let status = null, fehler = 0;
  // hard deadline BD_TIMEOUT_MIN; temporary errors are polled again with backoff (never triggered again: already paid)
  while (Date.now() < ende && !ABORT) {
    const a = await holeJson(`${BD_URL}/datasets/v3/progress/${snap}`, { headers: H, timeoutMs: 60000 });
    if ([401, 402, 403].includes(a.status)) { BD_AUS = `bd_http_${a.status}`; console.log(`\n  Bright Data: HTTP ${a.status} ${meldungVon(a.j, a.text).slice(0, 160)}`); break; }
    if (a.status === 404) { status = "failed"; break; }                                 // snapshot unknown/expired
    if (a.status >= 200 && a.status < 300) { status = a.j?.status ?? null; fehler = 0; }
    else {
      status = null;
      if (!voruebergehend(a.status)) { console.log(`\n  Bright Data: Fortschritt von ${snap} nicht abrufbar (HTTP ${a.status}: ${meldungVon(a.j, a.text).slice(0, 160)}) — wird beim nächsten Start erneut abgeholt.`); break; }
      if (++fehler > CFG.MAX_RETRIES) { console.log(`\n  Bright Data: Fortschritt von ${snap} ${fehler}× in Folge nicht abrufbar (${a.fehler ?? `HTTP ${a.status}`}) — wird beim nächsten Start erneut abgeholt.`); break; }
    }
    process.stdout.write(`\r  Kontakte (${job.ids.length} Verkäufer): ${status ?? "?"} …   `);
    if (status === "ready" || status === "failed") break;
    await pause(Math.min(fehler ? wartezeit(fehler, a.status, a.ra) : 8000, Math.max(0, ende - Date.now())));
  }
  // a job that never becomes ready must not block its leads forever: give up after 3 starts or 48 h
  if (status !== "ready" && status !== "failed" && !ABORT && !BD_AUS) {
    job.versuche = (job.versuche ?? 0) + 1;
    if (job.versuche >= 3 || Date.now() - (job.t ?? Date.now()) > 48 * 3600e3) status = "failed";
  }
  if (status === "failed") { for (const id of job.ids) { const s = S.seller[id]; if (!s) continue; s.kontakt_fehler = "bd_failed"; delete s.bd_job; if (s.status === "qa_ok") finalisieren(s); } delete S.bd_jobs[snap]; save(); return; }
  if (status !== "ready") { save(); console.log(`\n  Kontakt-Block ${snap} ist noch nicht fertig — wird beim nächsten Start abgeholt (bereits bezahlt).`); return; }
  let data = null;
  try {
    // HTTP 202 = snapshot still being built: retried like a temporary error
    data = (await abrufen(`${BD_URL}/datasets/v3/snapshot/${snap}?format=json`, { headers: H }, { label: "Bright Data", maxVersuche: CFG.MAX_RETRIES,
      timeoutMs: 120000, schlafen: pause, gueltig: (x) => Array.isArray(x.j) })).j;
  } catch (e) {
    if (!(e instanceof ApiFehler)) throw e;
    if ([401, 402, 403].includes(e.status)) BD_AUS = `bd_http_${e.status}`;
    API_FEHL.bd++;
    // a ready block that can never be downloaded must not block its leads forever: given up after 3 starts
    if (!BD_AUS && !ABORT && (job.versuche = (job.versuche ?? 0) + 1) >= 3) {
      console.log(`\n  Kontakt-Block ${snap} auch im 3. Start nicht lesbar (${e.message}) — die Leads werden ohne Kontaktdaten geliefert.`);
      for (const id of job.ids) { const s = S.seller[id]; if (!s) continue; s.kontakt_fehler = "bd_download_fehler"; delete s.bd_job; if (s.status === "qa_ok") finalisieren(s); }
      delete S.bd_jobs[snap]; save(); return;
    }
    save(); console.log(`\n  Kontakt-Block ${snap} nicht lesbar (${e.message}) — wird beim nächsten Start erneut abgeholt.`); return;
  }
  S.usage.bd += data.length;
  const erledigt = new Set();
  for (const rec of data) {
    let sid = rec?.seller_id;
    if (!sid) { try { sid = new URL(rec?.url ?? rec?.input?.url).searchParams.get("seller"); } catch {} }
    const s = sid && job.ids.includes(sid) ? S.seller[sid] : null; if (!s) continue;
    erledigt.add(sid);
    if (rec.error || rec.error_code) { s.kontakt_fehler = String(rec.error_code ?? rec.error).slice(0, 80); continue; }
    for (const f of (Array.isArray(rec.detailed_info) ? rec.detailed_info : [])) { const k = BD_MAP[String(f?.title ?? "").toLowerCase().trim()]; if (k && f?.value) s[k] = clean(f.value); }
    s.gf = gfAus(`${rec.description ?? ""} ${JSON.stringify(rec.detailed_info ?? "")}`);
    s.kontakt = true;
  }
  for (const id of job.ids) { const s = S.seller[id]; if (!s) continue; delete s.bd_job;
    if (!erledigt.has(id)) s.kontakt_fehler ??= "bd_kein_datensatz";
    if (s.status === "qa_ok") finalisieren(s); }
  delete S.bd_jobs[snap]; save();
}
async function stufe6() {
  AKTIV = 6;
  const offen = () => Object.entries(S.seller).filter(([, s]) => s.status === "qa_ok");
  if (!BD) { for (const [, s] of offen()) finalisieren(s); return; }
  for (const [snap, job] of Object.entries(S.bd_jobs)) await bdAbholen(snap, job);       // paid jobs from an earlier start first
  const ids = offen().filter(([, s]) => !s.bd_job).map(([id]) => id);
  if (ids.length) console.log(`Stufe 6: Kontaktdaten für ${de(ids.length)} Leads (Bright Data) …`);
  for (let off = 0; off < ids.length && !ABORT && !BD_AUS; off += CFG.BD_BATCH) {
    const chunk = ids.slice(off, off + CFG.BD_BATCH);
    const snap = await bdTrigger(chunk);
    if (!snap) continue;
    S.bd_jobs[snap] = { ids: chunk, t: Date.now() }; for (const id of chunk) S.seller[id].bd_job = snap; save();
    await bdAbholen(snap, S.bd_jobs[snap]);
  }
  for (const [, s] of offen()) {
    if (s.bd_job && S.bd_jobs[s.bd_job]) continue;                                      // still pending: next start
    if (!BD_AUS && (s.bd_versuche ?? 0) >= 3) { s.kontakt_fehler ??= "bd_trigger_fehler"; finalisieren(s); }
  }
  const warten = offen().length;
  // a rejected token or an empty balance must not turn paid leads into leads without contact data: they stay open
  if (BD_AUS && warten) {
    BD_STOPP = `Bright Data lehnt den Zugang ab (${BD_AUS.replace("bd_http_", "HTTP ")}) — ${de(warten)} Leads warten auf Kontaktdaten. Token bzw. Guthaben prüfen, dann denselben Befehl erneut starten. Bewusst ohne Kontaktdaten weiter: BRIGHTDATA_TOKEN aus der .env nehmen und erneut starten`;
    STOPGRUND = STOPGRUND ? `${STOPGRUND} · ${BD_STOPP}` : BD_STOPP;
  } else if (warten) console.log(`  ${de(warten)} Leads warten noch auf Kontaktdaten — beim nächsten Start werden sie abgeholt und exportiert.`);
  console.log("");
}

// ---------- rank model (second opinion, never filters, costs nothing) ----------
function rangModell() {
  const paare = {};
  for (const f of Object.values(FACTS)) for (const e of (f.rp ?? [])) if (e.u && e.r) (paare[e.k ?? "?"] ??= []).push([Math.log(e.r), Math.log(e.u)]);
  const fit = (pts) => {
    const n = pts.length; if (n < 8) return null;
    const sx = pts.reduce((a, [x]) => a + x, 0), sy = pts.reduce((a, [, y]) => a + y, 0);
    const sxx = pts.reduce((a, [x]) => a + x * x, 0), sxy = pts.reduce((a, [x, y]) => a + x * y, 0);
    const Braw = (n * sxy - sx * sy) / ((n * sxx - sx * sx) || 1);
    const B = Math.min(-0.15, Math.max(-1.2, Braw)), lnA = (sy - B * sx) / n;   // intercept from the CLAMPED slope
    const my = sy / n, ssT = pts.reduce((a, [, y]) => a + (y - my) ** 2, 0), ssR = pts.reduce((a, [x, y]) => a + (y - (lnA + B * x)) ** 2, 0);
    const r2 = ssT > 0 ? 1 - ssR / ssT : 0, A = Math.exp(lnA);
    return Number.isFinite(A) && Number.isFinite(B) ? { A, B, Braw, n, r2 } : null;
  };
  const modelle = {}; for (const [k, p] of Object.entries(paare)) { const m = fit(p); if (m && m.r2 >= 0.2) modelle[k] = m; }
  const gf = fit(Object.values(paare).flat()), global = gf && gf.r2 >= 0.2 ? gf : null;
  const umsatz = (s) => {
    const rp = (s.rp ?? []).filter((e) => e.r && e.p); if (!rp.length) return null;
    let sum = 0;
    for (const e of rp) { const m = modelle[e.k] ?? global; if (!m) return null; sum += m.A * Math.pow(e.r, m.B) * e.p; }
    return Math.round((sum * (s.familien ?? rp.length)) / rp.length);
  };
  return { modelle, global, roh: gf, umsatz, paare: Object.values(paare).flat().length };
}

// ---------- EXPORT ----------
const SPALTEN = ["Firma", "Marke", "Seller-ID", "Storefront-URL", "Verkäuferprofil-URL", "Haupt-ASIN", "Produkt-URL", "Kategorie", "Quelle", "Land", "Adresse",
  "Produktpreis", "Produktbilder", "Bulletpoints", "Beschreibungslänge", "Produkte", "Produkte gekappt", "Produktfamilien", "Portfolio-Bewertungen",
  "Markenanteil %", "Umsatz/Monat ca. EUR", "Umsatzbasis", "Bestseller-Rang", "Umsatz Rang-Modell EUR", "E-Mail", "Telefon", "Handelsregister",
  "USt-IdNr", "Rechtsform", "Vertretungsberechtigt", "Datenstand"];
const QUELLE_TXT = { kategorie: "Neuheiten Kategorie", unterkategorie: "Neuheiten Unterkategorie", keyword: "Keyword-Suche" };
// one line per cell, quoted when needed, formula-like values neutralised (phone numbers like "+49 30 123" stay untouched)
const esc = (v) => {
  let s = v == null ? "" : String(v).replace(/\r\n?|\n/g, " ");
  if (/^[=@\t]/.test(s) || /^[+-](?![\d\s()\/.-]*$)/.test(s)) s = "'" + s;
  return /[";]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
};
const stempel = () => { const d = new Date(), z = (n) => String(n).padStart(2, "0"); return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}_${z(d.getHours())}-${z(d.getMinutes())}-${z(d.getSeconds())}`; };
function exportieren(modell) {
  const datum = new Date().toISOString().slice(0, 10), kopf = SPALTEN.join(";");
  const neu = [];
  for (const [id, s] of Object.entries(S.seller)) {
    if (s.status !== "final" || s.exportiert_am) continue;
    if (MASTER_IDS.has(id)) { s.exportiert_am = "schon_im_master"; DELIV.add(id); continue; }
    const k = s.hp;
    neu.push([id, [s.firma, s.marke || k.marke, id, `https://www.amazon.de/s?me=${id}&marketplaceID=A1PA6795UKMFR9`, `https://www.amazon.de/sp?seller=${id}`,
      k.asin, k.url, k.kat, QUELLE_TXT[k.quelle] ?? k.quelle, s.land, s.adresse_bd ?? s.adresse, k.preis, k.bilder, k.bullets, k.beschr,
      s.kacheln, s.gekappt ? "ja" : "", s.familien, s.portfolio_rev, s.dominanz, s.umsatz, s.umsatz_basis, k.rang, modell.umsatz(s),
      s.email, s.telefon, s.hrb, s.ustid, s.rechtsform, s.gf, datum].map(esc).join(";")]);
  }
  if (!neu.length) return null;
  let batchF = `leads_${KAMPAGNE}_${stempel()}.csv`;
  for (let i = 2; existsSync(batchF); i++) batchF = `leads_${KAMPAGNE}_${stempel()}_${i}.csv`;
  writeAtomic(batchF, "﻿" + [kopf, ...neu.map(([, z]) => z)].join("\r\n") + "\r\n");
  if (existsSync(F.master) && readFileSync(F.master, "utf8").split(/\r?\n/)[0].replace(/^﻿/, "") !== kopf) {
    const altF = F.master.replace(/\.csv$/, `_alteSpalten_${stempel()}.csv`);
    writeFileSync(altF, readFileSync(F.master)); writeAtomic(F.master, "﻿" + kopf + "\r\n");
    console.log(`Hinweis: Spalten geändert — bisheriger Master gesichert als ${altF}`);
  }
  if (!existsSync(F.master)) writeFileSync(F.master, "﻿" + kopf + "\r\n");
  appendFileSync(F.master, neu.map(([, z]) => z).join("\r\n") + "\r\n");                 // append, never overwrite
  for (const [id] of neu) { S.seller[id].exportiert_am = new Date().toISOString(); DELIV.add(id); MASTER_IDS.add(id); }
  S.funnel.exportiert += neu.length;
  return { datei: batchF, anzahl: neu.length };
}

// ---------- REPORT ----------
function bericht(exp, modell, abgebrochen) {
  const alle = Object.values(S.seller), finals = alle.filter((s) => s.status === "final");
  const jeKat = {};
  const kat = (k) => (jeKat[k] ??= { listen: 0, tote_listen: 0, seiten: 0, treffer: 0, kandidaten: 0, leads: 0 });
  for (const l of Object.values(S.listen)) { const k = kat(l.kat); k.listen++; if (l.tot) k.tote_listen++; k.seiten += l.seiten; k.treffer += l.treffer; k.kandidaten += l.kandidaten; }
  for (const s of finals) kat(s.hp?.kat ?? "?").leads++;
  const fq = (f) => finals.filter((s) => s[f]).length;
  const usd = { oxylabs: +(S.usage.ox / 1000 * CFG.OX_USD_JE_1000).toFixed(2), brightdata: +(S.usage.bd / 1000 * CFG.BD_USD_JE_1000).toFixed(2) };
  usd.gesamt = +(usd.oxylabs + usd.brightdata).toFixed(2);
  const r = {
    kampagne: KAMPAGNE, smoke: SMOKE, abgebrochen, stopgrund: STOPGRUND, stufe: S.stufe, laeufe: S.laeufe,
    config: { ...CFG, filter_aktiv: FILTER_AN, kategorien_aktiv: KATEGORIEN.length, unterkategorien: SUBS.length, keywords: KEYWORDS.length, qa_reserve: QA_RESERVE },
    funnel: S.funnel, ausschluss: S.ausschluss, je_kategorie: jeKat,
    tote_listen: Object.values(S.listen).filter((l) => l.tot).map((l) => ({ liste: l.label, url: l.url })),
    erschoepfte_listen: Object.values(S.listen).filter((l) => l.ende).map((l) => ({ liste: l.label, letzte_seite: l.ende })),
    laender: S.land_stat, feld_stat: S.feld_stat,
    kontakte: { email: fq("email"), telefon: fq("telefon"), handelsregister: fq("hrb"), ustid: fq("ustid"), vertretungsberechtigt: fq("gf"), von: finals.length, offene_bd_jobs: Object.keys(S.bd_jobs).length },
    rang_modell: { kalibrier_paare: modell.paare, kategorien_mit_eigenem_fit: Object.keys(modell.modelle).length,
      global: modell.roh ? { A: +modell.roh.A.toFixed(2), B: +modell.roh.B.toFixed(3), B_roh: +modell.roh.Braw.toFixed(3), n: modell.roh.n, r2: +Math.max(-1, modell.roh.r2).toFixed(2), verwendet: !!modell.global } : null },
    usage: S.usage, kosten_usd: usd, requests_je_lead: finals.length ? Math.round(S.usage.ox / finals.length) : null,
    programmfehler: S.fehler, gedaechtnis: { seen_asins: Object.keys(SEEN).length, seller_fakten: Object.keys(FACTS).length, geliefert: DELIV.size },
    dateien: { batch: exp?.datei ?? null, master: F.master, state: F.state }, neu_exportiert: exp?.anzahl ?? 0,
    dauer_min: Math.round((Date.now() - new Date(S.start).getTime()) / 60000), ende: new Date().toISOString(),
  };
  writeAtomic(F.report, JSON.stringify(r, null, 1));
  console.log(`\n===== ERGEBNIS (${KAMPAGNE}${SMOKE ? ", SMOKE" : ""}) =====`);
  if (STOPGRUND) console.log(`Gestoppt: ${STOPGRUND}`);
  console.log(`Funnel: ${de(S.funnel.kandidaten)} Kandidaten → ${de(S.funnel.seller)} Verkäufer → ${de(S.funnel.profil_ok)} Profil ok → ${de(S.funnel.portfolio_ok)} Sortiment ok → ${de(finals.length)} Leads`);
  if (finals.length) console.log(`Kontakte: E-Mail ${fq("email")}/${finals.length} · Telefon ${fq("telefon")}/${finals.length} · Vertretungsberechtigt ${fq("gf")}/${finals.length}`);
  if (r.tote_listen.length) console.log(`Tote Listen: ${r.tote_listen.length} (Details im Report)`);
  console.log(`Verbrauch: ${de(S.usage.ox)}/${de(CFG.BUDGET)} Oxylabs-Abfragen · ${de(S.usage.bd)} Bright-Data-Datensätze · ca. ${usd.gesamt.toFixed(2).replace(".", ",")} USD${finals.length ? ` · ${r.requests_je_lead} Abfragen je Lead` : ""}`);
  console.log(`Dateien: ${exp ? `${exp.datei} (${exp.anzahl} neue Leads), ` : "keine neuen Leads, "}${F.master}, ${F.report}`);
  // short error summary: API calls of this start that failed for good, and items given up after repeated errors
  const abrufFehler = ["produktseite_fehler", "profil_fehler", "sortiment_fehler", "endkontrolle_fehler"].reduce((n, g) => n + (S.ausschluss[g] ?? 0), 0);
  const ohneKontakt = finals.filter((s) => /^bd_/.test(s.kontakt_fehler ?? "")).length, prog = Object.values(S.fehler).reduce((n, v) => n + v, 0);
  const teile = [API_FEHL.ox && `${de(API_FEHL.ox)} Oxylabs-Abrufe`, API_FEHL.bd && `${de(API_FEHL.bd)} Bright-Data-Abrufe`].filter(Boolean);
  if (teile.length || abrufFehler || ohneKontakt || prog)
    console.log(`Fehler: ${[teile.length && `${teile.join(" und ")} in diesem Start ohne Ergebnis (nach je bis zu ${CFG.MAX_RETRIES} Versuchen bzw. dauerhafter Fehler)`,
      abrufFehler && `${de(abrufFehler)} Einträge nach 3 fehlgeschlagenen Abrufen aussortiert (Kampagne gesamt)`, ohneKontakt && `${de(ohneKontakt)} Leads ohne Kontaktdaten wegen Bright-Data-Fehler`,
      prog && `${de(prog)} Programmfehler`].filter(Boolean).join(" · ")}`);
}

// ---------- optional enrichment (Skael) ----------
function anreicherung(exp) {
  if (USER_ABBRUCH || !existsSync(F.master)) return;
  if (!ANREICHERUNG_AN) { console.log("Anreicherung abgeschaltet (ANREICHERUNG=0)."); return; }
  const skript = join(SKRIPT_DIR, "anreicherung.mjs"), rel = relative(process.cwd(), skript);
  // short relative path when the script is nearby, otherwise the absolute one (quoted: it may contain spaces)
  const befehl = `KAMPAGNE=${KAMPAGNE} node ${rel && !rel.startsWith(join("..", "..", "..")) ? rel : JSON.stringify(skript)}`;
  if (!(env.SKAEL_API_KEY ?? env.SKAEL_KEY)) {
    if (exp) console.log(`\nOhne SKAEL_API_KEY: keine E-Mail-Prüfung (alle Adressen bleiben „Not Run“ und dürfen nicht per E-Mail angeschrieben werden), keine Website und Geschäftsführung.\n  Nachholen: Schlüssel in die .env eintragen, dann ${befehl}`);
    return;
  }
  if (!existsSync(skript)) { console.log(`Anreicherung übersprungen: ${skript} fehlt.`); return; }
  // the whole master is enriched on every start: progress is kept per seller id, so only open leads cost credits
  console.log(`\n===== ANREICHERUNG (Skael)${exp ? ` für ${exp.anzahl} neue Leads` : ""} → ${F.master.replace(/\.csv$/, "")}_angereichert.csv =====`);
  const r = spawnSync(process.execPath, [skript], { stdio: "inherit", cwd: process.cwd(), env: { ...env, CSV: F.master, KAMPAGNE } });
  const txt = { 1: "Eingabe- oder Konfigurationsfehler, oder Skael hat die Anfragen abgelehnt — Meldung oben lesen, ein Neustart allein hilft nicht", 2: "Skael-Zugang abgelehnt — SKAEL_API_KEY prüfen",
    3: "Skael-Credits aufgebraucht", 4: "Credit-Deckel SKAEL_MAX_CREDITS erreicht — Neustart mit höherem Deckel setzt fort",
    5: "Skael antwortet gerade nicht oder einzelne Leads sind noch offen — später erneut starten, es geht nichts verloren" };
  if (r.status !== 0) console.log(`Anreicherung nicht vollständig (Code ${r.status ?? "?"}): ${txt[r.status] ?? "Neustart setzt am Checkpoint fort"}.\n  Befehl: ${befehl}`);
}

// ---------- MAIN ----------
async function budgetRettung() {
  ABORT = false;
  const vorher = S.stufe;
  console.log(`\nBUDGET ERREICHT — gefundene Treffer werden noch geprüft, angereichert und exportiert …`);
  const treffer = Object.values(S.seller).some((s) => ["portfolio_ok", "qa_ok"].includes(s.status));
  if (!treffer) { console.log(`  Noch keine neuen Treffer — der Stand bleibt auf Stufe ${vorher}. Zum Fortsetzen mit höherem BUDGET neu starten (z. B. BUDGET=${CFG.BUDGET * 2}).`); return; }
  for (const st of [stufe5, stufe6]) {
    try { await st(); }
    catch (e) { if (!(e instanceof BudgetError || e instanceof StopError)) throw e; ABORT = USER_ABBRUCH;
      console.log(`  ${e instanceof BudgetError ? "Budget reicht nicht für alle Endkontrollen — der Rest wird beim nächsten Start geprüft." : e.message}`); }
  }
  S.stufe = vorher;                                                                       // never move the stage counter on a budget stop
}
const STUFEN = [null, stufe1, stufe2, stufe3, stufe4, stufe5, stufe6];
const hatArbeit = (n) => ({
  1: () => stufe1Offen() > 0, 2: () => S.kandidaten.some((k) => !k.done), 3: () => Object.values(S.seller).some((s) => s.status === "neu"),
  4: () => stufe4Offen() > 0, 5: () => Object.values(S.seller).some((s) => s.status === "portfolio_ok"),
  6: () => Object.keys(S.bd_jobs).length > 0 || Object.values(S.seller).some((s) => s.status === "qa_ok"),
})[n]();

(async () => {
  if (process.argv.includes("--pruefen")) {                  // setup check: node version, keys, one single Oxylabs request
    const major = Number(process.versions.node.split(".")[0]);
    console.log(`Node ${process.versions.node}: ${major >= 18 ? "ok" : "ZU ALT — bitte Node 18 oder neuer installieren (nodejs.org, LTS)"}`);
    let ok = false;
    try {
      const r = await fetch(OX_URL, { method: "POST", signal: AbortSignal.timeout(120000), headers: { "Content-Type": "application/json", Authorization: AUTH },
        body: JSON.stringify({ source: "amazon", url: nodeUrl(KATEGORIEN[0] ?? { node: 3167641 })(1), parse: true }) });
      const t = await r.text(); ok = r.ok;
      console.log(r.ok ? "Oxylabs: Zugang ok (1 Testabfrage)" : `Oxylabs: abgelehnt (HTTP ${r.status}) — Benutzername/Passwort bzw. Guthaben prüfen. ${t.slice(0, 120)}`);
    } catch (e) { console.log(`Oxylabs: nicht erreichbar (${e.message}) — Internetverbindung prüfen.`); }
    console.log(`Bright Data: ${BD ? "Token gesetzt (Kontaktdaten an)" : "nicht gesetzt — Leads ohne E-Mail und Telefon"}`);
    console.log(`Skael: ${env.SKAEL_API_KEY ?? env.SKAEL_KEY ? "Schlüssel gesetzt (E-Mail-Prüfung, Website, Geschäftsführung, Anrede an)" : "nicht gesetzt — ohne E-Mail-Prüfung (Pflicht für E-Mail-Versand), Website und Geschäftsführung"}`);
    process.exit(ok && major >= 18 ? 0 : 1);
  }
  console.log(`Amazon-Seller-Scraper [${SMOKE ? "SMOKE" : "PRODUKTION"}] — Kampagne ${KAMPAGNE} · Ziel ${CFG.ZIEL ? de(CFG.ZIEL) : "offen"} · Budget ${de(CFG.BUDGET)} · Stufe ${S.stufe}`);
  if (SMOKE_IGNORIERT.length) console.log(`  Smoke-Test: fest ${CFG.ZIEL} Leads und höchstens ${CFG.BUDGET} Abfragen, ohne Filter. Ignoriert: ${SMOKE_IGNORIERT.join(", ")}`);
  console.log(`  Filter: ${FILTER_AN.length ? FILTER_AN.join(" · ") : "alle aus"} · Sortiment ${CFG.SORTIMENT ? "an" : "aus"} · Endkontrolle ${CFG.ENDKONTROLLE ? "an" : "aus"}`);
  if (S.usage.ox >= CFG.BUDGET) console.log(`  Hinweis: Budget dieses Laufs ist bereits verbraucht (${de(S.usage.ox)}). Zum Weitermachen BUDGET erhöhen, z. B. BUDGET=${S.usage.ox + Math.max(1000, CFG.BUDGET)}.`);
  else if (CFG.ZIEL > 0) {
    const fehlt = Math.max(0, CFG.ZIEL - S.funnel.portfolio_ok), jeLead = CFG.SORTIMENT ? 30 : 5, frei = CFG.BUDGET - S.usage.ox;
    if (fehlt && frei < fehlt * jeLead) console.log(`  Hinweis: Ohne Filter braucht ein Lead erfahrungsgemäß ~${jeLead} Abfragen (mit Filtern mehr). Das freie Budget reicht für etwa ${de(Math.floor(frei / jeLead))} der ${de(fehlt)} fehlenden Leads — gefundene Leads werden in jedem Fall geliefert.`);
  }
  let fatal = null, budgetStopp = false;
  const lauf = async (n) => { if (S.stufe > n && !hatArbeit(n)) return; await STUFEN[n](); if (S.stufe <= n) S.stufe = n + 1; save(); };
  const stand = () => { const z = {}; for (const s of Object.values(S.seller)) z[s.status] = (z[s.status] ?? 0) + 1;
    return JSON.stringify([stufe1Offen(), S.kandidaten.reduce((a, k) => a + (k.done ? 1 : 0), 0), z]); };
  try {
    // stages 1-4 in waves until ZIEL is reached or nothing moves any more (lists exhausted), then final check + contacts
    for (let welle = 1; welle <= 1000; welle++) {
      const vorher = stand();
      for (let n = 1; n <= 4; n++) await lauf(n);
      if (zielErreicht() || stand() === vorher || ![1, 2, 3, 4].some(hatArbeit)) break;
      console.log(`\n— Welle ${welle + 1}: ${de(S.funnel.portfolio_ok)}${CFG.ZIEL ? ` von ${de(CFG.ZIEL)}` : ""} Treffern, es wird nachgeladen (${de(S.usage.ox)}/${de(CFG.BUDGET)} Abfragen) …`);
    }
    if (CFG.ZIEL > 0 && !zielErreicht() && !USER_ABBRUCH)
      console.log(`\nHinweis: Alle Listen ausgeschöpft — ${de(S.funnel.portfolio_ok)} von ${de(CFG.ZIEL)} Treffern. Mehr Auswahl: einmal ernter_unterkategorien.mjs ausführen und mit SUB_SEITEN=5 fortsetzen, oder KEYWORDS ergänzen.`);
    for (let n = 5; n <= 6; n++) await lauf(n);
  } catch (e) {
    if (e instanceof BudgetError) { STOPGRUND = e.message; budgetStopp = true; try { await budgetRettung(); } catch (e2) { fatal = e2; } }
    else if (e instanceof StopError) STOPGRUND ??= e.message;
    else { fatal = e; STOPGRUND ??= `Programmfehler: ${e.message}`; }
  }
  save(); saveMem();
  const modell = rangModell();
  const exp = exportieren(modell);
  save(); saveMem();
  bericht(exp, modell, !!STOPGRUND);
  if (fatal) { console.error(fatal.stack ?? fatal); process.exitCode = 1; }
  else if (USER_ABBRUCH) process.exitCode = 130;
  else if ((STOPGRUND && !budgetStopp) || BD_STOPP) process.exitCode = 2;
  if (!fatal) anreicherung(exp);
})();
