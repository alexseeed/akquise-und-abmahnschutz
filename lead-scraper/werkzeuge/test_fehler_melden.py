"""Offline-Tests für fehler_melden.py — ganz ohne Netz.

    python3 -m unittest discover -s werkzeuge -v   (aus lead-scraper/)
"""
import importlib.util
import io
import json
import os
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

spec = importlib.util.spec_from_file_location(
    "fehler_melden", Path(__file__).resolve().parent / "fehler_melden.py")
fm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fm)


class _Antwort:
    def __init__(self, body: bytes):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FehlerMeldenTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.tmp.name)
        self.env = mock.patch.dict(os.environ)
        self.env.start()
        os.environ.pop("AC_KONTAKT_EMAIL", None)

    def tearDown(self):
        self.env.stop()
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def main(self, argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = fm.main(argv)
        return code, out.getvalue()

    def test_env_werte_werden_geschwaerzt(self):
        Path(".env").write_text('SKAEL_API_KEY=supergeheim12345\nMAX_RETRIES=5\n', encoding="utf-8")
        text = fm.schwaerzen("Fehler mit supergeheim12345 und 5 Versuchen", fm.geheimnisse_lesen(), None)
        self.assertNotIn("supergeheim12345", text)
        self.assertIn("5 Versuchen", text)  # kurze Werte bleiben lesbar

    def test_tokenmuster_werden_geschwaerzt(self):
        text = fm.schwaerzen("sk-abc123XYZ . Bearer abc.def~1 Token " + "A" * 40 + " kurz: abc123", [], None)
        self.assertNotIn("sk-abc123XYZ", text)
        self.assertNotIn("abc.def~1", text)
        self.assertNotIn("A" * 40, text)
        self.assertIn("abc123", text)

    def test_fremde_email_geschwaerzt_kontakt_bleibt(self):
        os.environ["AC_KONTAKT_EMAIL"] = "kunde@beispiel.de"
        kontakt = fm.kontakt_lesen()
        text = fm.schwaerzen("kunde@beispiel.de meldet lead@firma.de", ["lead@firma.de"], kontakt)
        self.assertIn("kunde@beispiel.de", text)
        self.assertNotIn("lead@firma.de", text)

    def test_kontakt_aus_dotenv(self):
        Path(".env").write_text("AC_KONTAKT_EMAIL=aus-env@beispiel.de\n", encoding="utf-8")
        self.assertEqual(fm.kontakt_lesen(), "aus-env@beispiel.de")

    def test_kuerzung_auf_4000(self):
        payload = fm.nutzlast("x" * 5000, None, None, None)
        self.assertEqual(len(payload["text"]), 4000)

    def test_nutzlast_felder(self):
        payload = fm.nutzlast("Fehlertext lang genug", "s" * 300, "k@b.de", None)
        self.assertEqual(payload["skript"], "s" * 200)
        self.assertEqual(payload["kontakt"], "k@b.de")
        self.assertIsNone(payload["version"])
        knapp = fm.nutzlast("Fehlertext lang genug", None, None, "2026-10-28")
        self.assertNotIn("skript", knapp)
        self.assertNotIn("kontakt", knapp)
        self.assertEqual(knapp["version"], "2026-10-28")

    def test_version_aus_changelog(self):
        changelog = Path("CHANGELOG.md")
        changelog.write_text("# Titel\n\n## 2026-10-28 (2)\n\n- was\n", encoding="utf-8")
        self.assertEqual(fm.version_lesen(changelog), "2026-10-28 (2)")
        self.assertIsNone(fm.version_lesen(Path("fehlt.md")))

    def test_netzfehler_exit_0_mit_hinweis(self):
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("kein Netz")):
            code, out = self.main(["--skript", "run", "Fehlermeldung, lang genug für den Versand"])
        self.assertEqual(code, 0)
        self.assertIn("nicht gemeldet", out)

    def test_http_429_exit_0_mit_hinweis(self):
        fehler = urllib.error.HTTPError(fm.MELDUNG_URL, 429, "Too Many Requests", {}, None)
        with mock.patch("urllib.request.urlopen", side_effect=fehler):
            code, out = self.main(["--skript", "run", "Fehlermeldung, lang genug für den Versand"])
        self.assertEqual(code, 0)
        self.assertIn("Zu viele Meldungen", out)

    def test_dry_run_sendet_nicht(self):
        Path(".env").write_text("SKAEL_API_KEY=supergeheim12345\n", encoding="utf-8")
        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("darf nicht senden")) as m:
            code, out = self.main(["--dry-run", "--skript", "run", "Fehler mit supergeheim12345 drin"])
        self.assertEqual(code, 0)
        m.assert_not_called()
        self.assertNotIn("supergeheim12345", out)
        self.assertIn(fm.GESCHWAERZT, out)

    def test_erfolg_zeigt_id(self):
        body = json.dumps({"ok": True, "meldung_id": "abc123"}).encode("utf-8")
        with mock.patch("urllib.request.urlopen", return_value=_Antwort(body)) as m:
            code, out = self.main(["--skript", "run", "Fehlermeldung, lang genug für den Versand"])
        self.assertEqual(code, 0)
        self.assertIn("ID abc123", out)
        self.assertIn("Google Chat", out)
        req, = m.call_args.args
        self.assertEqual(req.get_header("User-agent"), "akquise-fehler-melden/1")
        self.assertEqual(m.call_args.kwargs.get("timeout"), 10)

    def test_text_ueber_stdin(self):
        body = json.dumps({"ok": True, "meldung_id": "s1"}).encode("utf-8")
        stdin = mock.Mock(**{"isatty.return_value": False, "read.return_value": "Fehler aus stdin, lang genug"})
        with mock.patch("urllib.request.urlopen", return_value=_Antwort(body)), mock.patch("sys.stdin", stdin):
            code, out = self.main(["--skript", "run"])
        self.assertEqual(code, 0)
        self.assertIn("ID s1", out)


if __name__ == "__main__":
    unittest.main()
