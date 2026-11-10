// Retry policy of the Amazon path (wiederholen.mjs). Offline: globalThis.fetch and the sleep function are stubbed,
// nothing goes over the network and nothing is paid.
//
//   node --test pfade/amazon/tests/
import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { abrufen, holeJson, skaelAbrufen, wartezeit, voruebergehend, ApiFehler, AuftragFehlgeschlagen } from "../wiederholen.mjs";

const echtesFetch = globalThis.fetch;
let anfragen, antworten, pausen, uhr;

// plays back a list of answers: { status, body, headers } | Error (fetch throws) | function(url, opt) -> one of these
function spiele(...liste) { antworten = liste; }
beforeEach(() => {
  anfragen = []; antworten = []; pausen = []; uhr = { t: 1_000_000, jeAnfrage: 0 };
  globalThis.fetch = async (url, opt = {}) => {
    anfragen.push({ url: String(url), method: opt.method ?? "GET", headers: { ...(opt.headers ?? {}) }, body: opt.body });
    if (!antworten.length) throw new Error(`unexpected request ${opt.method ?? "GET"} ${url}`);
    let a = antworten.shift();
    if (typeof a === "function") a = a(url, opt);
    uhr.t += uhr.jeAnfrage;
    if (a instanceof Error) throw a;
    const body = typeof a.body === "string" ? a.body : a.body === undefined ? "" : JSON.stringify(a.body);
    return new Response(body, { status: a.status ?? 200, headers: a.headers ?? {} });
  };
});
afterEach(() => { globalThis.fetch = echtesFetch; });
const schlafen = async (ms) => { pausen.push(ms); uhr.t += ms; };
const zwischen = (wert, min, max) => assert.ok(wert >= min && wert <= max, `${wert} not in [${min}, ${max}]`);
const netzwerkFehler = () => Object.assign(new TypeError("fetch failed"), { cause: { code: "ECONNRESET" } });
const OK = { status: 200, body: { results: [{ content: { ok: true } }] } };

// ---------- backoff ----------
test("wartezeit: 2/4/8/16 s, 429 5/10/20/40 s, capped at 60 s, jitter up to 25 %", () => {
  for (const [v, basis] of [[1, 2000], [2, 4000], [3, 8000], [4, 16000], [5, 32000], [6, 60000], [9, 60000]]) {
    assert.equal(wartezeit(v, 503, 0, () => 0), basis);
    assert.equal(wartezeit(v, 503, 0, () => 1), basis * 1.25);
  }
  for (const [v, basis] of [[1, 5000], [2, 10000], [3, 20000], [4, 40000], [5, 60000]]) assert.equal(wartezeit(v, 429, 0, () => 0), basis);
  assert.equal(wartezeit(1, 429, 7, () => 0), 7000);              // numeric Retry-After wins
  assert.equal(wartezeit(1, 503, 600, () => 0), 60000);           // … but is capped as well
});

test("voruebergehend: classification of status codes and Skael failure messages", () => {
  for (const s of [0, 408, 425, 429, 500, 502, 503, 504]) assert.equal(voruebergehend(s), true, `HTTP ${s}`);
  for (const s of [400, 401, 402, 403, 404, 422]) assert.equal(voruebergehend(s), false, `HTTP ${s}`);
  for (const m of ["Upstream returned HTTP 503", "Request timed out", "service unavailable", "model overloaded", "rate limit exceeded", "please try again", "ECONNRESET"])
    assert.equal(voruebergehend(422, m), true, m);
  for (const m of ["Unable to extract impressum data", "invalid domain", ""]) assert.equal(voruebergehend(422, m), false, m);
});

