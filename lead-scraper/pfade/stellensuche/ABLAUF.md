# Ablauf Stellensuche (Jobportale) – Anleitung für die KI

**Vorher lesen:** die Auftragsdatei in `auftraege/…md`. Frag nur, was dort fehlt.
**Hintergrund:** `../../wissen/18_pfad-stellensuche.md` · **Technik:** `../google-maps/docs/08_STELLENSUCHE.md`
**Programm:** Der Pfad läuft lokal im Scraper-Programm `../google-maps/`. Alle Befehle dort ausführen; Bedienregeln und Erstinbetriebnahme: `../google-maps/CLAUDE.md`.

Jede Suche ist eine **eigene Kampagne** unter `../google-maps/kampagnen/<name>/` (eigene `kampagne.env`, eigene Prompts, Datenbank und Exporte). Vor jedem Befehl `--kampagne <name>`. `./scraper.sh` sucht selbst ein Python ≥ 3.10; sonst `python3 -m scraper` (auf dem Mac ggf. `python3.12`).


**Weg noch offen?** Sind Beruf und Branche bekannt und ist unklar, ob Firmen-Website oder Jobportale besser liefern: erst den Testballon anbieten (`../google-maps/docs/09_TESTBALLON.md`). Er fährt beide Wege mit je ~100 Leads und vergleicht sie.

---

## Phase 0 – Zusatzfragen (nur, was die Auftragsdatei nicht beantwortet)

Eine Frage pro Nachricht, immer mit Beispiel:

| # | Frage | Beispiel | Wofür |
|---|---|---|---|
| S1 | „Nach welchen Stellen soll ich in den Jobportalen suchen?“ | „Zum Beispiel Berufskraftfahrer, LKW-Fahrer, Disponent – jeder Begriff ist eine eigene Suche.“ | `--suche` |
| S2 | „In welcher Gegend sollen die Stellen sein?“ | „Zum Beispiel Stuttgart und Ulm, ganz Baden-Württemberg oder ganz Deutschland.“ | `--orte` bzw. `--min-population`, `--umkreis` |
| S3 | „Willst du nur eine Liste der Stellen und Firmen, oder auch gleich Geschäftsführer, E-Mail und einen Einstiegssatz zur Stelle?“ | „Nur die Liste ist in Minuten fertig und kostet fast nichts.“ | `--nur-stellen` |
| S4 | „Wie frisch sollen die Anzeigen sein?“ | „Standard sind die letzten 30 Tage.“ | `--max-alter` |

Nicht fragen, sondern so einstellen:

- Portale: alle vier (Standard). Nur auf ausdrücklichen Wunsch einschränken (`--portale`).
- Zeitarbeit und Personalvermittler fliegen immer raus.
- Titel-Pflicht (`--titel-pflicht`): immer setzen, wenn die Suchbegriffe Allerweltswörter enthalten (Manager, Experte, Specialist). Indeed liefert sonst viele fremde Stellen. Pflichtbegriffe aus den Suchbegriffen ableiten (z. B. KI, AI, Automatisierung, RPA). Begriffe bis 3 Zeichen zählen nur als ganzes Wort.
- Titel-Ausschluss (`--titel-ausschluss`): Begriffe, die eine falsche Bedeutung des Suchworts anzeigen (z. B. SPS, Steuerungstechnik bei „Automation“), dazu Werkstudent, Praktikum, Ausbildung, Working Student, Internship, Trainee, Duales Studium.
- Größen-Check: immer an (Standard). Er sortiert vor der bezahlten Website-Suche Konzerne (> ~1.000 Mitarbeitende, börsennotiert, Konzerntöchter), öffentliche Hand/Verbände/Vereine und IT-Wettbewerber aus. Nur abschalten (`--no-groessen-check`), wenn der Nutzer ausdrücklich auch Konzerne oder Behörden will – oder wenn das Angebot nichts mit IT/KI zu tun hat und IT-Firmen als Kunden passen (sonst fallen sie als „IT-Wettbewerber“ raus).
- Prüfprofil: nur bauen, wenn der Suchbegriff viele unpassende Arbeitgeber liefern wird oder der Nutzer Ausschlüsse nennt (Branche). Die Größe prüft schon der Größen-Check; das Profil sieht nur die Startseite und erkennt Konzerne schlecht. Bauanleitung `../google-maps/prompts/icp_prompt_builder.md`, Beispiel für „offene Stelle ist bekannt, nur Ausschlüsse prüfen“: `../google-maps/prompts/beispiele/icp_ki_automation.txt`.

