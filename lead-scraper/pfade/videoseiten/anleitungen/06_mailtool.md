# Anleitung: Versandliste ins Mailtool übernehmen

**Für den Agenten:** Die Datei `…_mit_landingpage.csv` (Teil E im `ABLAUF.md`) enthält je Lead alle Spalten des Exports plus „Landingpage“ und „Vorschaubild“. Führe den Nutzer durch den Import in sein Mailtool. Die genaue Klickfolge hängt vom Programm ab; öffne bei Unsicherheit die aktuelle Hilfe-Seite des Tools zu „CSV importieren“ und „eigene Variablen“, statt zu raten.

## Was im Mailtool passieren muss

1. **Liste importieren:** die CSV-Datei hochladen. Trennzeichen ist das Semikolon (;), Zeichensatz UTF-8.
2. **Spalten zuordnen:** E-Mail → E-Mail-Adresse, Vorname, Nachname, Firmenname wie angeboten. „Landingpage“, „Vorschaubild“, „Ansprache Formal“ (bzw. die gewünschte Ansprache) und „Personalisierung“ als **eigene Felder** (oft „Custom Variable“, „Benutzerdefiniertes Feld“ oder „Attribut“) anlegen.
3. **In der Mail verwenden:** den Link als Platzhalter einsetzen, je nach Tool zum Beispiel `{{Landingpage}}`. Ein klickbares Vorschaubild: Bild mit der Adresse aus `{{Vorschaubild}}`, verlinkt auf `{{Landingpage}}`. Das Bild liegt auf dem eigenen Server, nicht bei Skael.
4. **Testmail an dich selbst** schicken und den Link anklicken: Es muss deine eigene Seite mit deinem Video erscheinen.
5. **Sperren übernehmen:** Die Liste 5 des Scrapers (gesperrt) und spätere Datenlöschungen (Teil F) als Sperrliste/„Unsubscribes“ im Mailtool hinterlegen.

## Typische Bezeichnungen

| Tool | Eigene Felder heißen | Platzhalter-Schreibweise |
|---|---|---|
| Instantly | Custom Variables | `{{Landingpage}}` |
| lemlist | Custom Variables | `{{Landingpage}}` |
| Brevo | Kontakt-Attribute | `{{ contact.LANDINGPAGE }}` |
| Outlook-Serienbrief | Seriendruckfelder | über „Seriendruckfeld einfügen“ |

Die Tabelle ist eine Orientierung (ungeprüft gegen den aktuellen Stand der Tools). Vor dem ersten Versand immer Schritt 4.

## Vor dem Versand (einmal sagen, nicht belehren)

- Zuerst nur an „Safe to Send“-Adressen, `Risky`/`Unknown` getrennt und vorsichtig.
- Die Datenschutzerklärung ist ergänzt (`05_datenschutzerklaerung.md`).
- E-Mail-Werbung an Firmen ohne Einwilligung bleibt rechtlich riskant (`wissen/08_versand-und-recht.md`).

## Häufige Probleme

| Symptom | Lösung |
|---|---|
| Umlaute kaputt (Ã¤ statt ä) | beim Import UTF-8 als Zeichensatz wählen |
| Alles steht in einer Spalte | Trennzeichen auf Semikolon stellen |
| Link führt auf „Not Found“ | Seiten noch nicht hochgeladen oder Lead hatte kein fertiges Video (steht nicht in der Datei) |
