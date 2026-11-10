# Glossar

**Zweck:** Begriffe aus Dokumentation, Code und Gespräch – kurz erklärt.
**Für wen:** alle.

---

| Begriff | Bedeutung |
|---|---|
| **Abmahnung** | Aufforderung, ein Verhalten zu unterlassen, meist mit Unterlassungserklärung und Kostenforderung (`10`) |
| **Anrede-Confidence** | Sicherheit (0–100), dass der **Vorname** männlich bzw. weiblich ist; ≤ 60 → neutrale Ansprache |
| **Art. 14 DSGVO** | Informationspflicht, wenn Daten nicht bei der Person selbst erhoben wurden – spätestens bei der ersten Kontaktaufnahme |
| **Art. 15 DSGVO** | Auskunftsrecht; Frist ein Monat |
| **Art. 82 DSGVO** | Schadensersatz bei Datenschutzverstoß; setzt einen konkreten Schaden voraus |
| **Auftragsdatei** | Markdown-Datei mit allen Interview-Antworten in `auftraege/`; der Pfad liest sie und fragt nur, was fehlt |
| **Bestätigt** (Sperrliste) | mindestens zwei unabhängige Meldungen zur selben Domain |
| **Buy-Box** | das Angebot, das bei Amazon beim „In den Einkaufswagen“-Knopf gewinnt; ihr Inhaber ist der Verkäufer, den der Amazon-Pfad prüft |
| **Catch-all** | Mailserver, der jede Adresse annimmt; Status `Risky` – Zustellung ungewiss |
| **Dedupe** | Entfernen doppelter Firmen, hier über die Domain |
| **GF / GF Confidence** | Geschäftsführung; Sicherheit, dass die **Firma** richtig zugeordnet ist (`sicher`/`unsicher`) |
| **Größen-Check** | Stellensuche, Stufe 3g: Die KI stuft jede Firma aus ihrem Modellwissen ein; Konzerne, öffentliche Hand/Verbände und IT-Wettbewerber fallen vor der bezahlten Website-Suche heraus (Liste 4). Abschaltbar mit `--no-groessen-check` (`18`) |
| **HR-Nummer** | Handelsregisternummer, z. B. „Amtsgericht Ulm HRB 123456“; Anker gegen gleichnamige Firmen |
| **ICP / Prüfprofil / Wunschkundenprofil** | Beschreibung des idealen Kunden, gegen die jede Website geprüft wird |
| **Kampagne** (Amazon) | Name eines Laufs (`KAMPAGNE=…`); trennt Lieferliste und Ergebnisse, das Gedächtnis teilen sich alle Kampagnen |
| **Kampagne** (Scraper-Programm) | eine Zielgruppe unter `pfade/google-maps/kampagnen/<name>/` mit eigener `kampagne.env`, eigenen Prompts, Datenbank und Exporten; hat genau eine Art: Google Maps, Recruiting oder Stellensuche |
| **Karriere-Seite** | Seite der Firmen-Website mit Stellenangeboten; die Stellen-Erkennung im Recruiting liest bis zu zwei davon |
| **Kostenzähler** | Tabelle `kosten` in der Datenbank einer Kampagne: echte Skael-Credits je Dienst, wie Skael sie abrechnet; `status` zeigt die Summe als „Skael-Kosten bisher“ (ohne KI-Schritte) |
| **Keyword / Suchbegriff** | Begriff für die Google-Maps-Suche; jeder zusätzliche Begriff vervielfacht die Kosten |
| **Mailtext (Vorlage)** | die Werbe-Mail des Nutzers: erste Zeile `Betreff: …`, dann der Text mit Platzhaltern. Im E-Commerce-Pfad wird sie je Lead gefüllt und steht im Export in den Spalten `Betreff` und `Mailtext` (`07`). Aus Angebot und Mailtext entsteht die Anweisung für den persönlichen Satz |
| **Match-Status** | wie sicher die gefundene Website zur Firma gehört: über das Impressum bestätigt (`register`, `ustid`, `firmenname`, `telefon`, `email`) oder nur vermutet (`domain`, `email-domain`) |
| **Modifizierte Unterlassungserklärung** | selbst formulierte, enger gefasste Erklärung ohne Schuldanerkenntnis und ohne Zahlungspflichten |
| **Oxylabs** | Scraping-Dienst, über den der Amazon-Pfad die amazon.de-Seiten abruft; rechnet je Abfrage ab |
| **Pfad** | eine Lead-Quelle mit eigenem Ablauf: Google Maps, Amazon, E-Commerce, Recruiting (Firmen-Website), Stellensuche (Jobportale) |
| **Platzhalter** | Stelle in einer Vorlage in doppelten geschweiften Klammern, z. B. `{{Firmenname}}`, die je Lead durch den passenden Wert ersetzt wird. Die Schreibweise muss genau stimmen; unbekannte Platzhalter lehnt der E-Commerce-Pfad ab (`07`, `12`) |
| **RC / NK** | die zwei Strecken im Recruiting: RC = Firma mit erkannter offener Stelle (Opener zur Stelle), NK = passende Firma ohne erkannte Stelle (Satz zur Website; nur mit `--nk`) |
| **Ready to Send / versandfertig** | E-Mail vorhanden (und Personalisierung/Videotitel, wenn eingeschaltet) |
| **Relay** | kleiner Webdienst des Betreibers, der Meldungen an die Sperrliste annimmt und ins Repository schreibt |
| **Safe to Send / Risky / Unknown / Invalid / Not Run** | Ergebnis der E-Mail-Prüfung: zustellbar / Catch-all / nicht prüfbar / ungültig (nie anschreiben) / nicht geprüft (nicht per E-Mail anschreiben) |
| **SEND / Traffic-Filter** | E-Commerce Stufe 1e: Ein Shop geht nur in die Anreicherung, wenn SimilarWeb Besuche misst (Schnitt bzw. Höchstwert ≥ Schwelle, Standard 1) |
| **Seller ID / Storefront** | Amazon-Verkäuferkennung; Link auf alle Angebote eines Verkäufers |
| **Shop-Profil** | E-Commerce: Beschreibung, welche aktiven Shops zum Kunden passen (Region, Sortiment, Ausschlüsse). Die KI prüft jede Startseite dagegen (Stufe 1c); nicht passende Shops kommen mit Grund in Liste 3. Gegenstück zum Prüfprofil im Google-Maps-Pfad. „Bewusst ohne“ = jeder aktive Shop zählt (`06`) |
| **Skael** | Dienst für Google-Maps-Suche, Impressum, E-Mail-Suche und -Prüfung, Website-Abruf |
| **Sperrliste** | Community-Liste von Domains, die nicht angeschrieben werden (`09`) |
| **Stellen-Erkennung** | Recruiting, Stufe 3e: Die KI liest Startseite und Karriere-Seiten der Firma und gibt genau eine passende offene Stelle zurück |
| **Stellensuche** | Pfad, der konkrete Anzeigen per Suchbegriff aus Jobportalen holt (Indeed, Stepstone, Arbeitsagentur, Kununu) und je Firma bündelt |
| **Stufe 1–4 / 3c** | Abschnitte des Google-Maps-Ablaufs; 3c = Prüfung gegen das Profil |
| **Testlauf (Dry-Run)** | kleiner Lauf über wenige Städte bzw. 20–50 Amazon-Leads, um Profil, Filter und Kosten zu prüfen |
| **UWG § 7** | Verbot unzumutbarer Belästigung; E-Mail-Werbung nur mit vorheriger ausdrücklicher Einwilligung |
| **Welle** (Amazon) | Abschnitt eines Laufs: Jede Stufe holt nur, was die nächste für das Lead-Ziel noch braucht |
| **Widerspruch** | Gelistete Firma verlangt Entfernung von der Sperrliste – wird dauerhaft entfernt |