Region übersetzen: Ein Bundesland oder „ganz Deutschland“ wird zu einer Städteliste (`--min-population 50000` für ein Land, sonst eine Liste der größten Städte der Region in `--orte`). „Ganz Deutschland“ ohne Orte geht auch: dann eine Suche je Portal ohne Ort, aber die Portale liefern höchstens `--max-seiten` × 100 Anzeigen.

Kennt der Nutzer nur die **Branche** der Firmen („Speditionen, die einstellen“), passt der andere Weg besser: `../recruiting/ABLAUF.md`.

## Phase 1 – Kampagne anlegen und Voraussetzungen

1. `./scraper.sh neue-kampagne <name>` (z. B. `fahrer-bw`).
2. `.env` im Projektordner: `SKAEL_API_KEY`. Die KI-Schritte (Größen-Check, Jobtitel, Opener) laufen standardmäßig über Skael. Ein `OPENAI_API_KEY` ist nur nötig, wenn `LLM_PROVIDER=openai` oder `DOMAINSUCHE=openai` gesetzt ist. „Nur Stellenliste“ braucht gar keine KI.
3. `kampagne.env` ausfüllen: `DO_VIDEO_TITLE=false`; `ABSATZ_EINLEITUNG` leer lassen (der Opener beginnt selbst mit „ich habe gesehen, …“), `ABSATZ_FOLGESATZ` und `ABSATZ_STANDARD` wie gewohnt; `KATEGORIE_NORMALFALL` löschen oder leeren.
4. `prompts/pain_kategorie.*` und `prompts/personalisierung.txt` der Vorlage braucht die Stellensuche nicht; löschen. Ohne Prüfprofil `icp.txt` einfach unverändert lassen: eine Vorlage mit `[[Platzhaltern]]` übernimmt `stellensuche` nicht.
5. Sperrliste ladbar (`doctor`, Zeile „Community-Sperrliste“). Sonst bricht der Export ab.

## Phase 2 – Opener-Prompt prüfen (nur voller Lauf)

`../google-maps/prompts/personalisierung_stellenanzeige.txt` ist **branchenneutral** und passt für die meisten Berufe. Branchengenaue Fassungen liegen in `../google-maps/prompts/beispiele/` (`personalisierung_stellenanzeige_logistik.txt`, `…_ki.txt`). Zum Anpassen eine Fassung als `prompts/personalisierung_stellenanzeige.txt` in die Kampagne kopieren und dort ändern – Struktur behalten. Standard-Prompts nie direkt ändern. Änderungen in der Auftragsdatei unter „Prompt-Anpassungen“ festhalten.

Dasselbe gilt für den Größen-Check (`groessen_check.txt`), falls er nachgeschärft werden muss (Phase 5).

## Phase 3 – Suche anlegen

```bash
./scraper.sh --kampagne <name> stellensuche \
    --suche "Berufskraftfahrer,LKW-Fahrer" --orte "Stuttgart,Ulm" \
    [--umkreis 25] [--max-alter 30] [--max-seiten 3] [--nur-stellen] [--icp-prompt prompts/icp.txt] \
    [--titel-pflicht "KI,AI,RPA"] [--titel-ausschluss "SPS,Werkstudent"] [--no-groessen-check]
./scraper.sh --kampagne <name> doctor
```

Die Ausgabe nennt die Zahl der Suchen, die Obergrenze an Seiten (je 1 Credit) und ob der Größen-Check an ist. Weitere Begriffe oder Orte: denselben Befehl mit den neuen Werten erneut aufrufen – erledigte Suchen werden nicht noch einmal bezahlt.

Mehr Anzeigen aus denselben Suchen: `stellensuche --max-seiten 3` (ohne `--suche`) – volle Suchen blättern beim nächsten `run --stage 1j` weiter, Seite 1 wird nicht erneut bezahlt (außer bei Indeed aus Läufen vor dem 15.10.2026).

`doctor` erst **nach** `stellensuche` laufen lassen: Erst dann kennt er die Kampagnen-Art und prüft die passenden Prompts.

## Phase 4 – Testlauf (Pflicht)

Ziel: eine Suche je Portal, Ergebnis prüfen. Kosten vorher nennen.

```bash
./scraper.sh --kampagne <name> run --stage 1 --limit 4     # 4 Suchen, je bis 3 Seiten
./scraper.sh --kampagne <name> status
```

Dem Nutzer übersetzen: wie viele Anzeigen, wie viele wegen Alter, Zeitarbeit/Personalvermittler oder Titel raus, wie viele Firmen. Zwei, drei Beispiele mit Stelle und Firma nennen.

