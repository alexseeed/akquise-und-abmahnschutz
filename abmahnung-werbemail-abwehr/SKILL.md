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
- **Schnell bei der Unterlassung, fest beim Geld.**
  - Nur bei der Unterlassungserklärung zählt Tempo. Sie allein beseitigt die Wiederholungsgefahr und verhindert eine einstweilige Verfügung.
  - Bei allen Geldforderungen gilt die feste Linie. Das betrifft Anwaltskosten, Art. 82 und Zahlungspflichten im UE-Entwurf.
  - Im ersten Schreiben wird nichts gezahlt. Kosten erst nach Kostennote und Nachweis der Zahlung oder Zahlungspflicht (Phase 7).
  - Den Gegenstandswert immer prüfen und, wenn er überhöht ist, begründet rügen.
  - Jede Forderung einzeln prüfen. Nachgeben nur, wo die Rechtslage es verlangt, nicht wegen kurzer Fristen, hoher Beträge oder Druck im Ton.
- **Fest heißt nicht laut.** Die Härte entsteht durch genaue, prüfbare Sätze, nicht durch Drohungen, Wertungen oder eine Flut von Rückfragen. Jede Nachweisforderung muss rechtlich etwas bringen (Phase 4).
- Jede Behauptung im Schreiben muss halten, wenn ein erfahrener Gegenanwalt sie liest. Lieber weglassen als angreifbar formulieren.
- **Nichts preisgeben, was gegen den Nutzer verwendet werden kann.** Keine Angaben zu Tools, Listen, Sequenzen, Versanddomains oder weiteren Mails. Wer systematisch versendet, bekommt einen höheren Gegenstandswert und Folgeabmahnungen. Das gilt auch für Briefkopf, Absenderadresse und die Formulierung der Sperre.
- Keine Gegendrohungen, keine Verknüpfung von Hinweisen auf fremde Verstöße mit Geld- oder Verzichtsforderungen (Nötigungs-/Erpressungsvorwurf §§ 240, 253 StGB, Anfechtbarkeit § 123 BGB). Das gilt auch, wenn der Nutzer ausdrücklich eine „Wenn Sie …, dann sehen wir uns gezwungen …“-Formulierung wünscht: erklären, warum sie schadet, und die neutrale Fassung aus `references/02_antwortbausteine.md` anbieten.
- Fristen zuerst: UE-Frist aus der Abmahnung, Auskunftsfrist Art. 15 DSGVO (1 Monat ab Zugang). Nenne beide Daten früh im Gespräch.
- In der Sperrliste stehen nur Domains und Sachdaten. Keine E-Mail-Adressen (auch nicht gehasht), keine Namen, keine Aktenzeichen, keine Wertungen („Abzocker“, „Serienabmahner“). Gesperrt wird immer die ganze Domain mit allen Subdomains und Adressen.

## Phase 1 – Abmahnung erfassen

Abmahnungen kommen oft als Scan-PDF ohne Textebene: `pdftotext` liefert dann nichts, also die Seiten als Bild lesen (Read mit `pages`). Erfassen:

