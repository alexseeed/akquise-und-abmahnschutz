"""HTTP-Clients für Skael, OpenAI und Findymail — inkl. Rate-Limit und Retry.

Übernommen aus pfade/google-maps/scraper/clients.py, ergänzt um `webtraffic` und (am Dateiende)
die Erkennung von Zugangsfehlern. Änderungen am gemeinsamen Teil in beiden Dateien nachziehen.
"""
from __future__ import annotations

import json
import logging
import random
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .config import CONFIG

log = logging.getLogger(__name__)


class RateLimiter:
    """Token-Bucket, thread-safe. rate = erlaubte Requests pro Sekunde."""

    def __init__(self, rate_per_sec: float):
        self.min_interval = 1.0 / rate_per_sec if rate_per_sec > 0 else 0.0
        self._lock = threading.Lock()
        self._next_slot = 0.0

    def acquire(self) -> None:
        if self.min_interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            wait = max(0.0, self._next_slot - now)
            self._next_slot = max(now, self._next_slot) + self.min_interval
        if wait:
            time.sleep(wait)


class ApiError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status = status
        self.payload = payload


def _request(
    url: str,
    *,
    method: str = "POST",
    headers: dict[str, str] | None = None,
    body: dict | None = None,
    timeout: int | None = None,
) -> tuple[int, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout or CONFIG.http_timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = raw
        return exc.code, payload
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        # Netzwerkfehler → Status 0, damit die Retry-Schleife greift
        return 0, {"message": f"network error: {exc}"}


class SkaelClient:
    """Client für https://api.skael.de — synchroner Modus, wie im Clay-Workbook."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or CONFIG.skael_api_key
        self.base = CONFIG.skael_base_url.rstrip("/")
        self.limiter = RateLimiter(CONFIG.skael_rate_limit_per_sec)

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    def call(
        self,
        endpoint: str,
        payload: dict,
        *,
        as_query: bool = False,
        timeout: int | None = None,
    ) -> dict:
        """Ruft /api/enrichments/<endpoint> auf und liefert das ausgepackte `output`.

        as_query=True übergibt die Parameter als Query-String statt im Body
        (im Google-Maps-Pfad für maps_search und icp_checker; hier ungenutzt).
        """
        url = f"{self.base}/api/enrichments/{endpoint}"
        body: dict | None = payload
        if as_query:
            clean = {k: v for k, v in payload.items() if v is not None}
            url = f"{url}?{urllib.parse.urlencode(clean)}"
            body = {}

        delay = 1.0
        last_error: str = ""
        for attempt in range(1, CONFIG.max_retries + 1):
            self.limiter.acquire()
            status, data = _request(url, headers=self._headers(), body=body, timeout=timeout)

            if status == 200:
                return self._unwrap(data)

            if status == 202:
                resource_id = self._resource_id(data)
                if resource_id:
                    polled = self._poll(endpoint, resource_id)
                    if polled is not None:
                        return polled
                last_error = "202 timeout ohne verwertbares Ergebnis"

            elif status == 429:
                last_error = "429 rate limited"

            elif status == 422:
                failed = isinstance(data, dict) and isinstance(data.get("data"), dict)
                if failed and data["data"].get("status") == "failed":
                    raise ApiError(
                        data["data"].get("error_message") or "enrichment failed",
                        status,
                        data,
                    )
                raise ApiError(
                    (data or {}).get("message", "validation error") if isinstance(data, dict) else "validation error",
                    status,
                    data,
                )

            elif 400 <= status < 500:
                raise ApiError(f"HTTP {status}", status, data)

            else:
                last_error = f"HTTP {status}"

            if attempt < CONFIG.max_retries:
                sleep_for = delay + random.uniform(0, 0.4)
                log.warning("%s: %s — retry %s/%s in %.1fs", endpoint, last_error, attempt, CONFIG.max_retries, sleep_for)
                time.sleep(sleep_for)
                delay = min(delay * 2, 30.0)

        raise ApiError(f"{endpoint}: {last_error} nach {CONFIG.max_retries} Versuchen")

    def _poll(self, endpoint: str, resource_id: int | str) -> dict | None:
        """Long-Polling gemäß API-Guide: GET /api/<resource>/{id}?wait=true&wait_time=50."""
        url = f"{self.base}/api/{endpoint}/{resource_id}?wait=true&wait_time=50"
        for _ in range(20):
            self.limiter.acquire()
            status, data = _request(url, method="GET", headers=self._headers(), body=None)
            if status == 200:
                return self._unwrap(data)
            if status == 202:
                continue
            if status == 422:
                raise ApiError("enrichment failed beim Polling", status, data)
            return None
        return None

    @staticmethod
    def _resource_id(data: Any) -> int | str | None:
        if isinstance(data, dict):
            inner = data.get("data")
            if isinstance(inner, dict):
                return inner.get("id")
            return data.get("id")
        return None

    @staticmethod
    def _unwrap(data: Any) -> dict:
        """Liefert das eigentliche Ergebnis-Objekt.

        Die API antwortet je nach Endpunkt entweder mit {"data": {..., "output": {...}}}
        oder direkt mit dem Output-Objekt.
        """
        if not isinstance(data, dict):
            return {}
        inner = data.get("data")
        if isinstance(inner, dict):
            if inner.get("status") == "failed":
                raise ApiError(inner.get("error_message") or "failed", 422, data)
            out = inner.get("output")
            return out if isinstance(out, dict) else (out or {})
        if "output" in data and isinstance(data["output"], dict):
            return data["output"]
        return data

    # --- Endpunkte ------------------------------------------------------

    def imprint_extractor(self, domain: str) -> dict:
        return self.call("imprint_extractor", {"domain": domain})

    def find_email_person(self, domain: str, full_name: str) -> dict:
        return self.call("find_email_person", {"domain": domain, "full_name": full_name})

    def verify_email(self, email: str) -> dict:
        return self.call("verify_email", {"email": email})

    def web_scraper(self, url: str) -> dict:
        return self.call("web_scraper", {"url": url})

    def webtraffic(self, domain: str) -> dict:
        """SimilarWeb-Daten; `found: false` ist ein gültiges Ergebnis (kostenlos), kein Fehler."""
        return self.call("webtraffic", {"domain": domain})

    def ai_research_agent(self, system_prompt: str, user_prompt: str, schema: dict,
                          max_steps: int = 10, model: str = "google/gemini-2.5-flash") -> dict:
        return self.call(
            "ai_research_agent",
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "schema": schema,
                "max_steps": max_steps,
                "model": model,
            },
            timeout=300,
        )


class OpenAIClient:
    """Chat Completions mit optionalem JSON-Schema (Structured Outputs)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or CONFIG.openai_api_key
        self.base = CONFIG.openai_base_url.rstrip("/")
        self.limiter = RateLimiter(CONFIG.openai_rate_limit_per_sec)

    def complete(
        self,
        prompt: str,
        *,
        model: str | None = None,
        json_schema: dict | None = None,
        schema_name: str = "result",
        temperature: float = 0.2,
        web_search: bool = False,
    ) -> Any:
        body: dict[str, Any] = {
            "model": model or CONFIG.model_default,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        if json_schema:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "strict": True, "schema": json_schema},
            }
        if web_search:
            # Nur wirksam, wenn das gewählte Modell Websuche unterstützt.
            body["tools"] = [{"type": "web_search_preview"}]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        delay = 1.0
        for attempt in range(1, CONFIG.max_retries + 1):
            self.limiter.acquire()
            status, data = _request(f"{self.base}/chat/completions", headers=headers, body=body)
            if status == 200:
                content = data["choices"][0]["message"]["content"]
                if json_schema:
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return {}
                return content
            if status in (429, 500, 502, 503, 504) and attempt < CONFIG.max_retries:
                time.sleep(delay + random.uniform(0, 0.4))
                delay = min(delay * 2, 30.0)
                continue
            raise ApiError(f"OpenAI HTTP {status}", status, data)
        raise ApiError("OpenAI: keine Antwort")


