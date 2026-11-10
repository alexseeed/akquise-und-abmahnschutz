# Änderungen

## 3.1 – Oktober 2026

Feste Linie statt schnellem Nachgeben. Grundlage sind die Erfahrungen aus zwei echten Fällen mit Gegenanwalt-Check.

- **Grundhaltung „schnell bei der Unterlassung, fest beim Geld“:**
  - Im ersten Schreiben wird nichts gezahlt.
  - Der Gegenstandswert wird immer geprüft und, wenn überhöht, gerügt.
  - Keine Angaben zur eigenen Versandinfrastruktur.
- **Kosten:** Standard ist jetzt Variante B, also Kostennote nach § 10 RVG und Zahlungsnachweis zuerst. Die Zahlung bleibt ausdrücklich offen (§ 250 BGB), die Antwort kommt binnen 14 Tagen. Volle Zahlung nur noch auf ausdrücklichen Wunsch.
- **Keine Rückfragen-Runde vor der UE.** Nachweisforderungen kommen in dasselbe Schreiben. Die zulässigen und die schädlichen Rückfragen sind aufgelistet.
- **Neue Prüfpunkte:**
  - Frist und Zugang
  - eigene Zitate des Abmahners gegen ihn wenden
  - Auskunftsrecht nur für natürliche Personen
  - überdehnte Klauseln wie „sonstige elektronische Nachrichten“
  - Rechtsform des Abgemahnten
  - frühere Abmahnungen
  - Geschäftsmodell der Kanzlei
  - eigene Angriffsfläche (Versanddomains)
- **Auskunft Art. 15:** Vollmacht oder anwaltliche Versicherung mit Frist anfordern, sonst verschlossener Umschlag über die Kanzlei. Nicht mehr direkt an die anwaltlich vertretene Person.
- **UE-Muster:**
  - „und ohne § 7 Abs. 3 UWG“
  - „Werbung mittels elektronischer Post“
  - „gleich an welche Adresse“
  - „wie mit Schreiben … beanstandet“
  - Variante für die GbR
- **Versand:**
  - Nie per Telefax, vorab nur per E-Mail.
  - Bei Nicht-Kaufleuten Schriftform mit Original per Einschreiben.
  - Bei der GbR unterschreiben alle Gesellschafter.
  - Feiertage einrechnen.
  - Neutrales Absender-Postfach, Briefkopf ohne Versanddomain.
- Neue **Textbausteine** in `references/02_antwortbausteine.md`. Dazu weitere verbotene Formulierungen, Fallstricke und Rechtsprechung zum Gegenstandswert (AG München 142 C 1633/22, OLG Hamm 9 U 73/14 als Beschluss).
- Neue **Phase 10 „Nachgang“:** Kostennote, Mahnung, Änderungswünsche, Mahnbescheid.
- Musterfälle in `beispiele/01` und `02` auf die neue Linie umgestellt.

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