- Abmahner (Person, Rechtsform, Branche, Adresse, **alle Domains**), Kanzlei (Briefkopf: Adressen, Telefon, E-Mail-Domain, Bank, USt-ID), Aktenzeichen, Datum
- Abgemahnter: Firma, Absenderdomain der Mail, Signatur (passt der Absender zur abgemahnten Firma?).
- **Rechtsform des Abgemahnten:** Kaufmann oder nicht (GbR, Freiberufler, Kleingewerbe)? Davon hängen Form und Unterschriften der UE ab (Phase 8).
- **Frühere Abmahnungen** gegen denselben Nutzer (eigene Fallakte, Sperrliste)? Mehrere in kurzer Zeit wirken wie systematischer Versand. Dann besonders streng auf Angaben zu Tools, Listen und Domains achten.
- Beanstandete Mail: Datum/Uhrzeit, Absender, Betreff, **Zieladresse**, Inhalt (Kopie vs. Inhaltsangabe im Schreiben abgleichen)
- **Zugang:** Datum und Weg (Einwurf-Einschreiben mit Sendungsnummer, Fax, E-Mail) festhalten. Umschlag und Sendungsverfolgung sichern lassen, falls das Schreiben mit der Frist argumentiert.
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
2. **Zitate**: Jedes Urteil prüfen (Az., Datum, Urteil oder Beschluss, worum ging es wirklich). Fehlzitate sind Indiz für Textbausteine. **Besonders prüfen, ob die eigenen Zitate des Abmahners einen niedrigeren Wert tragen** als den geforderten. Das ist das stärkste Argument gegen den Gegenstandswert (Beispiel in 01).
3. **Kosten**: RVG-Rechnung nachrechnen (Tabelle in 01). Gegenstandswert gegen die Rechtsprechung am Gerichtsstand des Abmahners halten (Phase 6). Erstattungsfähig sind nur Kosten, die der Mandant seinem Anwalt tatsächlich schuldet.
4. **UE-Entwurf**:
   - Zahlungspflichten gehören nicht hinein.
   - Feste Vertragsstrafe statt neuem Hamburger Brauch.
   - Überdehnte Reichweite: „sonstige elektronische Nachrichten“ ohne Werbebezug, alle Kanäle, verbundene Unternehmen.
   - „oder“-Falle bei § 7 Abs. 3 UWG.
   - Sinnlose Klauseln (z. B. „Gefährdungshaftung“), falsche Bezeichnungen, UWG-Formeln ohne Wettbewerbsverhältnis.
5. **Passivlegitimation**: Absender/Marke vs. abgemahnte Firma.
6. **Inhaltsabgleich**: Beschreibt das Schreiben Inhalte, die in der Mail-Kopie fehlen? Fehlt die Kopie ganz?
7. **Vollmacht**: Für die Abmahnung irrelevant (BGH I ZR 140/08), für Herausgabe personenbezogener Daten an Dritte darf sie verlangt werden.
8. **Frist und Zugang**: Läuft die Frist am oder vor dem Zugangstag ab, ist sie unangemessen kurz. Dann gilt eine angemessene Frist. Das im Schreiben kurz festhalten, trotzdem sofort handeln.
9. **Auskunft Art. 15**: Das Recht hat nur die betroffene natürliche Person, nicht die GmbH oder KG, die abmahnt. Die Forderung trotzdem als Antrag der Person behandeln (Phase 4).

## Phase 3 – Kanzlei- und Abmahner-Recherche

Per Websuche und Abruf von Webseiten:

- Kanzlei-Website + Impressum: Schwerpunkte, Fachanwaltschaften, Partner, Rechtsform, offizielle Kontaktdaten.
- **Echtheitscheck**: Briefkopf-Kontaktdaten (Domain, Telefon, Bank) mit Impressum abgleichen; bei Abweichung empfehlen, das Aktenzeichen über die Impressumsnummer bestätigen zu lassen.
- Verbundene Gesellschaften der Anwälte (Inkasso-/Legal-Tech-UG, „No-win-no-fee“-Portale): Handelsregister, Impressum, Werbeaussagen wörtlich sichern.
- **Geschäftsmodell der Kanzlei:** Einzelanwalt mit Abmahnroutine oder Massenbetrieb? Wirbt die Kanzlei öffentlich um Empfänger von Werbe-Mails, etwa mit Rechtstipps nach dem Muster „die Kosten trägt der Verursacher“? Quellen: Kanzlei-Website, anwalt.de-Profil, Abmahnanwälte-Liste des Händlerbunds. Für Rechtsmissbrauch reicht das nicht. Es stützt aber die Linie „erst Kostennachweis“. Im Schreiben nicht erwähnen.
- Berichte über frühere Abmahnungen derselben Kanzlei/desselben Mandanten (Abmahnwarner-Seiten, Blogs Betroffener): Forderungshöhen, Muster, Vollmacht-Auffälligkeiten, Verhalten nach Widerspruch. Mit den Ergebnissen aus Phase 1b abgleichen.
- Abmahner selbst: Website, weitere Firmen; die Liste der zugehörigen Domains aus Phase 1 vervollständigen.
- **Eigene Angriffsfläche des Nutzers:** Versanddomain prüfen (Registrierungsdatum, Website, Impressum, gleichzeitig registrierte Schwesterdomains). Was die Gegenseite findet, stützt einen höheren Wert. Es darf deshalb weder im Schreiben noch im Briefkopf auftauchen.
- Website des Abmahners prüfen? → **Modul W** anbieten. Die Sicherung muss **vor** Versand des Antwortschreibens fertig sein.
- Seiten, die einen einfachen Abruf mit 403 blocken, im Browser öffnen. Bot-Schutz nie umgehen, also keine gefälschten User-Agents.

