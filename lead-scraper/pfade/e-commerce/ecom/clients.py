"""HTTP-Clients für Skael, OpenAI und Findymail — inkl. Rate-Limit und Retry.

Übernommen aus pfade/google-maps/scraper/clients.py, ergänzt um `webtraffic` und (am Dateiende)
die Erkennung von Zugangsfehlern. Änderungen am gemeinsamen Teil in beiden Dateien nachziehen.
"""
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
from typing import Any

from .config import CONFIG

log = logging.getLogger(__name__)


# ---------------------------------------------------------------- retry policy
# One rule for all clients: temporary errors are retried with exponential backoff and jitter,
# permanent ones (wrong key, no credits, bad input) fail at once.
#   status 0 = network error / timeout / connection dropped / body not JSON (see _request)
WIEDERHOLBAR = {0, 408, 425, 429, 500, 502, 503, 504}
BACKOFF_START = 2.0       # seconds before the 2nd attempt, then 4, 8, 16 … (capped)
BACKOFF_START_429 = 5.0   # rate limits need longer: 5, 10, 20, 40 s
BACKOFF_MAX = 60.0

# Skael wraps failures of its upstream services as 422 "failed" — retry those that are temporary
_VORUEBERGEHEND = re.compile(
    r"HTTP 5\d\d|\b50[234]\b|timed? ?out|timeout|temporar|unavailable|overloaded|rate.?limit|"
    r"try again|ECONNRESET|connection (reset|refused|aborted)|bad gateway", re.IGNORECASE)

# OpenAI answers an empty account with 429 — no point waiting, the stage stops (pruefe_zugang)
_KONTINGENT_LEER = ("insufficient_quota", "credit_balance_exhausted")


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


