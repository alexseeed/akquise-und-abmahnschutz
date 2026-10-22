# Personalisierungs-Builder (E-Commerce) – Mailtext und persönlicher Einstiegssatz

> **Für dich (Claude), nicht für den Nutzer.** Anforderung **E6** aus `ABLAUF.md`, Phase 1.
> Pflicht, solange `DO_PERSONALISIERUNG=true` (Standard). Ohne gespeicherten Mailtext und gespeicherte Personalisierungs-Anweisung bricht `python3 -m ecom run` vor Stufe 2e ab, bevor etwas kostet.
>
> **Ergebnis:**
> - `auftraege/<auftrag>_mailtext.txt`, gespeichert mit `python3 -m ecom set-mailtext <datei>`,
> - `auftraege/<auftrag>_personalisierung.txt`, gespeichert mit `python3 -m ecom set-prompt personalisierung <datei>`,
> - und ein Nutzer, der seine fertige Beispiel-Mail gesehen und bestätigt hat.
>
> Die Fachbegriffe hier (Prompt, Platzhalter, Stufe, JSON, Confidence) sind nur für dich. Der Nutzer hört sie nie. Statt „Platzhalter“ sagst du z. B. „Hier steht später bei jedem Shop der richtige Name.“
> Alle Befehle laufen aus `pfade/e-commerce/`. Auftragsdateien liegen im Arbeitsordner unter `auftraege/`. Im Skill-Ordner (`lead-scraper/`) ist das von dort aus `../../auftraege/`; wurde der Pfad in einen eigenen Arbeitsordner kopiert (`../../SKILL.md`, Schritt 1), `../auftraege/`. Die Befehle unten zeigen den ersten Fall. Fehlt der Ordner (frisches Paket), vor der ersten Datei anlegen: `mkdir -p ../../auftraege`.

---

## Was technisch feststeht

### Der Einstiegssatz (Stufe 2e)

- **Was das Modell sieht:** den Text der Startseite, `{{Bodytext Website}}`, gekürzt auf `BODYTEXT_MAX_CHARS` (Standard 8.192 Zeichen). Keine Unterseiten, keine Bilder, **keine Linkliste** (anders als im Google-Maps-Pfad).
- **Weitere Platzhalter (optional):**
  - `{{Mailtext}}`: der gespeicherte Mailtext. Damit weiß das Modell, was nach seinem Satz kommt, und wiederholt es nicht. **Immer einbauen.**
  - `{{Firmenname}}`: Firmenname aus dem Impressum.
  - Andere Platzhalter bleiben wörtlich stehen.
- **Antwort:** JSON mit `complimentText` (`prompts/personalisierung.schema.json`, unverändert).
- **Position:** Der Satz steht als eigener Absatz direkt nach der Anrede („Hallo Herr Müller,“ + Leerzeile). Er beginnt deshalb **klein**. Das ist die Clay-Konvention.
- **Clay-Original:** `prompts/personalisierung.txt` ist für deutsche Beratungen und Agenturen geschrieben, also für die falsche Zielgruppe. Es bleibt nur als Vorlage für Aufbau, Verbotsliste und Satzanfänge. Für Läufe wird es nie verwendet. Nicht ändern.

### Der Mailtext

**Dateiformat (UTF-8):** erste Zeile `Betreff: …`, dann eine Leerzeile, dann der Text.

**Erlaubte Platzhalter,** exakt so geschrieben (Groß- und Kleinschreibung, Leerzeichen, Umlaut):

| Platzhalter | wird bei Namen + Anrede zu | ohne Namen im Impressum (vor allem info@) |
|---|---|---|
| `{{Ansprache Formal}}` | Sehr geehrter Herr Müller | Sehr geehrte Damen und Herren |
| `{{Ansprache Normal}}` | Hallo Herr Müller | Hallo |
| `{{Ansprache Guten Tag}}` | Guten Tag Herr Müller | Guten Tag |
| `{{Ansprache Persönlich}}` | Hallo Max | Hallo |
| `{{Personalisierung}}` | der Einstiegssatz | der Einstiegssatz |
| `{{Firmenname}}` | Firmenname aus dem Impressum, sonst aus der Liste | wie links |
| `{{Website}}` | Adresse des Shops | wie links |
| `{{Videotitel}}` | Videotitel, nur mit `DO_VIDEO_TITLE=true`; gehört meist ins Videotool, nicht in die Mail | wie links |
| `{{Anrede}}`, `{{Vorname}}`, `{{Nachname}}` | Herr / Max / Müller | **leer.** Nicht im Text verwenden (auch nicht im Betreff) |

**Was `set-mailtext` prüft:** Die vollständige Liste der Fehler (Abbruch mit Exit-Code 2, nichts gespeichert) und Hinweise steht an einer Stelle: `../../wissen/07_lead-ausgabe-und-spalten.md`, Abschnitt E-Commerce. Dazu gehört, dass die Begrüßung die erste Zeile ist und `{{Personalisierung}}` direkt darunter steht. Danach zeigt es eine Vorschau mit einem erfundenen Beispiel-Lead (Herr Max Mustermann, Beispiel Shop GmbH, mit Beispielsatz per Sie).

