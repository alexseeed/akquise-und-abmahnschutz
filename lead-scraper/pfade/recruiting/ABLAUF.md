# Ablauf Recruiting-Pfad (Firmen-Website) – Anleitung für die KI

**Vorher lesen:** die Auftragsdatei in `auftraege/…md`. Frag nur, was dort fehlt.
**Hintergrund:** `../../wissen/05_pfad-recruiting.md` · **Technik:** `../google-maps/docs/07_RECRUITING.md`
**Programm:** Der Pfad läuft lokal im Scraper-Programm `../google-maps/` (dasselbe Programm wie Google Maps). Alle Befehle dort ausführen; Bedienregeln und Erstinbetriebnahme: `../google-maps/CLAUDE.md`.

Jede Zielgruppe ist eine **eigene Kampagne** unter `../google-maps/kampagnen/<name>/` (eigene `kampagne.env`, eigene Prompts, Datenbank und Exporte). Vor jedem Befehl `--kampagne <name>`. `./scraper.sh` sucht selbst ein Python ≥ 3.10; sonst `python3 -m scraper` (auf dem Mac ggf. `python3.12`).


**Weg noch offen?** Sind Beruf und Branche bekannt und ist unklar, ob Firmen-Website oder Jobportale besser liefern: erst den Testballon anbieten (`../google-maps/docs/09_TESTBALLON.md`). Er fährt beide Wege mit je ~100 Leads und vergleicht sie.

---

## Phase 0 – Zusatzfragen (nur, was die Auftragsdatei nicht beantwortet)

Eine Frage pro Nachricht, immer mit Beispiel:

| # | Frage | Beispiel | Wofür |
|---|---|---|---|
| R1 | „Welche Stellen sollen die Firmen gerade ausgeschrieben haben?“ | „Zum Beispiel Berufskraftfahrer, Disponenten, Lageristen – das Wichtigste zuerst.“ | `--berufe` (Reihenfolge = Priorität) |
| R2 | „In welcher Branche und Region suchen wir die Firmen?“ | „Zum Beispiel Speditionen in Baden-Württemberg – ich schaue dann auf jeder Website nach offenen Stellen.“ | `--keywords`, `--countries`, `--min-population` |
| R3 | „Was ist mit passenden Firmen, die gerade **keine** Stelle ausgeschrieben haben – auch anschreiben, mit einem Satz zu ihrer Website?“ | „Ja, oder nur Firmen mit offener Stelle.“ | `--nk` |
| R4 | „Wen willst du erreichen – Geschäftsführung oder Personalabteilung?“ | „Bei kleinen Firmen meist die Geschäftsführung.“ | Der Pfad sucht die Geschäftsführung aus dem Impressum |

Kennt der Nutzer den **Beruf**, aber nicht die Branche der Firmen („alle, die Berufskraftfahrer suchen“), passt der andere Weg besser: `../stellensuche/ABLAUF.md`.

## Phase 1 – Kampagne anlegen und Voraussetzungen

1. `./scraper.sh neue-kampagne <name>` (z. B. `spedition-bw`).
2. `.env` im Projektordner: `SKAEL_API_KEY`. Die KI-Schritte laufen standardmäßig über Skael. Ein `OPENAI_API_KEY` ist nur nötig, wenn `LLM_PROVIDER=openai` oder `DOMAINSUCHE=openai` gesetzt ist.
3. `kampagne.env` der Kampagne ausfüllen. Für Recruiting:
   - `DO_VIDEO_TITLE=false` (der Pfad schreibt keine Videotitel).
   - `ABSATZ_EINLEITUNG` leer lassen – der Opener beginnt selbst mit „ich habe gesehen, …“. `ABSATZ_FOLGESATZ` = Überleitung zum Angebot, `ABSATZ_STANDARD` = Absatz für Leads ohne Satz.
   - `KATEGORIE_NORMALFALL` wird hier nicht gebraucht; Zeile löschen oder leeren.
   - Optional `NK_ON=true` statt `init --nk`.
4. `prompts/pain_kategorie.*` und `prompts/personalisierung.txt` der Vorlage braucht Recruiting nicht; löschen.
5. Sperrliste ladbar (`doctor`, Zeile „Community-Sperrliste“). Sonst bricht der Export ab.

## Phase 2 – Prompts auf die Zielgruppe einstellen

Die Standard-Prompts in `../google-maps/prompts/` sind **branchenneutral**. Die gesuchten Berufe kommen aus `init --berufe` in den Stellen-Prompt (Platzhalter `{{Gesuchte Berufe}}`); ohne `--berufe` zählt jede offene Stelle.