Daraus eine Reaktionsprognose ableiten (wahrscheinlich / möglich / unwahrscheinlich) und als Einschätzung kennzeichnen. Einzelquellen als solche benennen.

## Phase 4 – Antwortentwurf

Vorher `references/05_fallstricke.md` lesen. Aufbau, Textbausteine und UE-Muster: `references/02_antwortbausteine.md`; ein vollständiger fiktiver Musterfall liegt in `beispiele/`.

Kurzfassung des Aufbaus:

0. Zugang und, falls nötig, Absatz zur unangemessen kurzen Frist.
1. Modifizierte UE ohne Anerkennung einer Rechtspflicht:
   - Änderungen gegenüber dem Entwurf offen benennen.
   - Konkrete Änderungswünsche anbieten.
   - Sperre neutral formulieren.
   - Um alle Adressen und Domains des Abmahners bitten.
2. Art. 82 zurückweisen.
3. Kosten: Standard „erst Nachweis“ und im selben Schreiben die Rüge des Gegenstandswerts.
4. Auskunft Art. 15: Vollmacht oder anwaltliche Versicherung mit Frist anfordern, sonst verschlossen über die Kanzlei.
5. Optional Website-Hinweise aus Modul W.
6. Schluss: „Mit der anliegenden Erklärung ist die Wiederholungsgefahr entfallen.“

**Keine Rückfragen-Runde vor der UE.** Rückfragen halten die Frist nicht an. Sie kosten das Kostenprivileg nach § 93 ZPO und lesen sich als Hinhalten. Eine Kanzlei mit Abmahnroutine beantwortet sie nebenbei, eine einstweilige Verfügung kostet den Nutzer schnell 2.000 bis 3.000 €. Nachweisforderungen gehören deshalb **in dasselbe Schreiben wie die UE**. Zulässig sind nur Forderungen, die rechtlich etwas bringen:

- Kostennote nach § 10 RVG und Nachweis der Zahlung oder Zahlungspflicht
- Vollmacht oder anwaltliche Versicherung für die Herausgabe personenbezogener Daten
- Kopie der beanstandeten Mail, falls sie fehlt
- alle Adressen und Domains des Abmahners

Nie anfordern: Header oder .eml-Datei, Vollmacht für die Abmahnung, Schadensnachweis, wenn kein Schaden gefordert wird. Wünscht der Nutzer ein „Bombardement“, das kurz begründen und diese Auswahl anbieten.

## Phase 5 – Gegenanwalt-Check

Wenn Subagenten verfügbar sind, einen starten, der als der abmahnende Anwalt agiert; sonst selbst in einem bewusst getrennten Durchgang die Gegenrolle einnehmen. Übergeben: Pfad zur Abmahnungs-PDF (Hinweis: Scan, seitenweise als Bild lesen) und den Antwortentwurf als Datei. Auftrag: das Schreiben so scharf wie möglich zerlegen, sortiert nach kritisch/mittel/gering, je Punkt (a) Problem, (b) wie er es ausnutzt, (c) Korrekturvorschlag; Fundstellen recherchieren und Verifikationsstatus angeben; keine erfundenen Fundstellen. Ausdrücklich prüfen lassen:

