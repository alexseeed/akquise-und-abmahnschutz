#!/usr/bin/env node
/**
 * STANDARD FORMAT — last step before the blocklist check.
 *
 * Puts the standard fields shared by all lead paths (wissen/07_lead-ausgabe-und-spalten.md) in front of every
 * other column: Firmenname · Website · E-Mail · E-Mail Status · Anrede · Vorname · Nachname · Ansprache · Quelle · Pfad. Works on the scraper's lead CSV and on the enriched CSV (`…_angereichert.csv`).
 *
 *   node standardformat.mjs <liste.csv>      ->  <liste>_standard.csv
 *
 * Rules: company name from the imprint only when the imprint confirmed the company; salutation "Guten Tag Herr/Frau
 * <Nachname>" only when name and gender are certain, otherwise "Guten Tag". An address the deliverability check rated
 * "Invalid" is removed from the E-Mail field (kept in "E-Mail ungültig"); without a check the status is "Not Run".
 * Nothing is fetched, nothing is paid.
 */
import { readFileSync, writeFileSync, existsSync, renameSync } from "node:fs";

const fail = (m) => { console.error(`FEHLER: ${m}`); process.exit(1); };
const CSV_IN = process.argv[2];
if (!CSV_IN) fail("Aufruf: node standardformat.mjs <liste.csv>");
if (!existsSync(CSV_IN)) fail(`${CSV_IN} nicht gefunden.`);
const CSV_OUT = CSV_IN.replace(/\.csv$/i, "") + "_standard.csv";

