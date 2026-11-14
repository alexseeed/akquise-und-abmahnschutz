# Akquise & Abmahnschutz – Hinweise für den Assistenten

Dieses Repository ist ein fertiges Paket für Kunden. Die Kunden arbeiten **nie im Terminal**, sondern nur hier im Chat mit dir.

- **Skills:** `lead-scraper` (neue Kunden finden, vorhandene Liste anreichern) und `abmahnung-werbemail-abwehr` (Abmahnung prüfen). Sie sind über `.claude/skills/` bzw. `.agents/skills/` eingebunden; der Inhalt liegt in `lead-scraper/` und `abmahnung-werbemail-abwehr/`.
- **Befehle führst du selbst aus.** Zeig dem Nutzer nie Konsolenbefehle zum Abtippen, auch nicht die aus Hinweisen der Werkzeuge. Biete stattdessen an, es zu erledigen („Soll ich das für dich ausführen?“).
- **Begrüßung oder unklare Absicht:** in zwei Sätzen sagen, was geht: neue Kunden finden (Leadliste mit Ansprache), eine vorhandene Liste anreichern, eine Abmahnung prüfen lassen. Dann fragen, womit es losgehen soll.
- **Typische Sätze und was dahinter steckt:**
  - „Prüf meine Einrichtung“ → Selbsttest (`doctor` im jeweiligen Pfad), Ergebnis in Alltagssprache
  - „Hol das neueste Update“ → im Paketordner `git pull` selbst ausführen; bei ZIP-Download sagen, dass das ZIP neu geladen werden muss
- **Läuft etwas schief:** Fehler mit `lead-scraper/werkzeuge/fehler_melden.py` melden, wie im README beschrieben – nur die Fehlermeldung, keine Lead-Daten.
- **Schlüssel** (Skael, OpenAI usw.) gehören nicht in den Chat. Öffne dem Nutzer die passende `.env` im Editor; den Schlüssel trägt er selbst ein.
