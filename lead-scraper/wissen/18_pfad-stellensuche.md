# Pfad „Stellensuche“ – Recruiting über Jobportale

**Zweck:** was der Pfad tut, was er voraussetzt, was herauskommt und wo seine Grenzen liegen.
**Für wen:** Nutzer und KI-Modelle, die einen Stellensuche-Lauf planen oder Ergebnisse verstehen wollen.
**Verwandt:** `05_pfad-recruiting.md` · `02_zielgruppen-interview.md` · `07_lead-ausgabe-und-spalten.md` · `08_versand-und-recht.md` · `11_zugaenge-und-kosten.md`
**Technik im Detail:**

- Anleitung für die KI: `pfade/stellensuche/ABLAUF.md`
- Stufen, Datenfelder, Antwortformate: `pfade/google-maps/docs/08_STELLENSUCHE.md`

**Stand:** 2026-11-01 · **Prüfen bis:** 2027-02-01. Offline getestet. Die Antwortformate der Portale wurden am 14.10.2026 live geprüft (Indeed, Stepstone, Arbeitsagentur; Kununu war an dem Tag nicht erreichbar). Erster echter Lauf am 15.10.2026 (Abschnitt „Quoten“).

---

## Unterschied zum Pfad Recruiting

| | Recruiting | Stellensuche |
|---|---|---|
| Ausgangspunkt | Branche + Region → Firmen bei Google Maps | **Suchbegriff** (Beruf) + Orte → **Anzeigen in Jobportalen** |
| Stelle erkannt durch | KI liest die Firmen-Website und Karriereseiten | das Portal liefert die Anzeige direkt |
| findet | Firmen, die auf der **eigenen Website** ausschreiben | Firmen, die **über Portale** ausschreiben (Indeed, Stepstone, Arbeitsagentur, Kununu) |
| Stellen je Firma | genau eine | alle gefundenen, gebündelt je Firma |
| Datum der Anzeige | unbekannt | bekannt, Filter „nicht älter als n Tage“ |

Beide Pfade ergänzen sich: Kleine Betriebe schreiben oft nur auf der eigenen Website aus, größere fast immer über Portale. Faustregel im Interview: Beruf bekannt → Stellensuche; nur Branche bekannt → Recruiting. Sind beide bekannt, entscheidet der **Testballon**. Er fährt beide Wege mit je ~100 Leads und vergleicht sie (`pfade/google-maps/docs/09_TESTBALLON.md`). Gibt es zu wenige Anzeigen, erweitert er das Suchfenster und ergänzt verwandte Suchbegriffe, bevor er „Markt erschöpft“ meldet.

Läuft im Scraper-Programm `pfade/google-maps/` als eigene Kampagnen-Art in einer eigenen Kampagne (`./scraper.sh --kampagne <k> stellensuche --suche … --orte …`).

## Grundsatz

Wie beim Recruiting ist der Lead die **Firma, die einstellt** (Variante A), nicht die Bewerber. Angesprochen wird die Geschäftsführung, mit Bezug auf eine echte, aktuelle Anzeige.

## Ablauf

```
Suchbegriffe × Orte × Portale
  → 1j  Portale abfragen (über Skael, je Seite bis 100 Anzeigen)
        Filter: älter als n Tage · Zeitarbeit/Personalvermittler · Jobbörse statt Firma · ohne Firmenname · Titel-Pflicht/-Ausschluss
  → 1k  Anzeigen je Firma bündeln (Website laut Portal, sonst bereinigter Firmenname)
  ┌─ nur Stellenliste (--nur-stellen): Export Stellenliste + Firmenliste, fertig
  └─ voller Lauf:
  → 3g  Größen-Check per KI aus Modellwissen: Konzerne, öffentliche Hand/Verbände, IT-Wettbewerber raus
        – vor der bezahlten Website-Suche, je Kampagne abschaltbar (--no-groessen-check)
  → 3a  eigene Website per Impressum-Beleg (Skael find_domain), nur wo das Portal keine nennt
  → 3b  Dedupe über die Website (zwei Firmennamen, eine Website = eine Firma)
  → 3c  optional Prüfprofil; ohne Profil ist die offene Stelle das Kriterium
  → 4   Impressum, Geschäftsführung, E-Mail, Anrede, Opener zur Stelle (wie Recruiting)
  → Export: Stellenliste + die fünf Listen, Sperrliste eingebaut
```

## Was die Portale liefern

