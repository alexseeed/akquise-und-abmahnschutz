# Pfad „E-Commerce“ – Anleitung für die KI

> **Einstieg:** Dieser Pfad wird über `../../SKILL.md` gewählt. Die Rahmenfragen (Angebot, Kanal, Wunschkunde, Länder, Ausschlüsse, Ansprechpartner, Menge) stehen in der Auftragsdatei `auftraege/…md` – **nicht erneut fragen.** Was dieser Pfad zusätzlich braucht, klärt Phase 1, bevor irgendetwas kostet. Hintergrund für Menschen und andere KI-Modelle: `../../wissen/06_pfad-e-commerce.md`.
>
> **Herkunft:** 1:1-Nachbau des Clay-Workbooks „Vorlage | ECOM 2.0“. Jede Clay-Spalte und ihre Code-Stelle: `docs/01_PROZESS.md`. Dazu kommen Bausteine ohne Clay-Vorbild (Shop-Profil, Mailtext, Personalisierungs-Prompt je Auftrag, Anforderungs-Prüfung); sie sind dort mit „neu, nicht in Clay“ markiert. Bewusste Abweichungen: `docs/05_ABWEICHUNGEN.md`.
>
> Alle Befehle laufen aus diesem Ordner (`pfade/e-commerce/`), mit Python ≥ 3.10 (Phase 0, Schritt 0).

## Was der Pfad tut

Aus einer **vorhandenen Shop-Liste** (CSV mit Firmenname und/oder Website) werden versandfertige Leads:

| Stufe | Clay-Tabelle | Was passiert | Filter |
|---|---|---|---|
| **1** | Import | Website finden (falls nur Name) → Startseite abrufen → KI prüft „aktiver Onlineshop?“ und, wenn ein Shop-Profil gesetzt ist, „passt der Shop zum Profil des Kunden?“ (beides Stufe 1c) → Besucherzahlen (SimilarWeb) | nur aktive, zum Profil passende Shops mit messbarem Traffic gehen weiter |
| **2** | ANREICHERUNG | Impressum → Duplikate raus (gleiche E-Mail-Domain) → Geschäftsführer-Mail suchen und prüfen, sonst info@ → Anrede → persönlicher Einstiegssatz (nach dem Personalisierungs-Prompt des Auftrags) → Videotitel | nur „Ready to Send“ kommt in die Versandlisten, mit fertiger Mail je Lead, wenn ein Mailtext gesetzt ist |

Der Pfad **findet keine Shops selbst**. Er prüft und reichert eine Liste an. Woher die Liste kommen kann: `referenzen/discovery-quellen.md`.

## Phase 0 – Einrichtung (einmalig)

0. `python3 --version` ausführen. Unter 3.10 jeden Befehl dieser Anleitung und der Builder mit `python3.12` statt `python3` aufrufen (macOS: `brew install python@3.12`). **Windows:** `py -3.12` statt `python3` (Installation: `winget install Python.Python.3.12`).
1. `cp .env.example .env` (Windows-Eingabeaufforderung: `copy .env.example .env`)
2. Schlüssel eintragen lassen. Pflicht sind **Skael** (`eak_…`) und **OpenAI** (`sk-…`, Guthaben aufgeladen). **Findymail** ist optional: eigenes Abo, sucht die Geschäftsführer-Adresse, wenn Skael keine findet. `doctor` zeigt das Restguthaben.
   - **Schlüssel nie im Chat.** Der Nutzer öffnet `.env` in diesem Ordner selbst mit einem Texteditor und trägt die Schlüssel hinter `=` ein. Du zeigst `.env` nie an und gibst keine Schlüsselzeile aus; ob die Schlüssel stimmen, prüft `doctor`. Einstellungen wie `MIN_AVR_TRAFFIC` änderst du gezielt zeilenweise, ohne die Datei auszugeben.
   - Fügt der Nutzer trotzdem einen Schlüssel in den Chat ein: nicht wiederholen, ihn bitten, ihn selbst in `.env` einzutragen, und raten, den Schlüssel beim Anbieter neu zu erzeugen.
   - Liegt im Google-Maps-Pfad schon eine `.env` mit Schlüsseln: den Nutzer bitten, die Zeilen `SKAEL_API_KEY`, `OPENAI_API_KEY` und ggf. `FINDYMAIL_API_KEY` von dort in diese `.env` zu übernehmen.
