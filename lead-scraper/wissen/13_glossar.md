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
| **Brand-Liste** | Export aus einem Amazon-Analyse-Tool mit Marken, dominantem Verkäufer und Umsatzschätzung |
| **Catch-all** | Mailserver, der jede Adresse annimmt; Status `Risky` – Zustellung ungewiss |
| **Dedupe** | Entfernen doppelter Firmen, hier über die Domain |
| **Dominant Seller** | Verkäufer, der die meisten Angebote einer Marke auf Amazon hat; Referenz für die Seller ID |
| **GF / GF Confidence** | Geschäftsführung; Sicherheit, dass die **Firma** richtig zugeordnet ist (`sicher`/`unsicher`) |
| **HR-Nummer** | Handelsregisternummer, z. B. „Amtsgericht Ulm HRB 123456“; Anker gegen gleichnamige Firmen |
| **ICP / Prüfprofil / Wunschkundenprofil** | Beschreibung des idealen Kunden, gegen die jede Website geprüft wird |
| **Keyword / Suchbegriff** | Begriff für die Google-Maps-Suche; jeder zusätzliche Begriff vervielfacht die Kosten |
| **Mailtext (Vorlage)** | die Werbe-Mail des Nutzers: erste Zeile `Betreff: …`, dann der Text mit Platzhaltern. Im E-Commerce-Pfad wird sie je Lead gefüllt und steht im Export in den Spalten `Betreff` und `Mailtext` (`07`). Aus Angebot und Mailtext entsteht die Anweisung für den persönlichen Satz |
| **Modifizierte Unterlassungserklärung** | selbst formulierte, enger gefasste Erklärung ohne Schuldanerkenntnis und ohne Zahlungspflichten |
| **Pfad** | eine Lead-Quelle mit eigenem Ablauf: Google Maps, Amazon, E-Commerce, später Recruiting |
| **Platzhalter** | Stelle in einer Vorlage in doppelten geschweiften Klammern, z. B. `{{Firmenname}}`, die je Lead durch den passenden Wert ersetzt wird. Die Schreibweise muss genau stimmen; unbekannte Platzhalter lehnt der E-Commerce-Pfad ab (`07`, `12`) |
| **Ready to Send / versandfertig** | E-Mail vorhanden (und Personalisierung/Videotitel, wenn eingeschaltet) |
| **Relay** | kleiner Webdienst des Betreibers, der Meldungen an die Sperrliste annimmt und ins Repository schreibt |
| **SEND / Traffic-Filter** | E-Commerce Stufe 1e: Ein Shop geht nur in die Anreicherung, wenn SimilarWeb Besuche misst (Schnitt bzw. Höchstwert ≥ Schwelle, Standard 1) |
| **Safe to Send / Risky / Unknown** | Ergebnis der E-Mail-Prüfung: zustellbar / Catch-all / nicht prüfbar |
| **Seller ID / Storefront** | Amazon-Verkäuferkennung; Link auf alle Angebote eines Verkäufers |
| **Shop-Profil** | E-Commerce: Beschreibung, welche aktiven Shops zum Kunden passen (Region, Sortiment, Ausschlüsse). Die KI prüft jede Startseite dagegen (Stufe 1c); nicht passende Shops kommen mit Grund in Liste 3. Gegenstück zum Prüfprofil im Google-Maps-Pfad. „Bewusst ohne“ = jeder aktive Shop zählt (`06`) |
| **Skael** | Dienst für Google-Maps-Suche, Impressum, E-Mail-Suche und -Prüfung, Website-Abruf |
| **Sperrliste** | Community-Liste von Domains, die nicht angeschrieben werden (`09`) |
| **Stufe 1–4 / 3c** | Abschnitte des Google-Maps-Ablaufs; 3c = Prüfung gegen das Profil |
| **Subagent** | eigenständige KI-Instanz mit eigenem Kontext, die ein Arbeitspaket erledigt und nur eine Zeile zurückmeldet |
| **Testlauf (Dry-Run)** | kleiner Lauf über wenige Städte bzw. ein Arbeitspaket, um Profil und Kosten zu prüfen |
| **UWG § 7** | Verbot unzumutbarer Belästigung; E-Mail-Werbung nur mit vorheriger ausdrücklicher Einwilligung |
| **Widerspruch** | Gelistete Firma verlangt Entfernung von der Sperrliste – wird dauerhaft entfernt |
