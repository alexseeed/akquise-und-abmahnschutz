# Learnings aus der Kampagne Architekturbüros DACH (Oktober 2026)

**Zweck:** Erkenntnisse aus einem echten Lauf, damit der nächste Lauf günstiger, schneller und sauberer wird.
**Für wen:** Betreiber, Nutzer und KI-Modelle, die den Google-Maps-Pfad bedienen.
**Verwandt:** `02_zielgruppen-interview.md` · `03_pfad-google-maps.md` · `09_sperrliste.md` · `11_zugaenge-und-kosten.md` · `12_fehlerbehebung-faq.md`

---

## 1. Kosten

### Gemessene Skael-Kosten pro Schritt
Messung über den Kontostand vor und nach jedem Schritt (Bamberg + Passau, 62 fertige Leads, 1.185 Credits):

| Schritt | Preis laut Skael | Credits je fertigem Lead | Anteil |
|---|---|---|---|
| Städteliste | 10 je Land | – | – |
| Maps-Suche | 2 je Seite (bis 200 Treffer) | 0,1 | 1 % |
| ICP-Check | 2 direkt / 4 Proxy | 3,7 | 19 % |
| Impressum | 5 direkt / 10 Proxy / 0 ohne Treffer | 4,9 | 26 % |
| E-Mail finden | 15 gültig / 5 riskant / 0 nicht gefunden | 5,2 | 27 % |
| E-Mail prüfen | 3 pauschal | 3,0 | 16 % |
| Website-Text | 2 direkt / 5 Proxy | 2,0 | 10 % |
| **Summe** | | **≈ 19 Credits ≈ 1,9 Cent** | |

- Der ICP-Check kostet je Lead mehr als je Aufruf, weil nur ein Teil besteht (55 % in mittleren Städten, 75 % in Großstädten).
- Skael ist pro Lead günstig. Teuer wird es nur über die **Menge**.
- Der Kontostand je Organisation lässt sich über das Skael-MCP (`whoami` mit `organization`) abfragen. So lässt sich jeder Schritt messen, bevor der große Lauf startet.
- Das in `whoami` angezeigte Tageslimit (5.000 Credits) galt nicht für Aufrufe über den API-Schlüssel.

### OpenAI-Kosten (gemessen, ca. 2.100 Token Eingabe je Einstiegssatz)
| Modell | je Lead |
|---|---|
| gpt-4o-mini | 0,03 Cent |
| gpt-4.1-mini | 0,09 Cent |
| gpt-4.1 | 0,35–0,46 Cent |

- **Kostenfalle Domainsuche:** Die KI-Domainsuche für Firmen ohne Website lief mit OpenAI-Websuche. Das kostet ca. 1 Cent pro Firma, unabhängig vom Modell. Bei 4.177 Firmen ohne Website waren das rund 40 € und damit mehr als der ganze Rest. In Clay steckt derselbe Schritt (Claygent) unsichtbar in den Clay-Credits.
  → Für Kampagnen abschaltbar über `DO_DOMAINSUCHE=false`. Standard soll künftig Skael sein (`find_domain`, über das Impressum bestätigt, 15–35 Credits), alternativ ganz aus.

### Mengen realistisch schätzen
- DACH ab 50.000 Einwohnern: 268 Orte × 2 Suchbegriffe ergaben **21.000 Firmen**. Geschätzt waren 6.000–10.000.
- Die beiden Suchbegriffe „Architekturbüro“ und „Architekt“ überschneiden sich zu rund 45 %. „Architekt“ bringt viele zusätzliche Treffer, aber auch Fremde (z. B. Raumausstatter).
- **Immer von der Zielmenge rückwärts rechnen**, nicht vom Markt: Zielmenge × ca. 2 Cent (Skael) + Einstiegssatz-Kosten. Den Rest der gefundenen Firmen zurückstellen (`dedupe_status='deferred_menge'`) und bei Bedarf nachziehen.

## 2. Ablauf und Interview

- **Die Mengenfrage (Interview D4) nie überspringen.** Ohne Zielmenge reichert der Scraper alles an, was die Prüfung besteht. Hier wären das 13.000 Leads gewesen, gebraucht wurden 3.000–4.000.
- Vor jedem großen Lauf **jeden Schritt an 2 Städten messen**. Dafür Städte nehmen, die noch nicht abgefragt wurden, sonst verfälscht der Skael-Cache (20 Minuten) die Kosten.
- Skael-Warteschlange kann zeitweise stocken (Aufträge minutenlang `queued`). Nach dem Lauf einen zweiten Durchgang `run --stage 4` einplanen, er holt Ausreißer nach.
- Lange Läufe unabhängig von der Sitzung starten (`nohup caffeinate -i …`). Läufe sind fortsetzbar.
- Stufe 4 hat kein `--limit`. Eine Stichprobe läuft über eine Kopie der Datenbank (`DB_PATH=data/probe.db`).

