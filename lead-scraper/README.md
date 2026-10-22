# Lead-Scraper

Ein Einstieg für alle Lead-Quellen. Die KI fragt zuerst, wen du erreichen willst, und wählt dann den passenden Weg:

| Pfad | Für | Status |
|---|---|---|
| **Google Maps** | Firmen mit Standort: Handwerk, Praxen, Händler, Großhandel, Dienstleister | verfügbar |
| **Amazon-Seller** | Marken und Händler auf amazon.de (aus einer Brand-Liste) | verfügbar |
| **Eigene Firmenliste** | Website, Geschäftsführung und Anrede zu vorhandenen Firmen | verfügbar (über den Amazon-Pfad ab Phase 4) |
| **Recruiting** | Firmen, die gerade Personal suchen | geplant |
| **E-Commerce** | Onlineshops aus einer vorhandenen Shop-Liste: aktiver Shop? Traffic? Dann Impressum, E-Mail, Anrede (Nachbau des Clay-Workbooks ECOM 2.0) | verfügbar (Beta, erster echter Testlauf steht aus) |

Jede Liste wird vor der Ausgabe mit der **Community-Sperrliste** abgeglichen. Firmen, die schon einmal wegen einer Werbe-E-Mail abgemahnt haben, fallen raus.

## Loslegen

- **Claude (App):** diesen Ordner als ZIP unter Einstellungen → Funktionen → Skills hochladen (`skills/lead-scraper.zip` im Paket). Dann schreiben: *„Ich will neue Kunden finden.“*
- **Claude Code:** diesen Ordner öffnen und dasselbe sagen.
- **Andere KI (ChatGPT, Gemini …):** den Ordner `wissen/` hochladen und den Start-Prompt aus `wissen/00_INDEX.md` verwenden. Ausführen lassen sich die Skripte dort nur, wenn das Modell Code ausführen kann.

## Aufbau

```
lead-scraper/
├── SKILL.md            Einstieg für Claude: Interview → Pfad → Abschluss
├── CLAUDE.md           Projektkontext für Claude Code
├── wissen/             Wissensbibliothek (Markdown, modellunabhängig) – Start: 00_INDEX.md
├── pfade/
│   ├── google-maps/    Python-Projekt (Stufen 1–4, Export mit Sperrliste)
│   ├── amazon/         Ablauf, Browser-Bibliothek, Skripte, Agenten-Prompts
│   ├── recruiting/     geplant
│   ├── e-commerce/     Python-Projekt (Shop-Liste prüfen und anreichern)
│   └── _vorlage/       Pflichtenheft für neue Pfade
└── werkzeuge/
    └── sperrliste_abgleich.py   Abgleich für jede CSV
```

## Wichtig

E-Mail-Werbung an Unternehmen ohne vorherige Einwilligung ist in Deutschland grundsätzlich unzulässig (§ 7 UWG). Die Sperrliste senkt das Risiko, beseitigt es aber nicht. Details stehen in `wissen/08_versand-und-recht.md`. Keine Rechtsberatung.
