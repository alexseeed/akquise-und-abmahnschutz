# Stellensuche (Jobportale) im Scraper-Programm

Technische Referenz der Kampagnen-Art `stellensuche`: konkrete Stellenanzeigen aus Jobportalen über Skael.
Fachlicher Hintergrund: `../../../wissen/18_pfad-stellensuche.md` · Anleitung: `../../stellensuche/ABLAUF.md`.
Der zweite Recruiting-Weg über die Firmen-Website: `07_RECRUITING.md`.

---

## 0. Einordnung

```
stellensuche  stellensuche-Befehl ─► 1j → 1k ─┬─ nur Stellenliste ─► Export (0_stellen, 1_firmen_mit_stellen, 5)
                                              └─ 3g (Größen-Check) → 3a (find_domain) → 3b → 3c → 3d ─► 4a … 4h (strecke rc) ─► Export
```

`run --stage all` ruft alle Stufen auf; jede prüft selbst, ob sie zur Kampagne gehört. Stufen, die nur die Stellensuche hat, melden bei anderen Arten „übersprungen“. Eine Kampagne hat genau eine Art; für eine Stellensuche also eine eigene Kampagne anlegen (`neue-kampagne <name>`).

| Stufe | Funktion | Dienst | Kosten |
|---|---|---|---|
| 1j | `pipeline.stufe1j_stellensuche` | `indeed_jobs`, `stepstone_jobs`, `arbeitsagentur_jobs`, `kununu_jobs` | 1 Credit je Seite (bis 100 Anzeigen) |
| 1k | `pipeline.stufe1k_firmen` | – | 0 |
| 3g | `pipeline.stufe3g_groesse` | KI (`MODEL_GROESSE`) | ein KI-Aufruf je Firma, keine Skael-Credits für Datenabfragen |
| 3a | `pipeline._domains_stellensuche` | `find_domain` (asynchron) | ~15–25 Credits je Firma ohne Website (nicht für Aussortierte aus 3g) |
| 3b | `pipeline.stufe3b_dedupe` + `_stellen_nach_dedupe` | – | 0 |
| 3c | `pipeline.stufe3c_icp` | `icp_checker` nur mit Prüfprofil | 0 ohne Profil |
| 3d–4h | wie Recruiting, Strecke `rc` | wie Google Maps | wie Google Maps |

Die echten Credits je Dienst bucht der Kostenzähler in die Tabelle `kosten`; `status` zeigt die Summe als „Skael-Kosten bisher“.

## 1. Anlegen (`cli stellensuche`)

```bash
./scraper.sh --kampagne <k> stellensuche --suche "A,B" (--orte "X,Y" | --min-population N) \
    [--land DE] [--portale indeed,stepstone,arbeitsagentur,kununu] [--max-alter 30] [--max-seiten 3] \
    [--umkreis 25] [--nur-stellen | --no-nur-stellen] [--titel-ausschluss "SPS,Elektro"] \
    [--titel-pflicht "KI,AI,RPA"] [--groessen-check | --no-groessen-check] [--icp-prompt <datei>] \
    [--opener-prompt <datei>]
```

