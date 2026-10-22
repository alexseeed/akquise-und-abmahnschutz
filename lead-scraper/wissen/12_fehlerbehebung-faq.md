# Fehlerbehebung und häufige Fragen

**Zweck:** schnelle Antworten auf typische Probleme und Fragen.
**Für wen:** Nutzer und KI-Modelle, die Rückfragen beantworten.
**Verwandt:** alle Pfad-Dateien · `pfade/google-maps/docs/00_ANLEITUNG.md` (Abschnitt „Häufige Situationen“)

---

## Allgemein

**Welcher Pfad passt zu mir?**
Das klärt das Interview (`02`). Faustregel:

- Firma mit Adresse → Google Maps
- Marke auf Amazon → Amazon
- Liste von Onlineshops → E-Commerce (`06`)
- Firmen, die Personal suchen → Pfad noch geplant, Alternativen siehe `05`

**Kann ich eine eigene Firmenliste anreichern lassen?**
Ja. Mit Firmenname (ideal mit HR-Nummer und Ort) über den Amazon-Pfad ab Phase 4: Website, Geschäftsführung, Anrede. Für die E-Mail-Suche gibt es dafür noch keinen eigenen Pfad.

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
| „kein Browser verbunden“ | Chrome-Erweiterung nicht aktiv | Chrome öffnen, Erweiterung verbinden, auf amazon.de einloggen |
| alle Abrufe scheitern | Tab steht nicht auf amazon.de | auf eine amazon.de-Produktseite navigieren, Bibliothek neu laden |
| Tab friert ein | zu viele parallele Abrufe | höchstens ~8 Worker; Zwischenstände sichern |
| zweiter Download kommt nicht an | Chrome blockt den zweiten automatischen Download pro Tab | Umweg über `localStorage` und frischen Tab (`pfade/amazon/referenzen/browser-technik.md`) |
| Captcha oder Sperre | Amazon erkennt automatisierte Abrufe | pausieren, langsamer arbeiten, separates Konto nutzen |
| wenige Geschäftsführer | viele Seller aus HK/CN | erwartbar; deutsche Firmen haben ~95 % Fundquote |
| Impressum „leer“ beim Prüfen | Seite wird per JavaScript aufgebaut | über den Browser prüfen statt per einfachem Abruf |

## Sperrliste und Recht

**Darf ich nach dem Abgleich bedenkenlos versenden?**
Nein. Der Abgleich entfernt bekannte Abmahner. E-Mail-Werbung ohne Einwilligung bleibt grundsätzlich unzulässig (`08`).

**Eine Firma auf der Sperrliste ist ein Wunschkunde – was tun?**
Nicht anschreiben, über keinen Kanal. Wer eine Abmahnung ausgesprochen hat, will keinen Kontakt.

**Ich wurde abgemahnt – muss ich melden?**
Ja, das ist die Bedingung der Nutzung. Der Abmahnungs-Skill erledigt das automatisch und zeigt vorher, was gesendet wird.
