# Pfad „Recruiting“ – über die Firmen-Website

**Status:** verfügbar, läuft lokal im Scraper-Programm (`../google-maps/`) als eigene Kampagnen-Art. Offline getestet; Quoten aus einem echten Lauf stehen noch aus.

Findet Firmen, die **gerade Personal suchen**, und schreibt sie mit Bezug auf die konkrete Stelle an: „ich habe gesehen, dass Sie gerade jemanden als Berufskraftfahrer suchen, der den Führerschein Klasse CE und eine Fahrerkarte mitbringt.“

Ablauf: Branche und Region → Firmen über Google Maps → Prüfung gegen das Wunschkundenprofil → Startseite und Karriere-Seiten der Firmen-Website lesen → eine offene Stelle zu den gesuchten Berufen erkennen → Anreicherung (Impressum, Geschäftsführung, E-Mail, Anrede, Opener zur Stelle).

Passende Firmen ohne erkannte Stelle können optional (`--nk`) mit einem Satz zu ihrer Website angeschrieben werden.

Der zweite Recruiting-Weg holt konkrete Anzeigen aus Jobportalen (Indeed, Stepstone, Arbeitsagentur, Kununu): `../stellensuche/`. Faustregel: Branche bekannt → dieser Pfad; Beruf bekannt → Stellensuche.

| Datei | Inhalt |
|---|---|
| `ABLAUF.md` | Anleitung für die KI, Phase für Phase |
| `../google-maps/docs/07_RECRUITING.md` | Technik: Stufen, Datenfelder, Abweichungen vom Clay-Original |
| `../google-maps/prompts/` | `stellenanalyse.txt`, `jobtitel_normalisierung.txt`, `personalisierung_stellenanzeige.txt`, `personalisierung_website.txt` (branchenneutral); branchengenaue Fassungen in `beispiele/` |
| `referenzen/clay-vorlage.md` | Herkunft: das ausgelesene Clay-Workbook |

Voraussetzungen: wie Google Maps (Python ≥ 3.10, Skael; die KI läuft standardmäßig über Skael). Hintergrund, Grenzen und Recht: `../../wissen/05_pfad-recruiting.md`.
