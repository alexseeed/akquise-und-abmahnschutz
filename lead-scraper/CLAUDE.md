# Lead-Scraper – Projektkontext für Claude Code

Dieser Ordner ist zugleich der Claude-Skill `lead-scraper` und ein Arbeitsprojekt.

**Wenn der Nutzer Leads, eine Zielgruppe oder eine Leadliste will: folge `SKILL.md`.** Dort steht der Einstieg: Interview, Pfadwahl, Abschluss mit Sperrlisten-Abgleich. Gearbeitet wird direkt in diesem Ordner. Auftragsdateien landen in `auftraege/`.

| Ordner | Inhalt |
|---|---|
| `wissen/` | Wissensbibliothek: alles Fachliche, modellunabhängig, Einstieg `wissen/00_INDEX.md` |
| `pfade/google-maps/` | Python-Projekt für Firmen mit Standort (auch die beiden Recruiting-Wege); eigene `CLAUDE.md` mit Befehlen und Konventionen |
| `pfade/amazon/` | Amazon-Seller-Pfad (Node.js): `ABLAUF.md` mit allen Befehlen, Scraper, Anreicherung, Standardformat; Läufe in `pfade/amazon/arbeit/`, Zugänge in `pfade/amazon/.env` |
| `pfade/recruiting/` | Recruiting über die Firmen-Website: Firmen aus Google Maps, offene Stelle auf der eigenen Website/Karriereseite erkennen; Anleitung `ABLAUF.md`, Code und Prompts im Programm `pfade/google-maps/` |
| `pfade/stellensuche/` | Recruiting über Jobportale: konkrete Anzeigen aus Indeed, Stepstone, Arbeitsagentur, Kununu; Anleitung `ABLAUF.md`, Code und Prompts im Programm `pfade/google-maps/` |
| `pfade/e-commerce/` | Python-Projekt: Nachbau des Clay-Workbooks ECOM 2.0 (Shop-Liste prüfen und anreichern); eigene `CLAUDE.md` und `ABLAUF.md` (Phase 1: Anforderungen klären), Builder für Shop-Profil und Mailtext in `prompts/` |
| `pfade/videoseiten/` | nach dem Scrape: Video je Lead (Skael), eigene Landingpage im Branding des Nutzers, Hostinger-Server, Versandliste; Ablauf `ABLAUF.md`, Werkzeuge in `werkzeuge/`, Zugänge in `pfade/videoseiten/.env` |
| `pfade/_vorlage/` | Pflichtenheft für neue Pfade |
| `werkzeuge/` | `sperrliste_abgleich.py` für jede CSV, `wissen_pruefen.py` für die Wissensbibliothek |

Konventionen beim Ändern:

- Wissen gehört nach `wissen/`, nicht in Code-Kommentare oder Chats. Neue Erkenntnisse aus einem Lauf, z. B. Fundquoten oder Fehlermuster, dort ergänzen.
- Jede Tatsache steht an **einer** Stelle. Andere Dateien verweisen dorthin, statt sie zu kopieren (Preise, Quoten, Rechtslage).
- Fakten, die veralten können (Preise, Marktzahlen, Versionen, Rechtslage), bekommen im Dateikopf `**Stand:** JJJJ-MM-TT · **Prüfen bis:** JJJJ-MM-TT`. Wer sie prüft, erneuert beide Daten.
- Nach jeder Änderung an `wissen/`, `pfade/` oder `SKILL.md`: `python3 werkzeuge/wissen_pruefen.py` ausführen und Fehler beheben. Danach einen Eintrag in `CHANGELOG.md`.
- Ein neuer Pfad erfüllt `pfade/_vorlage/README.md`. Dazu gehören immer: Interview-Zeile in `wissen/02`, eine eigene `wissen/`-Datei und ein Sperrlisten-Abgleich vor der Ausgabe.
- `.env`, `data/`, `exports/`, `arbeit/` und `auftraege/` nie weitergeben. Sie enthalten Zugangsdaten bzw. personenbezogene Daten.
- Änderungen am Scraper-Programm `pfade/google-maps/`: danach dort `python3 -m unittest discover -s tests -v` (Offline-Tests, keine Kosten).
- Schlüssel nie im Chat abfragen und die Datei `.env` im Amazon-Pfad nie lesen, ausgeben oder durchsuchen. Der Nutzer trägt die Zugänge selbst ein.
- Codex liest statt dieser Datei `AGENTS.md` (gleicher Inhalt plus Codex-Hinweise). Änderungen in beiden Dateien nachziehen.
