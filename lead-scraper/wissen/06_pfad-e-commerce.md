# Pfad „E-Commerce“ – aus einer Shop-Liste werden geprüfte Kontakte

**Zweck:** was der Pfad leistet, was er voraussetzt, was er kostet, wo seine Grenzen liegen.
**Für wen:** Nutzer mit einer Liste von Onlineshops und KI-Modelle, die Rückfragen beantworten.
**Verwandt:** `02_zielgruppen-interview.md` · `03_pfad-google-maps.md` (gleiche Anreicherung) · `07_lead-ausgabe-und-spalten.md` · `08_versand-und-recht.md`
**Technik im Detail:**

- Anleitung für die KI: `pfade/e-commerce/ABLAUF.md`
- jede Clay-Spalte und ihr Code: `pfade/e-commerce/docs/01_PROZESS.md`
- Abweichungen von Clay: `pfade/e-commerce/docs/05_ABWEICHUNGEN.md`
- Shops ohne Liste finden (geplant): `pfade/e-commerce/referenzen/shop-katalog.md`

**Stand:** 2026-10-09 · **Prüfen bis:** 2027-01-08 (Preise der Dienste; nach dem ersten echten Lauf die Quoten eintragen)

---

## Stand

**Gebaut, erster echter Testlauf steht aus.** Der Pfad ist ein 1:1-Nachbau des Clay-Workbooks „Vorlage | ECOM 2.0“, das bisher in Clay lief. Er läuft lokal mit Python, Clay wird nicht mehr gebraucht. Neu gegenüber Clay: Vor dem Lauf klärt die KI alle Anforderungen im Gespräch, prüft die Shops gegen ein Shop-Profil des Kunden und schreibt den persönlichen Satz passend zum Mailtext des Kunden (`pfade/e-commerce/docs/05_ABWEICHUNGEN.md`, Nr. 14–16). Ein Offline-Test mit Attrappen statt echter Dienste läuft durch. Fund- und Fehlerquoten aus einem echten Lauf fehlen noch (Tabelle unten).

## Wann dieser Pfad

Für **Onlineshops**, deren Namen oder Websites schon in einer Liste stehen. Typische Herkunft der Liste:

- Export aus einem Shop-Verzeichnis
- eigene Recherche
- Kundenliste

Typische Zielgruppen sind Anbieter für Shop-Agenturleistungen, Performance-Marketing, Logistik, Zahlungsanbieter und Software für Händler.

**Der Pfad findet keine Shops selbst.** Ohne Liste:

- Shops mit Laden oder Lager → Google-Maps-Pfad
- Shops, die auch auf Amazon verkaufen → Amazon-Pfad
- Woher man Shop-Listen nach Shopsystem bekommt: `pfade/e-commerce/referenzen/discovery-quellen.md`

## Wie die Herausforderung gelöst ist

Shop-Listen sind voller Karteileichen: Seiten im Wartungsmodus, reine Firmenseiten ohne Kasse, Shops ohne Besucher. Wer jede Zeile voll anreichert, bezahlt Impressum und E-Mail-Suche für Firmen, die nie Kunde werden.

Der Pfad prüft deshalb **zuerst billig** und reichert **nur die Treffer** an:

```
Shop-Liste ─► 1 Website finden ─► Startseite abrufen ─► KI: aktiver Onlineshop? Passt er zum Shop-Profil? ─► Besucherzahlen (SimilarWeb)
                                                                                               │
                                                 nur aktive, passende Shops mit Traffic ◄──────┘
                                                   │
           2 Impressum ─► Duplikate raus ─► E-Mail Geschäftsführung (sonst info@) ─► Anrede ─► persönlicher Satz ─► Videotitel ─► Export mit fertiger Mail
```

