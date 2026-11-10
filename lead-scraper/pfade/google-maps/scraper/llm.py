"""Die KI-Schritte — Prompts kommen aus prompts/ bzw. kampagnen/<name>/prompts/.

Google Maps: Domain, Anrede, Einordnung, Personalisierung, Videotitel.
Recruiting: Stellenanalyse, Jobtitel-Normalisierung, Stellen-Opener, Website-Satz (NK).
Stellensuche: Jobtitel-Normalisierung, Stellen-Opener, Größen-Check.

Konvention: Jede Methode gibt `None` zurück, wenn der Aufruf **fehlgeschlagen** ist,
und einen (ggf. leeren) Wert, wenn das Modell geantwortet hat. Nur so kann die
Pipeline zwischen „erneut versuchen" und „hat nichts gefunden" unterscheiden.
"""
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from typing import Any

from .clients import OpenAIClient
from .config import CONFIG, PROMPT_DIRS

log = logging.getLogger(__name__)

_PLACEHOLDER = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")


def prompt_pfad(name: str):
    """Kampagnen-Prompt vor Standard-Prompt: kampagnen/<name>/prompts/ → prompts/."""
    for ordner in PROMPT_DIRS:
        if (ordner / name).exists():
            return ordner / name
    raise FileNotFoundError(f"Prompt '{name}' weder in {' noch in '.join(str(o) for o in PROMPT_DIRS)}")


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    return prompt_pfad(name).read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict:
    return json.loads(prompt_pfad(name).read_text(encoding="utf-8"))


def render(template: str, values: dict[str, Any]) -> str:
    """Ersetzt {{Spaltenname}} durch den Wert; unbekannte Platzhalter werden geleert."""
    def repl(match: re.Match[str]) -> str:
        value = values.get(match.group(1), "")
        return "" if value is None else str(value)

    return _PLACEHOLDER.sub(repl, template)


