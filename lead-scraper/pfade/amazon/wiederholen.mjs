/**
 * RETRY POLICY shared by all scripts of the Amazon path (Oxylabs, Bright Data, Skael).
 * Same rule as pfade/google-maps/scraper/clients.py:
 *
 *   temporary  -> retried with exponential backoff + jitter: network errors / timeouts (status 0), a body that is
 *                 not valid JSON, HTTP 408, 425, 429, 500, 502, 503, 504, and Skael jobs "failed" with a temporary cause
 *   permanent  -> fail at once with the API's own message: 400, 401, 402, 403, 404, 422 validation, Skael "failed"
 *                 with a non-temporary reason
 *
 * Pauses 2/4/8/16 s (429: 5/10/20/40 s), capped at 60 s, plus up to 25 % jitter; a numeric Retry-After wins.
 * Attempts: MAX_RETRIES (default 5). Skael jobs: polling has a hard deadline, temporary polling errors are polled
 * again (never resubmitted: that would pay twice), a job that failed temporarily is resubmitted with a new
 * Idempotency-Key suffix (the same key returns the same failed job for 24 h).
 *
 * Nothing in here reads files or keys; every network call goes through globalThis.fetch (stubbed in the tests).
 */

export const WIEDERHOLBAR = new Set([0, 408, 425, 429, 500, 502, 503, 504]);
export const BACKOFF_START_MS = 2000;       // before the 2nd attempt, then 4, 8, 16 s …
export const BACKOFF_START_429_MS = 5000;   // rate limits need longer: 5, 10, 20, 40 s
export const BACKOFF_MAX_MS = 60000;
// Skael wraps failures of its upstream services as "failed" / 422: only these causes are worth a new job
export const VORUEBERGEHEND_RE = new RegExp(
  "HTTP 5\\d\\d|\\b50[234]\\b|timed? ?out|timeout|temporar|unavailable|overloaded|rate.?limit|too many requests|" +
  "try again|ECONNRESET|connection (reset|refused|aborted|closed)|socket hang up|bad gateway", "i");

const ganzzahl = (v, def) => { const n = Number(String(v ?? "").trim()); return Number.isInteger(n) && n >= 1 ? n : def; };
/** Default number of attempts (env MAX_RETRIES, default 5). Scripts validate the value strictly and pass it explicitly. */
export const MAX_RETRIES = ganzzahl(process.env.MAX_RETRIES, 5);

export const sleep = (ms) => new Promise((r) => setTimeout(r, Math.max(0, ms)));
/** Sleep that ends early once abbrechen() is true (Ctrl+C must not wait for a 60 s backoff). */
export async function schlafen(ms, abbrechen = () => false) {
  const ende = Date.now() + ms;
  while (!abbrechen()) { const rest = ende - Date.now(); if (rest <= 0) return; await sleep(Math.min(250, rest)); }
}

/**
 * Pause in ms before the next attempt. versuch = number of the attempt that just failed (from 1).
 * retryAfterS = numeric Retry-After header in seconds (0/NaN = none).
 */
export function wartezeit(versuch, status, retryAfterS = 0, zufall = Math.random) {
  if (Number.isFinite(retryAfterS) && retryAfterS > 0) return Math.min(retryAfterS * 1000, BACKOFF_MAX_MS) + zufall() * 1000;
  const basis = Math.min((status === 429 ? BACKOFF_START_429_MS : BACKOFF_START_MS) * 2 ** (Math.max(1, versuch) - 1), BACKOFF_MAX_MS);
  return basis + zufall() * basis * 0.25;
}

/** True for errors worth retrying. A 422 / "failed" only counts as temporary when its message says so. */
export function voruebergehend(status, meldung = "") {
  if (WIEDERHOLBAR.has(status)) return true;
  if (status === 422) return VORUEBERGEHEND_RE.test(String(meldung ?? ""));
  return false;
}

/** Error of an API call. voruebergehend = may succeed later (the item stays open), otherwise final for this input. */
export class ApiFehler extends Error {
  constructor(message, { status = 0, meldung = "", voruebergehend = false, phase = null, daten = null } = {}) {
    super(message);
    Object.assign(this, { status, meldung, voruebergehend, phase, daten });
  }
}
/** A Skael job ran and failed for a non-temporary reason (e.g. "Unable to extract impressum data"). */
export class AuftragFehlgeschlagen extends ApiFehler {}

