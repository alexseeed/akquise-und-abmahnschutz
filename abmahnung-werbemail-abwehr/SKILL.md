---
name: abmahnung-werbemail-abwehr
description: Prüft Abmahnungen wegen Werbe-E-Mails/Cold-Mails (UWG, §§ 823/1004 BGB, Art. 82/15 DSGVO), gleicht den Abmahner mit der Community-Sperrliste ab und meldet seine Domains dorthin, recherchiert Kanzlei, Rechtsprechung und Webauftritt des Abmahners, sichert Website-Verstöße gerichtsfest, lässt Gegenanwalt-Check laufen und baut Antwortschreiben plus modifizierte Unterlassungserklärung als PDF. Nutzen bei jeder Abmahnung, Unterlassungsaufforderung oder DSGVO-Schadensersatzforderung wegen E-Mail-Werbung.
---

# Abmahnung Werbe-E-Mail – Prüfung & Abwehr

Verfahren für Unternehmen, die wegen einer unerlaubten Werbe-E-Mail (typisch: B2B-Cold-Mail) abgemahnt wurden. Ergebnis: fundierte Einschätzung, verifizierte Rechtsprechung, versandfertiges Antwortschreiben und modifizierte Unterlassungserklärung (UE) als PDF. Auf Wunsch zusätzlich: gesicherte Prüfung des Webauftritts des Abmahners. Jeder Fall wird am Ende an die **Community-Sperrliste** gemeldet: ein öffentliches GitHub-Repository mit den Domains aller gemeldeten Abmahner, das jeder Nutzer vor E-Mail-Kampagnen als Domain-Sperre lädt. Die Liste ergänzt sich ohne Moderation selbst. Keine Einrichtung, kein Konto, kein Token beim Nutzer.

**Nutzungsbedingung (einmal zu Beginn nennen, in einem Satz):** Der Skill ist kostenlos; im Gegenzug meldet er am Ende die Domains des Abmahners an die Community-Sperrliste – nur Domains und Sachangaben, keine E-Mail-Adressen, keine Namen, nicht der Name des Nutzers (Details: `NUTZUNGSBEDINGUNGEN.md`).

Der Nutzer ist in der Regel das abgemahnte Unternehmen selbst (Geschäftsführung oder Mitarbeiter). Weise einmal zu Beginn kurz darauf hin, dass der Skill Recherche und Entwürfe liefert, aber keine anwaltliche Beratung ersetzt, und dass bei Klage, einstweiliger Verfügung oder hohen Beträgen ein Anwalt hinzugezogen werden sollte. Danach keine wiederholten Disclaimer.

## Aufbau dieses Skills

Diese Datei steuert den Ablauf. Details stehen in eigenen Dateien – lies sie in der Phase, in der sie gebraucht werden, nicht alle vorab.

| Datei | Inhalt | Wann lesen |
|---|---|---|
| `references/01_rechtsprechung.md` | Entscheidungen, Normen, RVG-Werte | Phase 2 und 6 |
| `references/02_antwortbausteine.md` | Aufbau Antwortschreiben, UE-Muster, verbotene Formulierungen | Phase 4 |
| `references/03_website-pruefraster.md` | Prüfraster Website des Abmahners | Modul W |
| `references/04_beweissicherung.md` | Mitschnitt, Seitensicherung, Hashes, Zeitstempel, Protokoll | Modul W |
| `references/05_fallstricke.md` | Bekannte Eigentore und Fehlgriffe | vor Phase 4 und vor Versand |
| `references/06_community-sperrliste.md` | Repository, Datenmodell, Abgleich, Meldung, zugehörige Domains, Datenschutz | Phase 1, 1b und 9 |
| `NUTZUNGSBEDINGUNGEN.md` | Gegenseitigkeit, übermittelte Daten, Pflichten | zu Beginn (einmal nennen), Phase 9 |
| `listen/drittanbieter.csv` | Bekannte Drittserver: Anbieter, Kategorie, Sitz, typische Norm | Modul W, Auswertung |
| `listen/consent-tools.csv` | Consent-Tools und wo sie die Ablehnung speichern | Modul W, Szenario B |
| `beispiele/` | Fiktive Musterfälle: Antwortschreiben, UE, Website-Block, Protokoll-Gliederung, Meldung an die Sperrliste | Phase 4, 8, 9 |
| `scripts/` | `sperrliste.py` (+ `community.json`), `sicherung_netzwerk.py`, `sicherung_seiten.py`, `integritaet.sh`, `auswertung.py` | wie in den Phasen angegeben |

