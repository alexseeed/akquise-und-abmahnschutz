# Anleitung 1: Videokampagne in Skael anlegen und Grundvideo aufnehmen

> **Für den Agenten:** Lies diese Anleitung dem Nutzer Schritt für Schritt vor und warte nach jedem Schritt auf seine Rückmeldung.
>
> **Ehrlichkeitshinweis:** Die Skael-Weboberfläche ist nur mit Login sichtbar. Belegt sind nur die Menünamen **SkaelReach** und **Kampagnen** (aus den Oberflächentexten im Quelltext der Skael-Doku), die Login-Adresse und die Seitenadressen aus der Webhook-Doku. **Alle anderen Klicks in Skael sind als „ungeprüft“ markiert.** Wenn der Nutzer etwas anderes sieht, lass ihn vorlesen, was auf dem Bildschirm steht, und richte dich danach. Die Fragen am Ende gehen an den Skael-Support.
>
> Was du selbst prüfen kannst: Mit dem `SKAEL_API_KEY` liefert `GET https://api.skael.de/api/video-campaigns/{id}` die Kampagne mit allen Einstellungen (laut Webhook-Doku inklusive `webhook_secret` und `webhooks`). In der API-Antwort stehen außerdem `recording_path`, `timeline`, `settings.screenshot.mode` / `settings.screenshot.duration`, `facecam`, `ai_voice`, `custom_domain_id`, `delivery_mode` und `webhooks`. Diese Felder sind in der öffentlichen Doku nicht beschrieben; was ihre Werte bedeuten, ist *ungeprüft*.

Alle Quellen wurden am **25.10.2026** abgerufen (Liste am Ende).

---

## Worum geht es?

Du nimmst **ein einziges Video** auf, das **Grundvideo**. Skael macht daraus für jeden Lead (jeden möglichen Kunden auf deiner Liste) ein eigenes Video.

