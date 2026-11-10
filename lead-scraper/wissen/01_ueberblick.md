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
 sie?               E-Commerce          (Abmahner raus)                               │
                    Recruiting                 ▲                                      │
                    Stellensuche               └────── 6 Abmahner wird gemeldet ◄─────┘
```

Je mehr Unternehmen mitmachen, desto vollständiger wird die Sperrliste. Bedingung der Nutzung ist deshalb: Wer abgemahnt wird, meldet den Abmahner (`NUTZUNGSBEDINGUNGEN.md`).

## Die Teile

| Teil | Was er tut | Wo |
|---|---|---|
| **Lead-Scraper** (Claude-Skill + Projekt) | Interview, Pfadwahl, Durchführung, Abgleich | `lead-scraper/` |
| Pfad **Google Maps** | Firmen mit Standort finden, gegen Wunschkundenprofil prüfen, Impressum, Geschäftsführung, E-Mail, Anrede, Personalisierung | `lead-scraper/pfade/google-maps/` |
| Pfad **Amazon-Seller** | findet Drittanbieter auf amazon.de selbst: Firma, Land, Sortiment, Umsatz, Kontaktdaten, Website, Geschäftsführung, Anrede | `lead-scraper/pfade/amazon/` |
| Pfad **E-Commerce** | Shop-Liste → aktiver Onlineshop? Besucher? → Impressum, Geschäftsführung, E-Mail, Anrede, Personalisierung (Nachbau des Clay-Workbooks ECOM 2.0) | `lead-scraper/pfade/e-commerce/` |
| Pfad **Recruiting** (Firmen-Website) | Firmen, die gerade einstellen: Google Maps → Prüfprofil → offene Stelle auf der Firmen-Website erkennen → Geschäftsführung, E-Mail, Opener mit Bezug zur Stelle | Anleitung `lead-scraper/pfade/recruiting/`, läuft im Scraper-Programm `pfade/google-maps/` |
| Pfad **Stellensuche** (Jobportale) | Suchbegriff → Stellenanzeigen aus Indeed, Stepstone, Arbeitsagentur, Kununu → je Firma gebündelt → Größen-Check → wahlweise Website per Impressum-Beleg, Geschäftsführung, E-Mail, Opener zur Stelle | Anleitung `lead-scraper/pfade/stellensuche/`, läuft im Scraper-Programm `pfade/google-maps/` |
| **Sperrlisten-Abgleich** | sortiert Firmen aus, deren Domain nach einer Abmahnung gemeldet wurde | Google Maps, Recruiting, Stellensuche: beim Export; sonst `werkzeuge/sperrliste_abgleich.py` |
| **Abmahnungs-Abwehr** (Claude-Skill) | Abmahnung prüfen, Antwort und Unterlassungserklärung, Website-Sicherung, Meldung an die Sperrliste | `abmahnung-werbemail-abwehr/` |
| **Sperrliste** (GitHub) | öffentliche Liste, ergänzt sich selbst | Repository `werbemail-sperrliste` |

## Wer macht was

| Rolle | Aufgabe |
|---|---|
| **Nutzer** | beantwortet das Interview, gibt Kosten frei, prüft Stichproben, versendet |
| **KI (Claude o. a.)** | fragt, wählt den Pfad, führt Befehle aus, übersetzt Ergebnisse, nennt Grenzen |
| **Dienste** | Skael (Google Maps, Impressum, Geschäftsführung, E-Mail-Suche), OpenAI (Bewertungen, Texte), Oxylabs (Amazon-Seiten), Bright Data (Kontaktdaten der Amazon-Verkäufer) |
| **Betreiber** | betreibt Sperrliste und Relay, bearbeitet Widersprüche |

## Grundsätze

1. **Erst fragen, dann zahlen.** Interview und Testlauf kommen vor jedem großen Lauf.
2. **Lieber neutral als falsch.** Unsichere Namen oder Geschlechter bekommen „Guten Tag“ statt einer falschen persönlichen Anrede.
3. **Ehrliche Zahlen.** Fund- und Fehlerquoten werden genannt, nicht geschönt.
4. **Gesperrt heißt gesperrt.** Firmen auf der Sperrliste werden nie angeschrieben, über keinen Kanal.
5. **Kein Ersatz für Rechtsberatung.** Kaltakquise per E-Mail bleibt rechtlich riskant (`08_versand-und-recht.md`).
