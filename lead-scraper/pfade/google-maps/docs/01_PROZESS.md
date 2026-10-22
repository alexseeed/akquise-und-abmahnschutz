# Scraping- & Anreicherungs-Prozess — vollständige Dokumentation

Rekonstruiert 1:1 aus dem Clay-Workbook **„Beispiel-Workbook"**
(Workspace `WORKSPACE_ID`, Workbook `WORKBOOK_ID`), Stand der Analyse: 10.08.2026.
Am Workbook wurde **nichts verändert**.

Beispiel-Zielgruppe: Metallbaubetriebe DACH. Die Zielgruppe ist austauschbar — der Prozess
funktioniert für jede Zielgruppe, die über Google Maps auffindbar ist.

---

## 0. Überblick — die 4 Stufen

```
┌──────────────┐   find_cities    ┌──────────────┐   maps_search   ┌──────────────┐   imprint/mail/AI   ┌──────────────┐
│  EINGABE     │ ───────────────► │ VERARBEITUNG │ ──────────────► │ DATENSÄTZE   │ ──────────────────► │ ANREICHERUNG │
│  9 Zeilen    │  1 Zeile je      │ ~22.000 Zeilen│  1 Zeile je     │ ~26.500 Zeilen│  1 Zeile je         │ ~6.400 Zeilen │
│ Keyword×Land │  Stadt           │ Stadt+Keyword│  Google-Maps-   │ Firma (dedup)│  ICP-Treffer        │ versandfertig│
└──────────────┘                  └──────────────┘  Treffer        └──────────────┘                     └──────────────┘
```

| Stufe | Clay-Tabelle | Fan-out | Was passiert |
|---|---|---|---|
| 1 | **EINGABE** | 1 → n Städte | Keyword + Land + Mindest-Einwohnerzahl → Städteliste über `find_cities` |
| 2 | **VERARBEITUNG** | 1 → n Firmen | Query `"<Keyword> in <Stadt>"` → Google-Maps-Scrape über `maps_search` |
| 3 | **DATENSÄTZE** | Filter | Dedupe über Domain, Website-Fallback per KI, ICP-Prüfung über `icp_checker` |
| 4 | **ANREICHERUNG** | Anreicherung | Impressum, Geschäftsführer, E-Mail-Finder + Validierung, Anrede, Personalisierung, Videotitel |

`DATENSÄTZE 2` ist **kein eigener Schritt**, sondern nur ein Überlauf-Ziel für Stufe 2,
falls DATENSÄTZE das Clay-Limit von 50.000 Zeilen reißt (siehe §2.6). Für den lokalen
Nachbau irrelevant.

---

## 1. Stufe 1 — EINGABE (Städte auflösen)

Tabelle `TABELLE_EINGABE`, 9 Zeilen, 8 Spalten.
Eine Zeile = **eine Kombination aus Keyword × Land**.

### 1.1 Manuelle Eingabefelder

| Spalte | Typ | Beispielwerte | Bedeutung |
|---|---|---|---|
| `Keyword` | Text | `Metallbau`, `Schlosserei`, `Metallbauer` | Google-Maps-Suchbegriff |
| `Country Code` | Text | `DE`, `AT`, `CH` | ISO-3166-1 alpha-2 |
| `Min Population` | Zahl | `1` | Mindest-Einwohnerzahl je Stadt |
| `Skael API Key` | Formel (statisch) | `"eak_…"` | Der API-Key als Konstante in jeder Zeile |

Im Beispiel: 3 Keywords × 3 Länder = 9 Zeilen.

### 1.2 Spalte `SKAEL CITIES` — HTTP API

```
POST https://api.skael.de/api/enrichments/find_cities
Content-Type: application/json
Authorization: Bearer {{Skael API Key}}

{
  "country_code": "{{Country Code}}",
  "limit": 5000,
  "min_population": {{Min Population}}
}
```

* **Run-Bedingung:** `{{Min Population}} && {{Country Code}}`
* **Antwort:** `{ "total": 7571, "cities": [ { "name": "Berlin", "population": 3426354 }, … ], "country_code": "DE" }`
* In Clay liegt die Antwort unter `output`, also `{{SKAEL CITIES}}.output.cities`.
* Reale Ergebnisse: DE 5.000 (von ~7.600, durch `limit` gekappt), AT 1.310, CH 1.334.

