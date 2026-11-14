# Akquise & Abmahnschutz

Ein Paket für B2B-Akquise, von der Zielgruppe bis zur Abmahnung:

```
 1 Interview         2 Pfad                 3 Sperrliste          4 Versand        5 Abmahnung?
 Wen willst du?  ──► Google Maps        ──► Abmahner-Domains  ──► dein Tool   ──►  Skill abmahnung-
 Wo findet man       Amazon-Seller          fliegen raus                           werbemail-abwehr
 sie?                E-Commerce                  ▲                                       │
                     Recruiting, Stellensuche    └──── 6 Abmahner wird gemeldet ◄───────┘
```

Je mehr Leute mitmachen, desto vollständiger wird die Sperrliste. **Bedingung der Nutzung:** Wer abgemahnt wird, meldet den Abmahner. Der Skill erledigt das automatisch und zeigt vorher an, was übermittelt wird ([NUTZUNGSBEDINGUNGEN.md](NUTZUNGSBEDINGUNGEN.md)).

## Inhalt

| Was | Wozu | Für wen |
|---|---|---|
| `skills/lead-scraper.zip` | Claude-Skill: Interview, Pfadwahl, Google-Maps- und Amazon-Pfad, Sperrlisten-Abgleich, Wissensbibliothek | jeder Nutzer |
| `skills/abmahnung-werbemail-abwehr.zip` | Claude-Skill: Abmahnung prüfen, Antwort und Unterlassungserklärung als PDF, Website des Abmahners sichern, Meldung an die Sperrliste | jeder Nutzer |
| `lead-scraper/` | derselbe Skill als Ordner – zum Öffnen in Claude Code | jeder Nutzer |
| `lead-scraper/wissen/` | **Wissensbibliothek**: alles Fachwissen als Markdown, für jedes KI-Modell | jeder Nutzer |
| `WISSEN_KOMPLETT.md` | die Wissensbibliothek in einer Datei (für ChatGPT, Gemini & Co.) | jeder Nutzer |
| `abmahnung-werbemail-abwehr/` | der Abmahnungs-Skill als Ordner | jeder Nutzer |

## Für Nutzer

Du brauchst kein Terminal. Alles läuft im Chat mit Claude Code oder Codex.

1. **Paket holen und öffnen:** Auf GitHub bei `alexseeed/akquise-und-abmahnschutz` auf „Code“ → „Download ZIP“ und entpacken – oder in Claude Code bzw. Codex sagen: *„Hol mir github.com/alexseeed/akquise-und-abmahnschutz in einen neuen Ordner.“* Dann den Ordner in Claude Code oder Codex öffnen: Die beiden Skills `lead-scraper` und `abmahnung-werbemail-abwehr` sind damit sofort eingerichtet, ohne Installation. In Claude Code kannst du sie auch direkt aufrufen: `/lead-scraper`. Anderer Weg: In der Claude-App (Chat) beide ZIPs aus `skills/` unter Einstellungen → Funktionen → Skills hochladen.
2. **Loslegen:** *„Ich will neue Kunden finden.“* Claude fragt nach Angebot, Wunschkunden, Fundort, Ländern und Umfang. Danach schlägt es den passenden Weg vor und macht erst einen Testlauf.
3. **Voraussetzungen je Weg** (Details in `lead-scraper/wissen/11_zugaenge-und-kosten.md`):
   - **Google Maps:** Python 3.10+, eigener Zugang bei Skael (die KI läuft standardmäßig über Skael). OpenAI nur bei `LLM_PROVIDER=openai` oder `DOMAINSUCHE=openai`, dann mit aufgeladenem Guthaben.
   - **Amazon:** Node.js 18+, Oxylabs-Zugang (Pflicht); Bright Data für Kontaktdaten; Skael für E-Mail-Prüfung (Pflicht bei E-Mail-Versand), Website und Geschäftsführung. Zugänge in `pfade/amazon/.env`.
   - **E-Commerce:** eine Shop-Liste als CSV (Firmenname und/oder Website), Python 3.10+, eigene Zugänge bei Skael und OpenAI.
4. **Ergebnis:** Versandlisten ohne die Firmen auf der Sperrliste. Die gesperrten Firmen stehen in einer eigenen Datei – nie anschreiben.
5. **Abmahnung bekommen?** Das PDF in Claude legen: *„Ich habe diese Abmahnung wegen einer Werbe-Mail bekommen, bitte prüfen.“*
6. **Fragen zwischendurch:** einfach stellen. Die Antworten kommen aus der Wissensbibliothek. Mit einem anderen KI-Modell: `WISSEN_KOMPLETT.md` hochladen und den Start-Prompt aus `lead-scraper/wissen/00_INDEX.md` nutzen.

Nur die Sperrliste, ohne Scraper: `https://raw.githubusercontent.com/alexseeed/werbemail-sperrliste/main/data/sperrliste.txt` als Domain-Sperre ins eigene Versandtool importieren.

**So arbeiten wir sauber:** persönliche Ansprache mit klarem Absender, Abmeldeweg und Datenschutzhinweis nach Art. 14 DSGVO; Widersprüche sofort sperren; jede Liste vor dem Versand mit der Sperrliste abgleichen. Die Checkliste steht in `lead-scraper/wissen/08_versand-und-recht.md`. Keine Rechtsberatung.

## Betreiber

Diese Kunden-Fassung und die Sperrliste ([alexseeed/werbemail-sperrliste](https://github.com/alexseeed/werbemail-sperrliste)) betreibt Heeg Consulting GmbH (Agentur Consulting), Kontakt: support@agentur-consulting.de. Die Betreiber-Werkzeuge sind hier nicht enthalten. Meldungen an die Sperrliste sind noch nicht freigeschaltet. Läuft etwas schief, kann dein Claude Code die Fehlermeldung automatisch an uns schicken – nur die Meldung selbst, geschwärzt, an unsere Meldestelle (`werkzeuge/fehler_melden.py`); steht deine registrierte E-Mail als `AC_KONTAKT_EMAIL` in der `.env`, können wir uns bei dir im Google Chat melden.
