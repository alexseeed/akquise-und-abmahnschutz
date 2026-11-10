"""A second generator run must keep page links and lifetimes stable."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HIER = Path(__file__).resolve().parents[1]

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


if __name__ == "__main__":
    unittest.main()
