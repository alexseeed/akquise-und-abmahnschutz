# Pfad „Amazon-Seller“ – Anleitung für die KI

> **Einstieg:** Dieser Pfad wird über `SKILL.md` gewählt (Claude Code: `CLAUDE.md`, Codex: `AGENTS.md`). Das Interview ist dann gelaufen, die Antworten stehen in der Auftragsdatei `auftraege/<datum>_<name>.md` im Paketordner. **Lies sie zuerst** und frage nur, was dort fehlt. Hintergrund für Rückfragen: `wissen/04_pfad-amazon.md`.

Der Pfad findet Drittanbieter auf **amazon.de** selbst. Eine Brand-Liste ist nicht nötig. Er liefert pro Verkäufer Firma, Adresse, Land, Sortiment und geschätzten Umsatz, auf Wunsch Kontaktdaten (Bright Data), Website und Geschäftsführung (Skael). Am Ende stehen Standardformat und Sperrlisten-Abgleich.

```
Phase 0  Auftrag lesen, Einstellungen ableiten
Phase 1  Vorprüfung        node, .env, 1 Testabfrage          (--pruefen)
Phase 2  Smoke-Test         höchstens 300 Abfragen             (SMOKE=1)
Phase 3  Testlauf           20–50 Leads, Stichprobe zeigen     (KAMPAGNE=<name>-test)
Phase 4  Großlauf           Kosten nennen, Bestätigung abwarten (KAMPAGNE=<name>)
Phase 5  Anreicherung       E-Mail-Prüfung, Website, Geschäftsführung, Anrede (automatisch mit Skael-Schlüssel)
Phase 6  Standardformat     Pflichtfelder aller Pfade          (standardformat.mjs)
Phase 7  Sperrliste         immer, vor der Ausgabe             (werkzeuge/sperrliste_abgleich.py)
Phase 8  Ergebnis übersetzen
```

**Grundregeln** (aus `SKILL.md`):

- Befehle selbst ausführen und Ausgaben übersetzen.
- Eine Frage pro Nachricht.
- Kosten vor jedem großen Lauf nennen und bestätigen lassen.
- Nie nach Schlüsseln im Chat fragen. Der Nutzer trägt sie selbst in die Datei `.env` ein.
- Die Datei `.env` nie lesen, ausgeben oder durchsuchen. Ob Zugänge gesetzt sind, zeigt allein `node ../amazon_seller_scraper.mjs --pruefen`.
- Nie zwei Läufe derselben `KAMPAGNE` gleichzeitig. Vor jedem Neustart prüfen, dass kein Lauf mehr läuft (`pgrep -f amazon_seller_scraper`).

## Arbeitsordner und Befehle

Alle Befehle laufen im Ordner `pfade/amazon/arbeit/`. Er ist von Git ausgeschlossen und enthält später Lead-Daten und das Gedächtnis.

```bash
mkdir -p pfade/amazon/arbeit && cd pfade/amazon/arbeit   # bzw. <kopie>/amazon/arbeit, wenn der Pfad nach SKILL.md Schritt 1 kopiert wurde
```

Den Ordnerwechsel nur **einmal** ausführen, vom Paketordner aus. Im Zweifel vorher mit `pwd` prüfen, wo die Shell steht: Ein zweiter Aufruf aus `arbeit/` heraus legt einen falschen Unterordner an.

