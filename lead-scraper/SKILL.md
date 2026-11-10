---
name: lead-scraper
description: "Baut versandfertige B2B-Leadlisten: klärt im Interview Angebot, Wunschkunde, Fundort, Länder und Umfang und wählt den Pfad – Google Maps (Firmen mit Standort: Geschäftsführer, E-Mail, Anrede, Text), Amazon-Seller (Drittanbieter auf amazon.de), E-Commerce (Shop-Liste prüfen und anreichern) oder Recruiting auf zwei Wegen: offene Stelle auf der Firmen-Website erkennen oder konkrete Anzeigen aus Indeed, Stepstone, Arbeitsagentur und Kununu holen, jeweils mit Opener zur Stelle. Gleicht jede Liste mit der Sperrliste ab. Optional danach: Video je Lead (Skael) und eigene Landingpage. Nutze den Skill IMMER, wenn der User Leads finden, eine Zielgruppe scrapen, eine Leadliste aufbauen oder anreichern, Amazon-Händler, Firmen mit offenen Stellen oder Stellenanzeigen finden, Ansprachen erzeugen oder Video-Outreach einrichten will – z. B. „scrape mir alle Zahnärzte in Bayern“, „Speditionen, die Fahrer suchen“, „such mir Stellen als Berufskraftfahrer bei Indeed“, „reichere diese Shopliste an“."
---

# Lead-Scraper – Einstieg, Interview, Pfadwahl

Dieser Skill ist der gemeinsame Einstieg für alle Lead-Quellen. Er fragt zuerst, wen der Nutzer erreichen will, und leitet dann den passenden Pfad ein:

```
Interview (wissen/02) ─► Pfad wählen ─┬─► Google Maps   pfade/google-maps/   (verfügbar)
                                      ├─► Amazon-Seller pfade/amazon/        (verfügbar)
                                      ├─► Recruiting    pfade/recruiting/    (verfügbar: Stelle auf der Firmen-Website)
                                      ├─► Stellensuche  pfade/stellensuche/  (verfügbar: Anzeigen aus Jobportalen)
                                      └─► E-Commerce    pfade/e-commerce/    (verfügbar, Beta)
                                                 │
                                                 ▼
                              Sperrlisten-Abgleich (immer) ─► fertige Liste
                                                 │  mit Video (Interview A2)
                                                 ▼
                              Videoseiten pfade/videoseiten/: Video je Lead ─► eigene Landingpage ─► Versandliste
```

Alles Wissen steht in `wissen/` (Startpunkt: `wissen/00_INDEX.md`). Lies dort nach, statt zu raten. Beantworte Rückfragen des Nutzers aus diesen Dateien.

## Grundhaltung

- **Der Nutzer ist in der Regel kein Entwickler.** Befehle selbst ausführen, nicht zum Abtippen vorlegen. Ergebnisse übersetzen, keine Rohausgaben zeigen. Bei Fehlern sagen, was zu tun ist.
- **Eine Frage pro Nachricht**, immer mit Beispiel. Keine Fachbegriffe (ICP, Prompt, Confidence, Stage, API, `.env`) ohne Übersetzung.
- **Ehrlich über Grenzen:**
  - Recruiting und Stellensuche sind offline getestet; gemessene Quoten aus echten Läufen stehen in `wissen/05` und `wissen/18`, soweit vorhanden.
  - Stellensuche „nur Stellenliste“ ist nicht versandfertig: ohne Kontaktdaten und meist ohne Website (kein Sperrlisten-Abgleich).
  - Amazon nur für amazon.de. Geschäftsführung und Website gibt es dort praktisch nur für Firmen aus DE/AT/CH.
  - Fundquoten und Fehlerquoten offen nennen (`wissen/03`, `wissen/04`).
- **Kosten vor jedem großen Lauf nennen** und die Bestätigung abwarten. Immer erst ein Testlauf.

## Schritt 1 – Arbeitsordner klären

Der Skill-Ordner ist oft schreibgeschützt. Läufe brauchen einen beschreibbaren Ordner beim Nutzer, z. B. `~/Leads/`.

- **Claude Code oder Codex im Paketordner:** direkt dort arbeiten. Der Amazon-Pfad arbeitet in `pfade/amazon/arbeit/`.
- **Sonst:** den Nutzer nach einem Ordner fragen, mit Beispiel `~/Leads`. Den benötigten Pfad dorthin kopieren (`pfade/google-maps/`, `pfade/amazon/` bzw. `pfade/e-commerce/`) und `werkzeuge/` daneben legen.

