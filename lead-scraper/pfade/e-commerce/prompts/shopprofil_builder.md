# Shop-Profil-Builder – welche aktiven Shops passen zum Auftrag?

> **Für dich (Claude), nicht für den Nutzer.** Anforderung **E4** aus `ABLAUF.md`, Phase 1.
> Ohne Entscheidung zum Shop-Profil bricht `python3 -m ecom run` vor den Stufen 1c, 1d und 1e ab, bevor etwas kostet.
>
> **Ergebnis:** entweder eine Prüfanweisung in `auftraege/<auftrag>_shopprofil.txt`, gespeichert mit
> `python3 -m ecom set-prompt shopprofil <datei>`, oder die bewusste Entscheidung „ohne“
> (`python3 -m ecom set-prompt shopprofil --ohne`).
>
> Die Fachbegriffe hier (ICP, Prompt, Confidence, Platzhalter, Stufe, JSON) sind nur für dich. Der Nutzer hört sie nie.
> Alle Befehle laufen aus `pfade/e-commerce/`. Auftragsdateien liegen im Arbeitsordner unter `auftraege/`. Im Skill-Ordner (`lead-scraper/`) ist das von dort aus `../../auftraege/`; wurde der Pfad in einen eigenen Arbeitsordner kopiert (`../../SKILL.md`, Schritt 1), `../auftraege/`. Die Befehle unten zeigen den ersten Fall. Fehlt der Ordner (frisches Paket), vor der ersten Datei anlegen: `mkdir -p ../../auftraege`.

---

## Was technisch feststeht

- **Ablauf von Stufe 1c:**
  1. Zuerst die Clay-Prüfung „aktiver Onlineshop ja/nein“ (`prompts/icp_online_shop.txt`, unverändert).
  2. Danach prüft das Shop-Profil jeden aktiven Shop.

  Das Profil prüft also **nicht** noch einmal, ob es ein Shop ist (Warenkorb, Kasse, Wartungsseite).
- **Was das Modell sieht:** nur zwei Dinge.
  - Text der Startseite: `{{BodyText}}`, bis `ICP_BODYTEXT_MAX_CHARS` Zeichen.
  - Adresse: `{{website [Final]}}`.

  Es sieht keine Unterseiten, keine Bilder, kein HTML, keine Linkliste, kein Shopsystem und keine Besucherzahlen.
- **Antwort fest nach `prompts/shopprofil.schema.json`:** `{"is_icp": boolean, "confidence": 0..1, "reason": string}`. Keine weiteren Felder.
- **Was mit der Antwort passiert:**
  - `is_icp: true`: Der Shop geht weiter zu den Besucherzahlen (Stufe 1d, kostet) und in die Anreicherung.
  - `false`: Der Shop landet in Liste 3 „Aussortiert“, Grund `passt nicht zum Shop-Profil: <reason>`.

  Den Grund liest der Nutzer. Deshalb: ein kurzer deutscher Satz ohne Fachbegriffe.
- **Eine Liste „unsicher“ gibt es in diesem Pfad nicht.** Unsichere Fälle entscheidet die Zweifelsregel (Frage 3).
- **Die Prüfung läuft vor allen teuren Abfragen.** Jeder aussortierte Shop spart Besucherzahlen, Impressum und E-Mail-Suche.

---

## Schritt 0 – Auftragsdatei lesen, nichts davon erneut fragen

| Aus der Auftragsdatei | wird im Profil zu |
|---|---|
| A1 Angebot | Was ein Shop haben muss, damit das Angebot überhaupt greift (z. B. eigener Bestellablauf statt nur Marktplatz) |
| B1 Art der Shops | Prüfung 2: Sortiment, Muss-Kriterien |
| B2 typischer Wunschkunde | Prüfung 2: Privat- oder Geschäftskunden. Sofort raus „Struktur“: Ketten, Konzerne, Größe |
| B3 Beispielshops | Gegenprobe: Würden diese Shops durchkommen? |
| D1 Länder | Prüfung 1: Region |
| D2 Ausschlüsse | Sofort raus |

