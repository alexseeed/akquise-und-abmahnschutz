
# Pfad „Amazon-Seller“ – Brand-Liste zur Kontaktliste anreichern

> **Einstieg:** Dieser Pfad wird über `SKILL.md` (bzw. `CLAUDE.md`) gewählt. Die Rahmenfragen (Angebot, Zielgruppe, Länder, Ansprechpartner, Kanal) sind dann schon beantwortet – nicht erneut fragen. Hintergrund für Menschen und andere KI-Modelle: `wissen/04_pfad-amazon.md`.
>
> **Voraussetzungen:** eine Brand-Liste als CSV (typisch: SmartScout-Export mit `Brand Name`, `Dominant Seller`, `Est. Monthly Revenue`), Chrome mit eingeloggter amazon.de-Sitzung und der Claude-in-Chrome-Erweiterung, Subagenten für Phase 4. Alle Befehle laufen aus dem Ordner `pfade/amazon/`.

Aus einer rohen Brand-Liste wird eine Kontaktliste. Die Kette ist strikt sequenziell — jeder Schritt braucht das Ergebnis des vorigen:

```
Brand Name + Dominant Seller
  → Phase 1  Seller ID          (Amazon-Brand-Suche im Browser)
  → Phase 2  Storefront-URL     (aus der Seller ID gebaut)
  → Phase 3  Firma              (Amazon-Impressum: Name, HR-Nummer, Adresse)
  → Phase 4  Website + Geschäftsführer + Anrede   (Multi-Agent, Sonnet)
  → Phase 5  Ansprache          ("Guten Tag Herr Mustermann" / "Guten Tag")
  → Phase 6  Verifikation
  → Phase 7  Sperrlisten-Abgleich (Abmahner-Domains raus)
```

Ohne Seller ID kein Impressum, ohne Impressum kein Firmenname, ohne Firmenname kein Geschäftsführer, ohne Vornamen keine Anrede. Wer eine Phase überspringt, produziert Lücken, die später niemand mehr zuordnen kann. `analyse.py` sagt dir, wo die Liste gerade steht — vielleicht sind Phasen schon erledigt.

Der Engpass ist nie die Rechenzeit, sondern **Tool-Calls und Kontext**. Jeder Schritt ist deshalb so gebaut, dass Massendaten *niemals* durch dein Kontextfenster laufen. Wenn du dich dabei erwischst, hunderte Zeilen JSON zu pasten oder zu lesen, machst du es falsch — halte an und lies `referenzen/browser-technik.md`.

## Phase 0: Bestandsaufnahme (immer zuerst)

Nie raten, was fehlt. Zähle es:

```bash
python3 scripts/analyse.py <pfad/zur/liste.csv>
```

Das gibt aus, wie viele Zeilen welche Felder haben, und legt neben der Liste einen `arbeit/`-Ordner mit den Chunk-Dateien für die nächsten Phasen an. Zeig dem User die Zahlen und die geschätzte Laufzeit, bevor du loslegst.

**Vorprüfung Browser** (nur nötig, wenn Seller IDs oder Impressum fehlen): Der Amazon-Teil braucht Chrome mit eingeloggter amazon.de-Session, sonst liefert Amazon andere Seiten. Prüfe mit `mcp__claude-in-chrome__list_connected_browsers`. Kein Browser verbunden → sag das dem User klar und brich ab, statt in Phase 1 zu scheitern.

## Phase 1: Fehlende Seller IDs

**Das Prinzip, das alles trägt:** Du navigierst *einmal* zu einer amazon.de-Seite und feuerst von dort per JavaScript hunderte `fetch()`-Aufrufe ab. Weil du same-origin bist, greift CORS nicht, und weil du im Seitenkontext parst, kommt nur das Ergebnis zurück — nicht die 1,8 MB HTML. Ein Durchlauf schafft ~1.500 Brands in ~30 Minuten bei etwa 40 Tool-Calls.