3. `python3 -m ecom doctor`. Das Ergebnis in einem Satz übersetzen. **Vor dem ersten Lauf, der etwas kostet (Phase 3), muss dort ✓ stehen:**
   - bei `SKAEL_API_KEY` und `OPENAI_API_KEY`. Ein Platzhalter aus `.env.example` zählt als ✗, `run` startet dann nicht.
   - bei **Community-Sperrliste**. Ohne sie bricht jeder Export ab. Steht dort „nicht eingerichtet … Platzhalter OWNER“, fehlt ein Einrichtungsschritt des Paket-Betreibers: Der Nutzer erfragt beim Betreiber die Adresse der Sperrliste und trägt sie als `SPERRLISTE_URL` in `.env` ein. **Nicht** `SPERRLISTE_PFLICHT=false` setzen. Steht dort „nicht ladbar“: Internetverbindung prüfen. Phase 1 und 2 gehen schon vorher, Phase 3 erst mit ✓.

## Phase 1 – Anforderungen klären (Pflicht, vor jeder Abfrage)

Diese Liste ist die einzige Quelle für die Anforderungen des E-Commerce-Pfads. Du fragst nach, **bis jeder Punkt erfüllt ist** – erst dann kostet etwas.

**Gesprächsregeln** wie im Interview (`../../wissen/02_zielgruppen-interview.md`, „Regeln für das Gespräch“): eine Frage pro Nachricht, immer mit Beispiel und einem Vorschlag. Sagt der Nutzer „weiß nicht“, einen Vorschlag machen und bestätigen lassen. Keine Fachbegriffe (Prompt, ICP, Stage, `.env` …) – die Spalte „Woher / wohin“ ist nur für dich.

### Anforderungsliste

