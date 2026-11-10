# Recruiting (Firmen-Website) im Scraper-Programm

Technische Referenz der Kampagnen-Art `recruiting`, die neben Google Maps im selben Programm läuft.
Herkunft: Nachbau des Clay-Workbooks „GMAPS 3.0 Recruting + NK | BAFA“ (ausgelesen am 04.10.2026,
Spaltenreferenz: `../../recruiting/referenzen/clay-vorlage.md`). Clay wird nicht mehr verwendet.
Anleitung: `../../recruiting/ABLAUF.md` · Fachlicher Hintergrund: `../../../wissen/05_pfad-recruiting.md`.
Der zweite Recruiting-Weg über Jobportale: `08_STELLENSUCHE.md`.

---

## 0. Kampagnen-Arten

Eine Kampagne (`kampagnen/<name>/`) = eine Datenbank = eine Art. Die Art steht in `run_meta.pfad` und wird beim Anlegen gesetzt.
Eine zweite Art in derselben Kampagne lehnt das Programm ab → eigene Kampagne mit `neue-kampagne <name>`.

| Art | Anlegen | Einstieg | Eigene Stufen |
|---|---|---|---|
| `google-maps` | `init` (Standard) | Keyword × Land → Städte → Maps | – |
| `recruiting` | `init --pfad recruiting --berufe "A,B" [--nk]` | Keyword × Land → Städte → Maps, dann Firmen-Website | 3e, Weiche in 3d, 4e-RC/NK |
| `stellensuche` | `stellensuche --suche … --orte …` | Suchbegriff × Ort × Jobportal | 1j, 1k, 3g, 3a über `find_domain` (`08_STELLENSUCHE.md`) |

```
google-maps   1 → 2 → 3a → 3b → 3c ─────────────────► 3d ─► 4a … 4h   (strecke gmaps)
recruiting    1 → 2 → 3a → 3b → 3c → 3e ─┬ Stelle ───► 3d ─► 4a … 4h   (strecke rc)
                                         └ keine ───► 3d nur mit NK    (strecke nk)
```

`run --stage all` bzw. `--stage 3` ruft alle Stufen auf; jede Stufe prüft selbst, ob sie zur Kampagne gehört, und meldet sonst „übersprungen“.

## 1. Datenmodell (zusätzliche Spalten)

**`datensaetze`**

| Spalte | Bedeutung |
|---|---|
| `quelle` | `maps` (Recruiting) · `stellen` (Stellensuche) |
| `webscraper_raw` | Startseite (3e), wird an die Anreicherung weitergegeben und dort nicht erneut bezahlt |
| `stelle_raw`, `stelle_vorhanden`, `stelle_url` | Ergebnis der Stellen-Erkennung; Karriere-Seiten, auf denen gesucht wurde |
| `job_title`, `job_description`, `job_bereich` | die eine erkannte Stelle |

**`anreicherung`**: `quelle`, `strecke` (`gmaps`/`rc`/`nk`), `job_title`, `job_description`, `job_bereich`, `job_title_norm`.

**`run_meta`**: `pfad`, `berufe` (aus `init --berufe`, eine Zeile je Beruf, Reihenfolge = Priorität), `nk_on` (aus `init --nk`).

Ältere Datenbanken werden beim Start automatisch nachgerüstet (`db._MIGRATIONS`); fehlt `run_meta.pfad`, gilt `google-maps`.

## 2. Stufe 3e – Stellen-Erkennung (`pipeline.stufe3e_stellen`)

Clay: Claygent `Stelle` (Web-Recherche, GPT-4o mini) auf `Website final`, Run `Is Icp && QUALI ON/OFF`.

Lokal:

