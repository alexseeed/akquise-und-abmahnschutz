#!/usr/bin/env python3
"""Shared retry rule for the werkzeuge scripts (Skael, Hostinger, customer websites).

Temporary errors are retried with exponential backoff and jitter: network errors, timeouts,
connection resets, a body that is not valid JSON, HTTP 408/425/429/500/502/503/504, and Skael
jobs that failed with a temporary cause (5xx, timeout, unavailable, overloaded, rate limit …).
Permanent errors (400, 401, 402, 403, 404, 422 validation) fail at once.

Pauses 2/4/8/16 s (429: 5/10/20/40 s), capped at 60 s, plus up to 25 % jitter; a numeric
Retry-After header wins. Attempts: MAX_RETRIES from the environment or pfade/videoseiten/.env,
default 5. Same rule as pfade/google-maps/scraper/clients.py. Standard library only.
"""
from __future__ import annotations

import http.client
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from collections import namedtuple
from pathlib import Path
from typing import Any, Callable

HIER = Path(__file__).resolve().parents[1]          # pfade/videoseiten

#   status 0 = network error / timeout / connection dropped / invalid JSON (see http_json)
WIEDERHOLBAR = frozenset({0, 408, 425, 429, 500, 502, 503, 504})
BACKOFF_START = 2.0       # seconds before the 2nd attempt, then 4, 8, 16 … (capped)
BACKOFF_START_429 = 5.0   # rate limits need longer: 5, 10, 20, 40 s
BACKOFF_MAX = 60.0
STANDARD_VERSUCHE = 5

# Skael reports failures of its upstream services as 422 / status "failed": retry those that are temporary
_VORUEBERGEHEND = re.compile(
    r"HTTP 5\d\d|\b50[234]\b|timed? ?out|timeout|temporar|unavailable|overloaded|rate.?limit|"
    r"try again|ECONNRESET|connection (reset|refused|aborted)|bad gateway", re.IGNORECASE)
# Network errors that waiting does not fix
_DAUERHAFT_NETZ = re.compile(r"CERTIFICATE_VERIFY_FAILED|certificate verify failed|unknown url type", re.IGNORECASE)

Ergebnis = namedtuple("Ergebnis", "status daten meldung retry_after versuche", defaults=(None, 1))


def _aus_env_datei(name: str) -> str:
    env = HIER / ".env"
    try:
        zeilen = env.read_text(encoding="utf-8-sig").splitlines() if env.is_file() else []
    except OSError:
        return ""
    for zeile in zeilen:
        zeile = zeile.strip()
        if zeile.startswith("export "):
            zeile = zeile[7:].lstrip()
        if zeile.startswith(name + "="):
            return zeile.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def max_versuche() -> int:
    """Number of attempts per call: MAX_RETRIES (environment first, then .env), default 5, 1–20."""
    wert = os.environ.get("MAX_RETRIES") or _aus_env_datei("MAX_RETRIES")
    try:
        return max(1, min(int(str(wert).strip()), 20))
    except (TypeError, ValueError):
        return STANDARD_VERSUCHE


def wartezeit(versuch: int, status: int, retry_after: float | None = None) -> float:
    """Pause before the next attempt (versuch = number of the attempt that just failed, from 1)."""
    if retry_after is not None:
        try:
            return min(float(retry_after), BACKOFF_MAX) + random.uniform(0, 1.0)
        except (TypeError, ValueError):
            pass
    start = BACKOFF_START_429 if status == 429 else BACKOFF_START
    basis = min(start * 2 ** (versuch - 1), BACKOFF_MAX)
    return basis + random.uniform(0, basis * 0.25)


def voruebergehend_text(text: str) -> bool:
    """True if an error text (e.g. Skael's error_message of a failed video) names a temporary cause."""
    return bool(_VORUEBERGEHEND.search(text or ""))


def voruebergehend(status: int, meldung: str = "") -> bool:
    """True for errors worth retrying: network, timeouts, invalid JSON, 408/425/429/5xx, 422 with a temporary cause."""
    if status == 0:
        return not _DAUERHAFT_NETZ.search(meldung or "")
    if status in WIEDERHOLBAR:
        return True
    if status == 422:
        return voruebergehend_text(meldung)
    return False


def retry_after_aus(kopf: Any) -> int | None:
    wert = kopf.get("Retry-After") if kopf is not None else None
    wert = str(wert or "").strip()
    return int(wert) if wert.isdigit() else None


