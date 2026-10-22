---
name: lead-scraper
description: "Baut versandfertige B2B-Leadlisten: klärt im Interview Angebot, Wunschkunde, Fundort, Länder und Umfang und wählt den Pfad – Google Maps (Firmen mit Standort: Suche, Profil-Prüfung, Impressum, Geschäftsführer, E-Mail, Anrede, Personalisierung) oder Amazon-Seller (Brand-Liste → Seller ID, Amazon-Impressum, Website, Geschäftsführer, Anrede) oder E-Commerce (Shop-Liste → aktiver Shop? passt zum Shop-Profil? Traffic? → Impressum, E-Mail, Anrede, Personalisierung passend zum Mailtext). Gleicht jede Liste mit der Sperrliste ab; Recruiting ist geplant. Nutze den Skill IMMER, wenn der User Leads finden, eine Zielgruppe scrapen, eine Leadliste aufbauen oder anreichern, Firmen über Google Maps finden, Amazon-Seller recherchieren, Geschäftsführer ermitteln oder Ansprachen erzeugen will – z. B. „scrape mir alle Zahnärzte in Bayern“, „Leadliste für Metallbauer“, „wer steckt hinter diesen Amazon-Brands“, „reichere diese Shopliste an“, oder bei einer CSV mit „Brand Name“/„Dominant Seller“ bzw. einer Liste von Onlineshops."
---

# Lead-Scraper – Einstieg, Interview, Pfadwahl

Dieser Skill ist der gemeinsame Einstieg für alle Lead-Quellen. Er fragt zuerst, wen der Nutzer erreichen will, und leitet dann den passenden Pfad ein:

```
Interview (wissen/02) ─► Pfad wählen ─┬─► Google Maps   pfade/google-maps/   (verfügbar)
                                      ├─► Amazon-Seller pfade/amazon/        (verfügbar)
                                      ├─► Recruiting    pfade/recruiting/    (geplant)
                                      └─► E-Commerce    pfade/e-commerce/    (verfügbar, Beta)
                                                 │
                                                 ▼
                              Sperrlisten-Abgleich (immer) ─► fertige Liste
```

Alles Wissen steht in `wissen/` (Startpunkt: `wissen/00_INDEX.md`). Lies dort nach, statt zu raten. Beantworte Rückfragen des Nutzers aus diesen Dateien.

## Grundhaltung

- **Der Nutzer ist in der Regel kein Entwickler.** Befehle selbst ausführen, nicht zum Abtippen vorlegen. Ergebnisse übersetzen, keine Rohausgaben zeigen. Bei Fehlern sagen, was zu tun ist.
- **Eine Frage pro Nachricht**, immer mit Beispiel. Keine Fachbegriffe (ICP, Prompt, Confidence, Stage, API, `.env`) ohne Übersetzung.
- **Ehrlich über Grenzen:**
  - Geplante Pfade gibt es noch nicht.
  - Amazon nur für amazon.de.
  - Fundquoten und Fehlerquoten offen nennen (`wissen/03`, `wissen/04`).
- **Kosten vor jedem großen Lauf nennen** und die Bestätigung abwarten. Immer erst ein Testlauf.

## Schritt 1 – Arbeitsordner klären

Der Skill-Ordner ist oft schreibgeschützt. Läufe brauchen einen beschreibbaren Ordner beim Nutzer, z. B. `~/Leads/`.

- **Claude Code im Paketordner:** direkt dort arbeiten.
- **Sonst:** den Nutzer nach einem Ordner fragen, mit Beispiel `~/Leads`. Den benötigten Pfad dorthin kopieren (`pfade/google-maps/`, `pfade/amazon/` bzw. `pfade/e-commerce/`) und `werkzeuge/` daneben legen.

Auftragsdateien liegen in `auftraege/` im Arbeitsordner.

## Schritt 2 – Interview

Lies `wissen/02_zielgruppen-interview.md` und führe das Interview genau so:

- **Block A:** Angebot und Kanal.
- **Block B:** Wunschkunde.
- **Block C:** Wo man die Firmen findet.
- **Block D:** Länder, Ausschlüsse, Ansprechpartner, Menge und Budget.

Was der Nutzer schon gesagt hat, nicht erneut fragen.

Wenn der Kanal E-Mail ist, **einmal** kurz erwähnen: E-Mail-Werbung an Firmen ohne vorherige Einwilligung ist in Deutschland grundsätzlich unzulässig (§ 7 Abs. 2 Nr. 2 UWG). Die Sperrliste senkt das Risiko, beseitigt es aber nicht. Details: `wissen/08_versand-und-recht.md`. Nicht wiederholen, nicht belehren.

