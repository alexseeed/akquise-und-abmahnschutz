# Pflichtenheft für einen neuen Pfad

Jeder Pfad, z. B. Recruiting oder E-Commerce, erfüllt diese Punkte, bevor er im Interview angeboten wird. So bleiben Einstieg, Wissen und Sperrliste für alle Pfade gleich. Ausführlich: `wissen/14_neuen-pfad-anlegen.md`.

## Ordner

```
pfade/<pfad>/
  ABLAUF.md        Anleitung für die KI: Phasen, Befehle, Prüfpunkte (wie pfade/amazon/ABLAUF.md)
  README.md        Kurzbeschreibung für Menschen
  scripts/ …       Code (bevorzugt Python-Standardbibliothek)
  referenzen/ …    Prompts, Spaltenbeschreibungen, Technikdetails
```

## Pflichtpunkte

| # | Punkt | Woran man es erkennt |
|---|---|---|
| 1 | **Einstieg** – im Interview erkennbar | Zeile in `wissen/02_zielgruppen-interview.md`: Antwortmöglichkeit in Block C und Zeile in „Entscheidung“; Spalte in „Übersetzung der Antworten“ |
| 2 | **Liest die Auftragsdatei**, fragt nur, was fehlt | `ABLAUF.md` beginnt mit dem Hinweis auf `auftraege/…md` |
| 3 | **Wissen dokumentiert** | eigene Datei `wissen/NN_pfad-<pfad>.md` mit Zweck, Voraussetzungen, Ablauf, Kosten, Fundquoten, Grenzen, Rechtliches; Eintrag in `wissen/00_INDEX.md` |
| 4 | **Testlauf vor Vollstart** | kleiner Durchlauf mit Ergebnis-Stichprobe, Kosten vorher nennen |
| 5 | **Ausgabe im Standardformat** | Pflichtspalten aus `wissen/07_lead-ausgabe-und-spalten.md` (mindestens Firmenname, Website, Quelle/Pfad; wenn vorhanden E-Mail, Anrede, Vorname, Nachname, Ansprache) |
| 6 | **Sperrlisten-Abgleich vor Ausgabe** | `python3 ../../werkzeuge/sperrliste_abgleich.py <liste.csv>` als letzte Phase, Zahl der gesperrten Firmen nennen |
| 7 | **Ansprache vorsichtig** | neutrale Grußformel, wenn Name oder Geschlecht unsicher (Regeln wie Amazon-Pfad) |
| 8 | **Idempotent und fortsetzbar** | abgebrochener Lauf wird mit demselben Befehl fortgesetzt, gefüllte Felder werden nicht überschrieben |
| 9 | **Keine Geheimnisse, keine Personendaten im Paket** | Zugänge über `.env`; Arbeitsdaten in `data/`, `exports/` oder `arbeit/` (gitignored) |
| 10 | **Rechtliches geprüft** | Abschnitt in der Wissensdatei: Datenquelle, Nutzungsbedingungen der Quelle, DSGVO-Grundlage, Ansprache-Kanal |

## Freischalten

Erst wenn alle Punkte erfüllt sind, in `wissen/02` den Status von „geplant“ auf „verfügbar“ setzen und in `SKILL.md` die Pfadtabelle ergänzen.