Ablauf:

1. Tab auf eine beliebige Produktseite navigieren (`https://www.amazon.de/dp/B0CLXXWCGM` geht immer).
2. `scripts/browser_lib.js` per `javascript_tool` injizieren — der Dateiinhalt ist direkt als `text` einsetzbar.
3. Die Todo-Liste per **Datei-Upload** in die Seite geben, nicht per Paste. Warum: 1.500 Brands durchzupasten kostet ~40k Tokens, der Upload kostet 3 Calls. Wie das geht, steht in `referenzen/browser-technik.md` unter "Daten rein".
4. Worker starten: `__start(6)`. Mehr als ~8 Worker lassen den Renderer einfrieren.
5. Alle ~35 Sekunden pollen: `({done: __out.length, queued: __q.length})`. Länger als 40s warten geht nicht — der CDP-Aufruf läuft in ein Timeout.
6. Wenn fertig: `__save('seller_ids.json')` und die Datei aus dem Downloads-Ordner einlesen.

Die Matching-Regel: Eine Seller ID wird **nur** übernommen, wenn der Amazon-Verkäufername exakt (normalisiert: lowercase, ohne Sonderzeichen) dem Wert in `Dominant Seller` entspricht. Das ist bewusst streng — Amazon-Suchergebnisse sind voller Fremdprodukte und Anzeigen, und eine falsche Seller ID vergiftet alle Folgeschritte. Erwarte ~90% Trefferquote; der Rest sind Brands, deren Dominant Seller nicht unter den ersten sechs Treffern auftaucht.

## Phase 2: Storefront-URLs

Reine Rechenarbeit, kein Netzwerk:

```
https://www.amazon.de/s?me=<SELLER_ID>&marketplaceID=A1PA6795UKMFR9
```

Die Marketplace-ID ist für amazon.de konstant. `scripts/merge_amazon.py` erledigt das zusammen mit Phase 3.

## Phase 3: Amazon-Verkäufer-Impressum

`https://www.amazon.de/sp?seller=<ID>` liefert einen Impressum-Block mit genau sieben Feldern: Geschäftsname, Geschäftsart, Handelsregisternummer, UStID, Telefon, E-Mail, Geschäftsadresse.

**Wichtig, weil es sonst Stunden kostet:** Dort steht **kein Geschäftsführer**. Erwarte ihn nicht und versprich ihn dem User nicht aus dieser Quelle. Nur in Ausnahmefällen tragen Verkäufer die Person selbst in den Geschäftsnamen ein (`Muster Handel GmbH/Mustermann Max`) — das sind etwa 1 von 1.000. Der Wert dieser Phase liegt woanders: Geschäftsname und HR-Nummer sind der verlässliche Anker für Phase 4.

Technisch identisch zu Phase 1 — gleiche Bibliothek, gleicher Worker-Pool, `__startImpressum(6)`. Läuft schneller, weil pro Seller nur eine Seite geholt wird (~4-5/s).

Danach zusammenführen:

```bash
python3 scripts/merge_amazon.py <liste.csv> arbeit/seller_ids.json arbeit/impressum.json
```

Das schreibt Seller IDs, Storefront-URLs und die Impressumsfelder in die CSV und legt die Chunks für Phase 4 an.

## Phase 4: Website, Geschäftsführer und Anrede per Multi-Agent

Hier wird der Trick gewechselt. Fremde Domains kannst du nicht aus der Amazon-Seite heraus fetchen — CORS blockt, und zwar jeden Host. Der Browser-Weg müsste pro Firma navigieren und lesen; bei 1.000 Firmen sind das tausende Calls.

**Subagenten lösen das**, weil jeder sein eigenes Kontextfenster hat. Die ~900 Tokens Suchergebnis pro Firma landen dort, nicht bei dir. Der Agent schreibt sein Ergebnis in eine Datei und meldet dir nur eine Zeile zurück. So kosten 960 Firmen dich etwa 25 Agenten-Calls und ~10k Tokens statt ~870k.

