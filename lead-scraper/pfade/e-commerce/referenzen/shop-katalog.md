# Shop-Katalog DACH – Onlineshops ohne Liste finden und nach Shopsystem filtern

**Zweck:** die ausgewählte Methode, wie der E-Commerce-Pfad Shops selbst findet (z. B. „nur Shopware 5 in DACH“), statt eine Liste vorauszusetzen. Mit Architektur, ehrlichen Zahlen, Rechts- und Betriebspflichten, Phasen und offenen Entscheidungen.
**Für wen:** Betreiber (Entscheidung, Freigaben), Entwickler und KI-Modelle, die den Katalog bauen oder Nutzerfragen dazu beantworten.
**Verwandt:** `../../../wissen/06_pfad-e-commerce.md` · `fingerprints.md` (Erkennungsregeln) · `discovery-quellen.md` · `architektur.md` · `../prototypen/README.md` · `../../../wissen/08_versand-und-recht.md`
**Stand:** 2026-10-08 · **Prüfen bis:** 2027-01-08 (Zahlen sind Messungen vom 08.10.2026 bzw. Schätzungen; nach dem Echttest ersetzen)

<!-- geplante-dateien: universum.py, dns.py, abruf.py, fingerprint.py, plan.py, ereignisse.py, veroeffentlichen.py, waechter.py, ct.py, ecom/katalog.py -->
**Status: zurückgestellt, nicht gebaut.** Der Betreiber hat am 2026-10-09 entschieden: kein eigenes Crawlen von Hunderttausenden Websites. Gesucht wird eine Lösung, die Nutzer ohne Technikkenntnisse über Claude bedienen können (z. B. Datenanbieter mit Claude-Anbindung). Bis dahin startet der Pfad mit einer vorhandenen Shop-Liste. Diese Datei bleibt als Recherche-Grundlage. Entstanden aus 6 Recherchen mit eigenen Messungen, 3 konkurrierenden Architektur-Entwürfen, 2 Gutachten und 3 Gegenprüfungen am 08.10.2026.

Kennzeichnung der Zahlen:

- **[M]:** gemessen
- **[H]:** Hochrechnung aus Messwerten
- **[S]:** Schätzung

---

## 1. Die Antwort in Kürze

Ein zentraler, laufend gepflegter **Shop-Katalog** beim Betreiber. Er wird in vier Schritten aufgebaut:

1. **Universum:** Google veröffentlicht monatlich, welche Websites Chrome-Nutzer in einem Land besuchen (Chrome UX Report, kurz CrUX). Für DE, AT und CH sind das **1.156.093 Hosts** (980.354 registrierbare Domains) [M]. Die Daten sind frei, Lizenz CC BY 4.0, und es braucht kein Konto.
2. **Vorstufe DNS:** Tote und geparkte Domains fallen raus. Gehostete Systeme wie Shopify, Wix, Jimdo, Squarespace, Webflow und Shopware SaaS werden schon an DNS-Einträgen erkannt, ganz ohne Webseitenabruf.
3. **Höfliche Erkennung:** Für den Rest werden `robots.txt` und die ersten 64 KB der Startseite abgerufen. Daraus ergeben sich Shopsystem, Version (z. B. Shopware 5, 6.5, 6.6, 6.7), Plugins und Signale.
4. **Nachprüfung:** Shopware-Shops werden wöchentlich neu geprüft, andere Shops monatlich. Daraus entstehen Ereignisse wie „Shopware 5 → 6“ oder „zu Shopify gewechselt“.

Die Nutzer des Pakets holen sich mit `python3 -m ecom finden --system shopware5 --laender de,at,ch` genau ihr Segment. Danach läuft unverändert die Clay-Pipeline: aktiver Shop?, Traffic (SEND), Impressum, E-Mail, Anrede, Personalisierung.