> ⚠️ **`limit: 5000` kappt Deutschland.** DE hat ~7.600 Städte ≥1.000 Einwohner.
> Wer vollständig scrapen will, muss `limit` erhöhen oder über `page` paginieren.

### 1.3 Spalte `Send table data` — Fan-out nach VERARBEITUNG

* Ziel: Tabelle `VERARBEITUNG`
* Methode: **„Send row for each item in a list"**, Liste = `cities`
* Mitgegebene Felder: `Keyword`, `Country Code`, `Min Population`, `Created At`
  (der Skael API Key wird **nicht** mitgeschickt)
* **Run-Bedingung:** `{{Keyword}} && {{SKAEL CITIES}}?.output?.cities?.[0]`
* Ergebnis: 5.000 + 1.310 + 1.334 = ~7.600 Zeilen je Keyword → ~23.000 gesendet,
  ~22.000 tatsächlich in VERARBEITUNG (Differenz durch Zeilenlimits/Fehlläufe).

---

## 2. Stufe 2 — VERARBEITUNG (Google Maps scrapen)

Tabelle `TABELLE_VERARBEITUNG`, ~22.000 Zeilen, 16 Spalten.
Eine Zeile = **eine Stadt × ein Keyword**.

### 2.1 Eingehende Felder

`input_keyword`, `input_city` (= `name` aus dem City-Objekt), `input_country`, `Created At`
sowie die durchgereichten `Keyword`, `Country Code`, `Min Population` (ausgeblendet).

Die durchgereichten Felder sind Formeln auf den Parent-Datensatz:

```js
Country Code   = {{Rows from: EINGABE}}?.parent?.["Country Code"]
Min Population = {{Rows from: EINGABE}}?.parent?.["Min Population"]
Keyword        = {{Rows from: EINGABE}}?.parent?.["Keyword"]
Skael API Key  = "eak_…"          // erneut als Konstante
```

### 2.2 Spalte `query` — die Suchanfrage

```js
{{input_keyword}} + " in " + ({{input_city}} || {{input_country}})
```

→ z. B. `Metallbau in Tholey`. Fällt die Stadt weg, wird auf das Land zurückgefallen.

### 2.3 Spalte `RUN` — manueller Hauptschalter

Checkbox mit statischer Formel `true`. Dient als Not-Aus für die gesamte Maps-Stufe.

### 2.4 Spalte `SKAEL MAPS` — HTTP API

```
POST https://api.skael.de/api/enrichments/maps_search?zoom=11&limit=2000&query={{query}}
Content-Type: application/json
Authorization: Bearer {{Skael API Key}}
```

* Die Parameter liegen als **Query-String**, nicht im Body.
* **Run-Bedingung:** `{{RUN}} === true && {{query}}`
* **Rate-Limit (in Clay gesetzt):** 5 Requests / 1.000 ms
* Retry on failure: an. Follow redirects: an.
* **Antwort:** `{ "items": [ … ], "total": 10 }`

Ein `items`-Objekt (Skael-Default-Felder):

| Feld | Beispiel |
|---|---|
| `name` | `Muster Metallbau GmbH` |
| `type` | `Metallbaubetrieb` |
| `rating` | `4.9` |
| `review_count` | `92` |
| `website` | `https://www.muster-metallbau.de/standorte/musterstadt` |
| `place_id` | `ChIJ…` |
| `business_id` | `0x…:0x…` |
| `zip_code` | `12345` |
| `full_address` | `Musterstr. 1, 12345 Musterstadt` |
| `phone_numbers` | `["+49 30 …"]` |

`zoom=11` ist laut Skael-Doku der empfohlene Stadt-Radius.

### 2.5 Spalte `Contains Error` — Fehlererkennung

```js
{{SKAEL MAPS}}?.[0]
  ? (JSON.stringify({{SKAEL MAPS}}?.[0])?.toLowerCase()?.includes("error"))
  : false
```

### 2.6 Spalten `Send table data` / `Send table data (2)` — Fan-out

**Primär → DATENSÄTZE** (`TABELLE_DATENSAETZE`)