| Nr | Anforderung | Frage an den Nutzer (wörtlich, mit Beispiel) | Woher / wohin | Pflicht |
|---|---|---|---|---|
| A1 | Angebot | – steht in der Auftragsdatei, nicht erneut fragen | → Shop-Profil-Builder; Personalisierungs-Builder, Runde 1 | ja |
| A2 | Kanal, Video ja/nein | – Auftragsdatei | → E5 | ja |
| B1–B3 | Wunschkunde, Beschreibung, Beispielshops | – Auftragsdatei | → Shop-Profil-Builder; Beispielshops zur Kontrolle im Testlauf | ja |
| D1 | Länder | – Auftragsdatei | → Shop-Profil (Region zuerst); Liste vorab filtern, wenn sie eine Länder-Spalte hat | ja |
| D2 | Ausschlüsse | – Auftragsdatei | → Shop-Profil „sofort raus“; Liste vorab filtern, wenn möglich | ja |
| D3 | Ansprechpartner (Geschäftsführung oder info@) | – Auftragsdatei | → Exportliste 1 und/oder 2 | ja |
| D4 | Menge, Budget | – Auftragsdatei | → Größe des Testlaufs, Kostenrahmen, E3 | ja |
| E1 | Shop-Liste | Steht in der Auftragsdatei schon, dass es eine Liste gibt (C2): nur „Schick mir die Datei oder sag mir, wo sie liegt.“ Sonst: „Hast du schon eine Liste der Shops, die ich prüfen soll?“ – „Zum Beispiel eine Excel- oder CSV-Datei mit Shopnamen oder Websites, etwa ein Export aus einem Shop-Verzeichnis.“ | → Phase 2 (`import`). Dabei auf Spalten für Shopsystem und Land achten (E2, D1). **Excel-Datei (`.xlsx`):** den Nutzer bitten, sie in Excel als „CSV UTF-8 (durch Trennzeichen getrennt)“ zu speichern; `import` lehnt `.xlsx` mit dieser Anleitung ab. **Keine Liste:** ehrlich sagen, dass der Pfad noch keine Shops selbst findet; Quellen aus `referenzen/discovery-quellen.md` nennen; die Antworten trotzdem in der Auftragsdatei sichern | ja |
| E2 | Shopsystem | „Sollen es nur Shops mit einem bestimmten Shopsystem sein?“ – „Zum Beispiel nur Shopware oder nur Shopify – oder ist das egal?“ | Der Pfad erkennt das Shopsystem **nicht selbst**. Es muss aus der Liste kommen, z. B. aus einem Export eines Technologie-Verzeichnisses mit Spalte für das Shopsystem. Hat die Liste eine Spalte dafür: vor dem Import filtern. Sonst offen sagen und eine Folgefrage mit Vorschlag stellen: „Dann sind auch Shops mit anderen Systemen dabei. Ist das okay, oder besorgst du eine Liste mit Shopsystem-Spalte, z. B. einen Export aus einem Shop-Verzeichnis?“ (Quellen: `referenzen/discovery-quellen.md`). Antwort in die Auftragsdatei. Bleibt die Liste ungefiltert, darf die Mail das Shopsystem des Empfängers nicht voraussetzen (`prompts/personalisierung_builder.md`) | ja („egal“ ist eine Antwort) |
| E3 | Mindestgröße | „Sollen nur Shops mit nennenswert vielen Besuchern rein?“ – „Zum Beispiel ab ca. 5.000 Besuchen im Monat – oder egal, Hauptsache der Shop hat überhaupt messbare Besucher.“ | → `.env` (Stellschrauben unten): „egal“ = Standard 1/1; „ab ca. 5.000“ = `MIN_AVR_TRAFFIC=5000` **und** `MIN_MAX_TRAFFIC_3MO=5000`; „auch ganz kleine ohne Besucherdaten“ = beide 0 | ja |
| E4 | Shop-Profil oder bewusst ohne | „Soll ich jeden aktiven Onlineshop aus der Liste nehmen, oder nur Shops, die zu deiner Beschreibung passen?“ – „Zum Beispiel nur Modeshops für Endkunden aus Deutschland, keine reinen Marktplatz-Händler.“ | „nur passende“ → `prompts/shopprofil_builder.md` → Datei `auftraege/<auftrag>_shopprofil.txt` → `python3 -m ecom set-prompt shopprofil <datei>`. „alle“ → `python3 -m ecom set-prompt shopprofil --ohne` | ja. Ein Profil ist nötig, sobald B2, D1 oder D2 etwas einschränken, das auf der Startseite sichtbar ist (Sprache, Währung, Sortiment, Endkunden/Firmenkunden, Marktplatz-Händler). „ohne“ nur, wenn der Kunde wirklich jeden aktiven Shop will |
| E5 | Video | „Willst du die Shops mit einem persönlichen Video anschreiben?“ – „Dann schreibe ich zu jedem Shop einen passenden Videotitel dazu.“ | aus A2, wenn dort beantwortet → `.env` `DO_VIDEO_TITLE` | ja |
| E6 | Mailtext und persönlicher Einstiegssatz | „Hast du schon einen Mailtext, den du an die Shops schicken willst?“ – „Kopier ihn einfach hier rein. Wenn nicht, schreiben wir ihn zusammen – ich stelle dir dazu ein paar kurze Fragen.“ | → `prompts/personalisierung_builder.md` (Runden 1–3) → `auftraege/<auftrag>_mailtext.txt` und `auftraege/<auftrag>_personalisierung.txt` → `python3 -m ecom set-mailtext <datei>` und `python3 -m ecom set-prompt personalisierung <datei>`. Die Beispiel-Mail aus `set-mailtext` dem Nutzer zeigen | ja, solange `DO_PERSONALISIERUNG=true` (Standard) |
| E7 | Findymail | „Hast du zufällig einen Zugang bei Findymail?“ – „Nur falls ja: Das ist ein zweiter Dienst, der E-Mail-Adressen der Geschäftsführung findet. Ohne geht es auch.“ | → `.env` `FINDYMAIL_API_KEY`; nur fragen, wenn der Schlüssel leer ist | nein |

Fehlt eine Angabe A1–D4 in der Auftragsdatei, weil der Nutzer ohne Interview eingestiegen ist: die Frage wörtlich aus `../../wissen/02_zielgruppen-interview.md` stellen.

### So arbeitest du die Liste ab