**Warum CrUX als Basis:** Der Pfad lässt ohnehin nur Shops mit messbarem Traffic durch (SEND, vom Betreiber bestätigt). CrUX enthält genau die Websites mit nennenswertem Chrome-Traffic. Die Verzerrung der Quelle passt also zum Ziel. Ob CrUX und SimilarWeb dieselben Shops abdecken, ist **noch nicht gemessen**; das klärt der Echttest (Phase A).

## 2. Was es leistet – ehrlich

| Frage | Antwort |
|---|---|
| Wie viele Shopware-Shops in DACH? | Voraussichtlich **6.000–11.000** [S], davon **~2.000–3.000 Shopware 5** [S]. Das ist **etwa jeder dritte** der 22.549 Shopware-Shops, die StoreLeads für DACH zählt, nämlich die mit nennenswerten Besuchern. Die endgültige Zahl liefert der Erstlauf. |
| Welche fehlen? | **Sehr kleine Shops ohne Chrome-Traffic.** Nutzer, die beide Traffic-Schwellen auf 0 setzen, bedient der Katalog nicht; das im Interview sagen. **Shops, die Bots sperren:** 10–20 % der lebenden Hosts [M: 9,8 % schon an der robots.txt bei 300 Zufallshosts, vor allem im Long Tail]. **Headless-Shops ohne Merkmal.** |
| Wie sicher ist die Erkennung? | Die Regeln (fp v2) erkannten 20/20 Testdomains, darunter 7/7 Shopware [M]. Das gilt aber **auf der Entwicklungsstichprobe**; unabhängig geprüft ist erst 1 Fall, Shopware 5 nur mit n = 1. Belastbar wird es erst mit der Handprüfung von 50 zufällig gezogenen Shops (Abnahme ≥ 48/50). |
| SW5 vs. SW6? | Strukturell klar trennbar: SW5 `/web/cache/<10 Ziffern>_`, `themes/Frontend/`; SW6 `/theme/<32hex>/`, `sw-*`-Header. Bisher an 1 SW5-Shop belegt. |
| SW6-Unterversion? | Nur bei Standard-Storefronts ablesbar (4/4) [M]. Bei eigenem Build oder headless nicht (0/3). Diese Shops kommen in einen eigenen Topf „Version unbekannt“, es wird nicht geraten. Wie viele Shops auf ≤ 6.5 laufen, ist ungemessen. |
| Wie „live“? | Je nach Ereignis: Wechsel zu Shopify/SaaS **≤ 1 Tag** (DNS täglich) · Abgang bzw. Versionswechsel eines Shopware-Shops **≤ 7 Tage** · Zugang zu Shopware von anderen Systemen **≤ 30 Tage** (alle 14 Tage empfohlen) · aus „unklar/blockiert“ **≤ 90 Tage** · **neue Domains 2–3 Monate** (erst wenn CrUX sie führt). Neue Domains in Minuten gehen nur über den Zertifikats-Strom (Phase D, optional). |
| Was kostet es? | Server 5–15 €/Monat (EU-VPS, 4 vCPU empfohlen) [S]; keine Datenlizenzen. Bauaufwand realistisch **15–20 Entwicklertage** für den Kern [S]. Je Nutzer: Finden 0 €, danach wie bisher ~1 ct je Shop (Stufe 1) und ~2–4 ct je übergebenem Shop (Stufe 2). |

**Beispiel „nur Shopware 5, DACH“** [S]:

1. `finden --nur-zaehlen` zeigt ~2.000–3.000 Kandidaten.
2. Sperrliste, Ausschlussliste und schon bearbeitete Shops gehen ab: −5–15 %.
3. Stufe 1 lässt 60–90 % durch.
4. Variable Kosten ~25–115 €.

## 3. Architektur

### Rollen