// ---------- generic requests (Oxylabs, Bright Data) ----------
test("temporary errors are retried with growing pauses", async () => {
  spiele({ status: 503, body: "Service Unavailable" }, netzwerkFehler(), { status: 502, body: "<html>bad gateway</html>" }, OK);
  const a = await abrufen("https://x.test/q", { method: "POST" }, { maxVersuche: 5, schlafen });
  assert.equal(a.status, 200);
  assert.equal(anfragen.length, 4);
  assert.equal(pausen.length, 3);
  zwischen(pausen[0], 2000, 2500); zwischen(pausen[1], 4000, 5000); zwischen(pausen[2], 8000, 10000);
});

test("429 waits longer than other errors", async () => {
  spiele({ status: 429 }, { status: 429 }, OK);
  await abrufen("https://x.test/q", {}, { maxVersuche: 5, schlafen });
  zwischen(pausen[0], 5000, 6250); zwischen(pausen[1], 10000, 12500);
});

test("a numeric Retry-After header is honoured", async () => {
  spiele({ status: 429, headers: { "Retry-After": "7" } }, { status: 503, headers: { "Retry-After": "3" } }, OK);
  await abrufen("https://x.test/q", {}, { maxVersuche: 5, schlafen });
  zwischen(pausen[0], 7000, 8000); zwischen(pausen[1], 3000, 4000);
});

test("gives up after MAX_RETRIES attempts with a temporary ApiFehler", async () => {
  spiele(...Array.from({ length: 5 }, () => ({ status: 500, body: { message: "boom" } })));
  await assert.rejects(abrufen("https://x.test/q", {}, { label: "Oxylabs", maxVersuche: 5, schlafen }),
    (e) => e instanceof ApiFehler && e.voruebergehend && /nach 5 Versuchen/.test(e.message));
  assert.equal(anfragen.length, 5);
  assert.equal(pausen.length, 4);
});

test("permanent errors fail at once with the API's own message", async () => {
  for (const [status, body] of [[400, { message: "invalid query" }], [401, { error: "bad token" }], [402, "no credits"], [403, { message: "forbidden" }],
    [404, { detail: "not found" }], [422, { message: "domain must be a hostname" }]]) {
    anfragen = []; pausen = [];
    spiele({ status, body });
    await assert.rejects(abrufen("https://x.test/q", {}, { label: "API", maxVersuche: 5, schlafen }), (e) => {
      assert.ok(e instanceof ApiFehler); assert.equal(e.voruebergehend, false); assert.equal(e.status, status);
      assert.match(e.message, new RegExp(`HTTP ${status}: \\S`)); return true;
    });
    assert.equal(anfragen.length, 1, `HTTP ${status} must not be retried`);
    assert.equal(pausen.length, 0);
  }
});

test("a 2xx body that is not valid JSON is retried", async () => {
  spiele({ status: 200, body: "<html>proxy error</html>" }, { status: 200, body: "" }, OK);
  const a = await abrufen("https://x.test/q", {}, { maxVersuche: 5, schlafen });
  assert.deepEqual(a.j, OK.body);
  assert.equal(anfragen.length, 3);
});

test("holeJson never throws: timeouts and network errors become status 0", async () => {
  spiele(Object.assign(new Error("aborted"), { name: "TimeoutError" }), netzwerkFehler());
  const a = await holeJson("https://x.test/q", { timeoutMs: 1000 });
  assert.equal(a.status, 0); assert.match(a.fehler, /Zeitüberschreitung/);
  const b = await holeJson("https://x.test/q");
  assert.equal(b.status, 0); assert.match(b.fehler, /ECONNRESET/);
});

test("a 2xx answer that is not usable yet (gueltig) counts as temporary", async () => {
  spiele({ status: 202, body: { status: "building" } }, { status: 200, body: [{ seller_id: "A1" }] });
  const a = await abrufen("https://x.test/snap", {}, { maxVersuche: 5, schlafen, gueltig: (x) => Array.isArray(x.j) });
  assert.deepEqual(a.j, [{ seller_id: "A1" }]);
  assert.equal(pausen.length, 1);
});