* Methode: „Send row for each item in a list", Liste = `items`
* Feld-Mapping: `input_keyword → query_keyword`, `input_city → query_city`,
  `input_country → query_country`, dazu `query` und `Created At`
* **Run-Bedingung:** `{{SKAEL MAPS}} && !{{Contains Error}} && !!{{SKAEL MAPS}}?.output?.items?.[0]`

**Fallback → DATENSÄTZE 2** (`TABELLE_DATENSAETZE_2`)

* identisch, plus `&& !{{Send table data}}`
* Greift nur, wenn der erste Send fehlschlug (Clay-Limit 50.000 Zeilen/Tabelle).
* Status im Workbook: nie ausgelöst („Run condition not met" in allen Zeilen).

---

## 3. Stufe 3 — DATENSÄTZE (Dedupe + ICP-Qualifizierung)

Tabelle `TABELLE_DATENSAETZE`, ~26.500 Zeilen, 30 Spalten.
Eine Zeile = **ein Google-Maps-Treffer**, nach Dedupe: **eine Firma**.

### 3.1 Aus Maps übernommene Felder

`business_id`, `place_id`, `Firmenname` (← `name`), `website`, `address` (← `full_address`),
`zip` (← `zip_code`), `category` (← `type`), `phone` (← `phone_numbers`), `rating`, `review_count`
sowie `query_keyword`, `query_city`, `query_state`, `query_country`, `query`.

`Phone Number Export` = `{{phone}}?.replace("+", "")` (führendes Plus entfernen).

### 3.2 Website-Auffüllung (KI-Fallback)

**Spalte `Domain URL`** — Clay „Claygent" (Web-Research-Agent)

* Modell: **OpenAI GPT-4o-mini**
* **Run-Bedingung:** `!{{website}} && {{QUALI ON/OFF}}` — läuft nur, wenn Google Maps *keine* Website liefert
* Prompt: siehe `prompts/company_domain.txt`
* Output-Schema: `{ "response": string }` (leerer String, wenn nichts gefunden)

**Spalte `Website final`** — Merge-Spalte, Reihenfolge:

1. `{{website}}?.split("?")?.[0]?.split("#")?.[0] || {{website}}` — Query/Fragment abschneiden
2. `{{Domain URL}}?.response`

### 3.3 Spalte `QUALI ON/OFF`

Checkbox, statische Formel `true`. Hauptschalter für die gesamte Qualifizierungsstufe.

### 3.4 Spalte `Dedupe` — der Trick

```js
({{Website final}} && (
   ({{Website final}}?.replace(/^https?:\/\/(www\.)?/, "")?.split("/")?.[0]||"").includes(".fr") ||
   ({{Website final}}?.replace(/^https?:\/\/(www\.)?/, "")?.split("/")?.[0]||"").includes(".nl") ||
   ({{Website final}}?.replace(/^https?:\/\/(www\.)?/, "")?.split("/")?.[0]||"").includes(".it")
 ))
  ? "DEDUPE"
  : ({{Website final}}
      ? ({{Website final}}?.replace(/^https?:\/\/(www\.)?/, "")?.split("/")?.[0] || "")
      : ({{Domain URL}} ? "DEDUPE" : ""))
```

Ergebnis pro Zeile:

* **Normalfall:** der nackte Host, z. B. `muster-metallbau.de` → echter Dedupe-Schlüssel
* **`.fr` / `.nl` / `.it`:** Literal `"DEDUPE"` → alle nicht-DACH-Domains kollabieren auf **eine** Zeile
* **Keine Website, aber Domain-URL-Lauf:** ebenfalls `"DEDUPE"` → wird weggeräumt
* **Gar nichts:** leerer String → wird von der Dedupe **nicht** angefasst (bleibt erhalten)

**Tabellen-Einstellung:** Auto-Dedupe **an**, Dedupe-Spalte = `Dedupe`, Regel = **„Keep oldest row"**.
Clay löscht keine Zeile, deren Dedupe-Zelle leer oder länger als 200 Zeichen ist.

> Das ist ein bewusster Hack: Statt eines Filters wird der Dedupe-Mechanismus als
> Ausschluss-Filter zweckentfremdet. Beim lokalen Nachbau sauberer als expliziter Filter.

### 3.5 Spalte `ICP Check` — HTTP API

```
POST https://api.skael.de/api/enrichments/icp_checker?url={{Website final}}&prompt=<ICP-Prompt>
Content-Type: application/json
Authorization: Bearer {{Skael API Key}}
```

* Parameter liegen als **Query-String**.
* **Run-Bedingung:** `{{Website final}} && {{QUALI ON/OFF}}`
* Kein Custom-Rate-Limit gesetzt.
* **Antwort:** `{ "icp": true, "confidence": 0.87, "reason": "…" }`
  → in Clay als `{{ICP Check}}.output.icp` etc.

Der Beispiel-ICP-Prompt (Metallbaubetriebe) liegt vollständig unter
`prompts/icp_beispiel_metallbau.txt`. Wie ein solcher Prompt für eine neue Zielgruppe
entsteht, steht in §5.

### 3.6 Auswertung des ICP-Ergebnisses

| Spalte | Definition |
|---|---|
| `Is Icp` | Checkbox, Auto-Extract auf `icp` aus dem ICP-Check-Output |
| `ICP` | Select `True` / `False` / `Unknown`:<br>`{{ICP Check}}?.output?.icp === true ? "True" : {{ICP Check}}?.output?.icp === false ? "False" : "Unknown"` |
| `SEND ON/OFF` | Checkbox, statisch `true` |

### 3.7 Spalte `Send table data` → ANREICHERUNG

* Ziel: `ANREICHERUNG` (`TABELLE_ANREICHERUNG`), Methode **„Send row"** (1:1)
* Übertragene Spalten (11 von 25): `business_id`, `place_id`, `Firmenname`, `website`,
  `address`, `zip`, `category`, `phone`, `rating`, `review_count`, `Website final`
* **Run-Bedingung:** `{{SEND ON/OFF}} && {{Is Icp}}`
* „Update existing rows on re-run" ist **an**.

### 3.8 Views (nur Anzeige, keine Prozesslogik)

| View | Filter | Zweck |
|---|---|---|
| `Gesamt` | `ICP Check has an error` | Fehlersuche |
| `Reviews` | keiner | Sichtung aller Zeilen |
| `Export` | `query_keyword = "Spedition"` | Altlast aus einer anderen Kampagne |

---

## 4. Stufe 4 — ANREICHERUNG (Kontaktdaten & Ansprache)

Tabelle `TABELLE_ANREICHERUNG`, ~6.400 Zeilen, 94 Spalten.
Eine Zeile = **eine qualifizierte Firma**.

Quelle: `Rows from: DATENSÄTZE` (~6.900 Datensätze) + `Rows from: DATENSÄTZE 2` (0).

### 4.1 Website ermitteln

```js
website         = {{Rows from: Datensätze Firmen}}?.["Website final"]
Company Domain  = Claygent(gpt-4.1-mini)   // Run: !{{website}}
website [Final] = /^(https?:\/\/)?([a-z0-9-]+\.)+[a-z]{2,}(\/.*)?$/i.test({{website}})
                    ? {{website}}
                    : {{Company Domain}}?.response
```

`Company Domain` nutzt denselben Prompt wie `Domain URL` in Stufe 3, mit
Custom-Rate-Limit 2 Requests/Sekunde.

### 4.2 Impressum ziehen — `SKAEL Impressum`

```
POST https://api.skael.de/api/enrichments/imprint_extractor
Content-Type: application/json
Authorization: Bearer {{Skael API Key}}

{ "domain": "<Host aus website [Final], ohne Protokoll/www/Pfad/Query/Fragment>" }
```

* **Run-Bedingung:** `{{website [Final]}}`
* **Antwort:** `firmenname`, `adresse`, `land`, `telefon`, `email`,
  `rechtlicher_verantwortlicher`, `geschaeftsfuehrer[]`, `ust_id`, `steuernummer`,
  `handelsregister_number`, `handelsregister_court`, `website`

Abgeleitete Spalten:

| Spalte | Formel |
|---|---|
| `Firmenname [Impressum]` | `{{SKAEL Impressum}}?.output?.firmenname` |
| `Firmenname [Final]` | `{{Firmenname [Impressum]}} \|\| {{Firmenname}}` |
| `Adresse [Impressum]` | `{{SKAEL Impressum}}?.output?.adresse` |
| `Telefon [Impressum]` | `{{SKAEL Impressum}}?.output?.telefon` |
| `Kontaktperson` | `{{SKAEL Impressum}}?.output?.geschaeftsfuehrer?.[0]` — **nur der erste GF** |

### 4.3 `Kontaktperson [Sauber]` — Namensbereinigung

Vollständige Formel (gekürzte Darstellung):

1. Klammer-Inhalte entfernen: `(…)`, `{…}`, `[…]`
2. Tokens verwerfen: leer, enthält `.`, ist `herr`/`frau`/`hr`/`rechtsanwalt`,
   oder komplett Großbuchstaben mit Länge > 1 (Titel-/Firmenzusätze)
3. Auf **erstes + letztes** verbleibendes Token reduzieren
4. Diakritika normalisieren: `ä→ae`, `ö→oe`, `ü→ue`, `ß→ss`, `é/è/ê/ë→e`, `á/à/â→a`,
   `ó/ò/ô→o`, `ú/ù/û→u`, `ñ→n`, `ç→c`
5. Apostrophe/Backticks entfernen, alles außer `A-Za-z0-9`, Leerzeichen und `-` streichen, trimmen

### 4.4 E-Mail-Wasserfall

```
Launch Campaign = (!!{{Kontaktperson [Sauber]}} || !!{{Email [Impressum]}})
```

**a) Impressum-Mail**

