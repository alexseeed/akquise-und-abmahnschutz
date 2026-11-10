# Wissensbibliothek – komplett in einer Datei

Automatisch erzeugt aus `lead-scraper/wissen/` (einrichten.py). Für KI-Modelle, die nur eine Datei aufnehmen. Nicht von Hand bearbeiten.


---

<!-- Datei: wissen/00_INDEX.md -->

# Wissensbibliothek – Lead-Scraper und Abmahnschutz

Alles Fachwissen zum Paket als Markdown, unabhängig vom KI-Modell. Jede Datei steht für sich und nennt am Anfang Zweck, Zielgruppe und verwandte Dateien.

## Mit deinem KI-Modell nutzen

| Modell / Werkzeug | So geht's |
|---|---|
| **Claude (Skill)** | Skill `lead-scraper` hochladen – die Bibliothek ist enthalten, Claude liest sie selbst |
| **Claude Code** | Ordner `lead-scraper/` öffnen – `CLAUDE.md` verweist hierher |
| **ChatGPT Codex** | Ordner `lead-scraper/` öffnen – `AGENTS.md` verweist hierher; Netzwerkzugriff erlauben |
| **Claude-Projekt, ChatGPT (Custom GPT / Projekt), Gemini (Gem), NotebookLM** | den Ordner `wissen/` als Projektwissen hochladen – oder die Datei `WISSEN_KOMPLETT.md` aus dem Paketordner, wenn nur eine Datei geht |

Start-Prompt für andere Modelle:

> Du begleitest mich beim Aufbau von B2B-Leadlisten mit dem „Lead-Scraper“. Dein Wissen steht in den hochgeladenen Markdown-Dateien. Beginne mit dem Zielgruppen-Interview aus `02_zielgruppen-interview.md`: eine Frage pro Nachricht, immer mit Beispiel. Beantworte Rückfragen nur aus diesen Dateien. Wenn dort etwas nicht steht, sag das, statt zu raten. Rechtliche Themen sind keine Rechtsberatung.

## Inhalt

| Datei | Worum es geht | Lesen, wenn … |
|---|---|---|
| `01_ueberblick.md` | Gesamtablauf, Pfade, wer was macht | du neu bist |
| `02_zielgruppen-interview.md` | Fragen vor jedem Lauf, Wahl des Pfads, Auftragsdatei | ein neuer Auftrag beginnt |
| `03_pfad-google-maps.md` | Firmen mit Standort: Stufen, Kosten, Prüfprofil, Quoten | der Pfad Google Maps gewählt ist |
| `04_pfad-amazon.md` | Amazon-Seller: Ablauf, Filter, Kosten, Quoten, Grenzen, Risiken | Händler auf amazon.de gesucht sind oder eine eigene Firmenliste angereichert werden soll |
| `05_pfad-recruiting.md` | Recruiting über die Firmen-Website: Firmen aus Google Maps, offene Stelle auf der eigenen Website erkennen, Opener zur Stelle; Kosten, Grenzen, Recht | Firmen gesucht sind, die gerade einstellen, und die Branche bekannt ist |
| `06_pfad-e-commerce.md` | Onlineshops: erst Anforderungen klären, dann Shop-Liste prüfen (aktiver Shop, passt zum Shop-Profil, Traffic), anreichern und je Lead die fertige Mail ausgeben; Kosten, Grenzen, Recht | eine Liste von Onlineshops vorliegt |
| `07_lead-ausgabe-und-spalten.md` | Ausgabedateien, Spalten, Ansprache-Regeln, Standardformat | die Liste in ein Versandtool soll |
| `08_versand-und-recht.md` | UWG, DSGVO, Pflichtangaben, Quellen-Nutzungsbedingungen | vor dem ersten Versand |
| `09_sperrliste.md` | Community-Sperrliste: Abgleich, Melden, Widerspruch | Fragen zur Sperrliste |
| `10_abmahnung-was-tun.md` | erste Schritte nach einer Abmahnung | eine Abmahnung ist da |
| `11_zugaenge-und-kosten.md` | Konten, Schlüssel, Kostenhebel | vor der Einrichtung, vor großen Läufen |
| `12_fehlerbehebung-faq.md` | typische Probleme und Antworten | etwas klemmt |
| `13_glossar.md` | Begriffe von A bis Z | ein Wort unklar ist |
| `14_neuen-pfad-anlegen.md` | wie weitere Pfade dazukommen | ein Pfad gebaut wird |
| `15_learnings-architekturbueros-2026-10.md` | gemessene Kosten je Schritt, Kostenfallen, Prompt- und Mengen-Learnings aus einem echten Lauf | ein Lauf geplant oder kalkuliert wird |
| `16_videoseiten.md` | persönliches Video je Lead, eigene Landingpage im Branding des Nutzers, Server, Kosten, Recht | Video-Outreach geplant ist oder der Nutzer nach Seiten, Videos oder Server fragt |
| `17_learnings-videoseiten-testlauf-2026-10.md` | Fehler und Regeln aus dem ersten echten Videoseiten-Lauf: Skael-Eigenheiten, Player-Start, Texte im Datenschutz-Block, Prüfen der Seite | Videoseiten zum ersten Mal für einen Nutzer gebaut werden |
| `18_pfad-stellensuche.md` | Recruiting über Jobportale: konkrete Anzeigen per Suchbegriff aus Indeed, Stepstone, Arbeitsagentur, Kununu, Größen-Check, Stellenliste und Firmen, optional Kontakt und Opener; gemessene Quoten, Grenzen, Recht | Firmen gesucht sind, die einen bestimmten Beruf suchen |

## Pflege

- Neues Wissen aus Läufen hier eintragen, nicht nur im Chat: Fundquoten, Fehlermuster, Kosten.
- Jede Datei beginnt mit **Zweck / Für wen / Verwandt**.
- Jede Tatsache steht an einer Stelle; andere Dateien verweisen darauf.
- Fakten, die sich ändern können (Preise, Rechtslage, Quoten, Versionen), stehen unter `**Stand:** JJJJ-MM-TT · **Prüfen bis:** JJJJ-MM-TT`. Ist die Frist abgelaufen, gilt die Angabe als ungeprüft. Die KI sagt das dem Nutzer, statt die Zahl als sicher auszugeben.
- Technische Details zu einem Pfad stehen in `pfade/<pfad>/referenzen/`. Hier steht nur, was Nutzer und KI für Entscheidungen brauchen.
- Prüfen: `python3 werkzeuge/wissen_pruefen.py` (abgelaufene Fristen, fehlende Index-Einträge, tote Verweise, veraltete `WISSEN_KOMPLETT.md`).
- Änderungen mit Datum in `CHANGELOG.md` festhalten.
- Rechtsstand dieser Bibliothek: **Oktober 2026**. Rechtliche Aussagen vor Verwendung prüfen.


---

<!-- Datei: wissen/01_ueberblick.md -->

# Überblick – vom Wunschkunden zur versandfertigen Liste

**Zweck:** das große Bild – welche Teile es gibt, wie sie zusammenspielen und wer was tut.
**Für wen:** alle, die neu einsteigen, und KI-Modelle, die Rückfragen beantworten.
**Verwandt:** `02_zielgruppen-interview.md` · `09_sperrliste.md` · `10_abmahnung-was-tun.md`

---

## Der Kreislauf

```
 1 Interview        2 Pfad              3 Abgleich           4 Versand          5 Abmahnung?
 Wen willst du? ──► Google Maps    ──►  Community-      ──►  dein Versand- ──►  Skill abmahnung-
 Wo findet man      Amazon-Seller       Sperrliste           tool                werbemail-abwehr
 sie?               E-Commerce          (Abmahner raus)                               │
                    Recruiting                 ▲                                      │
                    Stellensuche               └────── 6 Abmahner wird gemeldet ◄─────┘
```

Je mehr Unternehmen mitmachen, desto vollständiger wird die Sperrliste. Bedingung der Nutzung ist deshalb: Wer abgemahnt wird, meldet den Abmahner (`NUTZUNGSBEDINGUNGEN.md`).

## Die Teile

| Teil | Was er tut | Wo |
|---|---|---|
| **Lead-Scraper** (Claude-Skill + Projekt) | Interview, Pfadwahl, Durchführung, Abgleich | `lead-scraper/` |
| Pfad **Google Maps** | Firmen mit Standort finden, gegen Wunschkundenprofil prüfen, Impressum, Geschäftsführung, E-Mail, Anrede, Personalisierung | `lead-scraper/pfade/google-maps/` |
| Pfad **Amazon-Seller** | findet Drittanbieter auf amazon.de selbst: Firma, Land, Sortiment, Umsatz, Kontaktdaten, Website, Geschäftsführung, Anrede | `lead-scraper/pfade/amazon/` |
| Pfad **E-Commerce** | Shop-Liste → aktiver Onlineshop? Besucher? → Impressum, Geschäftsführung, E-Mail, Anrede, Personalisierung (Nachbau des Clay-Workbooks ECOM 2.0) | `lead-scraper/pfade/e-commerce/` |
| Pfad **Recruiting** (Firmen-Website) | Firmen, die gerade einstellen: Google Maps → Prüfprofil → offene Stelle auf der Firmen-Website erkennen → Geschäftsführung, E-Mail, Opener mit Bezug zur Stelle | Anleitung `lead-scraper/pfade/recruiting/`, läuft im Scraper-Programm `pfade/google-maps/` |
| Pfad **Stellensuche** (Jobportale) | Suchbegriff → Stellenanzeigen aus Indeed, Stepstone, Arbeitsagentur, Kununu → je Firma gebündelt → Größen-Check → wahlweise Website per Impressum-Beleg, Geschäftsführung, E-Mail, Opener zur Stelle | Anleitung `lead-scraper/pfade/stellensuche/`, läuft im Scraper-Programm `pfade/google-maps/` |
| **Sperrlisten-Abgleich** | sortiert Firmen aus, deren Domain nach einer Abmahnung gemeldet wurde | Google Maps, Recruiting, Stellensuche: beim Export; sonst `werkzeuge/sperrliste_abgleich.py` |
| **Abmahnungs-Abwehr** (Claude-Skill) | Abmahnung prüfen, Antwort und Unterlassungserklärung, Website-Sicherung, Meldung an die Sperrliste | `abmahnung-werbemail-abwehr/` |
| **Sperrliste** (GitHub) | öffentliche Liste, ergänzt sich selbst | Repository `werbemail-sperrliste` |

## Wer macht was

| Rolle | Aufgabe |
|---|---|
| **Nutzer** | beantwortet das Interview, gibt Kosten frei, prüft Stichproben, versendet |
| **KI (Claude o. a.)** | fragt, wählt den Pfad, führt Befehle aus, übersetzt Ergebnisse, nennt Grenzen |
| **Dienste** | Skael (Google Maps, Impressum, Geschäftsführung, E-Mail-Suche), OpenAI (Bewertungen, Texte), Oxylabs (Amazon-Seiten), Bright Data (Kontaktdaten der Amazon-Verkäufer) |
| **Betreiber** | betreibt Sperrliste und Relay, bearbeitet Widersprüche |

## Grundsätze

1. **Erst fragen, dann zahlen.** Interview und Testlauf kommen vor jedem großen Lauf.
2. **Lieber neutral als falsch.** Unsichere Namen oder Geschlechter bekommen „Guten Tag“ statt einer falschen persönlichen Anrede.
3. **Ehrliche Zahlen.** Fund- und Fehlerquoten werden genannt, nicht geschönt.
4. **Gesperrt heißt gesperrt.** Firmen auf der Sperrliste werden nie angeschrieben, über keinen Kanal.
5. **Kein Ersatz für Rechtsberatung.** Kaltakquise per E-Mail bleibt rechtlich riskant (`08_versand-und-recht.md`).


---

<!-- Datei: wissen/02_zielgruppen-interview.md -->

# Zielgruppen-Interview und Wahl des Pfads

**Zweck:** Bevor auch nur ein Euro für Abfragen ausgegeben wird, klärt das Interview, *wen* der Nutzer erreichen will und *wo* man diese Firmen findet. Aus den Antworten folgt der Pfad (Google Maps, Amazon, E-Commerce, Recruiting über die Firmen-Website oder über Jobportale) und fast alle Einstellungen des Laufs.
**Für wen:** die KI, die den Nutzer begleitet (Claude, ChatGPT, Gemini …), und Menschen, die verstehen wollen, warum gefragt wird.
**Verwandt:** `01_ueberblick.md` · `03_pfad-google-maps.md` · `04_pfad-amazon.md` · `07_lead-ausgabe-und-spalten.md`

---

## Regeln für das Gespräch

- **Eine Frage pro Nachricht**, immer mit einem Beispiel, an dem sich der Nutzer orientieren kann.
- **Keine Fachbegriffe** ohne Halbsatz-Erklärung. Nicht erwähnen: ICP, Prompt, Confidence, Tier, TLD, Stage, API, `.env`.
- **Schon Gesagtes nicht erneut fragen.** Steht die Antwort in der ersten Nachricht oder in einer vorhandenen Auftragsdatei, überspringen.
- **Weiß der Nutzer etwas nicht:** einen Vorschlag machen und bestätigen lassen, nicht nachbohren.
- Nach jedem Block **in eigenen Worten zusammenfassen** und bestätigen lassen.
- Ziel: ca. 10 kurze Fragen, dann eine klare Empfehlung. Nicht mehr fragen als nötig. Mit Video kommen höchstens 9 weitere dazu (Blöcke V und L).

---

## Block A – Angebot und Kanal

| # | Frage an den Nutzer | Beispiel dazusagen | Wofür |
|---|---|---|---|
| A1 | „Was bietest du an – in einem Satz?“ | „Zum Beispiel: Wir bauen Vertriebssysteme für Großhändler.“ | Prüfprofil, Personalisierung |
| A2 | „Wie willst du die Firmen ansprechen?“ | „Per E-Mail, Telefon, Brief, LinkedIn oder mit einem persönlichen Video?“ | Rechtlicher Hinweis, Videotitel ja/nein |

## Block B – Wer ist der Wunschkunde?

| # | Frage | Beispiel | Wofür |
|---|---|---|---|
| B1 | „Was für Firmen sind deine Wunschkunden?“ | „Zum Beispiel Zahnarztpraxen, Metallbaubetriebe oder Marken, die auf Amazon verkaufen.“ | Branche, Suchbegriffe |
| B2 | „Beschreib mir einen typischen Wunschkunden in ein, zwei Sätzen.“ | „Ein Familienbetrieb mit eigener Werkstatt und 10 bis 50 Leuten.“ | Prüfprofil |
| B3 | „Kennst du ein, zwei Firmen, die perfekt passen würden?“ | „Name oder Website genügt.“ | Kalibrierung, Pfad-Erkennung |

## Block C – Wo findet man diese Firmen? (entscheidet den Pfad)

| # | Frage | Beispiel |
|---|---|---|
| C1 | „Wo sind diese Firmen am leichtesten zu finden?“ | Antwortmöglichkeiten unten vorlesen |
| C2 | „Hast du schon eine Liste, die nur ergänzt werden soll?“ | „Zum Beispiel ein Export aus einem Analyse-Tool als Excel oder CSV.“ |

Antwortmöglichkeiten für C1:

1. **Sie haben einen Standort und stehen bei Google Maps.** Beispiele: Handwerk, Praxen, Kanzleien, Händler, Dienstleister vor Ort.
2. **Sie verkaufen über Amazon**, als Händler oder mit eigener Marke.
3. **Sie haben einen eigenen Onlineshop** (Shopify, Shopware, WooCommerce …).
4. **Sie suchen gerade Personal** und schalten Stellenanzeigen.
   Nachfrage, wenn ja: „Kennst du den Beruf, den sie suchen – zum Beispiel Berufskraftfahrer –, oder eher die Branche der Firmen?“ Beruf bekannt → Stellensuche (Jobportale); nur Branche → Recruiting (Firmen-Website).
5. **Weiß ich nicht.** Dann schlägt die KI anhand von B1–B3 einen Weg vor.

## Block D – Rahmen (gilt für alle Pfade)

| # | Frage | Beispiel | Wofür |
|---|---|---|---|
| D1 | „In welchen Ländern sollen die Firmen sitzen?“ | „Nur Deutschland, oder auch Österreich und Schweiz?“ | Suchgebiet |
| D2 | „Gibt es Firmen, die du sicher nicht willst?“ | „Große Ketten, Konzerne, reine Onlineshops, Franchise.“ | Ausschlüsse |
| D3 | „Brauchst du die Geschäftsführung persönlich, oder reicht info@…?“ | „Ich sammle beides – du entscheidest, was in die Liste kommt.“ | Exportfilter |
| D4 | „Wie viele Firmen brauchst du ungefähr, und was darf es kosten?“ | „200 gute Kontakte für einen Test, oder ganz Deutschland?“ | Umfang, Kosten |


## Block V – Persönliches Video (nur wenn A2 „Video“ enthält)

Nach dem Scrape bekommt jeder Lead ein eigenes Video und eine eigene Seite (`16_videoseiten.md`). Hier nur klären, was sich nicht ablesen lässt.

| # | Frage | Beispiel | Wofür |
|---|---|---|---|
| V1 | „Hast du in Skael schon ein Video für diese Zielgruppe aufgenommen?“ | „Wenn nicht, zeige ich dir nach der Leadsuche Schritt für Schritt, wie das geht.“ | Kampagne, Anleitung `pfade/videoseiten/anleitungen/01_…` |
| V2 | „Jedes Video kostet bei bis zu 2 Minuten Länge 11 Cent. Ist das für alle Leads in Ordnung?“ | „Bei 500 Leads sind das 55 €.“ | Budget, Videolänge |

## Block L – Eigene Landingpage (nur wenn A2 „Video“ enthält)

Farben, Schriften, Logo, Impressum und Datenschutz liest der Agent später selbst von der Website ab und lässt sie nur bestätigen.

| # | Frage | Beispiel | Wofür |
|---|---|---|---|
| L1 | „Wie lautet die Adresse deiner Website?“ | „Zum Beispiel www.muster-agentur.de.“ | Branding, Impressum, Texte |
| L2 | „Wo hast du diese Domain gekauft?“ | „Zum Beispiel bei IONOS, STRATO, Hostinger oder GoDaddy. Weißt du es nicht, finde ich es heraus.“ | DNS-Anleitung, Seiten-Domain `angebot.<domain>` |
| L3 | „Wer soll auf der Seite als Ansprechpartner stehen?“ | „Meist du selbst, mit Foto und Rolle.“ | Unterschrift, Baustein Ansprechpartner |
| L4 | „Wie bucht man einen Termin bei dir?“ | „Zum Beispiel ein Calendly-Link, und wie lange der Termin dauert.“ | Termin-Knopf; ohne Tool `anleitungen/04_buchungstool.md` |
| L5 | „Hast du Kundenstimmen, die du zeigen darfst – als Text oder Video?“ | „Nur mit Zustimmung der Kunden.“ | Baustein Kundenstimmen |
| L6 | „Duzt oder siezt du deine Kunden?“ | „Die ganze Seite richtet sich danach.“ | Ansprache |
| L7 | „Mit welchem Programm verschickst du deine Mails?“ | „Zum Beispiel Instantly, lemlist, Brevo oder Outlook.“ | Versandliste, `anleitungen/06_mailtool.md` |

Der Server (Hostinger) wird erst nach der Leadsuche eingerichtet, nicht im Interview.

---

## Entscheidung: welcher Pfad?

