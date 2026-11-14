"""Generator: a second run keeps page links and lifetimes stable; lead data cannot break out of <script>."""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HIER = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("generator_ids", HIER / "server" / "generator.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

LEADS = [{"externe_id": "X1", "firma": "Alpha GmbH", "website": "https://alpha.example", "quelle": "intern",
          "quelle_url": "https://alpha.example/impressum", "erfasst_am": "2026-10-20",
          "video_url": "https://video.kunde.example/embed/T1"}]


def erzeuge(leads: Path, ziel: Path) -> dict:
    r = subprocess.run([sys.executable, str(HIER / "server" / "generator.py"), "--vorlage", str(HIER / "vorlage" / "index.html"),
                        "--leads", str(leads), "--ziel", str(ziel), "--basis", "https://angebot.kunde.example", "--probe"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads((ziel / "ergebnis.json").read_text(encoding="utf-8"))


class GeneratorIdTest(unittest.TestCase):
    def test_zweiter_lauf_behaelt_link_und_ablauf(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            leads, ziel = tmp / "leads.json", tmp / "seiten"
            leads.write_text(json.dumps(LEADS), encoding="utf-8")
            erst = erzeuge(leads, ziel)["seiten"][0]
            meta_vorher = json.loads((ziel / "v" / erst["seiten_id"] / ".meta.json").read_text(encoding="utf-8"))

            zweit = erzeuge(leads, ziel)["seiten"][0]
            self.assertEqual(zweit["seiten_id"], erst["seiten_id"])
            self.assertEqual(zweit["link"], erst["link"])
            self.assertEqual(len(list((ziel / "v").iterdir())), 1)
            meta_nachher = json.loads((ziel / "v" / erst["seiten_id"] / ".meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta_nachher["ablauf"], meta_vorher["ablauf"])


class JsLiteralTest(unittest.TestCase):
    def test_keine_spitzen_klammern_oder_ampersand(self):
        daten = {"firma": "</script><script>alert(1)</script> <!-- A&B \u2028"}
        text = generator.js_literal(daten)
        for zeichen in ("<", ">", "&", "\u2028"):
            self.assertNotIn(zeichen, text)
        self.assertEqual(json.loads(text), daten)            # still the same data for the browser


class ProbeOhneVideoTest(unittest.TestCase):
    def test_probe_ohne_video_url_erzeugt_seite(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            leads, ziel = tmp / "leads.json", tmp / "seiten"
            ohne_video = [{k: v for k, v in LEADS[0].items() if k != "video_url"}]
            leads.write_text(json.dumps(ohne_video), encoding="utf-8")
            r = subprocess.run([sys.executable, str(HIER / "server" / "generator.py"), "--vorlage",
                                str(HIER / "vorlage" / "index.html"), "--leads", str(leads),
                                "--ziel", str(ziel), "--basis", "https://angebot.kunde.example", "--probe"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            ergebnis = json.loads((ziel / "ergebnis.json").read_text(encoding="utf-8"))
            self.assertEqual(len(ergebnis["seiten"]), 1)
            self.assertEqual(ergebnis["fehler"], [])


class BasisTest(unittest.TestCase):
    def test_ohne_basis_und_ohne_probe_fehler(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            vorlage = tmp / "vorlage.html"
            vorlage.write_text('<html><head><script>const ABSENDER = "Test";</script></head><body>\n'
                               "/* LEAD:START */\n{}\n/* LEAD:END */\n</body></html>", encoding="utf-8")
            leads = tmp / "leads.json"
            leads.write_text(json.dumps(LEADS), encoding="utf-8")
            r = subprocess.run([sys.executable, str(HIER / "server" / "generator.py"), "--vorlage", str(vorlage),
                                "--leads", str(leads), "--ziel", str(tmp / "x")], capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("--basis", r.stderr)


class AufraeumenTest(unittest.TestCase):
    def test_kaputte_meta_wird_uebersprungen(self):
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp)
            kaputt = ziel / "v" / ("K" * 22)
            kaputt.mkdir(parents=True)
            (kaputt / ".meta.json").write_text("{kaputt", encoding="utf-8")
            alt = ziel / "v" / ("A" * 22)
            alt.mkdir(parents=True)
            (alt / ".meta.json").write_text(json.dumps({"ablauf": "2020-01-01T00:00:00+00:00"}), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                code = generator.cleanup(argparse.Namespace(ziel=str(ziel)))
            self.assertEqual(code, 0)
            self.assertTrue((kaputt / ".meta.json").is_file())
            self.assertFalse(alt.exists())


if __name__ == "__main__":
    unittest.main()