- Eine Zeile je Portal × Suchbegriff × Ort in `stellen_suche` (eindeutig, erneuter Aufruf legt nichts doppelt an).
- Ohne `--suche`: nur Einstellungen der Kampagne ändern (z. B. `--max-seiten 3 --max-alter 60`); die Ausgabe nennt, wie viele erledigte Suchen weiterblättern und was das höchstens kostet.
- Ohne `--orte` und `--min-population`: eine Suche ohne Ort (landesweit).
- `--min-population` holt die Städte einmalig über `find_cities` (1 Aufruf).
- Portale, die das Land nicht abdecken (`PORTALE` in `config.py`), werden mit Hinweis übersprungen.
- Prüfprofil: `--icp-prompt`, sonst `kampagnen/<k>/prompts/icp.txt`, falls vorhanden. Eine unveränderte Vorlage (mit `[[Platzhaltern]]`) wird übergangen – dann läuft die Stellensuche ohne Profil.
- Opener: `--opener-prompt <name>` wählt eine Datei aus `kampagnen/<k>/prompts/` oder `prompts/` (gespeichert in `run_meta.opener_prompt`); Standard `personalisierung_stellenanzeige.txt`. Dateien in `prompts/beispiele/` vorher in die Kampagne kopieren.
- Einstellungen je Kampagne in `run_meta`: `stellen_max_alter`, `stellen_max_seiten`, `stellen_umkreis`, `nur_stellen`, `groessen_check` (Standard an), `titel_ausschluss`, `titel_pflicht`, `icp_prompt`, `opener_prompt`. Ohne Angabe gelten `.env` bzw. `kampagne.env` (`STELLEN_MAX_ALTER`, `STELLEN_MAX_SEITEN`, `STELLEN_UMKREIS`).

## 2. Stufe 1j – Portale abfragen

- Offene Suchen: `status != 'done' AND attempts < 3`, mit `run --limit n` nur n Suchen.
- Je Suche Seite 1 bis `stellen_max_seiten`; weiter nur, solange das Portal weitere Seiten meldet (`stellen.naechste_seite`).
- **Weiterblättern:** Erledigte Suchen mit `weiter = 1` (bzw. bei älteren Läufen: letzte Seite voll) machen bei höherem `stellen_max_seiten` ab der nächsten Seite weiter. Indeed braucht den gespeicherten Blätter-Code (`cursor`); fehlt er, wird ab Seite 1 neu abgefragt. Gemessen am 15.10.2026: 474 volle Suchen auf 3 Seiten erweitert = 891 Credits, +11.900 Anzeigen, +311 Firmen.
- Fehler (z. B. Kununu 503): `note_failure`, die Suche bleibt offen und startet beim nächsten Lauf neu. Schon gespeicherte Anzeigen werden per `UNIQUE(portal, portal_id)` nur aktualisiert.
- Jede Anzeige bekommt sofort `ausschluss` (`stellen.ausschluss`):

| Grund | Regel |
|---|---|
| `ohne Firmenname` | weder Firmenname noch Website noch eigener Bewerbungslink |
| `Jobbörse/Bewerbersystem statt Firma` | Firmenname enthält einen Eintrag aus `FREMD_DOMAINS_STELLEN` (z. B. wenn Indeed keinen Namen nennt) |
| `Personaldienstleister` | Firmenname enthält einen Eintrag aus `PERSONALDIENSTLEISTER` (Zeitarbeit, Personalvermittler, Personalberatung, bekannte Namen) + `PERSONALDIENSTLEISTER_EXTRA` |
| `älter als n Tage` | Veröffentlichung vor heute − `stellen_max_alter` |
| `Titel enthält „…“` | Stellenbezeichnung enthält einen Wortteil aus `titel_ausschluss` (z. B. „sps“ gegen Industrieautomation) |
| `Titel passt nicht zur Suche` | `titel_pflicht` gesetzt und kein Begriff daraus in der Stellenbezeichnung; Begriffe bis 3 Zeichen nur als ganzes Wort (`stellen.titel_enthaelt`) |

Stufe 1k wendet alle Filter mit den aktuellen Einstellungen auf **alle** gespeicherten Anzeigen neu an. Filter nach dem Testlauf ändern: `stellensuche … --titel-pflicht/--titel-ausschluss/--max-alter` erneut aufrufen, dann `run --stage 1k` (bzw. `all`, das aber offene Suchen startet). Kostet nichts. Firmen, deren Anzeigen alle herausfallen, sortiert 3b aus (`dropped_excluded`).

**Indeed sucht unscharf:** Zu „KI Manager“ kommen auch „Sales Manager“ oder „Office Managerin“. Bei Rollen mit Allerweltswort (Manager, Experte, Specialist) immer `--titel-pflicht` setzen.

### Anfrage je Portal (`stellen.anfrage`)