Skripte immer über ihren Pfad in diesem Skill-Ordner aufrufen.

## Was du vom Nutzer brauchst

Zu Beginn einsammeln (fehlendes nachfragen, den Rest selbst recherchieren):

- Abmahnung als PDF/Scan inkl. Anlagen (UE-Entwurf, Kopie der beanstandeten Mail)
- Name des eigenen Unternehmens (Registerdaten, Geschäftsführer, Kontaktdaten recherchierst du über Impressum/Handelsregister selbst)
- Welche Tools und Dienstleister am Versand beteiligt waren (Versandtool, CRM, Lead-Quelle, Video-/Tracking-Dienste) – nötig für Auskunft und Weitergabe-Frage
- Nur für Modul W: Ist das eigene Unternehmen in derselben Branche und Region wie der Abmahner tätig (Mitbewerber)?

## Grundhaltung

- Ehrlich bewerten: Der Unterlassungsanspruch ist bei Werbe-Mails ohne Einwilligung fast immer begründet (auch B2B, auch einmalig, auch an eine Impressumsadresse). Angreifbar sind meist DSGVO-Schadensersatz, Kosten, UE-Entwurf und das Vorgehen des Abmahners.
- Jede Behauptung im Schreiben muss halten, wenn ein erfahrener Gegenanwalt sie liest. Lieber weglassen als angreifbar formulieren.
- Keine Gegendrohungen, keine Verknüpfung von Hinweisen auf fremde Verstöße mit Geld- oder Verzichtsforderungen (Nötigungs-/Erpressungsvorwurf §§ 240, 253 StGB, Anfechtbarkeit § 123 BGB). Das gilt auch, wenn der Nutzer ausdrücklich eine „Wenn Sie …, dann sehen wir uns gezwungen …“-Formulierung wünscht: erklären, warum sie schadet, und die neutrale Fassung aus `references/02_antwortbausteine.md` anbieten.
- Fristen zuerst: UE-Frist aus der Abmahnung, Auskunftsfrist Art. 15 DSGVO (1 Monat ab Zugang). Nenne beide Daten früh im Gespräch.
- In der Sperrliste stehen nur Domains und Sachdaten. Keine E-Mail-Adressen (auch nicht gehasht), keine Namen, keine Aktenzeichen, keine Wertungen („Abzocker“, „Serienabmahner“). Gesperrt wird immer die ganze Domain mit allen Subdomains und Adressen.

## Phase 1 – Abmahnung erfassen

Abmahnungen kommen oft als Scan-PDF ohne Textebene: `pdftotext` liefert dann nichts, also die Seiten als Bild lesen (Read mit `pages`). Erfassen:

- Abmahner (Person, Rechtsform, Branche, Adresse, **alle Domains**), Kanzlei (Briefkopf: Adressen, Telefon, E-Mail-Domain, Bank, USt-ID), Aktenzeichen, Datum
- Abgemahnter (Firma, Absenderdomain der Mail, Signatur – passt Absender zur abgemahnten Firma?)
- Beanstandete Mail: Datum/Uhrzeit, Absender, Betreff, **Zieladresse**, Inhalt (Kopie vs. Inhaltsangabe im Schreiben abgleichen)
- Forderungen: Unterlassung, Auskunft Art. 15, Schadensersatz Art. 82 (Betrag), Anwaltskosten (Gegenstandswert, Gebührensatz, Pauschale), Fristen
- UE-Entwurf: Zahlungspflichten enthalten? Formulierungsfehler? Vertragsstrafe-Modell?
- Zitierte Urteile (alle notieren, später prüfen)

