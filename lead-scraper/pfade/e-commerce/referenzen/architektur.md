# Architektur: Crawler, Impressum, Registerdaten, Recht

**Zweck:** Ideen für einen eigenen Crawler (Shopsystem-Erkennung, eigenes Impressum-Parsing, Registerdaten), falls der Pfad über den Clay-Nachbau hinaus wachsen soll.
**Für wen:** Entwickler und KI-Modelle (Claude Code), die den Pfad bauen oder ändern.
**Verwandt:** `../../../wissen/06_pfad-e-commerce.md` · `fingerprints.md` · `../../google-maps/CLAUDE.md` (Konventionen, die übernommen werden)
**Stand:** 2026-10-08 · **Prüfen bis:** 2027-04-08 (LLM-Preise, Register-Zugänge, Rechtslage)

Kennzeichnung:

- **[V]:** Primärquelle gelesen
- **[S]:** Sekundärquelle
- **[E]:** Einschätzung

## Inhalt

1. Grundsätze · 2. Crawler · 3. Datenhaltung · 4. Impressum-Auswertung
5. Register und Geschäftsführung · 6. E-Mail · 7. Recht im Detail


> **Einordnung:** Recherche vom 08.10.2026 für spätere Ausbaustufen. **Nicht Teil des aktuellen Pfads.** Der Pfad ist ein Nachbau des Clay-Workbooks ECOM 2.0 (`../ABLAUF.md`). Er erkennt das Shopsystem nicht und braucht eine fertige Shop-Liste.

---

## 1. Grundsätze

- **Python-Standardbibliothek wie im Rest des Pakets.** Zusätzliche Pakete nur, wenn eine Messung sie rechtfertigt, und dann hinter einer schmalen Schnittstelle. Beispiel: `fetch(url) -> Response`, dahinter wahlweise `urllib` oder `aiohttp`.
- **Wiederverwenden statt neu bauen:**
  - Skael-Client mit Rate-Limit und Retry aus `../../google-maps/scraper/clients.py`
  - Anrede-Regeln aus `../../amazon/scripts/anrede.py`
  - Sperrlisten-Abgleich aus `../../../werkzeuge/sperrliste_abgleich.py`
- **Konventionen aus Google Maps übernehmen:**
  - Fehler zählen `attempts` hoch und markieren das Feld nie als erledigt.
  - Jede Stufe verarbeitet nur Zeilen mit leerem Zielfeld.
  - Prompts liegen als Datei, nicht im Code.
- **Bot-Schutz wird nie umgangen.** Keine wechselnden Proxys, kein Fälschen von Browser-Fingerabdrücken.

## 2. Crawler

### Durchsatz

- Pro Domain fallen 3–5 Abrufe an (`robots.txt`, Startseite, Impressum, eventuell ein API-Abruf oder die Kontaktseite).
- Bei 100.000 Domains sind das 300.000–500.000 Abrufe. Mit `ThreadPoolExecutor` (100–200 Threads, eine Verbindung je Host) dauert das Stunden, nicht Tage [E].
- Der Engpass sind tote Domains und Zeitüberschreitungen, nicht die CPU.
- **httpx nicht nehmen:** Der Verbindungspool skaliert bei sehr vielen wartenden Anfragen quadratisch. Wenn ein Wechsel nötig wird, dann zu aiohttp [S, NVIDIA NeMo Gym].

### HTML auswerten

- `html.parser` der Standardbibliothek reicht für Links, Text und `<meta>`.
- Danach `html.unescape` anwenden und Regex **auf dem extrahierten Text** laufen lassen, nicht auf rohem HTML.
- Bei 3–5 Seiten je Domain ist der Parser kein Engpass [E].

### Höflich abrufen

- **Bot-Name** mit Kontaktseite, z. B. `<Betreiber>Bot/1.0 (+https://<betreiber>/bot)`. Die Seite nennt Zweck, Kontakt und den Weg zum Ausschluss.
- **Pro Host:** eine Verbindung, ≥ 1–2 s Abstand bzw. `Crawl-delay`, `Retry-After` beachten.
- **Fehlerbehandlung:**
  - höchstens 2–3 Wiederholungen mit wachsender Wartezeit
  - Zeitlimit 5–10 s für den Verbindungsaufbau, 15–20 s zum Lesen
  - Antworten auf 3–5 MB begrenzen, höchstens 5 Weiterleitungen
- **Adressen ausprobieren:** `https://domain`, dann `https://www.domain`, `http://` nur als Rückfall. Die endgültige URL speichern.
- **Abbruch:** Bei 403, 429, 430 und 503 mit Challenge-Seite (z. B. Header `cf-mitigated`) wird `status=blocked` gesetzt. Danach höchstens ein verzögerter zweiter Versuch, sonst manuell prüfen oder auf eine Datenquelle ausweichen.

### `robots.txt` – Python-Falle [V]