| Datei | Was tun |
|---|---|
| `kampagnen/<name>/prompts/icp.txt` (Prüfprofil) | Pflicht. Nach `../google-maps/prompts/icp_prompt_builder.md` bauen; Beispiel `../google-maps/prompts/beispiele/icp_logistik.txt` |
| `stellenanalyse.txt` | meist unverändert. Für eine branchengenaue Fassung mit Ausschlüssen und Prioritäten `../google-maps/prompts/beispiele/stellenanalyse_logistik.txt` als `prompts/stellenanalyse.txt` in die Kampagne kopieren und anpassen |
| `personalisierung_stellenanzeige.txt` (Opener) | meist unverändert. Branchengenaue Fassungen: `../google-maps/prompts/beispiele/personalisierung_stellenanzeige_logistik.txt`, `…_ki.txt` – als `prompts/personalisierung_stellenanzeige.txt` in die Kampagne kopieren |

Das Programm sucht jeden Prompt zuerst in `kampagnen/<name>/prompts/`, dann in `../google-maps/prompts/`. Standard-Prompts nie direkt ändern. Änderungen in der Auftragsdatei unter „Prompt-Anpassungen“ festhalten.

## Phase 3 – Suche anlegen

Firmen über Google Maps finden; die offene Stelle wird danach auf der Website jeder passenden Firma gesucht (Startseite + Karriere-Seiten).

```bash
./scraper.sh --kampagne <name> init --pfad recruiting \
    --keywords "Spedition,Logistik" --countries DE --min-population 200000 \
    --berufe "Berufskraftfahrer,Disponent,Lagerist"  [--nk]
./scraper.sh --kampagne <name> doctor
```

Ohne `--icp-prompt` nimmt `init` das `kampagnen/<name>/prompts/icp.txt`. `doctor` erst **nach** `init` laufen lassen: Erst dann kennt er die Kampagnen-Art und prüft die Recruiting-Prompts. Es darf kein ✗ mehr erscheinen.

## Phase 4 – Testlauf (Pflicht)

Ziel: 20–30 Firmen. Kosten vorher nennen.

```bash
./scraper.sh --kampagne <name> run --stage 1
./scraper.sh --kampagne <name> run --stage 2 --limit 2     # nur 2 Städte
./scraper.sh --kampagne <name> run --stage 3               # Dedupe, Profil, Stellen
./scraper.sh --kampagne <name> run --stage 4
./scraper.sh --kampagne <name> status
```

Kostentreiber: Maps-Suchen (Keywords × Städte), je Firma ein Profil-Check, je passender Firma 1–3 Website-Abrufe + 1 KI-Aufruf (Stellen), je Firma mit Stelle Impressum, E-Mail-Suche/-Prüfung und 3 KI-Aufrufe. `status` zeigt nach dem Testlauf die echten Skael-Kosten („Skael-Kosten bisher“) – damit hochrechnen.

## Phase 5 – Stichprobe

5 Firmen prüfen (SQL-Beispiele in `../google-maps/docs/07_RECRUITING.md`, Tabellen `datensaetze`/`anreicherung`):

- Passt die Firma? (`icp_reason`)
- Gibt es die Stelle wirklich? (`job_title`, `stelle_url` im Browser öffnen)
- Ist der Opener grammatisch sauber und beginnt mit „ich habe gesehen, dass Sie gerade jemanden als … suchen“?
- Stimmt der Geschäftsführer?

Gemessene Quoten in `../../wissen/05_pfad-recruiting.md`, Abschnitt „Quoten“ eintragen. Erst dann Vollstart mit Kostenschätzung und Freigabe (`run --stage all` ohne `--limit`).

Profil, Berufe oder Stellen-Prompt nachschärfen, ohne neu zu suchen:

```bash
./scraper.sh --kampagne <name> init --pfad recruiting --keywords "…" --countries DE --berufe "…"   # gleiche Werte, neue Berufe
sqlite3 kampagnen/<name>/data/leads.db "UPDATE datensaetze SET stelle_vorhanden=NULL, stelle_raw=NULL, attempts=0 WHERE is_icp=1;"
./scraper.sh --kampagne <name> run --stage 3e
```

(Die Startseiten sind gespeichert und werden nicht erneut bezahlt; nur die Karriere-Seiten und die KI laufen neu. Ein erneuter `init` mit denselben Suchbegriffen legt nichts doppelt an.)

Firmen ohne Stelle später doch anschreiben: `NK_ON=true` in `kampagne.env`, dann `run --stage 3d` und `run --stage 4`.

## Phase 6 – Export und Abschluss

```bash
./scraper.sh --kampagne <name> export
```

Die Listen liegen in `kampagnen/<name>/exports/`. Der Export gleicht selbst mit der Sperrliste ab (Liste 5). Liste 4 enthält auch passende Firmen **ohne** offene Stelle, wenn die NK-Strecke aus ist. Zahlen nennen: Firmen gefunden, passend, mit Stelle, mit E-Mail, versandfertig, persönliche vs. neutrale Ansprache (Spalte „Ansprache“: persönlich nur bei Anrede-Sicherheit > 60), gesperrt. Hinweise für den Versand wie in `../../SKILL.md`, Schritt 4.