```js
Email [Impressum] = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email?.replace(/\(at\)|\[at\]/g,"@"))
                      ? email.replace(/\(at\)|\[at\]/g,"@") : ""
Email [Domain]    = Freemail-Domain?  →  Host aus website [Final] (letzte 2 Labels)
                    sonst  →  Domain der Impressum-Mail
```

Freemail-Blacklist: `gmx.de, web.de, google.de, google.com, gmail.com, outlook.com,
outlook.de, t-online.de, aol.com, 1und1.de, freenet.de, arcor.de, yahoo.com, mail.de,
aikq.de, mailbox.org, posteo.de, tutanota.com, icloud.com, googlemail.com, mail.ru,
protonmail.com, mail.com`

**b) Geschäftsführer-Mail suchen — `Skael Mailfinder`**

```
POST https://api.skael.de/api/enrichments/find_email_person
{ "domain": "{{website [Final]}}", "full_name": "{{Kontaktperson [Sauber]}}" }
```

* **Run:** `{{Launch Campaign}} && {{Kontaktperson [Sauber]}}`
* Rate-Limit: 5 Requests/Sekunde
* Antwort: `{ email, email_status: valid|risky|not_found|blacklisted, valid_email }`

**c) Fallback Findymail — `Find Work Email`**

* Clay-native Action `findymail-find-work-email`
* **Run:** `{{Launch Campaign}} && {{Kontaktperson [Sauber]}} && !{{Skael Mailfinder}}?.output?.email`
* Input: `full_name`, `company_domain` (= `website [Final]`)

