# Fehlerbehebung und häufige Fragen

**Zweck:** schnelle Antworten auf typische Probleme und Fragen.
**Für wen:** Nutzer und KI-Modelle, die Rückfragen beantworten.
**Verwandt:** alle Pfad-Dateien · `pfade/google-maps/docs/00_ANLEITUNG.md` (Abschnitt „Häufige Situationen“)

---

## Allgemein

**Welcher Pfad passt zu mir?**
Das klärt das Interview (`02`). Faustregel:

- Firma mit Adresse → Google Maps
- Händler oder Marke auf Amazon → Amazon
- Liste von Onlineshops → E-Commerce (`06`)
- Firmen, die Personal suchen, Branche bekannt → Recruiting über die Firmen-Website (`05`)
- Firmen, die einen bestimmten Beruf suchen → Stellensuche über Jobportale (`18`)

**Kann ich eine eigene Firmenliste anreichern lassen?**
Ja, für Firmen aus DE/AT/CH. Mit Firmenname (ideal mit Ort, Land und HR-Nummer) über die Anreicherung im Amazon-Pfad (`pfade/amazon/ABLAUF.md`, „Sonderfall“): Website, Impressum, Geschäftsführung, Anrede. Nötig ist nur ein Skael-Zugang. Hat die Liste eine E-Mail-Spalte, wird jede Adresse auf Zustellbarkeit geprüft (3 Credits je Adresse). Für die E-Mail-Suche gibt es dafür noch keinen eigenen Pfad.

**Warum fragt die KI so viel, bevor sie anfängt?**
Weil jede ungenaue Antwort Geld kostet. Ein falscher Suchbegriff oder ein zu weiches Profil verbraucht tausende Abfragen für die falschen Firmen.

**Warum heißt es so oft nur „Guten Tag“?**
Weil Name oder Geschlecht nicht sicher genug waren. Eine falsche persönliche Anrede schadet mehr als eine neutrale.

## Google Maps

| Problem | Ursache | Lösung |
|---|---|---|
| OpenAI-Aufrufe scheitern | kein Guthaben aufgeladen | bei OpenAI Zahlungsmittel hinterlegen und Guthaben aufladen |
| `doctor` meldet Platzhalter | `.env` nicht ausgefüllt | Schlüssel eintragen (die KI macht das) |
| kaum Firmen gefunden | Begriff zu speziell, Orte zu klein | Synonyme ergänzen, Ortsgröße prüfen |
| Prüfprofil lässt fast alles durch | Profil zu weich | mehr „sofort raus“, Region strenger; nur Stufe 3c neu |
| Prüfprofil filtert fast alles | Profil zu streng | Begründungen lesen, Muss-Kriterien lockern |
| ganze Zielgruppe verschwindet | `EXCLUDED_TLDS` trifft das Zielland | in `.env` leeren |
| Deutschland unvollständig | `CITIES_LIMIT=5000` | auf 10000 erhöhen |
| Export leer | nichts versandfertig, oder alles bereits exportiert | `export --all` zum Prüfen; `status` ansehen |
| Export bricht ab: Sperrliste | Liste nicht ladbar, keine lokale Kopie | Internet und `SPERRLISTE_URL` prüfen; nicht einfach abschalten |
| Lauf abgebrochen | Netz, Rechner, Rate-Limit | denselben `run`-Befehl erneut – er setzt fort |
| Wiederholung liefert dasselbe Fehlerergebnis | Skael liefert 20 Minuten lang aus dem Zwischenspeicher | 20 Minuten warten |

## Recruiting und Stellensuche

