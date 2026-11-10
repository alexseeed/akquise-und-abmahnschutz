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