test("MAX_RETRIES comes from the environment (default 5)", async () => {
  const alt = process.env.MAX_RETRIES;
  try {
    delete process.env.MAX_RETRIES;
    assert.equal((await import("../wiederholen.mjs?standard")).MAX_RETRIES, 5);
    process.env.MAX_RETRIES = "3";
    assert.equal((await import("../wiederholen.mjs?drei")).MAX_RETRIES, 3);
  } finally { if (alt === undefined) delete process.env.MAX_RETRIES; else process.env.MAX_RETRIES = alt; }
});

// ---------- Skael: async jobs, long polling, Idempotency-Key ----------
const SKAEL = "https://skael.test";
const job = (status, extra = {}) => ({ data: { id: 42, status, output: status === "completed" ? { website: "firma.de" } : null, ...extra } });
const skael = (extra = {}) => {
  const buchungen = [];
  const p = skaelAbrufen({ basis: SKAEL, pfad: "imprint_extractor", body: { domain: "firma.de" }, schluessel: "k".repeat(64), maxVersuche: 5, maxWartenS: 600,
    schlafen, uhr: () => uhr.t, eingereicht: (x) => buchungen.push(["eingereicht", x]), abgeschlossen: (x) => buchungen.push(["abgeschlossen", x]), ...extra });
  return { p, buchungen };
};
const posts = () => anfragen.filter((a) => a.method === "POST");
const gets = () => anfragen.filter((a) => a.method === "GET");

test("Skael: completed job is returned and submitted async with an Idempotency-Key", async () => {
  spiele({ status: 202, body: job("queued") }, { status: 200, body: job("completed", { credits_cost: 5 }) });
  const { p, buchungen } = skael();
  const d = await p;
  assert.deepEqual(d.output, { website: "firma.de" });
  assert.equal(posts().length, 1);
  assert.equal(posts()[0].headers["Idempotency-Key"], "k".repeat(64));
  assert.equal(JSON.parse(posts()[0].body).async, true);
  assert.match(gets()[0].url, /\/api\/enrichments\/42\?wait=true&wait_time=50$/);
  assert.deepEqual(buchungen.map(([art, x]) => [art, x.ok ?? x.laeuft]), [["eingereicht", true], ["abgeschlossen", true]]);
});

test("Skael: a job that failed temporarily is resubmitted with a new Idempotency-Key suffix", async () => {
  spiele({ status: 200, body: job("failed", { error_message: "Upstream timeout after 30s" }) },
    { status: 202, body: job("queued") }, { status: 200, body: job("failed", { error_message: "HTTP 503 from provider" }) },
    { status: 200, body: job("completed") });
  const { p, buchungen } = skael();
  const d = await p;
  assert.equal(d.status, "completed");
  const keys = posts().map((a) => a.headers["Idempotency-Key"]);
  assert.deepEqual(keys, ["k".repeat(64), `${"k".repeat(56)}-w1`, `${"k".repeat(56)}-w2`]);
  assert.equal(new Set(keys).size, 3);
  // each failed job is closed (credit booking) before the next one is submitted
  assert.deepEqual(buchungen.filter(([art]) => art === "abgeschlossen").map(([, x]) => [x.schluessel.slice(-3), x.ok]), [["kkk", false], ["-w1", false], ["-w2", true]]);
  assert.equal(pausen.length, 2);
  zwischen(pausen[0], 2000, 2500);
});

test("Skael: a job that failed for a permanent reason is not resubmitted", async () => {
  spiele({ status: 422, body: job("failed", { error_message: "Unable to extract impressum data" }) });
  await assert.rejects(skael().p, (e) => e instanceof AuftragFehlgeschlagen && /Unable to extract/.test(e.message) && !e.voruebergehend);
  assert.equal(anfragen.length, 1);
});

test("Skael: validation errors and rejected requests fail at once", async () => {
  spiele({ status: 422, body: { message: "The domain field is required." } });
  await assert.rejects(skael().p, (e) => e instanceof ApiFehler && !e.voruebergehend && e.status === 422 && e.phase === "einreichen" && /domain field/.test(e.meldung));
  assert.equal(anfragen.length, 1);
});