| Problem | Ursache | Lösung |
|---|---|---|
| „Diese Kampagne enthält schon einen Lauf vom Typ …“ | eine Kampagne hat immer nur eine Art (Google Maps, Recruiting oder Stellensuche) | eigene Kampagne anlegen: `./scraper.sh neue-kampagne <name>` |
| `run` verlangt einen OpenAI-Schlüssel | `LLM_PROVIDER=openai` oder `DOMAINSUCHE=openai` ist gesetzt | Schlüssel eintragen oder die Einstellung zurücknehmen; Standard ist die KI über Skael |
| Recruiting: kaum Firmen mit Stelle | gesuchte Berufe passen nicht (`--berufe`), oder die Stellen stehen nur auf externen Bewerberportalen | Berufe prüfen; branchengenauen Stellen-Prompt aus `pfade/google-maps/prompts/beispiele/` in die Kampagne kopieren; `KARRIERE_SEITEN` erhöhen; oder den Weg über die Jobportale nehmen (`18`) |
| Recruiting: passende Firmen fehlen in Liste 1/2 | keine offene Stelle erkannt, NK-Strecke aus | stehen in Liste 4. Mit `NK_ON=true` in `kampagne.env` (oder `init … --nk`), dann `run --stage 3d` und `--stage 4`, bekommen sie einen Satz zur Website |
| Opener nennt einen Bereich statt eines Berufs | die Stelle auf der Website heißt nur „Logistik“ o. Ä. | Stichprobe; branchengenaue Opener-Fassung aus `prompts/beispiele/` in die Kampagne kopieren |
| Stellensuche: viele fremde Stellen | Indeed und Stepstone suchen unscharf | `stellensuche --titel-pflicht "…"` bzw. `--titel-ausschluss "…"` setzen, dann nur `run --stage 1k` – kostet nichts |
| Stellensuche: bekannter Konzern in der Lead-Liste | Größen-Check abgeschaltet, oder das Modell kennt die Firma nicht („unbekannt“) | Liste sichten; `groessen_check.txt` schärfen und nur den Größen-Check neu laufen lassen (`pfade/stellensuche/ABLAUF.md`, Phase 5) |
| Stellensuche: IT-Firmen fehlen | der Größen-Check sortiert „IT-Wettbewerber“ aus – gedacht für Angebote rund um IT/KI | bei anderen Angeboten `stellensuche --no-groessen-check` |
| Stellensuche: viele Firmen ohne Website | Stepstone und Arbeitsagentur nennen nur den Firmennamen; `find_domain` belegt nur Domains mit passendem Impressum | erwartbar (gemessen ≈ 75–80 % belegt); der Rest steht in Liste 4 mit „keine eigene Website gefunden“ |
| `python3 -m scraper` meldet „Python 3.10 oder neuer nötig“ | macOS liefert 3.9 aus | `./scraper.sh …` (sucht selbst ein passendes Python) oder `python3.12 -m scraper …` |

## E-Commerce

| Problem | Ursache | Lösung |
|---|---|---|
| Import erkennt keine Spalten | Spaltennamen unbekannt | `--name-spalte` bzw. `--website-spalte` angeben |
| Lauf stoppt: „Anforderung fehlt“ | Shop-Profil nicht entschieden, oder Mailtext bzw. Anweisung für den persönlichen Satz fehlen. Der Pfad startet dann bewusst nicht; es entstehen keine Kosten | `python3 -m ecom status` zeigt im Block „Anforderungen“, was fehlt, und nennt den Builder. Fehlendes mit dem Nutzer klären (`pfade/e-commerce/ABLAUF.md`, Phase 1), dann denselben `run`-Befehl erneut |
| Mailtext wird abgelehnt | meist ein Tippfehler in einem Platzhalter oder die Begrüßung bzw. `{{Personalisierung}}` steht nicht oben. Alle Fehler und Hinweise: `07_lead-ausgabe-und-spalten.md`, Abschnitt E-Commerce, „Was `set-mailtext` prüft“ | Schreibweise aus der Platzhalter-Tabelle dort übernehmen, dann `set-mailtext` erneut |
| viele Shops „kein messbarer Traffic“ | kleine Shops haben keine SimilarWeb-Daten | erwartbar; wer sie trotzdem will: beide Traffic-Schwellen auf 0, dann `run --stage 1e` |
| „Website ohne Text“ | Shop baut die Seite nur per JavaScript auf oder blockt Abrufe | in Liste 3 von Hand prüfen |
| weniger Leads als übergebene Shops | Duplikate (gleiche E-Mail-Domain) oder kein Impressum/keine E-Mail | Liste 3 zeigt den Grund je Shop |
| Lauf abgebrochen | Netz, Rechner, Rate-Limit | denselben `run`-Befehl erneut – er setzt fort |