| Portal | Parameter |
|---|---|
| indeed | `query`, `location`, `country` (klein), `radius` ≤ 100 + `radius_unit=KILOMETERS`, `sort=date`, `limit=100`, `cursor` |
| stepstone | `query`, `location`, `country`, `radius` ≤ 200, `sort=date`, `date_posted` (kleinste Stufe 1/3/7/30 ≥ Alter), `page`, `limit=100` |
| arbeitsagentur | `was`, `wo`, `umkreis` (10/25/50/100/150/200), `angebotsart=1`, `zeitarbeit=false`, `pav=false`, `veroeffentlichtseit`, `page`, `size=100` |
| kununu | `query`, `country`, `location`, `radius` (10/20/30/50/100/200), `sort=newest`, `page` |

Leere Werte werden nicht gesendet (`SkaelClient.stellen_suche`).

### Antwortformate (`stellen.stellen_aus_antwort`), geprüft am 14.10.2026

| Portal | Liste | Firma | Website | Datum | Link |
|---|---|---|---|---|---|
| indeed | `data.jobs[]` | `company.name` (kann `null` sein) | `company.website` (kann Jobseite der Firma sein → Host) | `date_published` `YYYY-MM-DD hh:mm:ss` | kein `url` → `https://de.indeed.com/viewjob?jk=<id>`; `apply_url` oft auf Firmendomain |
| stepstone | `data.jobs[]` | `company.name` | `company.url` (praktisch immer `null`) | `date_posted` ISO | `url` |
| arbeitsagentur | `data.stellenangebote[]` (sonst `data.ergebnisliste[]`) | `arbeitgeber` / `firma` | – | `aktuelleVeroeffentlichungsdatum` | `https://www.arbeitsagentur.de/jobsuche/jobdetail/<refnr>` |
| kununu | `data[]` | `company.name` | `company.website` | `postedAt` | `url` |

Websites und Bewerbungslinks auf Jobbörsen oder Bewerbermanagement-Systemen (`FREMD_DOMAINS_STELLEN`, z. B. personio, softgarden, heyjobs, gohiring, hibob, heyrecruit) zählen nie als Firmen-Website.

### Stellentext (`stellen.beschreibung_bereinigen`)

HTML → Klartext; ab dem ersten Kontakt-Signal („Ansprechpartner“, „Bei Interesse“, „Haben wir Ihr Interesse“ …, sofern davor mindestens 20 Zeichen Text stehen) abgeschnitten; E-Mail-Adressen und Telefonnummern entfernt; höchstens `STELLEN_BESCHREIBUNG_MAX` (4.000) Zeichen. Der Text dient nur dem Opener. Die Rohantwort bleibt in `stellen.raw` (lokale Datenbank, wird nicht exportiert).

## 3. Stufe 1k – Firmen bilden

- Nur übernommene Anzeigen (`ausschluss IS NULL`).
- Schlüssel: `web:<host>` (Website laut Portal) → sonst `name:<bereinigter Firmenname>` (`stellen.firmen_name_schluessel`: ohne Rechtsform, Niederlassungs-Zusatz, Satzzeichen) → sonst `hinweis:<Host des Bewerbungslinks>`.
- Nennt irgendein Portal für einen Namen eine Website, gilt sie für alle Anzeigen dieses Namens (spart `find_domain`).
- Je Schlüssel eine Zeile in `datensaetze` (`business_id = stelle:<schlüssel>`, `quelle='stellen'`, `stelle_vorhanden=1`). Die Firma vertritt die „beste Stelle“: mit Stellentext vor ohne, dann die neueste (`stellen.beste_stelle`).
- Erneuter Lauf aktualisiert Stellenfelder und Zähler, überschreibt aber keine Website aus 3a.

## 4. Stufe 3g – Größen-Check (vor der Website-Suche)

Das Prüfprofil (3c) sieht nur die Startseite. Dort zeigen Zalando, Miele, CHECK24 & Co. weder Mitarbeiterzahl noch Investor Relations – Konzerne rutschten im Lauf vom 15.10.2026 deshalb durch. 3g fragt stattdessen das **Modellwissen** ab, bevor `find_domain` bezahlt wird.

