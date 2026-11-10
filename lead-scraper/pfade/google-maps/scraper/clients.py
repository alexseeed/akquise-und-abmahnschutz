"""HTTP-Clients für Skael, OpenAI und Findymail — inkl. Rate-Limit und Retry."""
from __future__ import annotations

import hashlib
import http.client
import json
import logging
import random
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from .config import CONFIG

log = logging.getLogger(__name__)

# Kostenzähler: wird von der Kommandozeile gesetzt (db.kosten_buchen) und erhält je fertigem
# Skael-Auftrag (Endpunkt, berechnete Credits). Skael meldet die echten Kosten in `credits_cost`
# des Auftrags; ein laufender Auftrag zeigt dort nur die Vormerkung, deshalb erst bei „fertig“.
KOSTEN_ERFASSEN: Callable[[str, float], None] | None = None


def _kosten_merken(endpoint: str, data: Any) -> None:
    if KOSTEN_ERFASSEN is None or not isinstance(data, dict):
        return
    inner = data["data"] if isinstance(data.get("data"), dict) else data
    kosten = inner.get("credits_cost")
    if isinstance(kosten, (int, float)):
        try:
            KOSTEN_ERFASSEN(endpoint, float(kosten))
        except Exception as exc:  # noqa: BLE001 — der Zähler darf nie einen Lauf abbrechen
            log.debug("Kostenzähler: %s", exc)


# ---------------------------------------------------------------- retry policy
# One rule for all clients: temporary errors are retried with exponential backoff and jitter,
# permanent ones (wrong key, no credits, bad input) fail at once.
#   status 0 = network error / timeout / connection dropped (see _request)
WIEDERHOLBAR = {0, 408, 425, 429, 500, 502, 503, 504}
BACKOFF_START = 2.0       # seconds before the 2nd attempt, then 4, 8, 16 … (capped)
BACKOFF_START_429 = 5.0   # rate limits need longer: 5, 10, 20, 40 s (Skael find_domain, 15.10.2026)
BACKOFF_MAX = 60.0

# Skael wraps failures of its upstream services as 422 "failed" — retry those that are temporary
_VORUEBERGEHEND = re.compile(
    r"HTTP 5\d\d|\b50[234]\b|timed? ?out|timeout|temporar|unavailable|overloaded|rate.?limit|"
    r"try again|ECONNRESET|connection (reset|refused|aborted)|bad gateway", re.IGNORECASE)


def wartezeit(versuch: int, status: int, data: Any = None) -> float:
    """Pause before the next attempt (versuch = number of the attempt that just failed, from 1)."""
    if isinstance(data, dict) and data.get("_retry_after"):
        try:
            return min(float(data["_retry_after"]), BACKOFF_MAX) + random.uniform(0, 1.0)
        except (TypeError, ValueError):
            pass
    start = BACKOFF_START_429 if status == 429 else BACKOFF_START
    basis = min(start * 2 ** (versuch - 1), BACKOFF_MAX)
    return basis + random.uniform(0, basis * 0.25)


