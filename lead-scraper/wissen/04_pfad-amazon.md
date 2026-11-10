# Pfad „Amazon-Seller“ – Händler auf amazon.de finden und zu Kontakten machen

**Zweck:** was der Pfad leistet, was er voraussetzt, was er kostet, welche Quoten realistisch sind und welche Risiken bestehen.
**Für wen:** Nutzer, die Händler und Marken auf Amazon erreichen wollen, und KI-Modelle, die Rückfragen beantworten.
**Verwandt:** `02_zielgruppen-interview.md` · `07_lead-ausgabe-und-spalten.md` · `08_versand-und-recht.md` · `11_zugaenge-und-kosten.md`
**Technik im Detail:** Anleitung für die KI `pfade/amazon/ABLAUF.md` · alle Einstellungen, Dateien und Spalten `pfade/amazon/README.md`
**Stand:** Oktober 2026

---

## Wann dieser Pfad

Für Firmen, die auf **amazon.de** als Drittanbieter verkaufen, mit eigener Marke oder als Händler. Typische Anbieter, die diese Zielgruppe suchen: Amazon-Agenturen, Logistik und Fulfillment, Finanzierung, Software für Händler, Fotografie und Content, Steuer- und Rechtsberatung für Onlinehändler.

Der Pfad **findet die Verkäufer selbst**. Eine Brand-Liste aus einem Analyse-Tool ist nicht nötig.

Sonderfall: Für **jede eigene Firmenliste** mit Firmenname lassen sich mit `anreicherung.mjs` Website, Geschäftsführung und Anrede recherchieren (nur DE/AT/CH, `ABLAUF.md` → „Sonderfall“).

## Voraussetzungen

| Was | Pflicht? | Wofür |
|---|---|---|
| **Node.js ab Version 18** | ja | führt die Skripte aus, sonst nichts zu installieren |
| **Oxylabs-Konto** (Web Scraper API) | ja | ruft alle Amazon-Seiten ab. Kein eigenes Amazon-Konto nötig |
| **Bright Data** (Token) | ja, wenn per E-Mail oder Telefon angesprochen wird | Kontaktdaten der fertigen Leads: E-Mail, Telefon, Handelsregister, USt-IdNr., vertretungsberechtigte Person |
| **Skael** (API-Schlüssel) | ja, wenn per E-Mail angeschrieben wird | prüft die Zustellbarkeit jeder E-Mail-Adresse (alle Länder); dazu Website, Impressum, Geschäftsführung, Anrede (nur Firmen in DE/AT/CH) |

Die Zugänge stehen in `pfade/amazon/.env`, eingetragen vom Nutzer selbst. Die KI prüft sie mit `--pruefen` (eine einzige Testabfrage).

## Ablauf

| Stufe | Was passiert | Kosten-Treiber |
|---|---|---|
| 1 Suche | Neuheiten-Listen von 28 amazon.de-Kategorien (optional Unterkategorien, Suchbegriffe) | 1 Abfrage je Listenseite |
| 2 Produktseite | Welcher Händler hat die Buy-Box? Amazon selbst ist nie ein Lead | 1 Abfrage je Produkt |
| 3 Verkäuferprofil | Firmenname, Adresse, **Land des Firmensitzes** | 1 Abfrage je Verkäufer |
| 4 Sortiment | Produktzahl, 12er-Stichprobe: Produktfamilien, Hauptmarke, Markenanteil, Umsatz | ~5–30 Abfragen je Verkäufer |
| 5 Endkontrolle | Hat der Händler die Buy-Box noch? | 1–2 je Lead |
| 6 Kontaktdaten | Bright Data, nur für fertige Leads | 1 Datensatz je Lead |
| 7 Export | Gesamtliste, Lauf-Datei, Bericht | – |
| 8 Anreicherung | Skael: E-Mail-Prüfung (alle Länder), Website, Impressum, Geschäftsführung, Anrede (DACH) | 3 Credits je Adresse, ~5–50 Credits je DACH-Lead |
| 9 Standardformat + Sperrliste | Pflichtfelder vorn, Abgleich mit der Community-Sperrliste | – |