- UE-Wirksamkeit, Form und Unterschriften
- Zitate, auch Urteil oder Beschluss und Fundstelle
- Kostenargumente, besonders Sätze, die als ernsthafte Zahlungsverweigerung gelesen werden können (§ 250 BGB)
- Frist und Zugang
- Auskunftsstrategie und Zustellweg
- Website-Block: Aktivlegitimation, Nötigung, Beweislage jeder Feststellung
- Rückfragen
- Tatsachenbehauptungen und Eingeständnisse, etwa „nur eine Mail“ oder „in allen Systemen gesperrt“
- Hinweise auf die Versandinfrastruktur in Briefkopf und Absenderadresse
- Formalien

Danach jeden Punkt einarbeiten oder bewusst verwerfen und dem Nutzer knapp als Tabelle (Angriffspunkt → Korrektur) zeigen.

## Phase 6 – Rechtsprechungsprüfung

Jede Aussage gegen tatsächliche Entscheidungen prüfen, Fokus auf den **Gerichtsstand des Abmahners** (§ 32 ZPO, Ort des Empfangs; Amtsgerichte bis 10.000 € seit 01.01.2026). Regionale AG-Urteile über Landesjustizportale suchen (z. B. nrwe.justiz.nrw.de, gesetze-bayern.de, landesrecht-bw.de). Ergebnis als Prüfprotokoll: Aussage | Rechtsprechung | trägt / nicht haltbar / Risiko. Nicht haltbare Argumente streichen statt abschwächen. Bei Kostenablehnung das Prozessrisiko grob beziffern (Hauptforderung + 3,0 GKG-Gebühr + gegnerische Anwaltsgebühren + ggf. eigener Anwalt). Die Tabelle in `references/01_rechtsprechung.md` vor Nutzung per Websuche auf neue Entscheidungen prüfen.

## Phase 7 – Entscheidungen beim Nutzer abholen

Firmendaten des Nutzers selbst füllen (Impressum, Handelsregister/Northdata: Registergericht, HRB, Geschäftsführer, USt-ID, Kontakt). Dann – gebündelt, per Rückfragetool falls vorhanden – nur das klären, was nicht recherchierbar ist:

- **Kostenposition. Standard ist „erst Nachweis“ (Variante B):**
  - Kostennote nach § 10 RVG und Nachweis der Zahlung oder Zahlungspflicht anfordern.
  - Ausdrücklich schreiben, dass eine Zahlung damit nicht abgelehnt wird.
  - Antwort binnen 14 Tagen nach Eingang zusagen.
  - Im selben Schreiben den Gegenstandswert begründet rügen.

  Die anderen Optionen nur auf ausdrücklichen Wunsch, je mit beziffertem Risiko:
  - Teilzahlung auf reduzierten Wert, ohne Anerkennung, wenn der Nutzer Ruhe will.
  - Volle Zahlung ohne Anerkennung, nur bei Stufe A mit Wert bis 3.000 €.
  - Ablehnung, nur bei Missbrauchsverdacht mit belegbaren Tatsachen.

  Dazu Erfahrungswerte aus der Sperrliste. Volle Zahlung nie von sich aus empfehlen, nur weil sie bequem ist.
- Weitergabe-Satz zu Dienstleistern/AV-Verträgen: nur rein, wenn belegt; im Zweifel streichen
- Sperre umgesetzt? Formulierung neutral: „haben veranlasst, dass … keine Werbung mehr zugeht“. Nie „in allen Systemen gesperrt“, das verrät Massenversand.
- Gab es weitere Mails an den Abmahner (Follow-ups, Sequenzen)? Der Nutzer muss das intern prüfen. Gibt es welche, darf das Schreiben nicht von „einer E-Mail“ ausgehen.
- Versanddatum, Unterzeichner (bei der GbR alle Gesellschafter), PDF-Aufbau (Schreiben und UE getrennt ist praktisch zum Unterschreiben)
- Website-Hinweise aufnehmen? Nur gesicherte Punkte aus Modul W, höchstens 3–6.

## Phase 8 – PDFs bauen

