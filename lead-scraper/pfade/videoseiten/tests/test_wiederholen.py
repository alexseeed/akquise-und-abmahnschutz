"""Retry rule of the Videoseiten path: temporary errors are retried with exponential backoff,
permanent ones fail at once, video polling never resubmits and has a deadline, one lead never stops
the batch. Offline: urllib.request.urlopen and time.sleep are replaced.

    cd pfade/videoseiten && python3 -m unittest tests.test_wiederholen -v
"""
from __future__ import annotations

import argparse
import email.message
import http.client
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

HIER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HIER / "werkzeuge"))
import wiederholen  # noqa: E402


def lade(name: str, pfad: Path):
    spec = importlib.util.spec_from_file_location(name, pfad)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


videos = lade("videos_w", HIER / "werkzeuge" / "videos.py")
hostinger = lade("hostinger_w", HIER / "werkzeuge" / "hostinger.py")
branding = lade("branding_w", HIER / "werkzeuge" / "branding.py")
generator = lade("generator_w", HIER / "server" / "generator.py")
server = lade("server_w", HIER / "server" / "server.py")


# ---------------------------------------------------------------- fakes

class Antwort:
    """Minimal HTTP response: status, headers, read()/read1()."""

    def __init__(self, daten, status: int = 200, typ: str = "application/json"):
        self.roh = daten if isinstance(daten, bytes) else json.dumps(daten).encode()
        self.status = status
        self.headers = email.message.Message()
        self.headers["Content-Type"] = typ
        self._gelesen = False

    def read(self, *_):
        return self.roh

    def read1(self, _n=-1):
        if self._gelesen:
            return b""
        self._gelesen = True
        return self.roh

    def geturl(self):
        return "https://kunde.example/"

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def http_fehler(code: int, daten=None, retry_after: str | None = None) -> urllib.error.HTTPError:
    kopf = email.message.Message()
    if retry_after is not None:
        kopf["Retry-After"] = retry_after
    roh = json.dumps(daten).encode() if daten is not None else b""
    return urllib.error.HTTPError("https://x", code, "x", kopf, io.BytesIO(roh))


class Netz:
    """Fake urlopen: plays back answers per (method, path suffix) or in order; records every request."""

    def __init__(self, *reihe, routen: dict | None = None):
        self.reihe = list(reihe)
        self.routen = {k: list(v) for k, v in (routen or {}).items()}
        self.anfragen: list[tuple[str, str, dict | None]] = []

    def __call__(self, req, timeout=None):
        body = json.loads(req.data) if req.data else None
        self.anfragen.append((req.get_method(), req.full_url, body))
        antwort = None
        for (methode, ende), liste in self.routen.items():
            if req.get_method() == methode and req.full_url.endswith(ende) and liste:
                antwort = liste.pop(0) if len(liste) > 1 else liste[0]
                break
        else:
            if not self.reihe:
                raise AssertionError(f"unexpected request {req.get_method()} {req.full_url}")
            antwort = self.reihe.pop(0)
        if isinstance(antwort, BaseException):
            raise antwort
        return antwort if isinstance(antwort, Antwort) else Antwort(antwort)

    def methoden(self, methode: str) -> list:
        return [a for a in self.anfragen if a[0] == methode]


class Basis(unittest.TestCase):
    """Patches sleep (recording pauses), MAX_RETRIES=5, no jitter (tested in WartezeitTest), silent retry logs."""

    max_retries = "5"

    def setUp(self):
        self.pausen: list[float] = []
        for p in (mock.patch("time.sleep", side_effect=self.pausen.append),
                  mock.patch("random.uniform", lambda a, b: a),
                  mock.patch.dict("os.environ", {"MAX_RETRIES": self.max_retries}),
                  redirect_stderr(io.StringIO())):
            p.__enter__()
            self.addCleanup(p.__exit__, None, None, None)

    def netz(self, *reihe, routen=None) -> Netz:
        fake = Netz(*reihe, routen=routen)
        p = mock.patch("urllib.request.urlopen", fake)
        p.start()
        self.addCleanup(p.stop)
        return fake