/** Best guess at the API's own error text. */
export function meldungVon(j, text = "") {
  const d = j && typeof j === "object" ? (j.data && typeof j.data === "object" ? j.data : j) : null;
  const m = d?.error_message ?? d?.message ?? j?.message ?? j?.error?.message ?? j?.error ?? j?.detail ?? "";
  return String(typeof m === "string" ? m : JSON.stringify(m) || "").trim() || String(text ?? "").replace(/\s+/g, " ").trim().slice(0, 200);
}

/**
 * One HTTP request, never throws. Result: { status, http, j, text, ra, replay, fehler }.
 *   status 0 = network error, timeout (also while reading the body) or a 2xx body that is not valid JSON
 *   http     = the real HTTP status (0 when no answer arrived)
 *   ra       = numeric Retry-After in seconds (0 = none)
 */
export async function holeJson(url, { timeoutMs = 90000, ...opt } = {}) {
  let r;
  try {
    r = await globalThis.fetch(url, { ...opt, signal: AbortSignal.timeout(timeoutMs) });
    const text = await r.text();
    const raRoh = String(r.headers.get("retry-after") ?? "").trim();
    const basis = { http: r.status, text, ra: /^\d+$/.test(raRoh) ? Number(raRoh) : 0, replay: r.headers.get("idempotent-replayed") === "true" };
    let j = null, gueltig = true;
    try { j = text.trim() ? JSON.parse(text) : null; if (!text.trim()) gueltig = false; } catch { gueltig = false; }
    // e.g. an HTML error page of a proxy with status 200: retried like a network error
    if (!gueltig && r.ok) return { ...basis, status: 0, j: null, fehler: `ungültige Antwort (kein JSON, HTTP ${r.status}): ${text.replace(/\s+/g, " ").slice(0, 120)}` };
    return { ...basis, status: r.status, j, fehler: r.ok ? null : `HTTP ${r.status}` };
  } catch (e) {
    const grund = e?.name === "TimeoutError" || e?.name === "AbortError" ? `Zeitüberschreitung nach ${Math.round(timeoutMs / 1000)} s` : `Netzwerkfehler: ${e?.cause?.code ?? e?.message ?? e}`;
    return { status: 0, http: r?.status ?? 0, j: null, text: "", ra: 0, replay: false, fehler: grund };
  }
}

const beschreibe = (a) => a.status === 0 ? a.fehler ?? "Netzwerkfehler" : a.status === 429 ? "HTTP 429 (Rate-Limit)" : `HTTP ${a.status}`;

/**
 * Request with the retry rule. Returns the answer of the first usable 2xx response, otherwise throws ApiFehler
 * (voruebergehend = true after MAX_RETRIES temporary failures, false for permanent errors).
 *   vorVersuch(n)    before every attempt (budget, rate limit, abort); may throw
 *   nachVersuch(a)   after every answer (usage counting, quota detection); may throw
 *   gueltig(a)       a 2xx answer that is not usable (e.g. "still building") is treated as temporary
 */
export async function abrufen(url, opt = {}, { label = "API", maxVersuche = MAX_RETRIES, timeoutMs = 90000, schlafen: pause = sleep,
  vorVersuch, nachVersuch, gueltig = () => true, zusatzWiederholbar = [], log = () => {} } = {}) {
  let letzte = "";
  for (let n = 1; n <= maxVersuche; n++) {
    await vorVersuch?.(n);
    const a = await holeJson(url, { ...opt, timeoutMs });
    await nachVersuch?.(a);
    const ok = a.status >= 200 && a.status < 300;
    if (ok && gueltig(a)) return a;
    const meldung = ok ? "" : meldungVon(a.j, a.text);
    if (!ok && !voruebergehend(a.status, meldung) && !zusatzWiederholbar.includes(a.status))
      throw new ApiFehler(`${label}: HTTP ${a.status}${meldung ? `: ${meldung.slice(0, 200)}` : ""}`, { status: a.status, meldung, daten: a.j });
    letzte = ok ? `HTTP ${a.status} ohne verwertbaren Inhalt` : beschreibe(a);
    if (n < maxVersuche) {
      const ms = wartezeit(n, a.status, a.ra);
      log(`${label}: ${letzte} — Versuch ${n + 1}/${maxVersuche} in ${(ms / 1000).toFixed(1)} s`);
      await pause(ms);
    }
  }
  throw new ApiFehler(`${label}: ${letzte} — nach ${maxVersuche} Versuchen aufgegeben`, { voruebergehend: true, meldung: letzte });
}

