"""Reine Datentransformationen — 1:1-Portierung der Clay-Formeln.

Jede Funktion nennt in ihrem Docstring die Clay-Spalte, die sie nachbildet.
"""
from __future__ import annotations

import re
from typing import Any

from .config import CODE_ACCEPTED, CODE_INVALID, CODE_LABEL, CONFIG, FREEMAIL_DOMAINS

# ---------------------------------------------------------------- Stufe 2


def build_query(keyword: str, city: str | None, country: str | None) -> str:
    """Clay VERARBEITUNG.query:
    {{input_keyword}} + " in " + ({{input_city}} || {{input_country}})
    """
    place = city or country or ""
    return f"{keyword} in {place}"


def contains_error(maps_output: Any) -> bool:
    """Clay VERARBEITUNG.`Contains Error`.

    Das Original greift mit `{{SKAEL MAPS}}?.[0]` auf ein *Objekt* per Index zu —
    das ist immer `undefined`, die Spalte ist faktisch tot und blockiert nie.
    Hier wird die erkennbare Absicht abgebildet: nur eine Antwort, die selbst als
    Fehler markiert ist, gilt als Fehler. Ein Volltext-Scan über die Treffer wäre
    fatal, weil dann ein einzelnes "error" in einer Domain oder Beschreibung eine
    ganze Stadt mit bis zu 2.000 Firmen verwerfen würde.
    """
    if not isinstance(maps_output, dict):
        return False
    if maps_output.get("error") or maps_output.get("error_message"):
        return True
    return str(maps_output.get("status", "")).lower() == "failed"


# ---------------------------------------------------------------- Stufe 3


def strip_query_fragment(url: str | None) -> str:
    """Clay DATENSÄTZE.`Website final`, erste Stufe:
    {{website}}?.split("?")?.[0]?.split("#")?.[0] || {{website}}
    """
    if not url:
        return ""
    return url.split("?")[0].split("#")[0] or url


def website_final(website: str | None, domain_url_response: str | None) -> str:
    """Clay DATENSÄTZE.`Website final` (Merge-Spalte)."""
    cleaned = strip_query_fragment(website)
    return cleaned or (domain_url_response or "")


_WEBSITE_RE = re.compile(r"^(https?://)?([a-z0-9-]+\.)+[a-z]{2,}(/.*)?$", re.IGNORECASE)


def website_final_anreicherung(website: str | None, company_domain_response: str | None) -> str:
    """Clay ANREICHERUNG.`website [Final]`:
    Regex-Test auf {{website}}, sonst {{Company Domain}}?.response
    """
    if website and _WEBSITE_RE.match(website.strip()):
        return website.strip()
    return (company_domain_response or "").strip()


def host_of(url: str | None) -> str:
    """Nackter Host: Protokoll, www und Pfad entfernen."""
    if not url:
        return ""
    stripped = re.sub(r"^https?://(www\.)?", "", url.strip(), flags=re.IGNORECASE)
    return stripped.split("/")[0].split("?")[0].split("#")[0].lower()


def registrable_domain(url: str | None) -> str:
    """Letzte zwei Labels des Hosts — wie Clay `Email [Domain]` es berechnet."""
    host = host_of(url)
    if not host:
        return ""
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def dedupe_key(website_final_value: str | None, domain_url_present: bool) -> str:
    """Clay DATENSÄTZE.`Dedupe`.

    Rückgabe:
      * Host           → echter Dedupe-Schlüssel
      * "DEDUPE"       → Zeile wird durch die Auto-Dedupe eliminiert
                         (nicht-DACH-TLD, oder Website nur per KI geraten)
      * ""             → Zeile wird von der Dedupe nicht angefasst
    """
    if website_final_value:
        host = host_of(website_final_value)
        if any(tld in host for tld in CONFIG.excluded_tlds):
            return "DEDUPE"
        return host or ""
    return "DEDUPE" if domain_url_present else ""


def phone_number_export(phone: str | None) -> str:
    """Clay DATENSÄTZE.`Phone Number Export`: {{phone}}?.replace("+", "")"""
    if not phone:
        return ""
    return phone.replace("+", "", 1)


def icp_label(icp_output: dict | None) -> str:
    """Clay DATENSÄTZE.`ICP` (Select True/False/Unknown)."""
    if not isinstance(icp_output, dict):
        return "Unknown"
    value = icp_output.get("icp")
    if value is True:
        return "True"
    if value is False:
        return "False"
    return "Unknown"


# ---------------------------------------------------------------- Stufe 4

_DIACRITICS = {
    "é": "e", "è": "e", "ê": "e", "ë": "e",
    "á": "a", "à": "a", "â": "a", "ä": "ae",
    "ó": "o", "ò": "o", "ô": "o", "ö": "oe",
    "ú": "u", "ù": "u", "û": "u", "ü": "ue",
    "ñ": "n", "ç": "c", "ß": "ss",
}
_DROP_TOKENS = {"herr", "frau", "hr", "rechtsanwalt"}


