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