- Firmen: `quelle='stellen'`, `dedupe_status='kept'`, `groesse_kategorie IS NULL`, `attempts < 3` – also auch Firmen mit Website laut Portal (sie werden so vor 3c geprüft). Nicht im Modus „nur Stellenliste“.
- Abschaltbar je Kampagne: `stellensuche --no-groessen-check` (`run_meta.groessen_check = false`), wieder an mit `--groessen-check`. Standard: an.
- KI-Aufruf `LLM.groessen_check(firmenname, website, ort)`: Prompt `prompts/groessen_check.txt`, Schema `prompts/groessen_check.schema.json` (`kategorie`, `mitarbeitende_schaetzung`, `begruendung`), Temperatur 0, ohne Websuche. Modell `MODEL_GROESSE`: Standard `skael/smart` bei `LLM_PROVIDER=skael`, `gpt-4.1` bei `LLM_PROVIDER=openai`. gpt-4o-mini stufte im Vergleich zu viele Konzerne als Mittelstand ein.
- Kategorien: `mittelstand`, `konzern` (> ~1.000 Mitarbeitende, börsennotiert, Konzerntochter/-marke, große Filialkette), `oeffentlich_verband` (Behörde, Kommune, Hochschule, Stadtwerke, Sparkasse, Kirche, Verband, Verein, Stiftung), `it_wettbewerber` (verkauft selbst IT-, Software-, KI-, Automatisierungsleistungen), `unbekannt`. Unbekannte Antworten zählen als `unbekannt`.
- Ergebnis: `groesse_raw` (JSON), `groesse_kategorie`. Bei `konzern`, `oeffentlich_verband`, `it_wettbewerber` (`pipeline.GROESSE_AUSSCHLUSS`): `is_icp=0`, `icp_label='False'`, `icp_confidence=NULL`, `icp_reason = "Größen-Check: Konzern (über 10.000 Mitarbeitende) – <Begründung>"`. Die Dedupe bleibt `kept`, die Firma steht in Liste 4 mit Einstufung „Größen-Check: Konzern“ usw. `mittelstand` und `unbekannt` laufen normal weiter.
- Fehler (KI nicht erreichbar): `note_failure`, `groesse_kategorie` bleibt leer, nächster Lauf versucht erneut.
- **Reihenfolge erzwungen:** Ist der Check an, nehmen 3a und 3c nur Firmen mit gesetzter `groesse_kategorie` (`pipeline._groesse_bedingung`); Aussortierte prüfen sie nie. Wer `run --stage 3a` vor 3g aufruft, bekommt im Log „… warten auf den Größen-Check (run --stage 3g)“.
- Bekannte Grenze: `it_wettbewerber` ist für Angebote rund um IT/KI/Automatisierung gedacht. Bei anderen Angeboten (z. B. Fahrer-Recruiting) fallen IT-Firmen damit ebenfalls heraus – dann den Check abschalten oder die Liste 4 sichten.

## 5. Stufe 3a – Website per Impressum-Beleg

Nur Firmen mit `quelle='stellen'`, leerer Website und `domain_status IS NULL`, bei aktivem Größen-Check nur nach 3g und nicht aussortiert. Nicht im Modus „nur Stellenliste“. Mit `run --stage 3a --limit n` nur n Firmen (Testlauf der Website-Suche).

`find_domain` mit `company_name`, `city`, `postcode` (PLZ aus der Anzeige), `country`, `context` („Arbeitgeber mit offener Stelle …“), `website` = Host eines eigenen Bewerbungslinks als Hinweis (wird zuerst geprüft, zählt aber nur mit Impressum-Beleg), `max_pages` = `FIND_DOMAIN_MAX_PAGES` (3).

