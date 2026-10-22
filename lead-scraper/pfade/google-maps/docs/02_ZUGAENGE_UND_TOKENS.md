# Zugänge, API-Keys und Kosten

Alles, was nötig ist, um den Prozess auszuführen — einmal für Clay, einmal für den lokalen Nachbau.

> **Alle Zugangsdaten müssen selbst beschafft werden.** Im Paket sind keine enthalten.

---

## 1. Pflicht-Zugänge

### 1.1 Skael API

| | |
|---|---|
| **Base URL** | `https://api.skael.de` |
| **Auth** | `Authorization: Bearer eak_…` |
| **Doku** | https://api.skael.de/docs/api-guide |
| **Lokal** | `.env` → `SKAEL_API_KEY=` (eigener Key erforderlich) |
| **Rate-Limit (global)** | 10.000 Requests/Minute pro Organisation |
| **Rate-Limit (in Clay gesetzt)** | `maps_search` 5/s · `find_email_person` 5/s · `verify_email` 5/s |

Genutzte Endpunkte:

| Endpunkt | Stufe | Zweck |
|---|---|---|
| `POST /api/enrichments/find_cities` | 1 | Städte je Land |
| `POST /api/enrichments/maps_search` | 2 | Google-Maps-Firmensuche |
| `POST /api/enrichments/icp_checker` | 3 | ICP-Bewertung der Website |
| `POST /api/enrichments/imprint_extractor` | 4 | Impressum auslesen |
| `POST /api/enrichments/find_email_person` | 4 | E-Mail zu Person + Domain |
| `POST /api/enrichments/verify_email` | 4 | Zustellbarkeit prüfen |
| `POST /api/enrichments/web_scraper` | 4 | Bodytext für Personalisierung |
| `POST /api/enrichments/ai_research_agent` | 4 | LinkedIn-Suche *(im Workbook deaktiviert)* |

### 1.2 OpenAI

| | |
|---|---|
| **Nutzung in Clay** | ein im Workbook hinterlegtes OpenAI-Konto |
| **Modelle** | `gpt-4o-mini` (Domain-Suche Stufe 3, Anrede, Personalisierung, Videotitel), `gpt-4.1-mini` (Domain-Suche Stufe 4) |
| **Lokal** | `.env` → `OPENAI_API_KEY=` |

Vier KI-Schritte:

| Schritt | Modell | Prompt | Output-Schema |
|---|---|---|---|
| Domain-Suche Stufe 3 (`Domain URL`) | gpt-4o-mini | `prompts/company_domain.txt` | `{ response: string }` |
| Domain-Suche Stufe 4 (`Company Domain`) | gpt-4.1-mini | `prompts/company_domain.txt` | `{ response: string }` |
| Anrede (`Anrede [Prompt] (2)`) | gpt-4o-mini | `prompts/anrede.txt` | `prompts/anrede.schema.json` |
| Personalisierung (`Personalisierung AI`) | gpt-4o-mini | `prompts/personalisierung.txt` | `prompts/personalisierung.schema.json` |
| Videotitel (`Cleaned Video Title`) | gpt-4o-mini | `prompts/video_title_cleanup.txt` | `prompts/video_title_cleanup.schema.json` |

> Die Domain-Suche läuft in Clay als **Claygent** (Web-Research-Agent mit Browsing).
> Ein reines OpenAI-Chat-Modell kann nicht browsen — lokal ist dafür eine Websuche
> nötig (siehe `docs/05_ABWEICHUNGEN.md`).

---

## 2. Optionale Zugänge

