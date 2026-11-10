"""Konfiguration — liest .env und stellt alle Einstellungen zentral bereit.

Zwei Ebenen:
  * `.env` im Projektordner: Zugangsschlüssel und Standardwerte (einmal pro Rechner)
  * `kampagnen/<name>/kampagne.env`: alles, was zur Zielgruppe gehört (überschreibt `.env`)

Die aktive Kampagne kommt aus `--kampagne <name>` (siehe __main__.py) oder KAMPAGNE in `.env`.
Jede Kampagne hat eigene Prompts, Datenbank, Blockliste und Exporte unter `kampagnen/<name>/`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KAMPAGNEN_ROOT = ROOT / "kampagnen"
_PROZESS_ENV = set(os.environ)  # echte Umgebungsvariablen haben immer Vorrang


def _load_dotenv(path: Path, *, ueberschreiben: bool = False) -> None:
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
        if ueberschreiben and key not in _PROZESS_ENV:
            os.environ[key] = value
        else:
            os.environ.setdefault(key, value)


_load_dotenv(ROOT / ".env")
KAMPAGNE = os.environ.get("KAMPAGNE", "").strip()
KAMPAGNE_DIR: Path | None = KAMPAGNEN_ROOT / KAMPAGNE if KAMPAGNE else None
if KAMPAGNE_DIR is not None:
    if not KAMPAGNE_DIR.is_dir():
        raise SystemExit(f"Kampagne '{KAMPAGNE}' nicht gefunden: {KAMPAGNE_DIR}\n"
                         f"Anlegen mit:  python3 -m scraper neue-kampagne {KAMPAGNE}")
    _load_dotenv(KAMPAGNE_DIR / "kampagne.env", ueberschreiben=True)

_BASIS = KAMPAGNE_DIR or ROOT
PROMPTS_DIR = ROOT / "prompts"            # Standard-Prompts (zielgruppenneutral)
PROMPT_DIRS = ([KAMPAGNE_DIR / "prompts"] if KAMPAGNE_DIR else []) + [PROMPTS_DIR]
DATA_DIR = _BASIS / "data"
EXPORT_DIR = _BASIS / "exports"


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


_MODELL_STANDARD = {
    # Anbieter → (Standard, Personalisierung, Domainsuche)
    # GROESSE: Größen-Check der Stellensuche aus Modellwissen — braucht ein Modell mit gutem
    # Firmenwissen (gpt-4o-mini war zu nachsichtig, gpt-4.1 gemessen gut)
    "skael": {"DEFAULT": "skael/fast", "PERSONALISIERUNG": "skael/smart", "DOMAIN": "skael/fast",
              "GROESSE": "skael/smart"},
    "openai": {"DEFAULT": "gpt-4o-mini", "PERSONALISIERUNG": "gpt-4.1", "DOMAIN": "gpt-4.1-mini",
               "GROESSE": "gpt-4.1"},
}


def _modell(rolle: str) -> str:
    anbieter = os.environ.get("LLM_PROVIDER", "skael").strip().lower()
    wert = os.environ.get(f"MODEL_{rolle}") or (
        os.environ.get(f"OPENAI_MODEL_{rolle}") if anbieter == "openai" else "")
    return wert or _MODELL_STANDARD.get(anbieter, _MODELL_STANDARD["openai"])[rolle]


def _domainsuche() -> str:
    wert = os.environ.get("DOMAINSUCHE", "").strip().lower()
    if not wert and os.environ.get("DO_DOMAINSUCHE", "").strip().lower() in {"0", "false", "no", "nein", "off"}:
        wert = "aus"
    return wert if wert in {"skael", "openai", "aus"} else "aus"


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on", "ja"}


@dataclass
class Config:
    # --- Zugänge -------------------------------------------------------
    skael_api_key: str = field(default_factory=lambda: os.environ.get("SKAEL_API_KEY", ""))
    # Eigener Schlüssel mit der Fähigkeit llm:invoke für die KI-Schritte (optional). Neue Skael-Schlüssel
    # mit Fähigkeiten haben ein Tageslimit (Standard 5.000 Credits) — für Läufe höher setzen lassen.
    # Leer = SKAEL_API_KEY wird auch für die KI genutzt.
    skael_llm_api_key: str = field(default_factory=lambda: os.environ.get("SKAEL_LLM_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.environ.get("OPENAI_API_KEY", ""))
    # Ersatz, falls der Hauptschlüssel sein Budget/Rate-Limit erreicht
    openai_api_key_fallback: str = field(default_factory=lambda: os.environ.get("OPENAI_API_KEY_FALLBACK", ""))
    findymail_api_key: str = field(default_factory=lambda: os.environ.get("FINDYMAIL_API_KEY", ""))

    skael_base_url: str = field(default_factory=lambda: os.environ.get("SKAEL_BASE_URL", "https://api.skael.de"))
    openai_base_url: str = field(default_factory=lambda: os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))

    # --- KI-Anbieter ----------------------------------------------------
    # skael (Standard): OpenAI-kompatible Schnittstelle von Skael, abgerechnet in Skael-Credits,
    #   ohne die Rate-Limits einzelner ChatGPT-Konten. Der Schlüssel braucht die Fähigkeit llm:invoke.
    # openai: direkt bei OpenAI (OPENAI_API_KEY, optional OPENAI_API_KEY_FALLBACK).
    llm_provider: str = field(default_factory=lambda: os.environ.get("LLM_PROVIDER", "skael").strip().lower())

    # --- Modelle --------------------------------------------------------
    # MODEL_* gilt für den gewählten Anbieter. Die alten OPENAI_MODEL_* werden weiter gelesen.
    model_default: str = field(default_factory=lambda: _modell("DEFAULT"))
    model_personalisierung: str = field(default_factory=lambda: _modell("PERSONALISIERUNG"))
    model_domain: str = field(default_factory=lambda: _modell("DOMAIN"))
    model_groesse: str = field(default_factory=lambda: _modell("GROESSE"))
    # Websuche gibt es nur bei OpenAI — daher immer ein OpenAI-Modell
    openai_model_websuche: str = field(default_factory=lambda: os.environ.get("OPENAI_MODEL_DOMAIN", "gpt-4.1-mini"))

    # --- Domainsuche für Firmen ohne Website ----------------------------
    # aus (Standard): Firmen ohne Website fallen raus — günstig, und solche Firmen lassen sich
    #   ohnehin kaum prüfen oder anschreiben
    # skael: find_domain, über das Impressum bestätigt, 15–35 Credits je Firma, findet nur Belegtes
    # openai: Websuche über die Responses-API, ca. 1 Cent je Firma, findet mehr, rät aber auch
    domainsuche: str = field(default_factory=lambda: _domainsuche())

    # --- Durchsatz ------------------------------------------------------
    skael_rate_limit_per_sec: float = field(default_factory=lambda: _float("SKAEL_RATE_LIMIT_PER_SEC", 20.0))
    openai_rate_limit_per_sec: float = field(default_factory=lambda: _float("OPENAI_RATE_LIMIT_PER_SEC", 2.0))
    # 12 parallel: Skael-Aufrufe dauern 5–10 s, das Limit (5/s) wird damit bei Weitem nicht erreicht
    max_concurrency: int = field(default_factory=lambda: _int("MAX_CONCURRENCY", 12))
    http_timeout: int = field(default_factory=lambda: _int("HTTP_TIMEOUT", 180))
    # Höchstwartezeit je asynchronem Skael-Auftrag; danach wird die Zeile später erneut versucht
    skael_max_wartezeit: int = field(default_factory=lambda: _int("SKAEL_MAX_WARTEZEIT", 600))
    # Versuche je API-Aufruf bei vorübergehenden Fehlern (Netzwerk, 429, 5xx), Pause 2/4/8/16 s (429: 5/10/20/40 s)
    max_retries: int = field(default_factory=lambda: _int("MAX_RETRIES", 5))

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

    # --- Pfad Recruiting (Stelle auf der Firmen-Website erkennen) ---------
    # NK = Firmen, die zum Profil passen, aber keine offene Stelle haben.
    # Im Clay-Original abgeschaltet (`NK SEND … && false`), deshalb Default aus.
    nk_on: bool = field(default_factory=lambda: _bool("NK_ON", False))
    karriere_seiten: int = field(default_factory=lambda: _int("KARRIERE_SEITEN", 2))
    stellen_text_max: int = field(default_factory=lambda: _int("STELLEN_TEXT_MAX", 16000))

    # --- Pfad Stellensuche (Jobportale über Skael) ---------------------
    # Je Kampagne per `stellensuche --max-alter/--max-seiten/--umkreis` überschreibbar.
    stellen_max_alter: int = field(default_factory=lambda: _int("STELLEN_MAX_ALTER", 30))
    stellen_max_seiten: int = field(default_factory=lambda: _int("STELLEN_MAX_SEITEN", 3))
    stellen_umkreis: int = field(default_factory=lambda: _int("STELLEN_UMKREIS", 25))
    stellen_beschreibung_max: int = field(default_factory=lambda: _int("STELLEN_BESCHREIBUNG_MAX", 4000))
    find_domain_max_pages: int = field(default_factory=lambda: _int("FIND_DOMAIN_MAX_PAGES", 3))

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

    # Mailabsatz rund um den Beobachtungssatz (Export-Spalte "Absatz Beobachtung").
    # Gehört in kampagne.env. Leer = Spalte enthält nur den Satz bzw. bleibt leer.
    absatz_einleitung: str = field(default_factory=lambda: os.environ.get("ABSATZ_EINLEITUNG", ""))
    absatz_folgesatz: str = field(default_factory=lambda: os.environ.get("ABSATZ_FOLGESATZ", ""))
    absatz_standard: str = field(default_factory=lambda: os.environ.get("ABSATZ_STANDARD", ""))

    # Kategorie, die bei "unklar" eingesetzt wird — muss im enum von pain_kategorie.schema.json stehen
    kategorie_normalfall: str = field(default_factory=lambda: os.environ.get("KATEGORIE_NORMALFALL", ""))

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

# Kampagnen-Arten. Eine Datenbank (= eine Kampagne) hat genau eine Art; sie steht in run_meta "pfad".
PFADE = ("google-maps", "recruiting", "stellensuche")

# Strecken je Lead in der Anreicherung (steuern Personalisierung und Ready to Send)
#   gmaps = Google-Maps-Pfad          rc   = Recruiting bzw. Stellensuche, offene Stelle bekannt
#   nk    = Recruiting ohne Stelle
STRECKEN = ("gmaps", "rc", "nk")

# Jobportale der Stellensuche: Skael-Endpunkt und Länder, die das Portal bedient
PORTALE = {
    "indeed": {"endpoint": "indeed_jobs", "laender": None},          # None = jedes Land
    "stepstone": {"endpoint": "stepstone_jobs", "laender": ("DE", "AT", "NL", "BE")},
    "arbeitsagentur": {"endpoint": "arbeitsagentur_jobs", "laender": ("DE",)},
    "kununu": {"endpoint": "kununu_jobs", "laender": ("DE", "AT", "CH")},
}

# Zeitarbeit und Personalvermittler schreiben für ihre Kunden aus — sie sind selten
# der eigentliche Arbeitgeber. Treffer im Firmennamen (klein geschrieben) schließen die
# Stelle aus. Ergänzbar über .env: PERSONALDIENSTLEISTER_EXTRA=a,b,c
PERSONALDIENSTLEISTER = tuple(sorted({
    "zeitarbeit", "personaldienst", "personalservice", "personal-service", "personalleasing",
    "personalmanagement", "personalvermittlung", "personalberatung", "personal partner",
    "personalpartner", "arbeitnehmerüberlassung", "arbeitnehmerueberlassung", "staffing",
    "recruiting", "recruitment", "headhunt", "jobvermittlung", "jobagentur",
    "tempton", "randstad", "adecco", "manpower", "dekra arbeit", "orizon", "timepartner",
    "persona service", "amadeus fire", "hays ", "gi group", "piening", "start people",
    "tempo-team", "trenkwalder", "brunel", "gulp", "expertum", "office people",
    "fach-kraft personal", "tempster", "i. k. hofmann", "ik hofmann", "zag ", "arwa ",
    "unique personal", "jobactive", "jobimpulse", "instaffo", "vesterling",
} | {k.strip().lower() for k in os.environ.get("PERSONALDIENSTLEISTER_EXTRA", "").split(",") if k.strip()}))

# Bewerbermanagement-Systeme und Jobbörsen: deren Domain ist nie die Firmen-Website
FREMD_DOMAINS_STELLEN = (
    "indeed.", "stepstone.", "arbeitsagentur.", "kununu.", "linkedin.", "xing.", "heyjobs.",
    "personio.", "softgarden.", "join.com", "recruitee.", "smartrecruiters.", "workday",
    "successfactors.", "greenhouse.io", "lever.co", "onlyfy.", "dvinci", "rexx-systems.",
    "concludis.", "umantis.", "prescreen.", "jobware.", "meinestadt.", "monster.", "stellenanzeigen.de",
    "jobs.de", "jobvector.", "absolventa.", "azubiyo.", "ausbildung.de", "jobteaser.", "talent.com",
    "glassdoor.", "jobboerse.", "jobbörse", "gigajob.", "kimeta.", "jooble.", "careerjet.",
    "bewerbung.", "jobsite", "hr4you.", "coveto.", "pitchyou.", "truckerjobs", "jobninja.", "zvoove",
    "gohiring.", "hibob.", "heyrecruit.", "jobvector", "stellenwerk.", "jobware", "empfehlungsbund.",
)

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
