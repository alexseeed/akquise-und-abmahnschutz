#!/usr/bin/env python3
"""Small backend behind Caddy for the landing pages. Standard library only.

    POST /api/m               {"seiten_id", "ereignis"}   page events, no IP, no cookies
    POST /api/widerspruch     {"seiten_id"}               objection: page deleted, customer notified
    POST /webhook/skael       Skael webhook (HMAC-SHA256) video events

Everything is appended to JSON-lines files in DATEN_DIR. Configuration via env:
    SEITEN_DIR            folder the pages live in (same as generator --ziel)
    DATEN_DIR             folder for ereignisse.jsonl, widersprueche.jsonl, skael.jsonl
    SKAEL_WEBHOOK_SECRET  Skael webhook secret(s), comma-separated: one per campaign or the org secret
                          (optional; without it webhooks are refused)
    MELDUNG_URL           optional URL (e.g. n8n/Make) that receives every objection as JSON
    PORT                  default 8080, bound to 127.0.0.1 only
"""
from __future__ import annotations

import hashlib
import hmac
import http.client
import json
import os
import random
import re
import shutil
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SEITEN_DIR = Path(os.environ.get("SEITEN_DIR", "/srv/seiten"))
DATEN_DIR = Path(os.environ.get("DATEN_DIR", "/srv/daten"))
SECRETS = [s.strip() for s in os.environ.get("SKAEL_WEBHOOK_SECRET", "").split(",") if s.strip()]
MELDUNG_URL = os.environ.get("MELDUNG_URL", "")
PORT = int(os.environ.get("PORT", "8080"))

SEITEN_ID_RE = re.compile(r"^[A-Za-z0-9]{22}$")
EREIGNISSE = {"seite_geoeffnet", "video_geklickt", "ohne_video", "stimme_geklickt", "termin_geklickt", "widerspruch"}
MAX_BODY = 64 * 1024

# Notification to MELDUNG_URL: sent in a background thread so the visitor's request is answered at once.
# Short retry on purpose (server, standard library only, no queue): 3 attempts, 5 s timeout each,
# pauses 1 s and 2 s (+ jitter), Retry-After up to 5 s. Worst case ~25 s, then the failure goes to
# fehler.jsonl; the objection itself is already stored in widersprueche.jsonl.
WIEDERHOLBAR = {408, 425, 429, 500, 502, 503, 504}
MELDUNG_VERSUCHE = 3
MELDUNG_TIMEOUT = 5
MELDUNG_PAUSE = 1.0
MELDUNG_PAUSE_MAX = 5.0


def jetzt() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def anhaengen(name: str, eintrag: dict) -> None:
    DATEN_DIR.mkdir(parents=True, exist_ok=True)
    with (DATEN_DIR / name).open("a", encoding="utf-8") as f:
        f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")


def seite(sid: str) -> Path | None:
    if not SEITEN_ID_RE.match(sid or ""):
        return None
    p = SEITEN_DIR / "v" / sid
    return p if (p / ".meta.json").is_file() else None


def melden(eintrag: dict) -> None:
    if not MELDUNG_URL:
        return
    threading.Thread(target=melden_senden, args=(eintrag,), daemon=True).start()


def melden_senden(eintrag: dict) -> bool:
    """POST the entry to MELDUNG_URL; retries temporary errors briefly. True if delivered."""
    body = json.dumps(eintrag).encode()
    grund, versuch = "", 0
    for versuch in range(1, MELDUNG_VERSUCHE + 1):
        req = urllib.request.Request(MELDUNG_URL, data=body, headers={"Content-Type": "application/json"})
        retry_after = None
        try:
            with urllib.request.urlopen(req, timeout=MELDUNG_TIMEOUT):  # noqa: S310 (URL set by the operator)
                return True
        except urllib.error.HTTPError as exc:
            grund = f"HTTP {exc.code}"
            if exc.code not in WIEDERHOLBAR:
                break                                   # 4xx: wrong URL or refused, waiting does not help
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
        except (OSError, http.client.HTTPException) as exc:
            grund = f"{type(exc).__name__}: {exc}"
        if versuch < MELDUNG_VERSUCHE:
            if retry_after and retry_after.strip().isdigit():
                pause = min(float(retry_after.strip()), MELDUNG_PAUSE_MAX)
            else:
                pause = MELDUNG_PAUSE * 2 ** (versuch - 1)
                pause += random.uniform(0, pause * 0.25)
            time.sleep(pause)
    try:
        anhaengen("fehler.jsonl", {"zeit": jetzt(), "fehler": f"Meldung nicht zugestellt nach {versuch} Versuchen: {grund}",
                                   "seiten_id": eintrag.get("seiten_id")})
    except OSError:
        pass
    return False


class Handler(BaseHTTPRequestHandler):
    server_version = "seiten"
    sys_version = ""

    def log_message(self, *args) -> None:  # no access log, no IP addresses
        pass

    def antwort(self, code: int, daten: dict | None = None) -> None:
        body = json.dumps(daten or {}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def lesen(self) -> bytes | None:
        laenge = int(self.headers.get("Content-Length") or 0)
        if laenge <= 0 or laenge > MAX_BODY:
            return None
        return self.rfile.read(laenge)

    def do_POST(self) -> None:  # noqa: N802
        roh = self.lesen()
        if roh is None:
            return self.antwort(400)
        if self.path == "/webhook/skael":
            return self.skael(roh)
        try:
            daten = json.loads(roh)
        except ValueError:
            return self.antwort(400)
        sid = str(daten.get("seiten_id") or "")
        if self.path == "/api/m":
            ereignis = daten.get("ereignis")
            if seite(sid) and ereignis in EREIGNISSE:
                anhaengen("ereignisse.jsonl", {"zeit": jetzt(), "seiten_id": sid, "ereignis": ereignis})
            return self.antwort(204)
        if self.path == "/api/widerspruch":
            return self.widerspruch(sid)
        return self.antwort(404)

    def widerspruch(self, sid: str) -> None:
        p = seite(sid)
        if not p:
            return self.antwort(404)
        meta = json.loads((p / ".meta.json").read_text(encoding="utf-8"))
        eintrag = {"zeit": jetzt(), "seiten_id": sid, "externe_id": meta.get("externe_id")}
        anhaengen("widersprueche.jsonl", eintrag)
        shutil.rmtree(p)
        melden({"art": "widerspruch", **eintrag})
        return self.antwort(200, {"ok": True})

    def skael(self, roh: bytes) -> None:
        sig = self.headers.get("X-SkaelReach-Signature", "")
        ts = self.headers.get("X-SkaelReach-Timestamp", "")
        if not SECRETS or not sig or not ts.isdigit() or abs(time.time() - int(ts)) > 300:
            return self.antwort(401)
        gueltig = any(
            hmac.compare_digest(hmac.new(s.encode(), ts.encode() + b"." + roh, hashlib.sha256).hexdigest(), sig)
            for s in SECRETS)
        if not gueltig:
            return self.antwort(401)
        daten = json.loads(roh)
        prospect = daten.get("prospect") or {}
        anhaengen("skael.jsonl", {
            "zeit": jetzt(),
            "ereignis": daten.get("event"),
            "externe_id": (prospect.get("custom_vars") or {}).get("externe_id"),
            "token": prospect.get("token"),
            "prozent": (daten.get("metadata") or {}).get("percent"),
        })
        return self.antwort(200)

    def do_GET(self) -> None:  # noqa: N802
        self.antwort(404)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
