# Abweichungen: lokaler Nachbau vs. Clay-Original

Was der lokale Scraper anders macht — und warum.

---

## 1. Bewusste Korrekturen

| # | Clay-Original | Lokal | Grund |
|---|---|---|---|
| 1 | Dedupe-Hack: `.fr`/`.nl`/`.it` und geratene Domains bekommen den Literal-Wert `"DEDUPE"` und werden von der Auto-Dedupe auf eine Zeile kollabiert | Eigene Spalte `dedupe_status` mit den Werten `kept` / `dropped_duplicate` / `dropped_excluded` | Gleiches Ergebnis, aber nachvollziehbar. Nichts wird gelöscht — ausgeschlossene Zeilen bleiben zur Kontrolle in der DB. |
| 2 | `Kontaktperson [Sauber]` ersetzt nur **klein**geschriebene Umlaute; `Ä`, `Ö`, `Ü` fallen anschließend dem Zeichenfilter zum Opfer (`Änderung` → `nderung`) | Groß- und Kleinschreibung werden korrekt ersetzt (`Ä` → `Ae`) | Klarer Fehler im Original. `ß` bleibt ausgenommen, weil `"ß".upper() == "SS"`. |
| 3 | `Email [Impressum]` prüft dieselbe Bedingung zweimal (`X \|\| X \|\| ""`) | Einmal | Redundanz ohne Wirkung |
| 4 | `Email [GF][Status]` hat zwei identische Endzweige (`"None found"`) | Ein Zweig | dito |
| 5 | Dublette `Email [GF][Status] (2)` | entfällt | Toter Code |
| 6 | Sechs leere `HTTP RESERVE`-Spalten (`runIf: false`) | entfallen | Platzhalter ohne Funktion |
| 7 | Skael API Key als Klartextformel in jeder Tabelle | `.env` + `.gitignore` | Kein Key im Repo |
| 8 | Kein Custom-Rate-Limit für `icp_checker` | Globales Skael-Limit (Default 5/s), zentral einstellbar | Schützt vor 429 bei großen Läufen |
| 9 | `Contains Error` greift mit `{{SKAEL MAPS}}?.[0]` auf ein **Objekt** per Index zu → immer `undefined`, die Spalte ist faktisch tot | Prüft, ob die Antwort selbst als Fehler markiert ist (`error`, `error_message`, `status = failed`) | Ein Volltext-Scan über die Treffer wäre fatal: ein einzelnes „error" in einer Domain oder Beschreibung würde eine ganze Stadt mit bis zu 2.000 Firmen verwerfen |
| 10 | Maps-Treffer ohne `business_id` | Ersatzschlüssel `synthetic:<query-id>:<index>` | Laut Skael-Doku ist `business_id` immer gesetzt; falls doch nicht, geht die Firma nicht verloren |
| 11 | Adressvergleich in `Email [Domain]` ist Groß-/Kleinschreibungs-sensitiv (`info@GMX.DE` gilt nicht als Freemail); Protokoll-Strip ebenfalls (`HTTPS://…` ergibt den Dedupe-Key `"HTTPS:"`) | Beides case-insensitiv | Im Original stille Fehlklassifikationen |
| 12 | `website [Final]` testet die URL ohne `.strip()` → `" https://a.de "` fällt durch und landet beim KI-Fallback | Wird vorher getrimmt | Vermeidet unnötige KI-Calls |
| 13 | `Find Work Email` läuft über Clays Findymail-Integration; Fehler wie leeres Guthaben bleiben stille Leerzellen | Direkte Findymail-API mit eigenem Schlüssel und der Domain statt der URL. 401/402/423 lassen den Lead offen (siehe 2.4), Wiederholung bei 429/5xx; kein Findymail-Aufruf nach einem Mailfinder-Fehler | Sonst würden bei leerem Guthaben alle Leads still ohne Geschäftsführer-Adresse abgeschlossen |

---

## 2. Technisch notwendige Unterschiede

### 2.1 Domainsuche (`Domain URL` / `Company Domain`)

Clay nutzt **Claygent** — einen Web-Research-Agenten mit echtem Browsing.
Ein reines Chat-Modell kann nicht browsen.

Lokal: OpenAI Chat Completions mit `gpt-4.1-mini`, Structured Output
`{ "response": string }`, plus `web_search_preview` als Tool. Ob das Tool greift,
hängt vom gewählten Modell und Account ab.

**Konsequenz:** Diese Stufe liefert lokal potenziell schlechtere Ergebnisse als in
Clay. Betroffen sind nur Firmen **ohne** Website in Google Maps.

Alternativen, falls die Trefferquote nicht reicht:

* Skael `ai_research_agent` verwenden (agentisch, mit Websuche) — Umbau in
  `scraper/llm.py:company_domain`
* Diese Stufe abschalten: `run --stage 3b` statt `--stage 3` (überspringt 3a)

