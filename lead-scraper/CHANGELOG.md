# Änderungsprotokoll – Lead-Scraper

Neueste Einträge oben. Ein Eintrag je Änderung an Wissen, Pfaden oder Werkzeugen: Datum, was sich geändert hat und warum. So sieht jede KI und jeder Mensch, welcher Stand gilt und was neu ist.

## 2026-11-02

- **Retries mit exponential backoff für alle Dienste.** Anlass: Fehler der angebundenen Tools sollen den Scraper nicht abbrechen. Befund vorher: Ein ganzer Lauf brach selten ab, weil jede Stufe Fehler je Zeile abfängt. Es gab aber Lücken, die einzelne Leads kosteten:
  - KI-Aufrufe wiederholten Netzwerkfehler und Zeitüberschreitungen gar nicht.
  - Beim Abholen eines Skael-Auftrags führte jeder Netzwerk- oder 5xx-Fehler sofort zum Abbruch der Zeile.
  - Fehlgeschlagene Skael-Aufträge mit vorübergehender Ursache (z. B. „kununuJobs failed: HTTP 503“) wurden nicht wiederholt.
  - Die Pausen bei 5xx waren mit 1/2/4 s kurz.
  - Ein unerwarteter Fehler in einer Stufe beendete den ganzen `run`.
  - Jetzt gilt eine gemeinsame Regel in `clients.py` (`WIEDERHOLBAR`, `wartezeit`, `voruebergehend`):
    - Wiederholt werden Netzwerkfehler, 408/425/429, 5xx und Skael-„failed“ mit vorübergehender Ursache. Fehlgeschlagene Aufträge bekommen dabei einen neuen Idempotency-Key.
    - Pausen 2/4/8/16 s (429: 5/10/20/40 s), höchstens 60 s, mit Jitter; `Retry-After` wird beachtet.
    - `MAX_RETRIES` steht neu auf 5 (vorher 4).
    - Beim Abholen wird nur erneut abgeholt, nie doppelt eingereicht.
    - Dauerhafte Fehler (401, 402, ungültige Eingabe) brechen sofort ab.
  - `run` und der Testballon führen jede Stufe abgesichert aus: Ein unerwarteter Fehler beendet nur diese Stufe. Am Ende stehen ein Hinweis und Exit-Code 1.
  - 13 neue Offline-Tests in `tests/test_retry.py`. Doku: `pfade/google-maps/CLAUDE.md`.
- **Dieselbe Retry-Regel in allen Pfaden.** Anlass: Gab Skael einen Fehler zurück, „pausierte“ der Scraper oder verlor Arbeit. Der erste echte Testballon bestätigte das: 71 Skael-Fehler (500, 502, Netzwerk) in 2,5 Stunden, alle von den neuen Retries aufgefangen.
  - **Google Maps, Recruiting, Stellensuche:**
    - Antworten ohne gültiges JSON werden wiederholt.
    - Dauerhafte Fehler nennen die Meldung von Skael.
    - Lebenszeichen gegen scheinbaren Stillstand: Jede Stufe meldet spätestens jede Minute ihren Stand, ein lange laufender Skael-Auftrag alle 2 Minuten.
  - **E-Commerce (`ecom/clients.py`):**
    - Gleiche Regel wie Google Maps.
    - Skael-Aufrufe asynchron mit Idempotency-Key und Gesamtfrist. Vorher konnte eine Verbindung bis zu einer Stunde hängen.
    - Abholen über die richtige Adresse `/api/enrichments/{id}`. Vorher wurde dort nach 20 Versuchen neu eingereicht, also doppelt bezahlt.
    - Abgesicherte Stufen, `SKAEL_MAX_WARTEZEIT`.
    - Sperrliste fällt bei Verbindungsabbruch auf die lokale Kopie zurück.
    - 32 neue Tests.
  - **Amazon (`wiederholen.mjs`, neu):**
    - Gemeinsame Regel für Skael, Oxylabs und Bright Data.
    - Oxylabs wiederholte auch dauerhafte Fehler, und das mit Pausen unter 3 s.
    - Skael-„failed“ mit vorübergehender Ursache galt als endgültig (z. B. „kein Impressum“).
    - Das Abfragen bei Bright Data lief bei Fehlern bis zu 30 Minuten weiter. Jetzt bricht es bei dauerhaften Fehlern ab.
    - Pausen enden bei Strg+C sofort, am Ende jedes Starts steht eine Fehlerzeile.
    - 22 Tests (`node --test pfade/amazon/tests/*.test.mjs`).
  - **Videoseiten (`werkzeuge/wiederholen.py`, neu):**
    - Gleiche Regel für Skael-Videos, Hostinger und den Abruf der Website.
    - Ein Fehler beendet nicht mehr den ganzen `anlegen`-Batch. Nach 3 Ausfällen in Folge stoppt er, statt stundenlang zu warten.
    - `warten` legt nie neu an; vorübergehend fehlgeschlagene Videos legt `anlegen` mit neuem `dedupe_value` neu an.
    - Server: Vorschaubild mit kurzen Retries; die Meldung läuft im Hintergrund, der Besucher wartet nicht mehr.
    - 30 neue Tests.
  - **Überall gilt `MAX_RETRIES`, Standard 5.** Ältere `.env`-Dateien mit `MAX_RETRIES=4` überschreiben den neuen Standard.

