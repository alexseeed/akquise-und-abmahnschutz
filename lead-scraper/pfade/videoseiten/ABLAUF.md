# Videoseiten – persönliches Video und eigene Landingpage je Lead

**Für dich als Agent (Claude Code oder Codex).** Dieser Pfad schließt an einen fertigen Scrape an: Jeder Lead bekommt ein persönliches Video (Skael) und eine eigene Seite im Branding des Nutzers, gehostet auf seinem eigenen Server. Der Nutzer ist technisch völlig unerfahren.

```
A Seite gestalten ─► B Videos ─► C Server ─► D Seiten erzeugen und hochladen ─► E Versandliste ─► F Betrieb
  (einmal)           (je Liste)   (einmal)    (je Liste)                          (je Liste)
```

## Regeln

- **Du führst jeden Befehl selbst aus** und übersetzt das Ergebnis in einen Satz. Der Nutzer tippt nie einen Befehl.
- **Eine Frage pro Nachricht**, mit Beispiel und Vorschlag. Was du selbst herausfinden kannst (Website, Impressum, Farben), liest du ab und lässt es nur bestätigen.
- **Nutzer-Schritte** (Konto anlegen, kaufen, aufnehmen, Schlüssel erzeugen, DNS-Eintrag) führst du mit der passenden Datei aus `anleitungen/` durch: einen Schritt vorlesen, auf „erledigt“ warten, dann den nächsten. Nie alle Schritte auf einmal.
- **Schlüssel und Geheimnisse nie im Chat.** Du öffnest `pfade/videoseiten/.env` im Editor des Nutzers (bzw. nennst den Pfad), er fügt den Wert ein und speichert. Du liest `.env` nie aus und gibst nichts daraus wieder.
- **Kosten vor jedem kostenpflichtigen Schritt** in Credits und Euro nennen und ein ausdrückliches Ja abwarten. Erst dann `--ja`.
- **Texte auf der Seite:** nur, was der Nutzer belegen kann. Keine erfundenen Zahlen, Kunden oder Zitate. Kundenstimmen nur mit Zustimmung der Kunden.
- Arbeitsordner je Kampagne: `pfade/videoseiten/arbeit/<kampagne>/` (nie weitergeben, enthält personenbezogene Daten).

## Voraussetzungen

| Was | Prüfen | Fehlt es |
|---|---|---|
| Fertiger Scrape mit Lead-Format | `pfade/google-maps/kampagnen/<k>/exports/leads_*.json` | `python3 -m scraper --kampagne <k> export --lead-format` |
| Skael-Schlüssel mit Guthaben | `python3 werkzeuge/videos.py kampagnen` läuft | `wissen/11_zugaenge-und-kosten.md` |
| Website des Nutzers | aus der Auftragsdatei (Block L) | fragen |
| Eigene Domain | aus der Auftragsdatei | ohne Domain keine eigene Seite; Domain kaufen lassen (z. B. beim Hostinger-Kauf mit) |

Alle Befehle in diesem Dokument laufen im Ordner `pfade/videoseiten/`.

---

## A – Seite gestalten (einmal je Nutzer)

1. **Kopie anlegen:** `mkdir -p arbeit/<k> && cp -R vorlage arbeit/<k>/seite`. Ab jetzt nur noch `arbeit/<k>/seite/index.html` ändern, nie `vorlage/`.
2. **Branding:** `python3 werkzeuge/branding.py lesen --url <website> --aus arbeit/<k>/branding`. Zusammenfassung zeigen (Akzentfarbe, Schriften, Logo) und bestätigen lassen. Bei Kontrastwarnung die dunklere Variante vorschlagen.
   Dann die Schriften lokal holen: `python3 werkzeuge/branding.py schriften --familie "<Name>" --gewichte 400,500,600,700 --aus arbeit/<k>/seite/assets/fonts` (für Titel- und Textschrift). Ist es keine Google-Schrift: die vorgeschlagene ähnliche freie Schrift bestätigen lassen.
   Anwenden: `python3 werkzeuge/branding.py anwenden --vorlage arbeit/<k>/seite/index.html --branding arbeit/<k>/branding/branding.json`. Das Logo liegt danach in `assets/`.
3. **Absender und Recht** (Objekt `ABSENDER`): Impressum-Seite des Nutzers öffnen (Link aus `branding.json`), Rechtsträger, Anschrift ablesen, Impressum- und Datenschutz-Link übernehmen. Zeigen, bestätigen lassen. E-Mail für Datenlöschung erfragen (Vorschlag: die Kontaktadresse aus dem Impressum).
4. **Ansprechpartner:** Name, Rolle, Foto. Foto: von der Team-/Über-uns-Seite vorschlagen oder vom Nutzer in `arbeit/<k>/seite/assets/` legen lassen (du nennst den Ordner und öffnest ihn im Finder/Explorer). Ohne Foto erscheinen Initialen.
5. **Termin:** Buchungslink und Dauer. Hat der Nutzer keinen: `anleitungen/04_buchungstool.md`.
6. **Texte** (Objekt `SEITE.texte`): Überschrift, Angebot (3–4 Leistungen, Ablauf, Paketfelder), Kundenstimmen, Fragen. Lies die Website und schlage Formulierungen vor, die dort belegt sind; der Nutzer bestätigt oder korrigiert. Regeln und Bausteine: `../../wissen/16_videoseiten.md`, Abschnitt „Vorlage“.
   - Ansprache „Sie“ oder „du“: einmal fragen. Bei „du“ alle Texte in `SEITE.texte` und die festen Texte der Vorlage umstellen (Liste der Stellen: `wissen/16_videoseiten.md`, „Du-Fassung“).
   - Keine echten Kundenstimmen mit Zustimmung? Dann `"stimmen"` aus `SEITE.bausteine` streichen. Oder belegte Ergebnisse ohne Zitat zeigen (Name des Projekts, Rolle, Ergebnis) und `stimmen_hinweis` auf die Quelle ändern.