| Stufe | Was passiert | Dienst |
|---|---|---|
| 1a | Website per KI-Rechercheagent suchen, wenn nur ein Firmenname da ist | Skael-Agent (gemini-2.5-flash-lite) |
| 1b | Startseite abrufen | Skael `web_scraper` |
| 1c | KI prüft den Seitentext: Warenkorb, Kasse, Preise → aktiver Shop. Wartungsseite, Blog, reine Firmenseite → kein Shop. **Danach, wenn ein Shop-Profil gesetzt ist:** passt der aktive Shop zum Kunden (Region, Sortiment, Ausschlüsse)? Nicht passende Shops kosten keine Traffic-Abfrage mehr | OpenAI gpt-4o-mini |
| 1d | geschätzte Besuche der letzten Monate, nur für aktive, zum Profil passende Shops | Skael `webtraffic` (SimilarWeb) |
| 1e | **Filter:** Schnitt ≥ 1 **oder** Höchstwert ≥ 1 Besuch/Monat → weiter. Ohne SimilarWeb-Daten → raus. „Passt nicht zum Shop-Profil“ → raus | – |
| 2a–2g | Impressum, E-Mail-Wasserfall, Anrede, Personalisierung, Videotitel, „Ready to Send“ – dieselbe Logik wie Stufe 4 des Google-Maps-Pfads. Der persönliche Satz folgt der Anweisung, die für den Auftrag aus Angebot und Mailtext gebaut wurde | Skael, OpenAI, optional Findymail |

Die Schwellen sind einstellbar (`.env`: `MIN_AVR_TRAFFIC`, `MIN_MAX_TRAFFIC_3MO`, `TRAFFIC_MODE`). Mit höheren Werten bleiben nur größere Shops übrig, z. B. „ab 5.000 Besuchen im Monat“; dafür beide Schwellen anheben.

**Duplikate:** Mehrere Länder-Shops derselben Firma teilen meist eine E-Mail-Domain. Sie werden nur einmal angeschrieben.

**Export:** Ist ein Mailtext hinterlegt, enthält jede versandfertige Zeile die fertige Mail (Spalten `Betreff` und `Mailtext`, Platzhalter schon ersetzt).

## Shops ohne Liste finden – geplant

**Wunsch des Betreibers (08.10.2026):** keine Liste mehr vorgeben, sondern alle Onlineshops finden, nach Shopsystem filtern und z. B. nur Shopware-Shops holen.

**Gewählte Methode: ein zentraler Shop-Katalog.** Ausführlich in `pfade/e-commerce/referenzen/shop-katalog.md`.

1. Google veröffentlicht monatlich, welche Websites Chrome-Nutzer in DE, AT und CH besuchen (Chrome UX Report). Das sind ~1,16 Mio. Hosts, frei nutzbar (CC BY 4.0).
2. Ein höflicher Prüf-Roboter auf einem Server des Betreibers erkennt bei jedem Host das Shopsystem:
   - zuerst per DNS (Shopify, Wix, Jimdo …)
   - sonst per robots.txt und den ersten 64 KB der Startseite
3. Shopware-Shops werden wöchentlich nachgeprüft. Wechsel wie „Shopware 5 → 6“ oder „zu Shopify“ werden zu Ereignissen.
4. Nutzer holen ihr Segment mit `python3 -m ecom finden --system shopware5`. Danach läuft der Pfad wie oben.

**Was realistisch herauskommt:**

- **Menge:** Etwa jeder dritte Shopware-Shop in DACH, nämlich die mit nennenswerten Besuchern. Geschätzt 6.000–11.000, davon ~2.000–3.000 Shopware 5. Die Zahl ist noch nicht gemessen.
- **Was fehlt:** Sehr kleine Shops und Shops, die Bots sperren (10–20 %).
- **Wie aktuell:**
  - Systemwechsel zu Shopify ≤ 1 Tag
  - Shopware-Abgänge ≤ 7 Tage
  - neue Domains 2–3 Monate
  - Neue Domains in Minuten nur mit dem optionalen Zertifikats-Strom.

**Bevor gebaut wird (15–20 Entwicklertage):**

1. **Echttest:** ein kleiner Abruf von 5.000–10.000 Startseiten. Die gefundenen Shopware-Shops laufen durch diesen Pfad und zeigen, wie viele SEND und „Ready to Send“ erreichen.
2. **Recht und Betrieb klären:**
   - anwaltliche Kurzprüfung, vor allem zur Haftung des Betreibers als Lieferant der Ziele und zum Recht in AT/CH
   - Datenschutz-Folgenabschätzung
   - ein Hoster, der Crawling schriftlich erlaubt (Hetzner Cloud verbietet das Scannen fremder IPs)

