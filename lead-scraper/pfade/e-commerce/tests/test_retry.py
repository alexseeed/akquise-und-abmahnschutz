"""Retry policy of the API clients: temporary errors are retried with exponential backoff,
permanent ones fail at once, nothing waits forever. Offline: _request/urlopen and time.sleep
are replaced — no request leaves the machine, nothing costs money.

    cd pfade/e-commerce && python3 -m unittest tests.test_retry -v
"""
from __future__ import annotations

import contextlib
import email.message
import io
import itertools
import logging
import os
import sqlite3
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

TMP = tempfile.mkdtemp()
# Same environment as test_offline (whichever module is imported first builds CONFIG): dead local address,
# no keys, own database, MAX_RETRIES=1 for the pipeline tests. The tests here patch CONFIG themselves.
os.environ.update({
    "DB_PATH": str(Path(TMP) / "test.db"),
    "SPERRLISTE_PFLICHT": "false",
    "SPERRLISTE_URL": "https://example.invalid/OWNER-liste.txt",
    "SKAEL_API_KEY": "", "OPENAI_API_KEY": "", "FINDYMAIL_API_KEY": "",
    "SKAEL_BASE_URL": "http://127.0.0.1:9", "OPENAI_BASE_URL": "http://127.0.0.1:9",
    "MIN_AVR_TRAFFIC": "1", "MIN_MAX_TRAFFIC_3MO": "1", "TRAFFIC_MODE": "OR",
    "USE_FINDYMAIL": "true", "DO_PERSONALISIERUNG": "true", "DO_VIDEO_TITLE": "true",
    "MAX_RETRIES": "1",
})
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ecom import cli, clients, db, pipeline  # noqa: E402
from ecom.clients import ApiError, FindymailClient, OpenAIClient, SkaelClient, ZugangGesperrt  # noqa: E402
from ecom.config import CONFIG  # noqa: E402

FERTIG = {"data": {"status": "completed", "output": {"ok": True}}}
FERTIG_JSON = b'{"data": {"status": "completed", "output": {"ok": true}}}'


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


