#!/usr/bin/env node
/**
 * LEAD ENRICHMENT (Skael API): e-mail deliverability (required before e-mail outreach), official website, imprint,
 * managing director, salutation.
 *
 * Runs after the scraper (automatically when SKAEL_API_KEY is set, see README) or manually:
 *   SKAEL_API_KEY=... node anreicherung.mjs                      (master CSV of KAMPAGNE)
 *   SKAEL_API_KEY=... CSV=leads_standard_<time>.csv node anreicherung.mjs
 *
 * Step 0 for every lead with an e-mail address, in every country: verify_email (3 credits) -> column "E-Mail Status"
 *   (Safe to Send / Risky / Unknown / Invalid, same labels as the Google Maps path). EMAIL_PRUEFUNG=0 switches it off.
 *
 * Phases per lead (only countries in ANREICHERUNG_LAENDER, default DE/AT/CH):
 *   1 website from the e-mail domain (0 credits; free-mail and directory domains excluded)
 *   2 otherwise google_search "{company} {city} Impressum" (1 credit), top 3 candidate domains
 *   3 imprint_extractor per candidate (5-10 credits, free when nothing is found) until the match cascade confirms the company
 *   4 ai_research_agent (~3-10 credits) only to FIND a website; its own answer is never used as imprint
 *   -> cascade: hoster check -> register (+court) -> VAT id -> company name -> phone -> e-mail -> domain (e-mail source only)
 *   -> salutation only with an unambiguous first name (or Herr/Frau in the source); original columns are never changed.
 *
 * API contract: https://api.skael.de/docs/api-guide (envelope data.output, async + long polling, Idempotency-Key).
 * Checkpoint per lead and per paid call (anreicherung_<KAMPAGNE>_state.json): an abort costs nothing, just start again.
 * Temporary API errors (network, timeouts, 408/425/429/5xx, unreadable answers, jobs failed for a temporary reason) are
 * retried with exponential backoff (MAX_RETRIES attempts, wiederholen.mjs); what still fails stays open for the next
 * start (max. 3 starts per lead). Polling has a hard deadline (SKAEL_MAX_WARTEZEIT) and never resubmits a job.
 * Exit codes: 0 ok · 1 input/config error or requests rejected · 2 key rejected · 3 credits used up · 4 SKAEL_MAX_CREDITS reached ·
 *             5 Skael not answering / leads still open after temporary errors (start again later) · 130 Ctrl+C
 */
