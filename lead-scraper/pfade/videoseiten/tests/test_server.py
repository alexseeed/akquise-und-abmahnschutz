"""Offline test for server/server.py: webhook signatures with several secrets, objections, events."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

HIER = Path(__file__).resolve().parents[1]


def freier_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.sid = "A" * 22
        seite = root / "seiten" / "v" / cls.sid
        seite.mkdir(parents=True)
        (seite / ".meta.json").write_text(json.dumps({"externe_id": "X1"}), encoding="utf-8")
        cls.daten = root / "daten"
        cls.port = freier_port()
        env = dict(os.environ, SEITEN_DIR=str(root / "seiten"), DATEN_DIR=str(cls.daten),
                   SKAEL_WEBHOOK_SECRET="eins, zwei", PORT=str(cls.port))
        cls.proc = subprocess.Popen([sys.executable, str(HIER / "server" / "server.py")], env=env,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", cls.port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(5)
        cls.tmp.cleanup()

    def post(self, pfad, body: bytes, headers=None) -> int:
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{pfad}", data=body, method="POST",
                                     headers=dict({"Content-Type": "application/json"}, **(headers or {})))
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status
        except urllib.error.HTTPError as e:
            return e.code

    def webhook(self, geheimnis: str) -> int:
        body = json.dumps({"event": "video.started", "prospect": {"token": "T", "custom_vars": {"externe_id": "X1"}},
                           "metadata": {"ip": "1.2.3.4"}}).encode()
        ts = str(int(time.time()))
        sig = hmac.new(geheimnis.encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
        return self.post("/webhook/skael", body, {"X-SkaelReach-Signature": sig, "X-SkaelReach-Timestamp": ts})

    def test_mehrere_geheimnisse(self):
        self.assertEqual(self.webhook("eins"), 200)
        self.assertEqual(self.webhook("zwei"), 200)
        self.assertEqual(self.webhook("falsch"), 401)
        zeilen = (self.daten / "skael.jsonl").read_text(encoding="utf-8")
        self.assertNotIn("1.2.3.4", zeilen)      # no IP stored

    def test_messung_nur_bekannte_seiten_und_ereignisse(self):
        self.assertEqual(self.post("/api/m", json.dumps({"seiten_id": self.sid, "ereignis": "ohne_video"}).encode()), 204)
        self.assertEqual(self.post("/api/m", json.dumps({"seiten_id": "B" * 22, "ereignis": "video_geklickt"}).encode()), 204)
        self.assertEqual(self.post("/api/m", json.dumps({"seiten_id": self.sid, "ereignis": "boese"}).encode()), 204)
        zeilen = [json.loads(z) for z in (self.daten / "ereignisse.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([(z["seiten_id"], z["ereignis"]) for z in zeilen], [(self.sid, "ohne_video")])


if __name__ == "__main__":
    unittest.main()
