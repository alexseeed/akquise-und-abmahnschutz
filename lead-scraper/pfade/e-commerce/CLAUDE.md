# E-Commerce-Pfad – Projektkontext für Claude Code

Nachbau des Clay-Workbooks „Vorlage | ECOM 2.0“ in Python: Shop-Liste → aktive Onlineshops, die zum Shop-Profil passen und Traffic haben → Impressum, E-Mail, Anrede, Personalisierung, Videotitel → CSV mit fertiger Mail je Lead.

- **Bedienung und Gesprächsführung:** `ABLAUF.md` – dem folgen. Vor jeder Abfrage **Phase 1 – Anforderungen klären**: nachfragen, bis jeder Punkt der Anforderungsliste erfüllt ist. `run` bricht mit „Anforderung fehlt“ ab, solange Shop-Profil, Personalisierung oder Mailtext fehlen.
- **Builder (Anleitungen für dich):** `prompts/shopprofil_builder.md` (Shop-Profil) und `prompts/personalisierung_builder.md` (Mailtext und Personalisierung, Freigabe nach dem Testlauf). Beispiele für einen erfundenen Absender in `beispiel/`.
- **Befehle für die Anforderungen:** `python3 -m ecom set-prompt shopprofil <datei>` (oder `--ohne`), `python3 -m ecom set-prompt personalisierung <datei>`, `python3 -m ecom set-mailtext <datei>`. `status` und `doctor` zeigen den Block „Anforderungen“.
- **Fehler:** `status` zeigt Fehler je Stufe, `status --shops 20` je Shop; `fehler-zuruecksetzen` gibt liegen gebliebenen Zeilen neue Versuche. Zugangsfehler (falscher Schlüssel, kein Guthaben) brechen die Stufe ab, ohne Versuche zu zählen.
- **Schlüssel:** trägt der Nutzer selbst in `.env` ein. `.env` nie ausgeben, Schlüssel nie im Chat erfragen.
- **Clay-Spalte ↔ Code:** `docs/01_PROZESS.md`; Formeln und Prompts im Wortlaut: `docs/clay_spalten_lesbar.md`.
- **Abweichungen von Clay:** `docs/05_ABWEICHUNGEN.md` – vor jeder Änderung lesen.
- **Wissen für Nutzer:** `../../wissen/06_pfad-e-commerce.md`.

Beim Ändern:

- Clay ist die Vorlage. Neue Logik zuerst mit dem Workbook abgleichen. Bausteine ohne Clay-Vorbild in `docs/01_PROZESS.md` mit „neu, nicht in Clay“ markieren.
- Jede Abweichung in `docs/05_ABWEICHUNGEN.md` eintragen.
- `prompts/personalisierung.txt` ist der Clay-Prompt (für Beratungen und Agenturen geschrieben). Er bleibt als Referenz, Läufe nutzen den Prompt des Auftrags aus der Datenbank.
- `ecom/clients.py` ist eine Kopie aus `../google-maps/scraper/clients.py`. Änderungen am gemeinsamen Teil in beiden Dateien nachziehen.
- Danach ausführen:
  1. `python3 -m unittest discover -s tests` (Python ≥ 3.10, sonst `python3.12`)
  2. `python3 ../../werkzeuge/wissen_pruefen.py`
  3. einen Eintrag in `../../CHANGELOG.md` anlegen
- `.env`, `data/`, `exports/` und die Auftragsdateien nie weitergeben.
