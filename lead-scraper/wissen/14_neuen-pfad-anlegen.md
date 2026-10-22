# Einen neuen Pfad anlegen (z. B. Recruiting, E-Commerce)

**Zweck:** wie ein weiterer Pfad so eingebaut wird, dass Interview, Wissen, Ausgabe und Sperrliste für alle gleich funktionieren.
**Für wen:** Betreiber, Entwickler und KI-Modelle, die einen Pfad bauen (z. B. Claude Code).
**Verwandt:** `pfade/_vorlage/README.md` (Pflichtenheft) · `02_zielgruppen-interview.md` · `07_lead-ausgabe-und-spalten.md`

---

## Vorgehen

1. **Zielbild schärfen** in `wissen/NN_pfad-<name>.md`:
   - Wer ist der Lead?
   - Woher kommen die Daten?
   - Was darf man mit diesen Daten tun?

   Die offenen Entscheidungen dort festhalten (siehe `05`/`06`).
2. **Quelle prüfen:**
   - Nutzungsbedingungen, Kosten, API statt Scraping wo möglich.
   - Personenbezug der Daten.
   - Ergebnis im Abschnitt „Rechtliches“ der Wissensdatei.
3. **Ordner anlegen** nach `pfade/_vorlage/README.md`: `ABLAUF.md`, `README.md`, `scripts/`, `referenzen/`.
4. **Wiederverwenden statt neu bauen:**

   | Baustein | Wiederverwenden aus |
   |---|---|
   | Prüfprofil (Website gegen Wunschkunden) | Google Maps, Stufe 3c / Skael `icp_checker` |
   | Impressum, E-Mail-Suche, E-Mail-Prüfung | Google Maps, Stufe 4 / Skael-Endpunkte |
   | Geschäftsführung per Recherche-Agent | Amazon, Phase 4 (`referenzen/agent-prompt.md`) |
   | Anrede- und Ansprache-Regeln | Amazon `scripts/anrede.py` |
   | Sperrlisten-Abgleich | `werkzeuge/sperrliste_abgleich.py` |

5. **Interview erweitern** in `wissen/02_zielgruppen-interview.md`:
   - Antwortmöglichkeit in Block C,
   - Zeile in „Entscheidung“,
   - Spalte in „Übersetzung der Antworten“.

   Zusatzfragen nur für diesen Pfad gehören in seine `ABLAUF.md` und werden erst nach der Pfadwahl gestellt.
6. **Ausgabe im Standardformat** (`07`), letzte Phase immer der Sperrlisten-Abgleich.
7. **Testen:** ein kleiner echter Lauf und eine Stichprobe von 5–10 Datensätzen, die von Hand geprüft werden. Die gemessenen Quoten in die Wissensdatei eintragen.
8. **Freischalten:**
   - Status in `wissen/02` auf „verfügbar“ setzen.
   - Pfadtabelle in `SKILL.md` ergänzen.
   - Eintrag in `wissen/00_INDEX.md`.
   - `python3 werkzeuge/wissen_pruefen.py` ohne Fehler.
   - Skill-ZIP neu bauen (macht der Betreiber beim nächsten Paketstand).
   - Eintrag in `CHANGELOG.md`.

## Prompt für Claude Code zum Start

> Lies `lead-scraper/CLAUDE.md`, `wissen/14_neuen-pfad-anlegen.md`, `pfade/_vorlage/README.md` und `wissen/NN_pfad-<name>.md`. Baue den Pfad `<name>` nach dem Pflichtenheft. Kläre zuerst mit mir die offenen Entscheidungen aus der Wissensdatei, eine Frage pro Nachricht. Nutze die vorhandenen Bausteine, statt sie neu zu bauen.
