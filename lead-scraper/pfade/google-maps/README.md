# Lead-Scraper

Von einem Keyword zur versandfertigen Leadliste: Google Maps, Prüfung gegen dein Wunschkundenprofil, Impressum, E-Mail, Anrede, Personalisierung. Lokal, ohne Clay. Exportiert wird nur, was nicht auf der Community-Sperrliste steht.

```
Keyword + Land  →  Städte  →  Google Maps  →  ICP-Prüfung  →  Impressum, E-Mail, Anrede, Personalisierung
```

Die Zielgruppe ist austauschbar. Der Prozess funktioniert für alles, was über
Google Maps auffindbar ist.

---

## Schnellstart

```bash
cd <projektverzeichnis>

# 1. Eigene Zugänge in .env eintragen: SKAEL_API_KEY und OPENAI_API_KEY
python3 -m scraper doctor

# 2. ICP-Prompt bauen (siehe docs/00_ANLEITUNG.md) und ablegen
#    → prompts/icp_<zielgruppe>.txt

# 3. Lauf anlegen
python3 -m scraper init \
  --keywords "Metallbau,Schlosserei,Metallbauer" \
  --countries DE,AT,CH \
  --min-population 1 \
  --icp-prompt prompts/icp_beispiel_metallbau.txt

# 4. Dry-Run
python3 -m scraper run --stage 1
python3 -m scraper run --stage 2 --limit 3
python3 -m scraper run --stage 3

# 5. Vollstart (fortsetzbar — bei Abbruch einfach erneut aufrufen)
python3 -m scraper run --stage all

# 6. Export
python3 -m scraper export
```

Keine Fremdabhängigkeiten — reine Standardbibliothek, Python ≥ 3.10.

Mit Claude Code: Ordner öffnen und *„Richte den Scraper ein"* sagen — `CLAUDE.md`
wird automatisch gelesen und führt durch Einrichtung und Lauf.

---

## Befehle

| Befehl | Zweck |
|---|---|
| `doctor` | Zugänge, Prompt-Dateien und Erreichbarkeit prüfen |
| `init` | Keywords × Länder anlegen, ICP-Prompt hinterlegen |
| `run --stage <s>` | Pipeline ausführen (`all`, `1`, `2`, `3`, `3a`–`3d`, `4`, `4a`–`4h`) |
| `run --limit n` | nur n Zeilen verarbeiten (Dry-Run) |
| `status` | Fortschritt aller Stufen |
| `export` | CSV nach `exports/` (`--all`, `--mark`) |
| `set-icp <datei>` | ICP-Prompt nachträglich setzen |

---

## Verzeichnis

```
docs/
  00_ANLEITUNG.md            Durchlauf von der ersten Frage bis zum Export  ← hier anfangen
  01_PROZESS.md              vollständige Prozessdokumentation (alle Formeln, Bedingungen, Fan-outs)
  02_ZUGAENGE_UND_TOKENS.md  Zugänge, API-Keys, Kosten
  03_SKAEL_API_REFERENZ.md   Input/Output aller genutzten Endpunkte
  05_ABWEICHUNGEN.md         wo der Nachbau vom Original abweicht und warum
  06_WEITERGABE.md           was mitgeht, was nicht, was der Empfänger tun muss

prompts/
  icp_prompt_builder.md              Master-Prompt für die drei ICP-Runden
  icp_beispiel_metallbau.txt    fertiger ICP-Prompt (Beispiel)
  company_domain.txt                 KI-Domainsuche
  anrede.txt / .schema.json          Herr/Frau + Confidence
  personalisierung.txt / .schema.json  Kompliment aus dem Website-Bodytext
  video_title_cleanup.txt / .schema.json  Videotitel bereinigen
  linkedin_research_body.json.tpl    LinkedIn-Suche (optional)

scraper/
  config.py      Einstellungen aus .env
  clients.py     Skael, OpenAI, Findymail — mit Rate-Limit und Retry
  transforms.py  1:1-Portierung aller Clay-Formeln
  db.py          SQLite-Schema (ersetzt die vier Clay-Tabellen)
  llm.py         die vier KI-Schritte
  pipeline.py    die Prozessstufen
  export.py      CSV-Export (fünf Listen, Liste 5 = gesperrt)
  sperrliste.py  Community-Sperrliste laden und abgleichen
  cli.py         Kommandozeile

CLAUDE.md              Projektkontext — wird von Claude Code automatisch gelesen
data/                  SQLite-Datenbank
exports/               CSV-Exporte
```