1. Zeilen: `dedupe_status='kept' AND is_icp=1 AND stelle_vorhanden IS NULL AND website_final <> ''`.
2. Startseite über Skael `web_scraper` (oder gespeicherte Antwort).
3. Bis zu `KARRIERE_SEITEN` (Standard 2) Links der eigenen Domain, deren Pfad nach Karriere aussieht (`transforms.karriere_links`, Rangfolge: stellenangebot, offene-stellen, jobs, karriere, career, stellen, wir-suchen, bewerb, ausbildung, job, team), ebenfalls über `web_scraper`. Eine nicht ladbare Karriereseite blockiert die Prüfung nicht.
4. Texte zusammen (max. `STELLEN_TEXT_MAX` = 16.000 Zeichen) an `prompts/stellenanalyse.txt` mit `{{Gesuchte Berufe}}` aus `run_meta.berufe`, Schema `stellenanalyse.schema.json`, Temperatur 0, Modell `MODEL_DEFAULT`. Ohne Berufe zählt jede Stelle, die die Firma für den eigenen Betrieb ausschreibt.
5. `stellen_ergebnis`: `stelle_vorhanden` = `stellenGefunden` && erste Position vorhanden; `job_title` = `position`, `job_description` = `beschreibung`, `job_bereich` = `bereich`.
6. Website ohne lesbaren Text → `stelle_vorhanden = 0`. KI-Fehler → `note_failure`, nächster Lauf versucht erneut.

Kosten je passender Firma: 1–3 Website-Abrufe + 1 KI-Aufruf.

**Prompts.** `stellenanalyse.txt` ist branchenneutral. Die Logistik-Fassung aus Clay (feste Berufsliste, Priorität a–f, Ausschlüsse) liegt in `prompts/beispiele/stellenanalyse_logistik.txt`. Eine Kampagne überschreibt den Standard, indem sie eine Datei gleichen Namens in `kampagnen/<name>/prompts/` ablegt (Suche: Kampagne → `prompts/`).

## 3. Weiche (Stufe 3d)

| Strecke | Bedingung | Clay |
|---|---|---|
| `rc` | `is_icp=1 AND stelle_vorhanden=1` | `RC SEND` |
| `nk` | `is_icp=1 AND stelle_vorhanden=0`, nur mit `run_meta.nk_on` (`init --nk`) bzw. `NK_ON=true` | `NK SEND` (dort `&& false`) |

3d übergibt nur Firmen, die noch nicht in `anreicherung` stehen. NK nachträglich einschalten: `NK_ON=true` in `kampagne.env`, dann `run --stage 3d` und `--stage 4`.

Passende Firmen ohne Stelle (NK aus) stehen im Export in Liste 4 mit „passt, aber keine offene Stelle gefunden“.

## 4. Stufe 4e – Texte

| Strecke | Schritte | Prompt |
|---|---|---|
| `rc` | `job_title_norm` = Jobtitel normalisieren (Temperatur 0, sofort gespeichert) → Opener (Temperatur 0.7, `MODEL_PERSONALISIERUNG`) mit normalisiertem Titel, Stellenbeschreibung und Original-Bezeichnung | `jobtitel_normalisierung.txt`, `personalisierung_stellenanzeige.txt` |
| `nk` | Startseite (aus 3e) → Satz zur Website | `personalisierung_website.txt` |

Der Standard-Opener ist branchenneutral und beginnt hart mit „ich habe gesehen, dass Sie gerade jemanden als [Rolle] suchen“, danach höchstens zwei Anforderungen aus der Stellenbeschreibung. Ohne konkrete Anforderungen endet der Satz nach „suchen.“ – keine Floskeln. Branchengenaue Fassungen: `prompts/beispiele/personalisierung_stellenanzeige_logistik.txt` (Clay-Original), `…_ki.txt`.

Kein Videotitel (4f überspringt `rc`/`nk`).

## 5. Ready to Send (4h)

`rc`: E-Mail && Personalisierung && `job_title_norm` · `nk`: E-Mail && Personalisierung (jeweils nur, wenn `DO_PERSONALISIERUNG`).

## 6. Export

Zusätzliche Spalten in Liste 1/2:

- alle Arten: `Ansprache` / `Ansprache Grund` (Paketregel: „Guten Tag Herr/Frau Nachname“ nur bei Anrede-Sicherheit > 60, sonst „Guten Tag“), `Anrede Sicherheit`, `Kampagnen-Art`
- Recruiting: `Strecke`, `Jobtitel`, `Stelle (Original)`, `Bereich`, `Stellenbeschreibung`

Firmenlisten 3–5: Recruiting zusätzlich `Offene Stelle`, `Gefunden auf`.

Firmen, die nach der Übergabe nicht mehr `kept` oder nicht mehr passend sind, fallen aus den Listen 1 und 2 heraus und stehen nur in Liste 4.

## 7. Abweichungen vom Clay-Original