## Amazon

| Problem | Ursache | Lösung |
|---|---|---|
| `node: command not found` / „Node … ZU ALT“ | Node.js fehlt oder ist älter als 18 | Node.js LTS von nodejs.org installieren, Terminal bzw. App neu starten |
| „Oxylabs-Zugang fehlt“ | `.env` fehlt oder ist leer | `pfade/amazon/.env.example` als `.env` kopieren und selbst ausfüllen |
| „Oxylabs: abgelehnt (HTTP 401/403)“ | falscher API-Nutzer, oft der Dashboard-Login | Benutzer und Passwort des **API-Nutzers** eintragen |
| „HTTP 402“ / „traffic limit“ | Oxylabs-Guthaben bzw. Abo leer | aufladen, dann denselben Befehl erneut – er setzt fort |
| „Budget erreicht“ | harte Obergrenze erreicht | mit höherem `BUDGET` fortsetzen; gefundene Leads sind schon exportiert |
| „Alle Listen ausgeschöpft“ | Neuheiten-Listen der gewählten Kategorien sind durch | Unterkategorien ernten (`ernter_unterkategorien.mjs`, dann `SUB_SEITEN=5`) oder Suchbegriffe ergänzen |
| fast nur Leads aus China/Hongkong | ohne Länderfilter normal | `LAENDER=DE,AT,CH` setzen; Budget dann deutlich höher (`11`) |
| wenige Geschäftsführer | ohne Skael nur aus dem Verkäuferprofil (~13–36 %) | Skael-Zugang eintragen; die Anreicherung findet sie für DACH-Firmen |
| „Leads warten noch auf Kontaktdaten“ | Bright Data war noch nicht fertig | später denselben Befehl erneut, bereits bezahlt |
| `E-Mail Status` = `Not Run` | die E-Mail-Prüfung lief nicht (kein Skael-Schlüssel, Abbruch, Störung bei Skael, `EMAIL_PRUEFUNG=0`) | Schlüssel eintragen und `anreicherung.mjs` erneut starten. Eine Adresse wird höchstens in 3 Starts geprüft, danach einmal mit `ERNEUT_VERSUCHEN=1`. Ungeprüfte Adressen nicht per E-Mail anschreiben |
| „Skael liefert seit 10 Abfragen in Folge kein Ergebnis“ | Skael oder das Internet ist gestört | innerhalb von 24 Stunden erneut starten; der Stand ist gespeichert, schon abgeschickte Abfragen werden dann nicht noch einmal berechnet |
| „Skael lehnt alle Anfragen an … ab“ | Schnittstelle geändert oder `SKAEL_URL` falsch | nicht wiederholen, nichts wurde berechnet; an den Betreiber des Pakets melden |

## Sperrliste und Recht

**Darf ich nach dem Abgleich bedenkenlos versenden?**
Nein. Der Abgleich entfernt bekannte Abmahner. E-Mail-Werbung ohne Einwilligung bleibt grundsätzlich unzulässig (`08`).

**Eine Firma auf der Sperrliste ist ein Wunschkunde – was tun?**
Nicht anschreiben, über keinen Kanal. Wer eine Abmahnung ausgesprochen hat, will keinen Kontakt.

**Ich wurde abgemahnt – muss ich melden?**
Ja, das ist die Bedingung der Nutzung. Der Abmahnungs-Skill erledigt das automatisch und zeigt vorher, was gesendet wird.
