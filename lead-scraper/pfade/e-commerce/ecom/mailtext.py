"""Mailtext des Kunden: prüfen und je Lead ausfüllen (nicht in Clay).

Format (UTF-8-Text): erste nicht-leere Zeile `Betreff: …`, Leerzeile, dann der Text.
Platzhalter heißen wie die Exportspalten, z. B. `{{Ansprache Normal}}` und `{{Personalisierung}}`.
Gespeichert wird der Text per `python3 -m ecom set-mailtext <datei>` in der Lauf-Datenbank
(`meta.mailtext`); der Export füllt ihn je Lead in die Spalten „Betreff“ und „Mailtext“.
"""
from __future__ import annotations

import re
import unicodedata

from . import transforms as T
from .config import CONFIG
from .llm import platzhalter, render

# Platzhalter → Lead-Feld (gleiche Bezeichnungen wie die Exportspalten in export.py)
PLATZHALTER = {
    "Ansprache Formal": "ansprache_formal",
    "Ansprache Normal": "ansprache_normal",
    "Ansprache Guten Tag": "ansprache_normal_gt",
    "Ansprache Persönlich": "ansprache_persoenlich",
    "Personalisierung": "personalisierung",
    "Firmenname": "firmenname_final",      # leer → Firmenname aus der Import-Liste
    "Website": "website_final",
    "Videotitel": "video_title",
    "Anrede": "anrede",
    "Vorname": "first_name",
    "Nachname": "last_name",
}
ANSPRACHEN = ("Ansprache Formal", "Ansprache Normal", "Ansprache Guten Tag", "Ansprache Persönlich")
# Leer, wenn das Impressum keine Geschäftsführung nennt (vor allem info@-Leads);
# die Ansprachen haben dort eine neutrale Form („Guten Tag“)
LEER_OHNE_NAME = ("Anrede", "Vorname", "Nachname")
# {Vorname} statt {{Vorname}}: einfache Klammern, die nicht Teil von {{…}} sind
_EINFACHE_KLAMMER = re.compile(r"(?<!\{)\{\s*([^{}]+?)\s*\}(?!\})")

# Erfundener Beispiel-Lead für die Vorschau nach `set-mailtext`
BEISPIEL_LEAD = {
    "anrede": "Herr",
    "first_name": "Max",
    "last_name": "Mustermann",
    "firmenname_final": "Beispiel Shop GmbH",
    "website_final": "https://www.beispiel-shop.de",
    "personalisierung": "bei Ihnen fällt sofort auf, dass jede Kategorie eine eigene Größenberatung hat "
                        "und die Lieferzeit direkt am Produkt steht.",
    "video_title": "Video für Max Mustermann von Beispiel Shop",
    **T.ansprachen("Herr", "Max", "Mustermann", "max.mustermann@beispiel-shop.de"),
}


def _klammer(name: str) -> str:
    return "{{" + name + "}}"


def normalisieren(text: str) -> str:
    """Zeilenenden vereinheitlichen und Umlaute zusammensetzen (macOS speichert teils „o + ¨“)."""
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    return unicodedata.normalize("NFC", text).strip()


def zerlegen(text: str) -> tuple[str | None, str]:
    """(Betreff, Text). Betreff ist None, wenn die erste nicht-leere Zeile nicht mit „Betreff:“ beginnt."""
    zeilen = normalisieren(text).split("\n")
    erste = zeilen[0].strip()
    if not erste.lower().startswith("betreff:"):
        return None, "\n".join(zeilen).strip()
    return erste[len("betreff:"):].strip(), "\n".join(zeilen[1:]).strip()


