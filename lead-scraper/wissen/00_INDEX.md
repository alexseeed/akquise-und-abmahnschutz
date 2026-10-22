# Wissensbibliothek – Lead-Scraper und Abmahnschutz

Alles Fachwissen zum Paket als Markdown, unabhängig vom KI-Modell. Jede Datei steht für sich und nennt am Anfang Zweck, Zielgruppe und verwandte Dateien.

## Mit deinem KI-Modell nutzen

| Modell / Werkzeug | So geht's |
|---|---|
| **Claude (Skill)** | Skill `lead-scraper` hochladen – die Bibliothek ist enthalten, Claude liest sie selbst |
| **Claude Code** | Ordner `lead-scraper/` öffnen – `CLAUDE.md` verweist hierher |
| **Claude-Projekt, ChatGPT (Custom GPT / Projekt), Gemini (Gem), NotebookLM** | den Ordner `wissen/` als Projektwissen hochladen – oder die Datei `WISSEN_KOMPLETT.md` aus dem Paketordner, wenn nur eine Datei geht |

Start-Prompt für andere Modelle:

> Du begleitest mich beim Aufbau von B2B-Leadlisten mit dem „Lead-Scraper“. Dein Wissen steht in den hochgeladenen Markdown-Dateien. Beginne mit dem Zielgruppen-Interview aus `02_zielgruppen-interview.md`: eine Frage pro Nachricht, immer mit Beispiel. Beantworte Rückfragen nur aus diesen Dateien. Wenn dort etwas nicht steht, sag das, statt zu raten. Rechtliche Themen sind keine Rechtsberatung.

## Inhalt

| Datei | Worum es geht | Lesen, wenn … |
|---|---|---|
| `01_ueberblick.md` | Gesamtablauf, Pfade, wer was macht | du neu bist |
| `02_zielgruppen-interview.md` | Fragen vor jedem Lauf, Wahl des Pfads, Auftragsdatei | ein neuer Auftrag beginnt |
| `03_pfad-google-maps.md` | Firmen mit Standort: Stufen, Kosten, Prüfprofil, Quoten | der Pfad Google Maps gewählt ist |
| `04_pfad-amazon.md` | Amazon-Seller: Phasen, Voraussetzungen, Quoten, Risiken | eine Amazon-Brand-Liste vorliegt |
| `05_pfad-recruiting.md` | geplant: Zielbild und offene Entscheidungen | der Pfad gebaut werden soll |
| `06_pfad-e-commerce.md` | Onlineshops: erst Anforderungen klären, dann Shop-Liste prüfen (aktiver Shop, passt zum Shop-Profil, Traffic), anreichern und je Lead die fertige Mail ausgeben; Kosten, Grenzen, Recht | eine Liste von Onlineshops vorliegt |
| `07_lead-ausgabe-und-spalten.md` | Ausgabedateien, Spalten, Ansprache-Regeln, Standardformat | die Liste in ein Versandtool soll |
| `08_versand-und-recht.md` | UWG, DSGVO, Pflichtangaben, Quellen-Nutzungsbedingungen | vor dem ersten Versand |
| `09_sperrliste.md` | Community-Sperrliste: Abgleich, Melden, Widerspruch | Fragen zur Sperrliste |
| `10_abmahnung-was-tun.md` | erste Schritte nach einer Abmahnung | eine Abmahnung ist da |
| `11_zugaenge-und-kosten.md` | Konten, Schlüssel, Kostenhebel | vor der Einrichtung, vor großen Läufen |
| `12_fehlerbehebung-faq.md` | typische Probleme und Antworten | etwas klemmt |
| `13_glossar.md` | Begriffe von A bis Z | ein Wort unklar ist |
| `14_neuen-pfad-anlegen.md` | wie Recruiting, E-Commerce & Co. dazukommen | ein Pfad gebaut wird |

## Pflege

- Neues Wissen aus Läufen hier eintragen, nicht nur im Chat: Fundquoten, Fehlermuster, Kosten.
- Jede Datei beginnt mit **Zweck / Für wen / Verwandt**.
- Jede Tatsache steht an einer Stelle; andere Dateien verweisen darauf.
- Fakten, die sich ändern können (Preise, Rechtslage, Quoten, Versionen), stehen unter `**Stand:** JJJJ-MM-TT · **Prüfen bis:** JJJJ-MM-TT`. Ist die Frist abgelaufen, gilt die Angabe als ungeprüft. Die KI sagt das dem Nutzer, statt die Zahl als sicher auszugeben.
- Technische Details zu einem Pfad stehen in `pfade/<pfad>/referenzen/`. Hier steht nur, was Nutzer und KI für Entscheidungen brauchen.
- Prüfen: `python3 werkzeuge/wissen_pruefen.py` (abgelaufene Fristen, fehlende Index-Einträge, tote Verweise, veraltete `WISSEN_KOMPLETT.md`).
- Änderungen mit Datum in `CHANGELOG.md` festhalten.
- Rechtsstand dieser Bibliothek: **Oktober 2026**. Rechtliche Aussagen vor Verwendung prüfen.