def _bare_domain(value: str) -> str:
    """'https://www.shop.de/impressum' → 'shop.de'. Findymail erwartet eine Domain, keine URL."""
    host = re.sub(r"^https?://", "", (value or "").strip(), flags=re.IGNORECASE)
    host = host.split("/")[0].split("?")[0].split("#")[0].lower()
    return host[4:] if host.startswith("www.") else host


class FindymailClient:
    """Mailfinder per Name + Domain, entspricht der Clay-Action `findymail-find-work-email`.

    API: https://app.findymail.com/docs — 1 Finder-Credit nur, wenn eine verifizierte Adresse gefunden wird.
    """

    BASE = "https://app.findymail.com/api"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or CONFIG.findymail_api_key
        self.limiter = RateLimiter(2.0)

    def _call(self, path: str, *, method: str = "POST", body: dict | None = None) -> tuple[int, Any]:
        """Retry bei 429/5xx/Netzwerk. 404 und 422 gelten als „nichts gefunden“.

        Alles andere (401 Schlüssel falsch, 402 Guthaben leer, 423 Abo pausiert) ist ein ApiError,
        damit der Lead offen bleibt statt still als „keine E-Mail“ zu enden.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        delay = 1.0
        status, data = 0, None
        for attempt in range(1, CONFIG.max_retries + 1):
            self.limiter.acquire()
            status, data = _request(f"{self.BASE}/{path}", method=method, headers=headers, body=body)
            if status in (0, 429, 500, 502, 503, 504) and attempt < CONFIG.max_retries:
                time.sleep(delay + random.uniform(0, 0.4))
                delay = min(delay * 2, 30.0)
                continue
            if status in (200, 404, 422):
                return status, data
            break
        message = (data.get("error") or data.get("message")) if isinstance(data, dict) else None
        raise ApiError(f"Findymail HTTP {status}: {message or 'unbekannter Fehler'}", status, data)

    def find_work_email(self, full_name: str, company_domain: str) -> dict:
        """{"email": str | None, "raw": ...}; ohne Schlüssel {}."""
        if not self.api_key:
            return {}
        status, data = self._call("search/name", body={"name": full_name, "domain": _bare_domain(company_domain)})
        contact = data.get("contact") if status == 200 and isinstance(data, dict) else None
        return {"email": (contact or {}).get("email"), "raw": data}

    def credits(self) -> dict:
        """Restguthaben, z. B. {"credits": 150, "verifier_credits": 100}. Kostet nichts."""
        _, data = self._call("credits", method="GET")
        return data if isinstance(data, dict) else {}


# ---------------------------------------------------------------------------
# Nur im E-Commerce-Pfad (kein gemeinsamer Teil mit google-maps/scraper/clients.py):
# Fehler, die am Zugang liegen und nicht an der einzelnen Zeile. Jede weitere Zeile würde
# genauso scheitern – die Stufe bricht deshalb ab, ohne Fehlversuche (`attempts`) zu zählen.

_ZUGANG_HINWEIS = {
    401: "Schlüssel falsch oder abgelaufen",
    402: "Guthaben aufgebraucht",
    403: "kein Zugriff mit diesem Schlüssel bzw. Tarif",
    423: "Abo pausiert",
}
_ZUGANG_SCHLUESSEL = {"Skael": "SKAEL_API_KEY", "OpenAI": "OPENAI_API_KEY", "Findymail": "FINDYMAIL_API_KEY"}


class ZugangGesperrt(RuntimeError):
    """Ein Dienst lehnt den Zugang ab (Schlüssel, Guthaben, Abo). Bricht die laufende Stufe ab."""


def zugangsfehler(exc: BaseException) -> str | None:
    """Grund in Klartext, wenn der Fehler am Zugang liegt, sonst None."""
    if not isinstance(exc, ApiError):
        return None
    if exc.status in _ZUGANG_HINWEIS:
        return f"{_ZUGANG_HINWEIS[exc.status]} (HTTP {exc.status})"
    if exc.status == 429 and isinstance(exc.payload, dict) and isinstance(exc.payload.get("error"), dict):
        fehler = exc.payload["error"]
        if "insufficient_quota" in (fehler.get("code"), fehler.get("type")):
            return "Konto ohne Guthaben (HTTP 429, insufficient_quota)"
    return None


def pruefe_zugang(exc: BaseException, dienst: str) -> None:
    """Wirft ZugangGesperrt, wenn `exc` ein Zugangsfehler von `dienst` ist; sonst nichts."""
    grund = zugangsfehler(exc)
    if grund:
        hilfe = f"{_ZUGANG_SCHLUESSEL.get(dienst, 'Schlüssel')} in .env bzw. Konto beim Anbieter prüfen"
        if dienst == "Findymail":
            hilfe += " – oder ohne Findymail weiter: USE_FINDYMAIL=false"
        raise ZugangGesperrt(f"{dienst} lehnt den Zugang ab: {grund}. {hilfe}.") from exc