def voruebergehend(status: int, data: Any = None, meldung: str = "") -> bool:
    """True for errors worth retrying: network, timeouts, 429, 5xx, and Skael 'failed' with such a cause."""
    if status in WIEDERHOLBAR:
        return True
    if status == 422:
        inner = data.get("data") if isinstance(data, dict) and isinstance(data.get("data"), dict) else data
        text = meldung
        if isinstance(inner, dict):
            text += " " + str(inner.get("error_message") or inner.get("message") or "")
        return bool(_VORUEBERGEHEND.search(text))
    return False


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
        frist = timeout or CONFIG.http_timeout
        ende = time.monotonic() + frist
        with urllib.request.urlopen(req, timeout=min(frist, 60)) as resp:
            # Stückweise lesen mit fester Gesamtfrist: Skael hält Verbindungen mit Herzschlag-Bytes
            # offen (bis zu 1 h). Das Socket-Timeout greift dann nie, die Gesamtfrist schon.
            teile: list[bytes] = []
            while True:
                if time.monotonic() > ende:
                    return 0, {"message": f"Gesamtfrist {frist} s überschritten (Herzschlag-Antwort)"}
                stueck = resp.read1(65536) if hasattr(resp, "read1") else resp.read(65536)
                if not stueck:
                    break
                teile.append(stueck)
            raw = b"".join(teile).decode("utf-8", errors="replace").strip()
            try:
                return resp.status, (json.loads(raw) if raw else None)
            except json.JSONDecodeError:
                # z. B. HTML-Fehlerseite eines Proxys mit Status 200 → wie Netzwerkfehler wiederholen
                return 0, {"message": f"ungültige Antwort (kein JSON, HTTP {resp.status}): {raw[:120]}"}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = raw
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        if retry_after and str(retry_after).strip().isdigit():
            payload = payload if isinstance(payload, dict) else {"message": payload}
            payload["_retry_after"] = int(str(retry_after).strip())
        return exc.code, payload
    except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as exc:
        # Netzwerkfehler (auch abgerissene Antworten: IncompleteRead, RemoteDisconnected)
        # → Status 0, damit die Retry-Schleife greift
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

        as_query=True bildet die Clay-Spalten nach, die die Parameter als
        Query-String statt im Body übergeben (maps_search, icp_checker).
        """
        url = f"{self.base}/api/enrichments/{endpoint}"
        body: dict | None = payload
        headers = self._headers()
        if as_query:
            clean = {k: v for k, v in payload.items() if v is not None}
            # auch hier asynchron — sonst hält der synchrone Modus die Verbindung bis zu 1 h offen
            url = f"{url}?{urllib.parse.urlencode({**clean, 'async': '1'})}"
            body = {}
            schluessel = json.dumps([endpoint, clean], sort_keys=True, ensure_ascii=False)
            headers["Idempotency-Key"] = hashlib.sha256(schluessel.encode("utf-8")).hexdigest()[:64]
        else:
            # Asynchron einreichen: Der Standardmodus hält die Verbindung bis zu 1 h offen
            # (Heartbeat), unser Zeitlimit greift dann nie und der Lauf hängt. async=true liefert
            # sofort 202 + id, das Ergebnis holt _poll mit begrenzter Wartezeit ab.
            body = {**payload, "async": True}
            # Gleicher Schlüssel + gleicher Inhalt innerhalb 24 h = derselbe Auftrag, nicht erneut berechnet
            schluessel = json.dumps([endpoint, payload], sort_keys=True, ensure_ascii=False)
            headers["Idempotency-Key"] = hashlib.sha256(schluessel.encode("utf-8")).hexdigest()[:64]

        basis_schluessel = headers["Idempotency-Key"]
        last_error: str = ""
        for attempt in range(1, CONFIG.max_retries + 1):
            self.limiter.acquire()
            status, data = _request(url, headers=headers, body=body, timeout=timeout)
            fehler_status = status
            try:
                if status == 200:
                    _kosten_merken(endpoint, data)
                    return self._unwrap(data)       # raises ApiError(422) for status "failed"
                if status == 202:
                    resource_id = self._resource_id(data)
                    if resource_id:
                        polled = self._poll(endpoint, resource_id)
                        if polled is not None:
                            return polled
                    last_error = "202 timeout ohne verwertbares Ergebnis"
                    # Skael erkennt identische Anfragen und gibt denselben Auftrag zurück —
                    # ein erneuter Versuch kostet daher nicht doppelt, wartet aber weiter auf ihn.
                    fehler_status = 0
                elif voruebergehend(status, data):
                    last_error = "429 rate limited" if status == 429 else (
                        "Netzwerkfehler" if status == 0 else f"HTTP {status}")
                    if status == 422:
                        last_error = f"vorübergehender Fehler: {self._meldung(data)}"
                        # derselbe Idempotency-Key liefert 24 h lang denselben (fehlgeschlagenen) Auftrag
                        headers["Idempotency-Key"] = f"{basis_schluessel[:56]}-w{attempt}"
                elif status == 422:
                    raise ApiError(self._meldung(data) or "validation error", status, data)
                elif 400 <= status < 500:
                    meldung = self._meldung(data)                    # Schlüssel, Guthaben, Eingabe
                    raise ApiError(f"HTTP {status}" + (f": {meldung[:200]}" if meldung else ""), status, data)
                else:
                    last_error = f"HTTP {status}"
            except ApiError as exc:
                # Auftrag fehlgeschlagen bzw. Abholen gescheitert: nur vorübergehende Ursachen wiederholen
                if not voruebergehend(exc.status or 0, exc.payload, str(exc)) or exc.status == 202:
                    raise
                last_error, fehler_status = f"vorübergehender Fehler: {exc}", exc.status or 0
                if exc.status == 422:
                    # derselbe Idempotency-Key liefert 24 h lang denselben (fehlgeschlagenen) Auftrag
                    headers["Idempotency-Key"] = f"{basis_schluessel[:56]}-w{attempt}"

            if attempt < CONFIG.max_retries:
                sleep_for = wartezeit(attempt, fehler_status, data)
                log.warning("%s: %s — retry %s/%s in %.1fs", endpoint, last_error, attempt, CONFIG.max_retries, sleep_for)
                time.sleep(sleep_for)

        raise ApiError(f"{endpoint}: {last_error} nach {CONFIG.max_retries} Versuchen")

    @staticmethod
    def _meldung(data: Any) -> str:
        if not isinstance(data, dict):
            return str(data or "")
        inner = data.get("data") if isinstance(data.get("data"), dict) else data
        return str(inner.get("error_message") or inner.get("message") or data.get("message") or "")

    def _poll(self, endpoint: str, resource_id: int | str) -> dict | None:
        """Long-Polling: GET /api/enrichments/{id}?wait=true&wait_time=50.

        Achtung: Auch ein laufender Auftrag antwortet mit 200 (status processing/queued).
        Erst status=completed liefert das Ergebnis. Ein 404 hier heißt falsche URL — dann
        NICHT neu einreichen, sonst entstehen doppelte, bezahlte Aufträge.
        """
        url = f"{self.base}/api/enrichments/{resource_id}?wait=true&wait_time=50"
        beginn = time.monotonic()
        frist = beginn + CONFIG.skael_max_wartezeit
        naechste_meldung = beginn + 120
        pause = 2.0
        fehlversuche = 0
        while True:
            if time.monotonic() >= naechste_meldung:
                log.info("%s: Auftrag %s läuft bei Skael noch (%.0f s, Abbruch nach %s s)", endpoint, resource_id,
                         time.monotonic() - beginn, CONFIG.skael_max_wartezeit)
                naechste_meldung += 120
            if time.monotonic() > frist:
                # Nicht neu einreichen — die Zeile wird beim nächsten Lauf erneut versucht,
                # Skael liefert dann über Idempotency-Key/Dedupe denselben (fertigen) Auftrag.
                raise ApiError(f"{endpoint}: nach {CONFIG.skael_max_wartezeit} s noch nicht fertig "
                               f"(Auftrag {resource_id})", 202, None)
            # Abholen zählt nicht gegen die Drosselung: sonst blockieren wenige hängende Aufträge
            # (sofortige Antwort "läuft noch") mit Dauer-Nachfragen die Warteschlange aller Threads.
            gestartet = time.monotonic()
            status, data = _request(url, method="GET", headers=self._headers(), body=None)
            inner = data.get("data", data) if isinstance(data, dict) else {}
            zustand = str(inner.get("status", "")).lower() if isinstance(inner, dict) else ""
            if status == 200 and zustand in ("", "completed", "done", "succeeded"):
                _kosten_merken(endpoint, data)
                return self._unwrap(data)
            if status in (200, 202) and zustand in ("processing", "queued", "pending", "running", "waiting"):
                if time.monotonic() - gestartet < 5:   # kam sofort zurück → kurz warten statt Dauerfeuer
                    time.sleep(pause)
                    pause = min(pause * 1.5, 15.0)
                continue
            if status == 422 or zustand == "failed":
                meldung = self._meldung(data)
                raise ApiError(f"enrichment failed beim Polling: {meldung}" if meldung
                               else "enrichment failed beim Polling", 422, data)
            if status in WIEDERHOLBAR and fehlversuche < CONFIG.max_retries:
                # Netzwerk weg, 5xx, 429 beim Abholen: derselbe Auftrag läuft weiter — nur erneut abholen
                fehlversuche += 1
                sleep_for = wartezeit(fehlversuche, status, data)
                log.warning("%s: Abholen von Auftrag %s fehlgeschlagen (HTTP %s) — erneut in %.1fs",
                            endpoint, resource_id, status, sleep_for)
                time.sleep(sleep_for)
                continue
            raise ApiError(f"Polling HTTP {status} ({zustand or 'ohne Status'})", status, data)

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

    def find_cities(self, country_code: str, min_population: int, limit: int | None = None) -> dict:
        return self.call(
            "find_cities",
            {
                "country_code": country_code,
                "limit": limit if limit is not None else CONFIG.cities_limit,
                "min_population": min_population,
            },
        )

    def maps_search(self, query: str, zoom: int | None = None, limit: int | None = None) -> dict:
        return self.call(
            "maps_search",
            {
                "query": query,
                "zoom": zoom if zoom is not None else CONFIG.maps_zoom,
                "limit": limit if limit is not None else CONFIG.maps_limit,
            },
            as_query=True,
            timeout=240,
        )

    def icp_checker(self, url: str, prompt: str) -> dict:
        return self.call("icp_checker", {"url": url, "prompt": prompt}, as_query=True)

    def imprint_extractor(self, domain: str) -> dict:
        return self.call("imprint_extractor", {"domain": domain})

    def find_email_person(self, domain: str, full_name: str) -> dict:
        return self.call("find_email_person", {"domain": domain, "full_name": full_name})

    def verify_email(self, email: str) -> dict:
        return self.call("verify_email", {"email": email})

    def web_scraper(self, url: str) -> dict:
        return self.call("web_scraper", {"url": url})

    def find_domain(self, company_name: str, city: str = "", country: str = "", context: str = "",
                    max_pages: int = 3, postcode: str = "", website: str = "") -> dict:
        """Eigene Website einer Firma, über das Impressum bestätigt (asynchron, typisch 60 s).

        Kostet 5 Credits Basis + 10–15 je geprüfter Seite. `domain` ist nur bei status=verified gesetzt.
        `website` ist ein Hinweis (z. B. Bewerbungslink auf eigener Domain): wird zuerst geprüft,
        zählt aber nur mit Impressum-Beleg.
        """
        eingabe: dict[str, Any] = {"company_name": company_name, "max_pages": max_pages}
        if city:
            eingabe["city"] = city
        if postcode:
            eingabe["postcode"] = postcode
        if country:
            eingabe["country"] = country.upper()
        if context:
            eingabe["context"] = context
        if website:
            eingabe["website"] = website
        return self.call("find_domain", eingabe, timeout=300)

    def stellen_suche(self, endpoint: str, payload: dict) -> dict:
        """Jobportal-Suche (indeed_jobs, stepstone_jobs, arbeitsagentur_jobs, kununu_jobs).

        1 Credit je Aufruf, unabhängig von der Trefferzahl (bis 100 je Seite).
        """
        return self.call(endpoint, {k: v for k, v in payload.items() if v not in (None, "")}, timeout=240)

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
    """Chat Completions mit optionalem JSON-Schema (Structured Outputs).

    Zwei Anbieter mit derselben Schnittstelle:
      * skael (Standard): {SKAEL_BASE_URL}/api/v1/chat/completions mit SKAEL_API_KEY
      * openai: OPENAI_BASE_URL mit OPENAI_API_KEY (+ OPENAI_API_KEY_FALLBACK)
    Websuche (`web_search=True`) gibt es nur bei OpenAI und erzwingt diesen Anbieter.
    """

    # Gemeinsam für alle Instanzen: ist der Hauptschlüssel erschöpft, nutzen alle Threads den Ersatz.
    _ersatz_aktiv = False
    _ersatz_lock = threading.Lock()

    def __init__(self, api_key: str | None = None, provider: str | None = None):
        self._eigener_key = api_key
        self.provider = (provider or CONFIG.llm_provider or "skael").lower()
        if self.provider == "skael":
            self.base = CONFIG.skael_base_url.rstrip("/") + "/api/v1"
            self.limiter = RateLimiter(CONFIG.skael_rate_limit_per_sec)
        else:
            self.base = CONFIG.openai_base_url.rstrip("/")
            self.limiter = RateLimiter(CONFIG.openai_rate_limit_per_sec)

    @property
    def api_key(self) -> str:
        if self._eigener_key:
            return self._eigener_key
        if self.provider == "skael":
            return CONFIG.skael_llm_api_key or CONFIG.skael_api_key
        if OpenAIClient._ersatz_aktiv and CONFIG.openai_api_key_fallback:
            return CONFIG.openai_api_key_fallback
        return CONFIG.openai_api_key

    def _auf_ersatz_wechseln(self, status: int, data: Any, letzter_versuch: bool,
                             benutzter_key: str = "") -> bool:
        """Wechselt auf OPENAI_API_KEY_FALLBACK, wenn der Hauptschlüssel sein Limit erreicht hat.

        Auslöser: Guthaben/Kontingent erschöpft (insufficient_quota, credit_balance_exhausted) sofort,
        ein Rate-Limit (429) erst, wenn es auch nach allen Wiederholungen bestehen bleibt.
        Hat ein anderer Thread schon gewechselt, wird eine noch mit dem Hauptschlüssel gesendete
        Anfrage ebenfalls mit dem Ersatz wiederholt, statt zu scheitern.
        """
        if self.provider != "openai" or self._eigener_key or not CONFIG.openai_api_key_fallback:
            return False
        if OpenAIClient._ersatz_aktiv:
            return benutzter_key == CONFIG.openai_api_key
        code = ((data or {}).get("error") or {}).get("code") if isinstance(data, dict) else None
        erschoepft = code in ("insufficient_quota", "credit_balance_exhausted")
        if not (erschoepft or (status == 429 and letzter_versuch)):
            return False
        with OpenAIClient._ersatz_lock:
            if not OpenAIClient._ersatz_aktiv:
                OpenAIClient._ersatz_aktiv = True
                log.warning("OpenAI-Hauptschlüssel am Limit (HTTP %s, %s) — wechsle auf Ersatzschlüssel",
                            status, code or "rate limit")
        return True

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
        if web_search and self.provider != "openai":
            return OpenAIClient(provider="openai").complete(
                prompt, model=model, json_schema=json_schema, schema_name=schema_name,
                temperature=temperature, web_search=True)
        if web_search:
            # Websuche gibt es nur über die Responses-API — Chat Completions lehnt
            # das web_search-Tool mit HTTP 400 ab.
            url = f"{self.base}/responses"
            body: dict[str, Any] = {
                "model": model or CONFIG.model_default,
                "input": prompt,
                "temperature": temperature,
                "tools": [{"type": "web_search"}],
            }
            if json_schema:
                body["text"] = {"format": {"type": "json_schema", "name": schema_name,
                                           "strict": True, "schema": json_schema}}
        else:
            url = f"{self.base}/chat/completions"
            body = {
                "model": model or CONFIG.model_default,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }
            if json_schema:
                body["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {"name": schema_name, "strict": True, "schema": json_schema},
                }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        for attempt in range(1, CONFIG.max_retries + 1):
            self.limiter.acquire()
            status, data = _request(url, headers=headers, body=body)
            if status == 200:
                if web_search:
                    content = "".join(c.get("text", "") for o in data.get("output", [])
                                      if o.get("type") == "message" for c in o.get("content", []))
                else:
                    content = data["choices"][0]["message"]["content"]
                if json_schema:
                    return _json_aus_text(content)
                return content
            if status == 403 and self.provider == "skael":
                raise ApiError("Skael-KI: Schlüssel ohne Fähigkeit llm:invoke — bei Skael freischalten lassen "
                               "(SKAEL_LLM_API_KEY) oder LLM_PROVIDER=openai setzen", status, data)
            if status == 429 and self._auf_ersatz_wechseln(status, data, attempt >= CONFIG.max_retries,
                                                           headers["Authorization"][7:]):
                return self.complete(prompt, model=model, json_schema=json_schema, schema_name=schema_name,
                                     temperature=temperature, web_search=web_search)
            if status in WIEDERHOLBAR and attempt < CONFIG.max_retries:
                sleep_for = wartezeit(attempt, status, data)
                log.warning("KI (%s): HTTP %s — retry %s/%s in %.1fs", self.provider, status or "Netzwerk",
                            attempt, CONFIG.max_retries, sleep_for)
                time.sleep(sleep_for)
                continue
            raise ApiError(f"{self.provider} HTTP {status}", status, data)
        raise ApiError(f"{self.provider}: keine Antwort")


def _json_aus_text(content: Any) -> dict:
    """JSON aus der Modellantwort, auch wenn ein Modell es in Text oder ```json einbettet."""
    if isinstance(content, dict):
        return content
    text = str(content or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, ende = text.find("{"), text.rfind("}")
    if start != -1 and ende > start:
        try:
            return json.loads(text[start:ende + 1])
        except json.JSONDecodeError:
            pass
    return {}


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
        status, data = 0, None
        for attempt in range(1, CONFIG.max_retries + 1):
            self.limiter.acquire()
            status, data = _request(f"{self.BASE}/{path}", method=method, headers=headers, body=body)
            if status in WIEDERHOLBAR and attempt < CONFIG.max_retries:
                time.sleep(wartezeit(attempt, status, data))
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