### 2.2 Fan-out und Tabellen

Clay: vier physische Tabellen mit „Send table data"-Aktionen.
Lokal: vier SQLite-Tabellen (`eingabe`, `verarbeitung`, `datensaetze`, `anreicherung`)
mit denselben Beziehungen. Das „Senden" ist ein Insert.

### 2.3 `DATENSÄTZE 2`

Existiert lokal nicht. In Clay nur Überlaufziel für das 50.000-Zeilen-Limit,
im Workbook nie ausgelöst (0 Zeilen). SQLite kennt dieses Limit nicht.

### 2.4 Auto-Run und Fehlerbehandlung

Clay rechnet Zellen automatisch nach, sobald sich Abhängigkeiten ändern, und lässt
eine fehlgeschlagene Zelle leer — beim nächsten Lauf wird sie erneut versucht.

Lokal werden Stufen explizit aufgerufen. Jede Stufe ist **idempotent**: Sie
bearbeitet nur Zeilen, deren Zielfeld noch leer ist. Bei einem API-Fehler wird
bewusst **nicht** in dieses Zielfeld geschrieben; stattdessen zählt die Spalte
`attempts` hoch und `error` hält die Meldung. Die Zeile wird beim nächsten Lauf
erneut versucht, bis `MAX_ATTEMPTS` (Standard 3) erreicht ist.

Ohne diese Regel würde ein einzelner 429 einen Lead dauerhaft ausschließen —
genau die Falle, in die eine naive Portierung läuft.

Offene Fehler prüfen:

```sql
SELECT id, firmenname, attempts, error FROM anreicherung WHERE error IS NOT NULL;
```

Nach Behebung `attempts` zurücksetzen, dann läuft die Zeile wieder mit:

```sql
UPDATE anreicherung SET attempts = 0, error = NULL WHERE error IS NOT NULL;
```

### 2.5 Nebenläufigkeit

Clay parallelisiert intern. Lokal: `ThreadPoolExecutor` mit `MAX_CONCURRENCY`
(Default 5) plus Token-Bucket-Rate-Limiter je Client. Die in Clay gesetzten
Limits (5/s für `maps_search`, `find_email_person`, `verify_email`) sind als
globales Skael-Limit übernommen.

---

## 3. Übernommen, aber standardmäßig aus

| Baustein | Status im Clay-Original | Lokal |
|---|---|---|
| LinkedIn-Suche (`ai_research_agent`) | deaktiviert (`&& false`) | implementiert, `DO_LINKEDIN=false` |
| Personalisierung + Videotitel | aktiv | implementiert, `DO_PERSONALISIERUNG` / `DO_VIDEO_TITLE` = true |
| Findymail-Fallback | aktiv | implementiert, `USE_FINDYMAIL=true` (braucht `FINDYMAIL_API_KEY`) |

---

## 4. Nicht portiert

Der **Telefon-Wasserfall** (`Mobile Phone`) ist im Clay-Workbook vollständig
deaktiviert und stützt sich auf acht Clay-native Drittanbieter-Integrationen:

LeadMagic · Wiza · Upcell · Forager · Prospeo · ContactOut · Datagma · Clearout
(Validierung) · People Data Labs / MixRank (Personen-Anreicherung)

Jeder davon bräuchte einen eigenen API-Zugang und eine eigene Client-Implementierung.
Da im Original nichts davon läuft und keine Keys vorliegen, ist die Logik nur
dokumentiert (siehe `docs/01_PROZESS.md` §4.9), nicht implementiert.

Die Struktur ist vorbereitet: `anreicherung.linkedin_url` existiert, ein
Telefon-Feld lässt sich analog zu `stufe4g_linkedin` ergänzen.

---

## 5. Was 1:1 identisch ist

* Alle Skael-Endpunkte, Parameter und Query-String-vs-Body-Entscheidungen
* `query`-Aufbau: `"<Keyword> in <Stadt>"`, Fallback auf das Land
* `zoom=11`, `limit=2000` für `maps_search`; `limit=5000` für `find_cities`
* Alle vier KI-Prompts und JSON-Schemata (unverändert aus dem Workbook extrahiert)
* Modelle je Spalte: `DATENSÄTZE.Domain URL` = `gpt-4o-mini`,
  `ANREICHERUNG.Company Domain` = `gpt-4.1-mini`, die drei übrigen KI-Schritte = `gpt-4o-mini`
* Die gesamte E-Mail-Wasserfall-Logik inklusive Debounce-Codes 4/5/7 = brauchbar
* Freemail-Blacklist (23 Domains)
* Namensbereinigung inklusive Titel- und Firmenzusatz-Filter
* Alle vier Ansprache-Varianten
* `Bodytext` auf 8.192 Zeichen gekürzt
* `Ready to Send` = E-Mail && Personalisierung && Videotitel