# ---------------------------------------------------------------- the rule itself

class WartezeitTest(unittest.TestCase):
    def test_pausen_wachsen_mit_jitter_und_deckel(self):
        for versuch, basis in ((1, 2), (2, 4), (3, 8), (4, 16), (6, 60), (9, 60)):
            for _ in range(20):
                w = wiederholen.wartezeit(versuch, 503)
                self.assertGreaterEqual(w, basis)
                self.assertLessEqual(w, basis * 1.25)

    def test_429_wartet_laenger(self):
        for versuch, basis in ((1, 5), (2, 10), (3, 20), (4, 40)):
            w = wiederholen.wartezeit(versuch, 429)
            self.assertTrue(basis <= w <= basis * 1.25, (versuch, w))

    def test_retry_after_gewinnt_und_ist_gedeckelt(self):
        self.assertTrue(17 <= wiederholen.wartezeit(1, 429, 17) <= 18)
        self.assertLessEqual(wiederholen.wartezeit(1, 503, 3600), 61)

    def test_einordnung(self):
        for status in (0, 408, 425, 429, 500, 502, 503, 504):
            self.assertTrue(wiederholen.voruebergehend(status), status)
        for status in (400, 401, 402, 403, 404, 422):
            self.assertFalse(wiederholen.voruebergehend(status), status)
        self.assertTrue(wiederholen.voruebergehend(422, "upstream timed out, try again"))
        self.assertFalse(wiederholen.voruebergehend(0, "CERTIFICATE_VERIFY_FAILED"))
        self.assertTrue(wiederholen.voruebergehend_text("Rendering timed out"))
        self.assertFalse(wiederholen.voruebergehend_text("no chunks"))

    def test_max_retries_aus_umgebung(self):
        with mock.patch.dict("os.environ", {"MAX_RETRIES": "3"}):
            self.assertEqual(wiederholen.max_versuche(), 3)
        with mock.patch.dict("os.environ", {"MAX_RETRIES": "abc"}), \
                mock.patch.object(wiederholen, "_aus_env_datei", lambda _n: ""):
            self.assertEqual(wiederholen.max_versuche(), 5)


# ---------------------------------------------------------------- Skael (videos.py)

class SkaelBasis(Basis):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for name, wert in (("lade_schluessel", lambda: "eak_test"), ("ARBEIT", Path(self.tmp.name))):
            p = mock.patch.object(videos, name, wert)
            p.start()
            self.addCleanup(p.stop)