Mit Python/reportlab (Platypus); falls nicht installiert, nachinstallieren. Schrift: Carlito (Calibri-metrisch), sonst Liberation Sans oder DejaVu Sans – vorher mit `fc-list` prüfen. Layout angelehnt an DIN 5008: Firmenkopf oben, Rücksendezeile, Anschriftfeld links, Infoblock rechts (Ihr Zeichen, Ihr Schreiben vom, Datum), Betreff fett, Fließtext Blocksatz 11 pt, Fußzeile mit Pflichtangaben nach § 35a GmbHG (Registergericht, HRB, Geschäftsführer, USt-ID, Kontakt) und Seitenzahl. Zwei Dateien: `JJJJ-MM-TT_Antwort_[Kanzlei]_[Az].pdf` und `JJJJ-MM-TT_Unterlassungserklaerung_[Firma]_[Abmahner].pdf`. Keine Platzhalter im Endprodukt. Vor dem Ausliefern die Seiten rendern (z. B. pdftoppm) und ansehen.

Briefkopf ohne Versand- oder Akquisedomain: Firma, Anschrift und Telefon genügen. Bei der GbR in der Fußzeile alle Gesellschafter.

Versandhinweise:

- **Form:**
  - **Kaufleute:** unterschriebene UE als PDF per E-Mail genügt (BGH I ZR 49/22).
  - **Nicht-Kaufleute** (GbR, Freiberufler, Kleingewerbe): Schriftform (§§ 780, 781 BGB; § 350 HGB gilt nur für Kaufleute). Vorab per E-Mail senden, Original per Einschreiben hinterher.
  - **GbR:** alle Gesellschafter unterschreiben (§ 720 BGB).
- **Kein Telefax:** Es wird nie per Fax versendet, auch wenn die Kanzlei eine Faxnummer nennt. Vorab geht alles nur per E-Mail. Lässt die Kanzlei zur Fristwahrung ausdrücklich nur ein Fax genügen, das Original noch am selben Tag per Einschreiben aufgeben, damit es binnen der genannten Werktage ankommt.
- **Absender:** aus einem Postfach senden, das nicht für Akquise genutzt wird. An alle Kanzlei-Adressen, mit Lesebestätigung.
- **Fristen:** vor Fristablauf versenden. Verlangt die Kanzlei das Original binnen weniger Werktage, Feiertage an beiden Orten einrechnen und den Termin für die Post nennen.
- **Datum:** Das Schreiben trägt den Versandtag. Verschiebt sich der Versand, das Datum in allen Dokumenten anpassen.

To-do-Liste:

- Sperre umsetzen: alle Domains und Adressen des Abmahners, in allen Kanälen (Mail, LinkedIn, Telefon, Messenger) und bei Dienstleistern. Dokumentieren.
- Laufende Sequenzen an den Abmahner stoppen.
- Auskunft nach Art. 15 bis zum Fristende erteilen: Quelle, Zwecke, Empfänger namentlich, Speicherdauer, Kopie der Daten.
- Art.-14-Information nachholen.

Ist der Nutzer ein Dienstleister, der den Fall für einen Kunden bearbeitet, zusätzlich ein Begleitschreiben an den Kunden: Fristen, Einschätzung, Kosten und Risiko je Variante, To-dos mit Datum, nächste Schritte.

## Phase 9 – Meldung an die Community-Sperrliste (automatisch, transparent)

Am Ende jedes Falls meldet der Skill die Domains des Abmahners – das ist Bedingung der Nutzung. Details: `references/06_community-sperrliste.md`, Beispiel: `beispiele/05_meldung-sperrliste.md`.

1. Dem Nutzer die Meldung in zwei, drei Zeilen zeigen: Domains (mit Quelle), Kanzlei-Domain, Monat, Forderungsspanne, Art. 82 ja/nein, Vorgehen-Codes, Status. Dazu: Die eigene Domain dient nur der Berechnung eines anonymen Schlüssels und wird nicht gespeichert.
2. Dann senden – ohne eigene Rückfrage, außer der Nutzer korrigiert Angaben oder widerspricht ausdrücklich:
   ```bash
   python3 scripts/sperrliste.py melden --domains abmahner.de abmahner-shop.de --kanzlei-domain kanzlei.de \
     --monat 2026-09 --forderung 1000-2000 --art82 ja \
     --vorgehen UE_MODIFIZIERT,ART82_ABGELEHNT,KOSTEN_ABGELEHNT --status offen --melder-domain eigene-firma.de
   ```
   Bei „erst Nachweis“ (Variante B) noch keinen `KOSTEN_`-Code melden. Status bleibt `offen`. Der Code (`KOSTEN_GEZAHLT`, `KOSTEN_VERGLEICH`, `KOSTEN_ABGELEHNT`) wird nachgemeldet, sobald die Kostenfrage entschieden ist.
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

