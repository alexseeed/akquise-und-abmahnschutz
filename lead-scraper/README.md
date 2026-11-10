# Lead-Scraper (Universal)

Zielgruppenneutrale Version für alle Kunden. Jede Zielgruppe ist eine **Kampagne** mit eigenen Prompts, eigener Datenbank, Blockliste und eigenen Exporten. Der Code bleibt für alle gleich.

**Schnellstart Google Maps** (in `pfade/google-maps/`):

```bash
cp .env.example .env                            # einmal: SKAEL_API_KEY eintragen
./scraper.sh neue-kampagne steuerberater-bayern # Kampagne aus der Vorlage
# kampagnen/steuerberater-bayern/: kampagne.env + prompts/ ausfüllen (alle [[Platzhalter]])
./scraper.sh --kampagne steuerberater-bayern doctor
```

Danach: `kampagnen/_vorlage/README.md` (Ablauf) und `wissen/15_learnings-…` (gemessene Kosten, Kostenfallen).

**Standard:**
- Alle KI-Schritte laufen über Skael (`LLM_PROVIDER=skael`), OpenAI ist optional. Der Skael-Schlüssel braucht dafür die Fähigkeit `llm:invoke`, die Skael in der Beta auf Anfrage freischaltet.
- Die Domainsuche für Firmen ohne Website ist aus.

---

Ein Einstieg für alle Lead-Quellen. Die KI fragt zuerst, wen du erreichen willst, und wählt dann den passenden Weg:

| Pfad | Für | Status |
|---|---|---|
| **Google Maps** | Firmen mit Standort: Handwerk, Praxen, Händler, Großhandel, Dienstleister | verfügbar |
| **Amazon-Seller** | Händler und Marken auf amazon.de – der Pfad findet sie selbst, mit Land, Sortiment, Umsatz, Kontaktdaten und Geschäftsführung | verfügbar |
| **Eigene Firmenliste** | Website, Geschäftsführung und Anrede zu vorhandenen Firmen (DE/AT/CH) | verfügbar (über die Anreicherung im Amazon-Pfad) |
| **Recruiting** (Firmen-Website) | Firmen, die gerade Personal suchen: über Google Maps finden, offene Stelle auf der eigenen Website erkennen, Opener zur Stelle | verfügbar (im Programm `pfade/google-maps/`) |
| **Stellensuche** (Jobportale) | konkrete Stellenanzeigen aus Indeed, Stepstone, Arbeitsagentur und Kununu, je Firma gebündelt, wahlweise mit Geschäftsführung, E-Mail und Opener | verfügbar (im Programm `pfade/google-maps/`) |
| **E-Commerce** | Onlineshops aus einer vorhandenen Shop-Liste: aktiver Shop? Traffic? Dann Impressum, E-Mail, Anrede (Nachbau des Clay-Workbooks ECOM 2.0) | verfügbar (Beta, erster echter Testlauf steht aus) |

Jede Liste wird vor der Ausgabe mit der **Community-Sperrliste** abgeglichen. Firmen, die schon einmal wegen einer Werbe-E-Mail abgemahnt haben, fallen raus.

## Loslegen

- **Claude (App):** diesen Ordner als ZIP unter Einstellungen → Funktionen → Skills hochladen (`skills/lead-scraper.zip` im Paket). Dann schreiben: *„Ich will neue Kunden finden.“*
- **Claude Code:** diesen Ordner öffnen und dasselbe sagen.
- **ChatGPT Codex:** diesen Ordner öffnen (Codex liest `AGENTS.md`) und dasselbe sagen. Codex braucht Netzwerkzugriff, weil die Pfade externe Dienste abfragen.
- **Andere KI (ChatGPT, Gemini …):** den Ordner `wissen/` hochladen und den Start-Prompt aus `wissen/00_INDEX.md` verwenden. Ausführen lassen sich die Skripte dort nur, wenn das Modell Code ausführen kann.

## Aufbau

```
lead-scraper/
├── SKILL.md            Einstieg: Interview → Pfad → Abschluss
├── CLAUDE.md           Projektkontext für Claude Code
├── AGENTS.md           derselbe Projektkontext für Codex
├── wissen/             Wissensbibliothek (Markdown, modellunabhängig) – Start: 00_INDEX.md
├── pfade/
│   ├── google-maps/    Python-Projekt (Stufen 1–4, Export mit Sperrliste; auch beide Recruiting-Wege)
│   ├── amazon/         Node.js: Scraper, Anreicherung, Standardformat, ABLAUF.md (Läufe in arbeit/)
│   ├── recruiting/     Anleitung Recruiting über die Firmen-Website (ABLAUF.md)
│   ├── stellensuche/   Anleitung Stellensuche über Jobportale (ABLAUF.md)
│   ├── e-commerce/     Python-Projekt (Shop-Liste prüfen und anreichern)
│   └── _vorlage/       Pflichtenheft für neue Pfade
└── werkzeuge/
    └── sperrliste_abgleich.py   Abgleich für jede CSV
```

## Wichtig

E-Mail-Werbung an Unternehmen ohne vorherige Einwilligung ist in Deutschland grundsätzlich unzulässig (§ 7 UWG). Die Sperrliste senkt das Risiko, beseitigt es aber nicht. Details stehen in `wissen/08_versand-und-recht.md`. Keine Rechtsberatung.