- **Skripte:** liegen eine Ebene höher (`../`). Die Zugänge liest jedes Skript aus `../.env`.
- **Sperrlisten-Werkzeug:** im Paketordner `../../../werkzeuge/sperrliste_abgleich.py`, in einer Kopie nach SKILL.md Schritt 1 `../../werkzeuge/sperrliste_abgleich.py`.
- **Einstellungen:** stehen als `NAME=Wert` vor dem Befehl. Zahlen ohne Tausenderpunkt.
- **Smoke-Test, Testlauf und Großlauf im Hintergrund starten.** Sie können länger dauern, als ein Befehl im Vordergrund laufen darf: Bright Data braucht für die Kontaktdaten bis zu 30 Minuten. Claude Code: Hintergrund-Ausführung. Sonst die ganze Befehlszeile mit `nohup` und Log: `KAMPAGNE=<name> ZIEL=… BUDGET=… <Filter …> nohup node ../amazon_seller_scraper.mjs > lauf_<name>.log 2>&1 &`. Den Fortschritt mit `tail -n 15 lauf_<name>.log` ansehen und übersetzt melden.
- **Abbruch:** kostet nichts, derselbe Befehl setzt fort. Steht „Gestoppt: Abbruch (SIGTERM)“ in der Ausgabe, wurde der Lauf von außen beendet: denselben Befehl im Hintergrund erneut starten.
- **Windows (PowerShell):** Einstellungen einzeln mit `$env:NAME="Wert"` setzen (`../README.md`, Abschnitt 10). `python3` heißt dort meist `python` oder `py`.

## Phase 0: Auftrag lesen und Einstellungen ableiten

Aus der Auftragsdatei:

| Auftrag | Einstellung | Hinweis |
|---|---|---|
| B1 Branche / Produktbereich | `KATEGORIEN=Küche,Garten,…` (Namensteile aus `../kategorien.json`) oder `KEYWORDS=yogamatte,thermobecher` | ohne Angabe: alle 28 Kategorien. Bei sehr enger Nische Keywords zusätzlich |
| B2 kleine / mittlere / große Händler | `MAX_PRODUKTE`, `PORTFOLIO_MAX_BEWERTUNGEN` | „keine Konzerne“: z. B. `PORTFOLIO_MAX_BEWERTUNGEN=25000`. **Nach Umsatz wird nicht gefiltert:** Der Umsatz steht als Spalte in der Liste. `UMSATZ_MAX` nur setzen, wenn der Nutzer ausdrücklich eine Umsatz-Obergrenze verlangt |
| B2 „mit eigener Marke“ | `MIN_MARKENANTEIL=0.7` | Händler, die vor allem eine Marke verkaufen |
| D1 Länder | `LAENDER=DE,AT,CH` | **Sitz des Verkäufers.** Der Marktplatz ist immer amazon.de. Ohne Angabe: alle Länder (viele Verkäufer sitzen in China) |
| D2 Ausschlüsse | `FIRMEN_AUSSCHLUSS=verlag,…`, Kategorien weglassen, Größenfilter | Amazon selbst ist immer ausgeschlossen |
| D3 Ansprechpartner | Bright Data (E-Mail, Telefon, vertretungsberechtigte Person laut Amazon) und Skael (E-Mail-Prüfung, Website, Geschäftsführung, Anrede) | E-Mail-Prüfung für alle Länder, Website und Geschäftsführung nur für DE/AT/CH (Impressumspflicht) |
| A2 Kanal = E-Mail | **Skael-Schlüssel ist Pflicht** | ohne ihn bleiben alle Adressen ungeprüft (`Not Run`) und dürfen nicht in den Versand |
| D4 Menge | `ZIEL=<Anzahl Leads>` | zählt für die ganze Kampagne, auch über Neustarts |
| D4 Budget | `BUDGET=<Oxylabs-Abfragen>` | Faustregel unten |

- **Kampagnenname:** Kurzname aus der Auftragsdatei, z. B. `KAMPAGNE=agentur-dach`. Für den Testlauf `KAMPAGNE=agentur-dach-test`.
- **Budget-Faustregel:** Ohne Filter BUDGET ≈ 30 × ZIEL. Mit `LAENDER=DE,AT,CH` sind es eher 150–250 × ZIEL, weil nur ~15 % der Verkäufer dort sitzen. Mit weiteren Filtern noch mehr. Nach dem Testlauf zählt der gemessene Wert `requests_je_lead` aus `report_<kampagne>.json`.
- **Kosten:**
  - Oxylabs: ~0,45 USD je 1.000 Abfragen.
  - Bright Data: ~1,50 USD je 1.000 Leads.
  - Skael: 3 Credits je E-Mail-Prüfung, dazu ~5–50 Credits je DACH-Lead für Website und Geschäftsführung (ohne Firmen-E-Mail eher oben, Einzelfälle darüber).