- `status = verified` → `website = https://<domain>`, `domain_status = verified`.
- noch nicht fertig (`queued`, `processing`, `waiting`, `timeout`) → `note_failure`, nächster Lauf holt erneut ab; nie als „nichts gefunden“ gespeichert.
- sonst → Website bleibt leer, `domain_status` = `unverified`/`none`; Export Liste 4 „keine eigene Website gefunden“.
- Antwort in `domain_raw`. Die KI-Domainsuche der anderen Pfade (`DOMAINSUCHE`) wird hier nicht genutzt: deren geratene Domains verwirft 3b ohnehin.

`find_domain` antwortet immer mit `202`; `SkaelClient._poll` fragt `GET /api/enrichments/{id}?wait=true` ab. Ist das Ergebnis nach `wait_time` noch nicht fertig, antwortet Skael mit **HTTP 200** und `status: processing` (ohne `data`-Hülle) – der Client fragt dann weiter, 3a speichert unfertige Antworten nie als Ergebnis.

**Rate-Limit:** Skael bremst `find_domain` ab ca. 12 gleichzeitigen Aufträgen mit 429. Der Client wartet dann 5, 10, 20, 40 s (höchstens 60 s) plus einen Zufallsanteil bis 1 s (Jitter), damit parallele Aufträge nicht gleichzeitig wiederkommen. Parallelität über `MAX_CONCURRENCY`.

## 6. Stufe 3b–3d

- 3b: Dedupe wie immer über den Host. Danach `_stellen_nach_dedupe`: Anzeigen doppelter Firmen gehen an die behaltene Zeile, `stellen_anzahl` und `stellen_portale` werden neu gezählt.
- 3c: mit Prüfprofil wie Google Maps. Ohne Profil: alle behaltenen Firmen mit Website `is_icp=1` („ohne Prüfprofil: offene Stelle ist das Kriterium“). Beides ohne die vom Größen-Check Aussortierten.
- 3d: Übergabe `is_icp=1`, Strecke `rc`, mit `stelle_url`, `stelle_portal`, `stelle_datum`, `stelle_ort`, `stelle_gehalt`, `stellen_anzahl`, `stellen_portale`.
- 4e/4h: wie Recruiting RC (Jobtitel normalisieren → Opener aus `run_meta.opener_prompt`; kein Videotitel). Ohne Stellentext (Stepstone, Arbeitsagentur, Kununu) endet der Opener nach „… suchen.“.

## 7. Datenmodell

**`stellen_suche`**: `portal`, `suchbegriff`, `ort`, `land`, `seiten` (zuletzt abgerufene Seite), `treffer`, `weiter`, `cursor`, `status`, `attempts`, `error`.

**`stellen`**: `suche_id`, `portal`, `portal_id`, `suchbegriff`, `titel`, `firma`, `ort`, `plz`, `land`, `veroeffentlicht`, `url`, `bewerben_url`, `website`, `gehalt`, `beschreibung`, `ausschluss`, `datensatz_id`, `raw`.

**`datensaetze`** zusätzlich: `stelle_portal`, `stelle_datum`, `stelle_ort`, `stelle_gehalt`, `stellen_anzahl`, `stellen_portale`, `domain_raw`, `domain_status` (`portal`/`verified`/`unverified`/`none`), `groesse_raw`, `groesse_kategorie` (3g).

**`anreicherung`** zusätzlich: `stelle_url`, `stelle_portal`, `stelle_datum`, `stelle_ort`, `stelle_gehalt`, `stellen_anzahl`, `stellen_portale`.

**`kosten`** (alle Arten): `endpoint`, `aufrufe`, `credits` – echte Skael-Credits je Dienst aus `credits_cost` der fertigen Aufträge.

Ältere Datenbanken werden beim Start nachgerüstet (`db._MIGRATIONS`).

## 8. Export