Vorbereitung erledigen `analyse.py` bzw. `merge_amazon.py`: `arbeit/gf/chunk_00.json` … je 40 Firmen, nach Umsatz absteigend, dedupliziert nach Geschäftsname.

Starte die Agenten mit `subagent_type: "general-purpose"` und **`model: "sonnet"`** — die Aufgabe ist schematisch, Sonnet reicht und ist deutlich schneller. Schicke **6-9 Agenten pro Nachricht** parallel; ein Chunk à 40 Firmen dauert ~3-4 Minuten.

Den Prompt-Text nimm wörtlich aus `referenzen/agent-prompt.md` und ersetze nur die Chunk-Nummer. Er ist auf drei Dinge getrimmt, die sonst zuverlässig schiefgehen:

- **Nur eine Zeile zurückmelden.** Sonst schreiben die Agenten dir ihre 40 Ergebnisse in den Antworttext und der ganze Kontextvorteil ist weg.
- **Erst Website-Impressum, dann Handelsregister.** Der Geschäftsführer soll aus der Firmenwebsite kommen; northdata und Co. sind Fallback, wenn die Website ihn nicht nennt.
- **Anrede gleich mitliefern.** Der Agent hat den Vornamen ohnehin vor sich — die Anrede dort mitzunehmen kostet keinen zusätzlichen Call. Ein eigener Durchlauf dafür wäre pure Verschwendung.

Zusammenführen:

```bash
python3 scripts/merge_gf.py <liste.csv> arbeit/gf/
```

### Was hier realistisch herauskommt

Etwa 40% der Zeilen bekommen einen Geschäftsführer. Das klingt wenig, ist aber nah an der Obergrenze: Ein großer Teil der Amazon-Seller sind Firmen aus Hongkong und China, die keinen Geschäftsführer im deutschen Sinn haben. Rechne bei den gefundenen Namen mit ~10-20% Fehlern. Sag das dem User von dir aus — eine Leadliste, der er blind vertraut, ist gefährlicher als eine, deren Grenzen er kennt.

Zwei Fehlermuster, die du kennen solltest:

- **Länder-Töchter.** Der Agent findet `ch.example.com/impressum` statt `example.de/impressum` und liefert die Geschäftsführerin der Schweizer Tochter. Die HR-Nummer im Chunk ist das Gegenmittel — sie steht im Prompt, damit der Agent gegenprüfen kann.
- **Unvollständige Listen.** Agenten arbeiten aus Suchergebnis-Snippets. Nennt die Website drei Geschäftsführer, kommen manchmal nur zwei zurück. Für die Erstansprache reicht das, für Vollständigkeit nicht.

Deshalb schreibt `merge_gf.py` eine `GF Confidence`-Spalte. Die als `unsicher` markierten Zeilen gehören vor jeder Ansprache geprüft.

## Phase 5: Anrede und Ansprache

Das ist die Spalte, mit der der User am Ende arbeitet — hier landet das Ergebnis der ganzen Kette.

```bash
python3 scripts/anrede.py <liste.csv>
```

Die Regeln stecken im Skript, nicht in den Agenten. Absicht: Schwellwert und Wortlaut gehören an *eine* Stelle, sonst laufen sie über zwanzig Agenten-Antworten auseinander.

| Situation | `Ansprache` |
|---|---|
| Anrede-Confidence **> 60** | `Guten Tag Herr Mustermann` (nur Nachname) |
| Anrede-Confidence **≤ 60** | `Guten Tag` |
| GF-Angabe als `unsicher` markiert | `Guten Tag` |
| kein Geschäftsführer gefunden | `Guten Tag` |

