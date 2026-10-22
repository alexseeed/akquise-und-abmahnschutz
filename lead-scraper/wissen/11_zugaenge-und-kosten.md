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