**Im Export:** Liste 1 und 2 bekommen die Spalten `Betreff` und `Mailtext`, je Lead fertig ausgefüllt.

---

## Gesprächsregeln

Wie im Interview (`../../wissen/02_zielgruppen-interview.md`):

- **Eine Frage pro Nachricht.** Immer mit einem Beispiel aus der Shop-Welt und einem fertigen Vorschlag zum Bestätigen. Jede Frage in einem Satz beantwortbar.
- **„Weiß nicht“:** Vorschlag nehmen, bestätigen lassen, weiter. Nicht nachbohren.
- **Was in der Auftragsdatei steht, nicht erneut fragen.**
- **Nach jeder Runde** in eigenen Worten zusammenfassen und bestätigen lassen.
- **Keine Fachbegriffe** (Prompt, Platzhalter, Confidence, Stufe, JSON).
- **Den rechtlichen Hinweis zu § 7 UWG nicht wiederholen.** Er kam einmal im Interview.

**Budget:** so wenige Fragen wie möglich.

- Mit vorhandenem Mailtext: meist 3–4 Fragen (2.1, je eine pro fehlendem Pflichtteil, 3.1, 3.2). Das Problem (1.1) liest du aus dem Text ab und lässt es nur bestätigen.
- Mailtext gemeinsam schreiben: höchstens 8 Fragen (2.1, 1.1, 2.2–2.5, 3.1, 3.2), eine mehr, wenn A1 fehlt.

Dazu kommen die Bestätigungen. Die Schleife über den fertigen Text läuft, bis jeder Pflichtteil da ist oder unter „Vor dem Versand offen“ steht (siehe Pflichtteile) und der Nutzer ausdrücklich „passt“ sagt.

---

## Schritt 0 – Aus der Auftragsdatei übernehmen, nicht fragen

| Aus der Auftragsdatei | wofür hier |
|---|---|
| A1 Angebot | Angebotssatz in der Mail, ROLLE im Einstiegssatz |
| A2 Kanal, E5 Video | ob `{{Videotitel}}` erlaubt ist, ob der nächste Schritt „Video ansehen“ heißt |
| B1–B3 Wunschkunde | Zielgruppe im Einstiegssatz, Beispiele aus der richtigen Shop-Welt |
| D1 Länder | Region in der ROLLE |
| D3 Ansprechpartner | Mit info@: Nennt das Impressum keine Geschäftsführung, bleibt die Anrede neutral („Hallo“, „Guten Tag“). Das bei der Anrede-Frage sagen |
| E4 Shop-Profil | was die Shops gemeinsam haben, also woran der Einstieg anknüpfen kann |

---

## Runde 1 – Angebot und Problem

**Reihenfolge:** Zuerst Frage 2.1 stellen („Hast du schon einen Mailtext?“). Hat der Nutzer einen Text, nennt er das Problem meist schon. Dann Frage 1.1 nicht stellen, sondern das Problem aus dem Text ablesen und in der Zusammenfassung unten nur bestätigen lassen. Ohne Text: Runde 1 wie hier, dann 2B.

A1 steht in der Auftragsdatei. Fehlt A1 oder ist es länger als ein Satz, einen Satz vorschlagen und bestätigen lassen (zählt als zusätzliche Frage):

> „Wie würdest du dein Angebot einem Shop-Betreiber in einem Satz sagen?“
> Beispiel: „Zum Beispiel: Wir sorgen dafür, dass weniger Kunden zwischen Warenkorb und Kasse abspringen.“
> Vorschlag: „Aus deinen Angaben würde ich sagen: <Satz aus A1>. Passt das?“

**Frage 1.1 – Problem**

> „Welches Problem hat ein Shop, bevor er dich kennt?“
> Beispiel: „Zum Beispiel: Viele Besucher legen etwas in den Warenkorb, kaufen dann aber doch nicht.“
> Vorschlag aus A1: „Ich würde sagen: <Problem in einem Satz>. Stimmt das so?“

Das Problem kommt in die Mail (im Entwurf als Halbsatz vor dem Angebot, siehe Aufbau), **nie** in den Einstiegssatz.

**Zusammenfassen:**

> „Du hilfst <Shops aus B1> dabei, <Angebot>. Vorher haben sie das Problem: <Problem>. Richtig?“

---

## Runde 2 – Mailtext

**Frage 2.1** (Wortlaut wie E6 in `ABLAUF.md`)

> „Hast du schon einen Mailtext, den du an die Shops schicken willst?“
> Beispiel: „Kopier ihn einfach hier rein, gern mit Betreff. Wenn nicht, schreiben wir ihn zusammen. Ich stelle dir dazu ein paar kurze Fragen.“

