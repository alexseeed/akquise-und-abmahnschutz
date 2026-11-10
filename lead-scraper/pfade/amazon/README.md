# Pfad „Amazon-Seller“ (amazon.de)

Dieser Pfad findet Drittanbieter auf amazon.de **selbst**, eine Brand-Liste ist nicht nötig. Daraus baut er eine Lead-Liste: Firma, Adresse, Land, Sortiment, geschätzter Umsatz und auf Wunsch Kontaktdaten, Website, Geschäftsführung und Anrede. Er ist **auf keine Zielgruppe zugeschnitten**. Alle Filter sind ab Werk **aus**. Die KI setzt sie nach dem Zielgruppen-Interview, z. B. nur Verkäufer aus DACH oder nur kleine Sortimente.

Normalerweise startest du nichts selbst: Du sagst der KI (Claude Code oder Codex) im Paketordner *„Ich will neue Kunden finden“*. Sie führt dich durch das Interview und diesen Pfad. Die Schritt-für-Schritt-Anleitung für die KI steht in `ABLAUF.md`, Hintergrund und Grenzen in `../../wissen/04_pfad-amazon.md`.

| Datei | Zweck |
|---|---|
| `ABLAUF.md` | Anleitung für die KI: Phasen, Befehle, Prüfpunkte |
| `amazon_seller_scraper.mjs` | der Scraper (Hauptprogramm) |
| `kategorien.json` | die 28 geprüften amazon.de-Hauptkategorien (einzeln abschaltbar mit `"aktiv": false`) |
| `ernter_unterkategorien.mjs` | optional: findet Unterkategorien und vergrößert damit die Suchfläche |
| `anreicherung.mjs` | prüft die Zustellbarkeit jeder E-Mail-Adresse und ergänzt Website, Impressum, Geschäftsführung und persönliche Anrede (Skael). Geht auch mit einer eigenen Firmenliste |
| `standardformat.mjs` | stellt die Pflichtfelder aller Pfade nach vorn (Firmenname, Website, E-Mail, E-Mail Status, Anrede, Vorname, Nachname, Ansprache, Quelle, Pfad) |
| `wiederholen.mjs` | gemeinsame Fehlerbehandlung aller Skripte: vorübergehende API-Fehler mit wachsender Pause wiederholen (`MAX_RETRIES`), dauerhafte sofort melden. Muss neben den Skripten liegen |
| `tests/` | Offline-Tests dazu: `node --test pfade/amazon/tests/` (kein Netz, keine Kosten) |
| `.env.example` | Vorlage für die Zugangsdaten |
| `arbeit/` | Arbeitsordner aller Läufe: Ergebnisse, Gedächtnis, Fortschritt. Wird nie weitergegeben |
| `README.md` | diese Anleitung |

---

## 1. Was passiert bei einem Lauf?

1. **Suchen (Discovery):** Der Scraper liest die Listen „Neuheiten“ jeder Kategorie, höchstens 75 Seiten je Kategorie. Liefert eine Liste auf Seite 1 nichts, wird sie in diesem Lauf übersprungen und beim nächsten Start einmal nachgeprüft. Ist sie wieder leer, gilt sie als **tote Liste**, wird nicht mehr abgerufen und steht im Bericht.
2. **Produktseiten:** Für jedes neue Produkt wird geprüft, welcher Händler die Buy-Box hat. Amazon selbst ist nie ein Lead.
3. **Verkäuferprofil:** Firmenname, Adresse und Land des Händlers.
4. **Sortiment:** Wie viele Produkte hat der Händler? Eine Stichprobe von 12 Produktseiten liefert Produktfamilien, Hauptmarke, Markenanteil und den Umsatz. Der Umsatz ist gemessen, wenn Amazon „X+ gekauft“ anzeigt, sonst geschätzt.
5. **Endkontrolle:** Hat der Händler die Buy-Box seines Hauptprodukts noch?
6. **Kontaktdaten (optional, Bright Data):** E-Mail, Telefon, Handelsregister, USt-IdNr., Rechtsform, vertretungsberechtigte Person.
7. **Export:** Die neuen Leads werden an die Gesamtliste angehängt. Dazu kommen eine Datei nur mit den Leads dieses Laufs und ein Bericht.

Die Stufen 1–4 laufen in **Wellen** von je 100 Treffern: Jede Stufe holt nur so viel, wie die nächste für das Lead-Ziel (`ZIEL`) noch braucht. Die Durchlaufquoten misst der Scraper dabei laufend selbst. So bezahlt ein Lauf nie zehntausende Produktseiten, bevor der erste Lead da ist. Wird das Budget knapp, sind die Treffer der bisherigen Wellen sicher und werden geliefert.

Der Scraper hat ein **Gedächtnis**. Bereits geprüfte Produkte und Verkäufer werden nicht noch einmal bezahlt. Ein Verkäufer wird pro Kampagne nur einmal geliefert.

