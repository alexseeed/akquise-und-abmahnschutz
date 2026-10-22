# Pfad „E-Commerce“

Macht aus einer Shop-Liste versandfertige Leads – ein lokaler Nachbau des Clay-Workbooks „Vorlage | ECOM 2.0“, ohne Clay.

0. **Klären:** Vor dem ersten Lauf fragt die KI nach, bis alles da ist: Shop-Liste, Shopsystem, Mindestgröße, Shop-Profil, Mailtext und persönlicher Satz (`ABLAUF.md`, Phase 1)
1. **Prüfen:** Ist die Website ein aktiver Onlineshop? Passt er zum Shop-Profil? Hat er messbare Besucher?
2. **Anreichern:** Impressum, E-Mail der Geschäftsführung (sonst info@), Anrede, persönlicher Satz passend zum Mailtext, Videotitel
3. **Ausgeben:** CSV-Listen mit fertiger Mail je Lead, nach Abgleich mit der Community-Sperrliste

```bash
cp .env.example .env              # Skael- und OpenAI-Schlüssel selbst im Editor eintragen, nie im Chat
python3 -m ecom doctor                                 # Schlüssel und Community-Sperrliste müssen ✓ zeigen
python3 -m ecom set-prompt shopprofil <datei>          # oder: --ohne (jeder aktive Shop zählt)
python3 -m ecom set-mailtext <datei>                   # prüft den Text, zeigt eine Beispiel-Mail
python3 -m ecom set-prompt personalisierung <datei>
python3 -m ecom status                                 # Block „Anforderungen“: alles ✓?
python3 -m ecom import data/liste.csv                  # CSV (auch Excel-CSV); .xlsx erst als „CSV UTF-8“ speichern
python3 -m ecom run --stage 1 --limit 10   # Testlauf
python3 -m ecom status --shops 20                      # Ergebnis, Grund und Fehler je Shop
python3 -m ecom run --stage all
python3 -m ecom fehler-zuruecksetzen                   # nur nötig, wenn Zeilen nach 3 Fehlversuchen liegen blieben
python3 -m ecom export
```

**Python:** ≥ 3.10. Ist `python3` älter (`python3 --version`), `python3.12` aufrufen; unter **Windows** `py -3.12` statt `python3`.

| Datei | Inhalt |
|---|---|
| `ABLAUF.md` | Anleitung für die KI, Phase für Phase; Phase 1 = Anforderungsliste mit den Fragen an den Nutzer |
| `docs/01_PROZESS.md` | jede Clay-Spalte und ihre Code-Stelle, neue Bausteine, Kosten |
| `docs/05_ABWEICHUNGEN.md` | wo und warum der Nachbau anders arbeitet |
| `docs/clay_spalten_lesbar.md`, `docs/clay_export_ecom_2_0.json` | das Clay-Workbook im Wortlaut (Stand 08.10.2026); Personennamen in Beispielen, Tabellen- und Zugangs-IDs ersetzt |
| `prompts/` | die fünf KI-Prompts aus Clay mit Antwortschema (wörtlich), dazu das Antwortschema der Shop-Profil-Prüfung |
| `prompts/shopprofil_builder.md`, `prompts/personalisierung_builder.md` | Anleitungen für die KI: Shop-Profil bzw. Mailtext und Personalisierung erfragen und bauen |
| `referenzen/shop-katalog.md` | **zurückgestellt:** eigener Katalog durch Crawlen (Methode, Zahlen, Recht). Nur noch Recherche-Grundlage |
| `referenzen/` (übrige) | Shopsystem-Erkennung (fp v2), Quellen für Shop-Listen, Architektur-Ideen |
| `prototypen/` | Messwerkzeuge aus der Recherche (Erkennung, Abruf, DNS, Zertifikats-Parser), kein Produktcode |
| `beispiel/shops_beispiel.csv` | Format der Eingabeliste |
| `beispiel/shopprofil_beispiel.txt`, `beispiel/mailtext_beispiel.txt`, `beispiel/personalisierung_beispiel.txt` | Beispiele für Shop-Profil, Mailtext und Personalisierung (erfundener Absender) |

Voraussetzungen: Python ≥ 3.10, Zugänge bei Skael und OpenAI, optional Findymail; ein Mailtext oder die Bereitschaft, ihn mit der KI zu schreiben. Hintergrund, Grenzen, Recht: `../../wissen/06_pfad-e-commerce.md`.