class Antwort:
    """Stands in for the object urlopen returns: body in chunks, then b''."""

    def __init__(self, *teile, status=200):
        self.teile = [*teile, b""]
        self.status = status

    def read1(self, n):
        return self.teile.pop(0) if self.teile else b""

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class RetryTest(unittest.TestCase):
    def setUp(self):
        self.pausen: list[float] = []
        self.patches = [
            mock.patch.multiple(CONFIG, max_retries=5, skael_api_key="eak_test", openai_api_key="sk-test",
                                findymail_api_key="fm-test", skael_rate_limit_per_sec=1000.0,
                                openai_rate_limit_per_sec=1000.0, skael_max_wartezeit=600, http_timeout=180,
                                skael_base_url="http://127.0.0.1:9", openai_base_url="http://127.0.0.1:9"),
            # rate-limiter waits (milliseconds) are not backoff pauses
            mock.patch.object(clients.time, "sleep", side_effect=lambda s: s > 0.05 and self.pausen.append(s)),
            # nothing in here may reach the network: urlopen fails loudly unless a test replaces it
            mock.patch.object(clients.urllib.request, "urlopen",
                              side_effect=AssertionError("urlopen without a test double")),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()

    def antworten(self, *antworten) -> Antworten:
        fake = Antworten(*antworten)
        patch = mock.patch.object(clients, "_request", fake)
        patch.start()
        self.addCleanup(patch.stop)
        return fake

    def urlopen(self, *ergebnisse):
        """Replaces urlopen: each item is returned, or raised if it is an exception."""
        ergebnisse = list(ergebnisse)
        aufrufe: list = []

        def fake(req, timeout=None):
            aufrufe.append((req.get_method(), req.full_url, timeout))
            ergebnis = ergebnisse.pop(0)
            if isinstance(ergebnis, BaseException):
                raise ergebnis
            return ergebnis
        patch = mock.patch.object(clients.urllib.request, "urlopen", side_effect=fake)
        patch.start()
        self.addCleanup(patch.stop)
        return aufrufe

    # --- policy -------------------------------------------------------------
    def test_wartezeit_waechst_und_ist_gedeckelt(self):
        for versuch, basis in ((1, 2), (2, 4), (3, 8), (4, 16), (10, 60)):
            with self.subTest(versuch=versuch):
                pause = clients.wartezeit(versuch, 503)
                self.assertGreaterEqual(pause, basis)
                self.assertLessEqual(pause, basis * 1.25)
        for versuch, basis in ((1, 5), (2, 10), (3, 20), (4, 40)):
            self.assertGreaterEqual(clients.wartezeit(versuch, 429), basis)
        self.assertLessEqual(clients.wartezeit(1, 429, {"_retry_after": 3600}), clients.BACKOFF_MAX + 1)

    def test_voruebergehend(self):
        for status in (0, 408, 425, 429, 500, 502, 503, 504):
            self.assertTrue(clients.voruebergehend(status), status)
        for status in (400, 401, 402, 403, 404):
            self.assertFalse(clients.voruebergehend(status), status)
        self.assertTrue(clients.voruebergehend(422, {"data": {"error_message": "Upstream service overloaded"}}))
        self.assertFalse(clients.voruebergehend(422, {"message": "domain is required"}))

    # --- Skael -------------------------------------------------------------
    def test_netzwerk_und_5xx_mit_wachsender_pause(self):
        fake = self.antworten((0, {"message": "network error: timed out"}), (503, None), (502, None), (200, FERTIG))
        self.assertEqual(SkaelClient().verify_email("a@b.de"), {"ok": True})
        self.assertEqual(len(fake.anfragen), 4)
        self.assertEqual(len(self.pausen), 3)
        for pause, basis in zip(self.pausen, (2, 4, 8)):
            self.assertGreaterEqual(pause, basis)
            self.assertLessEqual(pause, basis * 1.25)

    def test_408_425_504_werden_wiederholt(self):
        fake = self.antworten((408, None), (425, None), (504, None), (200, FERTIG))
        self.assertEqual(SkaelClient().webtraffic("shop.de"), {"ok": True})
        self.assertEqual(len(fake.anfragen), 4)

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

    def test_retry_after_kopfzeile_wird_gelesen(self):
        kopf = email.message.Message()
        kopf["Retry-After"] = "9"
        fehler = urllib.error.HTTPError("http://127.0.0.1:9/x", 429, "Too Many Requests", kopf,
                                        io.BytesIO(b'{"message": "slow down"}'))
        self.urlopen(fehler, Antwort(FERTIG_JSON))
        self.assertEqual(SkaelClient().verify_email("a@b.de"), {"ok": True})
        self.assertGreaterEqual(self.pausen[0], 9)
        self.assertLess(self.pausen[0], 10.1)

    def test_aufgeben_nach_allen_versuchen(self):
        fake = self.antworten(*[(500, None)] * 5)
        with self.assertRaises(ApiError) as ctx:
            SkaelClient().verify_email("a@b.de")
        self.assertIn("nach 5 Versuchen", str(ctx.exception))
        self.assertEqual(len(fake.anfragen), 5)
        self.assertEqual(len(self.pausen), 4)
        self.assertLessEqual(max(self.pausen), clients.BACKOFF_MAX * 1.25)

    def test_max_retries_steuert_die_versuche(self):
        with mock.patch.object(CONFIG, "max_retries", 2):
            fake = self.antworten((503, None), (503, None))
            with self.assertRaises(ApiError) as ctx:
                SkaelClient().verify_email("a@b.de")
        self.assertEqual(len(fake.anfragen), 2)
        self.assertIn("nach 2 Versuchen", str(ctx.exception))

    def test_dauerhafte_fehler_sofort_mit_meldung(self):
        for status, payload in ((400, {"message": "url must be a valid URL"}), (401, {"message": "Invalid API key"}),
                                (402, {"message": "Insufficient credits"}), (403, {"message": "Forbidden"}),
                                (404, {"message": "Unknown endpoint"}), (422, {"message": "domain is required"})):
            with self.subTest(status=status):
                fake = self.antworten((status, payload))
                with self.assertRaises(ApiError) as ctx:
                    SkaelClient().web_scraper("shop.de")
                self.assertEqual(len(fake.anfragen), 1, "no retry for permanent errors")
                self.assertEqual(ctx.exception.status, status)
                self.assertIn(payload["message"], str(ctx.exception))
        self.assertEqual(self.pausen, [])

    def test_asynchron_mit_idempotency_key(self):
        fake = self.antworten((200, FERTIG))
        SkaelClient().imprint_extractor("shop.de")
        anfrage = fake.anfragen[0]
        self.assertTrue(anfrage["url"].endswith("/api/enrichments/imprint_extractor"))
        self.assertIs(anfrage["body"]["async"], True)
        self.assertEqual(len(anfrage["headers"]["Idempotency-Key"]), 64)

    def test_fehlgeschlagener_auftrag_mit_vorlaeufiger_ursache(self):
        fehlschlag = {"data": {"status": "failed", "error_message": "Upstream scraper failed: HTTP 503"}}
        fake = self.antworten((422, fehlschlag), (200, FERTIG))
        self.assertEqual(SkaelClient().web_scraper("https://shop.de"), {"ok": True})
        schluessel = [a["headers"]["Idempotency-Key"] for a in fake.anfragen]
        self.assertNotEqual(schluessel[0], schluessel[1], "new key, otherwise Skael returns the failed job again")
        self.assertEqual(len(self.pausen), 1)

    def test_fehlgeschlagen_mit_status_200_vorlaeufig(self):
        """`failed` can also come with HTTP 200 (sync answer) — same rule."""
        fehlschlag = {"data": {"status": "failed", "error_message": "connection reset by peer"}}
        fake = self.antworten((200, fehlschlag), (200, FERTIG))
        self.assertEqual(SkaelClient().find_email_person("shop.de", "Max Muster"), {"ok": True})
        self.assertNotEqual(fake.anfragen[0]["headers"]["Idempotency-Key"],
                            fake.anfragen[1]["headers"]["Idempotency-Key"])

    def test_fehlgeschlagener_auftrag_ohne_vorlaeufige_ursache(self):
        fehlschlag = {"data": {"status": "failed", "error_message": "Domain has no imprint page"}}
        fake = self.antworten((422, fehlschlag))
        with self.assertRaises(ApiError) as ctx:
            SkaelClient().imprint_extractor("shop.de")
        self.assertEqual(len(fake.anfragen), 1)
        self.assertIn("no imprint page", str(ctx.exception))

    def test_abholen_wiederholt_ohne_neu_einzureichen(self):
        fake = self.antworten(
            (202, {"data": {"id": 77, "status": "queued"}}),
            (0, {"message": "network error: connection reset"}),
            (502, None),
            (429, None),
            (200, {"data": {"status": "processing"}}),
            (200, FERTIG),
        )
        self.assertEqual(SkaelClient().ai_research_agent("sys", "user", {"type": "object"}), {"ok": True})
        self.assertEqual([a["method"] for a in fake.anfragen], ["POST", "GET", "GET", "GET", "GET", "GET"],
                         "the job is fetched again, never submitted twice")
        self.assertTrue(all(a["url"].startswith("http://127.0.0.1:9/api/enrichments/77?")
                            for a in fake.anfragen[1:]))

    def test_fehlgeschlagen_beim_abholen_vorlaeufig(self):
        fake = self.antworten(
            (202, {"data": {"id": 78, "status": "queued"}}),
            (200, {"data": {"status": "failed", "error_message": "upstream timeout"}}),
            (202, {"data": {"id": 79, "status": "queued"}}),
            (200, FERTIG),
        )
        self.assertEqual(SkaelClient().web_scraper("https://shop.de"), {"ok": True})
        self.assertEqual([a["method"] for a in fake.anfragen], ["POST", "GET", "POST", "GET"])
        self.assertNotEqual(fake.anfragen[0]["headers"]["Idempotency-Key"],
                            fake.anfragen[2]["headers"]["Idempotency-Key"])

    def test_abholen_hat_eine_frist(self):
        """A job that never finishes ends with an error after SKAEL_MAX_WARTEZEIT — no endless wait, no resubmit."""
        uhr = itertools.count(0, 100)       # every look at the clock: 100 s later
        fake = self.antworten((202, {"data": {"id": 80, "status": "queued"}}),
                              *[(200, {"data": {"status": "processing"}})] * 50)
        with mock.patch.object(clients.time, "monotonic", side_effect=lambda: float(next(uhr))):
            with self.assertRaises(ApiError) as ctx:
                SkaelClient().web_scraper("https://shop.de")
        self.assertEqual(ctx.exception.status, 202)
        self.assertIn("noch nicht fertig", str(ctx.exception))
        self.assertEqual([a["method"] for a in fake.anfragen].count("POST"), 1)
        self.assertLess(len(fake.anfragen), 10)

    def test_abholen_gibt_bei_dauerhaftem_fehler_auf(self):
        fake = self.antworten((202, {"data": {"id": 81}}), (401, {"message": "Invalid API key"}))
        with self.assertRaises(ApiError) as ctx:
            SkaelClient().web_scraper("https://shop.de")
        self.assertEqual(ctx.exception.status, 401)
        self.assertEqual(len(fake.anfragen), 2)

    def test_antwort_ohne_json_wird_wiederholt(self):
        self.urlopen(Antwort(b"<html>Bad Gateway</html>"), Antwort(FERTIG_JSON))
        self.assertEqual(SkaelClient().verify_email("a@b.de"), {"ok": True})
        self.assertEqual(len(self.pausen), 1)

    def test_abgerissene_verbindung_wird_wiederholt(self):
        aufrufe = self.urlopen(ConnectionResetError(54, "Connection reset by peer"),
                               TimeoutError("timed out"), Antwort(FERTIG_JSON))
        self.assertEqual(SkaelClient().verify_email("a@b.de"), {"ok": True})
        self.assertEqual(len(aufrufe), 3)
        self.assertTrue(all(timeout and timeout <= 60 for _, _, timeout in aufrufe), "every request has a timeout")

    def test_herzschlag_antwort_endet_nach_gesamtfrist(self):
        """Skael keeps connections open with heartbeat bytes — the overall deadline still ends the read."""
        class Herzschlag(Antwort):
            def read1(self, n):
                return b" "
        uhr = itertools.count(0, 10)
        self.urlopen(Herzschlag())
        with mock.patch.object(clients.time, "monotonic", side_effect=lambda: float(next(uhr))):
            status, data = clients._request("http://127.0.0.1:9/x", timeout=30)
        self.assertEqual(status, 0)
        self.assertIn("Gesamtfrist", data["message"])

    # --- KI und Findymail ---------------------------------------------------
    def test_ki_wiederholt_netzwerkfehler(self):
        antwort = {"choices": [{"message": {"content": "{\"x\": 1}"}}]}
        fake = self.antworten((0, {"message": "network error"}), (503, None), (200, antwort))
        ergebnis = OpenAIClient().complete("hi", json_schema={"type": "object"})
        self.assertEqual(ergebnis, {"x": 1})
        self.assertEqual(len(fake.anfragen), 3)
        self.assertGreaterEqual(self.pausen[1], 4)

    def test_ki_429_wartet_laenger(self):
        antwort = {"choices": [{"message": {"content": "ok"}}]}
        self.antworten((429, {"error": {"code": "rate_limit_exceeded"}}), (200, antwort))
        self.assertEqual(OpenAIClient().complete("hi"), "ok")
        self.assertGreaterEqual(self.pausen[0], 5)

    def test_ki_dauerhafter_fehler_sofort_mit_meldung(self):
        fake = self.antworten((400, {"error": {"message": "Invalid schema for response_format"}}))
        with self.assertRaises(ApiError) as ctx:
            OpenAIClient().complete("hi")
        self.assertEqual(len(fake.anfragen), 1)
        self.assertIn("Invalid schema", str(ctx.exception))

    def test_ki_ohne_guthaben_wird_nicht_wiederholt(self):
        fake = self.antworten((429, {"error": {"code": "insufficient_quota", "type": "insufficient_quota",
                                               "message": "You exceeded your current quota"}}))
        with self.assertRaises(ApiError) as ctx:
            OpenAIClient().complete("hi")
        self.assertEqual(len(fake.anfragen), 1, "an empty account does not refill by waiting")
        with self.assertRaises(ZugangGesperrt):
            clients.pruefe_zugang(ctx.exception, "OpenAI")

    def test_ki_aufgeben_nach_allen_versuchen(self):
        fake = self.antworten(*[(502, None)] * 5)
        with self.assertRaises(ApiError) as ctx:
            OpenAIClient().complete("hi")
        self.assertEqual(len(fake.anfragen), 5)
        self.assertIn("nach 5 Versuchen", str(ctx.exception))

    def test_findymail_wiederholt(self):
        fake = self.antworten((503, None), (0, None), (200, {"contact": {"email": "max@alpha.de"}}))
        self.assertEqual(FindymailClient().find_work_email("Max Muster", "alpha.de")["email"], "max@alpha.de")
        self.assertEqual(len(fake.anfragen), 3)
        # Findymail's own rate limiter (2/s) waits up to 0.5 s — only count the backoff pauses
        self.assertEqual(len([p for p in self.pausen if p >= 1]), 2)

    def test_findymail_dauerhafter_fehler_sofort(self):
        fake = self.antworten((402, {"error": "Not enough credits"}))
        with self.assertRaises(ApiError) as ctx:
            FindymailClient().find_work_email("Max Muster", "alpha.de")
        self.assertEqual(len(fake.anfragen), 1)
        self.assertIn("Not enough credits", str(ctx.exception))


class StufenTest(unittest.TestCase):
    """One row's error does not stop a stage, one stage's error does not stop the run."""

    def test_zeilenfehler_stoppt_die_stufe_nicht(self):
        erledigt: list[int] = []

        def worker(nr):
            if nr == 2:
                raise KeyError("output")
            erledigt.append(nr)
        with self.assertLogs("ecom.pipeline", level="ERROR"):
            pipeline._run_parallel([1, 2, 3], worker, "Test", max_workers=1)
        self.assertEqual(sorted(erledigt), [1, 3])

    def test_stufe_bricht_den_lauf_nicht_ab(self):
        def kaputt():
            raise sqlite3.OperationalError("database is locked")
        with self.assertLogs("ecom.pipeline", level="ERROR") as logs:
            self.assertFalse(pipeline.stufe_sicher("2b", kaputt))
        self.assertIn("Stufe 2b abgebrochen", logs.output[0])
        self.assertTrue(pipeline.stufe_sicher("2c", lambda: None))
        with self.assertRaises(SystemExit):
            pipeline.stufe_sicher("2e", lambda: (_ for _ in ()).throw(SystemExit("Mailtext fehlt")))
        with self.assertRaises(ZugangGesperrt):
            pipeline.stufe_sicher("1b", lambda: (_ for _ in ()).throw(ZugangGesperrt("Schlüssel falsch")))

    def test_naechste_stufe_laeuft_weiter(self):
        gelaufen: list[str] = []

        def kaputt(*_):
            raise RuntimeError("unerwartet")
        with mock.patch.object(pipeline, "stufe1e_uebergabe", kaputt), \
                mock.patch.object(pipeline, "stufe2g_ready", lambda conn: gelaufen.append("2g")), \
                self.assertLogs("ecom.pipeline", level="ERROR"):
            abgebrochen = cli._stufen_ausfuehren(None, {"1e", "2g"}, None, None, None, None)
        self.assertEqual(abgebrochen, ["1e"])
        self.assertEqual(gelaufen, ["2g"])

    def test_run_endet_mit_exit_1_und_hinweis(self):
        ordner = Path(tempfile.mkdtemp(dir=TMP))
        root = logging.getLogger()
        handler, level = list(root.handlers), root.level
        err = io.StringIO()
        with mock.patch.object(CONFIG, "db_path", ordner / "test.db"):
            conn = db.connect()
            db.init(conn)
            db.set_meta(conn, db.META_SHOPPROFIL, "")      # bewusst ohne Profil: 1e darf starten
            conn.close()

            def kaputt(*_):
                raise sqlite3.OperationalError("database is locked")
            try:
                with mock.patch.object(pipeline, "stufe1e_uebergabe", kaputt), \
                        contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err), \
                        self.assertRaises(SystemExit) as ctx:
                    cli.main(["run", "--stage", "1e"])
            finally:
                root.handlers, root.level = handler, level
        self.assertEqual(ctx.exception.code, 1)
        self.assertIn("Stufe 1e wegen eines unerwarteten Fehlers abgebrochen", err.getvalue())
        self.assertIn("denselben run-Befehl erneut", err.getvalue())


if __name__ == "__main__":
    unittest.main()
