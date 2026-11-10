"""generator.fetch_thumbnail: browser-like user agent and file suffix from the content type."""
from __future__ import annotations

import email.message
import importlib.util
import tempfile
import unittest
from pathlib import Path

HIER = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("generator_v", HIER / "server" / "generator.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class Antwort:
    def __init__(self, typ: str):
        self.headers = email.message.Message()
        self.headers["Content-Type"] = typ

    def read(self):
        return b"bild"

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class VorschaubildTest(unittest.TestCase):
    def test_jpeg_unter_png_namen_und_eigener_user_agent(self):
        gesehen = {}

        def fake_urlopen(req, timeout=0):
            gesehen["ua"] = req.get_header("User-agent")
            return Antwort("image/jpeg")

        alt = generator.urllib.request.urlopen
        generator.urllib.request.urlopen = fake_urlopen
        try:
            with tempfile.TemporaryDirectory() as tmp:
                name = generator.fetch_thumbnail("https://video.example/a/T/thumbnail.png", Path(tmp) / "vorschau")
                self.assertEqual(name, "vorschau.jpg")
                self.assertEqual((Path(tmp) / "vorschau.jpg").read_bytes(), b"bild")
        finally:
            generator.urllib.request.urlopen = alt
        self.assertNotIn("Python-urllib", gesehen["ua"])


if __name__ == "__main__":
    unittest.main()