| Portal | Firmen-Website | Stellentext | Datum | Besonderheit |
|---|---|---|---|---|
| Indeed | teilweise, oft über den Bewerbungslink | ja, vollständig | ja (teils sehr alt) | Firmenname fehlt manchmal; ältere Anzeigen fliegen über den Altersfilter raus |
| Stepstone | nein | nein | ja, sehr aktuell | nur DE, AT, NL, BE |
| Arbeitsagentur | nein | nein | ja | nur DE; Zeitarbeit und private Vermittler filtert das Portal selbst |
| Kununu | laut Doku ja | nein | ja | DE, AT, CH; am 14.10.2026 nicht erreichbar (Fehler 503) |

LinkedIn (nur Links) und Google Jobs (laut Skael unzuverlässig) sind bewusst nicht eingebaut.

**Folge für den Opener:** Nur Indeed liefert Anforderungen aus dem Stellentext. Hat eine Firma eine Indeed-Anzeige, vertritt diese die Firma. Ohne Stellentext endet der Satz nach der Rolle: „ich habe gesehen, dass Sie gerade jemanden als … suchen.“ – ohne Floskeln.

## Die Ausgabe

| Datei | Inhalt |
|---|---|
| `0_stellen_…csv` | **eine Zeile je Anzeige:** Firma, Stellenbezeichnung, Ort, PLZ, veröffentlicht am, Portal, Link zur Anzeige, Gehalt, Website, Suchbegriff, ob die Firma in Lead-Liste 1 oder 2 steht |
| `1_…` bis `5_…` | wie bei Google Maps, **eine Zeile je Firma**, zusätzlich: Jobtitel, Stellenbezeichnung, Ort der Stelle, veröffentlicht am, Portal, Link zur Anzeige, Gehalt, Offene Stellen (Anzahl), Gefunden auf. Vom Größen-Check Aussortierte stehen in Liste 4 („Größen-Check: Konzern“ usw.) |
| nur Stellenliste | statt 1–4: `1_firmen_mit_stellen_…csv` (Firmen ohne Kontaktdaten) |

Spalten im Detail: `07_lead-ausgabe-und-spalten.md`. Firmen auf der Community-Sperrliste fehlen auch in der Stellenliste und stehen nur in Liste 5. Im Modus „nur Stellenliste“ greift der Abgleich nur, wenn das Portal die Website nennt. Ohne Website gibt es keinen Abgleich – diese Liste ist deshalb **nicht versandfertig**.

## Kosten – wovon sie abhängen

```
Kosten ≈ Portale × Suchbegriffe × Orte × Seiten × 1 Credit                 ← Stellensuche (fast nichts)
           + Firmen × 1 KI-Aufruf Größen-Check (ohne Skael-Credits für Datenabfragen)  ← nur voller Lauf
           + Firmen ohne Website, nach Größen-Check × ~15–25 Credits (find_domain)
           + Firmen mit Website × (Impressum + E-Mail-Suche/-Prüfung + 2 KI-Aufrufe)
```

- Eine Seite mit bis zu 100 Anzeigen kostet 1 Credit (unter 0,01 €).
- Der größte Posten im vollen Lauf ist die Website-Suche: Stepstone und Arbeitsagentur nennen nur den Firmennamen.
- Der Größen-Check kostete im Lauf vom 15.10.2026 mit gpt-4.1 rund 0,3 Cent je Firma.
- `status` zeigt die echten Skael-Kosten des laufenden Projekts („Skael-Kosten bisher“, Kostenzähler); damit nach dem Testlauf hochrechnen.
- Ein Prüfprofil kostet je Firma einen Website-Check zusätzlich. Es lohnt sich, wenn der Suchbegriff viele unpassende Arbeitgeber liefert (z. B. „Fahrer“ trifft auch Pflegedienste und Bäckereien).

## Quoten

**Lauf 1 – KI/Automation, 15.10.2026** (nur Stellenliste): 13 Suchbegriffe (KI Manager, AI Engineer, Automation Manager, RPA Developer, n8n, Digitalisierungsmanager …) × 102 Städte ab 100.000 Einwohnern × 4 Portale, je 1 Seite, Umkreis 25 km, max. 30 Tage. 5.304 Suchen, 0 Fehler, rund 25 Minuten, ca. 5.300 Credits (5,30 €).