Auftragsdateien liegen in `auftraege/` im Arbeitsordner.

## Schritt 2 – Interview

Lies `wissen/02_zielgruppen-interview.md` und führe das Interview genau so:

- **Block A:** Angebot und Kanal.
- **Block B:** Wunschkunde.
- **Block C:** Wo man die Firmen findet.
- **Block D:** Länder, Ausschlüsse, Ansprechpartner, Menge und Budget.
- **Blöcke V und L** nur, wenn der Nutzer mit persönlichem Video arbeiten will: Video und eigene Landingpage.

Was der Nutzer schon gesagt hat, nicht erneut fragen.

**Liegt in `auftraege/` schon eine Auftragsdatei für dieses Vorhaben:** zuerst lesen, dem Nutzer in wenigen Sätzen zusammenfassen und bestätigen lassen. Dann nur fragen, was dort unter „Offene Punkte“ steht oder fehlt, und mit Schritt 3 weitermachen. Stehen dort fertige Einstellungen für den Pfad, genau diese verwenden.

Wenn der Kanal E-Mail ist, **einmal** kurz erwähnen: E-Mail-Werbung an Firmen ohne vorherige Einwilligung ist in Deutschland grundsätzlich unzulässig (§ 7 Abs. 2 Nr. 2 UWG). Die Sperrliste senkt das Risiko, beseitigt es aber nicht. Details: `wissen/08_versand-und-recht.md`. Nicht wiederholen, nicht belehren.

## Schritt 3 – Pfad wählen und bestätigen lassen

- **Entscheidung:** nach der Tabelle in `wissen/02_zielgruppen-interview.md`, Abschnitt „Entscheidung“.
- **Zusammenfassen:** Zielgruppe, Pfad mit Begründung, Gebiet, Menge, Kosten-Größenordnung, nächster Schritt.
- **Speichern:** Nach der Bestätigung die Auftragsdatei schreiben.

| Pfad | Anleitung für dich | Voraussetzungen |
|---|---|---|
| Google Maps | `pfade/google-maps/CLAUDE.md` (Bedienung) und `pfade/google-maps/docs/00_ANLEITUNG.md` (Durchlauf) | Python ≥ 3.10, Skael-Zugang (die KI läuft standardmäßig über Skael); OpenAI nur bei `LLM_PROVIDER=openai` oder `DOMAINSUCHE=openai`, dann mit aufgeladenem Guthaben |
| Amazon-Seller | `pfade/amazon/ABLAUF.md` | Node.js ≥ 18, Oxylabs-Zugang (Pflicht); Bright Data für Kontaktdaten; Skael für E-Mail-Prüfung (Pflicht bei E-Mail-Versand), Website und Geschäftsführung. Zugänge in `pfade/amazon/.env` |
| Eigene Firmenliste | `pfade/amazon/ABLAUF.md`, Abschnitt „Sonderfall“ | CSV mit Firmenname, ideal mit Ort, Land und HR-Nummer; Node.js ≥ 18, Skael-Zugang |
| E-Commerce | `pfade/e-commerce/ABLAUF.md` | Shop-Liste als CSV (Firmenname und/oder Website), Python ≥ 3.10, Zugänge Skael und OpenAI. Erkennt das Shopsystem nicht selbst: Wer nur z. B. Shopware will, braucht eine Liste mit Shopsystem-Spalte. Beta: erster echter Testlauf steht aus. Beides dem Nutzer vor der Pfad-Bestätigung sagen |
| Recruiting (Firmen-Website) | `pfade/recruiting/ABLAUF.md` (Programm: `pfade/google-maps/`) | wie Google Maps |
| Stellensuche (Jobportale) | `pfade/stellensuche/ABLAUF.md` (Programm: `pfade/google-maps/`) | wie Google Maps; „nur Stellenliste“ braucht keine KI |

Der Pfad übernimmt die Antworten aus der Auftragsdatei. Er fragt nur nach, was dort fehlt:

- **Google Maps:** die drei Runden zum Wunschkundenprofil und die Suchbegriffe.
- **Amazon:** höchstens Größe und Art der Händler (klein/groß, eigene Marke), wenn das Interview dazu nichts sagt. Danach Vorprüfung, Smoke-Test und Testlauf mit Stichprobe.
- **Recruiting:** gesuchte Berufe, Branche und Region, Umgang mit Firmen ohne Stelle (R1–R4 in `pfade/recruiting/ABLAUF.md`).
- **Stellensuche:** Suchbegriffe, Gegend, nur Stellenliste oder voller Lauf, Alter der Anzeigen (S1–S4 in `pfade/stellensuche/ABLAUF.md`).
- **Recruiting, Weg noch offen:** Testballon anbieten. Er fährt beide Wege mit je ~100 Leads, mit Budget je Weg und Fallback bei zu wenigen Stellen. Danach Vergleichsbericht, der Nutzer wählt. Siehe `pfade/google-maps/docs/09_TESTBALLON.md`. Kosten vorher nennen und bestätigen lassen.
- **E-Commerce:** Shop-Liste, Shopsystem, Mindestgröße, Shop-Profil, Mailtext und Personalisierung – Liste und Fragen in `pfade/e-commerce/ABLAUF.md`, Phase 1. Gestartet wird erst, wenn alles geklärt ist.

Google Maps, Recruiting und Stellensuche laufen im selben Programm (`pfade/google-maps/`), jede Zielgruppe als eigene Kampagne (`./scraper.sh --kampagne <name> …`).

## Schritt 4 – Abschluss (jeder Pfad)

1. **Sperrlisten-Abgleich:**
   - Google Maps, Recruiting und Stellensuche erledigen ihn beim Export selbst (Liste 5).
   - Alle anderen Pfade:
     ```bash
     python3 werkzeuge/sperrliste_abgleich.py <liste.csv>
     ```
     Amazon: den Befehl aus `pfade/amazon/ABLAUF.md`, Phase 7 nehmen (mit `--spalten`, damit Amazon-Links nicht mitgeprüft werden).
   - Ist die Liste nicht ladbar, wird nicht ausgeliefert. Ursache klären (Internet, `SPERRLISTE_URL`), nicht abschalten. Einzige Ausnahme: Die Sperrliste ist in diesem Paket noch nicht eingerichtet (`pfade/amazon/ABLAUF.md`, Phase 7).
2. **Zahlen nennen:**
   - gefundene Firmen,
   - Firmen mit Ansprechpartner,
   - Firmen mit persönlicher Ansprache,
   - Firmen, die wegen der Sperrliste rausgefallen sind.
3. **Hinweise für den Versand** (kurz):
   - Gesperrte Firmen nie anschreiben.
   - Zuerst nur an `Safe to Send` senden. `Risky`/`Unknown`-Adressen gesondert behandeln.
   - `Invalid` und `Not Run` nie per E-Mail anschreiben.
   - Bei einer Abmahnung den Skill `abmahnung-werbemail-abwehr` nutzen. Er meldet den Abmahner an die Sperrliste.

## Schritt 5 – Video und Landingpage (wenn A2 „Video“ enthält)

Nach Schritt 4 und erst wenn die Liste steht:

1. Export im Lead-Format: `./scraper.sh --kampagne <k> export --lead-format` (im Ordner `pfade/google-maps/`).
2. Dem Nutzer in zwei Sätzen sagen, was jetzt kommt: Seite in seinem Look gestalten, Video aufnehmen bzw. prüfen, Videos erzeugen, eigenen Server einrichten, Seiten hochladen, Versandliste. Was er selbst tun muss, zeigst du ihm an der jeweiligen Stelle Schritt für Schritt.
3. `pfade/videoseiten/ABLAUF.md` lesen und genau so durchführen (Teile A bis F). Antworten aus den Blöcken V und L der Auftragsdatei übernehmen, nicht erneut fragen.

## Rückfragen beantworten

Fragt der Nutzer „warum“, „was kostet“, „was bedeutet“ oder „was mache ich, wenn“, steht die Antwort in `wissen/`:

| Thema | Datei |
|---|---|
| Ablauf, Pfade | `01_ueberblick.md` |
| Interview | `02_zielgruppen-interview.md` |
| Google Maps | `03_pfad-google-maps.md` |
| Amazon | `04_pfad-amazon.md` |
| Recruiting (Firmen-Website) | `05_pfad-recruiting.md` |
| Stellensuche (Jobportale) | `18_pfad-stellensuche.md` |
| E-Commerce | `06_pfad-e-commerce.md` |
| Spalten, Ansprache | `07_lead-ausgabe-und-spalten.md` |
| Recht | `08_versand-und-recht.md` |
| Sperrliste | `09_sperrliste.md` |
| Abmahnung | `10_abmahnung-was-tun.md` |
| Zugänge, Kosten | `11_zugaenge-und-kosten.md` |
| Fehler, FAQ | `12_fehlerbehebung-faq.md` |
| Begriffe | `13_glossar.md` |
| Neuer Pfad | `14_neuen-pfad-anlegen.md` |
| Video, Landingpage, Server | `16_videoseiten.md` |
