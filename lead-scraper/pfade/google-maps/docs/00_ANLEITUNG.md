# Anleitung — von der Idee zur fertigen Leadliste

Was du beantworten musst, was das System tut, und was am Ende rauskommt.

Du kannst den ganzen Weg im Chat gehen (Skill `lead-scraper`) oder selbst auf der
Kommandozeile. Diese Anleitung beschreibt beides parallel.

---

## Die 12 Fragen, die vor jedem Lauf geklärt sein müssen

Der Skill fragt sie ab. Wer selbst startet, geht sie einmal durch.

### Runde 0 — Rahmen (Reichweite und Kosten)

| # | Frage | Warum sie zählt | Standard |
|---|---|---|---|
| 1 | **Welche Länder?** | Bestimmt die Städteliste. DE ≈ 7.600 Orte, AT ≈ 1.310, CH ≈ 1.334 | — |
| 2 | **Ab welcher Ortsgröße?** | Der größte Kostenhebel überhaupt. `--min-population 20000` reduziert DE von ~7.600 auf ~600 Orte | `1` |
| 3 | **Nicht-DACH-Kampagne?** | `EXCLUDED_TLDS` wirft `.fr`, `.nl`, `.it` raus. Bei einer Frankreich-Kampagne fällt damit die **komplette Zielgruppe** weg → in `.env` leeren | `.fr,.nl,.it` |
| 4 | **Video-Outreach geplant?** | Wenn nein: `DO_PERSONALISIERUNG=false`, `DO_VIDEO_TITLE=false`. Spart Webscraper- und zwei KI-Aufrufe pro Lead | beide `true` |
| 5 | **Reichen `info@`-Adressen?** | Wenn nur Geschäftsführer-Mails zählen: `Email [Final][Type] = "Info@"` beim Export filtern | beide werden gesammelt |
| 6 | **Findymail-Fallback nutzen?** | Zweiter Mailfinder, wenn Skael nichts findet. Braucht `FINDYMAIL_API_KEY` | `true`, greift ohne Key nicht |

### Runde 1 — Wer ist der ideale Kunde?

| # | Frage |
|---|---|
| 7 | Welche Branche/Nische? (z. B. Metallbau, Zahnarztpraxen, Recruiting-Agenturen) |
| 8 | Beschreib deinen idealen Kunden in 1–2 Sätzen |
| 9 | Welcher Markt? (Deutschland, DACH, Deutschschweiz …) |

### Runde 2 — Woran erkennt man ihn und woran nicht?

| # | Frage |
|---|---|
| 10 | Welche Begriffe/Leistungen **müssen** auf der Website stehen? |
| 11 | Was sieht ähnlich aus, ist aber **kein** ICP? (typische Fehlläufer) |
| 12 | Größen-Filter und harte Ausschlüsse? (Konzerne, Ketten, Franchise, Filialnetze) |

### Runde 3 — Feinschliff

| # | Frage |
|---|---|
| 13 | Was soll die Confidence erhöhen oder senken? |
| 14 | Prüfungsreihenfolge? (z. B. erst Sprache, dann Branche, dann Größe) |
| 15 | Bei fehlender Info eher durchlassen oder eher rausfiltern? |

Ergebnis: ein ICP-Prompt (max. 400 Wörter) und eine Keyword-Liste in drei Stufen.

---

## Keyword-Tiers — was das bedeutet

Nach dem ICP-Prompt kommen die Google-Maps-Suchbegriffe, gestaffelt nach Trefferqualität.
Beispiel Metallbaubetriebe:

| Tier | Beispiele | Charakter |
|---|---|---|
| **1** | `Metallbau`, `Schlosserei` | eng, hohe Trefferquote, wenig Streuung |
| **2** | `Metallbauer`, `Stahlkonstruktionen`, `Metallmontage` | Synonyme, etwas mehr Streuung |
| **3** | `Möbelhaus`, `Innenausbau` | breit, viele Fehlläufer — der ICP-Check muss sie abfangen |

