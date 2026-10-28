# Lead-Scraper – Projektkontext für Claude Code

Dieser Ordner ist zugleich der Claude-Skill `lead-scraper` und ein Arbeitsprojekt.

**Wenn der Nutzer Leads, eine Zielgruppe oder eine Leadliste will: folge `SKILL.md`.** Dort steht der Einstieg: Interview, Pfadwahl, Abschluss mit Sperrlisten-Abgleich. Gearbeitet wird direkt in diesem Ordner. Auftragsdateien landen in `auftraege/`.

| Ordner | Inhalt |
|---|---|
| `wissen/` | Wissensbibliothek: alles Fachliche, modellunabhängig, Einstieg `wissen/00_INDEX.md` |
| `pfade/google-maps/` | Python-Projekt für Firmen mit Standort; eigene `CLAUDE.md` mit Befehlen und Konventionen |
| `pfade/amazon/` | Amazon-Seller-Pfad: `ABLAUF.md`, Skripte, Agenten-Prompts |
| `pfade/recruiting/` | geplant – nur Anforderungen |
| `pfade/e-commerce/` | Python-Projekt: Nachbau des Clay-Workbooks ECOM 2.0 (Shop-Liste prüfen und anreichern); eigene `CLAUDE.md` und `ABLAUF.md` (Phase 1: Anforderungen klären), Builder für Shop-Profil und Mailtext in `prompts/` |
| `pfade/_vorlage/` | Pflichtenheft für neue Pfade |
| `werkzeuge/` | `sperrliste_abgleich.py` für jede CSV, `wissen_pruefen.py` für die Wissensbibliothek, `fehler_melden.py` meldet Fehler an Agentur Consulting |

Konventionen beim Ändern:

- Wissen gehört nach `wissen/`, nicht in Code-Kommentare oder Chats. Neue Erkenntnisse aus einem Lauf, z. B. Fundquoten oder Fehlermuster, dort ergänzen.
- Jede Tatsache steht an **einer** Stelle. Andere Dateien verweisen dorthin, statt sie zu kopieren (Preise, Quoten, Rechtslage).
- Fakten, die veralten können (Preise, Marktzahlen, Versionen, Rechtslage), bekommen im Dateikopf `**Stand:** JJJJ-MM-TT · **Prüfen bis:** JJJJ-MM-TT`. Wer sie prüft, erneuert beide Daten.
- Nach jeder Änderung an `wissen/`, `pfade/` oder `SKILL.md`: `python3 werkzeuge/wissen_pruefen.py` ausführen und Fehler beheben. Danach einen Eintrag in `CHANGELOG.md`.
- Ein neuer Pfad erfüllt `pfade/_vorlage/README.md`. Dazu gehören immer: Interview-Zeile in `wissen/02`, eine eigene `wissen/`-Datei und ein Sperrlisten-Abgleich vor der Ausgabe.
- `.env`, `data/`, `exports/` und `auftraege/` nie weitergeben. Sie enthalten Zugangsdaten bzw. personenbezogene Daten.

## Wenn etwas schiefgeht

- Scheitert ein Skript zweimal mit derselben Meldung, bricht ein Lauf ab oder meldet der Kunde ein Problem: Fehler mit Skriptname melden (aus dem Ordner `lead-scraper/`):
  `python3 werkzeuge/fehler_melden.py --skript <name> "<Fehlermeldung>"` (oder die Meldung über stdin senden).
  Nur die Fehlermeldung, keine Lead-Daten. Beim ersten Mal den Kunden einmal nach der E-Mail fragen, mit der er bei Agentur Consulting registriert ist, und sie als `AC_KONTAKT_EMAIL` in die `.env` schreiben. Dem Kunden sagen, dass das Team automatisch informiert ist und sich im Google Chat meldet.
- Fehler wie 401, 429 oder 5xx beim Anbieter (Skael, OpenAI): erst 1–5 Minuten warten und dann dort fortsetzen, wo der Lauf stand. Nicht neu beginnen und nicht vorschnell „Schlüssel falsch“ melden. Nur wenn der Fehler bleibt, melden.
- **Plan B:** Fällt der lokale Weg aus, kann der Kunde den gehosteten Lead-Scraper im Mitgliederbereich nutzen (Lernplattform → Lead-Scraper, MCP in Claude). Fällt der gehostete aus, umgekehrt. Beide nutzen dieselben eigenen Skael- und OpenAI-Schlüssel.