1. Auftragsdatei lesen. Was dort steht, gilt als beantwortet.
2. Die offenen E-Punkte in dieser Reihenfolge fragen: E1 → E2 → E3 → E5 → E7. Danach zusammenfassen und bestätigen lassen.
3. **E4** mit `prompts/shopprofil_builder.md`: Der Builder übernimmt A1, B1–B3, D1 und D2 und fragt nur, was fehlt. Ergebnis in eigenen Worten zusammenfassen und bestätigen lassen.
4. **E6** mit `prompts/personalisierung_builder.md`: Angebot und Problem, Mailtext (mitgebracht oder gemeinsam geschrieben), Aufhänger. Den fertigen Mailtext zeigen und so lange anpassen, bis der Nutzer ihn bestätigt.
5. Jede Antwort sofort in die Auftragsdatei schreiben (Ergänzung unten) und „Offene Punkte“ nachführen. Die Dateien aus den Buildern liegen in `auftraege/` des Arbeitsordners. Arbeitest du im Skill-Ordner (`lead-scraper/`), heißt der Pfad aus diesem Ordner `../../auftraege/<auftrag>_….txt`; wurde der Pfad in einen eigenen Arbeitsordner kopiert (`../../SKILL.md`, Schritt 1), `../auftraege/<auftrag>_….txt`. In einem frischen Paket fehlt der Ordner: vor der ersten Datei anlegen (`mkdir -p ../../auftraege` bzw. `mkdir -p ../auftraege`).
6. `python3 -m ecom status` ausführen und den Block „Anforderungen“ prüfen.

**Technische Sperre:** `python3 -m ecom run` prüft vor der ersten Stufe, ob die Anforderungen erfüllt sind:

- Enthält der Lauf Stufe `1c`, `1d` oder `1e`, muss das Shop-Profil entschieden sein (Profil gesetzt oder `--ohne`). Traffic und Übergabe hängen am Profil-Ergebnis.
- Enthält er Stufe `2e` und ist `DO_PERSONALISIERUNG=true`, müssen Personalisierungs-Prompt und Mailtext gesetzt sein.

Fehlt etwas, bricht der Lauf mit „Anforderung fehlt“ und Exit-Code 2 ab, bevor etwas kostet. Die Meldung nennt den passenden Builder. Nicht umgehen, sondern den Punkt mit dem Nutzer klären.

### Fertig, wenn

- die Auftragsdatei keine offenen Punkte mehr hat (Ausnahme unten),
- jeder Block zusammengefasst und vom Nutzer bestätigt ist,
- `python3 -m ecom status` im Block „Anforderungen“ überall ✓ zeigt (bzw. „– nicht nötig“),
- der Nutzer die Beispiel-Mail aus `set-mailtext` gesehen hat (entfällt nur, wenn kein Mailtext nötig ist).

**Ausnahme „Vor dem Versand offen“:** Ein fehlender Datenschutz-Link oder ein Pflichtteil der Mail, den der Nutzer ausdrücklich nicht will, steht in der Auftragsdatei unter „Vor dem Versand offen“ statt unter „Offene Punkte“ (Regeln: `prompts/personalisierung_builder.md`, Pflichtteile). Diese Punkte blockieren den Testlauf nicht, denn der Pfad verschickt nichts. Beim Export (Phase 5) nennst du sie einmal.

Erst dann der Testlauf (Phase 3, `--limit 10`). Der Vollstart erst, wenn der Nutzer Testergebnis, Beispiel-Mails und Kosten freigegeben hat.

### Ergänzung der Auftragsdatei

An die Auftragsdatei aus dem Interview anhängen:

```markdown
## E-Commerce (Phase 1)
Shop-Liste (E1): <Datei>, <Anzahl> Zeilen
Shopsystem (E2): egal | nur Shopware, Liste vorab gefiltert | nur Shopware gewünscht, Liste ohne Spalte: andere Systeme sind okay / Nutzer besorgt Liste mit Spalte
Mindestgröße (E3): egal (Standard) | ab ca. 5.000 Besuchen/Monat
Shop-Profil (E4): auftraege/<auftrag>_shopprofil.txt | bewusst ohne
Mailtext (E6): auftraege/<auftrag>_mailtext.txt
Personalisierung (E6): auftraege/<auftrag>_personalisierung.txt
Video (E5): ja | nein
Findymail (E7): vorhanden | nein
Offene Punkte: –
Vor dem Versand offen: – (z. B. Datenschutz-Link fehlt; Abmeldesatz vom Nutzer abgelehnt)
```

## Phase 2 – Liste laden

```bash
python3 -m ecom import <liste.csv>
```

