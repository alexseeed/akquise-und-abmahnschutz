"""Die KI-Spalten des Workbooks — Clay-Prompts und alle Schemas kommen unverändert aus prompts/.

Ausnahme: Shop-Profil und Personalisierung sind auftragsspezifisch. Ihre Prompts stehen in
der Lauf-Datenbank (`meta`, gesetzt per `python3 -m ecom set-prompt …`) und werden hier als
Vorlage übergeben. `prompts/personalisierung.txt` bleibt nur als Clay-Strukturvorlage liegen.

Konvention: Jede Methode gibt `None` zurück, wenn der Aufruf **fehlgeschlagen** ist,
und einen (ggf. leeren) Wert, wenn das Modell geantwortet hat. Nur so kann die
Pipeline zwischen „erneut versuchen“ und „hat nichts gefunden“ unterscheiden.
Ausnahme: Lehnt der Dienst den Zugang ab (Schlüssel, Guthaben), fliegt `ZugangGesperrt`
durch – das betrifft jede Zeile, die Stufe bricht ab, ohne Fehlversuche zu zählen.
"""
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from typing import Any

from .clients import OpenAIClient, SkaelClient, pruefe_zugang
from .config import CONFIG, PROMPTS_DIR

log = logging.getLogger(__name__)

_PLACEHOLDER = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")

# Clays Claygent bringt einen eigenen Systemprompt mit, der nicht exportierbar ist.
# Der Skael-Agent braucht einen; dieser beschreibt nur die Rolle, die Aufgabe steht
# wörtlich im Nutzer-Prompt aus prompts/company_domain.txt.
DOMAIN_AGENT_SYSTEM = (
    "You are a web research agent. Use Google search and read web pages to find the "
    "official website of the company named in the task. Answer only with the requested JSON."
)


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict:
    return json.loads((PROMPTS_DIR / name).read_text(encoding="utf-8"))


# Platzhalter der auftragsspezifischen Prompts: (Pflicht, alle bekannten)
PROMPT_PLATZHALTER = {
    "shopprofil": ("BodyText", {"BodyText", "website [Final]"}),
    "personalisierung": ("Bodytext Website", {"Bodytext Website", "Mailtext", "Firmenname"}),
}


def platzhalter(template: str) -> list[str]:
    """Namen aller {{Platzhalter}} in Reihenfolge des ersten Auftretens."""
    return list(dict.fromkeys(m.group(1) for m in _PLACEHOLDER.finditer(template)))


def render(template: str, values: dict[str, Any]) -> str:
    """Ersetzt {{Spaltenname}} durch den Wert.

    Unbekannte Platzhalter bleiben stehen: Der Clay-Personalisierungs-Prompt enthält
    `{{Anrede}} {{lastName}}` als wörtlichen Beispieltext. Eingesetzte Werte werden nicht
    erneut ersetzt – ein Mailtext mit `{{Personalisierung}}` erscheint im Prompt wörtlich.
    """
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            return match.group(0)
        value = values[key]
        return "" if value is None else str(value)

    return _PLACEHOLDER.sub(repl, template)


class LLM:
    """Kapselt die KI-Spalten aus Import und ANREICHERUNG."""

    def __init__(self, client: OpenAIClient | None = None, skael: SkaelClient | None = None):
        self.client = client or OpenAIClient()
        self.skael = skael or SkaelClient()

    def _complete(self, prompt_file: str, values: dict, schema_file: str, **kwargs) -> Any:
        return self._complete_template(load_prompt(prompt_file), values, schema_file, **kwargs)

    def _complete_template(self, template: str, values: dict, schema_file: str, **kwargs) -> Any:
        return self.client.complete(
            render(template, values),
            model=CONFIG.model_default,
            json_schema=load_schema(schema_file),
            schema_name=schema_file.split(".")[0],
            **kwargs,
        )

    # --- Clay Import/ANREICHERUNG `Company Domain` (Claygent, gemini-2.5-flash-lite) ---
    def company_domain(self, firmenname: str) -> str | None:
        prompt = render(load_prompt("company_domain.txt"), {"Firmenname": firmenname})
        try:
            out = self.skael.ai_research_agent(
                DOMAIN_AGENT_SYSTEM, prompt, load_schema("company_domain.schema.json"),
                max_steps=CONFIG.domain_agent_max_steps, model=CONFIG.model_domain_agent,
            )
        except Exception as exc:  # noqa: BLE001
            pruefe_zugang(exc, "Skael")
            log.warning("company_domain fehlgeschlagen für %r: %s", firmenname, exc)
            return None
        return (out or {}).get("response", "") or "" if isinstance(out, dict) else ""

    # --- Clay Import `ICP ONLINE SHOP` (gpt-4o-mini) ---------------------
    def icp_online_shop(self, bodytext: str, website: str) -> dict | None:
        try:
            result = self._complete("icp_online_shop.txt",
                                    {"BodyText": bodytext, "website [Final]": website},
                                    "icp_online_shop.schema.json")
        except Exception as exc:  # noqa: BLE001
            pruefe_zugang(exc, "OpenAI")
            log.warning("icp_online_shop fehlgeschlagen für %s: %s", website, exc)
            return None
        return result if isinstance(result, dict) else {}

    # --- Shop-Profil des Kunden (nicht in Clay; Vertrag wie der Maps-ICP-Builder) ---
    def shopprofil(self, bodytext: str, website: str, template: str) -> dict | None:
        try:
            result = self._complete_template(template,
                                             {"BodyText": bodytext, "website [Final]": website},
                                             "shopprofil.schema.json")
        except Exception as exc:  # noqa: BLE001
            pruefe_zugang(exc, "OpenAI")
            log.warning("shopprofil fehlgeschlagen für %s: %s", website, exc)
            return None
        return result if isinstance(result, dict) else {}

    # --- Clay ANREICHERUNG `Anrede [Prompt] (2)` -------------------------
    def anrede(self, first_name: str) -> dict | None:
        try:
            result = self._complete("anrede.txt", {"First Name [GF]": first_name}, "anrede.schema.json")
        except Exception as exc:  # noqa: BLE001
            pruefe_zugang(exc, "OpenAI")
            log.warning("anrede fehlgeschlagen für %r: %s", first_name, exc)
            return None
        return result if isinstance(result, dict) else {}

    # --- Clay ANREICHERUNG `Personalisierung AI` (Prompt aus dem Auftrag) ---
    def personalisierung(self, bodytext: str, template: str, mailtext: str = "",
                         firmenname: str = "") -> str | None:
        try:
            result = self._complete_template(
                template, {"Bodytext Website": bodytext, "Mailtext": mailtext, "Firmenname": firmenname},
                "personalisierung.schema.json", temperature=0.7)
        except Exception as exc:  # noqa: BLE001
            pruefe_zugang(exc, "OpenAI")
            log.warning("personalisierung fehlgeschlagen: %s", exc)
            return None
        if isinstance(result, dict):
            return result.get("complimentText", "") or ""
        return str(result or "")

    # --- Clay ANREICHERUNG `Cleaned Video Title` --------------------------
    def video_title(self, video_title_input: str) -> dict | None:
        try:
            result = self._complete("video_title_cleanup.txt", {"Video Title Input": video_title_input},
                                    "video_title_cleanup.schema.json")
        except Exception as exc:  # noqa: BLE001
            pruefe_zugang(exc, "OpenAI")
            log.warning("video_title fehlgeschlagen: %s", exc)
            return None
        return result if isinstance(result, dict) else {}