class SkaelAnfrageTest(SkaelBasis):
    def test_netzwerk_timeout_und_5xx_mit_wachsender_pause(self):
        netz = self.netz(urllib.error.URLError("connection reset"), TimeoutError("timed out"),
                         http.client.RemoteDisconnected("closed"), http_fehler(503), {"data": {"id": 1}})
        self.assertEqual(videos.anfrage("GET", "/video-prospects/1"), {"data": {"id": 1}})
        self.assertEqual(len(netz.anfragen), 5)
        self.assertEqual([int(p) for p in self.pausen], [2, 4, 8, 16])

    def test_429_laengere_pausen_und_retry_after(self):
        self.netz(http_fehler(429), http_fehler(429), http_fehler(503, retry_after="7"), {"ok": True})
        videos.anfrage("GET", "/x")
        self.assertEqual([int(p) for p in self.pausen], [5, 10, 7])

    def test_kein_json_wird_wiederholt(self):
        netz = self.netz(Antwort(b"<html>502 Bad Gateway</html>", typ="text/html"), {"ok": True})
        self.assertEqual(videos.anfrage("GET", "/x"), {"ok": True})
        self.assertEqual(len(netz.anfragen), 2)

    def test_gibt_nach_max_retries_auf(self):
        with mock.patch.dict("os.environ", {"MAX_RETRIES": "3"}):
            netz = self.netz(*[http_fehler(502)] * 3)
            with self.assertRaises(videos.SkaelFehler) as ctx:
                videos.anfrage("GET", "/video-prospects/1")
        self.assertEqual(len(netz.anfragen), 3)
        self.assertEqual(len(self.pausen), 2)
        self.assertTrue(ctx.exception.voruebergehend)
        self.assertIn("nach 3 Versuchen", str(ctx.exception))

    def test_dauerhafte_fehler_sofort_mit_meldung_der_api(self):
        for code, daten, erwartet in (
                (400, {"message": "screenshot_url is invalid"}, "screenshot_url is invalid"),
                (403, {"message": "Forbidden for this key"}, "Forbidden for this key"),
                (422, {"message": "The given data was invalid.", "errors": {"domain": ["is required"]}}, "domain: is required"),
                (404, {"message": "Prospect not found"}, "Prospect not found")):
            netz = self.netz(http_fehler(code, daten))
            with self.assertRaises(videos.SkaelFehler) as ctx:
                videos.anfrage("POST", "/video-campaigns/7/prospects", {"x": 1})
            self.assertEqual(len(netz.anfragen), 1, code)
            self.assertIn(erwartet, str(ctx.exception))
            self.assertFalse(ctx.exception.voruebergehend)
        self.assertEqual(self.pausen, [])

    def test_401_und_402_beenden_den_lauf_ohne_wiederholung(self):
        for code in (401, 402):
            netz = self.netz(http_fehler(code, {"message": "nope"}))
            with self.assertRaises(SystemExit):
                videos.anfrage("GET", "/video-campaigns/7")
            self.assertEqual(len(netz.anfragen), 1)

    def test_422_mit_voruebergehender_ursache_wird_wiederholt(self):
        netz = self.netz(http_fehler(422, {"message": "Screenshot service unavailable, try again"}), {"id": 5})
        self.assertEqual(videos.anfrage("POST", "/video-campaigns/7/prospects", {"x": 1}), {"id": 5})
        self.assertEqual(len(netz.anfragen), 2)


LEADS = [{"externe_id": f"L{i}", "firma": f"Firma {i}", "website": f"https://l{i}.example"} for i in (1, 2, 3)]
KAMPAGNE = {"data": {"id": 7, "recording_path": "r.webm", "recording_duration": 90, "timeline": [{"type": "screenshot"}]}}


def prospect(pid: int, status: str = "queued", fehler: str | None = None) -> dict:
    return {"data": {"id": pid, "token": f"t{pid}", "status": status, "error_message": fehler,
                     "landing_page_url": f"https://video.example/v/t{pid}", "thumbnail_url": None}}