- **Ablage:** Die Liste des Nutzers und jede gefilterte Kopie gehören nach `data/` in diesem Ordner, z. B. `data/<auftrag>_liste.csv`. `data/` wird nie weitergegeben oder eingecheckt; Verzeichnis-Exporte enthalten oft personenbezogene Spalten (z. B. E-Mails).
- **Vorher filtern**, wenn die Liste passende Spalten hat: Shopsystem (E2), Land (D1), Ausschlüsse (D2). Die gefilterte Kopie ebenfalls unter `data/` speichern und diese importieren. Dem Nutzer sagen, wie viele Zeilen dabei rausfielen.
- Erkannt werden Spalten wie `Firmenname`/`Company`/`Brand Name` und `Website`/`Domain`/`URL`, auch Exporte von Technologie-Verzeichnissen (z. B. BuiltWith: `Company` und `Location on Site`, die auch Shops auf Subdomains wie `shop.firma.de` zeigt). Sonst mit `--name-spalte` bzw. `--website-spalte` angeben. Prüfe in der Ausgabe, dass eine Website-Spalte erkannt wurde: Ohne Website sucht die KI jede Website einzeln, das kostet mehr.
- **Kodierung:** UTF-8, eine Excel-CSV „CSV (Trennzeichen-getrennt)“ (Windows-1252) und „Unicode-Text“ liest `import` selbst. Ist die Datei nicht UTF-8, meldet es die erkannte Kodierung: dann in zwei, drei Firmennamen die Umlaute prüfen. `.xlsx`, `.xls` und `.numbers` lehnt es mit Exit-Code 2 und Anleitung ab (als „CSV UTF-8“ speichern lassen).
- Ein erneuter Import derselben Liste legt nichts doppelt an. `www.shop.de`, `https://www.shop.de` und `shop.de` gelten als derselbe Shop.
- Dem Nutzer sagen: wie viele Shops geladen wurden und wie viele davon keine Website haben (`import` meldet „Davon ohne Website: n“). Für diese sucht die KI die Website, das kostet etwas mehr.

## Phase 3 – Testlauf (Pflicht vor dem Vollstart)

```bash
python3 -m ecom run --stage 1 --limit 10
python3 -m ecom run --stage 2
python3 -m ecom status
python3 -m ecom export          # ohne --mark: die Test-Leads kommen beim echten Export wieder
```

**1. Shop-Prüfung übersetzen**, keine Tabellen zeigen. Beispiel: „Von 10 Shops sind 8 aktive Onlineshops, 6 passen zu deiner Beschreibung, 5 davon haben messbare Besucher. Für 4 habe ich eine E-Mail gefunden, 3 sind versandfertig.“

- Zwei, drei Beispiele nennen, davon mindestens ein aussortierter Shop mit Grund, z. B. „passt nicht zum Shop-Profil: verkauft nur über Amazon“.
- Stehen Beispielshops aus B3 in der Liste: prüfen, ob sie durchgekommen sind.

So siehst du Beispiele, je Shop mit Prüfergebnis, Profil-Grund, Besuchen und Fehler (braucht kein `sqlite3`, das unter Windows fehlt):

```bash
python3 -m ecom status --shops 20
```

- **Fehler:** `status` zeigt je Stufe „mit Fehler / liegen gebl.“ und den häufigsten Grund. Den Grund in einem Satz übersetzen. Liegen gebliebene Zeilen (drei Fehlversuche) laufen erst nach `python3 -m ecom fehler-zuruecksetzen` wieder.
- **Exit-Codes von `run`:** 2 = nichts gestartet bzw. abgebrochen, weil eine Anforderung fehlt, ein Schlüssel noch Platzhalter ist oder ein Dienst den Zugang ablehnt (Meldung übersetzen, Ursache mit dem Nutzer klären). 1 = in einer Stufe ist jede Zeile gescheitert (Meldung nennt den Grund).

**2. Fertige Mails zeigen.** Aus Liste 1 bzw. 2 des Exports zwei, drei Leads nehmen und je `Betreff` und `Mailtext` vollständig zeigen, so wie sie verschickt würden. Dann fragen: „Passt das so?“

Sagt der Nutzer „nein“, eine Frage: was nicht passt. Dann:

