"""Stellensuche über Jobportale — reine Funktionen ohne Netz und Datenbank.

Die Portale werden über Skael abgefragt (indeed_jobs, stepstone_jobs, arbeitsagentur_jobs,
kununu_jobs); dieses Modul baut die Anfragen und übersetzt die vier Antwortformate in
ein gemeinsames Format:

    {portal, portal_id, titel, firma, ort, plz, land, veroeffentlicht, url,
     bewerben_url, website, gehalt, beschreibung, raw}

Antwortformate (Stand Oktober 2026, an echten Antworten geprüft):
  indeed          data.jobs[]  mit company.website, apply_url, description_html, date_published
  stepstone       data.jobs[]  nur company.name, url, date_posted (keine Beschreibung)
  arbeitsagentur  data.stellenangebote[] (normalisiert) bzw. data.ergebnisliste[] (roh)
  kununu          data[]       mit company.website laut Doku, postedAt
"""
from __future__ import annotations

import html
import json
import re
from datetime import date, timedelta
from typing import Any, Iterable

from .config import FREMD_DOMAINS_STELLEN, PERSONALDIENSTLEISTER
from .transforms import host_of, registrable_domain

SEITE_GROESSE = 100

# Umkreis-Stufen, die das jeweilige Portal annimmt
_UMKREIS_AA = (10, 25, 50, 100, 150, 200)
_UMKREIS_KUNUNU = (10, 20, 30, 50, 100, 200)
_ALTER_STEPSTONE = (1, 3, 7, 30)


def _stufe(wert: int, stufen: tuple[int, ...]) -> int:
    """Kleinste erlaubte Stufe, die den Wunsch abdeckt (sonst die größte)."""
    return next((s for s in stufen if s >= wert), stufen[-1])


# ---------------------------------------------------------------- Anfrage

def anfrage(portal: str, suchbegriff: str, ort: str, land: str, *, seite: int,
            cursor: str | None, umkreis: int, max_alter: int) -> dict:
    """Request-Body für eine Ergebnisseite. `seite` beginnt bei 1."""
    land_klein = (land or "DE").lower()
    if portal == "indeed":
        return {"query": suchbegriff, "location": ort or None, "country": land_klein,
                "radius": min(umkreis, 100) if ort else None,
                "radius_unit": "KILOMETERS" if ort else None,
                "sort": "date", "limit": SEITE_GROESSE, "cursor": cursor}
    if portal == "stepstone":
        return {"query": suchbegriff, "location": ort or None, "country": land_klein,
                "radius": min(umkreis, 200) if ort else None, "sort": "date",
                "date_posted": str(_stufe(max_alter, _ALTER_STEPSTONE)) if max_alter and max_alter <= 30 else None,
                "page": seite, "limit": SEITE_GROESSE}
    if portal == "arbeitsagentur":
        # angebotsart 1 = Arbeit (keine Ausbildung/Praktika); Zeitarbeit und private
        # Arbeitsvermittler filtert das Portal selbst heraus.
        return {"was": suchbegriff, "wo": ort or None,
                "umkreis": str(_stufe(umkreis, _UMKREIS_AA)) if ort else None,
                "angebotsart": "1", "zeitarbeit": False, "pav": False,
                "veroeffentlichtseit": min(max_alter, 100) if max_alter else None,
                "page": seite, "size": SEITE_GROESSE}
    if portal == "kununu":
        return {"query": suchbegriff, "country": land_klein, "location": ort or None,
                "radius": _stufe(umkreis, _UMKREIS_KUNUNU) if ort else None,
                "sort": "newest", "page": seite}
    raise ValueError(f"unbekanntes Portal {portal!r}")


