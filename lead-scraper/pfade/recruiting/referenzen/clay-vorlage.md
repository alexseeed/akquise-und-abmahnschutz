# Clay-Workbook „GMAPS 3.0 Recruting + NK | BAFA“ – Spaltenreferenz (Herkunft)

**Zweck:** jede Tabelle, jede neue Spalte, jede Run-Bedingung des Recruiting-Workbooks – so genau, dass man es prüfen, reparieren oder lokal nachbauen kann.
**Für wen:** Entwickler, die nachvollziehen wollen, woher der lokale Ablauf stammt.
**Verwandt:** `../ABLAUF.md` · `../../google-maps/docs/07_RECRUITING.md` · `../../google-maps/docs/01_PROZESS.md` · `../../../wissen/05_pfad-recruiting.md`
**Quelle:** Kopie der Vorlage (Workspace `WORKSPACE_ID`, Workbook `WORKBOOK_ID`), ausgelesen am 04.10.2026. Alle Tabellen waren leer (Vorlage). Am Workbook wurde nichts verändert.

> **Nur Herkunft.** Clay wird nicht mehr verwendet; der Pfad läuft lokal im Scraper-Programm (`../../google-maps/`). Wie der Nachbau arbeitet und wo er bewusst abweicht: `../../google-maps/docs/07_RECRUITING.md`. Die Prompts liegen angepasst in `../../google-maps/prompts/`: branchenneutral als Standard, die Logistik-Fassungen aus Clay in `../../google-maps/prompts/beispiele/`.

---

## 0. Überblick

```
Einstieg A – Google Maps (Branche + Region)
  EINGABE ──find_cities──► VERARBEITUNG ──maps_search──► DATENSÄTZE
                                                           │ Dedupe · ICP CHECK (Skael) · Stelle (Claygent)
                                                           ├─ RC SEND  (Stelle gefunden)      ──► ANREICHERUNG     (Opener zur Stelle)
                                                           └─ NK SEND  (keine Stelle) – AUS   ──► NK ANREICHERUNG  (Website-Kompliment)

Einstieg B – Stellenanzeigen (Indeed über Apify)
  Import ──Domain (Claygent)──► ICP CHECK (Skael) ──Send table data (3)──► ANREICHERUNG
```

| Tabelle | Spalten (sichtbar) | Rolle | Dedupe-Spalte |
|---|---|---|---|
| `EINGABE` | 8 (6) | Keyword × Land → Städte | – |
| `Import` | 15 (12) | Stellenanzeigen aus einem Apify-Actor | – |
| `VERARBEITUNG` | 15 | Stadt × Keyword → Google-Maps-Suche | ja |
| `DATENSÄTZE` | 35 (29) | Firma: Dedupe, ICP, Stellen-Erkennung, Weiche RC/NK | `Dedupe` |
| `ANREICHERUNG` | 70 (46) | **RC** = Recruiting-Ansprache | ja |
| `NK ANREICHERUNG` | 63 (44) | **NK** = Firmen ohne erkannte Stelle, Website-Kompliment | ja |

Alle Tabellen: Auto-run **an**. KI-Spalten nutzen einen in Clay hinterlegten OpenAI-Zugang (GPT-4o mini). Alle Skael-Spalten sind „HTTP API“-Spalten (Header `Authorization: Bearer {{Skael API Key}}`, `Content-Type: application/json`).

---

## 1. EINGABE und VERARBEITUNG

**Identisch mit dem Google-Maps-Original.** Spalten, Formeln und Run-Bedingungen: `../../google-maps/docs/01_PROZESS.md` §1 und §2.

- EINGABE: `Skael API Key`, `Keyword`, `Min Population`, `Country Code`, `SKAEL CITIES` (`find_cities`, `limit` 5000), `Send table data` (eine Zeile je Stadt nach VERARBEITUNG).
- VERARBEITUNG: `Rows from: EINGABE`, `Skael API Key`, `Created At`, `Updated At`, `input_keyword`, `input_city`, `input_country`, `query` (`"<Keyword> in <Stadt>"`), `RUN`, `SKAEL MAPS` (`maps_search`, `zoom=11`, `limit=2000`), Fan-out nach DATENSÄTZE.

