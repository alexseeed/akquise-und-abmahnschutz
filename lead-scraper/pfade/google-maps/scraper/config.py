"""Konfiguration — liest .env und stellt alle Einstellungen zentral bereit."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
DATA_DIR = ROOT / "data"
EXPORT_DIR = ROOT / "exports"


def _load_dotenv(path: Path = ROOT / ".env") -> None:
    """Minimaler .env-Loader ohne Fremdabhängigkeit."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
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
    model_domain: str = field(default_factory=lambda: os.environ.get("OPENAI_MODEL_DOMAIN", "gpt-4.1-mini"))
    model_default: str = field(default_factory=lambda: os.environ.get("OPENAI_MODEL_DEFAULT", "gpt-4o-mini"))

    # --- Durchsatz ------------------------------------------------------
    skael_rate_limit_per_sec: float = field(default_factory=lambda: _float("SKAEL_RATE_LIMIT_PER_SEC", 5.0))
    openai_rate_limit_per_sec: float = field(default_factory=lambda: _float("OPENAI_RATE_LIMIT_PER_SEC", 2.0))
    max_concurrency: int = field(default_factory=lambda: _int("MAX_CONCURRENCY", 5))
    http_timeout: int = field(default_factory=lambda: _int("HTTP_TIMEOUT", 180))
    max_retries: int = field(default_factory=lambda: _int("MAX_RETRIES", 4))

    # --- Prozess-Parameter (Clay-Defaults) ------------------------------
    cities_limit: int = field(default_factory=lambda: _int("CITIES_LIMIT", 5000))
    maps_zoom: int = field(default_factory=lambda: _int("MAPS_ZOOM", 11))
    maps_limit: int = field(default_factory=lambda: _int("MAPS_LIMIT", 2000))
    bodytext_max_chars: int = field(default_factory=lambda: _int("BODYTEXT_MAX_CHARS", 8192))

    # --- Feature-Schalter (entsprechen den Clay-ON/OFF-Spalten) ---------
    quali_on: bool = field(default_factory=lambda: _bool("QUALI_ON", True))
    send_on: bool = field(default_factory=lambda: _bool("SEND_ON", True))
    use_findymail: bool = field(default_factory=lambda: _bool("USE_FINDYMAIL", True))
    do_personalisierung: bool = field(default_factory=lambda: _bool("DO_PERSONALISIERUNG", True))
    do_video_title: bool = field(default_factory=lambda: _bool("DO_VIDEO_TITLE", True))
    do_linkedin: bool = field(default_factory=lambda: _bool("DO_LINKEDIN", False))

    # Nicht-DACH-TLDs, die in Clay über den "DEDUPE"-Trick aussortiert werden
    # ACHTUNG beim Zielgruppenwechsel: Diese TLDs werden komplett aussortiert.
    # Default = DACH-Kampagne (Clay-Original). Wer Frankreich, die Niederlande
    # oder Italien scrapen will, MUSS das hier leeren — sonst fällt die ganze
    # Zielgruppe raus.  .env:  EXCLUDED_TLDS=          bzw.  EXCLUDED_TLDS=.ru,.cn
    excluded_tlds: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            t.strip().lower() if t.strip().startswith(".") else "." + t.strip().lower()
            for t in os.environ.get("EXCLUDED_TLDS", ".fr,.nl,.it").split(",")
            if t.strip()
        )
    )

    # --- Community-Sperrliste (Abmahner-Domains) ------------------------
    sperrliste_url: str = field(default_factory=lambda: os.environ.get(
        "SPERRLISTE_URL", "https://raw.githubusercontent.com/alexseeed/werbemail-sperrliste/main/data/sperrliste.txt"))
    sperrliste_pflicht: bool = field(default_factory=lambda: _bool("SPERRLISTE_PFLICHT", True))

    db_path: Path = field(default_factory=lambda: Path(os.environ.get("DB_PATH", str(DATA_DIR / "leads.db"))))

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


# Konzerne und Filialketten, die der ICP-Checker nicht zuverlaessig erkennt.
# Der Skael-Endpunkt arbeitet intern mit einem Sprachmodell, dessen Temperatur
# nicht steuerbar ist: dieselbe URL faellt mal durch, mal nicht. Diese Liste
# greift deterministisch beim Export. Ergaenzbar ueber .env: KETTEN_EXTRA=a,b,c
KETTEN_AUSSCHLUSS = tuple(sorted({
    "metro", "selgros", "transgourmet", "wuerth", "würth", "obi ", "bauhaus",
    "hornbach", "fressnapf", "bunzl", "igepa", "prodinger", "schlau",
    "intergast", "service-bund", "servicebund", "hagebau", "toom", "globus",
    "edeka", "rewe", "aldi", "lidl", "kaufland", "handelshof", "gastro-star",
} | {k.strip().lower() for k in os.environ.get("KETTEN_EXTRA", "").split(",") if k.strip()}))
