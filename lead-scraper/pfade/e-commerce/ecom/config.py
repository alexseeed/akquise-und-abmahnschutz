"""Konfiguration — liest .env und stellt alle Einstellungen zentral bereit.

Standardwerte = Clay-Workbook „Vorlage | ECOM 2.0“ (Tabellen Import und ANREICHERUNG).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
DATA_DIR = ROOT / "data"
EXPORT_DIR = ROOT / "exports"


def _load_dotenv(path: Path = ROOT / ".env") -> None:
    """Minimaler .env-Loader ohne Fremdabhängigkeit.

    UTF-8 mit oder ohne BOM (Windows-Editor); sonst Windows-1252 statt eines Absturzes bei jedem Befehl.
    """
    if not path.exists():
        return
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="cp1252", errors="replace")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "") or default)
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, "") or default)
    except ValueError:
        return default


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on", "ja"}


@dataclass
class Config:
    # --- Zugänge -------------------------------------------------------
    skael_api_key: str = field(default_factory=lambda: os.environ.get("SKAEL_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.environ.get("OPENAI_API_KEY", ""))
    findymail_api_key: str = field(default_factory=lambda: os.environ.get("FINDYMAIL_API_KEY", ""))

    skael_base_url: str = field(default_factory=lambda: os.environ.get("SKAEL_BASE_URL", "https://api.skael.de"))
    openai_base_url: str = field(default_factory=lambda: os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))

    # --- Modelle (Clay-Defaults) ---------------------------------------
    # Clay `ICP ONLINE SHOP`, `Anrede [Prompt] (2)`, `Personalisierung AI`, `Cleaned Video Title`
    model_default: str = field(default_factory=lambda: os.environ.get("OPENAI_MODEL_DEFAULT", "gpt-4o-mini"))
    # Clay `Company Domain` ist ein Claygent (Websuche) mit gemini-2.5-flash-lite.
    # Nachgebaut über den Skael-Rechercheagenten mit demselben Modell.
    model_domain_agent: str = field(default_factory=lambda: os.environ.get(
        "DOMAIN_AGENT_MODEL", "google/gemini-2.5-flash-lite"))
    domain_agent_max_steps: int = field(default_factory=lambda: _int("DOMAIN_AGENT_MAX_STEPS", 5))

    # --- Durchsatz ------------------------------------------------------
    skael_rate_limit_per_sec: float = field(default_factory=lambda: _float("SKAEL_RATE_LIMIT_PER_SEC", 5.0))
    openai_rate_limit_per_sec: float = field(default_factory=lambda: _float("OPENAI_RATE_LIMIT_PER_SEC", 2.0))
    max_concurrency: int = field(default_factory=lambda: _int("MAX_CONCURRENCY", 5))
    http_timeout: int = field(default_factory=lambda: _int("HTTP_TIMEOUT", 180))
    max_retries: int = field(default_factory=lambda: _int("MAX_RETRIES", 4))

    # Clay `Bodytext Website` (Personalisierung) kürzt auf 8.192 Zeichen
    bodytext_max_chars: int = field(default_factory=lambda: _int("BODYTEXT_MAX_CHARS", 8192))
    # Clay `ICP ONLINE SHOP` schickt den vollen Text; die Kappung schützt nur vor Kontext-Überlauf
    icp_bodytext_max_chars: int = field(default_factory=lambda: _int("ICP_BODYTEXT_MAX_CHARS", 200000))

    # --- Traffic-Filter (Clay Import: MIN AVR TRAFFIC, MIN AVR H T 3 MO, MODE AND/OR) ---
    min_avr_traffic: float = field(default_factory=lambda: _float("MIN_AVR_TRAFFIC", 1))
    min_max_traffic: float = field(default_factory=lambda: _float("MIN_MAX_TRAFFIC_3MO", 1))
    traffic_mode: str = field(default_factory=lambda: (os.environ.get("TRAFFIC_MODE", "OR") or "OR").strip().upper())

    # --- Feature-Schalter ------------------------------------------------
    use_findymail: bool = field(default_factory=lambda: _bool("USE_FINDYMAIL", True))
    do_personalisierung: bool = field(default_factory=lambda: _bool("DO_PERSONALISIERUNG", True))
    do_video_title: bool = field(default_factory=lambda: _bool("DO_VIDEO_TITLE", True))

    # --- Community-Sperrliste (Abmahner-Domains) ------------------------
    # OWNER ist ein Platzhalter, den der Betreiber des Pakets beim Einrichten durch sein GitHub-Konto ersetzt
    sperrliste_url: str = field(default_factory=lambda: os.environ.get(
        "SPERRLISTE_URL", "https://raw.githubusercontent.com/alexseeed/werbemail-sperrliste/main/data/sperrliste.txt"))
    sperrliste_pflicht: bool = field(default_factory=lambda: _bool("SPERRLISTE_PFLICHT", True))

    db_path: Path = field(default_factory=lambda: Path(os.environ.get("DB_PATH", str(DATA_DIR / "shops.db"))))

    def require(self, *keys: str) -> None:
        missing = [k for k in keys if not getattr(self, k, "")]
        if missing:
            names = {
                "skael_api_key": "SKAEL_API_KEY",
                "openai_api_key": "OPENAI_API_KEY",
                "findymail_api_key": "FINDYMAIL_API_KEY",
            }
            raise SystemExit(
                "Fehlende Zugangsdaten in .env: " + ", ".join(names.get(k, k) for k in missing)
            )


CONFIG = Config()

# Clay ANREICHERUNG.`Email [Domain]` — wörtlich aus der Formel übernommen
FREEMAIL_DOMAINS = {
    "gmx.de", "web.de", "google.de", "google.com", "gmail.com", "outlook.com",
    "outlook.de", "t-online.de", "aol.com", "1und1.de", "freenet.de", "arcor.de",
    "yahoo.com", "mail.de", "aikq.de", "mailbox.org", "posteo.de", "tutanota.com",
    "icloud.com", "googlemail.com", "mail.ru", "protonmail.com", "mail.com",
}

# Debounce-Codes aus verify_email
CODE_LABEL = {5: "Safe to Send", 4: "Risky", 7: "Unknown"}
CODE_INVALID = {1, 2, 3, 6}
CODE_ACCEPTED = {4, 5, 7}