**Jedes Keyword multipliziert die Kosten.** Ein Keyword über DE/AT/CH mit
`min-population 1` sind bereits ~10.200 Google-Maps-Calls. Empfehlung: mit Tier 1
starten, Ergebnis prüfen, dann erweitern. Doppelte Firmen über mehrere Keywords
sind kein Problem — der Dedupe über die Domain fängt sie ab.

---

## Der Durchlauf

### Schritt 0 — Zugänge

`.env` ausfüllen: `SKAEL_API_KEY`, `OPENAI_API_KEY` (beide Pflicht),
`FINDYMAIL_API_KEY` optional.

```bash
cd <projektverzeichnis>
python3 -m scraper doctor
```

Prüft Keys, Prompt-Dateien, ICP-Prompt und macht eine Testabfrage gegen Skael.
Alles ✓ → weiter.

### Schritt 1 — ICP-Prompt bauen

Im Chat: *„Ich will [Zielgruppe] scrapen"* → der Skill führt durch die Runden und
legt `prompts/icp_<zielgruppe>.txt` an.

Ohne Chat: `prompts/icp_prompt_builder.md` als Vorlage nehmen,
`prompts/icp_beispiel_metallbau.txt` als fertiges Muster.

### Schritt 2 — Lauf anlegen

```bash
python3 -m scraper init \
  --keywords "Metallbau,Schlosserei" \
  --countries DE,AT,CH \
  --min-population 1 \
  --icp-prompt prompts/icp_metallbau.txt
```

Legt Keyword × Land als Zeilen an und hinterlegt den ICP-Prompt in der Datenbank.

### Schritt 3 — Dry-Run (nie überspringen)

```bash
python3 -m scraper run --stage 1            # Städte holen  (~30 s, sehr günstig)
python3 -m scraper run --stage 2 --limit 3  # nur 3 Städte  (~1 min)
python3 -m scraper run --stage 3            # Dedupe + ICP  (~2 min)
python3 -m scraper status
```

Jetzt in die Datenbank schauen — das ist der wichtigste Moment des ganzen Prozesses:

```bash
sqlite3 data/leads.db -header -column \
  "SELECT firmenname, website_final, icp_label, ROUND(icp_confidence,2) conf,
          substr(icp_reason,1,60) grund
     FROM datensaetze WHERE dedupe_status='kept' LIMIT 20;"
```

Prüfen:

* Sind die Firmen überhaupt die richtige Branche? → sonst Keywords anpassen
* Werden zu viele durchgelassen? → ICP-Prompt schärfen (mehr „SOFORT RAUS")
* Werden echte Kunden aussortiert? → ICP-Prompt lockern, `reason` verrät den Grund

Nach jeder Prompt-Änderung nur Stufe 3 neu fahren:

```bash
python3 -m scraper set-icp prompts/icp_metallbau.txt
sqlite3 data/leads.db "UPDATE datensaetze SET icp_raw=NULL, is_icp=NULL, attempts=0;"
python3 -m scraper run --stage 3c
```

Das kostet nur die ICP-Checks neu, nicht das Scraping.

### Schritt 4 — Vollstart

```bash
python3 -m scraper run --stage all
```

Läuft je nach Umfang Stunden. **Fortsetzbar:** Bei Abbruch (Strg+C, Rechner aus,
Netzwerkfehler) denselben Befehl erneut aufrufen — erledigte Zeilen werden
übersprungen. Fortschritt jederzeit über `python3 -m scraper status` in einem
zweiten Terminal.

### Schritt 5 — Kontrolle

```bash
python3 -m scraper status
```

```
  Stufe 1  Keyword × Land         6/6 erledigt
  Stufe 2  Städte-Queries         20.000/20.000 erledigt
  Stufe 3  Firmen gefunden        26590
           nach Dedupe            18.000
           ICP true / false       6445 / 11.600
  Stufe 4  Leads in Anreicherung  6445
           mit E-Mail             4.100
           Ready to Send          2447
```

Steckengebliebene Zeilen finden:

```bash
sqlite3 data/leads.db -header -column \
  "SELECT id, firmenname, attempts, substr(error,1,70)
     FROM anreicherung WHERE error IS NOT NULL LIMIT 20;"
```

Nach behobener Ursache erneut freigeben:

```bash
sqlite3 data/leads.db "UPDATE anreicherung SET attempts=0, error=NULL WHERE error IS NOT NULL;"
python3 -m scraper run --stage 4
```

### Schritt 6 — Export

```bash
python3 -m scraper export          # nur Ready to Send
python3 -m scraper export --all    # alles, auch unvollständige Leads
python3 -m scraper export --mark   # exportierte Leads markieren (nicht doppelt ausspielen)
```

CSV in `exports/`, Semikolon-getrennt mit BOM — öffnet sauber in Excel.

Vor jedem Export wird die **Community-Sperrliste** geladen: Domains von Unternehmen, die
nach einer Werbe-E-Mail abgemahnt haben. Treffer (auch Subdomains) landen ausschließlich in
`5_gesperrt_sperrliste_….csv` und nie in den Versandlisten. Ist die Liste nicht erreichbar,
wird die letzte lokale Kopie genutzt; gibt es keine, bricht der Export ab
(`SPERRLISTE_PFLICHT=true`).

---

## Was in der CSV steht

30 Spalten, u. a.:

| Spalte | Inhalt |
|---|---|
| Firmenname | aus dem Impressum, sonst aus Google Maps |
| Website | finale, bereinigte URL |
| E-Mail + Typ + Status + Quelle | Adresse, `GF`/`Info@`, `Safe to Send`/`Risky`/`Unknown`, `Skael`/`Findymail` |
| Anrede, Vorname, Nachname | aus dem Impressum, Geschlecht per KI bestimmt |
| Ansprache × 4 | Formal / Hallo / Guten Tag / Persönlich — fertig zum Einsetzen |
| Personalisierung | 1–2 Sätze KI-Kompliment, schließt direkt an die Anrede an |
| Videotitel | grammatikalisch korrekter Titel für Video-Outreach |
| Adresse, PLZ, Telefon | je einmal aus Impressum und aus Maps |
| Kategorie, Bewertung, Anzahl Bewertungen | Google-Maps-Daten |
| Keyword, Stadt, Land | woher der Lead kam |

**Für den Versand relevant:** `E-Mail Status` = `Safe to Send` ist sicher.
`Risky` (Catch-all) und `Unknown` sind im Export enthalten — separat behandeln
oder vor dem Versand rausfiltern.

---

## Kostenabschätzung vorab

```
Google-Maps-Calls = Keywords × Städte
```

| Setup | Städte | Keywords | Maps-Calls |
|---|---|---|---|
| DACH, ab 1 Einwohner | 10.244 | 1 | 10.244 |
| DACH, ab 1 Einwohner | 10.244 | 3 | 30.732 |
| DACH, ab 20.000 Einwohner | ~900 | 3 | ~2.700 |
| Nur DE, ab 50.000 Einwohner | ~190 | 2 | ~380 |

Danach je gefundener Firma: 1× ICP-Check, und je ICP-Treffer 1× Impressum,
1–2× Mailfinder, 1–2× Verify, 1× Webscraper.

---

## Häufige Situationen

| Situation | Ursache | Lösung |
|---|---|---|
| Kaum Firmen gefunden | Keyword zu speziell, oder Orte zu klein | Tier-2-Keywords ergänzen |
| ICP lässt fast alles durch | Prompt zu weich | Mehr „SOFORT RAUS", härtere Prüfung 1 |
| ICP filtert fast alles weg | Prompt zu streng | `icp_reason` lesen, Muss-Kriterien lockern |
| Ganze Zielgruppe verschwindet | `EXCLUDED_TLDS` trifft das Zielland | in `.env` leeren |
| Wenige E-Mails | Impressen ohne Geschäftsführer | `Email [Final][Type] = Info@` mitnehmen |
| Deutschland unvollständig | `CITIES_LIMIT=5000` kappt bei ~7.600 Orten | in `.env` auf `10000` erhöhen |
| Lauf bricht ab | Netz, Rate-Limit, Rechner | denselben `run`-Befehl erneut — er setzt fort |