import { readFileSync, writeFileSync, existsSync, renameSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { skaelAbrufen, schlafen, ApiFehler, AuftragFehlgeschlagen } from "./wiederholen.mjs";

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

const KEY = env.SKAEL_API_KEY ?? env.SKAEL_KEY;
if (!KEY) fail("SKAEL_API_KEY fehlt — Anreicherung nicht möglich.");
const BASIS = (env.SKAEL_URL || "https://api.skael.de").replace(/\/+$/, "");
const KAMPAGNE = String(env.KAMPAGNE || "standard").trim();
if (!/^[\w.-]{1,60}$/.test(KAMPAGNE)) fail(`KAMPAGNE=${KAMPAGNE}: nur Buchstaben, Ziffern, Punkt, Minus, Unterstrich.`);
const CSV_IN = env.CSV || `leads_${KAMPAGNE}_MASTER.csv`;
const STAMM = CSV_IN.replace(/\.csv$/i, "");
// progress per campaign and seller id: enriching the run file and later the master never pays a lead twice
const CSV_OUT = `${STAMM}_angereichert.csv`, STATE_F = `anreicherung_${KAMPAGNE}_state.json`;
const WORKER = num("SKAEL_WORKER", 12, 1);
const flag01 = (k, def) => { const v = String(env[k] ?? "").trim(); if (!v) return def; if (v === "0" || v === "1") return v === "1"; fail(`${k}=${v} ist ungültig (erlaubt: 0 oder 1).`); };
const MIT_AGENT = flag01("SKAEL_AGENT", true);
const MAIL_PRUEFEN = flag01("EMAIL_PRUEFUNG", true);
const ERNEUT = flag01("ERNEUT_VERSUCHEN", false);         // reopen leads and addresses that ran out of their 3 attempts         // deliverability check of every lead e-mail (3 credits each)
const RATE = num("SKAEL_RATE", 5, 1), MAX_WARTEN_S = num("SKAEL_MAX_WARTEZEIT", 600, 30);
const MAX_RETRIES = num("MAX_RETRIES", 5, 1);                // attempts per request on temporary errors (backoff 2/4/8/16 s, 429: 5/10/20/40 s)
const MAX_CREDITS = num("SKAEL_MAX_CREDITS", 0);           // 0 = no cap; counts all starts of this campaign together
// a legal imprint (Impressum) exists for companies in DE/AT/CH; elsewhere the search costs credits for nothing
const LAENDER_ROH = String(env.ANREICHERUNG_LAENDER ?? "DE,AT,CH").trim();
const LAENDER = /^(alle|\*)$/i.test(LAENDER_ROH) || !LAENDER_ROH ? null : LAENDER_ROH.split(",").map((s) => s.trim().toUpperCase()).filter(Boolean);
if (!existsSync(CSV_IN)) fail(`${CSV_IN} nicht gefunden. Mit CSV=datei.csv angeben (oder KAMPAGNE prüfen).`);

// ---------- lists ----------
const FREEMAIL = new Set(("gmail.com googlemail.com gmail.de web.de outlook.com outlook.de outlook.at hotmail.com hotmail.de hotmail.ch live.com live.de " +
  "icloud.com me.com mac.com msn.com t-online.de t-online.at aol.com mail.com email.de online.de freenet.de arcor.de vodafone.de kabelmail.de posteo.de " +
  "mailbox.org protonmail.com proton.me tutanota.de tutanota.com tuta.io tuta.com bluewin.ch bluemail.ch hispeed.ch sunrise.ch gmx.net gmx.de gmx.at gmx.ch " +
  "a1.net aon.at chello.at inode.at ymail.com rocketmail.com 163.com 126.com qq.com foxmail.com yandex.com yandex.ru libero.it seznam.cz wp.pl o2.pl onet.pl " +
  "interia.pl orange.fr free.fr laposte.net zoho.com fastmail.com hushmail.com vivaldi.net").split(/\s+/));
const FREEMAIL_RE = /^(gmx|yahoo|hotmail|outlook|live|aol|icloud|protonmail|yandex)\.(com|de|at|ch|net|fr|it|es|nl|pl|ru|co\.uk)$/;
const istFreemail = (d) => FREEMAIL.has(d) || FREEMAIL_RE.test(d);
const NIE_WEBSITE = new RegExp("(^|\\.)(amazon|ebay|etsy|kaufland|otto|idealo|check24|geizhals|alibaba|aliexpress|temu|firminform|northdata|firmenwissen|gelbeseiten|" +
  "wlw|cylex|gewerbedatenbank|sellwerk|fusionbase|unternehmen24|dasoertliche|dastelefonbuch|11880|meinestadt|golocal|yelp|branchenbuch|kleinanzeigen|" +
  "ebay-kleinanzeigen|handelsregister|online-handelsregister|unternehmensregister|bundesanzeiger|companyhouse|creditreform|implisense|moneyhouse|zefix|" +
  "help|local|search|firmenabc|herold|wko|compnet|kununu|xing|trustpilot|scribd|yumpu|calameo|issuu|ionos|strato|jimdoweb|jimdo|myshopify|wixsite|" +
  "facebook|instagram|linkedin|youtube|wikipedia|tiktok|pinterest|twitter|x|google|bing|duckduckgo|reddit)\\.|\\.gv\\.at$|\\.admin\\.ch$|\\.bund\\.de$|\\.gov$|zeitung|uni-|\\.edu$", "i");
// hosting / shop providers: only their own legal names count (no substring match: "Stratos GmbH" is a real company)
const istHoster = (f) => /^(1&1|1und1|ionos|strato|shopify|wix\.com|jimdo|united[- ]domains|hetzner|all-inkl(\.com)?|godaddy|squarespace)\b(\s+(internet|online|international|ionos|neue medien\S*))*\s*(se|ag|gmbh|ltd\.?|limited|inc\.?|& co\.? kg)?$/i.test(String(f ?? "").trim());
const BUNDESLAENDER = new Set(["baden-württemberg","bayern","bavaria","brandenburg","hessen","mecklenburg-vorpommern","niedersachsen","nordrhein-westfalen","nrw","rheinland-pfalz","saarland","sachsen","sachsen-anhalt","schleswig-holstein","thüringen","thuringia","österreich","oesterreich","austria","steiermark","tirol","kärnten","salzburg","vorarlberg","burgenland","niederösterreich","oberösterreich","deutschland","germany","schweiz","switzerland","zürich","bern","aargau","luzern"]);
const STADTSTAATEN = new Set(["berlin","hamburg","bremen","wien","basel","genf"]);
// curated first names, unambiguous only (Andrea, Simone, Gabriele, Kai, Nicola, Sascha ... stay neutral)
const M = new Set("albert alfred arnold benno bruno detlef dietmar dietrich eckhard edgar egon elias emil erwin ernst finn fritz gerd gert gottfried günter günther hartmut heinz jannik julian konrad leopold lothar ludwig maik malte manuel marius mathias mike mirko nico noah norman ole otto ralph reinhold rico roman rüdiger rupert silvio sören theo thilo timo ulf veit wilfried willi winfried alexander andreas anton armin axel bastian benedikt benjamin bernd bernhard björn boris carsten christian christoph clemens daniel david dennis dieter dirk dominik eduard erik fabian felix ferdinand florian frank franz frederik georg gerald gerhard gregor guido gunnar gustav hannes hans harald heiko heinrich helmut henrik herbert hermann holger horst hubert ingo jakob jan jens joachim jochen johann johannes jonas jörg josef jürgen karl karsten kevin klaus konstantin kurt lars leon lorenz lukas lutz manfred marc marcel marco marcus mario mark markus martin matthias max maximilian michael moritz nick niclas niklas nils norbert olaf oliver oskar pascal patrick paul peter philip philipp rainer ralf raphael reinhard rene richard robert roland rolf rudolf ruben sebastian severin siegfried simon stefan steffen sven thomas thorsten till tim tobias tom torsten udo ulrich uwe valentin viktor vincent volker walter werner wilhelm wolfgang mehmet mustafa ahmet ali hasan hüseyin ibrahim ismail murat osman ömer emre burak serkan tolga volkan ahmed mohamed mohammed omar khalid tarek samir karim rachid youssef pavel piotr pawel andrzej krzysztof tomasz marek jacek grzegorz dariusz zbigniew slawomir miroslav milan dragan goran igor ivan vladimir sergej dmitri alexei nikolai oleg juri bogdan adrian cristian mihai stefanos dimitrios georgios konstantinos".split(/\s+/));
const F = new Set("amelie anne annika christa denise edith elfriede ella emilia erika frieda gertrud greta hannelore heidi hildegard ida irmgard jacqueline jule kristina leonie lina liselotte luisa marianne marlies melissa mia michelle nadja nele nora paula ronja rosemarie silvia sofia stephanie susann susanna tina waltraud alexandra angela angelika anja anke anna annette antje barbara beate bettina birgit brigitte carina carla carmen carolin caroline charlotte christiane christina christine claudia cornelia dagmar daniela diana doris dorothea elena elisabeth elke ellen emma eva franziska gisela gudrun hanna hannah heike helena helga ines inge ingrid irene iris isabel isabell isabella jana janina jasmin jennifer jessica johanna julia juliane jutta karin karina katarina katharina kathrin katja katrin kerstin kirsten klara kristin lara laura lea lena lisa lucia luise magdalena maja manuela mareike margarete maria marie marina marion marlene martina melanie michaela miriam monika nadine natalie nicole nina olga petra pia ramona rebecca regina renate rita sabine sabrina sandra sarah silke sonja sophie stefanie steffi susanne svenja sylvia tanja tatjana theresa ulrike ursula ute vanessa vera verena veronika viktoria yvonne ayse fatma emine hatice zeynep elif merve esra amira leila yasmin fatima aisha polina swetlana irina ekaterina natalia oksana tatiana ludmila galina anastasia agnieszka katarzyna malgorzata joanna magda ewa zofia".split(/\s+/));

// ---------- CSV (delimiter from the header line, quotes only at field start, BOM optional) ----------
let text = readFileSync(CSV_IN, "utf8").replace(/^﻿/, "");
if (text.includes("�")) console.warn("WARNUNG: Die Datei ist offenbar nicht UTF-8 (Umlaute kaputt) — in Excel als „CSV UTF-8“ speichern.");
const kopfZeile = text.split(/\r?\n/)[0] ?? "";
const SEP = [";", ",", "\t"].map((s) => [s, kopfZeile.split(s).length]).sort((a, b) => b[1] - a[1])[0][0];
function csvParse(t) {
  const rows = []; let row = [], feld = "", inQ = false;
  for (let i = 0; i < t.length; i++) { const c = t[i];
    if (inQ) { if (c === '"') { if (t[i + 1] === '"') { feld += '"'; i++; } else inQ = false; } else feld += c; }
    else if (c === '"' && feld === "") inQ = true;
    else if (c === SEP) { row.push(feld); feld = ""; }
    else if (c === "\n" || c === "\r") { if (c === "\r" && t[i + 1] === "\n") i++; row.push(feld); feld = ""; rows.push(row); row = []; }
    else feld += c; }
  if (feld !== "" || row.length) { row.push(feld); rows.push(row); }
  return rows.filter((r) => r.some((v) => v.trim()));
}
// formula-like values from the web are neutralised for Excel (phone numbers like "+49 30 123" stay untouched)
const esc = (v) => { let s = v == null ? "" : String(v).replace(/\r\n?|\n/g, " ");
  if (/^[=@\t]/.test(s) || /^[+-](?![\d\s()\/.-]*$)/.test(s)) s = "'" + s;
  return /[";]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
const roh = csvParse(text); text = null;
if (!roh.length) fail(`${CSV_IN} ist leer.`);
const kopf = roh[0].map((k) => k.trim());
// column names of amazon_seller_scraper.mjs first, older names accepted as aliases
// (own company lists work too: only a company name is required, Seller-ID is optional)
const SPALTEN = { firma: ["Firma", "Firmenname", "Unternehmen", "Company"], seller: ["Seller-ID", "Seller ID"], marke: ["Marke", "Markenname", "Brand"],
  adresse: ["Adresse", "Geschäftsadresse", "Anschrift", "Ort", "Stadt"], land: ["Land", "Verkäuferland", "Country"],
  email: ["E-Mail", "Email", "E-Mail-Adresse"], telefon: ["Telefon", "Tel", "Telefonnummer"], hrb: ["Handelsregister", "HRB", "HR-Nummer", "Handelsregisternummer"],
  ustid: ["USt-IdNr", "USt-ID", "UStID"], gf: ["Vertretungsberechtigt", "Vertretungsberechtigte Person", "Geschäftsführer", "Inhaber"] };
const IDX = {};
for (const [k, namen] of Object.entries(SPALTEN)) { const i = kopf.findIndex((h) => namen.some((n) => n.toLowerCase() === h.toLowerCase())); if (i >= 0) IDX[k] = i; }
if (IDX.firma == null) fail(`Spalte "Firma" bzw. "Firmenname" fehlt in ${CSV_IN} (erkannte Spalten: ${kopf.join(" | ")}).`);
// results are written to NEW columns; a file that already carries them would be paid for without showing anything new
const SCHON = ["E-Mail Status", "Match-Status", "Anreicherung-Fehler", "Pfad"].filter((s) => kopf.includes(s));
if (SCHON.length) fail(`${CSV_IN} ist bereits angereichert bzw. im Standardformat (Spalte „${SCHON[0]}“). Bitte die MASTER- bzw. Original-CSV angeben, z. B. CSV=leads_${KAMPAGNE}_MASTER.csv.`);
const fehlend = Object.keys(SPALTEN).filter((k) => IDX[k] == null);
if (fehlend.length) console.warn(`Hinweis: optionale Spalten fehlen (${fehlend.map((k) => SPALTEN[k][0]).join(", ")}) — Abgleich ist dann schwächer.`);
const g = (r, k) => (IDX[k] != null ? String(r[IDX[k]] ?? "").trim() : "");
const leads = roh.slice(1).map((r) => { if (r.length > kopf.length) console.warn(`Hinweis: Zeile mit ${r.length} statt ${kopf.length} Feldern — überzählige Felder werden ignoriert.`);
  return Array.from({ length: kopf.length }, (_, j) => r[j] ?? ""); });
const idVon = (r) => g(r, "seller") || "x_" + createHash("sha1").update(`${g(r, "firma")}|${g(r, "adresse")}`).digest("hex").slice(0, 12);

// ---------- state (checkpoint per lead and per paid call) ----------
let S = {};
if (existsSync(STATE_F)) { try { S = JSON.parse(readFileSync(STATE_F, "utf8")); } catch (e) { fail(`${STATE_F} ist beschädigt (${e.message}) — umbenennen, dann beginnt die Anreicherung neu.`); } }
S.__meta ??= { credits: 0 };
const OFFEN = (S.__meta.offen ??= {});          // submitted but not yet collected jobs: idempotency key -> reserved credits
let lastSave = 0, credits = S.__meta.credits ?? 0, reserviert = 0, STOP = null;
const creditsStart = credits;
const saveT = (force) => { const n = Date.now(); if (force || n - lastSave > 5000) { lastSave = n; S.__meta.credits = credits; writeFileSync(STATE_F + ".tmp", JSON.stringify(S)); renameSync(STATE_F + ".tmp", STATE_F); } };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
class StopSignal extends Error {}
class TransientError extends Error {}
class Abgelehnt extends Error {}                // request not accepted for this input (validation 422 or another 4xx)
class Fehlgeschlagen extends Error {}           // the operation ran and failed (status "failed"), e.g. "Unable to extract impressum data"
const halt = (code, msg) => { if (!STOP) { STOP = { code, msg }; console.error(`\n${msg}`); } throw new StopSignal(msg); };
let sigints = 0;
for (const sig of ["SIGINT", "SIGTERM"]) process.on(sig, () => { if (++sigints > 1) { try { saveT(true); } catch {} process.exit(130); }
  STOP ??= { code: 130, msg: "Abbruch durch Benutzer" }; console.log("\nAbbruch angefordert — laufende Abfragen werden beendet, der Stand wird gespeichert …"); });

// ---------- Skael API ----------
// Every endpoint answers {"data": {id, status, output, error_message, credits_cost?, ...}} (api.skael.de/docs/api-guide).
// Requests are submitted with async=true and collected by long polling: the default sync mode keeps the connection
// open for up to an hour. The Idempotency-Key makes a retry free (same key + same body within 24 h is not charged again).
const HEADERS = { "Content-Type": "application/json", Accept: "application/json", Authorization: `Bearer ${KEY}` };
let naechsterSlot = 0;
const takt = async () => { const jetzt = Date.now(), warte = Math.max(0, naechsterSlot - jetzt); naechsterSlot = Math.max(jetzt, naechsterSlot) + 1000 / RATE; if (warte) await sleep(warte); };
const pause = (ms) => schlafen(ms, () => !!STOP);    // backoff pauses end early on Ctrl+C
const zugang = (status) => {
  if (status === 401 || status === 403) halt(2, `Skael-Zugang abgelehnt (HTTP ${status}) — SKAEL_API_KEY prüfen.`);
  if (status === 402) halt(3, "Skael-Credits aufgebraucht (HTTP 402) — Stand gespeichert.");
};
const STAT = {};                              // per endpoint: results, rejections, requests in flight
const laufend = new Map();                    // identical requests inside this process share one job and one poll
// consecutive calls without a usable answer, across all workers: an outage must stop the run instead of "finishing" it
let serie = 0;
const ohneAntwort = (grund) => { if (++serie >= 10) halt(5, `Skael liefert seit ${serie} Abfragen in Folge kein Ergebnis (${String(grund).slice(0, 140)}) — Lauf angehalten, der Stand ist gespeichert. Internet, SKAEL_URL und den Skael-Status prüfen, dann neu starten.`); };

// -> output object of the endpoint. Throws Abgelehnt, Fehlgeschlagen or TransientError; the caller decides what each means.
// salz changes the Idempotency-Key, so a retry on a later start does not get the same failed job replayed.
async function skael(pfad, body, kredite, salz = 0) {
  if (STOP) throw new StopSignal();
  const schluessel = createHash("sha256").update(JSON.stringify(salz ? [pfad, body, salz] : [pfad, body])).digest("hex");
  if (!laufend.has(schluessel)) {
    // credits of calls still in flight are reserved, otherwise parallel workers overshoot the cap
    if (MAX_CREDITS && credits + reserviert + kredite > MAX_CREDITS) halt(4, `Credit-Deckel SKAEL_MAX_CREDITS=${MAX_CREDITS} erreicht (${credits} verbraucht, ${reserviert} in laufenden Abfragen, alle Starts dieser Kampagne) — Stand gespeichert, Neustart mit höherem Deckel setzt fort.`);
    reserviert += kredite;
    laufend.set(schluessel, skaelAbruf(pfad, body, kredite, schluessel).finally(() => { reserviert -= kredite; laufend.delete(schluessel); }));
  }
  try { return await laufend.get(schluessel); }
  catch (e) {
    if (e instanceof TransientError) ohneAntwort(e.message);
    else if (e instanceof Abgelehnt) ohneAntwort(`abgelehnt: ${e.message}`);
    else if (e instanceof Fehlgeschlagen && (pfad === "verify_email" || pfad === "google_search")) ohneAntwort(`fehlgeschlagen: ${e.message}`);
    throw e;
  }
}
// submit + long polling + retry rule live in wiederholen.mjs; this wrapper books credits and maps the errors.
// A job that failed temporarily is resubmitted there under "<key>-w<n>"; every submitted key is booked on its own.
async function skaelAbruf(pfad, body, kredite, schluessel) {
  const st = (STAT[pfad] ??= { ok: 0, abgelehnt: 0, laeuft: 0 });
  const buchbar = {};                           // key -> false for the replay of a job that was already booked (or belongs to another list)
  const buche = (k, d, standard) => { if (buchbar[k]) { const c = Number(d?.credits_cost); credits += d?.credits_cost != null && Number.isFinite(c) ? c : standard; } delete OFFEN[k]; };
  st.laeuft++;
  try {
    const d = await skaelAbrufen({ basis: BASIS, pfad, body, schluessel, headers: HEADERS, maxVersuche: MAX_RETRIES, maxWartenS: MAX_WARTEN_S,
      schlafen: pause, takt, zugang, wartenS: () => (STOP ? 5 : 50), pruefeStop: () => { if (STOP) throw new StopSignal(); },
      // a replay is free, unless it is a job this campaign submitted earlier and never collected (stop, timeout)
      eingereicht: ({ schluessel: k, replay, laeuft }) => { buchbar[k] = !replay || k in OFFEN; if (laeuft && buchbar[k]) OFFEN[k] = kredite; },
      abgeschlossen: ({ schluessel: k, d: e, ok }) => buche(k, e, ok ? kredite : 0) });
    st.ok++; serie = 0;
    return d.output && typeof d.output === "object" ? d.output : {};
  } catch (e) {
    if (!(e instanceof ApiFehler)) throw e;                               // StopSignal, halt()
    if (e instanceof AuftragFehlgeschlagen) throw new Fehlgeschlagen(String(e.meldung || "Auftrag fehlgeschlagen").slice(0, 160));
    if (e.voruebergehend) throw new TransientError(e.message);
    if (e.status === 404 || e.status === 405) halt(1, `Skael-Endpunkt ${pfad} nicht gefunden (HTTP ${e.status}) — SKAEL_URL prüfen.`);
    // validation 422 or another 4xx: this input is not accepted. If an endpoint has never answered and rejects everything, the request itself is wrong.
    st.abgelehnt++;
    const msg = String(e.meldung || `HTTP ${e.status}`).slice(0, 160);
    if (!st.ok && st.abgelehnt >= 5 && st.laeuft <= 1) halt(1, `Skael lehnt alle Anfragen an ${pfad} ab: ${msg} — Lauf angehalten, es wurde dafür nichts berechnet.`);
    // before the first success of an endpoint nothing is stored as final: the lead stays open
    throw st.ok ? new Abgelehnt(msg) : new TransientError(`${pfad} abgelehnt: ${msg}`);
  } finally { st.laeuft--; }
}

// ---------- helpers ----------
const host = (u) => { try { return new URL(/^https?:/i.test(u) ? u : "https://" + u).hostname.replace(/^www\./, "").toLowerCase(); } catch { return null; } };
const normReg = (v) => { const m = String(v ?? "").toUpperCase().match(/(HR\s*[AB]|FN|GNR|GEN\.?R)(?:[\s-]*NR\.?)?\s*\.?\s*(\d+)(?:\s?([A-Z])(?![A-ZÄÖÜ]))?/);
  return m ? m[1].replace(/[\s.]/g, "") + m[2] + (m[3] ?? "") : null; };
const gerichtAus = (v) => (String(v ?? "").match(/amtsgericht\s+([A-Za-zÄÖÜäöüß.\- ]{3,40}?)(?=[,;()]|\s+HR|\s*$)/i)?.[1] ?? "").toLowerCase().replace(/[^a-zäöüß]/g, "") || null;
const normUst = (v) => { const s = String(v ?? "").toUpperCase().replace(/[^A-Z0-9]/g, ""); return s.length >= 8 ? s : null; };
const normFirma = (v) => String(v ?? "").toLowerCase().replace(/\b(gmbh|ug|ag|kg|ohg|gbr|mbh|co|e\.?\s?k\.?|e\.?\s?u\.?|inh\.?|inhaber(in)?|haftungsbeschr(ä|ae)nkt|limited|ltd|se|holding|handels?)\b/g, " ").replace(/[^a-zäöüß0-9]/g, "");
const normTel = (v) => { let s = String(v ?? "").replace(/\D/g, ""); s = s.replace(/^00/, "").replace(/^(49|43|41)0?/, "").replace(/^0/, ""); return s.length >= 8 ? s : null; };
// registrable label: shop.firma.de -> firma, firma.co.uk -> firma
const kernLabel = (h) => { const t = String(h ?? "").split("."); if (t.length < 2) return ""; const zweistufig = t.length >= 3 && /^(co|com|org|net|gv|ac|or)$/.test(t[t.length - 2]);
  return (zweistufig ? t[t.length - 3] : t[t.length - 2]).replace(/[^a-z0-9]/g, ""); };
const stadtAus = (adresse) => {
  const teile = String(adresse ?? "").split(",").map((t) => t.trim()).filter(Boolean);
  if (teile.length < 3) return "";
  const i = teile.length - 3; let kand = teile[i] ?? "";
  if (BUNDESLAENDER.has(kand.toLowerCase())) { const davor = teile[i - 1] ?? "";
    if (!/\d/.test(davor) && davor) kand = davor; else kand = STADTSTAATEN.has((teile[i + 1] ?? "").toLowerCase()) ? teile[i + 1] : ""; }
  kand = kand.replace(/\b\d{4,5}\b/g, "").trim();
  return BUNDESLAENDER.has(kand.toLowerCase()) ? "" : kand;
};
const organischeDomains = (res, max) => {
  const out = [];
  const listen = [res?.organic, res?.organic_results, res?.results, res?.items, Array.isArray(res) ? res : null].filter(Array.isArray);
  for (const l of listen) for (const e of l) { const u = e?.link ?? e?.url ?? e?.href; const h = u && host(u);
    if (h && !NIE_WEBSITE.test(h) && !istFreemail(h) && !out.includes(h)) out.push(h); if (out.length >= max) return out; }
  return out;
};
const gfListe = (imp) => { const x = imp?.geschaeftsfuehrer; return Array.isArray(x) ? x.filter((v) => typeof v === "string" && v.trim()) : typeof x === "string" && x.trim() ? [x] : []; };
const verantwortlich = (imp) => { const r = imp?.rechtlicher_verantwortlicher; return typeof r === "string" ? r : r?.name ?? null; };
const hatInhalt = (imp) => !!(imp && (imp.firmenname || gfListe(imp).length));

// salutation: first person only, titles removed, Herr/Frau in the source decides, otherwise unambiguous first names only
const ZUSATZ = new Set(["von", "van", "de", "di", "da", "ten", "zu", "al", "le", "mac", "der", "den", "dos", "el"]);
const TITEL = /^(dr|prof|dipl[.\-\w]*|mag|ing|b\.?sc|m\.?sc|mba|jr|ll\.?m)\.?$|^(sen|jun)\.$/i;
const geschlechtVon = (vor) => { const t = vor.toLowerCase().split("-"); const gs = t.map((x) => (M.has(x) ? "m" : F.has(x) ? "f" : null));
  return gs.every((x) => x && x === gs[0]) ? gs[0] : null; };
function person(rohname) {
  const r = String(rohname ?? "").replace(/[  ]/g, " ").trim();
  if (!r || /\d|@/.test(r)) return null;
  if (/^[^,\s]+,\s*[^,\s]+$/.test(r)) return { name: r, nach: null, geschlecht: null };             // "Nachname, Vorname": stay neutral
  let n = r.split(/\s*[,/;]\s*|\s+(?:und|&)\s+/i)[0].trim(), anrede = null;
  const a = n.match(/^(herr|frau)\s+/i); if (a) { anrede = a[1].toLowerCase() === "herr" ? "m" : "f"; n = n.slice(a[0].length); }
  const w = n.split(/\s+/).filter((t) => t && !TITEL.test(t));
  if (w.length < 2 || /^[A-ZÄÖÜ]\.?$/.test(w[0])) return null;                                       // initials cannot be resolved
  const fix = (t) => (ZUSATZ.has(t.toLowerCase()) ? t.toLowerCase()
    : t.split("-").map((x) => (x && (x === x.toUpperCase() || x === x.toLowerCase()) ? x[0].toUpperCase() + x.slice(1).toLowerCase() : x)).join("-"));
  const teile = w.map(fix);
  let nachStart = teile.length - 1;
  while (nachStart > 1 && ZUSATZ.has(teile[nachStart - 1].toLowerCase())) nachStart--;
  return { name: teile.join(" "), nach: teile.slice(Math.max(1, nachStart)).join(" "), geschlecht: anrede ?? geschlechtVon(teile[0]) };
}
const anredeVon = (p) => (!p?.geschlecht || !p.nach ? "Sehr geehrte Damen und Herren" : p.geschlecht === "m" ? `Sehr geehrter Herr ${p.nach}` : `Sehr geehrte Frau ${p.nach}`);
// standard fields shared by all lead paths: neutral "Guten Tag" whenever name or gender is not certain
const persoenlich = (p) => !!(p?.geschlecht && p.nach);
const standardVon = (p) => ({ anrede: persoenlich(p) ? (p.geschlecht === "m" ? "Herr" : "Frau") : "",
  vorname: p?.nach && p.name.endsWith(p.nach) ? p.name.slice(0, -p.nach.length).trim() : "", nachname: p?.nach ?? "",
  ansprache: persoenlich(p) ? `Guten Tag ${p.geschlecht === "m" ? "Herr" : "Frau"} ${p.nach}` : "Guten Tag" });

// ---------- match cascade (order matters: register before VAT id) ----------
function kaskade(lead, imp, quelle, domain) {
  if (istHoster(imp?.firmenname)) return null;                                                      // 0 hoster imprint
  const r1 = normReg(g(lead, "hrb")), r2 = normReg(imp?.handelsregister_number);
  if (r1 && r2 && r1 === r2) { const c1 = gerichtAus(g(lead, "hrb")), c2 = gerichtAus(`${imp?.handelsregister_court ?? imp?.registergericht ?? ""} ${imp?.handelsregister_number ?? ""}`);
    if (!c1 || !c2 || c1 === c2) return "register"; }                                               // 1 register (+ court if both known)
  const u1 = normUst(g(lead, "ustid")), u2 = normUst(imp?.ust_id);
  if (u1 && u2 && u1 === u2) return "ustid";                                                        // 2 VAT id
  const f1 = normFirma(g(lead, "firma")), f2 = normFirma(imp?.firmenname);
  if (f1.length >= 3 && f1 === f2) return "firmenname";                                             // 3 company name exact
  const t1 = normTel(g(lead, "telefon")), t2 = normTel(imp?.telefon);
  if (t1 && t2 && t1 === t2) return "telefon";                                                      // 4a phone
  const e1 = g(lead, "email").toLowerCase(), e2 = String(imp?.email ?? "").toLowerCase().trim();
  if (e1 && e2 && e1 === e2) return "email";                                                        // 4b e-mail
  if (quelle === "email") {                                                                         // 5 domain: ONLY for the e-mail domain itself
    const kern = kernLabel(domain), marke = normFirma(g(lead, "marke"));
    const passt = (x) => x.length >= 4 && (kern.includes(x) || x.includes(kern));
    if (kern.length >= 4 && (passt(f1) || passt(marke))) return "domain";
  }
  return null;
}

// ---------- per lead ----------
let agentAn = MIT_AGENT, agentFehl = 0;
async function bearbeite(lead, E) {
  const firma = g(lead, "firma"), marke = g(lead, "marke"), stadt = stadtAus(g(lead, "adresse"));
  const land = (g(lead, "land") || "DE").toLowerCase();
  E.gelesen ??= {};
  // "failed" is a normal outcome here (no imprint, site unreachable); a rejected domain is an input problem. Both are final for this domain.
  const lies = async (d) => { if (d in E.gelesen) return E.gelesen[d];
    try { return (E.gelesen[d] = await skael("imprint_extractor", { domain: d }, 10)); }
    catch (e) { if (e instanceof Fehlgeschlagen || e instanceof Abgelehnt) return (E.gelesen[d] = null); throw e; } };
  const em = g(lead, "email").toLowerCase().match(/@([a-z0-9.\-]+\.[a-z]{2,})$/)?.[1] ?? null;
  const emailDomain = em && !istFreemail(em) && !NIE_WEBSITE.test(em) ? em : null;
  const versuche = [];
  if (emailDomain) versuche.push({ d: emailDomain, src: "email" });                                // phase 1 (0 credits)
  else if (firma) {                                                                                 // phase 2 (1 credit per query)
    if (!E.kand) {
      let kand = [];
      for (const q of [`${firma} ${stadt} Impressum`, `${firma} ${stadt}`].map((x) => x.replace(/\s+/g, " ").trim())) {
        let r;
        try { r = await skael("google_search", { query: q.slice(0, 500), gl: ["de", "at", "ch"].includes(land) ? land : "de", hl: "de", num_results: 10 }, 1); }
        catch (e) { if (e instanceof Abgelehnt) r = {}; else if (e instanceof Fehlgeschlagen) throw new TransientError(`google_search: ${e.message}`); else throw e; }
        kand = organischeDomains(r, 3);
        if (kand.length) break;
      }
      E.kand = kand;
    }
    for (const d of E.kand) versuche.push({ d, src: "google" });
  }
  let treffer = null, hosterMail = false, gelesen = 0; const mismatch = [];
  for (const v of versuche) {                                                                       // phase 3
    const imp = await lies(v.d);
    if (!hatInhalt(imp)) continue;
    gelesen++;
    if (istHoster(imp.firmenname)) { if (v.src === "email") hosterMail = true; mismatch.push(v.d); continue; }
    const m = kaskade(lead, imp, v.src, v.d);
    if (m) { treffer = { ...v, imp, match: m }; break; }
    mismatch.push(v.d);
  }
  if (!treffer && agentAn && firma) {                                                               // phase 4: agent finds a website only
    if (E.agent === undefined) {
      try {
        const a = await skael("ai_research_agent", {
          system_prompt: "Du recherchierst die offizielle Website von Unternehmen. Nenne nur eine Website, die nachweislich zu genau dieser Firma gehört. Keine Marktplätze, Verzeichnisse oder Social-Media-Profile. Wenn du keine findest, gib einen leeren Text zurück.",
          user_prompt: `Finde die offizielle Firmenwebsite des Amazon-Händlers "${firma}"${marke ? ` (Marke: "${marke}")` : ""}${stadt ? ` mit Sitz in ${stadt}` : ""}${g(lead, "land") ? ` (Land: ${g(lead, "land")})` : ""}. Händler treten teils unter ihrer Marke statt unter dem Firmennamen auf.`,
          schema: { type: "object", properties: { website: { type: "string", description: "Root-Domain der offiziellen Firmenwebsite, leer wenn nicht gefunden" },
            impressum_url: { type: "string", description: "URL der Impressum-Seite, leer wenn nicht gefunden" } }, required: ["website"] },
          max_steps: 8, model: "google/gemini-2.5-flash" }, 10);
        agentFehl = 0; E.agent = (a?.website && host(a.website)) || null;
      } catch (e) {
        // optional step: an error never blocks the lead. After 5 errors in a row it is switched off for the rest of this run.
        if (!(e instanceof Fehlgeschlagen || e instanceof Abgelehnt)) throw e;
        if (++agentFehl >= 5 && agentAn) { agentAn = false; console.log(`\n  Hinweis: Die KI-Recherche liefert wiederholt Fehler (${e.message}) und ist für diesen Lauf abgeschaltet.`); }
      }
    }
    const h = E.agent;
    if (h && !NIE_WEBSITE.test(h) && !istFreemail(h) && !versuche.some((v) => v.d === h)) {
      const imp = await lies(h);
      if (hatInhalt(imp)) { gelesen++; const m = kaskade(lead, imp, "agent", h); if (m) treffer = { d: h, src: "agent", imp, match: m }; else mismatch.push(h); }
    }
  }
  if (treffer) Object.assign(E, { web: treffer.d, src: treffer.src, imp: treffer.imp, match: treffer.match, err: null });
  // the seller's own e-mail domain stays the website even if its imprint names another entity (often brand vs. company name);
  // Match-Status "email-domain" marks it as unconfirmed, the deviating imprint is noted in the error column
  else if (emailDomain && !hosterMail) Object.assign(E, { web: emailDomain, src: "email", imp: null, match: "email-domain",
    err: mismatch.length ? `Impressum nicht bestätigt: ${mismatch.join(", ")}` : null });
  else Object.assign(E, { web: null, src: null, imp: null, match: null,
    err: mismatch.length ? `MISMATCH: ${mismatch.join(", ")}` : gelesen || versuche.length || E.agent ? "kein Impressum lesbar" : "keine Website gefunden" });
  const gfImp = treffer ? gfListe(treffer.imp)[0] ?? verantwortlich(treffer.imp) : null;
  E.p = (gfImp && person(gfImp)) || person(g(lead, "gf")) || null;                                 // fallback: managing director from the seller page
}

// ---------- e-mail deliverability (every lead with an address, independent of the country) ----------
const MAIL_LABEL = { 5: "Safe to Send", 4: "Risky", 7: "Unknown" };   // Debounce codes; 1, 2, 3, 6 = Invalid
const MAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const mailVon = (lead) => g(lead, "email").toLowerCase();
async function pruefeMail(lead, E) {
  const a = mailVon(lead);
  if (!MAIL_RE.test(a) || a.length > 255) { E.mail = { a, code: 1, status: "Invalid", grund: "Syntax" }; return; }
  let o;
  try { o = await skael("verify_email", { email: a }, 3, E.mail_fehl?.a === a ? E.mail_fehl.n : 0); }
  catch (e) { if (!(e instanceof Abgelehnt)) throw e; E.mail = { a, code: 1, status: "Invalid", grund: `von Skael abgelehnt: ${e.message}`.slice(0, 120) }; delete E.mail_fehl; return; }
  const code = Number(o?.code);
  // only a real verdict is stored. Anything else stays "Not Run" and is tried again on the next start.
  if (!(code in MAIL_LABEL) && ![1, 2, 3, 6].includes(code)) { ohneAntwort("verify_email ohne Ergebnis"); throw new TransientError("verify_email: Antwort ohne Ergebnis"); }
  E.mail = { a, code, status: MAIL_LABEL[code] ?? "Invalid", grund: o.reason ?? null, rolle: o.is_role ?? null, catchall: o.is_catch_all ?? null };
  delete E.mail_fehl;
}
const mailStatus = (lead, E) => { const a = mailVon(lead); return !a ? "" : E?.mail?.a === a ? E.mail.status : "Not Run"; };

// ---------- main ----------
const leadVon = new Map(); for (const l of leads) { const id = idVon(l); if (!leadVon.has(id)) leadVon.set(id, l); }
const landVon = (l) => g(l, "land").toUpperCase();
const uebersprungen = new Set(LAENDER ? [...leadVon].filter(([, l]) => landVon(l) && !LAENDER.includes(landVon(l))).map(([id]) => id) : []);
const ids = [...leadVon.keys()];
if (ERNEUT) for (const E of Object.values(S)) { if (!E || typeof E !== "object") continue; delete E.mail_fehl; if (E.transient) { delete E.done; delete E.transient; delete E.versuche; } }
const mailGesperrt = (id) => { const a = mailVon(leadVon.get(id)), f = S[id]?.mail_fehl; return !!f && f.a === a && f.n >= 3; };
const brauchtMail = (id) => { const a = mailVon(leadVon.get(id)); return MAIL_PRUEFEN && !!a && S[id]?.mail?.a !== a && !mailGesperrt(id); };
const brauchtImp = (id) => !S[id]?.done && !uebersprungen.has(id);
const mailListe = ids.filter(brauchtMail), impListe = ids.filter(brauchtImp), nGesperrt = MAIL_PRUEFEN ? ids.filter(mailGesperrt).length : 0;
console.log(`Anreicherung: ${ids.length} Leads aus ${CSV_IN} · offen: ${mailListe.length} E-Mail-Prüfungen, ${impListe.length} Website/Impressum · ${WORKER} parallel · Agent ${MIT_AGENT ? "an" : "aus"}${MAX_CREDITS ? ` · Deckel ${MAX_CREDITS} Credits (bisher ${credits})` : ""}`);
if (uebersprungen.size) console.log(`  ${uebersprungen.size} Leads außerhalb von ANREICHERUNG_LAENDER=${LAENDER.join(",")}: nur E-Mail-Prüfung, keine Impressum-Suche.`);
if (!MAIL_PRUEFEN) console.log("  Hinweis: E-Mail-Prüfung abgeschaltet (EMAIL_PRUEFUNG=0) — Adressen bleiben ungeprüft (Not Run).");
if (nGesperrt) console.log(`  ${nGesperrt} Adressen wurden schon in 3 Starts ohne Ergebnis geprüft und bleiben Not Run. Neu versuchen: ERNEUT_VERSUCHEN=1.`);
if (mailListe.length || impListe.length) console.log(`  Grobe Schätzung: ~${mailListe.length * 3 + impListe.length * 5}–${mailListe.length * 3 + impListe.length * 50} Credits (E-Mail-Prüfung 3 je Adresse; Impressum-Suche ohne Firmen-E-Mail eher oben; Dashboard zählt verbindlich).`);
const gesamt = mailListe.length + impListe.length; let fertig = 0, speicherWarnung = false;
const FEHL = { mail: 0, offen: 0, endgueltig: 0 };   // failed items of this start (one lead's error never stops the others)
const schritt = () => { fertig++;
  try { saveT(); } catch (e) { if (!speicherWarnung) { speicherWarnung = true; console.warn(`\n  Zwischenstand gerade nicht speicherbar (${e.message}) — wird beim nächsten Schritt erneut versucht.`); } }
  if (fertig % 20 === 0 || fertig === gesamt) process.stdout.write(`\r  ${fertig}/${gesamt} · ~${credits - creditsStart} Credits  `); };
const pool = async (liste, fn) => { let i2 = 0; await Promise.all(Array.from({ length: Math.min(WORKER, Math.max(1, liste.length)) }, async () => {
  while (!STOP) { const i = i2++; if (i >= liste.length) return; await fn(liste[i]); schritt(); } })); };

// pass 1: every e-mail address first (cheap and mandatory for sending), so a tight credit budget is not spent on websites
await pool(mailListe, async (id) => {
  const E = (S[id] ??= {}), lead = leadVon.get(id), a = mailVon(lead);
  try { await pruefeMail(lead, E); }
  catch (e) { if (STOP || e instanceof StopSignal) return;      // a stop is nobody's failed attempt
    FEHL.mail++; E.mail_fehl = { a, n: (E.mail_fehl?.a === a ? E.mail_fehl.n : 0) + 1, grund: String(e?.message ?? e).slice(0, 120) }; }
});
// pass 2: website, imprint, managing director
await pool(impListe, async (id) => {
  const E = (S[id] ??= {});
  try { await bearbeite(leadVon.get(id), E); E.done = true; delete E.versuche; delete E.transient; }
  catch (e) {
    if (STOP || e instanceof StopSignal) return;
    if (e instanceof TransientError) { FEHL.offen++; E.versuche = (E.versuche ?? 0) + 1; E.err = e.message; if (E.versuche >= 3) { E.done = true; E.transient = true; } }
    else { FEHL.endgueltig++; E.err = String(e?.message ?? e).slice(0, 120); E.done = true; }
  }
});
for (let v = 0; ; v++) { try { saveT(true); break; } catch (e) { if (v >= 2) { console.error(`\nFEHLER: Der Stand konnte nicht gespeichert werden (${e.message}). Bezahlte Ergebnisse dieses Starts kommen beim nächsten Start kostenlos zurück, solange er innerhalb von 24 Stunden erfolgt.`); break; } await sleep(1500); } }
process.stdout.write("\n");
const restMail = STOP ? 0 : ids.filter(brauchtMail).length, restImp = STOP ? 0 : ids.filter(brauchtImp).length;

// ---------- export: original columns untouched + new columns ----------
// a column the input already has keeps its values; the result goes next to it as "<name> (Anreicherung)"
const NEU_BASIS = ["E-Mail Status", "Website", "Website-Quelle", "Impressum-URL", "Impressum-Firmenname", "Geschäftsführung", "Anrede (persönlich)", "Anrede", "Vorname", "Nachname",
  "Ansprache", "Match-Status", "Storefront-URL", "Anreicherung-Fehler"].filter((s) => s !== "Storefront-URL" || !kopf.includes(s));
const NEU = NEU_BASIS.map((s) => (kopf.includes(s) ? `${s} (Anreicherung)` : s));
const doppelt = NEU.filter((s) => s.endsWith(" (Anreicherung)"));
if (doppelt.length) console.log(`  Hinweis: Die Datei hat schon Spalten mit diesen Namen. Die Ergebnisse stehen daneben in: ${doppelt.join(", ")}`);
const zeilen = [[...kopf, ...NEU].map(esc).join(";")];
let stW = 0, stI = 0, stG = 0, stA = 0; const stM = {};
for (const lead of leads) {
  const E = S[idVon(lead)] ?? {}, sid = g(lead, "seller"), st = standardVon(E.p);
  const ms = mailStatus(lead, E); if (ms) stM[ms] = (stM[ms] ?? 0) + 1;
  const wert = { "E-Mail Status": ms, "Website": E.web, "Website-Quelle": E.web ? E.src : "", "Impressum-URL": E.imp?.impressum_url, "Impressum-Firmenname": E.imp?.firmenname,
    "Geschäftsführung": E.p?.name, "Anrede (persönlich)": anredeVon(E.p), "Anrede": st.anrede, "Vorname": st.vorname, "Nachname": st.nachname, "Ansprache": st.ansprache,
    "Match-Status": E.match ?? (E.err?.startsWith("MISMATCH") ? "MISMATCH" : ""),
    "Storefront-URL": sid ? `https://www.amazon.de/s?me=${sid}&marketplaceID=A1PA6795UKMFR9` : "",
    "Anreicherung-Fehler": E.done ? E.err : uebersprungen.has(idVon(lead)) ? `übersprungen: Land ${landVon(lead)} nicht in ANREICHERUNG_LAENDER` : E.err ? `offen: ${E.err}` : "offen" };
  if (E.web) stW++; if (E.imp && ["register", "ustid", "firmenname", "telefon", "email"].includes(E.match)) stI++; if (E.p) stG++; if (E.p?.geschlecht) stA++;
  zeilen.push([...lead, ...NEU_BASIS.map((s) => wert[s] ?? "")].map(esc).join(";"));
}
writeFileSync(CSV_OUT + ".tmp", "﻿" + zeilen.join("\r\n") + "\r\n"); renameSync(CSV_OUT + ".tmp", CSV_OUT);
const pz = (n) => (leads.length ? Math.round((n / leads.length) * 100) + " %" : "-");
console.log(`\n===== ANREICHERUNG ${STOP ? "UNTERBROCHEN" : "FERTIG"} =====`);
console.log(`Website ${pz(stW)} · Impressum bestätigt ${pz(stI)} · Geschäftsführung ${pz(stG)} · persönliche Anrede ${pz(stA)}`);
console.log(`E-Mail-Prüfung: ${["Safe to Send", "Risky", "Unknown", "Invalid", "Not Run"].filter((k) => stM[k]).map((k) => `${k} ${stM[k]}`).join(" · ") || "keine Adressen"}`);
{ const vorueb = [FEHL.mail && `${FEHL.mail} E-Mail-Prüfungen`, FEHL.offen && `${FEHL.offen} Leads`].filter(Boolean).join(" und ");
  const teile = [vorueb && `${vorueb} nach je bis zu ${MAX_RETRIES} Versuchen ohne Ergebnis (vorübergehend, beim nächsten Start erneut)`,
    FEHL.endgueltig && `${FEHL.endgueltig} Leads mit dauerhaftem Fehler (Spalte „Anreicherung-Fehler“)`].filter(Boolean);
  if (teile.length) console.log(`Fehler in diesem Start: ${teile.join(" · ")}`); }
console.log(`Verbrauch (laut Skael, sonst geschätzt): ~${credits - creditsStart} Credits in diesem Start · ~${credits} insgesamt für Kampagne ${KAMPAGNE}`);
console.log(`Datei: ${CSV_OUT}${STOP ? " (Zwischenstand — Neustart setzt fort)" : ""}`);
if (STOP) process.exitCode = STOP.code;
else if (restMail || restImp) { console.log(`UNVOLLSTÄNDIG: ${restMail} E-Mail-Prüfungen und ${restImp} Leads sind wegen vorübergehender Fehler offen — denselben Befehl später erneut starten.`); process.exitCode = 5; }
