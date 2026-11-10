# Lead-Scraper – Projektkontext für Codex (und andere Coding-Agenten)

Dieser Ordner ist ein Arbeitsprojekt zum Aufbau von B2B-Leadlisten. Inhaltlich gilt dasselbe wie in `CLAUDE.md`. Beide Dateien bleiben gleich.

**Wenn der Nutzer Leads, eine Zielgruppe oder eine Leadliste will: folge `SKILL.md`.** Dort steht der Einstieg: Interview, Pfadwahl, Abschluss mit Sperrlisten-Abgleich. Gearbeitet wird direkt in diesem Ordner. Auftragsdateien landen in `auftraege/`.

| Ordner | Inhalt |
|---|---|
| `wissen/` | Wissensbibliothek: alles Fachliche, modellunabhängig, Einstieg `wissen/00_INDEX.md` |
| `pfade/google-maps/` | Python-Projekt für Firmen mit Standort (auch die beiden Recruiting-Wege); eigene `CLAUDE.md` mit Befehlen und Konventionen (gilt auch für dich) |
| `pfade/amazon/` | Amazon-Seller-Pfad (Node.js): `ABLAUF.md` mit allen Befehlen, Scraper, Anreicherung, Standardformat; Läufe in `pfade/amazon/arbeit/`, Zugänge in `pfade/amazon/.env` |
| `pfade/recruiting/` | Recruiting über die Firmen-Website: Firmen aus Google Maps, offene Stelle auf der eigenen Website/Karriereseite erkennen; Anleitung `ABLAUF.md`, Code und Prompts im Programm `pfade/google-maps/` |
| `pfade/stellensuche/` | Recruiting über Jobportale: konkrete Anzeigen aus Indeed, Stepstone, Arbeitsagentur, Kununu; Anleitung `ABLAUF.md`, Code und Prompts im Programm `pfade/google-maps/` |
| `pfade/e-commerce/` | Python-Projekt: Nachbau des Clay-Workbooks ECOM 2.0 (Shop-Liste prüfen und anreichern); eigene `CLAUDE.md` und `ABLAUF.md` (Phase 1: Anforderungen klären), Builder für Shop-Profil und Mailtext in `prompts/` |
| `pfade/videoseiten/` | nach dem Scrape: Video je Lead (Skael), eigene Landingpage im Branding des Nutzers, Hostinger-Server, Versandliste; Ablauf `ABLAUF.md`, Werkzeuge in `werkzeuge/`, Zugänge in `pfade/videoseiten/.env` |
| `pfade/_vorlage/` | Pflichtenheft für neue Pfade |
| `werkzeuge/` | `sperrliste_abgleich.py` für jede CSV, `wissen_pruefen.py` für die Wissensbibliothek |

Hinweise für Codex:

- **Befehle selbst ausführen**, Ausgaben für den Nutzer übersetzen. Der Nutzer ist in der Regel kein Entwickler. Eine Frage pro Nachricht.
- **Lange Läufe** (über ~5 Minuten) im Hintergrund starten, mit der ganzen Befehlszeile, z. B. `KAMPAGNE=<name> ZIEL=… BUDGET=… nohup node ../amazon_seller_scraper.mjs > lauf_<name>.log 2>&1 &`, und den Fortschritt im Log lesen. Abbrüche kosten nichts, derselbe Befehl setzt fort. **Nie zwei Läufe derselben Kampagne gleichzeitig:** vor einem Neustart mit `pgrep -f amazon_seller_scraper` prüfen, dass keiner mehr läuft.
- **Netzwerk:** Die Pfade rufen externe Dienste auf (Oxylabs, Bright Data, Skael, Sperrliste). Läuft Codex in einer Sandbox ohne Netz, den Nutzer bitten, Netzwerkzugriff für diesen Ordner zu erlauben.
- **Schlüssel nie im Chat abfragen.** Der Nutzer trägt sie selbst in die jeweilige `.env` ein (Vorlage `.env.example`). Die Datei `.env` nie lesen, ausgeben oder durchsuchen.
- **Schreibzugriff:** Das Sperrlisten-Werkzeug legt eine Kopie der Liste unter `~/.cache/werbemail-sperrliste.txt` ab. Ist das in der Sandbox gesperrt, läuft der Abgleich trotzdem.
- **Videoseiten:** Für die Vorschau der Landingpage einen lokalen Server starten (`python3 -m http.server`) und den Link nennen; SSH und Hostinger-API laufen über `pfade/videoseiten/werkzeuge/`. Der Nutzer braucht dafür keine Konsole.
- Wo `SKILL.md` Claude-spezifische Funktionen nennt (Skills-Upload, Subagenten), gilt für dich der Ablauf in der jeweiligen `ABLAUF.md` bzw. `CLAUDE.md` des Pfads.

Konventionen beim Ändern:

- Wissen gehört nach `wissen/`, nicht in Code-Kommentare oder Chats. Neue Erkenntnisse aus einem Lauf, z. B. Fundquoten oder Fehlermuster, dort ergänzen.
- Jede Tatsache steht an **einer** Stelle. Andere Dateien verweisen dorthin, statt sie zu kopieren (Preise, Quoten, Rechtslage).
- Fakten, die veralten können (Preise, Marktzahlen, Versionen, Rechtslage), bekommen im Dateikopf `**Stand:** JJJJ-MM-TT · **Prüfen bis:** JJJJ-MM-TT`. Wer sie prüft, erneuert beide Daten.
- Nach jeder Änderung an `wissen/`, `pfade/` oder `SKILL.md`: `python3 werkzeuge/wissen_pruefen.py` ausführen und Fehler beheben. Danach einen Eintrag in `CHANGELOG.md`.
- Ein neuer Pfad erfüllt `pfade/_vorlage/README.md`. Dazu gehören immer: Interview-Zeile in `wissen/02`, eine eigene `wissen/`-Datei und ein Sperrlisten-Abgleich vor der Ausgabe.
- `.env`, `data/`, `exports/`, `arbeit/` und `auftraege/` nie weitergeben. Sie enthalten Zugangsdaten bzw. personenbezogene Daten.
- Änderungen am Scraper-Programm `pfade/google-maps/`: danach dort `python3 -m unittest discover -s tests -v` (Offline-Tests, keine Kosten).
