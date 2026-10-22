# Gliederung Beweisprotokoll (Modul W)

Als PDF bauen (z. B. HTML → PDF mit Chromium), **vor** dem Hashen in `00_Beweisprotokoll.pdf` speichern. Ca. 6–10 Seiten.

## Deckblatt / Kopf

| Feld | Inhalt |
|---|---|
| Gegenstand | Internetauftritt https://… (Betreiber laut Impressum) |
| Schwerpunkt | z. B. datenschutzrechtliche Feststellungen |
| Auftraggeber | Name des Nutzers / Unternehmens |
| Durchführung | automatisierte Sicherung per Skript, ausgeführt durch einen KI-Assistenten im Auftrag; Skripte im Ordner 04_methodik |
| Zeitraum | Datum, Uhrzeit von–bis in UTC und Ortszeit |
| Software | Browser und Version, Playwright-Version, curl, OpenSSL |
| Browserzustand | frisches leeres Profil je Szenario, Sprache, Zeitzone, Fenstergröße |
| Netzwerk | Ausgangs-IP und Land (aus netzwerk_meta.json), Proxy ja/nein, TLS-Fehler ignoriert ja/nein |

## 1. Zusammenfassung der Feststellungen

Nummerierte Liste, je Punkt 2–4 Sätze, nur Tatsachen.

## 2. Szenario A – Erstaufruf ohne Einwilligung

Ablauf, Screenshot mit sichtbarem Banner, Tabelle aus `auswertung.py` (Drittserver | Anbieter | Funktion | erster Abruf | Beleg | in DSE genannt?). Hinweis: Antwortcodes 401/403/404 ändern nichts daran, dass die Anfrage mit IP beim Drittserver angekommen ist.

## 3. Szenario B – nach Ablehnung

- Ablauf mit Uhrzeit des Klicks
- 3.1 Nachweis der gespeicherten Ablehnung (Consent-Status aus `_zustand.json`, Tabelle Dienst → erlaubt/abgelehnt)
- 3.2 Drittserver nach der Ablehnung, je aufgerufener Seite
- Einzelbelege mit CSV-Zeilennummern
- Klarstellung, ob Messaufrufe beobachtet wurden

## 4. Datenschutzerklärung – Abgleich

Tabelle festgestellter Dienst → in DSE erwähnt ja/nein; überholte Angaben mit Seitenzahl im gesicherten PDF und wörtlichem Zitat.

## 5. Weitere Feststellungen

Tabelle Fundstelle (Datei, Seite) → Feststellung. Klarstellungen zu Werten, die missverstanden werden könnten.

## 6. Integrität, Grenzen, Empfehlungen

- Integrität: SHA-256 aller Dateien, zwei RFC-3161-Zeitstempel, Verweis auf PRUEFANLEITUNG.txt
- Grenzen (immer): Eigendokumentation (§ 286 ZPO), KI-Durchführung, Ausgangs-IP/Proxy, Headless-Browser, ggf. ausgelassene Dateien
- Empfehlungen: Zeugenwiederholung (Schrittfolge), archive.org, Notar/Sachverständiger, Aufbewahrung

## Anlagen

- Anlage 1: Verzeichnis der gesicherten Seiten (aus `seiten_index.json`)
- Anlage 2: Verzeichnis der Netzwerkmitschnitte