7. **Vorschau:** `python3 -m http.server 8000 --directory arbeit/<k>/seite` starten, dem Nutzer `http://localhost:8000` nennen (in Claude Code/Codex mit Browser selbst öffnen). Platzhalter in `<…>` sind gelb markiert. Prüfen auf Handy- und Desktopbreite.
8. **Freigabe:** erst wenn der Nutzer „passt“ sagt und `python3 server/generator.py --vorlage arbeit/<k>/seite/index.html --leads <leads.json> --ziel arbeit/<k>/probe --probe` ohne Fehler läuft und der Lauf ohne `--probe` keine offenen Platzhalter mehr meldet.

## B – Videos (je Liste)

1. **Kampagne vorhanden?** `python3 werkzeuge/videos.py kampagnen`. Keine oder keine mit Aufnahme: mit dem Nutzer `anleitungen/01_skael-video-aufnehmen.md` durchgehen (Nutzer-Schritt).
2. **Prüfen:** `python3 werkzeuge/videos.py pruefen --kampagne <id>`. Jede Warnung dem Nutzer erklären. „Kein Screenshot-Teil“ heißt: jedes Video ist gleich. Nicht ohne seine ausdrückliche Entscheidung weitermachen.
3. **Testvideo:** `python3 werkzeuge/videos.py test --kampagne <id> --leads <leads.json>` nennt die Kosten. Nach dem Ja mit `--ja`. Dann `warten --kampagne <id>` und den Link aus `arbeit/videos_<id>.json` (`landing_page_url`) dem Nutzer zum Ansehen geben. Erst nach seinem „passt“ weiter.
4. **Alle Videos:** `anlegen … ` ohne `--ja` zeigt Anzahl und Kosten; nach dem Ja mit `--ja`. Dann `warten --kampagne <id>` (dauert, bei vielen Videos im Hintergrund laufen lassen und später erneut aufrufen; Fortschritt bleibt erhalten).
5. **Zusammenführen:** `python3 werkzeuge/videos.py zusammenfuehren --kampagne <id> --leads <leads.json>` → `<leads>_mit_video.json`. Fehlgeschlagene Videos erstattet Skael; diese Leads bekommen keine Seite.

An Skael gehen nur Vorname, Firma, Domain, Website und die interne Kennung. E-Mail und Telefon nie: Skael zeigt alles Übergebene offen auf der Videoseite.

## C – Server (einmal je Nutzer)

1. **Kauf und API-Schlüssel** (Nutzer-Schritt): `anleitungen/02_hostinger-vps.md`. Der Nutzer trägt `HOSTINGER_API_TOKEN` in `pfade/videoseiten/.env` ein.
2. `python3 werkzeuge/hostinger.py pruefen` → VM-ID und IP notieren (in `arbeit/<k>/server.md`).
3. `python3 werkzeuge/hostinger.py schluessel --vm <id>` (Zugang für dich, ohne Passwort).
4. **Domain auf den Server zeigen lassen:** `python3 werkzeuge/hostinger.py dns --domain <domain> --name angebot --ip <ip>`. Liegt die Domain nicht bei Hostinger: `anleitungen/03_dns.md` mit dem Nutzer (Nutzer-Schritt).
5. `python3 werkzeuge/hostinger.py einrichten --vm <id> --domain angebot.<domain>`, dann `status`. Fertig, wenn HTTPS antwortet und `X-Robots-Tag: noindex` kommt.
6. **Webhook für die Video-Auswertung** (Nutzer-Schritt, Teil „Webhook“ in `anleitungen/01_…`): Ziel `https://angebot.<domain>/webhook/skael`, in der Kampagne speichern. Danach holst du das Geheimnis selbst: `python3 werkzeuge/videos.py geheimnis --kampagne <id>` (schreibt es in `.env`, ohne es anzuzeigen) und `python3 werkzeuge/hostinger.py geheimnis --vm <id>`. Jede weitere Kampagne genauso; der Server akzeptiert mehrere Geheimnisse.

## D – Seiten erzeugen und hochladen (je Liste)

```bash
python3 server/generator.py --vorlage arbeit/<k>/seite/index.html --leads <leads>_mit_video.json \
        --ziel arbeit/<k>/seiten --basis https://angebot.<domain>
python3 werkzeuge/hostinger.py hochladen --vm <id> --seiten arbeit/<k>/seiten
```