## 2026-11-01 (2)

- **Testballon: beide Recruiting-Wege vergleichen.** Wunsch des Nutzers: Wer Recruiting-Leads braucht, soll nicht raten müssen, welcher Weg besser liefert. Der Scraper fährt beide mit derselben Zielgruppe und legt das Ergebnis nebeneinander. Danach entscheidet der Nutzer.
  - Neuer Befehl `testballon --name … --suche … --keywords …`: legt `kampagnen/<name>-website` (Recruiting) und `<name>-portale` (Stellensuche) an und fährt jede bis `--ziel` versandfertige Leads (Standard 100). Dann exportiert er je Weg und schreibt einen Vergleichsbericht nach `exports/testballon_<name>_….md`. Der Bericht zeigt Kosten je Lead, Geschäftsführer-Adressen, „Safe to Send“, persönliche Ansprache, Stellenbezug, Anzeigenalter, eine Hochrechnung der Marktgröße, die Überschneidung beider Wege, den Trichter, Beispiele und eine Empfehlung. `--nur-marktprobe` macht nur die günstigen Suchen, `--nur-bericht` schreibt nur den Vergleich neu.
  - Der Lauf je Kampagne (`testballon-lauf`) arbeitet in Runden. In die bezahlte Anreicherung gehen nur so viele Firmen, wie für das Ziel noch fehlen; gerechnet wird mit der gemessenen Quote.
  - **Zu wenig Stellen:** Fallback-Leiter. Portale: erst das Suchfenster erweitern (60 Tage, 3 Seiten, 50 km), dann verwandte Suchbegriffe per KI (neuer Prompt `suchbegriffe_synonyme.txt`). Firmen-Website: erst die NK-Strecke (nur mit Prüfprofil), dann kleinere Städte, ohne schon abgefragte Städte erneut zu bezahlen. Danach meldet der Bericht offen „Markt erschöpft“ mit der erreichbaren Menge und den nächsten Hebeln.
  - **Budget-Deckel für jede Kampagne:** `run --budget <€>` bzw. Testballon `--budget` (Standard 20 € je Weg). Jede bezahlte Stufe stoppt, sobald die echten Skael-Credits das Budget erreichen; ein späterer Lauf macht weiter. `status` zeigt das Budget.
  - Recruiting ohne Prüfprofil: Die offene Stelle ist das Kriterium, wie schon bei der Stellensuche. Eine unveränderte `icp.txt`-Vorlage mit `[[Platzhaltern]]` übernimmt `init` nicht mehr als Profil.
  - Doku: `pfade/google-maps/docs/09_TESTBALLON.md` (neu), Hinweise in `SKILL.md`, `wissen/02`, `05`, `11`, `18`, in beiden `ABLAUF.md` und in `pfade/google-maps/CLAUDE.md`. 9 neue Offline-Tests, insgesamt 44.

## 2026-11-01

