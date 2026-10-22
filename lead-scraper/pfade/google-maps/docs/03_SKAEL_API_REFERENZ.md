# Skael API — Referenz der genutzten Endpunkte

Base URL `https://api.skael.de` · Auth `Authorization: Bearer eak_…` · alle Endpunkte `POST`, `Content-Type: application/json`.
Antwort-Umschlag und Fehlerformat: siehe `docs/02_ZUGAENGE_UND_TOKENS.md` §4.

---

## `POST /api/enrichments/find_cities`

Alle Städte eines Landes (~142.000 weltweit, Bevölkerung > 1.000, Quelle GeoNames).

**Input**

| Feld | Typ | Pflicht | Constraints |
|---|---|---|---|
| `country_code` | string | ✅ | genau 2 Zeichen (ISO 3166-1 alpha-2) |
| `min_population` | integer | – | ≥ 0 |
| `region` | string | – | max 255; englischer oder nativer Regionsname (`Bavaria`, `Bayern`, `Bavière`) |
| `fields` | string | – | kommagetrennt, Default `name,population` |
| `limit` | integer | – | ≥ 1 |
| `sort` | string | – | Feldname, `-` für absteigend |
| `page` | integer | – | ≥ 1 |

**Verfügbare Felder:** `name`, `ascii_name`, `region`, `population`, `latitude`, `longitude`, `feature_code`, `timezone`

`feature_code`: `PPLC` Hauptstadt · `PPLA` Regionshauptstadt · `PPLA2`/`PPLA3` untergeordnet · `PPL` Ort · `PPLX` Ortsteil

**Output**

```json
{ "total": 7571, "cities": [ { "name": "Berlin", "population": 3426354 } ], "country_code": "DE" }
```

Antwortzeit < 1 s (lokale DB). Städtezahlen: US ~17.000 · FR ~9.000 · MX ~8.700 · **DE ~7.600** · IN ~6.900 · IT ~6.700 · BR ~5.700.

Regionsnamen nachschlagen: `GET https://api.skael.de/docs/data/regions/DE` (frei, 30 req/min/IP, nur für Tooling).

**Im Workbook verwendet:** `country_code`, `limit: 5000`, `min_population`.

---

## `POST /api/enrichments/maps_search`

Google-Maps-Firmensuche.

**Input**

| Feld | Typ | Pflicht | Constraints |
|---|---|---|---|
| `query` | string | ✅ | max 500 |
| `zoom` | integer | – | 3–21 |
| `limit` | integer | – | 1–2000 |
| `lat` / `lon` | numeric | – | −90…90 / −180…180 |
| `gl` | string | – | 2-stelliges Länderkürzel |
| `hl` | string | – | Sprachcode, max 5 |
| `fields` | string | – | kommagetrennt, max 500 |

**Zoom-Empfehlung:** 3–5 Land · 6–8 Bundesland · **9–11 Stadt (empfohlen)** · 12–14 Stadtteil · 15–17 Straße · 18–21 Gebäude

**Default-Felder**

```
name,website,phone_numbers,type,rating,review_count,full_address,business_id,place_id,zip_code
```

`business_id` ist immer enthalten (Dedupe).

**Weitere Felder:** `domain`, `price_level`, `price_level_text`, `street_address_full`, `city`, `state`, `country_code`, `district`, `latitude`, `longitude`, `subtypes`, `short_description`, `full_description`, `timezone`, `owner_id`, `owner_name`, `owner_link`, `order_link`, `google_mid`, `photos_sample`, `attributes`

**Output**

```json
{ "items": [ { "name": "…", "website": "…", "phone_numbers": ["…"], "type": "…",
               "rating": 4.9, "review_count": 92, "full_address": "…",
               "business_id": "0x…", "place_id": "ChIJ…", "zip_code": "12345" } ],
  "total": 10 }
```

**Antwortzeiten:** 1–200 Treffer 5–15 s · 201–1.000 15–45 s · 1.001–2.000 45–90 s.
Für große Läufe Async + Webhook empfohlen.

**Preis (Stand 2026-10-08, laut Skael-Preisliste):** bis 20 Credits reserviert, abgerechnet 2 Credits je gelieferte Seite (bis 200 Treffer je Seite); ohne Treffer kostenlos. 1.000 Credits = 1 €. Aktuelle Preise: Skael-Werkzeug `get_pricing`.

**Im Workbook verwendet:** `query`, `zoom: 11`, `limit: 2000` — als **Query-String**, Rate-Limit 5/s.

---

## `POST /api/enrichments/icp_checker`

Klassifiziert eine Website gegen ein Ideal Customer Profile. Das LLM erhält **nur den Bodytext
der einen angegebenen URL** — kein HTML, keine Bilder, keine Unterseiten.

**Input**

| Feld | Typ | Pflicht | Constraints |
|---|---|---|---|
| `url` | string | ✅ | max 2048 |
| `prompt` | string | ✅ | max 10000 |

**Output**

```json
{ "icp": true, "confidence": 0.87, "reason": "Site describes a B2B SaaS product targeting marketing teams." }
```

> ⚠️ Das Feld heißt **`icp`**, nicht `is_icp` — auch wenn der Prompt `is_icp` vorschreibt.

**Tipps aus der Doku:** detaillierte Kriterien schreiben · Prompt in der erwarteten
Sprache der Website · für Massenläufe Async mit `callback_url`.

**Im Workbook verwendet:** `url` und `prompt` als **Query-String**.

---

## `POST /api/enrichments/imprint_extractor`

Liest das Impressum einer deutschsprachigen Website aus.

**Input**