| Datei | Quelle | Spalten |
|---|---|---|
| `0_stellen_…` | `stellen` (übernommen) ⟕ `datensaetze` ⟕ `anreicherung`, ohne Sperrlisten-Treffer | Firma, Stellenbezeichnung, Ort, PLZ, veröffentlicht am, Portal, Link zur Anzeige, Gehalt, Website, Suchbegriff, Firma in Lead-Liste |
| `1_…`–`5_…` | wie alle Arten | zusätzlich Jobtitel, Stellenbezeichnung, Ort der Stelle, veröffentlicht am, Portal, Link zur Anzeige, Gehalt, Offene Stellen (Anzahl), Gefunden auf; dazu `Ansprache`, `Ansprache Grund`, `Anrede Sicherheit`, `Kampagnen-Art` |
| `4_nicht_zielgruppe_…` | wie alle Arten | vom Größen-Check Aussortierte mit Einstufung „Größen-Check: Konzern“ / „… öffentliche Hand/Verband“ / „… IT-Wettbewerber“, Details in „Begründung“ |
| nur Stellenliste | `1_firmen_mit_stellen_…`, `5_gesperrt_…` | Firmenspalten + Stellenspalten; keine Listen 2–4, kein JSON-Archiv |

Leads, die nach der Anreicherung nicht mehr `kept` sind (z. B. geschärfter Titel-Filter) oder später `is_icp=0` bekamen (z. B. Größen-Check), schreibt der Export nicht mehr in Liste 1 oder 2. Firmen ohne Sicherheitswert (Größen-Check setzt `icp_confidence=NULL`) landen dank `COALESCE` in Liste 4 statt in keiner Liste.

## 9. Stichprobe per SQL

Die Datenbank liegt in `kampagnen/<k>/data/leads.db`.

```bash
# Anzeigen und warum welche rausflogen
sqlite3 kampagnen/<k>/data/leads.db -header -column \
  "SELECT portal, COALESCE(ausschluss,'übernommen') stand, COUNT(*) n FROM stellen GROUP BY 1,2 ORDER BY 1,3 DESC;"

# Firmen mit den meisten Stellen
sqlite3 kampagnen/<k>/data/leads.db -header -column \
  "SELECT firmenname, stellen_anzahl, stellen_portale, domain_status, website_final, job_title
     FROM datensaetze WHERE dedupe_status='kept' ORDER BY stellen_anzahl DESC LIMIT 20;"

# Größen-Check: was fiel raus?
sqlite3 kampagnen/<k>/data/leads.db -header -column \
  "SELECT groesse_kategorie, COUNT(*) n FROM datensaetze WHERE dedupe_status='kept' GROUP BY 1 ORDER BY 2 DESC;"

# Opener je Lead
sqlite3 kampagnen/<k>/data/leads.db -header -column \
  "SELECT firmenname_final, job_title, stelle_datum, personalisierung FROM anreicherung LIMIT 10;"

# echte Skael-Kosten je Dienst
sqlite3 kampagnen/<k>/data/leads.db -header -column \
  "SELECT endpoint, aufrufe, credits FROM kosten ORDER BY credits DESC;"
```

Dem Nutzer nie die Tabelle zeigen, sondern übersetzen (Regeln in `../CLAUDE.md`).

## 10. Tests

`tests/test_pfade.py`, Klassen `TestStellensuche` und `TestStellenFunktionen`: voller Lauf mit allen vier Portalen (Kununu fällt aus, die anderen laufen weiter), Größen-Check vor der Website-Suche (Konzern ohne `find_domain`, Einstufung in Liste 4), `--no-groessen-check`, KI-Fehler hält die Website-Suche an, eigener Opener-Prompt je Kampagne, nur Stellenliste ohne KI und ohne `find_domain`, erneuter Lauf ohne Doppelungen, Titel-Ausschluss nachträglich ohne neue Abfrage, Weiterblättern nach Erhöhung der Seitenzahl, Ablehnung einer zweiten Kampagnen-Art in derselben Datenbank, Parameter je Portal, Ausschluss und Firmenschlüssel, Titel-Pflicht mit Wortgrenzen, Stellentext ohne Kontaktblock.

```bash
python3 -m unittest discover -s tests -v
```
