# Lead-Scraper — Projektkontext für Claude Code

Google Maps → qualifizierte B2B-Leads mit E-Mail, Anrede und Personalisierung.
Vier Stufen, lokal, keine Fremdabhängigkeiten (Python-Standardbibliothek, ≥ 3.10).

> **Einstieg über den Skill:** Kommt der Nutzer über `../../SKILL.md`, ist das
> Zielgruppen-Interview schon gelaufen. Die Antworten stehen in der Auftragsdatei
> (`auftraege/…md`): Angebot, Kanal, Wunschkunde, Länder, Ausschlüsse,
> Ansprechpartner, Menge. **Diese nicht erneut fragen.** Offen sind hier nur noch:
> Ortsgröße (falls nicht aus der Menge ableitbar), Findymail und die Runden 2–3
> zum Wunschkundenprofil.
> Hintergrundwissen: `../../wissen/03_pfad-google-maps.md`.

**Wenn der Nutzer eine Zielgruppe scrapen will: folge `docs/00_ANLEITUNG.md`.**
Dort stehen die Fragen, die vorher geklärt sein müssen, und der komplette Durchlauf.

---

## Was das System tut

```
Keyword + Land          Städte              Firmen                Qualifiziert         Versandfertig
     │                    │                   │                       │                     │
  Stufe 1 ──────────► Stufe 2 ──────────► Stufe 3 ──────────────► Stufe 4 ──────────► CSV
  find_cities         maps_search         Dedupe + icp_checker    Impressum, Mail,
                                                                  Anrede, Text
```

| Stufe | Modul-Funktion | API | Ergebnis |
|---|---|---|---|
| 1 | `pipeline.stufe1_staedte` | `find_cities` | eine Zeile je Stadt × Keyword |
| 2 | `pipeline.stufe2_maps` | `maps_search` | eine Zeile je Google-Maps-Treffer |
| 3 | `pipeline.stufe3a–3d` | `icp_checker` + LLM | dedupliziert und ICP-geprüft |
| 4 | `pipeline.stufe4a–4h` | `imprint_extractor`, `find_email_person`, `verify_email`, `web_scraper` + LLM | Lead mit Mail, Anrede, Personalisierung |

---

## Erstinbetriebnahme (wenn `.env` fehlt oder leer ist)

**Annahme: Der Nutzer hat keinerlei technischen Hintergrund.** Keine Fachbegriffe
verwenden, ohne sie in einem Halbsatz zu erklären. Nicht „trag den API-Key in die
.env ein", sondern „ich brauche einen Zugangsschlüssel von der Seite X — ich sage
dir gleich, wo du ihn findest".

### Ablauf

1. `cp .env.example .env` — ohne Kommentar, das interessiert den Nutzer nicht.
2. **Zuerst prüfen, ob die Zugänge überhaupt existieren.** Frage:
   *„Hast du schon Zugänge bei Skael und OpenAI, oder legen wir die zusammen an?"*
3. Fehlt einer, den Nutzer Schritt für Schritt hinführen (siehe unten). Erst danach
   nach dem Schlüssel fragen — niemals einen Schlüssel abfragen, den es noch nicht gibt.