Das Persönliche daran: Skael macht von der **Website des Leads** einen Screenshot (ein Bildschirmfoto der Seite) und blendet ihn in dein Video ein. Laut Skael-Doku erzeugt jeder neue Lead „einen personalisierten Screenshot“, eine Vorschau und eine eigene Seiten-Adresse ([Create Prospect](https://api.skael.de/docs/skaelreach/prospects/create)). Bis zu drei Screenshots je Video sind möglich.

Der Lead sieht also: dich, und an der passenden Stelle seine eigene Website.

### Das Wichtigste vorab

**Dein Video muss einen Screenshot-Teil enthalten.** Den Ablauf deines Videos legst du in Skael fest. Dort steht, wann deine Aufnahme läuft und wann die Website des Leads erscheint. In der API heißt das **Timeline**.

Fehlt dort der Screenshot-Teil, bekommt **jeder Lead genau dasselbe Video**. Das ist uns in einer echten Kampagne passiert. Deshalb prüft der Agent das in Schritt 7, bevor ein einziger echter Lead ein Video bekommt.

### Was es kostet

Laut Skael-Doku ([Create Prospect, Abschnitt „Pricing“](https://api.skael.de/docs/skaelreach/prospects/create)):

| Länge des fertigen Videos | Credits je Video | in Euro |
|---|---|---|
| bis 2:00 Minuten | 110 | 0,11 € |
| 2:01 bis 3:00 | 165 (110 + 55) | 0,165 € |
| 3:01 bis 4:00 | 220 (110 + 2 × 55) | 0,22 € |

- Jede weitere **angefangene** Minute über 2:00 kostet 55 Credits. Schon 2:01 kostet also 165.
- 1.000 Credits sind 1 € ([Skael-Leitfaden](https://api.skael.de/docs/mcp-leitfaden)).
- Ab 1.000 Videos in 60 Tagen wird es günstiger (dann 80 Credits bis 2 Minuten, weitere Stufen in der Doku).
- Die Credits werden beim Anlegen reserviert. Schlägt das Video oder der Screenshot fehl, bekommst du sie zurück.
- Zusätzliche Screenshot-Teile zählen mit ihrer Zeit zum Preis. Rechne deshalb immer mit der **Länge des fertigen Videos**, nicht nur mit deiner Aufnahme.

**Beispiel:** 500 Leads mit 1:45 Minuten kosten 500 × 0,11 € = 55 €. Mit 2:10 Minuten wären es 82,50 €.

**Empfehlung:** Bleib unter 2 Minuten. 60 bis 90 Sekunden sind ideal.

---

## Schritt 1: Skript schreiben (bevor du Skael öffnest)

Schreib auf, was du sagen willst. Lies es einmal laut mit Stoppuhr vor. Über 1:45? Kürzen.

**Fünf Regeln:**

1. **Keine Namen, keine Firmennamen.** Du nimmst einmal auf, das Video geht an Hunderte. Sag „Hallo“ statt „Hallo Herr Müller“. Den Namen kann Skael nur über eine **KI-Stimme** einsprechen lassen (in der API: `ai_voice`; die Doku nennt „Variablenwerte, die in das KI-Stimmen-Skript eingesetzt werden“). Ob der Name auch als Untertitel eingeblendet werden kann, ist *ungeprüft*.
2. **Nur Sätze, die für jede Website stimmen.** Sag nicht „Ihr blaues Logo“. Sag „Ich habe mir Ihre Website angesehen“.
3. **Auf die Website zeigen, wenn sie erscheint.** Sprich genau dann über „Ihre Seite“, wenn im Ablauf der Screenshot kommt. Plane die Stelle im Skript ein und merk dir die Sekunde.
4. **Ein Gedanke, ein Angebot.** Lieber eine klare Sache als drei halbe.
5. **Klarer Schluss.** Sag, was der Lead jetzt tun soll: „Direkt unter diesem Video können Sie sich einen Termin aussuchen.“ Die Termin-Buchung steht auf der Angebotsseite unter dem Video.

**Vorlage (ca. 75 Sekunden):**

| Zeit | Was im Bild ist | Was du sagst (Beispiel) |
|---|---|---|
| 0:00–0:10 | Du | „Hallo, schön, dass Sie reinschauen. Ich bin [dein Vorname] von [deine Agentur].“ |
| 0:10–0:40 | **Screenshot der Lead-Website** | „Ich habe mir Ihre Website angesehen. Mir ist aufgefallen, dass … [Punkt, der auf fast alle Websites deiner Zielgruppe zutrifft].“ |
| 0:40–1:05 | Du | „Wir helfen [Zielgruppe] dabei, [Ergebnis]. Zum Beispiel haben wir für … [ein kurzes Beispiel].“ |
| 1:05–1:15 | Du | „Wenn Sie das interessiert: Direkt unter diesem Video können Sie sich einen Termin aussuchen. Ich freue mich.“ |

**Was du dem Agenten meldest:** „Skript fertig, gemessene Länge: __ Sekunden.“ Der Agent kann dir beim Kürzen helfen.

---

## Schritt 2: Bei Skael einloggen

1. Öffne im Browser **https://api.skael.de/login** und melde dich an. *(Belegt: Die Adresse ist die Login-Seite von Skael; geschützte Skael-Seiten leiten dorthin um.)*
2. Im Menü findest du **SkaelReach** und darunter **Kampagnen**. *(Belegt: Diese Menünamen stehen in den Oberflächentexten von Skael. Wo genau sie auf dem Bildschirm stehen, ist ungeprüft.)*

**Was du dem Agenten meldest:** „Eingeloggt, ich sehe die Kampagnen.“

---

## Schritt 3: Neue Kampagne anlegen

*Ungeprüft, bitte mit Skael-Support abgleichen.*

1. In **Kampagnen** einen Knopf zum Anlegen suchen (vermutlich „Neue Kampagne“ oder ein Plus-Zeichen).
2. Einen Namen vergeben, an dem du die Kampagne später erkennst, z. B. `Steuerberater Bayern 2026-11`.
3. **Farbe des Players:** In den Einstellungen der Kampagne (Bereich Darstellung bzw. Aussehen) die Hauptfarbe von Skael-Lila auf deine Markenfarbe ändern. Sonst hat der Play-Knopf im Video eine fremde Farbe. Die Farbe nennt dir der Agent (sie steht in deinem Branding, z. B. `#1A7F5A`).
4. Speichern.

**Was du danach siehst:** Die Einstellungsseite der Kampagne. Laut Webhook-Doku hat sie die Adresse `/skaelreach/campaigns/{Nummer}`. Die Nummer am Ende ist die **Kampagnen-ID**.

**Was du dem Agenten meldest:** „Kampagne angelegt. Die Adresse oben im Browser lautet …“ (einfach die Adresszeile vorlesen oder kopieren). Der Agent braucht die Nummer.

---

## Schritt 4: Grundvideo aufnehmen

*Ungeprüft, bitte mit Skael-Support abgleichen.* Ob Skael im Browser aufnimmt, eine Datei zum Hochladen annimmt oder beides, steht nicht in der öffentlichen Doku. In der API gibt es dafür ein Feld `recording_path` (der Speicherort deiner Aufnahme) und ein Feld `facecam` (vermutlich die Einblendung deines Gesichts; *ungeprüft*).

Allgemeine Tipps, egal wie aufgenommen wird:

1. **Ruhiger Raum**, Tür zu, Handy stumm.
2. **Licht von vorne** (Fenster oder Lampe hinter der Kamera, nicht hinter dir).
3. **In die Kamera schauen**, nicht auf den Bildschirm.
4. Wenn der Browser fragt, ob Skael **Kamera und Mikrofon** benutzen darf: **Erlauben** klicken.
5. Skript neben die Kamera legen, nicht ablesen wie ein Nachrichtensprecher. Versprecher sind okay, das wirkt echt.
6. An der Stelle, an der später der Screenshot kommt, einfach weitersprechen. Das Bild der Website legt Skael darüber (*ungeprüft, wie genau das aussieht: Schau dir das Testvideo in Schritt 7 an*).

**Was du dem Agenten meldest:** „Aufnahme gespeichert, Länge: __.“

---

## Schritt 5: Ablauf (Timeline) mit Screenshot-Teil festlegen

*Ungeprüft, bitte mit Skael-Support abgleichen.*

1. In der Kampagne den Bereich suchen, in dem du den Ablauf des Videos festlegst.
2. **Einen Screenshot-Teil einfügen** an der Stelle aus deinem Skript (in der Vorlage ab 0:10).
3. Die Dauer des Screenshot-Teils einstellen (in der API: `settings.screenshot.duration`). Es gibt außerdem eine Einstellung `settings.screenshot.mode`; welche Möglichkeiten es dort gibt (z. B. stehendes Bild oder Scrollen über die Seite), ist *ungeprüft*.
4. Speichern.

**Was du dem Agenten meldest:** „Ablauf gespeichert, Screenshot ab Sekunde __ für __ Sekunden.“

---

## Schritt 6 (optional): KI-Stimme für den Namen

*Ungeprüft, bitte mit Skael-Support abgleichen.*

Wenn du willst, dass das Video den Namen oder die Firma des Leads ausspricht, braucht die Kampagne ein **KI-Stimmen-Stück** (in der API: `ai_voice`). Die Doku bestätigt nur, dass es so ein Stück geben kann und dass Variablen in dessen Text eingesetzt werden. Wie man es einrichtet und ob es extra kostet, steht dort nicht.

Wenn du unsicher bist: weglassen. Ein Video ohne Namen, aber mit der eigenen Website des Leads, wirkt schon persönlich.

**Was du dem Agenten meldest:** „KI-Stimme: ja / nein.“

---

## Schritt 7: Prüfen, bevor echte Leads ein Video bekommen (macht der Agent)

> **Agent:**
> 1. Hol die Kampagne über `GET /api/video-campaigns/{id}`. Prüfe: `recording_path` ist gesetzt, und `timeline` enthält einen Screenshot-Teil. Fehlt der Screenshot-Teil: **Stopp.** Zurück zu Schritt 5. Keine Leads anlegen.
> 2. Frag den Nutzer, ob du **zwei Testvideos** anlegen darfst (Kosten: 2 × 110 Credits = 0,22 €). Leg sie mit zwei **verschiedenen** Websites an, z. B. der Website des Nutzers und einer zweiten, über `POST /api/video-campaigns/{id}/prospects` mit `screenshot_url`. Die Doku warnt: Jeder Aufruf legt einen echten Lead an und reserviert Credits.
> 3. Wenn beide fertig sind (`status: ready`), gib dem Nutzer beide `landing_page_url`.

**Was du tust:** Beide Testvideos ansehen.

**Was du dem Agenten meldest:**
- „In Video 1 sehe ich Website A, in Video 2 Website B.“ → alles gut.
- „Beide Videos sind gleich“ oder „Ich sehe gar keine Website“ → der Screenshot-Teil fehlt. Zurück zu Schritt 5.
- „Der Screenshot erscheint an der falschen Stelle“ → Ablauf in Schritt 5 anpassen und neu testen.
- Gesamtlänge ansagen. Über 2:00? Kürzen (siehe Kosten).

---

## Schritt 8 (optional): Eigene Video-Domain

Ohne eigene Domain laufen die Videos unter einer Skael-Adresse. Mit eigener Domain stehen sie z. B. unter `video.deine-firma.de`. Laut Skael-Doku wird die eigene Domain **an der Kampagne** eingestellt und ersetzt dann die Standard-Adresse in allen Lead-Links ([Embed Guide, Abschnitt „Custom Domains“](https://api.skael.de/docs/skaelreach/embed-guide)). Die Doku verweist auf eine „Domain-Einrichtungsseite in den Kampagnen-Einstellungen“.

Du kannst diesen Schritt überspringen. Die Videos funktionieren auch ohne.

1. In den Kampagnen-Einstellungen die Domain-Einrichtung öffnen und `video.deine-firma.de` eintragen. *(Ungeprüft, bitte mit Skael-Support abgleichen.)*
2. Bei deinem Domain-Anbieter einen neuen DNS-Eintrag anlegen. Das geht genau wie in **Anleitung 3 (DNS)**, nur mit anderen Werten:

   | Feld | Wert |
   |---|---|
   | Typ | **CNAME** (ein Eintrag, der auf einen anderen Namen zeigt statt auf eine IP-Adresse) |
   | Name / Host | `video` |
   | Wert / Ziel | `cname.skael.de` |
   | TTL | nichts ändern |

   Der Zielwert `cname.skael.de` stammt aus der Antwort der Skael-API zur eigenen Domain; in der öffentlichen Doku steht er nicht. Zeigt Skael dir bei der Domain-Einrichtung einen anderen Wert an, nimm den von Skael.
3. Bei Cloudflare: Die Wolke grau lassen („DNS only“), wie in Anleitung 3. *(Ungeprüft für Skael, siehe Fragen an den Support.)*
4. Zurück in Skael die Domain prüfen lassen, falls es dafür einen Knopf gibt. *(Ungeprüft.)*

**Was du dem Agenten meldest:** „Video-Domain eingetragen, CNAME angelegt.“

> **Agent:** Prüfe mit `dig +short CNAME video.deine-firma.de` (Ergebnis: `cname.skael.de.`). Die Angebotsseiten übernehmen die Video-Adresse automatisch aus der `video_url` jedes Leads; der Generator setzt sie in die Sicherheitsregel der Seite ein (`frame-src`).

---

## Schritt 9: Webhook einrichten (Meldungen, wer das Video ansieht)

Ein **Webhook** ist eine automatische Nachricht: Skael meldet deinem Server, wenn jemand das Video startet oder zu Ende sieht. So weißt du später, welcher Lead wirklich zugeschaut hat.

**Erst machen, wenn deine Angebotsseiten-Domain läuft** (DNS aus Anleitung 3 ist angekommen und der Server ist eingerichtet). Der Agent sagt dir, wann es so weit ist.

Belegt aus der [Webhook-Doku](https://api.skael.de/docs/skaelreach/webhooks): Der Kampagnen-Webhook wird auf der Bearbeitungsseite der Kampagne (`/skaelreach/campaigns/{Nummer}`) eingestellt. Die genauen Knopfnamen dort sind *ungeprüft*.

1. Die Kampagne öffnen und den Bereich **Webhooks** suchen. *(Ungeprüft.)*
2. Als Adresse eintragen: `https://angebot.deine-firma.de/webhook/skael` *(der Agent sagt dir die genaue Adresse)*.
3. Diese fünf Ereignisse auswählen:
   - `video.started` (Video gestartet)
   - `video.progress.25` (ein Viertel gesehen)
   - `video.progress.50` (die Hälfte gesehen)
   - `video.progress.75` (drei Viertel gesehen)
   - `video.finished` (bis zum Ende gesehen)
4. Die Einstellung „höchstens einmal je Lead melden“ (in der Doku: `is_unique`) so lassen, wie sie ist. Laut Doku ist sie bei neuen Webhooks eingeschaltet. Wie der Schalter in der Oberfläche heißt, ist *ungeprüft*.
5. Speichern.

**Das Geheimnis (Secret):** Skael unterschreibt jede Meldung mit einem geheimen Schlüssel, damit dein Server echte Meldungen von gefälschten unterscheiden kann. Laut Doku wird es beim ersten Speichern eines Webhooks automatisch erzeugt. **Du musst es nicht abschreiben.** Der Agent holt es sich über die API und trägt es in die Server-Einstellungen ein.

**Was du dem Agenten meldest:** „Webhook gespeichert.“

**Zwei Dinge nicht tun:**
- **Nicht zusätzlich** denselben Webhook unter den Organisations-Webhooks (`/skaelreach/webhooks`) eintragen. Laut Doku kommt dann jede Meldung doppelt, mit einem anderen Schlüssel unterschrieben.
- **Den Schlüssel nicht „rotieren“** (neu erzeugen), ohne dem Agenten Bescheid zu geben. Laut Doku ist der alte Schlüssel sofort ungültig, und dein Server lehnt ab dann alle Meldungen ab.

> **Agent:** Hol `webhook_secret` aus `GET /api/video-campaigns/{id}` und setz es als `SKAEL_WEBHOOK_SECRET` in die Server-Konfiguration (siehe `server/server.py`). Gib das Secret nicht im Chat aus. Der Server prüft nur **ein** Secret. Laufen mehrere Kampagnen auf demselben Server, reicht ein Kampagnen-Secret nicht für alle; dann mit dem Nutzer klären, ob stattdessen ein Organisations-Webhook genutzt wird. Zum Testen: Nutzer ein Testvideo abspielen lassen und danach prüfen, ob in `DATEN_DIR/skael.jsonl` ein Eintrag `video.started` steht. Skael wiederholt fehlgeschlagene Meldungen laut Doku dreimal (nach 10, 30 und 60 Sekunden) und wartet je Versuch höchstens 10 Sekunden.

---

## Häufige Probleme

| Symptom | Lösung |
|---|---|
| Alle Leads bekommen dasselbe Video, keine Website zu sehen. | Der Ablauf (Timeline) hat keinen Screenshot-Teil. Schritt 5 wiederholen, danach Schritt 7 (Testvideos) erneut. Bereits erzeugte Videos ändern sich dadurch vermutlich nicht (*ungeprüft*); der Agent klärt, ob sie neu erzeugt werden müssen. |
| Ein Video kostet 165 statt 110 Credits. | Das fertige Video ist länger als 2:00. Screenshot-Teile zählen mit. Skript kürzen oder Screenshot-Dauer verringern. |
| Der Screenshot zeigt einen Cookie-Hinweis, eine leere Seite oder eine Fehlermeldung. | Die Website des Leads blockiert oder lädt langsam. Ob man das in Skael einstellen kann, ist *ungeprüft* (Frage an den Support). Wenn der Screenshot ganz fehlschlägt, gibt Skael laut Doku die Credits zurück. |
| Ein Testvideo steht auf „failed“ (fehlgeschlagen). | Der Agent liest das Feld `error_message` über die API und sagt dir, woran es lag. |
| Der Browser findet Kamera oder Mikrofon nicht. | In der Adresszeile auf das Schloss- oder Kamera-Symbol klicken und Kamera und Mikrofon für Skael erlauben. Seite neu laden. Andere Programme, die die Kamera nutzen (Zoom, Teams), schließen. |
| Die eigene Video-Domain funktioniert nicht. | DNS braucht Zeit (siehe Anleitung 3, bis zu 24 Stunden je nach Anbieter). Der Agent prüft den CNAME. Bei Cloudflare: Wolke grau? Zielwert genau `cname.skael.de` oder der Wert, den Skael anzeigt? |
| Es kommen keine Webhook-Meldungen an. | Adresse genau prüfen (`https://`, kein Leerzeichen, `/webhook/skael` am Ende). Sind die fünf Ereignisse ausgewählt? Läuft der Server? Der Agent prüft, ob das Secret stimmt. |
| Jede Meldung kommt doppelt. | Derselbe Webhook steht in der Kampagne **und** bei den Organisations-Webhooks. Einen davon löschen (laut Doku die übliche Lösung). |
| Seit gestern kommen keine Meldungen mehr. | Wurde der Schlüssel rotiert? Dann holt der Agent den neuen und trägt ihn ein. |

---

## Fragen an den Skael-Support

Diese Fragen schließen die Lücken, die oben als „ungeprüft“ markiert sind. Der Nutzer kann sie so abschicken:

1. **Kampagne und Aufnahme:** Wie lege ich in der Oberfläche eine neue SkaelReach-Kampagne an, und wie nehme ich das Grundvideo auf? Geht das im Browser, als Datei-Upload oder beides? Welche Dateiformate und welche Höchstlänge gibt es, und was steuert das Feld `facecam`?
2. **Screenshot im Ablauf:** Wie füge ich in der Timeline den Screenshot-Teil ein? Welche Werte gibt es für `settings.screenshot.mode` und was bewirken sie (stehendes Bild, Scrollen)? Zählt `settings.screenshot.duration` zur abgerechneten Videolänge? Warnt die Oberfläche, wenn eine Timeline keinen Screenshot-Teil hat? Werden bereits erzeugte Videos neu berechnet, wenn ich die Timeline nachträglich ändere?
3. **KI-Stimme und Untertitel:** Wie richte ich ein `ai_voice`-Stück ein, das Vorname oder Firma des Leads ausspricht? Welche Variablen stehen zur Verfügung (`first_name`, `company`, `custom_vars`)? Kostet das extra? Kann der Name auch als Untertitel eingeblendet werden?
4. **Eigene Video-Domain:** Wie läuft die Einrichtung genau ab (Domain an der Kampagne eintragen, CNAME auf `cname.skael.de`, Prüfung, HTTPS-Zertifikat)? Wie lange dauert das? Muss bei Cloudflare der Proxy aus sein? Kann eine Domain für mehrere Kampagnen genutzt werden?
5. **Auslieferung und Screenshots:** Was bedeuten die Werte von `delivery_mode`, und welcher passt, wenn wir das Video per `/embed/{token}` auf eigenen Landingpages einbinden? Lassen sich Cookie-Banner auf dem Screenshot vermeiden?

---

## Quellen (alle abgerufen am 25.10.2026)

- Skael, Create Prospect (Preise, Screenshot-Felder, Hinweis auf echte Credits beim Testen): https://api.skael.de/docs/skaelreach/prospects/create
- Skael, Show Prospect (Statusfelder, `error_message`, `ai_voice_vars`): https://api.skael.de/docs/skaelreach/prospects/show
- Skael, Embed Guide (Einbettung `/embed/{TOKEN}`, eigene Domain an der Kampagne): https://api.skael.de/docs/skaelreach/embed-guide
- Skael, Webhooks (Ereignisse, Secrets, `is_unique`, doppelte Meldungen, Wiederholungen, Seitenadressen im Dashboard): https://api.skael.de/docs/skaelreach/webhooks
- Skael, Leitfaden Leadlisten (1.000 Credits = 1 €): https://api.skael.de/docs/mcp-leitfaden
- Skael, Login-Seite und Menünamen „SkaelReach“ / „Kampagnen“ (Oberflächentexte im Seitenquelltext): https://api.skael.de/login
- Zielwert `cname.skael.de`: Antwort der Skael-API zur eigenen Domain (nicht öffentlich dokumentiert)