def kontaktperson_sauber(name: str | None) -> str:
    """Clay ANREICHERUNG.`Kontaktperson [Sauber]` — vollständige Portierung."""
    if not name:
        return ""
    text = re.sub(r"\([^)]*\)|\{[^}]*\}|\[[^\]]*\]", "", name)

    tokens = []
    for token in text.split(" "):
        stripped = token.strip()
        if not stripped:
            continue
        if "." in stripped:
            continue
        if stripped.lower() in _DROP_TOKENS:
            continue
        if stripped == stripped.upper() and len(stripped) > 1:
            continue
        tokens.append(stripped)

    joined = " ".join(tokens)
    # Auf erstes + letztes Token reduzieren
    match = re.match(r"^(\S+)(?:\s+\S+)*\s+(\S+)$", joined)
    if match:
        joined = f"{match.group(1)} {match.group(2)}"

    for src, dst in _DIACRITICS.items():
        joined = joined.replace(src, dst)
        # Abweichung vom Clay-Original: dort werden nur Kleinbuchstaben ersetzt,
        # Großbuchstaben-Umlaute fallen anschließend dem Zeichenfilter zum Opfer
        # ("Änderung" → "nderung"). Hier korrekt abgebildet. "ß" hat keine
        # Großform, die ersetzt werden dürfte ("ß".upper() == "SS").
        if src != "ß":
            joined = joined.replace(src.upper(), dst.capitalize())

    joined = joined.replace("'", "").replace("’", "").replace("`", "")
    joined = re.sub(r"[^A-Za-z0-9\s-]", "", joined)
    return joined.strip()


_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def email_impressum(raw_email: str | None) -> str:
    """Clay ANREICHERUNG.`Email [Impressum]` — (at)/[at] normalisieren + Syntaxprüfung."""
    if not raw_email:
        return ""
    candidate = re.sub(r"\(at\)|\[at\]", "@", raw_email, flags=re.IGNORECASE)
    return candidate if _EMAIL_RE.match(candidate) else ""


def email_domain(impressum_email: str, website_final_value: str) -> str:
    """Clay ANREICHERUNG.`Email [Domain]` — Freemail-Adressen auf die Website-Domain umbiegen."""
    if impressum_email:
        domain = impressum_email.split("@")[-1].lower()
        if domain not in FREEMAIL_DOMAINS:
            return domain
    return registrable_domain(website_final_value)


def launch_campaign(kontaktperson_clean: str, impressum_email: str) -> bool:
    """Clay ANREICHERUNG.`Launch Campaign`."""
    return bool(kontaktperson_clean) or bool(impressum_email)


def _code_of(verify_output: dict | None) -> int | None:
    if not isinstance(verify_output, dict):
        return None
    try:
        return int(verify_output.get("code"))
    except (TypeError, ValueError):
        return None


def email_from_verify(verify_output: dict | None) -> str:
    """Clay ANREICHERUNG.`Email [GF]` / `Email [Info@]` — Codes 4, 5, 7 gelten als brauchbar."""
    code = _code_of(verify_output)
    if code in CODE_ACCEPTED:
        return (verify_output or {}).get("email") or ""
    return ""


def email_status(verify_output: dict | None, *, kein_gf: bool = False, impressum_ran: bool = False) -> str:
    """Clay ANREICHERUNG.`Email [GF][Status]` bzw. `Email [Info@][Status]`.

    `verify_output=None` bedeutet: Validierung lief gar nicht → "Not Run".
    Lief sie, lieferte aber keinen brauchbaren Code (Fehlerobjekt, untypische
    Antwort), ist das Ergebnis "None found" — genau wie in Clay, wo alle
    Code-Zweige durchfallen, sobald die Action einmal gelaufen ist.
    """
    if kein_gf and impressum_ran:
        return "Kein GF"
    if verify_output is None:
        return "Not Run"
    code = _code_of(verify_output)
    if code in CODE_LABEL:
        return CODE_LABEL[code]
    if code in CODE_INVALID:
        return "Invalid"
    return "None found"


def email_source_gf(email_gf: str, skael_email: str | None, findymail_email: str | None) -> str:
    """Clay ANREICHERUNG.`Email source GF`."""
    if not email_gf:
        return "None Found"
    target = email_gf.lower()
    if skael_email and skael_email.lower() == target:
        return "Skael"
    if findymail_email and findymail_email.lower() == target:
        return "Findymail"
    return ""


def email_final(email_gf: str, email_info: str) -> str:
    """Clay ANREICHERUNG.`Email [Final]` — Wasserfall GF → Info@."""
    return email_gf or email_info or ""


def email_final_type(email_gf: str, email_info: str, status_gf: str, status_info: str) -> str:
    """Clay ANREICHERUNG.`Email [Final][Type]`."""
    if email_gf:
        return "GF"
    if email_info:
        return "Info@"
    if status_gf in ("Not Run", "Kein GF") and status_info == "Not Run":
        return "Not Run"
    return "None found"