- **Betreiber-Server („Shop-Katalog“):**
  - eigenes Repository, **nicht** im Skill-ZIP
  - EU-VPS mit fester IP, PTR-Eintrag `crawler.<domain>` und Bot-Infoseite
  - findet, erkennt, prüft nach, veröffentlicht
  - speichert **keine** Namen, E-Mails oder Telefonnummern
  - Die Erkennungsregeln liegen nur hier. Ändern sie sich, braucht kein Nutzer ein Update.
- **Nutzer-Rechner (`pfade/e-commerce`):**
  - lädt gefilterte Ausschnitte (neue Stufe 0), danach die unveränderten Stufen 1a–2g
  - kein Massenabruf beim Nutzer

### Datenfluss

```
[Betreiber-Server]
CrUX DE/AT/CH (monatlich, Host-Ebene) ─┐
Nachprüf-Planer (stündlich) ───────────┼─► Warteschlange ─► DNS ─┬─ tot / geparkt / Shopify / SaaS ──────────────────┐
optional später: CT-Strom ─────────────┘                         └─ selbst gehostet ─► robots.txt + GET / (≤ 64 KB) ─► fp v2 ─┤
                                 nur bei /_nuxt/ oder /_next/: Vollabruf ≤ 3 MB, GET /store-api/context (401?) ─────────────────┤
                        shops · seen · raw (90 T.) · checks · events · ausschluss · ausgaben ◄──────────────────────────────────┘
                                      │ täglich
         statische Dateien mit Token je Nutzer: stand.json · <system>.csv.gz · events · ausschluss.txt
[Nutzer]
python3 -m ecom finden --system shopware5 --laender de,at,ch   (Stufe 0)
  ─► shops (quelle = katalog:<Stand>) ─► 1b–1e (Clay Import) ─► 2a–2g (Clay ANREICHERUNG) ─► Export (+ Sperrliste + ausschluss.txt)
```

### Server-Bausteine (Python-Standardbibliothek, SQLite im WAL-Modus, ein Schreib-Thread)

| Baustein | Aufgabe |
|---|---|
| `universum.py` | CrUX-Listen laden (Spiegel github.com/zakird/crux-top-lists), `www.` entfernen, auf Host-Ebene zusammenführen. Daraus entsteht der Abrufplan: Apex-Hosts, Subdomains ohne Apex in CrUX und shopartige Subdomains (Label enthält shop, store, b2b, bestell, order, kauf; dazu de./at./ch./eu./online.). Plan 202608: ~1,04 Mio. Hosts [M], nach Vorfilter ~0,92 Mio. [M]. „Neu“ zählt erst nach 3 Monaten Abwesenheit, weil CrUX-DE sich um ~15 % pro Monat ändert [M]. |
| `dns.py` | `socket.gethostbyname_ex` für Host und `www.`. Regeln nach Alias-Kette **und** IP, siehe `fingerprints.md` Abschnitt 4a. Shopify-IPs nie per HTTP in Masse abrufen (Shopify sperrt mit 430). |
| `abruf.py` | Ablauf je Host: `robots.txt` (≤ 500 KB) → `GET /` mit gzip, Abbruch nach 64 KB auf der Leitung → Stufe 2 nur bei Framework-Signal. Härtung siehe Abschnitt 4. |
| `fingerprint.py` | Regeln fp v2 aus `../prototypen/classify.py`. Ausgabe: System, Hauptversion, Unterversion mit `version_quelle` (features/geschaetzt/unbekannt), Plugins, Status (live, passwort, platzhalter, blocked), DACH-Signal, Titel und Beschreibung (für den Stichwortfilter), hreflang-Gruppe. |
| `plan.py` | Rhythmus der Nachprüfung: Shopware wöchentlich (DNS täglich); Systeme, aus denen Shopware-Zugänge kommen (Magento, xt:Commerce, Gambio, JTL, OXID), alle 14 Tage; andere Shops monatlich; Nicht-Shops rollierend alle 90 Tage. Ein Systemwechsel wird erst nach einer Bestätigungsprüfung 24 h später veröffentlicht. |
| `ereignisse.py` | neu_im_katalog, system_wechsel, version_wechsel, saas_wechsel, weg, wieder_da. Als Wechsel zählt nur, wenn ein **anderes System positiv erkannt** wird. „Unbekannt“, 5xx oder Challenge bedeuten „unklar“. |
| `veroeffentlichen.py` | täglich: statische Dateien je System hinter Caddy mit Token je Nutzer. Nur Status „live“. Blockierte Shops und Shops mit TDM-Vorbehalt erscheinen nur als Zahl. |
| `waechter.py` | wöchentlich: Regressionsset offline, feste Stichprobe handgeprüfter Shops je System, Drift-Alarm, wenn > 2 % der Shopware-Labels ohne positives Gegenlabel verschwinden. Monatlich ein Abgleich mit der HTTP-Archive-Tech-Report-API (kostenlos, nur als Warnsignal). |
| `ct.py` | erst Phase C/D: Zertifikats-Strom, Parser aus `../prototypen/ctparse.py` |