| # | Clay | Lokal | Grund |
|---|---|---|---|
| 1 | Claygent `Stelle` browst selbst | Startseite + bis zu 2 Karriere-Seiten über Skael, Text an die KI | Ein Chat-Modell kann nicht browsen; so bleibt der Schritt deterministisch und günstig. Stellen, die nur über externe Bewerberportale verlinkt sind, findet er nicht |
| 2 | Stellen-Prompt verlangt `stellen_gefunden` und `"stellenangebote": "—"`, Schema `stellenGefunden`/Array | Prompt an das Schema angeglichen (`stellenGefunden`, leeres Array) | Strict-Schema erlaubt keinen String an Stelle eines Arrays |
| 3 | Stellen- und Opener-Prompt auf Logistik/Spedition geschrieben | Standard branchenneutral; gesuchte Berufe je Kampagne über `init --berufe` (`{{Gesuchte Berufe}}`); Logistik-Fassungen in `prompts/beispiele/` | Jede Zielgruppe ohne Prompt-Umbau |
| 4 | Jobtitel-Prompt referenziert die ganze Quellzeile | `{{JOB TITLE}}` | Fehler im Original (Befund 5) |
| 5 | `Hallo {{Anrede}} {{lastName}},` im Prompt-Text | `Hallo [Anrede] [Nachname],` | Der Renderer leert unbekannte Platzhalter – der Hinweis wäre sonst sinnlos |
| 6 | Website-Kompliment für „German consulting firms and agencies“ | „German companies“ | Wird für die NK-Strecke genutzt |
| 7 | `NK SEND … && false` | `NK_ON` (Standard aus) bzw. `init --nk` | bewusster Schalter statt toter Bedingung |
| 8 | Anrede-Prompt setzt bei Unsicherheit „Herr“ | unverändert, zusätzlich Spalte `Ansprache` mit Regel > 60 | Paketregel „im Zweifel neutral“ |
| 9 | Zweiter Einstieg über Indeed-Anzeigen (Apify-Actor, Tabelle „Import“) | nicht in Recruiting übernommen – Recruiting arbeitet nur mit Google Maps + Firmen-Website | Entscheidung vom 05.10.2026: der Weg über Apify/Indeed funktionierte nicht. Seit 14.10.2026 gibt es dafür die eigene Kampagnen-Art **Stellensuche** über die Skael-Jobendpunkte (Indeed, Stepstone, Arbeitsagentur, Kununu), siehe `08_STELLENSUCHE.md` |
| 10 | Skael-Schlüssel als Klartext-Spalte | `.env` | kein Schlüssel in Daten oder Exporten |

## 8. Stichprobe per SQL

Die Datenbank liegt in `kampagnen/<name>/data/leads.db`.

```bash
# erkannte Stellen und wo sie gefunden wurden
sqlite3 kampagnen/<name>/data/leads.db -header -column \
  "SELECT firmenname, job_title, substr(stelle_url,1,50) gefunden_auf
     FROM datensaetze WHERE is_icp=1 AND stelle_vorhanden=1 LIMIT 20;"

# Opener je Lead
sqlite3 kampagnen/<name>/data/leads.db -header -column \
  "SELECT firmenname_final, strecke, job_title_norm, personalisierung
     FROM anreicherung WHERE personalisierung <> '' LIMIT 10;"

# echte Skael-Kosten je Dienst (Kostenzähler)
sqlite3 kampagnen/<name>/data/leads.db -header -column \
  "SELECT endpoint, aufrufe, credits FROM kosten ORDER BY credits DESC;"
```

Dem Nutzer nie die Tabelle zeigen, sondern übersetzen (Regeln in `../CLAUDE.md`).

## 9. Tests

`tests/test_pfade.py` spielt die Kampagnen-Arten offline durch (alle Schnittstellen simuliert, keine Kosten):

```bash
python3 -m unittest discover -s tests -v
```

Recruiting (`TestRecruiting`): Maps-Einstieg mit Stelle auf der Karriere-Seite, NK-Strecke und Sperrliste, neutrale Ansprache bei unsicherem Vornamen, kein `import-indeed` mehr. Dazu `TestGoogleMapsUnveraendert` (Standardpfad, Ablehnung einer zweiten Kampagnen-Art in derselben Datenbank) und `TestTransforms` (Karriere-Links, Ansprache-Regel).