def email_final_status(email_gf: str, email_info: str, status_gf: str, status_info: str) -> str:
    """Clay ANREICHERUNG.`Email [Final][Status]`."""
    if email_gf:
        return status_gf
    if email_info:
        return status_info
    if status_gf == "None found" and status_info == "None found":
        return "None found"
    if status_gf in ("Not Run", "Kein GF") and status_info == "Not Run":
        return "Not Run"
    return "None found"


def first_name(clean_name: str) -> str:
    """Clay ANREICHERUNG.`First Name [GF]`."""
    return clean_name.split(" ")[0] if clean_name else ""


def last_name(clean_name: str) -> str:
    """Clay ANREICHERUNG.`Last Name [GF]`."""
    return clean_name.split(" ")[-1] if clean_name else ""


def formal_prefix(anrede: str | None) -> str:
    """Clay ANREICHERUNG.`Formal`."""
    if anrede == "Herr":
        return "Sehr geehrter"
    if anrede == "Frau":
        return "Sehr geehrte"
    return ""


def ansprachen(anrede: str | None, first: str, last: str, email_final_value: str) -> dict[str, str]:
    """Clay ANREICHERUNG.`Ansprache …[Final]` (4 Varianten)."""
    has_mail = bool(email_final_value)
    formal = formal_prefix(anrede)
    return {
        "ansprache_formal": (
            f"{formal} {anrede} {last}" if anrede else ("Sehr geehrte Damen und Herren" if has_mail else "")
        ),
        "ansprache_normal": (
            f"Hallo {anrede} {last}" if anrede else ("Hallo" if has_mail else "")
        ),
        "ansprache_normal_gt": (
            f"Guten Tag {anrede} {last}" if anrede else ("Guten Tag" if has_mail else "")
        ),
        "ansprache_persoenlich": (
            f"Hallo {first}" if (first and anrede) else ("Hallo" if has_mail else "")
        ),
    }


def video_title_input(first: str, last: str, firmenname: str) -> str:
    """Clay ANREICHERUNG.`Video Title Input`."""
    if not first:
        head = f"Videotitle: Video für {firmenname}"
    else:
        head = f"Videotitle: Video für {first} {last or ''} von {firmenname}"
    return (
        f"{head}\n"
        f"Firstname: {first or 'nicht vorhanden oder firstname'}, "
        f"Lastname: {last or 'nicht vorhanden oder lastname'}\n"
        f"Firmenname: {firmenname or ''}"
    )


def bodytext(scraper_output: dict | None) -> str:
    """Clay ANREICHERUNG.`Bodytext Website` — body_text auf 8.192 Zeichen gekürzt."""
    text = (scraper_output or {}).get("body_text") or ""
    return text[: CONFIG.bodytext_max_chars]


# Pfadbestandteile, die etwas ueber den Vertriebskanal aussagen. Solche Links
# werden bevorzugt uebernommen — bei Seiten mit hunderten Links landen die
# entscheidenden sonst hinter dem Limit und das Signal geht verloren.
_VERTRIEBS_SIGNALE = (
    "haendler", "handler", "partner", "vertrieb", "standort", "niederlass",
    "filial", "fachhandel", "wiederverkauf", "distribut", "importeur",
    "aussendienst", "b2b", "gewerbe", "shop", "katalog", "download",
    "schulung", "academy", "akademie", "datenblatt", "profi",
)


def site_links(scraper_output: dict | None, limit: int = 150) -> str:
    """Linkliste der Startseite, auf Pfade reduziert und nach Aussagekraft sortiert.

    Keine Clay-Entsprechung — der web_scraper liefert `links` bereits mit, im
    Workbook wurde das Feld aber nie genutzt. Fuer die Einordnung des
    Vertriebskanals ist der Pfad das Signal (/haendler-werden, /partnerportal),
    nicht die Domain. Fremde Domains und Duplikate fallen raus; Subdomains der
    eigenen Domain bleiben drin, weil dort haeufig genau diese Seiten liegen.
    """
    out = scraper_output or {}
    host = registrable_domain(out.get("final_url") or "")
    seen: set[str] = set()
    wichtig: list[str] = []
    rest: list[str] = []
    for link in out.get("links") or []:
        if not isinstance(link, str):
            continue
        if host and host not in link.lower():
            continue
        pfad = re.sub(r"^https?://", "", link.strip()).split("?")[0].split("#")[0]
        pfad = "/" + pfad.split("/", 1)[1] if "/" in pfad else ""
        if not pfad or pfad == "/":
            continue
        key = pfad.lower()
        if key in seen:
            continue
        seen.add(key)
        (wichtig if any(w in key for w in _VERTRIEBS_SIGNALE) else rest).append(pfad)
    return "\n".join((wichtig + rest)[:limit])


def ready_to_send(email_final_value: str, personalisierung: str, video_title: str) -> bool:
    """Clay ANREICHERUNG.`Ready to Send`."""
    return bool(email_final_value) and bool(personalisierung) and bool(video_title)