| Feld | Typ | Pflicht | Constraints |
|---|---|---|---|
| `domain` | string | ✅ | max 255, Root-Domain ohne Protokoll |

**Output**

| Feld | Beschreibung |
|---|---|
| `firmenname` | Firmenname inkl. Rechtsform; leer wenn nicht gefunden |
| `adresse` | Straße, PLZ, Ort als ein String |
| `land` | ISO-3166-1 alpha-2, **nur wenn die Seite es belegt** (Ländername, USt-Präfix DE/ATU/CHE, Registerbezeichnung). Wird nie aus Sprache, TLD, Vorwahl oder PLZ geraten. |
| `telefon` | bereinigte Telefonnummer |
| `email` | im Impressum genannte Adresse |
| `rechtlicher_verantwortlicher` | V.i.S.d.P. |
| `geschaeftsfuehrer` | Array von Namen |
| `ust_id`, `steuernummer` | Steuerkennzeichen |
| `handelsregister_number`, `handelsregister_court` | Registerdaten |
| `website` | erkannte Website |

---

## `POST /api/enrichments/find_email_person`

Findet die Geschäfts-E-Mail einer Person.

**Input** — entweder `domain` **oder** `company_name`, und entweder `full_name` **oder** `first_name` + `last_name`.

| Feld | Typ | Constraints |
|---|---|---|
| `domain` | string | max 255, ohne Protokoll; Pflicht wenn `company_name` fehlt |
| `company_name` | string | max 255; Pflicht wenn `domain` fehlt |
| `full_name` | string | max 255; Pflicht wenn `first_name`+`last_name` fehlen |
| `first_name` / `last_name` | string | max 255; nur gemeinsam gültig |

**Output**

| Feld | Beschreibung |
|---|---|
| `email` | gefundene Adresse, `null` wenn keine |
| `email_status` | `valid` · `risky` · `not_found` · `blacklisted` |
| `valid_email` | gesetzt wenn `email_status = valid`, sonst `null` |

**Im Workbook verwendet:** `domain` + `full_name`, Rate-Limit 5/s.

---

## `POST /api/enrichments/verify_email`

Prüft Zustellbarkeit (Debounce-basiert).

**Input**

| Feld | Typ | Pflicht | Constraints |
|---|---|---|---|
| `email` | email | ✅ | max 255, syntaktisch gültig |

**Output**

```json
{ "email": "jane.doe@example.com", "code": 5, "status": "deliverable",
  "is_deliverable": true, "is_disposable": false, "is_role": false,
  "is_catch_all": false, "is_free_provider": false, "reason": "Accepted email" }
```

**Codes**

| Code | Status | Bedeutung | Empfehlung |
|---|---|---|---|
| 5 | Valid | zustellbar | ✅ senden |
| 4 | Risky | Catch-all-/Accept-all-Domain | ⚠️ mit Vorsicht |
| 7 | Risky | nicht verifizierbar | ⚠️ mit Vorsicht |
| 1 | Invalid | ungültige Syntax | ❌ |
| 2 | Invalid | bekannte Spam-Trap | ❌ |
| 3 | Invalid | Wegwerf-Adresse | ❌ |
| 6 | Invalid | wird bouncen | ❌ |

**Im Workbook verwendet:** GF-Mail und Info@-Mail, Rate-Limit 5/s, akzeptiert werden Codes 4, 5, 7.

---

## `POST /api/enrichments/web_scraper`

Rendert eine Seite und liefert strukturierte Daten inkl. Bodytext.

**Input**

| Feld | Typ | Pflicht | Constraints |
|---|---|---|---|
| `url` | string | ✅ | max 2048, mit Protokoll und Pfad möglich |

**Output**

| Feld | Beschreibung |
|---|---|
| `site_status_code` | HTTP-Status, `0` wenn nicht erreichbar |
| `final_url` | URL nach Redirects |
| `title`, `description`, `keywords`, `favicon` | Meta-Daten |
| `social_links` | LinkedIn, X, Facebook … |
| `links` | alle absoluten Links |
| `emails` | gefundene Adressen |
| `body_text` | Fließtext der Seite |

**Im Workbook verwendet:** `url` = `website [Final]`; `body_text` wird auf **8.192 Zeichen** gekürzt.

---

## `POST /api/enrichments/ai_research_agent` *(im Workbook deaktiviert)*

Agentischer Rechercheagent mit Websuche.

**Im Workbook konfiguriert:**

```json
{
  "system_prompt": "You are an expert researcher trained on finding the right LinkedIn Profile URLs …",
  "user_prompt":   "<siehe prompts/linkedin_research_body.json.tpl>",
  "schema": {
    "type": "object",
    "properties": {
      "linkedin_url": { "type": "string" },
      "confidence":   { "type": "number" },
      "found":        { "type": "boolean" }
    },
    "required": ["linkedin_url", "confidence", "found"],
    "additionalProperties": false
  },
  "max_steps": 10,
  "model": "google/gemini-2.5-flash"
}
```

Rückgabe bei Misserfolg: `linkedin_url = "No LinkedIn profile found"`.

---

## Rate-Limits & Verhalten

* **Global:** 10.000 Requests/Minute pro Organisation · Auth-Endpunkte 3–5/min
* **429:** `{"message": "Too many requests. Please slow down."}` → exponentielles Backoff
* **Polling:** pro Ressource nur ein aktiver Poll gleichzeitig
* **Dedupe:** identische Requests innerhalb 20 Minuten liefern die alte Ressource (auch Fehlschläge).
  Um einen frischen Lauf zu erzwingen: ein validierungsrelevantes Input-Feld ändern oder warten.
* **Status-Werte:** `queued` → `processing` → (`waiting`) → `completed` / `failed` / `timeout`