---

## 2. DATENSÄTZE – Firma prüfen und Weiche stellen

Quelle: `Rows from: Firmen Scraper` (= VERARBEITUNG). Die ersten Spalten bis `ICP` entsprechen dem Original (`01_PROZESS.md` §3): `business_id`, `place_id`, `Firmenname`, `website`, `address`, `zip`, `category`, `phone`, `Phone Number Export`, `rating`, `review_count`, `QUALI ON/OFF`, `Domain URL`, `Website final`, `Dedupe`, `ICP CHECK`, `Is Icp`, `ICP`. Ausgeblendet: `query_keyword`, `query_city`, `query_state`, `query_country`, `query`, `Average Qualification`.

### 2.1 `ICP CHECK` – Skael `icp_checker`

```
POST https://api.skael.de/api/enrichments/icp_checker
Query-Parameter:  url    = {{Website final}}
                  prompt = <ICP-Prompt>          → ../../google-maps/prompts/beispiele/icp_logistik.txt
```

Antwort `{ icp, confidence, reason }`, daraus `Is Icp` (Checkbox) und `ICP` (True/False/Unknown). Der hinterlegte Prompt ist auf **Logistik und Spedition** zugeschnitten und muss je Zielgruppe ersetzt werden (Bauanleitung: `../../google-maps/prompts/icp_prompt_builder.md`).

### 2.2 `Stelle` – sucht eine offene Stelle auf der Website (neu)

| | |
|---|---|
| Typ | Clay „Web research (Claygent)“, OpenAI GPT-4o mini |
| Prompt | heute `../../google-maps/prompts/beispiele/stellenanalyse_logistik.txt` (Eingabe: `{{Website final}}`); der Standard `stellenanalyse.txt` ist branchenneutral und nimmt die gesuchten Berufe der Kampagne |
| Ausgabe-Schema | `../../google-maps/prompts/stellenanalyse.schema.json` → `stellenGefunden` (bool), `anzahl` (int), `stellenangebote` (Liste mit genau einem Objekt `position`, `bereich`, `beschreibung`) |
| Run-Bedingung | `{{Is Icp}}` und `{{QUALI ON/OFF}}` |

Der Prompt sucht Karriere-Bereiche und gibt **genau eine** Stelle aus, nach Priorität: Fahrer/Transport → Disposition → Lager → operative Führung → Ausbildung. Agentur- und Dienstleister-Stellen (z. B. „Webdesign by …“) werden ausgeschlossen.

### 2.3 Auswertung (neu)

| Spalte | Typ | Inhalt |
|---|---|---|
| `Stelle vorhanden` | Checkbox | Auto-Extrakt `stellenGefunden` aus `Stelle` |
| `JOB TITLE` | Text | Auto-Extrakt aus `Stelle` → `stellenangebote` (Feld `position`) |
| `JOB DESCRIPTION` | Text | Auto-Extrakt aus `Stelle` → `stellenangebote` (Feld `beschreibung`) |
| `SEND ON/OFF` | Checkbox | statisch `true` (Not-Aus) |

### 2.4 Weiche

| Spalte | Ziel | Run-Bedingung | Status |
|---|---|---|---|
| `RC SEND` | `ANREICHERUNG` | `{{SEND ON/OFF}}` && `{{Is Icp}}` && `{{Stelle vorhanden}}` | aktiv |
| `NK SEND` | `NK ANREICHERUNG` | `{{SEND ON/OFF}} && {{Is Icp}} && !{{Stelle vorhanden}} && false` | **abgeschaltet** (`&& false`) |

Beide: Methode „Send row“, „Update existing rows on re-run“ an. `RC SEND` überträgt 15 von 28 Spalten, darunter Firmendaten, `Website final`, `Stelle vorhanden`, `JOB TITLE`, `JOB DESCRIPTION` und die `query_*`-Herkunftsfelder.

---