| Was nicht passt | Anpassen | Neu laufen lassen |
|---|---|---|
| der persönliche Einstiegssatz | Personalisierungs-Datei ändern, `python3 -m ecom set-prompt personalisierung <datei>` (setzt die Sätze nicht exportierter Leads zurück) | `run --stage 2e`, dann `run --stage 2g`, dann `export` |
| der Mailtext selbst | Mailtext-Datei ändern, `python3 -m ecom set-mailtext <datei>` | `export`. Meldet `set-mailtext` den Hinweis zur Personalisierung: zusätzlich wie in der Zeile darüber |
| Shops falsch aussortiert oder durchgelassen | Shop-Profil-Datei schärfen, `python3 -m ecom set-prompt shopprofil <datei>` (setzt die Profil-Ergebnisse aller Shops zurück, die noch nicht übergeben oder noch nicht exportiert sind, also auch die aus dem Testlauf) | `run --stage 1c`, `1d`, `1e`, dann `2g`. Lehnt das neue Profil einen Shop aus dem Testlauf ab, fällt er aus Liste 1 und 2 heraus und steht mit Grund in Liste 3 |

Danach wieder zeigen und fragen, bis der Nutzer zustimmt. Nur einzelne Stufen neu laufen lassen, nicht `--stage 1` ohne `--limit`: Das würde die ganze Liste abrufen.

**3. Kosten hochrechnen** (`docs/01_PROZESS.md`, Abschnitt „Kosten“) und **vor dem Vollstart bestätigen lassen**.

## Phase 4 – Vollstart

```bash
python3 -m ecom run --stage all
```

- **Fortsetzbar:** Nach einem Abbruch denselben Befehl erneut ausführen. Erledigtes wird übersprungen. Zeilen mit drei Fehlversuchen bleiben liegen, bis `python3 -m ecom fehler-zuruecksetzen` sie wieder freigibt (kostet nichts).
- **Einzelne Stufen:** `--stage 1a … 1e`, `2a … 2g`.
- Die Anforderungs-Prüfung läuft bei jedem `run`. Nach Phase 1 und 3 ist sie erfüllt.

## Phase 5 – Export mit Sperrliste

```bash
python3 -m ecom export
```

| Datei | Inhalt | Verwenden |
|---|---|---|
| `1_geschaeftsfuehrer_….csv` | Ready to Send, E-Mail der Geschäftsführung; mit `Betreff` und `Mailtext`, wenn ein Mailtext gesetzt ist | Versand (erste Wahl) |
| `2_info_….csv` | Ready to Send, nur info@-Adresse; Spalten wie Liste 1 | Versand, wenn gewünscht |
| `3_aussortiert_….csv` | kein aktiver Shop, passt nicht zum Shop-Profil (auch Testlauf-Shops, die ein nachgeschärftes Profil ablehnt), kein Traffic, keine E-Mail, Duplikat, mit E-Mail, aber nicht versandfertig (z. B. persönlicher Satz dreimal gescheitert) – mit Grund und letzter Fehlermeldung | nur Nachvollziehbarkeit |
| `4_gesperrt_sperrliste_….csv` | Domain auf der Community-Sperrliste | **nie anschreiben** |
| `shops_archiv_….json` | alle Rohdaten | Bestand, ohne erneut abzufragen |

- Nach der Übergabe an das Versandtool `python3 -m ecom export --mark` ausführen. Sonst kommen dieselben Leads beim nächsten Export erneut. Die Meldung trennt versandfertige (Liste 1 und 2) und gesperrte Leads (Liste 4); für die vier Zahlen unten die versandfertigen nehmen.
- Am Ende vier Zahlen nennen:
  - geprüfte Shops,
  - übergebene Shops,
  - versandfertige Leads,
  - wegen der Sperrliste aussortierte Firmen.
- Einmal kurz auf § 7 UWG hinweisen (`../../wissen/08_versand-und-recht.md`). Stehen in der Auftragsdatei Punkte unter „Vor dem Versand offen“, sie im selben Satz nennen.

## Stellschrauben

| Einstellung (`.env`) | Clay-Spalte | Standard | Wann ändern |
|---|---|---|---|
| `MIN_AVR_TRAFFIC`, `MIN_MAX_TRAFFIC_3MO`, `TRAFFIC_MODE` | `MIN AVR TRAFFIC`, `MIN AVR H T 3 MO`, `MODE AND/OR` | 1, 1, OR | nach E3: höher setzen, wenn nur größere Shops gewünscht sind (z. B. 5000 Besuche/Monat); `AND` = beide Schwellen müssen erfüllt sein |
| `DO_PERSONALISIERUNG`, `DO_VIDEO_TITLE` | `Personalisierung AI`, `Cleaned Video Title` | an | aus, wenn kein Video- bzw. Kompliment-Outreach geplant ist (spart Kosten; Ready to Send zählt sie dann nicht). Ohne Personalisierung entfällt E6 |
| `USE_FINDYMAIL` | `Find Work Email` | an (wirkt nur mit Schlüssel) | – |