| Signal aus dem Interview | Pfad | Status |
|---|---|---|
| C1 = 1, oder die Branche ist ortsgebunden (Praxis, Handwerk, Kanzlei, Händler mit Laden/Lager) | **Google Maps** → `03_pfad-google-maps.md` | verfügbar |
| C1 = 2: Händler oder Marken, die auf Amazon verkaufen | **Amazon-Seller** → `04_pfad-amazon.md` | verfügbar (nur amazon.de; findet die Verkäufer selbst, keine Liste nötig) |
| C1 = 3: eigener Onlineshop **und** eine Shop-Liste liegt vor (C2) | **E-Commerce** → `06_pfad-e-commerce.md` | verfügbar (Beta, erster echter Testlauf steht aus) |
| C1 = 3 ohne Shop-Liste | Google Maps (Shops mit Laden/Lager) oder Amazon; Quellen für Shop-Listen: `pfade/e-commerce/referenzen/discovery-quellen.md` | – |
| C1 = 4: Firmen, die gerade einstellen, **Beruf bekannt** (z. B. „alle, die Berufskraftfahrer suchen“) | **Stellensuche** (Jobportale) → `18_pfad-stellensuche.md` | verfügbar (Indeed, Stepstone, Arbeitsagentur, Kununu über Skael) |
| C1 = 4: Firmen, die gerade einstellen, **Branche bekannt** (z. B. „Speditionen in Ulm, die einstellen“) | **Recruiting** (Firmen-Website) → `05_pfad-recruiting.md` | verfügbar (Google Maps + Stellen-Erkennung auf der Firmen-Website) |
| C2 = eigene Firmenliste mit Firmenname | **Sonderfall:** Anreicherung aus dem Amazon-Pfad (`pfade/amazon/ABLAUF.md`, „Sonderfall“). Website, Geschäftsführung und Anrede funktionieren für jede Firmenliste mit Firmen aus DE/AT/CH. | verfügbar |

**Mehrere Signale:** den Pfad mit der größten erwarteten Trefferzahl zuerst nehmen, den zweiten danach. Doppelte Firmen fallen spätestens beim Abgleich der Domains auf.

**Beide Recruiting-Wege ergänzen sich:** Kleine Betriebe schreiben oft nur auf der eigenen Website aus, größere fast immer über Portale. Unterschiede: `18_pfad-stellensuche.md`, Abschnitt „Unterschied zum Pfad Recruiting“.

**Weg unklar? Testballon anbieten.** Sind Beruf und Branche bekannt, kann der Testballon beide Wege mit je rund 100 Leads fahren. Das Budget ist je Weg gedeckelt, Standard 20 €. Danach entscheidet der Nutzer anhand des Vergleichsberichts: Kosten je Lead, Qualität, Marktgröße und Überschneidung. Gibt es zu wenige Stellen, erweitert der Testballon die Suche selbst in Stufen (Fallback-Leiter) und sagt am Ende offen, wie viel der Markt hergibt. Kosten vorher nennen und bestätigen lassen. Befehl und Ablauf: `pfade/google-maps/docs/09_TESTBALLON.md`.

**E-Commerce ohne Shop-Liste:** offen sagen, dass der Pfad keine Shops findet. Die beste verfügbare Alternative anbieten:

- Onlineshops mit Lager oder Laden stehen oft auch bei Google Maps.
- Shops, die zusätzlich auf Amazon verkaufen, findet der Amazon-Pfad.

Die Antworten trotzdem in der Auftragsdatei sichern.

**Grenzfälle:**

- **Großhändler und Hersteller mit Eigenvertrieb:** meist Google Maps, weil sie einen Standort haben. Wenn sie stark auf Amazon sind, zusätzlich den Amazon-Pfad.
- **Dienstleister ohne Laufkundschaft (Agenturen, Beratungen):** Google Maps funktioniert. Das Prüfprofil muss dann streng sein, weil viele Einträge Einzelpersonen sind.

---

## Zusammenfassung und Auftragsdatei

Nach dem Interview dem Nutzer in vier bis sechs Sätzen sagen:

- wen du suchst und wen nicht,
- welcher Pfad und warum,
- welches Gebiet, welche Menge und welche Kosten-Größenordnung,
- welche Ansprechpartner,
- was als Nächstes passiert: Testlauf, erst danach der große Lauf.

Bestätigung abwarten. Dann alles als **Auftragsdatei** speichern, z. B. `auftraege/2026-10-04_metallbau-dach.md`:

```markdown
# Auftrag: Metallbau DACH
Pfad: google-maps
Angebot (A1): …
Kanal (A2): E-Mail mit Video
Wunschkunde (B1–B3): …
Beispielfirmen: …
Fundort/Liste (C1/C2): Standort bei Google Maps | eigene Liste: <Datei oder „wird nachgereicht“>
Länder (D1): DE, AT, CH
Ausschlüsse (D2): Konzerne, Ketten
Ansprechpartner (D3): Geschäftsführung, info@ als Reserve
Menge/Budget (D4): ca. 500 Kontakte, Testlauf zuerst
Video (V1–V2): Skael-Kampagne „…“ / noch aufnehmen; Kosten bestätigt
Landingpage (L1–L7): www.…, Domain bei …, Ansprechpartner …, Termin …, Stimmen …, Sie/du, Mailtool …
Offene Punkte: –
```

Der Pfad liest diese Datei und fragt nur, was dort noch fehlt. Die Datei bleibt beim Nutzer und dient später als Nachweis, wie die Zielgruppe bestimmt wurde.

Bei Recruiting und Stellensuche zusätzlich: `Kampagne:` (Name unter `pfade/google-maps/kampagnen/`, z. B. `spedition-ulm`) und `Prompt-Anpassungen:` (welche Prompts in die Kampagne kopiert und geändert wurden). Ihre Zusatzfragen stehen in `pfade/recruiting/ABLAUF.md` (R1–R4) bzw. `pfade/stellensuche/ABLAUF.md` (S1–S4) und werden erst nach der Pfadwahl gestellt.

Der E-Commerce-Pfad stellt danach eigene Rückfragen (Shop-Liste, Shopsystem, Mindestgröße, Shop-Profil, Mailtext) und startet erst, wenn alles beantwortet ist: `pfade/e-commerce/ABLAUF.md`, Phase 1.

---

## Übersetzung der Antworten in Einstellungen

| Antwort | Google Maps | Amazon | E-Commerce |
|---|---|---|---|
| A1 Angebot | Prüfprofil (Zielgruppen-Prüfung), Personalisierung | Ansprache-Text (außerhalb der Pipeline) | Shop-Profil, Personalisierung, Mailtext |
| A2 Kanal, Video ja/nein | `DO_VIDEO_TITLE`, `DO_PERSONALISIERUNG`; bei Video nach dem Export Pfad `pfade/videoseiten/` (Export mit `--lead-format`) | Kanal E-Mail: Skael-Schlüssel ist Pflicht, sonst bleiben alle Adressen ungeprüft (`Not Run`). Personalisierung und Videotitel gibt es hier nicht | `DO_VIDEO_TITLE`, `DO_PERSONALISIERUNG` |
| B1 Branche | Suchbegriffe (eng zuerst, dann breiter) | `KATEGORIEN` (Produktbereiche) bzw. `KEYWORDS`; ohne Angabe alle 28 Kategorien | Filter beim Erstellen der Shop-Liste, Shop-Profil |
| B2/B3 Beschreibung, Beispiele | Prüfprofil, Testlauf-Kontrolle | Größe: `MAX_PRODUKTE`, `PORTFOLIO_MAX_BEWERTUNGEN` (nach Umsatz wird nicht gefiltert, er steht als Spalte in der Liste); eigene Marke: `MIN_MARKENANTEIL`; Kontrolle im Testlauf | Shop-Profil, Testlauf-Kontrolle |
| D1 Länder | `--countries`, ggf. `EXCLUDED_TLDS` leeren (FR/NL/IT) | `LAENDER` = Sitz des Verkäufers (Marktplatz immer amazon.de) | Shop-Profil (Sprache, Währung, Lieferländer), Zeilen vorab filtern |
| D2 Ausschlüsse | Prüfprofil „sofort raus“, `KETTEN_EXTRA` | `FIRMEN_AUSSCHLUSS`, Größenfilter, Kategorien weglassen | Shop-Profil „sofort raus“, Zeilen vorab filtern |
| D3 Ansprechpartner | Exportliste 1 (GF) und/oder 2 (info@) | Bright Data (E-Mail, Telefon) und Skael (E-Mail-Prüfung für alle Länder; Website und Geschäftsführung nur DACH) | Exportliste 1 (GF) und/oder 2 (info@) |
| D4 Menge/Budget | `--min-population`, Anzahl Suchbegriffe | `ZIEL` (Leads) und `BUDGET` (≈ 30 × ZIEL ohne Filter, mit Länderfilter deutlich mehr) | Zeilenzahl, Testlauf-Größe; Mindestgröße → E3 in `pfade/e-commerce/ABLAUF.md` (beide Traffic-Schwellen) |

### Recruiting und Stellensuche

| Antwort | Recruiting (Firmen-Website) | Stellensuche (Jobportale) |
|---|---|---|
| A1 Angebot | Prüfprofil; Opener bleibt stellenbezogen | optionales Prüfprofil; Opener stellenbezogen |
| A2 Kanal, Video ja/nein | kein Videotitel | kein Videotitel |
| B1 Branche bzw. Beruf | `--keywords` (Branche), `--berufe` (gesuchte Berufe) | `--suche` (Berufe), optional Prüfprofil |
| B2/B3 Beschreibung, Beispiele | Prüfprofil (`icp.txt` der Kampagne), Stichprobe | Stichprobe, optional Prüfprofil |
| D1 Länder | `--countries`; Prompts sind deutschsprachig | `--land`, `--orte` bzw. `--min-population`, `--umkreis` |
| D2 Ausschlüsse | Prüfprofil „sofort raus“, Stellen-Prompt „nicht zählen“ | Zeitarbeit und Personalvermittler immer raus; Größen-Check (Konzerne, öffentliche Hand, IT-Wettbewerber); `--titel-ausschluss`, `PERSONALDIENSTLEISTER_EXTRA` |
| D3 Ansprechpartner | Geschäftsführung aus dem Impressum, info@ als Reserve | wie Recruiting; „nur Stellenliste“ ganz ohne Kontakt |
| D4 Menge/Budget | `--min-population`, Anzahl Suchbegriffe, `--nk` | Orte × Suchbegriffe, `--max-seiten`, `--max-alter`, `--nur-stellen` |


---

<!-- Datei: wissen/03_pfad-google-maps.md -->

# Pfad „Google Maps“ – Firmen mit Standort

**Zweck:** was der Pfad tut, was er kostet, was herauskommt und wo seine Grenzen liegen.
**Für wen:** Nutzer und KI-Modelle, die einen Lauf planen oder Ergebnisse verstehen wollen.
**Verwandt:** `02_zielgruppen-interview.md` · `07_lead-ausgabe-und-spalten.md` · `11_zugaenge-und-kosten.md`
**Technik im Detail:**

- Bedienung: `pfade/google-maps/docs/00_ANLEITUNG.md`
- jede Formel: `pfade/google-maps/docs/01_PROZESS.md`
- API: `pfade/google-maps/docs/03_SKAEL_API_REFERENZ.md`

---

## Wann dieser Pfad

Für alles, was bei Google Maps steht: Handwerk, Praxen, Kanzleien, Händler, Großhändler und Hersteller mit Standort, lokale Dienstleister. Nicht geeignet für reine Onlinefirmen ohne Adresse, für Amazon-Marken und für Firmen, die nur über Stellenanzeigen auffallen.

## Ablauf in vier Stufen

```
Suchbegriff + Land ─► 1 Städte ─► 2 Google-Maps-Suche ─► 3 Dedupe + Prüfung ─► 4 Anreicherung ─► Export
```

| Stufe | Was passiert | Dienst |
|---|---|---|
| **1 Städte** | alle Orte je Land ab einer Mindestgröße | Skael `find_cities` |
| **2 Maps** | je Suchbegriff × Ort eine Google-Maps-Suche | Skael `maps_search` |
| **3a–3d** | fehlende Websites per KI, doppelte Firmen über die Domain entfernen, Website gegen das **Prüfprofil** (Wunschkundenprofil) prüfen, Treffer weitergeben | OpenAI, Skael `icp_checker` |
| **4a–4h** | Website, Impressum (Firmenname, Geschäftsführung, Adresse, Telefon, E-Mail), E-Mail der Geschäftsführung suchen und prüfen, Anrede, Personalisierung, Videotitel, optional LinkedIn, Versandfreigabe | Skael, OpenAI, optional Findymail |
| **Export** | fünf CSV-Listen, vorher Abgleich mit der Sperrliste | – |

Läufe sind **fortsetzbar**. Nach einem Abbruch setzt derselbe Befehl dort fort, wo er stehen geblieben ist.

## Das Prüfprofil – der wichtigste Hebel

Jede gefundene Website wird von einer KI gegen ein Prüfprofil bewertet: ja oder nein, mit Sicherheit und Begründung. Ein gutes Profil hat:

- **Prüfreihenfolge:** Region → Branche → Größe. Bei der ersten Verletzung abbrechen.
- **Muss-Kriterien:** Begriffe oder Leistungen, von denen mindestens zwei zutreffen müssen.
- **Sofort raus:** Ketten, Konzerne, Franchise, reine Onlineshops, Vermittler – je nach Zielgruppe.
- **Unsichere Fälle:** Sicherheit 0,40–0,60 und Begründung mit „UNSICHER:“. Diese Fälle landen in Exportliste 3 zur Handprüfung.

Vorlage: `pfade/google-maps/prompts/icp_prompt_builder.md`. Beispiele: `icp_beispiel_metallbau.txt`, `icp_grosshandel.txt`.

**Nach dem Testlauf kalibrieren:**

- Stichprobe ansehen: zwei, drei Treffer und mindestens einen aussortierten Fall.
- Profil schärfen.
- Nur Stufe 3c neu fahren. Das kostet keine neue Google-Maps-Suche.

## Suchbegriffe

Eng anfangen, dann erweitern:

1. Kernbegriffe, z. B. „Metallbau, Schlosserei“
2. Synonyme
3. Breite Begriffe – viele Fehltreffer, die das Prüfprofil abfangen muss

**Jeder Begriff multipliziert die Kosten.** Doppelte Firmen über mehrere Begriffe sind kein Problem; sie fallen beim Dedupe über die Domain raus.

## Kosten – die Faustregel

```
Google-Maps-Suchen = Suchbegriffe × Orte
```

| Setup | Orte | Begriffe | Suchen |
|---|---|---|---|
| DACH, alle Orte | ~10.200 | 3 | ~30.700 |
| DACH, ab 20.000 Einwohnern | ~900 | 3 | ~2.700 |
| nur DE, ab 50.000 Einwohnern | ~190 | 2 | ~380 |

Danach kostet jede gefundene Firma eine Prüfung. Jeder Treffer kostet zusätzlich:

- ein Impressum,
- ein bis zwei E-Mail-Suchen,
- ein bis zwei E-Mail-Prüfungen,
- einen Website-Abruf,
- mehrere kurze KI-Aufrufe.

Größter Hebel: **Mindest-Ortsgröße** (`--min-population`). Zweiter Hebel: Anzahl der Suchbegriffe.

## Was realistisch herauskommt

Größenordnung aus einem realen Lauf mit 3 Begriffen über DACH:

| Schritt | Zahl |
|---|---|
| Maps-Treffer | ~26.500 |
| nach Dedupe | ~18.000 |
| passend zum Prüfprofil | ~6.400 |
| mit E-Mail | ~4.100 |
| versandfertig | ~2.400 |

Die Quoten hängen stark von der Branche und vom Profil ab. Erst der Testlauf sagt, was im konkreten Fall zu erwarten ist.

## Einstellungen, die man kennen muss

| Einstellung | Standard | Wann ändern |
|---|---|---|
| `EXCLUDED_TLDS` | `.fr,.nl,.it` | **leeren**, wenn in Frankreich, den Niederlanden oder Italien gesucht wird – sonst verschwindet die ganze Zielgruppe |
| `CITIES_LIMIT` | 5000 | auf 10000, wenn ganz Deutschland mit allen Orten gesucht wird (~7.600) |
| `DO_PERSONALISIERUNG` / `DO_VIDEO_TITLE` | an | aus, wenn kein Video- oder Personalisierungs-Outreach geplant ist – spart Kosten |
| `SPERRLISTE_URL` / `SPERRLISTE_PFLICHT` | Repository / an | nur der Betreiber ändert die URL; Pflicht nicht abschalten |
| `KETTEN_EXTRA` | leer | zusätzliche Ketten oder Konzerne, die beim Export rausfallen sollen |

**Versandfertig** heißt: E-Mail vorhanden. Personalisierung und Videotitel zählen zusätzlich, wenn die jeweilige Stufe eingeschaltet ist.

## Grenzen

- Nur der **erste** Geschäftsführer aus dem Impressum wird verwendet.
- E-Mail-Status `Risky` (Catch-all) und `Unknown` sind im Export enthalten – vor dem Versand gesondert behandeln.
- Die Skael-API liefert identische Anfragen innerhalb von 20 Minuten aus dem Zwischenspeicher, auch Fehlschläge. Beim Wiederholen beachten.
- Der Prozess ist die Portierung eines Clay-Workbooks; Formeln und Prompts stammen von dort (`pfade/google-maps/docs/05_ABWEICHUNGEN.md`).

## Rechtliches in Kürze

- **Datenquellen:** Google-Maps-Einträge und Impressen werden über einen Drittanbieter abgefragt. Dessen Nutzungsbedingungen und die von Google gelten.
- **Personenbezogene Daten:** Namen der Geschäftsführung und persönliche E-Mail-Adressen sind personenbezogene Daten (DSGVO).
- **Kaltakquise per E-Mail** ist ohne Einwilligung grundsätzlich unzulässig.

Mehr in `08_versand-und-recht.md`.


---

<!-- Datei: wissen/04_pfad-amazon.md -->

# Pfad „Amazon-Seller“ – Händler auf amazon.de finden und zu Kontakten machen

**Zweck:** was der Pfad leistet, was er voraussetzt, was er kostet, welche Quoten realistisch sind und welche Risiken bestehen.
**Für wen:** Nutzer, die Händler und Marken auf Amazon erreichen wollen, und KI-Modelle, die Rückfragen beantworten.
**Verwandt:** `02_zielgruppen-interview.md` · `07_lead-ausgabe-und-spalten.md` · `08_versand-und-recht.md` · `11_zugaenge-und-kosten.md`
**Technik im Detail:** Anleitung für die KI `pfade/amazon/ABLAUF.md` · alle Einstellungen, Dateien und Spalten `pfade/amazon/README.md`
**Stand:** Oktober 2026

---

## Wann dieser Pfad

Für Firmen, die auf **amazon.de** als Drittanbieter verkaufen, mit eigener Marke oder als Händler. Typische Anbieter, die diese Zielgruppe suchen: Amazon-Agenturen, Logistik und Fulfillment, Finanzierung, Software für Händler, Fotografie und Content, Steuer- und Rechtsberatung für Onlinehändler.

Der Pfad **findet die Verkäufer selbst**. Eine Brand-Liste aus einem Analyse-Tool ist nicht nötig.

Sonderfall: Für **jede eigene Firmenliste** mit Firmenname lassen sich mit `anreicherung.mjs` Website, Geschäftsführung und Anrede recherchieren (nur DE/AT/CH, `ABLAUF.md` → „Sonderfall“).

## Voraussetzungen

| Was | Pflicht? | Wofür |
|---|---|---|
| **Node.js ab Version 18** | ja | führt die Skripte aus, sonst nichts zu installieren |
| **Oxylabs-Konto** (Web Scraper API) | ja | ruft alle Amazon-Seiten ab. Kein eigenes Amazon-Konto nötig |
| **Bright Data** (Token) | ja, wenn per E-Mail oder Telefon angesprochen wird | Kontaktdaten der fertigen Leads: E-Mail, Telefon, Handelsregister, USt-IdNr., vertretungsberechtigte Person |
| **Skael** (API-Schlüssel) | ja, wenn per E-Mail angeschrieben wird | prüft die Zustellbarkeit jeder E-Mail-Adresse (alle Länder); dazu Website, Impressum, Geschäftsführung, Anrede (nur Firmen in DE/AT/CH) |

