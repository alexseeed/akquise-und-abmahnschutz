# Neue Kampagne – Vorlage

Jede Zielgruppe ist eine Kampagne. Alles Zielgruppenspezifische liegt hier, alles andere teilen sich die Kampagnen.

```
kampagnen/<name>/
├── kampagne.env          Einstellungen der Zielgruppe (überschreibt die .env im Projektordner)
├── prompts/
│   ├── icp.txt           Prüfprofil: passt die Firma? (Skael ICP-Checker)
│   ├── pain_kategorie.txt + .schema.json   Einordnung je Firma → Spalte "Einordnung"
│   └── personalisierung.txt               Beobachtungssatz für die Mail
├── data/                 Datenbank + Blockliste (entsteht beim Lauf, nie weitergeben)
└── exports/              CSV-Listen (entstehen beim Export)
```

Anrede, Videotitel und Domainsuche kommen aus `prompts/` im Projektordner. Eine Kampagne kann jede Datei überschreiben, indem sie eine gleichnamige Datei in `kampagnen/<name>/prompts/` ablegt.

## Ablauf

1. **Anlegen:** `python3 -m scraper neue-kampagne <name>`
2. **Interview** nach `../../wissen/02_zielgruppen-interview.md`. Die Zielmenge immer mit abfragen.
3. **Ausfüllen:** alle `[[Platzhalter]]` in `kampagne.env` und `prompts/` ersetzen.
   - `icp.txt` nach `prompts/icp_prompt_builder.md`. Beispiele liegen in `prompts/beispiele/` und `kampagnen/beispiel-architekturbueros/`.
   - `personalisierung.txt` nach `prompts/personalisierung_builder.md`. **Den Satz für seinen echten Platz in der Mail bauen**, also für den Absatz aus `ABSATZ_EINLEITUNG` und `ABSATZ_FOLGESATZ`.
   - Die Kategorienamen in `pain_kategorie.txt`, `pain_kategorie.schema.json` (`enum`) und `KATEGORIE_NORMALFALL` müssen exakt übereinstimmen.
4. **Prüfen:** `python3 -m scraper --kampagne <name> doctor`. Es darf kein ✗ mehr erscheinen.
5. **Alt-Leads ausschließen:** `python3 -m scraper --kampagne <name> blockliste-import alte_leads.csv`
6. **Suche anlegen:** `python3 -m scraper --kampagne <name> init --keywords "…" --countries DE,AT,CH --min-population 50000`
7. **Kosten messen:** Stufe 1 laufen lassen, dann 2 frische Städte komplett durchlaufen lassen (siehe `../../wissen/15_learnings-…`).
8. **Menge festlegen:**
   - `python3 -m scraper --kampagne <name> run --stage 2`, dann `run --stage 3b`,
   - `schaetzen --leads 3000`,
   - `auswahl --firmen <Zahl aus schaetzen>`.
9. **Lauf:** `python3 -m scraper --kampagne <name> run --stage all`, lange Läufe mit `nohup caffeinate -i …`.
10. **Export:** `python3 -m scraper --kampagne <name> export`