| Anbieter | Wofür | In Clay aktiv? | Lokal nötig? |
|---|---|---|---|
| **Findymail** | Fallback-Mailfinder (`Find Work Email`) | ✅ aktiv | nur wenn Fallback gewünscht → `FINDYMAIL_API_KEY` |
| **Clay** | Plattform selbst (Growth-Plan für HTTP-API-Spalten) | ✅ | ❌ entfällt beim lokalen Nachbau |
| LeadMagic | Handynummern | ❌ (`&& false`) | optional |
| Wiza | Telefonnummern | ❌ | optional |
| Upcell | Handynummern | ❌ | optional |
| Forager | Telefonnummern | ❌ | optional |
| Prospeo | Handynummern | ❌ | optional |
| ContactOut | Telefonnummern | ❌ | optional |
| Datagma | Handynummern | ❌ | optional |
| Clearout | Nummern-Validierung | ❌ | optional |
| People Data Labs / MixRank | Personen-Anreicherung | ❌ | optional |

---

## 3. Kosten (Skael-Credits)

| Endpunkt | Tarif |
|---|---|
| `find_cities` | lokale DB-Abfrage, sehr günstig |
| `maps_search` | bis 10 Credits reserviert, abgerechnet **1 Credit je gelieferte Seite**; ohne Treffer kostenlos |
| `icp_checker` | pro Prüfung |
| `imprint_extractor` | pro Domain |
| `find_email_person` | pro Suche |
| `verify_email` | pro Adresse |
| `web_scraper` | pro URL |

Größenordnung im Beispiellauf:

| Stufe | Calls |
|---|---|
| `find_cities` | 9 |
| `maps_search` | ~22.000 |
| `icp_checker` | ≈ ~26.500 (minus Zeilen ohne Website) |
| `imprint_extractor` | ≈ ~6.400 |
| `find_email_person` | ≈ ~6.400 (nur mit gefundenem GF) |
| `verify_email` | ≈ ~6.400 (GF) + Info@-Fallback |
| `web_scraper` | ≈ 4.000 (nur mit `Email [Final]`) |

> **Vor jedem Vollstart einen Dry-Run mit 2–3 Städten fahren.** Der teuerste Posten ist
> `maps_search` × Anzahl Städte × Anzahl Keywords.

---

## 4. Antwort-Struktur der Skael-API

Alle Endpunkte liefern denselben Umschlag:

```json
{
  "data": {
    "id": 123,
    "type": "maps_search",
    "status": "completed",
    "input":  { "…": "…" },
    "output": { "…": "…" },
    "custom_vars": {},
    "error_message": null,
    "started_at":  "2026-01-15T10:30:00.000000Z",
    "completed_at":"2026-01-15T10:30:05.000000Z"
  }
}
```

* **Synchron (Default):** Timeout 3.600 s; bei Überschreitung `202` mit `status: "timeout"`.
* **Async-Polling:** `async=true` → `202` mit `id`, dann
  `GET /api/<resource>/{id}?wait=true&wait_time=50`.
* **Async-Webhook:** `async=true` + `callback_url` (öffentliche IP, Timeout 10 s).
* **Dedupe:** identische Requests innerhalb von **20 Minuten** liefern die alte Ressource zurück
  — auch fehlgeschlagene. `custom_vars` zählen dabei nicht mit.
* **Fehler:** `422` mit `errors`-Objekt = Validierungsfehler;
  `422` mit `data.status = "failed"` + `error_message` = fehlgeschlagener Lauf.
* **429:** `Too many requests` → exponentielles Backoff.

---

## 5. `.env`-Vorlage

```dotenv
# Pflicht — eigene Keys, nicht die aus dem Clay-Workbook
SKAEL_API_KEY=eak_...
OPENAI_API_KEY=sk-...

# Optional
FINDYMAIL_API_KEY=

# Modelle (Clay-Defaults)
OPENAI_MODEL_DOMAIN=gpt-4.1-mini
OPENAI_MODEL_DEFAULT=gpt-4o-mini

# Durchsatz
SKAEL_RATE_LIMIT_PER_SEC=5
MAX_CONCURRENCY=5
```

Die `.env` liegt in `.gitignore` und wird nie eingecheckt.