### 2A – Der Nutzer hat einen Text

1. **In das Dateiformat bringen:** `Betreff:` + Leerzeile + Text. Fehlt ein Betreff: einen ehrlichen vorschlagen. Das ist eine Frage.
2. **Anrede ersetzen:**

   | im Text des Nutzers | wird zu |
   |---|---|
   | „Hallo Herr X“ | `{{Ansprache Normal}}` |
   | „Sehr geehrte/r …“ | `{{Ansprache Formal}}` |
   | „Guten Tag …“ | `{{Ansprache Guten Tag}}` |
   | „Hallo Max“, Du-Form | `{{Ansprache Persönlich}}` |

   Das Komma nach der Anrede bleibt.

   **Sie oder Du** liest du aus dem Text ab, nicht aus der Anrede („Ihr Shop“ = Sie, „dein Shop“ = Du). Gemischt, z. B. „Hallo Max“ und danach per Sie: `{{Ansprache Persönlich}}`, der Einstiegssatz aber per Sie. Den Ton nennst du in der Zusammenfassung von Runde 2 und lässt ihn bestätigen. Frage 2.2 entfällt.
3. **`{{Personalisierung}}` einsetzen:** als eigenen Absatz direkt unter der Anrede-Zeile, nach einer Leerzeile.
   - Hat der Text schon einen eigenen Einstieg (z. B. „Ich bin auf Ihren Shop gestoßen …“): fragen, ob der persönliche Satz ihn ersetzt.
   - Vorschlag: ersetzen.
4. **Empfängerdaten ersetzen:** Konkrete Daten eines Empfängers (Firmenname, Shop-Adresse) durch `{{Firmenname}}` bzw. `{{Website}}` ersetzen.
   - Namen außerhalb der Anrede-Zeile (Vorname im Betreff, „Herr Müller“ mitten im Text, `{{Vorname}}`, `{{Nachname}}`, `{{Anrede}}`) umformulieren, z. B. Betreff „Kurze Frage zu {{Firmenname}}“ statt „Max, kurze Frage“. Als Vorschlag zeigen, Grund in einem Satz: „Bei Shops, deren Impressum keinen Geschäftsführer nennt, stünde dort sonst nichts.“
   - Will der Nutzer den Namen trotzdem behalten und geht nur Liste 1 (Geschäftsführung) in den Versand: in Ordnung, in der Auftragsdatei vermerken.
   - Ist die Liste nicht nach Shopsystem gefiltert (E2), darf der Text das Shopsystem des Empfängers nicht voraussetzen (nicht „Ihr Shopware-Shop“). Eine passende Umformulierung vorschlagen.
5. **Den Wortlaut des Nutzers nie ohne Rückfrage ändern.**
   - Kürzen, Umformulieren und jeder ergänzte Pflichtteil: als Vorschlag zeigen und bestätigen lassen.
   - Länge: Ist der Text deutlich länger als ca. 120 Wörter (von der Anrede bis zum Gruß), einmal eine Kürzung vorschlagen. Ein Nein ist in Ordnung, die 120-Wörter-Grenze gilt nur für gemeinsam geschriebene Texte (2B).
   - Was du an der Anrede gemacht hast, in einem Satz ohne Fachbegriffe erklären: „Die Anrede habe ich so eingestellt, dass bei jedem Shop automatisch der richtige Name steht, oder ‚Hallo‘, wenn wir keinen Namen haben.“
6. **Pflichtteile prüfen** (Checkliste unten). Für jeden fehlenden Teil eine Frage, eine pro Nachricht, mit fertigem Vorschlag. Beispiel:
   > „In deinem Text fehlt noch ein Satz, wie man sich abmelden kann. Ich würde unten anfügen: ‚Wenn Sie keine weiteren Nachrichten wünschen, antworten Sie einfach mit Abmelden.‘ Passt das?“

Danach weiter mit „Zeigen und bestätigen lassen“.

### 2B – Der Nutzer hat keinen Text: gemeinsam schreiben

Eine Frage pro Nachricht. Was schon bekannt ist, überspringen.

**Frage 2.2 – Sie oder Du, und welche Anrede?**

> „Wie sollen die Shops angesprochen werden? So sähe das aus:
> 1. Sehr geehrter Herr Müller
> 2. Hallo Herr Müller
> 3. Guten Tag Herr Müller
> 4. Hallo Max (per Du)“
>
> Vorschlag: „Ich würde 2 nehmen, freundlich, aber per Sie. Wenn wir keinen Namen haben, steht dort automatisch nur ‚Hallo‘.“

**Zuordnung:**

| Antwort | Platzhalter | Folge |
|---|---|---|
| 1 | `{{Ansprache Formal}}` | – |
| 2 | `{{Ansprache Normal}}` | – |
| 3 | `{{Ansprache Guten Tag}}` | – |
| 4 | `{{Ansprache Persönlich}}` | ganze Mail und Einstiegssatz per Du |