// ---------- Skael (https://api.skael.de/docs/api-guide) ----------
// the envelope normally sits under "data"; a failed operation may come back bare ({id, status: "failed", output: null, ...})
export const umschlag = (j) => (j && typeof j.data === "object" && j.data ? j.data : j && typeof j === "object" && "status" in j && ("output" in j || "id" in j) ? j : null);
const LAEUFT = new Set(["queued", "processing", "pending", "running", "waiting", "timeout"]);

/**
 * Submits a Skael job (async=true + Idempotency-Key) and collects it by long polling.
 * Returns the completed envelope ({id, status, output, credits_cost, …}). Throws
 *   AuftragFehlgeschlagen                      job failed for a non-temporary reason
 *   ApiFehler (voruebergehend: false)          request rejected (400, 422 validation, 404 …); phase "einreichen"
 *   ApiFehler (voruebergehend: true)           still failing after maxVersuche, polling deadline, polling errors
 * Hooks (all optional): takt() rate limit before every request · pruefeStop() may throw to stop · zugang(status)
 * may throw for key/credit errors · eingereicht({schluessel, replay, laeuft}) and abgeschlossen({schluessel, d, ok})
 * for credit booking · wartenS() long-poll seconds.
 */
export async function skaelAbrufen({ basis, pfad, body, schluessel, headers = {}, maxVersuche = MAX_RETRIES, maxWartenS = 600, timeoutMs = 90000,
  schlafen: pause = sleep, uhr = Date.now, takt = async () => {}, pruefeStop = () => {}, zugang = () => {}, wartenS = () => 50,
  eingereicht = () => {}, abgeschlossen = () => {}, log = () => {} }) {
  let key = schluessel, suffix = 0, wiederholungen = 0, letzte = "";
  for (let n = 1; n <= maxVersuche; n++) {
    pruefeStop();
    await takt();
    const a = await holeJson(`${basis}/api/enrichments/${pfad}`, { method: "POST", headers: { ...headers, "Idempotency-Key": key },
      body: JSON.stringify({ ...body, async: true }), timeoutMs });
    zugang(a.status);
    const d = umschlag(a.j), zustand = String(d?.status ?? "").toLowerCase();
    let fehlgeschlagen = null;
    if ((a.status === 200 || a.status === 202) && d && (zustand === "completed" || zustand === "failed" || d.id != null)) {
      const laeuft = zustand !== "completed" && zustand !== "failed";
      eingereicht({ schluessel: key, replay: a.replay, laeuft });
      const erg = !laeuft ? { d, failed: zustand === "failed" } : await skaelAbholen({ basis, pfad, id: d.id, headers, maxVersuche, maxWartenS, timeoutMs, pause, uhr, takt, pruefeStop, zugang, wartenS, log });
      if (!erg.failed) { abgeschlossen({ schluessel: key, d: erg.d, ok: true }); return erg.d; }
      fehlgeschlagen = erg.d;
    } else if (a.status === 422 && zustand === "failed") {
      eingereicht({ schluessel: key, replay: a.replay, laeuft: false });
      fehlgeschlagen = d;
    }
    if (fehlgeschlagen) {
      abgeschlossen({ schluessel: key, d: fehlgeschlagen, ok: false });
      const meldung = String(fehlgeschlagen?.error_message ?? fehlgeschlagen?.message ?? "Auftrag fehlgeschlagen");
      if (!voruebergehend(422, meldung)) throw new AuftragFehlgeschlagen(`${pfad}: ${meldung}`, { status: 422, meldung, daten: fehlgeschlagen });
      letzte = `Auftrag vorübergehend fehlgeschlagen: ${meldung.slice(0, 160)}`;
      // the same key returns the same failed job for 24 h -> a new job needs a new key
      key = `${schluessel.slice(0, 56)}-w${++suffix}`;
      // a replayed failure (earlier start) says nothing about Skael right now: straight on, without using up an attempt
      if (a.replay && ++wiederholungen <= maxVersuche * 4) { n--; continue; }
    } else if (a.status === 404 || a.status === 405) {
      throw new ApiFehler(`Skael-Endpunkt ${pfad} nicht gefunden (HTTP ${a.status})`, { status: a.status, phase: "einreichen", meldung: meldungVon(a.j, a.text) });
    } else if (a.status === 200 || a.status === 202) {
      letzte = `HTTP ${a.status} ohne Auftrag in der Antwort`;
    } else if (voruebergehend(a.status) || a.status === 409) {        // 409: the same key is still being processed
      letzte = beschreibe(a);
    } else {
      const meldung = meldungVon(a.j, a.text);
      throw new ApiFehler(`${pfad}: HTTP ${a.status}${meldung ? `: ${meldung.slice(0, 160)}` : ""}`, { status: a.status, phase: "einreichen", meldung: meldung || `HTTP ${a.status}`, daten: a.j });
    }
    if (n < maxVersuche) {
      const ms = wartezeit(n, a.status, a.ra);
      log(`${pfad}: ${letzte} — Versuch ${n + 1}/${maxVersuche} in ${(ms / 1000).toFixed(1)} s`);
      await pause(ms);
    }
  }
  throw new ApiFehler(`${pfad}: ${letzte} — nach ${maxVersuche} Versuchen aufgegeben`, { voruebergehend: true, phase: "einreichen", meldung: letzte });
}