def naechste_seite(portal: str, antwort: dict, seite: int, anzahl: int) -> tuple[bool, str | None]:
    """(gibt es eine weitere Seite?, Cursor für Indeed)."""
    daten = _daten(antwort)
    if anzahl == 0:
        return False, None
    if portal == "indeed":
        pag = (daten or {}).get("pagination") or {}
        cursor = pag.get("next_cursor")
        return bool(pag.get("has_more") and cursor), cursor
    if portal == "stepstone":
        pag = (daten or {}).get("pagination") or {}
        if "has_more" in pag:
            return bool(pag["has_more"]), None
        return seite < int(pag.get("total_pages") or 0), None
    if portal == "arbeitsagentur":
        try:
            gesamt = int((daten or {}).get("maxErgebnisse") or 0)
        except (TypeError, ValueError):
            gesamt = 0
        return seite * SEITE_GROESSE < gesamt, None
    # kununu: keine Seitenangabe in der Antwort — weiter, solange eine Seite etwas liefert
    return anzahl > 0, None


# ---------------------------------------------------------------- Antwort

def _daten(antwort: Any) -> Any:
    """Skael liefert {"success": …, "data": …}; manche Tests/Antworten direkt das Innere."""
    if isinstance(antwort, dict) and "data" in antwort:
        return antwort["data"]
    return antwort


def _datum(wert: Any) -> str:
    text = str(wert or "").strip()
    return text[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", text) else ""


def _gehalt(wert: Any) -> str:
    if not wert:
        return ""
    if isinstance(wert, str):
        return wert.strip()
    if isinstance(wert, dict):
        teile = [str(wert[k]) for k in ("min", "max") if wert.get(k) not in (None, "")]
        spanne = " – ".join(dict.fromkeys(teile))
        rest = " ".join(str(wert[k]) for k in ("currency", "unit") if wert.get(k))
        text = f"{spanne} {rest}".strip()
        return f"{text} (geschätzt)" if wert.get("is_estimated") and text else text
    return str(wert)


def _url(wert: Any) -> str:
    text = str(wert or "").strip()
    return text if text.lower().startswith("http") else ""


def stellen_aus_antwort(portal: str, antwort: dict, max_text: int = 4000) -> list[dict]:
    """Alle Stellen einer Ergebnisseite im gemeinsamen Format."""
    daten = _daten(antwort)
    stellen: list[dict] = []

    if portal in ("indeed", "stepstone"):
        for job in (daten or {}).get("jobs") or []:
            firma = job.get("company") or {}
            ort = job.get("location") or {}
            if not isinstance(ort, dict):
                ort = {"formatted": str(ort)}
            website = firma.get("website") or firma.get("url") or ""
            stellen.append({
                "portal": portal,
                "portal_id": str(job.get("id") or job.get("url") or ""),
                "titel": (job.get("title") or "").strip(),
                "firma": (firma.get("name") or "").strip(),
                "ort": ort.get("city") or ort.get("formatted") or "",
                "plz": ort.get("postal_code") or "",
                "land": (ort.get("country") or "").upper()[:2],
                "veroeffentlicht": _datum(job.get("date_published") or job.get("date_posted")),
                "url": _url(job.get("url")) or (f"https://de.indeed.com/viewjob?jk={job['id']}"
                                                if portal == "indeed" and job.get("id") else ""),
                "bewerben_url": _url(job.get("apply_url")),
                "website": website if _ist_firmenseite(website) else "",
                "gehalt": _gehalt(job.get("salary")),
                "beschreibung": beschreibung_bereinigen(job.get("description_html") or job.get("description"),
                                                        max_text),
                "raw": json.dumps(job, ensure_ascii=False),
            })

    elif portal == "arbeitsagentur":
        liste = (daten or {}).get("stellenangebote") or (daten or {}).get("ergebnisliste") or []
        for job in liste:
            refnr = job.get("refnr") or job.get("referenznummer") or ""
            ort = job.get("arbeitsort") or {}
            if not ort and job.get("stellenlokationen"):
                ort = (job["stellenlokationen"][0] or {}).get("adresse") or {}
            stellen.append({
                "portal": portal,
                "portal_id": str(refnr),
                "titel": (job.get("titel") or job.get("stellenangebotsTitel") or job.get("beruf") or "").strip(),
                "firma": (job.get("arbeitgeber") or job.get("firma") or "").strip(),
                "ort": ort.get("ort") or "",
                "plz": ort.get("plz") or "",
                "land": "DE",
                "veroeffentlicht": _datum(job.get("aktuelleVeroeffentlichungsdatum")
                                          or job.get("datumErsteVeroeffentlichung")),
                "url": f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}" if refnr else "",
                "bewerben_url": "",
                "website": "",
                "gehalt": "",
                "beschreibung": "",
                "raw": json.dumps(job, ensure_ascii=False),
            })

    elif portal == "kununu":
        liste = daten if isinstance(daten, list) else ((daten or {}).get("jobs") or [])
        for job in liste:
            firma = job.get("company") or {}
            website = firma.get("website") or ""
            stellen.append({
                "portal": portal,
                "portal_id": str(job.get("id") or job.get("url") or ""),
                "titel": (job.get("title") or "").strip(),
                "firma": (firma.get("name") or "").strip(),
                "ort": job.get("city") or "",
                "plz": "",
                "land": "",
                "veroeffentlicht": _datum(job.get("postedAt")),
                "url": _url(job.get("url")),
                "bewerben_url": "",
                "website": website if _ist_firmenseite(website) else "",
                "gehalt": "",
                "beschreibung": "",
                "raw": json.dumps(job, ensure_ascii=False),
            })

    return [s for s in stellen if s["portal_id"]]