- **Beide Recruiting-Wege im Paket.** Firmen, die gerade einstellen, findet der Scraper jetzt auf zwei Wegen. Beide laufen im Programm `pfade/google-maps/` als eigene Kampagnen-Art.
  - **Recruiting über die Firmen-Website – jetzt gebaut** (vorher „geplant“): Firmen über Google Maps, Prüfprofil, dann liest Stufe 3e Startseite und bis zu zwei Karriere-Seiten und erkennt eine offene Stelle. Die gesuchten Berufe kommen je Kampagne aus `init --pfad recruiting --berufe "A,B"` in den branchenneutralen Prompt `stellenanalyse.txt` (`{{Gesuchte Berufe}}`). Opener zur Stelle („ich habe gesehen, dass Sie gerade jemanden als … suchen …“). Optional `--nk`: passende Firmen ohne Stelle bekommen einen Satz zur Website. Anleitung `pfade/recruiting/ABLAUF.md`, Technik `pfade/google-maps/docs/07_RECRUITING.md`, Wissen `wissen/05` (neu gefasst), Herkunft `pfade/recruiting/referenzen/clay-vorlage.md`.
  - **Neu: Stellensuche über Jobportale** (`stellensuche --suche … --orte …`): konkrete Anzeigen aus Indeed, Stepstone, Arbeitsagentur und Kununu über die Skael-Jobendpunkte (Stufen 1j/1k). Zeitarbeit und Personalvermittler fliegen raus; Titel-Filter `--titel-pflicht`/`--titel-ausschluss` lassen sich kostenlos neu anwenden (`run --stage 1k`). Website-Suche per Skael `find_domain` mit Impressum-Beleg. Modus `--nur-stellen` liefert nur Stellen- und Firmenliste, fast kostenlos. Export `0_stellen_…` (eine Zeile je Anzeige). Anleitung `pfade/stellensuche/ABLAUF.md`, Technik `pfade/google-maps/docs/08_STELLENSUCHE.md`, Wissen `wissen/18` mit den Quoten des ersten echten Laufs.
  - **Größen-Check (Stufe 3g)** in der Stellensuche: Die KI sortiert Konzerne, öffentliche Hand/Verbände und IT-Wettbewerber aus Modellwissen aus – vor der bezahlten Website-Suche. Abschaltbar mit `--no-groessen-check`.
  - **Kostenzähler:** Tabelle `kosten` mit den echten Skael-Credits je Dienst; `status` zeigt die Summe als „Skael-Kosten bisher“.
  - Branchengenaue Prompts liegen in `pfade/google-maps/prompts/beispiele/` (`stellenanalyse_logistik.txt`, `personalisierung_stellenanzeige_logistik.txt`, `…_ki.txt`, `icp_logistik.txt`, `icp_ki_automation.txt`); die Standard-Prompts sind branchenneutral. Eine Kampagne überschreibt sie in ihrem eigenen `prompts/`-Ordner.
- **Korrekturen:**
  - `run` verlangt einen OpenAI-Schlüssel nur noch bei `LLM_PROVIDER=openai` oder `DOMAINSUCHE=openai`; Standard ist die KI über Skael.
  - Skael-429: Wiederholung mit wachsender Pause (5/10/20/40 s, höchstens 60 s) und Zufallsanteil (Jitter).
  - `find_domain` bekommt PLZ und den Host eines eigenen Bewerbungslinks als Hinweis.
  - Export: Leads, die später der Größen-Check oder ein geschärfter Filter aussortiert, stehen nicht mehr in Liste 1 oder 2, sondern nur in Liste 4. Firmen ohne Sicherheitswert fielen bisher aus Liste 3 **und** 4 heraus (fehlendes `COALESCE`), jetzt stehen sie in Liste 4.
  - Ansprache-Regel in allen drei Kampagnen-Arten: persönlich nur bei Anrede-Sicherheit > 60, sonst neutral (Spalten „Ansprache“, „Ansprache Grund“, „Anrede Sicherheit“); neue Spalte „Kampagnen-Art“.
- 22 neue Offline-Tests in `pfade/google-maps/tests/test_pfade.py` (Recruiting, Stellensuche, Größen-Check, unveränderter Google-Maps-Pfad).
- Geändert: `SKILL.md` (Pfadwahl mit beiden Recruiting-Wegen), `CLAUDE.md`/`AGENTS.md`, `pfade/google-maps/CLAUDE.md`, `docs/00_ANLEITUNG.md`, `docs/01_PROZESS.md`, `wissen/00`, `01`, `02` (Nachfrage Beruf oder Branche), `07`, `11`, `12`, `13`.
- Ein Vergleich beider Wege an derselben Zielgruppe („Testballon“) folgt in einer eigenen Änderung.

## 2026-10-27

