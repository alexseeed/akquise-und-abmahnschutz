# Agenten-Prompts

Alle Prompts wörtlich verwenden und nur die markierten Stellen ersetzen. Immer mit `subagent_type: "general-purpose"` und `model: "sonnet"`.

## Phase 4: Geschäftsführer, Anrede und Confidence

Ein Agent pro Chunk. `NN` durch die Chunk-Nummer ersetzen (`00`, `01`, …) und `<ARBEIT>` durch den Sandbox-Pfad des `arbeit`-Ordners. 6-9 Agenten pro Nachricht parallel starten.

Die Anrede wird bewusst **hier** mitermittelt und nicht in einem eigenen Durchlauf: Der Agent hat den Vornamen ohnehin vor sich, das kostet also keinen zusätzlichen Call und keine zusätzlichen Tokens.

Die scheinbar pedantischen Stellen tragen Gewicht: Punkt 7 hält deinen Kontext klein — ohne ihn schreiben Agenten ihre 40 Ergebnisse in den Antworttext und der ganze Vorteil ist weg. Die HR-Nummer in Punkt 4 ist das einzige Mittel gegen falsche Firmen gleichen Namens.

```
Du recherchierst Geschäftsführer deutscher Firmen. Arbeite strikt nach Vorgabe.

1. Lies <ARBEIT>/gf/chunk_NN.json (per Shell mit `cat`). JSON-Liste mit "firma", "hr", "ort".

2. Für JEDE Firma: EINE WebSearch mit Query: "<firma>" Impressum Geschäftsführer
   Bei unklaren Ergebnissen EINE zweite Suche mit der HR-Nummer. Nicht mehr.

3. Extrahiere:
   - website: Impressums-URL der EIGENEN Firmenwebsite (nicht northdata/creditreform/companyhouse). Falls keine eigene Website auffindbar, beste Registerquelle.
   - gf: ALLE aktuellen Geschäftsführer als Liste "Vorname Nachname". Keine ausgeschiedenen.
   - quelle: "website_impressum" wenn GF auf Firmenwebsite, sonst "handelsregister"
   PRIORITÄT: Erst Website-Impressum. Nur wenn dort kein GF steht, Registerquellen.

4. Genauigkeit:
   - HR-Nummer und Ort zur Verifikation nutzen — es gibt gleichnamige Firmen.
   - Vorsicht bei Länder-Töchtern: ch.firma.com oder firma.at führen zu anderen
     Geschäftsführern als die deutsche GmbH. Nimm die Seite, die zur HR-Nummer passt.
   - Unsicher, ob die Firma die richtige ist? "confidence":"unsicher", sonst "sicher".
   - Nichts auffindbar: gf=[], website="".
   - Erfinde NIEMALS Namen. Lieber leer lassen.

5. ANREDE für den ERSTEN Geschäftsführer aus "gf" bestimmen:
   - anrede: "Herr" oder "Frau" — abgeleitet aus dem VORNAMEN.
   - anrede_confidence: ganze Zahl 0-100. Wie sicher bist du dir beim Geschlecht
     DIESES Vornamens? Kalibriere ehrlich, die Zahl steuert später die Anrede
     in einer echten Kundenansprache:
       95-100 = im deutschen Sprachraum eindeutig (Roland, Susanne, Philipp)
       70-90  = überwiegend eindeutig, seltene Gegenbeispiele (Kim, Noel)
       40-60  = mehrdeutig oder kulturell uneindeutig (Andrea ist in Italien
                männlich, in Deutschland weiblich; Wei, Jin, Kelin)
       0-30   = du kennst den Namen nicht oder rätst nur
   - Wenn du den Namen nicht einschätzen kannst: anrede:"" und anrede_confidence:0.
     Das ist ein völlig akzeptables Ergebnis und besser als Raten — bei niedriger
     Confidence wird später neutral gegrüßt statt jemanden falsch anzureden.
   - Rate NICHT anhand der Firma, des Landes oder des Nachnamens. Nur der Vorname zählt.

6. Schreibe JSON-Array nach <ARBEIT>/gf/result_NN.json (bash heredoc). Format:
{"firma":"...","website":"...","gf":["Vorname Nachname"],"quelle":"website_impressum","confidence":"sicher","anrede":"Herr","anrede_confidence":95}

7. Antworte NUR mit: "chunk_NN: X von N Firmen mit GF, Datei geschrieben". Keine Ergebnisse im Text.
```