| Kennzahl | Wert |
|---|---|
| Anzeigen gesamt (eindeutig) | 28.213 – Stepstone 14.937, Indeed 7.803, Kununu 4.222, Arbeitsagentur 1.251 |
| raus: Titel passt nicht zur Suche | 20.198 (72 %) – Indeed und Stepstone suchen sehr unscharf |
| raus: älter als 30 Tage | 1.588 – fast nur Indeed (1.276) und Arbeitsagentur |
| raus: Personaldienstleister / Jobbörse als Firma / ohne Firma | 884 / 165 / 362 |
| raus: Titel-Ausschluss (Werkstudent, Ausbildung, Elektro, SPS …) | ≈ 2.800 |
| übernommen | 2.197 (7,8 %) – Stepstone 1.028, Indeed 612, Kununu 314, Arbeitsagentur 243 |
| Firmen | 1.241 (1,8 Anzeigen je Firma) |
| Firmen mit Website laut Portal | 343 (28 %) – der Rest bräuchte find_domain |
| Website per Impressum belegt (find_domain, Stichprobe 30) | 22 von 30 (73 %), Ø 22,3 Credits je Firma – belegt meist 15, erfolglos 35–55 |
| Prüfprofil bestanden – Firmen mit Website laut Portal | 46 von 343 (13 %) – Portale nennen die Website vor allem bei Großunternehmen |
| Prüfprofil bestanden – Firmen mit Website aus find_domain | 10 von 22 (45 %) – Stepstone/Arbeitsagentur-Firmen sind kleiner |
| Prüfprofil Ø Kosten | 1,97 Credits je Prüfung (505 Prüfungen, 996 Credits) |
| Weiterblättern + 60 statt 30 Tage (15.10.2026) | 474 volle Suchen auf 3 Seiten: 891 Credits, Anzeigen 28.213 → 40.103, übernommen 2.197 → 3.005, Firmen 1.240 → 1.553 (+25 %) |
| **Voller Lauf (15.10.2026)** | 1.047 Website-Suchen → 1.504 Firmen nach Dedupe → 927 Prüfungen → 335 bestanden → 321 mit Impressum → 314 mit E-Mail → **306 in den Lead-Listen** (270 Geschäftsführer, 36 info@) nach letztem Titel-Filter (Werkstudent/Trainee/Duales Studium) und Konzernliste |
| Website per Impressum belegt (voller Lauf) | ≈ 79 % (Stichprobe 73 %) |
| E-Mail-Status der 314 | 220 Safe to Send, 73 Risky (Catch-all), 21 Unknown |
| Kosten voller Lauf | 31.253 Credits (31,25 €): find_domain 23.095, E-Mail-Suche 3.680, Prüfprofil 1.844, Impressum 1.680, E-Mail-Prüfung 954 – Hochrechnung war 32.440 |
| Kosten gesamt inkl. Stellensuche und Test | 39.137 Credits (39,14 €) + OpenAI (< 1 €) → ≈ 0,13 € je Lead |
| Skael bremst find_domain | ab ca. 12 parallelen Aufträgen 429; mit 6 parallel und Backoff 5/10/20 s keine Fehler, ~14 Firmen/Minute. Seitdem wartet der Client bei 429 5/10/20/40 s plus Zufallsanteil (Jitter) |

Erkenntnisse aus Lauf 1:

- **Ohne Titel-Pflicht unbrauchbar:** Bei Allerweltswörtern (Manager, Experte, Specialist) passt nur rund jede zehnte Anzeige.
- **Weiterbildungsanbieter** schalten massenhaft Anzeigen („Werde Fachkraft für KI …“, im Lauf 250+ von zwei Anbietern). Titel-Ausschluss „werde, umschulung, weiterbildung, karriere-boost“ und Namen in `PERSONALDIENSTLEISTER_EXTRA`.
- **Bewerbersysteme** (gohiring, hibob, heyrecruit) tauchen als Firmenname auf, wenn Indeed keinen Namen nennt → stehen jetzt in `FREMD_DOMAINS_STELLEN`.
- **Konzerne und IT-Beratungen** stellen bei KI-Rollen die meisten Anzeigen je Firma (adesso, Accenture, Telekom, SAP). In der reinen Stellenliste bleiben sie stehen; aussortieren kann sie erst der Größen-Check (Stufe 3g) im vollen Lauf.
- **Prüfprofil-Falle:** Ein Profil „Anwender, der KI nutzen will“ lehnt fast alles ab, weil das Prüfmodell auf der Website nach KI-Nutzung sucht und sie nicht findet (erst 10 von 343). Richtig: Die offene Stelle als bekannt voraussetzen und nur Ausschlüsse prüfen (Wettbewerber, Konzern, öffentliche Hand, Vermittler) → 46 von 343. Vorlage: `pfade/google-maps/prompts/beispiele/icp_ki_automation.txt`.
- **Prüfprofil allein erkennt Konzerne nicht:** Das Profil „passt, solange kein Ausschluss greift“ ließ 335 Firmen durch – darunter Zalando, Vonovia, Miele, CHECK24, Bahlsen. Deren Startseiten zeigen weder Mitarbeiterzahl noch Investor Relations. Ein nachgelagerter Größen-Check per gpt-4.1 aus Modellwissen (ca. 1 €, ohne Websuche) stufte von 306 Leads 82 als Konzern, 25 als öffentliche Hand/Verband und 7 als IT-Wettbewerber ein → **191 Leads** (169 GF, 22 info@). gpt-4o-mini war dafür zu nachsichtig (nur 17 Konzerne erkannt).
- **Kosten-Lehre:** Der Größen-Check vor der Website-Suche hätte die bezahlte find_domain-Suche für rund 100 Konzerne gespart (≈ 2.200 Credits). Seit 16.10.2026 ist er deshalb feste Stufe 3g vor der Website-Suche (Standard an, `--no-groessen-check` schaltet ab); aussortierte Firmen stehen in Liste 4 mit „Größen-Check: Konzern“ usw. Das Modell ist `MODEL_GROESSE` (Standard `skael/smart` über Skael, `gpt-4.1` bei `LLM_PROVIDER=openai`). Technik: `pfade/google-maps/docs/08_STELLENSUCHE.md`, Abschnitt 4.
- **Englische Ausbildungsstellen** (Working Student, Internship, Trainee, Duales Studium) rutschen durch einen deutschen Titel-Ausschluss; in die Liste aufnehmen. Achtung: Kurze Wörter wie „intern“ treffen auch „Internal Tools“ – Leerzeichen am Rand werden beim Speichern entfernt.
- **Städte statt landesweit** brachte viele Doppelungen: 28.213 eindeutige Anzeigen aus 5.304 Seiten à bis zu 100. Für seltene Rollen reicht vermutlich eine landesweite Suche mit mehreren Seiten (nicht gemessen).

