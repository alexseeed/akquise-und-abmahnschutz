# Skill „Abmahnung Werbe-E-Mail – Prüfung & Abwehr“

Ein Claude-Skill für Unternehmen, die wegen einer Werbe-E-Mail (Cold-Mail) abgemahnt wurden. Claude prüft die Abmahnung, recherchiert Kanzlei und Rechtsprechung, gleicht den Abmahner mit der Community-Sperrliste ab und erstellt ein versandfertiges Antwortschreiben samt modifizierter Unterlassungserklärung als PDF. Optional prüft und sichert Claude Rechtsverstöße auf der Website des Abmahners.

**Wichtig:** Der Skill liefert Recherche und Entwürfe. Er ersetzt keine anwaltliche Beratung. Bei Klage, einstweiliger Verfügung, hohen Beträgen oder Unsicherheit einen Anwalt einschalten.

## Installation (2 Minuten, keine Einrichtung)

1. In Claude: **Einstellungen → Funktionen → Skills → Skill hochladen** und diese ZIP-Datei auswählen.
2. Fertig. Empfohlen ist eingeschaltete Code-Ausführung; ohne sie funktioniert der Skill auch, nur ohne Beweissicherung; die Meldung erfolgt dann über einen vorausgefüllten GitHub-Link.

Für Sperrlisten-Abgleich, Meldung und Beweissicherung muss die Umgebung `raw.githubusercontent.com`, `script.google.com`, die Zeitstempeldienste (`zeitstempel.dfn.de`, `timestamp.sectigo.com`) und die Website des Abmahners erreichen dürfen.

## Nutzung

Abmahnung als PDF in den Chat legen und schreiben: „Ich habe diese Abmahnung wegen einer Werbe-Mail bekommen, bitte prüfen.“ Claude führt durch die Schritte und fragt nur nach, was sich nicht recherchieren lässt.

## Nutzungsbedingung: Gegenseitigkeit

Der Skill ist kostenlos. Im Gegenzug meldet er am Ende jedes Falls die Domains des Abmahners an die **Community-Sperrliste**. Was übermittelt wird, zeigt Claude vor dem Senden an. Details stehen in [NUTZUNGSBEDINGUNGEN.md](NUTZUNGSBEDINGUNGEN.md).

## Community-Sperrliste

Ein öffentliches GitHub-Repository: https://github.com/alexseeed/werbemail-sperrliste

- **Inhalt:** Domains von Unternehmen, die wegen einer Werbe-E-Mail abgemahnt haben. Gesperrt wird jeweils die ganze Domain mit allen Subdomains und Adressen. Zusammengehörige Domains bilden eine Gruppe.
- **Gemeldet** werden nur Domains und Sachangaben: Kanzlei-Domain, Monat, Forderungsspanne, Vorgehen, Status. Keine E-Mail-Adressen, keine Namen, nicht Ihr Firmenname.
- **Automatisch:** Meldungen werden geprüft und in wenigen Minuten übernommen. Geprüft wird auf Format, existierende Domain, Schutzliste für Freemail und Plattformen sowie Missbrauchsgrenzen. Eine manuelle Freigabe gibt es nicht. Ab zwei unabhängigen Meldungen gilt ein Eintrag als „bestätigt“.
- **Vor jeder Kampagne:**
  ```bash
  python3 scripts/sperrliste.py laden --out sperrliste.txt                      # Domain-Sperre importieren
  python3 scripts/sperrliste.py abgleich --kontakte kontakte.csv --spalte email   # Kontaktliste bereinigen
  ```
  Ohne Skript: `https://raw.githubusercontent.com/alexseeed/werbemail-sperrliste/main/data/sperrliste.txt` direkt im Versand- oder CRM-Tool als Domain-Sperrliste hinterlegen.

## Ordnerstruktur

```
abmahnung-werbemail-abwehr/
├── SKILL.md                    Ablaufsteuerung für Claude
├── README.md · CHANGELOG.md · NUTZUNGSBEDINGUNGEN.md
├── references/                 Fachwissen, wird phasenweise geladen
├── listen/                     Drittserver und Consent-Tools (fest)
├── beispiele/                  fiktive Musterfälle
└── scripts/
    ├── sperrliste.py           Abgleich, Meldung, Sperrliste laden, Kontaktlisten-Abgleich
    ├── community.json          Repository und Relay der Sperrliste
    ├── sicherung_netzwerk.py   Browser-Mitschnitt in drei Szenarien
    ├── sicherung_seiten.py     Seitensicherung (HTML, PNG, PDF, MHTML)
    ├── auswertung.py           Zuordnung Drittserver + Consent-Status
    └── integritaet.sh          SHA-256 + RFC-3161-Zeitstempel
```

## Hinweise

- Die Inhalte entsprechen dem Rechtsstand Oktober 2026; Claude prüft vor jeder Nutzung per Websuche auf Neuerungen. Eine Gewähr für Vollständigkeit und Richtigkeit wird nicht übernommen.
- Widerspruch oder Löschung eines Eintrags in der Sperrliste: siehe `WIDERSPRUCH.md` im Repository.