Die Stufen 1–4 laufen in **Wellen**: Jede Stufe holt nur, was die nächste für das Lead-Ziel braucht, und misst die Durchlaufquoten dabei selbst. Ein Lauf bezahlt also nie zehntausende Produktseiten vor dem ersten Lead. Reicht das Budget nicht, kommen trotzdem die bis dahin gefundenen Leads heraus.

Alle Schritte sind **fortsetzbar**: Nach einem Abbruch setzt derselbe Befehl fort, ohne Bezahltes zu wiederholen. Ein **Gedächtnis** über alle Kampagnen merkt sich geprüfte Produkte und Fakten zu Verkäufern. Was einmal bezahlt wurde, kostet 90 Tage lang nicht noch einmal (`CACHE_TAGE`). In einer neuen Kampagne fallen je bekanntem Verkäufer nur wenige Abfragen an.

## Filter (ab Werk alle aus)

| Wunsch aus dem Interview | Filter |
|---|---|
| nur Firmen mit Sitz in DACH | `LAENDER=DE,AT,CH` |
| keine Konzerne / nur kleine Händler | `PORTFOLIO_MAX_BEWERTUNGEN`, `MAX_PRODUKTE` |
| Umsatz-Obergrenze (nur auf ausdrücklichen Wunsch) | `UMSATZ_MAX` |
| Händler mit eigener Marke | `MIN_MARKENANTEIL=0.7` |
| keine Verlage o. Ä. | `FIRMEN_AUSSCHLUSS=verlag,…` |
| nur bestimmte Produktbereiche | `KATEGORIEN=…` oder `KEYWORDS=…` |

Nach Umsatz wird ab Werk nicht gefiltert und nicht in Klassen eingeteilt. Fast jeder Händler bekommt eine Umsatzzahl. Die Spalte `Umsatzbasis` sagt, ob sie `gemessen`, `gemessen + geschätzt` oder `geschätzt` ist. Ohne Kauf- und Preisdaten bleibt sie leer (`nicht messbar`). Die Auswahl trifft der Nutzer in der fertigen Liste.

Filter wirken auch auf das Gedächtnis. Gespeichert werden Fakten, keine Urteile. Ein Verkäufer, der heute an einem Filter scheitert, kann in einer Kampagne mit anderen Filtern wieder dabei sein.

## Kosten und Mengen

| Kennzahl | Richtwert |
|---|---|
| Oxylabs | ~0,45 USD je 1.000 Abfragen |
| Abfragen je Lead **ohne Filter** | ~15–30, also 0,7–1,4 Cent je Lead |
| Abfragen je Lead mit `LAENDER=DE,AT,CH` | ~150–250, weil nur ~15 % der Verkäufer dort sitzen |
| Bright Data | ~1,50 USD je 1.000 Leads |
| Skael E-Mail-Prüfung | 3 Credits je Adresse, unabhängig vom Ergebnis |
| Skael Website und Geschäftsführung | ~5–50 Credits je DACH-Lead; mit Firmen-E-Mail günstig, ohne teuer |
| Smoke-Test | höchstens 300 Abfragen ≈ 0,15 USD |

**Budget-Regel:** ohne Filter BUDGET ≈ 30 × ZIEL. Nach dem Testlauf gilt der gemessene Wert: BUDGET ≈ ZIEL × `requests_je_lead` × 1,2. `BUDGET` ist eine harte Obergrenze, kein Verbrauchsziel.

**Herkunft der Verkäufer** (Messung an einer Stichprobe aus 8 Kategorien, ungefiltert): ~15 % DE/AT/CH, die große Mehrheit China und Hongkong. Ohne Länderfilter ist das normal und kein Fehler.

## Was realistisch herauskommt