test("Skael: temporary submit errors are retried, the same key is reused (no double charge)", async () => {
  spiele(netzwerkFehler(), { status: 503 }, { status: 200, body: "<html>oops</html>" }, { status: 200, body: job("completed") });
  await skael().p;
  assert.equal(posts().length, 4);
  assert.equal(new Set(posts().map((a) => a.headers["Idempotency-Key"])).size, 1);
});

test("Skael: polling errors are polled again with backoff, the job is never resubmitted", async () => {
  spiele({ status: 202, body: job("queued") }, netzwerkFehler(), { status: 503 }, { status: 429 }, { status: 200, body: "not json" },
    { status: 200, body: job("completed") });
  const d = await skael().p;
  assert.equal(d.status, "completed");
  assert.equal(posts().length, 1);
  assert.equal(gets().length, 5);
  assert.equal(pausen.length, 4);
  zwischen(pausen[0], 2000, 2500); zwischen(pausen[1], 4000, 5000); zwischen(pausen[2], 20000, 25000);   // 3rd failure is a 429
});

test("Skael: polling gives up after MAX_RETRIES failures in a row, without resubmitting", async () => {
  spiele({ status: 202, body: job("queued") }, ...Array.from({ length: 6 }, () => ({ status: 502 })));
  await assert.rejects(skael().p, (e) => e instanceof ApiFehler && e.voruebergehend && e.phase === "abholen" && /bleibt offen/.test(e.message));
  assert.equal(posts().length, 1);
  assert.equal(gets().length, 6);
});

test("Skael: polling has a hard deadline (never an endless wait)", async () => {
  uhr.jeAnfrage = 50_000;                                   // every long poll holds the connection for 50 s
  spiele({ status: 202, body: job("queued") }, ...Array.from({ length: 100 }, () => ({ status: 202, body: job("processing") })));
  const start = uhr.t;
  await assert.rejects(skael({ maxWartenS: 120 }).p, (e) => e instanceof ApiFehler && e.voruebergehend && /nach 120 s noch nicht fertig/.test(e.message));
  assert.equal(posts().length, 1);
  assert.equal(gets().length, 3);                           // polls at +50 s, +100 s, +150 s -> deadline
  assert.ok(uhr.t - start <= 120_000 + 2 * 50_000);
});

test("Skael: an immediate 'still running' answer is not polled in a tight loop", async () => {
  spiele({ status: 202, body: job("queued") }, ...Array.from({ length: 200 }, () => ({ status: 200, body: job("processing") })));
  await assert.rejects(skael({ maxWartenS: 60 }).p, /noch nicht fertig/);
  assert.ok(gets().length < 20, `${gets().length} polls`);
  assert.ok(pausen.every((ms) => ms > 0));
});

test("Skael: a replayed failed job (earlier start) is skipped without using up an attempt", async () => {
  const replay = { "idempotent-replayed": "true" };
  spiele({ status: 200, headers: replay, body: job("failed", { error_message: "service unavailable" }) },
    { status: 200, headers: replay, body: job("failed", { error_message: "service unavailable" }) },
    { status: 200, body: job("completed") });
  await skael({ maxVersuche: 1 }).p;
  assert.equal(posts().length, 3);
  assert.equal(pausen.length, 0);
});

test("Skael: hooks for access errors and stop are called and may throw", async () => {
  class Stopp extends Error {}
  spiele({ status: 401, body: { message: "Unauthenticated." } });
  await assert.rejects(skael({ zugang: (s) => { if (s === 401) throw new Stopp("key"); } }).p, Stopp);
  anfragen = [];
  await assert.rejects(skael({ pruefeStop: () => { throw new Stopp("stop"); } }).p, Stopp);
  assert.equal(anfragen.length, 0);
});