Die Zugänge stehen in `pfade/amazon/.env`, eingetragen vom Nutzer selbst. Die KI prüft sie mit `--pruefen` (eine einzige Testabfrage).

## Ablauf

| Stufe | Was passiert | Kosten-Treiber |
|---|---|---|
| 1 Suche | Neuheiten-Listen von 28 amazon.de-Kategorien (optional Unterkategorien, Suchbegriffe) | 1 Abfrage je Listenseite |
| 2 Produktseite | Welcher Händler hat die Buy-Box? Amazon selbst ist nie ein Lead | 1 Abfrage je Produkt |
| 3 Verkäuferprofil | Firmenname, Adresse, **Land des Firmensitzes** | 1 Abfrage je Verkäufer |
| 4 Sortiment | Produktzahl, 12er-Stichprobe: Produktfamilien, Hauptmarke, Markenanteil, Umsatz | ~5–30 Abfragen je Verkäufer |
| 5 Endkontrolle | Hat der Händler die Buy-Box noch? | 1–2 je Lead |
| 6 Kontaktdaten | Bright Data, nur für fertige Leads | 1 Datensatz je Lead |
| 7 Export | Gesamtliste, Lauf-Datei, Bericht | – |
| 8 Anreicherung | Skael: E-Mail-Prüfung (alle Länder), Website, Impressum, Geschäftsführung, Anrede (DACH) | 3 Credits je Adresse, ~5–50 Credits je DACH-Lead |
| 9 Standardformat + Sperrliste | Pflichtfelder vorn, Abgleich mit der Community-Sperrliste | – |

Die Stufen 1–4 laufen in **Wellen**: Jede Stufe holt nur, was die nächste für das Lead-Ziel braucht, und misst die Durchlaufquoten dabei selbst. Ein Lauf bezahlt also nie zehntausende Produktseiten vor dem ersten Lead. Reicht das Budget nicht, kommen trotzdem die bis dahin gefundenen Leads heraus.

Alle Schritte sind **fortsetzbar**: Nach einem Abbruch setzt derselbe Befehl fort, ohne Bezahltes zu wiederholen. Ein **Gedächtnis** über alle Kampagnen merkt sich geprüfte Produkte und Fakten zu Verkäufern. Was einmal bezahlt wurde, kostet 90 Tage lang nicht noch einmal (`CACHE_TAGE`). In einer neuen Kampagne fallen je bekanntem Verkäufer nur wenige Abfragen an.

## Filter (ab Werk alle aus)

| Wunsch aus dem Interview | Filter |
|---|---|
| nur Firmen mit Sitz in DACH | `LAENDER=DE,AT,CH` |
| keine Konzerne / nur kleine Händler | `PORTFOLIO_MAX_BEWERTUNGEN`, `MAX_PRODUKTE` |
| Umsatz-Obergrenze (nur auf ausdrücklichen Wunsch) | `UMSATZ_MAX` |
| Händler mit eigener Marke | `MIN_MARKENANTEIL=0.7` |
| keine Verlage o. Ä. | `FIRMEN_AUSSCHLUSS=verlag,…` |
| nur bestimmte Produktbereiche | `KATEGORIEN=…` oder `KEYWORDS=…` |

Nach Umsatz wird ab Werk nicht gefiltert und nicht in Klassen eingeteilt. Fast jeder Händler bekommt eine Umsatzzahl. Die Spalte `Umsatzbasis` sagt, ob sie `gemessen`, `gemessen + geschätzt` oder `geschätzt` ist. Ohne Kauf- und Preisdaten bleibt sie leer (`nicht messbar`). Die Auswahl trifft der Nutzer in der fertigen Liste.

Filter wirken auch auf das Gedächtnis. Gespeichert werden Fakten, keine Urteile. Ein Verkäufer, der heute an einem Filter scheitert, kann in einer Kampagne mit anderen Filtern wieder dabei sein.

## Kosten und Mengen

| Kennzahl | Richtwert |
|---|---|
| Oxylabs | ~0,45 USD je 1.000 Abfragen |
| Abfragen je Lead **ohne Filter** | ~15–30, also 0,7–1,4 Cent je Lead |
| Abfragen je Lead mit `LAENDER=DE,AT,CH` | ~150–250, weil nur ~15 % der Verkäufer dort sitzen |
| Bright Data | ~1,50 USD je 1.000 Leads |
| Skael E-Mail-Prüfung | 3 Credits je Adresse, unabhängig vom Ergebnis |
| Skael Website und Geschäftsführung | ~5–50 Credits je DACH-Lead; mit Firmen-E-Mail günstig, ohne teuer |
| Smoke-Test | höchstens 300 Abfragen ≈ 0,15 USD |

**Budget-Regel:** ohne Filter BUDGET ≈ 30 × ZIEL. Nach dem Testlauf gilt der gemessene Wert: BUDGET ≈ ZIEL × `requests_je_lead` × 1,2. `BUDGET` ist eine harte Obergrenze, kein Verbrauchsziel.

**Herkunft der Verkäufer** (Messung an einer Stichprobe aus 8 Kategorien, ungefiltert): ~15 % DE/AT/CH, die große Mehrheit China und Hongkong. Ohne Länderfilter ist das normal und kein Fehler.

## Was realistisch herauskommt

| Feld | Quote | Hinweis |
|---|---|---|
| Firma, Adresse, Land | ~100 % | aus dem Verkäuferprofil (Pflichtangaben) |
| Sortiment, Umsatz | ~100 % geschätzt, gemessen nur bei Produkten mit „X+ gekauft“ | Spalte `Umsatzbasis` sagt, was gemessen ist |
| E-Mail, Telefon (Bright Data) | hoch bei DACH, gering bei CN/HK | Firmenadresse aus dem Verkäuferprofil, keine persönliche Adresse der Geschäftsführung |
| E-Mail Status (Skael) | für jede Adresse | `Safe to Send`, `Risky`, `Unknown`, `Invalid`; ohne Prüfung `Not Run` |
| Vertretungsberechtigte Person (Bright Data) | ~13–36 % | steht nicht als Feld im Profil, wird aus dem Text gelesen |
| Website (Skael, DACH) | Referenzlauf ~98 % | Firmen-E-Mail ist die stärkste Quelle |
| Impressum bestätigt (Skael, DACH) | ~76 % | Abgleich über Register, USt-IdNr., Firmenname, Telefon, E-Mail |
| Geschäftsführung (Skael, DACH) | ~67 % | aus dem bestätigten Impressum |
| persönliche Anrede | ~62 % | nur bei eindeutigem Vornamen, sonst „Guten Tag“ |

Quoten aus einem Referenzlauf mit ~1.100 DACH-Leads. Sie hängen stark von der Zielgruppe ab. Nach jedem Testlauf die eigenen Zahlen nennen.

## E-Mail-Prüfung

Jede Adresse wird vor der Ausgabe auf Zustellbarkeit geprüft (Skael, 3 Credits). Die Werte sind dieselben wie im Google-Maps-Pfad:

| Status | Bedeutung | Versand |
|---|---|---|
| `Safe to Send` | zustellbar | ja |
| `Risky` | Catch-all: der Server nimmt jede Adresse an | getrennt und vorsichtig |
| `Unknown` | nicht prüfbar | getrennt und vorsichtig |
| `Invalid` | ungültig | nie; die Adresse wird aus dem E-Mail-Feld entfernt |
| `Not Run` | nicht geprüft (kein Schlüssel, Störung, abgeschaltet) | nie per E-Mail |

Geprüft wird die Firmenadresse aus dem Amazon-Profil. Oft ist das eine Sammeladresse wie info@.

## Ansprache-Regeln

Wie für alle Pfade (`07_lead-ausgabe-und-spalten.md`): „Guten Tag Herr/Frau Nachname“ nur bei sicherem Namen **und** Geschlecht, sonst „Guten Tag“. Die Spalte `Match-Status` zeigt, ob die Website über das Impressum bestätigt ist (`register`, `ustid`, `firmenname`, `telefon`, `email`) oder nur vermutet (`domain`, `email-domain`).

## Grenzen

- **Nur amazon.de.** Andere Marktplätze haben andere Kategorie-Nummern.
- **Neuheiten-Fokus:** Die Suche läuft über die Neuheiten-Listen. Sie findet aktive Händler mit neuen Produkten bevorzugt, sehr große Händler fallen über die Größenfilter heraus, wenn gewünscht.
- **Kontakte außerhalb von DACH:** Ohne Impressumspflicht gibt es dort kaum Geschäftsführung und Website.
- **Keine Personalisierung:** Einen individuellen Einstiegssatz liefert dieser Pfad nicht.
- **Ungetestete Echtläufe:** Die überarbeitete Version wurde gegen einen Test-Server geprüft, der Skael-Teil zusätzlich gegen die veröffentlichte Schnittstellen-Beschreibung (api.skael.de/docs). Den ersten echten Lauf immer mit Smoke-Test und Testlauf beginnen.

## Risiken und Recht

- **Amazon-Nutzungsbedingungen:** Die Seiten werden über einen Scraping-Dienst (Oxylabs) abgerufen, nicht über ein eigenes Amazon-Konto. Es gibt daher keine Kontosperre. Die Nutzung muss trotzdem mit den Bedingungen von Amazon und der Dienste vereinbar sein.
- **Datenschutz:** Namen von Geschäftsführung und Einzelunternehmern sind personenbezogene Daten. Bei Ansprache gilt die Informationspflicht nach Art. 14 DSGVO (`08_versand-und-recht.md`). Lead-Daten liegen in `pfade/amazon/arbeit/`. Den Ordner nie weitergeben.
- **E-Mail-Werbung:** ohne Einwilligung grundsätzlich unzulässig (§ 7 UWG), auch an Firmen.
- **Sperrliste:** Abgeglichen werden E-Mail-Domain (auch die einer als ungültig aussortierten Adresse), Website und Impressum-URL. Verkäufer ohne all das lassen sich nicht abgleichen, das dem Nutzer sagen.


---

<!-- Datei: wissen/05_pfad-recruiting.md -->

# Pfad „Recruiting“ – Firmen, die gerade Personal suchen (über die Firmen-Website)

**Zweck:** was der Pfad tut, was er voraussetzt, was herauskommt und wo seine Grenzen liegen.
**Für wen:** Nutzer und KI-Modelle, die einen Recruiting-Lauf planen oder Ergebnisse verstehen wollen.
**Verwandt:** `02_zielgruppen-interview.md` · `03_pfad-google-maps.md` · `18_pfad-stellensuche.md` · `07_lead-ausgabe-und-spalten.md` · `08_versand-und-recht.md` · `11_zugaenge-und-kosten.md`
**Technik im Detail:**

- Anleitung für die KI: `pfade/recruiting/ABLAUF.md`
- Stufen, Datenfelder, Abweichungen: `pfade/google-maps/docs/07_RECRUITING.md`
- Prompts: `pfade/google-maps/prompts/stellenanalyse.txt`, `jobtitel_normalisierung.txt`, `personalisierung_stellenanzeige.txt`, `personalisierung_website.txt`; branchengenaue Fassungen in `pfade/google-maps/prompts/beispiele/`

**Stand:** 2026-11-01 · **Prüfen bis:** 2027-02-01. Nachbau eines Clay-Workbooks (Herkunft: `pfade/recruiting/referenzen/clay-vorlage.md`), läuft lokal. Offline getestet, noch ohne gemessene Quoten.

---

## Stand und Entscheidung

**Verfügbar.** Läuft im Scraper-Programm `pfade/google-maps/` – demselben Programm wie der Google-Maps-Pfad, als eigene Kampagnen-Art (`init --pfad recruiting`) in einer eigenen Kampagne.

„Recruiting“ kann zweierlei bedeuten. Entschieden ist **Variante A**:

| Variante | Wer ist der Lead? | Beispiel-Angebot | Einordnung |
|---|---|---|---|
| **A – Firmen, die gerade einstellen** (gebaut) | das Unternehmen; angesprochen wird die Geschäftsführung | Personaldienstleister, Recruiting-Agentur, Employer-Branding, HR-Software | B2B; die üblichen Regeln für Kaltakquise gelten (`08`) |
| **B – Kandidaten** (nicht gebaut) | Privatpersonen bzw. Fachkräfte | Active Sourcing für eigene Stellen | Personendaten von Privatpersonen, strengere DSGVO-Anforderungen, Nutzungsbedingungen der Plattformen verbieten Scraping meist. **Deutlich höheres Risiko** |

Es gibt **zwei Wege** zu Variante A:

| | Recruiting (dieser Pfad) | Stellensuche (`18_pfad-stellensuche.md`) |
|---|---|---|
| Ausgangspunkt | Branche + Region → Firmen bei Google Maps | Beruf + Orte → Anzeigen in Jobportalen |
| findet | Firmen, die auf der **eigenen Website** ausschreiben | Firmen, die **über Portale** ausschreiben |
| passt, wenn | die Branche der Wunschkunden bekannt ist | der gesuchte Beruf bekannt ist |

Beide ergänzen sich: Kleine Betriebe schreiben oft nur auf der eigenen Website aus, größere fast immer über Portale.

## Wann dieser Pfad

- Wunschkunde ist erkennbar daran, dass er **gerade einstellt** (Block C, Antwort 4 im Interview), und die **Branche** ist bekannt („Speditionen in Ulm, die einstellen“).
- Die Ansprache soll an die **Stelle** anknüpfen: „ich habe gesehen, dass Sie gerade jemanden als Berufskraftfahrer suchen, der den Führerschein Klasse CE und eine Fahrerkarte mitbringt.“

Nicht geeignet für Kandidaten-Suche (Variante B).

Ist auch der **Beruf** bekannt, kommt ebenso die Stellensuche über Jobportale in Frage (`18_pfad-stellensuche.md`). Welcher Weg besser liefert, zeigt der **Testballon**. Er fährt beide Wege mit je ~100 Leads und vergleicht Kosten, Qualität und Marktgröße (`pfade/google-maps/docs/09_TESTBALLON.md`). Gibt es zu wenige Firmen mit Stelle, schaltet er die NK-Strecke zu (nur mit Prüfprofil) und nimmt kleinere Städte auf.

## Ablauf

```
Branche + Region + gesuchte Berufe
  → Städte → Maps-Suche → Firmen
  → Dedupe über die Domain
  → Prüfung gegen das Wunschkundenprofil
  → Stellen-Erkennung: Startseite + bis zu 2 Karriere-Seiten der Firmen-Website lesen
       ├─ Stelle gefunden ─► RC: Impressum, GF, E-Mail, Anrede, Jobtitel normalisieren, Opener zur Stelle
       └─ keine Stelle ────► NK (nur mit --nk): Satz zur Website;  sonst Liste 4
  → Export (5 Listen, Sperrliste eingebaut)
```

Einzige Quelle für offene Stellen ist hier die **Website der Firma**. Stellen aus Jobportalen (Indeed, Stepstone, Arbeitsagentur, Kununu) holt der Pfad **Stellensuche** (`18_pfad-stellensuche.md`).

| Schritt | Was passiert | Dienst |
|---|---|---|
| Städte, Maps-Suche, Dedupe | wie Google-Maps-Pfad, Stufe 1–3b | Skael |
| Prüfprofil | Website gegen Wunschkunden (ja/nein, Sicherheit, Begründung) | Skael `icp_checker` |
| **Stellen-Erkennung (3e)** | Startseite abrufen, Links zu Karriere/Jobs/Stellenangebote der eigenen Domain finden, bis zu 2 davon abrufen; KI gibt **genau eine** Stelle zu den gesuchten Berufen zurück: Bezeichnung, Bereich, Kurzbeschreibung | Skael `web_scraper`, KI |
| Anreicherung | Impressum, GF, E-Mail-Wasserfall, Anrede – identisch mit Google Maps Stufe 4 | Skael, Findymail, KI |
| **Opener** | Jobtitel normalisieren, dann ein Satz: „ich habe gesehen, dass Sie gerade jemanden als [Rolle] suchen, der [1–2 echte Anforderungen] mitbringt.“ Ohne echte Anforderungen endet der Satz nach „suchen.“ – keine Floskeln | KI |
| Versandfertig | E-Mail **und** Jobtitel **und** Opener (RC) bzw. E-Mail und Satz zur Website (NK) | – |

Die KI läuft standardmäßig über Skael (`LLM_PROVIDER=skael`), wahlweise über OpenAI.

## Was die Prompts können müssen

Die Standard-Prompts sind **branchenneutral**. Die gesuchten Berufe kommen je Kampagne aus `init --berufe "A,B,C"` (Reihenfolge = Priorität) in den Stellen-Prompt. Anzupassen ist meist nur:

1. **Prüfprofil** – wie im Google-Maps-Pfad (`icp.txt` der Kampagne), Bauanleitung `pfade/google-maps/prompts/icp_prompt_builder.md`, Beispiel `prompts/beispiele/icp_logistik.txt`.
2. Optional **branchengenaue Fassungen** von Stellen-Prompt (`pfade/google-maps/prompts/beispiele/stellenanalyse_logistik.txt`: feste Berufsliste, Ausschlüsse, Priorität) und Opener (`pfade/google-maps/prompts/beispiele/personalisierung_stellenanzeige_logistik.txt`, `…_ki.txt`). Dazu die Datei unter dem Standardnamen in `kampagnen/<name>/prompts/` kopieren; das Programm sucht dort zuerst.

## Befehle (Kurzfassung)

```bash
./scraper.sh neue-kampagne <k>
./scraper.sh --kampagne <k> init --pfad recruiting --keywords "Spedition" --countries DE \
        --min-population 200000 --berufe "Berufskraftfahrer,Disponent" [--nk]
./scraper.sh --kampagne <k> run --stage all
./scraper.sh --kampagne <k> export
```

Vollständig mit Testlauf und Stichprobe: `pfade/recruiting/ABLAUF.md`.

## Kosten – wovon sie abhängen

```
Kosten ≈ (Keywords × Städte) × Maps-Suche
           + gefundene Firmen × Prüfung
           + passende Firmen × (1–3 Website-Abrufe + 1 KI-Aufruf)       ← Stellen-Erkennung
           + Firmen mit Stelle × (Impressum + E-Mail-Suche/-Prüfung + 3 KI-Aufrufe)
```

- Die Stellen-Erkennung läuft für **jede passende Firma**, auch für die ohne Stelle. Ein strenges Prüfprofil spart hier am meisten.
- Hebel wie im Google-Maps-Pfad: Mindest-Ortsgröße, Anzahl Suchbegriffe.
- Bezahlte Startseiten werden gespeichert und für die NK-Strecke wiederverwendet.
- `status` zeigt nach jedem Lauf die echten Skael-Kosten („Skael-Kosten bisher“, Kostenzähler, `11_zugaenge-und-kosten.md`).

## Quoten

Noch nicht gemessen. Nach dem ersten echten Testlauf hier eintragen:

| Kennzahl | Wert | Lauf |
|---|---|---|
| Firmen mit Website, die zum Profil passen | – | – |
| davon mit erkannter Stelle | – | – |
| davon mit E-Mail | – | – |
| versandfertig | – | – |
| Opener mit Fehler in der Stichprobe | – | – |

Erwartung (ungeprüft): Die Stellen-Quote hängt stark von der Branche ab. Handwerk und Logistik schreiben häufig auf der eigenen Website aus, Konzerne über Bewerberportale, die der Pfad nicht liest.

## Grenzen

- **Eine Stelle je Firma.** Bei mehreren passenden Stellen wählt die KI nach der Reihenfolge der gesuchten Berufe eine aus.
- **Stellen-Erkennung liest nur die eigene Website** (Startseite + bis zu 2 Karriere-Seiten, `KARRIERE_SEITEN`). Stellen, die nur auf externen Bewerberportalen oder Jobbörsen stehen, findet dieser Pfad nicht – dafür gibt es den Pfad Stellensuche.
- **Alter der Stelle** wird nicht erfasst. Die Zahl offener Stellen auch nicht; beides liefert nur die Stellensuche.
- **Nur der erste Geschäftsführer** aus dem Impressum; die Personalabteilung wird nicht gesucht.
- **Anrede:** Der Anrede-Prompt setzt bei unsicheren Vornamen „Herr“. Die Exportspalte `Ansprache` ist deshalb nur bei Anrede-Sicherheit > 60 persönlich, sonst neutral.

