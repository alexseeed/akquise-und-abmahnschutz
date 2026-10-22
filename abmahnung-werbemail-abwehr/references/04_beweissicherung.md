# Beweissicherung (Modul W)

Ziel ist ein Paket, das ein Gericht nachvollziehen kann: was, wann, wie, womit, unverändert. Die Sicherung ist **vor** Versand des Antwortschreibens abzuschließen – danach korrigiert die Gegenseite erfahrungsgemäß schnell.

## Voraussetzungen

- Python 3 mit Playwright und Chromium (`python3 -c "import playwright"`; Browser per `playwright install chromium`, falls die Umgebung das erlaubt)
- curl, openssl, sha256sum, zip
- Netzwerkzugriff auf die Website des Abmahners und auf die Zeitstempeldienste

Fehlt etwas davon: Abschnitt „Ohne Shell oder Browser“ unten.

## Schritt 1 – Netzwerkverhalten mitschneiden

```bash
python3 scripts/sicherung_netzwerk.py https://www.abmahner.de "Ablehnen" paket/01_netzwerk /kontakt /datenschutz
```

Jedes Szenario läuft in einem frischen, leeren Browserprofil:

| Szenario | Ablauf | Belegt |
|---|---|---|
| A | Startseite, 8 s warten, keine Interaktion | Drittserver ohne Einwilligung |
| B | Startseite, Klick auf „Ablehnen“, danach Startseite und Folgeseiten | Ablehnung wird gespeichert und trotzdem geladen |
| C | erste angegebene Unterseite direkt, keine Interaktion | Einbindungen, die nur auf Unterseiten sitzen |

Ergebnis je Szenario: HAR-Datei (vollständiger Mitschnitt), CSV aller Anfragen mit Zeit und Phase, Screenshots, `_zustand.json` (Cookies, localStorage, dataLayer).

Hinweise:
- Den Text der Ablehnen-Schaltfläche vorher per Screenshot prüfen („Ablehnen“, „Nur notwendige“, „Alle ablehnen“, „Nur essenzielle Cookies akzeptieren“).
- Läuft die Umgebung hinter einem TLS-terminierenden Proxy, `--ignore-https-errors` setzen und das im Protokoll vermerken.

## Schritt 2 – Auswerten

```bash
python3 scripts/auswertung.py paket/01_netzwerk --eigene-domain abmahner.de > paket/01_netzwerk/auswertung.md
```

Das Skript ordnet jeden Drittserver über `listen/drittanbieter.csv` einem Anbieter zu, listet die Drittserver je Phase und Seite mit erster Anfrage und CSV-Zeilennummer und liest den Consent-Status über `listen/consent-tools.csv` aus. Unbekannte Hosts werden markiert: per Websuche zuordnen und – falls dauerhaft relevant – dem Skill-Betreiber zur Aufnahme in die Liste melden.

## Schritt 3 – Seiteninhalte sichern

```bash
python3 scripts/sicherung_seiten.py https://www.abmahner.de "Ablehnen" paket/02_seiteninhalte \
  /datenschutz /impressum /agb /widerrufsbelehrung /kontakt
```

Je Seite: Roh-HTML wie vom Server ausgeliefert plus Antwort-Header (curl), Ganzseiten-Screenshot, PDF mit URL und Sicherungszeit in der Kopfzeile, MHTML-Webarchiv (alle Ressourcen eingebettet). Downloads (PDF-Formulare usw.) mit `--download URL` zusätzlich direkt sichern. Das Cookie-Banner wird vor den Aufnahmen einmal mit „Ablehnen“ geschlossen; das steht im Protokoll.

## Schritt 4 – Integrität

```bash
bash scripts/integritaet.sh paket
```

Erzeugt `03_integritaet/SHA256SUMS.txt` über alle Dateien, holt zwei unabhängige RFC-3161-Zeitstempel (DFN-Verein, Sectigo; bei Ausfall weitere Dienste), extrahiert die Zertifikatsketten, prüft die Stempel und schreibt `PRUEFANLEITUNG.txt`. Erwartetes Ergebnis: zweimal „Verification: OK“.

Die DFN-Wurzel ist nicht in jedem Zertifikatsspeicher enthalten. Ihren Fingerabdruck in der Prüfanleitung nennen, damit Dritte ihn auf pki.dfn.de abgleichen können.

## Schritt 5 – Protokoll und Paket

- Protokoll als PDF nach `beispiele/04_beweisprotokoll-gliederung.md`. Das Protokoll muss **vor** Schritt 4 fertig sein, damit es von Hashes und Zeitstempel erfasst wird.
- Ordner: `00_Beweisprotokoll.pdf`, `01_netzwerk`, `02_seiteninhalte`, `03_integritaet`, `04_methodik` (verwendete Skripte kopieren).
- Upload-Grenzen der Umgebung beachten: das Paket in mehrere ZIPs unterhalb der Grenze aufteilen, Einzeldateien nicht zerlegen. Nach dem Entpacken aller Teile muss `sha256sum -c 03_integritaet/SHA256SUMS.txt` für jede Datei „OK“ melden. Zu große Einzeldateien weglassen, wenn dieselbe Seite in anderem Format gesichert ist, und das im Protokoll vermerken.

## Grenzen (immer im Protokoll nennen)

- Eigendokumentation einer Partei; das Gericht würdigt frei (§ 286 ZPO).
- Durchführung automatisiert durch einen KI-Assistenten im Auftrag des Nutzers – offen benennen.
- Ausgangs-IP aus einem Rechenzentrum, ggf. im Ausland, und ggf. TLS-terminierender Proxy: länder- oder bot-abhängige Auslieferung kann abweichen. Ausgangs-IP und Land per `curl https://ipinfo.io/json` erfassen.
- Headless-Browser statt manueller Nutzung.
- Unklare Werte nicht überinterpretieren. Beispiel: Ein URL-Parameter wie `ip=172.17.0.1` ist eine interne Serveradresse, nicht die Besucher-IP.

## Ohne Shell oder Browser

Der Nutzer sichert selbst nach der Zeugenanleitung unten. Die gelieferten Dateien (HAR, Screenshots) werden gehasht und, wenn möglich, mit Zeitstempel versehen. Aussagen über Ladeverhalten nie aus bloßem Textabruf per Websuche ableiten – solche Werkzeuge führen kein JavaScript aus und respektieren oft robots.txt.

## Empfehlungen an den Nutzer (immer mitgeben)

1. **Zeugenwiederholung** durch eine Person, die später aussagen kann, am eigenen Rechner mit deutschem Anschluss:
   1. Chrome im Inkognito-Fenster öffnen.
   2. F12 drücken, Reiter „Network“ wählen, „Preserve log“ aktivieren.
   3. Website aufrufen und „Ablehnen“ klicken.
   4. Zwei bis drei Unterseiten aufrufen.
   5. Im Filterfeld die festgestellten Drittserver eingeben und jeweils einen Screenshot mit sichtbarer Uhrzeit anfertigen.
   6. Über das Download-Symbol „Export HAR“ speichern.
   7. Ablauf kurz schriftlich festhalten und unterschreiben.
2. **Unabhängige Archivierung** der zentralen URLs über `https://web.archive.org/save` (aus Sandbox-Umgebungen oft gesperrt – dann der Nutzer).
3. **Höchste Beweiskraft** bei absehbarem Prozess: notarielle Tatsachenbescheinigung (Website-Feststellung) oder IT-Sachverständiger, bevor die Gegenseite ändert.
4. Original-ZIPs unverändert auf zwei Datenträgern aufbewahren und nur Kopien weitergeben.
