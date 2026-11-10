"""Offline tests for werkzeuge/videos.py (Skael calls are stubbed)."""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HIER = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("videos", HIER / "werkzeuge" / "videos.py")
videos = importlib.util.module_from_spec(spec)
spec.loader.exec_module(videos)

LEADS = [
    {"externe_id": "A1", "firma": "Alpha GmbH", "website": "https://alpha.example", "domain": "alpha.example",
     "vorname": "Anna", "email": "anna@alpha.example", "telefon": "+49 1", "video_titel": "Video für Anna"},
    {"externe_id": "B2", "firma": "Beta KG", "website": "beta.example", "vorname": ""},
    {"externe_id": "C3", "firma": "Ohne Website", "website": ""},
]


class FakeSkael:
    def __init__(self, kampagne: dict):
        self.kampagne = kampagne
        self.gesendet: list[dict] = []
        self.status = "ready"

    def __call__(self, methode, pfad, daten=None, versuche=4):
        if methode == "GET" and pfad.startswith("/video-campaigns/"):
            return {"data": self.kampagne}
        if methode == "POST" and pfad.endswith("/prospects"):
            self.gesendet.append(daten)
            n = len(self.gesendet)
            return {"id": 100 + n, "token": f"tok{n}", "status": "queued",
                    "landing_page_url": f"https://video.example/v/tok{n}", "thumbnail_url": None}
        if methode == "GET" and pfad.startswith("/video-prospects/"):
            pid = int(pfad.rsplit("/", 1)[1])
            return {"id": pid, "token": f"tok{pid - 100}", "status": self.status,
                    "landing_page_url": f"https://video.example/v/tok{pid - 100}",
                    "thumbnail_url": f"https://video.example/a/tok{pid - 100}/thumbnail.jpg"}
        raise AssertionError((methode, pfad))


class VideosTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        videos.ARBEIT = Path(self.tmp.name)
        self.leads = Path(self.tmp.name) / "leads.json"
        self.leads.write_text(json.dumps(LEADS), encoding="utf-8")
        self.kampagne = {"id": 7, "name": "Test", "recording_path": "r.webm", "recording_duration": 95,
                         "timeline": [{"type": "recording"}, {"type": "screenshot", "track": "screen"}],
                         "custom_domain_id": 1, "webhooks": []}
        self.fake = FakeSkael(self.kampagne)
        videos.anfrage = self.fake

    def tearDown(self):
        self.tmp.cleanup()

    def args(self, **kw):
        base = {"kampagne": 7, "leads": str(self.leads), "ja": False, "max_minuten": 1, "aus": None}
        base.update(kw)
        return argparse.Namespace(**base)

    def test_kosten(self):
        self.assertEqual(videos.kosten_je_video(95), 110)
        self.assertEqual(videos.kosten_je_video(120), 110)
        self.assertEqual(videos.kosten_je_video(136), 165)
        self.assertEqual(videos.kosten_je_video(274), 275)

    def test_screenshot_teil_fehlt_wird_gemeldet(self):
        k = dict(self.kampagne, timeline=[{"type": "recording"}, {"type": "facecam"}])
        meldungen = " ".join(m for _, m in videos.befunde(k))
        self.assertIn("kein Screenshot-Teil", meldungen)

    def test_ohne_ja_wird_nichts_angelegt(self):
        out = io.StringIO()
        with redirect_stdout(out):
            videos.cmd_anlegen(self.args())
        self.assertEqual(self.fake.gesendet, [])
        self.assertIn("2 Videos anzulegen", out.getvalue())
        self.assertIn("220 Credits", out.getvalue())

    def test_keine_kontaktdaten_an_skael_und_kein_doppeltes_anlegen(self):
        with redirect_stdout(io.StringIO()):
            videos.cmd_anlegen(self.args(ja=True))
            videos.cmd_anlegen(self.args(ja=True))  # second run must not create again
        self.assertEqual(len(self.fake.gesendet), 2)
        for d in self.fake.gesendet:
            self.assertNotIn("email", d)
            self.assertNotIn("phone", d)
            self.assertTrue(d["screenshot_url"].startswith("https://"))
            self.assertEqual(d["custom_vars"]["externe_id"], d["dedupe_value"])
        self.assertNotIn("first_name", self.fake.gesendet[1])  # empty first name is omitted

    def test_warten_und_zusammenfuehren(self):
        with redirect_stdout(io.StringIO()):
            videos.cmd_anlegen(self.args(ja=True))
            videos.cmd_warten(self.args())
            videos.cmd_zusammenfuehren(self.args())
        mit = json.loads((Path(self.tmp.name) / "leads_mit_video.json").read_text(encoding="utf-8"))
        self.assertEqual([l["externe_id"] for l in mit], ["A1", "B2"])
        self.assertEqual(mit[0]["video_url"], "https://video.example/embed/tok1")
        self.assertTrue(mit[0]["video_vorschaubild"].endswith("thumbnail.jpg"))
        self.assertEqual(mit[0]["video_titel"], "Video für Anna")
        self.assertEqual(mit[1]["video_titel"], "Video für Beta KG")

    def test_test_legt_genau_eins_an(self):
        with redirect_stdout(io.StringIO()):
            videos.cmd_test(self.args(ja=True))
        self.assertEqual(len(self.fake.gesendet), 1)

    def test_geheimnis_wird_eingetragen_aber_nie_ausgegeben(self):
        videos.HIER = Path(self.tmp.name)
        env = Path(self.tmp.name) / ".env"
        env.write_text("SKAEL_API_KEY=x\n", encoding="utf-8")
        self.kampagne["webhook_secret"] = "Zq9-WERT-EINS"
        out = io.StringIO()
        with redirect_stdout(out):
            videos.cmd_geheimnis(self.args())
            videos.cmd_geheimnis(self.args())            # same secret again: no duplicate
            self.kampagne["webhook_secret"] = "Zq9-WERT-ZWEI"
            videos.cmd_geheimnis(self.args())
        self.assertNotIn("Zq9-WERT", out.getvalue())
        inhalt = env.read_text(encoding="utf-8")
        self.assertIn("SKAEL_API_KEY=x", inhalt)
        self.assertIn("SKAEL_WEBHOOK_SECRET=Zq9-WERT-EINS,Zq9-WERT-ZWEI", inhalt)
        self.assertEqual(inhalt.count("SKAEL_WEBHOOK_SECRET="), 1)

    def test_nur_facecam_ueber_screenshot_ist_eine_aufnahme(self):
        # real campaign layout: facecam only, laid over the lead's website screenshot
        k = {"recording_path": None, "face_recording_path": "f.webm", "recording_duration": None,
             "face_recording_duration": 117, "timeline": [{"type": "screenshot"}, {"type": "facecam"}]}
        self.assertEqual(videos.aufnahme(k), (True, 117))
        stufen = [s for s, _ in videos.befunde(k)]
        self.assertNotIn("fehler", stufen)
        self.kampagne.update(k)
        with redirect_stdout(io.StringIO()) as out:
            videos.cmd_anlegen(self.args())
        self.assertIn("je 110 Credits", out.getvalue())


    def test_skael_standardfarbe_wird_gemeldet(self):
        k = dict(self.kampagne, settings={"appearance": {"primary_color": "#6366F1"}})
        self.assertIn("Skael-Standardfarbe", " ".join(m for _, m in videos.befunde(k)))
        k = dict(self.kampagne, settings={"appearance": {"primary_color": "#1A7F5A"}})
        self.assertNotIn("Skael-Standardfarbe", " ".join(m for _, m in videos.befunde(k)))

if __name__ == "__main__":
    unittest.main()