**Schwelle nachträglich ändern:** `.env` anpassen, dann `python3 -m ecom run --stage 1e`. Das rechnet `SEND` neu, ohne neue Abfragen und ohne Schlüssel (ebenso `--stage 2g`). Bereits übergebene Shops bleiben in der Anreicherung.

**Anforderungen nachträglich ändern** (stehen in der Datenbank, Tabelle `meta`, nicht in `.env`):

| Befehl | Setzt zurück | Danach |
|---|---|---|
| `python3 -m ecom set-prompt shopprofil <datei>` | Profil-Ergebnisse, Fehlversuche und Fehlermeldung aller aktiven Shops, die noch nicht übergeben oder noch nicht exportiert sind; deren Leads verlieren „Ready to Send“. Nennt die Anzahl | `run --stage 1c`, `1d`, `1e`, dann `2g` |
| `python3 -m ecom set-prompt shopprofil --ohne` | bewusste Entscheidung „jeder aktive Shop zählt“; alte Profil-Ergebnisse derselben Shops fallen weg | `run --stage 1d`, `1e`, dann `2g` |
| `python3 -m ecom set-prompt personalisierung <datei>` | Einstiegssätze, „Ready to Send“, Fehlversuche und Fehlermeldung aller noch nicht exportierten Leads mit Satz; nennt die Anzahl | `run --stage 2e`, dann `2g` |
| `python3 -m ecom set-mailtext <datei>` | nichts; prüft den Text und zeigt eine Beispiel-Mail. Nutzt der Personalisierungs-Prompt `{{Mailtext}}` und gibt es schon Sätze, weist er darauf hin, `set-prompt personalisierung` erneut auszuführen | `export` |

## Fallstricke

| Thema | Was zu beachten ist |
|---|---|
| „Anforderung fehlt“ | `run` bricht vor der ersten Stufe mit Exit-Code 2 ab, es entstehen keine Kosten. `status` zeigt im Block „Anforderungen“, was fehlt, und nennt den Builder. Phase 1 nachholen, nicht umgehen |
| Mailtext abgelehnt oder mit Hinweis | `set-mailtext` bricht bei Fehlern mit Exit-Code 2 ab und speichert nichts; Hinweise speichert es. Welche Fehler und Hinweise es gibt und welche Platzhalter erlaubt sind: `../../wissen/07_lead-ausgabe-und-spalten.md`, Abschnitt E-Commerce. Fehler selbst beheben, Hinweise dem Nutzer in einem Satz übersetzen |
| Einstiegssatz kleingeschrieben | gewollt: Der Satz setzt die Anrede-Zeile fort („Hallo Herr Müller,“ → „bei Ihnen …“). Clay-Konvention |
| Clay-Personalisierungsprompt | `prompts/personalisierung.txt` ist für deutsche Beratungen und Agenturen geschrieben, nicht für Shops. Er wird für Läufe nicht verwendet und dient nur als Struktur-Vorlage. Läufe nutzen den Prompt des Auftrags aus der Datenbank |
| Traffic-Schwelle nur halb angehoben | bei `TRAFFIC_MODE=OR` reicht eine erfüllte Schwelle. Wer nur `MIN_AVR_TRAFFIC` anhebt und `MIN_MAX_TRAFFIC_3MO=1` lässt, filtert praktisch nichts. Beide anheben |
| Shops ohne SimilarWeb-Daten | kleine Shops haben oft keine Daten und fallen bei Schwelle 1 raus (wie in Clay). Abfrage ohne Daten kostet nichts |
| Website ohne Text | per JavaScript aufgebaute Shops liefern teils leeren Text; dann keine Shop-Prüfung, Grund steht in Liste 3 |
| Skael-Zwischenspeicher | identische Anfragen liefern 20 Minuten lang das alte Ergebnis, auch Fehler |
| Fehler in einer Zeile | zählt `attempts` hoch, nach 3 Versuchen bleibt die Zeile liegen. `status` zeigt je Stufe „mit Fehler / liegen gebl.“ mit dem häufigsten Grund, `status --shops` den Fehler je Shop, Liste 3 die letzte Fehlermeldung. Scheitert in einer Stufe jede Zeile, endet `run` mit Exit-Code 1. Ursache beheben, dann `python3 -m ecom fehler-zuruecksetzen` und denselben `run`-Befehl erneut |
| Zugang abgelehnt | Lehnt ein Dienst Schlüssel oder Guthaben ab (Skael/OpenAI/Findymail HTTP 401, 402, 403, Findymail-Abo pausiert, OpenAI „insufficient_quota“), bricht `run` die Stufe sofort ab (Exit-Code 2) und zählt keinen Fehlversuch. Schlüssel bzw. Guthaben mit dem Nutzer klären, dann denselben Befehl erneut. Findymail: alternativ `USE_FINDYMAIL=false`. Ein Platzhalter-Schlüssel aus `.env.example` stoppt `run` schon vor der ersten Abfrage |
| Windows | `py -3.12` statt `python3` (Phase 0). Die Ausgabe ist auch bei umgeleiteter Konsole lesbar (UTF-8). Das Programm `sqlite3` fehlt dort, deshalb `status --shops` |
| Duplikate | Shops mit derselben E-Mail-Domain (z. B. mehrere Länder-Shops einer Firma) werden nur einmal angeschrieben |
| Clay-Änderungen | wird das Workbook geändert: Export neu ziehen (`docs/clay_export_ecom_2_0.json`), Unterschiede in `docs/01_PROZESS.md` und im Code nachziehen, `CHANGELOG.md` ergänzen |