## Rechtliches in Kürze

- **Datenquellen:** öffentliche Unternehmens-Websites und Google Maps (über Skael). Jobportale nutzt dieser Pfad nicht; die Stellensuche bezieht sie über die Skael-Schnittstelle (Einordnung in `18_pfad-stellensuche.md`).
- **Personenbezug:** Namen der Geschäftsführung und persönliche E-Mail-Adressen sind personenbezogen (DSGVO). Kontaktpersonen aus Stellenangeboten werden **nicht** übernommen.
- **Ansprache:** E-Mail-Werbung ohne Einwilligung bleibt unzulässig (§ 7 Abs. 2 Nr. 2 UWG). Der Bezug auf eine öffentliche Stellenanzeige ändert daran nichts. Den Aufhänger nicht fingieren: nur Stellen nennen, die wirklich ausgeschrieben sind (Stichprobe!), Listen nicht wochenlang liegen lassen.

Mehr in `08_versand-und-recht.md`.


---

<!-- Datei: wissen/06_pfad-e-commerce.md -->

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


---

<!-- Datei: wissen/07_lead-ausgabe-und-spalten.md -->

# Ausgabe – Dateien, Spalten, Ansprache

**Zweck:** was am Ende eines Laufs in welcher Datei steht und wie man es in ein Versandtool bringt.
**Für wen:** Nutzer vor dem Import und KI-Modelle, die Spalten erklären oder umbauen sollen.
**Verwandt:** `03_pfad-google-maps.md` · `04_pfad-amazon.md` · `05_pfad-recruiting.md` · `06_pfad-e-commerce.md` · `18_pfad-stellensuche.md` · `09_sperrliste.md`

---

## Google Maps – fünf Listen plus Archiv

Alle CSV-Dateien sind mit Semikolon getrennt, UTF-8 mit BOM, und öffnen sich sauber in Excel. Sie liegen in `pfade/google-maps/exports/`.

| Datei | Inhalt | Verwenden für |
|---|---|---|
| `1_zielgruppe_geschaeftsfuehrer_….csv` | passt zum Profil, E-Mail der Geschäftsführung | Versand (erste Wahl) |
| `2_zielgruppe_info_….csv` | passt zum Profil, nur allgemeine Adresse (info@) | Versand, wenn gewünscht |
| `3_unsicher_….csv` | Profil unsicher (Sicherheit 0,40–0,60), nur Firmendaten | von Hand prüfen |
| `4_nicht_zielgruppe_….csv` | aussortiert, nicht prüfbar, Ketten/Konzerne | nichts, nur Nachvollziehbarkeit |
| `5_gesperrt_sperrliste_….csv` | Domain steht auf der Community-Sperrliste | **nie anschreiben** |
| `leads_archiv_….json` | alle Rohdaten aller angereicherten Firmen | Bestand aufbauen, ohne neu zu scrapen |
| `leads_<kampagne>_….json` | nur mit `export --lead-format`: die Leads aus Liste 1 und 2 im festen Lead-Format (ohne Kampagne: Name der Datenbank) | Videos und Landingpages je Lead |

Wichtige Spalten in Liste 1 und 2:

| Spalte | Bedeutung |
|---|---|
| Firmenname, Website | aus dem Impressum, sonst aus Google Maps |
| E-Mail, E-Mail Typ, E-Mail Status, E-Mail Quelle | Adresse; `GF`/`Info@`; `Safe to Send`/`Risky`/`Unknown`; Skael/Findymail |
| Anrede, Vorname, Nachname, Kontaktperson | aus dem Impressum, Geschlecht per KI |
| Ansprache Formal / Normal / Guten Tag / Persönlich | fertige Grußformeln in vier Tonlagen |
| Ansprache, Ansprache Grund, Anrede Sicherheit | Standard-Grußformel nach der Paketregel: „Guten Tag Herr/Frau Nachname“ nur bei Anrede-Sicherheit > 60, sonst neutral „Guten Tag“; der Grund steht daneben (z. B. „Vorname mehrdeutig (55%)“, „kein Geschäftsführer“) |
| Personalisierung | ein bis zwei Sätze, die direkt an die Anrede anschließen |
| Pain / Angebot, Einordnung belegt durch | Einordnung des Bedarfs (wenn das Profil das vorsieht) |
| Videotitel | für Video-Outreach |
| Adresse, PLZ, Telefon | je aus Impressum und Google Maps |
| Kategorie, Bewertung, Anzahl Bewertungen | Google-Maps-Daten |
| Keyword, Stadt, Land | Herkunft des Leads |
| Externe ID | feste Kennung je Firma: Business ID, sonst Place ID, sonst `ds-<Datensatz-Nr.>` |
| Quelle URL | Impressum-Seite, von der die Kontaktdaten stammen; ohne Impressum-URL der Google-Maps-Eintrag (`https://www.google.com/maps/place/?q=place_id:<Place ID>`); leer, wenn beides fehlt |
| Erfasst am | Datum der letzten Anreicherung (`JJJJ-MM-TT`) |
| Kampagnen-Art | `google-maps`, `recruiting` oder `stellensuche` |

Externe ID, Quelle URL und Erfasst am belegen die Herkunft jedes Datensatzes für die Information nach Art. 14 DSGVO.

**Lead-Format (`export --lead-format`):** eine JSON-Liste, ein Objekt je Lead aus Liste 1 und 2. Gesperrte und blockierte Leads (Liste 5) fehlen immer. Leere Werte stehen als `""` drin. Felder:

`externe_id, firma, rechtsform, domain, website, strasse, plz, ort, land, telefon, branche, mitarbeiter, handelsregister, anrede, vorname, nachname, position, email, email_typ, email_status, kontakt_telefon, linkedin_url, quelle, quelle_url, erfasst_am, personalisierung, video_titel`

| Feld | Herkunft |
|---|---|
| firma, website, domain | Firmenname und Website wie in der CSV; Domain ohne Protokoll und `www` |
| strasse | aus der Impressum-Adresse, sonst aus der Maps-Adresse; leer, wenn nicht eindeutig lesbar |
| plz, ort, land | PLZ aus Google Maps; Ort und Land der Suche |
| telefon, branche | Telefon aus dem Impressum, sonst Google Maps; Kategorie aus Google Maps |
| handelsregister | Registergericht und -nummer aus dem Impressum, falls angegeben |
| position, email_typ | `Geschäftsführung` und `persoenlich` bei GF-Adresse; leer und `funktion` bei info@ |
| quelle, quelle_url | „Google-Maps-Suche nach „<Keyword>“ in <Stadt>“, mit Impressum-URL ergänzt um „; Kontaktdaten aus dem Impressum“; Link wie Spalte Quelle URL |
| video_titel | Videotitel |
| rechtsform, mitarbeiter, kontakt_telefon | bleiben leer, der Pfad erhebt sie nicht |

**E-Mail Status:**

- **`Safe to Send`:** zustellbar.
- **`Risky`:** Catch-all, der Server nimmt alles an.
- **`Unknown`:** nicht prüfbar.

`Risky` und `Unknown` getrennt und vorsichtig versenden, sonst leidet die Absender-Reputation.

## Recruiting und Stellensuche – dieselben fünf Listen

Beide Recruiting-Wege laufen im Programm `pfade/google-maps/` und exportieren dieselben fünf Listen plus Archiv, mit eingebautem Sperrlisten-Abgleich. Die Dateien liegen im Ordner `exports/` der Kampagne. Unterschiede:

| Liste | Recruiting (Firmen-Website) | Stellensuche (Jobportale) |
|---|---|---|
| `0_stellen_…` | – | **eine Zeile je Anzeige:** Firma, Stellenbezeichnung, Ort, PLZ, veröffentlicht am, Portal, Link zur Anzeige, Gehalt, Website, Suchbegriff, Firma in Lead-Liste (1/2). Firmen auf der Sperrliste fehlen |
| 1, 2 | zusätzlich `Strecke` (`rc` = mit Stelle, `nk` = ohne), `Jobtitel` (normalisiert), `Stelle (Original)`, `Bereich`, `Stellenbeschreibung` | eine Zeile je Firma, zusätzlich `Jobtitel`, `Stellenbezeichnung`, `Ort der Stelle`, `veröffentlicht am`, `Portal`, `Link zur Anzeige`, `Gehalt`, `Offene Stellen (Anzahl)`, `Gefunden auf` |
| 3 | wie Google Maps, dazu `Offene Stelle`, `Gefunden auf` | wie Google Maps, dazu die Stellenspalten |
| 4 | zusätzlich passende Firmen **ohne offene Stelle** („passt, aber keine offene Stelle gefunden“), wenn die NK-Strecke aus ist | zusätzlich Firmen ohne belegte Website („keine eigene Website gefunden“) und vom Größen-Check Aussortierte („Größen-Check: Konzern“, „… öffentliche Hand/Verband“, „… IT-Wettbewerber“; Details in „Begründung“) |
| 5 | gesperrt | gesperrt |

`Personalisierung` enthält bei einer erkannten Stelle den Satz „ich habe gesehen, dass Sie gerade jemanden als … suchen, …“, bei der NK-Strecke einen Satz zur Website. Videotitel gibt es auf beiden Wegen nicht.

Firmen, die nach der Anreicherung noch herausfallen (später geschärfter Titel-Filter, Größen-Check, Dedupe), stehen nicht mehr in Liste 1 oder 2, sondern nur noch in Liste 4.

**Stellensuche „nur Stellenliste“ (`--nur-stellen`):** statt der Listen 1–4 gibt es `1_firmen_mit_stellen_…` (eine Zeile je Firma, ohne Kontaktdaten, Einstufung „Stelle offen“ bzw. „Stelle offen, Website unbekannt“) und Liste 5. **Nicht versandfertig:** Ohne Website greift der Sperrlisten-Abgleich nicht, und es gibt keine Kontaktdaten.

## Amazon – eine Liste je Kampagne

Alle Dateien liegen in `pfade/amazon/arbeit/`, mit Semikolon getrennt, UTF-8 mit BOM.

| Datei | Inhalt | Verwenden für |
|---|---|---|
| `leads_<kampagne>_MASTER.csv` | alle gelieferten Leads der Kampagne (wird nur angehängt) | Grundlage |
| `…_angereichert.csv` | dazu E-Mail Status, Website, Impressum, Geschäftsführung, Anrede (Skael) | Grundlage, wenn angereichert |
| `…_standard.csv` | Standardfelder vorn, alle anderen Spalten dahinter | Sperrlisten-Abgleich |
| `…_standard_bereinigt.csv` | nach dem Abgleich | **Versand** |
| `…_standard_gesperrt.csv` | Domain auf der Sperrliste | **nie anschreiben** |
| `report_<kampagne>.json` | Funnel, Ausschlussgründe, Kosten, Abfragen je Lead | Kalkulation des nächsten Laufs |

Wichtige Spalten:

| Spalte | Bedeutung |
|---|---|
| Firma, Adresse, Land | aus dem Amazon-Verkäuferprofil (Pflichtangaben). Land = Firmensitz |
| Seller-ID, Storefront-URL, Verkäuferprofil-URL | Amazon-Verkäufer; Storefront `https://www.amazon.de/s?me=<ID>&marketplaceID=A1PA6795UKMFR9` |
| Marke, Markenanteil %, Produkte, Produktfamilien, Portfolio-Bewertungen | Sortiment aus einer Stichprobe von 12 Produkten |
| Umsatz/Monat ca. EUR, Umsatzbasis | `gemessen` (echte Kaufzahlen), `gemessen + geschätzt`, `geschätzt` oder `nicht messbar` (Umsatz leer) |
| E-Mail, Telefon, Handelsregister, USt-IdNr, Rechtsform, Vertretungsberechtigt | Kontaktdaten über Bright Data |
| E-Mail Status | Zustellbarkeit laut Skael: `Safe to Send`, `Risky`, `Unknown`, `Invalid`; ohne Prüfung `Not Run`. Ungültige Adressen stehen in `E-Mail ungültig` statt im Feld E-Mail |
| Website, Impressum-Firmenname, Geschäftsführung, Match-Status | Anreicherung; Match-Status sagt, ob das Impressum die Firma bestätigt (`register`, `ustid`, `firmenname`, `telefon`, `email`) oder nur vermutet (`domain`, `email-domain`) |
| Anrede, Vorname, Nachname, Ansprache | Standardfelder; „Guten Tag Herr/Frau Nachname“ nur bei sicherem Namen und Geschlecht |

## E-Commerce – vier Listen plus Archiv

Format wie Google Maps (Semikolon, UTF-8 mit BOM). Die Dateien liegen in `pfade/e-commerce/exports/`.

| Datei | Inhalt | Verwenden für |
|---|---|---|
| `1_geschaeftsfuehrer_….csv` | Ready to Send, E-Mail der Geschäftsführung | Versand (erste Wahl) |
| `2_info_….csv` | Ready to Send, nur allgemeine Adresse | Versand, wenn gewünscht |
| `3_aussortiert_….csv` | kein aktiver Shop, passt nicht zum Shop-Profil (mit Begründung), kein Traffic, keine E-Mail, Duplikat – Spalte „Grund“ | nichts, nur Nachvollziehbarkeit |
| `4_gesperrt_sperrliste_….csv` | Domain steht auf der Community-Sperrliste | **nie anschreiben** |
| `shops_archiv_….json` | alle Shops mit allen Rohdaten | Bestand aufbauen, ohne neu abzufragen |

Die Spalten in Liste 1 und 2 entsprechen Google Maps (Firmenname, Website, E-Mail, Anrede, vier Ansprachen, Personalisierung, Videotitel, Impressum-Daten). Ohne die Maps-Felder, dafür mit:

- `Besuche/Monat (Schnitt)` und `Besuche/Monat (Höchstwert)` – SimilarWeb-Schätzung
- `Firmenname (Import)` – der Name aus der Eingabeliste
- `Quelle` – Dateiname der Eingabeliste
- `Betreff` und `Mailtext` – **nur, wenn ein Mailtext hinterlegt ist:** die fertige Mail je Lead, Platzhalter schon ersetzt. Die zwei Spalten stehen direkt nach `Videotitel`. Ohne Mailtext fehlen sie.

**Platzhalter im Mailtext.** Der Mailtext beginnt mit einer Zeile `Betreff: …`, nach einer Leerzeile folgt der Text. Platzhalter heißen wie die Spalten und stehen in doppelten geschweiften Klammern. Die Schreibweise muss genau stimmen, auch Groß- und Kleinschreibung:

| Platzhalter | wird ersetzt durch |
|---|---|
| `{{Ansprache Formal}}`, `{{Ansprache Normal}}`, `{{Ansprache Guten Tag}}`, `{{Ansprache Persönlich}}` | die Grußformel in der gewählten Tonlage; mindestens eine davon muss im Text stehen |
| `{{Personalisierung}}` | der persönliche Satz; Pflicht, wenn die Personalisierung eingeschaltet ist. Er beginnt kleingeschrieben und gehört direkt hinter die Grußzeile |
| `{{Firmenname}}`, `{{Website}}` | Firmenname (aus dem Impressum, sonst aus der Liste) und Website |
| `{{Videotitel}}` | Videotitel; leer, wenn kein Video geplant ist |
| `{{Anrede}}`, `{{Vorname}}`, `{{Nachname}}` | Daten der Geschäftsführung aus dem Impressum; **leer, wenn das Impressum keine Geschäftsführung nennt** (betrifft vor allem info@-Leads), deshalb besser die Ansprache-Platzhalter nehmen |

**Was `set-mailtext` prüft.** Diese Liste gilt für den ganzen Pfad; andere Dateien verweisen hierher.

- **Fehler** – der Mailtext wird nicht gespeichert (Exit-Code 2), ein schon gespeicherter mit Fehler stoppt den Export:
  - die erste Zeile beginnt nicht mit `Betreff:`, oder der Betreff ist leer,
  - unter dem Betreff fehlt der Text,
  - unbekannter Platzhalter, z. B. `{{Personalisierungen}}` oder `{{ansprache normal}}` (Groß- und Kleinschreibung zählen),
  - ein Platzhalter ist unvollständig (`{{Firmenname}`) oder hat nur einfache Klammern (`{Vorname}`),
  - kein Ansprache-Platzhalter im Text, oder er steht nicht in der ersten Zeile unter dem Betreff,
  - `{{Personalisierung}}` fehlt oder steht nicht direkt unter der Begrüßung, solange die Personalisierung eingeschaltet ist.
- **Hinweise** – gespeichert wird trotzdem:
  - `{{Anrede}}`, `{{Vorname}}` oder `{{Nachname}}` im Text (leer ohne Geschäftsführung im Impressum),
  - `{{Videotitel}}`, obwohl Videotitel ausgeschaltet sind,
  - `{{Personalisierung}}`, obwohl die Personalisierung ausgeschaltet ist,
  - Text in einfachen geschweiften Klammern, der kein Platzhalter ist (bleibt so in der Mail stehen).

Danach zeigt `set-mailtext` die Mail an einem erfundenen Beispiel-Lead.

## Standardformat für alle Pfade

Damit Listen aus verschiedenen Pfaden in dasselbe Versandtool passen, liefert jeder Pfad mindestens diese Felder. Neue Pfade **müssen** sie liefern.

| Standardfeld | Google Maps | Amazon | E-Commerce |
|---|---|---|---|
| Firmenname | Firmenname | Firmenname (Impressum, wenn bestätigt, sonst Verkäuferprofil) | Firmenname |
| Website | Website | Website | Website |
| E-Mail | E-Mail | E-Mail (Bright Data) | E-Mail |
| E-Mail Status | E-Mail Status | E-Mail Status | E-Mail Status |
| Anrede | Anrede | Anrede | Anrede |
| Vorname / Nachname | Vorname / Nachname | Vorname / Nachname (Geschäftsführung) | Vorname / Nachname |
| Ansprache | Ansprache Guten Tag (bzw. gewünschte Tonlage) | Ansprache | Ansprache Guten Tag (bzw. gewünschte Tonlage) |
| Personalisierung | Personalisierung | – (nicht Teil des Pfads, keine Spalte) | Personalisierung |
| Quelle | Keyword, Stadt, Land | „amazon.de Seller <ID> · Kategorie · Land“ | Quelle (Dateiname), Firmenname (Import) |
| Pfad | `google-maps` | `amazon` (eigene Firmenliste: `eigene-liste`) | `e-commerce` |

Beim Amazon-Pfad stellt `pfade/amazon/standardformat.mjs` diese Felder nach vorn.

## Ansprache – gemeinsame Regeln

1. **Im Zweifel neutral.** Ist der Name oder das Geschlecht unsicher, heißt es „Guten Tag“ statt einer persönlichen Anrede.
2. **Nur Nachname** in der persönlichen Form: „Guten Tag Herr Mustermann“.
3. **Personalisierung beobachtet, unterstellt nicht.** Sie beschreibt, was auf der Website zu sehen ist, und benennt keine Probleme des Empfängers.

## In ein Versandtool übernehmen

1. Nur die bereinigten Listen importieren: Google Maps 1/2, E-Commerce 1/2, Amazon `…_standard_bereinigt.csv`.
2. Gesperrte Domains zusätzlich im Versandtool als Domain-Sperre hinterlegen (`09_sperrliste.md`).
3. Nach dem Export `export --mark` ausführen. Sonst landen dieselben Leads beim nächsten Export erneut in der Liste.


---

<!-- Datei: wissen/08_versand-und-recht.md -->

# Versand und Recht – was vor dem ersten Kontakt klar sein muss