Fehlt einer dieser Punkte in der Auftragsdatei: zuerst mit dem Wortlaut aus `../../wissen/02_zielgruppen-interview.md` fragen und die Auftragsdatei ergänzen. Diese Nachfragen zählen nicht zu den Fragen unten.

**Gehört nicht ins Profil:**

- **Shopsystem (E2):** Es steht fast nie im Startseitentext. Die Liste wird vorher gefiltert (`ABLAUF.md`, E2). Im Profil höchstens als Pluspunkt (z. B. „realisiert mit Shopware“ im Text), nie als Muss.
- **Mindestgröße (E3):** Das regeln die Besucherschwellen in `.env`, nicht das Profil.

---

## Schritt 1 – Mit Profil oder ohne?

Ein Profil ist **Pflicht**, sobald B2, D1 oder D2 etwas einschränken, das auf einer Startseite sichtbar ist. Beispiele: Sortiment, Privat- oder Geschäftskunden, Sprache und Land, Währung, Ketten, reine Marktplatz-Händler.

**`--ohne` ist nur richtig, wenn beides stimmt:**

1. Der Kunde will wirklich jeden aktiven Shop, egal was er verkauft. Beispiel: ein Zahlungsanbieter für alle Shops.
2. Länder und Ausschlüsse sind schon durch die Liste garantiert. Beispiel: Verzeichnis-Export nur mit .de-Shops, ohne Ketten.

Ist E4 in der Auftragsdatei noch offen und nicht ableitbar, die Frage aus `ABLAUF.md` stellen:

> „Soll ich jeden aktiven Onlineshop aus der Liste nehmen, oder nur Shops, die zu deiner Beschreibung passen?“
> Beispiel: „Zum Beispiel nur Modeshops für Endkunden aus Deutschland, keine reinen Marktplatz-Händler.“
> Vorschlag: „Ich würde mindestens prüfen lassen, ob der Shop auf Deutsch an Kunden in deinen Ländern verkauft. Das kostet sehr wenig und erspart dir Anfragen ins Leere.“

- **„Alle“, ohne Länderprüfung:**
  - `python3 -m ecom set-prompt shopprofil --ohne` ausführen.
  - In der Auftragsdatei eintragen: `Shop-Profil (E4): bewusst ohne`.
  - Weiter mit „Fertig, wenn“.
- **„Alle, aber nur aus meinen Ländern“:** Profil nur mit Prüfung 1 und „Sofort raus – Region“ bauen. Fragen 1 und 2 entfallen.
- **„Nur passende“:** weiter mit Schritt 2.

---

## Schritt 2 – Fragen: höchstens drei, eine pro Nachricht

**Budget:** Mit vollständiger Auftragsdatei sind es höchstens **vier Fragen**, die Frage aus Schritt 1 eingerechnet. Meist reichen zwei oder drei.

**Form jeder Frage:**

- ein Beispiel aus der Shop-Welt,
- ein fertiger Vorschlag aus A1, B1–B3, D1 und D2, den der Nutzer nur bestätigen muss,
- in einem Satz beantwortbar.

Sagt der Nutzer „weiß nicht“: den Vorschlag nehmen, bestätigen lassen, weiter.

**Überspringen, was die Auftragsdatei schon sagt:**

- **Frage 1 weglassen,** wenn B1 und B2 Sortiment und Kundschaft (Privat- oder Geschäftskunden) schon nennen. Den Inhalt zeigst du erst in der Zusammenfassung (Schritt 3), dort bestätigt ihn der Nutzer.
- **Frage 2 weglassen,** wenn D2 die typischen Shop-Ausschlüsse schon nennt. Den Standardblock (reine Marktplatz-Händler, Ware direkt vom Lieferanten, Ketten und Kaufhäuser, Hersteller ohne eigenen Verkauf) nimmst du ungefragt ins Profil und zeigst ihn in der Zusammenfassung.
- **Frage 3** stellst du immer, außer die Auftragsdatei sagt schon, ob Zweifelsfälle drauf oder raus sollen.

**Frage 1 – Woran erkennt man einen passenden Shop?**

