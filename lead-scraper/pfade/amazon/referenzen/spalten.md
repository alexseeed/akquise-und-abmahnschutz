# Spalten und Datenformat

## Eingabe

Die Listen kommen aus SmartScout-Exporten und sehen praktisch immer gleich aus: ~30 Spalten, UTF-8 mit BOM, alle Werte in Anführungszeichen. Die Pipeline liest davon nur vier:

| Spalte | Verwendung |
|---|---|
| `Brand Name` | Suchbegriff für die Amazon-Brand-Suche |
| `Dominant Seller` | Referenzname für das exakte Seller-Matching |
| `Seller ID` | teilweise vorbefüllt; leere Zeilen sind die Arbeit |
| `Est. Monthly Revenue` | Priorisierung — wertvollste Leads zuerst |

Fehlt `Dominant Seller`, ist die Zeile nicht bearbeitbar: Ohne Referenznamen kann man nicht prüfen, ob der gefundene Verkäufer der richtige ist. `analyse.py` zählt diese Zeilen separat und überspringt sie.

## Ausgabe

| Spalte | Inhalt |
|---|---|
| `Seller ID` | Amazon-Verkäufer-ID, z.B. `A1B2C3D4E5F6G7` |
| `Match Method` | `chrome_exact_dominant` für neu ermittelte IDs |
| `Seller Storefront URL` | `https://www.amazon.de/s?me=<ID>&marketplaceID=A1PA6795UKMFR9` |
| `Geschäftsname (Impressum)` | Firmenname laut Amazon-Impressum |
| `Handelsregister` | z.B. `Amtsgericht Ulm - HRB 727066` — Anker für Phase 4 |
| `Geschäftsadresse` | Straße, Ort, PLZ, Ländercode |
| `Website` | Impressums-URL der Firma |
| `GF Vorname` / `GF Nachname` | erster Geschäftsführer, aufgeteilt |
| `GF Alle` | alle Geschäftsführer, `; `-getrennt |
| `GF Quelle` | siehe unten |
| `GF Confidence` | `sicher` / `unsicher` — bezieht sich auf die **Firmenzuordnung** |
| `Anrede` | `Herr` / `Frau` / leer |
| `Anrede Confidence` | 0-100, wie sicher das Geschlecht des **Vornamens** ist |
| `Ansprache` | fertige Grußformel — das Zielfeld der Pipeline |
| `Ansprache Grund` | warum neutral gegrüßt wird, falls neutral |

### Die zwei Confidence-Spalten nicht verwechseln

`GF Confidence` beantwortet: *Ist das überhaupt die richtige Firma?* (Länder-Tochter erwischt? Gleichnamige GmbH?)
`Anrede Confidence` beantwortet: *Ist dieser Vorname männlich oder weiblich?*

Beide können unabhängig danebengehen. `Roland` ist zu 98% männlich — aber wenn die Firmenzuordnung falsch war, heißt der Geschäftsführer gar nicht Roland. Deshalb setzt `anrede.py` die Ansprache auch dann neutral, wenn nur die GF-Angabe unsicher ist.

### Ansprache-Regeln

| Situation | Ergebnis |
|---|---|
| `Anrede Confidence` > 60 und GF sicher | `Guten Tag Herr Mustermann` |
| `Anrede Confidence` ≤ 60 | `Guten Tag` |
| `GF Confidence` = `unsicher` | `Guten Tag` |
| kein Geschäftsführer | `Guten Tag` |

Die Schwelle 60 steht in `scripts/anrede.py` als `SCHWELLE`. Sie an einer Stelle zu ändern reicht.

### GF Quelle

| Wert | Bedeutung |
|---|---|
| `website_impressum` | vom Impressum der Firmenwebsite |
| `handelsregister` | aus northdata/openregister/companyhouse, weil die Website keinen GF nennt |
| `amazon_impressum_einzelunternehmer` | Geschäftsname ist der Personenname (Einzelunternehmer) |
| `amazon_impressum_gname` | Verkäufer hat die Person in den Geschäftsnamen geschrieben (`Firma GmbH/Nachname Vorname`) — selten und unsicher, die Reihenfolge Nachname/Vorname ist nicht garantiert |

## Idempotenz

Alle Skripte füllen nur leere Felder:

- `merge_amazon.py` überschreibt keine vorhandene `Seller ID` und kein vorhandenes Impressum.
- `merge_gf.py` überspringt Zeilen mit gefülltem `GF Vorname`.
- `Seller Storefront URL` wird als Einzige immer neu aus der aktuellen `Seller ID` berechnet — so können ID und URL nicht auseinanderlaufen.

Ein abgebrochener Lauf wird einfach wiederholt. `analyse.py` erneut laufen lassen, es zählt den Reststand und legt frische Chunks an.

## Größenordnungen

Aus einem realen Lauf mit 3.543 Zeilen:

| Kennzahl | Wert |
|---|---|
| Seller IDs gefunden | 92% der gesuchten |
| Zeilen mit Seller ID danach | 96% |
| Impressen mit Geschäftsname | 98% der Seller |
| Zeilen mit Geschäftsführer | ~33% |
| Adressverteilung | 35% DE, 8% HK, 3% CN, Rest gemischt |

Die GF-Quote ist durch die Herkunft gedeckelt, nicht durch die Recherche: Hongkong- und China-Firmen haben keinen Geschäftsführer im deutschen Sinn. Bei den DE-Firmen liegt die Fundquote bei ~95%.
