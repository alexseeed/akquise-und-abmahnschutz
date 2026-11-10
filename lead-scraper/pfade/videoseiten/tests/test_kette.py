"""End-to-end offline: lead format -> videos (stubbed Skael) -> generator -> mail list."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HIER = Path(__file__).resolve().parents[1]


def lade(name: str, pfad: Path):
    spec = importlib.util.spec_from_file_location(name, pfad)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


videos = lade("videos_k", HIER / "werkzeuge" / "videos.py")
versand = lade("versand_k", HIER / "werkzeuge" / "versandliste.py")

LEADS = [
    {"externe_id": "ChIJ1", "firma": "Alpha GmbH", "domain": "alpha.example", "website": "https://alpha.example",
     "plz": "12345", "ort": "Musterstadt", "land": "DE", "branche": "Werbeagentur", "anrede": "Frau",
     "vorname": "Anna", "nachname": "Alpha", "position": "Geschäftsführung", "email": "anna@alpha.example",
     "email_typ": "persoenlich", "email_status": "Safe to Send", "telefon": "+49 30 1",
     "quelle": "Google-Maps-Suche nach „Werbeagentur“ in Musterstadt; Kontaktdaten aus dem Impressum",
     "quelle_url": "https://alpha.example/impressum", "erfasst_am": "2026-10-20", "video_titel": "Video für Anna"},
    {"externe_id": "ChIJ2", "firma": "Beta KG", "domain": "beta.example", "website": "https://beta.example",
     "vorname": "", "nachname": "", "email": "info@beta.example", "quelle": "Google-Maps-Suche",
     "quelle_url": "https://beta.example/impressum", "erfasst_am": "2026-10-20"},
]


class Stub:
    def __call__(self, methode, pfad, daten=None, versuche=4):
        if pfad.startswith("/video-campaigns/") and methode == "GET":
            return {"id": 9, "recording_path": "r", "recording_duration": 100, "timeline": [{"type": "screenshot"}]}
        if methode == "POST":
            n = 1 if daten["dedupe_value"] == "ChIJ1" else 2
            return {"id": n, "token": f"T{n}", "status": "queued", "landing_page_url": f"https://video.kunde.example/v/T{n}"}
        if pfad.startswith("/video-prospects/"):
            n = int(pfad.rsplit("/", 1)[1])
            # second video fails: that lead must not get a page
            return {"id": n, "token": f"T{n}", "status": "ready" if n == 1 else "failed",
                    "landing_page_url": f"https://video.kunde.example/v/T{n}", "thumbnail_url": None,
                    "error_message": None if n == 1 else "render failed"}
        raise AssertionError(pfad)


class KetteTest(unittest.TestCase):
    def test_ganze_kette(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            videos.ARBEIT = tmp
            videos.anfrage = Stub()
            leads = tmp / "leads.json"
            leads.write_text(json.dumps(LEADS, ensure_ascii=False), encoding="utf-8")
            a = argparse.Namespace(kampagne=9, leads=str(leads), ja=True, max_minuten=1, aus=None)
            with redirect_stdout(io.StringIO()):
                videos.cmd_anlegen(a)
                videos.cmd_warten(a)
                videos.cmd_zusammenfuehren(a)
            mit_video = tmp / "leads_mit_video.json"
            self.assertEqual([l["externe_id"] for l in json.loads(mit_video.read_text(encoding="utf-8"))], ["ChIJ1"])

            # generator with the neutral template (placeholders allowed via --probe)
            seiten = tmp / "seiten"
            r = subprocess.run([sys.executable, str(HIER / "server" / "generator.py"), "--vorlage", str(HIER / "vorlage" / "index.html"),
                                "--leads", str(mit_video), "--ziel", str(seiten), "--basis", "https://angebot.kunde.example", "--probe"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            ergebnis = json.loads((seiten / "ergebnis.json").read_text(encoding="utf-8"))
            self.assertEqual(len(ergebnis["seiten"]), 1)
            seite = ergebnis["seiten"][0]
            html = (seiten / "v" / seite["seiten_id"] / "index.html").read_text(encoding="utf-8")
            self.assertIn("frame-src https://video.kunde.example", html)
            self.assertNotIn("anna@alpha.example", html)       # contact data never on the page
            self.assertNotIn("+49 30 1", html)
            self.assertNotIn("alpha.example/impressum", html)  # lead source stays internal
            self.assertNotIn("Google-Maps", html)
            self.assertIn("weitere öffentlich zugängliche Quellen", html)  # general Art. 14 source
            self.assertNotIn("Ihre Rechte", html)
            self.assertNotIn("IP-Adresse", html)

            # without --probe the neutral template must be refused (placeholders left)
            r2 = subprocess.run([sys.executable, str(HIER / "server" / "generator.py"), "--vorlage", str(HIER / "vorlage" / "index.html"),
                                 "--leads", str(mit_video), "--ziel", str(tmp / "x")], capture_output=True, text=True)
            self.assertNotEqual(r2.returncode, 0)

            # mail list
            export = tmp / "1_zielgruppe.csv"
            with export.open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["Firmenname", "E-Mail", "Externe ID"])
                w.writerow(["Alpha GmbH", "anna@alpha.example", "ChIJ1"])
                w.writerow(["Beta KG", "info@beta.example", "ChIJ2"])
            with redirect_stdout(io.StringIO()) as out:
                versand.cmd_links(argparse.Namespace(csv=str(export), ergebnis=str(seiten / "ergebnis.json"), aus=None))
            self.assertIn("1 Leads ohne Seite", out.getvalue())
            zeilen = list(csv.DictReader((tmp / "1_zielgruppe_mit_landingpage.csv").read_text(encoding="utf-8-sig").splitlines(), delimiter=";"))
            self.assertEqual(len(zeilen), 1)
            self.assertEqual(zeilen[0]["Landingpage"], seite["link"])
            self.assertEqual(zeilen[0]["Vorschaubild"], "https://angebot.kunde.example/assets/video-vorschau.svg")

    def test_loeschungen(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "w.jsonl").write_text(json.dumps({"zeit": "2026-10-24T10:00:00+00:00", "seiten_id": "x", "externe_id": "ChIJ1"}) + "\n"
                                         + json.dumps({"zeit": "2026-10-24T11:00:00+00:00", "seiten_id": "y", "externe_id": "fremd"}) + "\n",
                                         encoding="utf-8")
            (tmp / "l.json").write_text(json.dumps(LEADS), encoding="utf-8")
            with redirect_stdout(io.StringIO()) as out:
                versand.cmd_loeschungen(argparse.Namespace(datei=str(tmp / "w.jsonl"), leads=str(tmp / "l.json"), aus=None))
            self.assertIn("1 Einträge gehören zu keinem Lead", out.getvalue())
            zeilen = list(csv.DictReader((tmp / "datenloeschungen.csv").read_text(encoding="utf-8-sig").splitlines(), delimiter=";"))
            self.assertEqual(zeilen[0]["E-Mail"], "anna@alpha.example")
            self.assertEqual(zeilen[0]["Datenlöschung am"], "2026-10-24")


if __name__ == "__main__":
    unittest.main()