**Verworfen:** gekaufte Listen als Quelle (Weitergabeverbote), Common Crawl (Nutzungsbedingungen), HTTP Archive per BigQuery (Kostenfalle, erkennt Shopware 6 schlecht).

## Voraussetzungen

| Was | Warum |
|---|---|
| Shop-Liste als CSV mit Firmenname und/oder Website | Eingabe; Format siehe `pfade/e-commerce/beispiel/shops_beispiel.csv` |
| Python ≥ 3.10 | läuft lokal |
| Zugang **Skael** (`eak_…`) | Website-Abruf, Traffic, Impressum, E-Mail-Suche und -Prüfung, Rechercheagent |
| Zugang **OpenAI** (`sk-…`, Guthaben aufgeladen) | Shop-Prüfung, Shop-Profil, Anrede, persönlicher Satz, Videotitel |
| optional **Findymail** | zweiter E-Mail-Finder, wenn Skael keine Geschäftsführer-Adresse findet; eigenes Abo, Preise in `11_zugaenge-und-kosten.md` |

Die Zugänge sind dieselben wie im Google-Maps-Pfad.

## Was vor dem Lauf geklärt sein muss

Bevor der Pfad etwas kostet, fragt die KI nach, bis alles da ist: eine einfache Frage pro Nachricht, immer mit Beispiel und Vorschlag. Was im Zielgruppen-Interview schon gesagt wurde, fragt sie nicht noch einmal. Dazu kommen Shop-Liste, Shopsystem, Mindestgröße, Shop-Profil (oder die bewusste Entscheidung „jeder aktive Shop“), Video, Mailtext mit persönlichem Satz und, falls vorhanden, Findymail. Pflichtangaben in der Mail wie Absender und Abmeldeweg: `08_versand-und-recht.md`.

Der Pfad startet nicht, solange etwas Nötiges fehlt. Vor dem Testlauf sieht der Nutzer eine Beispiel-Mail, nach dem Testlauf zwei, drei fertige Mails aus seiner Liste. Erst nach seinem Okay läuft die ganze Liste.

Die vollständige Liste mit den genauen Fragen steht an einer Stelle: `pfade/e-commerce/ABLAUF.md`, Phase 1.

## Kosten

Grobe Größenordnung, Skael-Preise vom 08.10.2026 (1.000 Credits = 1 €):

- **Stufe 1:** ~1 Cent je Shop.
  - Website-Abruf 2–5 Credits
  - Traffic 7 Credits, nur wenn SimilarWeb Daten hat
  - Shop-Prüfung und Shop-Profil-Prüfung je Bruchteile eines Cents
- **Stufe 2:** ~2–4 Cent je übergebenem Shop.
  - Impressum 5–10 Credits
  - Mailfinder bis 15 Credits
  - E-Mail-Prüfung 3 Credits je Adresse
- **Website-Suche** für Zeilen ohne Website: ~3–10 Credits zusätzlich.
- **Beispiel:** 5.000 Shops, davon 2.000 übergeben, ergeben etwa 50 € Stufe 1 + 40–80 € Stufe 2.

Einzelposten: `pfade/e-commerce/docs/01_PROZESS.md`, Abschnitt „Kosten“.

## Was realistisch herauskommt

Noch nicht gemessen. Nach dem ersten echten Lauf hier eintragen:

| Kennzahl | gemessen |
|---|---|
| aktive Onlineshops unter den Kandidaten | – |
| davon passend zum Shop-Profil | – |
| davon mit SimilarWeb-Traffic (übergeben) | – |
| Impressum mit Geschäftsführung | – |
| mit E-Mail (GF / info@) | – |
| Ready to Send | – |
| Fehlerquote Stichprobe (5–10 Leads von Hand) | – |

## Ausgabe

Wie Google Maps, aber in vier Listen:

1. Geschäftsführer-Adresse
2. info@
3. Aussortiert, mit Grund (z. B. „passt nicht zum Shop-Profil“)
4. Gesperrt (Community-Sperrliste)

