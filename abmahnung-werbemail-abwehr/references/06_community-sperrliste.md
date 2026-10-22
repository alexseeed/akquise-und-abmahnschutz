# Community-Sperrliste (GitHub)

Ein öffentliches GitHub-Repository mit den Domains aller Unternehmen, die Nutzer wegen einer Werbe-E-Mail abgemahnt haben. Zwei Zwecke:

1. **Sperrliste** für E-Mail-Kampagnen: eine Domain je Zeile. Wer sie importiert, schreibt diese Unternehmen nie wieder an. Das gilt für alle Adressen und Subdomains.
2. **Erfahrungswerte**: Ist der Abmahner bekannt? Welche Kanzlei, welche Forderungen, wie wurde vorgegangen, wie ging es aus?

Die Liste ergänzt sich selbst. Jede Meldung wird automatisch geprüft und in wenigen Minuten übernommen. Es gibt keine manuelle Freigabe.

## Adressen

`alexseeed/werbemail-sperrliste` steht für den Wert `repo` in `scripts/community.json`.

| Was | URL |
|---|---|
| Repository | `https://github.com/alexseeed/werbemail-sperrliste` |
| Sperrliste (txt) | `https://raw.githubusercontent.com/alexseeed/werbemail-sperrliste/main/data/sperrliste.txt` |
| Sperrliste mit Gruppen (csv) | `…/main/data/sperrliste.csv` – Spalten: domain, gruppe, melder, bestaetigt, erste_meldung, letzte_meldung |
| Erfahrungswerte (json) | `…/main/data/statistik.json` – je Gruppe: domains, melder, bestaetigt, erste/letzte_meldung, kanzlei_domains (Liste), forderung, art82_gefordert, vorgehen, status (jeweils Wert → Anzahl) |
| Melden ohne Skript | `https://github.com/alexseeed/werbemail-sperrliste/issues/new?template=meldung.yml&domains=…&kanzlei_domain=…&monat=…&vorgehen=…` |

Netzwerk: Das Lesen braucht `raw.githubusercontent.com`. Das Melden braucht `script.google.com` (Relay) und hilfsweise `github.com`.

## Wie Meldungen in die Liste kommen

```
Skill (sperrliste.py melden) ──POST──► Relay (Google Apps Script, hält das GitHub-Token)
                                          │ prüft: Format, Schutzliste, DNS, Rate-Limit
                                          ▼
                              data/meldungen/JJJJ/MM/M-….json  (eine Datei je Meldung)
                                          │ GitHub Action „Sperrliste bauen“
                                          ▼
                     sperrliste.txt · sperrliste.csv · statistik.json
```

Der Nutzer braucht kein Konto und kein Token. Hilfsweise geht die Meldung über ein Issue-Formular. Daraus macht eine Action ebenfalls eine Meldungsdatei. Dort ist der GitHub-Name des Meldenden öffentlich sichtbar.

## Was übermittelt wird – und was nie

| Feld | Inhalt | Beispiel |
|---|---|---|
| domains | alle belegbar zugehörigen Domains des Abmahners (max. 15) | beispiel-immobilien.example, beispiel-immo.example |
| kanzlei_domain | Domain der abmahnenden Kanzlei, leer bei Freemail | kanzlei-exempel.example |
| monat | Monat der Abmahnung | 2026-09 |
| forderung | 0 · 1-500 · 500-1000 · 1000-2000 · 2000-5000 · >5000 · unbekannt | 1000-2000 |
| art82 | ja / nein | ja |
| vorgehen | Codes, siehe unten | UE_MODIFIZIERT,KOSTEN_ABGELEHNT |
| status | siehe unten | offen |
| melder_domain | eigene Domain des Nutzers. Wird **nicht** gespeichert, sondern nur zur Berechnung eines anonymen Schlüssels verwendet (HMAC mit geheimem Salt). | eigene-firma.example |

**Nie:** E-Mail-Adressen (auch nicht gehasht), Namen, Aktenzeichen, Anschriften, Telefonnummern, exakte Beträge, Freitexte, Wertungen, Name des Nutzers. Jede Meldung, die „@“ enthält, wird abgelehnt.

