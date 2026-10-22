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
| **Claude-Projekt, ChatGPT (Custom GPT / Projekt), Gemini (Gem), NotebookLM** | den Ordner `wissen/` als Projektwissen hochladen – oder die Datei `WISSEN_KOMPLETT.md` aus dem Paketordner, wenn nur eine Datei geht |

Start-Prompt für andere Modelle:

> Du begleitest mich beim Aufbau von B2B-Leadlisten mit dem „Lead-Scraper“. Dein Wissen steht in den hochgeladenen Markdown-Dateien. Beginne mit dem Zielgruppen-Interview aus `02_zielgruppen-interview.md`: eine Frage pro Nachricht, immer mit Beispiel. Beantworte Rückfragen nur aus diesen Dateien. Wenn dort etwas nicht steht, sag das, statt zu raten. Rechtliche Themen sind keine Rechtsberatung.

## Inhalt

| Datei | Worum es geht | Lesen, wenn … |
|---|---|---|
| `01_ueberblick.md` | Gesamtablauf, Pfade, wer was macht | du neu bist |
| `02_zielgruppen-interview.md` | Fragen vor jedem Lauf, Wahl des Pfads, Auftragsdatei | ein neuer Auftrag beginnt |
| `03_pfad-google-maps.md` | Firmen mit Standort: Stufen, Kosten, Prüfprofil, Quoten | der Pfad Google Maps gewählt ist |
| `04_pfad-amazon.md` | Amazon-Seller: Phasen, Voraussetzungen, Quoten, Risiken | eine Amazon-Brand-Liste vorliegt |
| `05_pfad-recruiting.md` | geplant: Zielbild und offene Entscheidungen | der Pfad gebaut werden soll |
| `06_pfad-e-commerce.md` | Onlineshops: erst Anforderungen klären, dann Shop-Liste prüfen (aktiver Shop, passt zum Shop-Profil, Traffic), anreichern und je Lead die fertige Mail ausgeben; Kosten, Grenzen, Recht | eine Liste von Onlineshops vorliegt |
| `07_lead-ausgabe-und-spalten.md` | Ausgabedateien, Spalten, Ansprache-Regeln, Standardformat | die Liste in ein Versandtool soll |
| `08_versand-und-recht.md` | UWG, DSGVO, Pflichtangaben, Quellen-Nutzungsbedingungen | vor dem ersten Versand |
| `09_sperrliste.md` | Community-Sperrliste: Abgleich, Melden, Widerspruch | Fragen zur Sperrliste |
| `10_abmahnung-was-tun.md` | erste Schritte nach einer Abmahnung | eine Abmahnung ist da |
| `11_zugaenge-und-kosten.md` | Konten, Schlüssel, Kostenhebel | vor der Einrichtung, vor großen Läufen |
| `12_fehlerbehebung-faq.md` | typische Probleme und Antworten | etwas klemmt |
| `13_glossar.md` | Begriffe von A bis Z | ein Wort unklar ist |
| `14_neuen-pfad-anlegen.md` | wie Recruiting, E-Commerce & Co. dazukommen | ein Pfad gebaut wird |

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
 sie?               (Recruiting,        (Abmahner raus)                               │
                     E-Commerce                ▲                                      │
                     geplant)                  └────── 6 Abmahner wird gemeldet ◄─────┘