Erwartung: ~95% der Firmen bekommen einen GF, ~12% davon markieren die Agenten selbst als unsicher.
Ein Chunk à 40 dauert ~3-4 Minuten und ~45 Tool-Calls im Agenten.

## Phase 4b: Anrede nachziehen

Nur nötig für Zeilen, deren Geschäftsführer nicht von einem Agenten kam — also die Einzelunternehmer, die `merge_amazon.py` direkt aus dem Amazon-Impressum gezogen hat. `anrede.py` schreibt diese Namen nach `arbeit/anrede_todo.json`, wenn welche offen sind. Ist die Datei leer, überspringe diese Phase.

```
Bestimme für jeden Vornamen die Anrede.

Lies <ARBEIT>/anrede_todo.json (per Shell mit `cat`). JSON-Liste mit "vorname" und "nachname".

Für jeden Eintrag:
- anrede: "Herr" oder "Frau", abgeleitet ALLEIN aus dem Vornamen.
- anrede_confidence: ganze Zahl 0-100, wie sicher du dir beim Geschlecht dieses Vornamens bist.
    95-100 = im deutschen Sprachraum eindeutig (Roland, Susanne, Philipp)
    70-90  = überwiegend eindeutig, seltene Gegenbeispiele (Kim, Noel)
    40-60  = mehrdeutig oder kulturell uneindeutig (Andrea ist in Italien männlich,
             in Deutschland weiblich; Wei, Jin, Kelin)
    0-30   = Name unbekannt oder geraten
- Kennst du den Namen nicht: anrede:"" und anrede_confidence:0. Das ist in Ordnung —
  bei niedriger Confidence wird neutral gegrüßt statt jemanden falsch anzureden.
- Rate NICHT anhand des Nachnamens oder der Herkunft. Nur der Vorname zählt.

Keine Websuche nötig, das ist reines Namenswissen.

Schreibe JSON-Array nach <ARBEIT>/anrede_result.json (bash heredoc). Format:
{"vorname":"Roland","nachname":"Mustermann","anrede":"Herr","anrede_confidence":98}

Antworte NUR mit: "X von N Namen bestimmt, Datei geschrieben". Keine Ergebnisse im Text.
```

## Phase 6: Verifikation

Ein Agent für die ganze Stichprobe. Die Zeilen liefert `pruefe.py`.

```
Du prüfst unabhängig, ob recherchierte Geschäftsführer-Angaben stimmen. Sei streng und kritisch.

Prüfe diese Behauptungen, indem du die angegebene Impressums-URL tatsächlich aufrufst
(mcp__workspace__web_fetch; falls die Seite JavaScript-gerendert ist und nur eine leere
Hülle zurückkommt, nutze stattdessen die Chrome-Tools — lade sie per ToolSearch mit query
"select:mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__tabs_context_mcp"):

<HIER DIE ZEILEN AUS pruefe.py EINSETZEN, nummeriert:>
1. <Firma> — behauptete GF: <Namen> — URL: <url>
...

Für jede: Lies das Impressum und stelle fest, welche Geschäftsführer dort TATSÄCHLICH stehen.

Antworte in genau diesem Format, eine Zeile pro Firma:
<Firma> | KORREKT / UNVOLLSTÄNDIG / FALSCH / SEITE_NICHT_ERREICHBAR | tatsächlich im Impressum: <Namen oder "-">

- KORREKT = die behaupteten Namen stimmen exakt mit dem Impressum überein
- UNVOLLSTÄNDIG = behauptete Namen stimmen, aber es stehen weitere GF im Impressum
- FALSCH = mindestens ein behaupteter Name steht nicht im Impressum

Danach eine Zeile: "Fazit: X/N korrekt, Y unvollständig, Z falsch". Sonst nichts.
```

Das Format ist so gewählt, dass du die Quote direkt an den User weitergeben kannst, ohne selbst zu interpretieren. `UNVOLLSTÄNDIG` und `FALSCH` sind bewusst getrennt: Ein fehlender dritter Geschäftsführer ist für die Erstansprache egal, ein falscher Name nicht.
