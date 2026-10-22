# Prüfraster: Website des Abmahners (Modul W)

Ziel: den Webauftritt des Abmahners prüfen, Verstöße objektiv und gerichtsverwertbar sichern und – falls gewünscht – wenige belastbare Punkte neutral im Antwortschreiben festhalten. Das Modul ist ein Zusatz, kein Hebel gegen die Unterlassung. Es läuft vollständig **vor** dem Versand des Antwortschreibens.

## M1 – Rahmen klären (vor jeder Prüfung)

- **Wer kann aus den Feststellungen etwas machen?**
  - Ein **Mitbewerber** kann UWG-Verstöße selbst abmahnen, seit EuGH C-21/23 auch DSGVO-Verstöße, soweit sie Marktverhaltensregeln betreffen. Das ist ein **eigenes, getrenntes Verfahren** über einen Anwalt, nie Teil des Antwortschreibens.
  - Ein **branchenfremdes** Unternehmen ist kein Mitbewerber (§ 8 Abs. 3 Nr. 1 UWG). Eine juristische Person hat keine DSGVO-Betroffenenrechte. Für sie bleiben die neutrale Erwähnung im Schreiben und – getrennt davon und ohne Ankündigung – eine Meldung an die Datenschutzaufsicht.
- **Kein eigener Schaden.** Feststellungen belegen den objektiven Zustand der Website. Sie dürfen nicht als eigene Rechtsverletzung dargestellt werden. Ein eigens zur Recherche durchgeführter Besuch wäre als provoziert angreifbar (vgl. EuGH C-526/24 zu provozierten Ansprüchen).
- **Grenzen der Recherche:** nur öffentlich zugängliche Seiten wie ein normaler Besucher. Keine Formulare absenden, kein Login, keine Umgehung von Bot-Schutz, keine Last erzeugen (Pausen zwischen Abrufen).

## M2 – Prüfraster

Einen Punkt nur dann als Befund führen, wenn er mit Datei und Fundstelle belegt ist. Die Spalte „Typischer Fehlgriff“ ist verbindlich.

