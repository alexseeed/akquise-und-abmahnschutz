// Ctrl+C during the Amazon run: no new Bright Data attempt, budget rescue yields to the user abort.
// The scraper itself is not importable (it runs on load), so the wiring is pinned at source level.
//
//   node --test pfade/amazon/tests/
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { abrufen } from "../wiederholen.mjs";

const HIER = dirname(fileURLToPath(import.meta.url));
const scraper = () => readFileSync(join(HIER, "..", "amazon_seller_scraper.mjs"), "utf-8");

test("vorVersuch throwing aborts before the first attempt (no request, error propagates)", async () => {
  let anfragen = 0;
  const echt = globalThis.fetch;
  globalThis.fetch = async () => { anfragen++; throw new Error("unexpected request"); };
  try {
    const stopp = new Error("Abbruch");
    await assert.rejects(abrufen("https://x.test/q", {}, { vorVersuch: () => { throw stopp; }, schlafen: async () => {} }),
      (e) => e === stopp);
    assert.equal(anfragen, 0);
  } finally {
    globalThis.fetch = echt;
  }
});

test("Bright Data retries stop after Ctrl+C (vorVersuch: bdStopp in trigger and snapshot)", () => {
  const quelle = scraper();
  assert.match(quelle, /const bdStopp = \(\) => \{ if \(ABORT\) throw new StopError/);
  assert.equal(quelle.match(/vorVersuch: bdStopp/g)?.length, 2);
});

test("budget rescue yields to a user abort", () => {
  const quelle = scraper();
  const rettung = quelle.slice(quelle.indexOf("async function budgetRettung()"), quelle.indexOf("const STUFEN"));
  assert.match(rettung, /ABORT = USER_ABBRUCH;/);
  assert.match(rettung, /if \(USER_ABBRUCH\) return;/);
  assert.doesNotMatch(rettung, /ABORT = false;/);
});