**d) Validierung — `Skael Validate GF`**

```
POST https://api.skael.de/api/enrichments/verify_email
{ "email": "<Skael-Mailfinder-Mail || Findymail-Mail>" }
```

* **Run:** `{{Skael Mailfinder}}?.output?.email || {{Find Work Email}}?.email`
* Rate-Limit: 5 Requests/Sekunde
* Antwort: `{ email, code, status, is_deliverable, is_disposable, is_role, is_catch_all, is_free_provider, reason }`

**Debounce-Codes:**

| Code | Status | Bedeutung |
|---|---|---|
| 5 | Valid | zustellbar → *Safe to Send* |
| 4 | Risky | Catch-all-Domain |
| 7 | Risky | nicht verifizierbar → *Unknown* |
| 1, 2, 3, 6 | Invalid | Syntax / Spamtrap / Wegwerf / bounct |

```js
Email [GF]        = [5,4,7].includes(code) ? {{Skael Validate GF}}?.output?.email : ""
Email [GF][Status]= !Kontaktperson && SKAEL Impressum       ? "Kein GF"
                  : !Skael Validate GF                     ? "Not Run"
                  : code == 5 ? "Safe to Send"
                  : code == 4 ? "Risky"
                  : code == 7 ? "Unknown"
                  : [1,2,3,6].includes(code) ? "Invalid"
                  : "None found"
Email source GF   = "Skael" | "Findymail" | "None Found"    // per Case-insensitivem Vergleich
```