Eine erzeugte Seite selbst öffnen (Link aus `arbeit/<k>/seiten/ergebnis.json`): Text stimmt, vor dem Klick lädt nichts von Dritten, Video startet nach **einem** Klick, Termin-Link führt zum Buchungstool. Dem Nutzer einen Link zum Ansehen geben.

Textänderung nach dem Erzeugen: Vorlage anpassen, denselben Befehl erneut ausführen, wieder hochladen. Vorhandene Seiten behalten Link und Löschdatum, auch wenn die Mails schon raus sind.

## E – Versandliste (je Liste)

```bash
python3 werkzeuge/versandliste.py links --csv <export 1_…csv> --ergebnis arbeit/<k>/seiten/ergebnis.json
```

Ergebnis `…_mit_landingpage.csv` mit den Spalten „Landingpage“ und „Vorschaubild“. Import ins Mailtool mit `anleitungen/06_mailtool.md` (Nutzer-Schritt). Vorher einmal auf `anleitungen/05_datenschutzerklaerung.md` hinweisen: Die Datenschutzerklärung des Nutzers muss Videoseiten und Skael nennen.

## F – Betrieb

- **Datenlöschungen** (wöchentlich oder auf Nachfrage): `scp -i arbeit/ssh/id_ed25519 -o UserKnownHostsFile=arbeit/ssh/known_hosts root@<ip>:/srv/daten/widersprueche.jsonl arbeit/<k>/` und `python3 werkzeuge/versandliste.py loeschungen --datei arbeit/<k>/widersprueche.jsonl --leads <leads>_mit_video.json`. Die Adressen im Mailtool sperren und `python3 -m scraper --kampagne <k> blockliste-import <datenloeschungen.csv>` im Ordner `pfade/google-maps/`. Die Seite selbst ist dann schon gelöscht.
- **Auswertung:** `ereignisse.jsonl` (Seitenaufrufe, Klicks) und `skael.jsonl` (Videoverlauf) auf dieselbe Weise holen und in Sätzen zusammenfassen: wie viele Seiten geöffnet, Videos gestartet, zu 75 % gesehen, Termin-Klicks.
- Seiten verschwinden nach 90 Tagen von selbst.

## Fehler bei Skael, Hostinger oder der Website (Wiederholungen)

Vorübergehende Fehler wiederholen die Werkzeuge selbst (gemeinsame Regel in `werkzeuge/wiederholen.py`, wie im Google-Maps-Pfad): Netzwerkfehler, Zeitüberschreitung, abgerissene Verbindung, Antwort ohne gültiges JSON, HTTP 408/425/429/500/502/503/504 sowie Skael-Fehler mit vorübergehender Ursache. Pausen 2/4/8/16 s (bei 429: 5/10/20/40 s), höchstens 60 s, plus bis zu 25 % Zufall; ein `Retry-After` von Skael/Hostinger gilt vorrangig. Anzahl Versuche: `MAX_RETRIES` in `.env` oder Umgebung (Standard 5). Dauerhafte Fehler (400, 401, 402, 403, 404, 422) brechen sofort mit der Meldung der API ab. `videos.py anlegen`: ein fehlgeschlagener Lead stoppt den Lauf nicht, er bleibt offen und wird beim nächsten Aufruf erneut versucht (nichts wird doppelt angelegt); erst wenn drei Leads nacheinander an einem Skael-Ausfall scheitern, endet der Lauf mit Zusammenfassung. Ein Video, das Skael wegen einer vorübergehenden Ursache (z. B. Zeitüberschreitung) als fehlgeschlagen meldet, legt `anlegen` neu an (höchstens 3-mal, Kosten werden vorher genannt). `warten` fragt nur den Status ab, legt nie neu an und endet spätestens nach `--max-minuten`. `branding.py` versucht die Website höchstens 3-mal; auf dem Server (Vorschaubilder im Generator, Meldung an `MELDUNG_URL`) sind es bewusst nur 3 kurze Versuche, die Meldung läuft im Hintergrund und blockiert den Besucher nicht.

## Wenn etwas hakt

| Symptom | Ursache und Lösung |
|---|---|
| `videos.py`: „Kampagne gibt es nicht“ | falsche Nummer oder Schlüssel eines anderen Skael-Kontos; `kampagnen` zeigt die richtigen |
| Videos schlagen fehl („no chunks“) | Kampagne ohne Aufnahme; Aufnahme nachholen |
| Generator: „Vorlage enthält noch Platzhalter“ | Texte in `<…>` in `ABSENDER`/`SEITE` fehlen; Schritt A6 |
| Seite zeigt kein HTTPS | DNS noch nicht verbreitet (bis zu einigen Stunden) oder A-Record falsch; `anleitungen/03_dns.md`, „Häufige Probleme“ |
| Webhook kommt nicht an | Geheimnis fehlt/falsch: Schritt C6 wiederholen |
| „Skael nicht erreichbar … nach 5 Versuchen“ | Skael gestört; später denselben Befehl erneut ausführen, Fortschritt bleibt erhalten |