Fehlt im Auftrag etwas, das die Liste stark verändert (Länder, Größe), **eine** Frage mit Beispiel stellen. Sonst die Standardwerte nehmen und das in der Zusammenfassung sagen.

## Phase 1: Vorprüfung

Im Arbeitsordner (siehe oben):

```bash
node ../amazon_seller_scraper.mjs --pruefen
python3 --version      # für den Sperrlisten-Abgleich in Phase 7; Windows: python --version oder py --version
```

| Ausgabe | Was tun |
|---|---|
| `node: command not found` oder „Node … ZU ALT“ | Nutzer bitten, Node.js LTS von nodejs.org zu installieren. Danach das Terminal bzw. die App neu starten |
| „Oxylabs-Zugang fehlt“ | Gibt es `../.env` noch nicht: `cp ../.env.example ../.env` ausführen. Die Datei dem Nutzer im Texteditor öffnen (macOS `open -e ../.env`, Windows `notepad ..\.env`), denn Dateien mit führendem Punkt zeigt der Finder nicht an. Er trägt Benutzer und Passwort des Oxylabs-API-Nutzers ein (Konto unter oxylabs.io, Produkt „Web Scraper API“), speichert und sagt Bescheid. **Nicht im Chat abfragen, die Datei nicht selbst lesen** |
| „Oxylabs: abgelehnt (HTTP 401/403)“ | Benutzer oder Passwort falsch, oder es ist der Dashboard-Login statt des API-Nutzers |
| „HTTP 402“ / „traffic limit“ | Guthaben bzw. Abo bei Oxylabs fehlt |
| Bright Data „nicht gesetzt“ | E-Mail-Adresse und Telefon kommen **nur** von Bright Data. Ist der Kanal E-Mail oder Telefon (A2), erst den Token eintragen lassen, dann weiter. Sonst dem Nutzer sagen, was fehlt: keine E-Mail und kein Telefon |
| `python3: command not found` | Nutzer bitten, Python 3 von python.org zu installieren. Es wird erst für Phase 7 gebraucht, der Lauf kann schon starten |
| Skael „nicht gesetzt“ | Dem Nutzer sagen, was dann fehlt: keine E-Mail-Prüfung, keine Website, Geschäftsführung und persönliche Anrede. **Will der Nutzer per E-Mail anschreiben (A2), ist der Schlüssel Pflicht**: erst eintragen lassen, dann weiter |

## Phase 2: Smoke-Test

```bash
SMOKE=1 node ../amazon_seller_scraper.mjs
```

Der Test macht höchstens 300 Abfragen (≈ 0,15 USD) und liefert bis zu 5 Leads in `leads_smoke_MASTER.csv`. Er nutzt eigene Dateien und berührt das echte Gedächtnis nicht. Einstellungen wie `ZIEL`, `BUDGET` oder Filter gelten im Smoke-Test nicht. Ist ein Skael-Schlüssel gesetzt, läuft die Anreicherung mit.

Der Smoke-Test merkt sich seinen Stand. **Vor einer Wiederholung** (z. B. nach einem korrigierten Zugang) seine Dateien löschen, sonst ruft er nichts mehr ab: `rm -f *smoke*` (PowerShell: `Remove-Item *smoke*`).

Erfolg heißt:

