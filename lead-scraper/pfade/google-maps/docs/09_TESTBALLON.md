# Testballon – beide Recruiting-Wege vergleichen

Für Firmen, die gerade einstellen, gibt es zwei Wege:

- **Firmen-Website (Recruiting):** Firmen über Google Maps, offene Stelle auf der eigenen Karriereseite. Anleitung: `../../recruiting/ABLAUF.md`.
- **Jobportale (Stellensuche):** Anzeigen aus Indeed, Stepstone, Arbeitsagentur und Kununu. Anleitung: `../../stellensuche/ABLAUF.md`.

Welcher Weg für eine Zielgruppe besser ist, hängt vom Beruf, von der Branche und von der Region ab. Der Testballon fährt beide Wege mit derselben Zielgruppe, bis jeder rund 100 versandfertige Leads hat. Ein Budget-Deckel begrenzt die Kosten. Am Ende steht ein Vergleichsbericht, und der Nutzer entscheidet.

## Befehl

```bash
./scraper.sh testballon --name fahrer-sued --suche "Berufskraftfahrer,LKW-Fahrer" \
    --keywords "Spedition,Logistik" --land DE --min-population 50000 \
    [--orte "Stuttgart,Ulm"] [--ziel 100] [--budget 20] [--wege website,portale] \
    [--icp-prompt …] [--opener-prompt …] [--stellen-prompt …] \
    [--titel-pflicht "…"] [--titel-ausschluss "…"] [--nur-marktprobe] [--nur-bericht]
```

Ohne `--kampagne` aufrufen: Der Befehl legt seine zwei Kampagnen selbst an.

| Option | Wirkung |
|---|---|
| `--suche` | gesuchte Berufe: Suchbegriffe der Portale und `--berufe` der Stellen-Erkennung auf der Website |
| `--keywords` | Branche für Google Maps (nur Weg Firmen-Website). Ohne diese Option läuft nur der Weg Portale |
| `--land`, `--min-population` | Region für beide Wege |
| `--orte` | nur Portale: feste Orte statt Städteliste |
| `--ziel` | versandfertige Leads je Weg (Standard 100) |
| `--budget` | höchstens so viele Euro Skael-Credits **je Weg** (Standard 20). Gilt dauerhaft für die Kampagne |
| `--icp-prompt` | Prüfprofil für beide Wege. Ohne Profil ist die offene Stelle das Kriterium |
| `--opener-prompt`, `--stellen-prompt` | eigene Prompts; sie werden in die Kampagnen kopiert |
| `--nur-marktprobe` | nur die günstigen Suchen (eine kleine Runde Maps bzw. Portale), ohne Anreicherung |
| `--nur-bericht` | nichts abfragen, nur den Vergleich aus den vorhandenen Daten neu schreiben |

## Was passiert

1. Der Befehl legt die Kampagnen `kampagnen/<name>-website` und `kampagnen/<name>-portale` an. Sie entstehen aus der Vorlage mit passender `kampagne.env`: kein Videotitel, keine Einordnung. Die Google-Maps-Vorlagen mit Platzhaltern werden gelöscht.
2. Er richtet beide Kampagnen ein: `init --pfad recruiting …` bzw. `stellensuche …`.
3. In jeder Kampagne startet `testballon-lauf --ziel … --budget …` als eigener Prozess, nacheinander.
4. `export` schreibt je Weg die fertigen Listen nach `kampagnen/<name>-<weg>/exports/`.
5. Der Vergleichsbericht landet in `exports/testballon_<name>_<zeit>.md` und wird angezeigt.

Ein zweiter Aufruf mit demselben Namen macht weiter. Erledigte Schritte werden nicht noch einmal bezahlt. Das Budget zählt die Kosten seit dem ersten Lauf.

## Der Lauf je Kampagne (`testballon-lauf`)

Der Lauf geht in Runden vor:

1. **Eingang:** die nächsten Maps-Suchen bzw. Portal-Suchen. Zu Beginn sind es 3 bzw. 4 je Runde. Bringt eine Runde zu wenig, verdoppelt sich die Zahl, höchstens auf 24 bzw. 32.
2. **Prüfen:** Größen-Check, Website-Suche (nur Portale), Dedupe, Prüfprofil, Stellen-Erkennung (nur Website).
3. **Übergabe nur nach Bedarf:** In die bezahlte Anreicherung gehen nur so viele Firmen, wie für das Ziel noch fehlen. Gerechnet wird mit der gemessenen Quote „versandfertig je übergebener Firma“, anfangs mit 70 %. Firmen mit offener Stelle kommen zuerst, bei den Portalen die mit den meisten Anzeigen. Bei den Portalen sucht der Lauf auch die Website nur für so viele Firmen, wie nötig sind (Annahme: 50 % Fundquote).
4. **Anreicherung:** Stufen 4a–4h wie im normalen Lauf.

Der Lauf endet, wenn einer dieser Fälle eintritt:

| Grund im Bericht | Bedeutung |
|---|---|
| Ziel erreicht | so viele versandfertige Leads wie `--ziel` |
| Budget aufgebraucht | die Skael-Credits der Kampagne haben das Budget erreicht |
| Markt erschöpft | keine neuen Firmen mehr, alle Fallback-Stufen genutzt |
| Rundenlimit erreicht | 25 Runden (Schutz gegen Endlosläufe) |

## Zu wenig Stellen? Die Fallback-Leiter

Bringt eine Runde nichts Neues und sind alle Suchen erledigt, nimmt der Lauf die nächste Stufe der Leiter:

| Weg | Stufe 1 | Stufe 2 |
|---|---|---|
| Portale | **Suchfenster erweitern:** Anzeigen bis 60 Tage, bis 3 Seiten je Suche (volle Suchen blättern weiter), Umkreis 50 km für neue Suchen. Ältere, schon gespeicherte Anzeigen zählen sofort, ohne neue Abfrage | **Verwandte Suchbegriffe:** Die KI schlägt bis zu 5 Bezeichnungen für dieselbe Tätigkeit vor (Prompt `prompts/suchbegriffe_synonyme.txt`). Sie werden als neue Suchen angelegt |
| Firmen-Website | **NK-Strecke:** Passende Firmen ohne offene Stelle bekommen einen Satz zur Website. Nur mit Prüfprofil, sonst wären es beliebige Firmen | **Kleinere Städte:** Mindestgröße halbieren, bis auf 10.000 Einwohner. Schon abgefragte Städte werden nicht noch einmal bezahlt |

Danach endet der Lauf mit „Markt erschöpft“. Der Bericht sagt dann offen, wie viele Leads der Markt mit diesen Einstellungen hergibt. Er nennt die nächsten Hebel: weitere Berufe oder Branchen, größere Region, beide Wege kombinieren.

## Budget-Deckel

`run --budget <€>` und `testballon-lauf --budget <€>` speichern das Budget in der Kampagne (`budget_credits` in `run_meta`). Gerechnet wird mit 1.000 Credits ≈ 1 €. Jede bezahlte Stufe prüft vor jedem Auftrag die echten Credits aus dem Kostenzähler. Ist das Budget erreicht, bleiben die restlichen Zeilen offen. Ein späterer Lauf mit höherem Budget macht dort weiter.

- Laufende Aufträge werden noch fertig. Das Budget kann deshalb um die Kosten von höchstens `MAX_CONCURRENCY` Aufträgen überschritten werden.
- Gezählt werden nur Skael-Datenabfragen, keine KI-Schritte.
- `--budget 0` hebt den Deckel auf.
- `status` zeigt das Budget und die Kosten bisher.

## Der Vergleichsbericht

| Abschnitt | Inhalt |
|---|---|
| Ergebnis | versandfertige Leads, Status, Skael-Kosten gesamt und je Lead, Anteil Geschäftsführer-Adressen, „Safe to Send“, persönliche Ansprache (Anrede-Sicherheit > 60), Leads mit konkreter Stelle, Anzeigenalter (Median), Marktgröße |
| Empfehlung | Hat nur ein Weg das Ziel erreicht, empfiehlt der Bericht ihn. Sonst den günstigeren je Lead. Liefert der andere Weg deutlich mehr Leads mit Stellenbezug oder Geschäftsführer-Adresse (≥ 15 Prozentpunkte), weist der Bericht darauf hin |
| Überschneidung | Firmen in beiden Ergebnissen (registrierbare Domain) und die Zahl der verschiedenen Firmen insgesamt |
| Trichter | Firmen gefunden → Dedupe → Größen-Check → passend → mit Stelle → angereichert → versandfertig, dazu erledigte Suchen |
| Zu wenig Stellen? | genutzte Fallback-Stufen je Weg und die ehrliche Mengenaussage |
| Kosten je Schritt | die teuersten Skael-Dienste je Weg |
| Beispiele | je Weg 3 Leads: Firma, Stelle, Art der Adresse, Opener. Ohne E-Mail-Adressen und Namen |

Die **Marktgröße** ist eine Hochrechnung: versandfertige Leads je erledigter Suche × alle Suchen der Kampagne. Bei wenigen erledigten Suchen ist sie grob.

## Beide Wege kombinieren

Reicht keiner der Wege allein, lassen sich beide zusammen nutzen. So bekommt keine Firma zwei Mails:

1. In der Kampagne mit dem besseren Ergebnis exportieren.
2. Diese Liste in der anderen Kampagne mit `blockliste-import` als „bereits kontaktiert“ eintragen.
3. Dann dort exportieren.

## Grenzen

- Die Wege laufen nacheinander. Bei großen Budgets dauert das entsprechend.
- Der Weg Firmen-Website prüft alle Firmen einer Maps-Runde (Prüfprofil, Stellen-Erkennung). Nur die Übergabe in die Anreicherung ist auf den Bedarf begrenzt.
- Die Quoten gelten für die Zielgruppe des Testballons. Bei einem anderen Beruf oder einer anderen Region neu messen.
