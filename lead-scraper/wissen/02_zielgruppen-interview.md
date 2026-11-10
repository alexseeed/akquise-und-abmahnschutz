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