- **Paket auf den Stand des Universal-Scrapers gebracht.** Der Lead-Scraper wird jetzt in einem Repository gepflegt und hierher gespiegelt.
  - **Google Maps:** Kampagnen (`kampagnen/<name>/`, `./scraper.sh`), eigene Blockliste, Skael als Standard-KI, Domainsuche wählbar (Standard aus), Mengenschätzung und Auswahl, Rate-Limiter-Fixes. Neues Lead-Format (`export --lead-format`) mit Quellenfeldern für die Videoseiten. Findymail-Härtung von hier übernommen.
  - **Amazon:** neuer Seller-Scraper (Node.js), findet Drittanbieter auf amazon.de selbst; die alten Skripte unter `pfade/amazon/scripts/` und `referenzen/` entfallen.
  - **Neu: Videoseiten** (`pfade/videoseiten/`): persönliches Skael-Video je Lead, eigene Landingpage im Branding des Nutzers, Hostinger-Server, Versandliste. Wissen: `wissen/16`, Learnings aus dem ersten echten Lauf in `wissen/17`.
  - **E-Commerce** bleibt unverändert verfügbar (Beta); die gemeinsamen Dokumente nennen ihn neben den neuen Teilen.
  - Neu: `wissen/15` (Learnings Architekturbüros, gemessene Kosten je Schritt), `AGENTS.md` für Codex.

## 2026-10-09 (2)

- **E-Commerce-Pfad: Nachbesserungen nach dem Review** von Anforderungen, Shop-Profil und Mailtext.
  - **Shop-Profil nachschärfen wirkt jetzt auch auf den Testlauf:** `set-prompt shopprofil` setzt die Ergebnisse aller aktiven Shops zurück, die noch nicht übergeben **oder** noch nicht exportiert sind, samt Fehlversuchen. Stufe 1c prüft sie neu. Lehnt das neue Profil einen Shop aus dem Testlauf ab, ist sein Lead nicht mehr „Ready to Send“ und steht mit Grund in Liste 3. Vorher kamen genau die beanstandeten Shops in den echten Export.
  - **Sperre auch für 1d und 1e:** Ohne Entscheidung zum Shop-Profil startet kein Lauf mit Traffic oder Übergabe.
  - **Ready to Send** verlangt jetzt berechnete Ansprachen. Scheiterte die Anrede-KI, begann die fertige Mail sonst mit „,“.
  - **Neu versuchen nach neuem Prompt:** `set-prompt shopprofil` und `set-prompt personalisierung` setzen Fehlversuche zurück. Leads mit drei Fehlversuchen bekamen sonst nie einen neuen Satz.
  - **`set-mailtext` prüft mehr:** einfache Klammern (`{Vorname}`) sind ein Fehler; die Begrüßung muss die erste Zeile sein, `{{Personalisierung}}` direkt darunter. Die vollständige Liste der Fehler und Hinweise steht nur noch in `wissen/07_lead-ausgabe-und-spalten.md`.
  - **Builder:** eine Regel für „Vor dem Versand offen“ (fehlender Datenschutz-Link, vom Nutzer abgelehnter Pflichtteil) statt widersprüchlicher „Fertig, wenn“-Regeln; Vorgehen, wenn der Nutzer einen Pflichtteil ablehnt; bei mitgebrachtem Text Sie/Du aus dem Text, Namen außerhalb der Anrede umformulieren, 120-Wörter-Grenze nur für gemeinsam geschriebene Texte; Abmeldesatz per Du; Problem aus dem mitgebrachten Text ablesen statt fragen; Shop-Profil-Fragen 1 und 2 entfallen, wenn die Auftragsdatei sie beantwortet.
  - **Phase 1:** E1 fragt nur noch nach der Datei, wenn die Liste schon feststeht (neue Zeile „Fundort/Liste (C1/C2)“ in der Auftragsdatei); E2 mit Folgefrage, wenn die Liste keine Shopsystem-Spalte hat. `SKILL.md` nennt diese Grenze vor der Pfad-Bestätigung.
  - Korrekturen: `{{Vorname}}` & Co. sind leer, wenn das Impressum keine Geschäftsführung nennt (nicht „bei jedem info@-Lead“); D4 → E3 mit beiden Traffic-Schwellen (`wissen/02`); Profil-Bedingung für Traffic und Übergabe in `docs/01_PROZESS.md` und `docs/05_ABWEICHUNGEN.md` (Nr. 9, 14) wie im Code; Pfad zu `auftraege/` auch für einen kopierten Arbeitsordner. Die Kurzbeschreibung in `SKILL.md` bleibt unter 1.024 Zeichen.