**e) Info@-Fallback — `Skael Validate Info@`**

```
POST https://api.skael.de/api/enrichments/verify_email
{ "email": "{{Email [Impressum]}}" }
```

* **Run:** `{{Launch Campaign}} === true && !{{Email [GF]}} && {{Email [Impressum]}}`
* `Email [Info@]` = `[4,5,7].includes(code) ? email : ""`
* `Email [Info@][Status]` analog zu oben (ohne den „Kein GF"-Zweig)

**f) Zusammenführen**

```js
Email [Final]        = Wasserfall:  {{Email [GF]}}  →  {{Email [Info@]}}
Email [Final][Type]  = Email [GF] ? "GF" : Email [Info@] ? "Info@"
                       : (GF-Status "Not Run"|"Kein GF") && Info@-Status "Not Run" ? "Not Run"
                       : "None found"
Email [Final][Status]= Email [GF] ? {{Email [GF][Status]}}
                       : Email [Info@] ? {{Email [Info@][Status]}}
                       : beide "None found" ? "None found"
                       : (GF "Not Run"|"Kein GF") && Info@ "Not Run" ? "Not Run"
                       : "None found"
```

### 4.5 Anrede & Namensteile

```js
First Name [GF] = {{Kontaktperson [Sauber]}}?.split(" ")?.[0]
Last Name [GF]  = {{Kontaktperson [Sauber]}}?.split(" ")?.pop()
```

**`Anrede [Prompt] (2)`** — Clay „Use AI", Modell **gpt-4o-mini**

* **Run:** `!!{{First Name [GF]}} && !!{{Email [Final]}}`
* Prompt: `prompts/anrede.txt`, Schema: `prompts/anrede.schema.json`
* Output: `{ "anrede": "Herr"|"Frau", "confidence": 0–100 }`
* Regel: bei Unisex-/unbekannten Vornamen **immer „Herr"**

Daraus:

| Spalte | Formel |
|---|---|
| `Anrede` | `{{Anrede [Prompt] (2)}}?.anrede` |
| `Confidence` | `{{Anrede [Prompt] (2)}}?.confidence` |
| `Formal` | `Anrede === "Herr" ? "Sehr geehrter" : Anrede === "Frau" ? "Sehr geehrte" : ""` |
| `Ansprache Formal [Final]` | `Anrede ? Formal + " " + Anrede + " " + Last Name : Email [Final] ? "Sehr geehrte Damen und Herren" : ""` |
| `Ansprache Normal [Final]` | `Anrede ? "Hallo " + Anrede + " " + Last Name : Email [Final] ? "Hallo" : ""` |
| `Ansprache Normal [GT] [Final]` | wie oben mit `"Guten Tag"` |
| `Ansprache Persönlich [Final]` | `First Name && Anrede ? "Hallo " + First Name : Email [Final] ? "Hallo" : ""` |

### 4.6 Personalisierung

```
Personalisierung generieren = {{Email [Final]}} ? true : false
```

**`SKAEL WEBSCRAPER`**

```
POST https://api.skael.de/api/enrichments/web_scraper
{ "url": "{{website [Final]}}" }
```

* **Run:** `!!{{website [Final]}} && !!{{Personalisierung generieren}}`
* Antwort u. a.: `site_status_code`, `final_url`, `title`, `description`, `keywords`,
  `favicon`, `social_links`, `links`, `emails`, `body_text`

```js
Bodytext Website = ({{SKAEL WEBSCRAPER}}?.output?.body_text || "")?.slice(0, 8192)
```

**`Personalisierung AI`** — „Use AI", **gpt-4o-mini**

* **Run:** `{{SKAEL WEBSCRAPER}} && {{Personalisierung generieren}}`
* Prompt: `prompts/personalisierung.txt` (RISE-Struktur, deutscher Copywriter)
* Schema: `prompts/personalisierung.schema.json` → `{ "complimentText": string }`
* Ergebnis: max. 2 Sätze / 30 Wörter, kleingeschrieben beginnend (Fortsetzung nach der Anrede)
* `Personalisierung` = `{{Personalisierung AI}}?.complimentText`