Bei D3 = nur info@: dazusagen, dass oft kein Name da ist, nämlich wenn das Impressum keine Geschäftsführung nennt. Dann steht dort „Hallo“, „Guten Tag“ bzw. „Sehr geehrte Damen und Herren“.

**Angebot in einem Satz:** aus Runde 1 übernehmen (A1, dort bei Bedarf schon auf einen Satz gebracht). Keine eigene Frage. Der Nutzer sieht den Satz im Entwurf und kann ihn dort ändern.

**Frage 2.3 – ein echter Beleg**

> „Gibt es ein Ergebnis, das du schon einmal für einen Shop erreicht hast?“
> Beispiel: „Zum Beispiel: Bei einem Modeshop haben nach drei Wochen deutlich weniger Kunden den Kauf abgebrochen. ‚Keins‘ ist auch völlig in Ordnung.“
> Vorschlag: „Wenn dir nichts einfällt, lasse ich den Satz einfach weg.“

**Nur echte Fakten.**

- Keine Zahl erfinden, runden oder „aufhübschen“.
- Kundennamen nur, wenn der Nutzer sagt, dass er sie nennen darf.
- Statt eines Ergebnisses geht auch ein ehrlicher Satz zum Vorgehen, z. B. „Meist sind das wenige gezielte Änderungen.“

**Frage 2.4 – nächster Schritt**

> „Was soll der Shop nach dem Lesen tun?“
> Beispiel: „Zum Beispiel kurz mit Ja antworten, einen 15-Minuten-Termin ausmachen oder sich ein kurzes Video ansehen.“
> Vorschlag: „Ich würde um eine kurze Antwort bitten. Das ist die kleinste Hürde.“

**Frage 2.5 – Absender**

> „Wie soll die Mail unterschrieben sein?“
> Beispiel: „Zum Beispiel: Jana Muster, Muster Agentur GmbH, Musterstraße 1, 12345 Musterstadt, Telefon und Website, dazu der Link zu deiner Datenschutzseite, falls du eine hast.“
> Vorschlag: „Am einfachsten kopierst du mir den Block aus deinem Impressum, dann baue ich die Unterschrift daraus.“

- **Nötig:** Name, Firma mit Rechtsform und vollständige Anschrift.
- **Datenschutz-Link fehlt:** einmal sagen, dass er vor dem Versand nötig ist (`../../wissen/08_versand-und-recht.md`). In der Auftragsdatei unter „Vor dem Versand offen“ eintragen (nicht unter „Offene Punkte“, siehe `ABLAUF.md`, „Fertig, wenn“). Keine Adresse erfinden.

**Abmeldesatz:** nicht fragen. Selbst anfügen und im Entwurf zeigen:

> Wenn Sie keine weiteren Nachrichten von uns wünschen, antworten Sie einfach mit Abmelden. Dann schreiben wir Ihnen nicht wieder.

Per Du (Frage 2.2, Antwort 4):

> Wenn du keine weiteren Nachrichten von uns möchtest, antworte einfach mit Abmelden. Dann schreiben wir dir nicht wieder.

**Entwurf schreiben (Regeln für dich):**

- **Betreff:** kurz und ehrlich, sagt, worum es geht.
  - Kein „AW:“, „WG:“ oder „Re:“.
  - Kein „Ihre Anfrage“, keine falsche Dringlichkeit.
  - Den werblichen Zweck nicht verstecken.
- **Aufbau, in dieser Reihenfolge:**
  1. `{{Ansprache …}},`
  2. Leerzeile
  3. `{{Personalisierung}}`
  4. Leerzeile
  5. wer schreibt, in einem Satz
  6. Angebot, eingeleitet mit dem Problem aus Runde 1 als Halbsatz (z. B. „Viele Shops verlieren Kunden zwischen Warenkorb und Kasse. Wir …“)
  7. Beleg, falls vorhanden
  8. eine Bitte für den nächsten Schritt
  9. Gruß und Signatur
  10. Abmeldesatz und Datenschutzhinweis
- **Länge:** höchstens 120 Wörter von der Anrede bis zum Gruß. Nicht mitgezählt: der Einstiegssatz und die Signatur.
- **Kein harter Verkauf.**
  - Keine Superlative, kein „einmalig“, „nur heute“ oder „garantiert“.
  - Genau eine Bitte am Ende.
- **Kein erfundener Aufhänger.** Nicht schreiben: „Ein Kollege hat mich auf Sie aufmerksam gemacht“, „wie besprochen“, „Sie hatten Interesse gezeigt“.
- **Sie oder Du** durchgehend, wie in Frage 2.2 gewählt.
- **Nur erlaubte Platzhalter.** Kein `{{Vorname}}`, `{{Nachname}}` oder `{{Anrede}}`.
- **Shopsystem** nur nennen, wenn die Liste danach gefiltert ist (E2). Sonst bekommen auch Shops mit anderem System die Mail.