Liste 1 und 2 enthalten die fertige Mail je Lead, wenn ein Mailtext hinterlegt ist.

Dazu kommt ein JSON-Archiv mit allen Rohdaten. Details: `07_lead-ausgabe-und-spalten.md`.

## Grenzen

- **Kleine Shops ohne SimilarWeb-Daten** fallen mit den Standard-Schwellen raus. So war es auch in Clay. Wer sie behalten will, setzt beide Schwellen auf 0.
- **Startseite ohne Text:** Manche Shops bauen die Startseite nur per JavaScript auf und liefern dann keinen Text. Sie werden nicht geprüft und stehen mit Grund in Liste 3.
- **Shop-Profil sieht nur die Startseite:** Merkmale, die nur auf Unterseiten stehen, kann es nicht prüfen. Im Zweifel sortiert es eher aus.
- **Erster Geschäftsführer:** Nur der erste Geschäftsführer aus dem Impressum wird verwendet.
- **Kein Shopsystem-Filter:** Der Pfad erkennt heute nicht, ob ein Shop auf Shopware, Shopify & Co. läuft, auch nicht über das Shop-Profil. Wer nur ein System will, braucht eine Liste mit Shopsystem-Spalte; die KI filtert sie vor dem Import. Geplant über den Shop-Katalog (Abschnitt oben).
- **Kein Sitzland-Filter:** Der Pfad prüft nicht, ob die Firma laut Impressum in den gewünschten Ländern sitzt (Interviewfrage D1). Das Shop-Profil prüft nur, was auf der Startseite steht (Sprache, Währung, Lieferländer). Ausländische Shops mit deutscher Seite verbrauchen deshalb weiter Credits und landen im Export. Clay filterte das auch nicht. Geplant als Schritt nach dem Impressum (`shop-katalog.md`, „Einbau“).
- **Kein Telefon, kein LinkedIn:** Telefon-Wasserfall und LinkedIn-Suche waren im Clay-Workbook abgeschaltet und sind nicht nachgebaut.

## Rechtliches

- **Datenquellen:**
  - Startseite, Impressum und SimilarWeb-Daten werden über Skael abgefragt. Es gelten dessen Nutzungsbedingungen.
  - Stammt die Shop-Liste aus einem bezahlten Verzeichnis, gelten dessen Lizenzbedingungen. Viele verbieten die Weitergabe der Daten an Dritte (`pfade/e-commerce/referenzen/discovery-quellen.md`, Abschnitt „Lizenzen“).
- **Personenbezogene Daten:**
  - Namen und persönliche E-Mail-Adressen der Geschäftsführung sind personenbezogen.
  - Informationspflicht nach Art. 14 DSGVO beim Erstkontakt.
- **Kaltakquise per E-Mail** ist ohne Einwilligung grundsätzlich unzulässig (§ 7 Abs. 2 Nr. 2 UWG). In Österreich gilt eine Impressum-Adresse ausdrücklich nicht als Einwilligung.
- **Sperrliste:** Der Abgleich ist eingebaut. Ohne ladbare Liste wird nicht exportiert.

Mehr in `08_versand-und-recht.md`.

## Offene Punkte

1. **Erster echter Lauf:** z. B. 20–50 Shops. Quoten oben eintragen, danach den Status in `02_zielgruppen-interview.md` auf „verfügbar“ setzen. Zurückgestellt, bis die Shop-Suche ohne Liste steht (Punkt 2).
2. **Shops ohne Liste finden** (Wunsch des Betreibers, 2026-10-08): Methode gewählt (Shop-Katalog, Abschnitt oben). Offene Entscheidungen in `shop-katalog.md`, Abschnitt 8.
3. **Shop-Profil und Mailtext im ersten echten Lauf prüfen** (neu seit 2026-10-09): Wie viele aktive Shops sortiert das Profil aus, stimmen die Gründe (Stichprobe)? Wiederholt der persönliche Satz den Mailtext, oder passt er? Quote oben eintragen.

Entschieden: Übergabe an Stufe 2 nur bei `SEND = true` (vom Betreiber bestätigt am 2026-10-08).