- mindestens 1 Lead, kein „Gestoppt“ außer „Budget erreicht“,
- mit Bright-Data-Token zusätzlich: keine Zeile „Bright Data: HTTP 4…“ und kein „Bright Data lehnt den Zugang ab“. In der Zeile „Kontakte: E-Mail x/y“ sollte x über 0 liegen,
- mit Skael-Schlüssel zusätzlich: Die Ausgabe enthält `===== ANREICHERUNG FERTIG =====` und keine Zeile „Anreicherung nicht vollständig“ oder „UNVOLLSTÄNDIG“. Hat ein Lead eine E-Mail-Adresse, steht in der Zeile „E-Mail-Prüfung:“ ein echter Status (`Safe to Send`, `Risky`, `Unknown` oder `Invalid`), nicht nur `Not Run`.

Ist die Anreicherung nicht sauber durchgelaufen, **nicht** in den Großlauf gehen. Die Meldung dem Nutzer übersetzen und nach „Wenn etwas klemmt“ vorgehen.

## Phase 3: Testlauf

Mit den Einstellungen aus Phase 0, aber kleinem Ziel:

```bash
KAMPAGNE=<name>-test ZIEL=20 BUDGET=<Faustregel × 1,5> <Filter …> node ../amazon_seller_scraper.mjs
```

Danach aus `report_<name>-test.json` lesen: `funnel`, `ausschluss`, `requests_je_lead`, `kosten_usd`. Aus der Ausgabe der Anreicherung die Zeilen „E-Mail-Prüfung:“ und „Verbrauch … Credits“ lesen und die Skael-Credits je Lead ausrechnen. Für die Anreicherung gelten dieselben Erfolgskriterien wie im Smoke-Test. Aus `leads_<name>-test_MASTER.csv` drei Leads ziehen (Firma, Land, Kategorie, Produkte, Umsatz/Monat ca. EUR). Dem Nutzer übersetzt zeigen, etwa so:

> „Ich habe 20 Händler gefunden, z. B. *Müller Haushaltswaren GmbH* aus Berlin mit 40 Produkten und rund 12.000 € Umsatz im Monat. Aussortiert habe ich vor allem Händler mit Sitz außerhalb von DACH. Ein Lead hat 140 Abfragen gekostet, also etwa 6 Cent. Passt das so?“

`ZIEL` zählt Treffer vor der Endkontrolle. Es können also etwas weniger als 20 Leads herauskommen.

- **Passt die Stichprobe nicht:** Filter anpassen und den Testlauf mit einem **neuen** Kampagnennamen wiederholen, z. B. `<name>-test2`. Unter dem alten Namen sind Ziel und Budget schon verbraucht, und die alten Leads blieben in der Liste. Das Gedächtnis gilt für alle Kampagnen: Bereits geprüfte Produkte und Verkäufer kosten kaum etwas.
- **Stoppt der Testlauf mit „Budget erreicht“:** nicht von selbst erhöhen. Mit den vorhandenen Leads die Stichprobe zeigen, `requests_je_lead` ablesen und ein höheres Budget nur nach Rückfrage mit Kostenangabe setzen.

## Phase 4: Großlauf

Vorher Kosten nennen und die Bestätigung abwarten:

- `BUDGET = ZIEL × requests_je_lead × 1,2`
- dazu Bright Data ZIEL × 1,5 USD je 1.000 und die Skael-Credits (ZIEL × Credits je Lead aus dem Testlauf).
- Beim ersten Großlauf `SKAEL_MAX_CREDITS=<freigegebener Betrag>` in die Befehlszeile setzen. Der Deckel stoppt die Anreicherung sauber, die E-Mail-Prüfungen laufen zuerst.

```bash
KAMPAGNE=<name> ZIEL=<D4> BUDGET=<berechnet> <Filter …> node ../amazon_seller_scraper.mjs
```