**Muster:** `beispiel/mailtext_beispiel.txt`. Fiktiver Absender, besteht `set-mailtext` ohne Fehler und Warnungen. Es nennt Shopware und setzt deshalb eine nach Shopware gefilterte Liste voraus (E2).

### Pflichtteile – Checkliste vor jeder Vorschau

Hintergrund: `../../wissen/08_versand-und-recht.md`, Abschnitte „Pflichtangaben in jeder Werbe-Nachricht“ und „Vor dem ersten Versand – Checkliste“. Die Rechtstexte dem Nutzer nicht vorlesen, nicht belehren.

| # | Pflichtteil | woran prüfen | wenn es fehlt |
|---|---|---|---|
| 1 | Ehrlicher Betreff | `Betreff:` vorhanden. Kein AW/WG/Re, kein vorgetäuschter Bezug, werblicher Zweck erkennbar | Betreff vorschlagen |
| 2 | Anrede | eine `{{Ansprache …}}` als erste Zeile des Texts | Frage 2.2 |
| 3 | Persönlicher Satz direkt nach der Anrede | `{{Personalisierung}}` als Absatz nach Anrede-Zeile und Leerzeile (bei `DO_PERSONALISIERUNG=true`) | selbst einsetzen |
| 4 | Kein erfundener Aufhänger | kein „Kollege“, „wie besprochen“, „Ihre Anfrage“ | Streichen vorschlagen |
| 5 | Absender klar erkennbar | Name, Firma mit Rechtsform, Anschrift in der Signatur | Frage 2.5 |
| 6 | Abmeldeweg | ein Satz, wie man weitere Nachrichten abbestellt | Standardsatz anfügen und zeigen |
| 7 | Datenschutzhinweis | Link zur Datenschutzseite des Absenders | in Frage 2.5 erfragen. Fehlt er: in der Auftragsdatei unter „Vor dem Versand offen“, der Testlauf darf trotzdem starten (er verschickt nichts) |
| 8 | Nur erlaubte Platzhalter, keine leeren | `set-mailtext` ohne Fehler; keine Hinweise zu `{{Vorname}}`, `{{Nachname}}`, `{{Anrede}}` (Ausnahme: nur Liste 1, siehe 2A) | ersetzen |

`set-mailtext` prüft die Punkte 2, 3 und 8 selbst, auch die Stellung: Begrüßung als erste Zeile unter dem Betreff, `{{Personalisierung}}` direkt darunter. Für 1 und 4–7 bist du zuständig.

**Lehnt der Nutzer einen Pflichtteil ab** (z. B. „Den Abmeldesatz lass weg, das klingt nach Massenmail“):

1. Einmal in einem Satz den Grund nennen, ohne zu belehren, z. B.: „Der Abmeldeweg ist in jeder Werbe-Mail vorgeschrieben; fehlt er, ist die Mail leicht angreifbar.“ Grundlage für dich: `../../wissen/08_versand-und-recht.md`, „Pflichtangaben in jeder Werbe-Nachricht“.
2. Eine mildere Form anbieten, z. B. den Abmeldesatz klein unter die Signatur, die Anschrift in eine Fußzeile statt in die Unterschrift, einen neugierigen, aber ehrlichen Betreff („Kurze Frage zu {{Firmenname}}“).
3. Bleibt es beim Nein:
   - **Teile 2, 3 und 8** braucht der Pfad technisch, ohne sie speichert `set-mailtext` nicht. Das so sagen. Will der Nutzer gar keinen persönlichen Satz: `DO_PERSONALISIERUNG=false` (`ABLAUF.md`, Stellschrauben), dann entfällt Teil 3.
   - **Teile 5, 6 und 7** (Absender, Abmeldeweg, Datenschutz): den Text so speichern, wie der Nutzer ihn will, und in der Auftragsdatei unter „Vor dem Versand offen“ eintragen, z. B. „Abmeldesatz vom Nutzer abgelehnt“. Der Testlauf darf starten.
   - **Teile 1 und 4** (ehrlicher Betreff, kein erfundener Aufhänger): Ein „AW:“, „WG:“ oder einen erfundenen Bezug schreibst du nicht in die Datei. Die ehrliche Fassung bleibt drin. Unter „Vor dem Versand offen“ vermerken, was der Nutzer stattdessen wollte. Ändert er es später selbst im Versandtool, ist das seine Entscheidung.
4. Nicht weiter nachhaken. Beim Export nennst du die Punkte einmal (`ABLAUF.md`, Phase 5).

### Zeigen und bestätigen lassen (Schleife)

1. **Speichern und prüfen:**
   ```bash
   python3 -m ecom set-mailtext ../../auftraege/<auftrag>_mailtext.txt
   ```
   Fehler selbst beheben und erneut ausführen. Die Rohmeldung nicht zeigen.