### Tabellen (katalog.db beim Betreiber)

| Tabelle | Inhalt |
|---|---|
| `shops` | host PK, reg_domain, system, major, minor, version_quelle, plugins, status, dach_signal, land_vermutet (ccTLD, hreflang, Währung, PLZ-Muster; ohne Adresse), titel, beschreibung, gruppe_id, laender_crux, crux_stufe_je_land, first_seen, geprueft_am, letzter_erfolg, fp_version |
| `seen` | eingeordnete Nicht-Shops: Schlüssel zur Deduplizierung, klasse, Prüfmonat; Löschfrist 13 Monate |
| `queue` | host, grund, prio, ziel_ip, ziel_netz (/24), due_at, attempts |
| `raw` | Roh-HTML nur von Shops, höchstens 90 Tage, als TDM-Kopie nach § 44b UrhG |
| `checks` · `events` | Prüfverlauf 12 Monate · Ereignisse 24 Monate |
| `ausschluss` | Opt-outs und Widersprüche, dauerhaft |
| `ausgaben` | **Pflicht:** welcher Token wann welche Dateiversion geladen hat, 24 Monate (Auskunft über Empfänger, Art. 15/19 DSGVO) |

### Einbau in `pfade/e-commerce`

- **Neue Datei `ecom/katalog.py`:**
  - Download mit Token, lokale Kopie unter `data/katalog/` mit Löschfrist
  - Altersprüfung: Shopware ≤ 14 Tage, Rest ≤ 37 Tage
  - Rückfall auf die letzte Kopie mit Hinweis
- **Neuer Befehl `finden`** (Stufe 0):
  - Filter: `--system`, `--version`, `--laender`, `--stichwort`, `--rang-bis`, `--max`, `--nur-zaehlen`, `--neu`
  - Vorab fallen heraus: Sperrliste, `ausschluss.txt`, schon importierte Shops, Dubletten derselben Gruppe
- **`shops` bekommt neue Spalten:** shop_system, shop_version, version_quelle, crux_stufe, katalog_stand, anlass, ziel_entfallen.
  - Stufe 1 überspringt Zeilen mit `ziel_entfallen = 1`; das kostet keine Credits.
- **Export:** zusätzliche Spalten Shopsystem, Version, Anlass, Datenquelle. Datenquelle = vollständiger CC-BY-Hinweis (Abschnitt 5).
- **Neu für alle Läufe (fehlt heute schon): Sitzland-Filter nach Stufe 2b.**
  - Land aus dem Impressum ableiten: PLZ-Länge, Ländername, USt-Präfix DE/ATU/CHE.
  - Stufe 2c (E-Mail-Suche) läuft nur, wenn das Land zur Auftragsfrage D1 passt.
  - Heute verbrauchen ausländische Shops Credits und landen im Export.