## 3. Import – Einstieg über Stellenanzeigen (Indeed via Apify)

> **Nicht übernommen.** Dieser Einstieg ist im lokalen Scraper bewusst entfernt (Entscheidung vom 05.10.2026). Recruiting arbeitet nur mit Google Maps + Firmen-Website. Stellenanzeigen aus Jobportalen holt seit 14.10.2026 die eigene Kampagnen-Art **Stellensuche** über die Skael-Jobendpunkte (`../../stellensuche/ABLAUF.md`).

| Spalte | Typ | Inhalt |
|---|---|---|
| `Import data from Apify actor` | Quelle | Zeilen aus einem Apify-Actor-Lauf (Indeed-Stellenanzeigen). Konto und Actor sind in der Quelle hinterlegt, nicht in einer Spalte. |
| `Rows from: Datensätze Firmen` | Quelle | zweite, optionale Quelle (Zeilen aus einer Datensätze-Tabelle) |
| `Skael API Key` | Text | muss gefüllt sein |
| `Company Name` | Formel | `company` ‖ `companyName` ‖ `employerName` ‖ Datensätze `title` ‖ Datensätze `Firmenname` ‖ `source` |
| `Indeed Url` | Formel | (ausgeblendet) Link zur Anzeige |
| `Job Title` | Formel | `positionName` ‖ `title` ‖ Datensätze `Job titel` / `Job title` |
| `Job Description` | Formel | `description` ‖ `descriptionText` ‖ Datensätze `Job Description` ‖ `textSnippet` |
| `Company Url` | Formel (URL) | `companyInfo.url` ‖ `companyLinks.corporateWebsite` ‖ Datensätze `website` |
| `Created At` | Datum | (ausgeblendet) |
| `Company Domain` | Claygent, GPT-4o mini | Prompt „Find domain for {{Company Name}}“ → `{ response }`; Run-Bedingung referenziert `{{Company Url}}` (siehe Befund 4) |
| `Final Company URL` | Formel (URL) | `{{Company Url}} ‖ {{Company Domain}}?.response ‖ ""` |
| `ICP CHECK` | HTTP API | wie 2.1, aber `url = {{Final Company URL}}`; Run: `{{Final Company URL}}`; Custom-Rate-Limit-Fenster 1.000 ms |
| `Is Icp` | Checkbox | Auto-Extrakt `output.icp` |
| `Send table data (3)` | Send row → `ANREICHERUNG` | überträgt `Company Name`, `Job Title`, `Job Description`, `Company Url`, `Final Company URL`; Run: `{{Is Icp}}` |

Die Feldnamen (`positionName`, `company`, `descriptionText`, `companyInfo.url`, `companyLinks.corporateWebsite`) decken die gängigen Indeed-Actors auf Apify ab. Welcher Actor genau angebunden ist, zeigt die Quelle in Clay (Konto + Actor + Lauf/Datensatz).

Hinweis: Über Einstieg B gibt es **keine** Website-Prüfung auf weitere Stellen – die Stelle steht ja schon fest.

---

## 4. ANREICHERUNG (RC) – Ansprache mit Bezug zur Stelle

Quelle: `Rows from: Datensätze Firmen` mit **zwei** Zuläufen (`RC SEND` aus DATENSÄTZE und `Send table data (3)` aus Import). Bis `Personalisierung generieren` Standard-Anreicherung (`../../google-maps/docs/01_PROZESS.md` §4). Danach:

| Spalte | Typ | Inhalt / Run-Bedingung |
|---|---|---|
| `JOB TITLE` | Formel | `Rows["JOB TITLE"]` ‖ `Rows["Job Title"]` (deckt beide Zuläufe ab) |
| `JOB DESCRIPTION` | Formel | analog |
| `Normalisierter Jobtitel` | Use AI, GPT-4o mini | Prompt `../../google-maps/prompts/jobtitel_normalisierung.txt`, Schema `…schema.json` → `normalisierterTitel`; Run: `{{Personalisierung generieren}}` && `{{JOB TITLE}}` |
| `Personalisierung AI` | Use AI, GPT-4o mini | Prompt heute `../../google-maps/prompts/beispiele/personalisierung_stellenanzeige_logistik.txt` mit `{{Job Titel}}` und `{{JOB DESCRIPTION}}`; Run: `{{Normalisierter Jobtitel}}?.normalisierterTitel && {{Personalisierung generieren}}` |
| `Job Titel` | Text | Auto-Extrakt `normalisierterTitel` |
| `Personalisierung` | Text | Ergebnis von `Personalisierung AI` (`complimentText`) |
| `Ready to Send` | Checkbox | `!!{{Email [Final]}} && !!{{Job Titel}} && !!{{Personalisierung}}` |

Kein Website-Scraper, kein Videotitel. Ergebnis-Beispiel: „…, ich habe gesehen, dass Sie Berufskraftfahrer suchen, die CE-Führerschein und Erfahrung im Fernverkehr mitbringen.“

---

## 5. NK ANREICHERUNG – Firmen ohne erkannte Stelle

Quelle: `Rows from: Datensätze Firmen` (`NK SEND`, derzeit aus). Standard-Anreicherung, danach `SKAEL WEBSCRAPER` → `Bodytext Website` → `Personalisierung AI` (RISE-Website-Kompliment, `../../google-maps/prompts/personalisierung_website.txt`) → `Personalisierung`. `Ready to Send` = `!!{{Email [Final]}} && !!{{Personalisierung}}`. Kein Videotitel.

---

## 6. Befunde im Clay-Original (Umgang im lokalen Nachbau: `../../google-maps/docs/07_RECRUITING.md` §5)

| # | Befund | Wirkung | Empfehlung |
|---|---|---|---|
| 1 | Workspace zeigt bei allen Skael-Spalten „Upgrade to Growth to unlock this feature! HTTP API Integrations are only available on Growth plans or higher.“ | Städte, Maps-Suche, ICP-Prüfung, Impressum, E-Mail-Suche und -Prüfung laufen **nicht** | Clay-Tarif Growth (oder höher) aktivieren, bevor getestet wird |
| 2 | `NK SEND` endet auf `&& false` | Firmen ohne erkannte Stelle werden nie angereichert | bewusst entscheiden: an (`&& false` entfernen) oder aus lassen |
| 3 | ICP-, Stellen- und Opener-Prompt sind auf Logistik/Spedition geschrieben; der Jobtitel-Prompt nennt Beispiele aus dem Fensterbau | andere Zielgruppen werden falsch bewertet | im Nachbau: Standard-Prompts branchenneutral, Logistik-Fassungen in `prompts/beispiele/`; je Kampagne anpassen |
| 4 | `Company Domain` (Import): In der Run-Bedingung ist `{{Company Url}}` referenziert; ob davor ein `!` steht, war im Auslesen nicht sicher erkennbar | ohne `!` sucht die KI die Domain gerade dann, wenn sie schon da ist | in Clay prüfen; richtig ist `!{{Company Url}}` |
| 5 | `Normalisierter Jobtitel`: Der Prompt-Platzhalter hinter „Jobtitel:“ ist die Quellspalte `Rows from: Datensätze Firmen`, nicht `JOB TITLE` | KI bekommt den ganzen Datensatz statt nur den Titel (funktioniert meist, kostet aber Tokens und kann danebengreifen) | Platzhalter auf `{{JOB TITLE}}` umstellen |
| 6 | Stellen-Prompt verlangt `stellen_gefunden`, das Schema heißt `stellenGefunden` | unkritisch – das Schema gewinnt | beim Nachbau Schema-Namen verwenden |
| 7 | `Skael API Key` ist in jeder Tabelle eine Textspalte | leere Zelle = Skael-Aufruf schlägt fehl; Schlüssel steht im Klartext im Workbook | als Formel mit festem Wert setzen; Workbook nicht weitergeben |
| 8 | Bedeutung von „NK“ und „BAFA“ im Workbook-Namen ist im Workbook nicht erklärt | – | beim Betreiber erfragen und hier ergänzen |