| Feld | Quote | Hinweis |
|---|---|---|
| Firma, Adresse, Land | ~100 % | aus dem Verkäuferprofil (Pflichtangaben) |
| Sortiment, Umsatz | ~100 % geschätzt, gemessen nur bei Produkten mit „X+ gekauft“ | Spalte `Umsatzbasis` sagt, was gemessen ist |
| E-Mail, Telefon (Bright Data) | hoch bei DACH, gering bei CN/HK | Firmenadresse aus dem Verkäuferprofil, keine persönliche Adresse der Geschäftsführung |
| E-Mail Status (Skael) | für jede Adresse | `Safe to Send`, `Risky`, `Unknown`, `Invalid`; ohne Prüfung `Not Run` |
| Vertretungsberechtigte Person (Bright Data) | ~13–36 % | steht nicht als Feld im Profil, wird aus dem Text gelesen |
| Website (Skael, DACH) | Referenzlauf ~98 % | Firmen-E-Mail ist die stärkste Quelle |
| Impressum bestätigt (Skael, DACH) | ~76 % | Abgleich über Register, USt-IdNr., Firmenname, Telefon, E-Mail |
| Geschäftsführung (Skael, DACH) | ~67 % | aus dem bestätigten Impressum |
| persönliche Anrede | ~62 % | nur bei eindeutigem Vornamen, sonst „Guten Tag“ |

Quoten aus einem Referenzlauf mit ~1.100 DACH-Leads. Sie hängen stark von der Zielgruppe ab. Nach jedem Testlauf die eigenen Zahlen nennen.

## E-Mail-Prüfung

Jede Adresse wird vor der Ausgabe auf Zustellbarkeit geprüft (Skael, 3 Credits). Die Werte sind dieselben wie im Google-Maps-Pfad:

| Status | Bedeutung | Versand |
|---|---|---|
| `Safe to Send` | zustellbar | ja |
| `Risky` | Catch-all: der Server nimmt jede Adresse an | getrennt und vorsichtig |
| `Unknown` | nicht prüfbar | getrennt und vorsichtig |
| `Invalid` | ungültig | nie; die Adresse wird aus dem E-Mail-Feld entfernt |
| `Not Run` | nicht geprüft (kein Schlüssel, Störung, abgeschaltet) | nie per E-Mail |

Geprüft wird die Firmenadresse aus dem Amazon-Profil. Oft ist das eine Sammeladresse wie info@.

## Ansprache-Regeln

Wie für alle Pfade (`07_lead-ausgabe-und-spalten.md`): „Guten Tag Herr/Frau Nachname“ nur bei sicherem Namen **und** Geschlecht, sonst „Guten Tag“. Die Spalte `Match-Status` zeigt, ob die Website über das Impressum bestätigt ist (`register`, `ustid`, `firmenname`, `telefon`, `email`) oder nur vermutet (`domain`, `email-domain`).

## Grenzen

- **Nur amazon.de.** Andere Marktplätze haben andere Kategorie-Nummern.
- **Neuheiten-Fokus:** Die Suche läuft über die Neuheiten-Listen. Sie findet aktive Händler mit neuen Produkten bevorzugt, sehr große Händler fallen über die Größenfilter heraus, wenn gewünscht.
- **Kontakte außerhalb von DACH:** Ohne Impressumspflicht gibt es dort kaum Geschäftsführung und Website.
- **Keine Personalisierung:** Einen individuellen Einstiegssatz liefert dieser Pfad nicht.
- **Ungetestete Echtläufe:** Die überarbeitete Version wurde gegen einen Test-Server geprüft, der Skael-Teil zusätzlich gegen die veröffentlichte Schnittstellen-Beschreibung (api.skael.de/docs). Den ersten echten Lauf immer mit Smoke-Test und Testlauf beginnen.

## Risiken und Recht

- **Amazon-Nutzungsbedingungen:** Die Seiten werden über einen Scraping-Dienst (Oxylabs) abgerufen, nicht über ein eigenes Amazon-Konto. Es gibt daher keine Kontosperre. Die Nutzung muss trotzdem mit den Bedingungen von Amazon und der Dienste vereinbar sein.
- **Datenschutz:** Namen von Geschäftsführung und Einzelunternehmern sind personenbezogene Daten. Bei Ansprache gilt die Informationspflicht nach Art. 14 DSGVO (`08_versand-und-recht.md`). Lead-Daten liegen in `pfade/amazon/arbeit/`. Den Ordner nie weitergeben.
- **E-Mail-Werbung:** ohne Einwilligung grundsätzlich unzulässig (§ 7 UWG), auch an Firmen.
- **Sperrliste:** Abgeglichen werden E-Mail-Domain (auch die einer als ungültig aussortierten Adresse), Website und Impressum-URL. Verkäufer ohne all das lassen sich nicht abgleichen, das dem Nutzer sagen.