Die Asymmetrie ist gewollt: Jemanden mit falschem Geschlecht oder falschem Namen anzuschreiben kostet den Lead sofort — ein neutrales „Guten Tag" kostet nichts. Im Zweifel also neutral. Deshalb gilt die Regel auch dann, wenn der Vorname eindeutig ist, die Firmenzuordnung aber wackelt.

`Ansprache Grund` hält fest, *warum* jemand neutral gegrüßt wird (`Vorname mehrdeutig (50%)`, `GF-Angabe unsicher`, …). Ohne diese Spalte ist die Ansprache eine Blackbox und niemand kann prüfen, ob die Schwelle richtig sitzt.

Meldet das Skript offene Namen (`anrede_todo.json`), stammen die aus dem Amazon-Impressum statt von einem Agenten — für die hat noch niemand ein Geschlecht bestimmt. Dann Phase 4b aus `referenzen/agent-prompt.md` fahren (ein einziger Agent, keine Websuche nötig) und danach:

```bash
python3 scripts/anrede.py <liste.csv> arbeit/anrede_result.json
```

## Phase 6: Verifikation

Nicht optional. Zieh 5 Zufallstreffer und lass einen Subagenten (`model: "sonnet"`) die Impressums-Seiten **tatsächlich aufrufen** und gegen die behaupteten Namen prüfen. Der Prompt steht in `referenzen/agent-prompt.md` unter "Phase 6: Verifikation".

Viele Impressen sind JavaScript-gerendert. `web_fetch` liefert dann nur eine leere Hülle — das ist kein Beleg dafür, dass die Seite kaputt ist, sondern der Hinweis, über die Chrome-Tools zu gehen.

Prüf außerdem programmatisch, das kostet nichts:

```bash
python3 scripts/pruefe.py <liste.csv>
```

Berichte die gemessene Quote ehrlich — und sag dazu, dass 5 Stichproben keine belastbare Quote sind, sondern eine Größenordnung.

## Phase 7: Abgleich mit der Community-Sperrliste (Pflicht vor jeder Ansprache)

```bash
python3 ../../werkzeuge/sperrliste_abgleich.py <liste.csv>
```

Schreibt `<liste>_bereinigt.csv` (für die Ansprache) und `<liste>_gesperrt.csv` (nie anschreiben). Abgeglichen werden Website- und E-Mail-Spalten; Zeilen ohne eigene Website lassen sich nicht abgleichen – das dem User sagen. Ist die Liste nicht ladbar, bricht das Skript ab.

## Spalten

Die Eingabelisten sehen praktisch immer gleich aus. Gelesen werden `Brand Name`, `Dominant Seller`, `Seller ID`, `Est. Monthly Revenue`. Geschrieben bzw. angelegt werden `Seller ID`, `Seller Storefront URL`, `Match Method`, `Geschäftsname (Impressum)`, `Handelsregister`, `Geschäftsadresse`, `Website`, `GF Vorname`, `GF Nachname`, `GF Alle`, `GF Quelle`, `GF Confidence`, `Anrede`, `Anrede Confidence`, `Ansprache`, `Ansprache Grund`.

Alle Skripte sind idempotent: Sie überschreiben nie eine bereits gefüllte Seller ID und überspringen Zeilen, die schon einen Geschäftsführer haben. Ein abgebrochener Lauf wird einfach neu gestartet. Details in `referenzen/spalten.md`.

Am Ende dem User immer vier Zahlen nennen: wie viele Zeilen eine Seller ID haben, wie viele einen Geschäftsführer, wie viele eine persönliche Ansprache – und wie viele wegen der Sperrliste rausgefallen sind. Die dritte ist die, die zählt.

## Zwischenstände sichern

Die Browser-Phasen laufen lange und der Tab kann einfrieren. Sichere alle ~1.500 Datensätze mit `__save()`. Chrome erlaubt pro Tab nur *einen* automatischen Download und blockt den zweiten stillschweigend — der Umweg über `localStorage` und einen frischen Tab steht in `referenzen/browser-technik.md`.