/**
 * Long polling GET /api/enrichments/{id}?wait=true&wait_time=50 with a hard deadline. HTTP 202 / status queued…
 * means "still running". Temporary errors are polled again with backoff (at most maxVersuche in a row); the job is
 * never resubmitted from here. -> { d, failed }
 */
async function skaelAbholen({ basis, pfad, id, headers, maxVersuche, maxWartenS, timeoutMs, pause, uhr, takt, pruefeStop, zugang, wartenS, log }) {
  const frist = uhr() + maxWartenS * 1000;
  let fehler = 0, kurz = 2000;
  for (let runde = 0; ; runde++) {
    // not submitted again: the next start gets the same (finished) job through the Idempotency-Key
    if (uhr() >= frist) throw new ApiFehler(`${pfad}: nach ${maxWartenS} s noch nicht fertig (Auftrag ${id})`, { voruebergehend: true, phase: "abholen", status: 202 });
    if (runde > 0) pruefeStop();          // a submitted job is charged anyway: it is collected once even while stopping
    await takt();
    const start = uhr();
    const a = await holeJson(`${basis}/api/enrichments/${id}?wait=true&wait_time=${wartenS()}`, { method: "GET", headers, timeoutMs });
    zugang(a.status);
    const d = umschlag(a.j), zustand = String(d?.status ?? "").toLowerCase();
    if (zustand === "failed" || a.status === 422) return { d, failed: true };
    if (a.status === 200 && d && (zustand === "completed" || (zustand === "" && d.output))) return { d, failed: false };
    if (a.status === 202 || (a.status === 200 && LAEUFT.has(zustand))) {
      fehler = 0;
      // came back at once instead of waiting: short pause instead of hammering the API
      if (uhr() - start < 5000) { await pause(Math.min(kurz, Math.max(0, frist - uhr()))); kurz = Math.min(kurz * 1.5, 15000); }
      continue;
    }
    if (voruebergehend(a.status) || a.status === 200) {
      const grund = a.status === 200 ? "Antwort ohne lesbaren Status" : beschreibe(a);
      if (++fehler > maxVersuche) throw new ApiFehler(`${pfad}: Abholen von Auftrag ${id} ${fehler}× in Folge fehlgeschlagen (${grund}) — bleibt offen`, { voruebergehend: true, phase: "abholen", status: a.status });
      const ms = Math.min(wartezeit(fehler, a.status, a.ra), Math.max(0, frist - uhr()));
      log(`${pfad}: Abholen von Auftrag ${id} fehlgeschlagen (${grund}) — erneut in ${(ms / 1000).toFixed(1)} s`);
      await pause(ms);
      continue;
    }
    const meldung = meldungVon(a.j, a.text);
    throw new ApiFehler(`${pfad}: Abholen von Auftrag ${id} fehlgeschlagen (HTTP ${a.status}${meldung ? `: ${meldung.slice(0, 160)}` : ""})`, { voruebergehend: true, phase: "abholen", status: a.status, meldung });
  }
}