# ---------------------------------------------------------------- Filter

def ist_personaldienstleister(firma: str) -> bool:
    name = f" {(firma or '').lower()} "
    return any(k in name for k in PERSONALDIENSTLEISTER)


def titel_enthaelt(titel: str, begriff: str) -> bool:
    """Begriff am Wortanfang der Stellenbezeichnung; Begriffe bis 3 Zeichen nur als ganzes Wort.

    So trifft „automatisier“ auf „Automatisierungsexperte“, „KI“ aber nicht auf „Kinder“
    und „AI“ nicht auf „Training“ oder „Supply Chain“.
    """
    rand = r"[a-z0-9äöüß]"
    muster = rf"(?<!{rand}){re.escape(begriff.lower())}" + (rf"(?!{rand})" if len(begriff) <= 3 else "")
    return re.search(muster, (titel or "").lower()) is not None


def ausschluss(stelle: dict, max_alter: int, heute: date | None = None,
               titel_ausschluss: Iterable[str] = (), titel_pflicht: Iterable[str] = ()) -> str | None:
    """Grund, warum eine Stelle nicht übernommen wird — None, wenn sie bleibt.

    `titel_ausschluss`: Wortteile, die in der Stellenbezeichnung nicht vorkommen dürfen
    (je Kampagne, z. B. „sps“ gegen Industrieautomation bei der Suche „Automation“).
    `titel_pflicht`: mindestens einer dieser Begriffe muss in der Stellenbezeichnung stehen —
    Indeed sucht unscharf und liefert zu „KI Manager“ auch „Sales Manager“.
    """
    if not stelle["firma"] and not firmen_host(stelle) and not bewerben_host(stelle):
        return "ohne Firmenname"
    if any(f in (stelle["firma"] or "").lower() for f in FREMD_DOMAINS_STELLEN):
        return "Jobbörse/Bewerbersystem statt Firma"
    if ist_personaldienstleister(stelle["firma"]):
        return "Personaldienstleister"
    titel = (stelle.get("titel") or "").lower()
    treffer = next((w for w in titel_ausschluss if w and w.lower() in titel), None)
    if treffer:
        return f"Titel enthält „{treffer}“"
    pflicht = [b for b in titel_pflicht if b]
    if pflicht and not any(titel_enthaelt(titel, b) for b in pflicht):
        return "Titel passt nicht zur Suche"
    if max_alter and stelle["veroeffentlicht"]:
        grenze = (heute or date.today()) - timedelta(days=max_alter)
        if stelle["veroeffentlicht"] < grenze.isoformat():
            return f"älter als {max_alter} Tage"
    return None


