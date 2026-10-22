# Pfad „Amazon-Seller“

Macht aus einer Amazon-Brand-Liste (z. B. SmartScout-Export) eine Kontaktliste:

1. Seller ID
2. Storefront-Link
3. Amazon-Impressum (Firma, Handelsregister, Adresse)
4. Website und Geschäftsführung
5. Anrede und fertige Ansprache
6. Stichprobenprüfung
7. Sperrlisten-Abgleich

| Datei | Inhalt |
|---|---|
| `ABLAUF.md` | Anleitung für die KI, Phase für Phase |
| `scripts/analyse.py` | Bestandsaufnahme: was fehlt, Arbeitspakete anlegen |
| `scripts/browser_lib.js` | wird in eine amazon.de-Seite geladen und holt Seller IDs und Impressen |
| `scripts/merge_amazon.py` | Seller IDs, Storefront-URLs und Impressum in die CSV |
| `scripts/merge_gf.py` | Ergebnisse der Geschäftsführer-Recherche in die CSV |
| `scripts/anrede.py` | Anrede und Ansprache nach festen Regeln |
| `scripts/pruefe.py` | Plausibilitätsprüfung |
| `referenzen/agent-prompt.md` | Prompts für die Recherche-Agenten |
| `referenzen/browser-technik.md` | Daten in den Browser hinein und wieder heraus |
| `referenzen/spalten.md` | Ein- und Ausgabespalten, Quoten aus einem realen Lauf |

Voraussetzungen:

- Chrome mit eingeloggter amazon.de-Sitzung und der Erweiterung Claude in Chrome
- Claude mit Subagenten (Claude Code oder Cowork)
- Python 3

Hintergrund, Grenzen und Risiken: `../../wissen/04_pfad-amazon.md`.