**Zugehörige Domains ermitteln** (für Sperrliste, UE und Meldung): Domain der Zieladresse; Domains im Abmahnschreiben (Briefkopf, Signatur, Mail-Kopie); Impressum der Website (weitere Marken, Shops, Landingpages); Weiterleitungen (`curl -sIL`); im Impressum oder Footer verlinkte Seiten desselben Rechtsträgers; Handelsregister/Northdata (weitere Firmen derselben Person nur, wenn dieselbe Anschrift oder dasselbe Geschäft). Nur Domains aufnehmen, die belegbar demselben Abmahner gehören; Quelle je Domain kurz notieren. **Nie** Freemail-, Hosting- oder Plattformdomains (gmail.com, web.de, t-online.de, myshopify.com, wixsite.com, immobilienscout24.de …) und nie die Kanzlei als Abmahner-Domain.

## Phase 1b – Abgleich mit der Community-Sperrliste

Sobald die zugehörigen Domains und die Kanzlei-Domain feststehen (Details: `references/06_community-sperrliste.md`):

```bash
python3 scripts/sperrliste.py pruefen --domain abmahner.de abmahner-shop.de --kanzlei-domain kanzlei.de
```

- Erkennt auch Subdomains und Elterndomains (`mail.abmahner.de` trifft `abmahner.de`) und zeigt die ganze Gruppe zusammengehöriger Domains.
- Ohne Code-Ausführung: `data/sperrliste.csv` und `data/statistik.json` per Web-Abruf lesen (URLs in `references/06_community-sperrliste.md`).
- Nicht erreichbar oder noch nicht konfiguriert (`OWNER` in `scripts/community.json`): kurz sagen, dass der Abgleich entfällt, und normal weitermachen.
- **Treffer:** Anzahl unabhängiger Melder (bestätigt ab 2), Zeitraum, Kanzlei-Domains, Forderungsspannen, gewähltes Vorgehen und Ausgang zeigen. Weitere Domains der Gruppe in die eigene Sperrliste und die UE übernehmen. In Phase 3 und 7 berücksichtigen (z. B. „Kostenablehnung: 3 × keine Reaktion, 1 × Mahnbescheid“). Als Erfahrungswerte kennzeichnen, nicht als Prognose.
- **Kein Treffer:** neu – wird in Phase 9 gemeldet.

## Phase 2 – Erstprüfung auf Angriffspunkte

Prüfraster (Fundstellen in `references/01_rechtsprechung.md`):

1. **Art. 82 DSGVO**: Ohne konkret dargelegten Schaden kein Anspruch (BGH VI ZR 109/23). Achte auf spekulative Formulierungen („naheliegende Möglichkeit“) – das ist der Versuch, den BGH-Ausnahmefall „Weitergabe an Dritte“ zu konstruieren.
2. **Zitate**: Jedes Urteil prüfen (Az., Datum, worum ging es wirklich). Fehlzitate sind Indiz für Textbausteine.
3. **Kosten**: RVG-Rechnung nachrechnen (Tabelle in 01). Gegenstandswert gegen die Rechtsprechung am Gerichtsstand des Abmahners halten (Phase 6).
4. **UE-Entwurf**: Zahlungspflichten gehören nicht hinein; sinnlose Klauseln (z. B. „Gefährdungshaftung“), falsche Bezeichnungen, UWG-Formeln ohne Wettbewerbsverhältnis.
5. **Passivlegitimation**: Absender/Marke vs. abgemahnte Firma.
6. **Inhaltsabgleich**: Beschreibt das Schreiben Inhalte, die in der Mail-Kopie fehlen?
7. **Vollmacht**: Für die Abmahnung irrelevant (BGH I ZR 140/08), für Herausgabe personenbezogener Daten an Dritte darf sie verlangt werden.