## 3. Blockliste vs. Community-Sperrliste

- **Bereits kontaktierte Firmen gehören nie auf die Community-Sperrliste.** Die ist öffentlich und nur für Abmahner gedacht. Für Alt-Leads gibt es die private Blockliste: `python3 -m scraper blockliste-import <csv>`.
- Freemail-Domains werden nicht gesperrt, sondern nur die einzelne Adresse. Spalten mit Absenderadressen (z. B. `last_contacted_from`) werden beim Import ignoriert.
- Die Blockliste greift vor dem ICP-Check, das spart Credits. Sie hat 181 von 21.000 Firmen ausgeschlossen.
- Steht in `SPERRLISTE_URL` noch der Platzhalter `OWNER`, bricht der Export ab. Dann bewusst `SPERRLISTE_PFLICHT=false` setzen und das dokumentieren.

## 4. Behobene Fehler im Paket

| Problem | Folge | Lösung |
|---|---|---|
| Websuche über Chat Completions (`web_search_preview`) | HTTP 400, Domainsuche fand nie etwas | Responses-API mit Tool `web_search` |
| Maps liefert Unterseiten (`/impressum.php`, `/kontakt`) | ICP-Check: „nicht erreichbar“ (ca. 6 %) | auf die Startseite kürzen |
| Instagram-/Facebook-Links als Website | alle fielen beim Dedupe auf einen Eintrag zusammen | gelten als „keine Website“ |
| Ausweich-Kategorie „Lead Gen“ fest im Code | passte nur zur Großhandels-Vorlage | `KATEGORIE_NORMALFALL` |
| Domainsuche nur mit Firmennamen | Fehltreffer bei Allerweltsnamen | Stadt wird mitgesucht |
| Dedupe setzt jeden Status zurück | Zurückstellungen gingen verloren | `deferred_menge` bleibt erhalten |
| OpenAI-Guthaben mitten im Lauf leer | Ausfall der KI-Schritte | `OPENAI_API_KEY_FALLBACK`, automatischer Wechsel |
| Mac-System-Python 3.9 | Scraper startet nicht | Homebrew `python3.12` |
| Skael-Standardmodus ist synchron mit Herzschlag (bis 1 h je Anfrage) | Lauf hing stundenlang bei 0 % CPU, unser Zeitlimit griff nie | `async=true` + Abholen über `GET /api/enrichments/{id}?wait=true&wait_time=50`, Frist `SKAEL_MAX_WARTEZEIT` |
| Abholen unter `/api/<endpunkt>/{id}` | 404, Auftrag wurde neu eingereicht | richtige URL `/api/enrichments/{id}`; dazu `Idempotency-Key` (24 h, nie doppelt berechnet) |
| Schlüsselwechsel bei leerem OpenAI-Guthaben (`credit_balance_exhausted`) | parallele Anfragen scheiterten, bevor der Wechsel griff (bis zu 11 Leads je Neustart) | sofort wechseln; noch mit dem alten Schlüssel gesendete Anfragen werden mit dem Ersatz wiederholt |
| Abgerissene Antworten (`IncompleteRead`) | Zeile übersprungen statt wiederholt | `http.client.HTTPException` als Netzwerkfehler behandeln → Wiederholung |

## 5. Prüfprofil (ICP)

- Die erste Fassung war zu streng: Büros flogen wegen der Rechtsform (PartG mbB, Planungsgesellschaft), einzelner Auslandsprojekte oder Zusatzleistungen (Innenarchitektur, Energieberatung) raus.
  → Eine Zeile **„KEIN AUSSCHLUSSGRUND“** im Prompt hat das behoben (Absagen von 118 auf 104 von 435).
- Bei Ausschlüssen immer „als Hauptgeschäft“ formulieren, sonst fliegen Mischbüros raus.
- Richtig aussortiert wurden: Galerien und Foren (Aedes, DAZ), Makler bzw. Projektentwickler, Büros mit über 50 Mitarbeitenden.
- Rund 5 % der Websites liefern kaum Text (reine JavaScript-Seiten, Baustellenseiten) und sind nicht prüfbar.

## 6. Einstiegssatz (Personalisierung)