> „Wenn du auf die Startseite eines passenden Shops schaust: Woran siehst du sofort, dass er zu dir passt?“
> Beispiel: „Zum Beispiel Damen- und Herrenmode, eine eigene Kollektion oder eine Größenberatung.“
> Vorschlag: „Ich würde auf <Sortiment aus B1> für <Privatkunden/Firmenkunden aus B2> achten. Passt das, oder fehlt etwas?“

Ob Privat- oder Geschäftskunden, steckt im Vorschlag. Sagen B1 und B2 dazu nichts, die wahrscheinlichere Variante vorschlagen. Der Nutzer korrigiert, wenn nötig.

**Frage 2 – Was sieht ähnlich aus, passt aber nicht?**

> „Welche Shops sehen auf den ersten Blick ähnlich aus, passen aber trotzdem nicht zu dir?“
> Beispiel: „Zum Beispiel Händler, die nur über große Marktplätze verkaufen, große Modeketten oder Shops, die nur Billigware aus Übersee weiterverschicken.“
> Vorschlag: „Ich sortiere ohnehin aus: reine Marktplatz-Händler, Shops, die nur fremde Ware direkt vom Lieferanten verschicken lassen, Ketten und Kaufhäuser, Hersteller ohne eigenen Verkauf <und die Ausschlüsse aus D2>. Soll noch etwas dazu?“

**Frage 3 – Im Zweifel drauf oder raus?**

> „Wenn ich mir bei einem Shop nicht sicher bin: Soll er lieber auf die Liste oder lieber rausfliegen?“
> Beispiel: „Ein Shop mit sehr wenig Text auf der Startseite lässt sich oft nicht sicher einordnen.“
> Vorschlag: „Ich würde ihn rausnehmen. Dann bezahlst du keine Suche für Shops, die wahrscheinlich nicht passen.“

Vorschlag „raus“ ist der Normalfall. Ist die Liste schon eng vorsortiert (z. B. ein Verzeichnis nur mit Modeshops), „drauf“ vorschlagen.

**Nicht fragen, selbst festlegen:**

- **Reihenfolge der Prüfung:** Region, dann Sortiment und Kundschaft, dann harte Ausschlüsse. Immer.
- **Was die Sicherheit erhöht oder senkt:** aus den Antworten ableiten.

---

## Schritt 3 – Zusammenfassen und bestätigen lassen

In eigenen Worten, drei bis fünf Sätze, ohne Fachbegriffe. Beispiel:

> „Ich lasse jetzt jeden aktiven Shop kurz prüfen: Verkauft er auf Deutsch an Kunden in Deutschland, Österreich oder der Schweiz? Ist Mode für Privatkunden sein Schwerpunkt? Raus fliegen reine Marktplatz-Händler, Shops mit Ware direkt vom Lieferanten, Ketten und Kaufhäuser. Im Zweifel fliegt ein Shop raus. Passt das so?“

Erst nach dem Ja die Datei schreiben. Bei „nein“: eine Frage, was nicht stimmt. Anpassen und neu zusammenfassen.

---

## Schritt 4 – Prüfanweisung schreiben (nur für dich)

Struktur, in dieser Reihenfolge:

```
ROLLE: Shop-Qualifizierer für [Sortiment/Shoptyp] mit [Privat-/Geschäftskunden] in [Region].

AUFGABE: Prüfe anhand des Startseitentexts, ob der Onlineshop [Kern in einem Satz]. Dass es ein aktiver Onlineshop ist, steht bereits fest. Kein [Kern] = kein Treffer. Keine Ausnahmen.

PRÜFUNG 1 — REGION: [Sprache des Texts, Währung (€ / CHF), Versandländer, im Text genannte Rechtstexte wie Impressum, AGB, Widerrufsbelehrung, Versand nach DE/AT/CH. Domain-Endung von {{website [Final]}} nur als Zusatzsignal. Abbruchbedingung nach D1.]

PRÜFUNG 2 — SORTIMENT UND KUNDSCHAFT: [Schwerpunkt aus B1, Privat- oder Geschäftskunden aus B2. Abbruchbedingung.]

PRÜFUNG 3 — SOFORT RAUS (ein Treffer reicht):
Verkaufsweg: [nur Marktplatz, Weiterleitung auf fremden Shop]
Dropshipping: [Lieferzeit mehrere Wochen, Versand aus Übersee, Sammelsurium ohne Schwerpunkt]
Struktur: [Filialkette, Kaufhaus, Konzern, Großversender, Franchise]
Hersteller ohne eigenen Verkauf: [Händlersuche, nur im Fachhandel erhältlich]
Sortiment: [falsches Sortiment]
[D2-Ausschlüsse]

MUSS-KRITERIEN (mindestens 2 müssen zutreffen):
[Kategorie]: [kommaseparierte Begriffe aus dem Startseitentext]
[Kategorie]: [...]
[Kategorie]: [...]

HARTE AUSSCHLUSSREGEL: [1–2 Sätze: Ist X nicht klar erkennbar → kein Treffer. Zweifelsregel aus Frage 3: „Im Zweifel raus.“ bzw. „Bei fehlenden Nebeninformationen durchlassen, solange Region und Sortiment passen und kein Sofort-raus-Treffer vorliegt.“]

CONFIDENCE ERHÖHEN: [kommasepariert]
CONFIDENCE SENKEN: [kommasepariert]

INPUT:
Website: {{website [Final]}}
Startseitentext: {{BodyText}}

OUTPUT (JSON):
{"is_icp": boolean, "confidence": 0.0-1.0, "reason": "Kurze Begründung auf Deutsch"}
Die reason ist ein kurzer deutscher Satz ohne Fachbegriffe, höchstens 15 Wörter.
Bei leerem oder unlesbarem Startseitentext: {"is_icp": false, "confidence": 1.0, "reason": "Startseite ohne lesbaren Text"}
```

**Regeln:**

- **Platzhalter exakt so:** `{{BodyText}}` (Pflicht, sonst lehnt `set-prompt` ab) und `{{website [Final]}}`, mit Leerzeichen und eckigen Klammern. Keine anderen Platzhalter.
- **Nur Kriterien aus dem Startseitentext und der Adresse.** Nicht verwenden:
  - Unterseiten, Bilder, HTML, Navigation, Linkliste,
  - Ladezeit, Shopsystem als Muss, Besucherzahlen.
- **Die Shop-Prüfung nicht wiederholen.** Warenkorb, Kasse und Wartungsseite sind schon geprüft.
- **Ausgabe immer genau** `{"is_icp": boolean, "confidence": 0.0-1.0, "reason": "string"}`, ohne zusätzliche Felder. Kein Wort „ICP“ in der `reason`.
- **Sprache:** Deutsch, kompakt. Aggressiv filtern, außer Frage 3 sagt „drauf“.
- **Keine Beispiele im Prompt.** Sie kosten Zeichen und färben die Bewertung.
- **Keine echten Firmennamen** als Muster im Prompt. Kategorien beschreiben, nicht einzelne Marktplätze oder Ketten aufzählen.
- **Höchstens 400 Wörter.** Nachzählen mit `wc -w`.
- **Keine Liste mit Suchbegriffen** (anders als im Google-Maps-Builder). Die Shops kommen aus der Liste (E1).

**Muster:** `beispiel/shopprofil_beispiel.txt`. Fiktiver Auftrag: Checkout-Optimierung für Shopware-Modeshops in DACH.

**Gegenprobe vor dem Speichern:** Die Beispielshops aus B3 im Kopf durch die Prüfungen schicken. Fliegt einer raus, ist eine Regel zu streng. Nachschärfen, bevor gespeichert wird.

---

## Schritt 5 – Speichern und setzen

```bash
# Datei: ../../auftraege/<auftrag>_shopprofil.txt  (<auftrag> = Name der Auftragsdatei ohne .md,
# z. B. 2026-10-09_mode-shopware-dach → 2026-10-09_mode-shopware-dach_shopprofil.txt)
python3 -m ecom set-prompt shopprofil ../../auftraege/<auftrag>_shopprofil.txt
python3 -m ecom status
```

**Was `set-prompt shopprofil` tut:**