- **Lange Läufe** im Hintergrund starten (siehe oben). Es gibt keine eigene Laufzeitmessung: Ab ~15 Abfragen pro Sekunde dauern 1.000 Leads ohne Filter etwa 30–60 Minuten.
- **Budget reicht nicht:** Der Lauf stoppt sauber und liefert die bisherigen Leads. Fortsetzen mit höherem `BUDGET`.
- **Mehr Leads später:** `ZIEL` erhöhen, derselbe Befehl setzt fort.
- **Ausgeschöpft:** Meldet der Lauf, dass die Listen leer sind, bevor das Ziel erreicht ist, einmal `KAMPAGNE=<name> node ../ernter_unterkategorien.mjs` ausführen und dann mit `SUB_SEITEN=5` fortsetzen. Der Ernter kostet bis zu 600 Abfragen (ca. 0,27 USD) **zusätzlich** zum `BUDGET`. Das dem Nutzer vorher sagen.

## Phase 5: Anreicherung und E-Mail-Prüfung (Skael)

Ist `SKAEL_API_KEY` in `../.env` gesetzt, startet sie am Ende jedes Scraper-Laufs automatisch für die Gesamtliste der Kampagne. Bezahlt werden dabei nur offene Leads. Was schon erledigt ist, kostet nichts.

Sie macht zwei Dinge, in dieser Reihenfolge:

1. **E-Mail-Prüfung** für jeden Lead mit Adresse, in allen Ländern (3 Credits je Adresse). Ergebnis in der Spalte `E-Mail Status`:

   | Status | Bedeutung | Versand |
   |---|---|---|
   | `Safe to Send` | zustellbar | ja |
   | `Risky` | Server nimmt jede Adresse an (Catch-all) | getrennt und vorsichtig |
   | `Unknown` | nicht prüfbar | getrennt und vorsichtig |
   | `Invalid` | ungültig, wird zurückkommen | nie. Die Adresse wird im Standardformat aus dem E-Mail-Feld entfernt |
   | `Not Run` | nicht geprüft (kein Schlüssel, Abbruch, Störung bei Skael, abgeschaltet) | nie per E-Mail |

2. **Website, Impressum, Geschäftsführung, Anrede** für Leads aus DE/AT/CH.

Manuell nachholen (beides) – nach einem Abbruch, nach Code 2, 3, 4 oder 5, oder wenn der Schlüssel erst später eingetragen wurde:

```bash
KAMPAGNE=<name> node ../anreicherung.mjs
```

- Ergebnis: `leads_<name>_MASTER_angereichert.csv` mit E-Mail Status, Website, Geschäftsführung, Anrede, Vorname, Nachname, Ansprache und Match-Status.
- Am Ende steht eine Zeile „E-Mail-Prüfung: Safe to Send … · Risky … · Invalid …“. Diese Zahlen in Phase 8 nennen.
- Der Fortschritt hängt an Kampagne und Seller-ID. Kein Lead wird doppelt bezahlt, ein Abbruch kostet nichts.
- Website und Geschäftsführung nur für DE/AT/CH (`ANREICHERUNG_LAENDER`). Leads aus anderen Ländern bekommen nur die E-Mail-Prüfung.
- Deckel für Credits: `SKAEL_MAX_CREDITS=<Zahl>`. Er gilt für alle Starts der Kampagne zusammen.
- **`Not Run` bleibt stehen:** Eine Adresse wird höchstens in 3 Starts geprüft. Meldet der Start „… Adressen wurden schon in 3 Starts ohne Ergebnis geprüft“, nicht weiter wiederholen. Erst wenn die Ursache behoben ist (Skael-Störung vorbei), einmal mit `ERNEUT_VERSUCHEN=1` starten.
- Stoppt die Anreicherung mit „Skael liefert seit 10 Abfragen in Folge kein Ergebnis“ (Code 5), ist der Stand gespeichert und nichts fälschlich als erledigt markiert. Denselben Befehl **innerhalb von 24 Stunden** erneut starten: Dann werden schon abgeschickte Abfragen nicht noch einmal berechnet.