Passen viele Treffer nicht: Titel-Filter schärfen (`stellensuche --titel-pflicht "…"` bzw. `--titel-ausschluss "…"`, ohne `--suche`), dann **nur** `run --stage 1k` – das kostet nichts. Achtung: `run --stage all` oder `--stage 1` starten zugleich alle noch offenen Suchen.

Voller Lauf: danach die Firmen des Testlaufs prüfen und anreichern und die Kosten hochrechnen:

```bash
./scraper.sh --kampagne <name> run --stage 3g              # Größen-Check
./scraper.sh --kampagne <name> run --stage 3a --limit 30   # Website-Suche nur für 30 Firmen
./scraper.sh --kampagne <name> run --stage 3b
./scraper.sh --kampagne <name> run --stage 3c
./scraper.sh --kampagne <name> run --stage 3d
./scraper.sh --kampagne <name> run --stage 4
./scraper.sh --kampagne <name> status                      # „Skael-Kosten bisher“ = echte Credits
```

Nicht `run --stage 3` nehmen: Das sucht die Website für **alle** Firmen des Testlaufs, ohne Begrenzung.

Kostentreiber im vollen Lauf: die Website-Suche (rund 15–25 Credits je Firma ohne Website im Portal), dann Impressum, E-Mail-Suche/-Prüfung und 2 KI-Aufrufe je Firma mit Website. Der Größen-Check läuft davor (ein KI-Aufruf je Firma, keine Skael-Credits für Datenabfragen; im Lauf vom 15.10.2026 wären so 114 von 306 Leads weggefallen) – die Website-Suche wird nur für die verbleibenden Firmen bezahlt. Kostenschätzung deshalb erst nach `run --stage 3g` machen. `status` zeigt die bisher wirklich abgerechneten Skael-Credits; damit hochrechnen statt mit Listenpreisen.

## Phase 5 – Stichprobe

5 Firmen prüfen (SQL-Beispiele in `../google-maps/docs/08_STELLENSUCHE.md`):

- Gibt es die Anzeige wirklich und ist sie aktuell? (`stelle_url` im Browser öffnen, `stelle_datum`)
- Ist die Firma der echte Arbeitgeber und kein Vermittler mit neutralem Namen? Treffer → `PERSONALDIENSTLEISTER_EXTRA` in `kampagne.env` ergänzen.
- Stimmt die Website (`domain_status` = `verified` oder `portal`)?
- Ist der Opener sauber und beginnt mit „ich habe gesehen, dass Sie gerade jemanden als … suchen“?
- Größen-Check: 3–5 Firmen aus Liste 4 mit Einstufung „Größen-Check: …“ ansehen – ist das wirklich ein Konzern, eine Behörde oder ein IT-Anbieter? Und umgekehrt: Ist in den Lead-Listen noch ein bekannter Konzern? Häufen sich Fehler, `groessen_check.txt` in die Kampagne kopieren, dort schärfen und nur die Größen-Prüfung neu laufen lassen (`groesse_kategorie`, `groesse_raw` auf NULL setzen, betroffene `is_icp` zurücksetzen, `run --stage 3g`).

Gemessene Quoten in `../../wissen/18_pfad-stellensuche.md`, Abschnitt „Quoten“ eintragen. Erst dann Vollstart mit Kostenschätzung und Freigabe (`run --stage all` ohne `--limit`).

## Phase 6 – Export und Abschluss

```bash
./scraper.sh --kampagne <name> export
```

Die Listen liegen in `kampagnen/<name>/exports/`.

- `0_stellen_…` = alle Anzeigen, eine Zeile je Anzeige.
- Voller Lauf: Listen 1–5 wie gewohnt, eine Zeile je Firma, mit Stellenspalten. Firmen, die nach der Anreicherung noch herausgefallen sind (Größen-Check, geschärfter Titel-Filter), stehen nur noch in Liste 4.
- Nur Stellenliste: `1_firmen_mit_stellen_…` und Liste 5. **Nicht versandfertig** – ohne Website kein Sperrlisten-Abgleich, keine Kontaktdaten.

Zahlen nennen: Anzeigen gefunden, raus (Alter, Zeitarbeit/Personalvermittler, Titel, ohne Firma), Firmen, davon per Größen-Check aussortiert (Konzern, öffentlich/Verband, IT-Wettbewerber), mit Website, mit E-Mail, versandfertig, persönliche vs. neutrale Ansprache (Spalte „Ansprache“), gesperrt. Hinweise für den Versand wie in `../../SKILL.md`, Schritt 4.