const text = readFileSync(CSV_IN, "utf8").replace(/^﻿/, "");
const SEP = [";", ",", "\t"].map((s) => [s, (text.split(/\r?\n/)[0] ?? "").split(s).length]).sort((a, b) => b[1] - a[1])[0][0];
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
// formula-like values are neutralised for Excel (phone numbers like "+49 30 123" stay untouched)
const esc = (v) => { let s = v == null ? "" : String(v).replace(/\r\n?|\n/g, " ");
  if (/^[=@\t]/.test(s) || /^[+-](?![\d\s()\/.-]*$)/.test(s)) s = "'" + s;
  return /[";]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };

const roh = csvParse(text);
if (roh.length < 2) fail(`${CSV_IN} enthält keine Leads.`);
const kopf = roh[0].map((k) => k.trim());
// first name that exists wins (results of the enrichment before columns the list brought along)
const col = (...namen) => { for (const n of namen) { const i = kopf.findIndex((h) => h.toLowerCase() === n.toLowerCase()); if (i >= 0) return i; } return -1; };
const I = { firma: col("Firma", "Firmenname", "Unternehmen", "Company"), impFirma: col("Impressum-Firmenname"), match: col("Match-Status"),
  web: col("Website"), webAnr: col("Website (Anreicherung)"), mail: col("E-Mail", "Email", "E-Mail-Adresse"), mailStatus: col("E-Mail Status"), ungueltig: col("E-Mail ungültig"),
  anrede: col("Anrede (Anreicherung)", "Anrede"), vor: col("Vorname (Anreicherung)", "Vorname"), nach: col("Nachname (Anreicherung)", "Nachname"),
  ansprache: col("Ansprache (Anreicherung)", "Ansprache"), gf: col("Vertretungsberechtigt", "Geschäftsführer", "Inhaber"), seller: col("Seller-ID", "Seller ID"),
  kat: col("Kategorie"), land: col("Land", "Verkäuferland") };
if (I.firma < 0) fail(`Spalte "Firma" bzw. "Firmenname" fehlt (erkannte Spalten: ${kopf.join(" | ")}).`);
const v = (r, k) => (I[k] >= 0 ? String(r[I[k]] ?? "").trim() : "");
const BESTAETIGT = new Set(["register", "ustid", "firmenname", "telefon", "email"]);
const angereichert = I.ansprache >= 0;

const STANDARD = ["Firmenname", "Website", "E-Mail", "E-Mail Status", "Anrede", "Vorname", "Nachname", "Ansprache", "Quelle", "Pfad"];
const GEPRUEFT = ["Safe to Send", "Risky", "Unknown", "Invalid"];
// the address source column and an earlier "E-Mail ungültig" are represented by the standard fields, not passed through
const rest = kopf.map((k, i) => [k, i]).filter(([k, i]) => i !== I.mail && i !== I.ungueltig && !STANDARD.some((s) => s.toLowerCase() === k.toLowerCase()));
const out = [[...STANDARD, ...rest.map(([k]) => k), "E-Mail ungültig"].map(esc).join(";")];
let nWeb = 0, nMail = 0, nPers = 0; const nStatus = {};
for (const r of roh.slice(1)) {
  const firma = BESTAETIGT.has(v(r, "match")) && v(r, "impFirma") ? v(r, "impFirma") : v(r, "firma");
  let anrede = v(r, "anrede"), vor = v(r, "vor"), nach = v(r, "nach"), ansprache = v(r, "ansprache");
  if (!angereichert) {                        // scraper list without enrichment: name from the seller page, gender unknown -> neutral
    const teile = v(r, "gf").split(/\s+/).filter(Boolean);
    if (teile.length >= 2) { nach = teile[teile.length - 1]; vor = teile.slice(0, -1).join(" "); }
    anrede = ""; ansprache = "Guten Tag";
  }
  if (!/^Guten Tag (Herr|Frau) \S/.test(ansprache)) { ansprache = "Guten Tag"; anrede = ""; }
  const sid = v(r, "seller");
  const quelle = sid ? `amazon.de Seller ${sid}${v(r, "kat") ? ` · ${v(r, "kat")}` : ""}${v(r, "land") ? ` · ${v(r, "land")}` : ""}` : "eigene Liste";
  // every status that is not a real verdict counts as "Not Run"; a file that already went through this script keeps its invalid addresses
  const schonUngueltig = !v(r, "mail") ? v(r, "ungueltig") : "", mailRoh = v(r, "mail") || schonUngueltig;
  const status = !mailRoh ? "" : schonUngueltig ? "Invalid" : GEPRUEFT.includes(v(r, "mailStatus")) ? v(r, "mailStatus") : "Not Run", mail = status === "Invalid" ? "" : mailRoh;
  const web = v(r, "web") || v(r, "webAnr");
  if (status) nStatus[status] = (nStatus[status] ?? 0) + 1;
  if (web) nWeb++; if (mail) nMail++; if (anrede) nPers++;
  out.push([firma, web, mail, status, anrede, vor, nach, ansprache, quelle, I.seller >= 0 ? "amazon" : "eigene-liste",
    ...rest.map(([, i]) => r[i] ?? ""), status === "Invalid" ? mailRoh : ""].map(esc).join(";"));
}
writeFileSync(CSV_OUT + ".tmp", "﻿" + out.join("\r\n") + "\r\n"); renameSync(CSV_OUT + ".tmp", CSV_OUT);
const n = roh.length - 1, pz = (x) => `${x} (${Math.round((x / n) * 100)} %)`;
console.log(`Standardformat: ${n} Leads · Website ${pz(nWeb)} · E-Mail ${pz(nMail)} · persönliche Ansprache ${pz(nPers)}${angereichert ? "" : " · ohne Anreicherung: Ansprache immer neutral"}`);
console.log(`E-Mail-Prüfung: ${["Safe to Send", "Risky", "Unknown", "Invalid", "Not Run"].filter((k) => nStatus[k]).map((k) => `${k} ${nStatus[k]}`).join(" · ") || "keine Adressen"}`);
if (nStatus["Not Run"]) console.log(`ACHTUNG: ${nStatus["Not Run"]} Adressen sind ungeprüft (Not Run) und dürfen nicht per E-Mail angeschrieben werden. Nachholen: anreicherung.mjs mit SKAEL_API_KEY auf die MASTER-Datei ausführen, dann dieses Skript auf die Datei …_angereichert.csv.`);
console.log(`Datei: ${CSV_OUT}`);