## Phase 6: Standardformat

```bash
node ../standardformat.mjs leads_<name>_MASTER_angereichert.csv     # ohne Anreicherung: leads_<name>_MASTER.csv
```

Schreibt `…_standard.csv`. Vorne stehen die Pflichtfelder aller Pfade (`wissen/07`): Firmenname, Website, E-Mail, E-Mail Status, Anrede, Vorname, Nachname, Ansprache („Guten Tag Herr Müller“ oder neutral „Guten Tag“), Quelle, Pfad. Dahinter folgen alle übrigen Spalten. Eine Personalisierung liefert dieser Pfad nicht.

Adressen mit Status `Invalid` stehen nicht mehr im Feld E-Mail, sondern in der letzten Spalte `E-Mail ungültig`.

Meldet das Skript „ACHTUNG: … Adressen sind ungeprüft“:

- **Der Nutzer schreibt per E-Mail an:** einmal Phase 5 nachholen und das Standardformat neu erzeugen. Bleiben danach Adressen `Not Run`, nicht weiter wiederholen. Die Liste ausliefern, die Zahl nennen und sagen, dass diese Adressen nicht per E-Mail angeschrieben werden dürfen.
- **Anderer Kanal (Telefon, Brief):** Die Meldung ist ohne Skael-Schlüssel normal. Weiter mit Phase 7.

## Phase 7: Sperrliste (immer)

```bash
python3 ../../../werkzeuge/sperrliste_abgleich.py leads_<name>_MASTER_angereichert_standard.csv --spalten "E-Mail,E-Mail ungültig,Website,Impressum-URL"
```

Ohne Anreicherung gibt es die Spalte `Impressum-URL` nicht. Dann:

```bash
python3 ../../../werkzeuge/sperrliste_abgleich.py leads_<name>_MASTER_standard.csv --spalten "E-Mail,E-Mail ungültig,Website"
```

- Ergebnis: `…_bereinigt.csv` für den Versand und `…_gesperrt.csv`. Gesperrte Firmen nie anschreiben, über keinen Kanal.
- `--spalten` ist Pflicht, sonst würden Amazon-Links mitgeprüft. `E-Mail ungültig` gehört dazu, damit auch die Domain einer aussortierten Adresse geprüft wird.
- Ist die Sperrliste nicht ladbar (Internet, Adresse falsch), wird **nicht** ausgeliefert. Die Ursache klären, nicht abschalten.
- **Ausnahme „nicht eingerichtet“:** Meldet das Werkzeug „SPERRLISTE_URL nicht eingerichtet (enthält noch OWNER)“, hat der Herausgeber des Pakets die Community-Sperrliste noch nicht online gestellt. Das dem Nutzer so sagen. Steht in der Auftragsdatei dazu ein Hinweis oder stimmt er zu, denselben Befehl mit `--ohne-liste` am Ende ausführen. Im Ergebnis ausdrücklich sagen, dass **kein** Abgleich stattgefunden hat. Nennt der Herausgeber später die Adresse: `SPERRLISTE_URL=<adresse>` vor den Befehl setzen und den Abgleich wiederholen.
- Ohne Anreicherung gibt es nur Bright-Data-E-Mails zum Abgleichen. Verkäufer ohne Website und E-Mail lassen sich nicht abgleichen, das dem Nutzer sagen.

## Phase 8: Ergebnis übersetzen

Dem Nutzer nennen (Abschluss nach `SKILL.md` Schritt 4):