## Phase 10 – Nachgang (wenn die Kanzlei antwortet)

Die feste Linie gilt auch nach dem Versand:

- **Kostennote kommt:**
  - Prüfen: Ist sie an den Mandanten gerichtet? Stimmen Datum, Wert und Betrag? Liegt ein Nachweis der Zahlung oder Zahlungspflicht bei?
  - Binnen der zugesagten Frist zahlen, aber auf Basis des eigenen, begründeten Werts, ohne Anerkennung einer Rechtspflicht.
  - Dazu der Satz: „Darüber hinausgehende Forderungen weisen wir zurück.“
- **Kein Nachweis, nur Mahnung:** Nicht von sich aus zahlen. Den Nachweis einmal sachlich erneut anfordern.
- **Änderungswünsche zur UE:** zügig prüfen. Berechtigte Wünsche übernehmen. Das sichert die Kostenposition nach § 93 ZPO.
- **Mahnbescheid:** binnen 2 Wochen Widerspruch einlegen und einen Anwalt beauftragen. Ebenso bei Klage, einstweiliger Verfügung oder Vertragsstrafe-Forderung.
- **Ausgang** an die Sperrliste nachmelden (Phase 9, Punkt 6).

## Modul W – Website-Verstöße des Abmahners

Nur auf Wunsch. Ablauf: Rahmen klären → prüfen → sichern → protokollieren → auswählen.

1. **Rahmen** (`references/03_website-pruefraster.md`, Abschnitt M1): Mitbewerber oder branchenfremd? Kein eigener Schaden, keine Gegendrohung, keine Formulare absenden.
2. **Prüfen** nach dem Raster in `references/03_website-pruefraster.md`. Die Spalte „Typischer Fehlgriff“ ist verbindlich.
3. **Sichern** nach `references/04_beweissicherung.md`: `scripts/sicherung_netzwerk.py` (Szenarien A/B/C), `scripts/sicherung_seiten.py`, `scripts/auswertung.py` (ordnet Drittserver über `listen/drittanbieter.csv` zu und liest den Consent-Status über `listen/consent-tools.csv`), `scripts/integritaet.sh` (SHA-256 + zwei RFC-3161-Zeitstempel).
4. **Protokoll** als PDF nach der Gliederung in `beispiele/04_beweisprotokoll-gliederung.md`, inklusive Grenzen und Empfehlungen (Zeugenwiederholung, archive.org, Notar).
5. **Auswahl** von höchstens 3–6 gesicherten Punkten und neutrale Formulierung nach `references/02_antwortbausteine.md`, Abschnitt „Website-Block“.

## Empfehlungen für künftige Kampagnen

Am Ende kurz mitgeben: keine frisch registrierten Versanddomains ohne Website und Impressum; nach einer Abmahnung die eigene Akquise auf weitere Risiken prüfen, denn zwei Abmahnungen in wenigen Wochen sind ein Muster; wer selbst versendet, kann auch persönlich abgemahnt werden; fingierte Aufhänger („Kollege hat mich aufmerksam gemacht“, falsche Weiterleitungen) aus Vorlagen streichen (§ 6 DDG), Footer mit Rechtsträger und Anschrift (§ 7 Abs. 2 Nr. 3 UWG), Art.-14-Information beachten, Community-Sperrliste vor jedem Versand abgleichen (`sperrliste.py laden` bzw. `abgleich`), und offen benennen, dass E-Mail-Kaltakquise ohne Einwilligung in Deutschland unzulässig bleibt.