**Zweck:** die rechtlichen Rahmenbedingungen für Datensammlung und Ansprache, kompakt und ehrlich.
**Für wen:** Nutzer vor dem Versand und KI-Modelle, die Fragen dazu beantworten.
**Verwandt:** `09_sperrliste.md` · `10_abmahnung-was-tun.md` · Skill `abmahnung-werbemail-abwehr` (Rechtsprechung im Detail)
**Stand:** 2026-10-04, Deutschland · **Prüfen bis:** 2027-04-04. **Keine Rechtsberatung.** Im Zweifel anwaltlich prüfen lassen.

---

## Das Wichtigste in drei Sätzen

1. **E-Mail-Werbung ohne vorherige ausdrückliche Einwilligung** ist eine unzumutbare Belästigung (§ 7 Abs. 2 Nr. 2 UWG). Das gilt auch gegenüber Unternehmen, auch bei einer einzigen Mail, auch an info@-Adressen aus dem Impressum.
2. Das Risiko ist eine **Abmahnung**:
   - durch Mitbewerber (§ 8 UWG),
   - oder durch den Empfänger selbst über §§ 823, 1004 BGB (Eingriff in den eingerichteten und ausgeübten Gewerbebetrieb).

   Dazu kommen oft Forderungen nach DSGVO-Auskunft und Schadensersatz.
3. **Die Sperrliste senkt das Risiko** wiederholter Abmahnungen durch bekannte Abmahner. Sie macht Kaltakquise per E-Mail **nicht zulässig**.

## Kanäle im Vergleich (B2B)

| Kanal | Regel | Einordnung |
|---|---|---|
| E-Mail, Fax | vorherige ausdrückliche Einwilligung nötig (§ 7 Abs. 2 Nr. 2 UWG). Ausnahme nur für Bestandskunden unter den engen Voraussetzungen des § 7 Abs. 3 UWG | höchstes Abmahnrisiko |
| Telefon | gegenüber Unternehmen genügt eine **mutmaßliche** Einwilligung (§ 7 Abs. 2 Nr. 1 UWG). Es muss ein konkreter, sachlicher Bezug zum Geschäft des Angerufenen bestehen. Gegenüber Verbrauchern ist eine ausdrückliche Einwilligung nötig | Einzelfallfrage |
| Brief | grundsätzlich zulässig, solange kein erkennbarer Widerspruch vorliegt | geringes Risiko |
| LinkedIn/Xing-Nachricht | Plattformregeln; massenhaft automatisiert oft unzulässig bzw. regelwidrig | Plattform- und Einzelfallfrage |

## Pflichtangaben in jeder Werbe-Nachricht

- **Absender klar erkennbar,** keine Verschleierung. Der Betreff darf den werblichen Charakter nicht verschleiern (§ 6 DDG, § 7 Abs. 2 Nr. 3 UWG).
- **Gültige Adresse,** über die der Empfänger weitere Nachrichten abbestellen kann (§ 7 Abs. 2 Nr. 3 UWG).
- **Rechtsträger und Anschrift** im Footer.
- **Keine fingierten Aufhänger** wie „Ein Kollege hat mich auf Sie aufmerksam gemacht“ oder ein falsches „AW:“/„WG:“ im Betreff. Das ist irreführend und leicht beweisbar.

## Datenschutz (DSGVO)

| Thema | Was gilt |
|---|---|
| **Personenbezug** | Namen der Geschäftsführung, persönliche E-Mail-Adressen (vorname.nachname@…) und Einzelunternehmer-Domains sind personenbezogene Daten. Firmendaten allein (info@, Firmenname) meist nicht. |
| **Rechtsgrundlage** | in der Regel berechtigtes Interesse (Art. 6 Abs. 1 lit. f, Erwägungsgrund 47). Verstößt die Ansprache gegen das UWG, trägt diese Abwägung kaum. |
| **Informationspflicht** | Werden Daten aus anderen Quellen erhoben (Google Maps, Impressum, Amazon), muss spätestens bei der ersten Kontaktaufnahme informiert werden (Art. 14 Abs. 3 lit. b). Das geht z. B. per Link zu einer Datenschutz-Seite mit Quelle, Zweck, Speicherdauer und Widerspruchsrecht. |
| **Widerspruch** | Widerspricht jemand der Direktwerbung, ist das endgültig (Art. 21 Abs. 2 und 3). Sofort sperren, in **allen** Systemen. |
| **Auskunft** | Anfragen nach Art. 15 innerhalb eines Monats vollständig beantworten: Quelle, Zwecke, Empfänger, Speicherdauer, Kopie der Daten. Dafür muss nachvollziehbar sein, woher jeder Lead stammt. Die Exporte enthalten dafür Keyword, Stadt, Quelle. |
| **Löschkonzept** | Rohdaten (`data/`, `exports/`, Archiv) nicht unbegrenzt aufbewahren; eine Frist festlegen. |
| **Auftragsverarbeitung** | Versandtool, CRM und Anreicherungsdienste verarbeiten Daten im Auftrag. AV-Verträge abschließen; bei Diensten außerhalb der EU die Übermittlungsgrundlage prüfen. |

## Nutzungsbedingungen der Datenquellen

- **Google Maps:** über einen Drittanbieter (Skael). Es gelten dessen Bedingungen und die von Google.
- **Amazon:** über einen Drittanbieter (Oxylabs), nicht über ein eigenes Amazon-Konto. Es gelten dessen Bedingungen und die von Amazon. Kontaktdaten der Verkäufer kommen von Bright Data (`04_pfad-amazon.md`).
- **Handelsregister und Wirtschaftsdatenbanken:** Abruf für Recherche üblich; massenhafte automatisierte Abrufe je nach Anbieter untersagt.
- **Jobbörsen, LinkedIn, Xing** (künftige Pfade): Scraping meist ausdrücklich untersagt.

## Vor dem ersten Versand – Checkliste

- [ ] Kanal und Rechtslage bewusst entschieden (siehe Tabelle oben)
- [ ] Nur bereinigte Listen; Sperrliste auch im Versandtool hinterlegt
- [ ] Absender, Footer, Abmeldeweg, Datenschutzhinweis nach Art. 14 vorhanden
- [ ] Keine fingierten Aufhänger in den Vorlagen
- [ ] Prozess für Widerspruch, Abmeldung und Auskunft steht (wer, wie schnell, in welchen Systemen)
- [ ] Leadquelle je Datensatz nachvollziehbar
- [ ] Bei einer Abmahnung: nicht vorschnell zahlen oder unterschreiben → `10_abmahnung-was-tun.md`


---

<!-- Datei: wissen/09_sperrliste.md -->

# Community-Sperrliste

**Zweck:** wie die Sperrliste funktioniert, wie sie in jedem Pfad wirkt, wie gemeldet und widersprochen wird.
**Für wen:** Nutzer, Betreiber und KI-Modelle.
**Verwandt:** `10_abmahnung-was-tun.md` · `08_versand-und-recht.md` · Repository `werbemail-sperrliste` (README, EINRICHTUNG, WIDERSPRUCH)

---

## Was sie ist

Eine öffentliche Liste von **Domains**, deren Unternehmen nach einer Werbe-E-Mail abgemahnt haben.

- Gesperrt wird immer die **ganze Domain** mit allen Subdomains und allen E-Mail-Adressen darunter.
- Zusammengehörige Domains desselben Unternehmens bilden eine Gruppe.
- Die Liste liegt in einem GitHub-Repository und **ergänzt sich selbst**: Jede Meldung wird automatisch geprüft und in wenigen Minuten übernommen.

Ein Eintrag bedeutet nur: Dieses Unternehmen möchte keine Werbe-E-Mails. Er sagt nichts darüber, ob eine Abmahnung berechtigt war.

## Wie sie in den Pfaden wirkt

| Pfad | Abgleich | Ergebnis |
|---|---|---|
| Google Maps | automatisch bei jedem `export` | Treffer nur in `5_gesperrt_sperrliste_….csv` |
| Amazon und alle weiteren | `python3 werkzeuge/sperrliste_abgleich.py <liste.csv>` als letzte Phase | `_bereinigt.csv` / `_gesperrt.csv` |
| eigenes Versandtool | Sperrliste importieren: `https://raw.githubusercontent.com/alexseeed/werbemail-sperrliste/main/data/sperrliste.txt` | Domain-Sperre |

Ist die Liste nicht erreichbar, wird die letzte lokale Kopie genutzt. Gibt es keine, wird **nicht** ausgeliefert. Das ist Absicht: Lieber kein Export als ein ungeprüfter.

## Melden – Bedingung der Nutzung

Wer abgemahnt wird, meldet den Abmahner. Der Skill `abmahnung-werbemail-abwehr` macht das am Ende jedes Falls automatisch und zeigt vorher, was gesendet wird.

| Gemeldet wird | Nie gemeldet wird |
|---|---|
| Domains des Abmahners und seine zugehörigen Domains (mit Beleg) | E-Mail-Adressen, Namen, Aktenzeichen, Schriftsätze |
| Domain der Kanzlei | der Name des meldenden Unternehmens |
| Monat, Forderungsspanne, Art. 82 ja/nein, Vorgehen, Status | Freitexte, Wertungen |

Die Domain des meldenden Unternehmens dient nur der Berechnung eines anonymen Schlüssels. So lassen sich unabhängige Meldungen zählen. Gespeichert wird sie nicht.

**Bestätigt** heißt: mindestens zwei unabhängige Unternehmen haben dieselbe Domain gemeldet.

## Schutz vor Missbrauch

- Jede gemeldete Domain muss im DNS existieren.
- **Schutzliste:** Freemail-Anbieter, große Plattformen und Behörden sind nie sperrbar.
- **Widerspruchsliste:** Nach einem Widerspruch wird eine Domain entfernt und nie wieder aufgenommen.
- Meldungen dürfen keine „@“ und keine Freitexte enthalten.
- Höchstgrenzen je Stunde und je meldendem Unternehmen.

## Widerspruch

Gelistete Unternehmen können jederzeit widersprechen (`WIDERSPRUCH.md` im Repository). Der Betreiber trägt die Domain in die Widerspruchsliste ein; sie verschwindet sofort aus allen Listen.

## Eigene Blockliste (bereits kontaktiert)

Firmen aus früheren Kampagnen gehören **nicht** auf die Community-Sperrliste, sondern auf die private Blockliste des Google-Maps-Pfads:

```bash
python3 -m scraper blockliste-import alte_leads.csv
```

- Liegt in `data/blockliste.txt`, bleibt lokal, wird nie weitergegeben.
- Firmen-Domains werden komplett gesperrt, Freemail-Adressen (t-online.de, web.de …) nur als einzelne Adresse.
- Greift vor der Prüfung gegen das Wunschkundenprofil (spart Kosten) und noch einmal beim Export (Liste 5).

## Grenzen

- Ohne Moderation sind **Falschmeldungen möglich**. Die harmlose Wirkung eines Eintrags (nur Werbe-Sperre) begrenzt den Schaden.
- Firmen **ohne eigene Website** (z. B. manche Amazon-Seller) lassen sich nicht abgleichen.
- Die Liste schützt nur vor **bekannten** Abmahnern. Sie macht Kaltakquise nicht zulässig (`08`).


---

<!-- Datei: wissen/10_abmahnung-was-tun.md -->

# Abmahnung erhalten – was jetzt?

**Zweck:** die ersten Schritte nach einer Abmahnung wegen einer Werbe-E-Mail. Die ausführliche Prüfung übernimmt der Skill `abmahnung-werbemail-abwehr`.
**Für wen:** Nutzer, die gerade eine Abmahnung bekommen haben, und KI-Modelle, die erste Fragen beantworten.
**Verwandt:** `08_versand-und-recht.md` · `09_sperrliste.md` · Skill `abmahnung-werbemail-abwehr` (Rechtsprechung, Bausteine, Beweissicherung)
**Stand:** Oktober 2026. **Keine Rechtsberatung.** Bei Klage, einstweiliger Verfügung oder hohen Beträgen einen Anwalt einschalten.

---

## Sofort (am selben Tag)

1. **Fristen notieren:**
   - Frist für die Unterlassungserklärung aus dem Schreiben.
   - Frist für eine DSGVO-Auskunft: ein Monat ab Zugang (Art. 15, Art. 12 Abs. 3).
2. **Zugang belegen:** Umschlag aufheben und die Sendungsverfolgung sichern. Läuft die Frist schon am Zugangstag ab, ist sie unangemessen kurz. Das gehört ins Antwortschreiben.
3. **Nichts unterschreiben, nichts zahlen,** bevor geprüft ist. Die beigelegte Unterlassungserklärung ist fast immer zu weit gefasst und enthält oft Zahlungspflichten.
4. **Absender sperren:** alle Domains und Adressen des Abmahners in allen Systemen (Versandtool, CRM, Lead-Listen, bei Dienstleistern) und Kanälen (Mail, LinkedIn, Telefon, Messenger). Laufende Sequenzen stoppen, nach Follow-ups suchen.
5. **Nicht anrufen, nicht diskutieren,** keine spontane Antwort-Mail mit Eingeständnissen. Nie aus dem Akquise-Postfach antworten.

## Die Linie: schnell bei der Unterlassung, fest beim Geld

- **Schnell:** Die eigene, modifizierte Unterlassungserklärung geht fristgerecht raus. Nur sie verhindert eine einstweilige Verfügung.
- **Fest:**
  - Im ersten Schreiben wird nichts gezahlt. Kosten gibt es erst nach Kostennote und Nachweis, dass der Abmahner seinen Anwalt zahlt oder zahlen muss.
  - Der Gegenstandswert wird geprüft und bei Überhöhung gerügt. Oft trägt schon das Urteil, das der Abmahner selbst zitiert, einen niedrigeren Wert.
  - Schadensersatz nach Art. 82 wird ohne dargelegten Schaden zurückgewiesen.
- **Nicht laut:** keine Drohungen, keine Wertungen, kein Rückfragen-Bombardement vor der Erklärung. Alle Nachweisforderungen stehen in **einem** Schreiben zusammen mit der Erklärung.
- **Nichts verraten:** keine Angaben zu Tools, Listen, Sequenzen oder Versanddomains, auch nicht im Briefkopf. Systematischer Versand treibt den Gegenstandswert und lädt zu Folgeabmahnungen ein.
- **Versand:** nie per Telefax, vorab nur per E-Mail. Bei GbR, Freiberuflern und Kleingewerbe muss das Original per Einschreiben folgen (Schriftform). Bei der GbR unterschreiben alle Gesellschafter.

## Mit dem Skill

Abmahnung als PDF in Claude legen: *„Ich habe diese Abmahnung wegen einer Werbe-Mail bekommen, bitte prüfen.“* Der Skill …

- gleicht den Abmahner mit der Sperrliste ab und zeigt Erfahrungswerte aus früheren Fällen,
- prüft Forderungen, Zitate, Kosten und den Entwurf der Unterlassungserklärung,
- recherchiert Kanzlei und Rechtsprechung am Gerichtsstand,
- lässt den Entwurf gegen einen simulierten Gegenanwalt antreten,
- erstellt Antwortschreiben und modifizierte Unterlassungserklärung als PDF,
- sichert auf Wunsch Rechtsverstöße auf der Website des Abmahners,
- meldet am Ende die Domains des Abmahners an die Sperrliste.

## Was meist gilt (Erfahrungswerte, keine Garantie)

| Forderung | Typische Lage |
|---|---|
| **Unterlassung** | meist begründet. Abgegeben wird eine **modifizierte** Unterlassungserklärung ohne Anerkennung einer Rechtspflicht und ohne Zahlungspflichten |
| **Schadensersatz nach Art. 82 DSGVO** | ohne konkret dargelegten Schaden kein Anspruch. Der bloße Erhalt einer Werbe-Mail genügt nach der BGH-Rechtsprechung nicht |
| **Auskunft nach Art. 15 DSGVO** | steht nur der betroffenen Person zu, nicht der abmahnenden Firma. Fristgerecht und vollständig erteilen. Ist die Person anwaltlich vertreten, Vollmacht anfordern, sonst verschlossen über die Kanzlei |
| **Anwaltskosten** | erst Kostennote und Zahlungsnachweis anfordern, Gegenstandswert rügen, dann auf begründeter Basis zahlen. Nie als „abgelehnt“ formulieren, das kann einen Zahlungsanspruch auslösen |

## Was man vermeiden muss

- **Gegendrohungen** wie „Wenn Sie weiter …, zeigen wir Ihre Website-Verstöße an“. Das kann als Nötigung oder Erpressung gewertet werden (§§ 240, 253 StGB) und macht eine Einigung anfechtbar.
- **Eingeständnisse**, z. B. „Die Adresse stand doch im Impressum“: Damit wird die Erhebung der Daten aus anderen Quellen eingestanden, was die Informationspflicht nach Art. 14 DSGVO auslöst.
- **Erkenntnisse aus der Sperrliste im Schreiben** („uns sind weitere Fälle bekannt“). Sie bleiben intern.
- **Vorschnelles Nachgeben:** zahlen, weil die Frist kurz ist oder der Betrag klein wirkt, oder den Entwurf der Gegenseite unterschreiben.

## Was die Akquise daraus lernt

- Keine frisch registrierten Versanddomains ohne Website und Impressum. Die Gegenseite prüft sie und nutzt sie für einen höheren Wert.
- Zwei Abmahnungen in wenigen Wochen sind ein Muster. Nach der ersten die Kampagne, die Liste und die Vorlagen prüfen.
- Wer selbst versendet, kann zusätzlich persönlich abgemahnt werden.
- Abmahner-Domains sofort in alle Sperrlisten und an die Community-Sperrliste (`09_sperrliste.md`).


---

<!-- Datei: wissen/11_zugaenge-und-kosten.md -->

# Zugänge und Kosten

**Zweck:** welche Konten und Schlüssel jeder Pfad braucht und wovon die Kosten abhängen.
**Für wen:** Nutzer vor der Einrichtung und vor großen Läufen.
**Verwandt:** `03_pfad-google-maps.md` · `04_pfad-amazon.md` · `05_pfad-recruiting.md` · `18_pfad-stellensuche.md` · `pfade/google-maps/docs/02_ZUGAENGE_UND_TOKENS.md`
**Stand:** 2026-11-01 · **Prüfen bis:** 2027-02-01. Preise der Anbieter ändern sich; aktuelle Tarife immer beim Anbieter prüfen (Skael: Werkzeug `get_pricing`, 1.000 Credits = 1 €).

---

## Je Pfad

| Pfad | Pflicht | Optional |
|---|---|---|
| **Google Maps** | Python ≥ 3.10; **Skael** (`SKAEL_API_KEY`, beginnt mit `eak_`); die KI-Schritte laufen standardmäßig über Skael (Schlüssel braucht `llm:invoke`) | **OpenAI** (`OPENAI_API_KEY`, beginnt mit `sk-`, **Guthaben vorher aufladen**) – Pflicht nur bei `LLM_PROVIDER=openai` oder `DOMAINSUCHE=openai`; Findymail (`FINDYMAIL_API_KEY`) als zweiter E-Mail-Finder |
| **Amazon** | Node.js ≥ 18; **Oxylabs** Web Scraper API (`OXYLABS_USER` / `OXYLABS_PASS`, API-Nutzer, nicht der Dashboard-Login); Python 3 nur für den Sperrlisten-Abgleich; bei E-Mail-Versand zusätzlich **Skael** (`SKAEL_API_KEY`) für die E-Mail-Prüfung | **Bright Data** (`BRIGHTDATA_TOKEN`) für E-Mail, Telefon, Register; Skael auch für Website, Geschäftsführung, Anrede (DE/AT/CH) |
| **Recruiting** (Firmen-Website) | wie Google Maps: Python ≥ 3.10, **Skael** (auch für die KI-Schritte) | wie Google Maps |
| **Stellensuche** (Jobportale) | Python ≥ 3.10, **Skael** (auch für die KI-Schritte); „nur Stellenliste“ braucht gar keine KI | wie Google Maps |
| **E-Commerce** | Shop-Liste als CSV; Python ≥ 3.10; **Skael** und **OpenAI** wie Google Maps | Findymail |
| **Videoseiten** | **Skael** mit Guthaben (110 Credits = 0,11 € je Video bis 2 Minuten); **Hostinger-VPS** (ab 5,49 €/Monat im Aktionszeitraum, danach 11,99 €) mit API-Schlüssel (`HOSTINGER_API_TOKEN`); eigene Domain; Zugänge in `pfade/videoseiten/.env` | eigene Video-Domain bei Skael; Buchungstool (Calendly kostenlos) |
| **Sperrliste** | nichts – öffentlich lesbar | – |
| **Abmahnungs-Skill** | Claude mit Code-Ausführung empfohlen | Zeitstempeldienste für die Beweissicherung |

