# Pfad „Recruiting“ – Firmen, die gerade Personal suchen (über die Firmen-Website)

**Zweck:** was der Pfad tut, was er voraussetzt, was herauskommt und wo seine Grenzen liegen.
**Für wen:** Nutzer und KI-Modelle, die einen Recruiting-Lauf planen oder Ergebnisse verstehen wollen.
**Verwandt:** `02_zielgruppen-interview.md` · `03_pfad-google-maps.md` · `18_pfad-stellensuche.md` · `07_lead-ausgabe-und-spalten.md` · `08_versand-und-recht.md` · `11_zugaenge-und-kosten.md`
**Technik im Detail:**

- Anleitung für die KI: `pfade/recruiting/ABLAUF.md`
- Stufen, Datenfelder, Abweichungen: `pfade/google-maps/docs/07_RECRUITING.md`
- Prompts: `pfade/google-maps/prompts/stellenanalyse.txt`, `jobtitel_normalisierung.txt`, `personalisierung_stellenanzeige.txt`, `personalisierung_website.txt`; branchengenaue Fassungen in `pfade/google-maps/prompts/beispiele/`

**Stand:** 2026-11-01 · **Prüfen bis:** 2027-02-01. Nachbau eines Clay-Workbooks (Herkunft: `pfade/recruiting/referenzen/clay-vorlage.md`), läuft lokal. Offline getestet, noch ohne gemessene Quoten.

---

## Stand und Entscheidung

**Verfügbar.** Läuft im Scraper-Programm `pfade/google-maps/` – demselben Programm wie der Google-Maps-Pfad, als eigene Kampagnen-Art (`init --pfad recruiting`) in einer eigenen Kampagne.

„Recruiting“ kann zweierlei bedeuten. Entschieden ist **Variante A**:

| Variante | Wer ist der Lead? | Beispiel-Angebot | Einordnung |
|---|---|---|---|
| **A – Firmen, die gerade einstellen** (gebaut) | das Unternehmen; angesprochen wird die Geschäftsführung | Personaldienstleister, Recruiting-Agentur, Employer-Branding, HR-Software | B2B; die üblichen Regeln für Kaltakquise gelten (`08`) |
| **B – Kandidaten** (nicht gebaut) | Privatpersonen bzw. Fachkräfte | Active Sourcing für eigene Stellen | Personendaten von Privatpersonen, strengere DSGVO-Anforderungen, Nutzungsbedingungen der Plattformen verbieten Scraping meist. **Deutlich höheres Risiko** |

Es gibt **zwei Wege** zu Variante A:

| | Recruiting (dieser Pfad) | Stellensuche (`18_pfad-stellensuche.md`) |
|---|---|---|
| Ausgangspunkt | Branche + Region → Firmen bei Google Maps | Beruf + Orte → Anzeigen in Jobportalen |
| findet | Firmen, die auf der **eigenen Website** ausschreiben | Firmen, die **über Portale** ausschreiben |
| passt, wenn | die Branche der Wunschkunden bekannt ist | der gesuchte Beruf bekannt ist |

Beide ergänzen sich: Kleine Betriebe schreiben oft nur auf der eigenen Website aus, größere fast immer über Portale.

## Wann dieser Pfad

- Wunschkunde ist erkennbar daran, dass er **gerade einstellt** (Block C, Antwort 4 im Interview), und die **Branche** ist bekannt („Speditionen in Ulm, die einstellen“).
- Die Ansprache soll an die **Stelle** anknüpfen: „ich habe gesehen, dass Sie gerade jemanden als Berufskraftfahrer suchen, der den Führerschein Klasse CE und eine Fahrerkarte mitbringt.“

Nicht geeignet für Kandidaten-Suche (Variante B).

