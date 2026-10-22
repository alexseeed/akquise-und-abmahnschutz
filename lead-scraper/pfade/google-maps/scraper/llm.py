"""Die vier KI-Schritte aus dem Workbook — Prompts kommen unverändert aus prompts/.

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
from .config import CONFIG, PROMPTS_DIR

log = logging.getLogger(__name__)

_PLACEHOLDER = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict:
    return json.loads((PROMPTS_DIR / name).read_text(encoding="utf-8"))


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
                model=model or CONFIG.model_domain,
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
                model=CONFIG.model_default,
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