Schlüssel gehören in die Datei `.env` im jeweiligen Pfad. Sie werden nie weitergegeben, nie in Screenshots gezeigt und nie eingecheckt.

## Wovon die Kosten abhängen

### Google Maps

```
Kosten ≈ (Suchbegriffe × Orte) × Maps-Suche
       + gefundene Firmen × Prüfung
       + passende Firmen × (Impressum + E-Mail-Suche + E-Mail-Prüfung + Website + KI-Texte)
```

- **Größter Hebel:** Mindest-Ortsgröße. Bei DACH reduziert „ab 20.000 Einwohner“ die Orte von ~10.200 auf ~900.
- **Zweiter Hebel:** Anzahl der Suchbegriffe. Eng anfangen.
- **Dritter Hebel:** Personalisierung und Videotitel abschalten, wenn sie nicht gebraucht werden.
- **Faustregel aus der Praxis:**
  - Ein Testlauf über drei Städte kostet wenige Cent bis Euro.
  - Ein Vollstart über DACH liegt im dreistelligen Bereich.
- Bei Skael kostet eine Maps-Suche ohne Treffer nichts; abgerechnet wird je gelieferte Ergebnisseite.

### Recruiting (Firmen-Website)

```
Kosten ≈ Google-Maps-Teil wie oben (Suchbegriffe × Orte, Prüfung je Firma)
       + passende Firmen × (1–3 Website-Abrufe + 1 KI-Aufruf)          ← Stellen-Erkennung
       + Firmen mit Stelle × (Impressum + E-Mail-Suche/-Prüfung + 3 KI-Aufrufe)
```

- Die Stellen-Erkennung läuft für **jede passende Firma**, auch die ohne Stelle. Ein strenges Prüfprofil spart hier am meisten.
- Startseiten werden einmal bezahlt und weiterverwendet (auch für die Sätze der NK-Strecke).

### Stellensuche (Jobportale)

```
Kosten ≈ Portale × Suchbegriffe × Orte × Seiten × 1 Credit              ← Anzeigen (bis 100 je Seite)
       + Firmen × 1 KI-Aufruf Größen-Check                               ← nur voller Lauf, ohne Skael-Credits für Datenabfragen
       + Firmen ohne Website im Portal, nach Größen-Check × ~15–25 Credits (find_domain)
       + Firmen mit Website × (Impressum + E-Mail-Suche/-Prüfung + 2 KI-Aufrufe)
```

- Eine Ergebnisseite mit bis zu 100 Anzeigen kostet 1 Credit. „Nur Stellenliste“ kostet deshalb fast nichts: 4 Portale × 3 Begriffe × 10 Orte × 3 Seiten sind höchstens 360 Credits (0,36 €).
- Im vollen Lauf ist die Website-Suche (`find_domain`, mit Impressum-Beleg) der größte Posten, weil Stepstone und Arbeitsagentur nur den Firmennamen nennen. Belegt kostet sie meist ~15 Credits, erfolglos 35–55.
- Der Größen-Check läuft **vor** der Website-Suche. Konzerne, öffentliche Hand und IT-Wettbewerber kosten dann keine `find_domain`-Suche mehr.
- Gemessene Kosten eines echten Laufs: `18_pfad-stellensuche.md`, Abschnitt „Quoten“.

### Kostenzähler (Google Maps, Recruiting, Stellensuche)

Das Scraper-Programm bucht die **echten Skael-Credits** jedes fertigen Auftrags in die Tabelle `kosten` der Kampagnen-Datenbank, getrennt je Dienst. `status` zeigt die Summe als „Skael-Kosten bisher“ (in Credits und Euro, ohne KI-Schritte). So lässt sich nach dem Testlauf hochrechnen, ohne Preise zu schätzen. Aufschlüsselung je Dienst: `pfade/google-maps/CLAUDE.md`, Abschnitt „Befehle“.

**Budget-Deckel:** `run --budget <€>` (und der Testballon) setzt eine harte Obergrenze für die Skael-Credits einer Kampagne (1.000 Credits ≈ 1 €). Ist sie erreicht, bleiben die restlichen Zeilen offen; ein späterer Lauf mit höherem Budget macht weiter. Laufende Aufträge werden noch fertig, deshalb kann das Budget um wenige Aufträge überschritten werden. KI-Schritte zählen nicht mit. Details: `pfade/google-maps/docs/09_TESTBALLON.md`.

### Amazon

```
Kosten ≈ Oxylabs-Abfragen × ~0,45 USD/1.000  +  Leads × Bright Data ~1,50 USD/1.000
       + Adressen × Skael 3 Credits (E-Mail-Prüfung)  +  DACH-Leads × Skael ~5–50 Credits (Website, Geschäftsführung)
Oxylabs-Abfragen ≈ ZIEL × Abfragen je Lead   (ohne Filter ~15–30, mit LAENDER=DE,AT,CH ~150–250)
```

- **Größter Hebel:** die Filter. Ein Länderfilter vervielfacht die Abfragen je Lead, weil die meisten Verkäufer aus China und Hongkong kommen und erst im Verkäuferprofil aussortiert werden.
- **Zweiter Hebel:** `SORTIMENT=0` spart die Sortimentsprüfung (etwa 5 statt 30 Abfragen je Lead), dann fehlen Umsatz, Produktzahl und Markenanteil.
- **Gedächtnis:** Was eine Kampagne schon geprüft hat, kostet die nächste nichts.
- **`BUDGET`** ist eine harte Obergrenze. Ein Lauf mit zu kleinem Budget liefert trotzdem die bis dahin gefundenen Leads.
- **Laufzeit:** je nach Dienst ~10–20 Abfragen pro Sekunde. 1.000 Leads ohne Filter dauern etwa 30–60 Minuten.

### E-Commerce

- **Stufe 1 (prüfen):** ~1 Cent je Shop. Website-Abruf, KI-Prüfung, Traffic nur bei aktiven Shops; Traffic ohne SimilarWeb-Daten ist kostenlos.
- **Stufe 2 (anreichern):** ~2–4 Cent je übergebenem Shop, wie Stufe 4 bei Google Maps.
- **Größter Hebel:** Die Traffic-Schwelle. Je höher sie liegt, desto weniger Shops kommen in die teurere Stufe 2.
- **Zweiter Hebel:** Websites schon in der Liste mitliefern. Die Website-Suche per Agent kostet extra.
- Einzelposten: `pfade/e-commerce/docs/01_PROZESS.md`.

### Findymail (optional, Google Maps und E-Commerce)

Zweiter Mailfinder für die Geschäftsführer-Adresse. Er wird nur gefragt, wenn der Skael-Mailfinder nichts findet. Bezahlt werden also nur die zusätzlichen Treffer.

- **Abrechnung:** 1 Finder-Credit je gefundener, von Findymail verifizierter Adresse. Ohne Treffer kostet die Suche nichts.
- **Tarif:** Abo, kein Kauf nach Verbrauch. Starter: 99 $ im Monat für 5.000 Finder- und 5.000 Verifier-Credits, also rund 2 US-Cent je Treffer (Herstellerseite). Andere Stufen stellt man über einen Regler ein; laut einer Drittquelle (09/2026) z. B. 49 $ für 1.000 bzw. 249 $ für 15.000 Credits. Vor dem Abschluss beim Anbieter prüfen.
- **Übertrag:** Ungenutzte Credits bleiben bis zum Doppelten des Monatskontingents erhalten (Herstellerseite).
- **Vergleich je gefundener Adresse:** Skael-Mailfinder 15 Credits plus Prüfung 3 Credits = 1,8 Cent. Findymail rund 2 US-Cent plus dieselbe Skael-Prüfung (0,3 Cent), wie in Clay.
- **Restguthaben:** zeigt der Befehl `doctor` im jeweiligen Pfad, kostenlos.

## Vor jedem großen Lauf

1. Testlauf (Google Maps: 3 Städte; Recruiting: 20–30 Firmen; Stellensuche: eine Suche je Portal; Amazon: Smoke-Test, dann 20–50 Leads mit den echten Filtern; E-Commerce: `--limit 10`).
2. Ergebnis prüfen und das Profil schärfen.
3. Kosten-Größenordnung nennen und Freigabe einholen.
4. Erst dann der Vollstart.


---

<!-- Datei: wissen/12_fehlerbehebung-faq.md -->

# Fehlerbehebung und häufige Fragen

**Zweck:** schnelle Antworten auf typische Probleme und Fragen.
**Für wen:** Nutzer und KI-Modelle, die Rückfragen beantworten.
**Verwandt:** alle Pfad-Dateien · `pfade/google-maps/docs/00_ANLEITUNG.md` (Abschnitt „Häufige Situationen“)

---

## Allgemein

**Welcher Pfad passt zu mir?**
Das klärt das Interview (`02`). Faustregel:

- Firma mit Adresse → Google Maps
- Händler oder Marke auf Amazon → Amazon
- Liste von Onlineshops → E-Commerce (`06`)
- Firmen, die Personal suchen, Branche bekannt → Recruiting über die Firmen-Website (`05`)
- Firmen, die einen bestimmten Beruf suchen → Stellensuche über Jobportale (`18`)

**Kann ich eine eigene Firmenliste anreichern lassen?**
Ja, für Firmen aus DE/AT/CH. Mit Firmenname (ideal mit Ort, Land und HR-Nummer) über die Anreicherung im Amazon-Pfad (`pfade/amazon/ABLAUF.md`, „Sonderfall“): Website, Impressum, Geschäftsführung, Anrede. Nötig ist nur ein Skael-Zugang. Hat die Liste eine E-Mail-Spalte, wird jede Adresse auf Zustellbarkeit geprüft (3 Credits je Adresse). Für die E-Mail-Suche gibt es dafür noch keinen eigenen Pfad.

**Warum fragt die KI so viel, bevor sie anfängt?**
Weil jede ungenaue Antwort Geld kostet. Ein falscher Suchbegriff oder ein zu weiches Profil verbraucht tausende Abfragen für die falschen Firmen.

**Warum heißt es so oft nur „Guten Tag“?**
Weil Name oder Geschlecht nicht sicher genug waren. Eine falsche persönliche Anrede schadet mehr als eine neutrale.

## Google Maps

| Problem | Ursache | Lösung |
|---|---|---|
| OpenAI-Aufrufe scheitern | kein Guthaben aufgeladen | bei OpenAI Zahlungsmittel hinterlegen und Guthaben aufladen |
| `doctor` meldet Platzhalter | `.env` nicht ausgefüllt | Schlüssel eintragen (die KI macht das) |
| kaum Firmen gefunden | Begriff zu speziell, Orte zu klein | Synonyme ergänzen, Ortsgröße prüfen |
| Prüfprofil lässt fast alles durch | Profil zu weich | mehr „sofort raus“, Region strenger; nur Stufe 3c neu |
| Prüfprofil filtert fast alles | Profil zu streng | Begründungen lesen, Muss-Kriterien lockern |
| ganze Zielgruppe verschwindet | `EXCLUDED_TLDS` trifft das Zielland | in `.env` leeren |
| Deutschland unvollständig | `CITIES_LIMIT=5000` | auf 10000 erhöhen |
| Export leer | nichts versandfertig, oder alles bereits exportiert | `export --all` zum Prüfen; `status` ansehen |
| Export bricht ab: Sperrliste | Liste nicht ladbar, keine lokale Kopie | Internet und `SPERRLISTE_URL` prüfen; nicht einfach abschalten |
| Lauf abgebrochen | Netz, Rechner, Rate-Limit | denselben `run`-Befehl erneut – er setzt fort |
| Wiederholung liefert dasselbe Fehlerergebnis | Skael liefert 20 Minuten lang aus dem Zwischenspeicher | 20 Minuten warten |

## Recruiting und Stellensuche

| Problem | Ursache | Lösung |
|---|---|---|
| „Diese Kampagne enthält schon einen Lauf vom Typ …“ | eine Kampagne hat immer nur eine Art (Google Maps, Recruiting oder Stellensuche) | eigene Kampagne anlegen: `./scraper.sh neue-kampagne <name>` |
| `run` verlangt einen OpenAI-Schlüssel | `LLM_PROVIDER=openai` oder `DOMAINSUCHE=openai` ist gesetzt | Schlüssel eintragen oder die Einstellung zurücknehmen; Standard ist die KI über Skael |
| Recruiting: kaum Firmen mit Stelle | gesuchte Berufe passen nicht (`--berufe`), oder die Stellen stehen nur auf externen Bewerberportalen | Berufe prüfen; branchengenauen Stellen-Prompt aus `pfade/google-maps/prompts/beispiele/` in die Kampagne kopieren; `KARRIERE_SEITEN` erhöhen; oder den Weg über die Jobportale nehmen (`18`) |
| Recruiting: passende Firmen fehlen in Liste 1/2 | keine offene Stelle erkannt, NK-Strecke aus | stehen in Liste 4. Mit `NK_ON=true` in `kampagne.env` (oder `init … --nk`), dann `run --stage 3d` und `--stage 4`, bekommen sie einen Satz zur Website |
| Opener nennt einen Bereich statt eines Berufs | die Stelle auf der Website heißt nur „Logistik“ o. Ä. | Stichprobe; branchengenaue Opener-Fassung aus `prompts/beispiele/` in die Kampagne kopieren |
| Stellensuche: viele fremde Stellen | Indeed und Stepstone suchen unscharf | `stellensuche --titel-pflicht "…"` bzw. `--titel-ausschluss "…"` setzen, dann nur `run --stage 1k` – kostet nichts |
| Stellensuche: bekannter Konzern in der Lead-Liste | Größen-Check abgeschaltet, oder das Modell kennt die Firma nicht („unbekannt“) | Liste sichten; `groessen_check.txt` schärfen und nur den Größen-Check neu laufen lassen (`pfade/stellensuche/ABLAUF.md`, Phase 5) |
| Stellensuche: IT-Firmen fehlen | der Größen-Check sortiert „IT-Wettbewerber“ aus – gedacht für Angebote rund um IT/KI | bei anderen Angeboten `stellensuche --no-groessen-check` |
| Stellensuche: viele Firmen ohne Website | Stepstone und Arbeitsagentur nennen nur den Firmennamen; `find_domain` belegt nur Domains mit passendem Impressum | erwartbar (gemessen ≈ 75–80 % belegt); der Rest steht in Liste 4 mit „keine eigene Website gefunden“ |
| `python3 -m scraper` meldet „Python 3.10 oder neuer nötig“ | macOS liefert 3.9 aus | `./scraper.sh …` (sucht selbst ein passendes Python) oder `python3.12 -m scraper …` |

## E-Commerce

| Problem | Ursache | Lösung |
|---|---|---|
| Import erkennt keine Spalten | Spaltennamen unbekannt | `--name-spalte` bzw. `--website-spalte` angeben |
| Lauf stoppt: „Anforderung fehlt“ | Shop-Profil nicht entschieden, oder Mailtext bzw. Anweisung für den persönlichen Satz fehlen. Der Pfad startet dann bewusst nicht; es entstehen keine Kosten | `python3 -m ecom status` zeigt im Block „Anforderungen“, was fehlt, und nennt den Builder. Fehlendes mit dem Nutzer klären (`pfade/e-commerce/ABLAUF.md`, Phase 1), dann denselben `run`-Befehl erneut |
| Mailtext wird abgelehnt | meist ein Tippfehler in einem Platzhalter oder die Begrüßung bzw. `{{Personalisierung}}` steht nicht oben. Alle Fehler und Hinweise: `07_lead-ausgabe-und-spalten.md`, Abschnitt E-Commerce, „Was `set-mailtext` prüft“ | Schreibweise aus der Platzhalter-Tabelle dort übernehmen, dann `set-mailtext` erneut |
| viele Shops „kein messbarer Traffic“ | kleine Shops haben keine SimilarWeb-Daten | erwartbar; wer sie trotzdem will: beide Traffic-Schwellen auf 0, dann `run --stage 1e` |
| „Website ohne Text“ | Shop baut die Seite nur per JavaScript auf oder blockt Abrufe | in Liste 3 von Hand prüfen |
| weniger Leads als übergebene Shops | Duplikate (gleiche E-Mail-Domain) oder kein Impressum/keine E-Mail | Liste 3 zeigt den Grund je Shop |
| Lauf abgebrochen | Netz, Rechner, Rate-Limit | denselben `run`-Befehl erneut – er setzt fort |

## Amazon

| Problem | Ursache | Lösung |
|---|---|---|
| `node: command not found` / „Node … ZU ALT“ | Node.js fehlt oder ist älter als 18 | Node.js LTS von nodejs.org installieren, Terminal bzw. App neu starten |
| „Oxylabs-Zugang fehlt“ | `.env` fehlt oder ist leer | `pfade/amazon/.env.example` als `.env` kopieren und selbst ausfüllen |
| „Oxylabs: abgelehnt (HTTP 401/403)“ | falscher API-Nutzer, oft der Dashboard-Login | Benutzer und Passwort des **API-Nutzers** eintragen |
| „HTTP 402“ / „traffic limit“ | Oxylabs-Guthaben bzw. Abo leer | aufladen, dann denselben Befehl erneut – er setzt fort |
| „Budget erreicht“ | harte Obergrenze erreicht | mit höherem `BUDGET` fortsetzen; gefundene Leads sind schon exportiert |
| „Alle Listen ausgeschöpft“ | Neuheiten-Listen der gewählten Kategorien sind durch | Unterkategorien ernten (`ernter_unterkategorien.mjs`, dann `SUB_SEITEN=5`) oder Suchbegriffe ergänzen |
| fast nur Leads aus China/Hongkong | ohne Länderfilter normal | `LAENDER=DE,AT,CH` setzen; Budget dann deutlich höher (`11`) |
| wenige Geschäftsführer | ohne Skael nur aus dem Verkäuferprofil (~13–36 %) | Skael-Zugang eintragen; die Anreicherung findet sie für DACH-Firmen |
| „Leads warten noch auf Kontaktdaten“ | Bright Data war noch nicht fertig | später denselben Befehl erneut, bereits bezahlt |
| `E-Mail Status` = `Not Run` | die E-Mail-Prüfung lief nicht (kein Skael-Schlüssel, Abbruch, Störung bei Skael, `EMAIL_PRUEFUNG=0`) | Schlüssel eintragen und `anreicherung.mjs` erneut starten. Eine Adresse wird höchstens in 3 Starts geprüft, danach einmal mit `ERNEUT_VERSUCHEN=1`. Ungeprüfte Adressen nicht per E-Mail anschreiben |
| „Skael liefert seit 10 Abfragen in Folge kein Ergebnis“ | Skael oder das Internet ist gestört | innerhalb von 24 Stunden erneut starten; der Stand ist gespeichert, schon abgeschickte Abfragen werden dann nicht noch einmal berechnet |
| „Skael lehnt alle Anfragen an … ab“ | Schnittstelle geändert oder `SKAEL_URL` falsch | nicht wiederholen, nichts wurde berechnet; an den Betreiber des Pakets melden |

## Sperrliste und Recht

**Darf ich nach dem Abgleich bedenkenlos versenden?**
Nein. Der Abgleich entfernt bekannte Abmahner. E-Mail-Werbung ohne Einwilligung bleibt grundsätzlich unzulässig (`08`).