class LLM:
    """Kapselt die vier Clay-KI-Spalten."""

    def __init__(self, client: OpenAIClient | None = None):
        self.client = client or OpenAIClient()

    # --- Clay: `Domain URL` (gpt-4o-mini) / `Company Domain` (gpt-4.1-mini) ---
    def company_domain(self, firmenname: str, *, model: str | None = None) -> str | None:
        prompt = render(load_prompt("company_domain.txt"), {"Firmenname": firmenname})
        schema = {
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    "description": "Die gefundene Domain der Firma, sonst leerer String.",
                }
            },
            "required": ["response"],
            "additionalProperties": False,
        }
        try:
            result = self.client.complete(
                prompt,
                model=model or CONFIG.openai_model_websuche,
                json_schema=schema,
                schema_name="company_domain",
                web_search=True,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("company_domain fehlgeschlagen für %r: %s", firmenname, exc)
            return None
        return (result or {}).get("response", "") if isinstance(result, dict) else ""

    # --- Clay: `Anrede [Prompt] (2)` ------------------------------------
    def anrede(self, first_name: str) -> dict | None:
        prompt = render(load_prompt("anrede.txt"), {"First Name [GF]": first_name})
        try:
            result = self.client.complete(
                prompt,
                model=CONFIG.model_default,
                json_schema=load_schema("anrede.schema.json"),
                schema_name="anrede",
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("anrede fehlgeschlagen für %r: %s", first_name, exc)
            return None
        return result if isinstance(result, dict) else {}

    # --- Einordnung des Vertriebskanals (Temperatur 0 = reproduzierbar) ---
    def pain_kategorie(self, bodytext: str, links: str = "") -> dict | None:
        """Ordnet den Vertriebskanal ein. Kein Werbetext.

        Bewusst von der Textgenerierung getrennt: Die Einordnung braucht
        Temperatur 0, damit dieselbe Website immer dasselbe Ergebnis liefert.
        Bei 0.7 schwankte sie in Messungen bei 6 von 10 identischen Eingaben.
        """
        prompt = render(load_prompt("pain_kategorie.txt"),
                        {"Bodytext Website": bodytext, "Links": links})
        try:
            result = self.client.complete(
                prompt,
                model=CONFIG.model_default,
                json_schema=load_schema("pain_kategorie.schema.json"),
                schema_name="pain_kategorie",
                temperature=0.0,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("pain_kategorie fehlgeschlagen: %s", exc)
            return None
        if not isinstance(result, dict):
            return {"kategorie": "", "netz": False, "beleg": ""}
        return {
            "kategorie": result.get("painCategory", "") or "",
            "netz": bool(result.get("partnernetzBelegt")),
            "beleg": result.get("beleg", "") or "",
        }

    # --- Clay: `Personalisierung AI` (Temperatur 0.7 = lebendige Sprache) ---
    def personalisierung(self, bodytext: str, links: str = "", kategorie: str = "") -> str | None:
        """Schreibt den Einstiegssatz zur bereits feststehenden Kategorie."""
        prompt = render(load_prompt("personalisierung.txt"),
                        {"Bodytext Website": bodytext, "Links": links, "Kategorie": kategorie})
        try:
            result = self.client.complete(
                prompt,
                model=CONFIG.model_personalisierung,
                json_schema=load_schema("personalisierung.schema.json"),
                schema_name="personalisierung",
                temperature=0.7,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("personalisierung fehlgeschlagen: %s", exc)
            return None
        if isinstance(result, dict):
            return result.get("complimentText", "") or ""
        return str(result or "")

    # --- Recruiting: Clay DATENSÄTZE.`Stelle` (dort Claygent) --------------
    def stellenanalyse(self, website: str, webseiteninhalt: str, berufe: str = "") -> dict | None:
        """Sucht genau eine passende offene Stelle im Text von Startseite und Karriere-Seiten.

        Clay lässt einen Recherche-Agenten selbst browsen. Hier holt Stufe 3e die Seiten
        vorher ab und gibt ihren Text mit. `berufe`: gesuchte Berufe der Kampagne (`init --berufe`),
        eine Zeile je Beruf, Reihenfolge = Priorität.
        """
        prompt = render(load_prompt("stellenanalyse.txt"),
                        {"Website final": website, "Webseiteninhalt": webseiteninhalt,
                         "Gesuchte Berufe": berufe})
        try:
            result = self.client.complete(
                prompt,
                model=CONFIG.model_default,
                json_schema=load_schema("stellenanalyse.schema.json"),
                schema_name="stellenanalyse",
                temperature=0.0,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("stellenanalyse fehlgeschlagen für %r: %s", website, exc)
            return None
        return result if isinstance(result, dict) else {}

    # --- Recruiting/Stellensuche: Clay ANREICHERUNG.`Normalisierter Jobtitel` ---
    def jobtitel_normalisieren(self, job_title: str) -> str | None:
        prompt = render(load_prompt("jobtitel_normalisierung.txt"), {"JOB TITLE": job_title})
        try:
            result = self.client.complete(
                prompt,
                model=CONFIG.model_default,
                json_schema=load_schema("jobtitel_normalisierung.schema.json"),
                schema_name="jobtitel",
                temperature=0.0,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("jobtitel_normalisieren fehlgeschlagen für %r: %s", job_title, exc)
            return None
        return (result.get("normalisierterTitel", "") or "") if isinstance(result, dict) else ""

    # --- Recruiting/Stellensuche: Clay ANREICHERUNG.`Personalisierung AI` (RC) ---
    def stellen_opener(self, job_titel: str, job_description: str, *,
                       prompt_datei: str = "personalisierung_stellenanzeige.txt",
                       original: str = "") -> str | None:
        """„ich habe gesehen, dass Sie … suchen, …“ — ein Satz zur offenen Stelle.

        `prompt_datei` je Kampagne wählbar (run_meta `opener_prompt`), `original` = Stellenbezeichnung
        aus der Anzeige für Prompts, die die Rolle selbst bereinigen.
        """
        prompt = render(load_prompt(prompt_datei),
                        {"Job Titel": job_titel, "JOB DESCRIPTION": job_description,
                         "Stelle (Original)": original})
        try:
            result = self.client.complete(
                prompt,
                model=CONFIG.model_personalisierung,
                json_schema=load_schema("personalisierung.schema.json"),
                schema_name="personalisierung",
                temperature=0.7,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("stellen_opener fehlgeschlagen: %s", exc)
            return None
        if isinstance(result, dict):
            return result.get("complimentText", "") or ""
        return str(result or "")

    # --- Recruiting NK: Website-Satz für passende Firmen ohne offene Stelle ---
    def personalisierung_website(self, bodytext: str) -> str | None:
        prompt = render(load_prompt("personalisierung_website.txt"), {"Bodytext Website": bodytext})
        try:
            result = self.client.complete(
                prompt,
                model=CONFIG.model_personalisierung,
                json_schema=load_schema("personalisierung.schema.json"),
                schema_name="personalisierung",
                temperature=0.7,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("personalisierung_website fehlgeschlagen: %s", exc)
            return None
        if isinstance(result, dict):
            return result.get("complimentText", "") or ""
        return str(result or "")

    # --- Stellensuche: Größen-Check vor der bezahlten Website-Suche --------
    def groessen_check(self, firmenname: str, website: str = "", ort: str = "") -> dict | None:
        """Konzern, öffentliche Hand/Verband, IT-Wettbewerber oder Mittelstand — aus Modellwissen.

        Kein Website-Abruf: Startseiten großer Firmen zeigen die Größe selten. Temperatur 0,
        Modell MODEL_GROESSE (gpt-4o-mini war im Vergleich zu nachsichtig, gpt-4.1 gemessen gut).
        """
        prompt = render(load_prompt("groessen_check.txt"),
                        {"Firmenname": firmenname, "Website": website or "unbekannt", "Ort": ort or "unbekannt"})
        try:
            result = self.client.complete(
                prompt,
                model=CONFIG.model_groesse,
                json_schema=load_schema("groessen_check.schema.json"),
                schema_name="groesse",
                temperature=0.0,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("groessen_check fehlgeschlagen für %r: %s", firmenname, exc)
            return None
        return result if isinstance(result, dict) else {}

    # --- Testballon: Fallback bei zu wenigen Stellen (keine Clay-Entsprechung) ---
    def suchbegriffe_synonyme(self, suchbegriffe: list[str], anzahl: int = 5) -> list[str] | None:
        """Weitere Suchbegriffe für dieselben Stellen; ohne die bisherigen, höchstens `anzahl`."""
        prompt = render(load_prompt("suchbegriffe_synonyme.txt"),
                        {"Suchbegriffe": "\n".join(suchbegriffe), "Anzahl": str(anzahl)})
        try:
            result = self.client.complete(
                prompt,
                model=CONFIG.model_default,
                json_schema=load_schema("suchbegriffe_synonyme.schema.json"),
                schema_name="suchbegriffe",
                temperature=0.0,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("suchbegriffe_synonyme fehlgeschlagen: %s", exc)
            return None
        bekannt = {s.strip().lower() for s in suchbegriffe}
        neu: list[str] = []
        for begriff in (result.get("suchbegriffe") or []) if isinstance(result, dict) else []:
            begriff = str(begriff).strip()
            if begriff and begriff.lower() not in bekannt and begriff.lower() not in {n.lower() for n in neu}:
                neu.append(begriff)
        return neu[:anzahl]

    # --- Clay: `Cleaned Video Title` ------------------------------------
    def video_title(self, video_title_input: str) -> dict | None:
        prompt = render(
            load_prompt("video_title_cleanup.txt"), {"Video Title Input": video_title_input}
        )
        try:
            result = self.client.complete(
                prompt,
                model=CONFIG.model_default,
                json_schema=load_schema("video_title_cleanup.schema.json"),
                schema_name="video_title",
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("video_title fehlgeschlagen: %s", exc)
            return None
        return result if isinstance(result, dict) else {}
