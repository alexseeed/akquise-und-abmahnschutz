"""Community-Sperrliste: Domains, die nach einer Abmahnung wegen Werbe-E-Mails gemeldet wurden.

Beim Export werden alle Leads aussortiert, deren E-Mail- oder Website-Domain (oder eine
Elterndomain davon) auf der Liste steht. Die Liste wird bei jedem Export frisch geladen und
als Kopie in data/sperrliste.txt abgelegt. Ist sie nicht erreichbar, wird die letzte Kopie
verwendet. Gibt es keine, bricht der Export ab (abschaltbar mit SPERRLISTE_PFLICHT=false).

Quelle: SPERRLISTE_URL in .env (Standard: Rohdatei im GitHub-Repository werbemail-sperrliste).
"""
from __future__ import annotations

import re
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from .config import CONFIG, DATA_DIR

CACHE = DATA_DIR / "sperrliste.txt"


def norm_domain(wert: str | None) -> str:
    d = str(wert or "").strip().lower()
    if "@" in d:
        d = d.rsplit("@", 1)[1]
    d = re.sub(r"^[a-z]+://", "", d)
    d = d.split("/")[0].split("?")[0].split("#")[0].split(":")[0].rstrip(".")
    return re.sub(r"^www\d?\.", "", d)


def _parse(text: str) -> set[str]:
    return {z.strip().lower() for z in text.splitlines() if z.strip() and not z.lstrip().startswith("#")}


class Sperrliste:
    def __init__(self, domains: set[str], quelle: str):
        self.domains = domains
        self.quelle = quelle

    def treffer(self, *werte: str | None) -> str | None:
        """Gibt die gesperrte Domain zurück, falls einer der Werte (E-Mail, URL, Domain) betroffen ist."""
        for wert in werte:
            d = norm_domain(wert)
            if not d:
                continue
            teile = d.split(".")
            for i in range(len(teile) - 1):
                kandidat = ".".join(teile[i:])
                if kandidat in self.domains:
                    return kandidat
        return None

    def __len__(self) -> int:
        return len(self.domains)


def konfiguriert() -> bool:
    return bool(CONFIG.sperrliste_url) and "OWNER" not in CONFIG.sperrliste_url


def laden(*, pflicht: bool | None = None) -> Sperrliste | None:
    """Lädt die Liste (online, sonst Kopie). None nur, wenn nicht Pflicht und nichts verfügbar ist."""
    pflicht = CONFIG.sperrliste_pflicht if pflicht is None else pflicht
    fehler = ""
    if konfiguriert():
        try:
            req = urllib.request.Request(CONFIG.sperrliste_url,
                                         headers={"User-Agent": "lead-scraper", "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=30) as r:
                text = r.read().decode("utf-8")
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            CACHE.write_text(text, encoding="utf-8")
            return Sperrliste(_parse(text), f"online ({datetime.now():%d.%m.%Y %H:%M})")
        except (urllib.error.URLError, TimeoutError, UnicodeDecodeError) as e:
            fehler = f"nicht erreichbar ({getattr(e, 'reason', e)})"
    else:
        fehler = "SPERRLISTE_URL nicht gesetzt (enthält noch OWNER)"

    if CACHE.exists():
        stand = datetime.fromtimestamp(CACHE.stat().st_mtime)
        return Sperrliste(_parse(CACHE.read_text(encoding="utf-8")),
                          f"lokale Kopie vom {stand:%d.%m.%Y} – online {fehler}")
    if pflicht:
        raise SystemExit(
            "Die Community-Sperrliste konnte nicht geladen werden: " + fehler + ".\n"
            "Ohne Abgleich wird nicht exportiert. Internetverbindung bzw. SPERRLISTE_URL in .env prüfen.\n"
            "Nur wenn bewusst ohne Abgleich exportiert werden soll: SPERRLISTE_PFLICHT=false setzen."
        )
    return None