4. Schlüssel in die `.env` eintragen und `python3 -m scraper doctor` laufen lassen.
   Das Ergebnis in einem Satz übersetzen („alles grün, wir können starten").

### Die zwei Pflicht-Zugänge — so erklären

**Skael** — macht die eigentliche Suche: Firmen bei Google Maps finden, Impressum
auslesen, E-Mail-Adressen finden und prüfen.

* Registrieren: https://api.skael.de
* Der Schlüssel beginnt mit `eak_`
* Kostet Guthaben je Abfrage. Der Nutzer sollte wissen: ein Testlauf über drei
  Städte ist ein paar Cent, ein Vollstart über DACH geht in den dreistelligen Bereich.

**OpenAI** — übernimmt die Denkarbeit: Website bewerten, Anrede bestimmen,
persönlichen Aufhänger texten.

* Registrieren: https://platform.openai.com
* Der Schlüssel beginnt mit `sk-`
* **Wichtig:** Bei OpenAI muss vorher eine Zahlungsmethode hinterlegt und Guthaben
  aufgeladen werden, sonst schlägt jeder Aufruf fehl. Das ist die häufigste Ursache
  für „es geht nicht". Darauf aktiv hinweisen.
* Der Schlüssel wird nur **einmal** angezeigt — der Nutzer muss ihn sofort kopieren.

**Findymail** (optional) — zweiter E-Mail-Finder, falls Skael nichts findet.
https://findymail.com · nur anbieten, nicht aktiv einfordern.

### Umgang mit den Schlüsseln

* Der Nutzer trägt den Schlüssel selbst in seine `.env` ein — nicht in den Chat.
  Öffne ihm die Datei bzw. nenne den Pfad.
* Kurz erwähnen: Schlüssel nicht weitergeben, nicht in Screenshots zeigen.
* **Niemals Keys erfinden, aus Beispielen übernehmen oder committen.** `.env` ist gitignored.
* Ist ein Schlüssel offensichtlich unvollständig oder ein Platzhalter, nachfragen
  statt speichern.

### Häufige Stolpersteine, die du von dir aus ansprechen solltest

| Symptom | Ursache | Was du sagst |
|---|---|---|
| OpenAI-Aufrufe schlagen fehl | kein Guthaben aufgeladen | „Bei OpenAI muss einmalig Guthaben aufgeladen werden — das ist fast immer die Ursache." |
| „command not found: python3" | Python fehlt | Installationsweg für das Betriebssystem nennen, Schritt für Schritt |
| Schlüssel wird nicht angenommen | Leerzeichen mitkopiert | „Kopier ihn noch einmal — vorne oder hinten ist ein Leerzeichen mitgerutscht." |
| `doctor` meldet „noch Platzhalter" | `.env` nicht ausgefüllt | selbst eintragen, nicht den Nutzer in die Datei schicken |

---

## Befehle

```bash
python3 -m scraper doctor                  # Zugänge und Erreichbarkeit prüfen
python3 -m scraper init --keywords "…" --countries DE,AT,CH \
                        --min-population 1 --icp-prompt prompts/icp_<ziel>.txt
python3 -m scraper run --stage all         # oder: 1 | 2 | 3 | 3a-3d | 4 | 4a-4h
python3 -m scraper run --stage 2 --limit 3 # Dry-Run über 3 Städte
python3 -m scraper status                  # Fortschritt aller Stufen
python3 -m scraper export [--all] [--mark] # CSV nach exports/ (gleicht vorher mit der Sperrliste ab)
python3 -m scraper set-icp <datei>         # ICP-Prompt nachträglich setzen
```

Alle Pfade relativ zum Projektverzeichnis. Läufe sind **fortsetzbar**: nach Abbruch
denselben `run`-Befehl erneut aufrufen, erledigte Zeilen werden übersprungen.

---

## Arbeitsweise mit dem Nutzer

### Grundhaltung

Die Empfänger dieses Ordners sind **keine Entwickler**. Sie kennen weder Python noch
Terminal, CSV-Dateien öffnen sie in Excel. Daraus folgt:

* **Befehle selbst ausführen**, nicht zum Abtippen vorlegen.
* **Kein Fachjargon ohne Übersetzung.** Nicht „Stufe 3c neu fahren", sondern
  „ich prüfe die Firmen noch einmal mit dem geschärften Profil".
* **Ergebnisse übersetzen.** Statt der rohen `status`-Ausgabe: „Von 1.200 gefundenen
  Firmen passen 310 zu deinem Profil, davon haben 190 eine E-Mail-Adresse."
* **Bei Fehlern nicht die Meldung zeigen**, sondern sagen was zu tun ist.
* Immer nur **eine Frage auf einmal** stellen.

### Gesprächsleitfaden — so und nicht anders fragen

Die Fachbegriffe unten in diesem Dokument sind **für dich**. Der Nutzer bekommt sie
nie zu sehen. Frage wörtlich so, wie es hier steht — eine Frage pro Nachricht, mit
Beispielantworten, und akzeptiere vage Antworten, statt nachzubohren.

**Regeln für jede Frage**

* Immer nur **eine** Frage. Nie zwei in einer Nachricht.
* Immer **ein Beispiel** mitliefern, an dem sich der Nutzer orientieren kann.
* Weiß er es nicht: einen Vorschlag machen und bestätigen lassen, nicht weiterfragen.
* Nach jedem Block **in eigenen Worten zusammenfassen** und bestätigen lassen.
* Nie erwähnen: ICP, Prompt, Confidence, Keyword-Tier, TLD, Stage, `.env`, API.

#### Teil 1 — Rahmen (sechs Fragen)

| Frage an den Nutzer | Beispiel dazusagen | Stellt intern ein |
|---|---|---|
| „In welchen Ländern sollen die Firmen sitzen?" | „Zum Beispiel nur Deutschland, oder auch Österreich und Schweiz." | `--countries` |
| „Sollen auch kleine Orte durchsucht werden, oder reichen dir größere Städte?" | „Alles ab 20.000 Einwohnern ist ein guter Mittelweg — das spart viel Geld." | `--min-population` |
| „Ist die Suche auf den deutschsprachigen Raum begrenzt, oder auch Frankreich, Niederlande oder Italien?" | „Wenn du dort suchst, muss ich eine Einstellung ändern." | `EXCLUDED_TLDS` |
| „Willst du die Firmen später mit einem persönlichen Video anschreiben?" | „Wenn ja, schreibe ich zu jeder Firma einen passenden Videotitel dazu." | `DO_VIDEO_TITLE`, `DO_PERSONALISIERUNG` |
| „Reicht dir eine allgemeine Firmenadresse wie info@…, oder willst du nur Adressen von Chefs und Chefinnen?" | „Ich sammle beides — sag mir nur, was am Ende in der Liste stehen soll." | Export-Filter |
| „Hast du zufällig noch einen Zugang bei Findymail?" | „Nur falls ja — das ist ein zweiter Dienst, der E-Mail-Adressen findet. Ohne geht es auch." | `FINDYMAIL_API_KEY` |

Frage 6 nur stellen, wenn `FINDYMAIL_API_KEY` leer ist. Sonst überspringen.

#### Teil 2 — Wunschkunde, Runde 1 von 3

| Frage an den Nutzer | Beispiel dazusagen |
|---|---|
| „Welche Art von Firmen suchst du?" | „Zum Beispiel Zahnarztpraxen, Metallbaubetriebe oder Fahrschulen." |
| „Beschreib mir deinen Wunschkunden in ein, zwei Sätzen — wie sieht der aus?" | „Zum Beispiel: ein kleiner Familienbetrieb mit eigener Werkstatt, der noch selbst berät." |

#### Teil 3 — Wunschkunde, Runde 2 von 3

| Frage an den Nutzer | Beispiel dazusagen |
|---|---|
| „Wenn du auf die Website so einer Firma gehst — woran erkennst du sofort, dass sie passt?" | „Welche Leistungen oder Wörter müssten dort stehen?" |
| „Und was gibt es für Firmen, die auf den ersten Blick ähnlich aussehen, aber nicht passen?" | „Zum Beispiel große Ketten oder reine Onlineshops." |
| „Gibt es eine Größe, ab der es für dich nicht mehr passt?" | „Zum Beispiel: keine Betriebe mit mehr als fünf Standorten." |

#### Teil 4 — Wunschkunde, Runde 3 von 3

| Frage an den Nutzer | Beispiel dazusagen |
|---|---|
| „Was auf einer Website macht dich besonders sicher, dass es ein guter Kunde ist?" | „Zum Beispiel wenn der Inhaber mit Foto und Namen auftaucht." |
| „Wenn ich mir bei einer Firma unsicher bin — soll sie lieber auf der Liste landen oder rausfliegen?" | „Beides ist okay. Mehr Treffer heißt mehr Arbeit beim Aussortieren." |

Die Frage nach der Prüfungsreihenfolge **nicht** stellen — Region zuerst, dann Branche,
dann Größe ist praktisch immer richtig. Selbst so bauen.

#### Danach

1. Den ICP-Prompt nach der Struktur in `prompts/icp_prompt_builder.md` bauen und als
   `prompts/icp_<zielgruppe>.txt` speichern. Struktur und Fachbegriffe gehören **in die
   Datei**, nicht ins Gespräch.
1b. **Den Personalisierungs-Prompt nach `prompts/personalisierung_builder.md` bauen.**
   Ohne diesen Schritt schreibt Stufe 4e allgemeine Komplimente, die weder zur
   Zielgruppe noch zum Angebot passen. Der Builder fragt in drei Runden ab, was
   verkauft wird, woran der Aufhänger auf der Website erkennbar ist und ob nach
   mehreren Angeboten segmentiert werden soll.
2. Dem Nutzer das Ergebnis **in eigenen Worten** zusammenfassen: „Ich suche jetzt nach
   Betrieben, die X anbieten, und sortiere Y aus. Passt das so?"
3. Suchbegriffe vorschlagen — ohne das Wort „Tier":
   „Ich fange mit den naheliegenden Begriffen an: *Metallbau, Schlosserei*.
   Wenn zu wenig kommt, nehme ich noch *Stahlbau, Geländerbau* dazu."

### Vor jedem Vollstart: Kosten nennen und bestätigen lassen

```
Google-Maps-Calls = Anzahl Keywords × Anzahl Städte
```

DE ≈ 7.600 Orte ab 1 Einwohner, AT ≈ 1.310, CH ≈ 1.334.
Drei Keywords über DACH sind ~30.000 Calls. Mit `--min-population 20000`
sind es ~2.700. Bei großen Läufen eine höhere Mindestgröße vorschlagen.

Dem Nutzer gegenüber **nicht** von Calls oder Credits sprechen, sondern:

> „Bei dieser Einstellung durchsuche ich rund 10.000 Orte. Das dauert mehrere Stunden
> und verbraucht einen guten Teil deines Guthabens. Wenn ich erst ab 20.000 Einwohnern
> suche, sind es nur noch etwa 900 Orte — deutlich schneller und günstiger.
> Womit sollen wir starten?"

### Immer: Dry-Run vor dem Vollstart

`--stage 1`, dann `--stage 2 --limit 3`, dann `--stage 3`. Ergebnis gemeinsam prüfen:

```bash
sqlite3 data/leads.db -header -column \
  "SELECT firmenname, website_final, icp_label, ROUND(icp_confidence,2) conf,
          substr(icp_reason,1,60) grund
     FROM datensaetze WHERE dedupe_status='kept' LIMIT 20;"
```

Dem Nutzer **nicht** die Tabelle zeigen, sondern übersetzen:

> „Ich habe 40 Firmen gefunden. 31 davon passen zu deiner Beschreibung, 9 habe ich
> aussortiert — zum Beispiel *Möbelhaus Krüger*, weil dort keine eigene Fertigung
> erkennbar war. Sieht das für dich richtig aus?"

Zwei bis drei Beispiele nennen, davon mindestens eines aus der Aussortiert-Gruppe.
Sagt der Nutzer „passt nicht", nachfragen **welche** Firma falsch einsortiert ist —
und danach den Prompt schärfen und **nur** Stufe 3c neu fahren, das kostet keine
Maps-Calls:

```bash
python3 -m scraper set-icp prompts/icp_<ziel>.txt
sqlite3 data/leads.db "UPDATE datensaetze SET icp_raw=NULL, is_icp=NULL, attempts=0;"
python3 -m scraper run --stage 3c
```

---

## Code-Aufbau

| Datei | Inhalt |
|---|---|
| `scraper/config.py` | alle Einstellungen aus `.env`, Freemail-Blacklist, Debounce-Codes |
| `scraper/clients.py` | Skael, OpenAI, Findymail — Rate-Limit (Token-Bucket), Retry mit Backoff, Long-Polling |
| `scraper/transforms.py` | reine Datentransformationen, jede Funktion nennt im Docstring die Clay-Spalte, die sie abbildet |
| `scraper/db.py` | SQLite-Schema: `eingabe`, `verarbeitung`, `datensaetze`, `anreicherung`, `run_meta` |
| `scraper/llm.py` | die vier KI-Schritte, Prompts kommen unverändert aus `prompts/` |
| `scraper/pipeline.py` | die Prozessstufen |
| `scraper/export.py` | CSV-Export (Semikolon + BOM, Excel-tauglich), sortiert Sperrlisten-Treffer in Liste 5 |
| `scraper/sperrliste.py` | lädt die Community-Sperrliste (Abmahner-Domains), Abgleich inkl. Subdomains |
| `scraper/cli.py` | Kommandozeile |

### Konventionen, die beim Ändern gelten

**Fehlerbehandlung.** Bei einem API-Fehler wird **nie** in das Feld geschrieben, das
die Stufe als „erledigt"-Marker abfragt. Stattdessen `db.note_failure(...)` — das
zählt `attempts` hoch und legt die Meldung in `error`. Die Zeile wird beim nächsten
Lauf erneut versucht, bis `MAX_ATTEMPTS` (3) erreicht ist. Ohne diese Regel macht
ein einzelner 429 aus einem Lead einen dauerhaften Ausfall.

**Idempotenz.** Jede Stufe verarbeitet nur Zeilen, deren Zielfeld noch `NULL` ist.
Wer eine Stufe erweitert, muss diese Bedingung mitziehen.

**LLM-Rückgaben.** `scraper/llm.py` gibt `None` zurück, wenn der Aufruf *fehlgeschlagen*
ist, und einen (ggf. leeren) Wert, wenn das Modell geantwortet hat. Der Unterschied
entscheidet über „erneut versuchen" vs. „hat nichts gefunden".

**Prompts nicht im Code.** Die vier KI-Prompts liegen als Dateien in `prompts/` und
werden über `{{Platzhalter}}` befüllt. Änderungen dort, nicht in `llm.py`.

---

## Nach dem Export: Versand und Abmahnungen

* Vor dem Versand den Nutzer **einmal** darauf hinweisen: E-Mail-Werbung an Unternehmen
  ohne vorherige Einwilligung ist in Deutschland grundsätzlich unzulässig (§ 7 UWG),
  dazu kommt die Informationspflicht nach Art. 14 DSGVO. Kurz, ohne Belehrung, nicht wiederholen.
* Liste 5 (`5_gesperrt_…`) nie anschreiben. Wer sich beschwert oder abmahnt, kommt sofort
  auf die eigene Sperrliste im Versandtool.
* Kommt eine Abmahnung: Skill **abmahnung-werbemail-abwehr** verwenden. Er meldet die
  Domains des Abmahners an die Community-Sperrliste — so wird die Liste für alle besser.

---

## Fallstricke

| Thema | Was zu beachten ist |
|---|---|
| `EXCLUDED_TLDS` | Default `.fr,.nl,.it` (DACH-Kampagne). Bei Kampagnen in diesen Ländern **zwingend leeren**, sonst verschwindet die ganze Zielgruppe kommentarlos |
| Feldname `icp` | Die Skael-API antwortet mit `icp`, nicht `is_icp` — obwohl der Prompt `is_icp` vorschreibt |
| `CITIES_LIMIT=5000` | Kappt Deutschland bei ~7.600 Orten. Für vollständige Abdeckung erhöhen |
| Skael-Dedupe | Identische Requests liefern innerhalb von **20 Minuten** das alte Ergebnis — auch Fehlschläge. Beim Debuggen beachten |
| Nur erster Geschäftsführer | `geschaeftsfuehrer[0]`, weitere gehen verloren (wie im Original) |
| E-Mail-Status | `Safe to Send` (Code 5) ist sicher. `Risky` (4, Catch-all) und `Unknown` (7) sind im Export enthalten und sollten vor dem Versand separat behandelt werden |
| Community-Sperrliste | Der Export lädt sie immer und sortiert Treffer in `5_gesperrt_sperrliste_….csv`. Diese Firmen **nie** anschreiben, auch nicht über einen anderen Kanal oder eine andere Adresse. Ist die Liste nicht ladbar, bricht der Export ab (`SPERRLISTE_PFLICHT`) — nicht einfach abschalten, sondern Ursache klären |
| Query-String vs. Body | `maps_search` und `icp_checker` erwarten ihre Parameter als **Query-String**, die übrigen Endpunkte im Body |

---

## Dokumentation

| Datei | Wofür |
|---|---|
| `docs/00_ANLEITUNG.md` | **Einstieg** — die 15 Fragen, Durchlauf, Kostenabschätzung, häufige Situationen |
| `docs/01_PROZESS.md` | jede Stufe mit Formeln, Run-Bedingungen und API-Payloads |
| `docs/02_ZUGAENGE_UND_TOKENS.md` | benötigte Zugänge, Kosten, Antwortstruktur der API |
| `docs/03_SKAEL_API_REFERENZ.md` | Input/Output aller genutzten Endpunkte |
| `docs/05_ABWEICHUNGEN.md` | wo dieser Nachbau von der Vorlage abweicht und warum |
| `prompts/icp_prompt_builder.md` | Fragebogen für das Prüfprofil (Stufe 3) |
| `prompts/personalisierung_builder.md` | Fragebogen für die Ansprache (Stufe 4e) |

---

## Herkunft

Portierung eines Clay-Workbooks nach Python. Die Logik — Formeln, Prompts,
Schwellwerte, Reihenfolge — stammt 1:1 von dort. Zugangsdaten wurden **keine** übernommen.