## Code-Aufbau

| Datei | Inhalt |
|---|---|
| `ecom/config.py` | Einstellungen aus `.env`, Freemail-Liste, Debounce-Codes |
| `ecom/clients.py` | Skael, OpenAI, Findymail (aus dem Google-Maps-Pfad übernommen, plus `webtraffic` und am Dateiende die Erkennung von Zugangsfehlern, `ZugangGesperrt`) |
| `ecom/transforms.py` | alle Clay-Formeln, jede Funktion nennt ihre Spalte |
| `ecom/llm.py` | die KI-Aufrufe: fünf Clay-Spalten (Prompts wörtlich in `prompts/`) und die Shop-Profil-Prüfung (neu). Shop-Profil- und Personalisierungs-Prompt kommen aus der Datenbank |
| `ecom/pipeline.py` | Stufen 1a–1e (1c mit Shop-Profil) und 2a–2g; `fehlende_anforderungen` prüft vor jedem Lauf die Anforderungen |
| `ecom/mailtext.py` | Mailtext prüfen (Fehler, Warnungen) und je Lead füllen; genutzt von `set-mailtext` und `export` |
| `ecom/db.py` | SQLite: `shops` (= Import, plus Shop-Profil-Spalten), `anreicherung` (= ANREICHERUNG), `meta` (Shop-Profil, Personalisierung, Mailtext) |
| `ecom/export.py` | CSV-Listen (mit `Betreff`/`Mailtext`, wenn gesetzt) und JSON-Archiv, Sperrlisten-Abgleich |
| `ecom/cli.py` | `import`, `set-prompt`, `set-mailtext`, `run`, `status` (`--shops N`), `fehler-zuruecksetzen`, `export`, `doctor` |
| `prompts/shopprofil_builder.md` | Anleitung für dich: Shop-Profil erfragen und bauen (E4) |
| `prompts/personalisierung_builder.md` | Anleitung für dich: Mailtext und Personalisierungs-Prompt erfragen und bauen (E6), Freigabe nach dem Testlauf |
| `prompts/shopprofil.schema.json` | Antwortschema der Shop-Profil-Prüfung (`is_icp`, `confidence`, `reason`) |
| `beispiel/shopprofil_beispiel.txt`, `beispiel/personalisierung_beispiel.txt`, `beispiel/mailtext_beispiel.txt` | Beispiele für einen erfundenen Absender |
| `tests/test_offline.py` | ganzer Durchlauf mit Attrappen, kostet nichts und liest keine Schlüssel aus `.env`: `python3 -m unittest discover -s tests` |

Konventionen wie im Google-Maps-Pfad:

- Fehler schreiben nie ins „erledigt“-Feld.
- Jede Stufe bearbeitet nur leere Zielfelder.
- Clay-Prompts stehen nur in `prompts/`. Shop-Profil, Personalisierungs-Prompt und Mailtext des Auftrags liegen als Datei in `auftraege/` und in der Datenbank (`meta`), nie im Code.
- Nach Code-Änderungen die Tests laufen lassen.