- `urllib.robotparser` versteht die Platzhalter `*` und `$` erst seit dem Fix zu cpython gh-138907 (gemergt 04.05.2026), und nur in den Branches 3.13, 3.14 und main.
- Unter 3.10–3.12 wird `Disallow: /*.json` wörtlich gelesen. `/products.json` gilt dann fälschlich als erlaubt.
- **Lösung:** ein eigener Prüfer nach RFC 9309 (~40 Zeilen) oder eine Mindestversion vorschreiben. Das Paket nennt sonst Python ≥ 3.10.

### Domains zusammenführen

- Schlüssel ist die **registrierbare Domain** nach der Public Suffix List.
- Ohne Zusatzpaket: `public_suffix_list.dat` mit Stand-Datum ins Paket legen, das Prüfskript warnt nach 180 Tagen.
- Plattform-Subdomains (`*.myshopify.com`, `*.shopware.store`) gesondert behandeln. ⚠ Prüfen, ob sie in der PSL stehen.
- Mehrere Länder-Domains derselben Firma fallen später über Firmenname und HR-Nummer aus dem Impressum zusammen.

### JavaScript-Seiten

- Fehlen der Impressum-Link oder sein Text im HTML (Headless-Shops), wird `needs_js` gesetzt.
- Diese Shops kommen in eine eigene Warteschlange mit 2–4 Browser-Kontexten (Playwright) oder laufen über Skael `imprint_extractor`, der bei Bedarf selbst rendert.
- Ein Browser kostet 200–500 MB und 2–8 s je Seite, statt 0,1–0,5 s per HTTP [S]. Deshalb nur für den Rest einsetzen.

## 3. Datenhaltung (SQLite) [E]

```
ecom_domains(
  reg_domain PK, quelle, stage, status, attempts, next_attempt_at, last_error,
  http_status, final_url, shop_system, shop_version, fp_version, signale_json,
  produktanzahl, fetched_at, content_hash
)
ecom_html(reg_domain, seite, abgerufen_am, html_gzip)   -- Startseite, Impressum
ecom_impressum(reg_domain PK, firmenname, rechtsform, gf_json, hr_gericht, hr_nummer,
               ust_id, adresse, plz, land, email, telefon, quelle, extraktor_version)
```

- WAL-Modus, ein einziger Schreib-Thread mit Warteschlange.
- Stufenwechsel per `INSERT … ON CONFLICT DO UPDATE`.
- **Gespeichertes HTML** ist der wichtigste Hebel: Erkennung (`fp_version`) und Impressum-Auswertung (`extraktor_version`) lassen sich nach jeder Verbesserung neu fahren, ohne erneut abzurufen.

## 4. Impressum-Auswertung (§ 5 DDG)

**Pflichtinhalt seit 14.05.2024 (§ 5 DDG statt § 5 TMG):**

- Name bzw. Firma und ladungsfähige Anschrift
- E-Mail
- bei juristischen Personen die Vertretungsberechtigten
- Register und Registernummer
- USt-IdNr.

Bußgeld bis 50.000 € [S, IHK Köln].

**Ablauf:**

1. **Link finden:** siehe `fingerprints.md`, Abschnitt 7.
2. **Text säubern:**
   - zeilenweise extrahieren
   - E-Mail-Verschleierungen auflösen: `[at]`, `(at)`, `&#64;` und Cloudflare-`data-cfemail` (Hex, XOR mit dem ersten Byte)
3. **Felder per Regex:**
   - Vertretung: `Geschäftsführer(in)?|Vertreten durch|Inhaber(in)?|Vorstand`
   - Register: `(HR[AB])\s*[:.]?\s*(\d{1,6}\s?[A-Z]{0,2})` mit `Amtsgericht|Registergericht\s+(\S+)`
   - USt-IdNr. DE: `DE\d{9}` (Prüfziffer nach ISO 7064 MOD 11,10); AT: `ATU\d{8}` und `FN\s?\d{1,6}\s?[a-z]`; CH: `CHE-\d{3}\.\d{3}\.\d{3}`
   - Rechtsform über eine Endungsliste: GmbH, UG (haftungsbeschränkt), GmbH & Co. KG, AG, e.K., OHG, KG, e.U., OG …
4. **Plausibilität prüfen:**
   - e.K. bzw. Einzelunternehmen haben keine Geschäftsführung
   - Die PLZ passt zum Land.
5. **KI nur als Rückfall,** wenn Pflichtfelder fehlen oder die Prüfung scheitert:
   - Eingabe ist der bereinigte Impressumstext, nicht das HTML.
   - Ausgabe als JSON-Schema mit `null` statt Raten.
   - **Jedes Feld muss wörtlich im Text vorkommen**, sonst wird es verworfen. Das ist der Schutz gegen erfundene Namen.
6. **Zweiter Rückfall:** Skael `imprint_extractor` (5–10 Credits, nur bei Treffer).

**KI-Kosten je 1.000 Impressen** (Annahme 2.500 Token rein, 300 raus; Stand 10/2026 [V Preise]):

| Modell | Standard | Batch |
|---|---|---|
| Claude Haiku 5.5 | ≈ 0,40 $ | ≈ 0,20 $ |
| GPT-5 nano | ≈ 0,25 $ | ≈ 0,12 $ |
| GPT-5 mini | ≈ 1,23 $ | ≈ 0,61 $ |
| Gemini 2.5 Flash-Lite (auch über Skael `ai_generate` als `skael/fast`) | ≈ 0,37 $ | – |