| Bereich | Was prüfen | Norm | Typischer Fehlgriff |
|---|---|---|---|
| Drittressourcen vor Einwilligung | Laden Google Fonts, Maps, YouTube, Tag Manager/Analytics, Bewertungs-Widgets, Karten, Chat, 3D-Touren, Bot-Schutz **vor** jeder Banner-Interaktion? Abgleich mit `listen/drittanbieter.csv` | Art. 6 Abs. 1 DSGVO (IP-Übermittlung); § 25 TDDDG nur bei Zugriff auf das Endgerät; LG München I 3 O 17493/20 | Alles pauschal unter § 25 TDDDG fassen. Antwortcodes 401/403/404 des Drittservers als „nicht geladen“ werten – die Anfrage samt IP ist trotzdem angekommen. |
| Ablehnung wird ignoriert | Nach „Ablehnen“: Was speichert das Consent-Tool (siehe `listen/consent-tools.csv`)? Welche Drittserver laden auf Folgeseiten trotzdem? | wie oben; Art. 7 DSGVO | Das bloße Laden eines Skripts (z. B. gtag.js) als Tracking bezeichnen, obwohl keine Messaufrufe (`/collect`, `/g/collect`) beobachtet wurden – genau so beschreiben, wie gesehen. |
| Datenschutzerklärung | Alle festgestellten Dienste genannt? Veraltete Angaben: Privacy Shield, „Google Inc.“, „Sperrung“, altes BDSG/TMG? Speicherdauern? Nicht existierende Funktionen (Registrierung, Newsletter)? | Art. 13 DSGVO; EuGH C-311/18; EU-US DPF seit 10.07.2023 | Fehlende Nennung behaupten, ohne die DSE per Textsuche gegengeprüft zu haben. |
| Impressum | Pflichtangaben nach § 5 DDG; Aufsichtsbehörde bei erlaubnispflichtigem Gewerbe; Link zur EU-OS-Plattform | § 5 DDG; VO (EU) 2024/3228 | Den veralteten OS-Link als schweren Verstoß darstellen – geringes Risiko. |
| Widerrufsbelehrung | Platzhalter-/Musterdaten, Warentext für Dienstleistungen, fehlender Wertersatzhinweis; Widerrufsbutton | § 312d BGB, Art. 246a EGBGB; § 356a BGB | Relevanz nur, wenn tatsächlich Verbraucherverträge im Fernabsatz geschlossen werden; Button nur bei Vertragsschluss über eine eigene Online-Oberfläche. |
| AGB | Beweislastumkehr, pauschalierter Schadensersatz ohne Gegenbeweis, Datenschutz-Einwilligung per AGB, überraschende Klauseln | §§ 305c, 307–309 BGB; Art. 7 DSGVO | AGB-Kontrolle bei reinen B2B-Verträgen wie bei Verbrauchern behandeln. |
| Bewertungen | Gegenleistung für Bewertungen (Prämie, Spende, „Baum pro Bewertung“) ohne Kennzeichnung; Vorsortierung (zufriedene Kunden zu Google, unzufriedene zu internem Formular); Hinweis zur Echtheitsprüfung; Klarnamen von Bewertenden | § 5a Abs. 4, § 5b Abs. 3 UWG; Anhang Nr. 23b/23c UWG; Art. 6 DSGVO | Einen Hinweis „Echtheit nicht geprüft“ als Verstoß werten – er erfüllt gerade die Informationspflicht. |
| Formulare & Downloads | Pflicht-Einwilligung statt Vertragsanbahnung; Erhebung von Daten Dritter (z. B. Tippgeber-Formulare mit Telefonnummern fremder Personen); übermäßige Abfragen in Download-Formularen (Vorstrafen, Familienstand, Ausweiskopien) | Art. 5, 6, 14 DSGVO; § 7 Abs. 2 Nr. 1 UWG bei anschließenden Werbeanrufen | Eine im Formular verlangte Einwilligung allein schon als Verstoß bezeichnen. |
| Branchenpflichten | Immobilien: Energieausweis-Angaben (§ 87 GEG); Preise: PAngV; Gesundheit: HWG; Finanzen: Pflichtangaben je Erlaubnis | jeweiliges Fachgesetz | § 87 GEG rügen, ohne zu wissen, ob ein Energieausweis vorliegt; mehr verlangen, als die Norm vorschreibt. |
| Werbeaussagen | Alleinstellungs-/Spitzenbehauptungen, Werbung mit Selbstverständlichkeiten, widersprüchliche Zahlen auf verschiedenen Seiten, ungekennzeichnete Testimonials | §§ 5, 5a UWG, Anhang Nr. 10 UWG | Unbelegte Gegenbehauptungen („Mitgliedschaft im Verband X ist falsch“) statt „konnte nicht verifiziert werden“. |

Vor jeder Normzuordnung eine Websuche zum aktuellen Stand machen und Fundstellen nur nennen, wenn sie geprüft sind.

## M3 – Gewichtung der Befunde

| Stufe | Kriterien | Beispiele |
|---|---|---|
| hoch | objektiv, maschinell belegt, eindeutige Norm, leicht nachprüfbar | Ablehnung gespeichert + Drittserver geladen; Musterdaten in Widerrufsbelehrung; fehlende § 87 GEG-Angaben |
| mittel | belegt, aber wertungsabhängig | unwirksame AGB-Klauseln; Bewertungsgegenleistung; DSE-Lücken |
| gering | belegt, aber geringe Relevanz | veralteter OS-Link; fehlende Bildnachweise |
| nicht verwenden | nicht belegbar oder in M2 als Fehlgriff markiert | Vermutungen über Mitgliedschaften; Folgerungen aus Antwortcodes |

Für den Website-Block nur Stufe „hoch“ und ausgewählte „mittel“-Punkte verwenden.