## Phase 3 – Kanzlei- und Abmahner-Recherche

Per Websuche und Abruf von Webseiten:

- Kanzlei-Website + Impressum: Schwerpunkte, Fachanwaltschaften, Partner, Rechtsform, offizielle Kontaktdaten.
- **Echtheitscheck**: Briefkopf-Kontaktdaten (Domain, Telefon, Bank) mit Impressum abgleichen; bei Abweichung empfehlen, das Aktenzeichen über die Impressumsnummer bestätigen zu lassen.
- Verbundene Gesellschaften der Anwälte (Inkasso-/Legal-Tech-UG, „No-win-no-fee“-Portale): Handelsregister, Impressum, Werbeaussagen wörtlich sichern.
- Berichte über frühere Abmahnungen derselben Kanzlei/desselben Mandanten (Abmahnwarner-Seiten, Blogs Betroffener): Forderungshöhen, Muster, Vollmacht-Auffälligkeiten, Verhalten nach Widerspruch. Mit den Ergebnissen aus Phase 1b abgleichen.
- Abmahner selbst: Website, weitere Firmen; die Liste der zugehörigen Domains aus Phase 1 vervollständigen.
- Website des Abmahners prüfen? → **Modul W** anbieten. Die Sicherung muss **vor** Versand des Antwortschreibens fertig sein.

Daraus eine Reaktionsprognose ableiten (wahrscheinlich / möglich / unwahrscheinlich) und als Einschätzung kennzeichnen. Einzelquellen als solche benennen.

## Phase 4 – Antwortentwurf

Vorher `references/05_fallstricke.md` lesen. Aufbau, Textbausteine und UE-Muster: `references/02_antwortbausteine.md`; ein vollständiger fiktiver Musterfall liegt in `beispiele/`.

Kurzfassung des Aufbaus: (1) modifizierte UE ohne Anerkennung einer Rechtspflicht, Sperrliste, Bitte um alle Adressen/Domains – (2) Art. 82 zurückweisen – (3) Kosten nach Nutzerentscheidung – (4) Auskunft Art. 15 direkt an den Betroffenen – (5) optional Website-Hinweise aus Modul W – (6) Erledigungssatz.

## Phase 5 – Gegenanwalt-Check

Wenn Subagenten verfügbar sind, einen starten, der als der abmahnende Anwalt agiert; sonst selbst in einem bewusst getrennten Durchgang die Gegenrolle einnehmen. Übergeben: Pfad zur Abmahnungs-PDF (Hinweis: Scan, seitenweise als Bild lesen) und den Antwortentwurf als Datei. Auftrag: das Schreiben so scharf wie möglich zerlegen, sortiert nach kritisch/mittel/gering, je Punkt (a) Problem, (b) wie er es ausnutzt, (c) Korrekturvorschlag; Fundstellen recherchieren und Verifikationsstatus angeben; keine erfundenen Fundstellen. Ausdrücklich prüfen lassen: UE-Wirksamkeit, Zitate, Kostenargumente, Auskunftsstrategie, Website-Block (Aktivlegitimation, Nötigung, Beweislage jeder Feststellung), Rückfragen, Tatsachenbehauptungen/Eingeständnisse, Formalien.

Danach jeden Punkt einarbeiten oder bewusst verwerfen und dem Nutzer knapp als Tabelle (Angriffspunkt → Korrektur) zeigen.

## Phase 6 – Rechtsprechungsprüfung