Die Kosten sind vernachlässigbar, weil die KI nur bei den 20–40 % läuft, die die Regex-Stufe nicht löst [E]. Wichtiger ist die Kontrolle gegen erfundene Angaben.

**Open Source zum Vergleich:** `oiat/impressum-extractor` (MIT, März 2026): Crawler plus Gemini-Auswertung aus dem österreichischen Projekt „Watchlist Internet“ [V Lizenz, S Inhalt].

## 5. Register und Geschäftsführung

**Das Impressum ist die Primärquelle.** Registerdaten dienen nur zur Gegenprüfung, und zwar erst **nach** der Prüfung gegen das Profil (z. B. für die besten 20–30 % der Treffer).

| Quelle | Zugang | Einordnung [E] |
|---|---|---|
| handelsregister.de | kostenlos; laut Nutzungsordnung höchstens **60 Abrufe/Stunde**, bei Massenabfragen wird auf §§ 303a/b StGB verwiesen; § 52 HRV: keine gezielte Suche nach Personen [S] | **nur manuelle Stichproben**, nie als Pipeline-Stufe |
| OpenRegister | Free 500 Credits/Monat; Firmendetails 10 Credits (Echtzeit 20); Zukauf 0,01 € je Credit [V] | erste Wahl für DE, ~0,10–0,20 € je Firma |
| Implisense | Plus 59 €/Monat; volles Profil ≤ 7 Implicents [S] | Alternative |
| North Data | Data API nur auf Anfrage [S] | erst bei großem Volumen |
| AT Firmenbuch | kostenlose HVD-Webservices, Vertrag mit einer Verrechnungsstelle nötig [S] | machbar, Aufwand vorab klären |
| CH Zefix | kostenlose REST-API, Zugangsdaten per E-Mail an zefix@bj.admin.ch [S] | für CH die beste Quelle |

Ohne Registerzugang bleibt die Recherche per Agent wie im Amazon-Pfad, Phase 4 (`../../amazon/referenzen/agent-prompt.md`).

## 6. E-Mail

1. **Impressum-E-Mail** übernehmen (Pflichtangabe, meist info@/service@) und mit Skael `verify_email` (3 Credits) prüfen. Catch-all-Domains (Status `Risky`) getrennt ausweisen; bei Shops kommen sie oft vor.
2. **Persönliche Adresse der Geschäftsführung** (Skael `find_email_person`, 15 Credits je Treffer) nur ermitteln, wenn der geplante Kanal sie erlaubt. Sonst bringt sie keinen Nutzen, aber zusätzliches DSGVO-Risiko.
3. **MX-Prüfung:** Die Standardbibliothek kann keine MX-Records abfragen. Das übernimmt Skael, oder `dnspython` kommt als optionales Paket dazu.

## 7. Recht im Detail (keine Rechtsberatung)

- **UWG § 7:** E-Mail-Werbung braucht eine vorherige ausdrückliche Einwilligung, auch B2B [V]. Telefon B2B: mutmaßliche Einwilligung, ein allgemeiner Sachbezug reicht nicht [S]. Österreich (§ 174 TKG 2021): Eine Adresse im Impressum ist **keine** Einwilligung [S, WKO].
- **DSGVO:**
  - Namen der Geschäftsführung und Adressen von Einzelunternehmern sind personenbezogen.
  - CNIL gegen Kaspr (12/2024, 240.000 €): Dass Daten online stehen, rechtfertigt ihre Wiederverwendung nicht. Die Info nach Art. 14 gilt auch hier [S].
  - BGH VI ZR 10/24 (18.11.2024): Schon der Kontrollverlust ist ein Schaden (~100 € je Person). **Die Lead-Datenbank muss gesichert sein** [S].
  - Der Entwurf EDSA-Leitlinien 03/2026 zu Web-Scraping wertet `robots.txt` als relevant für die Interessenabwägung [S].
- **Text- und Data-Mining (§ 44b UrhG):** Ein Vorbehalt muss maschinenlesbar sein (`robots.txt`, TDMRep-Header `tdm-reservation`, `/.well-known/tdmrep.json`). TDMRep ist kein W3C-Standard, sollte aber trotzdem beachtet werden [S]. Impressum-Fakten sind meist keine geschützten Werke, Produkttexte und -fotos oft schon [E].
- **Datenbankschutz (§ 87b UrhG, EuGH C-762/19):** Die Produktanzahl zu zählen ist unkritisch. Den Katalog zu übernehmen ist riskant [E].
- **AGB:**
  - Shopifys Scraping-Verbot (Ziffer 1.9) bindet Händler, nicht Besucher der Shops [V].
  - Eigene AGB der Händler können gelten [E].
  - Vertragliche Verbote bleiben auch bei nicht geschützten Datenbanken möglich (EuGH C-30/14 Ryanair) [S].

Risikotabelle in Kurzform: `../../../wissen/06_pfad-e-commerce.md`, Abschnitt „Rechtliches“.
