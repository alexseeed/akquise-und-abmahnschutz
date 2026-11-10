# Videoseiten – persönliches Video und eigene Landingpage je Lead

**Zweck:** Wissen zum Pfad `pfade/videoseiten/`: was entsteht, was es kostet, was der Nutzer selbst tun muss, wie die Vorlage aufgebaut ist und was rechtlich zu beachten ist.
**Für wen:** Nutzer mit Rückfragen und KI-Modelle, die den Ablauf (`pfade/videoseiten/ABLAUF.md`) begleiten.
**Verwandt:** `02_zielgruppen-interview.md` (Blöcke V und L) · `07_lead-ausgabe-und-spalten.md` (Lead-Format) · `08_versand-und-recht.md` · `11_zugaenge-und-kosten.md`

---

## Was entsteht

Für jeden Lead mit Website:

1. ein **persönliches Video** bei Skael: das Grundvideo des Nutzers, in dem die Website des Leads eingeblendet wird,
2. eine **eigene Seite** unter `https://angebot.<domain-des-nutzers>/v/<zufällige-kennung>/` im Branding des Nutzers: persönliche Überschrift, Video, Angebot, Kundenstimmen, Fragen, Termin-Knopf, Datenschutz-Information,
3. eine **Versandliste** mit dem Link zur Seite und einem Vorschaubild für die Mail.

Die Seite ist bis zum Klick auf Abspielen gesperrt: Man sieht nur Überschrift, Unterschrift, Video und die Rechtslinks. Nach dem Klick zoomt das Video groß, danach baut sich der Rest beim Scrollen auf. „Ohne Video weiterlesen“ öffnet die Seite, ohne das Video zu laden.

## Wer macht was

| Schritt | Agent | Nutzer |
|---|---|---|
| Branding, Impressum, Texte | liest die Website, schlägt vor, baut die Seite | bestätigt, liefert Foto und Termin-Link |
| Grundvideo | prüft die Kampagne (Aufnahme, Länge, Screenshot-Teil) | nimmt das Video in Skael auf (`anleitungen/01_…`) |
| Videos je Lead | legt an, wartet, führt zusammen | sagt Ja zu den Kosten, sieht das Testvideo an |
| Server | richtet alles per Hostinger-API ein | kauft den VPS, erzeugt den API-Schlüssel (`anleitungen/02_…`) |
| Domain | setzt den Eintrag, wenn die Domain bei Hostinger liegt | sonst den A-Record beim eigenen Anbieter (`anleitungen/03_dns.md`) |
| Versand | erstellt die Liste mit Links | importiert ins Mailtool (`anleitungen/06_mailtool.md`), passt die Datenschutzerklärung an (`anleitungen/05_…`) |

## Kosten

| Posten | Preis | Quelle |
|---|---|---|
| Video bis 2 Minuten | 110 Credits = 0,11 € | Skael-Doku „Create Prospect“ |
| je weitere angefangene Minute | 55 Credits | dto. |
| Staffel nach Videos der letzten 60 Tage | ab 1.000: 80 · 2.000: 70 · 4.000: 65 · 10.000: 55 · 14.000: 40 Credits | dto. |
| fehlgeschlagene Videos | werden erstattet | dto. |
| Hostinger VPS KVM 1 | ab 5,49 €/Monat im Aktionszeitraum, Verlängerung 11,99 €/Monat (Stand 2026-10) | hostinger.com |

Beispiel: 500 Leads mit einem 1:50-Minuten-Video = 55.000 Credits = 55 €. Mit 2:16 Minuten wären es 82,50 €.

## Vorlage

`pfade/videoseiten/vorlage/index.html`. Der Agent arbeitet immer auf einer Kopie in `arbeit/<kampagne>/seite/`.

| Teil | Wer füllt | Inhalt |
|---|---|---|
| `LEAD` (zwischen `/* LEAD:START */` und `/* LEAD:END */`) | Generator, je Lead | Lead-Format, `seiten_id`, `video_url`, `video_vorschaubild`, `video_titel` |
| `ABSENDER` | Agent, einmal | Name, Logo, Rechtsträger, Anschrift, Ansprechpartner, Rolle, Foto, Impressum-, Datenschutz-, Termin-Link, Termindauer, E-Mail für Datenlöschung |
| `SEITE` | Agent, einmal | `design` (Farben, Rundung), `bausteine`, `start_sperre`, `texte` |
| Gerüst (HTML/CSS) | niemand | fest; nur `branding.py anwenden` ersetzt Schriften und Farben |