**Eine Firma auf der Sperrliste ist ein Wunschkunde – was tun?**
Nicht anschreiben, über keinen Kanal. Wer eine Abmahnung ausgesprochen hat, will keinen Kontakt.

**Ich wurde abgemahnt – muss ich melden?**
Ja, das ist die Bedingung der Nutzung. Der Abmahnungs-Skill erledigt das automatisch und zeigt vorher, was gesendet wird.


---

<!-- Datei: wissen/13_glossar.md -->

# Glossar

**Zweck:** Begriffe aus Dokumentation, Code und Gespräch – kurz erklärt.
**Für wen:** alle.

---

| Begriff | Bedeutung |
|---|---|
| **Abmahnung** | Aufforderung, ein Verhalten zu unterlassen, meist mit Unterlassungserklärung und Kostenforderung (`10`) |
| **Anrede-Confidence** | Sicherheit (0–100), dass der **Vorname** männlich bzw. weiblich ist; ≤ 60 → neutrale Ansprache |
| **Art. 14 DSGVO** | Informationspflicht, wenn Daten nicht bei der Person selbst erhoben wurden – spätestens bei der ersten Kontaktaufnahme |
| **Art. 15 DSGVO** | Auskunftsrecht; Frist ein Monat |
| **Art. 82 DSGVO** | Schadensersatz bei Datenschutzverstoß; setzt einen konkreten Schaden voraus |
| **Auftragsdatei** | Markdown-Datei mit allen Interview-Antworten in `auftraege/`; der Pfad liest sie und fragt nur, was fehlt |
| **Bestätigt** (Sperrliste) | mindestens zwei unabhängige Meldungen zur selben Domain |
| **Buy-Box** | das Angebot, das bei Amazon beim „In den Einkaufswagen“-Knopf gewinnt; ihr Inhaber ist der Verkäufer, den der Amazon-Pfad prüft |
| **Catch-all** | Mailserver, der jede Adresse annimmt; Status `Risky` – Zustellung ungewiss |
| **Dedupe** | Entfernen doppelter Firmen, hier über die Domain |
| **GF / GF Confidence** | Geschäftsführung; Sicherheit, dass die **Firma** richtig zugeordnet ist (`sicher`/`unsicher`) |
| **Größen-Check** | Stellensuche, Stufe 3g: Die KI stuft jede Firma aus ihrem Modellwissen ein; Konzerne, öffentliche Hand/Verbände und IT-Wettbewerber fallen vor der bezahlten Website-Suche heraus (Liste 4). Abschaltbar mit `--no-groessen-check` (`18`) |
| **HR-Nummer** | Handelsregisternummer, z. B. „Amtsgericht Ulm HRB 123456“; Anker gegen gleichnamige Firmen |
| **ICP / Prüfprofil / Wunschkundenprofil** | Beschreibung des idealen Kunden, gegen die jede Website geprüft wird |
| **Kampagne** (Amazon) | Name eines Laufs (`KAMPAGNE=…`); trennt Lieferliste und Ergebnisse, das Gedächtnis teilen sich alle Kampagnen |
| **Kampagne** (Scraper-Programm) | eine Zielgruppe unter `pfade/google-maps/kampagnen/<name>/` mit eigener `kampagne.env`, eigenen Prompts, Datenbank und Exporten; hat genau eine Art: Google Maps, Recruiting oder Stellensuche |
| **Karriere-Seite** | Seite der Firmen-Website mit Stellenangeboten; die Stellen-Erkennung im Recruiting liest bis zu zwei davon |
| **Kostenzähler** | Tabelle `kosten` in der Datenbank einer Kampagne: echte Skael-Credits je Dienst, wie Skael sie abrechnet; `status` zeigt die Summe als „Skael-Kosten bisher“ (ohne KI-Schritte) |
| **Keyword / Suchbegriff** | Begriff für die Google-Maps-Suche; jeder zusätzliche Begriff vervielfacht die Kosten |
| **Mailtext (Vorlage)** | die Werbe-Mail des Nutzers: erste Zeile `Betreff: …`, dann der Text mit Platzhaltern. Im E-Commerce-Pfad wird sie je Lead gefüllt und steht im Export in den Spalten `Betreff` und `Mailtext` (`07`). Aus Angebot und Mailtext entsteht die Anweisung für den persönlichen Satz |
| **Match-Status** | wie sicher die gefundene Website zur Firma gehört: über das Impressum bestätigt (`register`, `ustid`, `firmenname`, `telefon`, `email`) oder nur vermutet (`domain`, `email-domain`) |
| **Modifizierte Unterlassungserklärung** | selbst formulierte, enger gefasste Erklärung ohne Schuldanerkenntnis und ohne Zahlungspflichten |
| **Oxylabs** | Scraping-Dienst, über den der Amazon-Pfad die amazon.de-Seiten abruft; rechnet je Abfrage ab |
| **Pfad** | eine Lead-Quelle mit eigenem Ablauf: Google Maps, Amazon, E-Commerce, Recruiting (Firmen-Website), Stellensuche (Jobportale) |
| **Platzhalter** | Stelle in einer Vorlage in doppelten geschweiften Klammern, z. B. `{{Firmenname}}`, die je Lead durch den passenden Wert ersetzt wird. Die Schreibweise muss genau stimmen; unbekannte Platzhalter lehnt der E-Commerce-Pfad ab (`07`, `12`) |
| **RC / NK** | die zwei Strecken im Recruiting: RC = Firma mit erkannter offener Stelle (Opener zur Stelle), NK = passende Firma ohne erkannte Stelle (Satz zur Website; nur mit `--nk`) |
| **Ready to Send / versandfertig** | E-Mail vorhanden (und Personalisierung/Videotitel, wenn eingeschaltet) |
| **Relay** | kleiner Webdienst des Betreibers, der Meldungen an die Sperrliste annimmt und ins Repository schreibt |
| **Safe to Send / Risky / Unknown / Invalid / Not Run** | Ergebnis der E-Mail-Prüfung: zustellbar / Catch-all / nicht prüfbar / ungültig (nie anschreiben) / nicht geprüft (nicht per E-Mail anschreiben) |
| **SEND / Traffic-Filter** | E-Commerce Stufe 1e: Ein Shop geht nur in die Anreicherung, wenn SimilarWeb Besuche misst (Schnitt bzw. Höchstwert ≥ Schwelle, Standard 1) |
| **Seller ID / Storefront** | Amazon-Verkäuferkennung; Link auf alle Angebote eines Verkäufers |
| **Shop-Profil** | E-Commerce: Beschreibung, welche aktiven Shops zum Kunden passen (Region, Sortiment, Ausschlüsse). Die KI prüft jede Startseite dagegen (Stufe 1c); nicht passende Shops kommen mit Grund in Liste 3. Gegenstück zum Prüfprofil im Google-Maps-Pfad. „Bewusst ohne“ = jeder aktive Shop zählt (`06`) |
| **Skael** | Dienst für Google-Maps-Suche, Impressum, E-Mail-Suche und -Prüfung, Website-Abruf |
| **Sperrliste** | Community-Liste von Domains, die nicht angeschrieben werden (`09`) |
| **Stellen-Erkennung** | Recruiting, Stufe 3e: Die KI liest Startseite und Karriere-Seiten der Firma und gibt genau eine passende offene Stelle zurück |
| **Stellensuche** | Pfad, der konkrete Anzeigen per Suchbegriff aus Jobportalen holt (Indeed, Stepstone, Arbeitsagentur, Kununu) und je Firma bündelt |
| **Stufe 1–4 / 3c** | Abschnitte des Google-Maps-Ablaufs; 3c = Prüfung gegen das Profil |
| **Testlauf (Dry-Run)** | kleiner Lauf über wenige Städte bzw. 20–50 Amazon-Leads, um Profil, Filter und Kosten zu prüfen |
| **UWG § 7** | Verbot unzumutbarer Belästigung; E-Mail-Werbung nur mit vorheriger ausdrücklicher Einwilligung |
| **Welle** (Amazon) | Abschnitt eines Laufs: Jede Stufe holt nur, was die nächste für das Lead-Ziel noch braucht |
| **Widerspruch** | Gelistete Firma verlangt Entfernung von der Sperrliste – wird dauerhaft entfernt |


---

<!-- Datei: wissen/14_neuen-pfad-anlegen.md -->

# Einen neuen Pfad anlegen (z. B. Recruiting, E-Commerce)

**Zweck:** wie ein weiterer Pfad so eingebaut wird, dass Interview, Wissen, Ausgabe und Sperrliste für alle gleich funktionieren.
**Für wen:** Betreiber, Entwickler und KI-Modelle, die einen Pfad bauen (z. B. Claude Code).
**Verwandt:** `pfade/_vorlage/README.md` (Pflichtenheft) · `02_zielgruppen-interview.md` · `07_lead-ausgabe-und-spalten.md`

---

## Vorgehen

1. **Zielbild schärfen** in `wissen/NN_pfad-<name>.md`:
   - Wer ist der Lead?
   - Woher kommen die Daten?
   - Was darf man mit diesen Daten tun?

   Die offenen Entscheidungen dort festhalten (siehe `05`/`06`).
2. **Quelle prüfen:**
   - Nutzungsbedingungen, Kosten, API statt Scraping wo möglich.
   - Personenbezug der Daten.
   - Ergebnis im Abschnitt „Rechtliches“ der Wissensdatei.
3. **Ordner anlegen** nach `pfade/_vorlage/README.md`: `ABLAUF.md`, `README.md`, `scripts/`, `referenzen/`.
4. **Wiederverwenden statt neu bauen:**

   | Baustein | Wiederverwenden aus |
   |---|---|
   | Prüfprofil (Website gegen Wunschkunden) | Google Maps, Stufe 3c / Skael `icp_checker` |
   | Impressum, E-Mail-Suche, E-Mail-Prüfung | Google Maps, Stufe 4 / Skael-Endpunkte |
   | Website, Impressum, Geschäftsführung zu einer Firmenliste (mit Abgleich über Register, USt-IdNr., Firmenname) | Amazon `anreicherung.mjs` (liest jede CSV mit Spalte `Firma`/`Firmenname`) |
   | Anrede- und Ansprache-Regeln, Standardfelder | Amazon `anreicherung.mjs` und `standardformat.mjs` |
   | Sperrlisten-Abgleich | `werkzeuge/sperrliste_abgleich.py` |

5. **Interview erweitern** in `wissen/02_zielgruppen-interview.md`:
   - Antwortmöglichkeit in Block C,
   - Zeile in „Entscheidung“,
   - Spalte in „Übersetzung der Antworten“.

   Zusatzfragen nur für diesen Pfad gehören in seine `ABLAUF.md` und werden erst nach der Pfadwahl gestellt.
6. **Ausgabe im Standardformat** (`07`), letzte Phase immer der Sperrlisten-Abgleich.
7. **Testen:** ein kleiner echter Lauf und eine Stichprobe von 5–10 Datensätzen, die von Hand geprüft werden. Die gemessenen Quoten in die Wissensdatei eintragen.
8. **Freischalten:**
   - Status in `wissen/02` auf „verfügbar“ setzen.
   - Pfadtabelle in `SKILL.md` ergänzen.
   - Eintrag in `wissen/00_INDEX.md`.
   - `python3 werkzeuge/wissen_pruefen.py` ohne Fehler.
   - Skill-ZIP neu bauen (macht der Betreiber beim nächsten Paketstand).
   - Eintrag in `CHANGELOG.md`.

## Prompt für Claude Code zum Start

> Lies `lead-scraper/CLAUDE.md`, `wissen/14_neuen-pfad-anlegen.md`, `pfade/_vorlage/README.md` und `wissen/NN_pfad-<name>.md`. Baue den Pfad `<name>` nach dem Pflichtenheft. Kläre zuerst mit mir die offenen Entscheidungen aus der Wissensdatei, eine Frage pro Nachricht. Nutze die vorhandenen Bausteine, statt sie neu zu bauen.


---

<!-- Datei: wissen/15_learnings-architekturbueros-2026-10.md -->

# Learnings aus der Kampagne Architekturbüros DACH (Oktober 2026)

**Zweck:** Erkenntnisse aus einem echten Lauf, damit der nächste Lauf günstiger, schneller und sauberer wird.
**Für wen:** Betreiber, Nutzer und KI-Modelle, die den Google-Maps-Pfad bedienen.
**Verwandt:** `02_zielgruppen-interview.md` · `03_pfad-google-maps.md` · `09_sperrliste.md` · `11_zugaenge-und-kosten.md` · `12_fehlerbehebung-faq.md`

---

## 1. Kosten

### Gemessene Skael-Kosten pro Schritt
Messung über den Kontostand vor und nach jedem Schritt (Bamberg + Passau, 62 fertige Leads, 1.185 Credits):

| Schritt | Preis laut Skael | Credits je fertigem Lead | Anteil |
|---|---|---|---|
| Städteliste | 10 je Land | – | – |
| Maps-Suche | 2 je Seite (bis 200 Treffer) | 0,1 | 1 % |
| ICP-Check | 2 direkt / 4 Proxy | 3,7 | 19 % |
| Impressum | 5 direkt / 10 Proxy / 0 ohne Treffer | 4,9 | 26 % |
| E-Mail finden | 15 gültig / 5 riskant / 0 nicht gefunden | 5,2 | 27 % |
| E-Mail prüfen | 3 pauschal | 3,0 | 16 % |
| Website-Text | 2 direkt / 5 Proxy | 2,0 | 10 % |
| **Summe** | | **≈ 19 Credits ≈ 1,9 Cent** | |

- Der ICP-Check kostet je Lead mehr als je Aufruf, weil nur ein Teil besteht (55 % in mittleren Städten, 75 % in Großstädten).
- Skael ist pro Lead günstig. Teuer wird es nur über die **Menge**.
- Der Kontostand je Organisation lässt sich über das Skael-MCP (`whoami` mit `organization`) abfragen. So lässt sich jeder Schritt messen, bevor der große Lauf startet.
- Das in `whoami` angezeigte Tageslimit (5.000 Credits) galt nicht für Aufrufe über den API-Schlüssel.

### OpenAI-Kosten (gemessen, ca. 2.100 Token Eingabe je Einstiegssatz)
| Modell | je Lead |
|---|---|
| gpt-4o-mini | 0,03 Cent |
| gpt-4.1-mini | 0,09 Cent |
| gpt-4.1 | 0,35–0,46 Cent |

- **Kostenfalle Domainsuche:** Die KI-Domainsuche für Firmen ohne Website lief mit OpenAI-Websuche. Das kostet ca. 1 Cent pro Firma, unabhängig vom Modell. Bei 4.177 Firmen ohne Website waren das rund 40 € und damit mehr als der ganze Rest. In Clay steckt derselbe Schritt (Claygent) unsichtbar in den Clay-Credits.
  → Für Kampagnen abschaltbar über `DO_DOMAINSUCHE=false`. Standard soll künftig Skael sein (`find_domain`, über das Impressum bestätigt, 15–35 Credits), alternativ ganz aus.

### Mengen realistisch schätzen
- DACH ab 50.000 Einwohnern: 268 Orte × 2 Suchbegriffe ergaben **21.000 Firmen**. Geschätzt waren 6.000–10.000.
- Die beiden Suchbegriffe „Architekturbüro“ und „Architekt“ überschneiden sich zu rund 45 %. „Architekt“ bringt viele zusätzliche Treffer, aber auch Fremde (z. B. Raumausstatter).
- **Immer von der Zielmenge rückwärts rechnen**, nicht vom Markt: Zielmenge × ca. 2 Cent (Skael) + Einstiegssatz-Kosten. Den Rest der gefundenen Firmen zurückstellen (`dedupe_status='deferred_menge'`) und bei Bedarf nachziehen.

## 2. Ablauf und Interview

- **Die Mengenfrage (Interview D4) nie überspringen.** Ohne Zielmenge reichert der Scraper alles an, was die Prüfung besteht. Hier wären das 13.000 Leads gewesen, gebraucht wurden 3.000–4.000.
- Vor jedem großen Lauf **jeden Schritt an 2 Städten messen**. Dafür Städte nehmen, die noch nicht abgefragt wurden, sonst verfälscht der Skael-Cache (20 Minuten) die Kosten.
- Skael-Warteschlange kann zeitweise stocken (Aufträge minutenlang `queued`). Nach dem Lauf einen zweiten Durchgang `run --stage 4` einplanen, er holt Ausreißer nach.
- Lange Läufe unabhängig von der Sitzung starten (`nohup caffeinate -i …`). Läufe sind fortsetzbar.
- Stufe 4 hat kein `--limit`. Eine Stichprobe läuft über eine Kopie der Datenbank (`DB_PATH=data/probe.db`).

## 3. Blockliste vs. Community-Sperrliste

- **Bereits kontaktierte Firmen gehören nie auf die Community-Sperrliste.** Die ist öffentlich und nur für Abmahner gedacht. Für Alt-Leads gibt es die private Blockliste: `python3 -m scraper blockliste-import <csv>`.
- Freemail-Domains werden nicht gesperrt, sondern nur die einzelne Adresse. Spalten mit Absenderadressen (z. B. `last_contacted_from`) werden beim Import ignoriert.
- Die Blockliste greift vor dem ICP-Check, das spart Credits. Sie hat 181 von 21.000 Firmen ausgeschlossen.
- Steht in `SPERRLISTE_URL` noch der Platzhalter `OWNER`, bricht der Export ab. Dann bewusst `SPERRLISTE_PFLICHT=false` setzen und das dokumentieren.

## 4. Behobene Fehler im Paket

| Problem | Folge | Lösung |
|---|---|---|
| Websuche über Chat Completions (`web_search_preview`) | HTTP 400, Domainsuche fand nie etwas | Responses-API mit Tool `web_search` |
| Maps liefert Unterseiten (`/impressum.php`, `/kontakt`) | ICP-Check: „nicht erreichbar“ (ca. 6 %) | auf die Startseite kürzen |
| Instagram-/Facebook-Links als Website | alle fielen beim Dedupe auf einen Eintrag zusammen | gelten als „keine Website“ |
| Ausweich-Kategorie „Lead Gen“ fest im Code | passte nur zur Großhandels-Vorlage | `KATEGORIE_NORMALFALL` |
| Domainsuche nur mit Firmennamen | Fehltreffer bei Allerweltsnamen | Stadt wird mitgesucht |
| Dedupe setzt jeden Status zurück | Zurückstellungen gingen verloren | `deferred_menge` bleibt erhalten |
| OpenAI-Guthaben mitten im Lauf leer | Ausfall der KI-Schritte | `OPENAI_API_KEY_FALLBACK`, automatischer Wechsel |
| Mac-System-Python 3.9 | Scraper startet nicht | Homebrew `python3.12` |
| Skael-Standardmodus ist synchron mit Herzschlag (bis 1 h je Anfrage) | Lauf hing stundenlang bei 0 % CPU, unser Zeitlimit griff nie | `async=true` + Abholen über `GET /api/enrichments/{id}?wait=true&wait_time=50`, Frist `SKAEL_MAX_WARTEZEIT` |
| Abholen unter `/api/<endpunkt>/{id}` | 404, Auftrag wurde neu eingereicht | richtige URL `/api/enrichments/{id}`; dazu `Idempotency-Key` (24 h, nie doppelt berechnet) |
| Schlüsselwechsel bei leerem OpenAI-Guthaben (`credit_balance_exhausted`) | parallele Anfragen scheiterten, bevor der Wechsel griff (bis zu 11 Leads je Neustart) | sofort wechseln; noch mit dem alten Schlüssel gesendete Anfragen werden mit dem Ersatz wiederholt |
| Abgerissene Antworten (`IncompleteRead`) | Zeile übersprungen statt wiederholt | `http.client.HTTPException` als Netzwerkfehler behandeln → Wiederholung |

## 5. Prüfprofil (ICP)