- **Gefundene Leads:** Zeilen in `_bereinigt.csv`.
- **Davon mit Website / E-Mail / persönlicher Ansprache:** aus der Ausgabe von `standardformat.mjs`.
- **E-Mail-Prüfung:** wie viele `Safe to Send`, `Risky`, `Unknown`, `Invalid` und `Not Run`. Dazu sagen: zuerst nur an `Safe to Send` senden, `Risky` und `Unknown` getrennt und vorsichtig, sonst leidet die Absender-Reputation.
- **Durch die Sperrliste gefallen:** Zeilen in `_gesperrt.csv`.
- **Kosten:** `kosten_usd` und `requests_je_lead` aus dem Report.
- **Datei für den Versand:** vollständiger Pfad zur `_bereinigt.csv`. Das ist eine Tabelle, die sich in Excel öffnet.
- **Lief Phase 7 mit `--ohne-liste`:** ausdrücklich sagen, dass die Liste trotz des Namens `_bereinigt` **nicht** mit der Sperrliste abgeglichen ist und der Abgleich nachgeholt wird, sobald die Sperrliste online ist.

## Sonderfall: eigene Firmenliste

Für eine vorhandene Liste (CSV mit Spalte `Firma` oder `Firmenname`, ideal dazu `Adresse`/`Ort`, `Land`, `Handelsregister`, `E-Mail`) ohne Amazon-Bezug. Braucht nur den Skael-Schlüssel. Hat die Liste eine E-Mail-Spalte, wird jede Adresse auf Zustellbarkeit geprüft (3 Credits je Adresse, alle Länder). Die Original-CSV angeben, keine schon angereicherte Datei:

```bash
cp <liste.csv> . && KAMPAGNE=<name> CSV=<liste.csv> ANREICHERUNG_LAENDER=alle node ../anreicherung.mjs
node ../standardformat.mjs <liste>_angereichert.csv
python3 ../../../werkzeuge/sperrliste_abgleich.py <liste>_angereichert_standard.csv --spalten "E-Mail,E-Mail ungültig,Website,Impressum-URL"
```

`ANREICHERUNG_LAENDER=alle` nur setzen, wenn die Liste keine Länderspalte hat oder ausschließlich DACH-Firmen enthält.

## Wenn etwas klemmt

**Vorübergehende API-Fehler wiederholen die Skripte selbst.** Das gilt für Oxylabs, Bright Data und Skael gleichermaßen (`wiederholen.mjs`). Netzwerkfehler, Zeitüberschreitungen, unlesbare Antworten und HTTP 408, 425, 429, 500, 502, 503 und 504 werden bis zu `MAX_RETRIES` Mal versucht (Standard 5). Dazwischen liegen 2, 4, 8 und 16 Sekunden Pause, bei 429 (Rate-Limit) 5, 10, 20 und 40 Sekunden. Eine Pause dauert höchstens 60 Sekunden, nennt die API eine Wartezeit (`Retry-After`), gilt diese. Dauerhafte Fehler (HTTP 400, 401, 402, 403, 404, Eingabe abgelehnt) brechen sofort ab, die Meldung der API steht dabei. Auf ein Skael-Ergebnis wird höchstens `SKAEL_MAX_WARTEZEIT` Sekunden gewartet, auf einen Bright-Data-Block höchstens `BD_TIMEOUT_MIN` Minuten. Danach holt der nächste Start es ab, ohne es neu zu bezahlen. Ist ein Skael-Auftrag aus vorübergehendem Grund gescheitert („timeout“, „unavailable“ …), wird er einmal neu eingereicht. Scheitert ein einzelner Lead oder Verkäufer auch nach allen Versuchen, bleibt er offen und der Lauf geht weiter. Am Ende steht eine Zeile „Fehler: …“ bzw. „Fehler in diesem Start: …“ mit der Anzahl. Ein Lauf hängt deshalb nie endlos. Läuft er scheinbar still, wartet er gerade eine Pause ab. Bei einer längeren Störung kann `MAX_RETRIES=8` helfen, ein Neustart setzt in jedem Fall am Checkpoint fort.

