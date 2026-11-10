# Pfad „Stellensuche“ – Recruiting über Jobportale

**Status:** verfügbar, läuft lokal im Scraper-Programm (`../google-maps/`) als eigene Kampagnen-Art. Offline getestet; Antwortformate der Portale am 14.10.2026 live geprüft; erster echter Lauf am 15.10.2026 (Quoten in `../../wissen/18_pfad-stellensuche.md`).

Sucht mit einem Begriff (z. B. „Berufskraftfahrer“) **konkrete Stellenanzeigen** in Indeed, Stepstone, der Jobbörse der Arbeitsagentur und Kununu. Heraus kommen eine Liste aller Anzeigen und eine Liste der Firmen dahinter – wahlweise angereichert mit Geschäftsführung, E-Mail und einem Opener zur Stelle: „ich habe gesehen, dass Sie gerade jemanden als Berufskraftfahrer suchen, der den Führerschein Klasse CE und eine Fahrerkarte mitbringt.“

Ablauf: Suchbegriffe × Orte × Portale → Anzeigen (Filter: Alter, Zeitarbeit/Personalvermittler, Titel) → je Firma bündeln → nur Stellenliste **oder** Größen-Check → Website per Impressum-Beleg → Anreicherung wie Recruiting → Export.

Der zweite Recruiting-Weg findet Firmen über Google Maps und liest die offene Stelle auf deren eigener Website: `../recruiting/`. Faustregel: Beruf bekannt → dieser Pfad; nur Branche bekannt → Recruiting.

| Datei | Inhalt |
|---|---|
| `ABLAUF.md` | Anleitung für die KI, Phase für Phase |
| `../google-maps/docs/08_STELLENSUCHE.md` | Technik: Stufen 1j/1k/3g/3a, Datenfelder, Antwortformate der Portale |
| `../google-maps/scraper/stellen.py` | Anfragen und Antworten je Portal, Filter, Stellentext-Bereinigung |
| `../google-maps/prompts/` | `groessen_check.txt`, `jobtitel_normalisierung.txt`, `personalisierung_stellenanzeige.txt` (branchenneutral); branchengenaue Opener in `beispiele/` |

Voraussetzungen: Python ≥ 3.10, Skael (die KI läuft standardmäßig über Skael; „nur Stellenliste“ braucht keine KI). Hintergrund, Grenzen und Recht: `../../wissen/18_pfad-stellensuche.md`.
