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