- Es prüft, ob `{{BodyText}}` vorkommt.
- Es speichert die Anweisung in der Lauf-Datenbank.
- Es setzt die Profil-Ergebnisse aller aktiven Shops zurück, die noch nicht übergeben oder noch nicht exportiert sind, samt Fehlversuchen, und nennt die Anzahl. Vor dem ersten Lauf ist das 0.
- Meldet es einen Fehler: Datei korrigieren und den Befehl erneut ausführen. Die Rohmeldung nicht zeigen.

**Danach:**

- In `status` muss im Block „Anforderungen“ stehen: `Shop-Profil: ✓ gesetzt (N Zeichen)`.
- In der Auftragsdatei eintragen: `Shop-Profil (E4): auftraege/<auftrag>_shopprofil.txt`.

Die Datei in `auftraege/` bleibt der Nachweis, wie die Shops geprüft wurden.

---

## Fertig, wenn

- [ ] A1, B1–B3, D1 und D2 stehen ohne offene Punkte in der Auftragsdatei.
- [ ] Der Nutzer hat die Zusammenfassung aus Schritt 3 bestätigt oder ausdrücklich „ohne“ gewählt.
- [ ] `../../auftraege/<auftrag>_shopprofil.txt` erfüllt alles:
  - enthält `{{BodyText}}` und `{{website [Final]}}` exakt so,
  - hat höchstens 400 Wörter,
  - endet mit dem festen OUTPUT-Block.

  Dieser Punkt entfällt bei „ohne“.
- [ ] `python3 -m ecom set-prompt shopprofil <datei>` bzw. `--ohne` lief ohne Fehler.
- [ ] `python3 -m ecom status` zeigt unter „Anforderungen“ `Shop-Profil: ✓ gesetzt (N Zeichen)` bzw. `✓ bewusst ohne`.
- [ ] Die Zeile `Shop-Profil (E4):` in der Auftragsdatei ist ausgefüllt.

---

## Nach dem Testlauf: Profil prüfen und nachschärfen

Nach `python3 -m ecom run --stage 1 --limit 10` (`ABLAUF.md`, Phase 3):

1. **Ergebnisse ansehen:**
   ```bash
   python3 -m ecom status --shops 20
   ```
   Je Shop: aktiver Onlineshop ja/nein, Profil ja/nein mit Sicherheit (0–1), Profil-Grund bzw. Stand, Fehler. Für das Profil zählen die Shops mit „Shop ja“.
2. **Dem Nutzer Beispiele zeigen:** zwei, drei Shops, die passen, und zwei, drei aussortierte, jeweils mit Grund in einem Satz. Stehen Beispielshops aus B3 in der Liste, müssen sie durchgekommen sein.
3. **Fragen:** „Passt die Auswahl so?“
4. **Bei „nein“ eine Frage stellen:**
   > „Was stimmt nicht?“
   > Beispiel: „Zum Beispiel: Der Shop X ist rausgeflogen, obwohl er passt, oder Y ist drin, obwohl es eine Kette ist.“
5. **Nachschärfen:**
   1. Nur die betroffene Regel in der Datei ändern.
   2. `python3 -m ecom set-prompt shopprofil ../../auftraege/<auftrag>_shopprofil.txt` ausführen. Das setzt die Ergebnisse aller Shops zurück, die noch nicht übergeben oder noch nicht exportiert sind, also auch die aus dem Testlauf.
   3. Dann:
      ```bash
      python3 -m ecom run --stage 1c   # prüft nur Shops mit Startseitentext neu, also die schon getesteten
      python3 -m ecom run --stage 1d
      python3 -m ecom run --stage 1e
      python3 -m ecom run --stage 2g   # Ready to Send neu: abgelehnte Testlauf-Shops fallen aus Liste 1 und 2
      ```
   4. Nicht `--stage 1` ohne `--limit`: Das würde die ganze Liste abrufen.
   5. Lehnt das neue Profil einen Shop aus dem Testlauf ab, bleibt er zwar in der Anreicherung, kommt aber nicht mehr in Liste 1 oder 2. Er steht mit Grund in Liste 3. Schon exportierte Leads (`export --mark`) prüft das Profil nicht neu.
6. **Wiederholen,** bis der Nutzer zustimmt.
