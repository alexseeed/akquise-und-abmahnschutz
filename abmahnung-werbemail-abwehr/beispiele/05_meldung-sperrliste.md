# Beispiel: Meldung an die Community-Sperrliste (fiktiver Fall)

Fall aus `01_antwortschreiben.md`. Der Abmahner ist die Beispiel Immobilien GmbH. Die Kanzlei Exempel hat abgemahnt. Abgemahnt wurde die Muster Vertrieb GmbH (`muster-vertrieb.example`).

## Phase 1 – zugehörige Domains

| Domain | Quelle |
|---|---|
| beispiel-immobilien.example | Zieladresse der Mail, Impressum |
| beispiel-immo.example | Weiterleitung auf beispiel-immobilien.example (`curl -sIL`) |
| beispiel-hausverwaltung.example | Impressum: gleicher Rechtsträger, gleiche Anschrift |

Nicht aufgenommen:

- `beispiel.immobilienscout24.de`: Portal, geschützt.
- `gmx.de`: privates Postfach des Geschäftsführers im Briefkopf, Freemail.

## Phase 1b – Abgleich

```bash
python3 scripts/sperrliste.py pruefen --domain beispiel-immobilien.example beispiel-immo.example beispiel-hausverwaltung.example \
  --kanzlei-domain kanzlei-exempel.example
```

```
Sperrliste: 412 Domains aus 530 Meldungen
  GELISTET  beispiel-immobilien.example → Gruppe beispiel-immobilien.example
  neu       beispiel-immo.example
  neu       beispiel-hausverwaltung.example

Gruppe beispiel-immobilien.example
  Domains:            beispiel-immobilien.example, beispiel-makler.example
  Unabhängige Melder: 3 (bestätigt)
  Zeitraum:           2026-05 bis 2026-09
  Kanzleien:          kanzlei-exempel.example
  Forderung (€):      1000-2000 ×2, 500-1000 ×1
  Art. 82 gefordert:  ja ×3
  Vorgehen:           UE_MODIFIZIERT ×3, ART82_ABGELEHNT ×3, KOSTEN_ABGELEHNT ×2, KOSTEN_GEZAHLT ×1
  Ausgang:            keine_reaktion ×2, erledigt_mit_zahlung ×1
```

Was Claude daraus macht:

- `beispiel-makler.example` in die eigene Sperrliste und die UE übernehmen.
- Dem Nutzer die Erfahrungswerte zeigen, als Erfahrungswerte gekennzeichnet.
- Im Antwortschreiben nichts davon erwähnen.

## Phase 9 – Meldung

Was Claude dem Nutzer schreibt (sinngemäß):

> Wie zu Beginn erwähnt, melde ich den Abmahner jetzt an die Community-Sperrliste:
> **Domains** beispiel-immobilien.example, beispiel-immo.example, beispiel-hausverwaltung.example · **Kanzlei** kanzlei-exempel.example · **2026-09** · Forderung 1.000–2.000 € · Art. 82 gefordert · Vorgehen: modifizierte UE, Art. 82 und Kosten abgelehnt, Auskunft erteilt · Status offen.
> Ihre Domain dient nur der Berechnung eines anonymen Schlüssels und wird nicht gespeichert.

```bash
python3 scripts/sperrliste.py melden \
  --domains beispiel-immobilien.example beispiel-immo.example beispiel-hausverwaltung.example \
  --kanzlei-domain kanzlei-exempel.example --monat 2026-09 --forderung 1000-2000 --art82 ja \
  --vorgehen UE_MODIFIZIERT,ART82_ABGELEHNT,KOSTEN_ABGELEHNT,AUSKUNFT_ERTEILT --status offen \
  --melder-domain muster-vertrieb.example
```

```
Gesendet. Meldungs-ID M-20261004-3fa91c2e. Übernahme in die Liste in wenigen Minuten.
```

## Zwei Monate später

Die Gegenseite hat sich nicht mehr gemeldet. Dieselben Domains werden mit `--status keine_reaktion` erneut gemeldet. Für die Statistik zählt automatisch nur die jüngste Meldung dieses Melders.

## Wenn der Nutzer widerspricht

> Verstanden, ich sende nichts. Kurzer Hinweis: Die kostenlose Nutzung des Skills setzt die Meldung voraus (NUTZUNGSBEDINGUNGEN.md). Sie können sie jederzeit nachholen.

Danach geht es ohne weitere Nachfrage weiter.