def _ist_firmenseite(url: str) -> bool:
    host = host_of(url)
    return bool(host) and "." in host and not any(f in host for f in FREMD_DOMAINS_STELLEN)


def firmen_host(stelle: dict) -> str:
    """Host der Firmen-Website, wenn das Portal sie nennt (nicht Jobbörse/Bewerbersystem)."""
    return registrable_domain(stelle.get("website")) if stelle.get("website") else ""


def bewerben_host(stelle: dict) -> str:
    """Host des Bewerbungslinks, wenn er auf eine eigene Seite zeigt — nur ein Hinweis, kein Beleg."""
    url = stelle.get("bewerben_url") or ""
    # jobs.firma.de / karriere.firma.de → firma.de
    return registrable_domain(url) if _ist_firmenseite(url) else ""


# ---------------------------------------------------------------- Text

_TAGS = re.compile(r"<[^>]+>")
_BLOCK = re.compile(r"</?(p|div|li|ul|ol|br|h\d|tr|section)[^>]*>", re.IGNORECASE)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_TELEFON = re.compile(r"(?:\+|\b0)[\d\s/().-]{6,}\d")
# Ab hier folgt meist der Kontaktblock mit Namen und Adressen — wird nicht übernommen
_KONTAKT = re.compile(
    r"(ansprechpartner|ihr kontakt|kontaktperson|bei fragen|haben wir ihr interesse|"
    r"bei interesse|bewerben sie sich|ihre bewerbung an|bewerbungsunterlagen|"
    r"wir freuen uns auf ihre bewerbung|wir freuen uns auf deine bewerbung|jetzt bewerben)",
    re.IGNORECASE)


def beschreibung_bereinigen(roh: Any, max_text: int = 4000) -> str:
    """Stellentext als Klartext, ohne Kontaktblock, E-Mail-Adressen und Telefonnummern.

    Kontaktpersonen aus Stellenanzeigen werden nicht übernommen (wissen/05, Rechtliches).
    Der Text dient nur dem Opener: 1–2 Anforderungen an Bewerber.
    """
    if not roh:
        return ""
    text = _BLOCK.sub("\n", str(roh))
    text = html.unescape(_TAGS.sub(" ", text))
    # Steht der Hinweis ganz am Anfang (Kopfzeile „Jetzt bewerben“), bliebe sonst nichts übrig
    treffer = next((t for t in _KONTAKT.finditer(text) if len(text[:t.start()].strip()) >= 20), None)
    if treffer:
        text = text[:treffer.start()]
    text = _EMAIL.sub("", text)
    text = _TELEFON.sub("", text)
    zeilen = [re.sub(r"[ \t\xa0]+", " ", z).strip() for z in text.splitlines()]
    text = "\n".join(z for z in zeilen if z)
    return text[:max_text].strip()


# ---------------------------------------------------------------- Firma

_RECHTSFORMEN = re.compile(
    r"\b(gmbh|mbh|ggmbh|ag|se|kg|kgaa|ohg|gbr|ug|e\.?\s?k\.?|e\.?\s?v\.?|co\.?|inh\.?|"
    r"haftungsbeschränkt|haftungsbeschraenkt|gesellschaft|und|&)\b", re.IGNORECASE)


def firmen_name_schluessel(firma: str) -> str:
    """Firmenname ohne Rechtsform, Zusätze und Satzzeichen — zum Zusammenführen von Stellen."""
    name = (firma or "").lower()
    name = re.split(r"\s+(niederlassung|nl|standort|filiale|zweigniederlassung)\b", name)[0]
    name = _RECHTSFORMEN.sub(" ", name)
    name = re.sub(r"[^\wäöüß]+", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def beste_stelle(stellen: Iterable[dict]) -> dict:
    """Die Stelle, die die Firma im Export vertritt: mit Stellentext vor ohne, dann die neueste."""
    return sorted(stellen, key=lambda s: (bool(s.get("beschreibung")), s.get("veroeffentlicht") or ""),
                  reverse=True)[0]