### 4.7 Videotitel

```js
Video Title Input =
  (!First Name ? "Videotitle: Video für " + Firmenname
               : "Videotitle: Video für " + First Name + " " + (Last Name || "") + " von " + Firmenname)
  + "\n" + "Firstname: " + (First Name || "nicht vorhanden oder firstname")
  + ", Lastname: " + (Last Name || "nicht vorhanden oder lastname")
  + "\n" + "Firmenname: " + (Firmenname || "")
```

**`Cleaned Video Title`** — „Use AI", **gpt-4o-mini**

* **Run:** `{{Video Title Input}} && {{Personalisierung generieren}}`
* Prompt: `prompts/video_title_cleanup.txt`
  (CAPS entfernen, `von` → `vom` / `von der` / `von den`, Firmenname kürzen)
* Schema: `{ "cleanedText": string, "cleanedCompanyName": string }`
* `Video Title` = `{{Cleaned Video Title}}?.cleanedText`

### 4.8 Versandfreigabe

```js
Ready to Send = !!{{Email [Final]}} && !!{{Personalisierung}} && !!{{Video Title}}
```

`Bereits exportiert` ist eine manuelle Checkbox.
Der View `Gesamt` filtert: `Bereits exportiert is not checked AND Ready to Send is checked`
→ ~2.400 von ~6.400 Zeilen versandbereit.

### 4.9 Deaktivierte Bausteine (im Workbook vorhanden, aber abgeschaltet)

Alle folgenden Spalten haben eine Run-Bedingung, die auf `&& false` endet, laufen also nie:

| Spalte | Anbieter | Zweck |
|---|---|---|
| `SKAEL Linked In Search` | Skael `ai_research_agent` (Gemini 2.5 Flash, max 10 Steps) | LinkedIn-Profil-URL finden |
| `Linked In Kontaktperson` | Formel | URL übernehmen, wenn ≠ „No LinkedIn profile found" |
| `Enrich Person` | Clay `enrich-person` | Person anreichern |
| `Enrich person` | Clay `enrich-person-with-mixrank-v2` | Person anreichern (v2) |
| `LinkedIn Match` | Use AI (gpt-4o-mini) | Prüft, ob das Profil zur Person gehört |
| `Find mobile number` | LeadMagic | Handynummer |
| `Find Phone Number` | Wiza | Telefonnummer |
| `Find Mobile Number` | Upcell | Handynummer |
| `Find phone numbers` | Forager | Telefonnummern |
| `Find Mobile Number (2)` | Prospeo | Handynummer |
| `Find Mobile Number from LinkedIn` | ContactOut | Telefonnummer |
| `Find Mobile Number (3)` | Datagma | Handynummer |
| `Validate …` (7×) | Clearout | Nummernvalidierung |
| `Mobile Phone` | Wasserfall über alle obigen | finale Handynummer |
| `HTTP RESERVE` … `(6)` | — | leere Platzhalter-Spalten (`runIf: false`) |

Der Telefon-Wasserfall probiert die Anbieter der Reihe nach durch und validiert jede
gefundene Nummer über Clearout; nur „valid" wird übernommen.

---

## 5. Der ICP-Prompt-Builder (Pflichtbestandteil vor jedem Lauf)

Bevor Stufe 3 laufen kann, muss für die neue Zielgruppe ein ICP-Prompt gebaut werden.
Dafür existiert ein fester Frage-Ablauf in **3 Runden**:

**Runde 1 — Wer ist der ideale Kunde?**
Branche/Nische · Beschreibung in 1–2 Sätzen · Markt (DE / DACH / Deutschschweiz …)

**Runde 2 — Woran erkennt man ihn, woran nicht?**
Pflichtbegriffe auf der Website · typische Fehlläufer · Größen-Filter · harte Ausschlüsse

**Runde 3 — Feinschliff**
Confidence-Treiber · Prüfungsreihenfolge · im Zweifel durchlassen oder rausfiltern

**Ergebnis-Struktur des Prompts:**

