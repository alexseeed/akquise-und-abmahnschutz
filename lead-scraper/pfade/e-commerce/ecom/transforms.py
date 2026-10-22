"""Reine Datentransformationen — 1:1-Portierung der Clay-Formeln.

Jede Funktion nennt in ihrem Docstring die Clay-Spalte, die sie nachbildet.
Die Funktionen ab „Stufe 2“ sind aus pfade/google-maps/scraper/transforms.py
übernommen: Die Formeln der Clay-Tabelle ANREICHERUNG sind in beiden Workbooks
zeichengleich (geprüft am 2026-10-08 gegen docs/clay_export_ecom_2_0.json).
"""
from __future__ import annotations

import math
import re

from .config import CODE_ACCEPTED, CODE_INVALID, CODE_LABEL, CONFIG, FREEMAIL_DOMAINS

# ---------------------------------------------------------------- Stufe 1 (Clay Import)


def website_final(website: str | None, company_domain_response: str | None) -> str:
    r"""Clay Import.`website [Final]` und ANREICHERUNG.`website [Final]` (identische Formel):
    /^(https?:\/\/)?([a-z0-9-]+\.)+[a-z]{2,}(\/.*)?$/i.test({{website}}) ? {{website}} : {{Company Domain}}?.response
    """
    return website_final_anreicherung(website, company_domain_response)


def _monthly_visits(webtraffic_output: dict | None) -> list[float]:
    visits = (webtraffic_output or {}).get("estimated_monthly_visits")
    if not isinstance(visits, dict) or not visits:
        return []
    werte = []
    for v in visits.values():
        try:
            werte.append(float(v))
        except (TypeError, ValueError):
            werte.append(float("nan"))
    return werte


def avr_traffic(webtraffic_output: dict | None) -> int | None:
    """Clay Import.`AVR TRAFFIC`: Math.round(Summe / Anzahl) der estimated_monthly_visits, sonst "".

    None steht für Clays leeren String. Math.round rundet .5 immer auf
    (Python-round rundet zur geraden Zahl) – deshalb floor(x + 0.5).
    """
    werte = _monthly_visits(webtraffic_output)
    if not werte:
        return None
    mittel = sum(werte) / len(werte)
    return None if math.isnan(mittel) else int(math.floor(mittel + 0.5))


def max_traffic_3mo(webtraffic_output: dict | None) -> int | None:
    """Clay Import.`H T 3 MO`: höchster Monatswert der estimated_monthly_visits (Startwert 0), sonst ""."""
    werte = _monthly_visits(webtraffic_output)
    if not werte:
        return None
    return int(max([0.0] + [w for w in werte if not math.isnan(w)]))


def send(avr: int | None, maximum: int | None, *, min_avr: float | None = None,
         min_max: float | None = None, mode: str | None = None) -> bool:
    """Clay Import.`SEND`.

    MODE "OR":  Number(AVR TRAFFIC) >= MIN AVR TRAFFIC  ||  Number(H T 3 MO) >= MIN AVR H T 3 MO
    MODE "AND": dieselben Vergleiche mit &&
    Number("") ist in JavaScript 0 – ein Shop ohne Traffic-Daten fällt deshalb bei MIN ≥ 1 raus.
    """
    min_avr = CONFIG.min_avr_traffic if min_avr is None else min_avr
    min_max = CONFIG.min_max_traffic if min_max is None else min_max
    mode = (mode or CONFIG.traffic_mode).upper()
    a = (avr or 0) >= min_avr
    b = (maximum or 0) >= min_max
    return (a and b) if mode == "AND" else (a or b)


def import_key(website: str | None, firmenname: str | None) -> str:
    """Schlüssel gegen doppelten Import derselben Zeile (in Clay entsteht bei erneutem Import eine neue Zeile).

    „www.shop.de“, „https://www.shop.de“ und „SHOP.de“ ergeben denselben Schlüssel. `host_of` entfernt
    „www.“ nur nach http(s):// (wie im Google-Maps-Pfad); hier zusätzlich ohne Protokoll.
    """
    host = re.sub(r"^www\.", "", host_of(website))
    if host:
        return host
    name = (firmenname or "").strip().lower()
    return f"name:{name}" if name else ""


# ---------------------------------------------------------------- Stufe 2 (Clay ANREICHERUNG)


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



def ready_to_send(email_final_value: str, personalisierung: str, video_title: str) -> bool:
    """Clay ANREICHERUNG.`Ready to Send`: !!Email [Final] && !!Personalisierung && !!Video Title"""
    return bool(email_final_value) and bool(personalisierung) and bool(video_title)
