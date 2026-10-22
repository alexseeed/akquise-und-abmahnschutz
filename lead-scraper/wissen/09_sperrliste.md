# Community-Sperrliste

**Zweck:** wie die Sperrliste funktioniert, wie sie in jedem Pfad wirkt, wie gemeldet und widersprochen wird.
**Für wen:** Nutzer, Betreiber und KI-Modelle.
**Verwandt:** `10_abmahnung-was-tun.md` · `08_versand-und-recht.md` · Repository `werbemail-sperrliste` (README, EINRICHTUNG, WIDERSPRUCH)

---

## Was sie ist

Eine öffentliche Liste von **Domains**, deren Unternehmen nach einer Werbe-E-Mail abgemahnt haben.

- Gesperrt wird immer die **ganze Domain** mit allen Subdomains und allen E-Mail-Adressen darunter.
- Zusammengehörige Domains desselben Unternehmens bilden eine Gruppe.
- Die Liste liegt in einem GitHub-Repository und **ergänzt sich selbst**: Jede Meldung wird automatisch geprüft und in wenigen Minuten übernommen.

Ein Eintrag bedeutet nur: Dieses Unternehmen möchte keine Werbe-E-Mails. Er sagt nichts darüber, ob eine Abmahnung berechtigt war.

## Wie sie in den Pfaden wirkt

| Pfad | Abgleich | Ergebnis |
|---|---|---|
| Google Maps | automatisch bei jedem `export` | Treffer nur in `5_gesperrt_sperrliste_….csv` |
| Amazon und alle weiteren | `python3 werkzeuge/sperrliste_abgleich.py <liste.csv>` als letzte Phase | `_bereinigt.csv` / `_gesperrt.csv` |
| eigenes Versandtool | Sperrliste importieren: `https://raw.githubusercontent.com/alexseeed/werbemail-sperrliste/main/data/sperrliste.txt` | Domain-Sperre |

Ist die Liste nicht erreichbar, wird die letzte lokale Kopie genutzt. Gibt es keine, wird **nicht** ausgeliefert. Das ist Absicht: Lieber kein Export als ein ungeprüfter.

## Melden – Bedingung der Nutzung

Wer abgemahnt wird, meldet den Abmahner. Der Skill `abmahnung-werbemail-abwehr` macht das am Ende jedes Falls automatisch und zeigt vorher, was gesendet wird.

| Gemeldet wird | Nie gemeldet wird |
|---|---|
| Domains des Abmahners und seine zugehörigen Domains (mit Beleg) | E-Mail-Adressen, Namen, Aktenzeichen, Schriftsätze |
| Domain der Kanzlei | der Name des meldenden Unternehmens |
| Monat, Forderungsspanne, Art. 82 ja/nein, Vorgehen, Status | Freitexte, Wertungen |

Die Domain des meldenden Unternehmens dient nur der Berechnung eines anonymen Schlüssels. So lassen sich unabhängige Meldungen zählen. Gespeichert wird sie nicht.

**Bestätigt** heißt: mindestens zwei unabhängige Unternehmen haben dieselbe Domain gemeldet.

## Schutz vor Missbrauch

- Jede gemeldete Domain muss im DNS existieren.
- **Schutzliste:** Freemail-Anbieter, große Plattformen und Behörden sind nie sperrbar.
- **Widerspruchsliste:** Nach einem Widerspruch wird eine Domain entfernt und nie wieder aufgenommen.
- Meldungen dürfen keine „@“ und keine Freitexte enthalten.
- Höchstgrenzen je Stunde und je meldendem Unternehmen.

## Widerspruch

Gelistete Unternehmen können jederzeit widersprechen (`WIDERSPRUCH.md` im Repository). Der Betreiber trägt die Domain in die Widerspruchsliste ein; sie verschwindet sofort aus allen Listen.

## Grenzen

- Ohne Moderation sind **Falschmeldungen möglich**. Die harmlose Wirkung eines Eintrags (nur Werbe-Sperre) begrenzt den Schaden.
- Firmen **ohne eigene Website** (z. B. manche Amazon-Seller) lassen sich nicht abgleichen.
- Die Liste schützt nur vor **bekannten** Abmahnern. Sie macht Kaltakquise nicht zulässig (`08`).