**Bausteine:** Pflicht sind `begruessung`, `video`, `termin`, `herkunft`. Wählbar: `angebot` (Paket-Karte mit Leistungen, Inklusive-Liste, Ablauf), `stimmen` (Kundenstimmen, erste groß; je Stimme optional `bild`, `video_vorschaubild`, `video_etikett` (Standard „Video-Interview“) und entweder `video_url` (externer Player, https) oder `video_datei` (eigene mp4/webm unter `assets/`, liegt auf dem eigenen Server; `zitat` darf fehlen, dann zeigt die Karte nur Name, Rolle und Ergebnis)), `ansprechpartner`, `fragen`. Reihenfolge = Reihenfolge in `SEITE.bausteine`.

**Texte:**
- In Texten setzt `{feld}` Werte aus `LEAD`, `ABSENDER` oder `SEITE` ein; `{ansprache}` ergibt „Guten Tag Frau Nachname“ bzw. „Guten Tag“.
- Überschrift: spricht die Person an und sagt, was das Video zeigt. Muster: „{ansprache}, ich habe Ihnen ein persönliches Video aufgenommen, wie Sie …“.
- `einleitung: ""` lässt die Einleitung weg; dann folgt die Unterschrift (Foto, Name, Rolle) direkt auf die Überschrift.
- Nur Belegbares. Zahlen, Kunden, Zitate ausschließlich vom Nutzer. Fehlt etwas, bleibt `<Platzhalter>` stehen; der Generator veröffentlicht dann nicht.
- Kundenstimmen nur mit Zustimmung der Kunden, auch für diese Seiten. Ohne Stimmen `stimmen` aus `bausteine` streichen.

**Du-Fassung:** Duzt der Nutzer seine Kunden, alle Texte in `SEITE.texte` umstellen und zusätzlich die festen Texte der Vorlage: Überschrift „Woher wir Ihre Daten haben“, die Quelle („insbesondere das Impressum der …“), der Video-Satz in „Video“, der Hinweis unter dem Video („laden Sie das Video …“), der Datenlöschungs-Dialog, die Bestätigung „Ihre Daten werden gelöscht“, „Ihr Paket“, der Mail-Text der Datenlöschung, `noscript`. Danach prüfen: `grep -nE "\b(Sie|Ihr|Ihre|Ihnen|Ihren|Ihrem|Ihrer)\b" arbeit/<k>/seite/index.html` darf außerhalb von `<style>` nichts mehr finden.

**Branding:** `branding.py` liest Farben, Schriften und Logo von der Website, lädt die Schriften als Dateien herunter (nie per Link einbinden) und schreibt sie in die Kopie. Vor dem Klick lädt die Seite nichts von Dritten.

## Datenschutz und Recht (Kurzfassung)

- **An Skael** gehen nur Vorname, Firma, Domain, Website und die interne Kennung. Skael zeigt alles Übergebene ohne Anmeldung auf der Videoseite an, deshalb nie E-Mail oder Telefon.
- **Link-Kennung:** 22 zufällige Zeichen, nicht der Skael-Token, nie Name oder Firma in der Adresse.
- **Datenschutz-Information nach Art. 14 DSGVO** steht auf jeder Seite: Verantwortlicher, Daten, Quelle, Zweck, Speicherdauer. Die Quelle ist bewusst allgemein gehalten („Impressum … sowie weitere öffentlich zugängliche Quellen“, dazu `erfasst_am`). `quelle` und `quelle_url` aus dem Lead-Format bleiben intern als Nachweis und landen nie auf der Seite. Die Rechte stehen nur in der Datenschutzerklärung, nicht auf der Seite, und die Seite nennt keine IP-Übertragung (beides steht in der Datenschutzerklärung).
- **„Keine weiteren Nachrichten – Datenlöschung vornehmen“:** löscht die Seite sofort und meldet die Kennung an den Server. Der Nutzer sperrt die Adresse im Mailtool und im Scraper (`ABLAUF.md`, Teil F).
- **Datenschutzerklärung des Nutzers** muss die Videoseiten, Skael und den Server nennen (`anleitungen/05_datenschutzerklaerung.md`).
- Werbe-Mails ohne Einwilligung bleiben nach § 7 Abs. 2 Nr. 2 UWG riskant (`08_versand-und-recht.md`). Die Seite senkt Angriffsflächen, ersetzt aber keine Rechtsberatung.