## 2026-10-09

- **E-Commerce-Pfad: Anforderungen, Shop-Profil, Mailtext.** Wunsch des Nutzers: Der Pfad soll wie die anderen feste Anforderungen haben, und Claude soll mit einfachen Rückfragen nachhaken, bis alles für ein sauberes Ergebnis da ist. Mailtexte sollen mit angegeben werden, damit die Personalisierung zur Mail passt.
  - Neu: `pfade/e-commerce/ABLAUF.md`, **Phase 1 – Anforderungen klären** (Pflicht, vor jeder Abfrage). Einzige Quelle der Anforderungsliste A1–D4 und E1–E7 mit den wörtlichen Fragen, „Fertig, wenn“ und der Ergänzung der Auftragsdatei. Die Phasen danach: Liste laden → Testlauf → Vollstart → Export. Im Testlauf zeigt Claude jetzt zwei, drei fertige Mails und holt die Freigabe ein.
  - Neu: **Shop-Profil** in Stufe 1c (neu, nicht in Clay). Aktive Shops werden gegen das Profil des Kunden geprüft, nur passende bekommen Traffic und Anreicherung, nicht passende stehen mit Grund in Liste 3. „Bewusst ohne“ ist möglich, muss aber ausdrücklich entschieden werden.
  - Neu: **Mailtext** (Betreff und Text mit Platzhaltern) und ein **Personalisierungs-Prompt je Auftrag**, gebaut aus Angebot und Mailtext. Der Clay-Prompt `prompts/personalisierung.txt` zielt auf Beratungen und Agenturen; er bleibt nur als Referenz. Export-Listen 1 und 2 bekommen die Spalten `Betreff` und `Mailtext`, wenn ein Mailtext gesetzt ist.
  - Neue Befehle `set-prompt shopprofil|personalisierung`, `set-mailtext`, Block „Anforderungen“ in `status` und `doctor`. `run` bricht mit „Anforderung fehlt“ ab, bevor etwas kostet. Builder `prompts/shopprofil_builder.md` und `prompts/personalisierung_builder.md`, Beispiele in `beispiel/`.
  - Wissen: `wissen/06` (Abschnitt „Was vor dem Lauf geklärt sein muss“, Stufen, Grenzen, offene Punkte), `wissen/02` (Übersetzungstabelle E-Commerce), `wissen/07` (Spalten `Betreff`/`Mailtext`, Platzhalter), `wissen/12` (FAQ), `wissen/13` (Shop-Profil, Mailtext, Platzhalter), `SKILL.md` Schritt 3. Abweichungen 14–16 in `pfade/e-commerce/docs/05_ABWEICHUNGEN.md`, neue Schritte in `docs/01_PROZESS.md`.

## 2026-10-08 (5)

- **Findymail sauber angebunden** (Google Maps und E-Commerce, gemeinsamer Client): direkte API laut Findymail-Doku, Domain statt URL, Wiederholung bei 429/5xx. Leeres Guthaben, pausiertes Abo oder falscher Schlüssel lassen den Lead offen, statt ihn still ohne Geschäftsführer-Adresse abzuschließen. `doctor` zeigt das Restguthaben. 5 neue Offline-Tests. Abweichung 13 in beiden `docs/05_ABWEICHUNGEN.md`, Preise in `wissen/11_zugaenge-und-kosten.md`.

## 2026-10-08 (4)

- **Verteilung an Kunden:** interne Entscheidungsvorlage des Betreibers, nicht Teil dieses Pakets.

## 2026-10-08 (3)