**Vorgehen-Codes:** UE_MODIFIZIERT · UE_ORIGINAL · UE_VERWEIGERT · ART82_ABGELEHNT · ART82_GEZAHLT · KOSTEN_ABGELEHNT · KOSTEN_GEZAHLT · KOSTEN_VERGLEICH · AUSKUNFT_ERTEILT · WEBSITE_BLOCK · ANWALT_BEAUFTRAGT

**Status:** offen · keine_reaktion · erledigt_ohne_zahlung · erledigt_mit_zahlung · vergleich · mahnbescheid · klage · unbekannt

## Gruppen und „bestätigt“

- Domains, die in einer Meldung gemeinsam genannt werden, bilden eine **Gruppe**. Gruppen verbinden sich meldungsübergreifend über gemeinsame Domains. Meldet A `x.de, y.de` und B `y.de, z.de`, entsteht die Gruppe `x.de, y.de, z.de`.
- Je Melder zählt für Statistik und Status nur seine **jüngste** Meldung zu einer Gruppe. Eine Statusänderung ist deshalb einfach eine neue Meldung derselben Domains.
- **Bestätigt** = mindestens zwei unabhängige Melder.

## Zugehörige Domains ermitteln (Phase 1)

| Quelle | Vorgehen |
|---|---|
| Zieladresse der beanstandeten Mail | Domain hinter dem „@“ (außer Freemail) |
| Abmahnschreiben | Domains im Briefkopf, in der Signatur und in der Mail-Kopie |
| Website des Abmahners | Impressum (weitere Marken, Shops, Landingpages), Footer-Links, `curl -sIL https://domain` für Weiterleitungen |
| Handelsregister / Northdata | weitere Firmen derselben Person. Nur aufnehmen, wenn dieselbe Anschrift **und** dasselbe Geschäft vorliegen. |

Nur aufnehmen, was belegbar demselben Abmahner gehört. Im Zweifel weglassen: Eine falsche Domain sperrt ein unbeteiligtes Unternehmen.

**Nie melden:**

- Freemail-Anbieter (gmail.com, web.de, gmx.de, t-online.de …)
- Hosting- und Shop-Plattformen (myshopify.com, wixsite.com, jimdosite.com, github.io …)
- Portale (immobilienscout24.de …)
- Behörden
- die Kanzlei als Abmahner
- die eigene Domain

Die Schutzliste `data/geschuetzt.txt` fängt das Gängigste ab, aber nicht alles.

## Automatische Prüfung (Relay und Build)

- gültiges Domainformat, Domain existiert im DNS
- nicht auf der Schutzliste und nicht auf der Widerspruchsliste (auch keine Subdomain davon)
- keine „@“, nur bekannte Codes, max. 15 Domains
- Rate-Limit: 60 Meldungen je Stunde insgesamt, 10 je meldendem Unternehmen und Tag
- Widerspruch: Domain in `data/widersprueche.txt`. Sie wird sofort aus allen Listen entfernt und nie wieder aufgenommen.

## Abgleich auswerten (Phase 1b)

- Treffer immer als **Erfahrungswerte aus Nutzermeldungen** kennzeichnen, ungeprüft und ohne Prognose.
- Unbestätigte Gruppen (1 Melder) mit besonderer Vorsicht nennen.
- Die Erkenntnisse nie im Antwortschreiben erwähnen (siehe `05_fallstricke.md`).
- Weitere Domains der Gruppe in die eigene Sperrliste und in die Bitte um Mitteilung aller Domains übernehmen.

## Datenschutz und Haftung

- Domains von Unternehmen sind meist keine personenbezogenen Daten. Ausnahme: Einzelunternehmer mit Namensdomain (z. B. `max-mustermann.de`). Für sie gelten Art. 15–21 DSGVO; Anfragen gehen an den Betreiber (`NUTZUNGSBEDINGUNGEN.md`).
- Rechtsgrundlage ist das berechtigte Interesse (Art. 6 Abs. 1 lit. f DSGVO): Unternehmen, die keine Werbung wollen, sollen nicht erneut angeschrieben werden. Ein Eintrag sagt nichts darüber aus, ob eine Abmahnung berechtigt war.
- Der Meldende ist für die Richtigkeit verantwortlich. Bewusst falsche Meldungen, etwa über Wettbewerber, sind unzulässig.