2. **Die Vorschau zeigen,** so wie der Shop die Mail sieht. Nicht die Datei mit den Platzhaltern. Dazu ein Satz: „Der zweite Absatz ist ein Beispiel. Dort steht später bei jedem Shop ein eigener Satz zu seiner Startseite.“ Der Beispielsatz ist immer per Sie. Ist die Mail per Du, dazusagen: „Bei deinen Shops schreibe ich diesen Satz natürlich per Du.“
3. **Fragen:** „Passt das so, oder möchtest du etwas ändern?“
4. **Änderungswunsch:** genau das ändern, speichern, `set-mailtext` erneut ausführen, wieder zeigen.
5. **Wiederholen,** bis ein klares Ja kommt und jeder Pflichtteil da ist oder unter „Vor dem Versand offen“ steht (fehlender Datenschutz-Link, vom Nutzer abgelehnter Teil, siehe oben).

---

## Runde 3 – Aufhänger für den Einstiegssatz

**Frage 3.1 – Woran knüpft der Satz an?**

> „Was auf der Startseite eines Shops verrät dir, dass er dein Angebot gebrauchen könnte?“
> Beispiel: „Zum Beispiel: viele Zahlarten, ein Hinweis auf kostenlose Rücksendung, Versand in mehrere Länder, Kundenbewertungen oder eine eigene Marke.“
> Vorschlag aus A1 und Runde 1: „Ich würde auf <drei, vier Signale aus der Tabelle> achten. Passt das?“

Signale, die im Startseitentext stehen können (Auswahl für deinen Vorschlag):

| Signal | so steht es im Text | passt oft zu Angeboten für |
|---|---|---|
| Sortimentsbreite | „über 3.000 Artikel“, viele Kategorien | Suche und Filter, Werbung, Produktdaten |
| Eigene Marke oder Fremdmarken | „unsere eigene Kollektion“, Markenliste | Markenaufbau, Großhandel, Marktplätze |
| Versandversprechen | „Versand in 24 Stunden“, „ab 50 € versandkostenfrei“ | Logistik, Checkout |
| Vertrauenszeichen | Gütesiegel, Kundenbewertungen, Sterne | Conversion, Bewertungen |
| Versandländer | „Wir liefern nach Österreich und in die Schweiz“ | Internationalisierung, Zoll, Übersetzung |
| B2B-Bereich | „Händlerbereich“, „für Gewerbekunden“ | B2B-Shop, Warenwirtschaft |
| Zahlarten | Rechnung, Raten, Lastschrift | Payment, Checkout |
| Aktionen | Sale, Newsletter-Rabatt, Gutscheincode | E-Mail-Marketing, Kundenbindung |

**Nicht verwendbar** ist alles, was nicht im Startseitentext steht:

- Bilder, Unterseiten, Ladezeit,
- Bewertungen auf fremden Portalen,
- Werbebudget, Interna („hat kein CRM“).

**Ton:** keine eigene Frage. Er folgt aus Frage 2.2 bzw. bei mitgebrachtem Text (2A) aus dem Text selbst: per Sie (Standard) oder per Du, natürlich gesprochen, keine Werbesprache. In der Zusammenfassung nennen.

**Frage 3.2 – Wörter, die nie vorkommen dürfen**

> „Gibt es Wörter, die in dem persönlichen Satz nie vorkommen sollen?“
> Beispiel: „Viele mögen keine Lobhudelei wie ‚beeindruckend‘ oder ‚großartig‘.“
> Vorschlag: „Die schließe ich sowieso aus, dazu Floskeln wie ‚Leidenschaft‘ oder ‚Expertise‘. Reicht dir das?“

**Grundstock der Verbotsliste** (Clay-Original + Google-Maps-Builder, für Shops ergänzt): beeindruckend, herausragend, außergewöhnlich, atemberaubend, großartig, fantastisch, wow, man merkt, Expertise, Kompetenz, Leidenschaft, Engagement, Professionalität, breit aufgestellt, gut aufgestellt, einzigartig, liebevoll.

**Zusammenfassen:**

> „Bei jedem Shop schreibe ich einen kurzen Satz zu dem, was auf seiner Startseite zu sehen ist, zum Beispiel <Signale>. Per Sie, ganz normal gesprochen, ohne Lob und ohne Verkaufsargument. Das Angebot steht ja danach in deiner Mail. Wörter wie ‚beeindruckend‘ kommen nie vor. Passt das?“

---

## Personalisierungs-Anweisung schreiben (nur für dich)

Struktur:

```
## ROLLE
Du schreibst den ersten Satz einer Kaltakquise-Mail an [Shops aus B1/B2] in [D1]. Absender ist [A1 in einem Satz, ohne Namen].

## KONTEXT
Dein Text wird direkt hinter der Anrede eingesetzt ([Anrede-Beispiel aus 2.2], oder nur [neutrale Form], wenn kein Name bekannt ist). Danach folgt die Mail unten; sie enthält Vorstellung, Angebot und Bitte bereits. An der Stelle, an der in der Mail das Wort Personalisierung in doppelten geschweiften Klammern steht, wird dein Satz eingesetzt.
<mailtext>
{{Mailtext}}
</mailtext>
Dein Satz zeigt nur, dass jemand die Startseite genau dieses Shops angesehen hat, und führt zum Thema [Thema aus A1] hin. Wiederhole nichts aus der Mail.

## VORGEHEN
1. Startseitentext lesen.
2. Ein konkretes Detail suchen: [Signale aus 3.1].
3. Nichts davon gefunden: ein konkretes Detail zu Sortiment oder Stil nehmen.
4. Satz schreiben, Selbstprüfung durchgehen.

## DIE WICHTIGSTE REGEL: beobachten, nicht unterstellen
[Falsch-/Richtig-Beispiel aus der Shop-Welt des Auftrags, Richtig beginnt klein]

## ANFORDERUNGEN
[Sprache Deutsch, per Sie/Du; höchstens 2 Sätze und 30 Wörter; erster Buchstabe klein, sonst normale Rechtschreibung;
 spezifisch und nur aus dem Startseitentext, nichts erfinden; Satzanfänge zur Auswahl (Clay-Liste, bei Du: bei dir …, wie du …, dass du …, dein …);
 Verben statt Hauptwörter; umschreiben statt zitieren; Schluss = Feststellung statt Lob]

## VERBOTEN
Wörter: [Liste aus 3.2]
Zeichen: Gedankenstrich (–), nur einfacher Bindestrich (-). Keine Anführungszeichen. Keine Semikolons.
Stil: allgemeines Lob, Behördendeutsch, Übertreibungen, Fragen, Problem nennen, Lösung nennen, Wiederholungen aus der Mail, Name des Absenders.

## SELBSTPRÜFUNG
[Checkliste: nur dieser Shop? Detail wirklich im Text? Beobachtung statt Unterstellung? ≤ 2 Sätze / 30 Wörter? erster Buchstabe klein?
 keine verbotenen Wörter und Zeichen? weder Problem noch Lösung, nichts aus der Mail wiederholt? Feststellung statt Lob?]

## INPUT
<company_info>
"bodyText":"{{Bodytext Website}}"
</company_info>

## OUTPUT
Gib ein JSON-Objekt mit dem Feld complimentText zurück. Es enthält nur den Satz.
```

**Regeln:**

- **Pflicht:** `{{Bodytext Website}}`, exakt so. Sonst lehnt `set-prompt` ab.
- **`{{Mailtext}}` immer einbauen.** Ohne ihn gibt `set-prompt` einen Hinweis aus, und das Modell wiederholt leichter, was in der Mail steht.
- **`{{Firmenname}}`** nur, wenn der Satz den Namen wirklich braucht. Meist nicht.
- **Andere Platzhalter nicht wörtlich hineinschreiben.** Die Stelle des Satzes in der Mail in Worten beschreiben, wie in der Vorlage oben.
- **Nie Problem oder Lösung im Einstieg.** Beides steht in der Mail.
- **Keine Drohungen wie im Clay-Original** („terminated“). Keine echten Firmennamen in den Beispielen.
- **Ein Angebot je Lauf.** Für ein zweites Angebot erst exportieren und `export --mark`, dann den Builder erneut durchlaufen.

**Muster:** `beispiel/personalisierung_beispiel.txt`. Gleicher fiktiver Auftrag wie `beispiel/mailtext_beispiel.txt`.

---

## Speichern und setzen

Erst den Mailtext, dann die Personalisierung. Die Personalisierung liest den gespeicherten Mailtext über `{{Mailtext}}`.

```bash
python3 -m ecom set-mailtext ../../auftraege/<auftrag>_mailtext.txt
python3 -m ecom set-prompt personalisierung ../../auftraege/<auftrag>_personalisierung.txt
python3 -m ecom status
```

- `<auftrag>` ist der Name der Auftragsdatei ohne `.md`. Beispiel: `auftraege/2026-10-09_mode-shopware-dach_mailtext.txt`.
- `set-prompt personalisierung` setzt die Einstiegssätze aller noch nicht exportierten Leads zurück und nennt die Anzahl. Vor dem ersten Lauf ist das 0.
- In `status` muss im Block „Anforderungen“ stehen:
  ```
  Personalisierung   ✓ gesetzt
  Mailtext           ✓ gesetzt (Betreff: …)
  ```
- In der Auftragsdatei eintragen:
  - `Mailtext (E6): auftraege/<auftrag>_mailtext.txt`
  - `Personalisierung (E6): auftraege/<auftrag>_personalisierung.txt`
- Die Vorschau aus `set-mailtext` hat der Nutzer in der Schleife gesehen. Wurde danach noch etwas geändert: die letzte Vorschau noch einmal zeigen.

**Mailtext später geändert?**