## 2. Was du brauchst

- **Node.js ab Version 18** ([nodejs.org](https://nodejs.org), „LTS“ installieren). Weitere Programme oder Pakete sind nicht nötig.
- **Oxylabs-Konto** (Web Scraper API) mit Benutzername und Passwort. Pflicht.
- **Bright-Data-Token**: für Kontaktdaten. E-Mail-Adresse und Telefon kommen nur von dort. Ohne Token gibt es Leads mit Firma, Adresse und Sortiment, aber ohne E-Mail und Telefon. Lehnt Bright Data den Token ab oder ist das Guthaben leer, bleiben die gefundenen Leads offen, bis der Zugang wieder geht.
- **Skael-API-Schlüssel**: für `anreicherung.mjs`. **Pflicht, wenn per E-Mail angeschrieben wird**, denn nur damit wird die Zustellbarkeit der Adressen geprüft. Dazu kommen Website und Geschäftsführung.

**Zugangsdaten** kommen in die Datei `pfade/amazon/.env`. Die Vorlage ist `.env.example`: kopieren, als `.env` speichern und die Werte selbst eintragen. Alle Skripte lesen sie automatisch. Die `.env` wird nie weitergegeben. Schlüssel gehören nie in einen Chat, auch nicht in den mit der KI, und nicht in Screenshots.

```bash
cp .env.example .env      # danach .env in einem Texteditor öffnen und ausfüllen
```

Alternativ gehen auch Umgebungsvariablen im Terminal. Sie haben Vorrang vor der `.env`.

## 3. Kosten (Faustregeln)

| Dienst | Preis (Richtwert, beim Anbieter prüfen) | Wofür |
|---|---|---|
| Oxylabs | ca. **0,40–0,50 USD je 1.000 Abfragen** | alle Amazon-Seiten (Stufen 1–5) |
| Bright Data | ca. **1,50 USD je 1.000 Datensätze** | Kontaktdaten, nur für fertige Leads |
| Skael | **3 Credits je E-Mail-Prüfung**, dazu ca. **5–50 Credits je DACH-Lead** (ohne Firmen-E-Mail eher oben, Einzelfälle darüber) | E-Mail-Prüfung, Website, Geschäftsführung |

**Budget richtig wählen:**

> **Ohne Filter: BUDGET ≈ 30 × ZIEL** (mit `SORTIMENT=0` etwa 5 × ZIEL)
>
> **Mit Filtern** deutlich mehr, weil viele Verkäufer geprüft und verworfen werden. Beispiel: Bei `LAENDER=DE,AT,CH` sitzen nur etwa 15 % der Verkäufer im Zielland, das ergibt eher 150–250 Abfragen je Lead.

Am genauesten ist dein eigener Wert. Nach jedem Lauf steht im Bericht `requests_je_lead`. Für den nächsten Lauf gilt dann **BUDGET ≈ ZIEL × requests_je_lead × 1,2**.

`BUDGET` ist eine **harte Obergrenze** für Oxylabs-Abfragen, kein Verbrauchsziel. Sie gilt für den ganzen Lauf einer Kampagne, auch über Neustarts hinweg. Ist sie erreicht, stoppt der Scraper sauber: Die bis dahin gefundenen Treffer werden noch geprüft und exportiert. Etwa 5 % des Budgets hält er dafür zurück. Ist das Budget für das Ziel zu knapp, sagt der Scraper das beim Start und liefert, was das Budget hergibt.

## 4. Schnellstart

Die KI erledigt diese Schritte selbst (`ABLAUF.md`). Von Hand geht es genauso. Alle Befehle laufen im Arbeitsordner `pfade/amazon/arbeit/`, die Skripte liegen eine Ebene höher. Dort landen alle Ergebnisse, Gedächtnis- und Fortschrittsdateien, also auch Namen, E-Mail-Adressen und Telefonnummern. **Den Ordner `arbeit/` nie weitergeben.**

```bash
mkdir -p pfade/amazon/arbeit && cd pfade/amazon/arbeit
node ../amazon_seller_scraper.mjs --pruefen      # Node-Version, Zugänge, 1 Testabfrage
```

**Schritt 1: Smoke-Test (höchstens 300 Abfragen, ca. 0,15 USD).** Prüft, ob Zugang und Technik funktionieren.

```bash
SMOKE=1 node ../amazon_seller_scraper.mjs
```

Der Smoke-Test nutzt eigene Dateien (`smoke_…`, Kampagne `smoke`) und berührt das echte Gedächtnis nicht. Ergebnis: `leads_smoke_MASTER.csv` mit bis zu 5 Leads. Der Smoke-Test ist fest eingestellt: `ZIEL`, `BUDGET` und Filter gelten dort nicht. Vor einer Wiederholung seine Dateien löschen (`rm -f *smoke*`), sonst ruft er nichts mehr ab.

**Schritt 2: Testlauf (50 Leads, höchstens 3.000 Abfragen, ca. 1,40 USD).**

```bash
KAMPAGNE=meine-liste-test ZIEL=50 BUDGET=3000 node ../amazon_seller_scraper.mjs
```

Danach im Bericht `report_meine-liste-test.json` den Wert `requests_je_lead` ansehen.

**Schritt 3: Großlauf.** Budget nach der Regel aus Abschnitt 3, z. B. 1.000 Leads ohne Filter:

```bash
KAMPAGNE=meine-liste ZIEL=1000 BUDGET=36000 node ../amazon_seller_scraper.mjs
```

`ZIEL` zählt für die ganze Kampagne, auch über Neustarts hinweg: Nach 300 gelieferten Leads holt `ZIEL=1000` noch 700 weitere. `ZIEL=0` heißt: kein Lead-Ziel, der Lauf geht in Wellen weiter, bis das Budget verbraucht ist oder alle Listen durch sind.

Mit Filtern, z. B. nur Händler aus Deutschland, Österreich und der Schweiz mit höchstens 100 Produkten (Budget deutlich höher ansetzen, siehe Abschnitt 3):

```bash
KAMPAGNE=meine-liste LAENDER=DE,AT,CH MAX_PRODUKTE=100 ZIEL=200 BUDGET=50000 node ../amazon_seller_scraper.mjs
```

**Schritt 4 (optional): Unterkategorien ernten.** Erst sinnvoll, wenn der Scraper meldet, dass alle Listen ausgeschöpft sind. Danach mit derselben `KAMPAGNE`:

```bash
KAMPAGNE=meine-liste node ../ernter_unterkategorien.mjs
```

Das schreibt `subkategorien.json`. Produkte, deren Kategoriepfad der Scraper schon gespeichert hat, kosten nichts, für den Rest höchstens `STICHPROBE` Abfragen. Danach den Scraper mit `SUB_SEITEN=5` starten. Die Unterkategorien vergrößern nur die Auswahl: Abgerufen wird weiterhin nur, was für `ZIEL` nötig ist, bereits bezahlte Seiten werden nicht wiederholt.

**Schritt 5: Anreicherung und E-Mail-Prüfung.** Ist beim Scraper-Lauf `SKAEL_API_KEY` gesetzt, startet sie am Ende jedes Scraper-Starts automatisch für die Gesamtliste der Kampagne. Bezahlt werden nur offene Leads, Erledigtes kostet nichts. Abschalten mit `ANREICHERUNG=0`. Manuell (z. B. nach einem Abbruch oder wenn der Schlüssel erst später eingetragen wurde):

```bash
KAMPAGNE=meine-liste node ../anreicherung.mjs                                           # Gesamtliste der Kampagne
KAMPAGNE=meine-liste CSV=leads_meine-liste_2026-10-08_14-30-00.csv node ../anreicherung.mjs  # nur eine Lauf-Datei
```

Der Fortschritt wird je Kampagne und Seller-ID gespeichert (`anreicherung_<KAMPAGNE>_state.json`). Wer erst die Lauf-Datei und später die Gesamtliste anreichert, bezahlt keinen Lead doppelt. Website, Impressum und Geschäftsführung werden standardmäßig nur für Leads aus DE, AT und CH gesucht, denn nur dort gibt es eine Impressumspflicht. Für alle anderen würde die Suche Credits ohne Ergebnis kosten. Ändern mit `ANREICHERUNG_LAENDER`. Die E-Mail-Prüfung läuft unabhängig davon für alle Länder und immer zuerst.

**E-Mail-Prüfung:** Jede Adresse wird auf Zustellbarkeit geprüft, in allen Ländern. Die Spalte `E-Mail Status` zeigt das Ergebnis: `Safe to Send` (zustellbar), `Risky` (der Server nimmt jede Adresse an), `Unknown` (nicht prüfbar), `Invalid` (ungültig, nie anschreiben) oder `Not Run` (nicht geprüft, nie per E-Mail anschreiben). Eine Adresse wird höchstens in 3 Starts geprüft; danach hilft `ERNEUT_VERSUCHEN=1`, wenn die Ursache behoben ist. Zuerst nur an `Safe to Send` senden. `Risky` und `Unknown` getrennt und vorsichtig behandeln, sonst leidet die Absender-Reputation. Abschalten mit `EMAIL_PRUEFUNG=0`.

Ergebnis: `<Dateiname>_angereichert.csv`. Alle Originalspalten bleiben unverändert. Neu dazu kommen E-Mail Status, Website, Website-Quelle, Impressum-URL, Impressum-Firmenname, Geschäftsführung, Anrede (persönlich), Anrede, Vorname, Nachname, Ansprache, Match-Status, Storefront-URL (nur falls noch nicht vorhanden) und Anreicherung-Fehler. Hat die Eingabe eine dieser Spalten schon (z. B. `Website` in einer eigenen Liste), bleibt sie unverändert und der neue Wert steht in `<Spalte> (Anreicherung)`. Persönlich wird es nur, wenn Name und Geschlecht eindeutig sind („Sehr geehrter Herr …“ bzw. „Guten Tag Herr …“), sonst neutral („Sehr geehrte Damen und Herren“ bzw. „Guten Tag“). Die Anreicherung liest auch CSV-Dateien mit Komma und eigene Firmenlisten: Pflicht ist nur eine Spalte `Firma` oder `Firmenname`, hilfreich sind `Adresse`/`Ort`, `Land`, `Handelsregister` und `E-Mail`. Immer die Master- bzw. Original-CSV angeben: Eine schon angereicherte Datei oder eine im Standardformat lehnt das Skript ab.

Endet die Anreicherung mit „UNVOLLSTÄNDIG“ oder „Skael liefert seit 10 Abfragen in Folge kein Ergebnis“ (Code 5), ist Skael oder das Internet gestört. Der Stand ist gespeichert und nichts fälschlich als erledigt markiert. Denselben Befehl innerhalb von 24 Stunden erneut starten, dann werden schon abgeschickte Abfragen nicht noch einmal berechnet. Weitere Codes: 2 = Schlüssel abgelehnt, 3 = Credits aufgebraucht, 4 = `SKAEL_MAX_CREDITS` erreicht.

**Schritt 6: Standardformat und Sperrliste (immer vor dem Versand).**

```bash
node ../standardformat.mjs leads_meine-liste_MASTER_angereichert.csv     # ohne Anreicherung: leads_meine-liste_MASTER.csv
python3 ../../../werkzeuge/sperrliste_abgleich.py leads_meine-liste_MASTER_angereichert_standard.csv --spalten "E-Mail,E-Mail ungültig,Website,Impressum-URL"
# ohne Anreicherung (keine Spalte Impressum-URL):
python3 ../../../werkzeuge/sperrliste_abgleich.py leads_meine-liste_MASTER_standard.csv --spalten "E-Mail,E-Mail ungültig,Website"
```

Für den Versand nur die Datei `…_bereinigt.csv` verwenden. Firmen in `…_gesperrt.csv` nie anschreiben. Adressen mit `Invalid` stehen im Standardformat nicht mehr im Feld E-Mail, sondern in der letzten Spalte `E-Mail ungültig`.

**Match-Status**, also wie sicher die Website zur Firma gehört:

| Wert | Bedeutung |
|---|---|
| `register`, `ustid`, `firmenname`, `telefon`, `email` | Das Impressum der Website bestätigt die Firma, und zwar über das genannte Merkmal. Website und Geschäftsführung sind verlässlich |
| `domain` | Die Domain passt zum Firmen- oder Markennamen. Das Impressum wurde gelesen, nennt die Firma aber nicht über Register, USt-IdNr., Namen, Telefon oder E-Mail. Geschäftsführung und Anrede vor Verwendung kurz prüfen |
| `email-domain` | Die Website ist die Domain der Firmen-E-Mail, ist aber nicht bestätigt. Steht in „Anreicherung-Fehler“ ein abweichendes Impressum, vor Verwendung kurz prüfen |
| `MISMATCH` | Es wurden nur Websites anderer Firmen gefunden. Die Website bleibt leer, die Geschäftsführung kommt höchstens aus dem Amazon-Verkäuferprofil |
| leer | keine Website gefunden |

## 5. Ergebnis

- `leads_<KAMPAGNE>_MASTER.csv`: alle bisher gelieferten Leads der Kampagne. Neue Leads werden **angehängt**, nichts wird überschrieben. Ändern sich die Spalten, wird die alte Datei vorher als `…_alteSpalten_<Zeit>.csv` gesichert.
- `leads_<KAMPAGNE>_<Datum_Zeit>.csv`: nur die neuen Leads dieses Laufs (für den Import in CRM, Clay usw.).
- `report_<KAMPAGNE>.json`: Bericht mit Einstellungen, Funnel, Ausschlussgründen, Treffern und Leads je Kategorie, toten Listen, Länderverteilung, Verbrauch, Kosten und Abfragen je Lead.

CSV-Spalten: Firma · Marke · Seller-ID · Storefront-URL · Verkäuferprofil-URL · Haupt-ASIN · Produkt-URL · Kategorie · Quelle · Land · Adresse · Produktpreis · Produktbilder · Bulletpoints · Beschreibungslänge · Produkte · Produkte gekappt · Produktfamilien · Portfolio-Bewertungen · Markenanteil % · Umsatz/Monat ca. EUR · Umsatzbasis · Bestseller-Rang · Umsatz Rang-Modell EUR · E-Mail · Telefon · Handelsregister · USt-IdNr · Rechtsform · Vertretungsberechtigt · Datenstand

Erklärungen zu einzelnen Spalten:

- **Produkte gekappt = ja**: Das Sortiment ist größer als `MAX_KACHELN`. Gezählt wurden nur so viele Produkte. Produktfamilien, Bewertungen und Umsatz sind dann aus der Stichprobe hochgerechnet und eher zu niedrig.
- **Markenanteil %**: Anteil der 12 Stichproben-Produktfamilien, die die Hauptmarke tragen. Platzhalter wie „Generic“ zählen als „keine Marke“.
- **Umsatzbasis**: Es gibt vier Fälle.
  - `gemessen`: echte Amazon-Kaufzahlen („X+ gekauft“) × Preis.
  - `gemessen + geschätzt`: Produkte unter Amazons Anzeigeschwelle wurden mit `SCHAETZ_KAEUFER` Käufern im Monat angesetzt.
  - `geschätzt`: Es gibt keine einzige Kaufzahl.
  - `nicht messbar`: Es gibt weder Kaufzahlen noch Preise, der Umsatz bleibt leer. Mit `SORTIMENT=0` fehlt er immer.
- **Umsatz Rang-Modell**: eine zweite Schätzung aus dem Bestseller-Rang. Die Kurve kalibriert sich selbst aus den gesammelten Daten und bleibt leer, solange zu wenige brauchbare Messpunkte vorliegen. Sie filtert nie.

**Excel:** Die Datei per Doppelklick zu öffnen funktioniert. Sicherer für Telefonnummern ist aber „Daten → Aus Text/CSV“ mit Trennzeichen Semikolon und den Spalten Telefon und Handelsregister als *Text*. Sonst kann Excel führende Nullen oder das „+“ entfernen.

## 6. Alle Einstellungen

Einstellungen werden vor den Befehl geschrieben (`NAME=Wert NAME2=Wert node …`). Zahlen schreibst du **ohne Tausenderpunkt** (`BUDGET=32000`, nicht `32.000`). Ungültige Werte führen sofort zu einer Fehlermeldung, bevor etwas bezahlt wird.

### Zugang

| Variable | Standard | Bedeutung |
|---|---|---|
| `OXYLABS_USER` / `OXYLABS_PASS` | – (Pflicht) | Oxylabs-Zugang. Alternativ `OXYLABS_USERNAME` / `OXYLABS_PASSWORD` |
| `BRIGHTDATA_TOKEN` | leer | Bright-Data-Token für Kontaktdaten. Alternativ `BRIGHTDATA_API_KEY` |
| `OXYLABS_URL` | `https://realtime.oxylabs.io/v1/queries` | nur für Tests (z. B. mit einem lokalen Test-Server) |
| `BRIGHTDATA_URL` | `https://api.brightdata.com` | nur für Tests |

### Lauf

| Variable | Standard | Bedeutung |
|---|---|---|
| `SMOKE` | aus | `SMOKE=1` = Mini-Test mit eigenen Dateien: Kampagne `smoke`, 2 Kategorien, 2 Seiten, Ziel 5, Budget 300 |
| `KAMPAGNE` | `standard` | Name des Laufs. Trennt Lieferliste, Fortschritt und Ergebnisdateien (Buchstaben, Ziffern, `-`, `_`, `.`) |
| `BUDGET` | `5000` | harte Obergrenze an Oxylabs-Abfragen für diese Kampagne (inkl. Neustarts) |
| `ZIEL` | `100` | so viele Treffer soll die Kampagne insgesamt finden (zählt wie `BUDGET` über Neustarts hinweg). Gezählt wird vor der Endkontrolle, geliefert werden also bis zu so viele Leads. Fehlen welche: `ZIEL` um die Differenz erhöhen und erneut starten. `0` = kein Ziel, Wellen bis Budget- oder Listenende |
| `RATE` | `40` | höchstens so viele Abfragen pro Sekunde |
| `CONC` | `40` | parallele Abfragen (Stufen 1, 2, 3, 5) |
| `CONC_PF` | `12` | parallel geprüfte Sortimente (Stufe 4) |
| `ENDKONTROLLE` | `1` | `0` = Endkontrolle überspringen (spart 1–2 Abfragen je Lead) |
| `SORTIMENT` | `1` | `0` = Sortimentsprüfung überspringen (viel billiger). Leads haben dann nur Profil- und Kontaktdaten |
| `CACHE_TAGE` | `90` | so lange gelten gespeicherte Fakten zu Produkten und Verkäufern. `0` = Gedächtnis nicht nutzen |
| `BD_TIMEOUT_MIN` | `30` | so lange wird auf einen Bright-Data-Block gewartet. Danach wird er beim nächsten Start abgeholt |
| `MAX_RETRIES` | `5` | so oft wird eine Abfrage bei vorübergehenden Fehlern versucht (Netz, Zeitüberschreitung, HTTP 408/425/429/5xx), mit wachsender Pause (2, 4, 8, 16 s, bei 429 5, 10, 20, 40 s, höchstens 60 s). Gilt für Oxylabs, Bright Data, den Ernter und die Anreicherung (Skael). Dauerhafte Fehler (400, 401, 402, 403, 404) werden nicht wiederholt |
| `OX_USD_JE_1000` | `0.45` | dein Oxylabs-Preis je 1.000 Abfragen (nur für die Kostenanzeige) |
| `BD_USD_JE_1000` | `1.5` | dein Bright-Data-Preis je 1.000 Datensätze (nur für die Kostenanzeige) |

### Suche (Discovery)

| Variable | Standard | Bedeutung |
|---|---|---|
| `NEU_SEITEN` | `75` | höchstens so viele Seiten der Neuheiten-Liste je Kategorie. Abgerufen wird nur, was für `ZIEL` nötig ist (`0` = Hauptkategorien aus) |
| `KATEGORIEN` | leer = alle aktiven | nur Kategorien, deren Name einen dieser Teile enthält, z. B. `KATEGORIEN=Küche,Garten,Sport`. Trifft ein Teil keine Kategorie, bricht der Start mit einer Liste der gültigen Namen ab |
| `KAT_LIMIT` | `0` = alle | nur die ersten N Kategorien aus `kategorien.json` |
| `SUB_SEITEN` | `0` = aus | Seiten je Unterkategorie aus `subkategorien.json` (siehe Ernter) |
| `KEYWORDS` | leer | zusätzliche Suchbegriffe, durch Komma getrennt, z. B. `KEYWORDS=yogamatte,thermobecher`. Alternativ eine Datei `keywords.txt` (ein Begriff je Zeile, `#` = Kommentar) |
| `KW_SEITEN` | `2` | Seiten je Suchbegriff (`0` = Keywords aus) |
| `PREIS_MIN` | `0` = aus | Amazon filtert serverseitig nach Mindestpreis in EUR, z. B. `PREIS_MIN=15`. In der Endkontrolle wird der Preis erneut geprüft |

### Filter (alle AUS: 0 oder leer = aus)

| Variable | Standard | Wirkung, wenn gesetzt |
|---|---|---|
| `LAENDER` | leer = alle Länder | nur Verkäufer mit Sitz in diesen Ländern, z. B. `LAENDER=DE,AT,CH`. Ist das Land nicht erkennbar, gilt der Grund `land_unklar` |
| `LISTING_MAX_BEWERTUNGEN` | `0` | Produkte mit mehr Bewertungen werden schon in der Suche verworfen. Produkte ohne Bewertungsangabe bleiben immer drin |
| `MAX_ANBIETER` | `0` | Produkte mit mehr Anbietern (laut Suchergebnis) werden verworfen. Fehlt die Angabe, bleibt das Produkt drin |
| `PORTFOLIO_MAX_BEWERTUNGEN` | `0` | Verkäufer mit mehr Bewertungen im ganzen Sortiment raus. Bricht früh ab, sobald die Grenze sicher überschritten ist |
| `MAX_PRODUKTE` | `0` | Verkäufer mit mehr Produkten raus. Bricht früh ab, sobald die Grenze überschritten ist |
| `MIN_MARKENANTEIL` | `0` | Anteil der Hauptmarke an den Stichproben-Produktfamilien als Zahl zwischen 0 und 1, z. B. `0.7` = mindestens 70 % (Händler, die vor allem eine eigene Marke verkaufen). Haben weniger als 3 Familien eine echte Marke, ist der Anteil nicht bestimmbar (`markenanteil_unklar`), und der Verkäufer fliegt raus |
| `UMSATZ_MAX` | `0` | Verkäufer raus, deren **gemessener** Umsatz über diesem Wert in EUR/Monat liegt. Gemessen heißt: Mindestens 2 Stichproben-Familien zeigen echte Kaufzahlen („X+ gekauft“), daraus wird auf alle Familien hochgerechnet. Geschätzte Umsätze filtern nie |
| `FIRMEN_AUSSCHLUSS` | leer | Firmennamen mit diesen Wortteilen raus, z. B. `FIRMEN_AUSSCHLUSS=verlag,publishing`. Wird vor und nach den Kontaktdaten geprüft |

Amazon selbst wird immer ausgeschlossen. Filter wirken auch auf das Gedächtnis: Ein Verkäufer, der heute an einem Filter scheitert, kann in einem späteren Lauf mit anderen Filtern wieder auftauchen. Gespeichert werden Fakten (Land, Produktzahl, Umsatz …), keine Urteile.

### Sortiment und Daten

| Variable | Standard | Bedeutung |
|---|---|---|
| `MAX_KACHELN` | `300` | höchstens so viele Produkte werden je Verkäufer gezählt. Darüber gilt „Produkte gekappt = ja“. Das ist **kein** Ausschluss |
| `MAX_SEITEN` | `20` | höchstens so viele Storefront-Seiten je Verkäufer (Kostendeckel) |
| `SCHAETZ_KAEUFER` | `25` | angenommene Käufer pro Monat je Produktfamilie, wenn Amazon keine Kaufzahl zeigt (nur Schätzung, filtert nie). `0` = nur gemessene Werte |

### Ernter (`ernter_unterkategorien.mjs`)

| Variable | Standard | Bedeutung |
|---|---|---|
| `KAMPAGNE` | `standard` | aus welchem Lauf die Produkte stammen (`state_<KAMPAGNE>.json`) |
| `STICHPROBE` | `600` | höchstens so viele Produktseiten werden neu abgerufen |
| `MAX_JE_BEREICH` | `40` | höchstens so viele Unterkategorien je Hauptkategorie |
| `MIN_TREFFER` | `2` | eine Unterkategorie muss mindestens so oft vorkommen |
| `MIN_SUBS` | `40` | unter so vielen Unterkategorien wird `subkategorien.json` nicht geschrieben |
| `RATE` / `CONC` | `30` / `25` | Tempo und Parallelität des Ernters |
| `OXYLABS_USER` / `OXYLABS_PASS` / `OXYLABS_URL` | wie oben | Zugang |

### Anreicherung (`anreicherung.mjs`)

| Variable | Standard | Bedeutung |
|---|---|---|
| `SKAEL_API_KEY` | leer | Skael-Schlüssel (alternativ `SKAEL_KEY`). Ist er beim Scraper gesetzt, startet die Anreicherung am Ende automatisch |
| `ANREICHERUNG` | an | `ANREICHERUNG=0` = kein automatischer Start nach dem Scraper |
| `CSV` | `leads_<KAMPAGNE>_MASTER.csv` | welche Datei angereichert wird |
| `KAMPAGNE` | `standard` | bestimmt die Standard-CSV |
| `SKAEL_WORKER` | `12` | parallel bearbeitete Leads |
| `EMAIL_PRUEFUNG` | `1` | `0` = E-Mail-Adressen nicht prüfen. Der Status bleibt dann `Not Run` |
| `SKAEL_AGENT` | `1` | `0` = KI-Recherche (teuerste Phase) aus |
| `ANREICHERUNG_LAENDER` | `DE,AT,CH` | Website, Impressum und Geschäftsführung nur für Leads aus diesen Ländern (Impressumspflicht). `alle` = alle Länder. Die E-Mail-Prüfung läuft unabhängig davon für alle Länder |
| `ERNEUT_VERSUCHEN` | `0` | `1` = Adressen und Leads, die nach 3 Starts ohne Ergebnis aufgegeben wurden, noch einmal versuchen |
| `SKAEL_MAX_CREDITS` | `0` = kein Deckel | Deckel für alle Starts dieser Kampagne zusammen (geschätzter Verbrauch). Stoppt sauber, ein Neustart mit höherem Deckel setzt fort |
| `SKAEL_RATE` | `5` | höchstens so viele Skael-Anfragen pro Sekunde |
| `SKAEL_MAX_WARTEZEIT` | `600` | so viele Sekunden wird auf ein einzelnes Ergebnis gewartet. Danach holt der nächste Start es ab |
| `MAX_RETRIES` | `5` | Versuche je Skael-Abfrage bei vorübergehenden Fehlern (wie beim Scraper). Ein aus vorübergehendem Grund gescheiterter Auftrag wird neu eingereicht, beim Abholen wird nie neu eingereicht |
| `SKAEL_URL` | `https://api.skael.de` | nur für Tests |

## 7. Dateien, die der Scraper anlegt

| Datei | Inhalt | Löschen? |
|---|---|---|
| `seen_asins.json` | Gedächtnis: geprüfte Produkte und deren Verkäufer (alle Kampagnen) | **nie**, spart bares Geld |
| `seller_cache.json` | Gedächtnis: Fakten je Verkäufer, z. B. Land, Produktzahl, Umsatz (alle Kampagnen) | **nie** |
| `delivered_<KAMPAGNE>.json` | bereits gelieferte Verkäufer dieser Kampagne | **nie**, sonst werden Leads doppelt geliefert |
| `leads_<KAMPAGNE>_MASTER.csv` | alle gelieferten Leads | **nie**, sie dient auch als Doppelschutz |
| `state_<KAMPAGNE>.json` | Fortschritt des aktuellen Laufs | nur für einen **frischen** Lauf |
| `report_<KAMPAGNE>.json`, `leads_<KAMPAGNE>_<Zeit>.csv` | Bericht und Lauf-Datei | nach Belieben |
| `subkategorien.json`, `keywords.txt` | optionale Suchlisten | nach Belieben |
| `smoke_…`, `*_smoke*` | Dateien der Smoke-Tests | jederzeit |
| `anreicherung_<KAMPAGNE>_state.json` | Fortschritt und Credit-Verbrauch der Anreicherung je Seller-ID | **nie**, solange die Kampagne weiter angereichert wird, sonst werden Leads doppelt bezahlt |
| `…_angereichert.csv`, `…_standard.csv`, `…_bereinigt.csv`, `…_gesperrt.csv` | Anreicherung, Standardformat, Ergebnis des Sperrlisten-Abgleichs | nach Belieben (aus dem Master jederzeit neu erzeugbar) |

Alle diese Dateien liegen in `arbeit/` und enthalten Lead-Daten. Gib sie nicht mit dem Paket weiter.

## 8. Abbruch und Fortsetzen

- **Strg+C** beendet die laufenden Abfragen, speichert den Stand und exportiert fertige Leads. Zweimal Strg+C beendet sofort.
- **Fortsetzen:** denselben Befehl noch einmal ausführen. Erledigte Seiten und Prüfungen werden nicht erneut bezahlt. Nie zwei Läufe derselben Kampagne gleichzeitig starten.
- **Andere Filter ausprobieren:** einen neuen Kampagnennamen nehmen. Unter dem alten Namen zählen Ziel und Budget weiter, und die alten Leads bleiben in der Liste.
- **Budget erreicht:** Mit höherem `BUDGET` fortsetzen. Das Budget gilt für den ganzen Lauf: War es 5000 und wurde voll verbraucht, bringt `BUDGET=10000` weitere ca. 5000 Abfragen.
- **Mehr Leads:** `ZIEL` erhöhen (und bei Bedarf `BUDGET`). Ist das Ziel schon erreicht, holt ein Neustart mit demselben `ZIEL` nichts Neues.
- **Mehr Seiten nachlegen:** Wer im selben Lauf `NEU_SEITEN` erhöht oder `SUB_SEITEN` setzt, vergrößert nur die Auswahl. Abgerufen werden die zusätzlichen Seiten erst, wenn sie für `ZIEL` gebraucht werden.
- **Frischer Lauf:** `state_<KAMPAGNE>.json` löschen und die Gedächtnisdateien behalten. Bekannte Produkte ohne neuen Nutzen werden kostenlos übersprungen: Amazon-Angebote, schon gelieferte Verkäufer und Verkäufer, die laut gespeicherten Fakten an einem aktiven Filter scheitern.
- **Langer Lauf:** Netzteil anschließen. Mac: `caffeinate -dimsu` vor den Befehl setzen. Windows: Energiesparmodus abschalten.

## 9. Mehrere Kampagnen

`KAMPAGNE=name` trennt Lieferliste, Fortschritt und Ergebnisdateien, z. B. `KAMPAGNE=kunde-a` und `KAMPAGNE=kunde-b`. Das teure Gedächtnis (`seen_asins.json`, `seller_cache.json`) teilen sich alle Kampagnen. Was eine Kampagne schon geprüft hat, kostet die nächste nichts. Jede Kampagne bewertet die Fakten mit ihren **eigenen** Filtern neu, und jeder Verkäufer kann in jeder Kampagne einmal geliefert werden.

## 10. Windows (PowerShell)

Die Skripte laufen unter Windows genauso. Zugangsdaten kommen auch hier in `pfade\amazon\.env`. Nur das Setzen von Einstellungen ist in PowerShell anders. Sie gelten bis zum Schließen des Fensters:

```powershell
mkdir pfade\amazon\arbeit -Force; cd pfade\amazon\arbeit
$env:SMOKE="1"; node ..\amazon_seller_scraper.mjs
Remove-Item Env:SMOKE        # wichtig: sonst läuft auch der nächste Start als Smoke-Test
$env:KAMPAGNE="meine-liste"; $env:ZIEL="1000"; $env:BUDGET="36000"; node ..\amazon_seller_scraper.mjs
```

In der klassischen Eingabeaufforderung (cmd) heißt es `set ZIEL=1000`, ohne Anführungszeichen. Variablen, die du nicht mehr willst, mit `set NAME=` leeren. `caffeinate` gibt es unter Windows nicht: Für lange Läufe den Energiesparmodus abschalten.

## 11. Rechtlicher Hinweis

Keine Rechtsberatung. Die Nutzung muss mit den Nutzungsbedingungen von Amazon und der eingesetzten Dienste vereinbar sein. Die Firmendaten auf Amazon-Verkäuferprofilen sind Pflichtangaben und öffentlich. Wer sie für Werbung oder Kontaktaufnahme verwendet, muss trotzdem **UWG** und **DSGVO** einhalten:

- E-Mail-Werbung ohne Einwilligung ist in Deutschland auch an Unternehmen in der Regel unzulässig (§ 7 UWG).
- Die Rechtsgrundlage für die Verarbeitung ist zu dokumentieren.
- Beim Erstkontakt gilt die Informationspflicht (Art. 14 DSGVO).
- Widersprüche gehören auf eine Sperrliste.

Vor dem produktiven Einsatz anwaltlich prüfen lassen.