---

## Kosten im Blick behalten

Der teuerste Posten ist Stufe 2: **Keywords × Städte** Google-Maps-Calls.

| Land | Städte ≥ 1.000 Einwohner |
|---|---|
| DE | ~7.600 |
| AT | ~1.310 |
| CH | ~1.334 |

Drei Keywords über DACH ≈ **30.000 Maps-Calls**.
`--min-population` hochsetzen, wenn kleine Orte nicht relevant sind.

---

## Feature-Schalter (`.env`)

| Variable | Default | Entspricht in Clay |
|---|---|---|
| `QUALI_ON` | `true` | Spalte `QUALI ON/OFF` |
| `SEND_ON` | `true` | Spalte `SEND ON/OFF` |
| `USE_FINDYMAIL` | `true` | Spalte `Find Work Email` |
| `DO_PERSONALISIERUNG` | `true` | `SKAEL WEBSCRAPER` + `Personalisierung AI` |
| `DO_VIDEO_TITLE` | `true` | `Cleaned Video Title` |
| `DO_LINKEDIN` | `false` | `SKAEL Linked In Search` (im Original deaktiviert) |
| `CITIES_LIMIT` | `5000` | `limit` in `find_cities` |
| `MAPS_ZOOM` | `11` | `zoom` in `maps_search` |
| `MAPS_LIMIT` | `2000` | `limit` in `maps_search` |
| `EXCLUDED_TLDS` | `.fr,.nl,.it` | Dedupe-Ausschluss. **Bei FR/NL/IT-Kampagnen leeren!** |

---

## Zugangsdaten

**Eigene Keys erforderlich.** Im Paket sind keine Zugangsdaten enthalten.

Benötigt werden:

| Variable | Wofür | Pflicht |
|---|---|---|
| `SKAEL_API_KEY` | alle Scraping- und Anreicherungs-Endpunkte | ✅ |
| `OPENAI_API_KEY` | die vier KI-Schritte | ✅ |
| `FINDYMAIL_API_KEY` | Fallback-Mailfinder | optional |

`.env`, `data/` und `exports/` stehen in `.gitignore`.

---

## Community-Sperrliste

`python3 -m scraper export` lädt vorher die Community-Sperrliste (`SPERRLISTE_URL` in `.env`):
Domains von Unternehmen, die nach einer Werbe-E-Mail abgemahnt haben. Treffer – auch über
Subdomains – landen nur in `5_gesperrt_sperrliste_….csv`, nie in den Versandlisten.
Ohne geladene Liste kein Export (`SPERRLISTE_PFLICHT=true`).

---

## Herkunft

Der Prozess ist die Portierung eines Clay-Workbooks nach Python. Formeln, Prompts,
Schwellwerte und Reihenfolge wurden von dort übernommen (`docs/01_PROZESS.md`,
`docs/05_ABWEICHUNGEN.md`). Zugangsdaten wurden keine übernommen.

## Rechtliches

E-Mail-Werbung an Unternehmen ohne vorherige Einwilligung ist in Deutschland grundsätzlich
unzulässig (§ 7 UWG); dazu kommen die Pflichten aus der DSGVO (Art. 6, 14). Details in
`docs/06_WEITERGABE.md`, Abschnitt 6. Keine Rechtsberatung.