1. `set-mailtext` erneut ausführen.
2. Gibt es schon Einstiegssätze, weist der Befehl darauf hin. Dann `python3 -m ecom set-prompt personalisierung <dieselbe datei>` erneut ausführen. Das setzt die Sätze zurück, ein automatisches Zurücksetzen gibt es nicht.
3. Danach `run --stage 2e` und `run --stage 2g`.

---

## Fertig, wenn

- [ ] Runde 1, 2 und 3 sind zusammengefasst und vom Nutzer bestätigt.
- [ ] `../../auftraege/<auftrag>_mailtext.txt` erfüllt alles:
  - beginnt mit `Betreff:`,
  - hat alle acht Pflichtteile der Checkliste; fehlt einer, steht er in der Auftragsdatei unter „Vor dem Versand offen“ (fehlender Datenschutz-Link oder vom Nutzer abgelehnt),
  - bei gemeinsam geschriebenem Text (2B): von der Anrede bis zum Gruß höchstens 120 Wörter, ohne Einstiegssatz und Signatur,
  - `set-mailtext` lief ohne Fehler; Hinweise zu `{{Vorname}}`, `{{Nachname}}`, `{{Anrede}}` sind behoben (Ausnahme wie in 2A), andere Hinweise, z. B. zu `{{Videotitel}}`, sind dem Nutzer in einem Satz erklärt.
- [ ] Der Nutzer hat die Vorschau gesehen und ausdrücklich „passt“ gesagt.
- [ ] `../../auftraege/<auftrag>_personalisierung.txt` enthält `{{Bodytext Website}}` und `{{Mailtext}}` und fordert `complimentText`. `set-prompt personalisierung` lief ohne Fehler.
- [ ] `python3 -m ecom status` zeigt unter „Anforderungen“ ✓ bei Personalisierung und Mailtext.
- [ ] Die Auftragsdatei enthält beide Dateinamen. Punkte für „Vor dem Versand offen“ sind vermerkt.

---

## Nach dem Testlauf: fertige Mails zeigen und freigeben lassen

Nach `run --stage 1 --limit 10`, `run --stage 2` und `export` ohne `--mark` (`ABLAUF.md`, Phase 3) holst du die fertigen Mails aus dem neuesten Export. Das Skript zeigt je bis zu zwei Mails aus Liste 1 (Geschäftsführung) und Liste 2 (info@):

```bash
python3 - <<'EOF'
import csv, glob
for muster in ("exports/1_geschaeftsfuehrer_*.csv", "exports/2_info_*.csv"):
    dateien = sorted(glob.glob(muster))
    if not dateien:
        continue
    with open(dateien[-1], encoding="utf-8-sig", newline="") as fh:
        for zeile in list(csv.DictReader(fh, delimiter=";"))[:2]:
            print("Betreff:", zeile["Betreff"], "\n")
            print(zeile["Mailtext"])
            print("-" * 60)
EOF
```

1. **Zwei, drei fertige Mails auswählen,** möglichst eine an die Geschäftsführung und eine an info@.
2. **Vollständig zeigen,** mit Betreff, so wie sie verschickt würden.
3. **Fragen:** „So kommen die Mails bei den Shops an. Passt das so?“
4. **Bei „nein“ eine Frage stellen:**
   > „Was stört dich am meisten?“
   > Beispiel: „Zum Beispiel: Der erste Satz ist zu lang, klingt nach Lob, passt nicht zum Shop oder sagt dasselbe wie der Rest der Mail.“
5. **Anpassen:**

   | Was nicht passt | Änderung in der Personalisierungs-Datei |
   |---|---|
   | zu lang | Wortgrenze senken, z. B. auf 20 |
   | klingt nach Lob | Wörter in VERBOTEN ergänzen, Regel „Feststellung statt Lob“ mit einem neuen Falsch-/Richtig-Beispiel schärfen |
   | wiederholt die Mail | KONTEXT strenger: die konkreten Inhalte der Mail aufzählen, die nicht vorkommen dürfen |
   | Detail stimmt nicht | „nur was wörtlich im Startseitentext steht, sonst Sortiment oder Stil“ |
   | immer derselbe Anfang | Satzanfänge ausdrücklich abwechseln lassen, häufigsten Anfang verbieten |
   | der Mailtext selbst | Mailtext-Datei ändern, `set-mailtext`, dann wie oben unter „Mailtext später geändert?“ |

6. **Neu laufen lassen:**
   ```bash
   python3 -m ecom set-prompt personalisierung ../../auftraege/<auftrag>_personalisierung.txt   # setzt die Sätze zurück
   python3 -m ecom run --stage 2e
   python3 -m ecom run --stage 2g
   python3 -m ecom export
   ```
   Der Startseitentext wird wiederverwendet. Nur die KI schreibt die Sätze neu.
7. **Wieder zeigen und fragen,** bis der Nutzer zustimmt.

Erst danach Kosten hochrechnen und den Vollstart bestätigen lassen (`ABLAUF.md`, Phase 3, Punkt 3).