```
ROLLE: B2B Lead-Qualifizierer für [Branche] in [Region].
AUFGABE: [1–2 Sätze]. Kein [Branche] = kein ICP. Keine Ausnahmen.
PRÜFUNG 1 — [härtester Filter]: [Beschreibung + Abbruchbedingung]
PRÜFUNG 2 — [nächster Filter]: [Beschreibung + Abbruchbedingung]
MUSS-KRITERIEN (mindestens 2 müssen zutreffen): [Kategorie]: [Begriffe] …
HARTE AUSSCHLUSSREGEL: [1–2 Sätze]
SOFORT RAUS (ein Treffer reicht): [Kategorie]: [Ausschlüsse] …
CONFIDENCE ERHÖHEN: [Signale]
CONFIDENCE SENKEN: [Signale]
OUTPUT (JSON): {"is_icp": boolean, "confidence": 0.0-1.0, "reason": "Kurze Begründung auf Deutsch"}
Bei nicht erreichbarer Website: {"is_icp": false, "confidence": 1.0, "reason": "Website nicht erreichbar"}
```

Regeln: nur Bodytext-basierte Kriterien, Deutsch, max. 400 Wörter, keine Beispiele im
Prompt, lieber aggressiv filtern. Danach wird eine Google-Maps-Keyword-Liste in
Tier 1/2/3 geliefert — das sind die `Keyword`-Werte für Stufe 1.

> **Wichtig:** Die Skael-API antwortet mit dem Feld `icp`, nicht `is_icp`.
> Der Prompt schreibt `is_icp` vor, die API normalisiert das. Im Code immer `icp` lesen.

Der vollständige Master-Prompt liegt in `prompts/icp_prompt_builder.md`,
das gebaute Beispiel in `prompts/icp_beispiel_metallbau.txt`.

---

## 6. Reihenfolge & Abhängigkeiten (für den lokalen Nachbau)

```
1  Keywords (Tier 1/2/3) + Länder + min. Einwohnerzahl festlegen
2  ICP-Prompt bauen (3 Runden)
3  find_cities   je Land                                  → Städte
4  maps_search   je (Keyword × Stadt)   [5 req/s]         → Firmen
5  Dedupe über Host von Website final; .fr/.nl/.it raus
6  Company Domain (LLM) wo Website fehlt
7  icp_checker   je Firma mit Website                     → icp/confidence/reason
8  Filter: icp === true
9  imprint_extractor je Firma                             → GF, Adresse, Telefon, Mail
10 Kontaktperson säubern
11 find_email_person (+ Findymail-Fallback)               → GF-Mail
12 verify_email GF-Mail; sonst verify_email Impressum-Mail
13 Anrede-LLM → Anrede, Confidence, Ansprachen
14 web_scraper → Bodytext → Personalisierung-LLM
15 Video-Title-LLM
16 Ready to Send = Mail && Personalisierung && Videotitel
17 Export
```

---

## 7. Bekannte Schwachstellen im Clay-Original

| # | Beobachtung | Auswirkung |
|---|---|---|
| 1 | `find_cities` `limit: 5000` | DE wird bei ~7.600 Städten gekappt |
| 2 | Dedupe-Hack über Literal `"DEDUPE"` | `.fr`/`.nl`/`.it` werden auf **eine** Zeile kollabiert statt sauber gefiltert; schwer nachvollziehbar |
| 3 | `Kontaktperson` nimmt nur `geschaeftsfuehrer[0]` | Weitere GF gehen verloren |
| 4 | `Email [Impressum]` prüft dieselbe Bedingung zweimal (`X || X || ""`) | Redundant, funktional egal |
| 5 | `Email [GF][Status]` hat zwei identische Endzweige (`"None found"`) | Redundant |
| 6 | Skael API Key als Klartext-Formel in **jeder** Tabelle | Key steht im Workbook; bei Weitergabe des Workbooks mit exportiert |
| 7 | `ICP Check` ohne Custom-Rate-Limit | Bei 26k Zeilen theoretisch Rate-Limit-Risiko |
| 8 | Zwei Spalten mit fast gleichem Namen (`Enrich Person` / `Enrich person`) | Verwechslungsgefahr |
| 9 | View `Export` filtert auf `query_keyword = "Spedition"` | Altlast einer anderen Kampagne |
| 10 | `Email [GF][Status] (2)` ist eine unbenutzte Dublette von `Email [GF][Status]` | Toter Code |