- Die erste Fassung war zu streng: Büros flogen wegen der Rechtsform (PartG mbB, Planungsgesellschaft), einzelner Auslandsprojekte oder Zusatzleistungen (Innenarchitektur, Energieberatung) raus.
  → Eine Zeile **„KEIN AUSSCHLUSSGRUND“** im Prompt hat das behoben (Absagen von 118 auf 104 von 435).
- Bei Ausschlüssen immer „als Hauptgeschäft“ formulieren, sonst fliegen Mischbüros raus.
- Richtig aussortiert wurden: Galerien und Foren (Aedes, DAZ), Makler bzw. Projektentwickler, Büros mit über 50 Mitarbeitenden.
- Rund 5 % der Websites liefern kaum Text (reine JavaScript-Seiten, Baustellenseiten) und sind nicht prüfbar.

## 6. Einstiegssatz (Personalisierung)

- **Den Prompt für seinen tatsächlichen Platz in der Mail bauen.** Hier ist das: „Beim Blick auf Ihre Website ist mir aufgefallen, [Satz] Gleichzeitig hatte ich den Eindruck …“. Daraus folgt:
  - Beginn mit „dass“ oder „wie“, genau ein Satz, höchstens 25 Wörter,
  - reine Beobachtung ohne Deutung am Ende, weil die Deutung im Folgesatz steht,
  - keine Überschneidung mit dem Folgesatz (Website, Empfehlungen, Netzwerk, Fachkräfte).
- **Bei dünnen Websites hilft kein Modell.** Lieber einen leeren Satz zurückgeben und im Export den Standardabsatz einsetzen (Spalte „Absatz Beobachtung“). Das betrifft etwa 40 % der Büros.
- Ist die Detailregel zu streng, bleiben zu viele leer (9 von 15). „Eine klar benannte Bauaufgabe oder ein Schwerpunkt genügt“ ergab 9 von 15 mit Satz, leer blieben genau die dünnen Seiten.
- Modellvergleich an 15 Büros:
  - **gpt-4o-mini** ignoriert die Verbotsliste (Engagement, spannend, anspruchsvoll).
  - **gpt-4.1-mini** macht vereinzelt schädliche Aussagen („zurückhaltende Auftragslage“).
  - **gpt-4.1** schreibt am verlässlichsten.
  - Bei 3.000–4.000 Leads liegt der Unterschied unter 15 $.
- Platzhaltertexte auf Websites („Referenz4“) ausdrücklich ausschließen.
- Die Einordnung **Fachkräfte/Projekte** (sichtbare Stellenanzeige) funktioniert, etwa 15 % der Büros suchen Personal. Für diese Gruppe passt eine eigene Mailvariante.

### Ergebnis im Lauf (3.088 Leads)
- 59 % mit konkretem Satz, 41 % Standardabsatz.
- Die Schlusskontrolle hat in 15 von rund 1.840 Sätzen echte Floskeln gefunden (spannend, anspruchsvoll, innovativ, Fokus, Lösungen) und sie durch den Standardabsatz ersetzt.
- Eine Wortliste allein ist zu grob: Eigennamen („Kompetenzzentrum“, „ICONIC AWARD … Innovative Materialien“) und Stellenanzeigen („fünf Jahre Berufserfahrung“) sind keine Floskeln. Treffer vor dem Ersetzen ansehen.

## 7. Mailvorlage

- Den Absatz nicht selbst zusammensetzen, sondern die fertige Spalte „Absatz Beobachtung“ einsetzen.
- Für die Anrede „Ansprache Normal“ nutzen statt „Hallo {Anrede} {Nachname}“. Sonst entsteht bei info@-Adressen „Hallo  ,“.
- Beim Wechsel der Zielgruppe alle Branchenbegriffe in der Vorlage anpassen (hier: „speziell für Ingenieurbüros entwickelt“).

## 8. E-Mail-Qualität

- Bei kleinen Büros landen rund 85 % der Adressen auf „Unknown“, weil deren Mailserver jede Adresse annehmen (Catch-all). Diese Adressen langsam hochfahren oder in eigenen Paketen versenden.
- Die E-Mail-Suche bestätigt manche Adressen schon als „gültig“. Die anschließende Prüfung (3 Credits) ist dann doppelt. Clay macht das genauso. Mögliche Ersparnis: ca. 0,6 Credits je Lead.

## 9. Vergleich mit der Clay-Vorlage „GMAPS 2.5 | ICP Checker“

- Die Abläufe sind identisch: Städte → Maps → Dedupe (inkl. .fr/.nl/.it) → ICP → Impressum → Mailfinder → Verify → Webscraper → Anrede, Einstiegssatz, Videotitel.
- Unterschiede gibt es nur bei den KI-Schritten:
  - Clay sucht Domains mit Claygent (gpt-4o-mini bzw. gemini-2.5-flash-lite) und rechnet über Clay-Credits ab.
  - Clay erzeugt den Einstiegssatz mit gpt-4o-mini in einem einzigen Aufruf.
- Telefon- und LinkedIn-Anreicherung sind in Clay eingebaut, aber abgeschaltet.
- **Vorgabe für das Paket:** Alle KI-Schritte und die Domainsuche laufen standardmäßig über Skael, weil die Rate-Limits einzelner ChatGPT-Konten oft nicht reichen. OpenAI bleibt als optionaler Schalter.


---

<!-- Datei: wissen/16_videoseiten.md -->

# Videoseiten – persönliches Video und eigene Landingpage je Lead

**Zweck:** Wissen zum Pfad `pfade/videoseiten/`: was entsteht, was es kostet, was der Nutzer selbst tun muss, wie die Vorlage aufgebaut ist und was rechtlich zu beachten ist.
**Für wen:** Nutzer mit Rückfragen und KI-Modelle, die den Ablauf (`pfade/videoseiten/ABLAUF.md`) begleiten.
**Verwandt:** `02_zielgruppen-interview.md` (Blöcke V und L) · `07_lead-ausgabe-und-spalten.md` (Lead-Format) · `08_versand-und-recht.md` · `11_zugaenge-und-kosten.md`

---

## Was entsteht

Für jeden Lead mit Website:

1. ein **persönliches Video** bei Skael: das Grundvideo des Nutzers, in dem die Website des Leads eingeblendet wird,
2. eine **eigene Seite** unter `https://angebot.<domain-des-nutzers>/v/<zufällige-kennung>/` im Branding des Nutzers: persönliche Überschrift, Video, Angebot, Kundenstimmen, Fragen, Termin-Knopf, Datenschutz-Information,
3. eine **Versandliste** mit dem Link zur Seite und einem Vorschaubild für die Mail.

Die Seite ist bis zum Klick auf Abspielen gesperrt: Man sieht nur Überschrift, Unterschrift, Video und die Rechtslinks. Nach dem Klick zoomt das Video groß, danach baut sich der Rest beim Scrollen auf. „Ohne Video weiterlesen“ öffnet die Seite, ohne das Video zu laden.

## Wer macht was

| Schritt | Agent | Nutzer |
|---|---|---|
| Branding, Impressum, Texte | liest die Website, schlägt vor, baut die Seite | bestätigt, liefert Foto und Termin-Link |
| Grundvideo | prüft die Kampagne (Aufnahme, Länge, Screenshot-Teil) | nimmt das Video in Skael auf (`anleitungen/01_…`) |
| Videos je Lead | legt an, wartet, führt zusammen | sagt Ja zu den Kosten, sieht das Testvideo an |
| Server | richtet alles per Hostinger-API ein | kauft den VPS, erzeugt den API-Schlüssel (`anleitungen/02_…`) |
| Domain | setzt den Eintrag, wenn die Domain bei Hostinger liegt | sonst den A-Record beim eigenen Anbieter (`anleitungen/03_dns.md`) |
| Versand | erstellt die Liste mit Links | importiert ins Mailtool (`anleitungen/06_mailtool.md`), passt die Datenschutzerklärung an (`anleitungen/05_…`) |

## Kosten

| Posten | Preis | Quelle |
|---|---|---|
| Video bis 2 Minuten | 110 Credits = 0,11 € | Skael-Doku „Create Prospect“ |
| je weitere angefangene Minute | 55 Credits | dto. |
| Staffel nach Videos der letzten 60 Tage | ab 1.000: 80 · 2.000: 70 · 4.000: 65 · 10.000: 55 · 14.000: 40 Credits | dto. |
| fehlgeschlagene Videos | werden erstattet | dto. |
| Hostinger VPS KVM 1 | ab 5,49 €/Monat im Aktionszeitraum, Verlängerung 11,99 €/Monat (Stand 2026-10) | hostinger.com |

Beispiel: 500 Leads mit einem 1:50-Minuten-Video = 55.000 Credits = 55 €. Mit 2:16 Minuten wären es 82,50 €.

## Vorlage

`pfade/videoseiten/vorlage/index.html`. Der Agent arbeitet immer auf einer Kopie in `arbeit/<kampagne>/seite/`.

| Teil | Wer füllt | Inhalt |
|---|---|---|
| `LEAD` (zwischen `/* LEAD:START */` und `/* LEAD:END */`) | Generator, je Lead | Lead-Format, `seiten_id`, `video_url`, `video_vorschaubild`, `video_titel` |
| `ABSENDER` | Agent, einmal | Name, Logo, Rechtsträger, Anschrift, Ansprechpartner, Rolle, Foto, Impressum-, Datenschutz-, Termin-Link, Termindauer, E-Mail für Datenlöschung |
| `SEITE` | Agent, einmal | `design` (Farben, Rundung), `bausteine`, `start_sperre`, `texte` |
| Gerüst (HTML/CSS) | niemand | fest; nur `branding.py anwenden` ersetzt Schriften und Farben |

**Bausteine:** Pflicht sind `begruessung`, `video`, `termin`, `herkunft`. Wählbar: `angebot` (Paket-Karte mit Leistungen, Inklusive-Liste, Ablauf), `stimmen` (Kundenstimmen, erste groß; je Stimme optional `bild`, `video_vorschaubild`, `video_etikett` (Standard „Video-Interview“) und entweder `video_url` (externer Player, https) oder `video_datei` (eigene mp4/webm unter `assets/`, liegt auf dem eigenen Server; `zitat` darf fehlen, dann zeigt die Karte nur Name, Rolle und Ergebnis)), `ansprechpartner`, `fragen`. Reihenfolge = Reihenfolge in `SEITE.bausteine`.

**Texte:**
- In Texten setzt `{feld}` Werte aus `LEAD`, `ABSENDER` oder `SEITE` ein; `{ansprache}` ergibt „Guten Tag Frau Nachname“ bzw. „Guten Tag“.
- Überschrift: spricht die Person an und sagt, was das Video zeigt. Muster: „{ansprache}, ich habe Ihnen ein persönliches Video aufgenommen, wie Sie …“.
- `einleitung: ""` lässt die Einleitung weg; dann folgt die Unterschrift (Foto, Name, Rolle) direkt auf die Überschrift.
- Nur Belegbares. Zahlen, Kunden, Zitate ausschließlich vom Nutzer. Fehlt etwas, bleibt `<Platzhalter>` stehen; der Generator veröffentlicht dann nicht.
- Kundenstimmen nur mit Zustimmung der Kunden, auch für diese Seiten. Ohne Stimmen `stimmen` aus `bausteine` streichen.

**Du-Fassung:** Duzt der Nutzer seine Kunden, alle Texte in `SEITE.texte` umstellen und zusätzlich die festen Texte der Vorlage: Überschrift „Woher wir Ihre Daten haben“, die Quelle („insbesondere das Impressum der …“), der Video-Satz in „Video“, der Hinweis unter dem Video („laden Sie das Video …“), der Datenlöschungs-Dialog, die Bestätigung „Ihre Daten werden gelöscht“, „Ihr Paket“, der Mail-Text der Datenlöschung, `noscript`. Danach prüfen: `grep -nE "\b(Sie|Ihr|Ihre|Ihnen|Ihren|Ihrem|Ihrer)\b" arbeit/<k>/seite/index.html` darf außerhalb von `<style>` nichts mehr finden.

**Branding:** `branding.py` liest Farben, Schriften und Logo von der Website, lädt die Schriften als Dateien herunter (nie per Link einbinden) und schreibt sie in die Kopie. Vor dem Klick lädt die Seite nichts von Dritten.

## Datenschutz und Recht (Kurzfassung)

- **An Skael** gehen nur Vorname, Firma, Domain, Website und die interne Kennung. Skael zeigt alles Übergebene ohne Anmeldung auf der Videoseite an, deshalb nie E-Mail oder Telefon.
- **Link-Kennung:** 22 zufällige Zeichen, nicht der Skael-Token, nie Name oder Firma in der Adresse.
- **Datenschutz-Information nach Art. 14 DSGVO** steht auf jeder Seite: Verantwortlicher, Daten, Quelle, Zweck, Speicherdauer. Die Quelle ist bewusst allgemein gehalten („Impressum … sowie weitere öffentlich zugängliche Quellen“, dazu `erfasst_am`). `quelle` und `quelle_url` aus dem Lead-Format bleiben intern als Nachweis und landen nie auf der Seite. Die Rechte stehen nur in der Datenschutzerklärung, nicht auf der Seite, und die Seite nennt keine IP-Übertragung (beides steht in der Datenschutzerklärung).
- **„Keine weiteren Nachrichten – Datenlöschung vornehmen“:** löscht die Seite sofort und meldet die Kennung an den Server. Der Nutzer sperrt die Adresse im Mailtool und im Scraper (`ABLAUF.md`, Teil F).
- **Datenschutzerklärung des Nutzers** muss die Videoseiten, Skael und den Server nennen (`anleitungen/05_datenschutzerklaerung.md`).
- Werbe-Mails ohne Einwilligung bleiben nach § 7 Abs. 2 Nr. 2 UWG riskant (`08_versand-und-recht.md`). Die Seite senkt Angriffsflächen, ersetzt aber keine Rechtsberatung.


---

<!-- Datei: wissen/17_learnings-videoseiten-testlauf-2026-10.md -->

# Learnings aus dem ersten echten Videoseiten-Lauf (Oktober 2026)

**Zweck:** Was beim ersten echten Durchlauf (ein Lead, ein Skael-Video, eine Seite im Branding des Absenders) schiefging und wie es jetzt geregelt ist. So läuft der nächste Aufbau ohne dieselben Umwege.
**Für wen:** KI-Modelle und Betreiber, die `pfade/videoseiten/` für einen Nutzer einrichten.
**Verwandt:** `16_videoseiten.md` · `pfade/videoseiten/ABLAUF.md` · `pfade/videoseiten/anleitungen/01_skael-video-aufnehmen.md` · `pfade/videoseiten/anleitungen/05_datenschutzerklaerung.md`

Stand: Oktober 2026. Alle Punkte sind im Code oder in den Anleitungen umgesetzt. Diese Datei erklärt das Warum.

---

## 1. Skael

| Beobachtung | Folge | Jetzt geregelt |
|---|---|---|
| Viele Kampagnen bestehen nur aus einer Facecam über dem Website-Screenshot, ohne Bildschirmaufnahme. | `videos.py` hielt die Kampagne für leer und konnte keine Kosten nennen. | Facecam allein zählt als Aufnahme. Kosten richten sich nach ihrer Länge. |
| Neue Kampagnen haben die Player-Farbe Lila (`#6366f1`). | Auf der Seite wirkt der Player fremd. | `videos.py pruefen` warnt. Anleitung 01, Schritt 3 lässt die Markenfarbe eintragen. |
| Cloudflare vor Skael lehnt den Standard-User-Agent von Python mit 403 ab. | Vorschaubilder fehlten, die Seite zeigte das Standardbild. | Der Generator sendet einen eigenen User-Agent. |
| Skael liefert Vorschaubilder als JPEG unter einer `.png`-Adresse. | Falsche Dateiendung. | Die Endung kommt aus dem Content-Type. |
| `warten` kennt kein `--leads`. | Abbruch mit Fehlermeldung. | Aufruf: `warten --kampagne <id>`. |

Kosten des Laufs: ein Video bis 2 Minuten = 110 Credits (0,11 €).

## 2. Video-Start auf der Seite

- **Ein Klick muss reichen.** Der Skael-Player nimmt den Play-Befehl erst an, wenn er `skaelreach:ready` gemeldet hat. Wird vorher gesendet, zeigt er seinen eigenen Play-Knopf und der Besucher muss zweimal klicken.
- **Schnell laden.** Browser erlauben Ton nur kurz nach dem Klick (etwa 5 Sekunden). Der Player lädt deshalb sofort beim Klick, parallel zur Zoom-Animation. Gemessen: rund 1 Sekunde vom Klick bis zum Abspielen, vorher über 3 Sekunden.
- **Prüfen ohne Bildschirm:** Im versteckten Browserfenster bleiben Screenshots des laufenden Videos schwarz. Ob es läuft, zeigen die Nachrichten des Players (`skaelreach:ready`, `skaelreach:playing`), nicht der Screenshot.

## 3. Seite gestalten

- **Keine freigegebenen Kundenstimmen?** Dann keine Zitate erfinden. Belegte Ergebnisse ohne Zitat zeigen und `stimmen_hinweis` auf die Quelle der Zahlen ändern (`ABLAUF.md`, Teil A).
- **Kein Testimonial-Video?** Ein vorhandenes Video des Nutzers (z. B. Erklärvideo von der Website) kann als `video_datei` in einer Ergebniskarte laufen. Es liegt dann auf dem eigenen Server und lädt nichts von Dritten.
- **Lange Wörter** in Überschriften und Angebotstiteln brachen mitten im Wort um. Jetzt mit automatischer Silbentrennung.
- **Kontrast:** Textfarbe für Akzente leitet sich aus der kontrastgeprüften Akzentfarbe ab. Helle Markenfarben (z. B. Lime) bleiben lesbar.

## 4. Texte im Datenschutz-Block

Der Block „Woher wir Ihre Daten haben“ soll informieren, ohne Angriffsfläche zu bieten. Festgelegt nach dem Testlauf:

- **Quelle allgemein halten:** „Öffentlich zugängliche Angaben, insbesondere das Impressum der Firma, sowie weitere öffentlich zugängliche Quellen.“ Nicht behaupten, die E-Mail-Adresse stamme aus dem Impressum. Das stimmt nicht immer.
- **Suchweg nie nennen** (z. B. „Google-Maps-Suche nach …“). `quelle` und `quelle_url` bleiben als interner Nachweis im Lead und werden nicht mehr in die Seite geschrieben, auch nicht in den Quelltext.
- **Keine Rechte-Aufzählung und kein IP-Satz auf der Seite.** Beides steht in der Datenschutzerklärung, auf die die Seite verlinkt. Der Knopf „Keine weiteren Nachrichten – Datenlöschung vornehmen“ bleibt.
- Ob der Verweis auf die Datenschutzerklärung für Art. 14 DSGVO genügt, steht als offener Punkt in Anleitung 05. Kein Rechtsrat.

## 5. Seiten erneut erzeugen

Nach einer Textänderung wird der Generator erneut ausgeführt. Früher bekam dabei jeder Lead eine neue Adresse, und schon verschickte Links wären ins Leere gelaufen. Jetzt behält eine vorhandene Seite im `--ziel`-Ordner ihre Adresse und ihr Löschdatum. Seiten mit Datenlöschung überspringt `hostinger.py hochladen` weiterhin.

## 6. Vorschau ohne eigenen Server

Für einen ersten Blick vor dem Hostinger-Server lässt sich der `seiten`-Ordner auch kurz auf einem statischen Hoster zeigen. Dabei gilt:

- `ergebnis.json` und `.meta.json` nicht mit hochladen (interne Daten).
- `noindex` setzen. Die Vorlage hat das Meta-Tag schon, zusätzlich den Header `X-Robots-Tag`.
- Nur zum Ansehen, nicht für den Versand. Datenlöschung und Zählung brauchen den eigenen Server.
- Nach einem neuen Upload zeigt der Browser oft noch die alte Fassung aus dem Cache. Vor dem Urteil neu laden.


---

<!-- Datei: wissen/18_pfad-stellensuche.md -->

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