## Schritt 3 – Pfad wählen und bestätigen lassen

- **Entscheidung:** nach der Tabelle in `wissen/02_zielgruppen-interview.md`, Abschnitt „Entscheidung“.
- **Zusammenfassen:** Zielgruppe, Pfad mit Begründung, Gebiet, Menge, Kosten-Größenordnung, nächster Schritt.
- **Speichern:** Nach der Bestätigung die Auftragsdatei schreiben.

| Pfad | Anleitung für dich | Voraussetzungen |
|---|---|---|
| Google Maps | `pfade/google-maps/CLAUDE.md` (Bedienung) und `pfade/google-maps/docs/00_ANLEITUNG.md` (Durchlauf) | Python ≥ 3.10, Zugänge Skael und OpenAI (OpenAI mit aufgeladenem Guthaben) |
| Amazon-Seller | `pfade/amazon/ABLAUF.md` | Brand-Liste als CSV, Chrome mit amazon.de-Login und Claude-in-Chrome, Subagenten |
| Eigene Firmenliste | `pfade/amazon/ABLAUF.md` ab Phase 4 | CSV mit Firmenname, optional HR-Nummer und Ort |
| E-Commerce | `pfade/e-commerce/ABLAUF.md` | Shop-Liste als CSV (Firmenname und/oder Website), Python ≥ 3.10, Zugänge Skael und OpenAI. Erkennt das Shopsystem nicht selbst: Wer nur z. B. Shopware will, braucht eine Liste mit Shopsystem-Spalte. Beta: erster echter Testlauf steht aus. Beides dem Nutzer vor der Pfad-Bestätigung sagen |
| Recruiting | `pfade/recruiting/README.md` | noch nicht gebaut – Alternative anbieten, Antworten trotzdem sichern |

Der Pfad übernimmt die Antworten aus der Auftragsdatei. Er fragt nur nach, was dort fehlt:

- **Google Maps:** die drei Runden zum Wunschkundenprofil und die Suchbegriffe.
- **Amazon:** die Brand-Liste.
- **E-Commerce:** Shop-Liste, Shopsystem, Mindestgröße, Shop-Profil, Mailtext und Personalisierung – Liste und Fragen in `pfade/e-commerce/ABLAUF.md`, Phase 1. Gestartet wird erst, wenn alles geklärt ist.

## Schritt 4 – Abschluss (jeder Pfad)

1. **Sperrlisten-Abgleich:**
   - Google Maps erledigt ihn beim Export selbst (Liste 5).
   - Alle anderen Pfade:
     ```bash
     python3 werkzeuge/sperrliste_abgleich.py <liste.csv>
     ```
   - Ist die Liste nicht ladbar, wird nicht ausgeliefert. Ursache klären (Internet, `SPERRLISTE_URL`), nicht abschalten.
2. **Zahlen nennen:**
   - gefundene Firmen,
   - Firmen mit Ansprechpartner,
   - Firmen mit persönlicher Ansprache,
   - Firmen, die wegen der Sperrliste rausgefallen sind.
3. **Hinweise für den Versand** (kurz):
   - Gesperrte Firmen nie anschreiben.
   - `Risky`/`Unknown`-Adressen gesondert behandeln.
   - Bei einer Abmahnung den Skill `abmahnung-werbemail-abwehr` nutzen. Er meldet den Abmahner an die Sperrliste.

## Rückfragen beantworten

Fragt der Nutzer „warum“, „was kostet“, „was bedeutet“ oder „was mache ich, wenn“, steht die Antwort in `wissen/`:

| Thema | Datei |
|---|---|
| Ablauf, Pfade | `01_ueberblick.md` |
| Interview | `02_zielgruppen-interview.md` |
| Google Maps | `03_pfad-google-maps.md` |
| Amazon | `04_pfad-amazon.md` |
| Recruiting (geplant) | `05_pfad-recruiting.md` |
| E-Commerce | `06_pfad-e-commerce.md` |
| Spalten, Ansprache | `07_lead-ausgabe-und-spalten.md` |
| Recht | `08_versand-und-recht.md` |
| Sperrliste | `09_sperrliste.md` |
| Abmahnung | `10_abmahnung-was-tun.md` |
| Zugänge, Kosten | `11_zugaenge-und-kosten.md` |
| Fehler, FAQ | `12_fehlerbehebung-faq.md` |
| Begriffe | `13_glossar.md` |
| Neuer Pfad | `14_neuen-pfad-anlegen.md` |