- **Anlass-Texte nur aus harten Signalen:** SW5 per HTML-Merkmal, SW6-Version mit `version_quelle = features`. Geschätzte Versionen nie in Filter oder Anlass.
- **Phase-B-Abkürzung:** Eine Katalog-CSV mit Spalte „Website“ liest der bestehende Befehl `ecom import` schon heute. Shopsystem und Version gehen dabei aber verloren, deshalb nur für den internen Pilot nutzen.

## 4. Härtung (Pflicht, aus der Gegenprüfung)

| Thema | Regel |
|---|---|
| Last je Provider | Zusätzlich zu ≤ 2 Abrufen je Ziel-IP ein Budget je /24 und je Netzbetreiber, z. B. ≤ 4 parallel und ≤ 3 Abrufe/s je /24. Grund: IONOS trägt in der Stichprobe 11,2 % der Domains in **einem** /24-Netz, Strato 7,0 % [M]. |
| Scan-Muster | Im Erstlauf höchstens ~10 neue Ziel-IPs/s. Der Lauf dauert dann ~1–1,5 Tage statt 6–14 h; für eine Monatsliste ist das egal. Gemessen werden neue Ziel-IPs/s und fehlgeschlagene Verbindungen/s. |
| SaaS ohne CNAME | IP-Regeln für Jimdo 162.159.128.70/129.70, Webflow 198.202.211.1, Wix 185.230.63.0/24, Squarespace 198.185.159.144/145 und 198.49.23.144/145 (gemessen bzw. aus Anleitungen). Vorher an 20 Hosts per Header bestätigen. |
| Einstiegs-URL | Zuerst exakt den CrUX-Origin abrufen (Schema und www wie gelistet), erst danach die andere Variante. |
| Wiederholung | Bei Zeitüberschreitung, 5xx-, TLS- oder Verbindungsfehler ein zweiter Versuch nach 24–72 h. Bei 403/429/430 und robots-Verbot nicht; dort nach 90 Tagen nur die robots.txt erneut prüfen. |
| robots.txt | Eigener Prüfer nach RFC 9309 (`urllib.robotparser` liest Platzhalter vor Python 3.13 falsch). Ist die robots.txt nicht erreichbar (5xx oder Zeitüberschreitung), gilt alles als verboten (RFC 9309, 2.3.1.4). Auch Pfade der Stufe 2 (`/store-api/`, `/wp-json/`) prüfen. |
| TDM | Header `tdm-reservation` und `/.well-known/tdmrep.json` (je Host gecacht) **vor** dem Speichern prüfen. Bei Vorbehalt sofort löschen. |
| Stufe 2 sparsam | Stufe 2 nur bei eindeutigem Framework-Signal (`/_nuxt/`, `/_next/`), höchstens 1× je Host und Quartal. Grund: WAFs werten solche API-Abrufe als Schwachstellen-Scan, das führt zu Blocklisten-Einträgen. Die eigene IP wöchentlich gegen Blocklisten prüfen. |
| Zeitlimits | Verbindungsaufbau 5 s, Lesen 10 s **und** eine Gesamtfrist je Anfrage (z. B. 20 s), gegen Tarpits. |
| Vorfilter | Vor dem Abruf entfernen: fremde Länderendungen (.ru, .pl, .it …), Behörden, Hochschulen, Login- und Intranetportale, private Plattform-Subdomains (echte Public Suffix List). Das spart ~11 % der Abrufe und ist Datenminimierung [M]. |
| Rechenlast | Klassifizieren kostet ~33 ms je Host [M]. Für 20–50 Hosts/s braucht es `multiprocessing` oder einen Bytes-Vorfilter, dazu 4 vCPU. |
| Rangstufen | Rangstufen je Land führen: Von 214.915 Hosts mit bester Stufe ≤ 100k stehen nur 99.398 im DE-Rang ≤ 100k [M]. |

## 5. Recht und Betrieb (keine Rechtsberatung)