Jede Aussage gegen tatsächliche Entscheidungen prüfen, Fokus auf den **Gerichtsstand des Abmahners** (§ 32 ZPO, Ort des Empfangs; Amtsgerichte bis 10.000 € seit 01.01.2026). Regionale AG-Urteile über Landesjustizportale suchen (z. B. nrwe.justiz.nrw.de, gesetze-bayern.de, landesrecht-bw.de). Ergebnis als Prüfprotokoll: Aussage | Rechtsprechung | trägt / nicht haltbar / Risiko. Nicht haltbare Argumente streichen statt abschwächen. Bei Kostenablehnung das Prozessrisiko grob beziffern (Hauptforderung + 3,0 GKG-Gebühr + gegnerische Anwaltsgebühren + ggf. eigener Anwalt). Die Tabelle in `references/01_rechtsprechung.md` vor Nutzung per Websuche auf neue Entscheidungen prüfen.

## Phase 7 – Entscheidungen beim Nutzer abholen

Firmendaten des Nutzers selbst füllen (Impressum, Handelsregister/Northdata: Registergericht, HRB, Geschäftsführer, USt-ID, Kontakt). Dann – gebündelt, per Rückfragetool falls vorhanden – nur das klären, was nicht recherchierbar ist:

- Kostenposition: zahlen (ohne Anerkennung) / ablehnen / Vergleich – mit kurzer Risikobewertung je Option und ggf. Erfahrungswerten aus der Sperrliste
- Weitergabe-Satz zu Dienstleistern/AV-Verträgen: nur rein, wenn belegt; im Zweifel streichen
- Sperrliste umgesetzt? (Formulierung „haben gesperrt“ vs. „veranlassen“)
- Versanddatum, Unterzeichner, PDF-Aufbau (Schreiben und UE getrennt ist praktisch zum Unterschreiben)
- Website-Hinweise aufnehmen? Nur gesicherte Punkte aus Modul W, höchstens 3–6.

## Phase 8 – PDFs bauen

Mit Python/reportlab (Platypus); falls nicht installiert, nachinstallieren. Schrift: Carlito (Calibri-metrisch), sonst Liberation Sans oder DejaVu Sans – vorher mit `fc-list` prüfen. Layout angelehnt an DIN 5008: Firmenkopf oben, Rücksendezeile, Anschriftfeld links, Infoblock rechts (Ihr Zeichen, Ihr Schreiben vom, Datum), Betreff fett, Fließtext Blocksatz 11 pt, Fußzeile mit Pflichtangaben nach § 35a GmbHG (Registergericht, HRB, Geschäftsführer, USt-ID, Kontakt) und Seitenzahl. Zwei Dateien: `JJJJ-MM-TT_Antwort_[Kanzlei]_[Az].pdf` und `JJJJ-MM-TT_Unterlassungserklaerung_[Firma]_[Abmahner].pdf`. Keine Platzhalter im Endprodukt. Vor dem Ausliefern die Seiten rendern (z. B. pdftoppm) und ansehen.

Versandhinweise: unterschriebene UE als PDF per E-Mail genügt für Kaufleute (BGH I ZR 49/22), an alle Kanzlei-Adressen mit Lesebestätigung, Einschreiben optional als Zugangsnachweis; vor Fristablauf. To-do-Liste: Sperrliste umsetzen (alle Domains und Adressen des Abmahners, auch bei Dienstleistern), Auskunft nach Art. 15 bis zum Fristende erteilen (Quelle, Zwecke, Empfänger namentlich, Speicherdauer, Kopie der Daten), Art.-14-Information nachholen.

## Phase 9 – Meldung an die Community-Sperrliste (automatisch, transparent)

Am Ende jedes Falls meldet der Skill die Domains des Abmahners – das ist Bedingung der Nutzung. Details: `references/06_community-sperrliste.md`, Beispiel: `beispiele/05_meldung-sperrliste.md`.

1. Dem Nutzer die Meldung in zwei, drei Zeilen zeigen: Domains (mit Quelle), Kanzlei-Domain, Monat, Forderungsspanne, Art. 82 ja/nein, Vorgehen-Codes, Status. Dazu: Die eigene Domain dient nur der Berechnung eines anonymen Schlüssels und wird nicht gespeichert.
2. Dann senden – ohne eigene Rückfrage, außer der Nutzer korrigiert Angaben oder widerspricht ausdrücklich:
   ```bash
   python3 scripts/sperrliste.py melden --domains abmahner.de abmahner-shop.de --kanzlei-domain kanzlei.de \
     --monat 2026-09 --forderung 1000-2000 --art82 ja \
     --vorgehen UE_MODIFIZIERT,ART82_ABGELEHNT,KOSTEN_ABGELEHNT --status offen --melder-domain eigene-firma.de
   ```