```

Je mehr Unternehmen mitmachen, desto vollständiger wird die Sperrliste. Bedingung der Nutzung ist deshalb: Wer abgemahnt wird, meldet den Abmahner (`NUTZUNGSBEDINGUNGEN.md`).

## Die Teile

| Teil | Was er tut | Wo |
|---|---|---|
| **Lead-Scraper** (Claude-Skill + Projekt) | Interview, Pfadwahl, Durchführung, Abgleich | `lead-scraper/` |
| Pfad **Google Maps** | Firmen mit Standort finden, gegen Wunschkundenprofil prüfen, Impressum, Geschäftsführung, E-Mail, Anrede, Personalisierung | `lead-scraper/pfade/google-maps/` |
| Pfad **Amazon-Seller** | Brand-Liste → Seller, Amazon-Impressum, Website, Geschäftsführung, Anrede | `lead-scraper/pfade/amazon/` |
| Pfad **E-Commerce** | Shop-Liste → aktiver Onlineshop? Besucher? → Impressum, Geschäftsführung, E-Mail, Anrede, Personalisierung (Nachbau des Clay-Workbooks ECOM 2.0) | `lead-scraper/pfade/e-commerce/` |
| Pfad **Recruiting** | geplant | `lead-scraper/pfade/recruiting/` |
| **Sperrlisten-Abgleich** | sortiert Firmen aus, deren Domain nach einer Abmahnung gemeldet wurde | Google Maps: beim Export; sonst `werkzeuge/sperrliste_abgleich.py` |
| **Abmahnungs-Abwehr** (Claude-Skill) | Abmahnung prüfen, Antwort und Unterlassungserklärung, Website-Sicherung, Meldung an die Sperrliste | `abmahnung-werbemail-abwehr/` |
| **Sperrliste** (GitHub) | öffentliche Liste, ergänzt sich selbst | Repository `werbemail-sperrliste` |

## Wer macht was

| Rolle | Aufgabe |
|---|---|
| **Nutzer** | beantwortet das Interview, gibt Kosten frei, prüft Stichproben, versendet |
| **KI (Claude o. a.)** | fragt, wählt den Pfad, führt Befehle aus, übersetzt Ergebnisse, nennt Grenzen |
| **Dienste** | Skael (Google Maps, Impressum, E-Mail-Suche), OpenAI (Bewertungen, Texte), Amazon (Seller-Daten), Websuche (Geschäftsführung) |
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


---

<!-- Datei: wissen/05_pfad-recruiting.md -->

# Pfad „Recruiting“ – geplant

**Zweck:** Zielbild, offene Entscheidungen und Anforderungen für den künftigen Pfad.
**Für wen:** den Betreiber bzw. Entwickler, der den Pfad baut, und KI-Modelle, die Nutzern den Stand erklären.
**Verwandt:** `14_neuen-pfad-anlegen.md` · `02_zielgruppen-interview.md` · `08_versand-und-recht.md`

---

## Stand

**Noch nicht gebaut.** Das Interview erkennt den Bedarf (Block C, Antwort 4) und sagt das offen. Die Antworten werden als Auftragsdatei gesichert. Bis dahin kann der Google-Maps-Pfad mit einem strengen Prüfprofil helfen, wenn die gesuchten Firmen einen Standort haben.

## Zu klärende Grundsatzfrage

„Recruiting“ kann zweierlei bedeuten. Das muss vor dem Bau entschieden werden:

| Variante | Wer ist der Lead? | Beispiel-Angebot | Rechtliche Einordnung |
|---|---|---|---|
| **A – Firmen, die gerade einstellen** | das Unternehmen (Personalabteilung, Geschäftsführung) | Personaldienstleister, Recruiting-Agentur, HR-Software | B2B; die üblichen Regeln für Kaltakquise gelten (`08`) |
| **B – Kandidaten** | Privatpersonen bzw. Fachkräfte | Active Sourcing für eigene Stellen | Personendaten von Privatpersonen. Strengere DSGVO-Anforderungen, Nutzungsbedingungen der Plattformen (Jobbörsen, LinkedIn, Xing) verbieten Scraping meist ausdrücklich. **Deutlich höheres Risiko.** |

Empfehlung für den Start: **Variante A.** Sie passt zum bestehenden Kreislauf aus Lead, Sperrliste und Abmahnschutz.

## Zielbild Variante A (Entwurf)

```
Berufsbild + Region ─► Stellenanzeigen finden ─► Arbeitgeber extrahieren ─► Dedupe über Domain
  ─► Prüfprofil (Größe, Branche) ─► Impressum / Geschäftsführung / HR-Kontakt ─► Ansprache mit Bezug zur Stelle
  ─► Sperrliste ─► Export