class SkaelBatchTest(SkaelBasis):
    def args(self, **kw):
        leads = Path(self.tmp.name) / "leads.json"
        leads.write_text(json.dumps(LEADS), encoding="utf-8")
        basis = {"kampagne": 7, "leads": str(leads), "ja": True, "max_minuten": 1, "aus": None}
        basis.update(kw)
        return argparse.Namespace(**basis)

    def test_ein_fehlgeschlagener_lead_stoppt_den_lauf_nicht(self):
        netz = self.netz(KAMPAGNE, prospect(1), http_fehler(400, {"message": "screenshot_url unreachable"}),
                         prospect(3))
        out = io.StringIO()
        with redirect_stdout(out):
            videos.cmd_anlegen(self.args())
        z = videos.zustand_laden(7)
        self.assertEqual(sorted(z["leads"]), ["L1", "L3"])
        self.assertIn("Zusammenfassung: 2 angelegt, 1 fehlgeschlagen", out.getvalue())
        self.assertIn("Firma 2: Skael POST /video-campaigns/7/prospects: HTTP 400 screenshot_url unreachable",
                      out.getvalue())
        # next run: only the open lead is sent again, with its normal dedupe value
        netz.reihe = [KAMPAGNE, prospect(2)]
        with redirect_stdout(io.StringIO()):
            videos.cmd_anlegen(self.args())
        gesendet = [a[2]["dedupe_value"] for a in netz.methoden("POST")]
        self.assertEqual(gesendet, ["L1", "L2", "L3", "L2"])

    def test_skael_ausfall_bricht_nach_drei_leads_ab_statt_zu_haengen(self):
        with mock.patch.dict("os.environ", {"MAX_RETRIES": "2"}):
            netz = self.netz(KAMPAGNE, routen={("POST", "/prospects"): [urllib.error.URLError("down")]})
            leads = LEADS + [{"externe_id": "L4", "firma": "Firma 4", "website": "https://l4.example"}]
            pfad = Path(self.tmp.name) / "viele.json"
            pfad.write_text(json.dumps(leads), encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                videos.cmd_anlegen(self.args(leads=str(pfad)))
        self.assertEqual(len(netz.methoden("POST")), 3 * 2)        # 3 leads x 2 attempts, lead 4 not tried
        self.assertIn("Skael ist gerade nicht erreichbar", out.getvalue())
        self.assertIn("1 nicht versucht", out.getvalue())
        self.assertEqual(videos.zustand_laden(7)["leads"], {})

    def test_voruebergehend_fehlgeschlagenes_video_wird_einmal_neu_angelegt(self):
        videos.zustand_speichern(7, {"kampagne": 7, "leads": {
            "L1": {"prospect_id": 1, "status": "failed", "fehler": "Rendering timed out"},
            "L2": {"prospect_id": 2, "status": "failed", "fehler": "no chunks"},
            "L3": {"prospect_id": 3, "status": "ready", "token": "t3"},
        }})
        netz = self.netz(KAMPAGNE, prospect(11))
        out = io.StringIO()
        with redirect_stdout(out):
            videos.cmd_anlegen(self.args())
        posts = netz.methoden("POST")
        self.assertEqual(len(posts), 1)                             # L2 (permanent cause) and L3 (ready) untouched
        self.assertEqual(posts[0][2]["dedupe_value"], "L1-w1")      # new key, otherwise Skael returns the failed one
        self.assertEqual(posts[0][2]["custom_vars"]["externe_id"], "L1")
        self.assertIn("Davon 1 erneut", out.getvalue())
        eintrag = videos.zustand_laden(7)["leads"]["L1"]
        self.assertEqual((eintrag["prospect_id"], eintrag["neu_angelegt"], eintrag["fruehere_prospect_ids"]), (11, 1, [1]))
        # it is still queued now: a further run must not create it again
        netz.reihe = [KAMPAGNE]
        with redirect_stdout(io.StringIO()):
            videos.cmd_anlegen(self.args())
        self.assertEqual(len(netz.methoden("POST")), 1)

    def test_polling_fragt_bei_fehlern_erneut_ab_und_legt_nie_neu_an(self):
        videos.zustand_speichern(7, {"kampagne": 7, "leads": {"L1": {"prospect_id": 1, "status": "queued"}}})
        netz = self.netz(routen={("GET", "/video-prospects/1"): [
            http_fehler(502), urllib.error.URLError("reset"), Antwort(b"<html>oops</html>"),
            prospect(1, "processing"), prospect(1, "ready")]})
        with redirect_stdout(io.StringIO()):
            videos.cmd_warten(self.args(max_minuten=60))
        self.assertEqual(netz.methoden("POST"), [])
        self.assertEqual(len(netz.methoden("GET")), 5)
        self.assertEqual(videos.zustand_laden(7)["leads"]["L1"]["status"], "ready")
        self.assertEqual([int(p) for p in self.pausen], [2, 4, 8, 30])   # backoff, then the 30 s round pause

    def test_polling_hat_eine_harte_frist(self):
        videos.zustand_speichern(7, {"kampagne": 7, "leads": {"L1": {"prospect_id": 1, "status": "queued"}}})
        uhr = [1_000_000.0]
        netz = self.netz(routen={("GET", "/video-prospects/1"): [prospect(1, "processing")]})

        def schlafen(s):
            self.pausen.append(s)
            uhr[0] += s

        out = io.StringIO()
        with mock.patch("time.time", lambda: uhr[0]), mock.patch("time.sleep", schlafen), redirect_stdout(out):
            videos.cmd_warten(self.args(max_minuten=5))
        self.assertLessEqual(uhr[0] - 1_000_000.0, 5 * 60)
        self.assertLessEqual(len(netz.methoden("GET")), 12)
        self.assertEqual(netz.methoden("POST"), [])
        self.assertIn("Noch nicht alle fertig", out.getvalue())

    def test_polling_bei_dauerausfall_endet_zur_frist(self):
        videos.zustand_speichern(7, {"kampagne": 7, "leads": {
            "L1": {"prospect_id": 1, "status": "queued"}, "L2": {"prospect_id": 2, "status": "queued"}}})
        uhr = [0.0]

        def schlafen(s):
            uhr[0] += s

        with mock.patch.dict("os.environ", {"MAX_RETRIES": "2"}):
            netz = self.netz(routen={("GET", "/video-prospects/1"): [http_fehler(503)],
                                     ("GET", "/video-prospects/2"): [http_fehler(503)]})
            out = io.StringIO()
            with mock.patch("time.time", lambda: uhr[0]), mock.patch("time.sleep", schlafen), redirect_stdout(out):
                videos.cmd_warten(self.args(max_minuten=2))
        # lead 2 is never asked while Skael is down: each round stops after the first unreachable lead
        self.assertFalse([a for a in netz.anfragen if a[1].endswith("/2")])
        self.assertIn("nächsten Runde", out.getvalue())
        self.assertEqual(netz.methoden("POST"), [])

    def test_voruebergehend_fehlgeschlagene_videos_werden_beim_warten_genannt(self):
        videos.zustand_speichern(7, {"kampagne": 7, "leads": {"L1": {"prospect_id": 1, "status": "queued"}}})
        self.netz(routen={("GET", "/video-prospects/1"): [prospect(1, "failed", "Upstream timeout (504)")]})
        out = io.StringIO()
        with redirect_stdout(out):
            videos.cmd_warten(self.args())
        self.assertIn("1 davon vorübergehend fehlgeschlagen", out.getvalue())


# ---------------------------------------------------------------- Hostinger

class HostingerTest(Basis):
    def test_5xx_und_kein_json_werden_wiederholt(self):
        netz = self.netz(http_fehler(504), Antwort(b"<html>maintenance</html>"), http_fehler(503, retry_after="3"),
                         [{"id": 1}])
        self.assertEqual(hostinger.anfrage("GET", "/api/vps/v1/virtual-machines", "tok"), [{"id": 1}])
        self.assertEqual(len(netz.anfragen), 4)
        self.assertEqual([int(p) for p in self.pausen], [2, 4, 3])

    def test_dauerhafte_fehler_sofort_mit_meldung(self):
        netz = self.netz(http_fehler(422, {"message": "Invalid zone", "errors": {"zone.0.name": ["bad"]}}))
        with self.assertRaises(hostinger.Abbruch) as ctx:
            hostinger.anfrage("PUT", "/api/dns/v1/zones/kunde.de", "tok", {"zone": []})
        self.assertEqual(len(netz.anfragen), 1)
        self.assertIn("Invalid zone", ctx.exception.was)
        self.assertIn("zone.0.name: bad", ctx.exception.was)

    def test_gibt_auf_und_meldet_verbindung(self):
        with mock.patch.dict("os.environ", {"MAX_RETRIES": "2"}):
            netz = self.netz(urllib.error.URLError("timed out"), urllib.error.URLError("timed out"))
            with self.assertRaises(hostinger.Abbruch) as ctx:
                hostinger.anfrage("GET", "/api/vps/v1/virtual-machines", "tok")
        self.assertEqual(len(netz.anfragen), 2)
        self.assertIn("Keine Verbindung zu developers.hostinger.com", ctx.exception.was)

    def test_zertifikatsfehler_wird_nicht_wiederholt(self):
        netz = self.netz(urllib.error.URLError("[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed"))
        with self.assertRaises(hostinger.Abbruch) as ctx:
            hostinger.anfrage("GET", "/api/vps/v1/virtual-machines", "tok")
        self.assertEqual(len(netz.anfragen), 1)
        self.assertIn("Zertifikat", ctx.exception.was)


# ---------------------------------------------------------------- customer website (branding.py)

class BrandingTest(Basis):
    def test_voruebergehender_fehler_wird_wiederholt(self):
        netz = self.netz(http_fehler(503), urllib.error.URLError("reset"), Antwort(b"<html></html>", typ="text/html"))
        antwort = branding.http_get("https://kunde.example/")
        self.assertEqual(antwort.daten, b"<html></html>")
        self.assertEqual(len(netz.anfragen), 3)

    def test_404_sofort_und_hoechstens_drei_versuche(self):
        netz = self.netz(http_fehler(404))
        with self.assertRaises(branding.HolFehler) as ctx:
            branding.http_get("https://kunde.example/fehlt.css")
        self.assertEqual((len(netz.anfragen), ctx.exception.code), (1, 404))
        netz = self.netz(*[http.client.IncompleteRead(b"")] * 5)
        with self.assertRaises(branding.HolFehler):
            branding.http_get("https://kunde.example/")
        self.assertEqual(len(netz.anfragen), 3)


# ---------------------------------------------------------------- server side

class GeneratorTest(Basis):
    def test_vorschaubild_wird_kurz_wiederholt(self):
        netz = self.netz(http_fehler(503), Antwort(b"bild", typ="image/jpeg"))
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(generator.fetch_thumbnail("https://v.example/t.png", Path(tmp) / "vorschau"), "vorschau.jpg")
        self.assertEqual(len(netz.anfragen), 2)
        self.assertLess(max(self.pausen), 2)

    def test_dauerhafter_fehler_und_abgerissene_verbindung_geben_oserror(self):
        netz = self.netz(http_fehler(404))
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(OSError):
            generator.fetch_thumbnail("https://v.example/t.png", Path(tmp) / "vorschau")
        self.assertEqual(len(netz.anfragen), 1)
        netz = self.netz(*[http.client.IncompleteRead(b"")] * 3)
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(OSError):
            generator.fetch_thumbnail("https://v.example/t.png", Path(tmp) / "vorschau")
        self.assertEqual(len(netz.anfragen), 3)


class ServerMeldungTest(Basis):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for name, wert in (("DATEN_DIR", Path(self.tmp.name)), ("MELDUNG_URL", "https://n8n.example/hook")):
            p = mock.patch.object(server, name, wert)
            p.start()
            self.addCleanup(p.stop)

    def fehler(self) -> str:
        datei = Path(self.tmp.name) / "fehler.jsonl"
        return datei.read_text(encoding="utf-8") if datei.is_file() else ""

    def test_kurze_wiederholung_dann_zugestellt(self):
        netz = self.netz(http_fehler(502), urllib.error.URLError("reset"), {})
        self.assertTrue(server.melden_senden({"seiten_id": "A" * 22}))
        self.assertEqual(len(netz.anfragen), 3)
        self.assertLess(sum(self.pausen), 5)
        self.assertEqual(self.fehler(), "")

    def test_dauerhafter_fehler_sofort_protokolliert(self):
        netz = self.netz(http_fehler(404))
        self.assertFalse(server.melden_senden({"seiten_id": "A" * 22}))
        self.assertEqual(len(netz.anfragen), 1)
        self.assertIn("HTTP 404", self.fehler())

    def test_hoechstens_drei_versuche(self):
        netz = self.netz(*[TimeoutError("timed out")] * 5)
        self.assertFalse(server.melden_senden({"seiten_id": "A" * 22}))
        self.assertEqual(len(netz.anfragen), 3)
        self.assertIn("nach 3 Versuchen", self.fehler())


if __name__ == "__main__":
    unittest.main()
