# Pfad „Amazon-Seller“ – aus einer Brand-Liste werden Kontakte

**Zweck:** was der Pfad leistet, was er voraussetzt, welche Quoten realistisch sind und welche Risiken bestehen.
**Für wen:** Nutzer mit einer Amazon-Brand-Liste und KI-Modelle, die Rückfragen beantworten.
**Verwandt:** `02_zielgruppen-interview.md` · `07_lead-ausgabe-und-spalten.md` · `08_versand-und-recht.md`
**Technik im Detail:**

- Anleitung für die KI: `pfade/amazon/ABLAUF.md`
- Spalten und Quoten: `pfade/amazon/referenzen/spalten.md`
- Browser-Technik: `pfade/amazon/referenzen/browser-technik.md`
- Agenten-Prompts: `pfade/amazon/referenzen/agent-prompt.md`

---

## Wann dieser Pfad

Für Marken und Händler, die auf **amazon.de** verkaufen. Typische Zielgruppen: Anbieter für Amazon-Agenturleistungen, Logistik, Finanzierung, Software für Händler.

Sonderfall: Auch für **jede eigene Firmenliste** mit Firmenname (ideal mit Handelsregisternummer und Ort) lassen sich ab Phase 4 Website, Geschäftsführung und Anrede recherchieren.

## Voraussetzungen

| Was | Warum |
|---|---|
| **Brand-Liste als CSV**, typisch ein SmartScout-Export mit `Brand Name`, `Dominant Seller`, `Est. Monthly Revenue` | Der Pfad findet keine Marken selbst, er reichert eine vorhandene Liste an |
| **Chrome mit eingeloggter amazon.de-Sitzung** und der Erweiterung „Claude in Chrome“ | Seller IDs und Impressen werden im Browser aus der Amazon-Seite heraus geholt |
| **Claude mit Subagenten** (Claude Code oder Cowork) | Die Recherche der Geschäftsführung läuft parallel in vielen Agenten |
| Zugriff auf den Downloads-Ordner | Ergebnisse kommen als Datei-Download aus dem Browser |

Ohne verbundenen Browser bricht der Pfad vor Phase 1 ab und sagt das.

## Ablauf in sieben Phasen

| Phase | Was passiert | Ergebnis |
|---|---|---|
| 0 Bestandsaufnahme | zählt, was fehlt, legt Arbeitspakete an | Zahlen und Laufzeit vorab |
| 1 Seller ID | Amazon-Brand-Suche im Browser; nur **exakte** Übereinstimmung mit `Dominant Seller` wird übernommen | ~90 % Trefferquote |
| 2 Storefront | Link aus der Seller ID | `https://www.amazon.de/s?me=<ID>&marketplaceID=A1PA6795UKMFR9` |
| 3 Amazon-Impressum | Geschäftsname, Geschäftsart, Handelsregister, USt-ID, Telefon, E-Mail, Adresse | **keine** Geschäftsführung |
| 4 Website + Geschäftsführung + Anrede | Recherche-Agenten, je 40 Firmen. Quelle: zuerst die Website, sonst Handelsregister. HR-Nummer zur Gegenprüfung | GF, Quelle, Sicherheit |
| 5 Ansprache | feste Regeln im Skript | „Guten Tag Herr Mustermann“ oder „Guten Tag“ |
| 6 Verifikation | 5 Stichproben echt aufrufen, programmatische Prüfung | gemessene Fehlerquote |
| 7 Sperrliste | Website-Domains gegen die Community-Sperrliste | bereinigte und gesperrte Liste |

Alle Skripte sind fortsetzbar und überschreiben keine gefüllten Felder.

## Was realistisch herauskommt

Aus einem realen Lauf mit ~3.500 Zeilen:

| Kennzahl | Wert |
|---|---|
| Seller IDs gefunden | ~92 % der gesuchten |
| Impressum mit Geschäftsname | ~98 % der Seller |
| Zeilen mit Geschäftsführung | ~33–40 % |
| Fehler bei gefundenen Namen | ~10–20 % |
| Herkunft der Seller | ~35 % DE, ~8 % HK, ~3 % CN, Rest gemischt |

Die Quote für die Geschäftsführung ist durch die Herkunft gedeckelt. Firmen aus Hongkong und China haben keine Geschäftsführung im deutschen Sinn. Bei deutschen Firmen liegt die Fundquote bei ~95 %.

## Typische Fehler und Gegenmittel

- **Länder-Töchter:** Gefunden wird die Geschäftsführung der Schweizer oder österreichischen Tochter. Gegenmittel: HR-Nummer im Agenten-Prompt.
- **Unvollständige Listen:** Hat eine Firma mehrere Geschäftsführer, fehlt manchmal einer. Für die Erstansprache reicht das.
- **Unsichere Zuordnung:** Die Spalte `GF Confidence` = `unsicher` führt automatisch zur neutralen Ansprache.

## Ansprache-Regeln

| Situation | Ansprache |
|---|---|
| Geschlecht des Vornamens sicher (> 60) und Firma sicher zugeordnet | „Guten Tag Herr/Frau Nachname“ |
| sonst | „Guten Tag“ |

Begründung: Eine falsche persönliche Anrede kostet den Kontakt sofort, ein neutrales „Guten Tag“ kostet nichts.

## Risiken

- **Amazon-Nutzungsbedingungen:** Automatisierte Abrufe aus der eigenen amazon.de-Sitzung können gegen die Bedingungen verstoßen. Es drohen Captchas oder eine Kontosperre. Ein separates Konto ohne Verkäufer- und Einkaufsbezug nutzen und nicht schneller als vorgesehen arbeiten (höchstens ~8 parallele Abrufe).
- **Datenschutz:** Namen der Geschäftsführung sind personenbezogene Daten. Bei Ansprache gilt die Informationspflicht nach Art. 14 DSGVO (`08_versand-und-recht.md`).
- **Sperrliste:** Seller ohne eigene Website lassen sich nicht abgleichen. Das wird dem Nutzer gesagt.