**Vor dem Vollauf zu erledigen** (der Probelauf mit ≤ 186k Hosts ist nur als Messung erlaubt):

1. **Anwaltliche Kurzprüfung**, ausdrücklich zu folgenden Punkten:
   - **Teilnehmerhaftung des Betreibers:** Er liefert künftig zentral Ziele samt „Anlass“ in eine E-Mail-Pipeline. Daher den Zweck des Katalogs in Interessenabwägung und Nutzungsbedingungen auf zulässige Kanäle binden: Brief; Telefon nur in DE mit konkretem Bezug; E-Mail nur mit Einwilligung.
   - **Länderrecht:**
     - AT: § 174 TKG 2021, Werbeanrufe auch B2B nur mit Einwilligung
     - CH: Art. 3 Abs. 1 lit. o und u UWG-CH, Art. 19 revDSG
     - `wissen/08` braucht eine Kanalregel je Land.
   - **Rollen:** getrennte oder gemeinsame Verantwortung (Art. 26) von Betreiber und Nutzern.
2. **DSFA (Art. 35)** und Eintrag im Verzeichnis der Verarbeitungstätigkeiten. Dokumentierte Interessenabwägung nach Art. 6 Abs. 1 lit. f. Information nach Art. 14 auf der Bot-Seite. Art. 14 Abs. 5 lit. b trägt für kommerzielle Zwecke nur schwach (EDSA-Leitlinien 03/2026 Rn. 27, gelten für KI-Scraping und hier nur analog, Entwurf).
3. **Hoster schriftlich:** Er bestätigt, dass HTTP-Crawling mit X Verbindungen/s erlaubt ist.
   - **Hetzner Cloud verbietet „Scanning foreign networks or foreign IP addresses“**, kennt keine Vorabfreigabe und sperrt automatisch. Deshalb nicht die erste Wahl.
   - Reserve-Hoster mit fertigem Image vorhalten.
   - Probelauf 7 Tage ohne Netscan-Ticket und ohne Abuse-Meldung.
4. **Bot-Seite:**
   - Inhalt: Zweck, Bot-Name für robots.txt, IP, Abuse-Kontakt (Antwort binnen 24 h), Opt-out vor der Erhebung, Impressum, Datenschutzerklärung
   - Im From-Header eine Rollenadresse angeben.

**Laufend:**

- **Nur eigene Erhebung und freie Quellen ohne Weitergabeverbot:** CrUX (CC BY 4.0), CT-Logs, Public Suffix List. Kein Common Crawl (Nutzungsbedingungen 2(g)/(l)), keine Kaufquellen als Katalogquelle.
- **Quellenangabe vollständig**, so wie CC BY 4.0 Ziff. 3(a) es verlangt: „Enthält Daten aus dem Chrome UX Report (Google), CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ – gefiltert, auf Hosts zusammengeführt und um eigene Klassifikation ergänzt.“ Nutzungsbedingungen („kein Weiterverkauf“) dürfen nur die eigenen Beiträge erfassen (System, Version, Prüfdatum), nicht Host und Rang (Ziff. 2(a)(5)(B)).
- **Personenbezug:** Bei Einzelunternehmern ist die Domain ein personenbezogenes Datum. Ehrlich formulieren: „Der Katalog enthält Webadressen und Technikdaten. Bei Einzelunternehmern sind das personenbezogene Daten. Namen, E-Mails und Telefonnummern speichert er nicht.“
- **Katalog = Liste verwundbarer Shops** (SW5 ohne Updates):
  - Zugang nur per Token
  - an Nutzer nur Hauptversion und EOL-Status, keine Unterversionen mit CVE-Bezug
  - Löschfristen auch für lokale Kopien
  - Meldeweg für Lecks