def _fehlertext(data: Any) -> str:
    """The API's own error message from a JSON body (Skael, OpenAI, Findymail shapes) or raw text."""
    if isinstance(data, dict):
        inner = data.get("data") if isinstance(data.get("data"), dict) else {}
        fehler = data.get("error")
        if isinstance(fehler, dict):
            fehler = fehler.get("message") or fehler.get("code")
        return str(inner.get("error_message") or inner.get("message") or fehler or data.get("message") or "")
    return str(data or "")


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
        try:
            raw = exc.read().decode("utf-8", errors="replace")
        except (OSError, http.client.HTTPException):
            raw = ""      # Fehlerseite abgerissen — der Status zählt trotzdem
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
    """Client für https://api.skael.de — Aufträge asynchron einreichen, Ergebnis mit begrenzter Wartezeit abholen."""

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
        headers = self._headers()
        if as_query:
            clean = {k: v for k, v in payload.items() if v is not None}
            # auch hier asynchron — sonst hält der synchrone Modus die Verbindung bis zu 1 h offen
            url = f"{url}?{urllib.parse.urlencode({**clean, 'async': '1'})}"
            body = {}
            schluessel = json.dumps([endpoint, clean], sort_keys=True, ensure_ascii=False)
        else:
            # Asynchron einreichen: Der Standardmodus hält die Verbindung bis zu 1 h offen
            # (Heartbeat), unser Zeitlimit greift dann nie und der Lauf hängt. async=true liefert
            # sofort 202 + id, das Ergebnis holt _poll mit begrenzter Wartezeit ab.
            body = {**payload, "async": True}
            schluessel = json.dumps([endpoint, payload], sort_keys=True, ensure_ascii=False)
        # Gleicher Schlüssel + gleicher Inhalt innerhalb 24 h = derselbe Auftrag, nicht erneut berechnet
        headers["Idempotency-Key"] = hashlib.sha256(schluessel.encode("utf-8")).hexdigest()[:64]

        basis_schluessel = headers["Idempotency-Key"]
        last_error: str = ""
        for attempt in range(1, CONFIG.max_retries + 1):
            self.limiter.acquire()
            status, data = _request(url, headers=headers, body=body, timeout=timeout)
            fehler_status = status
            try:
                if status == 200:
                    return self._unwrap(data)       # raises ApiError(422) for status "failed"
                if status == 202:
                    resource_id = self._resource_id(data)
                    if resource_id:
                        polled = self._poll(endpoint, resource_id)
                        if polled is not None:
                            return polled
                    last_error = "202 ohne Auftragsnummer"
                    # Skael erkennt identische Anfragen und gibt denselben Auftrag zurück —
                    # ein erneuter Versuch kostet daher nicht doppelt.
                    fehler_status = 0
                elif voruebergehend(status, data):
                    meldung = self._meldung(data)
                    last_error = "429 rate limited" if status == 429 else (
                        f"Netzwerkfehler ({meldung[:120]})" if status == 0 and meldung else
                        "Netzwerkfehler" if status == 0 else f"HTTP {status}")
                    if status == 422:
                        last_error = f"vorübergehender Fehler: {meldung}"
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
                # Auftrag fehlgeschlagen bzw. Abholen gescheitert: nur vorübergehende Ursachen wiederholen.
                # 202 = Höchstwartezeit erreicht: nicht neu einreichen, die Zeile läuft beim nächsten Lauf.
                if not voruebergehend(exc.status or 0, exc.payload, str(exc)) or exc.status == 202:
                    raise
                last_error, fehler_status = f"vorübergehender Fehler: {exc}", exc.status or 0
                if exc.status == 422:
                    # derselbe Idempotency-Key liefert 24 h lang denselben (fehlgeschlagenen) Auftrag
                    headers["Idempotency-Key"] = f"{basis_schluessel[:56]}-w{attempt}"

            if attempt < CONFIG.max_retries:
                sleep_for = wartezeit(attempt, fehler_status, data)
                log.warning("%s: %s — Versuch %s/%s, erneut in %.1f s", endpoint, last_error, attempt,
                            CONFIG.max_retries, sleep_for)
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
        frist = time.monotonic() + CONFIG.skael_max_wartezeit
        pause = 2.0
        fehlversuche = 0
        while True:
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
                log.warning("%s: Abholen von Auftrag %s fehlgeschlagen (HTTP %s) — erneut in %.1f s",
                            endpoint, resource_id, status or "Netzwerk", sleep_for)
                time.sleep(sleep_for)
                continue
            meldung = self._meldung(data)
            raise ApiError(f"Polling HTTP {status} ({zustand or 'ohne Status'})"
                           + (f": {meldung[:200]}" if meldung else ""), status, data)

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

        status, data, kontingent_leer = 0, None, False
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
            fehler = data.get("error") if isinstance(data, dict) else None
            kontingent_leer = isinstance(fehler, dict) and (
                fehler.get("code") in _KONTINGENT_LEER or fehler.get("type") in _KONTINGENT_LEER)
            if status in WIEDERHOLBAR and not kontingent_leer and attempt < CONFIG.max_retries:
                sleep_for = wartezeit(attempt, status, data)
                log.warning("OpenAI: HTTP %s — Versuch %s/%s, erneut in %.1f s", status or "Netzwerk",
                            attempt, CONFIG.max_retries, sleep_for)
                time.sleep(sleep_for)
                continue
            break
        meldung = _fehlertext(data)
        wiederholt = status in WIEDERHOLBAR and not kontingent_leer and CONFIG.max_retries > 1
        nachsatz = f" nach {CONFIG.max_retries} Versuchen" if wiederholt else ""
        raise ApiError(f"OpenAI HTTP {status}" + (f": {meldung[:200]}" if meldung else "") + nachsatz,
                       status, data)


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
        """Retry bei 408/425/429/5xx/Netzwerk. 404 und 422 gelten als „nichts gefunden“.

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
                sleep_for = wartezeit(attempt, status, data)
                log.warning("Findymail: HTTP %s — Versuch %s/%s, erneut in %.1f s", status or "Netzwerk",
                            attempt, CONFIG.max_retries, sleep_for)
                time.sleep(sleep_for)
                continue
            if status in (200, 404, 422):
                return status, data
            break
        message = _fehlertext(data)
        nachsatz = f" nach {CONFIG.max_retries} Versuchen" if status in WIEDERHOLBAR and CONFIG.max_retries > 1 else ""
        raise ApiError(f"Findymail HTTP {status}: {message or 'unbekannter Fehler'}{nachsatz}", status, data)

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
