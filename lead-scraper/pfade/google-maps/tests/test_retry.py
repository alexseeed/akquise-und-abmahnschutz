"""Retry policy of the API clients: temporary errors are retried with exponential backoff,
permanent ones fail at once. Offline: _request and time.sleep are replaced.

    cd pfade/google-maps && python3 -m unittest tests.test_retry -v
"""
from __future__ import annotations

import os
import unittest
from unittest import mock

os.environ.setdefault("SKAEL_API_KEY", "eak_test")

from scraper import clients, pipeline  # noqa: E402
from scraper.clients import ApiError, FindymailClient, OpenAIClient, SkaelClient  # noqa: E402
from scraper.config import CONFIG  # noqa: E402

FERTIG = {"data": {"status": "completed", "output": {"ok": True}}}


class Antworten:
    """Plays back a list of (status, payload) and records each request."""

    def __init__(self, *antworten):
        self.antworten = list(antworten)
        self.anfragen: list[dict] = []

    def __call__(self, url, *, method="POST", headers=None, body=None, timeout=None):
        self.anfragen.append({"url": url, "method": method, "headers": dict(headers or {}), "body": body})
        if not self.antworten:
            raise AssertionError(f"unexpected request {method} {url}")
        return self.antworten.pop(0)


class RetryTest(unittest.TestCase):
    def setUp(self):
        self.pausen: list[float] = []
        self.patches = [
            mock.patch.multiple(CONFIG, max_retries=5, skael_api_key="eak_test", openai_api_key="sk-test",
                                findymail_api_key="fm-test", skael_rate_limit_per_sec=1000.0,
                                openai_rate_limit_per_sec=1000.0, skael_max_wartezeit=600),
            # rate-limiter waits (milliseconds) are not backoff pauses
            mock.patch.object(clients.time, "sleep", side_effect=lambda s: s > 0.05 and self.pausen.append(s)),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def antworten(self, *antworten) -> Antworten:
        fake = Antworten(*antworten)
        patch = mock.patch.object(clients, "_request", fake)
        patch.start()
        self.addCleanup(patch.stop)
        return fake

    # --- Skael -------------------------------------------------------------
    def test_netzwerk_und_5xx_mit_wachsender_pause(self):
        fake = self.antworten((0, {"message": "network error: timed out"}), (503, None), (502, None), (200, FERTIG))
        self.assertEqual(SkaelClient().verify_email("a@b.de"), {"ok": True})
        self.assertEqual(len(fake.anfragen), 4)
        self.assertEqual(len(self.pausen), 3)
        for pause, basis in zip(self.pausen, (2, 4, 8)):
            self.assertGreaterEqual(pause, basis)
            self.assertLessEqual(pause, basis * 1.25)

    def test_429_wartet_laenger(self):
        self.antworten((429, None), (429, None), (200, FERTIG))
        SkaelClient().verify_email("a@b.de")
        self.assertGreaterEqual(self.pausen[0], 5)
        self.assertGreaterEqual(self.pausen[1], 10)

    def test_retry_after_wird_beachtet(self):
        self.antworten((429, {"message": "slow down", "_retry_after": 7}), (200, FERTIG))
        SkaelClient().verify_email("a@b.de")
        self.assertGreaterEqual(self.pausen[0], 7)
        self.assertLess(self.pausen[0], 8.1)

    def test_aufgeben_nach_allen_versuchen(self):
        fake = self.antworten(*[(500, None)] * 5)
        with self.assertRaises(ApiError) as ctx:
            SkaelClient().verify_email("a@b.de")
        self.assertIn("nach 5 Versuchen", str(ctx.exception))
        self.assertEqual(len(fake.anfragen), 5)
        self.assertEqual(len(self.pausen), 4)
        self.assertLessEqual(max(self.pausen), clients.BACKOFF_MAX * 1.25)

    def test_dauerhafte_fehler_sofort(self):
        for status, payload in ((401, {"message": "invalid key"}), (402, {"message": "no credits"}),
                                (422, {"message": "company_name is required"})):
            with self.subTest(status=status):
                fake = self.antworten((status, payload))
                with self.assertRaises(ApiError):
                    SkaelClient().verify_email("a@b.de")
                self.assertEqual(len(fake.anfragen), 1, "no retry for permanent errors")
        self.assertEqual(self.pausen, [])

    def test_fehlgeschlagener_auftrag_mit_vorlaeufiger_ursache(self):
        fehlschlag = {"data": {"status": "failed", "error_message": "Web scraper service kununuJobs failed: HTTP 503"}}
        fake = self.antworten((422, fehlschlag), (200, FERTIG))
        self.assertEqual(SkaelClient().stellen_suche("kununu_jobs", {"query": "Fahrer"}), {"ok": True})
        schluessel = [a["headers"]["Idempotency-Key"] for a in fake.anfragen]
        self.assertNotEqual(schluessel[0], schluessel[1], "new key, otherwise Skael returns the failed job again")

    def test_fehlgeschlagener_auftrag_ohne_vorlaeufige_ursache(self):
        fehlschlag = {"data": {"status": "failed", "error_message": "Unsupported country code XX"}}
        fake = self.antworten((422, fehlschlag))
        with self.assertRaises(ApiError):
            SkaelClient().stellen_suche("kununu_jobs", {"query": "Fahrer"})
        self.assertEqual(len(fake.anfragen), 1)

    def test_abholen_wiederholt_ohne_neu_einzureichen(self):
        fake = self.antworten(
            (202, {"data": {"id": 77, "status": "queued"}}),
            (0, {"message": "network error: connection reset"}),
            (502, None),
            (200, {"data": {"status": "processing"}}),
            (200, FERTIG),
        )
        self.assertEqual(SkaelClient().find_domain("Alpha GmbH", city="Ulm"), {"ok": True})
        self.assertEqual([a["method"] for a in fake.anfragen], ["POST", "GET", "GET", "GET", "GET"],
                         "the job is fetched again, never submitted twice")

    def test_fehlgeschlagen_beim_abholen_vorlaeufig(self):
        fake = self.antworten(
            (202, {"data": {"id": 78, "status": "queued"}}),
            (200, {"data": {"status": "failed", "error_message": "upstream timeout"}}),
            (202, {"data": {"id": 79, "status": "queued"}}),
            (200, FERTIG),
        )
        self.assertEqual(SkaelClient().find_domain("Beta GmbH"), {"ok": True})
        self.assertEqual([a["method"] for a in fake.anfragen], ["POST", "GET", "POST", "GET"])

    def test_antwort_ohne_json_wird_wiederholt(self):
        """Real case from the test balloon (02.11.2026): 200 with a non-JSON body."""
        class Antwort:
            status = 200
            def __init__(self, body): self.body = [body, b""]
            def read1(self, n): return self.body.pop(0)
            def __enter__(self): return self
            def __exit__(self, *a): return False
        bodies = [b"<html>Bad Gateway</html>", b'{"data": {"status": "completed", "output": {"ok": true}}}']
        with mock.patch.object(clients.urllib.request, "urlopen", side_effect=lambda *a, **k: Antwort(bodies.pop(0))):
            self.assertEqual(SkaelClient().verify_email("a@b.de"), {"ok": True})
        self.assertEqual(len(self.pausen), 1)

    def test_dauerhafter_fehler_nennt_die_meldung(self):
        self.antworten((401, {"message": "Invalid API key"}))
        with self.assertRaises(ApiError) as ctx:
            SkaelClient().verify_email("a@b.de")
        self.assertIn("Invalid API key", str(ctx.exception))

    # --- KI und Findymail ---------------------------------------------------
    def test_ki_wiederholt_netzwerkfehler(self):
        antwort = {"choices": [{"message": {"content": "{\"x\": 1}"}}]}
        fake = self.antworten((0, {"message": "network error"}), (503, None), (200, antwort))
        ergebnis = OpenAIClient(provider="openai").complete("hi", json_schema={"type": "object"})
        self.assertEqual(ergebnis, {"x": 1})
        self.assertEqual(len(fake.anfragen), 3)

    def test_ki_dauerhafter_fehler_sofort(self):
        fake = self.antworten((400, {"error": {"message": "bad request"}}))
        with self.assertRaises(ApiError):
            OpenAIClient(provider="openai").complete("hi")
        self.assertEqual(len(fake.anfragen), 1)

    def test_findymail_wiederholt(self):
        fake = self.antworten((503, None), (0, None), (200, {"contact": {"email": "max@alpha.de"}}))
        self.assertEqual(FindymailClient().find_work_email("Max Muster", "alpha.de")["email"], "max@alpha.de")
        self.assertEqual(len(fake.anfragen), 3)

    # --- Pipeline -----------------------------------------------------------
    def test_stufe_bricht_den_lauf_nicht_ab(self):
        def kaputt():
            raise RuntimeError("database is locked")
        with self.assertLogs("scraper.pipeline", level="ERROR") as logs:
            self.assertFalse(pipeline.stufe_sicher("3b", kaputt))
        self.assertIn("Stufe 3b abgebrochen", logs.output[0])
        self.assertTrue(pipeline.stufe_sicher("3c", lambda: None))
        with self.assertRaises(SystemExit):
            pipeline.stufe_sicher("3c", lambda: (_ for _ in ()).throw(SystemExit("ICP fehlt")))


    def test_langsame_stufe_meldet_lebenszeichen(self):
        import threading
        langsam = lambda _: threading.Event().wait(0.3)  # noqa: E731 — time.sleep is patched in setUp
        with mock.patch.object(pipeline, "LEBENSZEICHEN_S", 0.1), \
                self.assertLogs("scraper.pipeline", level="INFO") as logs:
            pipeline._run_parallel([1], langsam, "Stufe 3c")
        self.assertTrue(any("läuft – 0/1 fertig" in z for z in logs.output), logs.output)


if __name__ == "__main__":
    unittest.main()