- **Fristen:** Nicht-Shops mit Löschfrist, die archivierten CrUX-Dateien eingeschlossen. Ein HMAC-Schlüssel dient nur der Deduplizierung und ist kein Schutz, solange Klartextlisten auf demselben Server liegen.
- **Kein automatisierter Abruf von StoreLeads-Seiten** (AGB Ziff. 2(1), 2(5), 2(9)). Öffentliche Gesamtzahlen nur von Hand als Vergleich übernehmen.
- **Überfischung:**
  - Problem: Kleine Segmente (SW5: am Ende vielleicht 500–1.500 versandfähige Leads [S]) würden von jedem Nutzer erneut angeschrieben. Das treibt Beschwerden und Abmahnungen und belastet die Sperrlisten-Gemeinschaft.
  - Für Segmente unter ~5.000 Hosts: Zuteilung mit Sperrfrist je Host und Token (z. B. 90 Tage) über einen kleinen Endpunkt (+1–2 Tage Bau).
  - Mindestens Segmentgröße und Zahl der Bearbeiter anzeigen.
- **§ 7 UWG:** Die Rechtsregel bleibt, die Rolle des Betreibers ändert sich (siehe Punkt 1). Kanal im Interview **vor** `finden` abfragen.

## 6. Phasen (jede mit Messung und Abbruchkriterium)

| Phase | Inhalt | Aufwand [S] | Messung / Abbruch |
|---|---|---|---|
| **A – Echttest vor dem Bau** | Prototyp über 5.000–10.000 CrUX-Hosts (DE-Rang ≤ 100k) gedrosselt laufen lassen. Die ~50–100 gefundenen Shopware-Shops durch den **noch nie echt gelaufenen** Pfad schicken (Stufe 1+2, wenige Euro). Den Pilot nach Rangstufe schichten (≥ 30 Shops je Stufe). | 2–3 Tage | Gemessen werden: SEND-Quote je Rangstufe, Ready-to-Send-Quote, Erkennungsquote (Handprüfung), eigene Shopware-Zahl im DE-Rang ≤ 100k gegen HTTP Archive Top 100k (2.054) [M]. **Abbruch**, wenn die SEND-Quote der Katalog-Shops unter ~30 % liegt oder die Leads nicht verwertbar sind. |
| **0 – Freigaben** | VPS bestellen, Hoster-Bestätigung, Bot-Seite, DSFA, Anwalt beauftragen, Regressionsset aus 21 Fällen | 1–2 Tage + 1–2 Wochen Kalender | schriftliche Hoster-Bestätigung liegt vor |
| **B – Erkennungskern und Erstkatalog** | fp v2 einfrieren, Abruf härten (Abschnitt 4), Tabellen, Worker. Zuerst Probelauf ≤ 186k Hosts, nach der Rechtsprüfung Vollauf. Ausgabe nur intern bzw. an 1–3 Pilotnutzer. | 9–12 Tage | **Abnahme:** unabhängige Handprüfung von 50 Shopware-Treffern (≥ 48 richtig, geschichtet: ≥ 15 SW5, ≥ 10 eigener Build bzw. headless) und von 200 Hosts mit Shop-Signal ohne Shopware-Label (Recall). Unlesbarkeit nach Ursache. **Abbruch** bei Blockquote > 25 % oder Hoster-Sperre. |
| **C – Auslieferung** | Planer, Ereignisse, Auslieferung mit Token, `ecom finden`, Sitzland-Filter, Stichwortfilter, Gruppen gegen Dubletten, Zuteilung für kleine Segmente, Hinweis „seit deinem letzten Abruf n Wechsel“ beim Sitzungsstart, Wissensdatenbank | 5–6 Tage | ≥ 95 % der Shopware-Hosts höchstens 7 Tage alt erfolgreich geprüft (getrennt nach „versucht“ und „erfolgreich“) |
| **D – Zertifikats-Strom, nur nach Messtor** | CT-Tailer im Stichprobenmodus; Long-Tail-Probe mit ≥ 70.000 Nicht-CrUX-Domains aus dem CT-Strom (≥ 100 Shopware) durch Stufe 1. Kacheln mit gzip anfordern. | 2–3 Tage + 2–4 Wochen Laufzeit | Zensus nur bei SEND-Quote im Long Tail ≥ 20 % (Grauzone 15–25 % → Probe verlängern) **und** nach einem eigenen Rechts- und Hoster-Tor. Datenvolumen der Let's-Encrypt-Logs: 0,45–0,55 TB/Monat [H]. |
| **E – Kalibrierung** | nach ~90 Tagen Betrieb | 1–2 Tage | Quoten in `wissen/06` eintragen; dann entscheiden, ob CrUX-Präsenz SimilarWeb ersetzen darf (wäre eine Clay-Abweichung). |