def meldung_aus(daten: Any) -> str:
    """The API's own error message from a JSON error body (Skael, Hostinger) or a text body."""
    if daten is None:
        return ""
    if not isinstance(daten, dict):
        return str(daten).strip()[:300]
    text = ""
    inner = daten.get("data") if isinstance(daten.get("data"), dict) else {}
    for quelle in (inner, daten):
        for schluessel in ("error_message", "message", "error", "detail"):
            wert = quelle.get(schluessel)
            if isinstance(wert, dict):
                wert = wert.get("message") or json.dumps(wert, ensure_ascii=False)
            if wert:
                text = str(wert)
                break
        if text:
            break
    fehler = daten.get("errors")
    if isinstance(fehler, dict) and fehler:
        teile = "; ".join(f"{k}: {' '.join(map(str, v)) if isinstance(v, list) else v}" for k, v in fehler.items())
        text = f"{text} – {teile}" if text else teile
    return text[:300]


def http_json(url: str, methode: str = "GET", kopf: dict | None = None, daten: Any = None,
              timeout: float = 60) -> Ergebnis:
    """One HTTP request to a JSON API. Never raises for network problems.

    Network errors, timeouts, dropped connections and a 2xx body that is not JSON (e.g. a proxy's
    HTML error page) are returned as status 0, so the retry loop treats them as temporary.
    """
    body = json.dumps(daten).encode("utf-8") if daten is not None else None
    req = urllib.request.Request(url, data=body, method=methode, headers=dict(kopf or {}))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed https hosts)
            status = getattr(resp, "status", None) or 200
            if hasattr(resp, "read1"):
                # Read in chunks with an overall deadline: a server that keeps the connection open with
                # heartbeat bytes would never trip the socket timeout.
                ende = time.monotonic() + timeout
                teile: list[bytes] = []
                while True:
                    if time.monotonic() > ende:
                        return Ergebnis(0, None, f"Gesamtfrist {timeout:.0f} s überschritten")
                    stueck = resp.read1(65536)
                    if not stueck:
                        break
                    teile.append(stueck)
                roh = b"".join(teile)
            else:
                roh = resp.read()
        text = roh.decode("utf-8", errors="replace").strip()
        if not text:
            return Ergebnis(status, {}, "")
        try:
            return Ergebnis(status, json.loads(text), "")
        except json.JSONDecodeError:
            return Ergebnis(0, None, f"ungültige Antwort (kein JSON, HTTP {status}): {text[:120]}")
    except urllib.error.HTTPError as exc:
        try:
            roh = exc.read().decode("utf-8", errors="replace")
        except (OSError, http.client.HTTPException):
            roh = ""
        try:
            inhalt: Any = json.loads(roh) if roh.strip() else None
        except json.JSONDecodeError:
            inhalt = roh.strip()[:300] or None
        return Ergebnis(exc.code, inhalt, meldung_aus(inhalt), retry_after_aus(exc.headers))
    except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as exc:
        # also IncompleteRead / RemoteDisconnected (raised outside urlopen's own URLError wrapping)
        return Ergebnis(0, None, f"Netzwerkfehler: {getattr(exc, 'reason', None) or exc}")


def _grund(erg: Ergebnis) -> str:
    if erg.status == 0:
        return erg.meldung or "Netzwerkfehler"
    if erg.status == 429:
        return "HTTP 429 (zu viele Anfragen)"
    return f"HTTP {erg.status}" + (f" ({erg.meldung[:120]})" if erg.meldung else "")


def _melden(text: str) -> None:
    print(text, file=sys.stderr)


def wiederholen(einmal: Callable[[], Ergebnis], *, was: str, versuche: int | None = None,
                ausgabe: Callable[[str], None] = _melden) -> Ergebnis:
    """Calls einmal() until it succeeds, fails permanently or the attempts are used up.

    Returns the last Ergebnis (with .versuche = attempts made); the caller turns it into its own
    error message. Never loops endlessly: at most `versuche` (default MAX_RETRIES) calls.
    """
    anzahl = versuche or max_versuche()
    erg = Ergebnis(0, None, "kein Versuch")
    for versuch in range(1, anzahl + 1):
        erg = einmal()._replace(versuche=versuch)
        if 200 <= erg.status < 300 or not voruebergehend(erg.status, erg.meldung):
            return erg
        if versuch < anzahl:
            pause = wartezeit(versuch, erg.status, erg.retry_after)
            ausgabe(f"  … {was}: {_grund(erg)} – neuer Versuch {versuch + 1}/{anzahl} in {pause:.0f} s")
            time.sleep(pause)
    return erg