## Grenzen

- **Indeed sucht unscharf:** Zu „KI Manager“ liefert es auch „Sales Manager“ und „Office Managerin“. Deshalb bei Rollen mit Allerweltswort immer eine Titel-Pflicht setzen (`--titel-pflicht`). Ältere Anzeigen (bis 2018) kommen ebenfalls mit; im ersten Lauf waren 544 von 794 Indeed-Treffern älter als 30 Tage.
- **Personaldienstleister-Filter** arbeitet mit einer Namensliste (`PERSONALDIENSTLEISTER` in `pfade/google-maps/scraper/config.py`, ergänzbar über `PERSONALDIENSTLEISTER_EXTRA` in `kampagne.env`). Vermittler mit neutralem Namen rutschen durch – Stichprobe!
- **Zusammenführen über den Namen** ist unscharf: „Deutsche Bahn AG“ und „Deutsche Bahn AG Region Südwest“ bleiben zwei Firmen, bis die Website-Suche dieselbe Domain findet.
- **Konzerne** schreiben viel über Portale aus. Der Größen-Check (3g) erkennt sie aus dem Modellwissen; kennt das Modell eine Firma nicht („unbekannt“), läuft sie weiter. Ist der Check abgeschaltet, landen Konzerne in der Liste, sofern sie nicht in `KETTEN_AUSSCHLUSS` stehen.
- **Größen-Check und IT-Firmen:** Die Kategorie „IT-Wettbewerber“ ist für Angebote rund um IT/KI/Automatisierung gedacht. Bei anderen Angeboten fallen IT-Firmen damit ebenfalls heraus – dann den Check abschalten oder Liste 4 sichten.
- **Ohne belegte Website** keine Anreicherung: Die Firma steht in Liste 4 mit „keine eigene Website gefunden“.
- **Ort:** Die Suche im Umkreis überschneidet sich zwischen Nachbarorten. Doppelte Anzeigen werden über Portal und Anzeigen-ID erkannt, doppelte Firmen über Website oder Namen.

## Rechtliches in Kürze

- **Datenquelle:** Die Anzeigen kommen über die Skael-Schnittstelle, die die Portale abfragt. Wir lesen die Portale nicht selbst aus. Ob Nutzungsbedingungen der Portale berührt sind, ist eine Frage zwischen Skael und den Portalen; die Arbeitsagentur ist eine öffentliche Stelle. Genutzt werden nur Firmenangaben (wer stellt wen ein), keine Daten von Bewerbern.
- **Kontaktpersonen aus Anzeigen werden nicht übernommen.** Der Stellentext wird vor dem Speichern gekürzt: Kontaktblock, E-Mail-Adressen und Telefonnummern fallen weg. Ansprechpartner kommen nur aus dem Impressum (Geschäftsführung).
- **Ansprache:** E-Mail-Werbung ohne Einwilligung bleibt unzulässig (§ 7 Abs. 2 Nr. 2 UWG), auch mit Bezug auf eine öffentliche Anzeige. Den Aufhänger nicht fingieren: Liste zeitnah nutzen; das Datum der Anzeige steht in jeder Zeile.

Mehr in `08_versand-und-recht.md`.