Ist auch der **Beruf** bekannt, kommt ebenso die Stellensuche über Jobportale in Frage (`18_pfad-stellensuche.md`). Welcher Weg besser liefert, zeigt der **Testballon**. Er fährt beide Wege mit je ~100 Leads und vergleicht Kosten, Qualität und Marktgröße (`pfade/google-maps/docs/09_TESTBALLON.md`). Gibt es zu wenige Firmen mit Stelle, schaltet er die NK-Strecke zu (nur mit Prüfprofil) und nimmt kleinere Städte auf.

## Ablauf

```
Branche + Region + gesuchte Berufe
  → Städte → Maps-Suche → Firmen
  → Dedupe über die Domain
  → Prüfung gegen das Wunschkundenprofil
  → Stellen-Erkennung: Startseite + bis zu 2 Karriere-Seiten der Firmen-Website lesen
       ├─ Stelle gefunden ─► RC: Impressum, GF, E-Mail, Anrede, Jobtitel normalisieren, Opener zur Stelle
       └─ keine Stelle ────► NK (nur mit --nk): Satz zur Website;  sonst Liste 4
  → Export (5 Listen, Sperrliste eingebaut)
```

Einzige Quelle für offene Stellen ist hier die **Website der Firma**. Stellen aus Jobportalen (Indeed, Stepstone, Arbeitsagentur, Kununu) holt der Pfad **Stellensuche** (`18_pfad-stellensuche.md`).

| Schritt | Was passiert | Dienst |
|---|---|---|
| Städte, Maps-Suche, Dedupe | wie Google-Maps-Pfad, Stufe 1–3b | Skael |
| Prüfprofil | Website gegen Wunschkunden (ja/nein, Sicherheit, Begründung) | Skael `icp_checker` |
| **Stellen-Erkennung (3e)** | Startseite abrufen, Links zu Karriere/Jobs/Stellenangebote der eigenen Domain finden, bis zu 2 davon abrufen; KI gibt **genau eine** Stelle zu den gesuchten Berufen zurück: Bezeichnung, Bereich, Kurzbeschreibung | Skael `web_scraper`, KI |
| Anreicherung | Impressum, GF, E-Mail-Wasserfall, Anrede – identisch mit Google Maps Stufe 4 | Skael, Findymail, KI |
| **Opener** | Jobtitel normalisieren, dann ein Satz: „ich habe gesehen, dass Sie gerade jemanden als [Rolle] suchen, der [1–2 echte Anforderungen] mitbringt.“ Ohne echte Anforderungen endet der Satz nach „suchen.“ – keine Floskeln | KI |
| Versandfertig | E-Mail **und** Jobtitel **und** Opener (RC) bzw. E-Mail und Satz zur Website (NK) | – |

Die KI läuft standardmäßig über Skael (`LLM_PROVIDER=skael`), wahlweise über OpenAI.

## Was die Prompts können müssen

Die Standard-Prompts sind **branchenneutral**. Die gesuchten Berufe kommen je Kampagne aus `init --berufe "A,B,C"` (Reihenfolge = Priorität) in den Stellen-Prompt. Anzupassen ist meist nur:

1. **Prüfprofil** – wie im Google-Maps-Pfad (`icp.txt` der Kampagne), Bauanleitung `pfade/google-maps/prompts/icp_prompt_builder.md`, Beispiel `prompts/beispiele/icp_logistik.txt`.
2. Optional **branchengenaue Fassungen** von Stellen-Prompt (`pfade/google-maps/prompts/beispiele/stellenanalyse_logistik.txt`: feste Berufsliste, Ausschlüsse, Priorität) und Opener (`pfade/google-maps/prompts/beispiele/personalisierung_stellenanzeige_logistik.txt`, `…_ki.txt`). Dazu die Datei unter dem Standardnamen in `kampagnen/<name>/prompts/` kopieren; das Programm sucht dort zuerst.

## Befehle (Kurzfassung)

