# Zielgruppen-Interview und Wahl des Pfads

**Zweck:** Bevor auch nur ein Euro für Abfragen ausgegeben wird, klärt das Interview, *wen* der Nutzer erreichen will und *wo* man diese Firmen findet. Aus den Antworten folgt der Pfad (Google Maps, Amazon, E-Commerce, später Recruiting) und fast alle Einstellungen des Laufs.
**Für wen:** die KI, die den Nutzer begleitet (Claude, ChatGPT, Gemini …), und Menschen, die verstehen wollen, warum gefragt wird.
**Verwandt:** `01_ueberblick.md` · `03_pfad-google-maps.md` · `04_pfad-amazon.md` · `07_lead-ausgabe-und-spalten.md`

---

## Regeln für das Gespräch

- **Eine Frage pro Nachricht**, immer mit einem Beispiel, an dem sich der Nutzer orientieren kann.
- **Keine Fachbegriffe** ohne Halbsatz-Erklärung. Nicht erwähnen: ICP, Prompt, Confidence, Tier, TLD, Stage, API, `.env`.
- **Schon Gesagtes nicht erneut fragen.** Steht die Antwort in der ersten Nachricht oder in einer vorhandenen Auftragsdatei, überspringen.
- **Weiß der Nutzer etwas nicht:** einen Vorschlag machen und bestätigen lassen, nicht nachbohren.
- Nach jedem Block **in eigenen Worten zusammenfassen** und bestätigen lassen.
- Ziel: ca. 10 kurze Fragen, dann eine klare Empfehlung. Nicht mehr fragen als nötig.

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
2. **Sie verkaufen über Amazon** mit eigener Marke.
3. **Sie haben einen eigenen Onlineshop** (Shopify, Shopware, WooCommerce …).
4. **Sie suchen gerade Personal** und schalten Stellenanzeigen.
5. **Weiß ich nicht.** Dann schlägt die KI anhand von B1–B3 einen Weg vor.

## Block D – Rahmen (gilt für alle Pfade)

| # | Frage | Beispiel | Wofür |
|---|---|---|---|
| D1 | „In welchen Ländern sollen die Firmen sitzen?“ | „Nur Deutschland, oder auch Österreich und Schweiz?“ | Suchgebiet |
| D2 | „Gibt es Firmen, die du sicher nicht willst?“ | „Große Ketten, Konzerne, reine Onlineshops, Franchise.“ | Ausschlüsse |
| D3 | „Brauchst du die Geschäftsführung persönlich, oder reicht info@…?“ | „Ich sammle beides – du entscheidest, was in die Liste kommt.“ | Exportfilter |
| D4 | „Wie viele Firmen brauchst du ungefähr, und was darf es kosten?“ | „200 gute Kontakte für einen Test, oder ganz Deutschland?“ | Umfang, Kosten |

---

## Entscheidung: welcher Pfad?

| Signal aus dem Interview | Pfad | Status |
|---|---|---|
| C1 = 1, oder die Branche ist ortsgebunden (Praxis, Handwerk, Kanzlei, Händler mit Laden/Lager) | **Google Maps** → `03_pfad-google-maps.md` | verfügbar |
| C1 = 2, oder C2 = Liste mit Amazon-Marken / `Brand Name` + `Dominant Seller` | **Amazon-Seller** → `04_pfad-amazon.md` | verfügbar (nur amazon.de, Brand-Liste nötig) |
| C1 = 3: eigener Onlineshop **und** eine Shop-Liste liegt vor (C2) | **E-Commerce** → `06_pfad-e-commerce.md` | verfügbar (Beta, erster echter Testlauf steht aus) |
| C1 = 3 ohne Shop-Liste | Google Maps (Shops mit Laden/Lager) oder Amazon; Quellen für Shop-Listen: `pfade/e-commerce/referenzen/discovery-quellen.md` | – |
| C1 = 4: Firmen, die gerade einstellen | **Recruiting** → `05_pfad-recruiting.md` | geplant |
| C2 = eigene Firmenliste mit Firmenname (ohne Amazon-Bezug) | **Sonderfall:** Amazon-Pfad ab Phase 4. Die Recherche von Website, Geschäftsführung und Anrede funktioniert für jede Firmenliste. | verfügbar |

**Mehrere Signale:** den Pfad mit der größten erwarteten Trefferzahl zuerst nehmen, den zweiten danach. Doppelte Firmen fallen spätestens beim Abgleich der Domains auf.

**Geplanter Pfad gewählt:** offen sagen, dass er noch nicht fertig ist. Die beste verfügbare Alternative anbieten:

- Onlineshops mit Lager oder Laden stehen oft auch bei Google Maps.
- Shops, die zusätzlich auf Amazon verkaufen, findet der Amazon-Pfad.

Die Antworten trotzdem in der Auftragsdatei sichern; sie dienen als Anforderung für den Bau des Pfads.

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
Offene Punkte: –
```

Der Pfad liest diese Datei und fragt nur, was dort noch fehlt. Die Datei bleibt beim Nutzer und dient später als Nachweis, wie die Zielgruppe bestimmt wurde.

Der E-Commerce-Pfad stellt danach eigene Rückfragen (Shop-Liste, Shopsystem, Mindestgröße, Shop-Profil, Mailtext) und startet erst, wenn alles beantwortet ist: `pfade/e-commerce/ABLAUF.md`, Phase 1.

---

## Übersetzung der Antworten in Einstellungen

| Antwort | Google Maps | Amazon | E-Commerce |
|---|---|---|---|
| A1 Angebot | Prüfprofil (Zielgruppen-Prüfung), Personalisierung | Ansprache-Text (außerhalb der Pipeline) | Shop-Profil, Personalisierung, Mailtext |
| A2 Video ja/nein | `DO_VIDEO_TITLE`, `DO_PERSONALISIERUNG` | – | `DO_VIDEO_TITLE`, `DO_PERSONALISIERUNG` |
| B1 Branche | Suchbegriffe (eng zuerst, dann breiter) | Filter im Export des Analyse-Tools | Filter beim Erstellen der Shop-Liste, Shop-Profil |
| B2/B3 Beschreibung, Beispiele | Prüfprofil, Testlauf-Kontrolle | Plausibilitätsprüfung | Shop-Profil, Testlauf-Kontrolle |
| D1 Länder | `--countries`, ggf. `EXCLUDED_TLDS` leeren (FR/NL/IT) | nur amazon.de | Shop-Profil (Sprache, Währung, Lieferländer), Zeilen vorab filtern |
| D2 Ausschlüsse | Prüfprofil „sofort raus“, `KETTEN_EXTRA` | Zeilen vorab filtern | Shop-Profil „sofort raus“, Zeilen vorab filtern |
| D3 Ansprechpartner | Exportliste 1 (GF) und/oder 2 (info@) | GF-Recherche Phase 4 | Exportliste 1 (GF) und/oder 2 (info@) |
| D4 Menge/Budget | `--min-population`, Anzahl Suchbegriffe | Umsatz-Schwelle, Zeilenzahl | Zeilenzahl, Testlauf-Größe; Mindestgröße → E3 in `pfade/e-commerce/ABLAUF.md` (beide Traffic-Schwellen) |