- **Den Prompt für seinen tatsächlichen Platz in der Mail bauen.** Hier ist das: „Beim Blick auf Ihre Website ist mir aufgefallen, [Satz] Gleichzeitig hatte ich den Eindruck …“. Daraus folgt:
  - Beginn mit „dass“ oder „wie“, genau ein Satz, höchstens 25 Wörter,
  - reine Beobachtung ohne Deutung am Ende, weil die Deutung im Folgesatz steht,
  - keine Überschneidung mit dem Folgesatz (Website, Empfehlungen, Netzwerk, Fachkräfte).
- **Bei dünnen Websites hilft kein Modell.** Lieber einen leeren Satz zurückgeben und im Export den Standardabsatz einsetzen (Spalte „Absatz Beobachtung“). Das betrifft etwa 40 % der Büros.
- Ist die Detailregel zu streng, bleiben zu viele leer (9 von 15). „Eine klar benannte Bauaufgabe oder ein Schwerpunkt genügt“ ergab 9 von 15 mit Satz, leer blieben genau die dünnen Seiten.
- Modellvergleich an 15 Büros:
  - **gpt-4o-mini** ignoriert die Verbotsliste (Engagement, spannend, anspruchsvoll).
  - **gpt-4.1-mini** macht vereinzelt schädliche Aussagen („zurückhaltende Auftragslage“).
  - **gpt-4.1** schreibt am verlässlichsten.
  - Bei 3.000–4.000 Leads liegt der Unterschied unter 15 $.
- Platzhaltertexte auf Websites („Referenz4“) ausdrücklich ausschließen.
- Die Einordnung **Fachkräfte/Projekte** (sichtbare Stellenanzeige) funktioniert, etwa 15 % der Büros suchen Personal. Für diese Gruppe passt eine eigene Mailvariante.

### Ergebnis im Lauf (3.088 Leads)
- 59 % mit konkretem Satz, 41 % Standardabsatz.
- Die Schlusskontrolle hat in 15 von rund 1.840 Sätzen echte Floskeln gefunden (spannend, anspruchsvoll, innovativ, Fokus, Lösungen) und sie durch den Standardabsatz ersetzt.
- Eine Wortliste allein ist zu grob: Eigennamen („Kompetenzzentrum“, „ICONIC AWARD … Innovative Materialien“) und Stellenanzeigen („fünf Jahre Berufserfahrung“) sind keine Floskeln. Treffer vor dem Ersetzen ansehen.

## 7. Mailvorlage

- Den Absatz nicht selbst zusammensetzen, sondern die fertige Spalte „Absatz Beobachtung“ einsetzen.
- Für die Anrede „Ansprache Normal“ nutzen statt „Hallo {Anrede} {Nachname}“. Sonst entsteht bei info@-Adressen „Hallo  ,“.
- Beim Wechsel der Zielgruppe alle Branchenbegriffe in der Vorlage anpassen (hier: „speziell für Ingenieurbüros entwickelt“).

## 8. E-Mail-Qualität

- Bei kleinen Büros landen rund 85 % der Adressen auf „Unknown“, weil deren Mailserver jede Adresse annehmen (Catch-all). Diese Adressen langsam hochfahren oder in eigenen Paketen versenden.
- Die E-Mail-Suche bestätigt manche Adressen schon als „gültig“. Die anschließende Prüfung (3 Credits) ist dann doppelt. Clay macht das genauso. Mögliche Ersparnis: ca. 0,6 Credits je Lead.

## 9. Vergleich mit der Clay-Vorlage „GMAPS 2.5 | ICP Checker“

- Die Abläufe sind identisch: Städte → Maps → Dedupe (inkl. .fr/.nl/.it) → ICP → Impressum → Mailfinder → Verify → Webscraper → Anrede, Einstiegssatz, Videotitel.
- Unterschiede gibt es nur bei den KI-Schritten:
  - Clay sucht Domains mit Claygent (gpt-4o-mini bzw. gemini-2.5-flash-lite) und rechnet über Clay-Credits ab.
  - Clay erzeugt den Einstiegssatz mit gpt-4o-mini in einem einzigen Aufruf.
- Telefon- und LinkedIn-Anreicherung sind in Clay eingebaut, aber abgeschaltet.
- **Vorgabe für das Paket:** Alle KI-Schritte und die Domainsuche laufen standardmäßig über Skael, weil die Rate-Limits einzelner ChatGPT-Konten oft nicht reichen. OpenAI bleibt als optionaler Schalter.
