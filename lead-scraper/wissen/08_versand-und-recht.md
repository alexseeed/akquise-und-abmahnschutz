# Versand und Recht – was vor dem ersten Kontakt klar sein muss

**Zweck:** die rechtlichen Rahmenbedingungen für Datensammlung und Ansprache, kompakt und ehrlich.
**Für wen:** Nutzer vor dem Versand und KI-Modelle, die Fragen dazu beantworten.
**Verwandt:** `09_sperrliste.md` · `10_abmahnung-was-tun.md` · Skill `abmahnung-werbemail-abwehr` (Rechtsprechung im Detail)
**Stand:** 2026-10-04, Deutschland · **Prüfen bis:** 2027-04-04. **Keine Rechtsberatung.** Im Zweifel anwaltlich prüfen lassen.

---

## Das Wichtigste in drei Sätzen

1. **E-Mail-Werbung ohne vorherige ausdrückliche Einwilligung** ist eine unzumutbare Belästigung (§ 7 Abs. 2 Nr. 2 UWG). Das gilt auch gegenüber Unternehmen, auch bei einer einzigen Mail, auch an info@-Adressen aus dem Impressum.
2. Das Risiko ist eine **Abmahnung**:
   - durch Mitbewerber (§ 8 UWG),
   - oder durch den Empfänger selbst über §§ 823, 1004 BGB (Eingriff in den eingerichteten und ausgeübten Gewerbebetrieb).

   Dazu kommen oft Forderungen nach DSGVO-Auskunft und Schadensersatz.
3. **Die Sperrliste senkt das Risiko** wiederholter Abmahnungen durch bekannte Abmahner. Sie macht Kaltakquise per E-Mail **nicht zulässig**.

## Kanäle im Vergleich (B2B)

| Kanal | Regel | Einordnung |
|---|---|---|
| E-Mail, Fax | vorherige ausdrückliche Einwilligung nötig (§ 7 Abs. 2 Nr. 2 UWG). Ausnahme nur für Bestandskunden unter den engen Voraussetzungen des § 7 Abs. 3 UWG | höchstes Abmahnrisiko |
| Telefon | gegenüber Unternehmen genügt eine **mutmaßliche** Einwilligung (§ 7 Abs. 2 Nr. 1 UWG). Es muss ein konkreter, sachlicher Bezug zum Geschäft des Angerufenen bestehen. Gegenüber Verbrauchern ist eine ausdrückliche Einwilligung nötig | Einzelfallfrage |
| Brief | grundsätzlich zulässig, solange kein erkennbarer Widerspruch vorliegt | geringes Risiko |
| LinkedIn/Xing-Nachricht | Plattformregeln; massenhaft automatisiert oft unzulässig bzw. regelwidrig | Plattform- und Einzelfallfrage |

## Pflichtangaben in jeder Werbe-Nachricht

- **Absender klar erkennbar,** keine Verschleierung. Der Betreff darf den werblichen Charakter nicht verschleiern (§ 6 DDG, § 7 Abs. 2 Nr. 3 UWG).
- **Gültige Adresse,** über die der Empfänger weitere Nachrichten abbestellen kann (§ 7 Abs. 2 Nr. 3 UWG).
- **Rechtsträger und Anschrift** im Footer.
- **Keine fingierten Aufhänger** wie „Ein Kollege hat mich auf Sie aufmerksam gemacht“ oder ein falsches „AW:“/„WG:“ im Betreff. Das ist irreführend und leicht beweisbar.

## Datenschutz (DSGVO)

| Thema | Was gilt |
|---|---|
| **Personenbezug** | Namen der Geschäftsführung, persönliche E-Mail-Adressen (vorname.nachname@…) und Einzelunternehmer-Domains sind personenbezogene Daten. Firmendaten allein (info@, Firmenname) meist nicht. |
| **Rechtsgrundlage** | in der Regel berechtigtes Interesse (Art. 6 Abs. 1 lit. f, Erwägungsgrund 47). Verstößt die Ansprache gegen das UWG, trägt diese Abwägung kaum. |
| **Informationspflicht** | Werden Daten aus anderen Quellen erhoben (Google Maps, Impressum, Amazon), muss spätestens bei der ersten Kontaktaufnahme informiert werden (Art. 14 Abs. 3 lit. b). Das geht z. B. per Link zu einer Datenschutz-Seite mit Quelle, Zweck, Speicherdauer und Widerspruchsrecht. |
| **Widerspruch** | Widerspricht jemand der Direktwerbung, ist das endgültig (Art. 21 Abs. 2 und 3). Sofort sperren, in **allen** Systemen. |
| **Auskunft** | Anfragen nach Art. 15 innerhalb eines Monats vollständig beantworten: Quelle, Zwecke, Empfänger, Speicherdauer, Kopie der Daten. Dafür muss nachvollziehbar sein, woher jeder Lead stammt. Die Exporte enthalten dafür Keyword, Stadt, Quelle. |
| **Löschkonzept** | Rohdaten (`data/`, `exports/`, Archiv) nicht unbegrenzt aufbewahren; eine Frist festlegen. |
| **Auftragsverarbeitung** | Versandtool, CRM und Anreicherungsdienste verarbeiten Daten im Auftrag. AV-Verträge abschließen; bei Diensten außerhalb der EU die Übermittlungsgrundlage prüfen. |

## Nutzungsbedingungen der Datenquellen

- **Google Maps:** über einen Drittanbieter (Skael). Es gelten dessen Bedingungen und die von Google.
- **Amazon:** Automatisierte Abrufe können gegen die Amazon-Nutzungsbedingungen verstoßen. Risiko: Captcha oder Kontosperre (`04_pfad-amazon.md`).
- **Handelsregister und Wirtschaftsdatenbanken:** Abruf für Recherche üblich; massenhafte automatisierte Abrufe je nach Anbieter untersagt.
- **Jobbörsen, LinkedIn, Xing** (künftige Pfade): Scraping meist ausdrücklich untersagt.

## Vor dem ersten Versand – Checkliste

- [ ] Kanal und Rechtslage bewusst entschieden (siehe Tabelle oben)
- [ ] Nur bereinigte Listen; Sperrliste auch im Versandtool hinterlegt
- [ ] Absender, Footer, Abmeldeweg, Datenschutzhinweis nach Art. 14 vorhanden
- [ ] Keine fingierten Aufhänger in den Vorlagen
- [ ] Prozess für Widerspruch, Abmeldung und Auskunft steht (wer, wie schnell, in welchen Systemen)
- [ ] Leadquelle je Datensatz nachvollziehbar
- [ ] Bei einer Abmahnung: nicht vorschnell zahlen oder unterschreiben → `10_abmahnung-was-tun.md`
