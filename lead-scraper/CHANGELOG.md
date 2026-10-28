# Änderungsprotokoll – Lead-Scraper

Neueste Einträge oben. Ein Eintrag je Änderung an Wissen, Pfaden oder Werkzeugen: Datum, was sich geändert hat und warum. So sieht jede KI und jeder Mensch, welcher Stand gilt und was neu ist.

## 2026-10-28

- **Fehler melden und Plan B:** Neues Werkzeug `werkzeuge/fehler_melden.py` meldet eine Fehlermeldung an Agentur Consulting – nur die Meldung, geschwärzt (`.env`-Werte, Schlüssel, Tokens, fremde E-Mails), höchstens 4000 Zeichen, Kontakt aus `AC_KONTAKT_EMAIL`. `CLAUDE.md` und `SKILL.md` haben einen Abschnitt „Wenn etwas schiefgeht“ (zweimal derselbe Fehler → melden; 401/429/5xx erst abwarten und fortsetzen; Plan B: gehosteter Lead-Scraper im Mitgliederbereich und umgekehrt). `START_HIER.md` erwähnt die Meldung in einem Satz.

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
