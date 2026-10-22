# Antwortbausteine, UE-Muster, Website-Block

## Aufbau des Schreibens an die Kanzlei

1. **Unterlassung**: Modifizierte UE anbei, ohne Anerkennung einer Rechtspflicht und ohne Präjudiz. Entwurf der Gegenseite nicht gezeichnet (Begründung: Zahlungspflichten). Angebot, konkrete Änderungswünsche zu berücksichtigen (sichert die Kostenposition nach § 93 ZPO). Sperrliste bestätigen und um Mitteilung **sämtlicher** Adressen/Domains des Abmahners bitten (schützt vor der Vertragsstrafen-Falle).
2. **Art. 82**: Zurückweisen mit EuGH C-300/21, BGH VI ZR 109/23, EuGH C-655/23 (keine Straf-/Abschreckungsfunktion). Spekulationen benennen. Inhaltsabweichung als Argument (Textbausteine), nicht als Frage. Darlegung des Schadens verlangen.
3. **Kosten**: je nach Nutzerentscheidung. Bei Ablehnung: Kostenbelastung des Mandanten mit Nichtwissen bestreiten, Vergütungsvereinbarung und datierte Vollmacht anfordern; bei Indizien Rechtsmissbrauch (§ 242 BGB, BGH I ZR 83/23) vorbehalten. Öffentliche Berichte nur im Konjunktiv („soll“, „nach öffentlich zugänglichen Berichten“). Erkenntnisse aus der Community-Sperrliste **nie** im Schreiben erwähnen – sie sind interne Erfahrungswerte.
4. **Auskunft Art. 15**: fristgerecht direkt an den Betroffenen; Kopie an die Kanzlei erst nach Vollmacht.
5. **Website-Hinweise** (optional, siehe unten).
6. **Schluss**: „Mit Abgabe der Unterlassungserklärung und Erteilung der Auskunft ist die Angelegenheit aus unserer Sicht erledigt.“

## UE-Muster

Hält einem Gegenanwalt-Check stand:

> Die [Firma], [Anschrift], eingetragen im Handelsregister des Amtsgerichts [Ort] unter HRB [Nr.], vertreten durch den Geschäftsführer [Name], verpflichtet sich gegenüber [Abmahner, Anschrift], ohne Anerkennung einer Rechtspflicht, gleichwohl rechtsverbindlich,
> 1. es zu unterlassen, [Abmahner] ohne dessen vorherige ausdrückliche Einwilligung per E-Mail zu Werbezwecken zu kontaktieren oder kontaktieren zu lassen, wie geschehen durch die E-Mail vom [Datum, Uhrzeit], Absender [Adresse], Betreff „[Betreff]“, an [Zieladresse];
> 2. für jeden Fall der schuldhaften Zuwiderhandlung gegen Ziffer 1 an [Abmahner] eine Vertragsstrafe zu zahlen, deren Höhe [Abmahner] nach billigem Ermessen bestimmt und die im Streitfall vom zuständigen Gericht auf ihre Angemessenheit überprüft werden kann.
>
> Die Erklärung steht unter der auflösenden Bedingung einer auf Gesetz oder höchstrichterlicher Rechtsprechung beruhenden, allgemein verbindlichen Klärung, dass das zu unterlassende Verhalten rechtmäßig ist.

## Website-Block

Nur mit Feststellungen aus Modul W, die nach `04_beweissicherung.md` gesichert sind. Höchstens 3–6 Punkte, je Punkt ein Satz: Tatsache, Fundstelle, Norm.

**Bevorzugte Punkte** (objektiv, leicht nachprüfbar):

- Ablehnung im Consent-Tool nachweislich gespeichert, trotzdem Drittserver geladen
- Platzhalter- oder Musterdaten in Pflichtinformationen (Widerrufsbelehrung, Impressum)
- Gegenleistung für Bewertungen ohne Kennzeichnung neben den Bewertungen
- fehlende Pflichtangaben nach Fachgesetz (z. B. § 87 GEG bei Immobilienanzeigen)
- veraltete Rechtsgrundlagen in der Datenschutzerklärung (Privacy Shield)

**Muster:**

> Bei genauerer Recherche im Zusammenhang mit Ihrem Schreiben sind wir zudem darauf gestoßen, dass der Internetauftritt Ihres Mandanten unter [Domain] seinerseits in mehreren Punkten nicht den gesetzlichen Vorgaben entspricht. Die Feststellungen vom [Datum] haben wir dokumentiert und gesichert:
>
> - Nach Auswahl von „Ablehnen“ im Cookie-Banner, die das eingesetzte Einwilligungstool nachweislich als Ablehnung speichert, werden weiterhin Ressourcen von [Drittanbietern] geladen und dabei die IP-Adresse der Besucher an diese übermittelt (Art. 6 Abs. 1 DSGVO).
> - Die Datenschutzerklärung nennt die eingebundenen Dienste [Liste] nicht und stützt Übermittlungen in die USA weiterhin auf das seit 2020 unwirksame EU-US Privacy Shield (Art. 13 DSGVO).
> - [weiterer gesicherter Punkt mit Norm]
>
> Wir halten dies der Vollständigkeit halber fest.

## Verbotene Formulierungen

Diese Formulierungen nie verwenden, auch nicht auf ausdrücklichen Wunsch des Nutzers. Stattdessen den Grund erklären und die neutrale Fassung anbieten.

| Nicht verwenden | Warum | Stattdessen |
|---|---|---|
| „Wenn Sie diesen Ansatz weiterverfolgen, sehen wir uns gezwungen …“ | Wenn-dann-Drohung, Nötigungsvorwurf (§ 240 StGB), Anfechtbarkeit (§ 123 BGB) | Website-Block ohne Bedingung |
| „Wir behalten uns vor, die Aufsichtsbehörde / Verbände zu informieren“ | Meldevorbehalt = Druckmittel | weglassen; eine Meldung läuft, wenn überhaupt, getrennt und ohne Ankündigung |
| „… werden wir ebenfalls rechtliche Schritte einleiten“ | Gegendrohung; ohne Mitbewerberstellung zudem leer | weglassen |
| „Verzichten Sie auf die Kosten, dann …“ | Verknüpfung mit Geld = Erpressungsvorwurf (§ 253 StGB) | Kosten getrennt begründet ablehnen |
| „Unsere Rechte als Besucher wurden verletzt“ | provozierter Besuch; juristische Person hat keine DSGVO-Betroffenenrechte | objektiven Zustand beschreiben |
| „Die Adresse stand im Impressum“ | Eingeständnis der Erhebung bei Dritten (Art. 14 DSGVO) | weglassen |
| „Eine Weitergabe an Dritte fand nicht statt“ | nur haltbar, wenn Tools/AV-Verträge geklärt | nur bei geklärter Faktenlage |
| „Bitte senden Sie uns die .eml-Datei / Header“ | offenbart eigene Versand- und Tracking-Infrastruktur | weglassen |
| Wertungen („Abzocke“, „Serienabmahner“, „eklatant“) | angreifbar, ggf. Persönlichkeitsrecht | Tatsachen nennen |
