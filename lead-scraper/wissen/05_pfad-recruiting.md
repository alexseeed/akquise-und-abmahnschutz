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