```

Mögliche Signale für die Personalisierung: Zahl offener Stellen, wie lange eine Stelle schon ausgeschrieben ist, Berufsbilder.

## Offene Entscheidungen

1. Variante A oder B?
2. **Datenquelle:**
   - Jobbörsen-APIs
   - Google for Jobs
   - Karriereseiten
   - Anbieter-APIs, die Stellenanzeigen aggregieren

   Nutzungsbedingungen und Kosten je Quelle prüfen.
3. **Ansprechpartner:** Geschäftsführung, Personalleitung oder die Kontaktperson aus der Anzeige? Letztere ist oft eine namentlich genannte Person, also personenbezogen.
4. Wiederverwendung von Stufe 3–4 des Google-Maps-Pfads: Prüfprofil, Impressum, E-Mail-Suche.

## Zusätzliche Interviewfragen (wenn gebaut)

| Frage | Beispiel |
|---|---|
| „Welche Berufe sollen die Firmen gerade suchen?“ | „Zum Beispiel Elektriker, Pflegekräfte, Vertriebsleute.“ |
| „Wie lange muss eine Stelle schon offen sein, damit es für dich interessant ist?“ | „Ab vier Wochen ist der Druck meist spürbar.“ |
| „Wen willst du erreichen – Geschäftsführung oder Personalabteilung?“ | „Bei kleinen Firmen meist die Geschäftsführung.“ |

Pflichtenheft für den Bau: `pfade/_vorlage/README.md`.


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
**Verwandt:** `03_pfad-google-maps.md` · `04_pfad-amazon.md` · `06_pfad-e-commerce.md` · `09_sperrliste.md`

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

Wichtige Spalten in Liste 1 und 2:

| Spalte | Bedeutung |
|---|---|
| Firmenname, Website | aus dem Impressum, sonst aus Google Maps |
| E-Mail, E-Mail Typ, E-Mail Status, E-Mail Quelle | Adresse; `GF`/`Info@`; `Safe to Send`/`Risky`/`Unknown`; Skael/Findymail |
| Anrede, Vorname, Nachname, Kontaktperson | aus dem Impressum, Geschlecht per KI |
| Ansprache Formal / Normal / Guten Tag / Persönlich | fertige Grußformeln in vier Tonlagen |
| Personalisierung | ein bis zwei Sätze, die direkt an die Anrede anschließen |
| Pain / Angebot, Einordnung belegt durch | Einordnung des Bedarfs (wenn das Profil das vorsieht) |
| Videotitel | für Video-Outreach |
| Adresse, PLZ, Telefon | je aus Impressum und Google Maps |
| Kategorie, Bewertung, Anzahl Bewertungen | Google-Maps-Daten |
| Keyword, Stadt, Land | Herkunft des Leads |

**E-Mail Status:**

- **`Safe to Send`:** zustellbar.
- **`Risky`:** Catch-all, der Server nimmt alles an.
- **`Unknown`:** nicht prüfbar.

`Risky` und `Unknown` getrennt und vorsichtig versenden, sonst leidet die Absender-Reputation.

## Amazon – eine angereicherte Liste

Die Eingabe-CSV wird um Spalten ergänzt, Originalspalten bleiben erhalten. Nach dem Abgleich gibt es `<liste>_bereinigt.csv` und `<liste>_gesperrt.csv`.

| Spalte | Bedeutung |
|---|---|
| Seller ID, Seller Storefront URL, Match Method | Amazon-Verkäufer |
| Geschäftsname (Impressum), Handelsregister, Geschäftsadresse | aus dem Amazon-Impressum |
| Website | Impressums-URL der eigenen Website |
| GF Vorname, GF Nachname, GF Alle, GF Quelle, GF Confidence | Geschäftsführung; Quelle `website_impressum`/`handelsregister`/…; Zuordnung `sicher`/`unsicher` |
| Anrede, Anrede Confidence | Herr/Frau; 0–100 = Sicherheit beim **Vornamen** |
| Ansprache, Ansprache Grund | fertige Grußformel; warum neutral, falls neutral |

Die zwei Sicherheitswerte nicht verwechseln:

- **`GF Confidence`:** Ist es überhaupt die richtige Firma?
- **`Anrede Confidence`:** Ist der Vorname männlich oder weiblich?

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
| Firmenname | Firmenname | Geschäftsname (Impressum) | Firmenname |
| Website | Website | Website | Website |
| E-Mail | E-Mail | – (nicht Teil des Pfads) | E-Mail |
| Anrede | Anrede | Anrede | Anrede |
| Vorname / Nachname | Vorname / Nachname | GF Vorname / GF Nachname | Vorname / Nachname |
| Ansprache | Ansprache Guten Tag (bzw. gewünschte Tonlage) | Ansprache | Ansprache Guten Tag (bzw. gewünschte Tonlage) |
| Personalisierung | Personalisierung | – | Personalisierung |
| Quelle | Keyword, Stadt, Land | Brand Name, Seller ID | Quelle (Dateiname), Firmenname (Import) |
| Pfad | `google-maps` | `amazon` | `e-commerce` |

## Ansprache – gemeinsame Regeln

1. **Im Zweifel neutral.** Ist der Name oder das Geschlecht unsicher, heißt es „Guten Tag“ statt einer persönlichen Anrede.
2. **Nur Nachname** in der persönlichen Form: „Guten Tag Herr Mustermann“.
3. **Personalisierung beobachtet, unterstellt nicht.** Sie beschreibt, was auf der Website zu sehen ist, und benennt keine Probleme des Empfängers.

## In ein Versandtool übernehmen

1. Nur die bereinigten Listen importieren: Google Maps 1/2, E-Commerce 1/2, Amazon `_bereinigt`.
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
- **Amazon:** Automatisierte Abrufe können gegen die Amazon-Nutzungsbedingungen verstoßen. Risiko: Captcha oder Kontosperre (`04_pfad-amazon.md`).
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
2. **Nichts unterschreiben, nichts zahlen,** bevor geprüft ist. Die beigelegte Unterlassungserklärung ist fast immer zu weit gefasst und enthält oft Zahlungspflichten.
3. **Absender sperren:** alle Domains und Adressen des Abmahners in allen Systemen (Versandtool, CRM, Lead-Listen, bei Dienstleistern).
4. **Nicht anrufen, nicht diskutieren,** keine spontane Antwort-Mail mit Eingeständnissen.

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
| **Auskunft nach Art. 15 DSGVO** | fristgerecht und vollständig erteilen, direkt an die betroffene Person |
| **Anwaltskosten** | Höhe und Gegenstandswert prüfen; Ablehnung hat ein Prozesskostenrisiko |

## Was man vermeiden muss

- **Gegendrohungen** wie „Wenn Sie weiter …, zeigen wir Ihre Website-Verstöße an“. Das kann als Nötigung oder Erpressung gewertet werden (§§ 240, 253 StGB) und macht eine Einigung anfechtbar.
- **Eingeständnisse**, z. B. „Die Adresse stand doch im Impressum“: Damit wird die Erhebung der Daten aus anderen Quellen eingestanden, was die Informationspflicht nach Art. 14 DSGVO auslöst.
- **Erkenntnisse aus der Sperrliste im Schreiben** („uns sind weitere Fälle bekannt“). Sie bleiben intern.


---

<!-- Datei: wissen/11_zugaenge-und-kosten.md -->

# Zugänge und Kosten

**Zweck:** welche Konten und Schlüssel jeder Pfad braucht und wovon die Kosten abhängen.
**Für wen:** Nutzer vor der Einrichtung und vor großen Läufen.
**Verwandt:** `03_pfad-google-maps.md` · `04_pfad-amazon.md` · `pfade/google-maps/docs/02_ZUGAENGE_UND_TOKENS.md`
**Stand:** 2026-10-08 · **Prüfen bis:** 2027-01-08. Preise der Anbieter ändern sich; aktuelle Tarife immer beim Anbieter prüfen (Skael: Werkzeug `get_pricing`, 1.000 Credits = 1 €).

---

## Je Pfad

| Pfad | Pflicht | Optional |
|---|---|---|
| **Google Maps** | Python ≥ 3.10; **Skael** (`SKAEL_API_KEY`, beginnt mit `eak_`); **OpenAI** (`OPENAI_API_KEY`, beginnt mit `sk-`, **Guthaben vorher aufladen**) | Findymail (`FINDYMAIL_API_KEY`) als zweiter E-Mail-Finder |
| **Amazon** | Brand-Liste (z. B. SmartScout-Export, eigenes Abo); Chrome mit amazon.de-Login und Erweiterung „Claude in Chrome“; Claude mit Subagenten; Python 3 | – |
| **E-Commerce** | Shop-Liste als CSV; Python ≥ 3.10; **Skael** und **OpenAI** wie Google Maps | Findymail |
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

### Amazon

- **Laufende Kosten:** im Wesentlichen das Abo des Analyse-Tools für die Brand-Liste und die Claude-Nutzung.
- **Claude-Nutzung:** Die Recherche der Geschäftsführung läuft in Subagenten; ~1.000 Firmen sind ~25 Agenten-Aufrufe.
- **Laufzeit:**
  - ~1.500 Brands in ~30 Minuten für die Seller IDs
  - ~3–4 Minuten je 40 Firmen für die Geschäftsführung

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

1. Testlauf (Google Maps: 3 Städte; Amazon: ein Arbeitspaket; E-Commerce: `--limit 10`).
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
- Marke auf Amazon → Amazon
- Liste von Onlineshops → E-Commerce (`06`)
- Firmen, die Personal suchen → Pfad noch geplant, Alternativen siehe `05`

**Kann ich eine eigene Firmenliste anreichern lassen?**
Ja. Mit Firmenname (ideal mit HR-Nummer und Ort) über den Amazon-Pfad ab Phase 4: Website, Geschäftsführung, Anrede. Für die E-Mail-Suche gibt es dafür noch keinen eigenen Pfad.

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
| „kein Browser verbunden“ | Chrome-Erweiterung nicht aktiv | Chrome öffnen, Erweiterung verbinden, auf amazon.de einloggen |
| alle Abrufe scheitern | Tab steht nicht auf amazon.de | auf eine amazon.de-Produktseite navigieren, Bibliothek neu laden |
| Tab friert ein | zu viele parallele Abrufe | höchstens ~8 Worker; Zwischenstände sichern |
| zweiter Download kommt nicht an | Chrome blockt den zweiten automatischen Download pro Tab | Umweg über `localStorage` und frischen Tab (`pfade/amazon/referenzen/browser-technik.md`) |
| Captcha oder Sperre | Amazon erkennt automatisierte Abrufe | pausieren, langsamer arbeiten, separates Konto nutzen |
| wenige Geschäftsführer | viele Seller aus HK/CN | erwartbar; deutsche Firmen haben ~95 % Fundquote |
| Impressum „leer“ beim Prüfen | Seite wird per JavaScript aufgebaut | über den Browser prüfen statt per einfachem Abruf |

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
| **Brand-Liste** | Export aus einem Amazon-Analyse-Tool mit Marken, dominantem Verkäufer und Umsatzschätzung |
| **Catch-all** | Mailserver, der jede Adresse annimmt; Status `Risky` – Zustellung ungewiss |
| **Dedupe** | Entfernen doppelter Firmen, hier über die Domain |
| **Dominant Seller** | Verkäufer, der die meisten Angebote einer Marke auf Amazon hat; Referenz für die Seller ID |
| **GF / GF Confidence** | Geschäftsführung; Sicherheit, dass die **Firma** richtig zugeordnet ist (`sicher`/`unsicher`) |
| **HR-Nummer** | Handelsregisternummer, z. B. „Amtsgericht Ulm HRB 123456“; Anker gegen gleichnamige Firmen |
| **ICP / Prüfprofil / Wunschkundenprofil** | Beschreibung des idealen Kunden, gegen die jede Website geprüft wird |
| **Keyword / Suchbegriff** | Begriff für die Google-Maps-Suche; jeder zusätzliche Begriff vervielfacht die Kosten |
| **Mailtext (Vorlage)** | die Werbe-Mail des Nutzers: erste Zeile `Betreff: …`, dann der Text mit Platzhaltern. Im E-Commerce-Pfad wird sie je Lead gefüllt und steht im Export in den Spalten `Betreff` und `Mailtext` (`07`). Aus Angebot und Mailtext entsteht die Anweisung für den persönlichen Satz |
| **Modifizierte Unterlassungserklärung** | selbst formulierte, enger gefasste Erklärung ohne Schuldanerkenntnis und ohne Zahlungspflichten |
| **Pfad** | eine Lead-Quelle mit eigenem Ablauf: Google Maps, Amazon, E-Commerce, später Recruiting |
| **Platzhalter** | Stelle in einer Vorlage in doppelten geschweiften Klammern, z. B. `{{Firmenname}}`, die je Lead durch den passenden Wert ersetzt wird. Die Schreibweise muss genau stimmen; unbekannte Platzhalter lehnt der E-Commerce-Pfad ab (`07`, `12`) |
| **Ready to Send / versandfertig** | E-Mail vorhanden (und Personalisierung/Videotitel, wenn eingeschaltet) |
| **Relay** | kleiner Webdienst des Betreibers, der Meldungen an die Sperrliste annimmt und ins Repository schreibt |
| **SEND / Traffic-Filter** | E-Commerce Stufe 1e: Ein Shop geht nur in die Anreicherung, wenn SimilarWeb Besuche misst (Schnitt bzw. Höchstwert ≥ Schwelle, Standard 1) |
| **Safe to Send / Risky / Unknown** | Ergebnis der E-Mail-Prüfung: zustellbar / Catch-all / nicht prüfbar |
| **Seller ID / Storefront** | Amazon-Verkäuferkennung; Link auf alle Angebote eines Verkäufers |
| **Shop-Profil** | E-Commerce: Beschreibung, welche aktiven Shops zum Kunden passen (Region, Sortiment, Ausschlüsse). Die KI prüft jede Startseite dagegen (Stufe 1c); nicht passende Shops kommen mit Grund in Liste 3. Gegenstück zum Prüfprofil im Google-Maps-Pfad. „Bewusst ohne“ = jeder aktive Shop zählt (`06`) |
| **Skael** | Dienst für Google-Maps-Suche, Impressum, E-Mail-Suche und -Prüfung, Website-Abruf |
| **Sperrliste** | Community-Liste von Domains, die nicht angeschrieben werden (`09`) |
| **Stufe 1–4 / 3c** | Abschnitte des Google-Maps-Ablaufs; 3c = Prüfung gegen das Profil |
| **Subagent** | eigenständige KI-Instanz mit eigenem Kontext, die ein Arbeitspaket erledigt und nur eine Zeile zurückmeldet |
| **Testlauf (Dry-Run)** | kleiner Lauf über wenige Städte bzw. ein Arbeitspaket, um Profil und Kosten zu prüfen |
| **UWG § 7** | Verbot unzumutbarer Belästigung; E-Mail-Werbung nur mit vorheriger ausdrücklicher Einwilligung |
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
   | Geschäftsführung per Recherche-Agent | Amazon, Phase 4 (`referenzen/agent-prompt.md`) |
   | Anrede- und Ansprache-Regeln | Amazon `scripts/anrede.py` |
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