- **Shops ohne Liste finden:** Methode gewählt, noch nicht gebaut. Grundlage: 6 Recherchen mit eigenen Messungen, 3 Architektur-Entwürfe, 2 Gutachten, 3 Gegenprüfungen.
  - Neu: `pfade/e-commerce/referenzen/shop-katalog.md`. Zentraler Shop-Katalog aus den CrUX-Länderlisten mit eigener Shopsystem-Erkennung, wöchentliche Shopware-Nachprüfung, neue Stufe 0 `ecom finden`; Härtung, Recht, Phasen, Entscheidungen.
  - Neu: `pfade/e-commerce/prototypen/` mit den Messwerkzeugen.
  - `referenzen/fingerprints.md`: Regelstand fp v2 (\u-codiertes `window.features` ab 6.7, SW-Header, `/bundles/storefront/`, Gambio GX4, Store-API nur auf dem API-Host) und DNS-Regeln für gehostete Systeme.
  - `referenzen/discovery-quellen.md`: Korrekturen. Die HTTP-Archive-Namen lauten `JTL Shop`/`xtCommerce`. „crt.sh unbrauchbar für Shopify“ gilt nur für `*.myshopify.com`. Neu ist die kostenlose Tech-Report-API.
  - `wissen/06`: Abschnitt „Shops ohne Liste finden“. Als Grenze nachgetragen: Der Pfad hat keinen Sitzland-Filter.
- **Entscheidung:** Übergabe an Stufe 2 nur bei `SEND = true`, vom Betreiber bestätigt.

## 2026-10-08 (2)

- **E-Commerce-Pfad gebaut:** 1:1-Nachbau des Clay-Workbooks „Vorlage | ECOM 2.0“ als Python-Projekt `pfade/e-commerce/` (`python3 -m ecom`), läuft lokal ohne Clay.
  - Stufe 1 (= Clay Import): Website finden, Startseite abrufen, KI-Prüfung „aktiver Onlineshop?“, SimilarWeb-Traffic, Filter SEND.
  - Stufe 2 (= Clay ANREICHERUNG): Impressum, Dedupe auf E-Mail-Domain, E-Mail-Wasserfall, Anrede, Personalisierung, Videotitel, Ready to Send.
  - Clay-Export und alle Formeln/Prompts im Wortlaut in `pfade/e-commerce/docs/`; Prompts wörtlich in `prompts/`.
  - Abweichungen dokumentiert in `docs/05_ABWEICHUNGEN.md`. Wichtigste: Die Übergabe erfolgt nur bei SEND = true (in Clay ohne Laufbedingung), die Domain-Suche läuft über den Skael-Agenten statt Claygent.
  - Offline-Test `tests/test_offline.py` läuft. Ein echter Testlauf steht aus, deshalb Status „Beta“.
- **Wissen:** `wissen/06` neu geschrieben. E-Commerce ergänzt in `01`, `02` (Pfadwahl, Übersetzungstabelle), `07`, `11`, `12`, `13`, `SKILL.md`, `README.md`, `START_HIER.md`. Die Recherche vom Vormittag (`referenzen/`) ist als Ausbau-Idee gekennzeichnet.
- **Prüfskript:** Verweise in Pfad-Dokumenten werden relativ zum Pfad-Ordner aufgelöst.

## 2026-10-08

- **E-Commerce-Pfad: Recherche abgeschlossen** (noch kein Code):
  - `wissen/06_pfad-e-commerce.md` neu geschrieben: Zielbild in 8 Phasen, Quellen, Kosten, Recht und offene Entscheidungen.
  - Neu: `pfade/e-commerce/referenzen/fingerprints.md` (Erkennung von Shopware 5/6, Shopify, WooCommerce, JTL u. a.).
  - Neu: `pfade/e-commerce/referenzen/discovery-quellen.md` (StoreLeads, HTTP Archive, Marktgrößen, Lizenzen).
  - Neu: `pfade/e-commerce/referenzen/architektur.md` (Crawler, Impressum-Auswertung, Register, Recht im Detail).
- **Pflege der Wissensbibliothek:**
  - Neu: `werkzeuge/wissen_pruefen.py`. Es prüft auf abgelaufene `Prüfen bis`-Fristen, fehlende Index-Einträge, tote Verweise und eine veraltete `WISSEN_KOMPLETT.md`.
  - Regeln dazu in `CLAUDE.md` und `wissen/00_INDEX.md`.
  - `Prüfen bis` ergänzt in `wissen/08` und `wissen/11`.
- **Korrektur:** Der Preis der Skael-Maps-Suche ist jetzt 2 Credits je Ergebnisseite statt 1 (`pfade/google-maps/docs/03_SKAEL_API_REFERENZ.md`, laut Skael-Preisliste vom 08.10.2026).

## 2026-10-04

- Ausgangsstand des Pakets: Google-Maps- und Amazon-Pfad verfügbar; Recruiting und E-Commerce geplant.