| Meldung | Bedeutung | Was tun |
|---|---|---|
| „Budget erreicht“ | harte Obergrenze erreicht, Leads wurden geliefert | mit höherem `BUDGET` fortsetzen. Vorher dem Nutzer die Mehrkosten nennen |
| „KATEGORIEN: kein Treffer für …“ | ein Kategoriename ist falsch geschrieben oder die Umlaute kamen verstümmelt an | Namen aus der Meldung übernehmen. Es wurde nichts bezahlt |
| „Bright Data: HTTP 401/402/403“ / „Bright Data lehnt den Zugang ab“ | Token falsch oder Guthaben leer. Die Leads sind gefunden und warten auf Kontaktdaten | Nutzer bitten, Token bzw. Guthaben zu prüfen, dann denselben Befehl erneut. Nur wenn er ausdrücklich ohne E-Mail und Telefon weitermachen will: Token aus der `.env` nehmen lassen und erneut starten |
| „Gestoppt: Abbruch (SIGTERM)“ | der Lauf wurde von außen beendet, z. B. durch ein Zeitlimit | denselben Befehl im Hintergrund erneut starten, es geht nichts verloren |
| „Leer auf Seite 1 …“ / „Tote Listen“ | Kategorie liefert keine Neuheiten | nichts. Nach zwei leeren Starts wird die Liste nicht mehr bezahlt |
| „HTTP 402“ / „Ausfall: 30 Abrufe in Folge ohne Ergebnis“ | Oxylabs-Guthaben leer bzw. Netz weg | Guthaben bzw. Internet prüfen, dann denselben Befehl erneut |
| „X ist ungültig“ | Tippfehler in einer Einstellung | Wert korrigieren, es wurde nichts bezahlt |
| „Leads warten noch auf Kontaktdaten“ | Bright Data war noch nicht fertig | später denselben Befehl erneut, bereits bezahlt |
| Anreicherung Code 2 / 3 / 4 | Skael-Schlüssel abgelehnt / Credits leer / Deckel erreicht | Schlüssel bzw. Guthaben prüfen, Deckel erhöhen, dann `KAMPAGNE=<name> node ../anreicherung.mjs` |
| Anreicherung Code 5: „Skael liefert seit 10 Abfragen in Folge kein Ergebnis“ oder „UNVOLLSTÄNDIG“ | Skael oder das Internet ist gerade gestört | der Stand ist gespeichert. Innerhalb von 24 Stunden erneut starten, dann wird nichts doppelt berechnet: `KAMPAGNE=<name> node ../anreicherung.mjs` |
| „Skael lehnt alle Anfragen an … ab“ (Code 1) | die Schnittstelle hat sich geändert oder `SKAEL_URL` ist falsch | nicht wiederholen, es wurde nichts berechnet. Meldung an den Betreiber des Pakets geben |
| `E-Mail Status` = `Not Run` | Prüfung lief nicht: kein Schlüssel, Störung, `EMAIL_PRUEFUNG=0` | Skael-Schlüssel prüfen, einmal `KAMPAGNE=<name> node ../anreicherung.mjs`. Nach 3 Starts ohne Ergebnis hilft nur `ERNEUT_VERSUCHEN=1`, wenn die Ursache behoben ist. Sonst die Adressen nicht per E-Mail anschreiben |
| „… ist bereits angereichert bzw. im Standardformat“ | der Anreicherung wurde eine fertige Datei übergeben | die MASTER- bzw. Original-CSV angeben |
| Sperrliste: „SPERRLISTE_URL nicht eingerichtet (enthält noch OWNER)“ | die Community-Sperrliste ist in diesem Paket noch nicht online | Phase 7, Ausnahme „nicht eingerichtet“: mit `--ohne-liste` ausführen und sagen, dass nicht abgeglichen wurde |
| fast nur Leads aus China/HK | ohne `LAENDER` normal | Filter `LAENDER=DE,AT,CH` vorschlagen |

Alle Einstellungen, Dateien und Spalten stehen in `README.md` in diesem Ordner.
