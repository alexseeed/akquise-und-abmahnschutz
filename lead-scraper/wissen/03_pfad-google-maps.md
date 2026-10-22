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