**Kern (0, B, C): realistisch 15–20 Entwicklertage, im Kalender 4–6 Wochen** [S]. Phase A vorab: 2–3 Tage und wenige Euro Credits.

## 7. Verworfene Ansätze (mit Grund)

| Ansatz | Grund |
|---|---|
| Kauflisten (StoreLeads, BuiltWith, Wappalyzer, TechnologyChecker) als Katalogquelle | Weitergabe an Kunden nur mit schriftlicher Erlaubnis bzw. verboten. Für **interne** Kalibrierung zulässig (z. B. StoreLeads einen Monat oder DataForSEO ~1 $/1.000 Domains) |
| Netlas.io (49 $/Monat), PublicWWW | nur ~25–40 % Abdeckung [S], Weitergabe nur mit Enterprise-Zusatz |
| HTTP Archive per BigQuery | Google-Konto nötig, Kostenfalle (Forumsfall 14.000 $), SW6 nur über Header erkannt (verfehlt gecachte und headless Shops), Zählungen schwanken ×2,3. Die kostenlose **Tech-Report-API** bleibt als Warnsignal |
| Common Crawl | Nutzungsbedingungen 2(g) (keine unerwünschte Werbung) und 2(l); zstd-Parquet ohne Zusatzpaket nicht lesbar |
| Shodan, Censys, FOFA, urlscan | IP-zentriert, teuer oder nicht kommerziell nutzbar |
| Zonendateien | .de und .at gibt es nicht, die .ch-Zone ist zweckgebunden (nicht für Akquise) |
| Tranco, Umbrella, Majestic, Cloudflare Radar | zu wenige DACH-Domains bzw. Lizenz nicht kommerziell |
| Crawl vom Heimanschluss bzw. durch Nutzer | Abuse-Risiko ohne feste IP, Regeln bei jedem Nutzer |
| Ersatzlabels für Shops, die unseren Bot sperren | unterläuft deren Opt-out |

## 8. Offene Entscheidungen des Betreibers

1. **Echttest (Phase A) zuerst?** Empfehlung: ja, bevor 15–20 Tage gebaut werden. Er braucht:
   - Skael- und OpenAI-Schlüssel und wenige Euro Credits
   - einen kleinen, gedrosselten Abruf von 5.000–10.000 Startseiten
2. **Wer betreibt den Katalog?** Empfehlung:
   - Wer den Katalog anbietet, ist Verantwortlicher (Bot-Seite, Opt-out, Interessenabwägung).
   - Ein technischer Dienstleister kann ihn als Auftragsverarbeiter bauen und betreiben.
   - Bot-Name und Domain der Infoseite gleich festlegen.
3. **Hoster:** einer, der Crawling schriftlich bestätigt (nicht Hetzner Cloud).
4. **Verteilung an Nutzer:**
   - Token je Nutzer
   - Zuteilung mit Sperrfrist für kleine Segmente (SW5)
   - Nutzer melden Widersprüche an den Betreiber zurück
5. **Zertifikats-Strom (Phase D):** nur wenn Kunden ausdrücklich neue Shops binnen Tagen wollen. Das betrifft vor allem Shopify, weil neue Shopware-Shops selten mit neuer Domain entstehen.