def pruefen(text: str) -> tuple[list[str], list[str]]:
    """(Fehler, Hinweise). Fehler verhindern das Speichern bzw. den Export."""
    fehler: list[str] = []
    hinweise: list[str] = []
    gesamt = normalisieren(text)
    betreff, body = zerlegen(gesamt)

    if betreff is None:
        fehler.append("Die erste Zeile muss mit „Betreff:“ beginnen, z. B. „Betreff: Kurze Frage zu "
                      "{{Firmenname}}“. Danach eine Leerzeile, dann der Text.")
    elif not betreff:
        fehler.append("Der Betreff ist leer.")
    if not body:
        fehler.append("Unter dem Betreff fehlt der eigentliche Mailtext.")

    genutzt = platzhalter(gesamt)
    erlaubt = ", ".join(_klammer(n) for n in PLATZHALTER)
    for name in genutzt:
        if name not in PLATZHALTER:
            fehler.append(f"Unbekannter Platzhalter {_klammer(name)} (Tippfehler?). Erlaubt sind: {erlaubt}")
    rest = render(gesamt, dict.fromkeys(genutzt, ""))   # alle vollständigen Platzhalter entfernt
    if "{{" in rest or "}}" in rest:
        fehler.append("Ein Platzhalter ist unvollständig: Jeder braucht zwei geschweifte Klammern auf "
                      "jeder Seite, z. B. {{Firmenname}}.")
    bekannt = {n.lower(): n for n in PLATZHALTER}
    for name in dict.fromkeys(m.group(1) for m in _EINFACHE_KLAMMER.finditer(rest)):
        if name.lower() in bekannt:
            fehler.append(f"{{{name}}} hat nur eine Klammer auf jeder Seite – richtig: "
                          f"{_klammer(bekannt[name.lower()])}.")
        else:
            hinweise.append(f"{{{name}}} in einfachen Klammern wird nicht ersetzt und bleibt so in der Mail stehen.")

    im_text = platzhalter(body)
    if CONFIG.do_personalisierung and "Personalisierung" not in im_text:
        fehler.append("{{Personalisierung}} fehlt im Text. Der persönliche Satz gehört direkt unter die "
                      "Begrüßung (er beginnt klein und setzt die Begrüßungszeile fort).")
    if not any(a in im_text for a in ANSPRACHEN):
        fehler.append("Im Text fehlt die Begrüßung. Bitte einen dieser Platzhalter als erste Zeile nutzen: "
                      + ", ".join(_klammer(a) for a in ANSPRACHEN) + " (z. B. „{{Ansprache Normal}},“).")
    else:
        fehler += _position_pruefen(body, im_text)

    for name in LEER_OHNE_NAME:
        if name in genutzt:
            hinweise.append(f"{_klammer(name)} ist leer, wenn das Impressum keine Geschäftsführung nennt (betrifft "
                            "vor allem info@-Adressen). Besser die {{Ansprache …}}-Platzhalter nutzen – die "
                            "haben dort eine neutrale Form wie „Guten Tag“.")
    if "Videotitel" in genutzt and not CONFIG.do_video_title:
        hinweise.append("{{Videotitel}} bleibt leer, weil Videotitel ausgeschaltet sind (DO_VIDEO_TITLE=false).")
    if "Personalisierung" in genutzt and not CONFIG.do_personalisierung:
        hinweise.append("{{Personalisierung}} bleibt leer, weil die Personalisierung ausgeschaltet ist "
                        "(DO_PERSONALISIERUNG=false).")
    return fehler, hinweise


def _position_pruefen(body: str, im_text: list[str]) -> list[str]:
    """Begrüßung als erste Zeile, persönlicher Satz direkt danach (er beginnt klein)."""
    zeilen = [z.strip() for z in body.split("\n") if z.strip()]
    if not any(zeilen[0].startswith(_klammer(a)) for a in ANSPRACHEN):
        return ["Die Begrüßung muss die erste Zeile unter dem Betreff sein, z. B. „{{Ansprache Normal}},“."]
    if CONFIG.do_personalisierung and "Personalisierung" in im_text:
        naechste = zeilen[1] if len(zeilen) > 1 else ""
        if _klammer("Personalisierung") not in zeilen[0] and not naechste.startswith(_klammer("Personalisierung")):
            return ["{{Personalisierung}} muss direkt unter der Begrüßung stehen, als eigener Absatz nach "
                    "einer Leerzeile. Der Satz beginnt klein und setzt die Begrüßung fort."]
    return []


def rendern(text: str, lead: dict) -> tuple[str, str]:
    """(Betreff, Mailtext) für einen Lead."""
    werte = {name: lead.get(feld) for name, feld in PLATZHALTER.items()}
    werte["Firmenname"] = lead.get("firmenname_final") or lead.get("firmenname") or ""
    betreff, body = zerlegen(text)
    return render(betreff or "", werte), render(body, werte)