```bash
./scraper.sh neue-kampagne <k>
./scraper.sh --kampagne <k> init --pfad recruiting --keywords "Spedition" --countries DE \
        --min-population 200000 --berufe "Berufskraftfahrer,Disponent" [--nk]
./scraper.sh --kampagne <k> run --stage all
./scraper.sh --kampagne <k> export
```

Vollständig mit Testlauf und Stichprobe: `pfade/recruiting/ABLAUF.md`.

## Kosten – wovon sie abhängen

```
Kosten ≈ (Keywords × Städte) × Maps-Suche
           + gefundene Firmen × Prüfung
           + passende Firmen × (1–3 Website-Abrufe + 1 KI-Aufruf)       ← Stellen-Erkennung
           + Firmen mit Stelle × (Impressum + E-Mail-Suche/-Prüfung + 3 KI-Aufrufe)
```

- Die Stellen-Erkennung läuft für **jede passende Firma**, auch für die ohne Stelle. Ein strenges Prüfprofil spart hier am meisten.
- Hebel wie im Google-Maps-Pfad: Mindest-Ortsgröße, Anzahl Suchbegriffe.
- Bezahlte Startseiten werden gespeichert und für die NK-Strecke wiederverwendet.
- `status` zeigt nach jedem Lauf die echten Skael-Kosten („Skael-Kosten bisher“, Kostenzähler, `11_zugaenge-und-kosten.md`).

## Quoten

Noch nicht gemessen. Nach dem ersten echten Testlauf hier eintragen:

| Kennzahl | Wert | Lauf |
|---|---|---|
| Firmen mit Website, die zum Profil passen | – | – |
| davon mit erkannter Stelle | – | – |
| davon mit E-Mail | – | – |
| versandfertig | – | – |
| Opener mit Fehler in der Stichprobe | – | – |

Erwartung (ungeprüft): Die Stellen-Quote hängt stark von der Branche ab. Handwerk und Logistik schreiben häufig auf der eigenen Website aus, Konzerne über Bewerberportale, die der Pfad nicht liest.

## Grenzen

- **Eine Stelle je Firma.** Bei mehreren passenden Stellen wählt die KI nach der Reihenfolge der gesuchten Berufe eine aus.
- **Stellen-Erkennung liest nur die eigene Website** (Startseite + bis zu 2 Karriere-Seiten, `KARRIERE_SEITEN`). Stellen, die nur auf externen Bewerberportalen oder Jobbörsen stehen, findet dieser Pfad nicht – dafür gibt es den Pfad Stellensuche.
- **Alter der Stelle** wird nicht erfasst. Die Zahl offener Stellen auch nicht; beides liefert nur die Stellensuche.
- **Nur der erste Geschäftsführer** aus dem Impressum; die Personalabteilung wird nicht gesucht.
- **Anrede:** Der Anrede-Prompt setzt bei unsicheren Vornamen „Herr“. Die Exportspalte `Ansprache` ist deshalb nur bei Anrede-Sicherheit > 60 persönlich, sonst neutral.

## Rechtliches in Kürze

- **Datenquellen:** öffentliche Unternehmens-Websites und Google Maps (über Skael). Jobportale nutzt dieser Pfad nicht; die Stellensuche bezieht sie über die Skael-Schnittstelle (Einordnung in `18_pfad-stellensuche.md`).
- **Personenbezug:** Namen der Geschäftsführung und persönliche E-Mail-Adressen sind personenbezogen (DSGVO). Kontaktpersonen aus Stellenangeboten werden **nicht** übernommen.
- **Ansprache:** E-Mail-Werbung ohne Einwilligung bleibt unzulässig (§ 7 Abs. 2 Nr. 2 UWG). Der Bezug auf eine öffentliche Stellenanzeige ändert daran nichts. Den Aufhänger nicht fingieren: nur Stellen nennen, die wirklich ausgeschrieben sind (Stichprobe!), Listen nicht wochenlang liegen lassen.

Mehr in `08_versand-und-recht.md`.