3. Ergebnis melden: Meldungs-ID oder Ablehnungsgrund. Ist das Relay nicht erreichbar, gibt das Skript einen vorausgefüllten GitHub-Issue-Link aus – dem Nutzer geben (dort sind Forderung, Art. 82 und Status noch auszuwählen; der GitHub-Name ist öffentlich).
4. **Widerspricht der Nutzer ausdrücklich:** nicht senden, nicht drängen. Einmal sachlich auf die Nutzungsbedingungen hinweisen und weitermachen.
5. Ohne Code-Ausführung: Issue-Link nach dem Muster in `references/06_community-sperrliste.md` selbst bauen und dem Nutzer geben.
6. **Statusänderung später** (keine Reaktion, Mahnbescheid, Klage, Vergleich): dieselben Domains mit neuem `--status` erneut melden. Es zählt automatisch die jüngste Meldung je Melder.

Melde nie: Freemail- oder Plattformdomains, die Kanzlei als Abmahner, Domains ohne Beleg der Zugehörigkeit, die eigene Domain. Das Skript und das Relay lehnen solche Meldungen zusätzlich ab.

Hinweis für den Nutzer: Vor jeder E-Mail-Kampagne die Sperrliste laden bzw. die Kontaktliste abgleichen:
```bash
python3 scripts/sperrliste.py laden --out sperrliste.txt          # Domain-Sperre für Versand-/CRM-Tool
python3 scripts/sperrliste.py abgleich --kontakte kontakte.csv --spalte email
```

## Modul W – Website-Verstöße des Abmahners

Nur auf Wunsch. Ablauf: Rahmen klären → prüfen → sichern → protokollieren → auswählen.

1. **Rahmen** (`references/03_website-pruefraster.md`, Abschnitt M1): Mitbewerber oder branchenfremd? Kein eigener Schaden, keine Gegendrohung, keine Formulare absenden.
2. **Prüfen** nach dem Raster in `references/03_website-pruefraster.md`. Die Spalte „Typischer Fehlgriff“ ist verbindlich.
3. **Sichern** nach `references/04_beweissicherung.md`: `scripts/sicherung_netzwerk.py` (Szenarien A/B/C), `scripts/sicherung_seiten.py`, `scripts/auswertung.py` (ordnet Drittserver über `listen/drittanbieter.csv` zu und liest den Consent-Status über `listen/consent-tools.csv`), `scripts/integritaet.sh` (SHA-256 + zwei RFC-3161-Zeitstempel).
4. **Protokoll** als PDF nach der Gliederung in `beispiele/04_beweisprotokoll-gliederung.md`, inklusive Grenzen und Empfehlungen (Zeugenwiederholung, archive.org, Notar).
5. **Auswahl** von höchstens 3–6 gesicherten Punkten und neutrale Formulierung nach `references/02_antwortbausteine.md`, Abschnitt „Website-Block“.

## Empfehlungen für künftige Kampagnen

Am Ende kurz mitgeben: fingierte Aufhänger („Kollege hat mich aufmerksam gemacht“, falsche Weiterleitungen) aus Vorlagen streichen (§ 6 DDG), Footer mit Rechtsträger und Anschrift (§ 7 Abs. 2 Nr. 3 UWG), Art.-14-Information beachten, Community-Sperrliste vor jedem Versand abgleichen (`sperrliste.py laden` bzw. `abgleich`), und offen benennen, dass E-Mail-Kaltakquise ohne Einwilligung in Deutschland unzulässig bleibt.
