# Änderungen

## 3.0 – Oktober 2026

- Community-Sperrliste auf ein **GitHub-Repository** umgestellt (vorher Google Sheet + Formular + Moderation).
- Gesperrt werden nur noch **Domains** mit allen Subdomains. Keine E-Mail-Adressen und keine Hashes mehr.
- Neuer Schritt in Phase 1: **zugehörige Domains ermitteln**, mit Quelle je Domain.
- Phase 9: Meldung ist **Nutzungsbedingung**. Sie wird angezeigt und automatisch über ein Relay gesendet, ohne Token beim Nutzer. Ersatzweise gibt es einen vorausgefüllten GitHub-Issue-Link.
- Automatische Prüfung statt Moderation:
  - Format, DNS, Schutzliste, Widerspruchsliste
  - Rate-Limits
  - anonymer Melder-Schlüssel
  - „bestätigt“ ab zwei Meldern
- `scripts/sperrliste.py` ersetzt `blockliste.py` (pruefen, melden, laden, abgleich); neu `scripts/community.json` und `NUTZUNGSBEDINGUNGEN.md`.
- Ersetzt: `references/06_community-sperrliste.md`, `beispiele/05_meldung-sperrliste.md`.

## 2.1 – Oktober 2026

- Keine Einrichtung mehr: Token, `config.json` und Web-Schnittstelle entfallen.
- Community-Blockliste: öffentlich lesbares Google Sheet, Meldung per vorausgefülltem Google-Formular (der Nutzer sendet selbst), Moderation durch den Betreiber vor der Veröffentlichung.
- `scripts/blockliste.py` ersetzt `register_client.py` (pruefen, meldelink, statuslink, sperrliste, abgleich, hash).
- Funktioniert eingeschränkt auch ohne Code-Ausführung (Abgleich über Domain, Link manuell gebaut).

## 2.0 – Oktober 2026

- Projektstruktur mit `references/`, `listen/`, `beispiele/`, `scripts/`; SKILL.md als schlanke Ablaufsteuerung.
- Modul W „Website-Verstöße des Abmahners“ mit Prüfraster, Beweissicherung (Browser-Mitschnitt, Seitensicherung, SHA-256, zwei RFC-3161-Zeitstempel) und Protokoll-Gliederung.
- Referenzlisten bekannter Drittserver (68 Einträge) und Consent-Tools (15 Einträge).
- Liste verbotener Formulierungen; Wenn-dann-Drohungen werden auch auf Nutzerwunsch nicht formuliert.
- Rechtsprechung ergänzt: EuGH C-21/23, LG München I 3 O 17493/20, EuGH C-311/18/DPF, VO (EU) 2024/3228, § 356a BGB; Amtsgerichtszuständigkeit bis 10.000 € seit 01.01.2026.

## 1.0

- Prüfung, Recherche, Gegenanwalt-Check, Antwortschreiben und modifizierte UE als PDF.
